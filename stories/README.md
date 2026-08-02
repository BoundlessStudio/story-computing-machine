# Stories

Every production story lives in `stories/<lowercase-kebab-slug>/`. `_template/` is the transactional scaffold.

## Artifacts

1. `00-prompt.md` — verbatim prompt and acceptance contract.
2. `01-canon-brief.md` — researched constraints and safe invention space.
3. `02-story-plan.md` — scene-ready causal plan and proposed names.
4. `03-draft.md` — complete working prose.
5. `04-review.md` — preserved numbered draft and final review payloads.
6. `05-story.md` — polished reader-facing story.
7. `06-canon-delta.md` — reusable facts proposed for promotion.

Records beside them:

- `story.json` v2 — lifecycle and `pipeline` or `legacy-user-attested` provenance.
- `authority.json` v2 — base branch commit, universe paths, admitted canon slugs.
- `handoffs.json` v3 — ordered specialist events, reports, inputs, and outputs.
- `release.json` v3 — certification basis, final review, name result, paths, and dates.
- `promotion.json` v2 — authorization, stewardship, dispositions, changed files, transaction result.
- `README.md` and `stories/INDEX.md` — checked lifecycle projections.

Only `05-story.md` is reader-facing. Candidate and final stories may publish only with a currently valid v3 release.

## Branch and lifecycle rules

Production mutation scripts refuse `main`. New work starts on `codex/story-<slug>` from current `main`, and each specialist begins from a clean branch checkpoint. Pull requests enforce chronology and required co-changes.

New stories are in-progress, non-canon, pending, and unpublished. Candidate completion requires passing final review and names. Explicit promotion creates a final canon story with accepted disposition and a promotion date. Rejected stories are abandoned and unpublished. Publication never establishes canon.

Use transaction scripts for lifecycle changes:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Set-StoryLifecycle.ps1 -Story <slug> -Action <Accept|Reject|Publish|Unpublish|Reopen>
```

Transactions hold a repository lock, compare captured raw preimages, update all coordinated projections, validate the result, and restore the original bytes on failure.

## Handoffs and reviews

Open a specialist turn with `New-StoryHandoffGuard.ps1`; finish with `Complete-StoryHandoffGuard.ps1 -GuardId <id> -ReportText <exact payload>`. The guard verifies branch state and changed-path scope. The ledger uses contiguous sequence numbers and preserves actor, persister, mode, status, report, inputs, outputs, errors, and resolution ownership.

Review payloads use the exact 20-field contract. Preserve all passes. A release requires the newest final review to be `PASS`, no unresolved Critical or Major findings, and a passing strict final name gate.

## Legacy acceptance

`legacy-acceptance.json` lists the exact user-reviewed legacy canon set. Listed stories may use a legacy attestation as their release basis without fabricated historical authority, handoff, or stewardship artifacts. Their final/canon/accepted/published projections and retained promotion dates must agree everywhere.
