# Story Computing Machine

A small shared-universe story room. A `[WP]` prompt becomes four files:

```text
prompt.md → outline.md → story.md → review.md
```

The coordinator delegates one compact outline pass, one skilled prose pass,
and one independent review. The reviewer checks people, places, prompt
fulfillment, and continuity. There are no draft/final duplicates, canon briefs,
handoff ledgers, or release certificates.

## Quick start

1. Create `codex/story-<slug>` from current `main`.
2. Open this repository as the Codex workspace.
3. Submit a prompt such as:

   ```text
   [WP] Every city has a ghost assigned to it. Tonight, ours resigns.
   Target: about 3,000 words; close third person; melancholy but hopeful.
   ```

The default result is a reviewed, non-canon story. Adding it to shared canon is
a separate explicit user decision.

## Repository map

- `AGENTS.md` — the complete operating rules.
- `.agents/skills/story-room/` — the workflow and its two scripts.
- `.agents/skills/short-story-writing/` — the one compact prose-craft skill.
- `.codex/agents/` — the narrow outliner, writer, and reviewer roles.
- `stories/_template/` — the four-file scaffold.
- `universe/` — authoritative shared-universe facts and style constraints.
- `stories/` — locked legacy bundles and current four-file stories.
- `pages/catalog.json` — the stored publication snapshot used by Pages.
- `pages/build.py` — captures reviewed stories and renders the snapshot.

## Two validation phases

```powershell
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Phase Final
```

The agent runs the targeted pre-review phase before review and the final phase
locally after a passing review. Both ignore locked legacy bundles; semantic
noun extraction and continuity judgment remain the reviewer's responsibility.

## Pages

Pages does not read `stories/` during its build. Every passing story is handed
to the stored catalog once:

```powershell
python pages/build.py capture <slug>
```

Capture requires a passing review but does not duplicate the full story check.
Verify the stored snapshot and reader locally:

```powershell
python pages/build.py check
python -m unittest discover -s pages -p "test_*.py" -v
python pages/build.py build --output _site
```

After merge, GitHub Actions only builds, uploads, and deploys
`pages/catalog.json`; it does not rerun story validation or reader tests.
