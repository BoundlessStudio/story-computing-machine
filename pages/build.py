#!/usr/bin/env python3
"""Build the reader-facing story collection for GitHub Pages."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import markdown


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
ASSETS_ROOT = Path(__file__).resolve().parent
STORY_METADATA_FIELDS = {
    "schemaVersion",
    "slug",
    "title",
    "created",
    "stage",
    "status",
    "canon",
    "userDisposition",
    "publish",
    "promotionDate",
}
RELEASE_FIELDS = {
    "schemaVersion",
    "certified",
    "storySlug",
    "certifiedAt",
    "artifacts",
    "review",
    "nameCheck",
}
RELEASE_ARTIFACTS_FIELDS = {"story", "canonDelta"}
RELEASE_ARTIFACT_FIELDS = {"path", "sha256"}
RELEASE_REVIEW_FIELDS = {
    "artifact",
    "pass",
    "verdict",
    "reviewer",
    "unresolvedCritical",
    "unresolvedMajor",
}
RELEASE_NAME_CHECK_FIELDS = {
    "story",
    "passed",
    "checkedAt",
    "scopedRegistrySha256",
}
ALLOWED_STAGES = {
    "prompt",
    "canon-research",
    "planning",
    "drafting",
    "draft-review",
    "final-edit",
    "final-review",
    "candidate",
    "final",
    "abandoned",
}
ALLOWED_STATUSES = {"in-progress", "candidate", "final", "abandoned"}
PUBLISHABLE_STATUSES = {"candidate", "final"}
USER_DISPOSITIONS = {"pending", "accepted", "rejected"}
PLACEHOLDER_TEXT = "No reader-facing final story yet."
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
WORD_PATTERN = re.compile(r"\b[\w’'-]+\b", re.UNICODE)


@dataclass(frozen=True)
class StoryMetadata:
    title: str
    slug: str
    created: str
    stage: str
    status: str
    canon: bool
    user_disposition: str
    publish: bool
    promotion_date: str | None
    directory: Path


@dataclass(frozen=True)
class PublishedStory:
    metadata: StoryMetadata
    body: str
    word_count: int

    @property
    def title(self) -> str:
        return self.metadata.title

    @property
    def slug(self) -> str:
        return self.metadata.slug


@dataclass(frozen=True)
class Catalog:
    stories: tuple[PublishedStory, ...]

    @property
    def total_words(self) -> int:
        return sum(story.word_count for story in self.stories)


def parse_front_matter(content: str, path: Path) -> tuple[dict[str, object], str]:
    """Parse the deliberately small YAML subset used by story frontmatter."""
    lines = content.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: expected YAML frontmatter")

    try:
        closing_line = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValueError(f"{path}: frontmatter is not closed") from error

    metadata: dict[str, object] = {}
    for line_number, line in enumerate(lines[1:closing_line], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}:{line_number}: invalid frontmatter field")
        key, raw_value = line.split(":", maxsplit=1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty frontmatter key")
        if key in metadata:
            raise ValueError(f"{path}:{line_number}: duplicate frontmatter field {key!r}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            metadata[key] = value[1:-1]
        elif value.lower() in {"true", "false"}:
            metadata[key] = value.lower() == "true"
        elif value.lower() == "null":
            metadata[key] = None
        else:
            metadata[key] = value

    return metadata, "\n".join(lines[closing_line + 1 :]).strip()


def markdown_text(value: str) -> str:
    """Return a conservative plain-text representation for word counting."""
    value = re.sub(r"```.*?```", " ", value, flags=re.DOTALL)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"^[#>*+\-\d.\s]+", "", value, flags=re.MULTILINE)
    return re.sub(r"[*_~]", "", value)


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def require_exact_fields(
    value: dict[str, Any], expected: set[str], path: Path, context: str
) -> None:
    missing = expected - value.keys()
    extra = value.keys() - expected
    details = []
    if missing:
        details.append(f"missing {', '.join(sorted(missing))}")
    if extra:
        details.append(f"unknown {', '.join(sorted(extra))}")
    if details:
        raise ValueError(f"{path}: invalid {context} fields ({'; '.join(details)})")


def require_schema_version(value: object, path: Path) -> None:
    if type(value) is not int or value != 1:
        raise ValueError(f"{path}: schemaVersion must be 1")


def require_nonempty_text(value: object, path: Path, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {field} must be a non-empty string")
    return value.strip()


def require_slug(value: object, path: Path, field: str) -> str:
    slug = require_nonempty_text(value, path, field)
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(f"{path}: invalid {field} {slug!r}")
    return slug


def require_date(value: object, path: Path, field: str) -> str:
    text_value = require_nonempty_text(value, path, field)
    try:
        parsed = date.fromisoformat(text_value)
    except ValueError as error:
        raise ValueError(f"{path}: {field} must be an ISO date") from error
    if parsed.isoformat() != text_value:
        raise ValueError(f"{path}: {field} must use YYYY-MM-DD")
    return text_value


def require_utc_timestamp(value: object, path: Path, field: str) -> str:
    text_value = require_nonempty_text(value, path, field)
    try:
        parsed = datetime.fromisoformat(text_value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{path}: {field} must be an ISO-8601 UTC timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{path}: {field} must be an ISO-8601 UTC timestamp")
    return text_value


def require_digest(value: object, path: Path, field: str) -> str:
    if not isinstance(value, str) or not DIGEST_PATTERN.fullmatch(value):
        raise ValueError(f"{path}: {field} must be a lowercase SHA-256")
    return value


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ValueError(f"Cannot read {path}: {error}") from error


def load_story_metadata(story_directory: Path) -> StoryMetadata:
    metadata_file = story_directory / "story.json"
    if not metadata_file.is_file():
        raise ValueError(f"{story_directory}: missing required story.json")
    value = read_json_object(metadata_file)
    require_exact_fields(value, STORY_METADATA_FIELDS, metadata_file, "story metadata")
    require_schema_version(value["schemaVersion"], metadata_file)

    slug = require_slug(value["slug"], metadata_file, "slug")
    if slug != story_directory.name:
        raise ValueError(
            f"{metadata_file}: slug {slug!r} does not match its directory name"
        )
    title = require_nonempty_text(value["title"], metadata_file, "title")
    created = require_date(value["created"], metadata_file, "created")
    stage = require_nonempty_text(value["stage"], metadata_file, "stage")
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"{metadata_file}: unsupported stage {stage!r}")
    status = require_nonempty_text(value["status"], metadata_file, "status")
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"{metadata_file}: unsupported status {status!r}")
    canon = value["canon"]
    if not isinstance(canon, bool):
        raise ValueError(f"{metadata_file}: canon must be a boolean")
    user_disposition = require_nonempty_text(
        value["userDisposition"], metadata_file, "userDisposition"
    )
    if user_disposition not in USER_DISPOSITIONS:
        raise ValueError(
            f"{metadata_file}: unsupported userDisposition {user_disposition!r}"
        )
    publish = value["publish"]
    if not isinstance(publish, bool):
        raise ValueError(f"{metadata_file}: publish must be a boolean")
    promotion_date_value = value["promotionDate"]
    promotion_date = None
    if promotion_date_value is not None:
        promotion_date = require_date(
            promotion_date_value, metadata_file, "promotionDate"
        )

    if status == "in-progress":
        if (
            stage in {"candidate", "final", "abandoned"}
            or canon
            or user_disposition != "pending"
            or publish
            or promotion_date is not None
        ):
            raise ValueError(f"{metadata_file}: invalid in-progress lifecycle state")
    elif status == "candidate":
        if (
            stage != "candidate"
            or canon
            or user_disposition not in {"pending", "accepted"}
            or promotion_date is not None
        ):
            raise ValueError(f"{metadata_file}: invalid candidate lifecycle state")
    elif status == "final":
        if (
            stage != "final"
            or not canon
            or user_disposition != "accepted"
            or promotion_date is None
        ):
            raise ValueError(f"{metadata_file}: invalid final lifecycle state")
    elif status == "abandoned":
        if (
            stage != "abandoned"
            or canon
            or user_disposition != "rejected"
            or publish
            or promotion_date is not None
        ):
            raise ValueError(f"{metadata_file}: invalid abandoned lifecycle state")

    if publish and status not in PUBLISHABLE_STATUSES:
        raise ValueError(
            f"{metadata_file}: only candidate or final stories may be published"
        )

    return StoryMetadata(
        title=title,
        slug=slug,
        created=created,
        stage=stage,
        status=status,
        canon=canon,
        user_disposition=user_disposition,
        publish=publish,
        promotion_date=promotion_date,
        directory=story_directory,
    )


def load_final_artifact(metadata: StoryMetadata) -> tuple[str, int]:
    story_file = metadata.directory / "05-story.md"
    if not story_file.is_file():
        raise ValueError(f"{metadata.directory}: missing required 05-story.md")
    frontmatter, body = parse_front_matter(
        story_file.read_text(encoding="utf-8"), story_file
    )
    expected = {
        "title": metadata.title,
        "slug": metadata.slug,
        "created": metadata.created,
    }
    require_exact_fields(frontmatter, set(expected), story_file, "frontmatter")
    for field, expected_value in expected.items():
        if frontmatter[field] != expected_value:
            raise ValueError(
                f"{story_file}: {field} disagrees with story.json "
                f"({frontmatter[field]!r} != {expected_value!r})"
            )

    prose = markdown_text(body)
    return body, len(WORD_PATTERN.findall(prose))


def load_review_certification(metadata: StoryMetadata) -> dict[str, str]:
    review_file = metadata.directory / "04-review.md"
    if not review_file.is_file():
        raise ValueError(
            f"{metadata.directory}: published prose requires 04-review.md"
        )
    try:
        review_content = review_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"Cannot read {review_file}: {error}") from error
    section_match = re.search(
        r"(?ms)^## Current certification\s*\n(.*?)(?=^##\s+|\Z)",
        review_content,
    )
    if not section_match:
        raise ValueError(f"{review_file}: missing Current certification section")

    certification: dict[str, str] = {}
    for match in re.finditer(
        r"(?m)^-\s+([^:]+):\s*(.+?)\s*$", section_match.group(1)
    ):
        label = match.group(1).strip()
        if label in certification:
            raise ValueError(
                f"{review_file}: duplicate Current certification field {label!r}"
            )
        certification[label] = match.group(2).strip().replace("`", "")

    required = {
        "Reviewed artifact",
        "Artifact SHA-256",
        "Canon delta SHA-256",
        "Review pass",
        "Verdict",
        "Reviewer",
        "Unresolved Critical findings",
        "Unresolved Major findings",
    }
    missing = required - certification.keys()
    if missing:
        raise ValueError(
            f"{review_file}: Current certification missing "
            f"{', '.join(sorted(missing))}"
        )
    return certification


def require_review_binding(
    metadata: StoryMetadata, release: dict[str, Any]
) -> None:
    review_file = metadata.directory / "04-review.md"
    certification = load_review_certification(metadata)
    reviewed_artifact = certification["Reviewed artifact"].replace("\\", "/")
    if reviewed_artifact != "05-story.md" and not reviewed_artifact.endswith(
        f"/{metadata.slug}/05-story.md"
    ):
        raise ValueError(
            f"{review_file}: Current certification does not bind 05-story.md"
        )

    pass_match = re.fullmatch(r"(\d+)(?:\s.*)?", certification["Review pass"])
    if not pass_match:
        raise ValueError(f"{review_file}: Current certification pass is invalid")
    expected = {
        "Artifact SHA-256": release["artifacts"]["story"]["sha256"],
        "Canon delta SHA-256": release["artifacts"]["canonDelta"]["sha256"],
        "Review pass": release["review"]["pass"],
        "Verdict": release["review"]["verdict"],
        "Reviewer": release["review"]["reviewer"],
        "Unresolved Critical findings": release["review"]["unresolvedCritical"],
        "Unresolved Major findings": release["review"]["unresolvedMajor"],
    }
    actual_pass = int(pass_match.group(1))
    for field, expected_value in expected.items():
        actual_value: object = certification[field]
        if field == "Review pass":
            actual_value = actual_pass
        elif field in {
            "Unresolved Critical findings",
            "Unresolved Major findings",
        }:
            if not certification[field].isdigit():
                raise ValueError(
                    f"{review_file}: Current certification {field} must be an integer"
                )
            actual_value = int(certification[field])
        if actual_value != expected_value:
            raise ValueError(
                f"{review_file}: Current certification {field} "
                "does not match release.json"
            )


def require_release(metadata: StoryMetadata) -> None:
    release_file = metadata.directory / "release.json"
    if not release_file.is_file():
        raise ValueError(
            f"{metadata.directory}: published {metadata.status} prose requires release.json"
        )
    value = read_json_object(release_file)
    require_exact_fields(value, RELEASE_FIELDS, release_file, "release")
    require_schema_version(value["schemaVersion"], release_file)
    if value["certified"] is not True:
        raise ValueError(f"{release_file}: published prose must be certified")
    if value["storySlug"] != metadata.slug:
        raise ValueError(f"{release_file}: storySlug must be {metadata.slug!r}")
    require_utc_timestamp(value["certifiedAt"], release_file, "certifiedAt")

    artifacts = value["artifacts"]
    if not isinstance(artifacts, dict):
        raise ValueError(f"{release_file}: artifacts must be an object")
    require_exact_fields(
        artifacts, RELEASE_ARTIFACTS_FIELDS, release_file, "artifacts"
    )
    artifact_contracts = {
        "story": "05-story.md",
        "canonDelta": "06-canon-delta.md",
    }
    for key, artifact_name in artifact_contracts.items():
        artifact = artifacts[key]
        if not isinstance(artifact, dict):
            raise ValueError(f"{release_file}: artifacts.{key} must be an object")
        require_exact_fields(
            artifact,
            RELEASE_ARTIFACT_FIELDS,
            release_file,
            f"artifacts.{key}",
        )
        if artifact["path"] != artifact_name:
            raise ValueError(
                f"{release_file}: artifacts.{key}.path must be {artifact_name!r}"
            )
        expected_digest = require_digest(
            artifact["sha256"], release_file, f"artifacts.{key}.sha256"
        )
        artifact_path = metadata.directory / artifact_name
        actual_digest = sha256_file(artifact_path)
        if actual_digest != expected_digest:
            raise ValueError(
                f"{release_file}: {artifact_name} SHA-256 mismatch; "
                f"expected {expected_digest}, got {actual_digest}"
            )

    review = value["review"]
    if not isinstance(review, dict):
        raise ValueError(f"{release_file}: review must be an object")
    require_exact_fields(review, RELEASE_REVIEW_FIELDS, release_file, "review")
    if review["artifact"] != "05-story.md":
        raise ValueError(f"{release_file}: review.artifact must be '05-story.md'")
    if type(review["pass"]) is not int or review["pass"] < 1:
        raise ValueError(f"{release_file}: review.pass must be a positive integer")
    if review["verdict"] != "PASS":
        raise ValueError(f"{release_file}: review.verdict must be 'PASS'")
    require_nonempty_text(review["reviewer"], release_file, "review.reviewer")
    for field in ("unresolvedCritical", "unresolvedMajor"):
        if type(review[field]) is not int or review[field] != 0:
            raise ValueError(f"{release_file}: review.{field} must be 0")

    name_check = value["nameCheck"]
    if not isinstance(name_check, dict):
        raise ValueError(f"{release_file}: nameCheck must be an object")
    require_exact_fields(
        name_check, RELEASE_NAME_CHECK_FIELDS, release_file, "nameCheck"
    )
    if name_check["story"] != metadata.slug:
        raise ValueError(f"{release_file}: nameCheck.story must be {metadata.slug!r}")
    if name_check["passed"] is not True:
        raise ValueError(f"{release_file}: nameCheck.passed must be true")
    require_utc_timestamp(
        name_check["checkedAt"], release_file, "nameCheck.checkedAt"
    )
    require_digest(
        name_check["scopedRegistrySha256"],
        release_file,
        "nameCheck.scopedRegistrySha256",
    )
    require_review_binding(metadata, value)


def load_catalog(repository_root: Path = REPOSITORY_ROOT) -> Catalog:
    repository_root = repository_root.resolve()
    stories_root = repository_root / "stories"
    if not stories_root.is_dir():
        raise ValueError(f"{stories_root}: stories directory does not exist")

    published: list[PublishedStory] = []
    for story_directory in sorted(
        path
        for path in stories_root.iterdir()
        if path.is_dir() and not path.name.startswith(("_", "."))
    ):
        metadata = load_story_metadata(story_directory)
        if not metadata.publish:
            continue
        require_release(metadata)
        body, word_count = load_final_artifact(metadata)
        if PLACEHOLDER_TEXT in body:
            raise ValueError(
                f"{story_directory / '05-story.md'}: published story contains the placeholder"
            )
        if word_count < 100:
            raise ValueError(
                f"{story_directory / '05-story.md'}: published story has only "
                f"{word_count} words"
            )
        published.append(
            PublishedStory(
                metadata=metadata,
                body=body,
                word_count=word_count,
            )
        )

    if not published:
        raise ValueError("No published stories were found")
    return Catalog(
        stories=tuple(sorted(published, key=lambda story: story.title.casefold()))
    )


def page_template(
    *,
    title: str,
    description: str,
    stylesheet: str,
    content: str,
    body_class: str,
) -> str:
    safe_title = html.escape(title)
    safe_description = html.escape(description, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{safe_description}">
  <title>{safe_title}</title>
  <link rel="stylesheet" href="{stylesheet}">
</head>
<body class="{body_class}">
{content}
</body>
</html>
"""


def status_label(status: str) -> str:
    return status.replace("-", " ").title()


def render_story_card(story: PublishedStory) -> str:
    canon_label = "Canon" if story.metadata.canon else "Not canon"
    return f"""      <li class="story-card">
        <a class="story-link" href="stories/{html.escape(story.slug)}/">
          <span class="story-title">{html.escape(story.title)}</span>
          <span class="story-meta">
            <span class="status status-{html.escape(story.metadata.status)}">{html.escape(status_label(story.metadata.status))}</span>
            <span>{story.word_count:,} words</span>
            <span>{canon_label}</span>
          </span>
        </a>
      </li>"""


def render_index(catalog: Catalog) -> str:
    cards = "\n".join(render_story_card(story) for story in catalog.stories)
    content = f"""  <header class="site-header">
    <a class="site-name" href="./">Story Computing Machine</a>
    <a class="repository-link" href="https://github.com/BoundlessStudio/story-computing-machine" aria-label="View this project on GitHub" title="View this project on GitHub">
      <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">
        <path d="M8 0C3.58 0 0 3.64 0 8.13c0 3.59 2.29 6.64 5.47 7.71.4.08.55-.17.55-.39 0-.19-.01-.82-.01-1.49-2.01.44-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.59 1.23.83.72 1.23 1.87.88 2.33.67.07-.53.28-.88.51-1.08-1.78-.21-3.64-.9-3.64-4.01 0-.89.31-1.62.82-2.19-.08-.21-.36-1.04.08-2.16 0 0 .67-.22 2.2.84A7.45 7.45 0 0 1 8 3.92c.68 0 1.36.09 2 .28 1.53-1.06 2.2-.84 2.2-.84.44 1.12.16 1.95.08 2.16.51.57.82 1.3.82 2.19 0 3.12-1.87 3.8-3.65 4.01.29.25.54.73.54 1.49 0 1.07-.01 1.93-.01 2.2 0 .22.15.47.55.39A8.03 8.03 0 0 0 16 8.13C16 3.64 12.42 0 8 0Z"/>
      </svg>
    </a>
  </header>
  <main class="library">
    <p class="eyebrow">Shared-universe fiction</p>
    <h1>Short stories</h1>
    <p class="lede">Reader-facing stories from the Boundless shared universe.</p>
    <p class="collection-count">{len(catalog.stories)} reader-ready stories · {catalog.total_words:,} words</p>
    <section class="collection-section" aria-labelledby="stories-heading">
      <h2 id="stories-heading">Reader-ready stories</h2>
      <ul class="story-grid">
{cards}
      </ul>
    </section>
  </main>"""
    return page_template(
        title="Story Computing Machine",
        description="Short stories from the Boundless shared universe.",
        stylesheet="assets/styles.css",
        content=content,
        body_class="index-page",
    )


def markdown_to_html(body: str) -> str:
    return markdown.markdown(
        body,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )


def render_story(story: PublishedStory) -> str:
    canon_label = "Canon" if story.metadata.canon else "Not canon"
    content = f"""  <header class="site-header">
    <a class="site-name" href="../../">← All stories</a>
  </header>
  <main>
    <article class="story">
      <p class="story-page-meta">
        <span class="status status-{html.escape(story.metadata.status)}">{html.escape(status_label(story.metadata.status))}</span>
        <span>{story.word_count:,} words</span>
        <span>{canon_label}</span>
      </p>
{markdown_to_html(story.body)}
    </article>
  </main>
  <footer class="site-footer">
    <p><a href="../../">Return to the story index</a></p>
  </footer>"""
    return page_template(
        title=f"{story.title} · Story Computing Machine",
        description=(
            f"Read {story.title}, a short story from the Boundless shared universe."
        ),
        stylesheet="../../assets/styles.css",
        content=content,
        body_class="story-page",
    )


def prepare_output(output: Path, repository_root: Path) -> Path:
    output = output.resolve()
    try:
        relative_output = output.relative_to(repository_root.resolve())
    except ValueError as error:
        raise ValueError("Output directory must be inside the repository") from error
    if not relative_output.parts or not relative_output.parts[0].startswith("_site"):
        raise ValueError(f"Refusing unsafe output directory: {output}")
    if output.exists():
        if output.is_symlink():
            raise ValueError(f"Refusing to replace symlinked output directory: {output}")
        if not output.is_dir():
            raise ValueError(f"Output path is not a directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def build(
    output: Path,
    repository_root: Path = REPOSITORY_ROOT,
    assets_root: Path = ASSETS_ROOT,
) -> Catalog:
    repository_root = repository_root.resolve()
    catalog = load_catalog(repository_root)
    output = prepare_output(output, repository_root)

    (output / "index.html").write_text(render_index(catalog), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")

    assets_output = output / "assets"
    assets_output.mkdir()
    shutil.copy2(assets_root / "styles.css", assets_output / "styles.css")

    for story in catalog.stories:
        story_output = output / "stories" / story.slug
        story_output.mkdir(parents=True)
        (story_output / "index.html").write_text(
            render_story(story), encoding="utf-8"
        )

    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "_site",
        help="Site output directory (must be inside the repository)",
    )
    args = parser.parse_args()

    catalog = build(args.output)
    print(
        f"Built {len(catalog.stories)} reader-ready story pages in "
        f"{args.output.resolve()} ({catalog.total_words:,} words)."
    )


if __name__ == "__main__":
    main()
