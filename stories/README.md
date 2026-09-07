# Stories

Each current package in `stories/<slug>/` contains `prompt.md`, `outline.md`,
`story.md`, and `review.md`. After review passes, `title-image.jpg` completes the
package. Only `story.md` is reader-facing prose.

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
