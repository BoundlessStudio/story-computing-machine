# Story Computing Machine

A project-local Codex story room for writing short fiction in one shared
universe. Give Codex a prompt tagged `[WP]`; the project instructions route it
through canon research, story architecture, drafting, continuity review, and a
final edit followed by review of the reader-facing story.

## Quick start

1. Open this repository as the Codex workspace.
2. Add known setting facts to `universe/` (or ask Codex to help seed them).
3. Start a new task with a prompt such as:

   ```text
   [WP] Every city has a ghost assigned to it. Tonight, ours resigns.
   Target: about 3,000 words; close third person; melancholy but hopeful.
   ```

4. Codex creates `stories/<story-slug>/` and keeps the prompt, canon brief,
   plan, draft, review, final story, and proposed canon changes together.

If length, point of view, or tone are omitted, the workflow records reasonable
defaults instead of stopping for low-impact questions.

## On-demand prompt discovery

Ask `Run the prompt scout` to have the project inspect the newest 100 previously
unscanned `[WP]` posts from r/WritingPrompts, rank all 100 against the persistent
taste profile, and return the best ten. Ask `Run the prompt calibrator` to get a
diverse comparison set drawn from ranks 11–100; ordering that set teaches the
scout what should rise or fall in later runs. Neither agent is scheduled.

Prompt rankings, deduplication IDs, feedback, and calibration history live in
`prompt-scout/`. Recommendations remain non-canon prompts until separately sent
through the story workflow.

## Project layout

- `AGENTS.md` — the project director and non-negotiable workflow rules.
- `.codex/agents/` — project-scoped specialist roles Codex can delegate to.
- `.agents/skills/` — reusable story-room workflows for those roles.
- `universe/` — the authoritative shared-universe notes.
- `stories/` — one directory per story plus an index, reusable template, and
  non-canon legacy archive under `stories/_legacy/`.
- `scripts/new-story.ps1` — optional deterministic story-folder scaffolder.
- `prompt-scout/` — on-demand Reddit prompt rankings and persistent taste data.

## Canon policy

Universe notes are authoritative. Drafts and plans are never canon. A final
story becomes shared-universe canon only after the user explicitly approves
its canon promotion; until then, `06-canon-delta.md` records proposed additions
without silently changing the setting.

Codex detects repo skills automatically. If newly added custom roles do not
appear in an already-open task, start a new task or restart Codex.
