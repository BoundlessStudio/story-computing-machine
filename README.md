# Story Computing Machine

A shared-universe fiction workspace. A writing prompt becomes a complete story
through specialist outline, prose, independent review, and cover assignments:

```text
prompt.md → outline.md → story.md → review.md → title-image.jpg
```

Stories, universe notes, and illustrated editions are the product. Story
production stays in these five artifacts, with Git preserving history and Pages publishing a stored snapshot.

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

## Illustrate a finished story

```text
[Illustrate] "Exact Story Title"
[IL] "Exact Story Title" cinematic
[IL] "story-slug" deluxe
```

`[IL]` is an exact shortcut for `[Illustrate]`. Both preserve the complete prose
and create an illustrated reading edition. Classic is the default; Deluxe adds
more art and Cinematic emphasizes full-page illustrations. Shared house rules
control typography and layout, while the source cover, references, and story
tone guide each edition's art direction. Comics and speech bubbles are deferred.

The agent proposes meaningful illustration moments and reference counts. You
approve the plan, then character/location/object references, the cover, and a
layout sample. After that it creates scenes, assembles the web reader and PDF,
and obtains independent review followed by your final approval. Request changes
through Codex: regenerate a named image, move or resize a placement, or revise
art direction. Changes renew the affected approval stages. The original cover
is reused unless you request a new edition cover; source stories remain intact.

See [illustrated-create](.agents/skills/illustrated-create/SKILL.md) for the stage
contract and [edition tooling](illustrated/README.md) for setup and commands.

## Project map

- [AGENTS.md](AGENTS.md): authority, permissions, artifact boundaries, worktrees.
- [universe/](universe/README.md): shared facts;
  [style guide](universe/style-guide.md): narrative policy and craft profiles.
- [story-create](.agents/skills/story-create/SKILL.md): coordination and completion.
- [story-room](.agents/skills/story-room/SKILL.md): outline, review, cover contracts,
  scaffold, and validation scripts.
- [short-story-writing](.agents/skills/short-story-writing/SKILL.md): prose adapter;
  other craft skills are pinned references tracked by `skills-lock.json`.
- `.codex/agents/`: story and illustrated-edition specialist entry points.
- [illustrated/](illustrated/README.md): edition packages, house rules, lifecycle and PDF exporter.
- [stories/](stories/README.md): current and supported bundle packages;
  `_template/` supplies the four-file scaffold.
- `pages/catalog.json`, `pages/covers/`: story publication snapshot.
- `pages/illustrated.json`, `pages/illustrated/`: illustrated-edition snapshot.
- `pages/timeline.json`: retained chronology model; `universe/` remains authoritative.

GitHub Pages publishes the Library, story pages, and approved illustrated readers/PDFs. The
Chronology/Timeline page and its assets are no longer published, and the site
build and `python pages/build.py check` do not load chronology data. The model
and renderer remain in the repository for local reference and dedicated tests.

The stored chronology reconstructs one world's long history through Galactic
Cycles, historical eras, and individual stories. An era groups stories by compatible
institutions, technology, magical conditions, and inherited history. Different
societies can coexist within a period; similar forms can recur long afterward.
Cycles are orbital units, so magic's extinction or return can happen within
one. The magic phase belongs to the era, not the entire cycle. An ordinary
story's lack of visible magic does not by itself place its society in the zero.
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
Four recurring histories connect the cycles: authority, public works,
extraordinary bodies, and inherited memory. These are editorial interpretations;
a continuous visual thread does not establish descent, common origin, or a
shared cause. `historyThreads` stages cite stories placed in their own cycles.
The retained model's dedicated validator requires complete coverage of its
selected stories, unique era IDs, historical
context for each era, finite windows contained by their eras, valid connection
endpoints and evidence categories, and a feasible partial chronological order
when called directly with that story selection. Both sides of the extinction and
return are checked, including when stories share an orbit with a boundary. History-current anchors
must belong to their cited cycles. Circular or transitively impossible sequences are rejected;
overlapping windows and independent display orders are supported.

`python pages/build.py check` validates source packages, the bundle index,
catalog, cover-byte parity, and authoritative source/catalog canon flags.
New publications do not require a chronology entry.

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
