# Stories

New stories live in `stories/<slug>/` and contain exactly four files:

1. `prompt.md`
2. `outline.md`
3. `story.md`
4. `review.md`

`story.md` is the only reader-facing file. It carries `title`, `slug`,
`created`, and `canon` in frontmatter. A new story is non-canon until the user
explicitly approves it and the relevant shared facts are written into
`universe/`.

The prompt is authoritative. The outline is a compact, advisory handoff from
the outline specialist to the prose writer; it declares proposed people and
places as `new` or `recurring`. The final review inventories the nouns actually
used in prose and makes the prompt and continuity decision.

A directory containing `05-story.md` is a locked legacy story. Its larger file
set belongs to the retired workflow. Do not edit or migrate those directories.
The current validator ignores them. The explicit Pages capture command retains
a compatibility reader only for intentional snapshot refreshes.

`NAMES.md` remains the frozen people-name baseline from legacy production. New
people and places are inventoried in each current story's `review.md`, avoiding
another central record that must be synchronized.

Every passing current story is captured into `pages/catalog.json` as the final
workflow step. The Pages builder treats that catalog as a separate publication
snapshot and does not reopen story sources during CI builds.
