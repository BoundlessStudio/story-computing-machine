from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import markdown

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class StoryMetadata:
    directory: Path
    slug: str
    title: str
    created: str
    stage: str
    status: str
    canon: bool
    user_disposition: str
    publish: bool
    promotion_date: str | None
    provenance: str


@dataclass(frozen=True)
class PublishedStory:
    metadata: StoryMetadata
    body: str
    word_count: int


@dataclass(frozen=True)
class Catalog:
    stories: tuple[PublishedStory, ...]


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def require_exact_fields(value: dict[str, Any], fields: list[str], path: Path) -> None:
    missing = sorted(set(fields) - set(value))
    extra = sorted(set(value) - set(fields))
    if missing or extra:
        raise ValueError(f"{path} fields differ; missing={missing}, extra={extra}")


def load_pipeline_contract(path: Path | None = None) -> dict[str, Any]:
    contract_path = path or REPOSITORY_ROOT / "schemas" / "pipeline-contract.json"
    value = read_json_object(contract_path)
    if value.get("schemaVersion") != 2 or value.get("trustModel") != "git-pr-human-review":
        raise ValueError(f"Unsupported pipeline contract in {contract_path}")
    return value


def parse_front_matter(content: str, path: Path) -> tuple[dict[str, str], str]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError(f"{path} lacks required frontmatter")
    end = normalized.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path} has unterminated frontmatter")
    metadata: dict[str, str] = {}
    for line in normalized[4:end].splitlines():
        if ":" not in line:
            raise ValueError(f"Malformed frontmatter line in {path}: {line}")
        key, raw = line.split(":", 1)
        value = raw.strip().strip('"').strip("'")
        metadata[key.strip()] = value
    return metadata, normalized[end + 5 :]


def validate_repository_integrity(repository_root: Path) -> None:
    script = repository_root / ".agents" / "skills" / "story-integrity" / "scripts" / "Test-StoryIntegrity.ps1"
    completed = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(script), "-OutputFormat", "Text", "-ProjectRoot", str(repository_root)],
        cwd=repository_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        detail = (completed.stdout + completed.stderr).strip()
        raise ValueError(f"Repository integrity failed: {detail}")


def _story_metadata(directory: Path, contract: dict[str, Any]) -> StoryMetadata:
    path = directory / "story.json"
    value = read_json_object(path)
    require_exact_fields(value, contract["story"]["fields"], path)
    if value["schemaVersion"] != 2 or value["slug"] != directory.name or not SLUG.fullmatch(value["slug"]):
        raise ValueError(f"Invalid story identity in {path}")
    if not isinstance(value["title"], str) or not value["title"].strip() or not DATE.fullmatch(value["created"]):
        raise ValueError(f"Invalid title or creation date in {path}")
    state = contract["lifecycle"]["states"].get(value["status"])
    if state is None or value["stage"] not in state["stages"]:
        raise ValueError(f"Invalid lifecycle in {path}")
    if value["canon"] is not state["canon"] or value["userDisposition"] not in state["userDispositions"] or value["publish"] not in state["publish"]:
        raise ValueError(f"Contradictory lifecycle in {path}")
    if state["promotionDate"] == "required" and not isinstance(value["promotionDate"], str):
        raise ValueError(f"Final story lacks promotion date in {path}")
    if state["promotionDate"] == "null" and value["promotionDate"] is not None:
        raise ValueError(f"Non-final story has promotion date in {path}")
    if value["provenance"] not in contract["story"]["provenanceValues"]:
        raise ValueError(f"Invalid provenance in {path}")
    return StoryMetadata(directory, value["slug"], value["title"], value["created"], value["stage"], value["status"], value["canon"], value["userDisposition"], value["publish"], value["promotionDate"], value["provenance"])


def _validate_release(metadata: StoryMetadata, contract: dict[str, Any]) -> None:
    path = metadata.directory / "release.json"
    value = read_json_object(path)
    spec = contract["release"]
    require_exact_fields(value, spec["fields"], path)
    if value["schemaVersion"] != 3 or value["storySlug"] != metadata.slug or value["certified"] is not True:
        raise ValueError(f"Invalid release header in {path}")
    if value["certificationBasis"] not in spec["certificationBases"]:
        raise ValueError(f"Invalid release basis in {path}")
    require_exact_fields(value["artifacts"], spec["artifactContainerFields"], path)
    for key, expected in (("story", "05-story.md"), ("canonDelta", "06-canon-delta.md")):
        require_exact_fields(value["artifacts"][key], spec["artifactFields"], path)
        if value["artifacts"][key]["path"] != expected:
            raise ValueError(f"Invalid release artifact path in {path}")
    require_exact_fields(value["review"], spec["reviewFields"], path)
    review = value["review"]
    if review["artifact"] != "05-story.md" or review["verdict"] != "PASS" or review["unresolvedCritical"] != 0 or review["unresolvedMajor"] != 0:
        raise ValueError(f"Release review gate failed in {path}")
    require_exact_fields(value["nameCheck"], spec["nameCheckFields"], path)
    if value["nameCheck"]["story"] != metadata.slug or value["nameCheck"]["phase"] != "Final" or value["nameCheck"]["passed"] is not True:
        raise ValueError(f"Release name gate failed in {path}")
    require_exact_fields(value["dependencies"], spec["dependencyFields"], path)


def _legacy_slugs(root: Path) -> set[str]:
    path = root / "stories" / "legacy-acceptance.json"
    value = read_json_object(path)
    require_exact_fields(value, ["schemaVersion", "acceptedBy", "acceptedAt", "reviewBasis", "stories"], path)
    if value["schemaVersion"] != 1 or not value["acceptedBy"] or not value["reviewBasis"]:
        raise ValueError(f"Invalid legacy acceptance header in {path}")
    result: set[str] = set()
    for item in value["stories"]:
        require_exact_fields(item, ["slug", "promotionDate"], path)
        if item["slug"] in result:
            raise ValueError(f"Duplicate legacy acceptance story: {item['slug']}")
        result.add(item["slug"])
    return result


def load_catalog(repository_root: Path = REPOSITORY_ROOT) -> Catalog:
    contract = load_pipeline_contract(repository_root / "schemas" / "pipeline-contract.json")
    legacy = _legacy_slugs(repository_root)
    published: list[PublishedStory] = []
    story_root = repository_root / "stories"
    for directory in sorted((item for item in story_root.iterdir() if item.is_dir() and not item.name.startswith("_")), key=lambda item: item.name):
        metadata = _story_metadata(directory, contract)
        if not metadata.publish:
            continue
        if metadata.status not in contract["lifecycle"]["publishableStatuses"]:
            raise ValueError(f"Published story is not terminal: {metadata.slug}")
        _validate_release(metadata, contract)
        if metadata.provenance == "legacy-user-attested" and metadata.slug not in legacy:
            raise ValueError(f"Legacy story is not attested: {metadata.slug}")
        front, body = parse_front_matter((directory / "05-story.md").read_text(encoding="utf-8"), directory / "05-story.md")
        if set(front) != {"title", "slug", "created"}:
            raise ValueError(f"Final frontmatter fields differ for {metadata.slug}")
        if front != {"title": metadata.title, "slug": metadata.slug, "created": metadata.created}:
            raise ValueError(f"Final frontmatter identity differs for {metadata.slug}")
        word_count = len(re.findall(r"\b[\w’'-]+\b", body))
        published.append(PublishedStory(metadata, body.strip(), word_count))
    published.sort(key=lambda story: story.metadata.created, reverse=True)
    return Catalog(tuple(published))


def _page(title: str, body: str) -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>body{{max-width:48rem;margin:0 auto;padding:2rem;font:18px/1.65 Georgia,serif;color:#241f1a;background:#fcf8f1}}a{{color:#70451f}}article{{margin:2rem 0}}.meta{{color:#6d645a;font:14px system-ui}}li{{margin:.7rem 0}}</style></head><body>{body}</body></html>'''


def render_index(catalog: Catalog) -> str:
    items = []
    for story in catalog.stories:
        status = "Canon" if story.metadata.canon else "Candidate"
        items.append(f'<li><a href="stories/{html.escape(story.metadata.slug)}.html">{html.escape(story.metadata.title)}</a><div class="meta">{status} · {story.word_count:,} words</div></li>')
    return _page("Stories", f"<h1>Stories</h1><p>{len(items)} published stories from the current validated checkout.</p><ol>{''.join(items)}</ol>")


def render_story(story: PublishedStory) -> str:
    prose = markdown.markdown(story.body, extensions=["extra", "smarty"])
    status = "Canon" if story.metadata.canon else "Candidate"
    body = f'<p><a href="../index.html">← All stories</a></p><article><h1>{html.escape(story.metadata.title)}</h1><p class="meta">{status} · {story.word_count:,} words</p>{prose}</article>'
    return _page(story.metadata.title, body)


def prepare_output(output: Path, repository_root: Path) -> Path:
    resolved = output.resolve()
    root = repository_root.resolve()
    protected = [root / name for name in (".git", ".agents", ".codex", "pages", "schemas", "sources", "stories", "tests", "universe")]
    if resolved == root or resolved in root.parents or any(resolved == item or item in resolved.parents for item in protected):
        raise ValueError("Output overlaps protected repository content")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    return resolved


def build(output: Path, repository_root: Path = REPOSITORY_ROOT, require_integrity_validator: bool = True) -> Catalog:
    if require_integrity_validator:
        validate_repository_integrity(repository_root)
    catalog = load_catalog(repository_root)
    destination = prepare_output(output, repository_root)
    (destination / "stories").mkdir()
    (destination / "index.html").write_text(render_index(catalog), encoding="utf-8")
    for story in catalog.stories:
        (destination / "stories" / f"{story.metadata.slug}.html").write_text(render_story(story), encoding="utf-8")
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPOSITORY_ROOT / "_site")
    args = parser.parse_args()
    catalog = build(args.output)
    print(f"Built {len(catalog.stories)} published stories in {args.output}")


if __name__ == "__main__":
    main()
