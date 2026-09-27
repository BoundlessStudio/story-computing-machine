"""List accepted, tracked art and give every selected file a stable public URL."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

from .assets import CONTENT_TYPES, INDEX_KEY, base_url, object_key, public_url, sha256, source_file


ROOT = Path(__file__).resolve().parents[1]
IMAGE_TYPES = {suffix for suffix in CONTENT_TYPES if suffix != ".pdf"}


def tracked_paths(root: Path) -> set[str]:
    output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    return {path for path in output.decode("utf-8").split("\0") if path}


def selection_notes(root: Path, tracked: set[str]) -> tuple[set[str], dict[str, str]]:
    notes = json.loads((root / "art" / "selection-notes.json").read_text(encoding="utf-8"))
    if not isinstance(notes, dict) or set(notes) != {"excluded", "selectedCorrections"}:
        raise ValueError("Invalid art selection notes")
    excluded = set()
    corrections = {}
    selected_targets = set()
    for item in notes["excluded"]:
        path = item["file"]
        if path in excluded or path not in tracked:
            raise ValueError(f"Duplicate or missing excluded artwork: {path}")
        excluded.add(path)
    for item in notes["selectedCorrections"]:
        original, selected = item["original"], item["selected"]
        original_parts, selected_parts = PurePosixPath(original).parts, PurePosixPath(selected).parts
        if (original in corrections or selected in selected_targets or original not in tracked
                or selected not in tracked or len(original_parts) != 5 or len(selected_parts) != 6
                or original_parts[:4] != selected_parts[:4]
                or selected_parts[4] != "selected" or original_parts[4] != selected_parts[5]
                or original_parts[3] not in {"landscapes", "interiors"}):
            raise ValueError(f"Invalid selected correction: {original} -> {selected}")
        corrections[original] = selected
        selected_targets.add(selected)
    return excluded, corrections


def selected_paths(tracked: set[str], excluded: set[str], corrections: dict[str, str]) -> list[str]:
    selected_targets = set(corrections.values())
    chosen = []
    for path in sorted(tracked):
        parts = PurePosixPath(path).parts
        suffix = PurePosixPath(path).suffix.lower()
        if len(parts) == 3 and parts[0] == "stories" and parts[2] == "title-image.jpg":
            chosen.append(path)
        elif len(parts) >= 5 and parts[0] == "stories" and parts[2] == "art":
            collection = parts[3]
            if collection == "characters" and len(parts) == 5 and suffix in IMAGE_TYPES:
                if path not in excluded:
                    chosen.append(path)
            elif collection in {"landscapes", "interiors"} and suffix in IMAGE_TYPES:
                if len(parts) == 5 and path not in excluded and path not in corrections:
                    chosen.append(path)
                elif len(parts) == 6 and path in selected_targets:
                    chosen.append(path)
        elif len(parts) == 3 and parts[0] == "illustrated" and parts[2] in {"cover.jpg", "edition.pdf"}:
            chosen.append(path)
        elif len(parts) == 4 and parts[0] == "illustrated" and parts[2] == "illustrations" and suffix in IMAGE_TYPES:
            chosen.append(path)
        elif len(parts) == 3 and parts[0] == "graphic-novels" and parts[2] in {"cover.png", "edition.pdf"}:
            chosen.append(path)
        elif len(parts) == 4 and parts[0] == "graphic-novels" and parts[2] == "pages" and suffix in IMAGE_TYPES:
            chosen.append(path)
    if not chosen or not selected_targets.issubset(chosen):
        raise ValueError("Selected artwork is missing from the public media set")
    return chosen


def build(root: Path, origin: str, tracked: set[str] | None = None, commit: str | None = None) -> dict:
    root = root.resolve()
    origin = base_url(origin)
    tracked = tracked_paths(root) if tracked is None else tracked
    excluded, corrections = selection_notes(root, tracked)
    paths = selected_paths(tracked, excluded, corrections)
    if commit is None:
        commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    assets = []
    for relative in paths:
        file = source_file(root, relative)
        digest = sha256(file)
        key = object_key(relative, digest)
        assets.append({
            "path": relative, "sha256": digest, "size": file.stat().st_size,
            "key": key, "contentType": CONTENT_TYPES[file.suffix.lower()],
            "url": public_url(origin, key),
        })
    return {
        "schemaVersion": 1, "sourceCommit": commit, "baseUrl": origin,
        "indexUrl": public_url(origin, INDEX_KEY), "assets": assets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path("_media/manifest.json"))
    parser.add_argument("--base-url", default=os.environ.get("ASSET_BASE_URL", ""))
    args = parser.parse_args()
    result = build(args.root, args.base_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(item["size"] for item in result["assets"])
    print(f"Selected {len(result['assets'])} public media files ({total / 2**30:.2f} GiB)")
    print(f"Downstream index: {result['indexUrl']}")


if __name__ == "__main__":
    main()
