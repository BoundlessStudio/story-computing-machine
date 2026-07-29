#!/usr/bin/env python3
"""Build the reader-facing story collection for GitHub Pages."""

from __future__ import annotations

import argparse
import html
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import markdown


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
STORIES_ROOT = REPOSITORY_ROOT / "stories"
ASSETS_ROOT = Path(__file__).resolve().parent
PUBLISHABLE_STATUSES = {"candidate", "final", "abandoned", "apocrypha"}
PLACEHOLDER_TEXT = "No reader-facing final story yet."
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WORD_PATTERN = re.compile(r"\b[\w’'-]+\b", re.UNICODE)


@dataclass(frozen=True)
class Story:
    title: str
    slug: str
    status: str
    canon: bool
    body: str | None
    word_count: int
    prompt: str | None
    legacy_source_form: str | None

    @property
    def is_readable(self) -> bool:
        return self.body is not None

    @property
    def is_legacy_seed(self) -> bool:
        return self.body is None and self.legacy_source_form is not None


def parse_front_matter(source: str, path: Path) -> tuple[dict[str, object], str]:
    """Parse the deliberately small YAML subset used by story front matter."""
    lines = source.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: expected YAML front matter")

    try:
        closing_line = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration as error:
        raise ValueError(f"{path}: front matter is not closed") from error

    metadata: dict[str, object] = {}
    for line_number, line in enumerate(lines[1:closing_line], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}:{line_number}: invalid front matter field")
        key, raw_value = line.split(":", maxsplit=1)
        key = key.strip()
        value = raw_value.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty front matter key")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if value.lower() in {"true", "false"}:
            metadata[key] = value.lower() == "true"
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


def parse_prompt_contract(story_directory: Path) -> tuple[str | None, str | None]:
    """Extract an actual [WP] and selected legacy-seed metadata, when present."""
    prompt_file = story_directory / "00-prompt.md"
    if not prompt_file.is_file():
        return None, None

    source = prompt_file.read_text(encoding="utf-8")
    prompt_match = re.search(
        r"^## Verbatim writing prompt\s*(?P<prompt>.*?)(?=^## |\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    writing_prompt = None
    if prompt_match:
        prompt_lines = []
        for line in prompt_match.group("prompt").strip().splitlines():
            cleaned_line = re.sub(r"^\s*>\s?", "", line).strip()
            if cleaned_line:
                prompt_lines.append(cleaned_line)
        prompt_text = re.sub(r"\*\*", "", " ".join(prompt_lines)).strip()
        if prompt_text.startswith("[WP]"):
            writing_prompt = prompt_text.removeprefix("[WP]").strip()

    legacy_source_form = None
    if re.search(r"(?m)^- Imported seed:\s+legacy source\b", source):
        source_form_match = re.search(r"(?m)^- Source form:\s*(.+?)\s*$", source)
        if source_form_match:
            legacy_source_form = source_form_match.group(1).strip()

    return writing_prompt, legacy_source_form


def load_stories() -> list[Story]:
    stories: list[Story] = []
    for story_file in sorted(STORIES_ROOT.glob("*/05-story.md")):
        if story_file.parent.name.startswith("_"):
            continue

        metadata, body = parse_front_matter(
            story_file.read_text(encoding="utf-8"), story_file
        )
        missing = {"title", "slug", "status", "canon"} - metadata.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"{story_file}: missing front matter field(s): {fields}")

        title = str(metadata["title"]).strip()
        slug = str(metadata["slug"]).strip()
        status = str(metadata["status"]).strip().lower()
        canon = metadata["canon"]
        writing_prompt, legacy_source_form = parse_prompt_contract(story_file.parent)

        if not title:
            raise ValueError(f"{story_file}: title cannot be empty")
        if not SLUG_PATTERN.fullmatch(slug):
            raise ValueError(f"{story_file}: invalid slug {slug!r}")
        if slug != story_file.parent.name:
            raise ValueError(
                f"{story_file}: slug {slug!r} does not match its directory name"
            )
        if not isinstance(canon, bool):
            raise ValueError(f"{story_file}: canon must be true or false")

        if status in PUBLISHABLE_STATUSES:
            if PLACEHOLDER_TEXT in body:
                raise ValueError(
                    f"{story_file}: publishable story still contains the placeholder"
                )
            prose = markdown_text(body)
            word_count = len(WORD_PATTERN.findall(prose))
            if word_count < 100:
                raise ValueError(
                    f"{story_file}: publishable story has only {word_count} words"
                )
            story_body: str | None = body
        elif legacy_source_form:
            story_body = None
            word_count = 0
        else:
            continue

        stories.append(
            Story(
                title=title,
                slug=slug,
                status=status,
                canon=canon,
                body=story_body,
                word_count=word_count,
                prompt=writing_prompt,
                legacy_source_form=legacy_source_form,
            )
        )

    if not any(story.is_readable for story in stories):
        raise ValueError("No publishable stories were found")
    return sorted(stories, key=lambda story: story.title.casefold())


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


def render_readable_card(story: Story) -> str:
    canon_label = "Canon" if story.canon else "Not canon"
    prompt = ""
    if story.prompt:
        prompt = f"""
          <span class="story-prompt">
            <span class="story-prompt-text">{html.escape(story.prompt)}</span>
          </span>"""
    return f"""      <li class="story-card">
        <a class="story-link" href="stories/{html.escape(story.slug)}/">
          <span class="story-title">{html.escape(story.title)}</span>{prompt}
          <span class="story-meta">
            <span class="status status-{html.escape(story.status)}">{html.escape(status_label(story.status))}</span>
            <span>{story.word_count:,} words</span>
            <span>{canon_label}</span>
          </span>
        </a>
      </li>"""


def render_legacy_card(story: Story) -> str:
    canon_label = "Canon" if story.canon else "Not canon"
    return f"""      <li class="story-card">
        <article class="story-link story-link-static">
          <span class="story-title">{html.escape(story.title)}</span>
          <span class="legacy-description">
            Selected legacy seed: {html.escape(story.legacy_source_form or "historical source")}.
          </span>
          <span class="story-meta">
            <span class="status status-legacy">Legacy seed</span>
            <span>In development</span>
            <span>{canon_label}</span>
          </span>
        </article>
      </li>"""


def render_index(stories: list[Story]) -> str:
    readable_stories = [story for story in stories if story.is_readable]
    legacy_stories = [story for story in stories if story.is_legacy_seed]
    cards = []
    for story in readable_stories:
        cards.append(render_readable_card(story))
    legacy_cards = []
    for story in legacy_stories:
        legacy_cards.append(render_legacy_card(story))

    total_words = sum(story.word_count for story in readable_stories)
    legacy_section = ""
    if legacy_cards:
        legacy_section = f"""
    <section class="collection-section legacy-section" aria-labelledby="legacy-heading">
      <h2 id="legacy-heading">Legacy seeds</h2>
      <p class="section-intro">Selected historical stories and outlines retained for future adaptation. These entries are in development and are not canon.</p>
      <ul class="story-grid">
{chr(10).join(legacy_cards)}
      </ul>
    </section>"""
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
    <p class="collection-count">{len(readable_stories)} readable stories · {len(legacy_stories)} legacy seeds · {total_words:,} words</p>
    <section class="collection-section" aria-labelledby="stories-heading">
      <h2 id="stories-heading">Reader-ready stories</h2>
      <ul class="story-grid">
{chr(10).join(cards)}
      </ul>
    </section>{legacy_section}
  </main>"""
    return page_template(
        title="Story Computing Machine",
        description="Short stories from the Boundless shared universe.",
        stylesheet="assets/styles.css",
        content=content,
        body_class="index-page",
    )


def render_story(story: Story) -> str:
    if story.body is None:
        raise ValueError(f"{story.slug}: legacy seed has no reader-facing story")
    story_html = markdown.markdown(
        story.body,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )
    canon_label = "Canon" if story.canon else "Not canon"
    content = f"""  <header class="site-header">
    <a class="site-name" href="../../">← All stories</a>
  </header>
  <main>
    <article class="story">
      <p class="story-page-meta">
        <span class="status status-{html.escape(story.status)}">{html.escape(status_label(story.status))}</span>
        <span>{story.word_count:,} words</span>
        <span>{canon_label}</span>
      </p>
{story_html}
    </article>
  </main>
  <footer class="site-footer">
    <p><a href="../../">Return to the story index</a></p>
  </footer>"""
    return page_template(
        title=f"{story.title} · Story Computing Machine",
        description=f"Read {story.title}, a short story from the Boundless shared universe.",
        stylesheet="../../assets/styles.css",
        content=content,
        body_class="story-page",
    )


def prepare_output(output: Path) -> Path:
    output = output.resolve()
    try:
        relative_output = output.relative_to(REPOSITORY_ROOT)
    except ValueError as error:
        raise ValueError("Output directory must be inside the repository") from error
    if (
        not relative_output.parts
        or not relative_output.parts[0].startswith("_site")
    ):
        raise ValueError(f"Refusing unsafe output directory: {output}")
    if output.exists():
        if output.is_symlink():
            raise ValueError(f"Refusing to replace symlinked output directory: {output}")
        if not output.is_dir():
            raise ValueError(f"Output path is not a directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def build(output: Path) -> list[Story]:
    stories = load_stories()
    readable_stories = [story for story in stories if story.is_readable]
    output = prepare_output(output)

    (output / "index.html").write_text(render_index(stories), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")

    assets_output = output / "assets"
    assets_output.mkdir()
    shutil.copy2(ASSETS_ROOT / "styles.css", assets_output / "styles.css")

    for story in readable_stories:
        story_output = output / "stories" / story.slug
        story_output.mkdir(parents=True)
        (story_output / "index.html").write_text(
            render_story(story), encoding="utf-8"
        )

    missing_pages = [
        story.slug
        for story in readable_stories
        if not (output / "stories" / story.slug / "index.html").is_file()
    ]
    if missing_pages:
        raise RuntimeError(f"Missing generated story pages: {', '.join(missing_pages)}")

    return stories


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "_site",
        help="Site output directory (must be inside the repository)",
    )
    args = parser.parse_args()

    stories = build(args.output)
    readable_count = sum(story.is_readable for story in stories)
    legacy_count = sum(story.is_legacy_seed for story in stories)
    print(
        f"Built {readable_count} story pages and listed {legacy_count} legacy seeds "
        f"in {args.output.resolve()} "
        f"({sum(story.word_count for story in stories):,} words)."
    )


if __name__ == "__main__":
    main()
