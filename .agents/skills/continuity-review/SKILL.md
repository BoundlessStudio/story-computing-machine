---
name: continuity-review
description: "Review a shared-universe story for canon contradictions, chronology, character knowledge, narrative causality, prompt fulfillment, pacing, and prose readiness. Use after drafting and before finalization; do not silently rewrite the story."
---

# Continuity and story review

Review one assigned artifact in one explicit mode: `REVIEW_DRAFT` names
`03-draft.md`; `REVIEW_FINAL` names `05-story.md` and `06-canon-delta.md`.
Mode/artifact disagreement is a `HANDOFF_ERROR`. The independent
`continuity_critic` is read-only; the coordinator persists its bounded payload.
The coordinator may not self-review, and a non-independent substitute cannot
produce certification evidence.

## Inputs and authority

Require the story slug, mode, artifact paths and hashes,
`authorityManifest: stories/<slug>/authority.json`, its current
`authorityManifestSha256`,
`handoffLedger: stories/<slug>/handoffs.json`, its raw-byte
`handoffLedgerSha256` immediately before the review handoff, and that same
pre-handoff ledger's `chainHead`. Read the complete `00-prompt.md`,
`01-canon-brief.md`, `02-story-plan.md`, all prior `04-review.md` passes, the
assigned artifact, `universe/README.md`, relevant universe notes,
`stories/INDEX.md`, each relevant `story.json`, and `stories/NAMES.md`. For a
final review also read `06-canon-delta.md` and the coordinator's latest
available successful plan/final name-check result. This is review evidence, not
a substitute for the mandatory Final check after final prose is stable.

Validate `stories/<slug>/authority.json` and require its raw-byte hash to match
the handoff. It is the deterministic current-authority snapshot. Validate the ledger path,
digest, and `chainHead`; these values intentionally bind the pre-review ledger
snapshot the critic received. A missing, malformed, or stale
authority/ledger/artifact hash returns
`HANDOFF_ERROR`, `resolutionOwner: coordinator`, and no verdict. Never build an
ad hoc authority snapshot.

If a post-PASS repair is being reopened from terminal `candidate` state, require
the coordinator's atomic lifecycle reopen to `in-progress`/`final-review`,
pending, non-canon, unpublished state before issuing the new pass. Otherwise
return `HANDOFF_ERROR`, `resolutionOwner: coordinator`; do not append review
history that would silently invalidate a terminal release.

Only stories whose index row says canon `yes` and whose `story.json` says
`canon: true`, with those records agreeing, are continuity authority.
Candidate, in-progress, and abandoned stories are non-canon production context.
Archived source material is separate non-canon evidence with authority `none`;
it never classifies a production story. Do not turn resemblance to any of these
into a canon constraint.
An index/metadata disagreement for a relevant authority source is a
`HANDOFF_ERROR` owned by the coordinator, not a canon verdict; do not silently
choose one. The coordinator repairs it, regenerates the story's
`authority.json`, reruns `RESEARCH_CANON` when the brief's authority snapshot changed, and then
re-delegates the review.

## Pass identity and previous findings

Read all of `04-review.md`. Count only completed passes that identify a real
artifact and have a non-PENDING verdict. The untouched scaffold `Pass 1 —
pending` is not completed history and is replaced for the first review. A
coordinator-assigned pass is valid only if it is one greater than the highest
completed pass, or 1 when none exists. If the coordinator omits it, compute that
number. If completed history contains duplicates, malformed IDs, or a
non-monotonic sequence, return `HANDOFF_ERROR` without a verdict rather than
guessing.

A completed PASS does not close review history. A failed Final name receipt or
a changed/failed current-authority recheck legally reopens the gate with the
next `REVIEW_FINAL` pass against unchanged current story/delta hashes, the
failed receipt when applicable, and current `authorityManifestSha256`. That new
independent pass may PASS again or assign a repair owner. Never revise directly
from the earlier PASS.

For every prior unresolved Critical or Major finding relevant to the current
artifact, report a stable finding ID and one disposition:
`RESOLVED`, `STILL_OPEN`, or `SUPERSEDED`, with current evidence. A review
cannot pass while any such finding is still open.

For `REVIEW_FINAL`, require the latest accepted editor report to be present in
the handoff ledger. If it contains `NAME_REGISTRATION_REQUIRED`, non-empty name
proposals, or a final inventory not reconciled to the supplied registry digest,
return `HANDOFF_ERROR` with `resolutionOwner: coordinator`; registry
reconciliation must finish before review. A registry change after a review
stales that review and requires the next pass.

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
   without being pre-approved. Audit every row under
   `## Reviewed prose name-audit allowlist` against final prose: it must name the exact extracted label,
   use a template-allowed non-character classification, and give a human
   rationale. A character-facing form may never be excused by the allowlist.

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
  `resolutionOwner: coordinator` (the next gate owner).
- `REVISE`: one or more repairable Major findings; `blockType: NONE`, with
  exactly one earliest dependency owner: `coordinator` for central
  records/registry/ledger, `canon_librarian` for evidence or canon-brief work,
  `story_architect` for plan work, `prose_writer` for draft prose, or
  `story_editor` for final prose/delta.
- `BLOCK` plus `blockType: REPAIRABLE`: a Critical defect can be repaired in
  an existing owned artifact or central record; assign the same earliest valid
  repair owner. Do not misassign a brief/plan/registry defect to the prose
  owner merely because it surfaced in prose.
- `BLOCK` plus `blockType: USER_RULING_REQUIRED`: conflicting authority or an
  authorization choice cannot be repaired within current canon;
  `resolutionOwner: user` and an exact ruling question are mandatory.

When findings span owners, choose the earliest invalid dependency as
`resolutionOwner`; the coordinator repairs/routes that dependency, invalidates
and reruns all downstream gates, then requests a new review that can expose any
remaining later-owner work. A reviewer never edits the artifact it critiques.

## Exact persistence handoff

Return exactly one block bounded by `REVIEW_PASS_PAYLOAD` and
`END_REVIEW_PASS_PAYLOAD` with these fields:

```text
REVIEW_PASS_PAYLOAD
story: <slug>
mode: <REVIEW_DRAFT|REVIEW_FINAL>
status: <READY|HANDOFF_ERROR|USER_RULING_REQUIRED>
pass: <positive integer|not-issued for HANDOFF_ERROR>
reviewedArtifact: <03-draft.md|05-story.md>
artifactSha256: <raw-byte lowercase sha256>
canonDeltaSha256: <raw-byte lowercase sha256|not-applicable>
canonBriefSha256: <raw-byte lowercase sha256>
planSha256: <raw-byte lowercase sha256>
scopedRegistrySha256: <raw-byte lowercase sha256>
authorityManifest: stories/<slug>/authority.json
authorityManifestSha256: <raw-byte lowercase sha256>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <pre-review raw-byte lowercase sha256 supplied at delegation>
handoffLedgerChainHead: <pre-review chainHead supplied at delegation>
reviewer: continuity_critic
reviewedAt: <ISO-8601 timestamp with offset>
reviewBasis: <current authority/index snapshot>
verdict: <PASS|REVISE|BLOCK|not-issued>
blockType: <NONE|REPAIRABLE|USER_RULING_REQUIRED>
resolutionOwner: <coordinator|canon_librarian|story_architect|prose_writer|story_editor|user>
resolutionQuestion: <none|exact question requiring the user's decision>
errorCode: <none|INVALID_MODE|STALE_INPUT|INVALID_HISTORY|UNRECONCILED_REGISTRY|AUTHORITY_MANIFEST_INVALID|LEDGER_INVALID>
unresolvedCounts: { critical: <n>, major: <n>, minor: <n> }
priorFindingDispositions: <list with IDs, dispositions, and evidence>
findings: <structured list with all required finding fields>
certificationEligible: <true|false>
changeReport: read-only; no files changed
END_REVIEW_PASS_PAYLOAD
```

Use the exact lowercase token `none` when either structured list is empty.
Otherwise, each `priorFindingDispositions` item begins with `- findingId:`
and contains exactly one `disposition:` and `evidence:` field. Each `findings`
item begins with `- findingId:` and contains exactly one `lane:`, `severity:`,
`location:`, `evidence:`, `whyItMatters:`, and `smallestEffectiveFix:` field.
Finding IDs are unique within a pass. The Critical, Major, and Minor item
counts must exactly equal `unresolvedCounts`; Optional items are not included
in those counts. Every Critical or Major item from the preceding pass in the
same review mode must appear once in the next pass's dispositions, and a
`STILL_OPEN` item must retain the same finding ID in current findings.

`status` is the handoff discriminant. A structurally valid review uses `READY`
even when its verdict requires repair; `resolutionOwner` is the next authorized
owner and `errorCode` is `none`. A ruling block uses
`USER_RULING_REQUIRED`, verdict `BLOCK`, owner `user`, and the exact question.
It also uses `errorCode: none`. An invalid/stale delegation uses
`HANDOFF_ERROR`, pass/verdict `not-issued`, `blockType: NONE`,
`certificationEligible: false`, no pass append, and the exact mechanical
owner/prerequisite. Never combine a user status
with an artifact owner or a READY repair verdict with `resolutionOwner: user`.

For a real verdict, the coordinator verifies the hashes, appends this payload
without discarding earlier passes, and updates Current certification with the pass's artifact and
canon-delta hashes under exact labels `Artifact SHA-256` and `Canon delta
SHA-256`, plus reviewer, verdict, and unresolved counts. A `03-draft.md` review never
certifies `05-story.md`. Any artifact edit makes the matching review stale. A
final PASS is only the review component of `release.json`; release certification
also requires matching final-artifact hashes and a successful final name-check
receipt. Those coordinator writes occur inside the active critic handoff guard;
completing that guard records the accepted report in the hash-chained
`stories/<slug>/handoffs.json`. A HANDOFF_ERROR changes no review history but
is completed/ledgered with that status. No stage advance or release may cite a
report absent from the ledger.

The coordinator passes the exact complete `REVIEW_PASS_PAYLOAD` response as
`-ReportText`; the ledger stores it as `report` with `reportSha256`. It never
reconstructs the report from `04-review.md`, and HANDOFF_ERROR text remains
recoverable even though it is not appended there.

The completed REVIEW ledger entry records `stories/<slug>/handoffs.json` in
its inputs with exactly the payload's pre-review `handoffLedgerSha256`, and its
`previousEntrySha256` equals `handoffLedgerChainHead`. Guard completion then
changes the ledger hash/head. Release provenance binds that post-acceptance
current ledger digest; it is intentionally not equal to the review payload's
pre-handoff digest.
