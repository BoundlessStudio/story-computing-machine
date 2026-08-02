---
name: prose-drafting
description: "Create or review-revise 03-draft.md from this project's prompt, canon brief, cleared names, and story plan. Final-story editing uses final-edit instead."
---

# Prose drafting

This skill owns `stories/<slug>/03-draft.md` only. The coordinator must specify
one mode: `CREATE_DRAFT` or `REVISE_DRAFT`, and supply the exact current
`beforeDraftSha256`, captured `draftScaffoldSha256`, and
`handoffLedgerSha256` for `stories/<slug>/handoffs.json`.

## Gates and inputs

Read `00-prompt.md`, `01-canon-brief.md`, `02-story-plan.md`, and
`stories/NAMES.md`. Accept only a canon brief with status `READY`. Hard-stop
with no edit if any current handoff says `HANDOFF_ERROR` or
`USER_RULING_REQUIRED`, or if an input/ledger/current-draft hash differs from
the delegation.

Before either mode, require a successful plan-phase name-check receipt. It must
name the same story, report `passed: true`, and bind the current plan and scoped
registry state. A missing, failed, or stale receipt is a `HANDOFF_ERROR` with
`errorCode: NAME_GATE_REQUIRED` and `resolutionOwner: coordinator`; do not
start prose.

- `CREATE_DRAFT` writes the initial complete `03-draft.md` only when the current
  raw bytes match `beforeDraftSha256` and that value exactly equals
  `draftScaffoldSha256`. Stop rather than overwrite a changed target.
- `REVISE_DRAFT` also reads all of `04-review.md` and the current draft. It is
  allowed only when the latest hash-matched review names `03-draft.md` and is
  `REVISE`, or is `BLOCK` with `blockType: REPAIRABLE` and
  `resolutionOwner: prose_writer`.

Never infer the mode from content. `REVISE_DRAFT` requires the current bytes to
match `beforeDraftSha256` and the authorizing review's `artifactSha256`; the
scaffold hash is still echoed so the coordinator can prove the transition.

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
  it. Return `status: NAME_REGISTRATION_REQUIRED`, `errorCode: none`,
  `resolutionOwner: coordinator`, `modifiedFiles: none`, and a structured
  `nameProposals` list. The coordinator sends accepted proposals through
  `REVISE_PLAN`, registry reconciliation, and a fresh Plan name receipt. For
  `CREATE_DRAFT`, it may then re-delegate the same unchanged create handoff.
  For `REVISE_DRAFT`, the plan change invalidates the authorizing review: first
  obtain a new `REVIEW_DRAFT` against the unchanged current draft and revised
  plan, and re-delegate only if that pass assigns repair to `prose_writer`.
- Deliver actual story prose with a title, not an outline, preface, critique, or
  explanation to the reader.

On revision, preserve effective voice and imagery. Fix the cited defect at its
cause rather than merely rephrasing the criticized sentence. Recheck downstream
continuity after structural changes. Report a disposition for every assigned
finding. A name change uses the same `NAME_REGISTRATION_REQUIRED` proposal flow
before the prose edit; never make it silently.

## Write boundary and handoff

The only permitted write is `stories/<slug>/03-draft.md`. Do not edit the plan,
review history, final artifacts, story metadata, production record,
`stories/INDEX.md`, `stories/NAMES.md`, universe notes, source archive, or
another story. Any draft edit invalidates a prior draft PASS and requires a new
draft review. It also invalidates final artifact review/PASS, the Final name
receipt, current-authority preflight, and `release.json`. After accepting and
ledgering the report, the coordinator reruns draft review; final edit when the
new review requires it; final registry reconciliation; final review; Final name
validation; current-authority recheck; release issuance; and story/repository
integrity, in that order. No downstream PASS survives changed draft bytes.

Return exactly:

```text
DRAFT_CHANGE_REPORT
story: <slug>
mode: <CREATE_DRAFT|REVISE_DRAFT>
status: <READY|HANDOFF_ERROR|USER_RULING_REQUIRED|NAME_REGISTRATION_REQUIRED>
resolutionOwner: <coordinator|prose_writer|user>
errorCode: <none|INVALID_MODE|STALE_INPUT|INVALID_CREATE_TARGET|NAME_GATE_REQUIRED|MISSING_REPAIR_AUTHORIZATION>
resolutionQuestion: <none|exact prerequisite or user decision>
modifiedFiles:
- stories/<slug>/03-draft.md
beforeDraftSha256: <raw-byte lowercase sha256>
draftScaffoldSha256: <raw-byte lowercase sha256>
inputNameCheckReceipt: <receiptId, checkedAt, planSha256, scopedRegistrySha256>
newDraftSha256: <post-write hash for READY|unchanged beforeDraftSha256 otherwise>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <delegated pre-handoff raw-byte lowercase sha256>
findingDispositions: <each finding ID/disposition/evidence, or none for create>
nameProposals: <exact forms/identity/rationale for NAME_REGISTRATION_REQUIRED|none>
requiresReview: <true for READY|false otherwise>
invalidatesDownstream: <complete ordered gate list for READY|none otherwise>
```

`READY` uses `resolutionOwner: coordinator` and `errorCode: none`. If a gate
fails, keep the same header, preserve the exact before/scaffold hashes, report
`modifiedFiles: none`, use `status: HANDOFF_ERROR`, assign the mechanical
prerequisite to `coordinator` or an invalid writer-owned artifact to
`prose_writer`, and state it in `resolutionQuestion`. A name proposal instead
uses `status: NAME_REGISTRATION_REQUIRED`, `errorCode: none`, and includes exact
proposed forms/rationale. A user decision uses `status: USER_RULING_REQUIRED`,
`resolutionOwner: user`, and the exact question. The coordinator records every
accepted report in the hash-chained ledger before stage advancement.
It passes the exact complete `DRAFT_CHANGE_REPORT` as `-ReportText`; ledger
`report`/`reportSha256` preserve READY, proposal, and error responses.
