---
name: story-room
description: "Create or review a shared-universe short story using only prompt, outline, story, and review."
---

# Story room

Use for `[WP]` prompts or a named story stage. Prefer safe, low-impact
assumptions over questions. Default to a coherent 2,500–4,000 word story unless
the prompt says otherwise.

## CREATE mode

1. Work on a non-main branch and scaffold with `scripts/new-story.ps1`.
2. Preserve the prompt, then delegate OUTLINE to `story_outliner`. It writes
   only `outline.md` after targeted canon and noun searches.
3. Delegate WRITE to `story_writer`. It uses `short-story-writing` and writes
   the complete prose directly to `story.md`; there is no draft/final split.
4. Run `scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview` once and pass
   its concise result to the reviewer. Do not save another report file.
5. Delegate one independent REVIEW to `story_reviewer`. The prompt is the
   acceptance authority; `outline.md` is advisory context.
6. If the verdict is `REVISE`, delegate only the blocking fixes to
   `story_writer`, repeat the pre-review check, and request one fresh review.
   Stop for the user only when authority or prompt meaning requires a ruling.
7. After `PASS`, capture the story with `python pages/build.py capture <slug>`.
   This mandatory final handoff updates the publication catalog; GitHub CI runs
   final validation and publishes from the stored snapshot.

Do not create research briefs, authority snapshots, handoff records, separate
draft/final files, canon deltas, release records, promotion manifests, story
READMEs, or index projections. Do not reread the complete legacy corpus when a
targeted search answers the continuity question.

## OUTLINE responsibility

Write only `outline.md`. Keep causal beats scene-ready and compact. Declare
every proposed person and place noun as `new` or `recurring`, using one `None`
row for an empty category. Record relevant canon and unresolved boundaries, but
do not turn the outline into a canon brief or an acceptance contract.

## REVIEW mode

Write only `review.md`. Follow its template exactly:

- inventory all story-facing people and place proper nouns;
- mark each noun `new` or `recurring`, with `None` for an empty category;
- check the prompt, current universe authority, and internal story facts;
- use the outline as context, not as a reason to reject a prompt-faithful story;
- use `Verdict: PASS` only when all continuity lines are `PASS` and blocking
  findings are `none`; otherwise use `REVISE` and list concise fixes.

Keep the review short. Findings and outcomes belong in the file; hidden
reasoning, audit narration, and repeated plot summaries do not.
