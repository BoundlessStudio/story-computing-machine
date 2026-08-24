from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import markdown

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(__file__).with_name("catalog.json")
STYLESHEET_PATH = Path(__file__).with_name("styles.css")
TITLE_IMAGE_NAME = "title-image.jpg"
TITLE_IMAGE_WIDTH = 864
TITLE_IMAGE_HEIGHT = 1536
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RATINGS = frozenset({"PG", "YA", "R+"})


@dataclass(frozen=True)
class Story:
    slug: str
    title: str
    created: str
    created_at: str
    edited: str
    rating: str
    canon: bool
    status: str
    prompt: str
    cover: str
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
    prompt = re.sub(r"^(?:#{1,6}\s*)?\[?WP\]\s*", "", prompt, count=1).strip()
    if not prompt:
        raise ValueError(f"{path} has an empty Prompt section")
    return prompt


def _content_rating(content: str) -> str:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    lowered = normalized.casefold()
    if (
        re.search(r"\bhard[- ]?r\b|\br[- ]rated\b", lowered)
        or "explicit consensual sexual content may remain" in lowered
        or "graphic mob violence" in lowered
    ):
        return "R+"

    audience = re.search(
        r"(?mi)^-\s*(?:Audience/content rating|Tone and audience):\s*(?P<value>.+(?:\n(?: {2,}|\t).+)*)",
        normalized,
    )
    if audience is None:
        return "PG"

    value = audience.group("value").casefold()
    if re.search(r"\b(?:pg-?13|teen|young[- ]adult|ya|adult)\b", value):
        return "YA"
    return "PG"


def _bool(value: str, path: Path, field: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"{path} field {field} must be true or false")


def _jpeg_dimensions(path: Path) -> tuple[int, int]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Cannot read title image {path}: {exc}") from exc
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError(f"{path} is not a readable JPEG")

    start_of_frame = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    offset = 2
    while offset < len(data):
        while offset < len(data) and data[offset] != 0xFF:
            offset += 1
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break

        marker = data[offset]
        offset += 1
        if marker in {0x01, 0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 1 >= len(data):
            break

        segment_length = int.from_bytes(data[offset : offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in start_of_frame:
            if segment_length < 7:
                break
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            return width, height
        offset += segment_length
    raise ValueError(f"{path} is not a readable JPEG")


def _validate_title_image(path: Path) -> None:
    width, height = _jpeg_dimensions(path)
    if (width, height) != (TITLE_IMAGE_WIDTH, TITLE_IMAGE_HEIGHT):
        raise ValueError(
            f"{path} must be exactly {TITLE_IMAGE_WIDTH}x{TITLE_IMAGE_HEIGHT}; "
            f"found {width}x{height}"
        )


def _cover_value(slug: str) -> str:
    return f"covers/{slug}.jpg"


def _source_cover(directory: Path, slug: str) -> str:
    path = directory / TITLE_IMAGE_NAME
    _validate_title_image(path)
    return _cover_value(slug)


def _parse_created_at(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO 8601 timestamp with a timezone") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def _resolve_created_at(path: Path, created: str, source_value: str | None) -> str:
    if source_value is None:
        modified = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        resolved = datetime.combine(date.fromisoformat(created), modified.timetz())
    else:
        if not isinstance(source_value, str):
            raise ValueError(f"created-at in {path} must be a string")
        resolved = _parse_created_at(source_value, f"created-at in {path}")
    if resolved.date().isoformat() != created:
        raise ValueError(f"created-at in {path} must use the same date as created")
    return resolved.isoformat(timespec="seconds")


def _resolve_edited(paths: Iterable[Path], repository_root: Path) -> str:
    source_paths = tuple(path for path in paths if path.is_file())
    if not source_paths:
        raise ValueError("Cannot resolve an edited date without source files")

    root = repository_root.resolve()
    try:
        relative_paths = [path.resolve().relative_to(root).as_posix() for path in source_paths]
    except ValueError:
        relative_paths = []

    if relative_paths:
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain=v1", "--", *relative_paths],
            text=True,
            capture_output=True,
            check=False,
        )
        if status.returncode == 0 and status.stdout.strip():
            return date.today().isoformat()

        history = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%cs", "--", *relative_paths],
            text=True,
            capture_output=True,
            check=False,
        )
        resolved = history.stdout.strip()
        if history.returncode == 0 and DATE.fullmatch(resolved):
            return resolved

    latest_modified = max(path.stat().st_mtime for path in source_paths)
    return datetime.fromtimestamp(latest_modified).astimezone().date().isoformat()


def _load_current_story(directory: Path) -> Story:
    story_path = directory / "story.md"
    front, body = parse_front_matter(story_path.read_text(encoding="utf-8"), story_path)
    required = {"title", "slug", "created", "canon"}
    if set(front) not in (required, required | {"created-at"}):
        raise ValueError(
            f"{story_path} fields must be title, slug, created, optional created-at, and canon"
        )
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
    prompt_source = prompt_path.read_text(encoding="utf-8")
    return Story(
        slug=front["slug"],
        title=front["title"],
        created=front["created"],
        created_at=_resolve_created_at(story_path, front["created"], front.get("created-at")),
        edited=_resolve_edited(
            (prompt_path, story_path, review_path, directory / TITLE_IMAGE_NAME),
            directory.parents[1],
        ),
        rating=_content_rating(prompt_source),
        canon=_bool(front["canon"], story_path, "canon"),
        status="canon" if front["canon"] == "true" else "reviewed",
        prompt=parse_writing_prompt(prompt_source, prompt_path),
        cover=_source_cover(directory, front["slug"]),
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
    prompt_source = prompt_path.read_text(encoding="utf-8")
    return Story(
        slug=record["slug"],
        title=record["title"],
        created=record["created"],
        created_at=_resolve_created_at(story_path, record["created"], record.get("createdAt")),
        edited=_resolve_edited(
            (prompt_path, story_path, record_path, directory / TITLE_IMAGE_NAME),
            directory.parents[1],
        ),
        rating=_content_rating(prompt_source),
        canon=record["canon"],
        status=record["status"],
        prompt=parse_writing_prompt(prompt_source, prompt_path),
        cover=_source_cover(directory, record["slug"]),
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
    return tuple(
        sorted(
            stories,
            key=lambda item: _parse_created_at(item.created_at, f"createdAt for {item.slug}"),
            reverse=True,
        )
    )


def load_catalog(snapshot_path: Path = SNAPSHOT_PATH) -> Catalog:
    value = read_json_object(snapshot_path)
    require_exact_fields(value, {"schemaVersion", "stories"}, str(snapshot_path))
    if value["schemaVersion"] != 4 or not isinstance(value["stories"], list):
        raise ValueError(f"Unsupported snapshot in {snapshot_path}")

    stories: list[Story] = []
    seen: set[str] = set()
    fields = {
        "slug",
        "title",
        "created",
        "createdAt",
        "edited",
        "rating",
        "canon",
        "status",
        "prompt",
        "cover",
        "body",
    }
    for index, item in enumerate(value["stories"]):
        if not isinstance(item, dict):
            raise ValueError(f"Snapshot story {index} is not an object")
        require_exact_fields(item, fields, f"snapshot story {index}")
        created_at = (
            _parse_created_at(item["createdAt"], f"createdAt in snapshot story {index}")
            if isinstance(item["createdAt"], str)
            else None
        )
        if (
            not isinstance(item["slug"], str)
            or not SLUG.fullmatch(item["slug"])
            or item["slug"] in seen
            or not isinstance(item["title"], str)
            or not item["title"].strip()
            or not isinstance(item["created"], str)
            or not DATE.fullmatch(item["created"])
            or created_at is None
            or created_at.date().isoformat() != item["created"]
            or not isinstance(item["edited"], str)
            or not DATE.fullmatch(item["edited"])
            or not isinstance(item["rating"], str)
            or item["rating"] not in RATINGS
            or not isinstance(item["canon"], bool)
            or not isinstance(item["status"], str)
            or not item["status"].strip()
            or not isinstance(item["prompt"], str)
            or not item["prompt"].strip()
            or item["cover"] != _cover_value(item["slug"])
            or not isinstance(item["body"], str)
            or not item["body"].strip()
        ):
            raise ValueError(f"Invalid snapshot story {index}")
        _validate_title_image(snapshot_path.parent / item["cover"])
        seen.add(item["slug"])
        stories.append(
            Story(
                slug=item["slug"],
                title=item["title"],
                created=item["created"],
                created_at=item["createdAt"],
                edited=item["edited"],
                rating=item["rating"],
                canon=item["canon"],
                status=item["status"],
                prompt=item["prompt"],
                cover=item["cover"],
                body=item["body"],
            )
        )

    ordered = _ordered(stories)
    if tuple(stories) != ordered:
        raise ValueError(f"{snapshot_path} stories are not in newest-first order")
    return Catalog(ordered)


def save_catalog(stories: Iterable[Story], snapshot_path: Path = SNAPSHOT_PATH) -> Catalog:
    catalog = Catalog(_ordered(stories))
    value = {
        "schemaVersion": 4,
        "stories": [
            {
                "slug": story.slug,
                "title": story.title,
                "created": story.created,
                "createdAt": story.created_at,
                "edited": story.edited,
                "rating": story.rating,
                "canon": story.canon,
                "status": story.status,
                "prompt": story.prompt,
                "cover": story.cover,
                "body": story.body,
            }
            for story in catalog.stories
        ],
    }
    snapshot_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return catalog


def _capture_cover(story: Story, repository_root: Path, snapshot_path: Path) -> None:
    source = repository_root / "stories" / story.slug / TITLE_IMAGE_NAME
    _validate_title_image(source)
    destination = snapshot_path.parent / story.cover
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def capture_story(
    slug: str,
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> Catalog:
    story = load_story_source(slug, repository_root)
    existing = list(load_catalog(snapshot_path).stories) if snapshot_path.exists() else []
    _capture_cover(story, repository_root, snapshot_path)
    remaining = (item for item in existing if item.slug != story.slug)
    return save_catalog((story, *remaining), snapshot_path)


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
    stories = tuple(load_story_source(slug, repository_root) for slug in slugs)
    for story in stories:
        _capture_cover(story, repository_root, snapshot_path)
    return save_catalog(stories, snapshot_path)


REPOSITORY_URL = "https://github.com/BoundlessStudio/story-computing-machine"
GITHUB_ICON = '''<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 2.29 6.64 5.47 7.71.4.08.55-.17.55-.39 0-.19-.01-.82-.01-1.49-2.01.44-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.59 1.23.83.72 1.23 1.87.88 2.33.67.07-.53.28-.88.51-1.08-1.78-.21-3.64-.9-3.64-4.01 0-.89.31-1.62.82-2.19-.08-.21-.36-1.04.08-2.16 0 0 .67-.22 2.2.84A7.45 7.45 0 0 1 8 3.92c.68 0 1.36.09 2 .28 1.53-1.06 2.2-.84 2.2-.84.44 1.12.16 1.95.08 2.16.51.57.82 1.3.82 2.19 0 3.12-1.87 3.8-3.65 4.01.29.25.54.73.54 1.49 0 1.07-.01 1.93-.01 2.2 0 .22.15.47.55.39A8.03 8.03 0 0 0 16 8.13C16 3.64 12.42 0 8 0Z"/></svg>'''


def _page(title: str, body: str, home_href: str, stylesheet_href: str) -> str:
    repository_link = f'<a class="repository-link" href="{REPOSITORY_URL}" aria-label="View BoundlessStudio/story-computing-machine on GitHub" title="View repository on GitHub">{GITHUB_ICON}</a>'
    header = f'<header class="site-header"><a class="site-name" href="{home_href}">Story Computing Machine</a>{repository_link}</header>'
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)}</title>'
        f'<link rel="stylesheet" href="{html.escape(stylesheet_href, quote=True)}">'
        f'</head><body>{header}<main>{body}</main></body></html>'
    )


def _prompt(value: str) -> str:
    return f'<div class="prompt"><span class="prompt-label">Prompt</span><blockquote>{html.escape(value)}</blockquote></div>'


def _without_leading_title(body: str) -> str:
    heading = re.match(r"^#\s+[^\n]+?\s*(?:\n+|\Z)", body)
    return body if heading is None else body[heading.end() :].lstrip()


def _story_label(story: Story) -> str:
    return "Canon" if story.canon else story.status.replace("-", " ").title()


def _display_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"


def render_index(catalog: Catalog) -> str:
    items = []
    for index, story in enumerate(catalog.stories):
        created = html.escape(story.created)
        edited = html.escape(story.edited)
        slug = html.escape(story.slug, quote=True)
        title = html.escape(story.title)
        cover = html.escape(story.cover, quote=True)
        story_label = html.escape(_story_label(story))
        status_class = re.sub(r"[^a-z0-9]+", "-", _story_label(story).casefold()).strip("-")
        rating = html.escape(story.rating)
        rating_class = story.rating.casefold().replace("+", "-plus")
        loading = "eager" if index == 0 else "lazy"
        items.append(
            f'<li class="story-card"><a class="story-card-link" href="stories/{slug}.html">'
            f'<img class="card-cover" src="{cover}" alt="Cover art for {title}" width="864" height="1536" '
            f'loading="{loading}" decoding="async">'
            f'<div class="card-copy"><h2 class="story-title">{title}</h2>'
            f'<span class="card-prompt"><span class="prompt-label">Prompt</span>'
            f'{html.escape(story.prompt)}</span>'
            f'<dl class="card-details">'
            f'<div class="card-detail"><dt>Date created</dt><dd><time datetime="{created}">{_display_date(story.created)}</time></dd></div>'
            f'<div class="card-detail"><dt>Date edited</dt><dd><time datetime="{edited}">{_display_date(story.edited)}</time></dd></div>'
            f'<div class="card-detail"><dt>State</dt><dd><span class="status status-{status_class}">{story_label}</span></dd></div>'
            f'<div class="card-detail"><dt>Word count</dt><dd><span class="word-count">{story.word_count:,}</span></dd></div>'
            f'<div class="card-detail"><dt>Rating</dt><dd><span class="rating rating-{rating_class}">{rating}</span></dd></div>'
            f'</dl></div></a></li>'
        )
    body = (
        '<section class="library"><h1>Shared-Universe Fiction</h1>'
        '<p class="lede">Choose a cover and step into another world.</p>'
        f'<p class="collection-count">{len(items)} stored publications.</p>'
        f'<ol class="story-grid">{"".join(items)}</ol></section>'
    )
    return _page("Shared-Universe Fiction", body, "index.html", "styles.css")


def render_story(story: Story) -> str:
    prose = markdown.markdown(_without_leading_title(story.body), extensions=["extra", "smarty"])
    title = html.escape(story.title)
    cover = html.escape(f"../{story.cover}", quote=True)
    body = (
        f'<article class="story"><p class="back-link"><a href="../index.html">← All stories</a></p>'
        f'<h1>{title}</h1>'
        f'<p class="story-page-meta">{_story_label(story)} · {story.word_count:,} words</p>'
        f'{_prompt(story.prompt)}'
        f'<figure class="story-cover"><img src="{cover}" alt="Cover art for {html.escape(story.title, quote=True)}" '
        f'width="864" height="1536" decoding="async"></figure>'
        f'<div class="story-prose">{prose}</div></article>'
    )
    return _page(story.title, body, "../index.html", "../styles.css")


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
    (destination / "covers").mkdir()
    shutil.copy2(STYLESHEET_PATH, destination / "styles.css")
    (destination / "index.html").write_text(render_index(catalog), encoding="utf-8")
    for story in catalog.stories:
        shutil.copy2(snapshot_path.parent / story.cover, destination / story.cover)
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
