# Story Computing Machine

A small shared-universe story room. A `[WP]` prompt becomes four authored files
and, after review, one title image. An explicitly named replacement removes the
old package and creates the same clean shape while Git preserves its history:

```text
prompt.md → outline.md → story.md → review.md → title-image.jpg
```

The coordinator delegates fresh outliner, writer, and reviewer agents for each
story. The writer uses one local production adapter for in-place structural,
dialogue, and language revision; that writer may also make a targeted REVISE
pass, while every later review is fresh. The reviewer reads
the prose before the outline and checks people, places, prompt fulfillment,
dialogue, binding narrative policy, and continuity. For new stories it also
checks recent-story interchangeability. Clean CREATE prompts derive a dialogue promise,
dialogic medium, dialogue engine, and relationship movement before drafting;
the illustrator reads the finished prose and creates an exact 864x1536 portrait
novel cover.
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

   Additional context may follow in a separate paragraph. It remains in
   prompt.md for story production but is not displayed as the prompt on Pages.

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
- `.agents/skills/story-create/` — the user-facing new-story and replacement coordinator.
- `.agents/skills/story-room/` — shared outline, review, and title-image stage
  contracts plus scaffold and validation scripts.
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
- `stories/` — bundle-format and current-format story packages; title images live
  beside their story prose as `title-image.jpg`.
- `pages/catalog.json` — the stored publication snapshot used by Pages.
- `pages/covers/` — captured title images used by the index and story pages.
- `pages/timeline.json` — the curated in-universe era map and placement confidence
  used by the visual chronology.
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
Both phases validate current-format prose. Final validation also inventories
bundle-format packages and verifies that each has a boolean canon flag; semantic
noun extraction, dialogue judgment, and continuity judgment remain the
reviewer's responsibility.

## Replacing a completed story

A whole-story remake, rewrite, overwrite, or replacement uses the same
`story-create` workflow as a new story. It is available only for an explicitly
named package. The coordinator creates `codex/story-<slug>` and a dedicated
worktree before inspecting the target's canon marker or story inputs.

A canon story must first receive a separate marker-only unlock patch and commit.
For an editable target, the coordinator preserves every verbatim user-authored
prompt or request block, the new request, and every associated reference-image
display-name inventory. Machine selection, cover-policy, and workflow metadata
are discarded. The images must still be available as external paths or attachments; a display name
cannot recover an image, so inaccessible originals must be reattached.

The old package and its catalog entry, captured cover, chronology placement, and
bundle index row are then removed. `stories/NAMES.md` remains frozen production
memory, and authoritative universe facts are never removed as part of a
replacement. Once the target path is absent, `new-story.ps1` creates a clean
four-file package with the preserved prompt text and all accessible references.
The outliner, writer, and reviewer receive no prior outline, prose, review, or
cover. A replacement receives the ordinary CREATE craft profile, recent-story
comparison, fresh cover, final validation, capture, parity check, push, and draft
pull request.

A narrowly requested edit to one named non-canon bundle-format story may still
modify that bundle's prose directly under `AGENTS.md`'s canon-state rules. Completed
packages with historical rewrite sections remain readable, but those sections
are inert history and are never produced by the current workflow.

## Pages

Pages does not read `stories/` during its build. Every passing story is handed
to the stored catalog once:

```powershell
python pages/build.py capture <slug>
```

Capture requires a passing review but does not duplicate the full story check.
It stores the prose in `pages/catalog.json` and copies the title image into
`pages/covers/`. Capture and `capture-all` refuse to demote a catalog-canon story
when its source marker disagrees; reconcile that marker through the named canon
process first. When a Prompt section contains `[WP]`, only the text from that
marker to the end of its blockquote paragraph is reader-facing; surrounding
untagged context remains available in `prompt.md` but is omitted from Pages.
Legacy untagged Prompt sections continue to publish in full. The Pages index
renders cover cards with each story's title,
prompt, cover, created and edited dates, state, word count, and content rating;
each story page places the cover below its title and prompt. The separate
`timeline.html` page arranges every cover by its proposed place in the universal
chronology—not publication or reading order—from the first wonders through the
Long Zero and Joined-Sky reawakening. Solid, dashed, dotted, and open-split
rings distinguish fixed, inferred, speculative, and unresolved placement
confidence. Numbered era nodes order the eras; story groups inside each chapter
are explicitly unordered.
The chronology is a reader-facing working model; `universe/` remains the shared
fact authority. It uses the same captured cover files as the library and story
pages. The check command requires exact parity among source packages, the bundle
index, catalog, captured-cover bytes, chronology placements, and authoritative
source/catalog canon flags. Verify the snapshot and reader locally:

```powershell
python pages/build.py check
python -m unittest discover -s pages -p "test_*.py" -v
python pages/build.py build --output _site
```

After merge, GitHub Actions only builds, uploads, and deploys
the stored catalog, chronology map, captured covers, reader stylesheet, and
chronology interaction script; it does not rerun story validation or reader
tests.
