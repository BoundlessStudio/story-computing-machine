# Stories

Each current package in `stories/<slug>/` contains `prompt.md`, `outline.md`,
`story.md`, and `review.md`. After prose review passes, new stories and replacements
create reviewed character sheets and separate exterior/interior references in
`art/characters/`, `art/landscapes/` and `art/interiors/`, then use the accepted
references to generate `title-image.jpg`. References follow the gallery's oil style
and are captured into the Image Gallery with the story. Only `story.md` is
reader-facing prose; no extra Markdown production records belong in the package.

Packages containing `05-story.md` retain the supported bundle layout. Their
`story.json` canon marker controls editability; current packages use `story.md`
frontmatter. See [artifact and permission rules](../AGENTS.md#two-story-layouts).

Use [story-create](../.agents/skills/story-create/SKILL.md#workflow) for new
stories or named replacements. Completed stories retain their recorded prompt
and craft profile. Canon promotion requires a separate user decision.

`NAMES.md` is frozen production memory; current `review.md` inventories extend
it. Shared facts belong to [universe/](../universe/README.md). Pages publishes
captured stories and covers from its stored snapshot; see
[publication](../.agents/skills/story-create/SKILL.md#publication).
