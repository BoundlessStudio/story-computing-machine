---
name: story-room
description: "Run the complete shared-universe short-story workflow for prompts tagged [WP], from prompt capture through canon vetting, planning, drafting, review, final prose, and a canon delta. Do not use for a request limited to one named stage."
---

# Story room

Produce the whole story and its audit trail.

## Start

1. Read `AGENTS.md`, `universe/README.md`, `stories/INDEX.md`, and
   `stories/NAMES.md`.
2. Derive a lowercase kebab-case slug. Never reuse an existing story directory.
3. Create the story directory from `stories/_template/`. On Windows, run
   `.agents/skills/story-room/scripts/new-story.ps1` with
   `-Slug <slug> -Title "<title>"`.
4. Put the user's verbatim prompt in `00-prompt.md`. Record target length,
   audience/rating, POV, tense, tone, required elements, prohibited elements,
   assumptions, and completion tests. Never silently remove a prompt promise.
5. Update the production record in `README.md`: set the current stage to
   `prompt` and check `Prompt contract captured` only after verifying the file.

## Run the stages

Use the custom agents in the order defined by `AGENTS.md`; dependencies matter.
If delegation is unavailable, invoke the corresponding skill locally.

At every handoff, name the story directory and the exact input/output artifact.
Do not ask a subagent to rediscover the workflow. After a subagent returns,
verify that its output exists and follows the template before continuing.

The primary agent updates `README.md` after each verified artifact: `canon-brief`,
`story-plan`, `draft`, `draft-review`, `final-edit`, `final-review`, and finally
`candidate`. Check only work that actually exists and passed its applicable
gate. Specialist agents do not update this record.

After verifying `02-story-plan.md`, check its complete `Name check` against
`stories/NAMES.md`. Use the `story-name-validation` skill. The primary agent
registers the planned names and aliases, records any meaningful reuse rationale
and reader-disambiguation strategy, and runs
`.agents/skills/story-name-validation/scripts/check-story-names.ps1` with
`-Story <slug>` before drafting. A new or unresolved collision must be renamed
or explicitly justified before prose begins.

Save every continuity critic response as an identified pass in `04-review.md`.
Preserve earlier passes and update `Current certification` to the latest pass.
Each pass must name the reviewed artifact. A `BLOCK` verdict must be resolved.
A `REVISE` verdict requires the relevant fixes and a focused recheck. `PASS` may
still include optional polish notes.

The first review gate evaluates `03-draft.md`. After it earns `PASS`, the story
editor writes `05-story.md` and `06-canon-delta.md`. The second, mandatory gate
evaluates `05-story.md`. If the final story receives `REVISE` or `BLOCK`, have
the editor revise `05-story.md` and `06-canon-delta.md`, then repeat the final
review. Do not finish until the latest pass identifies `05-story.md` and earns
`PASS` with no unresolved Critical or Major findings.

## Finish

Verify that:

- `05-story.md` is polished, complete prose within the agreed length tolerance;
- the ending resolves the central dramatic question;
- `04-review.md` preserves the review history and its latest certification
  identifies `05-story.md` with verdict `PASS`;
- no Critical or Major findings remain unresolved;
- every reusable invention is listed in `06-canon-delta.md`;
- the plan and canon brief include their name-registry sections;
- every character-facing name and alias used in `05-story.md` is reconciled in
  `stories/NAMES.md`, and the `story-name-validation` skill's scoped check
  succeeds;
- `stories/INDEX.md` has one current row. Unless explicit promotion was already
  authorized, its status is `candidate` and canon is `no`;
- the production record's current stage is `candidate`, all required checklist
  items are checked, and its state agrees with the index. The optional canon
  promotion item remains unchecked unless promotion was explicitly approved.

Report the final story path, approximate word count, review verdict, whether the
canon delta contains proposals, and whether any deliberate name reuse was
approved. Do not promote canon without explicit user approval.
