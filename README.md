# Story Computing Machine

A small shared-universe story room. A `[WP]` prompt becomes four authored files
and, after review, one title image. An explicit rewrite updates those same
artifacts in place while Git preserves the previous version:

```text
prompt.md → outline.md → story.md → review.md → title-image.jpg
```

The coordinator delegates one compact outline pass, one skilled prose assignment
with in-place structural, dialogue, and language revision,
one independent review, and one final-story title-image pass. The reviewer reads
the prose before the outline and checks people, places, prompt fulfillment,
dialogue, binding narrative policy, and continuity; the illustrator
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
- `.agents/skills/story-room/` — the create, rewrite, and review workflow plus
  scaffold, rewrite-preparation, and validation scripts.
- `.agents/skills/creative-writing-craft/`, `dialogue/`, and `prose-style/` —
  pinned upstream prose, scene, dialogue, and line-level craft references.
- `.agents/skills/story-analysis/`, `story-sense/`, and `sensitivity-check/` —
  pinned upstream review references used within the repository review contract.
- `skills-lock.json` — upstream skill sources and content hashes for restoration
  and updates; `.agents/skills/THIRD_PARTY_NOTICES.md` records attribution.
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
validation requires a readable 864x1536 JPEG for every current story. For the
new prospective craft profile, local validation also enforces the compact
outline ceiling and structured dialogue verdict. Both phases ignore locked
legacy bundles; semantic noun extraction, dialogue judgment, and continuity
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
  -Cover Auto
```

Cover policies are `Auto`, `Keep`, and `Regenerate`. Auto reuses the existing
cover when it still passes a fresh visual comparison against the rewritten
story and generates a replacement only when needed. Keep never generates a new
cover automatically. Regenerate removes the old cover during preparation and
requires a fresh image after the new prose passes review.

Preparation preserves the original prompt and package identity, adds the rewrite
request to `prompt.md`, and resets `outline.md`, `story.md`, and `review.md` to
clean scaffolds. The ordinary OUTLINE, WRITE, REVIEW, and REVISE stages then run
with the same upstream craft skills as a new story. Prior narrative artifacts
are out of scope unless the rewrite request explicitly names something to
retain; in that case, only the minimum relevant material is recovered from Git.
The workflow finishes with optional cover replacement, final validation,
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
