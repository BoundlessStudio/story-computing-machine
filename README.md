# Story Computing Machine

A project-local Codex story room for writing short fiction in one shared
universe. Give Codex a prompt tagged `[WP]`; the project routes it through canon
research, story architecture, drafting, two continuity gates, final editing,
name reconciliation, and a content-bound release check.

## Quick start

1. Open this repository as the Codex workspace.
2. Add known setting facts to `universe/` (or ask Codex to help seed them).
3. Start a task with a prompt such as:

   ```text
   [WP] Every city has a ghost assigned to it. Tonight, ours resigns.
   Target: about 3,000 words; close third person; melancholy but hopeful.
   ```

4. Codex creates `stories/<story-slug>/` and keeps the prompt, authority
   snapshot, canon brief, plan, draft, review history, final story, proposed
   canon changes, specialist ledger, lifecycle metadata, promotion provenance,
   and release certificate together.

If length, point of view, or tone are omitted, the workflow records reasonable
defaults instead of stopping for low-impact questions. A completed workflow
produces a candidate; canon promotion remains a separate, explicit decision.

## Project layout

- `AGENTS.md` — project direction, lifecycle invariants, and ownership rules.
- `.codex/agents/` — project-scoped specialist roles Codex can delegate to.
- `.agents/skills/` — reusable workflows, validators, and supporting scripts.
- `universe/` — authoritative shared-universe notes.
- `stories/` — one directory per story, the production index and name registry.
- `sources/` — inert evidence and decision history, always `authority: none`.
- `pages/` — the deterministic reader-site builder.

Within each story, `story.json` is the lifecycle authority and `release.json`
binds publication readiness to exact prompt-through-final artifacts, the
current authority snapshot, the exact authority actually reviewed, the handoff ledger, the exact final PASS, and the
strict scoped name receipt. `authority.json` captures the raw authoritative
inputs used by the run, `handoffs.json` is a hash-chained record of bounded
specialist work and exact returned reports, and `promotion.json` records the
separate canon transaction. Human README and index fields are validated
projections of the machine record.

## Pipeline integrity

Specialist work runs inside a repository mutation guard bound by the returned
`guardId` and coordinator-retained `guardSha256`. Each handoff declares exact
contract inputs and outputs before delegation; completion rejects any
out-of-scope write and records the exact `ReportText`, output byte changes,
specialist actor, actual persister, and previous entry hash in a
schema-version-2 ledger. Dirty aborts are refused; explicit crash recovery
verifies a fully committed entry before lock cleanup. Continuity review uses an exact 28-field payload whose
artifact, authority, registry, and pre-review ledger hashes are checked again
at release time.

The story name gates reject unregistered, exact, reversed, close, and
punctuation-confusable character-facing names unless deliberate reuse is fully
documented. Final validation also compares an explicit inventory to an
independent prose-derived candidate audit. Its `story-names/2` receipt binds the
story, canon delta, scoped registry rows, active comparison set, and warnings.

These SHA-256 records are deterministic dependency links and stale-change
detectors, not cryptographic signatures. They protect the workflow from races,
partial edits, and accidental/manual drift; they do not claim to resist a
malicious repository writer who rewrites every artifact and checksum. Reviewer
independence, protected branches, and repository access controls remain the
trust boundary for authorship.

Lifecycle changes use locked compare-and-swap transactions with byte-for-byte
rollback:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Set-StoryLifecycle.ps1 -Story <slug> -Action Accept
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Set-StoryLifecycle.ps1 -Story <slug> -Action Publish
```

Canon promotion is never a lifecycle flag edit. After explicit authorization
and a verified `canon_steward` handoff produce a schema-valid ready manifest,
the only finalization entry point is:

```powershell
pwsh -NoProfile -File .agents/skills/canon-maintenance/scripts/Complete-CanonPromotion.ps1 -Story <slug> -PromotionDate <YYYY-MM-DD>
```

It verifies and completes `promotion.json`, applies coordinated production
updates, regenerates authority and release provenance, and rolls the whole
transaction back if a post-write gate fails.

The ready manifest has an immutable preparation digest. Promotion finalization
preserves that digest in both the completed manifest and final release, so the
post-promotion authority snapshot cannot be confused with the candidate
snapshot the critic reviewed. Legacy terminal records are never upgraded by
inventing those receipts: `Convert-PipelineRecordsV2.ps1 -WhatIf` reports the
required live revalidation, while a normal conversion refuses without writes
unless the record is already current and passes scoped integrity.

## GitHub Pages

The Pages workflow builds entirely from the current checkout. Reader-facing
finals are included only when `story.json` opts them into publication and their
release certificate is current. Canon, candidate, and publication are separate
concepts, so rejected or unfinished work is not exposed automatically.

The `sources/` tree is not part of the reader site and does not participate in
story lifecycle, naming, publication, or canon state. Every production story
uses the same metadata, release gate, page type, and canon workflow.

To preview the generated files locally:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
python -m pip install --requirement pages/requirements.txt
python pages/build.py --output _site
python -m http.server --directory _site
```

Every pull request and every push runs the cross-platform PowerShell tests and
validates the entire repository, regardless of which paths changed. The Pages
workflow also validates the complete pipeline before its Python tests or build;
pushes to `main` deploy only that checked result.

## Canon policy

Universe notes and explicitly promoted final stories are authoritative. Prompts,
plans, drafts, reviews, proposed deltas, and material marked `authority: none`
are not canon. A
released candidate becomes shared-universe canon only after the user explicitly
authorizes promotion, its facts are rechecked against current authority, and
the approved delta dispositions are applied one story at a time.

Codex detects repository skills automatically. If newly added custom roles do
not appear in an already-open task, start a new task or restart Codex.
