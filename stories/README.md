# Story packages

New short stories use five text files.

| File | Contents |
| --- | --- |
| `prompt.md` | The complete user request and each later direction verbatim, the supplied image inventory, and the audience direction. |
| `outline.md` | The reading experience promised by the request, the short provisional plan, and the scene decisions that emerged from trying the story. |
| `story.md` | Finished prose with `title`, `created`, and `canon: false` frontmatter for a new story. |
| `notes.md` | What was tried, the effects readers reported, what the writer changed, and the results of rereading. Git keeps the full drafts. |
| `ratings.md` | The finished prose's reviewed General, Teen, Mature, or Explicit rating, with a brief reason and specific content notes. Use the template's explicit rating field. |

Store supplied originals under the recorded names in `art/references/`. Keep trials and raw reading material in the worktree's ignored `tmp/`. Use [the templates](_template/) and [the workshop](../.agents/skills/story-create/SKILL.md) for current work.

## Older stories

Existing four-file packages, `05-story.md` bundles, and their artwork retain their historical layouts. For a bundle, read its README for the file map and its `story.json` for current canon status. Current packages use the marker in `story.md`. Keep new decisions in `notes.md` when an authorized edit changes meaning, action, or voice. [Repository permissions](../AGENTS.md) govern edits.

Earlier `PG`, `YA`, and `R+` directions belong to the saved prompt. The current rating is in `ratings.md`. `NAMES.md` is name memory. [Universe authority](../universe/README.md) establishes shared facts.

## Visualization handoff

Give Storytelling Machine the slug and reviewed Git revision. The handoff consists of `story.md` with its frontmatter, `ratings.md`, and the supplied references approved for that edition from `art/references/`. The artist reads those originals at the pinned revision. The outline, writing prompt and editorial notes stay in the workshop. Publishing a writing prompt is a separate editorial choice.

Importing the pinned story in the presentation project starts its illustrator. The import produces the character and location studies the story needs, checks the cover against the reviewed edition and audience, and prepares the public library images there. Historical editions can still use their archived R2 art. [Storytelling Machine illustration and import](https://github.com/BoundlessStudio/storytelling-machine#illustrate-and-import-a-story)
