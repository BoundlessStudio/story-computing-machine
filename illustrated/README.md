# Illustrated edition tooling

Start with `[Illustrate] "Story Name"` or `[IL] "Story Name"` in Codex. Both
route to the same [production contract](../.agents/skills/illustrated-create/SKILL.md).
Use `deluxe` or `cinematic` after the title to change presentation; otherwise
Classic applies. [House rules](STYLE.md) define the shared typography/layout.

Source stories remain unchanged. Editions are separate derivative packages,
including when their source is canon. Do not create a package until the source
and dedicated worktree are resolved. Generation and approval are agent-driven;
the website is the published reader, not an editor. Web-only is the default.
The approved edition replaces the reader at the existing story URL and uses
that story's single Library card with its illustrated cover and label. Source
metadata, catalog position and count stay intact. No extra entry or original-reader
link is added. PDF output and its download link require an explicit request.
The reader retains a Writing Prompt box before the prose, using the exact
existing catalog prompt. Changes to that published prompt invalidate pending
render/review approval; edition workflow instructions never replace it.
Illustrated readers and early layout previews use the same Pages header as the
Library and ordinary stories: branding, Library, theme icons, and GitHub link.
Illustrated typography is confined to the reading area.

## Install

From the dedicated worktree, use an isolated Python environment. Web rendering
requires Python; the pinned Node/browser dependencies are only needed for an
explicitly requested PDF export.

```powershell
python -m venv --system-site-packages illustrated/.venv
illustrated/.venv/Scripts/python -m pip install -r illustrated/requirements.txt
```

For requested PDF output only:

```powershell
npm ci --prefix illustrated
npm run install-browser --prefix illustrated
```

On macOS/Linux the Python executable is `illustrated/.venv/bin/python`.
Use that environment for the following Python commands (or activate it first).
The fonts are bundled locally with their licenses, so rendering works offline.
The optional PDF exporter uses pinned Playwright Chromium; a system browser is not substituted.

Image generation uses the imagegen skill's built-in Codex tool by default; no
API key is required. The tool selects its backend model, so do not claim an
unreported API variant. Do not run a paid API/CLI fallback without an explicit
user request. Installation and lifecycle preparation make no image requests.
Legacy API editions retain their original provenance until deliberately changed.

The built-in tool accepts at most five reference images per call, including the
cover and any correction image. Select useful inputs for each asset and give
every original a useful role across reference development. Each character sheet
contains one identity only; it may show multiple views, expressions, outfits or
states of that character. Never combine identities to fit the five-image limit.
Use the exact source name as the readable heading and derive its filesystem-safe
filename from that name. An unnamed figure gets an accurate descriptive role
label, never an invented name. Interior scenes have no added lettering or
reference-sheet headings.

Each location reference image contains one distinct place in a single coherent
environment view. Give separate rooms, approaches, gates, streets and alleys
accurately named files; do not combine them into a montage or shared sheet.
When a different state needs a reference, use a separate asset only when
necessary and preserve that place's geography. Do not pack state views into one
image or combine locations to fit the reference-input limit.

Honor an explicit user art style. If none is specified, default to the anime
illustration style used for the repository's covers; see [art direction](STYLE.md#story-art-direction).
Accepted character sheets remain the concrete style anchor for an existing
edition rather than being replaced by a generic interpretation of that default.
Accepted character sheets set the rendering style for subsequent location and
object references. Attach their actual images as primary style inputs within
the five-image limit. Originals guide geometry/content; the cover contributes
subordinate style accents. Check matching pen contours, hatching, restrained
washes, paper texture and stylization, not just palette. Reject painterly,
photographic or 3D drift even when the image is otherwise attractive. Character
images condition style without adding their figures or sheet layout to locations.

## Lifecycle and layout

Run commands only inside the edition's worktree. Multiline requests, prompts,
evidence, and actual user approval responses go in temporary UTF-8 input files.

```powershell
python -m illustrated.edition new "Story Title" --request-file tmp/request.md
python -m illustrated.edition validate edition-slug --phase draft
python -m pages.illustrated_editions anchors edition-slug
python -m illustrated.edition --help
```

The planner fills plan.md and registers reference/scene assets using
`set-asset`. Each scene names an `after` anchor returned by `anchors`; IDs include
position and content so repeated paragraphs remain distinguishable and changed
source cannot silently reuse placements. Parse the complete Markdown; never
render individual prose fragments to insert images.

Before plan approval, map each major exchange to an illustration or explicit
prose-only treatment. Name the hardest or most important composition as the
centerpiece, list every reference's downstream use, and remove unused sheets.
A reference used through another needed reference counts as a downstream use.
Register the exact source instant and required/absent states for each scene,
and explain every input's identity, style, or geometry role. For example:

```powershell
python -m illustrated.edition set-asset edition-slug centerpiece --kind illustration --prompt-file tmp/centerpiece.md --state-file tmp/centerpiece-state.md --size 1536x1024 --after ANCHOR_FROM_COMMAND --layout inline --alt "Description of the planned scene" --reference character-id --reference setting-id --reference-role "character-id=Identity and rendering style" --reference-role "setting-id=Room geography at the scene's required state"
python -m illustrated.edition configure-production edition-slug --pilot centerpiece
python -m illustrated.edition approve edition-slug plan --decision-file tmp/user-plan.md
```

A scene-state file names the source moment, what is present, and what is absent
or changed. An example for a scene before assembly: "The apparatus is empty.
All sockets are visibly empty; the retaining rod has not been inserted."
Use compatible inputs; a reference showing full sockets and an inserted rod
would work against that state. Change the reference or framing before spending
more generations on conflicting instructions.

After actual plan approval, generate only the centerpiece's required reference
chain and cover first. Prepare one built-in call at a time:

```powershell
python -m illustrated.edition prepare-tool edition-slug asset-id
# Call Codex's built-in image tool with the returned prompt and image paths.
python -m illustrated.edition record-tool-output edition-slug asset-id PATH_FROM_TOOL --evidence-file tmp/tool-output.md
# Inspect the saved pixels before accepting or rejecting.
python -m illustrated.edition accept edition-slug asset-id --evidence-file tmp/image-review.md
```

For a small defect in an otherwise successful rejected image, edit its verified
pixels while preserving the rest of the scene:

```powershell
python -m illustrated.edition prepare-tool edition-slug asset-id --edit-last-rejected --reference accepted-character-id --reference accepted-object-id --correction-file tmp/correction.md
```

The rejected image is the first input and counts toward the five-image limit.
Choose accepted dependencies relevant to the edit, keeping the input set small.
Unchanged people and places are preserved from the verified base; changes to
character identity, clothing or state require that character's sheet.
The request records the target and selected input hashes; use its paths
and order exactly. This is a counted correction with the same source,
dependency, and applicable legacy attempt checks as a fresh generation.
`--dry-run` checks preparation without consuming an attempt.

Keep the edit prompt limited to the correction and the details that must stay
fixed. Do not resend the full scene-generation brief or ask for fresh art
direction. Inspect the entire result for unintended changes: preservation is
not guaranteed to be pixel-identical. This follows OpenAI's
[current image prompting guidance](https://developers.openai.com/api/docs/guides/image-prompting)
and [Codex image editing guidance](https://learn.chatgpt.com/docs/image-generation),
checked September 13, 2026. Images 2.5's announced editing improvements do not
change the local tool interface: use the built-in image inputs and prompt,
without inventing API-only mask, action or model-selection parameters.

To migrate an existing edition with explicit user authorization, use
`configure-workflow edition-slug --backend codex-imagegen --visual-review-policy assistant --decision-file FILE`.
This records the actual decision and invalidates affected approval state.
Use `configure-output edition-slug --format web --decision-file FILE` to switch
an older edition to web-only. Use `--format web-pdf` only for an explicit PDF
request. New editions default to web; old manifests preserve their original
output choice until deliberately changed.

New editions use `productionPolicy` version 1. For an existing edition, adopt
it only with explicit user direction using
`configure-production edition-slug --pilot centerpiece --decision-file FILE`,
then renew plan approval. Migration preserves old attempts and provenance.
Unmigrated editions keep their historical stage ordering and three-attempt
allowance; `extra-attempt` remains their explicit extension mechanism.

Once the centerpiece's references and cover are inspected and accepted:

```powershell
python -m pages.illustrated_editions layout-sample edition-slug --output tmp/layout-sample
python -m illustrated.edition layout-preview edition-slug tmp/layout-sample/stories/source-slug.html --evidence-file tmp/layout-evidence.md
python -m illustrated.edition review-visuals edition-slug --pilot --reviewer coordinator --evidence-file tmp/pilot-visual-review.md
# Generate, inspect, and accept the centerpiece with the lifecycle above.
python -m pages.illustrated_editions layout-sample edition-slug --output tmp/layout-sample
python -m illustrated.edition layout-preview edition-slug tmp/layout-sample/stories/source-slug.html --evidence-file tmp/pilot-layout-evidence.md
python -m illustrated.edition review-pilot edition-slug --reviewer coordinator --evidence-file tmp/pilot-review.md
```

Use the exact returned reader path, substituting the real source slug. The
first sample can use an accepted reference while other references remain
pending. The second uses the accepted centerpiece's actual pixels, anchor,
and layout. Inspect its narrative impact, scale, state, and framing at desktop
and mobile reading sizes. After that assistant review passes, produce the
remaining references, record ordinary full `review-visuals` for the complete
reference set/cover/layout, and generate the remaining scenes.
Remaining references may use the reviewed centerpiece, but cannot depend on
later scenes: the full reference review must precede those scenes.

These reviews belong to the assistant. The user approves the plan and final
edition; there is no new routine permission stage. If the user explicitly
requests intermediate approval, use `approve edition-slug pilot-visuals
--decision-file FILE` for the initial centerpiece visual inputs and honor the
configured approval workflow thereafter.

New-policy editions have no numeric generation budget or per-asset cap.
Correct visible problems within the requested scope. After two unsuccessful
fixes, diagnose the cause and change composition, conflicting references, or
state guidance instead of repeating the same call. Ask only for an actual
blocking tool/access/source issue or a user-owned decision. Preserve counters
and provenance when changing strategy, renaming files, or resuming work.

Use `python -m illustrated.edition stats edition-slug` for compact recorded
outcomes, durations, and unused-reference diagnostics. Historic missing timing
stays unknown; attempt counts cannot establish weekly account usage. Statistics
use attempt evidence from the existing manifest and produce command output,
without extra records.
Assign artists one asset with bounded instructions and exact source/reference
paths. For historical audits, read sanitized local text extracts and inspect
selected image files separately; avoid image-heavy `read_thread` payloads that
can overwhelm the app.

After every scene is accepted:

```powershell
python -m pages.illustrated_editions render edition-slug
python -m pages.illustrated_editions preview edition-slug --output tmp/edition-preview
python -m illustrated.edition record-review edition-slug --reviewer independent-agent-id --evidence-file tmp/review-evidence.md
python -m illustrated.edition approve edition-slug final --decision-file tmp/user-final.md
python pages/build.py capture-illustrated edition-slug
python pages/build.py check
python pages/build.py build --output _site
```

Rendering creates edition.html. The preview command returns
`stories/<source-slug>.html` inside a disposable Library copy, with the same
single story card, illustrated cover/label, and complete shared Pages header.
It does not capture or publish anything. Inspect the complete HTML at mobile
and desktop widths before independent review/final approval. Only when PDF
output was requested, render also creates the digital 6×9-inch edition.pdf;
inspect every PDF page with the PDF skill and include its download link.
Temporary previews are not
publication. The original must already be published, with reconciled canon
markers, before capturing its edition. Commit, push, and open a draft PR.

Source changes pause production. Explicit source repinning is a user version
decision and invalidates dependent approvals/assets while retaining attempts.
Existing published editions remain frozen until named recapture. A second
production edition needs another slug. Named final-approved capture replaces
the published selection for that source story; only one edition supplies its
Library card and reader. Captured prose/art remain stored separately from the
unchanged original catalog and source package. Ordinary capture/capture-all
never refresh an edition.

Shared-header/template fixes take effect when Pages rebuilds the stored
snapshots; they require no art regeneration, production-package edits, or
recapture. For new artwork, capture is still required. A draft PR is reviewable
work, not a changed live reader: verify the selected illustration snapshot at
the built story URL and report deployment status separately from PR creation.
