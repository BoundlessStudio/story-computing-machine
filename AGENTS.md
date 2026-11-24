# Story Computing Machine

This is a short-fiction workshop. The writer has room to discover the story through drafts. The coordinator uses editorial experiments and independent reading to decide what the page needs.

## Improving the workshop

For requests to improve how the machine writes, reviews or rates stories, change the relevant skill, agent instructions or tool. Use existing manuscripts and revisions as read-only test material. A quoted writing prompt or a question in an editorial note can identify a test case. Creating a story package or revising a manuscript takes a commission for that work.

Start from one observed failure and a passage where the same intervention could spoil an effect. Compare the current and proposed methods on the same inputs with comparable review effort. Record what the change caught, what it put at risk and whether to keep it. On a continuing improvement request, choose the next weakness in the workflow from that evidence.

## Authority and permission

- For a commissioned story, preserve the complete user request verbatim in `prompt.md`. Append later directions in their original words. Keep explicit requirements distinct from interpretations and ideas the writer is free to change.
- [Universe authority](universe/README.md) lives in `universe/`. `LOCKED` outranks `CANON` and `PROVISIONAL` supplies guidance. Check only the shared facts the story uses. Verify proposed additions against their sources and record only the scope the user approves. Ask the user to resolve a confirmed conflict with established facts and record approved retcons in `universe/retcons.md`.
- Follow the shared [style guide](universe/style-guide.md). A deliberate voice or prompt may depart from a craft default within the `LOCKED` boundaries. General is the starting audience target when the user leaves it open.
- Read the named story's canon marker before any content edit. In current packages it is in `story.md` frontmatter, and in older bundles it is in `story.json`. Ask if the marker is missing or unclear. A story with `canon: true` requires an explicit unlock naming the story before any package file changes. Commit only the marker change first and include the user's request in that commit message. Make separately authorized edits after that commit.
- New stories start with `canon: false`. Promote a named story only with the user's explicit approval after checking the finished prose against current universe authority. A story's promotion or unlock leaves authority over shared facts with the user.

## Working area

Use the Codex worktree attached to the current chat. Run story production, edits, commits, and pull request work there, and give agents its absolute path. Read-only external inputs are allowed. Use a pull request for merging and leave the merge to the user.

Keep task files inside the worktree. Use its ignored `tmp/` for scene trials, reader inputs and outputs, scratch scripts, logs, and pull request body files. Derive the absolute root with `git rev-parse --show-toplevel`, pass an explicit directory to temporary-file APIs, and set `TMPDIR`, `TMP`, and `TEMP` to that root's `tmp/` for subprocesses when needed. Check resolved temporary paths for links or junctions that would leave the worktree. Git and agent applications manage their own metadata.

## Story work

For a request to write a new story or substantially revise an identified manuscript, use the [story workshop](.agents/skills/story-create/SKILL.md). Give one writer ownership. Try approaches on the page before settling the outline, concentrating on the decisive scene or conversation. Use an independent cold reader on the complete draft, rewrite at the scale of what the reading reveals, then line-edit and obtain a fresh whole-story reading. Use more reading or further rewriting when the evidence warrants it. Give the writer room to change the provisional plan.

Review prompt fulfillment and craft through the actual scenes and ending. Ground material objections in passages, relevant sources, and reader experience. Check consequential continuity in context, including who could know what and what later scenes establish. Preserve deliberate ambiguity the reader can follow. The coordinator owns the decision and records the reasons, including useful dissent. Treat model feedback as editorial evidence to examine. Decisions is available for [optional research](.agents/skills/story-create/references/fidelity-checkpoints.md).

Use the five text files in [the package guide](stories/README.md) for new work. Preserve all supplied original images with their recorded names in `art/references/`, inspect each original, and ask for reattachment when an input is inaccessible. The finished prose receives a reviewed AO3 rating in `ratings.md`. Commit the first complete draft and subsequent substantial rewrites. Use `notes.md` for concise editorial memory, including the reason for substantial changes and the results of rereading.

## Existing packages

Keep older layouts and historical reviews. Read a bundle's `README.md` as a file map and use its `story.json` for current canon status. For a localized change to meaning, action, or voice, have an independent reader check the changed passage in the whole story and record the useful finding in `notes.md`. The coordinator can reread a mechanical correction. Reassess the rating after a substantial authorized revision.

Clean replacement requires an explicit request to remake one named non-canon story. Preserve the original prompt, later directions, reference inventory, and supplied originals. Read the prior editorial notes for evidence of what failed. Remove the superseded package, restore the preserved inputs, and develop the story afresh from them. Git preserves the former work. If there is an illustrated or graphic-novel edition, tell the user it belongs to that earlier text and leave it intact.

## Visualization handoff

Hand off the reviewed prose, rating, and approved references by story slug and source revision. Keep the complete prompt and workshop discussion in the editorial package. Storytelling Machine owns the illustration agent, art direction, covers, character and location studies, and the public presentation. [Visualization handoff](stories/README.md#visualization-handoff)

Existing art, `illustrated/`, and `graphic-novels/` are authored records subject to the same package permissions. The existing `media/` workflow serves historical source assets to the public library.
