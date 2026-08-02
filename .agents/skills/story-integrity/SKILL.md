---
name: story-integrity
description: "Validate story metadata, production records, review and name gates, inert evidence records, and content-bound release certificates; issue a release certificate only for a completed candidate or final bundle."
---

# Story integrity

Use this skill before declaring a story candidate, before canon promotion, and
whenever repository story records or evidence records change. `story.json` is
the authoritative lifecycle record. The production README and
`stories/INDEX.md` are derived lifecycle views that must agree with it.
`05-story.md` frontmatter contains only immutable identity fields (`title`,
`slug`, and `created`) so lifecycle transitions never invalidate reviewed prose
bytes.

## Machine contracts and transaction evidence

`schemas/pipeline-contract.json` is the central machine contract; its strict
JSON Schema, semantics, and story templates must agree. Validate it before
interpreting lifecycle, review, handoff, release, or template fields:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-PipelineContract.ps1 -OutputFormat Json
```

Every story has schema-version-1 `story.json` plus `authority.json`,
schema-version-2 `handoffs.json`, `promotion.json`, and schema-version-2
`release.json`. The handoff ledger records causal specialist work, exact input
and output hashes, the returned report, and distinct `actor` and `persister`
identities. A legacy or mechanically reconstructed report is inert evidence;
it never substitutes for live READY research/review or an independent critic.
`Convert-PipelineRecordsV2.ps1` is therefore an assessment tool, not an
evidence synthesizer: `-WhatIf` reports the live gates a legacy terminal story
must repeat, an ordinary run refuses without changing bytes, and only an
already-current record with a passing scoped integrity receipt returns
`ALREADY_CURRENT`.

Open a specialist turn with `New-StoryHandoffGuard.ps1` and retain both its
`guardId` and `guardSha256`. Complete it with those exact values and exact
`ReportText`. Abort refuses unless every captured path is restored. Use
`-RecoverCommittedGuard` only to validate and clean up a durable append after a
crash. Lifecycle projections change through `Complete-StoryCandidate.ps1` and
`Set-StoryLifecycle.ps1`, whose lock, compare-and-swap, postcondition, and
byte-for-byte rollback cover the coordinated records.

`New-AuthorityManifest.ps1` reconciles the exact story-directory/index
bijection and every lifecycle projection before admitting promoted stories.
It double-checks the complete input inventory before and after capture, and
restores the prior manifest if a concurrent change is detected during a write.

Allowed stages are `prompt`, `canon-research`, `planning`, `drafting`,
`draft-review`, `final-edit`, `final-review`, `candidate`, `final`, and
`abandoned`. Allowed statuses are `in-progress`, `candidate`, `final`, and
`abandoned`; use only the combinations in the central lifecycle contract.
`sources/MANIFEST.json` has `authority: none` and never classifies a story.

## Name gates

Run the plan gate after the plan and registry rows are current:

```powershell
pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 `
  -Story <slug> -Phase Plan
```

Run the final gate after final prose, the canon delta, and the registry are
reconciled. `06-canon-delta.md` must contain the explicit final name inventory;
every inventoried form must occur in final prose and have an exact story-scoped
registry reservation.

Use `-OutputFormat Json` when another workflow needs a machine receipt. A plan
receipt contains the plan hash; a final receipt contains story and canon-delta
hashes. Both bind exact story-scoped registry rows and report exact, reversed,
close, and punctuation-confusable forms. Global/active registry context is
diagnostic; unrelated stories must not stale this story's scoped release.

## Issue a release

Prefer atomic candidate completion after every gate is current:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1 `
  -Story <slug>
```

The finalizer verifies authority, the required READY handoff chain, review,
names, lifecycle projections, and release postcondition, rolling all of its
writes back on failure. For an already eligible candidate/final
re-certification, the current certification
in `04-review.md` must identify `05-story.md`, record a positive pass number,
name the reviewer, say `PASS`, and record zero unresolved Critical and Major
findings. Then run:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-StoryRelease.ps1 `
  -Story <slug>
```

The issuer reruns the final scoped name gate and writes schema-version-2
`release.json`. It binds prompt-through-final artifacts, exact draft and final
review evidence/history, scoped name evidence, current authority, and the
current handoff ledger. Editing any bound dependency invalidates the
certificate. Never patch hashes or set `certified` by hand.

## Validate

Validate one story while working:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 `
  -Story <slug>
```

Run the repository mode before completion, promotion, or publication:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
```

Both modes return nonzero for defects. Story mode authenticates the staged
artifact contract; repository mode additionally enforces directory/index
bijection, the central contract/templates, inert evidence manifest, universe
provenance, and global name registry. CI also runs the adversarial agent,
handoff, review, name, promotion, migration, transaction, and site suites.
