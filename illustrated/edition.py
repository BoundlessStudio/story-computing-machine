"""Approval-bound illustrated editions. Run ``python -m illustrated.edition --help``.

The CLI records actual human decisions; it cannot authenticate a chat identity.
Agents must never invent approvals. Image calls use the bundled imagegen CLI
unchanged, and temporary candidates remain outside the edition package.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Callable
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-image-2.5-sunburst-2026-09-08"
QUALITY = "high"
MODES = {"Classic": 8, "Deluxe": 12, "Cinematic": 8}
SIZES = {"1024x1024", "1536x1024", "1024x1536"}
KINDS = {"character", "location", "object", "style", "illustration", "cover"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def file_hash(path: Path, *, text: bool = False) -> str:
    return hashlib.sha256(_text(path).encode("utf-8") if text else path.read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty")
    return value.strip()


def _safe_path(parent: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Use a nonempty repository-relative POSIX path")
    component = Path(relative)
    if component.is_absolute() or ".." in component.parts or ":" in relative:
        raise ValueError(f"Unsafe relative path: {relative}")
    result = (parent / component).resolve()
    if not result.is_relative_to(parent.resolve()) or result == parent.resolve():
        raise ValueError(f"Path escapes its root: {relative}")
    return result


def edition_directory(root: Path, slug: str) -> Path:
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise ValueError("Edition slug must be lowercase kebab-case")
    return _safe_path(Path(root).resolve() / "illustrated", slug)


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"Cannot verify Git worktree: {result.stderr.strip()}")
    return result.stdout.strip()


def _mutable(root: Path) -> None:
    root = Path(root).resolve()
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise ValueError("Use the absolute root of the assigned worktree")
    branch = _git(root, "branch", "--show-current")
    if not branch or branch in {"main", "master"}:
        raise ValueError("Use a dedicated non-main illustrated worktree before editing an edition")


require_worktree = _mutable


def _front(path: Path, *, body: bool = False) -> tuple[dict[str, str], str]:
    # Title resolution reads only frontmatter, never unrelated prose.
    with path.open(encoding="utf-8-sig") as stream:
        if stream.readline().strip() != "---":
            raise ValueError(f"Missing frontmatter: {path}")
        front: dict[str, str] = {}
        for line in stream:
            if line.strip() == "---":
                return front, stream.read().replace("\r\n", "\n").replace("\r", "\n") if body else ""
            if ":" not in line:
                raise ValueError(f"Malformed frontmatter: {path}")
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if key in front:
                raise ValueError(f"Duplicate frontmatter field: {key}")
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid quoted metadata in {path}") from error
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            front[key] = value
    raise ValueError(f"Unterminated frontmatter: {path}")


def _identity(directory: Path) -> dict[str, Any]:
    current, bundle = directory / "story.md", directory / "05-story.md"
    if current.is_file() == bundle.is_file():
        raise ValueError(f"Missing or ambiguous story layout: {directory.name}")
    if current.is_file():
        front, _ = _front(current)
        if not {"title", "slug", "created", "canon"}.issubset(front) or front["canon"] not in {"true", "false"}:
            raise ValueError(f"Invalid authoritative story marker: {current}")
        record = {"title": front["title"], "slug": front["slug"], "canon": front["canon"] == "true"}
        record.update(layout="current", prose="story.md", prompt="prompt.md")
    else:
        try:
            data = json.loads(_text(directory / "story.json"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid authoritative bundle marker: {directory}") from error
        if not isinstance(data, dict) or type(data.get("canon")) is not bool:
            raise ValueError(f"Invalid authoritative bundle marker: {directory}")
        front, _ = _front(bundle)
        if any(front.get(key) != data.get(key) for key in ("title", "slug", "created")):
            raise ValueError(f"Bundle identity differs from prose metadata: {directory}")
        record = {"title": data.get("title"), "slug": data.get("slug"), "canon": data["canon"]}
        record.update(layout="bundle", prose="05-story.md", prompt="00-prompt.md")
    if record["slug"] != directory.name or not SLUG.fullmatch(record["slug"]):
        raise ValueError(f"Invalid source slug: {directory}")
    _nonempty(record["title"], "Source title")
    return record


def resolve_source(root: Path, selector: str) -> dict[str, Any]:
    """Resolve an exact slug first, otherwise an exact case-sensitive title."""
    selector = _nonempty(selector, "Source title or slug")
    story_root = Path(root).resolve() / "stories"
    if SLUG.fullmatch(selector) and (story_root / selector).is_dir():
        return _identity(_safe_path(story_root, selector))
    matches = []
    for directory in sorted(story_root.iterdir()):
        if not directory.is_dir() or directory.name.startswith("_"):
            continue
        try:
            identity = _identity(directory)
        except (ValueError, OSError):
            continue
        if identity["title"] == selector:
            matches.append(identity)
    if not matches:
        raise ValueError(f"No repository story has exact title or slug {selector!r}")
    if len(matches) != 1:
        raise ValueError(f"Ambiguous title {selector!r}; choose a source slug: {', '.join(item['slug'] for item in matches)}")
    return matches[0]


def _source_reference_names(prompt: str) -> list[str]:
    names = []
    for match in re.finditer(r"(?ims)^#{1,3}[^\n]*reference[^\n]*image[^\n]*\n(?P<body>.*?)(?=^#{1,3}\s|\Z)", prompt):
        for line in match["body"].splitlines():
            value = re.sub(r"^\s*[-*]\s*", "", line).strip().strip("`")
            if not value or value.lower().rstrip(".") in {"none", "none supplied"}:
                continue
            if re.search(r"\.(?:png|jpe?g|webp|gif|avif)(?:\s+\(\d+\))?$", value, re.I):
                names.append(re.sub(r"\s+\(\d+\)$", "", value))
    return names


def _pin_source(root: Path, identity: dict[str, Any]) -> dict[str, Any]:
    prefix = f"stories/{identity['slug']}/"
    paths = [prefix + identity["prose"], prefix + identity["prompt"], prefix + "title-image.jpg"]
    if identity["layout"] == "bundle":
        paths.append(prefix + "story.json")
    else:
        from pages.build import _review_problems
        review_path = _safe_path(root, prefix + "review.md")
        prompt_source = _text(_safe_path(root, prefix + identity["prompt"]))
        profiles = re.findall(r"(?m)^-[ \t]+Craft profile:[ \t]*([^\r\n]+)", prompt_source)
        if not review_path.is_file():
            raise ValueError("A finished current-format source requires its existing passing review")
        problems = _review_problems(_text(review_path), profiles[-1].strip() if profiles else None)
        if problems:
            raise ValueError("Current source review is not passing: " + "; ".join(problems))
        paths.append(prefix + "review.md")
    for relative in paths:
        if not _safe_path(root, relative).is_file():
            raise ValueError(f"Required source input missing: {relative}")
    _, body = _front(_safe_path(root, prefix + identity["prose"]), body=True)
    return {
        "slug": identity["slug"], "title": identity["title"], "layout": identity["layout"],
        "commit": _git(root, "rev-parse", "HEAD"), "prose": prefix + identity["prose"],
        "files": {relative: file_hash(_safe_path(root, relative), text=relative.endswith((".md", ".json"))) for relative in paths},
        "bodySha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "referenceNames": _source_reference_names(_text(_safe_path(root, prefix + identity["prompt"]))),
        "coverInspection": None,
    }


def verify_source(root: Path, manifest: dict[str, Any]) -> None:
    source = manifest["source"]
    identity = _identity(_safe_path(Path(root) / "stories", source["slug"]))
    if any(identity[key] != source[key] for key in ("title", "layout", "slug")):
        raise ValueError("Source identity changed; a deliberate source version decision is required")
    for relative, expected in source["files"].items():
        path = _safe_path(Path(root), relative)
        if not path.is_file() or file_hash(path, text=relative.endswith((".md", ".json"))) != expected:
            raise ValueError(f"Source changed: {relative}; renew the source version decision, never silently refresh")
    _, body = _front(_safe_path(Path(root), source["prose"]), body=True)
    if hashlib.sha256(body.encode("utf-8")).hexdigest() != source["bodySha256"]:
        raise ValueError("Source body differs from the pinned edition")


def get_source_body(root: Path, manifest: dict[str, Any]) -> str:
    verify_source(root, manifest)
    return _front(_safe_path(Path(root), manifest["source"]["prose"]), body=True)[1]


source_body = get_source_body


def _assets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [manifest["cover"], *manifest["references"], *manifest["illustrations"]]


def _asset(manifest: dict[str, Any], asset_id: str) -> dict[str, Any]:
    for asset in _assets(manifest):
        if asset["id"] == asset_id:
            return asset
    raise ValueError(f"Unknown asset: {asset_id}")


def load_edition(root: Path, slug: str) -> dict[str, Any]:
    path = edition_directory(root, slug) / "edition.json"
    try:
        manifest = json.loads(_text(path))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot load edition: {path}") from error
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1 or manifest.get("slug") != slug:
        raise ValueError("Unsupported or mismatched edition manifest")
    if manifest.get("mode") not in MODES or manifest.get("model") != MODEL or manifest.get("quality") != QUALITY:
        raise ValueError("Edition must use a supported mode and the pinned Sunburst model at high quality")
    for field in ("source", "approvals", "cover"):
        if not isinstance(manifest.get(field), dict):
            raise ValueError(f"Edition requires an object: {field}")
    for field in ("references", "illustrations", "externalReferences"):
        if not isinstance(manifest.get(field), list):
            raise ValueError(f"Edition requires a list: {field}")
    source = manifest["source"]
    required = {"slug", "title", "layout", "commit", "prose", "files", "bodySha256"}
    if not required.issubset(source) or source["layout"] not in {"current", "bundle"} or not isinstance(source["slug"], str) or not SLUG.fullmatch(source["slug"]):
        raise ValueError("Missing or invalid pinned source identity")
    prefix = f"stories/{source['slug']}/"
    names = {"05-story.md", "00-prompt.md", "story.json", "title-image.jpg"} if source["layout"] == "bundle" else {"story.md", "prompt.md", "review.md", "title-image.jpg"}
    expected_prose = prefix + ("05-story.md" if source["layout"] == "bundle" else "story.md")
    if source["prose"] != expected_prose or not isinstance(source["files"], dict) or set(source["files"]) != {prefix + name for name in names}:
        raise ValueError("Pin exactly the authoritative source, prompt, cover and review/identity inputs")
    for value in [source["bodySha256"], *source["files"].values()]:
        if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ValueError("Source pins require SHA-256 hashes")
    if not isinstance(source["commit"], str) or not re.fullmatch(r"[a-f0-9]{40,64}", source["commit"]):
        raise ValueError("Source provenance requires a full Git commit ID")
    if manifest["cover"].get("id") != "cover" or manifest["cover"].get("kind") != "cover" or type(manifest["cover"].get("reused")) is not bool:
        raise ValueError("The edition requires one explicit reused or generated cover")
    if any(item.get("kind") not in {"character", "location", "object", "style"} for item in manifest["references"]) or any(item.get("kind") != "illustration" for item in manifest["illustrations"]):
        raise ValueError("Reference sheets and interior illustrations must have their proper kinds")
    assets = _assets(manifest)
    ids = [asset.get("id") for asset in assets] + [item.get("id") for item in manifest["externalReferences"]]
    if any(not isinstance(item, str) or not SLUG.fullmatch(item) or item == "source-cover" for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("Asset and external-reference IDs must be unique kebab-case values")
    for asset in assets:
        _safe_path(edition_directory(root, slug), asset["path"])
        expected_path = ("cover.jpg" if asset.get("reused") else "cover.png") if asset["id"] == "cover" else f"{'illustrations' if asset.get('kind') == 'illustration' else 'references'}/{asset['id']}.png"
        if asset["path"] != expected_path:
            raise ValueError(f"Asset must use its dedicated image path: {asset['id']}")
        if asset.get("kind") not in KINDS or type(asset.get("attempts")) is not int or asset["attempts"] < 0:
            raise ValueError(f"Invalid asset kind or attempt count: {asset['id']}")
        if not isinstance(asset.get("references"), list):
            raise ValueError(f"Asset requires reference IDs: {asset['id']}")
        for dependency in asset["references"]:
            if dependency not in ids and dependency != "source-cover":
                raise ValueError(f"Unknown reference {dependency!r} in {asset['id']}")
    return manifest


def save_edition(root: Path, manifest: dict[str, Any]) -> None:
    _mutable(root)
    path = edition_directory(root, manifest["slug"]) / "edition.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _image(path: Path, size: str | None = None) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("Use JPEG, PNG or WebP images")
            if size and image.size != tuple(map(int, size.split("x"))):
                raise ValueError(f"Expected {size}, found {image.width}x{image.height}")
    except (OSError, SyntaxError, ValueError) as error:
        raise ValueError(f"Invalid image {path}: {error}") from error


def create_edition(root: Path, selector: str, request: str, *, slug: str | None = None, mode: str = "Classic", references: list[Path] | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    _mutable(root)
    if mode not in MODES:
        raise ValueError(f"Unknown presentation mode: {mode}")
    _nonempty(request, "Verbatim user request")
    identity = resolve_source(root, selector)
    slug = slug or identity["slug"]
    directory = edition_directory(root, slug)
    if directory.exists():
        raise ValueError(f"Edition already exists: {slug}; explicit revisions resume it, additional editions need a distinct slug")
    source = _pin_source(root, identity)
    originals = []
    for index, path in enumerate(references or [], 1):
        path = Path(path).resolve()
        _image(path)
        originals.append({"id": f"external-{index:03d}", "displayName": path.name, "path": str(path), "sha256": file_hash(path), "inspection": None})
    supplied = Counter(item["displayName"] for item in originals)
    missing = Counter(source["referenceNames"]) - supplied
    if missing:
        raise ValueError(f"Restore or reattach every inventoried original: {', '.join(missing.elements())}")
    cover_source = _safe_path(root, f"stories/{identity['slug']}/title-image.jpg")
    _image(cover_source)
    manifest = {
        "schemaVersion": 1, "slug": slug, "title": identity["title"], "createdAt": _now(),
        "source": source, "mode": mode, "model": MODEL, "quality": QUALITY,
        "externalReferences": originals, "references": [], "illustrations": [],
        "cover": {"id": "cover", "kind": "cover", "path": "cover.jpg", "sha256": file_hash(cover_source), "reused": True,
                  "prompt": "Reuse the original cover without alteration.", "size": "1024x1536", "references": ["source-cover"], "attempts": 0, "accepted": None},
        "approvals": {}, "layoutPreview": None, "render": None, "review": None,
    }
    directory.mkdir(parents=True)
    (directory / "references").mkdir()
    (directory / "illustrations").mkdir()
    shutil.copy2(cover_source, directory / "cover.jpg")
    inventory = "\n".join(f"- `{item['displayName']}` ({item['id']})" for item in originals) or "- None supplied."
    (directory / "prompt.md").write_text(f"# Illustrated edition request\n\n{request}\n\n## Source\n\n- Story: {identity['title']} (`{identity['slug']}`).\n- Source commit: `{source['commit']}`.\n\n## External reference images\n\n{inventory}\n", encoding="utf-8", newline="\n")
    (directory / "plan.md").write_text(f"# Illustration plan\n\nStatus: PENDING\n\n## Story analysis\n\nSeparate source-established people, places, objects and changes from proposed visual choices.\n\n## Art direction and house layout\n\nMode: {mode}. Planning target: {MODES[mode]} interior illustrations; cover and references counted separately.\n\n## Moments and placements\n\nRecord every illustration, its stable block anchor, reveal timing, layout and generation brief.\n\n## Reference inventory and generation counts\n\nRecord character/outfit, location, object and style references, plus any custom cover.\n", encoding="utf-8", newline="\n")
    (directory / "review.md").write_text("# Illustrated edition review\n\nVerdict: PENDING\n\n- Source fidelity: PENDING\n- Visual continuity: PENDING\n- Web readability: PENDING\n- Every PDF page: PENDING\n- Blocking: pending independent review.\n", encoding="utf-8", newline="\n")
    save_edition(root, manifest)
    return manifest


def configure_asset(root: Path, slug: str, asset_id: str, *, kind: str, prompt: str, size: str = "1536x1024", references: list[str] | None = None, after: str | None = None, layout: str = "inline", alt: str = "", caption: str = "") -> dict[str, Any]:
    manifest = load_edition(root, slug)
    verify_source(root, manifest)
    if not SLUG.fullmatch(asset_id) or asset_id == "source-cover" or kind not in KINDS or size not in SIZES:
        raise ValueError("Invalid asset ID, kind, or explicit image size")
    if kind == "cover" and asset_id != "cover" or asset_id == "cover" and kind != "cover":
        raise ValueError("The edition cover has the reserved ID 'cover'")
    if asset_id in {item["id"] for item in manifest["externalReferences"]}:
        raise ValueError("Asset ID collides with an external reference")
    previous = next((item for item in _assets(manifest) if item["id"] == asset_id), None)
    if previous and previous["kind"] != kind:
        raise ValueError("An existing stable asset ID cannot change kind")
    refs = references if references is not None else (["source-cover"] + [item["id"] for item in manifest["externalReferences"]] if kind != "illustration" else [])
    ids = {item["id"] for item in _assets(manifest)} | {item["id"] for item in manifest["externalReferences"]} | {"source-cover"}
    if len(set(refs)) != len(refs) or asset_id in refs or any(item not in ids for item in refs):
        raise ValueError("References must be unique known IDs and cannot refer to the asset itself")
    asset = dict(previous or {})
    asset.update(id=asset_id, kind=kind, prompt=_nonempty(prompt, "Generation brief"), size=size, references=refs)
    asset.setdefault("attempts", 0)
    asset.setdefault("sha256", None)
    asset.setdefault("accepted", None)
    asset["path"] = "cover.png" if kind == "cover" else f"{'illustrations' if kind == 'illustration' else 'references'}/{asset_id}.png"
    if kind == "illustration":
        if layout not in {"inline", "full-page", "spot"}:
            raise ValueError("Unknown illustration layout")
        asset.update(after=_nonempty(after, "Stable placement anchor"), layout=layout, alt=_nonempty(alt, "Accessible image description"), caption=caption)
    if kind == "cover":
        asset["reused"] = False
        manifest["cover"] = asset
    elif previous is None:
        manifest["illustrations" if kind == "illustration" else "references"].append(asset)
    else:
        collection = manifest["illustrations" if kind == "illustration" else "references"]
        collection[collection.index(previous)] = asset
    save_edition(root, manifest)
    return manifest


def inspect_original(root: Path, slug: str, reference_id: str, evidence: str) -> dict[str, Any]:
    manifest = load_edition(root, slug)
    verify_source(root, manifest)
    evidence = _nonempty(evidence, "Visible inspection evidence")
    if reference_id in {"cover", "source-cover"}:
        path = _safe_path(Path(root), f"stories/{manifest['source']['slug']}/title-image.jpg")
        _image(path)
        inspection = {"sha256": file_hash(path), "evidence": evidence}
        manifest["source"]["coverInspection"] = inspection
        if manifest["cover"]["reused"]:
            cover = manifest["cover"]
            saved = _safe_path(edition_directory(root, slug), cover["path"])
            if file_hash(saved) != inspection["sha256"]:
                raise ValueError("Reused edition cover differs from the source cover")
            cover["accepted"] = {"sha256": cover["sha256"], "inputsSha256": _digest({"sourceCover": inspection["sha256"]}), "evidence": evidence}
    else:
        item = next((item for item in manifest["externalReferences"] if item["id"] == reference_id), None)
        if item is None:
            raise ValueError(f"Unknown original reference: {reference_id}")
        path = Path(item["path"])
        _image(path)
        if file_hash(path) != item["sha256"]:
            raise ValueError("Original reference changed; resolve the changed input before continuing")
        item["inspection"] = {"sha256": item["sha256"], "evidence": evidence}
    save_edition(root, manifest)
    return manifest


def _check_originals(root: Path, manifest: dict[str, Any], *, inspected: bool = True) -> None:
    source_cover = manifest["source"]["files"][f"stories/{manifest['source']['slug']}/title-image.jpg"]
    inspection = manifest["source"].get("coverInspection")
    if inspected and (not isinstance(inspection, dict) or inspection.get("sha256") != source_cover or not inspection.get("evidence")):
        raise ValueError("Inspect the exact original cover before continuing")
    for item in manifest["externalReferences"]:
        path = Path(item["path"])
        if not path.is_absolute() or not path.is_file() or file_hash(path) != item["sha256"]:
            raise ValueError(f"Missing or changed original reference: {item['displayName']}; restore access or reattach")
        _image(path)
        inspection = item.get("inspection")
        if inspected and (not isinstance(inspection, dict) or inspection.get("sha256") != item["sha256"] or not inspection.get("evidence")):
            raise ValueError(f"Inspect the exact original reference: {item['displayName']}")


def _asset_spec(asset: dict[str, Any]) -> dict[str, Any]:
    return {key: asset[key] for key in ("id", "kind", "path", "prompt", "size", "references", "after", "layout", "alt", "caption", "reused") if key in asset}


def _plan_payload(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    directory = edition_directory(root, manifest["slug"])
    source = {key: value for key, value in manifest["source"].items() if key != "coverInspection"}
    return {"slug": manifest["slug"], "title": manifest["title"], "source": source, "mode": manifest["mode"], "model": manifest["model"], "quality": manifest["quality"],
            "promptSha256": file_hash(directory / "prompt.md", text=True), "planSha256": file_hash(directory / "plan.md", text=True),
            "assets": [_asset_spec(asset) for asset in _assets(manifest)],
            "originals": [{key: item[key] for key in ("id", "displayName", "sha256")} for item in manifest["externalReferences"]]}


def _selected(asset: dict[str, Any]) -> dict[str, Any]:
    return {"id": asset["id"], "sha256": asset.get("sha256"), "accepted": asset.get("accepted")}


def _renderer_hashes() -> dict[str, str]:
    paths = [ROOT / name for name in ("pages/illustrated.css", "pages/illustrated_editions.py", "illustrated/export.mjs", "illustrated/package-lock.json")]
    fonts = ROOT / "pages/fonts"
    if fonts.is_dir():
        paths += sorted(path for path in fonts.rglob("*") if path.is_file())
    return {path.relative_to(ROOT).as_posix(): file_hash(path) for path in paths if path.is_file()}


def stage_digest(root: Path, manifest: dict[str, Any], stage: str) -> str:
    """Hash stage inputs, excluding counters and that stage's own approval."""
    payload = _plan_payload(root, manifest)
    if stage == "plan":
        return _digest(payload)
    payload.update(references=[_selected(asset) for asset in manifest["references"]], cover=_selected(manifest["cover"]), layoutPreview=manifest.get("layoutPreview"))
    if stage == "visuals":
        return _digest(payload)
    payload["illustrations"] = [_selected(asset) for asset in manifest["illustrations"]]
    payload["renderer"] = _renderer_hashes()
    if stage == "render":
        return _digest(payload)
    if stage == "final":
        payload.update(render=manifest.get("render"), review=manifest.get("review"))
        return _digest(payload)
    raise ValueError(f"Unknown approval stage: {stage}")


def _require_approval(root: Path, manifest: dict[str, Any], stage: str) -> None:
    approval = manifest["approvals"].get(stage)
    if not isinstance(approval, dict) or approval.get("actor") != "user" or not isinstance(approval.get("decision"), str) or not approval["decision"].strip() or approval.get("inputsSha256") != stage_digest(root, manifest, stage):
        raise ValueError(f"Missing or stale explicit user {stage} approval")


def _dependency(root: Path, manifest: dict[str, Any], reference_id: str, visiting: set[str] | None = None) -> tuple[Path, str]:
    if reference_id == "source-cover":
        path = _safe_path(Path(root), f"stories/{manifest['source']['slug']}/title-image.jpg")
        return path, file_hash(path)
    external = next((item for item in manifest["externalReferences"] if item["id"] == reference_id), None)
    if external:
        return Path(external["path"]), external["sha256"]
    asset = _asset(manifest, reference_id)
    _check_asset(root, manifest, asset, visiting)
    return _safe_path(edition_directory(root, manifest["slug"]), asset["path"]), asset["sha256"]


def _art_direction(root: Path, manifest: dict[str, Any]) -> str:
    plan = _text(edition_directory(root, manifest["slug"]) / "plan.md")
    sections = re.findall(r"(?ms)^## Art direction(?: and house layout)?[ \t]*\n(.*?)(?=^## |\Z)", plan)
    if len(sections) != 1 or not sections[0].strip():
        raise ValueError("The plan requires exactly one nonempty '## Art direction' section")
    return sections[0].strip()


def _asset_inputs(root: Path, manifest: dict[str, Any], asset: dict[str, Any], visiting: set[str] | None = None) -> tuple[str, list[Path]]:
    ids = list(asset["references"])
    if asset["kind"] != "illustration":
        ids = list(dict.fromkeys(["source-cover", *[item["id"] for item in manifest["externalReferences"]], *ids]))
    dependencies = [_dependency(root, manifest, item, visiting) for item in ids]
    direction = _art_direction(root, manifest)
    visual_spec = {key: asset[key] for key in ("id", "kind", "prompt", "size")}
    value = {"source": manifest["source"]["files"], "model": manifest["model"], "quality": manifest["quality"],
             "artDirection": direction, "asset": visual_spec,
             "dependencies": dict(zip(ids, [digest for _, digest in dependencies]))}
    return _digest(value), [path for path, _ in dependencies]


def _check_asset(root: Path, manifest: dict[str, Any], asset: dict[str, Any], visiting: set[str] | None = None) -> None:
    visiting = set(visiting or ())
    if asset["id"] in visiting:
        raise ValueError(f"Cyclic asset dependencies at {asset['id']}")
    visiting.add(asset["id"])
    path = _safe_path(edition_directory(root, manifest["slug"]), asset["path"])
    if not path.is_file() or not asset.get("sha256") or file_hash(path) != asset["sha256"]:
        raise ValueError(f"Missing or changed selected asset: {asset['id']}")
    _image(path, None if asset.get("reused") else asset.get("size"))
    accepted = asset.get("accepted")
    if not isinstance(accepted, dict) or accepted.get("sha256") != asset["sha256"] or not accepted.get("evidence"):
        raise ValueError(f"Inspect and accept the exact saved image: {asset['id']}")
    expected = _digest({"sourceCover": manifest["source"]["files"][f"stories/{manifest['source']['slug']}/title-image.jpg"]}) if asset.get("reused") else _asset_inputs(root, manifest, asset, visiting)[0]
    if accepted.get("inputsSha256") != expected:
        raise ValueError(f"Selected asset has stale generation dependencies: {asset['id']}")


def _preview_dependencies(path: Path) -> dict[str, str]:
    """Pin resources actually displayed by the generated local HTML preview."""
    if path.suffix.lower() not in {".html", ".htm"}:
        return {}
    dependencies: dict[str, str] = {}

    def include(value: str, parent: Path) -> None:
        location = urlsplit(value)
        if location.scheme == "data":
            return
        if location.scheme not in {"", "file"} or location.netloc:
            raise ValueError("The approval layout preview must use local rendering resources")
        resource = Path(url2pathname(location.path)) if location.scheme == "file" else parent / unquote(location.path)
        resource = resource.resolve()
        if not resource.is_file():
            raise ValueError(f"Missing layout preview resource: {resource}")
        key = str(resource)
        if key in dependencies:
            return
        dependencies[key] = file_hash(resource)
        if resource.suffix.lower() == ".css":
            for match in re.finditer(r"url\(\s*['\"]?(.*?)['\"]?\s*\)", _text(resource), re.I):
                include(match[1], resource.parent)

    class Resources(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if tag in {"img", "script", "source"} and attributes.get("src"):
                include(attributes["src"], path.parent)
            if tag == "link" and "stylesheet" in attributes.get("rel", "").lower().split() and attributes.get("href"):
                include(attributes["href"], path.parent)

    Resources().feed(_text(path))
    return dependencies


def record_layout_preview(root: Path, slug: str, path: Path, evidence: str) -> dict[str, Any]:
    manifest = load_edition(root, slug)
    verify_source(root, manifest)
    _require_approval(root, manifest, "plan")
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("Layout preview must exist for display and inspection")
    manifest["layoutPreview"] = {"path": str(path), "sha256": file_hash(path), "planSha256": stage_digest(root, manifest, "plan"), "renderer": _renderer_hashes(), "dependencies": _preview_dependencies(path), "evidence": _nonempty(evidence, "Layout preview inspection evidence")}
    save_edition(root, manifest)
    return manifest


def _check_plan(root: Path, manifest: dict[str, Any]) -> None:
    plan = _text(edition_directory(root, manifest["slug"]) / "plan.md")
    if re.search(r"(?im)^Status:\s*PENDING\s*$", plan) or not plan.strip():
        raise ValueError("Complete the story-specific plan before approval")
    if not manifest["references"] or not manifest["illustrations"]:
        raise ValueError("The plan must declare reference sheets and interior illustrations, with approved counts")
    for asset in _assets(manifest):
        _nonempty(asset.get("prompt"), f"Generation brief for {asset['id']}")
        if asset.get("size") not in SIZES:
            raise ValueError(f"Use explicit square, landscape or portrait dimensions for {asset['id']}")
    _art_direction(root, manifest)
    from pages.illustrated_editions import block_anchors
    anchors = {item["id"] for item in block_anchors(get_source_body(root, manifest), manifest["title"])}
    reference_ids = {asset["id"] for asset in manifest["references"]}
    for asset in manifest["illustrations"]:
        _nonempty(asset.get("after"), "Illustration placement anchor")
        if asset["after"] not in anchors:
            raise ValueError(f"Unknown or stale illustration anchor: {asset['after']}")
        _nonempty(asset.get("alt"), "Accessible image description")
        if asset.get("layout") not in {"inline", "full-page", "spot"} or not reference_ids.intersection(asset["references"]):
            raise ValueError(f"Illustration {asset['id']} needs a layout and applicable character/location/object references")


def _check_visuals(root: Path, manifest: dict[str, Any], *, preview_file: bool = False) -> None:
    _require_approval(root, manifest, "plan")
    for asset in [manifest["cover"], *manifest["references"]]:
        _check_asset(root, manifest, asset)
    preview = manifest.get("layoutPreview")
    if not isinstance(preview, dict) or preview.get("planSha256") != stage_digest(root, manifest, "plan") or not preview.get("evidence"):
        raise ValueError("Display and inspect a representative layout preview for the current plan")
    if preview.get("renderer") != _renderer_hashes():
        raise ValueError("Layout rendering resources changed; display a current layout preview before approval")
    if preview_file:
        for relative, expected in preview.get("dependencies", {}).items():
            dependency = Path(relative)
            if not dependency.is_file() or file_hash(dependency) != expected:
                raise ValueError("Displayed layout preview resources are missing or changed")
    if preview_file and (not Path(preview["path"]).is_file() or file_hash(Path(preview["path"])) != preview["sha256"]):
        raise ValueError("Displayed layout preview is missing or changed")


def _check_render(root: Path, manifest: dict[str, Any]) -> None:
    _check_visuals(root, manifest)
    _require_approval(root, manifest, "visuals")
    for asset in manifest["illustrations"]:
        _check_asset(root, manifest, asset)


def _check_pdf(root: Path, manifest: dict[str, Any]) -> None:
    render = manifest.get("render")
    pdf = edition_directory(root, manifest["slug"]) / "edition.pdf"
    if not isinstance(render, dict) or render.get("inputsSha256") != stage_digest(root, manifest, "render") or not pdf.is_file() or file_hash(pdf) != render.get("pdfSha256"):
        raise ValueError("Missing or stale rendered PDF; render the current approved inputs")
    if not pdf.read_bytes().startswith(b"%PDF-"):
        raise ValueError("Edition PDF is not a PDF document")


def _check_review(root: Path, manifest: dict[str, Any]) -> None:
    _check_pdf(root, manifest)
    review = manifest.get("review")
    path = edition_directory(root, manifest["slug"]) / "review.md"
    if not isinstance(review, dict) or review.get("verdict") != "PASS" or review.get("inputsSha256") != stage_digest(root, manifest, "render") or review.get("pdfSha256") != manifest["render"]["pdfSha256"] or review.get("sha256") != file_hash(path, text=True) or not review.get("reviewer") or not review.get("evidence"):
        raise ValueError("A fresh independent passing review must cover the exact illustrations and PDF")


def validate_edition(root: Path, slug: str, phase: str = "draft") -> dict[str, Any]:
    manifest = load_edition(root, slug)
    verify_source(root, manifest)
    _check_originals(root, manifest, inspected=phase != "draft")
    if phase == "draft":
        return manifest
    _check_plan(root, manifest)
    if phase == "plan":
        return manifest
    if phase == "references":
        _require_approval(root, manifest, "plan")
        for asset in [manifest["cover"], *manifest["references"]]:
            _check_asset(root, manifest, asset)
        return manifest
    _check_render(root, manifest)
    if phase in {"render", "visuals"}:
        return manifest
    if phase not in {"review", "final", "capture"}:
        raise ValueError(f"Unknown validation phase: {phase}")
    _check_review(root, manifest)
    if phase in {"final", "capture"}:
        _require_approval(root, manifest, "final")
    return manifest


def approve(root: Path, slug: str, stage: str, decision: str, *, actor: str = "user") -> dict[str, Any]:
    if actor != "user":
        raise ValueError("Only an actual user decision can approve an edition stage")
    decision = _nonempty(decision, "Actual user decision text")
    manifest = validate_edition(root, slug, "plan")
    if stage == "visuals":
        _check_visuals(root, manifest, preview_file=True)
    elif stage == "final":
        _check_render(root, manifest)
        _check_review(root, manifest)
    elif stage != "plan":
        raise ValueError("Approval stage must be plan, visuals or final")
    manifest["approvals"][stage] = {"actor": "user", "decision": decision, "at": _now(), "inputsSha256": stage_digest(root, manifest, stage)}
    save_edition(root, manifest)
    return manifest


def allow_extra_attempt(root: Path, slug: str, asset_id: str, decision: str) -> dict[str, Any]:
    manifest = load_edition(root, slug)
    verify_source(root, manifest)
    asset = _asset(manifest, asset_id)
    attempts = asset.setdefault("extraAttempts", [])
    if asset["attempts"] < 3 + len(attempts):
        raise ValueError("The image still has an authorized attempt available")
    attempts.append({"actor": "user", "decision": _nonempty(decision, "Actual user direction for one additional attempt"), "afterAttempt": asset["attempts"], "at": _now()})
    save_edition(root, manifest)
    return manifest


def generation_command(root: Path, manifest: dict[str, Any], asset_id: str, output: Path, *, imagegen_cli: Path | None = None, python: str | None = None, correction: str = "", dry_run: bool = False) -> list[str]:
    asset = _asset(manifest, asset_id)
    if asset.get("reused"):
        raise ValueError("The original cover is reused; request a custom edition cover before generating")
    _, paths = _asset_inputs(root, manifest, asset)
    cli = Path(imagegen_cli or os.environ.get("IMAGE_GEN", Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills/.system/imagegen/scripts/image_gen.py")).resolve()
    if not cli.is_file():
        raise ValueError("Bundled imagegen CLI not found; pass --imagegen-cli or set IMAGE_GEN")
    prompt = "Use case: illustration-story\nAsset type: " + asset["kind"] + "\n\n" + asset["prompt"]
    prompt += "\n\nApproved story art direction:\n" + _art_direction(root, manifest)
    prompt += "\n\nArtwork only. Do not add prose, captions, speech bubbles, author credits or watermarks; the layout engine supplies typography."
    if paths:
        reference_ids = list(asset["references"])
        if asset["kind"] != "illustration":
            reference_ids = list(dict.fromkeys(["source-cover", *[item["id"] for item in manifest["externalReferences"]], *reference_ids]))
        prompt += "\n\nInput image roles:\n" + "\n".join(f"Image {index}: {reference_id}" for index, reference_id in enumerate(reference_ids, 1))
    if paths:
        prompt += "\n\nInput images are visual references. Preserve established identity, costume, setting geometry and the approved art direction. Create the requested complete asset with the layout specified above."
    if correction:
        prompt += "\n\nTargeted correction: " + correction.strip()
    command = [python or sys.executable, str(cli), "edit" if paths else "generate", "--model", MODEL, "--quality", QUALITY, "--size", asset["size"], "--output-format", "png", "--n", "1", "--no-augment", "--prompt", prompt, "--out", str(output)]
    for path in paths:
        command += ["--image", str(path)]
    if dry_run:
        command.append("--dry-run")
    return command


def generate_asset(root: Path, slug: str, asset_id: str, output: Path, *, imagegen_cli: Path | None = None, python: str | None = None, correction: str = "", dry_run: bool = False, runner: Callable[..., Any] | None = None) -> dict[str, Any]:
    manifest = validate_edition(root, slug, "plan")
    _require_approval(root, manifest, "plan")
    asset = _asset(manifest, asset_id)
    if asset["kind"] == "illustration":
        _check_visuals(root, manifest)
        _require_approval(root, manifest, "visuals")
    if any(item.get("candidate", {}).get("status") == "generating" for item in _assets(manifest)):
        raise ValueError("Resolve the outstanding generation before starting another image")
    if any(item["id"] != asset_id and item.get("candidate", {}).get("status") == "ready" for item in _assets(manifest)):
        raise ValueError("Inspect and accept or reject the completed candidate before starting another image")
    extras = asset.get("extraAttempts", [])
    if any(not item.get("decision") or item.get("actor") != "user" for item in extras):
        raise ValueError("Additional attempts require actual user direction")
    if asset["attempts"] >= 3 + len(extras):
        raise ValueError("Initial generation plus two corrections exhausted; further attempts require user direction")
    if asset["attempts"] and not correction.strip():
        raise ValueError("A corrective generation needs a targeted correction brief")
    output = Path(output).resolve()
    protected = [Path(root).resolve() / name for name in ("stories", "universe", "illustrated", "pages", ".git", ".agents", ".codex")]
    if any(output == path or output.is_relative_to(path) for path in protected):
        raise ValueError("Keep temporary image candidates outside edition, story and other protected production directories")
    if output.exists():
        raise ValueError("Candidate output already exists; use a fresh external path")
    command = generation_command(root, manifest, asset_id, output, imagegen_cli=imagegen_cli, python=python, correction=correction, dry_run=dry_run)
    if dry_run:
        return {"command": command, "attempts": asset["attempts"], "dryRun": True}
    inputs, _ = _asset_inputs(root, manifest, asset)
    asset["attempts"] += 1
    asset["candidate"] = {"path": str(output), "inputsSha256": inputs, "attempt": asset["attempts"], "correction": correction, "status": "generating"}
    save_edition(root, manifest)  # Reserve the attempt before the potentially paid call.
    try:
        (runner or subprocess.run)(command, check=True)
        _image(output, asset["size"])
        asset["candidate"].update(status="ready", sha256=file_hash(output))
    except Exception as error:
        asset["candidate"]["status"] = "failed"
        save_edition(root, manifest)
        raise ValueError(f"Image attempt {asset['attempts']} failed; its persisted attempt is retained") from error
    save_edition(root, manifest)
    return manifest


def accept_candidate(root: Path, slug: str, asset_id: str, evidence: str) -> dict[str, Any]:
    manifest = validate_edition(root, slug, "plan")
    _require_approval(root, manifest, "plan")
    asset = _asset(manifest, asset_id)
    if asset["kind"] == "illustration":
        _check_visuals(root, manifest)
        _require_approval(root, manifest, "visuals")
    candidate = asset.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("status") != "ready":
        raise ValueError("No completed candidate is ready for visual inspection")
    path = Path(candidate["path"])
    if not path.is_file() or file_hash(path) != candidate.get("sha256"):
        raise ValueError("Candidate bytes changed after generation")
    inputs, _ = _asset_inputs(root, manifest, asset)
    if candidate["inputsSha256"] != inputs:
        raise ValueError("Candidate has stale plan or reference dependencies")
    _image(path, asset["size"])
    evidence = _nonempty(evidence, "Visible saved-image inspection evidence")
    target = _safe_path(edition_directory(root, slug), asset["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    _mutable(root)
    shutil.copy2(path, target)
    if asset["kind"] == "cover":
        old_cover = _safe_path(edition_directory(root, slug), "cover.jpg")
        if old_cover != target and old_cover.is_file():
            old_cover.unlink()
    asset["sha256"] = file_hash(target)
    asset["accepted"] = {"sha256": asset["sha256"], "inputsSha256": inputs, "evidence": evidence}
    asset.pop("candidate", None)
    save_edition(root, manifest)
    return manifest


def record_render(root: Path, slug: str, pdf_path: Path | None = None) -> dict[str, Any]:
    manifest = validate_edition(root, slug, "render")
    destination = edition_directory(root, slug) / "edition.pdf"
    pdf_path = Path(pdf_path or destination).resolve()
    if not pdf_path.is_file() or not pdf_path.read_bytes().startswith(b"%PDF-"):
        raise ValueError("Render a valid PDF before recording it")
    _mutable(root)
    if pdf_path != destination:
        shutil.copy2(pdf_path, destination)
    manifest["render"] = {"inputsSha256": stage_digest(root, manifest, "render"), "pdfSha256": file_hash(destination)}
    save_edition(root, manifest)
    return manifest


def record_review(root: Path, slug: str, reviewer: str, evidence: str) -> dict[str, Any]:
    manifest = validate_edition(root, slug, "render")
    _check_pdf(root, manifest)
    path = edition_directory(root, slug) / "review.md"
    report = _text(path)
    if re.findall(r"(?m)^Verdict:\s*(\S+)\s*$", report) != ["PASS"]:
        raise ValueError("Independent review.md must declare exactly one Verdict: PASS")
    for label in ("Source fidelity", "Visual continuity", "Web readability", "Every PDF page"):
        if re.findall(rf"(?m)^- {re.escape(label)}:\s*(\S+)\s*$", report) != ["PASS"]:
            raise ValueError(f"Independent review must pass {label}")
    if re.findall(r"(?m)^- Blocking:\s*(.*?)\s*$", report) != ["none"]:
        raise ValueError("Independent review must declare Blocking: none")
    manifest["review"] = {"verdict": "PASS", "reviewer": _nonempty(reviewer, "Fresh independent reviewer identity"), "evidence": _nonempty(evidence, "Review evidence including every PDF page"), "sha256": file_hash(path, text=True), "inputsSha256": stage_digest(root, manifest, "render"), "pdfSha256": manifest["render"]["pdfSha256"]}
    save_edition(root, manifest)
    return manifest


def repin_source(root: Path, slug: str, decision: str) -> dict[str, Any]:
    """An explicit source-version decision invalidates all downstream approvals."""
    manifest = load_edition(root, slug)
    _mutable(root)
    decision = _nonempty(decision, "Actual user source-version decision")
    identity = resolve_source(root, manifest["source"]["slug"])
    previous = manifest["source"]
    updated = _pin_source(Path(root), identity)
    if updated["files"] == previous["files"]:
        raise ValueError("The pinned source inputs have not changed")
    missing = Counter(updated["referenceNames"]) - Counter(item["displayName"] for item in manifest["externalReferences"])
    if missing:
        raise ValueError(f"Restore new source references before repinning: {', '.join(missing.elements())}")
    manifest["source"] = updated
    manifest["title"] = identity["title"]
    manifest["sourceDecision"] = {"actor": "user", "decision": decision, "previousCommit": previous["commit"], "previousFiles": previous["files"], "at": _now()}
    manifest["approvals"] = {}
    manifest["layoutPreview"] = manifest["render"] = manifest["review"] = None
    for asset in _assets(manifest):
        asset["accepted"] = None
        asset.pop("candidate", None)
    if manifest["cover"]["reused"]:
        cover = manifest["cover"]
        source = _safe_path(Path(root), f"stories/{identity['slug']}/title-image.jpg")
        shutil.copy2(source, _safe_path(edition_directory(root, slug), cover["path"]))
        cover["sha256"] = file_hash(source)
    save_edition(root, manifest)
    return manifest


def reject_candidate(root: Path, slug: str, asset_id: str, evidence: str) -> dict[str, Any]:
    manifest = load_edition(root, slug)
    asset = _asset(manifest, asset_id)
    candidate = asset.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("status") != "ready":
        raise ValueError("There is no completed candidate to reject")
    path = Path(candidate["path"])
    if not path.is_file() or file_hash(path) != candidate.get("sha256"):
        raise ValueError("Candidate bytes changed before inspection")
    candidate.update(status="rejected", evidence=_nonempty(evidence, "Visible rejection finding"))
    save_edition(root, manifest)
    return manifest


def resolve_generation(root: Path, slug: str, asset_id: str, outcome: str, evidence: str) -> dict[str, Any]:
    """Record observed process completion/failure after authoritative terminal checks.

    Never infer that a process died from an old timestamp or a resumed task.
    Recovery consumes no additional attempt and never claims image approval.
    """
    manifest = load_edition(root, slug)
    asset = _asset(manifest, asset_id)
    candidate = asset.get("candidate")
    if not isinstance(candidate, dict) or candidate.get("status") not in {"generating", "failed"}:
        raise ValueError("There is no interrupted or failed generation to resolve")
    evidence = _nonempty(evidence, "Authoritative process/terminal completion evidence")
    if outcome not in {"failed", "ready"}:
        raise ValueError("Recovery outcome must be failed or ready")
    if outcome == "ready":
        verify_source(root, manifest)
        path = Path(candidate["path"])
        _image(path, asset["size"])
        if candidate["inputsSha256"] != _asset_inputs(root, manifest, asset)[0]:
            raise ValueError("Recovered output has stale generation inputs")
        candidate["sha256"] = file_hash(path)
    candidate.update(status=outcome, recoveryEvidence=evidence)
    save_edition(root, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("new", help="Scaffold an edition from an exact repository story title or slug")
    new.add_argument("source")
    new.add_argument("--slug")
    new.add_argument("--request-file", type=Path, required=True)
    new.add_argument("--mode", type=str.title, choices=MODES, default="Classic")
    new.add_argument("--reference", type=Path, action="append", default=[])
    inspect = commands.add_parser("inspect-original")
    inspect.add_argument("slug"); inspect.add_argument("id"); inspect.add_argument("--evidence-file", type=Path, required=True)
    configure = commands.add_parser("set-asset")
    configure.add_argument("slug"); configure.add_argument("id")
    configure.add_argument("--kind", choices=sorted(KINDS), required=True)
    configure.add_argument("--prompt-file", type=Path, required=True)
    configure.add_argument("--size", choices=sorted(SIZES), default="1536x1024")
    configure.add_argument("--reference", action="append")
    configure.add_argument("--after"); configure.add_argument("--layout", choices=("inline", "full-page", "spot"), default="inline")
    configure.add_argument("--alt", default=""); configure.add_argument("--caption", default="")
    approval = commands.add_parser("approve", help="Record an actual explicit user decision, never an inferred approval")
    approval.add_argument("slug"); approval.add_argument("stage", choices=("plan", "visuals", "final")); approval.add_argument("--decision-file", type=Path, required=True)
    preview = commands.add_parser("layout-preview")
    preview.add_argument("slug"); preview.add_argument("path", type=Path); preview.add_argument("--evidence-file", type=Path, required=True)
    generate = commands.add_parser("generate")
    generate.add_argument("slug"); generate.add_argument("id"); generate.add_argument("--out", type=Path, required=True)
    generate.add_argument("--imagegen-cli", type=Path); generate.add_argument("--python"); generate.add_argument("--correction-file", type=Path); generate.add_argument("--dry-run", action="store_true")
    accept = commands.add_parser("accept")
    accept.add_argument("slug"); accept.add_argument("id"); accept.add_argument("--evidence-file", type=Path, required=True)
    reject = commands.add_parser("reject")
    reject.add_argument("slug"); reject.add_argument("id"); reject.add_argument("--evidence-file", type=Path, required=True)
    extra = commands.add_parser("extra-attempt")
    extra.add_argument("slug"); extra.add_argument("id"); extra.add_argument("--decision-file", type=Path, required=True)
    recovery = commands.add_parser("resolve-generation")
    recovery.add_argument("slug"); recovery.add_argument("id")
    recovery.add_argument("--outcome", choices=("failed", "ready"), required=True)
    recovery.add_argument("--evidence-file", type=Path, required=True)
    review = commands.add_parser("record-review")
    review.add_argument("slug"); review.add_argument("--reviewer", required=True); review.add_argument("--evidence-file", type=Path, required=True)
    repin = commands.add_parser("repin-source")
    repin.add_argument("slug"); repin.add_argument("--decision-file", type=Path, required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("slug"); validate.add_argument("--phase", choices=("draft", "plan", "references", "visuals", "render", "review", "final", "capture"), default="draft")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == "new":
            result = create_edition(root, args.source, _text(args.request_file), slug=args.slug, mode=args.mode, references=args.reference)
        elif args.command == "inspect-original":
            result = inspect_original(root, args.slug, args.id, _text(args.evidence_file))
        elif args.command == "set-asset":
            result = configure_asset(root, args.slug, args.id, kind=args.kind, prompt=_text(args.prompt_file), size=args.size, references=args.reference, after=args.after, layout=args.layout, alt=args.alt, caption=args.caption)
        elif args.command == "approve":
            result = approve(root, args.slug, args.stage, _text(args.decision_file))
        elif args.command == "layout-preview":
            result = record_layout_preview(root, args.slug, args.path, _text(args.evidence_file))
        elif args.command == "generate":
            result = generate_asset(root, args.slug, args.id, args.out, imagegen_cli=args.imagegen_cli, python=args.python, correction=_text(args.correction_file) if args.correction_file else "", dry_run=args.dry_run)
        elif args.command == "accept":
            result = accept_candidate(root, args.slug, args.id, _text(args.evidence_file))
        elif args.command == "reject":
            result = reject_candidate(root, args.slug, args.id, _text(args.evidence_file))
        elif args.command == "extra-attempt":
            result = allow_extra_attempt(root, args.slug, args.id, _text(args.decision_file))
        elif args.command == "resolve-generation":
            result = resolve_generation(root, args.slug, args.id, args.outcome, _text(args.evidence_file))
        elif args.command == "record-review":
            result = record_review(root, args.slug, args.reviewer, _text(args.evidence_file))
        elif args.command == "repin-source":
            result = repin_source(root, args.slug, _text(args.decision_file))
        else:
            result = validate_edition(root, args.slug, args.phase)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")
    if args.command == "generate" and args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"OK: {args.command} — {result['slug']}")


if __name__ == "__main__":
    main()
