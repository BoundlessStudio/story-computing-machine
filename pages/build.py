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
class ReaderStory:
    metadata: StoryMetadata
    prompt: str
    body: str
    word_count: int


@dataclass(frozen=True)
class Catalog:
    stories: tuple[ReaderStory, ...]


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


def parse_writing_prompt(content: str, path: Path) -> str:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(
        r"^## Verbatim writing prompt\s*\n(?P<prompt>.*?)(?=^## |\Z)",
        normalized,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError(f"{path} lacks a Verbatim writing prompt section")

    lines = []
    for line in match.group("prompt").strip().splitlines():
        cleaned = re.sub(r"^\s*>\s?", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    prompt = re.sub(r"\*\*", "", " ".join(lines)).strip()
    if prompt.startswith("[WP]"):
        prompt = prompt.removeprefix("[WP]").strip()
    if not prompt:
        raise ValueError(f"{path} has an empty Verbatim writing prompt section")
    return prompt


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
    stories: list[ReaderStory] = []
    story_root = repository_root / "stories"
    for directory in sorted((item for item in story_root.iterdir() if item.is_dir() and not item.name.startswith("_")), key=lambda item: item.name):
        metadata = _story_metadata(directory, contract)
        if metadata.provenance == "legacy-user-attested" and metadata.slug not in legacy:
            raise ValueError(f"Legacy story is not attested: {metadata.slug}")
        front, body = parse_front_matter((directory / "05-story.md").read_text(encoding="utf-8"), directory / "05-story.md")
        if set(front) != {"title", "slug", "created"}:
            raise ValueError(f"Final frontmatter fields differ for {metadata.slug}")
        if front != {"title": metadata.title, "slug": metadata.slug, "created": metadata.created}:
            raise ValueError(f"Final frontmatter identity differs for {metadata.slug}")
        prompt_path = directory / "00-prompt.md"
        prompt = parse_writing_prompt(prompt_path.read_text(encoding="utf-8"), prompt_path)
        word_count = len(re.findall(r"\b[\w’'-]+\b", body))
        stories.append(ReaderStory(metadata, prompt, body.strip(), word_count))
    stories.sort(key=lambda story: story.metadata.created, reverse=True)
    return Catalog(tuple(stories))


REPOSITORY_URL = "https://github.com/BoundlessStudio/story-computing-machine"
GITHUB_ICON = '''<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 2.29 6.64 5.47 7.71.4.08.55-.17.55-.39 0-.19-.01-.82-.01-1.49-2.01.44-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.59 1.23.83.72 1.23 1.87.88 2.33.67.07-.53.28-.88.51-1.08-1.78-.21-3.64-.9-3.64-4.01 0-.89.31-1.62.82-2.19-.08-.21-.36-1.04.08-2.16 0 0 .67-.22 2.2.84A7.45 7.45 0 0 1 8 3.92c.68 0 1.36.09 2 .28 1.53-1.06 2.2-.84 2.2-.84.44 1.12.16 1.95.08 2.16.51.57.82 1.3.82 2.19 0 3.12-1.87 3.8-3.65 4.01.29.25.54.73.54 1.49 0 1.07-.01 1.93-.01 2.2 0 .22.15.47.55.39A8.03 8.03 0 0 0 16 8.13C16 3.64 12.42 0 8 0Z"/></svg>'''


def _page(title: str, body: str, home_href: str) -> str:
    repository_link = f'<a class="repository-link" href="{REPOSITORY_URL}" aria-label="View BoundlessStudio/story-computing-machine on GitHub" title="View repository on GitHub">{GITHUB_ICON}</a>'
    header = f'<header class="site-header"><a class="site-name" href="{home_href}">Story Computing Machine</a>{repository_link}</header>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>
:root{{color-scheme:light dark;--background:#fcf8f1;--surface:#fffdf8;--text:#241f1a;--muted:#6d645a;--link:#70451f;--border:#d8cec0}}
@media (prefers-color-scheme:dark){{:root{{--background:#181512;--surface:#211d19;--text:#eee8df;--muted:#b8aea2;--link:#e4b780;--border:#4a4036}}}}
body{{max-width:48rem;margin:0 auto;padding:2rem;font:18px/1.65 Georgia,serif;color:var(--text);background:var(--background)}}
a{{color:var(--link)}}
.site-header{{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding-bottom:1rem;border-bottom:1px solid var(--border)}}
.site-name{{font:700 13px system-ui;text-decoration:none;letter-spacing:.04em;text-transform:uppercase}}
.repository-link{{display:inline-flex;align-items:center;justify-content:center;width:2.25rem;height:2.25rem;border-radius:50%;color:var(--text)}}
.repository-link:hover{{background:var(--surface);color:var(--link)}}
.repository-link svg{{width:1.35rem;height:1.35rem;fill:currentColor}}
article{{margin:2rem 0}}
.meta,.prompt-label{{color:var(--muted);font:14px system-ui}}
.prompt{{margin:1rem 0;padding:1rem 1.2rem;border:1px solid var(--border);border-radius:.35rem;background:var(--surface)}}
.prompt-label{{display:block;margin-bottom:.25rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}}
.prompt blockquote{{margin:0}}
li{{margin:1rem 0}}
</style></head><body>{header}<main>{body}</main></body></html>'''


def _prompt(value: str) -> str:
    return f'<div class="prompt"><span class="prompt-label">Prompt</span><blockquote>{html.escape(value)}</blockquote></div>'


def _without_leading_title(body: str) -> str:
    heading = re.match(r"^#\s+[^\n]+?\s*(?:\n+|\Z)", body)
    if heading is None:
        return body
    return body[heading.end() :].lstrip()


def _story_label(metadata: StoryMetadata) -> str:
    status = metadata.status.replace("-", " ").title()
    return f"{status} · Canon" if metadata.canon else status


def render_index(catalog: Catalog) -> str:
    items = []
    for story in catalog.stories:
        status = _story_label(story.metadata)
        items.append(f'<li><a href="stories/{html.escape(story.metadata.slug)}.html">{html.escape(story.metadata.title)}</a>{_prompt(story.prompt)}<div class="meta">{status} · {story.word_count:,} words</div></li>')
    return _page("Stories", f"<h1>Stories</h1><p>{len(items)} stories from the current validated checkout.</p><ol>{''.join(items)}</ol>", "index.html")


def render_story(story: ReaderStory) -> str:
    prose = markdown.markdown(_without_leading_title(story.body), extensions=["extra", "smarty"])
    status = _story_label(story.metadata)
    body = f'<p><a href="../index.html">← All stories</a></p><article><h1>{html.escape(story.metadata.title)}</h1><p class="meta">{status} · {story.word_count:,} words</p>{_prompt(story.prompt)}{prose}</article>'
    return _page(story.metadata.title, body, "../index.html")


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
    print(f"Built {len(catalog.stories)} stories in {args.output}")


if __name__ == "__main__":
    main()
