# Story Computing Machine

This is a shared-universe fiction workspace. Stories, universe notes, and illustrated editions are the
product; process records are not. This file owns authority, permissions,
artifact boundaries, and worktree rules. Production details belong to the
linked contracts below.

## Authority

Read [universe/README.md](universe/README.md) before interpreting canon.
`universe/` alone establishes shared facts: `LOCKED` precedes `CANON`, and
`PROVISIONAL` is nonbinding guidance. Never silently reconcile conflicting
authority; obtain a user ruling and record an approved retcon in
`universe/retcons.md`.

[universe/style-guide.md](universe/style-guide.md) owns binding narrative
policy, including [story craft defaults](universe/style-guide.md#story-craft-defaults),
dialogue standards, and prospective profile semantics. A new profile does not
reopen completed stories. For an existing package, its complete recorded prompt
remains the acceptance authority and its last recorded profile remains active.
Historical rewrite sections are inert acceptance context, not edit permission;
do not create new managed rewrite sections.

The prompt controls acceptance; the outline is advisory intent. Neither prompts,
outlines, reviews, plans, source notes, nor non-canon stories establish shared
facts. `stories/NAMES.md` is frozen production memory, not canon; passing current
`review.md` inventories extend name memory without another central record.

## Two story layouts

A current story contains exactly four authored Markdown files and, after a
passing review, one generated image:

- `prompt.md`: verbatim user request, explicit constraints, reference-image
  display names, and the applicable craft profile.
- `outline.md`: draftable narrative design, proposed people and places, and
  relevant continuity boundaries.
- `story.md`: reader-facing prose and minimal metadata; its frontmatter is the
  authoritative canon marker.
- `review.md`: final people/place inventory, verdicts, and blocking findings.
- `title-image.jpg`: the final-story 864×1536 (9:16) portrait cover; never canon
  authority. Its exact title and visual requirements belong to
  [Title image](.agents/skills/story-room/SKILL.md#title-image).

The scaffold contains only the four Markdown files until review passes. No
other files belong in a current story directory. Do not create draft copies,
canon briefs or deltas, authority snapshots, handoff guards, release or promotion
records, ledgers, receipts, story READMEs, index rows, or duplicate lifecycle
artifacts. Git preserves history. Supporting judgments belong in the existing
artifacts or conversation; optional craft-skill scripts and persistence outputs
are forbidden.

A package containing `05-story.md` uses supported bundle format. Its
`story.json` canon flag is authoritative; extra historical files are not
lifecycle authority. Keep that layout during localized edits. Current-format
validation does not certify bundle prose. Pages capture supports both layouts.
An authorized title-image assignment may add or replace `title-image.jpg`
beside a non-canon bundle without reopening its prose.

Reference images remain external inputs. Record their display names in
`prompt.md`; never copy them into the story package or treat them as canon.
Resolve and visually inspect every original and provide them to both outliner
and illustrator. A display name is not a path. If an original cannot be
accessed, restore access or ask for reattachment; never silently omit it. Written
prompt and universe authority control outlining conflicts; final prose controls
depicted story facts unless the prompt explicitly makes an image detail binding.
The stage contracts specify inspection and image-generation requirements.

## Branches

Before any new story, replacement, or AI-performed story edit, make branch
setup the first repository action:

1. Switch the primary checkout to `main`.
2. Pull `origin/main` with a fast-forward-only pull.
3. Create `codex/story-<slug>` from updated `main`, leaving the primary checkout
   on `main`.
4. Add a dedicated sibling worktree for that branch. Use it for the coordinator
   and every delegated agent throughout production.

Do not scaffold, inspect replacement or edit material for production, or modify
story files before this sequence completes. Resolve and retain the absolute
worktree path before delegating; include it in every assignment. Run validation,
capture, Git, push, and pull-request commands there. If local changes prevent a
safe switch to `main`, or the intended worktree path is occupied, stop and ask
how to preserve or reuse it. Never change `stories/` or `universe/` in the primary
`main` checkout. Merge story branches through pull requests.

## Canon lock and story editing

Canon state alone controls editability, regardless of age, layout, status,
editor identity, or process metadata. After worktree setup, inspect only the
named story's authoritative marker before reading for production:
`story.md` frontmatter for current format, `story.json` for bundles. If the
state file is missing, invalid, or ambiguous, stop for user direction.

Humans and AI may directly edit a story only with `canon: false`. An explicit
localized-edit request for that named non-canon story is sufficient AI
authorization; require no special waiver. A whole-story remake, rewrite,
overwrite, or replacement uses
[Replacement](.agents/skills/story-create/SKILL.md#replacement), which removes
the named package before clean creation. It is never an in-place rewrite.

With `canon: true`, reject an edit or replacement request. Do not edit,
overwrite, regenerate, or remove any package file. Such a request does not
authorize an unlock. A review, critique, general approval to improve stories,
or unnamed request authorizes neither editing nor unlocking.

An explicit request to unlock one named story authorizes a separate action:
change only its authoritative canon marker from `true` to `false` in its own
verified patch and commit. Do not combine that commit with prose, cover,
review, catalog, captured-page, or universe edits. Complete and verify the
marker-only commit before beginning any subsequently authorized content work.

If the source says `canon: false` while the publication catalog says canon, and
no verified authorized unlock commit explains it, treat the story as locked and
stop for an explicit reconciliation ruling. Never exploit an unexplained false
marker or silently demote publication through capture. A verified authorized
unlock commit reconciles editability even while the catalog retains its former
state; capture remains blocked until the named publication state is deliberately
reconciled.

Unlocking does not demote or erase `LOCKED` or `CANON` universe facts. An edit
that changes those facts requires a separate user-approved canon or retcon
ruling. Prose changes preserving those facts need no additional ruling.

### Localized edits

Limit work to the named story and authorized files or changes. Use the smallest
edit consistent with the request; do not expand it into general modernization.
Patch current `story.md` or the authorized bundle prose directly, preserving its
layout. Leave other package and historical bundle files unchanged unless
explicitly included or a current-format prose change requires a fresh
`review.md`.

Inspect the resulting prose and diff. For current format, run
`Test-Stories.ps1 -Story <slug> -Phase PreReview`, obtain a fresh independent
[Review](.agents/skills/story-room/SKILL.md#review), and run Final validation
after PASS. A targeted REVISE uses the ordinary writer/reviewer loop with a fresh
reviewer; it need not become a replacement. Bundle edits receive compatible
targeted checks; neither current-format validation nor an old bundle review
certifies changed prose. State when an old review, cover, or Pages snapshot may
be stale. Do not refresh publication until the changed story has the required
passing review.

## Canon promotion

New stories start with `canon: false`. Promotion requires explicit user approval
for one named story and a fresh passing review against current authority. Add
or amend only the smallest relevant universe entries needed for newly
established facts, then set the authoritative canon flag to `true`. A conflict
with `LOCKED` canon stops for a user ruling. Git records the transaction; create
no promotion or delta artifact. Promotion locks every story-package file under
the rules above.

## Production contracts

Use [story-create](.agents/skills/story-create/SKILL.md#workflow) for new `[WP]`
stories and named replacements. Its
[Collection context](.agents/skills/story-create/SKILL.md#collection-context)
owns recent-story selection and the rolling audit; its
[Publication](.agents/skills/story-create/SKILL.md#publication) owns validation,
capture, commit, push, draft PR, and completion. A replacement preserves every
verbatim user-authored request and associated reference inventory, while
discarding machine workflow metadata and all prior creative artifacts, as
specified in [Replacement](.agents/skills/story-create/SKILL.md#replacement).

Use [story-room](.agents/skills/story-room/SKILL.md) for the shared
[Outline](.agents/skills/story-room/SKILL.md#outline),
[Review](.agents/skills/story-room/SKILL.md#review), and
[Title image](.agents/skills/story-room/SKILL.md#title-image) stages, or one
explicitly requested stage. Use
[short-story-writing](.agents/skills/short-story-writing/SKILL.md#inputs) for
prose [drafting and revision](.agents/skills/short-story-writing/SKILL.md#draft-and-revise).
Those contracts own role inputs, writable files, stage ordering, independent
review, name checks, and all seven saved-pixel cover gates. Mechanical validation
never replaces semantic review or the coordinator's independent image review.

## Illustrated editions

`[Illustrate] "Story Name" (details)` and `[IL] "Story Name" (details)` are exact
aliases for [illustrated-create](.agents/skills/illustrated-create/SKILL.md).
Classic is the default; Deluxe and Cinematic change presentation, not the prose
or art style. `[WP]` continues to create stories. `[Comic]` is reserved for a
future workflow; V1 does not produce comics or panel scripts.

Editions live in the separate `illustrated/` collection. A package contains
`prompt.md`, `plan.md`, `edition.json`, `review.md`, selected cover/reference/
illustration assets, and `edition.html`. Add `edition.pdf` only when explicitly
requested. The four-file story rule applies to
`stories/`, not edition packages. Temporary candidates/previews stay outside
packages. No duplicate prose drafts or additional lifecycle records are allowed.

The original current or bundle story, its prompt, cover, and canon marker are
read-only inputs, including when canon is true. Creating or revising an edition
is not a source edit or unlock and never establishes universe facts. Preserve
universe authority and binding narrative policy; do not re-review/rewrite old
prose under a new profile. Missing/ambiguous source identity and substantive
source/authority conflicts require user direction. References remain external
inputs except generated approved sheets and the reused edition cover.

Extend the branch sequence above to editions using `codex/illustrated-<slug>`.
Resolve a dedicated absolute sibling worktree before production or delegation;
leave the primary checkout on main. Keep the same safe-switch and occupied-path
stops. Never write an edition in the primary checkout. Explicit edits can resume
an edition; another edition needs a distinct slug and never implicitly overwrites.

The user approves the plan/counts. The assistant then reviews and corrects the
selected references, cover, layout and scene artwork before presenting the
independently reviewed final web edition for the user's final approval. PDF
generation, page review, and download links are optional and require a user request.
Record intermediate assistant review separately from user approval. User approval
is an actual response bound to exact inputs, never an agent verdict or elapsed time.
Use the imagegen skill's built-in Codex image generation by default, with accepted
reference images attached, one asset per call. New editions resolve the
centerpiece and its necessary references first, then review its actual pixels
in the reading layout before producing the remaining artwork. Map major
exchanges to images or explicit prose-only treatment, justify every reference
through a downstream use, and bind scene states and reference roles in the
existing plan/manifest. Correct within the authorized scope; after two
unsuccessful fixes, diagnose the cause and change the composition or conflicting
inputs. New editions have no numeric generation budget or attempt cap. Legacy
manifests retain their recorded production rules until explicitly migrated;
never reset their attempt history. Do not use the API, an API key, a CLI
image runner or another paid fallback unless the user explicitly requests that
path. Do not claim a specific backend model variant when the built-in tool does
not report it. Persist actual tool provenance and attempts across resumes. Source
or dependency changes block stale approval use; the stage contract owns renewal
and explicit repinning.

Before plan approval, obtain an independent pre-generation review of the briefs
and reference dependencies, repair concrete findings, and recheck affected
inputs. Before every image call, check the complete prepared prompt against
the source moment, actual selected reference pixels, feasible framing and
reading size. Resolve contradictions before generation; do not use generated
candidates to discover problems visible in the brief. These are assistant
checks, not extra user approval stages. The illustrated-create contract owns
the review loop and its existing-artifact evidence.

Each character reference sheet depicts one identity only; multiple viewpoints,
expressions, outfits, or states of that same character are allowed. Use the exact
source name in its readable heading and an unambiguous filename derived from
that name. For unnamed figures, use accurate descriptive role labels without
inventing names. Each location reference image depicts one distinct place in a
single coherent environment view, with no montage or combined location sheet.
Separate rooms, approaches, gates, streets, and alleys into accurately named
files. When a different state needs its own reference, use a separate asset that
preserves the same place's geography rather than packing states into one image.
Interior illustrations do not carry reference-sheet headings.
The built-in image tool accepts at most five reference images per call. Select
useful inputs for each asset and assign every original a useful role across the
edition; never combine characters or locations to evade that limit.

Honor an explicitly requested art style. When none is specified, default to the
anime illustration style used for the repository's covers. Once character
sheets are accepted, their actual rendering remains the concrete style anchor;
do not replace it with a generic interpretation of the default.
Accepted character sheets establish the rendering style for subsequent location
and object references. Attach their actual image bytes as the primary style
inputs; originals guide geometry and content, while the cover supplies
subordinate style accents. Match the character sheets' pen contours, hatching,
restrained washes, paper texture, and stylization, not just their palette.
Reject painterly, photographic, or 3D drift even when the image is otherwise
attractive. Plan these style dependencies within the five-input limit.

`pages/illustrated.json` and `pages/illustrated/` store approved artwork and prose
snapshots backing the existing story catalog. An approved illustrated edition
replaces the reader at `stories/<source-slug>.html` and uses that story's one
Library card, with its illustrated cover and label. Preserve the source title,
catalog position, metadata, and count.
Use the same shared Pages header in illustrated readers and early layout
previews, including branding, Library, theme controls, and the repository link.
Scope illustrated styling to the reading area. Header/template fixes apply to
builds of stored snapshots without regenerating art or recapturing an edition.
Keep the existing catalog Writing Prompt visible before the story prose, using
the exact published text and literal HTML escaping, separately from story content.
Do not substitute edition workflow instructions or a regenerated prompt.
Do not add a second entry or reader, an
Original story self-link, or a PDF link when no PDF was requested. Keep the source
package and `pages/catalog.json` intact. Only one edition per source is selected
for publication; named approved capture replaces the previous selection.
Named `capture-illustrated` requires final approval,
independent PASS, unchanged source, and deliberately reconciled source/catalog
canon. It never publishes the original story implicitly. Ordinary capture and
capture-all never refresh editions. Published editions stay frozen until an
explicit recapture; Pages builds use stored prose/art and any requested PDF only and never render
PDFs, generate art, or traverse production sources. Merge edition branches
through draft pull requests, never automatically.

## Graphic novels (draft)

`[GN] "Story Name" (details)` starts the separate
[graphic-novel-create](.agents/skills/graphic-novel-create/SKILL.md) draft workflow.
It takes a finished repository story title or slug and proposes a sequential
panel adaptation using the source cover and suitable existing illustrations as
visual inputs. While the contract is draft, prepare the concrete plan for user
review; image generation needs explicit approval to try that plan. `[GN]` has
no aliases. `[Comic]` remains reserved. `[Illustrate]` / `[IL]`, their contracts,
agents, tooling, artifacts and publication behavior are unchanged.

Graphic novels belong in `graphic-novels/<edition-slug>/`, separate from source
stories and prose-preserving illustrated editions. Read
[graphic-novels/STYLE.md](graphic-novels/STYLE.md) for panel interaction,
palette, lettering and visual continuity rules. The draft contract owns package
files, source pinning, adaptation coverage, reference reuse, one-page-at-a-time
generation, independent per-page review and a fresh complete-book review.
The user approves the plan and independently reviewed final PDF book; intermediate
reference/page checks are assistant reviews unless more checkpoints are requested.

Extend the branch sequence to this workflow with
`codex/graphic-novel-<edition-slug>` and a dedicated absolute sibling worktree.
Keep the same safe-switch and occupied-path stops, and pass that worktree to
every agent. Canon and non-canon stories may be read for adaptation; every
source-package file and existing illustrated edition remains read-only.
Adaptations establish no universe facts and authorize no unlock or source edit.

Existing source covers and compatible same-story artwork may supply inspected,
versioned references; never silently inherit stale art or a prior edition's
visual departures. Generate one reference or one complete comic page per built-in
image-tool call and inspect its actual pixels. Page N must pass independent
review before page N+1 is generated. Assemble the selected cover and all ordered
comic-page images into `edition.pdf`, one image per PDF page, with no omissions
or duplicates and no cropping or stretching. References remain production assets
unless the user expressly requests an appendix. Use the PDF skill, inspect every
rendered PDF page at full and reading sizes, and obtain a fresh independent
complete-book review. Bind final user approval to the actual PDF hash. An HTML
preview is optional temporary production material outside the package, not the
final deliverable. Keep exact panel transcripts in the existing plan.
PDF is the required final GN output. The draft has no comic generation CLI or
automated lifecycle validator. After final approval, named
`python pages/build.py capture-graphic-novel <edition-slug>` stores the reviewed
PDF in `pages/graphic-novels/` with its selection in `pages/graphic-novels.json`.
Capture requires an unchanged source, matching source/catalog canon, current
selected-image/PDF hashes, independent complete-book PASS and final approval
bound to those exact bytes. It never captures the source story implicitly.
One selected comic per source adds a `Download comic PDF` link to that story's
existing standard or illustrated reader. Preserve the reader, prose, Writing
Prompt, Library card, catalog metadata and any illustrated PDF download.
Ordinary story/illustrated capture does not refresh comics. Pages builds copy
only the stored comic PDF, without traversing production editions or generating
art/PDFs. Published comic downloads stay frozen until an explicit named recapture.
Merge any later edition branch through a pull request, never automatically.

## Pages

`pages/catalog.json` and `pages/covers/` are the stored story publication snapshot;
`pages/graphic-novels.json` and `pages/graphic-novels/` store approved comic PDFs
linked from their existing story readers. No comic snapshot means no comic link.
`pages/timeline.json` is a retained local chronology model, not canon authority
or a required publication artifact.
Pages builds publish the snapshot only, without traversing `stories/` or running
story validation. Capture requires a passing review without repeating full
validation.

On first capture, `[WP]` identifies the reader-facing prompt through the end of
its blockquote paragraph; surrounding context remains in source `prompt.md`.
Legacy untagged Prompt sections publish in full. Later capture and `capture-all`
preserve the existing catalog prompt as editorial publication text. An
authorized public-prompt edit changes that catalog field directly.

Keep the catalog ordered by full creation timestamp, newest first. New
scaffolds record `created-at`; date-only sources combine `created` with prose
filesystem modification time. `capture-all` refreshes only existing catalog
stories, never republishes an unpublished package, refuses source/catalog canon
demotion, and is not used by CI. `python pages/build.py check` checks source,
bundle index, catalog, cover-byte parity, and authoritative
source/catalog canon flags. Canon mismatches block publication until deliberately
reconciled through the named canon process.
