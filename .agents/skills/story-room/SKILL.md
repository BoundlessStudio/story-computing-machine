---
name: story-room
description: "Shared outline, review, and title-image stage contract used by the separate story-create and story-rewrite workflows."
---

# Story room

Use as the shared stage contract behind `story-create` and `story-rewrite`, or
when the user explicitly requests one named OUTLINE, REVIEW, or TITLE IMAGE
stage. Route new prompts to `story-create` and explicit rewrites to
`story-rewrite`. Prefer safe, low-impact assumptions over questions. Default to
a coherent 2,500–4,000 word story unless the prompt says otherwise.

For CREATE mode, the scaffold marks the self-contained prospective craft profile
implemented by the binding style defaults, compact outline handoff, prose skill,
and dialogue-aware review.
Completion alone never authorizes reopening. Route to `story-rewrite` only when
the user explicitly requests a rewrite of one named non-canon current story.
Locked legacy bundles remain immutable.

## CREATE handoff reference

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
   binding craft defaults. Under `prospective-2026-08-21` or
   `prospective-2026-08-23`, target 700–1,000 words and never exceed 1,200.
3. Delegate WRITE to a fresh `story_writer`. It uses the project-owned
   `short-story-writing` adapter, with `creative-writing-craft` primary and
   `dialogue`/`prose-style` only as diagnostic revision references. It writes
   the complete prose directly to `story.md` and revises it in place; there is
   no draft/final split, diagnostic report, or craft artifact.
4. Run `scripts/Test-Stories.ps1 -Story <slug> -Phase PreReview` once and pass
   its concise result to the reviewer. Do not save another report file.
5. Delegate one fresh independent REVIEW to `story_reviewer`. For an 08-23
   CREATE story, include the six most recent resolved passing current-story
   paths excluding the target for its collection comparison, or all available
   when fewer than six exist. It reads prompt and
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

Before delegating an 08-23 CREATE outline, count passing current stories whose
base Constraints profile is 08-23 and whose prompt has no Rewrite request. At
each nonzero multiple of ten, perform a no-artifact rolling audit of the ten
most recent: compare dialogic
media, articulate-competence structures, workplace triads, reasoning patterns,
humor levels, and ending gestures. Give the outliner only a compact collection
anti-default brief. Do not expose prior prose or Voice capsules to the outliner
or writer.

## REWRITE handoff reference

`story-rewrite` owns rewrite intake, scope, prior-version access, preparation,
and selection compliance. A rewrite still delegates fresh OUTLINE, WRITE, and
REVIEW stages and uses this skill's shared responsibilities. Its managed prompt
records REBUILD, RESHAPE, or SELECTIVE plus Keep exact, Keep in substance,
Change or replace, Remove, and outside-scope behavior.

For rewrite stages, treat the original prompt, latest Rewrite request, and
Rewrite selections as one amended authority. The request and selections control
conflicts; unnamed prior material follows the recorded outside-scope policy.
Prior outline and review remain history. Prior prose access is scope-bound:
minimal named passages for REBUILD, the full throughline for RESHAPE, and the
retained editing base for SELECTIVE. The current craft profile governs changed
prose and necessary seams, but never authorizes rewriting protected material
merely to modernize it. The old PASS is not evidence for the new verdict.

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
For `Craft profile: prospective-2026-08-21` or
`prospective-2026-08-23`, target 700–1,000 words when useful and never exceed
1,200. The outline supplies choices and pressure, not a miniature prose draft.
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

Under `prospective-2026-08-23`, first derive and complete the `Dialogue promise`,
`Dialogic medium`, and `Dialogue engine` Story fields. The promise names the
relationship, tonal, and communication experience implied by this prompt. The
medium deliberately selects speech, writing, internal voices, signs,
interfaces, gesture, silence, failed contact, or a story-specific mix. The
engine explains why these people must communicate and how communication itself
creates movement. Spoken conversation is not the default and dialogue quantity
is not the goal.

Complete the six-field 08-23 Voice capsule in at most 220 words. Add
`Relationship movement`: what each major participant wants from another, cannot
comfortably request, and what their exchange changes in knowledge, leverage,
trust, commitment, risk, or relationship. Broaden `Rhetorical ownership` to
assign humor, evasion, affection, misreading, social authority, and willingness
to listen, not merely expertise, precision, or sentence length. The four
dialogue-specific Voice fields and three dialogue Story fields may use the
exact N/A value only when there is truly no meaningful dialogic action;
non-spoken contact is still dialogue for this purpose. Notice and resist the
interchangeable default of uniformly articulate professionals solving a
material problem when the prompt instead supports play, error, pettiness,
embarrassment, distraction, poor explanation, or social unevenness.

Before settling the shape, skim only the `## Story` section, including any
`Narrative design` fields, of up to five recent passing current outlines. Use
them solely to avoid repeating their movement, climax venue, collective turn,
or ending gesture; never open prior Voice sections or prose. They are not canon
or models to imitate. Quiet, private, observational, recursive, or non-climactic
outcomes are valid. Record draftable
beats or movements, not a craft audit.

For a prepared rewrite, perform the OUTLINE assignment from the amended prompt
and Rewrite selections. Prior outline and review remain out of scope. Access
prior prose according to the recorded scope: named passages only for REBUILD,
the full throughline for RESHAPE, and the retained editing base for SELECTIVE.
Express preservation and change through the existing Story, Voice, and Beats
sections; write no comparison, change log, or alternate outline.

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
- when `## Rewrite request` exists, treat it and any Rewrite selections as an
  amendment whose conflicting terms override the original prompt; unnamed
  prior-story material follows Outside named selections;
- when `## Rewrite selections` exists, verify every Keep exact, Keep in
  substance, Change or replace, Remove, and outside-scope obligation against the
  prior prose after forming the provisional judgment of the new story;
- for a prompt carrying `Craft profile: prospective-2026-08-08`,
  `prospective-2026-08-18`, `prospective-2026-08-21`, or
  `prospective-2026-08-23`, check material
  compliance with the binding story craft defaults without reproducing the
  in-place revision criteria;
- for `prospective-2026-08-18`, `prospective-2026-08-21`, or
  `prospective-2026-08-23`, record exactly one
  `Dialogue` verdict under `## Craft`: `PASS`, `REVISE`, or `N/A`; use N/A only
  when there is essentially
  no meaningful dialogue;
- use the outline as context, not as a reason to reject a prompt-faithful story;
- use `Verdict: PASS` only when all continuity lines and the applicable dialogue
  gate pass, and blocking findings are `none`; otherwise use `REVISE` and list
  concise fixes.

Under the older profile, craft blocks only when a failure materially breaks the
prompt's central promise, reader-facing causality, or binding narrative policy.
Under `prospective-2026-08-18`, `prospective-2026-08-21`, or
`prospective-2026-08-23`, a material
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

For an 08-23 CREATE story, treat speech, writing, internal voices, signs,
interfaces, gesture, silence, and failed contact as first-class dialogic media.
Judge major exchanges by whether they change knowledge, leverage, trust,
commitment, risk, relationship, or action, not by how many lines they contain.
Check competence overuse and whether the ending defaults to practical
instructions, resumed maintenance, inventory, breakfast, or returning to work
without earning that gesture from this prompt and relationship.

Only after the target passes that standalone judgment, use the six most recent
resolved passing current stories as bounded comparison context, or all
available when fewer than six exist. Inspect only each prior story's dialogic
pattern, one representative major exchange, and final
meaningful exchange with the minimum adjacent action or narration needed. Do
not read prior Voice capsules or treat prior prose as canon or a model. Repeated
media or competence is not automatically blocking; material convergence is.
Use Dialogue REVISE when changing only job, system, or setting nouns could
transplant the target's reasoning pattern, relationship action, or ending
gesture into the recent set. Record one concise dialogue finding and no audit,
comparison section, or extra verdict field.

For a prepared rewrite, selection compliance is independently blocking. Read
the prior version only after the provisional prompt, story, and dialogue
judgment. Exact keeps must remain exact; substantive keeps must retain the named
identity, function, relationship, fact, or effect; Change targets must be
materially different; Remove targets must be absent rather than renamed; and
unnamed material must follow FLEXIBLE, KEEP, or KEEP EXACT. Judge changed prose
and necessary seams under the active craft profile without forcing protected
outside-scope prose through a prospective modernization pass. Record failures
as concise prompt or dialogue findings in the existing review structure; add no
rewrite-comparison field or artifact.

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
