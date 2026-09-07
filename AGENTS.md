# Story Computing Machine

This is a shared-universe fiction workspace. Stories and universe notes are the
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

## Pages

`pages/catalog.json` and `pages/covers/` are the stored publication snapshot;
`pages/timeline.json` is a reader-facing chronology model, not canon authority.
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
bundle index, catalog, chronology, cover-byte parity, and authoritative
source/catalog canon flags. Canon mismatches block publication until deliberately
reconciled through the named canon process.
