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
2. Delegate `outline.md` to `story_outliner`. It reads the universe README and
   style guide, searches only relevant authority and noun history, and proposes
   people and places as `new` or `recurring`.
3. Delegate `story.md` to `story_writer`. It uses the compact
   `short-story-writing` skill and writes the complete story directly; there is
   no separate draft or final-edit pass.
4. Run `Test-Stories.ps1 -Story <slug> -Phase PreReview` once. Pass its concise
   result to the reviewer without creating another file.
5. Delegate one independent review to `story_reviewer`. It writes only
   `review.md`, inventories every story-facing person and place noun, and checks
   prompt fulfillment, universe continuity, chronology, causality, and internal
   facts. The prompt is authoritative; the outline is advisory.
6. If the verdict is `REVISE`, delegate only blocking fixes to `story_writer`,
   repeat the pre-review check, and request one fresh review. Ask the user only
   when a canon ruling, retcon, or material prompt reinterpretation is required.
7. After `PASS`, run `python pages/build.py capture <slug>` once and commit
   `pages/catalog.json`. Capture is the final story handoff; GitHub CI performs
   final validation and publication.

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
outline declarations. CI uses `-Phase Final` to validate the final review
structure, exact inventory, and continuity verdict. Neither mode substitutes
for the reviewer's semantic judgment.

## Review and continuity

A `PASS` review requires all three continuity lines to pass:

- `Prompt` — the story fulfills the request and resolves its central promise.
- `Universe` — people, places, chronology, capabilities, and facts do not
  contradict current `LOCKED` or `CANON` notes.
- `Internal` — the story is causally coherent and keeps its own facts straight.

The prompt is the only acceptance authority. The reviewer may use the outline
to understand design intent, but deviation from it is not blocking unless the
result breaks the prompt, universe continuity, or internal coherence.

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
`capture` command requires a passing review and copies one completed story into
the catalog without rerunning full validation. `capture-all` exists only for an
intentional full refresh, not for CI.

## Completion

A current story is complete when its four files exist, `review.md` says `PASS`,
people and places are inventoried, all three continuity lines pass, and the
story has been captured into `pages/catalog.json`. Repository acceptance also
requires the final CI validator to pass.
