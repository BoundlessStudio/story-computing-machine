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

4. Codex creates `stories/<story-slug>/` and keeps the prompt, canon brief,
   plan, draft, review history, final story, proposed canon changes, lifecycle
   metadata, and release certificate together.

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
binds publication readiness to the exact final prose, canon delta, final PASS,
and scoped name check. Human README and index fields are validated projections
of the machine record.

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
python -m pip install --requirement pages/requirements.txt
python pages/build.py --output _site
python -m http.server --directory _site
```

Pull requests validate repository integrity and the site build. Relevant pushes
to `main` deploy the checked result.

## Canon policy

Universe notes and explicitly promoted final stories are authoritative. Prompts,
plans, drafts, reviews, proposed deltas, and material marked `authority: none`
are not canon. A
released candidate becomes shared-universe canon only after the user explicitly
authorizes promotion, its facts are rechecked against current authority, and
the approved delta dispositions are applied one story at a time.

Codex detects repository skills automatically. If newly added custom roles do
not appear in an already-open task, start a new task or restart Codex.
