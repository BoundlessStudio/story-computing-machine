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

Creation and rewriting have separate entry workflows. A new story starts from a
fresh prompt through `story-create`. An explicitly requested rewrite uses
`story-rewrite`, which records one scope in `prompt.md`: `REBUILD` for a new
whole-story execution, `RESHAPE` for a whole-story pass that preserves unnamed
material in substance, or `SELECTIVE` for named edits while all other prose
remains exact. Keep-exact, keep-in-substance, change-or-replace, and remove
selections make the preservation boundary reviewable. Both workflows use the
same outline, prose, dialogue, independent review, and cover standards; no
rewrite brief, comparison report, or backup prose is added to the story folder.

A directory containing `05-story.md` is a locked legacy story. Its larger file
set belongs to the retired workflow. Do not edit or migrate its bundle files;
the title-image workflow may add or replace only `title-image.jpg` beside them.
The current validator ignores legacy bundles. The explicit Pages capture
command retains a compatibility reader only for intentional snapshot refreshes.

`NAMES.md` remains the frozen people-name baseline from legacy production. New
people and places are inventoried in each current story's `review.md`, avoiding
another central record that must be synchronized.

Every passing current story is captured into `pages/catalog.json` as the final
workflow step. The Pages builder treats that catalog as a separate publication
snapshot and does not reopen story sources during CI builds. Capture also copies
the story's title image into `pages/covers/` for publication on the card index
and story detail page.
