"""Refresh the source-cover inventory for this study without touching story packages."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from PIL import Image


STUDY_DIR = Path(__file__).resolve().parent
REPO_ROOT = STUDY_DIR.parents[1]
STORIES_DIR = REPO_ROOT / "stories"
MANIFEST_PATH = STUDY_DIR / "manifest.json"


def read_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError(f"Missing YAML frontmatter: {path}")
    values = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return values


def parse_title(raw: str) -> str:
    if raw.startswith('"'):
        return json.loads(raw)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    return raw


def source_metadata(package: Path) -> tuple[str, str, bool]:
    story_md = package / "story.md"
    story_json = package / "story.json"
    if story_md.exists():
        values = read_frontmatter(story_md)
        title = parse_title(values["title"])
        canon_value = values["canon"].lower()
        if canon_value not in {"true", "false"}:
            raise ValueError(f"Unclear canon marker in {story_md}: {canon_value}")
        return story_md.relative_to(REPO_ROOT).as_posix(), title, canon_value == "true"
    if story_json.exists():
        values = json.loads(story_json.read_text(encoding="utf-8-sig"))
        if not isinstance(values.get("canon"), bool):
            raise ValueError(f"Unclear canon marker in {story_json}")
        return story_json.relative_to(REPO_ROOT).as_posix(), values["title"], values["canon"]
    raise ValueError(f"No authoritative canon marker in {package}")


def main() -> None:
    previous_entries = {}
    if MANIFEST_PATH.exists():
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        previous_entries = {entry["slug"]: entry for entry in previous.get("entries", [])}
    review_fields = {"candidate_path", "style_status", "style_reason", "style_confidence",
                     "detail_class", "candidate_status", "candidate_notes"}
    entries = []
    for cover in sorted(STORIES_DIR.glob("*/title-image.jpg")):
        package = cover.parent
        story_path, title, canon = source_metadata(package)
        with Image.open(cover) as image:
            if image.format != "JPEG":
                raise ValueError(f"Unexpected image format: {cover}")
            width, height = image.size
        entry = {
                "slug": package.name,
                "title": title,
                "story_path": story_path,
                "canon": canon,
                "source_cover_path": cover.relative_to(REPO_ROOT).as_posix(),
                "source_width": width,
                "source_height": height,
                "source_bytes": cover.stat().st_size,
                "candidate_path": (
                    f"studies/cover-style-2026-09-28/candidates/{package.name}/painted-v1.jpg"
                ),
            }
        entry.update({key: value for key, value in previous_entries.get(package.name, {}).items()
                      if key in review_fields})
        entries.append(entry)

    if len(entries) != 200 or len({entry["slug"] for entry in entries}) != len(entries):
        raise ValueError(f"Unexpected cover inventory: {len(entries)} entries")

    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()
    manifest = {
        "schema_version": 1,
        "source_commit": source_commit,
        "source_count": len(entries),
        "candidate_policy": "Study outputs only; no story package is changed.",
        "entries": entries,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
