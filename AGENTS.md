# Story Computing Machine

This repository is a shared-universe fiction workspace. Prose and universe notes are the product.

## Authority and records

- `universe/` is authoritative for shared-universe facts. Read `universe/README.md` before interpreting canon.
- `stories/<slug>/story.json` v2 is the lifecycle authority. `stories/INDEX.md` and each story README are checked projections.
- `stories/NAMES.md` is production memory, not canon.
- `authority.json` v2 records the selected base branch commit, universe-file inventory, and admitted canon stories.
- `handoffs.json` v3 is an ordered specialist-work ledger.
- `release.json` v3 records the current release decision, review result, name result, artifacts, and dependencies.
- `promotion.json` v2 records one explicitly authorized canon transaction.
- `stories/legacy-acceptance.json` is the user attestation for the listed legacy stories. Do not invent missing historical specialist work.
- `sources/` contains inert evidence with `authority: none`.
- `schemas/pipeline-contract.json` is the strict shared field contract.

Templates, prompts, plans, drafts, reviews, proposed deltas, source evidence, and anything marked `authority: none` do not establish canon.

## Trust model

Correctness is established from the current checkout, the branch and pull-request history, required co-changes, strict schemas, transactional writes, specialist role boundaries, automated checks, and human acceptance. The project does not maintain custom cryptographic file-binding records.

Git commits establish stage chronology. Specialist work begins from a clean checkpoint on a non-protected branch. Temporary raw byte copies may be used only for rollback and concurrent-write comparison; they are never durable evidence.

## Branch workflow

- Never mutate `stories/` or `universe/` on `main`.
- New stories start on `codex/story-<slug>` from current `main`.
- Checkpoint the branch before every specialist delegation.
- Ordinary local work runs fast story-scoped checks. Pull requests run the complete suite, repository validator, source and universe checks, pull-request policy, and reader-site test/build.
- `main` accepts squash merges through pull requests only. It requires all configured checks, must be current before merge, blocks force pushes and deletion, and has no routine administrative bypass.
- Do not require signatures, CODEOWNERS, or approving reviews unless the user changes this policy.

## Lifecycle

Keep these `story.json` axes independent: `stage`, `status`, `canon`, `userDisposition`, `publish`, and `provenance`.

| Status | Stage | Canon | Disposition | Promotion date | Publication |
| --- | --- | --- | --- | --- | --- |
| `in-progress` | nonterminal | false | pending | null | false |
| `candidate` | candidate | false | pending or accepted | null | optional |
| `final` | final | true | accepted | required | optional |
| `abandoned` | abandoned | false | rejected | null | false |

Use transaction entry points; do not hand-edit coordinated lifecycle projections.

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Set-StoryLifecycle.ps1 -Story <slug> -Action <Accept|Reject|Publish|Unpublish|Reopen>
```

## Complete `[WP]` workflow

A request containing `[WP]` uses the `story-room` skill unless the user requests a named stage only.

1. Scaffold with `new-story.ps1`; preserve the verbatim prompt and explicit assumptions in `00-prompt.md`.
2. Create `authority.json` from the branch base commit and current inventories.
3. Delegate canon research to `canon_librarian`; the coordinator persists `01-canon-brief.md`.
4. Delegate a scene-ready plan to `story_architect`, which writes only `02-story-plan.md`.
5. Validate and register every planned character-facing name.
6. Delegate draft creation or revision to `prose_writer`, which writes only `03-draft.md`.
7. Delegate draft review to `continuity_critic`; the coordinator appends the exact 20-field payload to `04-review.md`.
8. Resolve every Critical or Major finding. Stop for user authority when a canon ruling, retcon, or material prompt reinterpretation is required.
9. Delegate final creation or revision to `story_editor`, which writes only `05-story.md` and `06-canon-delta.md`.
10. Delegate final review to `continuity_critic`; revise and repeat until the latest final pass is `PASS` with zero unresolved Critical and Major findings.
11. Reconcile final names and run the strict final gate.
12. Complete the candidate transaction and run story-scoped validation.
13. Run the full validator in the pull request. Leave canon false unless the user explicitly authorizes promotion.

Dependent stages are sequential. Independent read-only research may be parallelized. Every specialist delegation states the slug, mode, inputs, allowed outputs, current stage, and acceptance condition.

## Specialist handoffs

Open a handoff with `New-StoryHandoffGuard.ps1`. It requires a UUID, a clean/checkpointed branch, exact inputs, and an output allowlist. Complete it with `Complete-StoryHandoffGuard.ps1 -GuardId <id> -ReportText <exact returned payload>`. Completion checks `git diff --name-only`, rejects out-of-scope changes, and appends one sequence-numbered ledger event. Abort never discards work.

Role ownership:

| Role | Writes |
| --- | --- |
| `canon_librarian` | nothing; returns canon-brief payload |
| `story_architect` | `02-story-plan.md` |
| `prose_writer` | `03-draft.md` |
| `continuity_critic` | nothing; returns one review payload |
| `story_editor` | `05-story.md`, `06-canon-delta.md` |
| `canon_steward` | approved topical `universe/*.md` entries only |
| coordinator | read-only payload persistence, metadata, index, registry, releases, promotion records |

## Review and release

Each persisted review payload uses the exact fields in `schemas/pipeline-contract.json`. It identifies the story, mode, sequence pass, reviewed path, current authority and ledger paths, reviewer, time, basis, verdict, block ownership, findings, unresolved counts, eligibility, and change report. Preserve every pass.

A v3 release is certified only when the latest final review is `PASS`, Critical and Major counts are zero, the strict final name gate passes, and required pipeline records exist. A release records paths and decision facts, not duplicate file identities. Final prose, delta, review, or relevant registry changes require release reconsideration in the same pull request.

The 24 stories named in `stories/legacy-acceptance.json` use `provenance: legacy-user-attested`. They are exempt from nonexistent historical authority, handoff, and promotion records when their lifecycle projections, simplified releases, and acceptance entries agree. This exemption never applies to a new pipeline story.

## Name discipline

Read `stories/NAMES.md` before proposing any character-facing name. Register planned names after planning and reconcile them after final review. Check exact matches, aliases, close spellings, reversals, and confusable forms. Reuse requires an intentional story reason and documented identity relationship. The coordinator alone edits the registry. Abandoned rows remain searchable unless explicitly released.

## Canon and promotion

Canon promotion requires explicit user authorization for one named story. Recheck the story against current `LOCKED` and `CANON` entries. Give every concrete delta item a disposition and target. Promote only into the smallest topical scope, preserve local qualifiers, and record story provenance. A discovered conflict with `LOCKED` canon stops for a user ruling; do not infer a retcon.

The `canon_steward` edits only approved universe files and returns an exact stewardship report. The coordinator owns `promotion.json`, lifecycle/index/registry changes, validation, and rollback. Finalization uses `Complete-CanonPromotion.ps1` for pipeline candidates. A legacy correction may record a completed v2 promotion after user attestation, exact delta disposition, universe validation, and successful transactional projection updates.

## Source evidence

A local source record declares a repository path, controlled version label, verification status, and verification time. An external record declares a controlled locator, version when known, access date, access requirements, and verification status. A descriptive-only locator cannot support a reproducible claim. Evidence never grants canon or production status.

## Completion

A story workflow is complete when final prose and delta exist, the newest final review passes, strict final names pass, release v3 is certified, projections agree, authority and handoff records are current, and the pull-request checks pass. A promoted final additionally requires explicit authorization, complete dispositions, updated universe notes, and a completed promotion record.
