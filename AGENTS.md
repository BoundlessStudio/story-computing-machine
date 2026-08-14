# Story Computing Machine

This repository is a shared-universe fiction workspace. The prose and the
universe notes are the product; process records are not.

## Two story layouts

A completed current story has four authored Markdown files and one generated
title image:

- `prompt.md` — the verbatim request and its few explicit constraints.
- `outline.md` — the draftable narrative shape, proposed people and places, and
  relevant continuity boundaries.
- `story.md` — the reader-facing prose and its minimal metadata.
- `review.md` — the final people/place inventory and continuity verdict.
- `title-image.jpg` — the final-story 9:16 portrait visual; never canon authority.

The cover displays the exact reader-facing story title once. It has no author
name, caption, logo, border, watermark, or other text.

The scaffold contains only the four Markdown files until the story passes
review. No other files belong in a current story directory.

Any existing story directory containing `05-story.md` is a locked legacy
bundle. Do not edit, migrate, validate, or regenerate its bundle files. Its
extra files are historical residue from the retired pipeline. The title-image
workflow may add or replace only `title-image.jpg` beside a legacy bundle;
that asset does not alter or reopen the bundle. Only the explicit Pages capture
command understands the legacy layout; normal story validation does not.

## Authority

- `universe/` is authoritative for shared facts. Read `universe/README.md`
  before interpreting canon.
- `universe/style-guide.md` is the binding narrative policy. Current scaffolds
  apply its prospective craft profile through the outline and writer skills;
  never use that profile to reopen completed current stories or locked legacy
  bundles.
- `stories/NAMES.md` is the frozen name baseline for legacy stories, not canon.
- Current `review.md` files extend production memory for new people and places.
- Plans, reviews, prompts, source notes, and non-canon stories never establish
  shared-universe facts.

## Branches

Before starting any new story, make branch setup the first repository action:

1. Switch to `main`.
2. Pull the latest changes from `origin/main` with a fast-forward-only pull.
3. Create a new `codex/story-<slug>` branch from the updated `main` without
   switching the primary checkout away from `main`.
4. Add a dedicated sibling Git worktree for that branch, then use the worktree
   as the working directory for the coordinator and every delegated agent for
   the rest of the story workflow.

Do not scaffold, read for story production, or modify story files until this
sequence is complete. Resolve and retain the worktree's absolute path before
delegating, and include that path in every agent assignment so no story work
lands in the primary checkout. Run all validation, capture, Git, push, and pull
request commands from the worktree. If local changes prevent switching the
primary checkout to `main` safely, or if the intended worktree path is already
occupied, stop and ask the user how to preserve or reuse it. Never change
`stories/` or `universe/` in the primary `main` checkout; merge the story branch
through a pull request. Git is the history; do not create manifests, ledgers,
receipts, release certificates, or duplicate lifecycle records.

## `[WP]` workflow

Use the `story-room` skill for a prompt tagged `[WP]` unless the user requests
one named stage.

1. Scaffold the four files with `new-story.ps1` and preserve the prompt.
2. Delegate `outline.md` to `story_outliner`. It reads the universe README and
   style guide, searches only relevant authority and noun history, skims the
   design sections of up to five recent passing current outlines, and proposes
   a story-specific generating force and narrative shape plus people and places
   as `new` or `recurring`. Recent outlines are comparison context only, never
   canon or models to imitate.
3. Delegate `story.md` to `story_writer`. It uses the compact
   `short-story-writing` skill, writes the complete story directly, and revises
   it in place at whole-story, movement/information, and language/sound scales.
   This remains one prose assignment; there is no separate draft, craft report,
   or final-edit artifact.
4. Run `Test-Stories.ps1 -Story <slug> -Phase PreReview` once. Pass its concise
   result to the reviewer without creating another file.
5. Delegate one independent review to `story_reviewer`. It writes only
   `review.md`, inventories every story-facing person and place noun, and checks
   prompt fulfillment, universe continuity, chronology, causality, and internal
   facts. The prompt is authoritative; the outline is advisory.
6. If the verdict is `REVISE`, delegate only blocking fixes to `story_writer`,
   repeat the pre-review check, and request one fresh review. Ask the user only
   when a canon ruling, retcon, or material prompt reinterpretation is required.
7. After `PASS`, delegate `title-image.jpg` to `story_title_illustrator`. It
   reads the complete final prose and writes only the spoiler-light 9:16 title
   visual. Unless the prompt says otherwise, use the repository's premium
   anime/light-novel key-visual default defined in that agent.
   The illustrator and coordinator must each judge the saved image through
   three separate gates:
   - **Story promise** — the image foregrounds the story's distinctive emotional
     or narrative contradiction, could not be mistaken for a generic genre
     cover, preserves character roles and relationships, and does not imply a
     resolution the prose has not earned.
   - **Cover read** — at thumbnail scale the exact title is readable once, the
     focal hierarchy is immediate, and the important figures, relationships,
     and story-specific objects remain legible rather than collapsing into a
     crowded tableau.
   - **Image integrity** — at full resolution anatomy and object counts are
     plausible, hands and faces withstand close inspection, perspective and
     physical connections are coherent, and there is no unintended text,
     pseudo-text, watermark, or visual artifact.
   The coordinator must compare the actual saved image against the prompt and
   final prose and make an independent decision; the illustrator's self-report
   is not acceptance. Technical polish cannot compensate for a generic or
   off-promise concept. When a gate fails, delegate a concise regeneration brief
   that says what to preserve, names the blocking miss, directs the composition
   or focal change, and restates the invariants. Require a new composition for a
   story-promise failure and a targeted correction for a localized integrity
   failure. Repeat review until all three gates pass, and do not capture a
   rejected image.
8. Run `Test-Stories.ps1 -Phase Final` locally, capture the story with
   `python pages/build.py capture <slug>` once, and run
   `python pages/build.py check`. Stage the story's four Markdown files together
   with `title-image.jpg`, `pages/catalog.json`, and the captured
   `pages/covers/<slug>.jpg`; commit them, push the current story branch to
   `origin` with upstream tracking, and open a draft pull request against the
   repository's default branch. Capture is the final prose-and-cover handoff.

Do not create a canon brief, authority snapshot, draft copy, canon delta,
handoff guard, release record, promotion record, story README, or index row.

## People and places

The outline proposes nouns and labels them `new` or `recurring`. The pre-review
check catches exact declared collisions. The review inventories the final prose
and owns exhaustive extraction, aliases, close spellings, and semantic
confusion checks. For every story-facing proper noun that names a person,
person-like being, or place:

- label it `new` or `recurring` in the review;
- search `stories/NAMES.md`, current `review.md` files, and the relevant
  `universe/characters.md` or `universe/locations.md` entries;
- avoid accidental exact, alias, close-spelling, and easily confused reuse;
- explain intentional recurrence briefly; and
- use a single `None` row when the story has no named noun of that kind.

`PreReview` validates the scaffold, usable prompt/outline/story, and exact
outline declarations. Run `-Phase Final` locally after review to validate the
final review structure, exact inventory, and continuity verdict. Neither mode
substitutes for the reviewer's semantic judgment.

## Review and continuity

A `PASS` review requires all three continuity lines to pass:

- `Prompt` — the story fulfills the request and resolves its central promise.
- `Universe` — people, places, chronology, capabilities, and facts do not
  contradict current `LOCKED` or `CANON` notes.
- `Internal` — the story is causally coherent and keeps its own facts straight.

The prompt is the only acceptance authority. The reviewer may use the outline
to understand design intent, but deviation from it is not blocking unless the
result breaks the prompt, universe continuity, or internal coherence.

For prompts carrying `Craft profile: prospective-2026-08-08`, the reviewer also
checks material compliance with the binding story craft defaults. Craft is
blocking only when it breaks the prompt's central promise, reader-facing
causality, or binding narrative policy. Do not copy the writer's in-place
revision criteria into `review.md`, and do not apply them retroactively to
existing stories.

Review prose concisely. Record only blocking findings and short useful notes;
do not preserve reviewer chain-of-thought, repeated summaries, or audit logs.

## Canon

New stories begin with `canon: false`. Canon promotion requires explicit user
approval for one named story, a fresh passing review against current authority,
and direct edits to the smallest relevant `universe/*.md` entries. Then set
`canon: true` in `story.md`. A conflict with `LOCKED` canon stops for a user
ruling. Git records the transaction; no separate delta or promotion file is
needed.

## Pages

`pages/catalog.json` and `pages/covers/` form the stored publication snapshot.
GitHub Pages builds and publishes only that snapshot; it never traverses
`stories/` or runs story validation. The `capture` command requires a passing
review and copies one completed story and its title image into the snapshot
without rerunning full validation. Keep the catalog ordered by full creation
timestamp, newest to oldest, so the newest story is always the first card on the
GitHub Pages index. New scaffolds record `created-at`; when a source has only a
`created` date, capture combines that date with the story prose file's filesystem
modification time. `capture-all` exists only for an intentional full refresh,
not for CI.

## Completion

A current story is complete when its four Markdown files and 9:16 portrait
`title-image.jpg` exist, `review.md` says `PASS`, people and places are
inventoried, all three continuity lines pass, and the story plus image have
been completed in the story directory and captured into `pages/catalog.json`
and `pages/covers/`. Repository acceptance also requires the local final
validator and catalog check to pass, the completed changes to be committed and
pushed on the story branch, and a draft pull request to be open against the
repository's default branch.
