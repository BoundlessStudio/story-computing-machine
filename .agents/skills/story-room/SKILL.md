---
name: story-room
description: "Create or review a shared-universe short story using only prompt, outline, story, and review."
---

# Story room

Use for `[WP]` prompts or a named story stage. Prefer safe, low-impact
assumptions over questions. Default to a coherent 2,500–4,000 word story unless
the prompt says otherwise.

For CREATE mode, the scaffold marks the self-contained prospective craft profile
implemented by the binding style defaults, compact outline handoff, prose skill,
and dialogue-aware review.
Never use it to reopen a completed current or locked legacy story.

## CREATE mode

1. Work on a non-main branch. Identify and visually inspect every reference
   image supplied with the request, then scaffold with `scripts/new-story.ps1`,
   passing those paths or attachment labels through `-ReferenceImage` so
   `prompt.md` inventories their display names. Record `None supplied` when the
   request has no reference images. Reference originals remain external inputs;
   never copy them into the story directory.
2. Preserve the prompt, then delegate OUTLINE to `story_outliner`. Include every
   supplied reference image in the assignment with a resolvable path or
   unambiguous attachment identifier and any purpose stated by the user. The
   outliner must inspect all of them before designing the story and must not
   silently omit an inaccessible image. It writes
   only `outline.md` after targeted canon and noun searches, selecting a
   story-specific generating force and a distinct narrative shape from the
   binding craft defaults. Under `prospective-2026-08-18`, target 700–1,000
   words and never exceed 1,200.
3. Delegate WRITE to `story_writer`. It uses `short-story-writing`, applies its
   self-contained in-place revision pass, and writes the complete prose directly
   to `story.md`; there is no draft/final split or craft report.
4. Run `scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview` once and pass
   its concise result to the reviewer. Do not save another report file.
5. Delegate one independent REVIEW to `story_reviewer`. It reads prompt and
   prose first and forms a provisional reader-facing judgment before opening
   the outline. The prompt is the acceptance authority; `outline.md` is
   advisory context.
6. If the verdict is `REVISE`, delegate only the blocking fixes to
   `story_writer`, repeat the pre-review check, and request one fresh review.
   Stop for the user only when authority or prompt meaning requires a ruling.
7. After `PASS`, delegate the final prose to `story_title_illustrator`. It reads
   the complete story and writes only `title-image.jpg`, an exact 9:16 portrait,
   spoiler-light title visual. Unless the assignment overrides it, use the
   agent's premium anime/light-novel key-visual default.
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
   actual saved file at cover-card size and full resolution through six gates:
   story promise, scene truth, role legibility, cover read, image integrity,
   and production finish. Each pass must cite visible evidence rather than
   repeat the generation prompt or the illustrator's claims. If a required
   action, role, object connection, or spatial fact is ambiguous, fail it rather
   than filling the gap from the prose. A mechanically clean but generic image,
   or one that omits the prompt's defining relationship or contradiction, does
   not pass. When a gate fails, send a regeneration brief that identifies what
   to preserve, the blocking miss, the required focal or compositional change,
   and the unchanged constraints. Use a new composition for an editorial,
   scene-truth, or role-legibility miss and a targeted correction for a localized
   defect. Do not capture until all six gates pass.
8. Run final validation, then capture the story with
   `python pages/build.py capture <slug>`. This mandatory final handoff updates
   the stored prose catalog and its matching Pages cover asset.

Do not create research briefs, authority snapshots, handoff records, separate
draft/final files, canon deltas, release records, promotion manifests, story
READMEs, or index projections. Do not reread the complete legacy corpus when a
targeted search answers the continuity question.

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
For `Craft profile: prospective-2026-08-18`, target 700–1,000 words when useful
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

If dialogue will carry a decisive conflict, an optional `Dialogue pressure`
note may use at most 75 words for the speakers' asymmetrical aims, knowledge or
withheld information, likely tactics or proxy subjects, and character-specific
diction sources. Do not draft exchanges, confessions, apologies,
reconciliation protocols, speeches, banter, or final thematic lines unless the
prompt requires exact wording.

Before settling the shape, skim only the `## Story` section, including any
`Narrative design` fields, of up to five recent passing current outlines. Use
them solely to avoid repeating their movement, climax venue, collective turn,
or ending gesture; they are not canon or models to imitate. Quiet, private,
observational, recursive, or non-climactic outcomes are valid. Record draftable
beats or movements, not a craft audit.

## REVIEW mode

Write only `review.md`. Follow its template exactly:

- read prompt and story first and form a provisional judgment before opening
  the outline;
- inventory all story-facing people and place proper nouns;
- mark each noun `new` or `recurring`, with `None` for an empty category;
- check the prompt, current universe authority, and internal story facts;
- for a prompt carrying `Craft profile: prospective-2026-08-08` or
  `prospective-2026-08-18`, check material compliance with the binding story
  craft defaults without reproducing the in-place revision criteria;
- for `prospective-2026-08-18`, record exactly one `Dialogue` verdict under
  `## Craft`: `PASS`, `REVISE`, or `N/A`; use N/A only when there is essentially
  no meaningful dialogue;
- use the outline as context, not as a reason to reject a prompt-faithful story;
- use `Verdict: PASS` only when all continuity lines and the applicable dialogue
  gate pass, and blocking findings are `none`; otherwise use `REVISE` and list
  concise fixes.

Under the older profile, craft blocks only when a failure materially breaks the
prompt's central promise, reader-facing causality, or binding narrative policy.
Under `prospective-2026-08-18`, a material reader-facing dialogue defect also
blocks. Scan all dialogue, closely inspect the decisive and final meaningful
exchanges with their adjacent narration, and record at most one targeted
dialogue finding supported by no more than three short examples. Outline
compliance is not evidence that dialogue works. A deliberate prompt-led
departure from a default is not a finding. Keep the review short. Findings and
outcomes belong in the file; hidden reasoning, audit narration, the craft
checklist, and repeated plot summaries do not.

## TITLE IMAGE responsibility

Read the complete final reader-facing story, select one spoiler-light scene or
visual metaphor that carries its emotional promise, and write only
`title-image.jpg`. Preserve story-specific character, setting, era, mood, and
material details. Before generating, form a compact internal cover brief: the
story's distinctive promise, the relationship or contradiction the image must
foreground, the minimum story-specific visual evidence, the spoiler boundary,
and likely anatomy, crowding, typography, or spatial risks. Do not save this as
another artifact.

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

The source asset must be a high-quality JPEG at exactly 864x1536 pixels. It
must display the exact reader-facing story title once, with no author name,
caption, logo, border, watermark, or other text. Generate the illustration and
verbatim title together in one image-generation pass; canvas normalization may
not add or replace typography.

Before saving, review the candidate at cover-card size and full resolution
through all six gates. For each pass, identify visible evidence in the actual
candidate. Do not infer a missing action, relationship, or physical fact from
the prose or generation prompt. After saving the normalized JPEG, open the exact
saved path with the available image-viewing tool and repeat the gates; file
metadata and the generation response cannot establish a visual pass:

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
- **Scene truth:** verify every story-critical action, position, direction of
  movement, spatial constraint, possession, support, and cause-and-effect
  relation in the selected moment. Openings, rooms, vehicles, restraints,
  tools, and other affordances must have plausible scale and geometry. Reject
  an attractive approximation that changes how the scene works, puts an object
  in the wrong hand or place, reverses movement, removes the stated constraint,
  or makes the decisive action physically ambiguous.
- **Role legibility:** verify that story-important figures remain distinct in
  silhouette, face, clothing, posture, and placement. A viewer must be able to
  tell who is doing what, who holds power, how figures are grouped, and which
  objects belong to whom without prose explanation. Reject near-duplicate
  faces, ambiguous couples or groups, or static posing that erases opposing
  choices.
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
- **Production finish:** verify intentional lighting, value and color
  separation, consistent rendering, clean edges, and professional typography.
  Reject muddy or crushed values, overprocessed texture, malformed or damaged
  title letters, accidental tangencies, generic decoration, visible scaling or
  JPEG artifacts, and title placement outside the safe crop.

If any gate fails, regenerate before saving. For a story-promise, scene-truth,
role-legibility, or focal miss, choose a materially different composition
instead of cosmetically repairing the same idea. For a localized integrity or
finish defect, make one targeted correction while repeating every invariant
that already works. Use this regeneration structure:
`Preserve`, `Blocking miss`, `Change`, and `Keep fixed`. Return the final cover
thesis, one-sentence visual description, exact verified title, concise pass
result for all six gates, final prompt/spec, and saved path. The image is
presentation, not canon authority, and must never cause prose or continuity
edits.
