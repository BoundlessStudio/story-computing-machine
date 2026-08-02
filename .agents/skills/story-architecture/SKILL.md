---
name: story-architecture
description: "Design a scene-ready short-story plan from a captured prompt and canon brief. Use for plot, character arc, scene structure, stakes, and ending design; do not use to draft final prose."
---

# Short-story architecture

The coordinator must name one story and exactly one mode: `CREATE_PLAN` or
`REVISE_PLAN`. The handoff must include the exact paths and current raw-byte
lowercase hashes for `00-prompt.md`, `01-canon-brief.md`,
`stories/<slug>/02-story-plan.md`, and `stories/<slug>/handoffs.json`, plus the
captured scaffold hash for the plan:

```text
mode: <CREATE_PLAN|REVISE_PLAN>
inputPromptSha256: <lowercase sha256>
inputCanonBriefSha256: <lowercase sha256>
beforePlanSha256: <lowercase sha256>
planScaffoldSha256: <lowercase sha256>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <pre-handoff lowercase sha256>
```

Read `00-prompt.md`, `01-canon-brief.md`, `stories/NAMES.md`, and the current
plan before writing. Accept only a canon brief whose durable research status is
`READY`. A stale/missing hash, invalid mode, non-READY brief, or inconsistent
record is `HANDOFF_ERROR`; an unresolved authority choice is
`USER_RULING_REQUIRED`. Do not plan around either state.

`CREATE_PLAN` is legal only when `beforePlanSha256` equals both the current
plan bytes and `planScaffoldSha256`. `REVISE_PLAN` is legal only when the
current bytes equal `beforePlanSha256` and the coordinator supplies a current,
hash-matched repair authorization: an accepted critic report whose
`resolutionOwner` is `story_architect`, or an accepted
`NAME_REGISTRATION_REQUIRED` proposal that requires the plan's Name check to
change. The authorization must bind the same plan hash. Never infer CREATE
versus REVISE from file contents, and never overwrite a plan after a hash race.

Build `02-story-plan.md` around one central dramatic question and one meaningful
change. The protagonist needs a concrete desire, pressure that makes delay
costly, a blind spot or internal tension, and a final choice that causes the
ending. Each scene must change the situation and cause or constrain the next.

Include:

- one-sentence premise and story promise;
- POV, tense, tone, length budget, and content boundaries;
- protagonist, desire, stakes, opposition, internal movement, and key cast;
- beginning state, inciting disruption, escalating turns, crisis, climax, and
  resonant aftermath;
- a scene table with purpose, conflict, turn, canon used, and word budget;
- seeded details and their payoffs;
- canon constraints and clearly labeled proposed inventions;
- a `Name check` section containing only the exact four-column table from
  `stories/_template/02-story-plan.md`: `Character/entity`, `Reserved forms
  used in prose`, `Registry result`, and `Reuse rationale and reader
  disambiguation`. Put the table immediately after the heading, put every
  planned character-facing form in its second column separated by semicolons,
  and begin any commentary after it under a new level-two heading. Do not add,
  remove, rename, or merge columns;
- failure modes the writer and critic should watch.

Fit the plan to short fiction. Avoid subplots that cannot pay off within the
word budget, lore tours, delayed inciting incidents, and endings solved by new
information or unseeded powers.

Default to names absent from the registry and readily distinguishable from
reserved aliases and close variants. Reuse a name only when it has clear
narrative meaning, and state whether it is the same identity or a distinct
identity. Never infer a crossover from a matching name. The primary coordinator,
not the architect, updates `stories/NAMES.md` after verifying the plan.

Every new or changed character-facing form is a proposal, not a reservation.
List it in `nameProposals` with identity, all forms, collision analysis, and any
meaningful-reuse rationale, and return status `NAME_REGISTRATION_REQUIRED`
with `resolutionOwner: coordinator`. The coordinator ledgers the proposal,
reconciles only those forms into `stories/NAMES.md`, then re-delegates
`REVISE_PLAN` so the architect can record the verified registry results. That
second report must be `READY` before the coordinator runs the scoped Plan name
gate and records its receipt. The architect never claims a proposal is
registered and never edits the registry.

The only permitted write is `stories/<slug>/02-story-plan.md`. Do not edit the
prompt, canon brief, prose, review, final artifacts, metadata, production
record, registry, index, universe notes, source archive, or another story.

Changing the plan invalidates every downstream gate: the Plan name receipt,
draft review/PASS, final artifacts' review/PASS, Final name receipt,
`release.json`, and any current-authority/release preflight. The coordinator
must rerun, in order, Plan registry reconciliation and name validation, draft
review (and `REVISE_DRAFT` plus another draft review when findings require it),
final registry reconciliation and final review (with `REVISE_FINAL` loops when
required), Final name validation, current-authority recheck, release issuance,
and story/repository integrity. A plan report never performs those steps.

Return exactly:

```text
PLAN_CHANGE_REPORT
story: <slug>
mode: <CREATE_PLAN|REVISE_PLAN>
status: <READY|HANDOFF_ERROR|USER_RULING_REQUIRED|NAME_REGISTRATION_REQUIRED>
resolutionOwner: <coordinator|story_architect|user>
errorCode: <none|INVALID_MODE|STALE_INPUT|INVALID_CREATE_TARGET|MISSING_REPAIR_AUTHORIZATION>
resolutionQuestion: <none|exact prerequisite or user question>
modifiedFiles:
- stories/<slug>/02-story-plan.md
inputPromptSha256: <raw-byte lowercase sha256>
inputCanonBriefSha256: <raw-byte lowercase sha256>
beforePlanSha256: <raw-byte lowercase sha256>
planScaffoldSha256: <raw-byte lowercase sha256>
newPlanSha256: <post-write hash for READY/NAME_REGISTRATION_REQUIRED|unchanged beforePlanSha256 otherwise>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <pre-handoff raw-byte lowercase sha256 supplied at delegation>
repairAuthorization: <accepted report id/hash or none for CREATE_PLAN>
nameProposals: <complete structured list or none>
nextAction: <REGISTER_NAMES_AND_REVISE_PLAN|PLAN_NAME_CHECK_REQUIRED>
invalidatesDownstream: <complete ordered gate list for READY/NAME_REGISTRATION_REQUIRED|none otherwise>
```

`READY` uses `resolutionOwner: coordinator`, `errorCode: none`, no unresolved
name proposals, and reports the post-write hash. `NAME_REGISTRATION_REQUIRED`
also reports the post-write hash, uses owner `coordinator`, and supplies exact
proposals; it cannot advance to the Plan name gate. `HANDOFF_ERROR` uses the owner of the failed prerequisite
(`coordinator` for a stale/bad handoff, `story_architect` only for a malformed
architect-owned prior plan), reports `modifiedFiles: none`, preserves the exact
before/scaffold hashes, and names the repair. `USER_RULING_REQUIRED` uses
`resolutionOwner: user`, `modifiedFiles: none`, and the exact decision in
`resolutionQuestion`. The coordinator verifies and records every accepted
report in the hash-chained `stories/<slug>/handoffs.json` before changing stage.
It passes the exact complete `PLAN_CHANGE_REPORT` as `-ReportText`; the ledger's
`report`/`reportSha256` must preserve it, including no-write/error proposals.
