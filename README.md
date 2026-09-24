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
tone guide each edition's art direction. This prose-preserving process does not
produce comic pages or speech bubbles.

The agent proposes meaningful illustration moments and reference counts. You
approve the plan; the agent reviews character/location/object references, the
cover and a layout sample. After that it creates scenes and assembles the web reader,
and obtains independent review followed by your final approval. Request changes
through Codex: regenerate a named image, move or resize a placement, or revise
art direction. Changes renew the affected approval stages. The original cover
is reused unless you request a new edition cover; source stories remain intact.
Web-only is the default. The approved illustrated reader replaces the story at
its existing Library card and URL, preserving catalog metadata and position.
PDF generation and downloads are available only when requested.

See [illustrated-create](.agents/skills/illustrated-create/SKILL.md) for the stage
contract and [edition tooling](illustrated/README.md) for setup and commands.

## Draft a graphic novel from a story

```text
[GN] "Exact Story Title"
[GN] "story-slug" — use its existing illustrations as visual references
```

`[GN]` is a separate draft process for adapting a finished story into sequential
comic pages. It inspects the story's cover and suitable existing artwork,
proposes references and a page/panel script, then creates and independently
reviews one page at a time after explicit approval to try the plan. The selected
cover and all ordered comic-page images are assembled into edition.pdf exactly
once, after all image generation, corrections and reviews are complete. No
partial/progress PDFs, automatic rebuilds or HTML previews are part of GN.
The PDF has one complete image per page with preserved aspect ratios. A fresh reviewer
checks every rendered PDF page and the complete book before final user approval
of that exact PDF. Rendering it for inspection does not regenerate it; the final
deliverable is the PDF.

Read the [draft workflow and choices](graphic-novels/README.md) and
[written house style](graphic-novels/STYLE.md). Page composition follows the
story; the style is documented as text without a visual template preview.
Approved comics can be published as PDF downloads on their existing story pages;
comic creation and visual review remain an agent workflow.
`[GN]` has no aliases; `[Comic]` remains reserved. `[IL]` and all its existing
behavior stay unchanged. Graphic-novel output is separate from both the source
story and its illustrated edition.

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
- [graphic-novels/](graphic-novels/README.md): draft `[GN]` agent contract and comic house style.
- [illustrated/](illustrated/README.md): edition packages, house rules, lifecycle and PDF exporter.
- [stories/](stories/README.md): current and supported bundle packages;
  `_template/` supplies the four-file scaffold.
- `pages/catalog.json`, `pages/covers/`: story publication snapshot.
- `pages/illustrated.json`, `pages/illustrated/`: illustrated-edition snapshot.
- `pages/graphic-novels.json`, `pages/graphic-novels/`: comic PDF download snapshot.
- `pages/landscapes.json`, `pages/landscapes/`: landscape gallery snapshot and web images.
- `pages/interiors.json`, `pages/interiors/`: interior study snapshot and web images.
- `pages/characters.json`, `pages/characters/`: reviewed character sheet snapshot and web images.
- `pages/timeline.json`: retained chronology model; `universe/` remains authoritative.

GitHub Pages publishes the Library and story pages; an approved illustrated
edition replaces its story's reader and card presentation. A selected comic adds
a **Download comic PDF** link to the existing story reader. The
Chronology/Timeline page and its assets are no longer published, and the site
build and `python pages/build.py check` do not load chronology data. The model
and renderer remain in the repository for local reference.

The **Image Gallery** navigation link opens `gallery.html`: oil-painted landscape,
interior and character studies grouped by story, with search, story and study filters, and an image viewer.
Arrow keys move between paintings; Escape closes the viewer. Filter URLs can be
shared. Without JavaScript, every painting remains available as a direct image
link. Original PNGs live in each story's `art/landscapes/` and `art/interiors/`
directories. `python pages/build.py capture-landscapes` and
`python pages/build.py capture-interiors` independently save full-resolution WebP
copies, small thumbnails and their collection's gallery snapshot. Neither changes
prose nor recaptures the story catalog or the other art collection. Ordinary Pages builds copy those stored web images
without reading source artwork or encoding new images. The existing GitHub
Actions workflow deploys the gallery with the rest of the site after merge.

The art study explores the spaces of each story through oil painting, inspired
by the Group of Seven's bold colour shapes and expressive brushwork. Interior
studies carry that treatment indoors with visible impasto, warm and cool light,
and source-grounded architecture and furnishings. Choose about three compelling
settings per story, or different views of the same room when there is only one.
Stories set entirely outdoors receive no interior studies. These independent
environment paintings establish no new canon facts. They carry no added titles or
captions; signs and labels may appear when they belong to the story setting.
Open `gallery.html?type=interiors` to browse just the interior collection.
For a small batch, `python pages/build.py capture-interiors <slug> [<slug> ...]`
updates only those stories and retains the other stored interior studies.

Character reference sheets use **Sculpted Impasto**: expressive forms built from
thick oil paint, with each character's name and story title on a landscape 3:2
sheet. Originals live in `stories/<slug>/art/characters/<character-id>.png`.
The collection inventory is `pages/character-manifest.json`; each story's
`pages/character-specs/<slug>.json` records its source reading, character design,
selected references, generation and inspected-image review. These visual
interpretations establish no shared canon facts.

`python pages/build.py capture-characters <slug> [<slug> ...]` captures only
`completed` or `reused` characters with a passing visual review and current
source, specification, selected-reference and output hashes. Omit slugs to
capture all eligible specifications. Pending sheets are never selected from an
art-directory scan. Named capture preserves other stored stories, and neither
form changes the story catalog, prose, landscapes or interiors. View the
selected sheets at `gallery.html?type=characters`. Builds use the frozen
`pages/characters.json` and WebP copies without opening specifications, story
sources, original references or generation tools.

For each selected character, `output` is its repository-relative PNG path and
`outputSha256` pins the inspected bytes. `generation.prompt` records the actual
prompt; `generation.references` lists one to five selected inputs with `path`,
`sha256`, `role` and `inspected: true`. `validation` records `status: "PASS"`,
nonempty `evidence`, `sourceSha256`, `specificationSha256`, `outputSha256`, and an
identical `references` list. The source path/hash are the specification's flat
`source`/`sourceSha256` fields. Compute the specification pin with
`pages.landscape_gallery.character_specification_sha256(specification, character)`
after saving creative inputs and provenance. It excludes mutable status, output,
review and attempt history, while retaining the actual prompt and selected inputs.

Editorial removals are recorded in the collection's `pages/landscapes.json` or
`pages/interiors.json` as `excludedSources`, with the inspected source hash and a
story-specific reason. Remove their selected entries and web copies together.
Capture preserves these exclusions, including when an original remains in a
canon-locked story package; changing its pixels does not silently restore it.
Restoring a painting requires explicit editorial selection by removing its
exclusion before capture.

Reviewed replacement PNGs live in `pages/landscape-replacements/<slug>/<image-id>.png`
or `pages/interior-replacements/<slug>/<image-id>.png`, outside the original story
package. The matching collection snapshot selects that path in `source` and pins
its bytes with `sourceSha256`. Its `revision` records `originalSource`,
`originalSha256`, `correction`, `prompt`, and `generator`; the original source and
hash must match an `excludedSources` entry in the same collection. Capture
preserves that selection and refuses changed replacement bytes until the
selection is reviewed and updated. Named interior capture also supports stories
whose originals are all excluded, including those with only selected replacements.
Pages builds use only the stored WebP copies.

Replacement artwork keeps the collection's Canadian Group of Seven inspired
oil-painting direction. Inspect the original image as the style reference and
use the story-specific removal reason as correction context. Preserve broad
painted shapes, rhythmic brushwork, strong silhouettes and simplified detail
across the whole image, including interiors, buildings and any necessary small
figures. Paint texture alone does not establish a match. Review the actual
result against both the story and the original artwork before selecting it.

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

## Social link previews

The Library and standard/illustrated readers include Twitter large-image cards,
Open Graph metadata, and canonical URLs on `https://stories.rgbknights.com/`.
Story cards use the published writing prompt as their description (up to 200
characters). All cards share [the generated artwork](pages/social-preview.jpg),
a 1200×630 JPEG copied into the site by the build. If the public domain changes,
update `SITE_URL` in `pages/build.py`.

The artwork was generated with the built-in Codex image tool using this prompt:

```text
Use case: ads-marketing. Create a finished landscape social link preview for Story Computing Machine, a shared-universe fiction library. Canvas: exactly 1200 by 630 pixels. On warm ivory paper, set large, exceptionally readable dark espresso literary serif type on the left: "Story" / "Computing" / "Machine" on three lines, with the smaller subtitle "Shared-Universe Fiction". On the right, illustrate an open book whose curling pages become a luminous miniature landscape of a distant city, mountains, and stars, with subtle brass mechanical details near the binding. Use refined anime-inspired pen contours, delicate hatching, restrained watercolor washes, warm amber light and muted teal accents. Editorial book-jacket composition, generous breathing room, compelling at small mobile-card size. Keep all text and important artwork comfortably inside an 80-pixel safe margin. Only the exact title and subtitle are readable text. No people, logos, URLs, watermarks, mockup frame, or interface elements.
```

The title line spacing was refined with two built-in image edits:

```text
Use case: text-localization. Edit the supplied social preview image with one precise typography adjustment: add a little more vertical space between the three title lines "Story", "Computing", and "Machine". Preserve the exact serif typeface, font sizes, word widths, dark espresso color, left alignment, and spelling. Increase the baseline spacing by about 20 pixels per gap on the 1200×630 canvas: move "Story" about 40 pixels upward and "Computing" about 20 pixels upward, keeping "Machine" in its current position. The descenders should have visible breathing room above the following line. Keep the decorative rule, star, subtitle "Shared-Universe Fiction", paper texture, and entire book/landscape illustration in exactly their existing positions and appearance. Do not redraw, restyle, add, or remove any other elements. Preserve the 1200×630 landscape composition.
```

```text
Use case: text-localization. Make one precise correction to the supplied image. Keep the word "Story" exactly where it is. Move BOTH complete words "Computing" and "Machine" upward by the same small distance: 24 pixels in this supplied 1731×909 image (equivalent to about 17 pixels at 1200×630). Do not change their horizontal positions, serif typeface, font size, color, spelling, or word widths. This should give the three title lines evenly spaced baselines and restore a comfortable gap above the gold decorative rule. Keep the gold rule and star, "Shared-Universe Fiction" subtitle, paper background, book, mechanical details, city, mountains, sky, and every other part of the illustration as in the supplied image. Only the vertical position of the two specified title words changes. Preserve the landscape aspect ratio.
```

The large moon was removed, retaining the small moon on the curved line, with this built-in image edit:

```text
Use case: precise-object-edit. The user wants to KEEP the small moon because it belongs to the curved orbital line in the sky. Edit the supplied two-moon preview by removing ONLY the LARGE moon, the big round body toward the upper-left of the illustrated sky, above the mountains. Replace its disk with a natural continuation of the surrounding muted teal starry sky, preserving the bordering clouds. Keep the SMALL moon to its right exactly as it is, including its position on the curved line; preserve that whole curved line, the bright gold star, and all other stars. The finished sky has exactly one moon: the small moon on the line. Preserve the city, mountains, open book, brass details, paper texture, exact three-line "Story Computing Machine" typography with its existing wider vertical spacing, decorative rule, and "Shared-Universe Fiction" subtitle. Do not move, redesign, repaint, or restyle any other elements. Preserve the 1200×630 landscape composition.
```

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
python pages/build.py capture-graphic-novel <edition-slug>
python pages/build.py capture-landscapes
python pages/build.py capture-interiors
python pages/build.py capture-characters <slug>
python pages/build.py check
```

PreReview checks the current scaffold and declarations. Final checks the
completed structure, verdicts, inventory, and decodable cover. Semantic and
visual judgment remains with the reviewers. Bundle prose receives only
compatible checks.

For a local site preview:

```powershell
python pages/build.py build --output _site
```

Capture derives the public prompt on first publication and preserves editorial
catalog text on recapture. `capture-all` refreshes existing catalog entries only.
Both refuse canon demotion; see [Pages rules](AGENTS.md#pages). GitHub Actions
builds and deploys the stored snapshot after merge; it does not reopen story
sources or run production review.

`capture-graphic-novel` stores a separately approved and independently reviewed
comic PDF for an already cataloged story. It leaves prose, reader presentation
and catalog metadata intact. Later builds copy that frozen PDF; updating the
production edition requires a deliberate named recapture to change the download.

## Published media on R2

The Pages workflow builds the frozen `pages/` snapshots, uploads their images and
PDFs to Cloudflare R2, and verifies every public asset URL before deploying the
site. Library covers, gallery thumbnails and full images, illustrated readers,
PDF downloads, and the social preview use `https://art.rgbknights.com`. HTML,
styles, scripts, and fonts remain in the Pages artifact.

In GitHub repository **Settings → Secrets and variables → Actions**, publishing
uses these variables and secrets:

| Type | Name | Value |
| --- | --- | --- |
| Variable | `ASSET_BASE_URL` | `https://art.rgbknights.com` |
| Variable | `R2_BUCKET` | `story-computing-machine` |
| Variable | `R2_ENDPOINT` | The account's `https://<account-id>.r2.cloudflarestorage.com` S3 endpoint |
| Secret | `R2_ACCESS_KEY_ID` | Bucket-scoped R2 access key ID |
| Secret | `R2_SECRET_ACCESS_KEY` | Matching R2 secret access key |

The R2 credential needs **Object Read & Write** access to this bucket, and the
bucket's custom domain must be active. Account administrator access is not
needed. `R2_ACCOUNT_ID` may also be stored for reference; the workflow uses the
complete endpoint above. Do not put credentials in this repository.

Asset URLs contain a SHA-256 hash of the published bytes. Unchanged assets are
reused; updated art receives a new URL and can be cached for one year without
serving a stale image. Uploads never delete earlier objects, preserving existing
pages and rollbacks. PDFs include a download disposition for cross-origin links.
An upload or public URL check failure prevents Pages deployment.

For a local build that matches the deployed CDN links:

```powershell
python pages/build.py build --output _site --asset-base-url https://art.rgbknights.com --asset-output _assets
```

`_site/` contains the website; `_assets/` contains the staged binaries and upload
manifest. Both are disposable, ignored build outputs. The ordinary local preview
command above still copies assets into `_site/` and needs no R2 access. To run
the upload tests or publish a staged build locally, install
`pages/requirements-publish.txt`; the upload command is
`python pages/publish_assets.py --manifest _assets/manifest.json` and reads the
four `R2_*` connection/credential values listed above from the environment.

Pull requests test and build without using R2 credentials. **Actions → Pages →
Run workflow** uploads and verifies assets without deploying by default, including
when run on a branch. Selecting **deploy** publishes only when the selected ref is
`main`. A merge into `main` uploads the assets and deploys Pages automatically.

Continue generating and approving assets locally, then use the existing named
capture commands and commit the selected publication snapshots. GitHub runners
can only upload committed snapshots; they cannot see uncommitted local artwork.
This moves media out of the Pages artifact, while snapshots still reside in Git.
The sparse checkout excludes production artwork; moving snapshot bytes out of
Git would be a separate migration to reduce checkout size further.
