---
name: graphic-novel-create
description: "Draft a sequential-art adaptation of a named finished repository story with [GN]; create pages only after explicit approval to try the draft plan."
---

# Graphic-novel production — draft v0.4

## Entry and scope

`[GN] "Exact Story Title" (preferences)` is the sole new trigger. Accept a
repository story title or slug, like `[IL]`. `[Comic]` stays reserved and is not
an alias. Do not change the `[IL]` route, agents, tools or publication behavior.
Do not interpret a new writing prompt as an existing source. While this contract
is draft, prepare and review the concrete adaptation/reference plan first;
generation requires the user's explicit approval to try that plan. Installing
or discussing these instructions does not create a book.

Read root AGENTS.md, universe/README.md, applicable universe/style-guide.md
policy and graphic-novels/STYLE.md. Source events, identities, relationships,
causes, ending and binding universe facts survive adaptation. Condense prose
into panels/dialogue with documented coverage; do not silently invent new plot,
replace motivations or turn cover symbolism into literal story events. Existing
source prompt/profile remains relevant; do not reopen its prose review under a
new craft profile. Substantive authority conflicts need user direction.

GN's reusable rendering instructions are encoded as text in
graphic-novels/STYLE.md. Photo 1.jpg is recorded there as provenance, not a
compulsory image input or layout template. Do not automatically attach it to
generation calls or require it to start an edition. Use bold black contours, saturated flat fills, hard-edged
shadows, white gutters, yellow narration boxes and uppercase comic lettering.
Same-story covers and IL art guide compatible identity/content, not an overriding
wash/hatching style. Establish new GN sheets when existing sheets render
differently; preserve the originals. Do not copy Photo 1's cast or story facts.

Both canon and non-canon source stories are read-only inputs. Never change any
source-package file, canon marker, original cover or existing illustrated
edition. Adaptation is neither an unlock nor canon promotion. `[IL]` remains
the distinct prose-preserving route; its no-lettering and complete-prose rules
do not define a graphic novel. Its commands do not support this new format.

## Worktree and artifact boundaries

Before production, switch the primary checkout to main, pull origin/main with
fast-forward-only, create `codex/graphic-novel-<edition-slug>` from updated main
and add a dedicated sibling worktree. Leave the primary checkout on main. Stop
if local changes prevent a safe switch or the intended worktree path is occupied.
Retain the resolved absolute worktree and include it in every assignment.
All production, inspection, validation and Git work happens there. This process
contract's own development worktree is not an edition worktree.

An edition lives under `graphic-novels/<edition-slug>/`:

- `prompt.md`: verbatim request, constraints, source identity, external image
  display names and subsequent user decisions.
- `plan.md`: adaptation coverage, art direction, page/panel script, exact
  lettering, reference roles and dependencies; no duplicate source prose.
- `edition.json`: source/input hashes, asset paths, per-page state, attempts,
  dependency versions, review evidence and actual user approval bindings.
- `review.md`: independent preflight, page and final verdicts with concise
  findings; preserve actual review scope and versions within this file.
- `cover.jpg` or `cover.png`, `references/`, `pages/page-001.png` etc.: selected
  reused/generated assets only; cover is separate and not numbered as page 1.
- `edition.html`: local assembled reader with ordered pages and accessible
  transcripts. Optional `edition.pdf` only on explicit request.

This is a proposed manually maintained format, not an implemented schema/CLI.
No command can currently certify its state. Keep discarded candidates, debug
previews and temporary evidence outside the package. Do not add approval
receipts, separate bibles, duplicated scripts, prose drafts or process ledgers.
Keep decisions in the files above. Source originals/external references remain
external; a selected existing cover or accepted same-story reference/illustration
may be copied into this separate package with source path and hash recorded.
Never overwrite the original. Existing packages need explicit edit permission;
a second adaptation needs a distinct slug.

## Responsibilities

The main coordinator owns the worktree, user communication and approval records.
Assign `graphic_novel_creator` the absolute worktree, exact source/package paths
and a bounded stage (plan, one reference, one page, correction, assembly).
The creator owns plan/script and assigned visuals/reader, and returns actual
tool provenance and inspected evidence for the coordinator's edition.json.
It cannot record user approval or certify its own independent PASS.

Assign `graphic_novel_reviewer` independently. It owns only review.md, reads
source and plan as needed, and returns PASS or concrete REVISE findings with
page/panel/asset IDs and minimal fixes. A reviewer must not be the producer of
the material it reviews. A fresh reviewer performs the final book review and
rechecks a revised final book. Do not silently substitute illustrated agents:
their contracts require a different output. If new role configs have not loaded,
use a default agent with this complete bounded contract or explain the runtime
limitation. Never claim a new role was exercised when only its TOML was parsed.

## Workflow

1. **Identify the source and inspect originals.** Resolve an exact title/slug;
   ask on ambiguous identity. Inspect the authoritative marker before source
   prose: story.md frontmatter, or story.json beside 05-story.md. Missing/invalid
   state blocks production; canon true permits reading for adaptation. Read the
   complete source and prompt. Inventory original reference display names and
   new attachments, resolve actual paths,
   and inspect every original plus the
   source cover. Missing originals need restored access or reattachment, never
   silent omission. Pin source commit and hashes of prose, prompt, state and cover.
   Inspect existing same-story illustrated plans/manifests and selected actual
   sheets/interiors for useful visual continuity. Check source version, review
   status and visual departures before proposing reuse. Existing art is a
   candidate, not automatic authority. Catalog canon discrepancies must be
   surfaced and deliberately resolved before any future publication.
2. **Plan the complete adaptation.** Map every major exchange, decision and reveal
   to pages/panels, or explain its proposed condensation/omission. Keep core plot
   and ending. Record source passages, panel order, framing, exact action/instant,
   each character's state, entrances/exits, props, light, required absences and
   exact speaker/text for every panel. Distinguish source quotations from adapted
   lines. Describe how neighboring panels interact: border/gutter treatment,
   visual flow, transitions in time or attention, and any inset, overlap or frame
   break. Make their reading sequence and purpose explicit. There is no preferred
   panel count or required grid. Specify page-turn beats, palette, lettering
   treatment and reference consumers. Reuse the source cover unchanged by default; a new
   edition cover requires an explicit request. Preserve its aspect ratio.
   Propose an exact page count justified by coverage, not a fixed quota, and
   separate counts for reused/new reference assets and cover generation.
3. **Review the plan, then ask the user.** The independent reviewer reads the
   source, script, image-role plan and available pixels. Resolve infeasible
   panels, overloaded text, misplaced reveals, inconsistent states and reference
   conflicts before presenting the plan. Recheck repaired inputs. Show a concise
   plan with counts, art references and adaptation tradeoffs for explicit user
   approval. Bind the response to exact source/plan/style hashes. This is the
   user decision to try the draft workflow, not a claim that future pixels pass.
4. **Develop references.** Load the imagegen skill. Reuse suitable inspected art
   first; create only missing references with downstream consumers. Establish
   character identities individually in the user-selected GN rendering, then
   location/object references anchored to accepted actual GN character-sheet
   pixels. Establish those sheets using the written STYLE.md traits and selected
   edition inputs; keep any differently rendered IL sheet's role to identity/content only. Use cover and originals for
   their assigned palette/identity/geometry roles with explicit exclusions.
   Begin with dependencies needed for page 1; later references can be created
   when their first page needs them. A new reference not in the approved count
   or a material style change requires an updated plan decision. Review each
   reference against source and selected style, with coordinator acceptance
   before dependent artwork. Match the written style's contours, flat fills, shadow
   edges and lettering as appropriate to the asset, not just its palette.
   Keep one identity per sheet and one place per
   environment image. Reused sheets get the same current-edition checks.
5. **Create page 1 and settle the page treatment.** Preflight the complete prepared
   prompt, exact words, reading path and selected actual reference pixels before
   generation. Generate one complete comic page, inspect and correct it, then
   obtain independent page review in a local reading preview. Review at full
   size and approximately 390 px mobile/desktop reading sizes, including actual
   lettering. PASS on page 1 establishes the treatment within the approved plan.
   If that treatment requires changing the approved art direction or page count,
   obtain the updated plan decision first. This is otherwise an assistant review,
   not an extra user approval checkpoint.
6. **Repeat sequentially.** Only after page N passes, prepare page N+1. Generate
   one page per image call, never a contact sheet of multiple pages or parallel
   future pages. One page can contain its approved multiple panels. Follow the
   same preflight → generate → inspect → correct → independent review loop.
   Compare to the accepted preceding page and identity/location anchors. Update
   character/object/location state and selected output hashes after acceptance.
   Do not propagate an unnoticed continuity error just because an earlier page
   passed. Resolve affected pages and dependencies before advancing.
7. **Assemble and review the entire book.** Build a self-contained local reader
   with cover, ordered complete pages, page navigation/zoom, descriptive alt
   text and panel transcripts. Escape source/request text as literal text.
   Do not require a network connection for essential artwork or fonts. Use
   legible keyboard controls, light/dark UI, and preserve art colors under both
   themes. A fresh independent reviewer inspects every selected full-size page,
   the complete sequence and the actual desktop/mobile reader. Per-page passes
   do not imply a whole-book PASS. Repair findings, re-review changed pages and
   affected neighbors, and repeat the final review. If PDF was requested, use
   the PDF skill and inspect every rendered PDF page after layout changes.
8. **Present for final approval.** Show the exact independently passing book and
   request the user's final approval, bound to its current output hashes. Provide
   a PDF only when requested. Retain draft/awaiting-approval status until an
   actual response. Do not claim that an assistant review or elapsed time is
   user approval. Stop at the reviewed local deliverable in this draft; website
   capture/publication needs a separate implemented and authorized route.

## Image calls and correction loop

Use built-in Codex image generation, one reference or one full page per call.
Never use API keys, CLI generation or another paid fallback without explicit
user request. Do not claim a model variant the tool did not report. Save selected
project assets into the edition, not only the tool's generated-images directory.

For each call, inspect and attach actual accepted inputs: at most five images
including a correction target. Select essential identity/style, setting/prop
and preceding-page guidance, with explicit roles. The preceding page alone is
insufficient identity evidence. For larger casts choose panel framings that fit
the available identity references; never merge identities into a sheet to evade
the limit. Every original input needs a useful assigned role across development.
Do not carry cover text, sheet headings or irrelevant figures into the page.

Before every initial call and correction, check source moment, reference state,
anatomy/contact feasibility, spatial axis, framing, text fit and reading order.
Resolve contradictions visible in the brief rather than generating to discover
them. Persist the full actual prompt, input hashes/roles, timestamp, output path,
returned tool provenance and subsequent evidence in edition.json.

Inspect saved pixels; a description, thumbnail or successful tool result is not
acceptance. Prefer a targeted image-tool edit for a localized flaw, explicitly
preserving passing regions and including relevant identity references. Inspect
the entire edited page again; preservation is not a pixel guarantee. After two
unsuccessful fixes, diagnose and change the conflicting inputs, composition or
text load within approved scope. There is no arbitrary attempt cap; preserve
actual attempts across strategy changes/resumes. Tool/access problems are
reported honestly and never bypassed with an unrequested backend.

## Review gates

Record PASS, REVISE or NOT REVIEWED per assigned scope with reviewer identity,
input/output hashes and concrete evidence. Only PASS permits dependent work.

| Scope | Required checks |
| --- | --- |
| Plan | Source coverage/intent; complete readable script; feasible panel states; clear panel relationships and transitions; reference roles/counts; no unsupported story changes |
| References (coordinator) | Source identity/geography; actual style match; one subject/place per reference; current versions and downstream use |
| Every page (independent) | Planned beats/action without missing or duplicated panels; clear reading path, transitions, gutters, inset/overlap hierarchy and frame crossings; correct speakers and every visible word; readable balloons/tails; anatomy/contact; source state; identities/costumes/props; palette/ink consistency; adjacent-page continuity; full-size and reader-size inspection |
| Complete book (fresh independent) | Every page inspected; missing/duplicated beats/pages; source coverage and ending; pacing and page turns; cumulative visual drift; all lettering/transcripts; actual reader navigation, mobile/desktop usability and requested PDF pages |

Review.md records the reviewed page/asset versions and concrete findings. A
whole-book verdict names each gate and says `PDF: NOT REQUESTED` when applicable.
REVISE returns to the responsible producer. Reviewers never fix the art/script
they are independently certifying or record user approval.

## Resumes and changes

On resume compare recorded source, cover, style, script and input hashes to
actual files. Never silently repin a changed source or reuse stale user approval.
Ask for direction if source identity/content changed. A style/script/reference
change invalidates dependent page acceptance and whole-book/final approval;
identify actual dependencies and recheck affected pages, including neighbors.
Renew plan approval only for material changes to approved scope/art direction,
counts or adaptation, not routine fixes that achieve the existing plan.
Preserve previous attempt history and actual decisions in existing artifacts.

Do not run story capture, capture-all or capture-illustrated for a comic.
Do not edit pages/catalog.json, pages/illustrated.json or their snapshots, add
another Library card or replace a published reader. Current validators certify
neither this format nor its prose adaptation. Future publication requires its
own explicit implementation and review. Keep work on its branch; merge only
through a pull request, never automatically. Draft-contract checks are TOML
parsing, links and consistency; they are not end-to-end production validation.
