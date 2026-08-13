---
name: story-room
description: "Create or review a shared-universe short story using only prompt, outline, story, and review."
---

# Story room

Use for `[WP]` prompts or a named story stage. Prefer safe, low-impact
assumptions over questions. Default to a coherent 2,500–4,000 word story unless
the prompt says otherwise.

For CREATE mode, the scaffold marks the self-contained prospective craft profile
implemented by the binding style defaults, outline handoff, and prose skill.
Never use it to reopen a completed current or locked legacy story.

## CREATE mode

1. Work on a non-main branch and scaffold with `scripts/new-story.ps1`.
2. Preserve the prompt, then delegate OUTLINE to `story_outliner`. It writes
   only `outline.md` after targeted canon and noun searches, selecting a
   story-specific generating force and a distinct narrative shape from the
   binding craft defaults.
3. Delegate WRITE to `story_writer`. It uses `short-story-writing`, applies its
   self-contained in-place revision pass, and writes the complete prose directly
   to `story.md`; there is no draft/final split or craft report.
4. Run `scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview` once and pass
   its concise result to the reviewer. Do not save another report file.
5. Delegate one independent REVIEW to `story_reviewer`. The prompt is the
   acceptance authority; `outline.md` is advisory context.
6. If the verdict is `REVISE`, delegate only the blocking fixes to
   `story_writer`, repeat the pre-review check, and request one fresh review.
   Stop for the user only when authority or prompt meaning requires a ruling.
7. After `PASS`, delegate the final prose to `story_title_illustrator`. It reads
   the complete story and writes only `title-image.jpg`, an exact 9:16 portrait,
   spoiler-light title visual. Unless the assignment overrides it, use the
   agent's premium anime/light-novel key-visual default.
   The illustrator self-reviews and the coordinator independently reviews the
   actual saved file through three gates: story promise, thumbnail cover read,
   and full-resolution image integrity. A mechanically clean but generic image,
   or one that omits the prompt's defining relationship or contradiction, does
   not pass. When a gate fails, send a regeneration brief that identifies what
   to preserve, the blocking miss, the required focal or compositional change,
   and the unchanged constraints. Use a new composition for an editorial miss
   and a targeted correction for a localized defect. Do not capture until all
   three gates pass.
8. Run final validation, then capture the story with
   `python pages/build.py capture <slug>`. This mandatory final handoff updates
   the stored prose catalog and its matching Pages cover asset.

Do not create research briefs, authority snapshots, handoff records, separate
draft/final files, canon deltas, release records, promotion manifests, story
READMEs, or index projections. Do not reread the complete legacy corpus when a
targeted search answers the continuity question.

## OUTLINE responsibility

Write only `outline.md`. Keep scenes or movements ready to draft and compact.
Declare every proposed person and place noun as `new` or `recurring`, using one
`None` row for an empty category. Record relevant canon and unresolved
boundaries, but do not turn the outline into a canon brief or an acceptance
contract.

Choose a generating force appropriate to the prompt. For a plot-led story,
identify immediate and competing wants plus a useful flaw or limit. For another
shape, identify the attachment, attention, relationship, discovery, loss,
recurrence, accumulation, or change that creates movement. Name a credible
counterforce or complication when one exists; do not manufacture an antagonist.
Also choose the intended reader experience, POV and distance, time shape,
information strategy, non-thematic speculative effect, structural distinction,
decisive turn or deepening, aftereffect, and opening/ending relation. Use `none`
for speculative surplus when the story is deliberately ordinary.

Before settling the shape, skim only the `## Story` section, including any
`Narrative design` fields, of up to five recent passing current outlines. Use
them solely to avoid repeating their movement, climax venue, collective turn,
or ending gesture; they are not canon or models to imitate. Quiet, private,
observational, recursive, or non-climactic outcomes are valid. Record draftable
beats or movements, not a craft audit.

## REVIEW mode

Write only `review.md`. Follow its template exactly:

- inventory all story-facing people and place proper nouns;
- mark each noun `new` or `recurring`, with `None` for an empty category;
- check the prompt, current universe authority, and internal story facts;
- for a prompt carrying `Craft profile: prospective-2026-08-08`, check material
  compliance with the binding story craft defaults without reproducing the
  in-place revision criteria in `review.md`;
- use the outline as context, not as a reason to reject a prompt-faithful story;
- use `Verdict: PASS` only when all continuity lines are `PASS` and blocking
  findings are `none`; otherwise use `REVISE` and list concise fixes.

Craft is blocking only when a failure materially breaks the prompt's central
promise, reader-facing causality, or binding narrative policy. A deliberate
prompt-led departure from a default is not a finding. Keep the review short.
Findings and outcomes belong in the file; hidden reasoning, audit narration,
the craft checklist, and repeated plot summaries do not.

## TITLE IMAGE responsibility

Read the complete final reader-facing story, select one spoiler-light scene or
visual metaphor that carries its emotional promise, and write only
`title-image.jpg`. Preserve story-specific character, setting, era, mood, and
material details. Before generating, form a compact internal cover brief: the
story's distinctive promise, the relationship or contradiction the image must
foreground, the minimum story-specific visual evidence, the spoiler boundary,
and likely anatomy, crowding, typography, or spatial risks. Do not save this as
another artifact.

The source asset must be a high-quality JPEG at exactly 864x1536 pixels. It
must display the exact reader-facing story title once, with no author name,
caption, logo, border, watermark, or other text. Generate the illustration and
verbatim title together in one image-generation pass; canvas normalization may
not add or replace typography.

Before saving, review the candidate through all three gates:

- **Story promise:** the image reads as this story rather than merely its genre.
  It makes the defining relationship, contrast, or pressure visually primary,
  preserves who is aligned with whom and who holds power, and does not falsely
  advertise reconciliation, triumph, romance, scale, or stakes absent from the
  prose. A generic action pose or literal captivity image fails when the prompt's
  real promise is the relationship revealed inside that situation. When the
  promise depends on contrasting couples, groups, roles, or relationships, show
  enough people or unmistakable visual evidence to make that contrast legible.
  Reducing the cast or hiding anatomy risk is valid only if it does not erase the
  premise.
- **Cover read:** inspect at reduced cover-card scale. The exact title remains
  immediately readable once; the silhouette, focal hierarchy, emotional read,
  important relationships, and story-specific object or setting cue survive
  reduction. Reject crowding, competing focal points, decorative detail that
  looks like text, or a composition whose premise becomes legible only after
  reading the story.
- **Image integrity:** inspect at full resolution. Count every intended person
  and visible limb; trace hands, fingers, faces, restraints, held or suspended
  objects, reflections, shadows, and contact points. Reject fused or duplicate
  anatomy, ambiguous couples or roles, floating or disconnected objects,
  incoherent perspective, impossible support or restraint geometry, accidental
  extra figures, unintended text or pseudo-text, watermarks, and crop damage.

If any gate fails, regenerate before saving. For a story-promise or focal miss,
choose a materially different composition instead of cosmetically repairing the
same idea. For a localized integrity defect, make one targeted correction while
repeating every invariant that already works. Use this regeneration structure:
`Preserve`, `Blocking miss`, `Change`, and `Keep fixed`. Return the final cover
thesis, one-sentence visual description, exact verified title, concise pass
result for all three gates, final prompt/spec, and saved path. The image is
presentation, not canon authority, and must never cause prose or continuity
edits.
