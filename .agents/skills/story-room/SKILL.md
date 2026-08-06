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
2. Preserve the prompt. Read `universe/README.md` and
   `universe/style-guide.md`, then search only relevant canon entries, legacy
   names, and current reviews.
3. Write a compact `outline.md` with causal beats, ending, people, places, and
   continuity boundaries. Keep it useful to the prose pass, not exhaustive.
4. Write the complete prose directly to `story.md`.
5. Delegate one independent REVIEW to `story_reviewer`.
6. Resolve blocking findings only. Re-review once after changes; stop for the
   user only when authority or prompt meaning genuinely requires a ruling.
7. Run `scripts/Test-Stories.ps1` once.
8. If the story should appear on Pages, capture it once with
   `python pages/build.py capture <slug>`. Pages builds only from that stored
   snapshot.

Do not create research briefs, authority snapshots, handoff records, separate
draft/final files, canon deltas, release records, promotion manifests, story
READMEs, or index projections. Do not reread the complete legacy corpus when a
targeted search answers the continuity question.

## REVIEW mode

Write only `review.md`. Follow its template exactly:

- inventory all story-facing people and place proper nouns;
- mark each noun `new` or `recurring`, with `None` for an empty category;
- check the prompt, current universe authority, and internal story facts;
- use `Verdict: PASS` only when all continuity lines are `PASS` and blocking
  findings are `none`; otherwise use `REVISE` and list concise fixes.

Keep the review short. Findings and outcomes belong in the file; hidden
reasoning, audit narration, and repeated plot summaries do not.
