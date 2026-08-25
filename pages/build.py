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
from PIL import Image, ImageOps

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(__file__).with_name("catalog.json")
STYLESHEET_PATH = Path(__file__).with_name("styles.css")
TIMELINE_PATH = Path(__file__).with_name("timeline.json")
TIMELINE_SCRIPT_PATH = Path(__file__).with_name("timeline.js")
WORLDLINE_HERO_ART_PATH = Path(__file__).with_name("worldline-hero-art.webp")
TIMELINE_ICON_DIRECTORY = "timeline-icons"
TIMELINE_ICON_SIZE = 160
# Kept as aliases for the retired chronology renderers below. The live page uses
# these square assets strictly as small story emblems, never as cover cards.
TIMELINE_COVER_DIRECTORY = TIMELINE_ICON_DIRECTORY
TIMELINE_COVER_WIDTH = TIMELINE_ICON_SIZE
TIMELINE_COVER_HEIGHT = TIMELINE_ICON_SIZE
TITLE_IMAGE_NAME = "title-image.jpg"
TITLE_IMAGE_WIDTH = 864
TITLE_IMAGE_HEIGHT = 1536
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RATINGS = frozenset({"PG", "YA", "R+"})
PLACEMENT_CONFIDENCE = frozenset({"fixed", "inferred", "speculative", "unresolved"})
TIMELINE_MAGIC_STATES = frozenset(
    {"old-magic", "long-dark", "new-magic", "uncertain", "off-axis"}
)


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


@dataclass(frozen=True)
class TimelineGroup:
    id: str
    ordered: bool
    eyebrow: str
    title: str
    description: str
    sequence_note: str
    confidence: str
    stories: tuple[str, ...]


@dataclass(frozen=True)
class TimelineChapter:
    id: str
    magic_state: str
    ordered: bool
    type: str
    eyebrow: str
    title: str
    description: str
    sequence_note: str
    confidence: str
    stories: tuple[str, ...]
    constellations: tuple[TimelineGroup, ...]


@dataclass(frozen=True)
class TimelineSpan:
    start: str
    end: str
    note: str


@dataclass(frozen=True)
class Timeline:
    chapters: tuple[TimelineChapter, ...]
    story_moments: dict[str, tuple[str, ...]]
    story_spans: dict[str, TimelineSpan]
    story_confidence: dict[str, str]


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


def _timeline_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _timeline_story_slugs(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    slugs = tuple(value)
    if any(not isinstance(slug, str) or not SLUG.fullmatch(slug) for slug in slugs):
        raise ValueError(f"{label} contains an invalid story slug")
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"{label} contains a duplicate story slug")
    return slugs


def _timeline_group(value: Any, label: str) -> TimelineGroup:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    require_exact_fields(
        value,
        {
            "id",
            "ordered",
            "eyebrow",
            "title",
            "description",
            "sequenceNote",
            "confidence",
            "stories",
        },
        label,
    )
    group_id = _timeline_text(value["id"], f"{label} id")
    if not SLUG.fullmatch(group_id):
        raise ValueError(f"{label} id must be a slug")
    confidence = _timeline_text(value["confidence"], f"{label} confidence")
    if not isinstance(value["ordered"], bool):
        raise ValueError(f"{label} ordered must be a boolean")
    if confidence not in PLACEMENT_CONFIDENCE:
        raise ValueError(f"{label} has unsupported confidence {confidence}")
    return TimelineGroup(
        id=group_id,
        ordered=value["ordered"],
        eyebrow=_timeline_text(value["eyebrow"], f"{label} eyebrow"),
        title=_timeline_text(value["title"], f"{label} title"),
        description=_timeline_text(value["description"], f"{label} description"),
        sequence_note=_timeline_text(value["sequenceNote"], f"{label} sequenceNote"),
        confidence=confidence,
        stories=_timeline_story_slugs(value["stories"], f"{label} stories"),
    )


def load_timeline(catalog: Catalog, path: Path = TIMELINE_PATH) -> Timeline:
    value = read_json_object(path)
    require_exact_fields(
        value,
        {
            "schemaVersion",
            "chapters",
            "storyMoments",
            "storySpans",
            "storyConfidence",
        },
        str(path),
    )
    if value["schemaVersion"] != 3 or not isinstance(value["chapters"], list):
        raise ValueError(f"Unsupported timeline snapshot in {path}")
    if not isinstance(value["storyMoments"], dict):
        raise ValueError(f"storyMoments in {path} must be an object")
    if not isinstance(value["storySpans"], dict):
        raise ValueError(f"storySpans in {path} must be an object")
    if not isinstance(value["storyConfidence"], dict):
        raise ValueError(f"storyConfidence in {path} must be an object")

    known_slugs = {story.slug for story in catalog.stories}
    seen_ids: set[str] = set()
    placed_slugs: set[str] = set()
    default_confidence: dict[str, str] = {}
    chapters: list[TimelineChapter] = []
    chapter_fields = {
        "id",
        "magicState",
        "ordered",
        "type",
        "eyebrow",
        "title",
        "description",
        "sequenceNote",
        "confidence",
        "stories",
        "constellations",
    }
    supported_types = {"era", "branch", "field", "hinge", "interval"}

    for index, item in enumerate(value["chapters"]):
        label = f"timeline chapter {index}"
        if not isinstance(item, dict):
            raise ValueError(f"{label} must be an object")
        require_exact_fields(item, chapter_fields, label)
        chapter_id = _timeline_text(item["id"], f"{label} id")
        magic_state = _timeline_text(item["magicState"], f"{label} magicState")
        if not isinstance(item["ordered"], bool):
            raise ValueError(f"{label} ordered must be a boolean")
        chapter_type = _timeline_text(item["type"], f"{label} type")
        chapter_confidence = _timeline_text(item["confidence"], f"{label} confidence")
        if not SLUG.fullmatch(chapter_id) or chapter_id in seen_ids:
            raise ValueError(f"{label} has an invalid or duplicate id")
        if chapter_type not in supported_types:
            raise ValueError(f"{label} has unsupported type {chapter_type}")
        if magic_state not in TIMELINE_MAGIC_STATES:
            raise ValueError(f"{label} has unsupported magic state {magic_state}")
        if chapter_confidence not in PLACEMENT_CONFIDENCE:
            raise ValueError(
                f"{label} has unsupported confidence {chapter_confidence}"
            )
        if not isinstance(item["constellations"], list):
            raise ValueError(f"{label} constellations must be a list")

        seen_ids.add(chapter_id)
        stories = _timeline_story_slugs(item["stories"], f"{label} stories")
        groups: list[TimelineGroup] = []
        for group_index, group_value in enumerate(item["constellations"]):
            group = _timeline_group(group_value, f"{label} constellation {group_index}")
            if group.id in seen_ids:
                raise ValueError(f"Timeline id {group.id} is duplicated")
            seen_ids.add(group.id)
            groups.append(group)

        chapter_slugs = [*stories, *(slug for group in groups for slug in group.stories)]
        unknown = sorted(set(chapter_slugs) - known_slugs)
        repeated_here = sorted(
            slug for slug in set(chapter_slugs) if chapter_slugs.count(slug) > 1
        )
        duplicate = sorted(slug for slug in chapter_slugs if slug in placed_slugs)
        if unknown:
            raise ValueError(f"{label} references unknown stories: {unknown}")
        if repeated_here:
            raise ValueError(f"{label} repeats stories within the chapter: {repeated_here}")
        if duplicate:
            raise ValueError(f"{label} repeats already placed stories: {duplicate}")
        placed_slugs.update(chapter_slugs)
        default_confidence.update({slug: chapter_confidence for slug in stories})
        for group in groups:
            default_confidence.update({slug: group.confidence for slug in group.stories})

        chapters.append(
            TimelineChapter(
                id=chapter_id,
                magic_state=magic_state,
                ordered=item["ordered"],
                type=chapter_type,
                eyebrow=_timeline_text(item["eyebrow"], f"{label} eyebrow"),
                title=_timeline_text(item["title"], f"{label} title"),
                description=_timeline_text(item["description"], f"{label} description"),
                sequence_note=_timeline_text(
                    item["sequenceNote"], f"{label} sequenceNote"
                ),
                confidence=chapter_confidence,
                stories=stories,
                constellations=tuple(groups),
            )
        )

    moments: dict[str, tuple[str, ...]] = {}
    for slug, labels in value["storyMoments"].items():
        if slug not in known_slugs:
            raise ValueError(f"storyMoments references unknown story {slug}")
        if not isinstance(labels, list) or not labels or len(labels) > 8:
            raise ValueError(f"storyMoments for {slug} must contain one to eight labels")
        moments[slug] = tuple(
            _timeline_text(moment, f"storyMoments for {slug}") for moment in labels
        )

    spans: dict[str, TimelineSpan] = {}
    for slug, span in value["storySpans"].items():
        if slug not in known_slugs:
            raise ValueError(f"storySpans references unknown story {slug}")
        if slug not in placed_slugs:
            raise ValueError(f"storySpans references unplaced story {slug}")
        if not isinstance(span, dict):
            raise ValueError(f"storySpans for {slug} must be an object")
        require_exact_fields(span, {"start", "end", "note"}, f"storySpans for {slug}")
        spans[slug] = TimelineSpan(
            start=_timeline_text(span["start"], f"storySpans start for {slug}"),
            end=_timeline_text(span["end"], f"storySpans end for {slug}"),
            note=_timeline_text(span["note"], f"storySpans note for {slug}"),
        )

    confidence = dict(default_confidence)
    for slug, level in value["storyConfidence"].items():
        if slug not in known_slugs:
            raise ValueError(f"storyConfidence references unknown story {slug}")
        if level not in PLACEMENT_CONFIDENCE:
            raise ValueError(f"storyConfidence for {slug} is unsupported: {level}")
        confidence[slug] = level

    return Timeline(tuple(chapters), moments, spans, confidence)


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


def _page(
    title: str,
    body: str,
    library_href: str,
    timeline_href: str,
    stylesheet_href: str,
    *,
    current: str | None = None,
    script_href: str | None = None,
) -> str:
    repository_link = f'<a class="repository-link" href="{REPOSITORY_URL}" aria-label="View BoundlessStudio/story-computing-machine on GitHub" title="View repository on GitHub">{GITHUB_ICON}</a>'
    library_current = ' aria-current="page"' if current == "library" else ""
    timeline_current = ' aria-current="page"' if current == "timeline" else ""
    header = (
        f'<header class="site-header"><a class="site-name" href="{library_href}">Story Computing Machine</a>'
        f'<nav class="site-nav" aria-label="Primary">'
        f'<a href="{library_href}"{library_current}>Library</a>'
        f'<a href="{timeline_href}"{timeline_current}>Chronology</a></nav>'
        f'{repository_link}</header>'
    )
    script = (
        f'<script src="{html.escape(script_href, quote=True)}" defer></script>'
        if script_href is not None
        else ""
    )
    body_class = ' class="timeline-body"' if current == "timeline" else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)}</title>'
        f'<link rel="stylesheet" href="{html.escape(stylesheet_href, quote=True)}">'
        f'{script}</head><body{body_class}>{header}<main>{body}</main></body></html>'
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
    return _page(
        "Shared-Universe Fiction",
        body,
        "index.html",
        "timeline.html",
        "styles.css",
        current="library",
    )


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
    return _page(
        story.title,
        body,
        "../index.html",
        "../timeline.html",
        "../styles.css",
    )


def _timeline_cover(story: Story) -> str:
    return f"{TIMELINE_COVER_DIRECTORY}/{story.slug}.jpg"


def _write_timeline_cover(source: Path, destination: Path) -> None:
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        image = ImageOps.fit(
            image,
            (TIMELINE_ICON_SIZE, TIMELINE_ICON_SIZE),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.42),
        )
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(
            destination,
            format="JPEG",
            quality=84,
            optimize=True,
            progressive=True,
        )


def _timeline_card(
    story: Story,
    sequence_label: str,
    moments: tuple[str, ...],
    span: TimelineSpan | None,
    confidence: str,
) -> str:
    slug = html.escape(story.slug, quote=True)
    title = html.escape(story.title)
    cover = html.escape(_timeline_cover(story), quote=True)
    state_label = _story_label(story)
    state = re.sub(r"[^a-z0-9]+", "-", state_label.casefold()).strip("-")
    confidence_labels = {
        "fixed": "Era fixed",
        "inferred": "Era strongly inferred",
        "speculative": "Era speculative",
        "unresolved": "Era unresolved",
    }
    confidence_label = confidence_labels[confidence]
    if sequence_label.startswith("≈"):
        sequence_accessible = (
            f' aria-label="Approximate position {int(sequence_label[1:])} '
            f'in this era band"'
        )
    elif sequence_label == "?":
        sequence_accessible = ' aria-label="Position unresolved within this era band"'
    else:
        sequence_accessible = ' aria-label="Only story in this era band"'
    moment_list = ""
    if moments:
        moment_list = (
            '<ol class="timeline-moments" aria-label="Key moments">'
            + "".join(f"<li>{html.escape(moment)}</li>" for moment in moments)
            + "</ol>"
        )
    span_marker = ""
    if span is not None:
        span_marker = (
            f'<div class="timeline-span" role="group" aria-label="Story spans from '
            f'{html.escape(span.start, quote=True)} to {html.escape(span.end, quote=True)}">'
            f'<span class="timeline-span-labels"><span>{html.escape(span.start)}</span>'
            f'<span>{html.escape(span.end)}</span></span>'
            f'<i class="timeline-span-track" aria-hidden="true"></i>'
            f'<span class="timeline-span-note">{html.escape(span.note)}</span></div>'
        )
    return (
        f'<li class="timeline-story" data-story-state="{state}" '
        f'data-placement-confidence="{confidence}">'
        f'<a class="timeline-story-link" href="stories/{slug}.html">'
        f'<span class="timeline-cover-frame">'
        f'<img src="{cover}" alt="" width="{TIMELINE_COVER_WIDTH}" '
        f'height="{TIMELINE_COVER_HEIGHT}" loading="lazy" decoding="async">'
        f'<span class="timeline-sequence"{sequence_accessible}>{sequence_label}</span>'
        f'</span><div class="timeline-story-copy">'
        f'<span class="timeline-story-title">{title}</span>'
        f'<span class="timeline-story-state">{state_label}</span>'
        f'<span class="timeline-placement">{confidence_label}</span>'
        f'{span_marker}{moment_list}</div></a></li>'
    )


def _timeline_ribbon(
    slugs: tuple[str, ...],
    stories_by_slug: dict[str, Story],
    moments: dict[str, tuple[str, ...]],
    spans: dict[str, TimelineSpan],
    confidence: dict[str, str],
    *,
    ordered: bool = True,
) -> str:
    cards = "".join(
        _timeline_card(
            stories_by_slug[slug],
            f"≈{index:02d}" if ordered and len(slugs) > 1 else "◆" if ordered else "?",
            moments.get(slug, ()),
            spans.get(slug),
            confidence.get(slug, "unresolved"),
        )
        for index, slug in enumerate(slugs, start=1)
    )
    return (
        f'<div class="timeline-story-group" data-story-group data-story-total="{len(slugs)}">'
        f'<p class="timeline-group-count"><span data-group-visible>{len(slugs)}</span> '
        f'<span aria-hidden="true">/</span> {len(slugs)} stories</p>'
        f'<ol class="timeline-ribbon">{cards}</ol></div>'
    )


def _timeline_with_fallback(timeline: Timeline, catalog: Catalog) -> tuple[TimelineChapter, ...]:
    assigned = {
        slug
        for chapter in timeline.chapters
        for slug in (
            *chapter.stories,
            *(story for group in chapter.constellations for story in group.stories),
        )
    }
    unplaced = tuple(
        story.slug for story in reversed(catalog.stories) if story.slug not in assigned
    )
    if not unplaced:
        return timeline.chapters
    fallback = TimelineChapter(
        id="unplaced-stories",
        magic_state="off-axis",
        ordered=False,
        type="field",
        eyebrow="Chronology still open",
        title="The Uncharted Expanse",
        description=(
            "These stories have not yet been given an evidence-backed era placement. "
            "They remain visible here without acquiring a date or a canon relationship."
        ),
        sequence_note="No in-world sequence is asserted inside this holding branch.",
        confidence="unresolved",
        stories=unplaced,
        constellations=(),
    )
    return (*timeline.chapters, fallback)


def _render_timeline_legacy(catalog: Catalog, timeline: Timeline) -> str:
    chapters = _timeline_with_fallback(timeline, catalog)
    stories_by_slug = {story.slug: story for story in catalog.stories}
    confidence_counts = {
        level: sum(
            timeline.story_confidence.get(story.slug, "unresolved") == level
            for story in catalog.stories
        )
        for level in ("fixed", "inferred", "speculative", "unresolved")
    }

    def chapter_slugs(chapter: TimelineChapter) -> tuple[str, ...]:
        return (
            *chapter.stories,
            *(slug for group in chapter.constellations for slug in group.stories),
        )

    chapters_by_state = {
        state: tuple(chapter for chapter in chapters if chapter.magic_state == state)
        for state in TIMELINE_MAGIC_STATES
    }
    state_counts = {
        state: sum(len(chapter_slugs(chapter)) for chapter in state_chapters)
        for state, state_chapters in chapters_by_state.items()
    }

    dark_slugs = tuple(
        slug
        for chapter in chapters_by_state["long-dark"]
        for slug in chapter_slugs(chapter)
    )
    hero_candidates = (
        "all-accounts-due",
        dark_slugs[len(dark_slugs) // 2] if dark_slugs else "all-accounts-due",
        "the-sky-remembers-us-return",
    )
    hero_slugs = tuple(slug for slug in hero_candidates if slug in stories_by_slug)
    hero_covers = "".join(
        f'<span class="hero-cover hero-cover-{index + 1}"><img '
        f'src="{html.escape(_timeline_cover(stories_by_slug[slug]), quote=True)}" alt="" '
        f'width="{TIMELINE_COVER_WIDTH}" height="{TIMELINE_COVER_HEIGHT}" '
        f'decoding="async"></span>'
        for index, slug in enumerate(hero_slugs)
    )

    state_content = {
        "old-magic": {
            "number": "I",
            "sigil": "✦",
            "eyebrow": "Magic state · active",
            "title": "The Many Ages of Magic",
            "description": (
                "These are recurring civilizational forms, not stages of one society. "
                "Kingdoms, modernities, industries, and ruins may recur in any order across old magic."
            ),
            "start": "First wonders",
            "end": "All Accounts Due",
            "cycles": (
                "wild / local",
                "crown / covenant",
                "civic arcana",
                "high systems",
                "falls / refoundings",
            ),
        },
        "long-dark": {
            "number": "II",
            "sigil": "0",
            "eyebrow": "Magic state · zero · our present is here",
            "title": "The Long Dark",
            "description": (
                "Human modernities rise more than once, fail in different ways, and leave silos, "
                "cities, stations, successor peoples, and archives. Similar technology does not establish shared ancestry or order."
            ),
            "start": "After All Accounts Due",
            "end": "Before The Sky Remembers Us",
            "cycles": (
                "magicless modernities",
                "human afterfalls",
                "synthetic worlds",
                "orbital successors",
                "archive refoundings",
            ),
        },
        "new-magic": {
            "number": "III",
            "sigil": "↗",
            "eyebrow": "Magic state · reciprocal",
            "title": "Magic Begins Again",
            "description": (
                "The Sky does not restore the six dead systems. Living participants originate "
                "a new reciprocal magic; later public, modern, fantasy, and fallen worlds need not form one ascent."
            ),
            "start": "The Sky Remembers Us",
            "end": "The unwritten future",
            "cycles": (
                "reciprocal awakening",
                "public-magic worlds",
                "later fantasy forms",
                "future falls",
            ),
        },
        "uncertain": {
            "number": "?",
            "sigil": "⇄",
            "eyebrow": "Boundary field",
            "title": "Stories That Refuse a Side",
            "description": (
                "Active impossibilities exclude these stories from the Long Dark, but their settings "
                "do not yet reveal whether they occur before extinction or after reawakening."
            ),
            "start": "Old magic",
            "end": "New magic",
            "cycles": (
                "hidden magic modernity",
                "folkloric modernity",
                "public magic modernity",
            ),
        },
        "off-axis": {
            "number": "∞",
            "sigil": "◇",
            "eyebrow": "Outside the worldline",
            "title": "Off-Axis Realms",
            "description": (
                "Unequal clocks, external realities, and locations outside material time keep "
                "their own sequences without borrowing a place on the main current."
            ),
            "start": "Known internal sequence",
            "end": "Universal position open",
            "cycles": (
                "unequal clocks",
                "external worlds",
                "outside material time",
            ),
        },
    }

    state_sections: dict[str, str] = {}
    for state in ("old-magic", "long-dark", "new-magic", "uncertain", "off-axis"):
        state_chapters = chapters_by_state[state]
        if not state_chapters:
            continue
        state_meta = state_content[state]
        rendered_chapters: list[str] = []
        era_links: list[str] = []
        for chapter_index, chapter in enumerate(state_chapters, start=1):
            special_markers = {
                "terminal-convergence": "END",
                "our-present-marker": "YOU ARE HERE",
                "joined-sky": "BEGIN",
                "western-bay-invasion": "ANCHOR",
                "glass-sea": "LATER",
                "contemporary-supernatural": "⇄",
                "old-dark-hinge": "?",
                "off-axis-realms": "∞",
            }
            unordered_markers = {
                "old-magic": "WAVE",
                "long-dark": "ISLAND",
                "new-magic": "WAVE",
                "uncertain": "?",
                "off-axis": "∞",
            }
            chapter_marker = special_markers.get(
                chapter.id,
                f"{state_meta['number']}.{chapter_index}"
                if chapter.ordered
                else unordered_markers[state],
            )
            chapter_id = html.escape(chapter.id, quote=True)
            era_links.append(
                f'<li><a data-chapter-link href="#{chapter_id}">'
                f'<span>{html.escape(chapter_marker)}</span>'
                f'<em>{html.escape(chapter.title)}</em></a></li>'
            )

            groups = []
            if chapter.stories:
                groups.append(
                    _timeline_ribbon(
                        chapter.stories,
                        stories_by_slug,
                        timeline.story_moments,
                        timeline.story_spans,
                        timeline.story_confidence,
                        ordered=chapter.ordered,
                    )
                )
            for group in chapter.constellations:
                groups.append(
                    f'<section class="timeline-constellation" id="{html.escape(group.id, quote=True)}" '
                    f'data-group-confidence="{group.confidence}">'
                    f'<header class="constellation-heading"><p class="timeline-eyebrow">{html.escape(group.eyebrow)}</p>'
                    f'<h4>{html.escape(group.title)}</h4>'
                    f'<p>{html.escape(group.description)}</p>'
                    f'<p class="sequence-note">{html.escape(group.sequence_note)}</p></header>'
                    f'{_timeline_ribbon(group.stories, stories_by_slug, timeline.story_moments, timeline.story_spans, timeline.story_confidence, ordered=group.ordered)}'
                    f'</section>'
                )

            rendered_chapters.append(
                f'<section class="timeline-chapter chapter-{chapter.type}" id="{chapter_id}" '
                f'data-timeline-chapter data-group-confidence="{chapter.confidence}">'
                f'<div class="timeline-chapter-inner"><header class="chapter-heading">'
                f'<div class="chapter-number" aria-hidden="true">{html.escape(chapter_marker)}</div>'
                f'<div><p class="timeline-eyebrow">{html.escape(chapter.eyebrow)}</p>'
                f'<h3>{html.escape(chapter.title)}</h3>'
                f'<p class="chapter-description">{html.escape(chapter.description)}</p>'
                f'<p class="sequence-note">{html.escape(chapter.sequence_note)}</p></div></header>'
                f'{"".join(groups)}</div></section>'
            )

        state_id = f"state-{state}"
        cycle_labels = "".join(
            f'<span>{html.escape(label)}</span>' for label in state_meta["cycles"]
        )
        state_sections[state] = (
            f'<section class="timeline-state {state_id}" id="{state_id}" '
            f'data-timeline-state="{state}">'
            f'<header class="timeline-state-header"><div class="timeline-state-header-inner">'
            f'<div class="state-sigil" aria-hidden="true">{state_meta["sigil"]}</div>'
            f'<div class="state-heading"><p class="timeline-eyebrow">{state_meta["eyebrow"]}</p>'
            f'<h2>{state_meta["title"]}</h2><p>{state_meta["description"]}</p>'
            f'<div class="state-range"><span>{state_meta["start"]}</span><i aria-hidden="true"></i>'
            f'<span>{state_meta["end"]}</span></div>'
            f'<div class="state-cycles" aria-label="Recurring civilizational shapes">{cycle_labels}</div></div>'
            f'<p class="state-story-count"><strong data-state-visible>{state_counts[state]}</strong> '
            f'stor{"y" if state_counts[state] == 1 else "ies"}</p></div>'
            f'<nav class="state-era-nav" aria-label="Jump within {html.escape(state_meta["title"])}"><ol>'
            f'{"".join(era_links)}</ol></nav></header>{"".join(rendered_chapters)}</section>'
        )

    total = len(catalog.stories)
    cosmology = (
        '<nav class="timeline-cosmology" aria-label="The three states of the universal timeline">'
        '<a class="cosmology-state cosmology-old" href="#state-old-magic">'
        f'<span>I</span><small>Magic active</small><strong>The many ages</strong><em>{state_counts["old-magic"]} stories</em></a>'
        '<div class="cosmology-boundary boundary-end"><small>Old magic ends</small><strong>All Accounts Due</strong></div>'
        '<a class="cosmology-state cosmology-dark" href="#state-long-dark">'
        f'<span>II</span><small>Magic absent</small><strong>The Long Dark</strong><em>{state_counts["long-dark"]} stories · our present</em></a>'
        '<div class="cosmology-boundary boundary-begin"><small>New magic begins</small><strong>The Sky Remembers Us</strong></div>'
        '<a class="cosmology-state cosmology-new" href="#state-new-magic">'
        f'<span>III</span><small>Magic reciprocal</small><strong>The second history</strong><em>{state_counts["new-magic"]} stories</em></a>'
        '</nav>'
    )
    body = (
        '<div class="timeline-page" data-timeline>'
        '<section class="timeline-hero"><div class="timeline-hero-inner">'
        '<div class="timeline-hero-copy">'
        '<p class="timeline-kicker">A chronology of the shared universe</p>'
        '<h1>The Worldline</h1>'
        '<p class="timeline-lede">Every story placed by universal era—this is not a publication or reading sequence. '
        'Magic is the measuring instrument: alive across many ages, absent through our present, '
        'then born anew when <em>The Sky Remembers Us</em>.</p>'
        f'<p class="timeline-total">All {total} published stories are accounted for below. '
        'The eras flow downward and the covers wrap into visible constellations. Border style '
        'shows placement confidence; wave and island markers deliberately avoid inventing an internal order.</p>'
        '<div class="timeline-legend" aria-label="Chronology legend">'
        '<span><i class="legend-line legend-line-solid" aria-hidden="true"></i>Era fixed</span>'
        '<span><i class="legend-line legend-line-inferred" aria-hidden="true"></i>Era inferred</span>'
        '<span><i class="legend-line legend-line-dotted" aria-hidden="true"></i>Era speculative</span>'
        '<span><i class="legend-orbit" aria-hidden="true"></i>Era unresolved</span>'
        '<span><i class="legend-star" aria-hidden="true">✦</i>Canon story</span></div>'
        '<div class="timeline-controls">'
        '<div class="timeline-filter" role="group" aria-label="Filter stories by era confidence">'
        f'<button type="button" data-timeline-filter="all" aria-pressed="true">All <span>{total}</span></button>'
        f'<button type="button" data-timeline-filter="fixed" aria-pressed="false">Era fixed <span>{confidence_counts["fixed"]}</span></button>'
        f'<button type="button" data-timeline-filter="inferred" aria-pressed="false">Era inferred <span>{confidence_counts["inferred"]}</span></button>'
        f'<button type="button" data-timeline-filter="speculative" aria-pressed="false">Era speculative <span>{confidence_counts["speculative"]}</span></button>'
        f'<button type="button" data-timeline-filter="unresolved" aria-pressed="false">Era unresolved <span>{confidence_counts["unresolved"]}</span></button>'
        '</div><p class="timeline-filter-result" aria-live="polite">'
        f'<span data-visible-total>{total}</span> placements in view</p></div>'
        f'{cosmology}'
        '<div class="timeline-side-jumps"><span>Not forced onto the line:</span>'
        f'<a href="#state-uncertain">⇄ Extinction side unresolved · {state_counts["uncertain"]}</a>'
        f'<a href="#state-off-axis">◇ Off-axis · {state_counts["off-axis"]}</a></div>'
        f'</div><div class="timeline-hero-covers" aria-hidden="true">{hero_covers}</div>'
        '</div></section>'
        '<div class="timeline-current">'
        f'{state_sections.get("old-magic", "")}'
        f'{state_sections.get("long-dark", "")}'
        f'{state_sections.get("new-magic", "")}'
        '</div><aside class="timeline-side-fields" aria-label="Chronology branches">'
        f'{state_sections.get("uncertain", "")}'
        f'{state_sections.get("off-axis", "")}'
        '</aside>'
        '<aside class="timeline-coda"><p class="timeline-eyebrow">How to read the map</p>'
        '<h2>One world. Three conditions. Honest uncertainty.</h2>'
        '<p>A fixed card means its broad era or boundary is established—not that its exact neighbor is. '
        'The Long Dark contains all magicless history, including our modern time; a contemporary aesthetic '
        'alone is not enough to enter it. Stories with active impossibilities remain between old and new '
        'magic until a real hinge identifies their side. Off-axis stories keep their own causal sequences '
        'without pretending they have a material-world date.</p>'
        '<p><a href="index.html">Return to the complete cover library →</a></p></aside>'
        '</div>'
    )
    return _page(
        "The Worldline — Story Chronology",
        body,
        "index.html",
        "timeline.html",
        "styles.css",
        current="timeline",
        script_href="timeline.js",
    )


def _atlas_story_card(
    story: Story,
    moments: tuple[str, ...],
    span: TimelineSpan | None,
    confidence: str,
) -> str:
    slug = html.escape(story.slug, quote=True)
    title = html.escape(story.title)
    cover = html.escape(_timeline_cover(story), quote=True)
    story_state = _story_label(story)
    state_class = re.sub(r"[^a-z0-9]+", "-", story_state.casefold()).strip("-")
    evidence = {
        "fixed": ("●", "Fixed anchor"),
        "inferred": ("↔", "Relative link"),
        "speculative": ("◇", "Compatible candidate"),
        "unresolved": ("?", "Coordinate open"),
    }
    glyph, evidence_label = evidence[confidence]
    note = (
        f'<span class="atlas-story-note">{html.escape(moments[0])}</span>'
        if moments
        else ""
    )
    span_marker = ""
    if span is not None:
        span_marker = (
            f'<span class="timeline-span" aria-label="{html.escape(span.note, quote=True)}">'
            f'<span>{html.escape(span.start)}</span><i aria-hidden="true"></i>'
            f'<span>{html.escape(span.end)}</span></span>'
        )
    canon_marker = (
        '<span class="atlas-canon" aria-hidden="true">✦</span>' if story.canon else ""
    )
    return (
        f'<li class="timeline-story" data-story-state="{state_class}" '
        f'data-placement-confidence="{confidence}">'
        f'<a class="timeline-story-link" href="stories/{slug}.html" aria-label="{title}">'
        f'<span class="timeline-cover-frame"><img src="{cover}" alt="" '
        f'width="{TIMELINE_COVER_WIDTH}" height="{TIMELINE_COVER_HEIGHT}" '
        f'loading="lazy" decoding="async">{canon_marker}'
        f'<span class="timeline-evidence evidence-{confidence}" aria-hidden="true">{glyph}</span></span>'
        f'<span class="timeline-story-copy"><strong class="timeline-story-title">{title}</strong>'
        f'<span class="timeline-story-meta"><span>{html.escape(story_state)}</span>'
        f'<span>{evidence_label}</span></span>{span_marker}{note}</span></a></li>'
    )


def _atlas_story_group(
    slugs: tuple[str, ...],
    stories_by_slug: dict[str, Story],
    timeline: Timeline,
) -> str:
    cards = "".join(
        _atlas_story_card(
            stories_by_slug[slug],
            timeline.story_moments.get(slug, ()),
            timeline.story_spans.get(slug),
            timeline.story_confidence.get(slug, "unresolved"),
        )
        for slug in slugs
    )
    count = len(slugs)
    return (
        f'<div class="timeline-story-group" data-story-group data-story-total="{count}">'
        f'<p class="timeline-group-count"><span data-group-visible>{count}</span> '
        f'of {count} stor{"y" if count == 1 else "ies"} visible</p>'
        f'<ol class="timeline-cover-grid">{cards}</ol></div>'
    )


def _atlas_constellation(
    group: TimelineGroup,
    stories_by_slug: dict[str, Story],
    timeline: Timeline,
    tone: str,
) -> str:
    group_id = html.escape(group.id, quote=True)
    count = len(group.stories)
    return (
        f'<details class="atlas-constellation constellation-{tone}" id="{group_id}" '
        f'data-constellation data-group-confidence="{group.confidence}">'
        f'<summary><span class="constellation-orbit" aria-hidden="true"><i></i></span>'
        f'<span class="constellation-summary-copy"><span class="timeline-eyebrow">'
        f'{html.escape(group.eyebrow)}</span><strong>{html.escape(group.title)}</strong>'
        f'<span>{html.escape(group.description)}</span></span>'
        f'<span class="constellation-summary-meta"><span class="constellation-count">'
        f'<b data-group-summary-visible>{count}</b> stor{"y" if count == 1 else "ies"}</span>'
        f'<span class="constellation-action"><span class="when-closed">Explore</span>'
        f'<span class="when-open">Close</span></span></span></summary>'
        f'<div class="constellation-body"><p class="sequence-note">'
        f'{html.escape(group.sequence_note)}</p>'
        f'{_atlas_story_group(group.stories, stories_by_slug, timeline)}</div></details>'
    )


def _atlas_anchor(
    chapter: TimelineChapter,
    stories_by_slug: dict[str, Story],
    timeline: Timeline,
    role: str,
) -> str:
    return (
        f'<article class="atlas-anchor anchor-{role}" id="{html.escape(chapter.id, quote=True)}" '
        f'data-timeline-chapter data-group-confidence="{chapter.confidence}">'
        f'<header><p class="timeline-eyebrow">{html.escape(chapter.eyebrow)}</p>'
        f'<h3>{html.escape(chapter.title)}</h3>'
        f'<p>{html.escape(chapter.description)}</p></header>'
        f'{_atlas_story_group(chapter.stories, stories_by_slug, timeline)}'
        f'<p class="sequence-note">{html.escape(chapter.sequence_note)}</p></article>'
    )


def render_timeline(catalog: Catalog, timeline: Timeline) -> str:
    chapters = _timeline_with_fallback(timeline, catalog)
    stories_by_slug = {story.slug: story for story in catalog.stories}
    chapters_by_id = {chapter.id: chapter for chapter in chapters}
    required_ids = {
        "western-bay-invasion",
        "glass-sea",
        "terminal-convergence",
        "our-present-marker",
        "long-dark-candidates",
        "joined-sky",
        "relative-links",
        "side-of-zero-open",
        "off-axis-realms",
    }
    missing_ids = sorted(required_ids - set(chapters_by_id))
    if missing_ids:
        raise ValueError(f"Timeline atlas is missing required chapters: {missing_ids}")

    confidence_order = ("fixed", "inferred", "speculative", "unresolved")
    confidence_counts = {
        level: sum(
            timeline.story_confidence.get(story.slug, "unresolved") == level
            for story in catalog.stories
        )
        for level in confidence_order
    }

    def chapter_slugs(chapter: TimelineChapter) -> tuple[str, ...]:
        return (
            *chapter.stories,
            *(slug for group in chapter.constellations for slug in group.stories),
        )

    state_counts = {
        state: sum(
            len(chapter_slugs(chapter))
            for chapter in chapters
            if chapter.magic_state == state
        )
        for state in TIMELINE_MAGIC_STATES
    }
    total = len(catalog.stories)

    hero_slugs = (
        "all-accounts-due",
        "the-room-that-waited",
        "the-sky-remembers-us-return",
    )
    hero_covers = "".join(
        f'<span class="hero-cover hero-cover-{index + 1}"><img '
        f'src="{html.escape(_timeline_cover(stories_by_slug[slug]), quote=True)}" alt="" '
        f'width="{TIMELINE_COVER_WIDTH}" height="{TIMELINE_COVER_HEIGHT}" '
        f'decoding="async"></span>'
        for index, slug in enumerate(hero_slugs)
    )

    old_anchors = "".join(
        _atlas_anchor(chapters_by_id[chapter_id], stories_by_slug, timeline, role)
        for chapter_id, role in (
            ("western-bay-invasion", "minor"),
            ("glass-sea", "minor"),
            ("terminal-convergence", "boundary"),
        )
    )
    long_dark = chapters_by_id["long-dark-candidates"]
    long_dark_arcs = "".join(
        _atlas_constellation(group, stories_by_slug, timeline, "dark")
        for group in long_dark.constellations
    )
    joined_sky = _atlas_anchor(
        chapters_by_id["joined-sky"], stories_by_slug, timeline, "boundary"
    )
    relative = chapters_by_id["relative-links"]
    relative_links = "".join(
        _atlas_constellation(group, stories_by_slug, timeline, "relative")
        for group in relative.constellations
    )
    uncertainty = chapters_by_id["side-of-zero-open"]
    uncertainty_groups = "".join(
        _atlas_constellation(group, stories_by_slug, timeline, "uncertain")
        for group in uncertainty.constellations
    )
    off_axis = chapters_by_id["off-axis-realms"]
    off_axis_groups = "".join(
        _atlas_constellation(group, stories_by_slug, timeline, "offaxis")
        for group in off_axis.constellations
    )
    present = chapters_by_id["our-present-marker"]

    body = (
        '<a class="timeline-skip-link" href="#timeline-atlas">Skip to the worldline map</a>'
        '<div class="timeline-page" data-timeline>'
        '<section class="timeline-hero"><div class="timeline-hero-inner">'
        '<div class="timeline-hero-copy"><p class="timeline-kicker">A universal chronology, not a reading order</p>'
        '<h1>The Worldline</h1>'
        '<p class="timeline-lede">Four fixed lights in a history measured by magic: '
        'alive, extinguished through our present, then born anew. Everything else keeps '
        'only the position its evidence earns.</p>'
        '<dl class="timeline-proof-strip">'
        f'<div><dt>Fixed anchors</dt><dd>{confidence_counts["fixed"]}</dd></div>'
        f'<div><dt>Relative links</dt><dd>{confidence_counts["inferred"]}</dd></div>'
        f'<div><dt>Long Dark candidates</dt><dd>{confidence_counts["speculative"]}</dd></div>'
        f'<div><dt>Coordinates open</dt><dd>{confidence_counts["unresolved"]}</dd></div></dl>'
        f'<p class="timeline-total">All {total} stories appear exactly once. Open a constellation '
        'when you want its covers; the map itself stays compact.</p></div>'
        f'<div class="timeline-hero-covers" aria-hidden="true">{hero_covers}</div>'
        '</div></section>'
        '<nav class="worldline-dock" aria-label="Worldline map">'
        '<div class="worldline-dock-main">'
        f'<a href="#old-magic-map" data-worldline-link="old-magic"><span>✦</span><strong>Old Magic</strong>'
        f'<small>{state_counts["old-magic"]} fixed · ends at All Accounts</small></a>'
        f'<a href="#long-dark-map" data-worldline-link="long-dark"><span>0</span><strong>The Long Dark</strong>'
        f'<small>{state_counts["long-dark"]} candidates · our present inside</small></a>'
        f'<a href="#new-magic-map" data-worldline-link="new-magic"><span>✧</span><strong>New Magic</strong>'
        f'<small>{state_counts["new-magic"]} fixed · begins at the Sky</small></a></div>'
        '<div class="worldline-dock-branches">'
        f'<a href="#uncertainty-map" data-worldline-link="uncertain">⇄ Uncertainty belt · {state_counts["uncertain"]}</a>'
        f'<a href="#off-axis-map" data-worldline-link="off-axis">◇ Off-axis · {state_counts["off-axis"]}</a>'
        '</div></nav>'
        '<section class="timeline-tools" aria-label="Timeline controls">'
        '<div><p class="timeline-eyebrow">Filter by evidence</p>'
        '<div class="timeline-filter" role="group" aria-label="Filter stories by placement evidence">'
        f'<button type="button" data-timeline-filter="all" aria-pressed="true">All <span>{total}</span></button>'
        f'<button type="button" data-timeline-filter="fixed" aria-pressed="false">Anchor <span>{confidence_counts["fixed"]}</span></button>'
        f'<button type="button" data-timeline-filter="inferred" aria-pressed="false">Relative <span>{confidence_counts["inferred"]}</span></button>'
        f'<button type="button" data-timeline-filter="speculative" aria-pressed="false">Candidate <span>{confidence_counts["speculative"]}</span></button>'
        f'<button type="button" data-timeline-filter="unresolved" aria-pressed="false">Open <span>{confidence_counts["unresolved"]}</span></button>'
        '</div></div><div class="timeline-tool-status">'
        f'<p><strong data-visible-total>{total}</strong> placements in view</p>'
        '<button type="button" data-collapse-constellations>Collapse all constellations</button>'
        '</div></section>'
        '<div class="timeline-atlas" id="timeline-atlas">'
        '<section class="atlas-worldline" aria-label="The fixed universal worldline">'
        f'<section class="atlas-state atlas-old" id="old-magic-map" data-map-section="old-magic" '
        f'data-timeline-state="old-magic"><header class="atlas-state-heading"><span class="atlas-sigil">✦</span>'
        f'<div><p class="timeline-eyebrow">Before perfect zero · <strong data-state-visible>{state_counts["old-magic"]}</strong> stories fixed</p>'
        '<h2>Old Magic</h2><p>Countless magical civilizations may rise and fall here. '
        'Only this narrow chain is presently anchored.</p></div></header>'
        f'<div class="atlas-anchor-stack">{old_anchors}</div></section>'
        f'<section class="atlas-state atlas-dark" id="long-dark-map" data-map-section="long-dark" '
        f'data-timeline-state="long-dark"><header class="atlas-state-heading"><span class="atlas-sigil">0</span>'
        f'<div><p class="timeline-eyebrow">Perfect material zero · <strong data-state-visible>{state_counts["long-dark"]}</strong> candidates</p>'
        '<h2>The Long Dark</h2><p>Not one civilization, but a vast interval containing '
        'independent modernities, afterfalls, successors, and archives.</p></div></header>'
        f'<aside class="our-present"><span>You are here</span><strong>{html.escape(present.title)}</strong>'
        f'<p>{html.escape(present.description)}</p></aside>'
        f'<div class="parallel-arcs" aria-label="Parallel Long Dark possibilities">{long_dark_arcs}</div></section>'
        f'<section class="atlas-state atlas-new" id="new-magic-map" data-map-section="new-magic" '
        f'data-timeline-state="new-magic"><header class="atlas-state-heading"><span class="atlas-sigil">✧</span>'
        f'<div><p class="timeline-eyebrow">After perfect zero · <strong data-state-visible>{state_counts["new-magic"]}</strong> story fixed</p>'
        '<h2>New Magic</h2><p>The second history begins with reciprocal life. '
        'No later published civilization is fixed here yet.</p></div></header>'
        f'{joined_sky}<div class="new-horizon" aria-hidden="true"><span></span><span></span><span></span>'
        '<p>The future remains unwritten</p></div></section></section>'
        f'<section class="uncertainty-field" id="uncertainty-map" data-map-section="uncertain" '
        f'data-timeline-state="uncertain"><header class="field-heading"><div><p class="timeline-eyebrow">'
        f'Side branches · <strong data-state-visible>{state_counts["uncertain"]}</strong> stories</p>'
        f'<h2>{html.escape(uncertainty.title)}</h2><p>{html.escape(uncertainty.description)}</p></div>'
        '<div class="uncertainty-symbol" aria-hidden="true">⇄</div></header>'
        f'<div class="relative-link-field"><header><p class="timeline-eyebrow">{html.escape(relative.eyebrow)}</p>'
        f'<h3>{html.escape(relative.title)}</h3><p>{html.escape(relative.description)}</p></header>'
        f'<div class="constellation-grid relative-grid">{relative_links}</div></div>'
        f'<div class="constellation-grid uncertainty-grid">{uncertainty_groups}</div></section>'
        f'<aside class="offaxis-field" id="off-axis-map" data-map-section="off-axis" '
        f'data-timeline-state="off-axis"><header class="field-heading"><div>'
        f'<p class="timeline-eyebrow">Outside stable material dating · '
        f'<strong data-state-visible>{state_counts["off-axis"]}</strong> stories</p>'
        f'<h2>{html.escape(off_axis.title)}</h2><p>{html.escape(off_axis.description)}</p></div>'
        '<div class="offaxis-orbit" aria-hidden="true"><i></i><i></i><i></i></div></header>'
        f'<div class="constellation-grid offaxis-grid">{off_axis_groups}</div></aside></div>'
        '<aside class="timeline-coda"><p class="timeline-eyebrow">The evidence rule</p>'
        '<h2>Shape is not a date.</h2><p>A kingdom can rise after a city. A superhero '
        'modernity can precede extinction or follow the joined sky. A ruin can belong to '
        'any fall. The map fixes cross-story chronology only where the stories or universe '
        'authority actually supply a hinge.</p><p><a href="index.html">Return to the complete cover library →</a></p></aside>'
        '</div>'
    )
    return _page(
        "The Worldline — Story Chronology",
        body,
        "index.html",
        "timeline.html",
        "styles.css",
        current="timeline",
        script_href="timeline.js",
    )


def _signal_chapter_slugs(chapter: TimelineChapter) -> tuple[str, ...]:
    return (
        *chapter.stories,
        *(slug for group in chapter.constellations for slug in group.stories),
    )


def _signal_evidence(level: str) -> tuple[str, str]:
    return {
        "fixed": ("Fixed anchor", "Solid double ring"),
        "inferred": ("Relative link", "Linked ring"),
        "speculative": ("Compatible candidate", "Dotted ring"),
        "unresolved": ("Working era fit", "Open split ring"),
    }[level]


def _signal_story_marker(story: Story, confidence: str) -> str:
    title = html.escape(story.title, quote=True)
    slug = html.escape(story.slug, quote=True)
    evidence, _ = _signal_evidence(confidence)
    return (
        f'<span class="signal-story-name marker-{confidence}" data-story-marker '
        f'data-story-slug="{slug}" data-placement-confidence="{confidence}" '
        f'data-title="{title}" title="{title} · {html.escape(evidence, quote=True)}">'
        f'<i aria-hidden="true"></i><span>{title}</span></span>'
    )


def _signal_story_link(
    story: Story,
    confidence: str,
) -> str:
    slug = html.escape(story.slug, quote=True)
    cover = html.escape(story.cover, quote=True)
    return (
        f'<a class="signal-story-link" href="stories/{slug}.html" aria-label="{html.escape(story.title, quote=True)}" '
        f'data-story-link data-story-slug="{slug}" data-title="{html.escape(story.title, quote=True)}" '
        f'data-placement-confidence="{confidence}">'
        '<span class="signal-story-cover">'
        f'<img src="{cover}" alt="" width="{TITLE_IMAGE_WIDTH}" height="{TITLE_IMAGE_HEIGHT}" '
        'loading="lazy" decoding="async"></span></a>'
    )


def _signal_era_stop(
    chapter: TimelineChapter,
    era_number: int,
    side: str,
    stories_by_slug: dict[str, Story],
    timeline: Timeline,
    epoch_hue: int,
    era_offset: int,
) -> str:
    slugs = _signal_chapter_slugs(chapter)
    markers = "".join(
        _signal_story_marker(stories_by_slug[slug], timeline.story_confidence[slug])
        for slug in slugs
    )
    links = "".join(
        _signal_story_link(
            stories_by_slug[slug],
            timeline.story_confidence[slug],
        )
        for slug in slugs
    )
    total = len(slugs)
    count_label = (
        f"{total} {'story' if total == 1 else 'stories'}"
        if total
        else "Open future"
    )
    marker_field = markers or '<span class="signal-future-dots" aria-hidden="true">· · ·</span>'
    drawer = (
        f'<div class="signal-era-drawer"><div class="signal-story-index" '
        f'data-story-group data-story-total="{total}">{links}</div></div>'
        if total
        else (
            f'<div class="signal-era-drawer signal-era-drawer-empty"><p>{html.escape(chapter.sequence_note)}</p></div>'
        )
    )
    node_label = f"{era_number:02d}"
    if chapter.id == "all-accounts-due":
        node_label = "0"
    elif chapter.id == "joined-sky":
        node_label = "✧"
    elif chapter.confidence == "fixed":
        node_label = "✦"
    elif chapter.confidence == "inferred":
        node_label = "↔"
    era_hue = (epoch_hue + era_offset * 7) % 360
    return (
        f'<details class="signal-era signal-era-{chapter.magic_state} signal-type-{chapter.type} side-{side}" '
        f'id="{html.escape(chapter.id, quote=True)}" data-era-stop data-timeline-state="{chapter.magic_state}" '
        f'data-era-has-stories="{str(bool(total)).lower()}" data-era-number="{era_number}" '
        f'style="--era-hue:{era_hue};--epoch-hue:{epoch_hue}">'
        '<summary>'
        f'<span class="signal-era-node" aria-hidden="true"><i></i><b>{node_label}</b></span>'
        '<span class="signal-era-card">'
        f'<span class="signal-era-kicker">{html.escape(chapter.eyebrow)}</span>'
        f'<span class="signal-era-title">{html.escape(chapter.title)}</span>'
        f'<span class="signal-era-description">{html.escape(chapter.description)}</span>'
        f'<span class="signal-marker-cloud">{marker_field}</span>'
        f'<span class="signal-era-footer"><span><strong data-era-visible>{total}</strong> '
        f'<span data-era-count-label>{html.escape("story" if total == 1 else "stories") if total else "future"}</span></span>'
        f'<span class="signal-era-action">{"Open index" if total else "Unwritten"}</span></span>'
        '</span></summary>'
        f'{drawer}</details>'
    )


def render_timeline(catalog: Catalog, timeline: Timeline) -> str:
    """Render a continuous vertical era signal with compact story-name lists."""
    stories_by_slug = {story.slug: story for story in catalog.stories}
    chapters_by_id = {chapter.id: chapter for chapter in timeline.chapters}
    confidence_order = ("fixed", "inferred", "speculative", "unresolved")
    confidence_counts = {
        level: sum(
            timeline.story_confidence.get(story.slug, "unresolved") == level
            for story in catalog.stories
        )
        for level in confidence_order
    }
    total = len(catalog.stories)

    epoch_specs = (
        (
            "first-breath",
            "old",
            "Epoch I",
            "The First Magical Rise",
            "Old Magic · Rise",
            "Guardians, village gifts, dangerous names, and first compacts form the earliest magical civilizations.",
            (
                "Wild magic + handcraft",
                "Gifted + ordinary",
                "Humans + ancient beings",
                "Village compacts",
            ),
            (
                "ancient-guardians",
                "first-gifts-and-compacts",
            ),
        ),
        (
            "roads-between-wonders",
            "old",
            "Epoch II",
            "The Road Age",
            "Old Magic · Expansion",
            "Hospitality, markets, repair, and living crossings connect small magical communities into wider exchange networks.",
            (
                "Practical magic + craft",
                "Bearers + ordinary traders",
                "Mixed peoples + guests",
                "Roads + markets",
            ),
            (
                "old-towers-and-first-guests",
                "roads-markets-and-living-doors",
            ),
        ),
        (
            "crowned-age",
            "old",
            "Epoch III",
            "The Crowned Height",
            "Old Magic · Height",
            "Founding legends mature into succession crises, dragon governments, sacred opposition, and monster sanctuary.",
            (
                "Court magic + weapons",
                "Rulers + commoners",
                "Humans + dragons + monsters",
                "Kingdoms + sanctuaries",
            ),
            (
                "founding-legends",
                "succession-and-broken-prophecy",
                "dragon-polities",
                "saints-demons-and-monster-sanctuaries",
            ),
        ),
        (
            "civic-arcana",
            "old",
            "Epoch IV",
            "Civic Arcana",
            "Old Magic · Civic height",
            "Healers, guilds, schools, houses, and classification systems make impossible power accountable to public life.",
            (
                "Measured magic + medicine",
                "Gifted + ordinary",
                "Many peoples",
                "Guilds + schools",
            ),
            (
                "healers-blood-and-bounded-bodies",
                "guilds-gods-and-repair",
                "schools-houses-and-classification",
            ),
        ),
        (
            "engineered-magic",
            "old",
            "Epoch V",
            "Arcane Industry",
            "Old Magic · Industrial height",
            "Infrastructure, colleges, apprenticeships, constructed life, and engineered peril turn magic into repeatable systems.",
            (
                "Engineered magic + machines",
                "Mages + constructed life",
                "Human + infernal + unknown",
                "Colleges + infrastructure",
            ),
            (
                "arcane-infrastructure-and-engineered-peril",
                "colleges-and-apprenticeship-reform",
                "constructed-life-at-cinder-annex",
            ),
        ),
        (
            "old-modern-end",
            "old",
            "Epoch VI",
            "The First Fall",
            "Old Magic · Fall",
            "A low-signal modernity, unequal-world bridge, catastrophe, museum memory, and terminal convergence close the first magical history.",
            (
                "Fading magic + modern tech",
                "Mostly ordinary lives",
                "Unequal worlds",
                "Modernity → collapse",
            ),
            (
                "old-modern-age",
                "ravel-bridge",
                "glass-sea-age",
                "museum-hinge",
                "all-accounts-due",
            ),
        ),
        (
            "material-dawn",
            "dark",
            "Epoch VII",
            "Material Refounding",
            "The Long Dark · Refounding",
            "Colossi, buried engines, dangerous ecologies, and creature peoples begin new civilizations under perfect material zero.",
            (
                "No magic + buried tech",
                "Normals + altered bodies",
                "Creature peoples + colossi",
                "Refounding settlements",
            ),
            (
                "colossi-and-buried-engines",
                "altered-memory-and-valley-medicine",
                "bodies-outside-the-old-measure",
            ),
        ),
        (
            "crowns-without-magic",
            "dark",
            "Epoch VIII",
            "Crowns Without Magic",
            "The Long Dark · Crowned height",
            "Courts, creature cultures, guild blades, gaslight houses, and engineers rebuild fantasy-shaped societies without operative magic.",
            (
                "No magic + craft / steam",
                "Unusual bodies, no spellcraft",
                "Humans + dragons + slimes",
                "Kingdoms + guilds",
            ),
            (
                "refuge-courts-and-marriage-states",
                "creature-cultures-without-enchantment",
                "guild-blades-gaslight-houses-and-engineers",
            ),
        ),
        (
            "long-dark-modernities",
            "dark",
            "Epoch IX",
            "The Machine Rise",
            "The Long Dark · Machine rise",
            "Ordinary lives, political power, unexplained anomalies, networked cities, and synthetic bodies occupy separate material modernities.",
            (
                "No magic + networked tech",
                "Normals + exceptional actors",
                "Humans + synthetics",
                "Modern states + cities",
            ),
            (
                "ordinary-present-and-familiar-lives",
                "private-powers-and-public-states",
                "anomalies-beside-material-zero",
                "layered-and-networked-cities",
                "synthetic-bodies-and-war-legacies",
            ),
        ),
        (
            "great-falls",
            "dark",
            "Epoch X",
            "The Great Falls",
            "The Long Dark · Fall",
            "Independent material civilizations collapse into wreckage, silent weapons, salvage codes, and exposed ruins.",
            (
                "No magic + ruin tech",
                "Survivors + weapons",
                "Humans + successors",
                "Collapse + salvage",
            ),
            (
                "great-falls-and-salvage",
            ),
        ),
        (
            "successor-orbital-rise",
            "dark",
            "Epoch XI",
            "Successor & Orbital Civilizations",
            "The Long Dark · Successor rise",
            "Mobile cities, restored bodies, orbital watchers, inherited Earths, and archives rise from unrelated material pasts.",
            (
                "No magic + orbital tech",
                "Restored + altered bodies",
                "Humans + posthumans + apes",
                "Mobile cities + successor Earths",
            ),
            (
                "mobile-cities-and-restored-bodies",
                "orbital-watchers-and-successor-earths",
                "archive-refoundings",
            ),
        ),
        (
            "joined-hidden-return",
            "new",
            "Epoch XII",
            "Magic Refounded",
            "New Magic · Refounding",
            "The joined sky starts magic again; foresight, inheritances, altered selves, visitors, and threshold assignments follow privately.",
            (
                "New magic + modern tech",
                "Hidden powers + normals",
                "Humans + visitors + altered selves",
                "Private refoundings",
            ),
            (
                "joined-sky",
                "time-foresight-and-copies",
                "inheritances-and-altered-selves",
                "visitors-at-the-door",
                "assignment-bridge",
            ),
        ),
        (
            "public-magic-height",
            "new",
            "Epoch XIII",
            "The Public-Magic Height",
            "New Magic · Public height",
            "Monsters, transformations, superhero institutions, transit, and civic myth become the infrastructure of a second magical modernity.",
            (
                "New magic + high tech",
                "Supers + normals",
                "Humans + monsters + gods",
                "Heroic + civic institutions",
            ),
            (
                "monsters-gods-and-avatars",
                "transformations-become-public",
                "hero-and-villain-institutions",
                "threshold-transit-and-unstable-travel",
                "civic-myth-and-dangerous-archives",
            ),
        ),
        (
            "second-sky-rise",
            "new",
            "Epoch XIV",
            "Second-Sky Kingdoms",
            "New Magic · Second rise",
            "Magic outlives its modern institutions and begins producing fantasy-shaped kingdoms again; their eventual height and fall remain unwritten.",
            (
                "New magic + later craft",
                "Publicly enchanted lives",
                "Humans + mythical peoples",
                "Kingdoms rising again",
            ),
            (
                "second-sky-kingdoms",
            ),
        ),
    )
    epoch_hues = {
        "first-breath": 34,
        "roads-between-wonders": 43,
        "crowned-age": 18,
        "civic-arcana": 52,
        "engineered-magic": 326,
        "old-modern-end": 7,
        "material-dawn": 198,
        "crowns-without-magic": 222,
        "long-dark-modernities": 204,
        "great-falls": 239,
        "successor-orbital-rise": 184,
        "joined-hidden-return": 158,
        "public-magic-height": 172,
        "second-sky-rise": 139,
    }
    if set(epoch_hues) != {spec[0] for spec in epoch_specs}:
        raise ValueError("Every timeline epoch must have one visual hue")
    expected_ids = {
        chapter_id
        for _, _, _, _, _, _, _, chapter_ids in epoch_specs
        for chapter_id in chapter_ids
    }
    if set(chapters_by_id) != expected_ids:
        missing = sorted(expected_ids - set(chapters_by_id))
        extra = sorted(set(chapters_by_id) - expected_ids)
        raise ValueError(f"Timeline renderer chapter mismatch; missing={missing}, extra={extra}")

    era_number = 0
    epoch_sections: list[str] = []
    phase_specs = (
        ("old", "World age I", "Old Magic"),
        ("dark", "World age II", "The Long Dark"),
        ("new", "World age III", "New Magic"),
    )
    nav_links: list[str] = []
    for phase_key, cycle_title, phase_title in phase_specs:
        phase_epochs = [spec for spec in epoch_specs if spec[1] == phase_key]
        phase_stories = sum(
            len(_signal_chapter_slugs(chapters_by_id[chapter_id]))
            for spec in phase_epochs
            for chapter_id in spec[7]
        )
        epoch_numbers = [spec[2].removeprefix("Epoch ") for spec in phase_epochs]
        epoch_range = (
            f"Epoch {epoch_numbers[0]}"
            if len(epoch_numbers) == 1
            else f"Epochs {epoch_numbers[0]}–{epoch_numbers[-1]}"
        )
        nav_links.append(
            f'<a href="#epoch-{phase_epochs[0][0]}" data-cycle-link="{phase_key}">'
            f'<span>{cycle_title}</span><strong>{phase_title}</strong>'
            f'<small>{epoch_range} · {phase_stories} plotted</small></a>'
        )

    hero_artwork = (
        '<figure class="signal-hero-art" aria-hidden="true">'
        '<img src="worldline-hero-art.webp" alt="" width="1536" height="1024" '
        'decoding="async" fetchpriority="high"></figure>'
    )
    for (
        epoch_key,
        epoch_phase,
        epoch_number,
        epoch_title,
        epoch_phase_title,
        epoch_description,
        epoch_world_tags,
        chapter_ids,
    ) in epoch_specs:
        epoch_stories = sum(
            len(_signal_chapter_slugs(chapters_by_id[chapter_id]))
            for chapter_id in chapter_ids
        )
        epoch_story_label = "story marker" if epoch_stories == 1 else "story markers"
        epoch_era_label = "era" if len(chapter_ids) == 1 else "eras"
        stops: list[str] = []
        for local_index, chapter_id in enumerate(chapter_ids):
            era_number += 1
            chapter = chapters_by_id[chapter_id]
            stops.append(
                _signal_era_stop(
                    chapter,
                    era_number,
                    "left" if local_index % 2 == 0 else "right",
                    stories_by_slug,
                    timeline,
                    epoch_hues[epoch_key],
                    local_index,
                )
            )
        epoch_sections.append(
            f'<section class="signal-epoch epoch-{epoch_phase}" id="epoch-{epoch_key}" '
            f'data-epoch-section="{epoch_key}" data-cycle-section="{epoch_phase}" '
            f'style="--epoch-hue:{epoch_hues[epoch_key]}"><header class="signal-epoch-heading">'
            f'<span>{epoch_number}</span><div><p>{epoch_phase_title} · {epoch_stories} {epoch_story_label} across {len(chapter_ids)} {epoch_era_label}</p>'
            f'<h2>{epoch_title}</h2><p>{epoch_description}</p>'
            '<div class="signal-world-texture" aria-label="World conditions in this epoch"><b>This world</b>'
            f'{"".join(f"<span>{html.escape(tag)}</span>" for tag in epoch_world_tags)}</div></div></header>'
            f'<div class="signal-era-sequence">{"".join(stops)}</div></section>'
        )

    body = (
        '<a class="signal-skip-link" href="#worldline-sequence">Skip to the worldline</a>'
        '<div class="signal-page" data-timeline>'
        '<section class="signal-hero"><div class="signal-hero-copy">'
        f'<p>One worldline · {len(epoch_specs)} civilizational epochs</p><h1>The Worldline</h1>'
        '<p class="signal-hero-lede">Civilizations rise, peak, fall, and begin again—under old magic, repeatedly through the Long Dark, and once more after the sky remembers. Every epoch names the kind of world its stories inhabit.</p>'
        f'<dl><div><dt>Epochs</dt><dd>{len(epoch_specs)}</dd></div>'
        f'<div><dt>Named eras</dt><dd>{era_number}</dd></div>'
        f'<div><dt>Stories plotted</dt><dd>{total}</dd></div>'
        f'<div><dt>Fixed anchors</dt><dd>{confidence_counts["fixed"]}</dd></div></dl>'
        f'</div><div class="signal-hero-graphic">{hero_artwork}</div></section>'
        '<nav class="signal-nav" aria-label="Timeline epochs">'
        f'<div class="signal-nav-epochs">{"".join(nav_links)}</div>'
        '<div class="signal-nav-tools"><div class="signal-filter" role="group" aria-label="Filter by placement evidence">'
        f'<button type="button" data-timeline-filter="all" aria-pressed="true">All <span>{total}</span></button>'
        f'<button type="button" data-timeline-filter="fixed" aria-pressed="false">Fixed <span>{confidence_counts["fixed"]}</span></button>'
        f'<button type="button" data-timeline-filter="inferred" aria-pressed="false">Linked <span>{confidence_counts["inferred"]}</span></button>'
        f'<button type="button" data-timeline-filter="speculative" aria-pressed="false">Candidate <span>{confidence_counts["speculative"]}</span></button>'
        f'<button type="button" data-timeline-filter="unresolved" aria-pressed="false">Working fit <span>{confidence_counts["unresolved"]}</span></button>'
        '</div><label class="signal-search"><span>Find a story</span>'
        '<input type="search" data-timeline-search placeholder="Search titles" autocomplete="off"></label>'
        '<p class="signal-result"><strong data-visible-total>'
        f'{total}</strong> stories in view</p><button type="button" data-collapse-eras>Close era indexes</button>'
        '</div></nav>'
        '<div class="signal-legend" aria-label="Placement evidence legend">'
        '<strong>Placement evidence</strong>'
        '<span class="marker-fixed">Fixed anchor</span><span class="marker-inferred">Relative link</span>'
        '<span class="marker-speculative">Compatible candidate</span><span class="marker-unresolved">Working era fit</span>'
        '</div>'
        f'<div class="signal-worldline" id="worldline-sequence">{"".join(epoch_sections)}</div>'
        '</div>'
    )
    return _page(
        "The Worldline — Story Chronology",
        body,
        "index.html",
        "timeline.html",
        "styles.css",
        current="timeline",
        script_href="timeline.js",
    )


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
    timeline = load_timeline(catalog)
    destination = prepare_output(output)
    (destination / "stories").mkdir()
    (destination / "covers").mkdir()
    (destination / TIMELINE_COVER_DIRECTORY).mkdir()
    shutil.copy2(STYLESHEET_PATH, destination / "styles.css")
    shutil.copy2(TIMELINE_SCRIPT_PATH, destination / "timeline.js")
    shutil.copy2(WORLDLINE_HERO_ART_PATH, destination / WORLDLINE_HERO_ART_PATH.name)
    (destination / "index.html").write_text(render_index(catalog), encoding="utf-8")
    (destination / "timeline.html").write_text(
        render_timeline(catalog, timeline),
        encoding="utf-8",
    )
    for story in catalog.stories:
        source_cover = snapshot_path.parent / story.cover
        shutil.copy2(source_cover, destination / story.cover)
        _write_timeline_cover(
            source_cover,
            destination / _timeline_cover(story),
        )
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
        timeline = load_timeline(catalog)
        placed = {
            slug
            for chapter in timeline.chapters
            for slug in (
                *chapter.stories,
                *(story for group in chapter.constellations for story in group.stories),
            )
        }
        print(
            f"PASS: {len(catalog.stories)} stored stories; "
            f"{len(placed)} curated chronology placements"
        )


if __name__ == "__main__":
    main()
