from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import markdown

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(__file__).with_name("catalog.json")
STYLESHEET_PATH = Path(__file__).with_name("styles.css")
THEME_SCRIPT_PATH = Path(__file__).with_name("theme.js")
TIMELINE_PATH = Path(__file__).with_name("timeline.json")
TIMELINE_SCRIPT_PATH = Path(__file__).with_name("timeline.js")
WORLDLINE_HERO_ART_PATH = Path(__file__).with_name("worldline-hero-art.webp")
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


def _load_bundle_story(directory: Path) -> Story:
    record_path = directory / "story.json"
    record = read_json_object(record_path)
    for field in ("slug", "title", "created", "canon"):
        if field not in record:
            raise ValueError(f"{record_path} lacks {field}")
    if record["slug"] != directory.name or not SLUG.fullmatch(record["slug"]):
        raise ValueError(f"Invalid bundle-format slug in {record_path}")
    if not isinstance(record["title"], str) or not DATE.fullmatch(record["created"]):
        raise ValueError(f"Invalid bundle-format title or date in {record_path}")
    if not isinstance(record["canon"], bool):
        raise ValueError(f"Invalid canon flag in {record_path}")

    story_path = directory / "05-story.md"
    front, body = parse_front_matter(story_path.read_text(encoding="utf-8"), story_path)
    expected = {
        "title": record["title"],
        "slug": record["slug"],
        "created": record["created"],
    }
    if front != expected:
        raise ValueError(f"Bundle-format story identity differs in {story_path}")

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
        status="canon" if record["canon"] else "reviewed",
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
        return _load_bundle_story(directory)
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


def _refuse_canon_demotions(stories: Iterable[Story], published: Catalog) -> None:
    published_by_slug = {story.slug: story for story in published.stories}
    demotions = sorted(
        story.slug
        for story in stories
        if story.slug in published_by_slug
        and published_by_slug[story.slug].canon
        and not story.canon
    )
    if demotions:
        raise ValueError(
            "Refusing to demote published canon stories from source markers: "
            f"{demotions}. Reconcile the authoritative canon markers first."
        )


def capture_story(
    slug: str,
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> Catalog:
    story = load_story_source(slug, repository_root)
    published = load_catalog(snapshot_path) if snapshot_path.exists() else Catalog(())
    _refuse_canon_demotions((story,), published)
    _capture_cover(story, repository_root, snapshot_path)
    remaining = (item for item in published.stories if item.slug != story.slug)
    return save_catalog((story, *remaining), snapshot_path)


def capture_all(
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> Catalog:
    published = load_catalog(snapshot_path)
    stories = tuple(load_story_source(story.slug, repository_root) for story in published.stories)
    _refuse_canon_demotions(stories, published)
    for story in stories:
        _capture_cover(story, repository_root, snapshot_path)
    return save_catalog(stories, snapshot_path)


def _bundle_index_slugs(path: Path) -> set[str]:
    rows = re.findall(
        r"^\| `([^`]+)` \|",
        path.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    duplicates = sorted(slug for slug, count in Counter(rows).items() if count > 1)
    if duplicates:
        raise ValueError(f"Bundle index repeats story rows: {duplicates}")
    return set(rows)


def _source_canon_marker(directory: Path) -> bool:
    current_path = directory / "story.md"
    bundle_record_path = directory / "story.json"
    if current_path.is_file():
        metadata, _ = parse_front_matter(
            current_path.read_text(encoding="utf-8"), current_path
        )
        return _bool(metadata.get("canon", ""), current_path, "canon")
    if bundle_record_path.is_file():
        value = read_json_object(bundle_record_path)
        source_canon = value.get("canon")
        if not isinstance(source_canon, bool):
            raise ValueError(f"Invalid canon marker in {bundle_record_path}")
        return source_canon
    raise ValueError(f"No canon marker found in {directory}")


def published_canon_marker_conflicts(
    catalog: Catalog,
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[str, ...]:
    conflicts: list[str] = []
    for story in catalog.stories:
        directory = repository_root / "stories" / story.slug
        if not directory.is_dir():
            continue
        source_canon = _source_canon_marker(directory)
        if source_canon != story.canon:
            conflicts.append(story.slug)
    return tuple(sorted(conflicts))


def validate_repository_inventory(
    catalog: Catalog,
    timeline: Timeline,
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> tuple[int, int, int]:
    story_root = repository_root / "stories"
    story_directories = {
        item.name: item
        for item in story_root.iterdir()
        if item.is_dir() and item.name != "_template"
    }
    invalid_sources = {
        slug
        for slug, directory in story_directories.items()
        if (directory / "story.md").is_file()
        == (directory / "05-story.md").is_file()
    }
    source_slugs = set(story_directories) - invalid_sources
    bundle_slugs = {
        slug
        for slug, directory in story_directories.items()
        if (directory / "05-story.md").is_file()
    }
    index_slugs = _bundle_index_slugs(story_root / "INDEX.md")
    catalog_slugs = {story.slug for story in catalog.stories}
    cover_root = snapshot_path.parent / "covers"
    cover_slugs = {path.stem for path in cover_root.glob("*.jpg")}
    invalid_cover_entries = {
        path.name
        for path in cover_root.iterdir()
        if not path.is_file() or path.suffix.lower() != ".jpg"
    }
    placements = [
        slug
        for chapter in timeline.chapters
        for slug in (
            *chapter.stories,
            *(story for group in chapter.constellations for story in group.stories),
        )
    ]
    placement_slugs = set(placements)

    problems: list[str] = []
    if invalid_sources:
        problems.append(f"unrecognized story directories: {sorted(invalid_sources)}")
    if bundle_slugs != index_slugs:
        problems.append(
            f"bundle index differs from bundle-format sources: index-only={sorted(index_slugs - bundle_slugs)}, "
            f"source-only={sorted(bundle_slugs - index_slugs)}"
        )
    if catalog_slugs != cover_slugs:
        problems.append(
            f"catalog differs from captured covers: catalog-only={sorted(catalog_slugs - cover_slugs)}, "
            f"cover-only={sorted(cover_slugs - catalog_slugs)}"
        )
    if invalid_cover_entries:
        problems.append(f"unrecognized captured-cover entries: {sorted(invalid_cover_entries)}")
    if catalog_slugs != placement_slugs or len(placements) != len(placement_slugs):
        problems.append(
            f"catalog differs from chronology: catalog-only={sorted(catalog_slugs - placement_slugs)}, "
            f"chronology-only={sorted(placement_slugs - catalog_slugs)}, placements={len(placements)}"
        )
    if catalog_slugs != source_slugs:
        problems.append(
            f"catalog differs from story sources: catalog-only={sorted(catalog_slugs - source_slugs)}, "
            f"source-only={sorted(source_slugs - catalog_slugs)}"
        )
    source_canon = {
        slug: _source_canon_marker(directory)
        for slug, directory in story_directories.items()
        if slug in source_slugs
    }
    canon_conflicts = sorted(
        story.slug
        for story in catalog.stories
        if story.slug in source_canon and source_canon[story.slug] != story.canon
    )
    if canon_conflicts:
        problems.append(
            f"catalog canon states differ from authoritative source flags: {canon_conflicts}"
        )
    missing_source_covers = [
        slug for slug in sorted(catalog_slugs) if not (story_root / slug / TITLE_IMAGE_NAME).is_file()
    ]
    if missing_source_covers:
        problems.append(f"published stories without source covers: {missing_source_covers}")
    stale_covers = [
        slug
        for slug in sorted(catalog_slugs)
        if slug not in missing_source_covers
        if (story_root / slug / TITLE_IMAGE_NAME).read_bytes()
        != (cover_root / f"{slug}.jpg").read_bytes()
    ]
    if stale_covers:
        problems.append(f"captured covers differ from story sources: {stale_covers}")
    if problems:
        raise ValueError("Repository inventory mismatch: " + "; ".join(problems))
    return len(source_slugs), len(catalog_slugs), sum(source_canon.values())


REPOSITORY_URL = "https://github.com/BoundlessStudio/story-computing-machine"
GITHUB_ICON = '''<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 2.29 6.64 5.47 7.71.4.08.55-.17.55-.39 0-.19-.01-.82-.01-1.49-2.01.44-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.59 1.23.83.72 1.23 1.87.88 2.33.67.07-.53.28-.88.51-1.08-1.78-.21-3.64-.9-3.64-4.01 0-.89.31-1.62.82-2.19-.08-.21-.36-1.04.08-2.16 0 0 .67-.22 2.2.84A7.45 7.45 0 0 1 8 3.92c.68 0 1.36.09 2 .28 1.53-1.06 2.2-.84 2.2-.84.44 1.12.16 1.95.08 2.16.51.57.82 1.3.82 2.19 0 3.12-1.87 3.8-3.65 4.01.29.25.54.73.54 1.49 0 1.07-.01 1.93-.01 2.2 0 .22.15.47.55.39A8.03 8.03 0 0 0 16 8.13C16 3.64 12.42 0 8 0Z"/></svg>'''
SUN_ICON = '''<svg class="theme-icon theme-icon-light" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v2.2M12 19.8V22M4.93 4.93l1.56 1.56M17.51 17.51l1.56 1.56M2 12h2.2M19.8 12H22M4.93 19.07l1.56-1.56M17.51 6.49l1.56-1.56"/></svg>'''
MOON_ICON = '''<svg class="theme-icon theme-icon-dark" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M20.2 15.2A8.5 8.5 0 0 1 8.8 3.8a8.5 8.5 0 1 0 11.4 11.4Z"/></svg>'''
THEME_BOOTSTRAP = '''<script>(function(){var key="story-computing-machine-theme",theme=null;try{theme=localStorage.getItem(key)}catch(error){}if(theme!=="light"&&theme!=="dark"){try{theme=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}catch(error){theme="light"}}document.documentElement.dataset.theme=theme;document.documentElement.style.colorScheme=theme}());</script>'''


def _page(
    title: str,
    body: str,
    library_href: str,
    timeline_href: str,
    stylesheet_href: str,
    theme_script_href: str,
    *,
    current: str | None = None,
    script_href: str | None = None,
) -> str:
    repository_link = f'<a class="repository-link" href="{REPOSITORY_URL}" aria-label="View BoundlessStudio/story-computing-machine on GitHub" title="View repository on GitHub">{GITHUB_ICON}</a>'
    theme_toggle = (
        '<button class="theme-toggle" type="button" data-theme-toggle '
        'aria-label="Toggle color theme" title="Toggle color theme">'
        f'{SUN_ICON}{MOON_ICON}'
        '<span class="theme-label" data-theme-label="light">Light</span>'
        '<span class="theme-label" data-theme-label="dark">Dark</span></button>'
    )
    library_current = ' aria-current="page"' if current == "library" else ""
    timeline_current = ' aria-current="page"' if current == "timeline" else ""
    header = (
        f'<header class="site-header"><a class="site-name" href="{library_href}">Story Computing Machine</a>'
        f'<nav class="site-nav" aria-label="Primary">'
        f'<a href="{library_href}"{library_current}>Library</a>'
        f'<a href="{timeline_href}"{timeline_current}>Chronology</a></nav>'
        f'<div class="site-actions">{theme_toggle}{repository_link}</div></header>'
    )
    theme_script = (
        f'<script src="{html.escape(theme_script_href, quote=True)}" defer></script>'
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
        '<meta name="color-scheme" content="light dark">'
        '<meta name="theme-color" content="#f5f0e7">'
        f'<title>{html.escape(title)}</title>'
        f'{THEME_BOOTSTRAP}'
        f'<link rel="stylesheet" href="{html.escape(stylesheet_href, quote=True)}">'
        f'{theme_script}{script}</head><body{body_class}>{header}<main>{body}</main></body></html>'
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
        "theme.js",
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
        "../theme.js",
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
                "perfumed-manners",
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
        f'</div><div class="signal-hero-graphic">{hero_artwork}</div></section>'
        '<nav class="signal-nav" aria-label="Timeline epochs">'
        f'<div class="signal-nav-epochs">{"".join(nav_links)}</div>'
        '<div class="signal-nav-tools"><button type="button" data-collapse-eras>Close era indexes</button></div>'
        '</nav>'
        '<div class="signal-legend" aria-label="Placement evidence legend">'
        '<strong>Placement evidence</strong>'
        '<span class="marker-fixed">Fixed anchor</span><span class="marker-inferred">Relative link</span>'
        '<span class="marker-speculative">Compatible candidate</span><span class="marker-unresolved">Working era fit</span>'
        '</div>'
        f'<div class="signal-worldline" id="worldline-sequence">{"".join(epoch_sections)}</div>'
        '<footer class="signal-continuation" aria-labelledby="signal-continuation-title">'
        '<div class="signal-continuation-mark" aria-hidden="true"><i></i></div>'
        '<div class="signal-continuation-copy">'
        '<p>Past the last plotted age</p>'
        '<h2 id="signal-continuation-title">The line goes on.</h2>'
        '<p>Every ending on this map becomes someone else’s deep history. Beyond the final marker, unnamed ages are already beginning.</p>'
        '<a href="index.html">Return to the story library <span aria-hidden="true">→</span></a>'
        '</div></footer>'
        '</div>'
    )
    return _page(
        "The Worldline — Story Chronology",
        body,
        "index.html",
        "timeline.html",
        "styles.css",
        "theme.js",
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
    shutil.copy2(STYLESHEET_PATH, destination / "styles.css")
    shutil.copy2(THEME_SCRIPT_PATH, destination / "theme.js")
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

    commands.add_parser("capture-all", help="Refresh every published story from its source package.")
    commands.add_parser("check", help="Validate publication and source inventory parity.")

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
        source_count, published_count, canon_count = validate_repository_inventory(
            catalog, timeline
        )
        print(
            f"PASS: {published_count} published stories, covers, and chronology placements; "
            f"{source_count} source packages ({canon_count} canon, "
            f"{source_count - canon_count} non-canon)"
        )


if __name__ == "__main__":
    main()
