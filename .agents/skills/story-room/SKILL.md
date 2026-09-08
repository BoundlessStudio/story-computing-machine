---
name: story-room
description: "Shared outline, review, and title-image stage contract used by story-create for new and replacement stories."
---

# Story room

Use one named stage below, or as the stage contract for
[story-create](../story-create/SKILL.md#workflow). Before acting, read
[AGENTS.md](../../../AGENTS.md) for authority, permissions, artifacts, and
worktree boundaries. WRITE uses [short-story-writing](../short-story-writing/SKILL.md).
Narrative standards and historical profile applicability are owned by the
[style guide](../../../universe/style-guide.md#story-craft-defaults); read
that policy rather than substituting generic craft advice.

## OUTLINE

Write only `outline.md` on a clean CREATE scaffold. Read the complete prompt,
[universe README](../../../universe/README.md), and style guide. Search only
relevant authority and noun history. A replacement is new creative work:
never retrieve the removed package's outline, prose, review, or cover.

Inspect every assigned reference original before designing, applying its
requested character, setting, object, relationship, mood, palette, or style
role. Written prompt and universe authority control conflicts; incidental
image details are not canon. Record useful evidence in the existing Story,
Beats, or Continuity fields. Report inaccessible inputs rather than omit them.

Use the template's Story, Beats, People, Places, and Continuity sections.
Record a central promise, focal pressure or attachment, credible complication
when present, POV/distance/information limit, governing movement/time shape,
operative speculative or ordinary-world constraint, and flexible movements.
Choose actionable pressure, not a miniature prose draft. No antagonist is
required. Do not draft speeches, confessions, reconciliations, banter, or final
thematic lines; preserve exact dialogue only when required by the prompt.

For 08-18, 08-21, and 08-23, target 700–1,000 words when useful and never exceed
1,200. The optional 08-18 dialogue-pressure note is at most 75 words.
For 08-21 and 08-23, include exactly one `## Voice` within that total:

| Field | Drafting instruction |
| --- | --- |
| Narrative texture | How this narration moves, notices, selects, and sounds. |
| Conversational texture | Range, rhythm, and ordinary texture of communication. |
| Rhetorical ownership | Assign thought, metaphor, precision, and argument to specific participants. |
| Pressure behavior | What stress changes in fluency, listening, evasion, repetition, silence, or directness. |
| Anti-default | A concrete, plausible default that would make this story interchangeable. |

08-21 caps Voice at 180 words. 08-23 caps it at 220 and adds
`Relationship movement`: what each major participant wants from another,
cannot comfortably request, and what exchanges change. Under 08-23 also
complete `Dialogue promise`, `Dialogic medium`, and `Dialogue engine` in
Story. Their meanings, expanded rhetorical ownership, and non-spoken forms are
defined in the style guide. These are story-specific design choices, not quotas.
No sample lines, catchphrases, phonetic accents, or empty boilerplate.

The three dialogue-specific Voice fields in 08-21, or four Voice and three Story
dialogue fields in 08-23, may be `N/A — no meaningful dialogue expected` only
when no meaningful dialogic action is expected. Non-spoken communication does
not qualify. Narrative texture and Anti-default are always required.

Propose every named person/person-like being and place as `new` or
`recurring`; give recurrence a short identity/location note. Use one `None`
row for an empty category. Search the frozen name baseline, passing current
review inventories, and relevant universe entries for exact, alias, close, and
confusing reuse. Continuity states relevant authority and unknowns, without
becoming another canon brief.

Read only the Story design sections of the recent outlines supplied under
[Collection context](../story-create/SKILL.md#collection-context). Use these and
any compact audit brief to consider the style guide's
[collection variation](../../../universe/style-guide.md#collection-variation)
questions alongside movement, climax venue, and collective turn. Make useful
choices within the existing Story, Beats, and Anti-default fields, without
scripting dialogue or an ending to satisfy the brief. Never open prior Voice
sections or prose, reproduce the brief as a new section, or treat comparisons
as canon. Return a one-sentence change report.

## REVIEW

Write only `review.md`. First read the complete prompt and prose and form a
provisional reader-facing judgment, including applicable dialogue judgment,
before opening the outline. Then read the outline as advisory intent, the
universe README and style guide, and the coordinator's concise PreReview result.
The prompt is acceptance authority; outline deviation alone is not a defect.
Historical request sections remain acceptance context and the last recorded
craft profile remains active. Do not retrieve prior versions or apply a new
profile retroactively.

Use `story-analysis` and `dialogue` as default diagnostic references.
Use `story-sense` only for unclear narrative failure, `prose-style` for material
sentence-level defects, and `sensitivity-check` when representation or sensitive
experience warrants it. Their optional scripts, separate reports, persistence
and user-question instructions do not apply. Apply conclusions through the
existing review template, not generic requirements for conflict, hidden agendas,
verbal tics, compulsory subtext, or a shattering moment.

Inventory every story-facing proper noun naming a person, person-like being,
or place, including aliases. Mark each `new` or `recurring`, explaining
intentional recurrence; use one `None` row for an empty category. Search those
forms in `stories/NAMES.md`, passing current reviews, relevant universe
characters/locations, and relevant canon bundle prose. Check exact, alias,
close-spelling, and semantic confusion. Never load the whole baseline, bundle
corpus, or unrelated history. When recurrence relies on a variant rather than
an exact name, cite that prior spelling in backticks in the continuity note
and explain the relationship. The validator can verify cited bundle text;
semantic equivalence remains the independent reviewer's judgment.

Check prompt fulfillment and its central promise, universe facts and chronology,
and internal causality, time, space, capabilities, relationships, and knowledge.
For 08-08, craft blocks only when it materially breaks the prompt's central
promise, reader-facing causality, or binding narrative policy. Apply later
profiles' additional thresholds from the style guide. Scan
every exchange, including adjacent action/narration, for the policy's semantic
coherence gate before higher-order dialogue judgment. Closely inspect the
decisive and final meaningful exchanges; if they coincide, inspect the next
most consequential exchange too. Do not infer a pass from outline intent or
repair unclear prose charitably. One materially incoherent line can block;
higher-order convergence uses the distinct scene-wide threshold in policy.

For an 08-23 CREATE/replacement, only after standalone Dialogue PASS or valid
N/A, compare the target's dialogic pattern, one major exchange, and final
meaningful exchange with the supplied recent-story set. Open prior review only
to confirm PASS and only the bounded prose passages plus adjacent action needed;
never prior outlines or Voice capsules. Apply the style guide's collection
interchangeability standard. This is the sole exception to unrelated-history
limits; do not expose the passages to the outliner/writer.
The coordinator's broader collection audit is prospective planning guidance;
it does not add a verdict or expand the active profile's blocking thresholds.

Follow the template exactly, using one declaration of each verdict:

- `Verdict: PASS` only when every required gate passes, otherwise `REVISE`.
- Under Continuity: `Prompt`, `Universe`, and `Internal`, each PASS or REVISE.
- Under Craft for 08-18/08-21/08-23: exactly one `Dialogue: PASS`,
  `Dialogue: REVISE`, or `Dialogue: N/A`. N/A means essentially no meaningful
  dialogic action, not merely little spoken dialogue. Dialogue REVISE requires
  overall REVISE.
- Under Findings: `Blocking: none` for PASS, otherwise concise actionable
  blocking findings. A dialogue failure gets one targeted finding with at most
  three short examples; no new comparison field or extra verdict.
- Keep useful notes short. Save no reasoning trace, repeated plot summary,
  diagnostic checklist, or audit record. Do not edit prose or reopen another
  story. Return a one-sentence change report.

## TITLE IMAGE

Write only `title-image.jpg` after prose passes review. Read the complete final
`story.md`, or `05-story.md` for an explicitly permitted bundle cover assignment,
and the recorded prompt. Use the imagegen skill. Final prose controls depicted
facts unless the written prompt makes a reference detail binding.

Inspect every inventoried reference and include all originals in image
generation: resolved local paths when all have them, otherwise the smallest
supported recent-image set containing all, never both mechanisms. Preserve
recognizable traits for their requested role. If an original cannot be supplied,
report the blocker and restore it or request reattachment before generation.

Design premium illustrated novel packaging unless the prompt specifies another
style. Anime influence, painterly fantasy, cinematic light, and other appropriate
rendering are available, with one dominant image and deliberate negative space.
Use a symbol, figure/object, threshold, or tightly selected literal fragment.
Withhold most characters, clues, events, and explanation.

Form an internal brief covering genre/emotional temperature, defining
contradiction, unanswered question, dominant image/negative space, minimum
story-specific evidence, spoiler boundary, and anatomy/typography/spatial risks.
Consider three materially different one-sentence treatments; at least one is
nonliteral unless literal scene art is required. Choose the strongest and
generate only that treatment. Lead the prompt with composition, scale, type,
palette, and light, then visible facts; do not paste the plot or cast inventory.
No brief or candidate file belongs in the story package.

Read the exact title from frontmatter. Generate illustration and title together,
with the title once, inside the safe crop, and no author, caption, logo, border,
watermark, or other text. Normalize only the canvas to a high-quality
864x1536 JPEG; never add or replace typography in post-processing.

The illustrator reviews candidates and opens the exact saved JPEG again.
The coordinator independently opens that same saved file and compares it with
prompt and final prose. Both inspect cover-card size and full-resolution detail,
using extra views/crops for doubt; temporary review images stay outside the
story directory and are not committed. Generation output, file metadata, and
written self-reports are not visual evidence. Each reviewer must name visible
evidence for each separate gate:

1. **Cover identity:** professional novel-cover composition with one dominant
   idea and integrated typography. Reject an interior scene, screenshot, film
   poster, ensemble key visual, split-panel montage, or visual plot summary.
2. **Story promise:** this story's genre, tone, distinctive contradiction/motif,
   and an unanswered question survive. Reject generic genre imagery or implied
   resolution, romance, victory, scale, or stakes the prose has not earned.
3. **Editorial restraint:** each figure, prop, setting cue, and action earns its
   place. Reject clue inventories, sequential beats, evenly weighted roomfuls,
   decorative lore, and factual completeness used in place of a focal idea.
4. **Depiction truth:** chosen people, roles, relationships, objects, actions,
   and spatial connections agree with prose. Symbolism may compress reality,
   but cannot advertise false events, allegiance, possession, power, or outcome.
   Literal fragments preserve necessary geometry and cause-and-effect.
5. **Cover read:** at thumbnail size the exact title is readable once, hierarchy
   is immediate, and dominant silhouette, emotional tone, and story-specific
   hook remain clear. Reject crowding, competing focal points, and text-like
   decoration; preserve negative space and controlled detail.
6. **Image integrity:** at full resolution count figures and limbs; trace hands,
   fingers, faces, held/suspended objects, restraints, reflections, shadows,
   contact points, and supports. Reject fused/duplicate anatomy, disconnected
   objects, incoherent perspective, impossible connections, extra figures,
   unintended/pseudo-text, watermarks, and artifacts.
7. **Production finish:** intentional lighting, value/color separation, coherent
   rendering, edge treatment, and typography. Reject muddy values, overprocessed
   texture, malformed title letters, accidental tangencies, generic decoration,
   crop damage, or visible scaling/compression defects.

Ambiguous depicted facts fail; never fill gaps from the prose. Polish cannot
excuse a generic promise, and completeness cannot excuse an illustrated synopsis.
For cover identity, story promise, or editorial restraint failure, require a new
concept; a focal-hierarchy failure also requires a new concept. For depiction
truth failure, require a new composition. Only localized integrity/finish
defects permit a targeted correction. Send a concise brief with `Preserve`,
`Blocking miss`, `Change`, and `Keep fixed`; repeat all seven gates until both
reviewers accept. Never capture a rejected image or rely on the coordinator to
catch a known defect.

Return the cover thesis, one-sentence visual description, exact verified title,
concise visible-evidence result for every gate, final prompt/spec, and saved
path. Images never establish canon or justify changes to prose.
