# Story Computing Machine

A small shared-universe story room. A `[WP]` prompt becomes four authored files
and, after review, one title image:

```text
prompt.md → outline.md → story.md → review.md → title-image.jpg
```

The coordinator delegates one compact outline pass, one skilled prose assignment
with in-place structural and language revision,
one independent review, and one final-story title-image pass. The reviewer
checks people, places, prompt fulfillment, binding narrative policy, and
continuity; the illustrator
reads the finished prose and creates an exact 864x1536 portrait key visual. There are no
draft/final duplicates, canon briefs, handoff ledgers, or release certificates.
Each cover includes the exact reader-facing story title once.

## Quick start

1. Open the primary `main` checkout as the Codex workspace.
2. Submit a prompt such as:

   ```text
   [WP] Every city has a ghost assigned to it. Tonight, ours resigns.
   Target: about 3,000 words; close third person; melancholy but hopeful.
   ```

3. The coordinator updates `main`, creates `codex/story-<slug>`, adds a
   dedicated sibling Git worktree for the branch, and runs the complete story
   workflow from that worktree.

The default result is a reviewed, non-canon story. Adding it to shared canon is
a separate explicit user decision.

## Repository map

- `AGENTS.md` — the complete operating rules.
- `.agents/skills/story-room/` — the workflow and its two scripts.
- `.agents/skills/short-story-writing/` — the self-contained prose-craft skill
  and in-place revision pass for prospectively scaffolded stories.
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
validation requires a readable 864x1536 JPEG for every current story. Both
phases ignore locked legacy bundles; semantic noun extraction and continuity
judgment remain the reviewer's responsibility.

## Pages

Pages does not read `stories/` during its build. Every passing story is handed
to the stored catalog once:

```powershell
python pages/build.py capture <slug>
```

Capture requires a passing review but does not duplicate the full story check.
It stores the prose in `pages/catalog.json` and copies the title image into
`pages/covers/`. The Pages index renders cover cards with each story's title and
prompt; each story page places the cover below its title and prompt.
Verify the stored snapshot and reader locally:

```powershell
python pages/build.py check
python -m unittest discover -s pages -p "test_*.py" -v
python pages/build.py build --output _site
```

After merge, GitHub Actions only builds, uploads, and deploys
the stored `pages/catalog.json` and `pages/covers/` snapshot with the reader
stylesheet; it does not rerun story validation or reader tests.
