# Story Computing Machine

A shared-universe fiction workspace. A writing prompt becomes a complete story
through specialist outline, prose, independent review, and cover assignments:

```text
prompt.md → outline.md → story.md → review.md → title-image.jpg
```

The stories and universe notes are the product. Production stays in these five
artifacts, with Git preserving history and Pages publishing a stored snapshot.

## Start a story

Open the primary checkout in Codex and submit a prompt:

```text
[WP] Every city has a ghost assigned to it. Tonight, ours resigns.

Target: about 3,000 words; close third person; melancholy but hopeful.
```

Put additional context in a separate paragraph. Attach any visual references to
the request. The coordinator prepares a dedicated branch and sibling worktree,
then follows [story-create](.agents/skills/story-create/SKILL.md#workflow) through
a draft pull request. New stories are non-canon; promotion is a separate user
decision. For named replacements and localized edits, see
[permissions](AGENTS.md#canon-lock-and-story-editing).

## Project map

- [AGENTS.md](AGENTS.md): authority, permissions, artifact boundaries, worktrees.
- [universe/](universe/README.md): shared facts;
  [style guide](universe/style-guide.md): narrative policy and craft profiles.
- [story-create](.agents/skills/story-create/SKILL.md): coordination and completion.
- [story-room](.agents/skills/story-room/SKILL.md): outline, review, cover contracts,
  scaffold, and validation scripts.
- [short-story-writing](.agents/skills/short-story-writing/SKILL.md): prose adapter;
  other craft skills are pinned references tracked by `skills-lock.json`.
- `.codex/agents/`: four specialist entry points.
- [stories/](stories/README.md): current and supported bundle packages;
  `_template/` supplies the four-file scaffold.
- `pages/catalog.json`, `pages/covers/`: publication snapshot.
- `pages/timeline.json`: curated chronology; `universe/` remains authoritative.

The Chronology reconstructs one world's long history through Galactic Cycles,
historical eras, and individual stories. An era groups stories by compatible
institutions, technology, magical conditions, and inherited history. Different
societies can coexist within a period; similar forms can recur long afterward.
Each era explains its context and place in the larger succession. Era and
story windows describe possible horizons within a cycle, not measured durations.
Overlapping horizons allow regional contemporaries; a story's location is not
inferred from its position in a displayed list. Each has a placement rationale
in `pages/timeline.json`.
Grouping and broad succession are editorial proposals; established local
intervals and the worldline backbone constrain them. Exact Galactic dates
remain unresolved. Evidence labels describe established boundaries, constraints,
relative sequences, contextual evidence, or undated frames independently of
proposed placement. Connections distinguish direct sequences, explicitly proposed
historical interpretations, and thematic echoes. Only connections marked
`ordering: before` impose a relative order.
The page presents one vertical worldline, with the great ages, cycles, and eras
along the same path. Era entries open their stories, historical context, and
local sequences in a focused panel. Each story's “Place in history” disclosure
holds its placement rationale, internal sequence, recorded span, and connections;
older remembered events can reach outside the story's proposed era. Connections
open on demand and distinguish direct links, historical hypotheses, and echoes.
Search finds stories throughout the chronology without creating another timeline.
The same content remains available through native era and story disclosures
when JavaScript is unavailable.
The validator requires complete story coverage, unique era IDs, historical
context for each era, finite windows contained by their eras, valid connection
endpoints and evidence categories, and a feasible partial chronological order
before Pages can build. Circular or transitively impossible sequences are rejected;
overlapping windows and independent display orders are supported.

## Local commands

Install the Python dependencies, Markdown and Pillow:

```powershell
python -m pip install -r pages/requirements.txt
```

Run these from the story worktree at the appropriate workflow stage:

```powershell
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Phase Final
python pages/build.py capture <slug>
python pages/build.py check
```

PreReview checks the current scaffold and declarations. Final checks the
completed structure, verdicts, inventory, and decodable cover. Semantic and
visual judgment remains with the reviewers. Bundle prose receives only
compatible checks.

For tooling changes and a local site preview:

```powershell
python -m unittest discover -s pages -p "test_*.py" -v
python pages/build.py build --output _site
```

Capture derives the public prompt on first publication and preserves editorial
catalog text on recapture. `capture-all` refreshes existing catalog entries only.
Both refuse canon demotion; see [Pages rules](AGENTS.md#pages). GitHub Actions
builds and deploys the stored snapshot after merge; it does not reopen story
sources or run production review.
