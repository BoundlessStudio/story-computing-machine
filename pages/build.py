from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import markdown

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(__file__).with_name("catalog.json")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Story:
    slug: str
    title: str
    created: str
    canon: bool
    status: str
    prompt: str
    body: str

    @property
    def word_count(self) -> int:
        return len(re.findall(r"\b[\w’'-]+\b", self.body))


@dataclass(frozen=True)
class Catalog:
    stories: tuple[Story, ...]


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def require_exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - set(value))
    extra = sorted(set(value) - fields)
    if missing or extra:
        raise ValueError(f"{label} fields differ; missing={missing}, extra={extra}")


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
        key = key.strip()
        if key in metadata:
            raise ValueError(f"Repeated frontmatter field in {path}: {key}")
        metadata[key] = raw.strip().strip('"').strip("'")
    return metadata, normalized[end + 5 :]


def parse_writing_prompt(content: str, path: Path) -> str:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    match = re.search(
        r"^## (?:Verbatim writing prompt|Prompt)\s*\n(?P<prompt>.*?)(?=^## |\Z)",
        normalized,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise ValueError(f"{path} lacks a Prompt section")

    lines = []
    for line in match.group("prompt").strip().splitlines():
        cleaned = re.sub(r"^\s*>\s?", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    prompt = re.sub(r"\*\*", "", " ".join(lines)).strip()
    if prompt.startswith("[WP]"):
        prompt = prompt.removeprefix("[WP]").strip()
    if not prompt:
        raise ValueError(f"{path} has an empty Prompt section")
    return prompt


def _bool(value: str, path: Path, field: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"{path} field {field} must be true or false")


def _load_current_story(directory: Path) -> Story:
    story_path = directory / "story.md"
    front, body = parse_front_matter(story_path.read_text(encoding="utf-8"), story_path)
    require_exact_fields(front, {"title", "slug", "created", "canon"}, str(story_path))
    if front["slug"] != directory.name or not SLUG.fullmatch(front["slug"]):
        raise ValueError(f"Invalid slug in {story_path}")
    if not front["title"] or not DATE.fullmatch(front["created"]):
        raise ValueError(f"Invalid title or date in {story_path}")

    review_path = directory / "review.md"
    review = review_path.read_text(encoding="utf-8")
    required_review_lines = (
        r"(?m)^Verdict:\s*PASS\s*$",
        r"(?m)^-\s+Prompt:\s*PASS\s*$",
        r"(?m)^-\s+Universe:\s*PASS\s*$",
        r"(?m)^-\s+Internal:\s*PASS\s*$",
        r"(?m)^-\s+Blocking:\s*none\s*$",
    )
    if any(re.search(pattern, review) is None for pattern in required_review_lines):
        raise ValueError(f"{review_path} is not a passing review")

    prompt_path = directory / "prompt.md"
    return Story(
        slug=front["slug"],
        title=front["title"],
        created=front["created"],
        canon=_bool(front["canon"], story_path, "canon"),
        status="canon" if front["canon"] == "true" else "reviewed",
        prompt=parse_writing_prompt(prompt_path.read_text(encoding="utf-8"), prompt_path),
        body=body.strip(),
    )


def _load_legacy_story(directory: Path) -> Story:
    record_path = directory / "story.json"
    record = read_json_object(record_path)
    for field in ("slug", "title", "created", "status", "canon"):
        if field not in record:
            raise ValueError(f"{record_path} lacks {field}")
    if record["slug"] != directory.name or not SLUG.fullmatch(record["slug"]):
        raise ValueError(f"Invalid legacy slug in {record_path}")
    if not isinstance(record["title"], str) or not DATE.fullmatch(record["created"]):
        raise ValueError(f"Invalid legacy title or date in {record_path}")
    if not isinstance(record["canon"], bool) or not isinstance(record["status"], str):
        raise ValueError(f"Invalid legacy status in {record_path}")

    story_path = directory / "05-story.md"
    front, body = parse_front_matter(story_path.read_text(encoding="utf-8"), story_path)
    expected = {
        "title": record["title"],
        "slug": record["slug"],
        "created": record["created"],
    }
    if front != expected:
        raise ValueError(f"Legacy story identity differs in {story_path}")

    prompt_path = directory / "00-prompt.md"
    return Story(
        slug=record["slug"],
        title=record["title"],
        created=record["created"],
        canon=record["canon"],
        status=record["status"],
        prompt=parse_writing_prompt(prompt_path.read_text(encoding="utf-8"), prompt_path),
        body=body.strip(),
    )


def load_story_source(slug: str, repository_root: Path = REPOSITORY_ROOT) -> Story:
    if not SLUG.fullmatch(slug):
        raise ValueError(f"Invalid story slug: {slug}")
    directory = repository_root / "stories" / slug
    if (directory / "story.md").is_file():
        return _load_current_story(directory)
    if (directory / "05-story.md").is_file():
        return _load_legacy_story(directory)
    raise ValueError(f"No readable story source for {slug}")


def _ordered(stories: Iterable[Story]) -> tuple[Story, ...]:
    return tuple(sorted(stories, key=lambda item: (item.created, item.slug), reverse=True))


def load_catalog(snapshot_path: Path = SNAPSHOT_PATH) -> Catalog:
    value = read_json_object(snapshot_path)
    require_exact_fields(value, {"schemaVersion", "stories"}, str(snapshot_path))
    if value["schemaVersion"] != 1 or not isinstance(value["stories"], list):
        raise ValueError(f"Unsupported snapshot in {snapshot_path}")

    stories: list[Story] = []
    seen: set[str] = set()
    fields = {"slug", "title", "created", "canon", "status", "prompt", "body"}
    for index, item in enumerate(value["stories"]):
        if not isinstance(item, dict):
            raise ValueError(f"Snapshot story {index} is not an object")
        require_exact_fields(item, fields, f"snapshot story {index}")
        if (
            not isinstance(item["slug"], str)
            or not SLUG.fullmatch(item["slug"])
            or item["slug"] in seen
            or not isinstance(item["title"], str)
            or not item["title"].strip()
            or not isinstance(item["created"], str)
            or not DATE.fullmatch(item["created"])
            or not isinstance(item["canon"], bool)
            or not isinstance(item["status"], str)
            or not item["status"].strip()
            or not isinstance(item["prompt"], str)
            or not item["prompt"].strip()
            or not isinstance(item["body"], str)
            or not item["body"].strip()
        ):
            raise ValueError(f"Invalid snapshot story {index}")
        seen.add(item["slug"])
        stories.append(Story(**item))

    ordered = _ordered(stories)
    if tuple(stories) != ordered:
        raise ValueError(f"{snapshot_path} stories are not in newest-first order")
    return Catalog(ordered)


def save_catalog(stories: Iterable[Story], snapshot_path: Path = SNAPSHOT_PATH) -> Catalog:
    catalog = Catalog(_ordered(stories))
    value = {
        "schemaVersion": 1,
        "stories": [asdict(story) for story in catalog.stories],
    }
    snapshot_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return catalog


def capture_story(
    slug: str,
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> Catalog:
    story = load_story_source(slug, repository_root)
    existing = list(load_catalog(snapshot_path).stories) if snapshot_path.exists() else []
    by_slug = {item.slug: item for item in existing}
    by_slug[story.slug] = story
    return save_catalog(by_slug.values(), snapshot_path)


def capture_all(
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> Catalog:
    story_root = repository_root / "stories"
    slugs = [
        item.name
        for item in story_root.iterdir()
        if item.is_dir()
        and not item.name.startswith("_")
        and ((item / "story.md").is_file() or (item / "05-story.md").is_file())
    ]
    return save_catalog((load_story_source(slug, repository_root) for slug in slugs), snapshot_path)


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
    return body if heading is None else body[heading.end() :].lstrip()


def _story_label(story: Story) -> str:
    return "Canon" if story.canon else story.status.replace("-", " ").title()


def render_index(catalog: Catalog) -> str:
    items = []
    for story in catalog.stories:
        created = html.escape(story.created)
        items.append(
            f'<li><a href="stories/{html.escape(story.slug)}.html">{html.escape(story.title)}</a>'
            f'{_prompt(story.prompt)}<div class="meta"><time datetime="{created}">{created}</time> · '
            f'{_story_label(story)} · {story.word_count:,} words</div></li>'
        )
    body = f"<h1>Stories</h1><p>{len(items)} stored publications.</p><ol>{''.join(items)}</ol>"
    return _page("Stories", body, "index.html")


def render_story(story: Story) -> str:
    prose = markdown.markdown(_without_leading_title(story.body), extensions=["extra", "smarty"])
    body = (
        f'<p><a href="../index.html">← All stories</a></p><article>'
        f'<h1>{html.escape(story.title)}</h1>'
        f'<p class="meta">{_story_label(story)} · {story.word_count:,} words</p>'
        f'{_prompt(story.prompt)}{prose}</article>'
    )
    return _page(story.title, body, "../index.html")


def prepare_output(output: Path, repository_root: Path = REPOSITORY_ROOT) -> Path:
    resolved = output.resolve()
    root = repository_root.resolve()
    protected = [
        root / name
        for name in (".git", ".agents", ".codex", "pages", "sources", "stories", "universe")
    ]
    if (
        resolved == root
        or resolved in root.parents
        or any(resolved == item or item in resolved.parents for item in protected)
    ):
        raise ValueError("Output overlaps protected repository content")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)
    return resolved


def build(output: Path, snapshot_path: Path = SNAPSHOT_PATH) -> Catalog:
    catalog = load_catalog(snapshot_path)
    destination = prepare_output(output)
    (destination / "stories").mkdir()
    (destination / "index.html").write_text(render_index(catalog), encoding="utf-8")
    for story in catalog.stories:
        (destination / "stories" / f"{story.slug}.html").write_text(
            render_story(story),
            encoding="utf-8",
        )
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    build_parser = commands.add_parser("build", help="Build Pages from the stored snapshot.")
    build_parser.add_argument("--output", type=Path, default=REPOSITORY_ROOT / "_site")

    capture_parser = commands.add_parser("capture", help="Store one reviewed story for Pages.")
    capture_parser.add_argument("slug")

    commands.add_parser("capture-all", help="Regenerate the stored snapshot from every story source.")
    commands.add_parser("check", help="Validate the stored publication snapshot.")

    args = parser.parse_args()
    if args.command == "build":
        catalog = build(args.output)
        print(f"Built {len(catalog.stories)} stored stories in {args.output}")
    elif args.command == "capture":
        catalog = capture_story(args.slug)
        print(f"Stored {args.slug}; publication catalog now has {len(catalog.stories)} stories")
    elif args.command == "capture-all":
        catalog = capture_all()
        print(f"Stored {len(catalog.stories)} stories in {SNAPSHOT_PATH}")
    else:
        catalog = load_catalog()
        print(f"PASS: {len(catalog.stories)} stored stories")


if __name__ == "__main__":
    main()
