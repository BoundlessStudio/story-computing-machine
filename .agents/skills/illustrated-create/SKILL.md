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
final edition.pdf. No duplicate prose draft belongs there. Existing source
prose is loaded by its pinned identity; publication captures a complete body.
Temporary candidates, prompt/decision/evidence input files, HTML previews, and
PDF page renders stay in an ignored temporary directory or OS temporary space.
Git preserves history. Do not create ledgers, separate bibles, approval receipts,
or extra lifecycle documents.

The coordinator owns prompt.md and edition.json. The planner owns plan.md. The
artist owns assigned reference/illustration assets through lifecycle commands.
The independent reviewer owns review.md. The export tool owns edition.pdf.
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
   reused or requested new cover, art direction, and correction allowance. Stop
   for explicit user plan approval. Only the coordinator records the actual
   response with `approve EDITION plan --decision-file FILE`.
3. **Visual development.** Use the imagegen skill's explicitly authorized API
   path. Generate references one asset per call, based on inspected source cover
   and original image evidence. Cover character faces, silhouettes, proportions,
   clothes, relevant expressions and viewpoints; include each story-required
   outfit/form. Location references establish stable geography, entrances,
   materials, scale, and recurring lighting conditions. Add object/style sheets
   only when needed. Every external reference must have an assigned useful role
   in reference development. Proposed unspecified details are visual design,
   never new universe facts. Inspect and accept each selected image.
4. **Visual approval.** Reuse the existing cover by default; display it explicitly.
   A requested new cover belongs only to this edition. Generate artwork without
   lettering; the layout engine renders the exact source title as selectable
   text on its title page, with no invented credit. Produce a representative layout with
   `python -m pages.illustrated_editions layout-sample EDITION --output TEMP_DIR`.
   Inspect it, then record `layout-preview EDITION HTML_PATH --evidence-file FILE`.
   Show all selected references, cover, and layout. Require explicit approval
   before any scene artwork. Record `approve EDITION visuals --decision-file FILE`.
5. **Illustrate.** Assign illustrated_artist one planned image, its exact brief,
   approved character/location/object reference files, and any supplementary
   preceding accepted scene. Always attach the applicable approved reference
   bytes to the API; preceding scenes alone are insufficient. The written brief
   distinguishes each input's role. Generate a complete illustration per call,
   never the typeset prose. Inspect source truth, identity, clothing, geometry,
   objects/contact points, anatomy, time of day, palette, and tone. Accept only
   visibly successful outputs; fix targeted problems within the allowance.
6. **Compose and review.** Run `python -m pages.illustrated_editions render EDITION`
   and `preview EDITION --output TEMP_DIR`. Use the PDF skill to render every PDF
   page to images and inspect them. Assign a fresh illustrated_reviewer the
   source, final accepted assets, plan, exact HTML/PDF, and rendered pages.
   Review is of the edition, not permission to revise its source story. A REVISE
   goes to the responsible producer, followed by a fresh reviewer. Record a
   passing review with `record-review EDITION --reviewer ID --evidence-file FILE`.
7. **Final user approval and publication.** Show the web preview and downloadable
   PDF after independent PASS. Obtain explicit final approval of those exact
   outputs, then record `approve EDITION final --decision-file FILE`. Follow
   Publication below. The final response links the edition/PDF and draft PR.

## Planner contract

Write plan.md with these sections:

- **Source and visual analysis:** summary, themes, tone; all characters, locations,
  important objects, and appearance/state changes relevant to the illustrations.
  Attribute established facts to source passages; label proposed visual choices.
- **Art direction:** use one nonempty `## Art direction` section; line/rendering language, palette, light, texture, camera,
  realism/stylization, mood, and recognizable connections to cover/originals.
- **Reference inventory:** stable IDs, requested roles, outfits/forms, locations,
  objects, external-input mapping, and exactly what must remain consistent.
- **Illustration plan:** stable ID, source anchor, scene purpose, visible facts,
  framing, referenced asset IDs, layout, alt text, optional caption, and prompt.
  Choose opening, reveals, emotional turns, climax, and ending where the source
  earns them. Avoid quotas of repetitive scenes, spoilers placed before their
  reveal, invented events, and decorative explanatory lore.
- **Presentation and counts:** mode, house-rule exceptions explicitly requested,
  exact reference/interior/cover counts, one initial generation plus two
  automatic corrections per generated asset, and selected page treatments.

Source-based prose and facts control depicted events; an outline is design
intent. Reference sheets guide visual continuity, never authorize source edits.
No captions by default. Optional captions are editorial additions clearly
separate from prose; any quoted passage must be exact. Never invent sections,
author credits, dialogue, captions claiming new story facts, or omitted prose.

## Generation and lifecycle controls

Use the unchanged bundled imagegen/scripts/image_gen.py through the edition
lifecycle's `generate` command. Model: gpt-image-2.5-sunburst-2026-09-08. Quality:
high. Output: PNG. Sizes: 1024x1024, 1536x1024, or 1024x1536, explicitly chosen per
asset. Reference-conditioned generation uses its edit API path and actual image
inputs. No silent model downgrade or switch to the built-in tool. Local
OPENAI_API_KEY and model access are prerequisites; never print or request the
secret in chat. Installing this workflow does not authorize a sample paid run.

Useful commands (all `python -m illustrated.edition`):

- `inspect-original EDITION ID --evidence-file FILE`
- `set-asset EDITION ID --kind character|location|object|style|illustration|cover
  --prompt-file FILE --size SIZE [--reference ID ...] [--after ANCHOR]
  [--layout inline|full-page|spot --alt TEXT --caption TEXT]`
- `generate EDITION ID --out TEMP_IMAGE [--dry-run] [--correction-file FILE]`
- `accept EDITION ID --evidence-file FILE`
- `reject EDITION ID --evidence-file FILE`
- `repin-source EDITION --decision-file FILE`
- `validate EDITION --phase draft|plan|references|render|review|final|capture`

Inspect and accept or reject a ready candidate before starting another image.
Use UTF-8 files for multiline prompts, decisions, and evidence. Read-only dry
runs do not consume an attempt or approval. Persist attempts by stable asset ID;
renaming files or resuming a session cannot reset them. After the initial run
plus two corrections, stop for actual user direction; `extra-attempt EDITION ID
--decision-file FILE` records authorization for another attempt. Failed calls
are counted conservatively. A request to change an approved visual invalidates
its dependent scenes, render, review, and approval.

If a generation is interrupted, verify its exact process/tool handle is terminal
or missing before recovery. A stored `generating` flag, elapsed time, or observation
timeout is not proof. `resolve-generation EDITION ID --outcome failed|ready
--evidence-file FILE` records the authoritative process evidence, validates any
completed candidate, and retains the consumed attempt. Never restart a live call.

Source hashes are checked before stages and resumption. Source drift requires a
user version decision; never read historical Git prose to bypass it. Explicit
repinning invalidates approvals and dependent outputs, retaining attempt counts.
Every approval records user decision text and a digest of the precise stage
inputs. Agent self-reports never substitute for user approval or visible review.

## Independent review contract

Read the complete source first, then the final edition. Inspect every selected
reference and scene, the responsive preview, and all rendered PDF pages. Check:

- complete prose, punctuation, emphasis, scene breaks, and ordering;
- depicted events and appearances against source and universe authority;
- cross-image identity, costumes/forms, geography, objects, lighting and style;
- clean anatomy, contact points, object integrity, and image finish;
- useful moment selection, spoiler placement, alt text and optional captions;
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
- Every PDF page: PASS

## Findings

- Blocking: none
- Evidence: concise visible observations, including all inspected PDF pages.
```

Use `Blocking: none` only on PASS. Include page references for findings,
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
that original to satisfy the prerequisite. Store edition publication separately;
ordinary story capture/capture-all never refresh it. Published snapshots remain
frozen until explicitly replaced. Stage the edition, illustrated snapshot and
captured assets; commit, push with upstream, and open a draft PR. Do not merge.
Builds use only captured prose, artwork, and PDFs; never production generation
or source traversal. Final edition assets are derivative illustrations, not
canon authority.
