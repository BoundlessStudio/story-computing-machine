from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import markdown

if __package__:
    from .image_validation import (
        TITLE_IMAGE_WIDTH, TITLE_IMAGE_HEIGHT, validate_title_image as _validate_title_image,
    )
else:
    from image_validation import (
        TITLE_IMAGE_WIDTH, TITLE_IMAGE_HEIGHT, validate_title_image as _validate_title_image,
    )

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = Path(__file__).with_name("catalog.json")
STYLESHEET_PATH = Path(__file__).with_name("styles.css")
THEME_SCRIPT_PATH = Path(__file__).with_name("theme.js")
TIMELINE_PATH = Path(__file__).with_name("timeline.json")
TIMELINE_SCRIPT_PATH = Path(__file__).with_name("timeline.js")
WORLDLINE_HERO_ART_PATH = Path(__file__).with_name("worldline-hero-art.webp")
TITLE_IMAGE_NAME = "title-image.jpg"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RATINGS = frozenset({"PG", "YA", "R+"})
TIMELINE_EVIDENCE = frozenset({"boundary", "constrained", "relative", "contextual", "undated"})
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
class TimelineSpan:
    start: str
    end: str
    note: str


@dataclass(frozen=True)
class TimelineWindow:
    start: float
    end: float


@dataclass(frozen=True)
class TimelineEra:
    id: str
    title: str
    description: str
    context: tuple[str, ...]
    sequence_note: str
    stories: tuple[str, ...]
    window: TimelineWindow


@dataclass(frozen=True)
class TimelineCycle:
    id: str
    title: str
    eyebrow: str
    magic_state: str
    description: str
    sequence_note: str
    eras: tuple[TimelineEra, ...]

    @property
    def stories(self) -> tuple[str, ...]:
        return tuple(slug for era in self.eras for slug in era.stories)


@dataclass(frozen=True)
class TimelineConnection:
    id: str
    source: str
    target: str
    kind: str
    label: str
    note: str
    ordering: str
    basis: str


@dataclass(frozen=True)
class TimelinePlacement:
    window: TimelineWindow
    note: str


@dataclass(frozen=True)
class Timeline:
    cycles: tuple[TimelineCycle, ...]
    story_placements: dict[str, TimelinePlacement]
    story_moments: dict[str, tuple[str, ...]]
    story_spans: dict[str, TimelineSpan]
    story_evidence: dict[str, str]
    connections: tuple[TimelineConnection, ...]


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

    source = match.group("prompt").strip()
    wp_marker = re.search(r"\[?WP\]", source, flags=re.IGNORECASE)
    if wp_marker is not None:
        source = source[wp_marker.end() :]
        paragraph_end = re.search(r"\n(?:[ \t]*>[ \t]*)?\n", source)
        if paragraph_end is not None:
            source = source[: paragraph_end.start()]

    lines = []
    for line in source.splitlines():
        cleaned = re.sub(r"^\s*>\s?", "", line).strip()
        if cleaned:
            lines.append(cleaned)
    prompt = re.sub(r"\*\*", "", " ".join(lines)).strip()
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


def _review_problems(review: str, profile: str | None) -> list[str]:
    """Read declarations only; prose, names, and craft still need independent review."""
    review = review.replace("\r\n", "\n").replace("\r", "\n")
    rules = {
        "Verdict": (None, {"PASS"}),
        "Prompt": ("Continuity", {"PASS"}),
        "Universe": ("Continuity", {"PASS"}),
        "Internal": ("Continuity", {"PASS"}),
        "Blocking": ("Findings", {"none"}),
    }
    dialogue_required = profile in {
        "prospective-2026-08-18", "prospective-2026-08-21", "prospective-2026-08-23",
    }
    # Older profiles need no Dialogue field, but an explicit failure is never PASS.
    if dialogue_required or re.search(r"(?m)^-[ \t]+Dialogue:", review):
        rules["Dialogue"] = ("Craft", {"PASS", "N/A"})
    problems = []
    for label, (section, allowed) in rules.items():
        prefix = "" if label == "Verdict" else r"-[ \t]+"
        pattern = rf"(?m)^{prefix}{label}:[ \t]*(?P<value>[^\n]*?)[ \t]*$"
        declarations = list(re.finditer(pattern, review))
        if len(declarations) != 1:
            problems.append(f"{label} must have exactly one declaration")
            continue
        if declarations[0]["value"] not in allowed:
            problems.append(f"{label} must be {' or '.join(sorted(allowed))}")
        if section is None:
            body = re.split(r"(?m)^##[ \t]+", review, maxsplit=1)[0]
        else:
            sections = list(re.finditer(
                rf"(?ms)^##[ \t]+{section}[ \t]*\n(?P<body>.*?)(?=^##[ \t]+|\Z)",
                review,
            ))
            if len(sections) != 1:
                problems.append(f"{label} requires exactly one {section} section")
                continue
            body = sections[0]["body"]
        if len(re.findall(pattern, body)) != 1:
            problems.append(f"{label} is outside its required section")
    return problems


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
    prompt_path = directory / "prompt.md"
    prompt_source = prompt_path.read_text(encoding="utf-8")
    profiles = re.findall(r"(?m)^-[ \t]+Craft profile:[ \t]*([^\r\n]+)", prompt_source)
    profile = profiles[-1].strip() if profiles else None
    problems = _review_problems(review, profile)
    if problems:
        raise ValueError(f"{review_path} is not a passing review: {'; '.join(problems)}")

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


def _timeline_window(value: Any, label: str) -> TimelineWindow:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    require_exact_fields(value, {"start", "end"}, label)
    start, end = value["start"], value["end"]
    if any(isinstance(number, bool) or not isinstance(number, (int, float))
           or not math.isfinite(number) for number in (start, end)):
        raise ValueError(f"{label} bounds must be finite numbers")
    if not 0 <= start < end <= 100:
        raise ValueError(f"{label} must have 0 <= start < end <= 100")
    return TimelineWindow(float(start), float(end))


def _validate_timeline_order(cycles, placements, connections):
    """Check a partial order against possible horizons, without dating peers."""
    locations = {slug: index for index, cycle in enumerate(cycles) for slug in cycle.stories}
    successors = {slug: set() for slug in placements}
    incoming = {slug: 0 for slug in placements}
    earliest = {slug: locations[slug] * 100 + place.window.start for slug, place in placements.items()}
    latest = {slug: locations[slug] * 100 + place.window.end for slug, place in placements.items()}
    state_order = {"old-magic": 0, "long-dark": 1, "new-magic": 2}
    states = [state_order[cycle.magic_state] for cycle in cycles if cycle.magic_state in state_order]
    if states != sorted(states):
        raise ValueError("Worldline history must preserve old magic, Long Dark, then new magic")

    # These magical histories were already admitted when the terminal boundary
    # was locked on 2026-08-24. Their unresolved local dates permit contextual
    # movement, but do not place them after that boundary. Later admissions
    # explicitly leaving old/new open are not covered by this constraint.
    for slug in ("the-last-bus-to-briar-hill", "the-trouble-with-tuesdays",
                 "self-reflection", "the-wrong-side-of-the-part",
                 "transitions-in-common", "a-place-for-the-living",
                 "the-warmest-person-in-the-room", "realms"):
        if slug in locations and cycles[locations[slug]].magic_state != "old-magic":
            raise ValueError(f"Established magical history {slug} must precede the old magic extinction")

    def precedes(source, target):
        if target not in successors[source]:
            successors[source].add(target)
            incoming[target] += 1

    for link in connections:
        if link.ordering == "before":
            precedes(link.source, link.target)
    # The material frames respect the two boundaries even without individual
    # connection cards repeating the same worldline rule for every story.
    for anchor, state, closes in (("all-accounts-due", "old-magic", True),
                                  ("the-sky-remembers-us-return", "new-magic", False)):
        if anchor not in locations:
            continue
        if cycles[locations[anchor]].magic_state != state:
            raise ValueError(f"Worldline boundary {anchor} has the wrong magic state")
        for cycle in cycles:
            if cycle.magic_state == state:
                for slug in cycle.stories:
                    if slug != anchor:
                        precedes(slug, anchor) if closes else precedes(anchor, slug)
    ready = [slug for slug, degree in incoming.items() if degree == 0]
    visited = 0
    while ready:
        source = ready.pop()
        visited += 1
        if earliest[source] >= latest[source]:
            raise ValueError(f"Chronological connection contradicts the proposed window for {source}")
        for target in successors[source]:
            earliest[target] = max(earliest[target], earliest[source])
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)
    if visited != len(placements):
        raise ValueError("Chronological connections contain a cycle")


def load_timeline(catalog: Catalog, path: Path = TIMELINE_PATH) -> Timeline:
    value = read_json_object(path)
    require_exact_fields(value, {
        "schemaVersion", "cycles", "storyPlacements", "storyMoments",
        "storySpans", "storyEvidence", "connections",
    }, str(path))
    if value["schemaVersion"] != 7:
        raise ValueError(f"Unsupported timeline snapshot in {path}")
    for key in ("storyPlacements", "storyMoments", "storySpans", "storyEvidence"):
        if not isinstance(value[key], dict):
            raise ValueError(f"{key} must be an object")
    known = {story.slug for story in catalog.stories}
    for key in ("storyPlacements", "storyEvidence"):
        if set(value[key]) != known:
            raise ValueError(f"{key} must cover every published story exactly once")

    placements: dict[str, TimelinePlacement] = {}
    for slug, item in value["storyPlacements"].items():
        if not isinstance(item, dict):
            raise ValueError(f"Placement for {slug} must be an object")
        require_exact_fields(item, {"window", "note"}, f"Placement for {slug}")
        placements[slug] = TimelinePlacement(_timeline_window(item["window"], f"Placement window for {slug}"),
                                            _timeline_text(item["note"], f"Placement note for {slug}"))

    if not isinstance(value["cycles"], list) or not value["cycles"]:
        raise ValueError("Timeline cycles must be a non-empty list")
    cycles: list[TimelineCycle] = []
    cycle_ids: set[str] = set()
    era_ids: set[str] = set()
    assigned: set[str] = set()
    for item in value["cycles"]:
        if not isinstance(item, dict):
            raise ValueError("Timeline cycle must be an object")
        require_exact_fields(item, {"id", "title", "eyebrow", "magicState", "description", "sequenceNote", "eras"}, "Timeline cycle")
        cycle_id = _timeline_text(item["id"], "Cycle id")
        if not SLUG.fullmatch(cycle_id) or cycle_id in cycle_ids:
            raise ValueError("Timeline cycle has an invalid or duplicate id")
        state = _timeline_text(item["magicState"], "Cycle magic state")
        if state not in TIMELINE_MAGIC_STATES:
            raise ValueError("Timeline cycle has an unsupported magic state")
        if not isinstance(item["eras"], list) or not item["eras"]:
            raise ValueError("Cycle eras must be a non-empty list")
        eras = []
        for era in item["eras"]:
            if not isinstance(era, dict):
                raise ValueError("Timeline era must be an object")
            require_exact_fields(era, {"id", "title", "description", "context", "sequenceNote", "stories", "window"}, "Timeline era")
            era_id = _timeline_text(era["id"], "Era id")
            if not SLUG.fullmatch(era_id) or era_id in era_ids:
                raise ValueError("Timeline era has an invalid or duplicate id")
            era_slugs = _timeline_story_slugs(era["stories"], "Era stories")
            if not era_slugs or set(era_slugs) - known:
                raise ValueError("Era stories must be known and non-empty")
            if set(era_slugs) & assigned:
                raise ValueError("Era repeats already placed stories")
            if not isinstance(era["context"], list) or not 2 <= len(era["context"]) <= 4:
                raise ValueError("Era context must give two to four historical observations")
            context = tuple(_timeline_text(observation, "Era context") for observation in era["context"])
            window = _timeline_window(era["window"], f"Era window for {era_id}")
            for slug in era_slugs:
                if not window.start <= placements[slug].window.start < placements[slug].window.end <= window.end:
                    raise ValueError(f"Story window for {slug} lies outside its era")
            eras.append(TimelineEra(
                era_id, _timeline_text(era["title"], "Era title"),
                _timeline_text(era["description"], "Era description"), context,
                _timeline_text(era["sequenceNote"], "Era sequenceNote"), era_slugs, window,
            ))
            era_ids.add(era_id)
            assigned.update(era_slugs)
        cycles.append(TimelineCycle(
            cycle_id, _timeline_text(item["title"], "Cycle title"),
            _timeline_text(item["eyebrow"], "Cycle eyebrow"), state,
            _timeline_text(item["description"], "Cycle description"),
            _timeline_text(item["sequenceNote"], "Cycle sequenceNote"), tuple(eras),
        ))
        cycle_ids.add(cycle_id)
    if assigned != known:
        raise ValueError(f"Chronology is missing published stories: {sorted(known - assigned)}")

    evidence = {}
    for slug, level in value["storyEvidence"].items():
        if not isinstance(level, str) or level not in TIMELINE_EVIDENCE:
            raise ValueError(f"storyEvidence for {slug} is unsupported")
        evidence[slug] = level
    moments = {}
    for slug, labels in value["storyMoments"].items():
        if slug not in known:
            raise ValueError(f"storyMoments references unknown story {slug}")
        if not isinstance(labels, list) or not labels or len(labels) > 8:
            raise ValueError(f"storyMoments for {slug} must contain one to eight labels")
        moments[slug] = tuple(_timeline_text(label, f"Moment for {slug}") for label in labels)
    spans = {}
    for slug, span in value["storySpans"].items():
        if slug not in known or not isinstance(span, dict):
            raise ValueError(f"Invalid storySpans entry for {slug}")
        require_exact_fields(span, {"start", "end", "note"}, f"storySpans for {slug}")
        spans[slug] = TimelineSpan(*(_timeline_text(span[key], f"Span {key} for {slug}") for key in ("start", "end", "note")))

    if not isinstance(value["connections"], list):
        raise ValueError("Timeline connections must be a list")
    connections = []
    connection_ids: set[str] = set()
    connection_pairs: set[tuple[str, str, str]] = set()
    for item in value["connections"]:
        if not isinstance(item, dict):
            raise ValueError("Timeline connection must be an object")
        require_exact_fields(item, {"id", "from", "to", "kind", "label", "note", "ordering", "basis"}, "Timeline connection")
        connection_id = _timeline_text(item["id"], "Connection id")
        source = _timeline_text(item["from"], "Connection source")
        target = _timeline_text(item["to"], "Connection target")
        kind = _timeline_text(item["kind"], "Connection kind")
        if not SLUG.fullmatch(connection_id) or connection_id in connection_ids:
            raise ValueError("Timeline connection has an invalid or duplicate id")
        if source not in known or target not in known or source == target:
            raise ValueError("Connection endpoints must be different published stories")
        if kind not in {"direct", "echo", "historical"}:
            raise ValueError("Connection kind must be direct, historical or echo")
        ordering = _timeline_text(item["ordering"], "Connection ordering")
        basis = _timeline_text(item["basis"], "Connection basis")
        if ordering not in {"before", "none"}:
            raise ValueError("Connection ordering must be before or none")
        allowed_basis = {"direct": {"established", "reading-sequence"},
                         "historical": {"proposed"}, "echo": {"thematic"}}
        if basis not in allowed_basis[kind] or (kind == "echo" and ordering != "none"):
            raise ValueError("Connection basis and ordering must match its kind")
        pair = (min(source, target), max(source, target), kind)
        if pair in connection_pairs:
            raise ValueError("Timeline connection repeats a story pair")
        connections.append(TimelineConnection(connection_id, source, target, kind,
            _timeline_text(item["label"], "Connection label"),
            _timeline_text(item["note"], "Connection note"), ordering, basis))
        connection_ids.add(connection_id)
        connection_pairs.add(pair)
    _validate_timeline_order(cycles, placements, connections)
    return Timeline(tuple(cycles), placements, moments, spans, evidence, tuple(connections))


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
    previous = next((item for item in published.stories if item.slug == slug), None)
    if previous is not None:
        story = replace(story, prompt=previous.prompt)
    _capture_cover(story, repository_root, snapshot_path)
    remaining = (item for item in published.stories if item.slug != story.slug)
    return save_catalog((story, *remaining), snapshot_path)


def capture_all(
    repository_root: Path = REPOSITORY_ROOT,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> Catalog:
    published = load_catalog(snapshot_path)
    stories = tuple(
        replace(load_story_source(story.slug, repository_root), prompt=story.prompt)
        for story in published.stories
    )
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
    placements = [slug for cycle in timeline.cycles for slug in cycle.stories]
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
    atlas_styles = '<link rel="stylesheet" href="atlas.css">' if current == "timeline" else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light dark">'
        '<meta name="theme-color" content="#f5f0e7">'
        f'<title>{html.escape(title)}</title>'
        f'{THEME_BOOTSTRAP}'
        f'<link rel="stylesheet" href="{html.escape(stylesheet_href, quote=True)}">'
        f'{atlas_styles}{theme_script}{script}</head><body{body_class}>{header}<main>{body}</main></body></html>'
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


def render_timeline(catalog: Catalog, timeline: Timeline) -> str:
    if __package__:
        from .atlas import render
    else:
        from atlas import render
    return _page(
        "The Worldline — A Chronology of One World", render(catalog, timeline),
        "index.html", "timeline.html", "styles.css", "theme.js",
        current="timeline", script_href="timeline.js",
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
    shutil.copy2(Path(__file__).with_name("atlas.css"), destination / "atlas.css")
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
