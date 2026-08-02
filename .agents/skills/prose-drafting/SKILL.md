---
name: prose-drafting
description: "Create or review-revise 03-draft.md from this project's prompt, canon brief, cleared names, and story plan. Final-story editing uses final-edit instead."
---

# Prose drafting

This skill owns `stories/<slug>/03-draft.md` only. The coordinator must specify
one mode: `CREATE_DRAFT` or `REVISE_DRAFT`.

## Gates and inputs

Read `00-prompt.md`, `01-canon-brief.md`, `02-story-plan.md`, and
`stories/NAMES.md`. Accept only a canon brief with status `READY`. Hard-stop
with no edit if any current handoff says `COORDINATOR_REPAIR_REQUIRED` or
`USER_RULING_REQUIRED`.

Before either mode, require a successful plan-phase name-check receipt. It must
name the same story, report `passed: true`, and bind the current plan and scoped
registry state. A missing, failed, or stale receipt returns
`NAME_GATE_REQUIRED`; do not start prose.

- `CREATE_DRAFT` writes the initial complete `03-draft.md` only when the target
  is absent or still the unchanged scaffold placeholder. Stop rather than
  overwrite substantive unreviewed prose.
- `REVISE_DRAFT` also reads all of `04-review.md` and the current draft. It is
  allowed only when the latest hash-matched review names `03-draft.md` and is
  `REVISE`, or is `BLOCK` with `blockType: REPAIRABLE` and
  `resolutionOwner: prose_writer`.

A final-story review never authorizes a draft revision. Do not use this skill
for `05-story.md` or `06-canon-delta.md`; use `final-edit`.

- Begin near the first meaningful disturbance.
- Maintain the chosen POV and tense. Filter world detail through immediate
  desire, perception, consequence, and action.
- Prefer precise sensory and behavioral detail over explanatory lore blocks.
- Give each scene a live want, resistance, and irreversible change.
- Make dialogue carry strategy, subtext, or relationship movement.
- Seed solutions before payoff and make the protagonist's climax choice causal.
- Obey hard canon. Keep inventions local and record reusable ones for the canon
  delta; do not state speculative lore as established history.
- Use the names and aliases cleared in the plan's `Name check`. Do not add,
  rename, shorten, or retitle a character in a way that creates an unreviewed
  registry form. If prose genuinely needs another named character, surface the
  proposed name for coordinator registration instead of silently introducing
  it.
- Deliver actual story prose with a title, not an outline, preface, critique, or
  explanation to the reader.

On revision, preserve effective voice and imagery. Fix the cited defect at its
cause rather than merely rephrasing the criticized sentence. Recheck downstream
continuity after structural changes. Report a disposition for every assigned
finding. A name change requires coordinator registration and a fresh successful
plan-phase receipt before the prose edit; never make it silently.

## Write boundary and handoff

The only permitted write is `stories/<slug>/03-draft.md`. Do not edit the plan,
review history, final artifacts, story metadata, production record,
`stories/INDEX.md`, `stories/NAMES.md`, universe notes, source archive, or
another story. Any draft edit invalidates a prior draft PASS and requires a new
draft review.

Return exactly:

```text
DRAFT_CHANGE_REPORT
story: <slug>
mode: <CREATE_DRAFT|REVISE_DRAFT>
modifiedFiles:
- stories/<slug>/03-draft.md
inputNameCheckReceipt: <receiptId, checkedAt, planSha256, scopedRegistrySha256>
newDraftSha256: <raw-byte lowercase sha256>
findingDispositions: <each finding ID/disposition/evidence, or none for create>
newNamesProposed: none
requiresReview: true
```

If a gate fails, keep the same header, report `modifiedFiles: none`, result
`NAME_GATE_REQUIRED | COORDINATOR_REPAIR_REQUIRED | USER_RULING_REQUIRED |
INVALID_MODE`, and the exact missing prerequisite. A user-ruling result also
includes the exact `rulingQuestion`.
