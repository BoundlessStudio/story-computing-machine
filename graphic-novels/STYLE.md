# Graphic-novel house style — draft v0.5

Publisher design guidance, not universe facts. These are proposed defaults for
user review. Explicit preferences and the approved edition plan take precedence
over design defaults; source truth and binding narrative policy still apply.
This file does not change existing stories, covers or illustrated editions.

## Written style and reference provenance

This document is the reusable `[GN]` style specification. It encodes drawing,
color, lettering and composition as text; there is no visual style preview or
fixed example page to reproduce. Choose every page's composition from its story
beats. Consistency means a shared drawing language, not repeated layouts,
camera angles, blue backgrounds or identical pacing.

On 2026-09-17 the user supplied **Photo 1.jpg** (Image #1) and directed:
"Use this image as reference for graphic noval style."
This replaces the initial GN proposal of pen hatching, restrained washes and
paper texture. It changes `[GN]` only; `[IL]` keeps its existing house style.

- Original: [Photo 1.jpg](D:/Development/BoundlessAi/story-computing-machine/.codex-remote-attachments/01a0b02d-ff15-77d1-a1f8-a8f9cc8c6d79/93838bec-9eb5-4eab-b208-87e8e04ea1a3/1-Photo-1.jpg).
- Inspected dimensions: 853 × 1280 pixels, approximately 2:3 portrait.
- SHA-256: `e1fbbc451fe6d37ee940d078213b933d98033675fccc77e7f7ef54b354a27173`.
- Role: provenance for the written GN rendering, color and lettering rules.
  Its cast, harbor, bells, costumes, dialogue and plot are not new story facts.
- The original remains external and unchanged. These text rules carry its useful
  visual qualities forward; it is not a compulsory input for each new edition
  or a page-layout template. Do not automatically attach it to generation calls.
  If the user explicitly selects it as an image input for an edition, resolve
  and inspect the original then, following ordinary reference-access rules.

## Drawing language and reference priority

Use crisp black contours, heavier outer silhouettes and broad, mostly flat
color fills. Shape shadows with clean hard edges and limited tonal steps.
Faces are expressive and stylized with clear anatomy; hair, cloth and hands
remain readable through confident linework. Environments use the same outlined,
graphic treatment. Keep selective texture subordinate; avoid the earlier wash,
dense-hatching or aged-paper default, soft painted modeling, photorealism,
glossy 3D surfaces and indiscriminate gradients.

The reference contrasts wide environmental views with face, ensemble, contact
and object close-ups. Carry that variation and clarity into the adaptation.
Do not copy the reference's particular action, composition subjects or captions.

At production time also inspect the **named story's** cover and existing
illustrations. Compatible same-story art can guide identity, costume, geography,
object design and motifs; this document controls the default GN rendering.
Source colors and tone can vary the palette without reverting to an IL wash
style or forcing every story into a blue night scene. A later explicit user
style instruction takes precedence for its stated scope.

Read candidates' source/review status. Rejected, unreviewed or stale images are
not accepted identity references. Never silently inherit an older edition's
visual departure. Record useful and excluded traits for every image. Resolve
source conflicts before use. When a compatible IL sheet uses a different
rendering style, use it as identity-only input to make a new GN sheet using
the drawing and color instructions in this document. Keep the IL asset unchanged.

Once accepted, those **GN** character sheets propagate the requested rendering
to places, objects and pages through their actual pixels. A previously accepted
IL sheet does not become a GN rendering anchor merely because it exists. Attach
useful accepted edition-specific reference pixels within the five-input limit.
Use the written traits to diagnose style drift. Never copy the provenance
image's figures, headings or panel arrangement into new reference sheets.

## Page format and reading order

- Portrait **2:3** page; request **1024 × 1536** as an initial digital target.
  Inspect the actual returned dimensions. Use a consistent approved canvas;
  do not stretch artwork or crop speech, faces or story-bearing action to fit.
- Left-to-right, then top-to-bottom. Panel position, gaze, motion and speech
  placement reinforce that route. A different reading direction is edition-wide
  and requires explicit preference in the plan.
- Keep text and important action safely inside the page. The panel treatment
  below must remain readable in the assembled PDF, including at reduced reading size.
- Finish all image generation, corrections, required image reviews and checks
  of the complete ordered image sequence before generating edition.pdf exactly
  once at the end. No partial, intermediate or progress PDFs and no automatic
  rebuilds. Assemble the selected cover followed by all ordered comic-page images,
  one image per PDF page. Preserve each complete image and its
  aspect ratio without cropping or stretching; verify none is omitted or
  duplicated. Reference sheets are production assets unless an appendix is
  expressly requested. A differently proportioned cover retains its own ratio.
- There is no preferred panel count. Determine the necessary panels from the
  scene's action, dialogue and pacing after deciding how its moments connect.
- A page has a dramatic purpose and a clear final beat. Page turns can reveal or
  change the situation; they do not need to manufacture a cliffhanger each time.

## How panels interact

Panel style describes the relationships between frames: how they separate,
connect, contain detail, direct attention and carry time. Plan those relationships
in words for the scene, rather than selecting a numbered layout or filling a grid.

### Borders, gutters and grouping

Use crisp black frames and clean white gutters as the ordinary visual language.
Keep border weight and spacing coherent so the reader sees intentional groups.
Aligned edges can connect related moments; an offset or a larger gap can set a
beat apart. Let a wider gutter provide breathing room where the scene needs it,
without assigning every spacing change a fixed meaning or amount of elapsed time.
Protect speech, faces and gestures from crowded edges and accidental tangencies.

### Flow between neighboring panels

Lead the eye through gaze, gesture, motion, silhouettes and balloon placement.
The end of one panel should make the next point of attention easy to find.
Use matching shapes, a repeated object or a continued movement to connect a cut
when the story supports it. Such visual links must not imply an invented
relationship or cause. Avoid diagonals, tails or bright accents that send the
reader past the next panel or into a later reveal.

Decide what each transition carries: a small movement, action and reaction,
another view of the same moment, a shift of attention, or a clear change of time
or place. The artwork must make the intended connection understandable. Keep a
conversation's spatial axis legible; establish a position change before reversing
it. Track entrances, exits, gaze targets, handedness and held objects through cuts.

### Insets and overlapping frames

An inset can bring a face, hand or object detail into focus while the surrounding
panel establishes its context. Give it a clear border and visual hierarchy;
make its position in the reading sequence apparent. Distinguish a simultaneous
detail from a later action so the reader does not infer an extra event.

Overlapping frames can compress or interrupt a sequence. Keep their stacking
order and reading path clear, and leave each panel's essential action and words
visible. Do not merge separate places or moments into an impossible continuous
space. Use insets and overlaps when they clarify the scene, not as decoration.

### Breaking or opening the frame

A figure, gesture or effect may cross a frame edge to emphasize force, closeness
or scale. Preserve the destination panel's readability and the distinction
between separate moments. A borderless panel or image extending to the page edge
can open up an expansive or quiet beat; use surrounding white space, contrast
and lettering placement to keep its boundaries and reading order clear.
No frame-break or borderless treatment is required on any page.

If an image continues across adjoining panels, maintain spatial alignment and
make clear whether this is one continuous view or a sequence through time.
Do not split important faces, gestures or words merely to create a visual effect.

### Shape, scale and rhythm

Choose panel proportions for the attention the moment needs: a wide view can
hold geography or a pause; a tall frame can carry height or vertical movement;
a close crop can isolate a reaction. Angled edges can add tension if their joins
and reading order remain clear. No shape has a mandatory narrative meaning.

Let relative size, spacing and framing create emphasis and rhythm across the
page. Repeated framing can hold a deliberate beat; a change of scale can mark a
shift in attention. Balance dense exchanges with space to see and feel their
consequences. Leave silent moments to the image when captions would repeat it.
Judge these choices by their story effect, not by a panel total or a repeated
opening/middle/closing template.

## Color and marks

The reference uses strong blue/cyan fields, black ink, near-white highlights
and figures, pale-yellow captions and sparse red/green accents. The hex values
below are proposed approximations of that visual direction, not sampled values.
Each book records its actual story-appropriate palette in its approved plan.

| Role | Starting suggestion | Use |
| --- | --- | --- |
| Ink | `#11151B` near black | Contours, panel frames and lettering |
| Deep field | `#083B70` navy | Large dark fields with clear silhouettes |
| Midtone | `#196FB4` strong blue | Flat environmental color and light/shadow separation |
| Bright accent | `#22A9C7` cyan | Selected light, water or effects when supported by the story |
| White | `#FFFDF4` near white | Gutters, speech balloons and highlights |
| Narration | `#FFE783` pale yellow | Black-outlined narration boxes |

Use broad saturated fields with controlled accents and clean value separation. Keep
character skin tones faithful; do not wash everyone into one palette color.
Day/night and location shifts change light while retaining identity colors and
ink character. Saturated effects earn their contrast through story context.
Do not assign moral meaning to warm/cool palettes without story support.
Do not add wash texture or dense hatching as a default finish. Faces, gestures
and speech remain legible in reduced-size and grayscale
checks. Do not rely on color alone to identify speakers or communicate action.

## Lettering, captions and sound

- Script exact dialogue, narration and sound effects before generation. Quote
  retained source words exactly; label condensed or newly adapted wording in
  the script. Preserve speaker intent, voice, causal meaning and key wording.
- Proposed v1 output is a complete lettered page from the built-in image tool.
  Supply the exact text per panel and speaker; generated spelling is never
  assumed correct. Inspect every balloon and caption against the script.
- Use bold, condensed, hand-lettered-looking **uppercase** comic text, matching
  the reference's captions and balloons. Record exact display casing in the
  script while retaining source quotations' original wording/case for provenance.
  Case conversion is a lettering treatment, not a change of meaning; preserve
  any case-sensitive in-world code or sign. Start around 40–44 px on a
  1024 px-wide page; verify actual legibility at approximately 390 px wide
  and at desktop reading size, including the rendered PDF. Enlarge text or
  simplify/split a page if it fails. Zoom and the plan transcript supplement
  a readable page, not excuse unreadable type.
- Aim for 10–22 words per balloon, normally no more than two balloons per panel,
  and roughly 50–90 words on a dialogue page. These are planning guides; silent
  pages can have none. Do not add filler to reach a target or shrink letters to
  force text to fit. Page-count changes need renewed plan approval.
- White or near-white balloons with black text and black contours; tails clearly
  identify the speaker without crossing faces or other tails. Place balloons in
  reading order. Narration uses pale-yellow rectangular boxes with black borders
  and uppercase black text, generally near panel tops with safe inset. Do not
  narrate visible action twice or add captions merely to imitate the reference.
- Thoughts only when the adaptation needs interiority; distinguish them clearly
  from spoken lines. Sound effects are sparse, scripted and story-bearing.
- No reference headings, watermark, invented credit or unsolicited decorative
  writing inside final pages. Necessary signs have exact scripted wording.

Maintain the exact per-panel transcript in plan.md, with speakers, words and
brief essential visual actions. Do not create, serve or open HTML previews,
even outside the package. Inspect image files directly and do not add another
authored transcript document. The
transcript must match the selected page after every correction. OCR may assist
inspection but cannot certify text, tails or reading order. Correct lettering
through the image tool and review the entire changed page for collateral drift.

## Continuity and finish

Keep one identity per character sheet, named exactly as in the source. Multiple
views or necessary outfits of that identity are allowed. One distinct place
per location reference, in a coherent environment view; do not combine locations
or unrelated identities to evade input limits. Label unnamed figures by role.

Every panel specifies who is present, costume, bodily state, pose, prop state,
location, light and required absences. At page boundaries track the changes
explicitly. A preceding accepted page helps continuity but cannot replace the
character references or overrule the source. Do not propagate a page error as
the new standard.

Inspect the actual saved page at full size and reading size: anatomy, contact,
spatial connections, stable faces and outfits, lettering, tails, panel transitions,
gutter clarity, inset/overlap hierarchy, frame crossings, clipping and compression.
Trace the intended reading path across the page and compare adjacent pages,
not just isolated panels.
Use the PDF skill for the single final assembly after all image work and reviews
are complete. Render the existing PDF for inspection without regenerating it.
A later REVISE does not authorize another PDF generation; that requires an explicit
user change to the single-generation instruction. Inspect every
page at full and reading sizes, including approximately 390 px wide. A fresh
independent whole-book pass checks the complete rendered PDF for image order,
page count, omissions/duplicates, undistorted complete artwork and readable
lettering, along with pacing, repetitive compositions, palette drift, missing
exchanges and whether the ending still lands. Record the reviewed PDF hash and
ordered image versions; final user approval applies to that exact PDF. PDF is
the only GN reading deliverable. Temporary raster reductions of images for
reading-size inspection are allowed; HTML previews are prohibited.
