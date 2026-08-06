# Story Computing Machine

This repository is a shared-universe fiction workspace. The prose and the
universe notes are the product; process records are not.

## Two story layouts

A current story has exactly four files:

- `prompt.md` — the verbatim request and its few explicit constraints.
- `outline.md` — the causal shape, proposed people and places, and relevant
  continuity boundaries.
- `story.md` — the reader-facing prose and its minimal metadata.
- `review.md` — the final people/place inventory and continuity verdict.

Any existing story directory containing `05-story.md` is a locked legacy
bundle. Do not edit, migrate, validate, or regenerate it. Its extra files are
historical residue from the retired pipeline. Only the explicit Pages capture
command understands that layout; normal validation and site builds do not.

## Authority

- `universe/` is authoritative for shared facts. Read `universe/README.md`
  before interpreting canon.
- `universe/style-guide.md` is the binding narrative policy.
- `stories/NAMES.md` is the frozen name baseline for legacy stories, not canon.
- Current `review.md` files extend production memory for new people and places.
- Plans, reviews, prompts, source notes, and non-canon stories never establish
  shared-universe facts.

## Branches

Never change `stories/` or `universe/` on `main`. Start a new story on
`codex/story-<slug>` and merge through a pull request. Git is the history; do
not create manifests, ledgers, receipts, release certificates, or duplicate
lifecycle records.

## `[WP]` workflow

Use the `story-room` skill for a prompt tagged `[WP]` unless the user requests
one named stage.

1. Scaffold the four files with `new-story.ps1` and preserve the prompt.
2. Read the universe README and style guide. Search only the universe entries,
   legacy names, and current reviews relevant to this prompt.
3. Write a compact, scene-ready `outline.md`. Check proposed people and places
   before drafting.
4. Write the complete story directly to `story.md`; there is no separate draft
   or final-edit pass.
5. Delegate one independent review to `story_reviewer`. The reviewer writes
   only `review.md` and checks prompt fulfillment, every story-facing person and
   place noun, universe continuity, chronology, causality, and internal facts.
6. If the verdict is `REVISE`, fix only blocking findings and request one fresh
   review. Ask the user only when a canon ruling, retcon, or material prompt
   reinterpretation is actually required.
7. Run `Test-Stories.ps1` once. A passing review makes a non-canon story
   complete.
8. If the story should appear on Pages, run
   `python pages/build.py capture <slug>` once and commit `pages/catalog.json`.

Do not create a canon brief, authority snapshot, draft copy, canon delta,
handoff guard, release record, promotion record, story README, or index row.

## People and places

The outline proposes names; the review inventories the final prose. For every
story-facing proper noun that names a person, person-like being, or place:

- label it `new` or `recurring` in the review;
- search `stories/NAMES.md`, current `review.md` files, and the relevant
  `universe/characters.md` or `universe/locations.md` entries;
- avoid accidental exact, alias, close-spelling, and easily confused reuse;
- explain intentional recurrence briefly; and
- use a single `None` row when the story has no named noun of that kind.

The validator catches declared exact collisions and missing review structure.
The reviewer owns exhaustive extraction and semantic confusion checks.

## Review and continuity

A `PASS` review requires all three continuity lines to pass:

- `Prompt` — the story fulfills the request and resolves its central promise.
- `Universe` — people, places, chronology, capabilities, and facts do not
  contradict current `LOCKED` or `CANON` notes.
- `Internal` — the story is causally coherent and keeps its own facts straight.

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

`pages/catalog.json` is the publication boundary. GitHub Pages validates and
renders only that stored snapshot; it never traverses `stories/`. The
`capture` command copies one reviewed story into the catalog. `capture-all`
exists only for an intentional full refresh, not for CI.

## Completion

A current story is complete when its four files exist, `review.md` says `PASS`,
people and places are inventoried, all three continuity lines pass, and the
single story validator succeeds.
