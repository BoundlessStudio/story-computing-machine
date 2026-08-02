---
name: story-integrity
description: "Validate story metadata, production records, ordered handoffs, review and name gates, inert evidence, Git chronology, and simplified release decisions."
---

# Story integrity

Use before candidate completion, canon promotion, publication, and after pipeline or evidence changes.

## Trust model

Validate the current checkout against `schemas/pipeline-contract.json`. Git identifies the selected base and establishes stage order; a pull request proves required co-changes. Strict fields, narrow specialist writes, current validation, transactional rollback, and human acceptance establish correctness. Do not create a parallel custom file-identity system.

Records:

- `story.json` v2 owns lifecycle and provenance.
- `authority.json` v2 names base branch/commit, universe files, and admitted canon slugs.
- `handoffs.json` v3 stores contiguous specialist events.
- `release.json` v3 stores certification basis, artifact paths, review/name results, and dependencies.
- `promotion.json` v2 stores authorization, stewardship, dispositions, modified files, and transaction result.

## Commands

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-PipelineContract.ps1 -OutputFormat Json
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 -Story <slug> -OutputFormat Json
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 -OutputFormat Json
```

Mutation scripts must call `Assert-ProductionBranch`. `PipelineTransactions.ps1` holds the repository lock, stores raw preimages temporarily, compares current bytes to the captured preimages, validates postconditions, and restores originals on failure.

## Authority

Create after branching from current `main`:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1 -Story <slug> -OutputFormat Json
```

Verify before every dependent gate. A changed base commit or changed authority inventory makes the record stale and requires the affected stages to run again.

## Handoffs

Checkpoint the branch first. Open the exact mode with `New-StoryHandoffGuard.ps1`; retain `guardId`. The guard records actor, persister, exact inputs, allowed outputs, and starting branch state. Complete with the exact returned report text. Completion uses changed-path inspection, rejects writes outside the allowlist, and appends one sequence event. Abort only removes an unchanged guard; it never discards edits.

A release chain contains one successful event from each required family in dependency order: research, plan, draft, draft review, final edit, final review.

## Reviews and release

Persist the exact 20-field review payload in the next numbered `04-review.md` pass. The current certification summary must match the newest pass. Do not reconstruct a missing review.

`New-StoryRelease.ps1` requires a pipeline candidate/final, current authority, complete handoff sequence, final `PASS`, zero unresolved Critical/Major findings, and strict final names. `Complete-StoryCandidate.ps1` performs the coordinated transition.

Listed legacy stories use the explicit user attestation instead. Their v3 release preserves declared review results but does not pretend historical pipeline dependencies existed.

## Pull-request policy

PR validation checks branch protection, base commit, changed paths, required story/index/registry/release co-changes, review-after-artifact order, release-after-review/name order, source locator/version completeness, and a single authorized completed promotion for universe edits.
