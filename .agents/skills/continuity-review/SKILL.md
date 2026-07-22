---
name: continuity-review
description: "Review a shared-universe story for canon contradictions, chronology, character knowledge, narrative causality, prompt fulfillment, pacing, and prose readiness. Use after drafting and before finalization; do not silently rewrite the story."
---

# Continuity and story review

Review the assigned story artifact: `03-draft.md` for the draft gate or
`05-story.md` for the mandatory final gate. Compare it with the prompt contract,
canon brief, plan, authoritative universe notes, and any relevant canon stories.
For a final review, also compare `06-canon-delta.md` with the final prose and
check that editing introduced no continuity, causality, or prompt regressions.

Check these lanes separately:

1. Canon: facts, terminology, capabilities, costs, geography, institutions.
2. Continuity: time, travel, injuries, objects, names, knowledge, POV access.
3. Causality: motivations, setup/payoff, escalation, climax agency, resolution.
4. Prompt: required premise, tone, POV, length, boundaries, and story promise.
5. Craft: scene function, pacing, clarity, dialogue, exposition, repetition.
6. Canon delta: reusable inventions are captured without being pre-approved.

For each finding provide `Severity`, `Location`, `Evidence`, `Why it matters`,
and `Smallest effective fix`. Severity is `Critical`, `Major`, `Minor`, or
`Optional`. Do not report preferences as defects.

Begin each pass by identifying the exact reviewed artifact and pass number. The
primary agent will append the pass to `04-review.md` and update its `Current
certification`; never imply that a review of `03-draft.md` certifies
`05-story.md`.

End with exactly one verdict:

- `PASS` — no Critical or Major issues remain.
- `REVISE` — one or more Major issues remain but canon is resolvable.
- `BLOCK` — a Critical issue or canon ruling prevents safe finalization.
