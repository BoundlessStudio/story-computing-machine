# Stories

New stories live in `stories/<slug>/`. Their scaffold contains exactly four
authored Markdown files:

1. `prompt.md`
2. `outline.md`
3. `story.md`
4. `review.md`

After `review.md` passes, the title-image agent reads the complete final story
and adds `title-image.jpg`. A completed current story directory therefore has
those four Markdown files plus one exact 864x1536 (9:16 portrait) JPEG and nothing else.
The cover includes the exact reader-facing story title once and no other text.

`story.md` is the only reader-facing file. It carries `title`, `slug`,
`created`, and `canon` in frontmatter. A new story is non-canon until the user
explicitly approves it and the relevant shared facts are written into
`universe/`.

The prompt is authoritative. The outline is a compact, advisory handoff from
the outline specialist to the prose writer; it declares proposed people and
places as `new` or `recurring`. The final review inventories the nouns actually
used in prose and makes the prompt and continuity decision.

New scaffolds carry `Craft profile: prospective-2026-08-23`. Before drafting,
the outline derives a dialogue promise, deliberately chooses a dialogic medium,
states the communication engine, and completes the six-field Voice capsule with
Relationship movement. The prose and review skills apply those defaults
prospectively, including a bounded recent-story interchangeability check. The
workflow stays inside the four authored Markdown files: it adds no checklist or
audit artifact and does not reopen completed stories.

Both new stories and explicitly requested whole-story replacements use
`story-create`. Replacement is remove then create, never mutation of the old
package. After the dedicated branch and worktree are ready, inspect the named
story's canon marker and complete a separately authorized marker-only unlock
commit when it is `true`. Preserve every verbatim user-authored prompt or
request block, the verbatim new request, and all associated reference-image
display names; discard machine workflow metadata, then resolve and inspect the external
originals, requesting reattachment when one is inaccessible. Remove only that
story's source package and publication, cover, timeline, and legacy-index
remnants, confirm the target directory is absent, and scaffold it anew with
`new-story.ps1`. The new package carries all retained user-authored text and the new request in its
single CREATE prompt and inventories every reference, but it never loads or
carries the old outline, prose, review, or cover. It receives the full CREATE
outline, prose, recent-story comparison, independent review, cover, capture, and
publication workflow.

Some completed stories retain amendment metadata from a retired production
path. It remains inert acceptance context, including the last recorded craft
profile, when those packages are reviewed. New production does not create or
alter that metadata and does not compare a replacement against the removed
version.

A directory containing `05-story.md` is a legacy story. Its larger file set
belongs to the retired workflow, while `story.json` controls editability. A
named story with `canon: false` permits only an explicitly requested narrow
direct edit to the authorized legacy file. When `canon: true`, every bundle file
remains locked until a separately authorized marker-only unlock is committed.
A whole-story legacy remake uses remove-then-create replacement instead of
migration or in-place transformation. The current validator ignores legacy
bundles. The explicit Pages capture command retains a compatibility reader only
for intentional snapshot refreshes.

`NAMES.md` remains the frozen people-name baseline from legacy production. New
people and places are inventoried in each current story's `review.md`, avoiding
another central record that must be synchronized.

Every passing current story is captured into `pages/catalog.json` as the final
workflow step. The Pages builder treats that catalog as a separate publication
snapshot and does not reopen story sources during CI builds. Capture also copies
the story's title image into `pages/covers/` for publication on the card index
and story detail page.
