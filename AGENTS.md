# Story Computing Machine

This repository exists to turn `[WP]` prompts into memorable short stories. The story is the product. Use tools, agents, art, and continuity only when they help the story or protect a real boundary. Give writers room to discover a better story than their first plan.

## Authority and permission

- Preserve the user's request verbatim in `prompt.md`. It controls what the story must deliver. An outline or an agent's preference does not.
- Read [universe/README.md](universe/README.md) when using shared facts. `universe/` alone establishes them: `LOCKED` outranks `CANON`, and `PROVISIONAL` is guidance. A story, image, review, or editorial note does not silently add canon. Ask the user to resolve a conflict with an established fact; record an approved retcon in `universe/retcons.md`.
- [universe/style-guide.md](universe/style-guide.md) holds the few shared narrative and content boundaries. Its craft advice guides new work; it does not reopen finished stories. A deliberate prompt or story voice can depart from a default unless a `LOCKED` boundary says otherwise.
- For a named existing story, read its canon marker before making a content edit: `story.md` frontmatter in current packages, `story.json` in bundles. If the marker is missing or unclear, ask. `canon: true` locks every file in that story package until the user explicitly unlocks that named story. An explicit unlock changes only the authoritative marker in its own commit; put the user's request in that commit message. Complete that commit before any separately authorized prose or art edit. Do not infer an unlock from a critique or a general wish to improve the collection.
- New stories start with `canon: false`. Promotion needs the user's explicit approval for that named story. Check the finished prose against current universe authority, add only facts the user approves as shared, then set the marker to `true`. Promotion does not follow automatically from a good review. Unlocking a story never demotes or erases `LOCKED` or `CANON` universe facts; changing those needs its own user ruling.

## Working area and story files

Set up a branch and dedicated worktree from updated `main` before story production. Do all story reads for production, edits, commits, and pull-request work there; leave the primary checkout on `main`. Keep the absolute worktree path in agent assignments. Use a pull request for merging and never merge on the user's behalf. Preserve authored work when changing layouts or retiring tools.

For a new story, keep `stories/<slug>/` small:

- `prompt.md` — the exact request, explicit constraints, and display names of any supplied reference images. Keep the originals outside the package; inspect every supplied original, and ask for reattachment if one is inaccessible.
- `story.md` — the reader-facing story, with `title`, `created`, and `canon: false` frontmatter.
- `notes.md` — concise editorial memory in the spirit of the one-paragraph template. Preserve the reader effects, reasoning, repairs, and any useful dissent without making a scorecard or transcript.
- A `title-image.jpg` cover follows a new `[WP]` story by default after its prose is ready, unless the user asks for prose only. `outline.md` and additional accepted `art/` images are optional. Drafts and rejected image candidates stay outside the package.

Older four-file current packages and `05-story.md` bundles may stay as they are. Their old reviews, profiles, and extra historical files are records, not instructions to recreate the retired process. For an authorized edit, preserve the layout and scope; use `notes.md` for new editorial decisions without rewriting old `review.md`. Git commits for the first complete draft and each substantial revision preserve the actual prose changes; `notes.md` preserves the reasoning even if a pull request is squash-merged. No hashes, PASS tokens, or generated process records are needed.

## The editorial work

Use [story-create](.agents/skills/story-create/SKILL.md) for a new `[WP]` story or a substantial authorized revision. It centers on a writer, independent first readers, an actual discussion among them, revision, and rereading. A reader's well-supported objection matters even when another reader likes the story. The coordinator judges the passage and records a reason; agents do not vote a story into readiness. Check prompt fulfillment, relevant canon, names, and internal consistency after judging whether the story itself works.

A localized edit should remain local unless reading exposes a structural problem that the user has authorized fixing. For a whole-story replacement, obtain a named request and verify the canon marker first. Preserve the user's original request and reference inventory, and let the coordinator read earlier notes to understand what failed. Remove the named package before clean creation, including its old prose, notes, outline, review, cover, and art. Remove that slug's top-level `art/characters/`, `art/landscapes/`, and `art/interiors/` assets and its `art/selection-notes.json` entries; leave other stories alone. Carry useful diagnosis into fresh notes, but do not use the old prose as a template. Git history retains the former work.

Make art after the prose is strong. A cover or reference image must match the finished story and any supplied reference; inspect its actual pixels. There is no mandatory gallery inventory. Existing story art and the preserved legacy art collection remain creative assets, not canon.

`illustrated/` and `graphic-novels/` contain existing editions. Keep them as authored artifacts; neither changes the source story or establishes canon. The former site and automated publication processes are retired. Any new edition or publication method is a separate, explicit project.
