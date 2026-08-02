# Story Computing Machine

A project-local Codex story room for short fiction in a shared universe. A prompt tagged `[WP]` moves through canon research, planning, drafting, continuity review, final editing, name validation, and release validation.

## Quick start

1. Create or switch to `codex/story-<slug>` from current `main`.
2. Open this repository as the Codex workspace.
3. Submit a prompt such as:

   ```text
   [WP] Every city has a ghost assigned to it. Tonight, ours resigns.
   Target: about 3,000 words; close third person; melancholy but hopeful.
   ```

4. The workflow keeps the prompt, authority inventory, brief, plan, draft, review history, final story, canon delta, handoff ledger, lifecycle record, and release decision together under `stories/<slug>/`.

A completed workflow produces a non-canon candidate. Canon promotion is a separate explicit decision.

## Trust and branches

The repository relies on the current checkout, Git chronology, strict schemas, transactional writes, specialist boundaries, pull-request co-change policy, automated checks, and human acceptance. It does not maintain a parallel custom file-fingerprinting system.

Story and universe changes are refused on `main`. Local story branches run focused checks; pull requests run the full repository and reader-site suite. `main` is intended to accept only current, passing squash merges through protected pull requests.

## Layout

- `AGENTS.md` — workflow, lifecycle, ownership, and branch rules.
- `.codex/agents/` — narrow specialist roles.
- `.agents/skills/` — workflows and integrity scripts.
- `schemas/pipeline-contract.json` — strict shared record contract.
- `universe/` — authoritative setting notes.
- `stories/` — production story bundles, index, registry, and legacy attestation.
- `sources/` — inert evidence and decision history.
- `pages/` — deterministic reader-site builder.

`story.json` v2 is lifecycle authority. `authority.json` v2 names the base commit and admitted authority inventory. `handoffs.json` v3 preserves ordered specialist work. `release.json` v3 records the review/name basis for publication. `promotion.json` v2 records one authorized canon transaction.

## Validation

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
pwsh -NoProfile -File tests/run.ps1
python pages/test_build.py
```

The 24 user-reviewed legacy stories are explicitly listed in `stories/legacy-acceptance.json`; no historical agent activity is fabricated for them.
