# The Shape of Mercy — independent graphic-novel review

## Pre-generation plan review — 2026-09-18

- **Verdict: REVISE.** Two narrow preflight repairs below are required before plan PASS; two accompanying clarifications are minor. The proposed 25 comic pages, 95 main panels, 12 new references, unchanged reused cover, and 26-page PDF scope need no change.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; producer: `/root/mercy_plan`. The reviewer did not create or alter the source, plan, artwork, manifest, or approvals.
- Worktree: `D:/Development/BoundlessAi/story-computing-machine-gn-the-shape-of-mercy`; branch: `codex/graphic-novel-the-shape-of-mercy`.
- Scope: complete source and original prompt read after verifying valid bundle `canon: true`; complete edition prompt, 25-page script, reference inventory/input plan, and relevant manifest inspected. Read AGENTS.md, the GN contract, universe README and style guide, applicable Bellweather authority in characters/rules/factions/locations/timeline/glossary, and GN STYLE.md. This is adaptation feasibility review, not renewed prose certification.
- Available pixels: selected `cover.jpg` inspected at native 864 × 1536 with `view_image`. Its SHA-256 matches the source `title-image.jpg`, so the inspected copy contains the unchanged source pixels. No generated reference, comic-page, or PDF pixels exist to inspect at this stage. No external original images were recorded in the source or edition request.

### Required fixes

1. **R1 — page 02, panels 02.1–02.3; shared N1 state.** N1 currently includes active blue ward panes, and page 02 explicitly enters N1 at 02.1. Rowena only raises those panes at 03.1. Page 02 excludes fire/ice but never overrides the early panes. This inherited state can depict her response before the intrusion/accusation. Minimal repair: split the broken-door/pre-ward state from the active-ward state, or explicitly exclude projected panes throughout page 02 and start them at 03.1. Preserve ordinary silver clothing channels; the repair concerns projected blue panes.
2. **R2 — reference generation dependencies R02, R04, R06, R07, R10.** Their first-use timing is specified, but their actual accepted image inputs are not. This leaves five proposed references disconnected from the edition's concrete GN rendering anchor; R10 also needs its Hall threshold geometry tied to the already established interior. Minimal repair: give explicit image input IDs and roles for each, for example accepted R01 style pixels for R02/R04/R06/R07, and accepted R01 style plus R08 doorway/threshold geometry for R10. Keep one identity/place per output, all sets within five images, and no transfer of the style-reference character into another sheet. No new reference is needed.

### Minor clarifications to include in the repair

- **R3 — per-page input legend and page 21.** Define `Pnn` as the identified accepted earlier page, rather than necessarily the immediately preceding page. The intentional P19 bedroom return input for page 21 is appropriate; keep independent inspection of page 20 for sequence continuity. No input substitution is required.
- **R4 — panel 03.1 source provenance.** The source's quoted segment is `“You will leave,”`, while the Q-original field currently ends it with a period. Correct only that original-case provenance punctuation and identify the sentence-ending display punctuation as lettering/adapted punctuation if needed. The exact printed `YOU WILL LEAVE.` can remain. The speaker and meaning are already correct.

### Findings that support the proposed scope

- **Coverage and causal intent:** Pages 01–05 retain the appointment/ink setup, father's accusation, surviving imposed command, failed wards, destructive rescue, ice entrapment, and injury. Pages 06–13 preserve Adrian's initially sincere ignorance, subjective perception, childhood abuse testimony, permanent loss of Garran's faculty, bounded memory cost, testing and concealment, competing parental commands, and Phoebe's distinction between the creature's own desires and coercion. Pages 14–25 retain voluntary sibling restraint, the exact pre-act consent boundaries, all four witness acknowledgments, Garran's unrepairable loss and continuing responsibility, narrow approach, morning evidence, negotiated safeguards, agreement, damaged orchard, and actual final stewardship signature.
- **Knowledge boundaries:** 08.1 shows only the remembered pre-cut childhood fragment; testimony supplies what Adrian cannot remember. 18.3 ends before active severance and turns directly to morning. Page 20 has explicit witness-account captions and distinct double framing; it does not give witnesses Adrian's subjective magical sight or imply recovered memory. 21.4 states that evidence cannot fill the absence. These are faithful choices.
- **Mechanics and moral consequence:** The bracelet remains a nonliving focus fed through the living beast's old bond. Records remain ordinary evidence. Native storm, affinity, fire, cold, and wards are not destroyed by the narrow cut. The local desire doctrine is explicitly attributed to the household. Garran's real grief is retained without excusing coercion. The consent and final safeguards preserve the source's exceptions and limits.
- **Panel feasibility and reading path:** Varied action-to-reaction frames, clearly subordinate simultaneous insets, wider pauses, matched gazes, and protected gutters serve these scenes. Page 04's tall left frame has an explicit route into the right frames. Page 16 separates dictation, completed writing, pen handoff, signing, and witnesses; no simultaneous writing/signing contradiction remains. Page 24 adds hands chronologically with fixed handedness and injury states. Their close framing is feasible with five individual identity inputs and does not require a sixth location image. No panel-count change is indicated.
- **Lettering feasibility:** Exact display text is supplied for all 95 main panels, with original wording distinguished from adaptations. The longest page has approximately 74 visible words; the longest panel approximately 27. The long consent and safeguard sentences are divided without dropping their scope. At the proposed 40–44 px type, this is a feasible 1024-wide plan, including the five-panel consent page, provided art leaves the stated lettering space. This is not a pixel legibility PASS: every future balloon, signature, tail, and caption must still be checked at full, desktop, and approximately 390 px reading width.
- **References and state overrides:** All 12 references have concrete consumers; one-person/one-place constraints are respected, and every comic-page input set has at most five images. R09's N3 geometry is explicitly overridden by N4/N5/N6 at later consumers. R10's intact geometry is explicitly overridden by burned trees, meltwater, nighttime reconstruction, wall break, and morning aftermath on pages 20/25. These written overrides are feasible, with actual-pixel preflight still required. The five-identity correction strategy must preserve omitted identities from the edit target or regenerate with the five sheets; it cannot silently add a sixth input.
- **Cover and style:** The actual cover reads `The Shape of Mercy` and depicts a wet ordinary sheet, pen, broken black cord, intact lightning/ice/fire lines, and antler shadow. Its photographic texture is not a GN style anchor and its cords are symbolism. The plan correctly excludes both from literal interiors while reusing the cover unchanged. The proposed crisp black contours, flat saturated fills, hard-edged shadows, white gutters, yellow captions, and uppercase lettering follow STYLE.md. No future reference or page style PASS is implied.

### Reviewed versions

Paths below are relative to the dedicated worktree. SHA-256 binds this verdict to the bytes inspected.

| Input | SHA-256 |
| --- | --- |
| `graphic-novels/the-shape-of-mercy/plan.md` | `d5cdc967d879d44512c5d95434cc810a268527943b519c1f7c7e7535fbf78ece` |
| `graphic-novels/the-shape-of-mercy/prompt.md` | `176e72c32088810574534b010c74344fa2c0a153a10744cac29757bfcdc52db7` |
| `graphic-novels/the-shape-of-mercy/edition.json` | `a2b30dc960005ba988f2c84f7eb7e73240d0ba2c05c8aa3026da5ea63f1d28ec` |
| `stories/the-shape-of-mercy/05-story.md` | `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a` |
| `stories/the-shape-of-mercy/00-prompt.md` | `a403840d96154a5985b9a7a3de7d8b6a1e05fc9f5d872afada4735293e81c13d` |
| `stories/the-shape-of-mercy/story.json` | `1a08afc35706cb7d9d0c8cec437e1debdba589cd791c785bd50ffc1ed67de7d5` |
| Source `title-image.jpg` and selected `cover.jpg` | `fe21bdac14823ff34de1aa354a64f68c085457e1d5be555fd23abf6c1c1ccbe9` |
| `graphic-novels/STYLE.md` | `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f` |
| `AGENTS.md` | `6f9845be186dcff8117705ecd39eb78a25d91c1b31a68282e08cc8fae75099d1` |
| `.agents/skills/graphic-novel-create/SKILL.md` | `54e437d058244a5fe83547f53af88687d554c70136ad962b80b18418bb6fd8bc` |
| `universe/README.md` | `ff7a9e9568c52737f06dffd190584d16a68a1754e18d7444f8010607637f5aef` |
| `universe/style-guide.md` | `9059f1dcfa9d01fb5279ae8d921a33bb09cf45c9844446034620ee8496bff966` |
| `universe/rules.md` | `4885af39c8b4652bcd03064e95d7d5fd814402014888b1de30b55f5228e049ca` |
| `universe/characters.md` | `dbe1d4e8cb8b9bab1936994fbc945ac655ecb659d90a7e879eb2234a2d87e8f6` |
| `universe/factions.md` | `87606896be6880257fa3225c439d5df2d1216a8143db79ddbf7c422b2d779b57` |
| `universe/locations.md` | `767211808229a55c2373606027a7e7d9b95fdcdfa6318eacfbbd6ed44fb8205d` |
| `universe/timeline.md` | `a81e89dd8ba4827fde5d5777339461e44ec4233970f026ccaf439f196708205e` |
| `universe/glossary.md` | `dc77578ce53305cbfaf7ca6fb90c9cda9aadceddea62c5de8e303dc917b07ceb` |

Source snapshot commit recorded by the coordinator: `dd47e0ff894a93f0a397a43d80b3c4541b0b6954`. Output of this assignment: this `review.md` only. The creator/coordinator must repair the plan; an independent recheck must bind a subsequent verdict to its new hash.

### Other scopes

- Generated references: **NOT REVIEWED** (not generated).
- Comic pages 01–25: **NOT REVIEWED** (not generated).
- Complete PDF book: **NOT REVIEWED** (not assembled; zero rendered PDF pages inspected).
- User plan/count approval: pending; this review is not user approval.
- Final user/PDF approval and publication: pending; not covered by this review.

## Targeted independent plan recheck — 2026-09-18

- **Current plan verdict: PASS.** R1–R4 are resolved in the revised input below. No blocking plan finding remains. The earlier REVISE is retained as the verdict on its earlier plan version.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`. Repairs were made by the coordinator, not this reviewer. Review output remains this `review.md` only.
- Rechecked plan SHA-256: `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`.
- Rechecked manifest SHA-256: `bcd215b21c5bd15c48ccade8c1dfe2f3e1e23214fe045a824a4d078a343deff8` (input state: `awaiting-independent-plan-recheck`). Its plan pin matches the actual file; its reference dependencies match the revised table.
- Confirmed unchanged: edition prompt, complete source prose/prompt/state, selected cover, GN STYLE.md, AGENTS.md, GN contract, and all authority files listed in the preceding reviewed-version table. Their listed hashes continue to bind this review. The existing full-source and cover-pixel inspection therefore remains applicable.

Recheck evidence:

1. **R1 resolved — pages 01–04 and shared states.** N1a now explicitly excludes projected blue panes throughout page 02. N1b begins at 03.1, where the script says Rowena first raises them; page 04 inherits N1b before the firebreak state. Searches find no remaining unsuffixed N1 inheritance. Door intrusion, accusation, ward response, and rescue now have a consistent order.
2. **R2 resolved — R01–R12 dependency table and manifest.** All reference outputs now have exact accepted-image inputs and roles. R02/R04/R06/R07 use R01 for rendering only; R10 uses R01 for rendering and R08 for the shared Hall threshold geometry. Explicit exclusions prevent style references from transferring their character, costume, anatomy, or heading into another subject. All sets are acyclic, available before their first consumers, and within the five-image limit. One-identity/one-place output boundaries remain intact.
3. **R3 resolved — input legend and pages 19–22.** Pnn now means the identified accepted earlier page. The explicit P19 choice supports page 21's return to the bedroom; the immediately preceding page still receives independent adjacent-page inspection. Rereading the surrounding sequence confirms that page 20 remains marked witness reconstruction and page 21 returns to ordinary morning frames.
4. **R4 resolved — panel 03.1.** The Q-original field now preserves the source comma; the unchanged printed period is explicitly labeled standalone-balloon punctuation. Speaker, wording, and intent are unchanged.

The repair retains 25 comic-page sections and 95 main panels, the same page-image input sets, 12 proposed new references, one unchanged reused cover, zero cover generations, and a 26-page final PDF. The source-coverage, narrative, lettering-feasibility, page-turn, and five-identity close-framing findings from the original review stand. No broader recertification or art inspection is claimed by this targeted recheck.

**Limits of PASS:** This is the independent pre-generation plan gate only. Reference images, comic pages 01–25, and the assembled PDF remain **NOT REVIEWED** because they do not yet exist. Actual 390 px readability, complete saved-pixel page review, and fresh complete-PDF review remain future gates. Plan/count approval still requires the user's actual response bound to these inputs; this assistant verdict grants no user approval or image-generation authorization.

## Page 001 independent pixel review — 2026-09-18, attempt 01

- **Verdict: REVISE.** Scope is saved `pages/page-001.png` only, SHA-256 `c9f2c3914cedd802f34e0b3dc5c18c6c6a6e7f200cfc1a18512e98cb7c4bfcb7`.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; this reviewer did not produce the page or references. Only this review file is changed.
- Inspected every panel and visible word in the actual 1024 × 1536 image and supplied 768 px and approximately 390 px previews using `view_image`. Also inspected actual accepted R01/R03/R05/R08 pixels, reread source lines 9–31 and Page 01 script, and confirmed the complete previously reviewed script/coverage and STYLE.md hashes remain unchanged. Page 001 has no preceding comic page; page 002 does not yet exist.

### Blocking findings

1. **P001-R1 — all panels, especially 01.2 and 01.3: reading-size lettering.** Wording is correct, but the approximately 390 px image reduces letters to roughly 6–9 px high. Marcus's opening balloon and the gathering/recalled-ink captions are too small for comfortable ordinary phone-size reading without magnification. Desktop/full-size readability does not cure this. Enlarge and reflow the lettering and its reserved balloon/caption space within the existing four panels, using the approved approximately 40–44 px starting scale at 1024 width and checking the actual result at 390 px. Recompose the surrounding crops as needed; retain every exact word, the recalled-speech distinction, speaker tails, and the four beats. Do not merely upscale the current whole page.
2. **P001-R2 — 01.1, 01.2, 01.4: rendering drift in environments and props.** Background columns, guests, candles, foreground flowers, and reflective goblets use conspicuous soft photographic depth-of-field blur, bloom, and smooth reflective modeling. The blurred flowers/goblet at the lower-left of 01.4 are especially evident at native size. Accepted R08 retains crisp outlined architecture/objects and graphic value steps; its localized candle light does not justify this broad soft-focus treatment. Re-render these areas with crisp black contours, broad flat fills, and hard-edged shadows, keeping candlelight subordinate. Preserve the passing faces, clothing, exact text, anatomy, props, and staging; inspect the whole corrected page for collateral changes.

### Passing observations to preserve

All 74 scripted words are present with correct spelling and punctuation, including the recollection's quotation marks and final interruption dash. Marcus's and Adrian's tails are unambiguous, Rowena's final tail points to her cropped figure, and the quoted earlier remark remains in yellow narration rather than present speech. Four frames read cleanly downward with white gutters and no confusing inset, overlap, or frame crossing. The knife joke, two-person exchange, gathering/recalled ink remark, and interrupted appointment occur in order. Adrian, Marcus, and Rowena retain accepted facial/hair identities, respective charcoal/blue/dark costumes, and silver sleeve channels. Visible hands, cup grip, and two-finger ledger contact are coherent. The ordinary brown ledger has no added readable text or magic. N0 remains intact and candlelit, with no storm, crisis ice, projected wards, extra named siblings, or injuries.

### Version bindings

| Input | SHA-256 |
| --- | --- |
| Approved `plan.md` | `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2` |
| Source `05-story.md` | `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a` |
| GN `STYLE.md` | `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f` |
| R01 `references/adrian-bellweather.png` | `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3` |
| R03 `references/marcus-bellweather.png` | `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f` |
| R05 `references/lady-rowena-bellweather.png` | `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f` |
| R08 `references/bellweather-hall-intact.png` | `d2a43f461f9cb0832d12213249f08fc8e4bb169b5f4972528c14d43b32b85051` |
| Inspected manifest snapshot | `9843645ba5571717eb846f4516d79c3cd6ddadeb16359ef31ac5f1fd640d5077` |
| QA `page-001-390.png` | `ae0a2aeb0ba74375683472964256f61efa2eb37fab9964edab44871c147906a1` |
| QA `page-001-768.png` | `f27d36e3366517831b0f82ee3c44803ecf4855e380af8c6fdf058e97f67a7c81` |

QA files were supplied under `C:/Users/jamie/AppData/Local/Temp/codex-gn-the-shape-of-mercy/qa/` and were read-only review inputs. No page PASS is granted; recheck the corrected saved page independently before page 002 generation. This verdict is not a complete-book review or user approval.
## Page 001 independent corrected-page recheck — 2026-09-18

- **Current page 001 verdict: PASS.** Reviewed selected `pages/page-001.png`, SHA-256 `b293e56f238a4bc18191b78faf04a43c8cb03313d049c8bdb5979713ffb3ba65`. The earlier REVISE remains the verdict on the superseded image.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the page producer. Scope: both prior findings and the entire edited page for collateral changes. Only `review.md` is written.
- Viewed the actual saved 1024 × 1536 page and its 768 px and approximately 390 px previews in full. Re-read every visible word and punctuation mark against the approved Page 01 transcript; inspected every panel, face, hand, prop, balloon/tail, gutter, and transition. No neighboring comic page exists yet.
- Confirmed unchanged actual hashes for approved plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`, source prose `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`, STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`, and R01/R03/R05/R08 at their hashes recorded in the preceding page review. Their full-source/script and actual reference-pixel inspections remain applicable.

**P001-R1 resolved:** Caption and balloon lettering is materially enlarged and reflowed. All 74 words, quotation marks, punctuation, and the interruption dash remain correct and are readable at the actual 390 px preview without enlarging it. The larger boxes retain safe text insets, clear speaker tails, visible faces, the recalled-speech distinction, and the knife/ledger actions. No text is clipped or added.

**P001-R2 resolved:** Architecture, guests, candles, flowers, and vessels now have clear graphic edges and substantially flatter shading. Candle light remains localized; the earlier broad photographic blur and bloom no longer governs the room or foreground. The ink contours, saturated fills, hard shadow steps, white gutters, yellow captions, and uppercase letters are coherent with the accepted GN references and written style. Some controlled reflective highlights remain on tableware without defeating the outlined treatment.

**Whole-page collateral check: PASS.** All four planned beats remain in order with clear downward reading. Marcus and Adrian's distinct accepted faces/hair and blue/charcoal coats remain stable; Rowena retains her graying swept-back hair, dark high collar, and silver channels. Visible anatomy, Marcus's cup grip, Adrian's plain-knife scrutiny, and Rowena's two-finger contact with the ordinary ledger remain coherent. The Hall is intact in N0, with anonymous guests, candlelight and orchard glimpses; no premature crisis state, named extra sibling, magical ledger, or new readable writing appears. No overlap, frame crossing, clipping, or gutter ambiguity was introduced.

QA preview bindings, under `C:/Users/jamie/AppData/Local/Temp/codex-gn-the-shape-of-mercy/qa/`:

- `exec-12a30b44-5a8c-49b6-a755-beb19755351d-390.png`: `5d5a49f6847f6f6b091c568edc577f4c73a5880df2a57f767600697d25b377e1`.
- `exec-12a30b44-5a8c-49b6-a755-beb19755351d-768.png`: `72ab4d3075e9d639c40a6c13b1cddd75db76bbede8dcb3d0602fac2d5f186fbe`.

This PASS satisfies the independent page 001 gate for these bytes. It is not a whole-book verdict or user approval; pages 002–025 and the actual assembled PDF remain NOT REVIEWED.
## Page 002 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-002.png`, SHA-256 `fc48c0c36209fc54f80aed8f69789a0a939c8329ca10199764fc39708d51dcce`, 1024 × 1536 RGB.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected all saved page pixels at native, 768 px, and approximately 390 px widths; reread Page 02 and source lines 33–55; inspected actual R04/R06/R07 and compared against previously inspected, unchanged R01/R05 and accepted page 001. The complete reviewed script/coverage remains unchanged. Only this `review.md` is written.
- **Text and reading: PASS.** All 26 scripted words and punctuation are correct, with no unlisted writing. The upper absence caption, Phoebe's plea, the family's look, and Garran's accusation remain legible at 390 px. Both balloon tails identify their speakers; Adrian's silence/ignorance is preserved. Three panels read down clearly through white gutters; the large intrusion, compressed reaction, and lower confrontation have distinct narrative weight. No antler, balloon, or text is clipped in the upper panel; the lower beast crop is intentional.
- **Identity, anatomy, and state: PASS.** Phoebe is the sixteen-year-old reference identity in her green tunic, with a plausible raised five-finger hand; Rowena retains her mature face, gray hair and silver-channel gown. Garran is the lean current adult in a soaked coat; the dull bracelet is on his anatomical right wrist in both views and emits no power. Adrian matches page 001. The stormhart's enormous scale, complete upper-panel antlers, translucent-looking hide/internal storm, visible forelegs/hooves and irregular bloody throat scar match R07; hidden hindquarters are naturally occluded by the doorway. No leash or collar is added.
- **Chair finding: nonblocking.** Panel 02.2 visibly shows a sharply tilted chair beside/behind the abruptly standing Phoebe. Its floor contact is cropped, but the tilted back/rails and the fully sideways chair amid the intrusion debris in 02.1 make the toppled-chair beat readable. It does not read as her calmly remaining seated or as a floating prop. No additional frame or floor detail is required.
- **Continuity and style: PASS.** The intact supper gives way to the broken orchard threshold, scattered furniture and extinguished candles. N1a contains no projected wards, ashfire or ice. Head-on intrusion followed by the family reaction and Adrian's foreground confrontation keeps the threat/location understandable. Contours, graphic shadows, flat color fields, yellow captions and uppercase lettering match the settled page treatment; stormlight is a story-supported effect. No photographic blur or broad candle bloom returns.

Version bindings (SHA-256):

| Input | SHA-256 |
| --- | --- |
| Approved plan | `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2` |
| Source prose | `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a` |
| GN STYLE.md | `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f` |
| Adjacent accepted page 001 | `b293e56f238a4bc18191b78faf04a43c8cb03313d049c8bdb5979713ffb3ba65` |
| R01 Adrian | `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3` |
| R04 Phoebe | `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251` |
| R05 Rowena | `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f` |
| R06 Garran | `e3d8e22d3b687e899d5eb79ebbe5876c456c5909c29078a65622bb17997494b0` |
| R07 Stormhart | `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6` |
| QA 390 px | `faba7cd84099219d2fb75ba154e406afa27e660e59990a18bc1ebcd69e1b41a2` |
| QA 768 px | `d13d35bae3daccf75a11a4db243d129cdb0e1d1bf74d3cbaed55cda40a1cc147` |

QA images are `exec-09dff5a2-5069-47ae-9f68-69bbf113c41a-{390,768}.png` in the previously recorded temporary QA directory. This passes page 002 only for the selected bytes. Page 003 onward and the assembled PDF are NOT REVIEWED; this is neither whole-book PASS nor user approval.