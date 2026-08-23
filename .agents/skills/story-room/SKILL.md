---
name: story-room
description: "Create, rewrite, or review a shared-universe short story using only prompt, outline, story, and review."
---

# Story room

Use for `[WP]` prompts, an explicit rewrite of one named current story, or a
named story stage. Prefer safe, low-impact assumptions over questions. Default
to a coherent 2,500–4,000 word story unless the prompt says otherwise.

For CREATE mode, the scaffold marks the self-contained prospective craft profile
implemented by the binding style defaults, compact outline handoff, prose skill,
and dialogue-aware review.
Completion alone never authorizes reopening. Use REWRITE mode only when the
user explicitly requests a rewrite of one named non-canon current story. Locked
legacy bundles remain immutable.

## CREATE mode

1. Work on a non-main branch. Identify and visually inspect every reference
   image supplied with the request, then scaffold with `scripts/new-story.ps1`,
   passing those paths or attachment labels through `-ReferenceImage` so
   `prompt.md` inventories their display names. Record `None supplied` when the
   request has no reference images. Reference originals remain external inputs;
   never copy them into the story directory.
2. Preserve the prompt, then delegate OUTLINE to a fresh `story_outliner`.
   Include every
   supplied reference image in the assignment with a resolvable path or
   unambiguous attachment identifier and any purpose stated by the user. The
   outliner must inspect all of them before designing the story and must not
   silently omit an inaccessible image. It writes
   only `outline.md` after targeted canon and noun searches, selecting a
   story-specific generating force and a distinct narrative shape from the
   binding craft defaults. Under `prospective-2026-08-21`, target 700–1,000
   words and never exceed 1,200.
3. Delegate WRITE to a fresh `story_writer`. It uses the project-owned
   `short-story-writing` adapter, with `creative-writing-craft` primary and
   `dialogue`/`prose-style` only as diagnostic revision references. It writes
   the complete prose directly to `story.md` and revises it in place; there is
   no draft/final split, diagnostic report, or craft artifact.
4. Run `scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview` once and pass
   its concise result to the reviewer. Do not save another report file.
5. Delegate one fresh independent REVIEW to `story_reviewer`. It reads prompt
   and
   prose first and forms a provisional reader-facing judgment with
   `story-analysis` and, when applicable, `dialogue` before opening the outline.
   It may use `story-sense`, `prose-style`, or `sensitivity-check` only for a
   material problem in that skill's scope. The prompt is the acceptance
   authority; `outline.md` is advisory context.
6. If the verdict is `REVISE`, the story's writer may handle only the blocking
   fixes, repeat the pre-review check, and request a fresh reviewer agent. Every
   subsequent review must be independent and fresh. Stop for the user only when
   authority or prompt meaning requires a ruling.
7. After `PASS`, delegate the final prose to `story_title_illustrator`. It reads
   the complete story and writes only `title-image.jpg`, an exact 9:16 portrait,
   spoiler-light novel cover. Unless the assignment overrides it, use the
   agent's premium illustrated-novel-cover default. Anime-influenced rendering
   is available when it suits the story, but franchise key-art, poster, and
   scene-still composition are not the default.
   Include every reference image from the original request in the assignment
   and as an actual image-generation reference. Use resolved local paths when
   all originals have them; otherwise use the smallest recent-attachment set
   containing them all. The illustrator inspects each reference before forming
   the cover brief and preserves recognizable traits relevant to the requested
   character, object, setting, mood, palette, or style. Final prose controls
   story facts; a reference image is not canon unless the written prompt makes
   its detail binding. If any reference cannot be included, restore access or
   ask the user to attach it again before generating.
   After saving, both the illustrator and coordinator must use the available
   image-viewing tool on that exact file. Generation output, prompt text, file
   metadata, and written self-reports do not count as visual inspection. View
   the whole cover at reduced size and full-resolution details; use additional
   visual crops or views for doubtful anatomy, objects, typography, or spatial
   relations. Keep any temporary review images outside the story directory and
   do not commit them.
   The illustrator self-reviews and the coordinator independently reviews the
   actual saved file at cover-card size and full resolution through seven gates:
   cover identity, story promise, editorial restraint, depiction truth, cover
   read, image integrity, and production finish. Each pass must cite visible
   evidence rather than repeat the generation prompt or the illustrator's
   claims. If a depicted action, role, object connection, or spatial fact is
   ambiguous, fail it rather than filling the gap from the prose. A mechanically
   clean but generic image, one that omits the prompt's defining contradiction,
   or one that reads as an illustrated synopsis does not pass. When a gate
   fails, send a regeneration brief that identifies what to preserve, the
   blocking miss, the required concept, focal, or compositional change, and the
   unchanged constraints. Use a new concept for cover-identity, story-promise,
   or editorial-restraint failure, a new composition for a depiction-truth
   failure, and a targeted correction only for a localized defect. Do not
   capture until all seven gates pass.
8. Run final validation, then capture the story with
   `python pages/build.py capture <slug>`. This mandatory final handoff updates
   the stored prose catalog and its matching Pages cover asset.

Do not create research briefs, authority snapshots, handoff records, separate
draft/final files, canon deltas, release records, promotion manifests, story
READMEs, or index projections. Do not reread the complete legacy corpus when a
targeted search answers the continuity question.

## REWRITE mode

REWRITE is a package-reset entry point, not a separate writing mode. It applies
only to one completed current-format story with `canon: false`; locked legacy
bundles cannot be rewritten, and canon changes require a separate ruling. After
preparation, a rewrite uses the same OUTLINE, WRITE, REVIEW, and REVISE stages
and the same local production adapter as CREATE. Every story begins with fresh
outliner, writer, and reviewer agents; a writer may perform that story's
targeted REVISE pass, but every later review uses a fresh reviewer.

1. Complete the repository's rewrite branch and worktree setup before reading
   story files. Use only `prompt.md` and package metadata to prepare the reset;
   the preparation script may verify the prior PASS and frontmatter, but the
   prior outline, prose, and review are not creative inputs. Inspect the saved
   cover only when AUTO or KEEP makes it a candidate. Resolve and inspect every
   original and newly supplied reference image; restore access or ask the user
   to attach it again when an original cannot be resolved.
2. Run
   `scripts/prepare-rewrite.ps1 -Story <slug> -Title <fresh-title> -Request <verbatim-request>`.
   Pass each new reference through `-ReferenceImage`, and select `-Cover Auto`,
   `Keep`, or `Regenerate`. The script preserves the original prompt and
   immutable package identity, records the rewrite request and reference display
   names, and resets `outline.md`, `story.md`, and `review.md` to clean
   scaffolds. It creates no backup or rewrite artifact. The prepared rewrite
   records `prospective-2026-08-21` as the active production profile. AUTO keeps
   an unchanged-title cover as a post-review candidate but removes it when the
   title changes; KEEP requires an unchanged title; Regenerate removes it after
   the Markdown reset succeeds.
3. Treat the original prompt plus the latest `## Rewrite request` as the
   acceptance authority. The rewrite request controls a conflict; every
   unaffected original requirement remains binding, while the latest profile
   in Rewrite constraints controls production craft. Delegate the ordinary
   OUTLINE assignment to `story_outliner`, then the ordinary WRITE assignment
   to `story_writer`. Do not load the prior outline, prose, or review from Git.
   If the user explicitly asks to retain a named element from the old story,
   retrieve only the minimum old material needed for that element and include
   it in the relevant assignment.
4. Run `scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview` and delegate a
   fresh independent REVIEW. The old passing review is history, not evidence.
   Resolve a `REVISE` verdict through the normal blocking-fix loop.
5. After `PASS`, apply the recorded cover policy:
   - `AUTO`: when an unchanged-title cover was retained, the coordinator opens
     the JPEG at cover-card size and full resolution and independently repeats
     all seven cover gates against the final rewrite. Reuse it when every gate
     passes; otherwise regenerate through the
     normal title-image workflow.
   - `KEEP`: perform the same fresh comparison and reuse only on a seven-gate
     pass. If it fails, stop for the user rather than silently generating a new
     cover under a keep-only request.
   - `REGENERATE`: run the normal title-image workflow after the prose review
     passes.
   Cover generation is conditional: reuse is permitted when the retained image
   passes, but a valid final cover remains mandatory for completion. Reused
   covers already passed their original production review, but that does
   not establish cover identity, story promise, editorial restraint, depiction
   truth, or title accuracy for changed prose. Reference-image requirements
   apply whenever a new cover is generated.
6. Run final validation, capture the story again with
   `python pages/build.py capture <slug>`, run the catalog check, and complete
   the normal commit, push, and draft-pull-request handoff. Git history preserves
   the prior prose, outline, review, and cover; create no backup copies.

## OUTLINE responsibility

Write only `outline.md`. Keep scenes or movements ready to draft and compact.
Inspect every reference image supplied in the assignment with the available
image-viewing tool before choosing the story design. Use relevant visible
evidence for the role the prompt implies,
such as character appearance, relationships, setting, objects, atmosphere,
palette, or visual contrast. Do not treat incidental background detail as
canon, override the written prompt or universe authority, or invent certainty
about an ambiguous image. Translate the useful evidence into the existing
Story, Beats, or Continuity fields so the writer can act on it; do not add an
image-analysis section or another artifact. If a supplied reference is
inaccessible, report the blocker instead of proceeding without it.
For `Craft profile: prospective-2026-08-21`, target 700–1,000 words when useful
and never exceed 1,200. The outline supplies choices and pressure, not a
miniature prose draft.
Declare every proposed person and place noun as `new` or `recurring`, using one
`None` row for an empty category. Record relevant canon and unresolved
boundaries, but do not turn the outline into a canon brief or an acceptance
contract.

Choose a generating force appropriate to the prompt. For a plot-led story,
identify immediate and competing wants plus a useful limit. For another shape,
identify the attachment, attention, relationship, discovery, loss, recurrence,
accumulation, or change that creates movement. Name a credible counterforce or
complication when one exists; do not manufacture an antagonist. Record the
central promise, focal pressure, POV and information limit, governing movement
and time shape, operative speculative or ordinary-world constraint, and
flexible beats. Omit design commentary the writer cannot act on.

Under `prospective-2026-08-21`, complete the mandatory `## Voice` capsule in at
most 180 words. Each field must give actionable, story-specific guidance:

- `Narrative texture` describes how this narration moves, notices, selects, and
  sounds.
- `Conversational texture` describes the range, rhythm, and ordinary texture of
  talk.
- `Rhetorical ownership` assigns forms of reasoning, metaphor, precision, or
  argument to particular speakers rather than the whole cast.
- `Pressure behavior` names what stress does to fluency, listening, evasion,
  repetition, silence, or directness.
- `Anti-default` identifies the plausible voice or dialogue default that would
  make this particular story interchangeable.

The three dialogue-specific fields may use
`N/A — no meaningful dialogue expected` when appropriate. Narrative texture and
Anti-default remain required even without dialogue. Do not use sample lines,
catchphrases, phonetic accents, or boilerplate such as
merely `avoid house style`. Do not draft exchanges, confessions, apologies,
reconciliation protocols, speeches, banter, or final thematic lines unless the
prompt requires exact wording.

Before settling the shape, skim only the `## Story` section, including any
`Narrative design` fields, of up to five recent passing current outlines. Use
them solely to avoid repeating their movement, climax venue, collective turn,
or ending gesture; never open prior Voice sections or prose. They are not canon
or models to imitate. Quiet, private, observational, recursive, or non-climactic
outcomes are valid. Record draftable
beats or movements, not a craft audit.

For a prepared rewrite, perform the ordinary OUTLINE assignment from the
amended prompt and clean scaffold. Prior outline, prose, and review are out of
scope unless the assignment explicitly names old material the user asked to
retain. Write no comparison, change log, or alternate outline.

## REVIEW mode

Write only `review.md`. Follow its template exactly:

Treat installed craft skills as internal diagnostic references. Ignore their
requests to choose an output directory, run optional scripts, ask the user where
to persist a report, or create another file. Record only conclusions required by
the repository review template. The prompt, universe authority, binding style
guide, and chosen narrative form outrank a generic checklist: a quiet story need
not gain a shattering moment, and earned directness need not be replaced with
hidden agendas, verbal tics, or compulsory subtext.

- read prompt and story first and form a provisional judgment before opening
  the outline;
- inventory all story-facing people and place proper nouns;
- mark each noun `new` or `recurring`, with `None` for an empty category;
- check the prompt, current universe authority, and internal story facts;
- when `## Rewrite request` exists, treat it as an amendment whose conflicting
  terms override the original prompt while unaffected original terms remain;
- for a prompt carrying `Craft profile: prospective-2026-08-08`,
  `prospective-2026-08-18`, or `prospective-2026-08-21`, check material
  compliance with the binding story craft defaults without reproducing the
  in-place revision criteria;
- for `prospective-2026-08-18` or `prospective-2026-08-21`, record exactly one
  `Dialogue` verdict under `## Craft`: `PASS`, `REVISE`, or `N/A`; use N/A only
  when there is essentially
  no meaningful dialogue;
- use the outline as context, not as a reason to reject a prompt-faithful story;
- use `Verdict: PASS` only when all continuity lines and the applicable dialogue
  gate pass, and blocking findings are `none`; otherwise use `REVISE` and list
  concise fixes.

Under the older profile, craft blocks only when a failure materially breaks the
prompt's central promise, reader-facing causality, or binding narrative policy.
Under `prospective-2026-08-18` or `prospective-2026-08-21`, a material
reader-facing dialogue defect also blocks. Scan all dialogue, closely inspect
the decisive and final meaningful
exchanges with their adjacent narration, and record at most one targeted
dialogue finding supported by no more than three short examples. Outline
compliance is not evidence that dialogue works. A deliberate prompt-led
departure from a default is not a finding. Keep the review short. Findings and
outcomes belong in the file; hidden reasoning, audit narration, the craft
checklist, and repeated plot summaries do not.

For `prospective-2026-08-21`, form the provisional dialogue judgment before
opening the outline, then compare it with the Voice capsule as intent rather
than proof. Test context dependence and quote-card neatness, rhetorical
ownership, reasoning-shape diversity, secondary-character chorus, unequal
fluency under pressure, ordinary or single-purpose speech, and whether the
final exchange explains what action already established. Upstream preferences
for hidden agendas, verbal tics, universal subtext, multiple simultaneous
functions, or punchy sentences are diagnostic suggestions, not requirements.
One earned aphorism or articulate exchange is acceptable; only material
scene-wide convergence changes the existing Dialogue verdict to REVISE.

## TITLE IMAGE responsibility

Read the complete final reader-facing story, distill its narrative invitation,
and write only `title-image.jpg`. A cover is editorial packaging, not a visual
description of the story. It should make a reader ask one useful question, not
answer several plot questions at once. Choose the least explanatory visual
strategy that can carry the story's promise: a singular symbol or visual
metaphor, an iconic figure or object, an atmospheric threshold or setting, or a
literal scene only when that scene compresses into one charged image at a
glance. Most characters, events, clues, and props should be absent.

Do not default to an ensemble lineup, a roomful of people performing separate
actions, an inventory of significant objects, a split-panel or sequential
composition, a scene reconstruction that requires prose to decode, or a collage
of multiple beats. A prompt may explicitly require one of those structures, but
it must still pass the cover gates. Preserve story-specific character, setting,
era, mood, and material details only where they support the chosen cover idea.
Before generating, form a compact internal cover brief: the genre and emotional
temperature; the distinctive contradiction; the unanswered question the cover
should create; the one dominant image and its negative space; the minimum
story-specific evidence; the spoiler boundary; and likely anatomy, typography,
or spatial risks. Do not save this as another artifact.

Before calling image generation, consider three materially different
one-sentence treatments from different cover strategies; at least one must not
be a literal scene unless the prompt explicitly requires literal scene art.
Choose the treatment that best passes cover identity, story promise, and
editorial restraint, then send only that treatment. Write the generation prompt
as art direction: lead with the dominant image, layout, scale, negative space,
typography, palette, and light, followed only by facts actually visible in the
frame. Do not paste a plot summary or enumerate the cast, clues, props, and beats
that the image is meant to omit.

Inspect every reference image supplied with the original request and include
all of them as actual inputs to image generation. Use `referenced_image_paths`
when every reference has a resolved local path; otherwise use the smallest
supported recent-image set that includes them all, never both mechanisms. Keep
the requested subject identity, design traits, setting cues, mood, palette, or
style recognizable while making the composition specific to the final story.
When a reference conflicts with final prose, prose controls story facts unless
the written prompt explicitly makes the visual detail binding. If every supplied
reference cannot be included, request the missing attachment again rather than
generating without it.

Unless the prompt says otherwise, design a premium illustrated novel cover.
The rendering may use polished anime-influenced character art, digital cel
shading, painterly fantasy, cinematic light, or another story-appropriate
illustrative language, but its layout must use the restraint and hierarchy of a
book cover rather than an anime-series key visual, film poster, screenshot, or
interior plate. One dominant silhouette, gesture, object, absence, or visual
contradiction should control the image. Typography and illustration must feel
art-directed together, with enough calm space for the title to read as part of
the cover rather than a label placed over a scene.

The source asset must be a high-quality JPEG at exactly 864x1536 pixels. It
must display the exact reader-facing story title once, with no author name,
caption, logo, border, watermark, or other text. Generate the illustration and
verbatim title together in one image-generation pass; canvas normalization may
not add or replace typography.

Before saving, review the candidate at cover-card size and full resolution
through all seven gates. For each pass, identify visible evidence in the actual
candidate. Do not infer a missing action, relationship, or physical fact from
the prose or generation prompt. After saving the normalized JPEG, open the exact
saved path with the available image-viewing tool and repeat the gates; file
metadata and the generation response cannot establish a visual pass:

- **Cover identity:** the image reads first as a professionally art-directed
  novel cover. Reject an interior illustration, screenshot, film poster,
  franchise key visual, character lineup, split-panel montage, or visual plot
  summary. One dominant image idea must control the page, and the typography
  must belong to the same design. If removing the title would leave only a busy
  story scene with no iconic shape, tension, or visual thesis, the gate fails.
- **Story promise:** the image reads as this story rather than merely its genre.
  It signals genre and emotional temperature, makes the defining contradiction
  or charged motif primary, and creates an unanswered question. It must not
  falsely advertise reconciliation, triumph, romance, scale, stakes, or an
  outcome absent from the prose. The cover may imply a relationship through
  distance, absence, a shared object, reflected form, or another compressed cue;
  it need not put every relevant person on the canvas.
- **Editorial restraint:** verify that every visible figure, prop, setting cue,
  and action earns space in the one cover idea. Reject full-cast explanation,
  clue inventories, evenly weighted group tableaux, multiple chronological
  beats, decorative lore, and compositions that try to prove story specificity
  by showing more facts. Deliberate omission, negative space, cropping, scale,
  and ambiguity are strengths when they sharpen the invitation without
  falsifying the story.
- **Depiction truth:** verify every person, role, relationship, object, action,
  position, and spatial connection the cover actually depicts. A symbolic image
  may compress or juxtapose reality, but it may not advertise a false event,
  allegiance, power relation, possession, or outcome. A literal scene must keep
  the geometry and cause-and-effect necessary for that chosen fragment to be
  true. Reject an attractive approximation that reverses movement, changes who
  acts, removes a defining constraint, or turns intentional ambiguity into a
  factual claim.
- **Cover read:** inspect at reduced cover-card scale. The exact title remains
  immediately readable once; a single focal hierarchy, dominant silhouette or
  motif, emotional read, genre signal, and story-specific hook survive
  reduction. Reject crowding, competing focal points, decorative detail that
  looks like text, or a composition whose concept becomes legible only after
  reading the story. Intentional negative space and controlled detail should
  still be visible at thumbnail size.
- **Image integrity:** inspect at full resolution. Count every intended person
  and visible limb; trace hands, fingers, faces, restraints, held or suspended
  objects, reflections, shadows, and contact points. Reject fused or duplicate
  anatomy, unintentionally ambiguous figures or roles, floating or disconnected
  objects,
  incoherent perspective, impossible support or restraint geometry, accidental
  extra figures, unintended text or pseudo-text, watermarks, and crop damage.
- **Production finish:** verify intentional lighting, value and color
  separation, consistent rendering, clean edges, and professional typography.
  Reject muddy or crushed values, overprocessed texture, malformed or damaged
  title letters, accidental tangencies, generic decoration, visible scaling or
  JPEG artifacts, and title placement outside the safe crop.

If any gate fails, regenerate before saving. For a cover-identity,
story-promise, editorial-restraint, or focal miss, choose a materially different
cover concept instead of cosmetically repairing the same illustrated scene. For
a depiction-truth failure, choose a new composition unless the error is truly
local. For a localized integrity or finish defect, make one targeted correction
while repeating every invariant that already works. Use this regeneration
structure:
`Preserve`, `Blocking miss`, `Change`, and `Keep fixed`. Return the final cover
thesis, one-sentence visual description, exact verified title, concise pass
result for all seven gates, final prompt/spec, and saved path. The image is
presentation, not canon authority, and must never cause prose or continuity
edits.
