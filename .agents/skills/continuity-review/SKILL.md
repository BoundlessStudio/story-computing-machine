---
name: continuity-review
description: "Review a shared-universe story for canon contradictions, chronology, character knowledge, narrative causality, prompt fulfillment, pacing, and prose readiness. Use after drafting and before finalization; do not silently rewrite the story."
---

# Continuity and story review

Review one assigned artifact: `03-draft.md` for the draft gate or
`05-story.md` for the mandatory final gate. The critic is read-only; the
coordinator persists its bounded payload.

## Inputs and authority

Require the story slug and artifact. Read the complete `00-prompt.md`,
`01-canon-brief.md`, `02-story-plan.md`, all prior `04-review.md` passes, the
assigned artifact, `universe/README.md`, relevant universe notes,
`stories/INDEX.md`, each relevant `story.json`, and `stories/NAMES.md`. For a
final review also read `06-canon-delta.md` and the coordinator's latest
available successful plan/final name-check result. This is review evidence, not
a substitute for the mandatory Final check after final prose is stable.

Only stories whose index row says canon `yes` and whose `story.json` says
`canon: true`, with those records agreeing, are continuity authority.
Candidate, in-progress, and abandoned stories are non-canon production context.
Archived source material is separate non-canon evidence with authority `none`;
it never classifies a production story. Do not turn resemblance to any of these
into a canon constraint.
An index/metadata disagreement for a relevant authority source is a
`HANDOFF_ERROR` owned by the coordinator, not a canon verdict; do not silently
choose one.

## Pass identity and previous findings

Read all of `04-review.md`. Count only completed passes that identify a real
artifact and have a non-PENDING verdict. The untouched scaffold `Pass 1 —
pending` is not completed history and is replaced for the first review. A
coordinator-assigned pass is valid only if it is one greater than the highest
completed pass, or 1 when none exists. If the coordinator omits it, compute that
number. If completed history contains duplicates, malformed IDs, or a
non-monotonic sequence, return `HANDOFF_ERROR` without a verdict rather than
guessing.

For every prior unresolved Critical or Major finding relevant to the current
artifact, report a stable finding ID and one disposition:
`RESOLVED`, `STILL_OPEN`, or `SUPERSEDED`, with current evidence. A review
cannot pass while any such finding is still open.

Check these lanes separately:

1. Canon: facts, terminology, capabilities, costs, geography, institutions.
2. Continuity: time, travel, injuries, objects, names, knowledge, POV access.
3. Names: every character-facing name and alias appears in the plan's name
   check and central registry; matches or close confusions are either the same
   identity or have a documented meaningful-reuse rationale and clear reader
   disambiguation.
4. Causality: motivations, setup/payoff, escalation, climax agency, resolution.
5. Prompt: required premise, tone, POV, length, boundaries, and story promise.
6. Craft: scene function, pacing, clarity, dialogue, exposition, repetition.
7. Canon delta: reusable inventions and the final name inventory are captured
   without being pre-approved.

For each finding provide `findingId`, `lane`, `Severity`, `Location`,
`Evidence`, `Why it matters`, and `Smallest effective fix`. Severity is
`Critical`, `Major`, `Minor`, or `Optional`. Do not report preferences as
defects. An undocumented accidental name reuse is at least Major. A collision
that falsely implies identity, kinship, chronology, or crossover may be
Critical. Reserved candidate and abandoned names still count as
production-memory collisions even though their stories are not canon. Names
found only in the source archive may be reported as collision evidence, but do
not create a different registry state or validation exception for a production
story.

## Verdict and resolution ownership

- `PASS`: no unresolved Critical or Major; `blockType: NONE`,
  `resolutionOwner: none`.
- `REVISE`: one or more repairable Major findings; `blockType: NONE`, with
  `resolutionOwner: prose_writer` for the draft or `story_editor` for final.
- `BLOCK` plus `blockType: REPAIRABLE`: a Critical defect can be repaired in
  the reviewed artifact; assign its artifact owner.
- `BLOCK` plus `blockType: USER_RULING_REQUIRED`: conflicting authority or an
  authorization choice cannot be repaired within current canon;
  `resolutionOwner: user` and an exact ruling question are mandatory.

## Exact persistence handoff

Return exactly one block bounded by `REVIEW_PASS_PAYLOAD` and
`END_REVIEW_PASS_PAYLOAD` with these fields:

```text
story: <slug>
pass: <positive integer>
reviewedArtifact: <03-draft.md|05-story.md>
artifactSha256: <raw-byte lowercase sha256>
canonDeltaSha256: <raw-byte lowercase sha256|not-applicable>
reviewer: <continuity_critic|explicit primary fallback identifier>
reviewedAt: <ISO-8601 timestamp with offset>
reviewBasis: <current authority/index snapshot>
verdict: <PASS|REVISE|BLOCK>
blockType: <NONE|REPAIRABLE|USER_RULING_REQUIRED>
resolutionOwner: <none|prose_writer|story_editor|user>
resolutionQuestion: <none|exact question requiring the user's decision>
unresolvedCounts: { critical: <n>, major: <n>, minor: <n> }
priorFindingDispositions: <list with IDs, dispositions, and evidence>
findings: <structured list with all required finding fields>
certificationEligible: <true|false>
changeReport: read-only; no files changed
```

The coordinator verifies the hashes, appends this payload without discarding
earlier passes, and updates Current certification with the pass's artifact and
canon-delta hashes under exact labels `Artifact SHA-256` and `Canon delta
SHA-256`, plus reviewer, verdict, and unresolved counts. A `03-draft.md` review never
certifies `05-story.md`. Any artifact edit makes the matching review stale. A
final PASS is only the review component of `release.json`; release certification
also requires matching final-artifact hashes and a successful final name-check
receipt.
