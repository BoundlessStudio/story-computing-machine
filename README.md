# Story Computing Machine

A small shared-universe story room. A `[WP]` prompt becomes four files:

```text
prompt.md → outline.md → story.md → review.md
```

One writer/coordinator handles the first three. One independent reviewer checks
people, places, prompt fulfillment, and continuity. There are no draft/final
duplicates, canon briefs, handoff ledgers, release certificates, or per-stage
agents.

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
- `.agents/skills/story-room/` — the one workflow and its two scripts.
- `.codex/agents/story-reviewer.toml` — the one specialist.
- `stories/_template/` — the four-file scaffold.
- `universe/` — authoritative shared-universe facts and style constraints.
- `stories/` — locked legacy bundles and current four-file stories.
- `pages/catalog.json` — the stored publication snapshot used by Pages.
- `pages/build.py` — captures reviewed stories and renders the snapshot.

## One check

```powershell
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1
```

It ignores locked legacy bundles. For current stories it checks the four-file
shape, minimal story metadata, declared people/place nouns, and the final
continuity verdict.

## Pages

Pages does not read `stories/` during CI. Publish a reviewed story into the
stored catalog once:

```powershell
python pages/build.py capture <slug>
```

GitHub Pages subsequently validates and renders `pages/catalog.json` alone.
