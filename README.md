# Story Computing Machine

A small shared-universe story room. A `[WP]` prompt becomes four authored files
and, after review, one title image. An explicit rewrite updates those same
artifacts in place while Git preserves the previous version:

```text
prompt.md → outline.md → story.md → review.md → title-image.jpg
```

The coordinator delegates fresh outliner, writer, and reviewer agents for each
story. The writer uses one local production adapter for in-place structural,
dialogue, and language revision; that writer may also make a targeted REVISE
pass, while every later review is fresh. The reviewer reads
the prose before the outline and checks people, places, prompt fulfillment,
dialogue, binding narrative policy, and continuity. For new stories it also
checks recent-story interchangeability. New prompts derive a dialogue promise, dialogic medium, dialogue
engine, and relationship movement before drafting; the illustrator
reads the finished prose and creates an exact 864x1536 portrait key visual.
Reference images attached to the prompt are inspected and supplied to both the
outliner and the cover generator; only their display names are recorded in
`prompt.md`, and the source images remain outside the story directory. There are
no draft/final duplicates, canon briefs, handoff ledgers, or release
certificates. Each cover includes the exact reader-facing story title once.

## Quick start

1. Open the primary `main` checkout as the Codex workspace.
2. Submit a prompt such as:

   ```text
   [WP] Every city has a ghost assigned to it. Tonight, ours resigns.
   Target: about 3,000 words; close third person; melancholy but hopeful.
   ```

   Attach any character, setting, object, mood, palette, or style references to
   that same request. Every supplied image will inform the outline and be passed
   as a reference input when generating the cover.

3. The coordinator updates `main`, creates `codex/story-<slug>`, adds a
   dedicated sibling Git worktree for the branch, and runs the complete story
   workflow from that worktree.

The default result is a reviewed, non-canon story. Adding it to shared canon is
a separate explicit user decision.

## Repository map

- `AGENTS.md` — the complete operating rules.
- `.agents/skills/story-create/` — the user-facing new-story coordinator.
- `.agents/skills/story-rewrite/` — the user-facing scoped rewrite coordinator.
- `.agents/skills/story-room/` — shared outline, review, and title-image stage
  contracts plus scaffold, rewrite-preparation, and validation scripts.
- `.agents/skills/short-story-writing/` — the compact project-owned production
  adapter that resolves upstream craft advice into one in-place prose workflow.
- `.agents/skills/creative-writing-craft/`, `dialogue/`, and `prose-style/` —
  pinned upstream craft references; the first is primary and the other two are
  diagnostic lenses inside the local adapter.
- `.agents/skills/story-analysis/`, `story-sense/`, and `sensitivity-check/` —
  pinned upstream review references used within the repository review contract.
- `skills-lock.json` — upstream skill sources, immutable commit refs, and content
  hashes for restoration and updates.
- `.codex/agents/` — the narrow outliner, writer, reviewer, and title-image roles.
- `stories/_template/` — the four-file scaffold.
- `universe/` — authoritative shared-universe facts and style constraints.
- `stories/` — legacy bundles and current story packages; title images live
  beside their story prose as `title-image.jpg`.
- `pages/catalog.json` — the stored publication snapshot used by Pages.
- `pages/covers/` — captured title images used by the index and story pages.
- `pages/build.py` — captures reviewed stories and renders the snapshot.

## Two validation phases

```powershell
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Phase Final
```

The agent runs the targeted pre-review phase before review, generates the title
image only after a passing review, and then runs the final phase locally. Final
validation requires a readable 864x1536 JPEG for every current story. For
`prospective-2026-08-23`, local validation also enforces the compact outline
ceiling, the three dialogue-design fields, the six-field Voice capsule, and the
existing structured dialogue verdict. The earlier 08-18 and 08-21 contracts
remain valid unchanged; 08-21 retains its five-field, 180-word Voice capsule.
Both phases ignore locked legacy bundles; semantic noun extraction, dialogue
judgment, and continuity
judgment remain the reviewer's responsibility.

## Rewriting a completed story

A rewrite is available only for an explicitly named, completed current-format
story with `canon: false`. Locked legacy bundles remain immutable; canon stories
require a separate retcon or canon decision.

After creating `codex/rewrite-<slug>` and its dedicated worktree, prepare the
same four-file package with:

```powershell
pwsh -NoProfile -File .agents/skills/story-room/scripts/prepare-rewrite.ps1 `
  -Story <slug> `
  -Title "<fresh story title>" `
  -Request "<verbatim rewrite request>" `
  -Scope Selective `
  -Keep "the two sisters' relationship" `
  -Change "the public confrontation" `
  -Remove "the breakfast epilogue" `
  -Cover Auto
```

Scopes are `Rebuild`, `Reshape`, and `Selective`. Rebuild produces new
whole-story prose and treats unnamed old material as flexible. Reshape rewrites
the whole execution while preserving unnamed material in substance. Selective
retains the existing prose and edits named Change or Remove targets plus the
smallest necessary seams. Selections may be passed through `-KeepExact`,
`-Keep`, `-Change`, and `-Remove`. Each scope's outside rule is fixed so the
preservation boundary cannot contradict the chosen mode; named selections are
the explicit exceptions to that default.

Cover policies are `Auto`, `Keep`, and `Regenerate`. Auto retains an
unchanged-title cover as a candidate for fresh visual comparison, but removes a
changed-title cover and records that fresh generation is required. Keep requires
an unchanged title and never generates a replacement automatically. Regenerate
removes the old cover after the Markdown reset succeeds and requires a fresh
image after the new prose passes review.

Preparation preserves the original prompt outside four managed rewrite
sections, keeps package identity, records the selection contract and
`prospective-2026-08-23`, and updates the package in one guarded operation with
rollback. Rebuild and Reshape reset prose; Selective preserves it. All scopes
use the same outliner, writer, reviewer, local production adapter, and six-field
Voice capsule as current CREATE, while the selection boundary controls how much
prior prose they may read and change.
Cover generation is conditional because a retained image may be reused after a
fresh six-gate pass; a valid final cover is still mandatory for completion. The
workflow finishes with conditional cover replacement, final validation,
recapture, commit, push, and a draft pull request. No backup prose or
rewrite-history artifact is created.

## Pages

Pages does not read `stories/` during its build. Every passing story is handed
to the stored catalog once:

```powershell
python pages/build.py capture <slug>
```

Capture requires a passing review but does not duplicate the full story check.
It stores the prose in `pages/catalog.json` and copies the title image into
`pages/covers/`. The Pages index renders cover cards with each story's title,
prompt, cover, created and edited dates, state, word count, and content rating;
each story page places the cover below its title and prompt.
Verify the stored snapshot and reader locally:

```powershell
python pages/build.py check
python -m unittest discover -s pages -p "test_*.py" -v
python pages/build.py build --output _site
```

After merge, GitHub Actions only builds, uploads, and deploys
the stored `pages/catalog.json` and `pages/covers/` snapshot with the reader
stylesheet; it does not rerun story validation or reader tests.
