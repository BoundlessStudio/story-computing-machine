---
name: illustrated-create
description: "Create or explicitly revise a prose-preserving illustrated edition with [Illustrate] or its exact alias [IL]."
---

# Illustrated editions

## Entry and authority

`[Illustrate] "Story Name" (details)` and `[IL] "Story Name" (details)` are
identical routing triggers. A slug is also accepted. Default to Classic; an
explicit `deluxe` or `cinematic` selects that presentation. `[WP]` remains the
story-writing route; `[Comic]` is reserved for future panel-based work.

Read root AGENTS.md, universe/README.md, applicable universe/style-guide.md
policy, and illustrated/STYLE.md. This is an edition of finished prose, never
a rewrite, comic script, or canon promotion. The entire source story remains
unchanged. Source prompt/profile and universe authority retain their meanings.
Do not apply newer prose profiles retroactively. Stop on substantive conflicts.
Both canon and non-canon stories may be read for this separate derivative work;
no source-package file may be changed, even its review or cover.

Before production, use the existing main → fast-forward pull → new branch →
sibling worktree sequence, with `codex/illustrated-<edition-slug>`. Leave the
primary checkout on main. Stop on unsafe local changes or an occupied target.
Resolve the absolute worktree path and include it in every assignment. All
commands and production work happen there. Never use a main checkout to scaffold.

Resolve only repository sources, by exact title or slug, supporting story.md
and legacy 05-story.md/story.json. Inspect the authoritative canon marker before
source reading; missing or invalid identity is a blocker, true is not an edit
permission requirement for a separate edition. Ask on ambiguous titles. An
existing edition is not overwrite permission: explicit edits resume it; a
second edition needs a distinct slug. No story is generated merely by installing
this workflow.

## Artifact contract

Each edition under illustrated/<edition-slug> contains only prompt.md, plan.md,
edition.json, review.md, cover artwork, references/, illustrations/, and the
rendered edition.html. Add edition.pdf only when requested. No duplicate prose
draft belongs there. Existing source
prose is loaded by its pinned identity; publication captures a complete body.
Temporary candidates, prompt/decision/evidence input files, HTML previews, and
PDF page renders stay in an ignored temporary directory or OS temporary space.
Git preserves history. Do not create ledgers, separate bibles, approval receipts,
or extra lifecycle documents.

The coordinator owns prompt.md and edition.json. The planner owns plan.md. The
artist owns assigned reference/illustration assets through lifecycle commands.
The independent reviewer owns review.md. The renderer owns edition.html and,
only when explicitly requested, edition.pdf. Web-only is the default output.
Original external references remain external; record their display names, source
roles, paths, hashes, and visual inspection evidence without copying them into
the edition. Original cover pixels may be copied to the edition cover.

## Workflow

1. **Resolve and scaffold.** Write the verbatim request to a temporary UTF-8 file,
   then use `python -m illustrated.edition new "Exact title or slug"
   --request-file FILE [--slug EDITION] [--mode classic|deluxe|cinematic]
   [--reference ORIGINAL ...]`. Inventory every reference recorded in the source
   prompt as well as new attachments. Display names are not paths. Resolve and
   inspect originals, including the source cover. If unavailable, restore access
   or ask for reattachment; never silently omit one. Supply every resolved input
   to the planner and artist. Pin source commit and content hashes, including
   prompt, original cover, and bundle identity. Never fake review of unseen pixels.
2. **Plan.** Assign illustrated_planner the absolute worktree, edition, complete
   source/prompt, reference paths, and relevant universe boundaries. Plan a full
   prose-preserving reading experience using the required sections below. Obtain
   block anchors with `python -m pages.illustrated_editions anchors EDITION`.
   Register each planned visual with `set-asset`; anchors place scenes after the
   corresponding source passage. Show the plan, exact reference/interior counts,
   reused or requested new cover, art direction, and coverage of each major
   exchange as an image or explicit prose-only treatment. Name the centerpiece
   with `configure-production EDITION --pilot ASSET` before approval. Plan its
   minimum reference dependencies first, including any dependencies of those
   references. Give every reference a downstream use and every attached input
   a role. Bind each scene to an exact source state with `--state-file`; register
   input roles with repeated `--reference-role ID=ROLE`. Complete the independent
   [Pre-generation review](#pre-generation-review) loop and repair its concrete
   findings before presenting the plan for approval. Stop
   for explicit user plan approval. Only the coordinator records the actual
   response with `approve EDITION plan --decision-file FILE`.
3. **Visual development.** Use the imagegen skill's built-in Codex image tool.
   Honor an explicit user art style; if none is specified, default to the anime
   illustration style used for the repository's covers, as defined in
   illustrated/STYLE.md. Accepted character sheets remain the concrete style
   anchor for an existing edition; do not replace them with a generic default.
   For new editions, first generate only the centerpiece's required reference
   chain and cover. Generate references one asset per call, based on inspected
   source cover and original image evidence. Establish and accept character
   sheets before subsequent location/object references. Their actual image bytes are the
   primary style inputs for those references; original images guide geometry
   and content, while the cover supplies subordinate style accents. Match the
   accepted character sheets' pen contours, hatching, restrained washes, paper
   texture, and stylization, not merely their palette. Reject painterly,
   photographic, or 3D drift even if the result is otherwise attractive. Style
   conditioning does not authorize copying character figures or sheet layouts
   into environment/object images. Cover character faces, silhouettes, proportions,
   clothes, relevant expressions and viewpoints; include each story-required
   outfit/form. Each character sheet contains only one identity, with multiple
   views or states of that same character permitted. Give it the exact source
   name as a readable heading and a filesystem-safe filename derived from that
   name; use an accurate descriptive role label for an unnamed figure, without
   inventing a name. Do not mix identities in a family, cast, or paired sheet.
   Each location reference image shows one distinct place in a single coherent
   environment view. No montages, combined locations, or collages of states.
   Separate rooms, approaches, gates, streets, and alleys into accurately named
   files. Establish stable geography, entrances, materials, scale, and lighting.
   If a materially different state needs its own reference, make a separate asset
   only when necessary and preserve that same place's geography. Add object/style sheets
   only when needed. Every external reference must have an assigned useful role
   in reference development. Proposed unspecified details are visual design,
   never new universe facts. Inspect and accept each selected image.
4. **Review the centerpiece first.** Reuse and explicitly inspect the cover by
   default. A requested new cover belongs only to this edition and has no
   generated lettering; the layout supplies the exact selectable title. Generate
   `layout-sample EDITION --output TEMP_DIR` through
   `python -m pages.illustrated_editions`. It returns a reader at
   `stories/<source-slug>.html` inside a disposable Library with the shared
   Pages header, theme controls, and local assets. Record the inspected reader
   with `layout-preview EDITION HTML_PATH --evidence-file FILE`.
   Review the centerpiece's accepted references, cover, and sample with
   `review-visuals EDITION --pilot --reviewer ID --evidence-file FILE`.
   Generate, inspect, and accept the centerpiece. Run layout-sample again: it
   now uses that scene's actual pixels, placement, and presentation. Inspect
   narrative impact, scale, framing, source state, and legibility in context;
   record the new layout preview, then
   `review-pilot EDITION --reviewer ID --evidence-file FILE`.
   These are assistant reviews, with no added user approval stage. If the user
   explicitly requested intermediate approval, honor that workflow using
   `approve EDITION pilot-visuals --decision-file FILE` for the initial pilot
   visual inputs. The user still approves the complete final edition.
5. **Complete the artwork.** After the centerpiece review passes, generate the
   remaining references. Refresh the sample as needed and record ordinary full
   `review-visuals EDITION --reviewer ID --evidence-file FILE` after inspecting
   all references, cover, and layout. Then generate the remaining scenes.
   Assign illustrated_artist one planned image, its exact source moment/brief,
   accepted reference file paths, and any useful preceding accepted scene.
   Always attach applicable accepted reference bytes; preceding scenes alone
   are insufficient. Keep source truth, required and absent states, framing,
   and input roles prominent in a concise generation prompt. Generate one
   complete illustration per call, never typeset prose or reference headings.
   Inspect identity, clothing, geography, contact points, objects, anatomy,
   lighting, style, and tone. Correct visible failures within the requested
   scope. After two unsuccessful fixes, diagnose and change the conflicting
   reference or composition before trying again. Resolve consequences for
   dependent images and reviews through the existing lifecycle.
6. **Compose and review.** Run `python -m pages.illustrated_editions render EDITION`
   and `preview EDITION --output TEMP_DIR`. Review the Library card and complete
   responsive reader at the existing story URL. Assign a fresh illustrated_reviewer
   the source, final accepted assets, plan and exact HTML. Only when the user
   requested a PDF, use the PDF skill to render and inspect every PDF page and
   provide those outputs to the reviewer too.
   Review is of the edition, not permission to revise its source story. A REVISE
   goes to the responsible producer, followed by a fresh reviewer. Record a
   passing review with `record-review EDITION --reviewer ID --evidence-file FILE`.
7. **Final user approval and publication.** Show the web preview after independent
   PASS; include a PDF only when requested. Obtain explicit final approval of those exact
   outputs, then record `approve EDITION final --decision-file FILE`. Follow
   Publication below. The final response links the story's illustrated reader
   and draft PR, plus the PDF only when requested.

New manifests use `productionPolicy` version 1 and a selected `pilotAssetId`.
Existing manifests keep their historical stage ordering and initial-plus-two
attempt rule until explicitly migrated with `configure-production` and a
recorded user decision. Migration preserves attempts/provenance and requires
renewed plan approval; it does not authorize source or unrelated package edits.

## Planner contract

Write plan.md with these sections:

- **Source and visual analysis:** summary, themes, tone; all characters, locations,
  important objects, and appearance/state changes relevant to the illustrations.
  Attribute established facts to source passages; label proposed visual choices.
- **Coverage:** list every major interaction, exchange, reveal, and turn with its
  source anchor and planned scene ID or explicit prose-only treatment. Counts
  follow this coverage, not a quota. Name the centerpiece whose emotional impact
  or composition needs to be settled first.
- **Art direction:** use one nonempty `## Art direction` section; line/rendering language, palette, light, texture, camera,
  realism/stylization, mood, and recognizable connections to cover/originals.
  Honor explicit user style; otherwise use the repository's anime cover
  illustration style. An edition's accepted character sheets provide the
  concrete style anchor rather than a fresh interpretation of that default.
  Identify accepted character sheets as the primary rendering-style target for
  subsequent location/object references. Define visible continuity in pen
  contours, hatching, wash restraint, paper texture, and stylization; original
  images guide content/geometry and cover influence remains subordinate.
- **Reference inventory:** stable IDs, requested roles, outfits/forms, locations,
  objects, external-input mapping, and exactly what must remain consistent.
  Plan a separate sheet for each character identity, with the exact source name
  or accurate unnamed-role label and its corresponding filename. Count sheets
  individually, even when characters are related or appear together in scenes.
  Plan one distinct place and one coherent environment view per location image,
  giving each room, approach, gate, street, or alley its own accurate filename.
  Name a separate state asset only when needed; keep its identity and geography
  tied to the same place. Do not plan location montages or combined state sheets.
  Limit each call's input mapping to five images; assign every original a useful
  role across reference development rather than attaching all originals to every
  call. Never combine character identities or locations to fit the input limit.
  Include explicit style dependencies on accepted character sheets for each
  subsequent location/object asset, with those actual images attached within
  the same five-input limit. Keep content and style roles distinct in prompts.
  Name each reference's downstream consumers; indirect use through another
  needed reference counts. Remove references that no scene or generated cover
  consumes. Put the centerpiece's dependency chain first. A separate state
  reference needs a concrete downstream reason, not speculative completeness.
- **Illustration plan:** stable ID, source anchor, scene purpose, visible facts,
  framing, referenced asset IDs and their roles, layout, alt text, optional
  caption, and prompt. State the exact source instant, what must be visible,
  and what must be absent or already changed. Register that description with
  `set-asset --state-file FILE`; use `--reference-role ID=ROLE` for every input.
  Distinguish identity, rendering style, and geography/object shape, and state
  which reference details do not apply to this instant.
  Choose opening, reveals, emotional turns, climax, and ending where the source
  earns them. Avoid quotas of repetitive scenes, spoilers placed before their
  reveal, invented events, and decorative explanatory lore.
- **Presentation and counts:** mode, house-rule exceptions explicitly requested,
  exact reference/interior/cover counts, centerpiece-first order, and selected
  page treatments. Counts describe coverage and production work; do not impose
  a generation budget or infer a weekly usage percentage from them.

Source-based prose and facts control depicted events; an outline is design
intent. Reference sheets guide visual continuity, never authorize source edits.
No captions by default. Optional captions are editorial additions clearly
separate from prose; any quoted passage must be exact. Never invent sections,
author credits, dialogue, captions claiming new story facts, or omitted prose.

## Generation and lifecycle controls

### Pre-generation review

Use reasoning and source/reference inspection to resolve contradictions before
spending an image call. This is required assistant work, not an additional user
approval stage or a promise that a clear prompt will produce perfect pixels.

**Plan review.** The planner checks every asset brief and the reference graph.
Then assign an independent illustrated_reviewer, who did not write those
briefs, the complete source, plan, edition.json, original image paths and proposed references.
Before art exists, review the proposed contents; do not require generated
references or claim to have inspected future pixels. Return concrete findings
with asset IDs and source/prompt evidence. The planner fixes plan.md; the
coordinator re-registers affected prompts, sceneState, references, roles,
placements and layouts in edition.json, then runs `validate EDITION --phase plan`.
The reviewer rechecks affected briefs and downstream dependencies, including
agreement between the repaired plan and registered fields. Finish when the
known contradictions are resolved and the coordinator has verified that the
manifest matches the cleared plan before recording user plan approval.
Keep a concise findings/repairs summary
in plan.md, not another report or ledger. This clearance never certifies final
artwork or substitutes for user plan approval.

**Checks for both the plan and each prepared image request:**

- Bind one visible instant to the source: who is present, what has happened,
  posture, costume/wetness, season, prop state, and what must still be absent.
  Check placements for spoilers and premature relationship or event outcomes.
- Compare positive instructions and exclusions across the brief, sceneState,
  reference roles and actual inputs. Reject incompatible crops/body parts,
  gestures, occupied hands, contact points, object counts, or open/closed states.
- Check camera and composition: coherent sightlines, consistent room fixtures,
  clear subject separation, and visible contact points. A mid-thigh crop cannot
  also show feet. Do not require a direct view of a wall behind the camera or
  full frontal readability from labels seen at oblique angles. Distinguish a
  contradiction from an impossible perspective deliberately required by the
  source or approved art direction.
- Assess the planned aspect ratio and actual desktop/mobile display width.
  Faces, hands, mechanisms and necessary inscriptions must remain readable at
  that size. Change the framing or layout before drawing an action that would
  become an illegible spot image. Use current CSS or a disposable layout sketch
  for this check; generate no art just to measure the available space.
- Check what each reference will encourage beyond its declared role. Keep
  reusable identity/style sheets free of unnecessary transient story props.
  An umbrella before its introduction or a closed book in an open-page scene
  can conflict despite a role label. Prefer compatible inputs and concise
  scene-specific descriptions for simple props. Add a state reference only
  when an actual recurring continuity need requires it.
- Resolve conflicts by removing competing instructions, choosing useful inputs
  or clarifying staging. Do not accumulate a longer list of negatives while
  leaving the conflicting positive reference in place. Preserve source facts,
  established identities and approved style while simplifying.

**Before every image call, including corrections.** Once the approved stage and
accepted dependencies are ready, the artist inspects their actual pixels and
runs `prepare-tool EDITION ID --dry-run` with the intended correction/edit
options. Review the complete assembled prompt and resolved paths using the
checks above; mechanical dry-run success alone is insufficient. Send concrete
conflicts to the coordinator for repair in the authorized plan/asset fields,
follow existing approval/dependency renewal rules, then repeat the dry run.
Do not silently amend the returned prompt or paths. Reserve the real attempt
only after these checks pass and use its current returned inputs exactly.

For a correction, identify the visible defect, likely cause, exact change and
details to preserve; inspect the rejected base and selected references together.
When a defect recurs, diagnose the conflicting input or staging before the next
call rather than resending the same request with stronger wording. Record short
evidence in the existing handoff or lifecycle review evidence. Recheck changed
inputs and unresolved concerns; do not endlessly repeat a clean review, invent
extra assets, impose an attempt cap, or create new user permission checkpoints.

### Tool and dependency rules

Default to the imagegen skill's built-in Codex image generation. Do not invoke
the API, use OPENAI_API_KEY, run an image-generation CLI or choose a paid fallback
unless the user explicitly requests that path. A missing or failed built-in tool
is not permission to switch. The built-in tool chooses its model; record actual
tool provenance and do not claim an unreported API model or variant. No API key
is required for the default workflow.

The built-in tool accepts at most five reference images per call, including any
cover, original, accepted sheet, preceding scene, or correction image. Select
the most useful inputs for the exact asset and state each input's role in the
prompt. Keep applicable identity and continuity references within this limit;
plan framing and reference dependencies accordingly. Do not evade the limit by
combining character or location sheets or silently omit an original from the edition's
overall reference-development mapping.

A reference is evidence for its declared role, not authority for every depicted
state. Do not attach a fully assembled object or an inserted retaining rod as a
literal state guide for a scene before assembly or after removal. Prefer a
compatible reference; if needed, change framing or create a justified state
asset while preserving geography. For example, an empty apparatus must specify
empty sockets and an absent rod in its scene-state file; the character sheet
supplies identity/style, while an apparatus input may guide shape only when its
visible state is compatible. Prompts lead with the exact event and required or
absent details, then the useful input roles and composition. Avoid long repeated
style descriptions that bury source truth.

Give each delegated artist the absolute worktree, one asset ID, concise
assignment, and exact source/plan/reference paths. Read relevant originals and
source files directly; do not resend an entire image-heavy conversation to
coordinate a single asset. When auditing historical tasks, use bounded,
sanitized local text extracts and inspect selected image files separately.
Avoid `read_thread` for histories whose embedded images cause oversized tool
responses; do not repeatedly reload a crashing image payload.

Use `prepare-tool` to reserve one attempt and obtain the complete prompt and
resolved image paths. Pass those actual inputs to the built-in image tool. Record
its real saved output with `record-tool-output`, then visibly inspect and accept
or reject it. Request PNG and the asset's planned 1024x1024, 1536x1024, or
1024x1536 dimensions in the prompt; verify the saved pixels. Do not fabricate a
tool response, backend name, generation receipt or successful attempt. Original
cover pixels are reused unchanged by default. An explicitly requested API run
uses the imagegen skill's unchanged bundled CLI and separately recorded backend
authorization; it is never an automatic fallback.

Useful commands (all `python -m illustrated.edition`):

- `inspect-original EDITION ID --evidence-file FILE`
- `set-asset EDITION ID --kind character|location|object|style|illustration|cover
  --prompt-file FILE --size SIZE [--reference ID ...] [--after ANCHOR]
  [--layout inline|full-page|spot --alt TEXT --caption TEXT]
  [--state-file FILE] [--reference-role ID=ROLE ...]`
- `configure-production EDITION --pilot ASSET [--decision-file FILE]`
- `configure-workflow EDITION --backend codex-imagegen --visual-review-policy assistant --decision-file FILE`
- `configure-output EDITION --format web|web-pdf --decision-file FILE`
- `prepare-tool EDITION ID [--dry-run] [--correction-file FILE]`
- `prepare-tool EDITION ID --edit-last-rejected --reference ACCEPTED_ID ... --correction-file FILE [--dry-run]`
- `record-tool-output EDITION ID SAVED_IMAGE --evidence-file FILE`
- `review-visuals EDITION [--pilot] --reviewer ID --evidence-file FILE`
- `review-pilot EDITION --reviewer ID --evidence-file FILE`
- `stats EDITION`
- `accept EDITION ID --evidence-file FILE`
- `reject EDITION ID --evidence-file FILE`
- `repin-source EDITION --decision-file FILE`
- `validate EDITION --phase draft|plan|references|render|review|final|capture`

Inspect and accept or reject a ready candidate before starting another image.
For a localized defect in an otherwise successful rejected image, prefer an
edit of that actual image over regenerating the entire composition. Inspect
the rejected pixels, then use `--edit-last-rejected` with a precise correction
brief. The tool request attaches the verified rejected image first as the edit
target and the explicitly selected accepted dependencies afterward. Attach the
references relevant to the requested change; the verified base preserves
unaffected people and places. Changes to character identity, clothing or state
require that character's accepted sheet. Preserve all unaffected people,
geography, state, style and composition in the brief. The
target counts toward the five-image cap. A subset changes only this attempt's
inputs, not the asset's full dependency binding. Persist the actual target hash,
selected inputs, prompt and prior provenance. Never replace returned paths by
hand or use a targeted edit to bypass dependency checks or legacy attempt rules.
Keep the edit prompt focused on the local change and explicit invariants; do not
replay the full scene-generation brief or request a fresh interpretation of its
style. The base image supplies the established composition and rendering. No
API-only model selector, mask, action or conversation-ID control is implied by
the built-in tool. A preservation instruction is not a guarantee of identical
pixels. Inspect the whole edited image, including previously passing regions,
and reject new drift before proceeding.
Use UTF-8 files for multiline prompts, decisions, and evidence. Read-only dry
runs do not consume an attempt or approval. Persist attempts by stable asset ID;
renaming files or resuming a session cannot reset them. New-policy editions have
no numeric generation budget or per-asset cap. Correct autonomously within the
requested scope. After two unsuccessful fixes, explain the diagnosed cause and
change the composition, state guidance, or conflicting references instead of
repeating the same request. Ask only when an actual tool/access problem,
source conflict, or user-owned decision prevents progress. Legacy editions
retain one initial run plus two corrections and their `extra-attempt EDITION ID
--decision-file FILE` mechanism until explicit migration. Failed calls count
conservatively. A changed accepted visual invalidates its dependent scenes,
render, review, and approval.

`stats EDITION` reports recorded attempts, outcomes, durations, and unused
references from the existing manifest. Preserve actual timestamps and tool
provenance across resumes; missing historic timing is unknown. These statistics
help diagnose rework. They do not represent account-wide weekly usage, establish
a budget, or create another ledger/artifact.

If a generation is interrupted, verify its exact process/tool handle is terminal
or missing before recovery. A stored `generating` flag, elapsed time, or observation
timeout is not proof. `resolve-generation EDITION ID --outcome failed|ready
--evidence-file FILE` records the authoritative process evidence, validates any
completed candidate, and retains the consumed attempt. Never restart a live call.

Changing an edition's generation backend or review policy requires the actual
user instruction through `configure-workflow`. Preserve prior attempts and
provenance, invalidate affected approvals and outputs, and keep user decisions
distinct from assistant reviews. New editions default to Codex generation and
assistant intermediate review; do not silently relabel legacy API outputs.

Source hashes are checked before stages and resumption. Source drift requires a
user version decision; never read historical Git prose to bypass it. Explicit
repinning invalidates approvals and dependent outputs, retaining attempt counts.
Every user approval records decision text and a digest of the precise stage
inputs. Assistant visual review has its own evidence and digest; it cannot
substitute for final user approval or independent edition review. Never claim
visible review without inspecting the actual pixels.

## Independent review contract

Read the complete source first, then the final edition. Inspect every selected
reference and scene and the responsive preview. Inspect all PDF pages only when
PDF output was requested. Check:

- complete prose, punctuation, emphasis, scene breaks, and ordering;
- depicted events and appearances against source and universe authority;
- cross-image identity, costumes/forms, geography, objects, lighting and style;
- location/object rendering against the accepted character sheets' pen contours,
  hatching, restrained washes, paper texture, and stylization; matching palette
  alone does not pass, and painterly/photographic/3D drift requires correction;
- one identity per character reference sheet, correct name/role heading and
  filename, and no reference-sheet labels carried into interior scenes;
- one distinct place per location image, shown as a single coherent environment
  rather than a montage, with accurate filenames and consistent state geography;
- clean anatomy, contact points, object integrity, and image finish;
- coverage of major exchanges, useful moment selection, centerpiece impact at
  actual reader size, exact depicted state, spoiler placement, alt text and
  optional captions;
- one existing Library card and canonical story URL, preserved source metadata
  and order, illustrated cover/label, the shared Pages branding/Library/theme/
  repository header with one working theme control, and no
  redundant original-reader or unrequested PDF link;
- the existing catalog's exact Writing Prompt displayed as escaped literal text
  before the story prose, separately from it; no workflow instructions, regenerated
  prompt, omitted content or Markdown reinterpretation;
- typography, cover proportions, page numbers, margins, scene breaks, readable
  text, image placement, and absence of clipping/overlap/accidental blank pages.

Write review.md using this declaration structure (REVISE wherever a gate fails):

```markdown
# Illustrated edition review

Verdict: PASS
Reviewer: <independent agent ID>

- Source fidelity: PASS
- Visual continuity: PASS
- Web readability: PASS
- Every PDF page: NOT REQUESTED

## Findings

- Blocking: none
- Evidence: concise visible observations of the complete web edition and, when requested, all PDF pages.
```

Use `Every PDF page: PASS` only for a requested PDF after inspecting every page;
use `NOT REQUESTED` for web-only output. Use `Blocking: none` only on PASS. Include page references for PDF findings,
not a reasoning trace. The artist cannot
certify its own output. Mechanical tests alone cannot establish semantic PASS.

## Publication

Require final approval and a current passing edition review. From the worktree:

```powershell
python -m illustrated.edition validate EDITION --phase capture
python pages/build.py capture-illustrated EDITION
python pages/build.py check
python pages/build.py build --output _site
```

Capture requires the original story already in the publication catalog and
reconciled source/catalog canon markers. Never automatically publish or edit
that original to satisfy the prerequisite. Store edition artwork/prose separately
while replacing the reader at `stories/<source-slug>.html` and the cover/label
on its existing Library card. Preserve source metadata, order, count and catalog
bytes; do not publish another reader or entry. One captured edition per source
is selected; named final-approved capture replaces its previous selection.
Ordinary story capture/capture-all never refresh editions. Published snapshots remain
frozen until explicitly replaced. Stage the edition, illustrated snapshot and
captured assets; commit, push with upstream, and open a draft PR. Do not merge.
Builds use only captured prose, artwork, and explicitly requested PDFs; never production generation
or source traversal. Final edition assets are derivative illustrations, not
canon authority.

A renderer/header change builds from stored snapshots without recapture,
regeneration, or editing old production packages. Publication of new artwork
still requires the named capture above. A pushed branch or draft PR alone is
not a changed live reader: verify the intended captured selection in the built
story URL, and report draft-PR status separately from deployed publication.
