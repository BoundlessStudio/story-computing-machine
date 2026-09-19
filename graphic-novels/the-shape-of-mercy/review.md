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
## Page 003 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-003.png`, SHA-256 `7a8b48546c757d27a6063f49c6686c52111f8a1f53c9ebbbd603caa47574cd65`, 1024 × 1536 RGB.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected the entire actual page at native, 768 px and approximately 390 px widths, including every visible word, face, hand, balloon/tail, prop, pane and inset. Reread approved Page 03 and source lines 57–87. Full previously reviewed script/coverage, source, style, five accepted reference versions and preceding page 002 remain unchanged by verified hashes. Only this review file is written.
- **Words, speakers, reading size: PASS.** All six scripted text elements retain exact words and punctuation and are readable at 390 px. The 03.2 balloon exits toward off-frame Phoebe at left while Garran's mouth remains closed. In 03.3 Phoebe's speech has a clear tail and Adrian's account is a separate yellow caption. In 03.4 Garran's upper balloon reads before Adrian's lower reply, with distinct tails; no speaker or order reversal remains.
- **Sequence and framing: PASS.** Four main panels progress from Rowena raising overlapping wards to the bracelet/scar cause-and-reaction, Phoebe's distinction, and the first pane breaking. The small framed scar detail is subordinate to 03.2 and reads as simultaneous, without covering its essential action or adding a separate event. The middle row reads left then right before the broad bottom frame. White gutters, nested borders and gaze/gesture keep the path clear; no problematic frame crossing or clipped lettering appears.
- **State, anatomy and continuity: PASS.** N1a on the preceding page becomes N1b here: candles remain out; blue ward panes appear for the first time. The bottom impact scatters one pane while deeper blue panes remain. No ashfire, ice, physical command rope or early perception braid appears. Garran's dull bracelet remains on his anatomical right wrist and supplies no emitted power. The scar remains a bodily wound, separate from intrinsic storm currents. Phoebe's open five-finger palm stays physically clear of the beast and blue plane. Current ages, reference faces, hair, dark/green costumes, Rowena's silver channels and plausible limb/contact states hold. Adrian remains Hall-left and Garran threshold-right in the final confrontation.
- **Rendering: PASS.** Clear black contours, graphic shadow shapes, controlled saturated color, white gutters, yellow narration and uppercase lettering retain the accepted treatment. Luminous blue is confined to story-supported ward/storm effects; the environment does not revert to photographic blur. The complete edited page shows no blocking collateral drift.

Version bindings:

- Plan: `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source: `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md: `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 002: `fc48c0c36209fc54f80aed8f69789a0a939c8329ca10199764fc39708d51dcce`.
- R01: `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R04: `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R05: `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R06: `e3d8e22d3b687e899d5eb79ebbe5876c456c5909c29078a65622bb17997494b0`; R07: `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`.
- Temporary QA `page-003-390.png`: `474741efd4d8f0a00c13c72a74b759456dd32fd41bd00f89a2bb6adb7dcb3825`; `page-003-768.png`: `74f51468ae154562b8ead08b59021297a6ab8ce9e5e1303725063e47726a0048` (same previously recorded QA directory).

This passes page 003 for the selected bytes only. Page 004 onward and the assembled PDF remain NOT REVIEWED. It is not whole-book PASS or user approval.
## Page 004 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-004.png`, attempt 02, SHA-256 `83e9b7dbe3d8eacd97cae84f7d63ea0339b63f65ab5c48dbe8e0d7d9119cfe66`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected the entire saved image at native, 768 px and approximately 390 px widths, including every caption, figure, hand, prop and panel transition. Reread approved Page 04 and source lines 89–97; inspected new actual R02/R10 pixels and compared previously inspected R01/R07/R08 and preceding accepted page 003 at verified unchanged hashes. The complete approved script/coverage remains applicable. Only `review.md` is written.
- **Text and reading: PASS.** Both yellow captions reproduce all 17 exact scripted words and punctuation and remain comfortably legible at 390 px. The pond panel is silent with no added text. The tall left action leads through Evelyn's arms into the upper-right firebreak, then down into the pond impact; three black-framed panels and white gutters keep the time and reading order clear. Effects remain inside their frames.
- **Action, anatomy and state: PASS.** Evelyn's two distinct arms and open palms direct white-orange ashfire through the damaged threshold away from fleeing guests. Her anatomical left glove remains worn and visibly smoking; the right hand is bare, with no premature bandage or exposed left burn. Adrian stays low behind an interior table and does not cast. The upper-right scene retains the costly burned crescent, blackening nearest trees, surviving flowering trees beyond, escaping birds and Evelyn at the doorway. The lower-right stormhart impacts visibly liquid pond water; curved sheets and droplets rise toward the Hall windows, without frozen shapes or ice. Visible limbs, hoof/water contact, enormous creature scale, branching antlers, living hide, intrinsic storm and throat scar remain coherent.
- **Continuity and style: PASS.** Hall/interior stays left of the orchard threat; the facade, threshold, low pond and tree/wall relationship follow the accepted environments while their intact states are correctly overridden. Broken doors and cracked glass remain. Indoor candle sconces now show unlit wicks, including the doorway view; the valid orchard ashfire is preserved. No extra named relatives appear. Evelyn's rust-red clothing, braid and face and Adrian's formal appearance match their references. Crisp contours, graphic shadow steps, saturated fire/storm accents, flat environmental treatment, white gutters and uppercase lettering remain consistent with the accepted pages; no blocking collateral drift is visible.

Version bindings:

| Input | SHA-256 |
| --- | --- |
| Plan | `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2` |
| Source prose | `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a` |
| GN STYLE.md | `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f` |
| Adjacent page 003 | `7a8b48546c757d27a6063f49c6686c52111f8a1f53c9ebbbd603caa47574cd65` |
| R01 Adrian | `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3` |
| R02 Evelyn | `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5` |
| R07 Stormhart | `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6` |
| R08 Hall | `d2a43f461f9cb0832d12213249f08fc8e4bb169b5f4972528c14d43b32b85051` |
| R10 Orchard | `c56eca8acdf1097a15e396d48b57f4f93d16964ecdd83bc4bf72ad5ef3eda272` |
| QA 390 px | `46d666b3cd52424398650b5849452420bcc226e585bd1b86049c1994c7be0eec` |
| QA 768 px | `7ade4a63d1a07bb60ceb089f9e031206755ab5012ef06f995e79281cca3c4cb9` |

QA previews are `exec-a390cb72-f68a-4a06-b7be-99a18b2b13f9-{390,768}.png` in the previously recorded temporary QA directory. This passes page 004 for these bytes only. Page 005 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.
## Page 005 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-005.png`, attempt 02, SHA-256 `33be47e8f265f20abfa3814fc17191cf466c5edda7e4838b3e2cf0b9320d210c`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and visible word at native, 768 px and approximately 390 px widths; reread approved Page 05 and source lines 99–113. Compared preceding accepted page 004 and previously inspected actual R01/R03/R05/R07/R08 at unchanged verified hashes. Only `review.md` is written.
- **Text and framing: PASS.** Both exact text units, punctuation and all 20 words match the script and remain readable at 390 px. Marcus's balloon tail is unambiguous; the last yellow caption remains narration. Four panels read downward through frozen wave, barrier/reaction, lightning/ward failure, and aftermath; the wider final gutter gives the injury a pause. No inset, overlap, frame crossing, clipped word or added text confuses the sequence.
- **Action and geography: PASS.** The previously liquid flood becomes a curved frozen wave, then a substantial jagged ice barrier between the orchard beast and gallery guests. The additional iced openings are visibly architectural passages: gallery-left and two passages flanking the head-table/fireplace area. The recessed fireplace with its separate lintel remains distinguishable and is not being counted as an exit. The intact reference state is overridden by frost, blocked routes and progressive window damage. Lightning branches through substantial ice; Rowena's thinner rectangular blue panes catch glass in the strike panel and are absent afterward. These effects remain distinguishable at reading size.
- **Anatomy, identity and continuity: PASS.** Marcus's hands/arms, panting stance and later slump against the pillar are coherent. His anatomical left sleeve becomes iced only in the final panel; the other sleeve remains blue. Adrian crawls behind an overturned table through glass/slush without an invented wound. Accepted faces, hair and formal costumes hold; Rowena and the stormhart match their actual references, and no additional named cast appears. Ordinary candles remain extinguished. Ashfire remains outside, and no early healing, recovered ward panes, physical command rope or misplaced bandage appears.
- **Rendering: PASS.** Crisp contours, graphic flat color/shadow shapes, white gutters, yellow narration and uppercase lettering follow the settled GN treatment. Lightning/ice reflections are story-supported, not broad photographic background blur. The whole corrected page shows no blocking collateral change.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 004 `83e9b7dbe3d8eacd97cae84f7d63ea0339b63f65ab5c48dbe8e0d7d9119cfe66`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`; R08 `d2a43f461f9cb0832d12213249f08fc8e4bb169b5f4972528c14d43b32b85051`.
- QA `exec-cad13307-a29c-43ce-a7e1-be865eebf65c-390.png` `fa544ddf75ac555b638e72e3842c7e4745132cce4075c264cb851f0c3dea88d0`; corresponding `-768.png` `ccffcb3dcbdaf00206d7cd9550aa1925bb9b93e8ad7326cf406e52acb3f4df76`, in the previously recorded temporary QA directory.

This passes page 005 only for the selected bytes. Page 006 onward and the actual assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.
## Page 006 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-006.png`, attempt 02, SHA-256 `15f4d74927ea9d32432ef7ffc477279a4769c74c52cd67c5612851b920fd0e68`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected the whole saved page at native, 768 px and approximately 390 px widths and reread Page 06/source lines 113–145. Inspected actual new R09 pixels; compared previously inspected R01/R02/R04/R07 and preceding accepted page 005 at verified unchanged hashes. The existing complete script/coverage review remains applicable. Only this review file is written.
- **Text/speakers: PASS.** All five exact text units retain their wording and punctuation, including the semicolon, with readable lettering at 390 px. Phoebe's upper balloon and Adrian's final question have correct tails; the three yellow units remain narration. No extra words appear.
- **Action/state/identity: PASS.** Phoebe is curled on the floor with distressed unfocused eyes; Adrian gently catches her wrist, then visibly separates both hands from her in the final frame. Their limbs and contact remain coherent. The explicitly labeled subjective view distinguishes loose, unhooked gold empathy from native silver storm currents and the continuous foreign black twist at the bodily scar. The black endpoint leaves toward the off-frame focus, with no invented hand, physical leash, completed cut, or erased native faculty. Evelyn retains her braid/rust clothing, worn smoking left glove and bare flaming right hand; Adrian/Phoebe and the stormhart match their reference identities. N3 maintains damaged windows/threshold, extinguished candles, absent projected wards, physical ice, overturned table, glass and slush, with the threat to the right and the family sheltered toward the Hall side.
- **Inset/reading hierarchy: PASS; no containment correction required.** Three main frames plus the framed scar detail supply the four scripted panels. The inset begins clearly within the middle subjective frame and magnifies that frame's stormhart. Its small lower-edge overlap crosses the gutter/border area into background only, without obscuring any words, faces, or gestures. Its complete border and attached caption keep it grouped with the perceived scar and read before the distinct lower reaction frame; the overlap implies neither another time nor merged physical space. The hierarchy remains clear at 390 px.
- **Rendering and collateral check: PASS.** Crisp contours, hard graphic shadows, saturated controlled effects, yellow captions, white gutters and uppercase lettering remain consistent. The ordinary room remains legible beneath sparse subjective overlays. The entire saved page shows no blocking collateral change; prepared but ungenerated attempt 03 has not been reviewed or treated as an output.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 005 `33be47e8f265f20abfa3814fc17191cf466c5edda7e4838b3e2cf0b9320d210c`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- QA `exec-f9a05018-6e28-4ba2-9d60-2a2b0320c635-390.png` `c7c798e8f6f3d5b7cf7afec4dc90098b32379517ec3d9371b1a5fba109b5bd6b`; corresponding `-768.png` `42f12ced22a15a719e9444561645940ffa02a9922da2c52b2f0ae30f9fe09449`, in the previously recorded temporary QA directory.

This passes page 006 only for these bytes. Page 007 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.
## Page 007 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-007.png`, attempt 02, SHA-256 `57e0f31739704e180aef5c6e0bd9615d34db6d5a12775dec1312d8f807b842ee`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected the whole saved page at native, 768 px and approximately 390 px widths; reread approved Page 07 and source lines 129–155. Compared the preceding accepted page 006 and previously inspected actual R01/R02/R03/R05/R09 at verified unchanged hashes. The complete approved script/coverage remains applicable. Only `review.md` is written.
- **Text and reading: PASS.** All six text units match the exact script, including punctuation, and remain comfortably readable at 390 px. The two yellow units remain Adrian's narration; `STOP.` is not spoken or cast. Marcus, Rowena and Evelyn have unambiguous speech attribution. The broad perception frame leads into Marcus at middle-left, Rowena at middle-right, then Evelyn's lower revelation. Marcus's reply tail crosses the narrow middle gutter toward his adjacent panel without covering a face, hand or word; the upper Rowena reply and lower Marcus reply retain their clear order within the same exchange. This crossing causes no temporal or spatial confusion. No added text appears.
- **Action, anatomy and state: PASS.** The first panel alone shows intact subjective connections: Evelyn's red living core, Marcus's blue pressure behind his heart, and Rowena's pulse/silver channels toward stone. No severance or restored projected ward panes appears. Marcus's anatomical left sleeve remains iced while his bare right palm braces naturally against the pillar. Evelyn keeps her smoking worn left glove and lowers her burning bare right hand; the outside firebreak continues. Adrian listens without casting. Hands, arm ownership, seated contact and gazes are coherent; no premature flashback or extra named character appears.
- **Continuity and rendering: PASS.** Faces, age states, hair and costumes match the accepted references. Damaged Hall geography, extinguished candles, physical ice, glass/slush and overturned furniture continue N3 from page 006. Crisp black contours, graphic shadow shapes, saturated flat fills, white gutters, yellow captions and uppercase lettering maintain the accepted GN treatment. Subjective effects do not turn into physical ropes or broad photographic background blur. No blocking collateral drift is visible.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 006 `15f4d74927ea9d32432ef7ffc477279a4769c74c52cd67c5612851b920fd0e68`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `page-007-390.png` `783e719f1c1ec634a5bd014bea1ceeadfb50442644f813e984bbab47f081c846`; `page-007-768.png` `a61ad81fbf6e200d186505b3885936b9e7daf394538fcbffae702c18c43c6f94`, in the previously recorded temporary QA directory.

This passes page 007 only for these bytes. Page 008 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 008 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-008.png`, attempt 01, SHA-256 `f82066ceb6a7414b112213b06f646f5d20761265ca2e8428e12784f233dbe874`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and word at native, 768 px and approximately 390 px widths; reread approved Page 08 and source lines 157–169 with surrounding context. Compared accepted page 007 and previously inspected actual R01/R02/R04/R06/R09 at verified unchanged hashes. The existing full-script/coverage review remains applicable. Only this review file is written.
- **Text and transitions: PASS.** All five exact text units retain their wording and punctuation, with clear speaker tails and readable lettering at 390 px. Both yellow captions belong to Adrian's incomplete memory. The shallow childhood crop and white gap lead into two present testimony frames, left to right, then Phoebe's final response. The caption explicitly identifying Phoebe at six, her distinctly younger face, Garran's younger state, and the return to the damaged Hall make the temporal transition clear. `THEN MORNING. NOTHING BETWEEN.` does not introduce a pictured morning or recovered interval. No child Adrian, forgotten severance, added speech or extra scene appears.
- **Figures, action and state: PASS.** Younger, broader Garran grips the clothed child's wrist with coherent adult/child hand ownership; her tearful face and the caged fox's defensive distress remain non-graphic. Present Phoebe reads as sixteen, lifts her exhausted face toward Garran, and retains Adrian's cropped charcoal shoulder alongside. Evelyn's rust clothing, braid and scorched smoking left glove remain intact. Current Garran is leaner and graying, with the sole ordinary bracelet on his anatomical right wrist and his empty left hand raised defensively. Visible anatomy, clothing and gazes remain coherent across the opposed testimony.
- **Environment and rendering: PASS.** Present panels preserve N3 broken windows, ice, glass/slush, overturned furniture, dark candles and outside ashfire without restored ward panes or subjective gift overlays. Identities and Hall-side/threshold-side relationships continue accepted references and page 007. Crisp contours, flat saturated color, graphic shadows, white gutters, yellow narration and uppercase lettering maintain the edition style; no blocking photographic or painterly drift appears.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 007 `57e0f31739704e180aef5c6e0bd9615d34db6d5a12775dec1312d8f807b842ee`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R06 `e3d8e22d3b687e899d5eb79ebbe5876c456c5909c29078a65622bb17997494b0`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `exec-97e44cd8-1468-4674-a835-aaf465613d33-390.png` `ae56c5e015df1a33e22132c115e00e00d7dc8967bd0456881a9cdda43313ef5c`; corresponding `-768.png` `b1105fa5c1e54b7726edfdcaa53d57f8049ce840a2e68668aba5a3d0a4aa6ea8`, in the previously recorded temporary QA directory.

This passes page 008 only for these bytes. Page 009 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 009 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-009.png`, attempt 01, SHA-256 `79c4474188894932a52df2062d17bb9758ef8263d681de031949c96e048a7965`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and word at native, 768 px and approximately 390 px widths; reread approved Page 09 and source lines 171–179 with adjacent context. Compared preceding accepted page 008 and previously inspected actual R01/R02/R03/R06/R09 at verified unchanged hashes. The complete approved script/coverage remains applicable. Only `review.md` is written.
- **Text and reading: PASS.** All four speech units reproduce the exact approved text and punctuation, including `COMMAND-BOND` and Adrian's final contraction. Lettering remains readable at 390 px and each tail clearly identifies its speaker. Four downward panels move from Marcus's witness account to Evelyn's correction, Garran's accusation and Adrian's uncertain response. The larger gutter before Garran gives his grief space without implying a new time. No crossing, inset or added text obscures the reading path.
- **Action, anatomy and characterization: PASS.** Marcus supports himself with his anatomical right palm against the pillar while his left sleeve remains iced. Evelyn holds Adrian's gaze with her scorched smoking left glove still worn; her other hand is bare. Garran spreads two empty, anatomically coherent hands, retaining one ordinary dull bracelet on his right wrist with no emitted power. His strained face shows grief under anger; the preceding abuse testimony is neither contradicted nor absolved. Adrian is small against the ruined Hall, looking toward Garran without triumph. No childhood cut, recovered interval, literal command rope or returning faculty is shown.
- **Continuity and rendering: PASS.** Accepted identities, hair, ages and costumes remain stable. N3 continues broken windows/threshold, ice, glass/slush, overturned furniture, unlit candles and ashfire outside without restored projected wards. Opposed gazes and the Hall/threshold setting preserve scene geography. Crisp contours, graphic flat color and shadow shapes, white gutters and bold uppercase lettering follow the accepted GN style; no blocking collateral drift appears.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 008 `f82066ceb6a7414b112213b06f646f5d20761265ca2e8428e12784f233dbe874`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R06 `e3d8e22d3b687e899d5eb79ebbe5876c456c5909c29078a65622bb17997494b0`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `page-009-390.png` `ef9d8502981372cb1cadcd0e16915a57d18b7efa8bb3e1fbcd6712498edbb8dc`; `page-009-768.png` `8658216b2aa7208abfbf87ee04657fbf72a1fc09daf43b5c61be349daa159773`, in the previously recorded temporary QA directory.

This passes page 009 only for these bytes. Page 010 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 010 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-010.png`, attempt 02, SHA-256 `63cda19684168795b557684c584ab0f260dadf945048b3511a34ed9bce2b1405`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected the whole saved image at native, 768 px and approximately 390 px widths; reread approved Page 10 and source lines 181–191 with adjacent context. Compared preceding accepted page 009 and previously inspected actual R01/R02/R05/R09 at verified unchanged hashes. The existing complete script/coverage review remains applicable. Only this review file is written.
- **Text and reading: PASS.** All six exact blocks retain scripted words and punctuation and remain readable at 390 px. Panel 1 belongs to Rowena; panel 2's tail exits toward off-frame Rowena on the right, not Adrian. Both panel 3 balloons direct toward Rowena and read left to right. The last two tails correctly assign Adrian's question and Evelyn's admission. Four quieter frames flow downward without obscured faces, hands, inset confusion or added text.
- **Meaning and action: PASS.** The dialogue preserves local household belief and limits the memory loss to making the cut and the moments of that act; it expressly preserves childhood, knowledge and love. Nothing depicts a new severance, erased identity, recovered childhood interval or a physical connection being cut. Adrian's ordinary hands remain clearly separated from Rowena's open hand, with coherent fingers, arm ownership and visible air between them. Rowena's silver sleeve channels remain unlit cloth and metal. Evelyn's lowered ashamed gaze supports the admission; her scorched left glove stays worn and her right hand is bare.
- **Continuity and rendering: PASS.** Accepted faces, ages, hair and clothing remain stable. N3 holds broken windows, physical ice, glass/slush, overturned furniture and dark candles; exterior fire remains beyond the wrecked Hall. No restored ward panes or literal ropes appear. Gazes retain the conversation's geography and the final turn toward Evelyn. Crisp black contours, graphic flat fills and shadows, white gutters and bold uppercase lettering remain consistent with accepted GN references. No blocking collateral change appears in the edited page.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 009 / P09 `79c4474188894932a52df2062d17bb9758ef8263d681de031949c96e048a7965`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `exec-51904ec4-222e-471e-b15c-f64a4f96fbd9-390.png` `67c21442d4bb308850657dfd86a2620a6e8063a6db833dc1e678f163068f25c8`; corresponding `-768.png` `c5b9d97c0d9d38d1ad81e945a81a3e8e7aae07c026d06f8a6614828766b30c7a`, in the previously recorded temporary QA directory.

This passes page 010 only for these bytes. Page 011 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 011 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-011.png`, attempt 02, SHA-256 `eb2aaf73ce38549e52dcdee34c50eeac46fb64276bcc3a884d4bf11ad04c1e34`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and visible word at native, 768 px and approximately 390 px widths; reread approved Page 11 and source lines 191–207 with adjacent context. Compared preceding accepted page 010 and previously inspected actual R01/R02/R03/R05/R09 at verified unchanged hashes. The complete approved script/coverage remains applicable. Only `review.md` is written.
- **Text and sequence: PASS.** All six exact blocks preserve wording, punctuation and both em dashes. Dialogue and yellow narration remain readable at 390 px. Tails assign Evelyn's admission, Rowena's claim, Adrian's two challenges and Rowena's final answer correctly. Panel 2 reads Rowena first, then Adrian below; panel 3 reads the caption before Adrian's accusation. Four distinct present-time frames, white gutters and the final isolated close-up keep the exchange clear without inset or overlap confusion.
- **Source intent: PASS.** Evelyn explicitly places agreement after each cut began and places question, answer and completion inside the lost interval. The page invents neither testing equipment nor a testing flashback. Past avoidance remains Adrian's narrated realization over present figures. Rowena's strained final expression and unsparing `BOTH` retain fear for Adrian alongside fear of him; the framing does not resolve the admission into reassurance or exoneration.
- **Anatomy, states and continuity: PASS.** Marcus's corrected panel 3 torso has a clear centerline: his anatomical left sleeve is iced on the viewer's right, while his normal right hand supports that forearm. Hand/arm ownership is coherent and he does not touch Adrian. Evelyn's scorched left glove remains worn in panels 1 and 3, with her right hand bare; her withdrawn hand remains separated from Adrian. Rowena's silver channels are unlit. Faces, ages, hair and clothing hold. N3 retains broken windows, physical ice, glass/slush, dark candles and outside ashfire, without restored projected wards or literal magical ropes.
- **Rendering: PASS.** Crisp black contours, flat saturated fills, hard graphic shadows, white gutters, yellow narration and uppercase lettering follow the accepted edition style. The whole edited page shows no blocking collateral change.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 010 `63cda19684168795b557684c584ab0f260dadf945048b3511a34ed9bce2b1405`.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `exec-9ad1178e-5177-409a-ba05-1bcec77c9103-390.png` `a5bf038f136269e467e9f9f216b6c82bfc45a70dd446783e4ab07ff907389084`; corresponding `-768.png` `9e637fc3a83c20b8abda342cc7a605a85bca0ce4c16eca3108eec80e5ee58373`, in the previously recorded temporary QA directory.

This passes page 011 only for these bytes. Page 012 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 012 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-012.png`, attempt 02, SHA-256 `ed6c4461394ba1f9ce60fe21a2028bb4909cc9bddee4140dafe3acbbca363a0e`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and word at native, 768 px and approximately 390 px widths; reread approved Page 12 and source lines 209–223 with adjacent context. Compared accepted page 011, actual attempt 01 edit-target pixels, and previously inspected R01/R04/R05/R06/R07/R09 at verified unchanged hashes; reinspected R07 at native size. The full approved script/coverage remains applicable. Only `review.md` is written.
- **Text and reading: PASS.** The first panel remains silent. The following five exact text blocks retain words, punctuation and speaker/narrator roles, including all possessives. Lettering is readable at 390 px. Four downward frames clearly show renewed coercion, Garran's revenge invitation, Rowena's competing command, and Adrian's consideration; the wider last gutter separates perception from the intervening physical action. Tails point to Garran and Rowena; yellow blocks belong to Adrian. No clipped words or extra text appears.
- **Action, anatomy and state: PASS.** Garran's left fingers pull the sole dull focus on his right wrist without emitting a restored native gift. The stormhart's antlers meet substantial cracking ice; its translucent living hide, native silver storm, throat scar, scale and visible hoof anatomy retain R07. Phoebe's hand at her throat and distressed face show the linked pain without a wound or strangling object. Rowena places her body and outstretched arms between father and son without touching Adrian or casting. The later gazes direct Adrian toward Phoebe rather than either parent. Visible hands, arms and contact points remain coherent.
- **Subjective view: PASS.** Final-panel colored curves are thin, flat graphic overlays confined to Adrian's perceptual frame. They have no rope texture, cast shadow, knots, wrist attachments, gripping hand or weapon. Their uninterrupted paths remain distinct from physical ice/lightning and indicate available connection edges, with no cut, severed endpoint, extinguished power or depicted mass attack. Phoebe and the stormhart retain living faculties; the caption makes Adrian's deliberation explicit.
- **Continuity and style: PASS.** Present identities, ages and costumes hold. N3 damage now continues broken panes, overturned furniture, glass/slush, physical ice, extinguished candles and exterior ashfire; intact reference states do not repair the Hall. Crisp contours, flat saturated fills, hard shadow shapes, white gutters, yellow captions and uppercase lettering maintain the accepted GN rendering. The edit removes the earlier neon treatment and preserves all required beats without blocking collateral change.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 011 `eb2aaf73ce38549e52dcdee34c50eeac46fb64276bcc3a884d4bf11ad04c1e34`.
- Attempt 02's actual target: attempt 01 `6a2c4ed0ca57482ed9c38ba024edd7361f10656791ac1408d59267e6bb20fa60`, inspected as a superseded input, not passed. Its remaining actual inputs are R09/R07/R06/R01 below. Original generation also used R04/R05.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R06 `e3d8e22d3b687e899d5eb79ebbe5876c456c5909c29078a65622bb17997494b0`; R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `exec-b9336cd4-e797-47d1-9161-9dd9ee197eb8-390.png` `cedf28b01e7d2d46daeaa9fc92be0a4cf9e3cb1370ac5c6dd6221af0d279ef17`; corresponding `-768.png` `2effb98615c14a6c8e4f22370be552c4a59a4298ec7d5fa1c9152e22dfbed8d9`, in the previously recorded temporary QA directory.

This passes page 012 only for these bytes. Page 013 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 013 independent pixel review — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-013.png`, attempt 03, SHA-256 `9b55da79b208ff8197ac5553ae1bf5f7af5cdbedc5890b064af384d688c40a07`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and word at native, 768 px and approximately 390 px widths; reread approved Page 13 and source lines 225–239 with adjacent context. Compared preceding accepted page 012, reinspected accepted page 006's perception grammar, inspected actual attempt 02 target pixels, and compared previously inspected R01/R04/R07/R09 at verified unchanged hashes. Only `review.md` is written.
- **Text, meaning and reading: PASS.** All five exact spoken blocks retain words and punctuation, including `THAT'S ALL ITS.` All remain readable at 390 px with unambiguous tails. Four downward frames move from approach to consultation, Phoebe's account of the beast's own desires, and the narrow distinction between those desires and the foreign order. The last frame reads Adrian's question before Phoebe's answer. No added narration, flashback or competing reading path appears.
- **Bodies, contact and creature: PASS.** Adrian crawls through the debris, then lowers himself to Phoebe's eye level. Both of Phoebe's hands brace separately on the floor; no wrist grip or other controlling contact replaces the listening. Fingers, wrists, knees and weight-bearing poses remain coherent. Her loose hair and distressed expression support the wind/empathy beat. The visible stormhart keeps its living silver currents, old throat scar, branching antlers and hooved anatomy. The few upper antler tips cropped in panel 3 are normal framing here: its head, branching silhouette, native lightning, intact body and blocked threshold remain legible. No causal action or essential identity feature is hidden; no correction is required.
- **Subjective detail: PASS.** The final unbordered translucent scar echo is small and peripheral, with the Hall visible around and through it. Its dark scar edge and separate open gold cue are detached from human hair, skin and clothing. In the established page 006/page 012 grammar, this reads as perceived distinctions during the same conversation, not a giant physical throat, added time, physical leash or Phoebe commanding the animal. No connection is cut and no native gift disappears.
- **Continuity and rendering: PASS.** Current identities, ages, hair and costumes hold. N3 retains the ice-blocked damaged threshold, broken windows, glass/slush, overturned furniture, unlit candles and exterior fire. Crisp contours, flat saturated color, graphic shadows, white gutters and uppercase lettering maintain the accepted GN rendering. No blocking collateral change appears.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 012 / P12 `ed6c4461394ba1f9ce60fe21a2028bb4909cc9bddee4140dafe3acbbca363a0e`; perception context page 006 `15f4d74927ea9d32432ef7ffc477279a4769c74c52cd67c5612851b920fd0e68`.
- Actual attempt 03 target: attempt 02 `6ec331b67dae90046fcb624f3816460e6214098a45b652acb54b84c836f5a90e`, inspected as a superseded input, not passed. Attempt 03 also used R07/R09; earlier generation/editing supplied R01/R04/P12.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `exec-0f858b4d-a3c6-4ca3-a2ce-d1ecf84ae664-390.png` `83953088a9d771cbec03edcd490accea39881d107a03fd5978d7ba4757f78470`; corresponding `-768.png` `8e9e29c807426869d168cbf51d9a9becc3f1e3e4816f95581adf3559286ec342`, in the previously recorded temporary QA directory.

This passes page 013 only for these bytes. Page 014 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 014 independent pixel review — 2026-09-18

- **Verdict: REVISE.** Selected `pages/page-014.png`, attempt 03, SHA-256 `14f39d2d8b97b6df800693e4c4849f5765bf0868a5ab610b50441bf38ef727e1`, 1024 × 1536.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Inspected every panel and word at native, 768 px and approximately 390 px widths; reread approved Page 14 and source lines 241–259 with adjacent context. Compared accepted page 013, actual attempt 02 target pixels and previously inspected R01/R02/R03/R07/R09 at verified unchanged hashes. Only `review.md` is written.
- **Blocking R14.1 — panels 14.1, 14.2 and 14.4, exterior time-of-day continuity.** The clear bright blue sky, pale daylight clouds and brightly green tree crowns read as daytime at all three inspected sizes. This is still the uninterrupted night crisis, not the later morning. Extinguishing the white fire core should not introduce a daylight orchard. **Minimal fix:** change only the exterior sky and tree illumination to dark night values throughout these three views. Keep living foliage recognizable, retain the white magical fire core in 14.1 and ordinary low wet embers/smoke afterward, and preserve all text, figures, hand states, damage and ice-release actions. Avoid a sunrise/horizon glow. Recheck the whole corrected page for collateral drift.
- **Other gates: PASS.** All five exact text blocks, punctuation, roles and tails remain legible at 390 px; panel 14.2 is silent. Reading order is upper-left, upper-right, middle, bottom. Evelyn's left glove is worn before release, then her bare scorched left palm is displayed while her bare right hand holds the removed glove; no bandage appears. The magical white core disappears before the ice release. Marcus's left sleeve stays iced, his right arm normal; the gallery remains ice-blocked in 14.3, with no early retreat. In 14.4 Marcus alone lowers both palms while Adrian's hands rest at his sides. Guests retreat toward the opened inner gallery on the left; softened channels and slumped ice give the stormhart footing toward the right threshold without an explosive collapse. Its native storm and foreign command persist, with no Adrian cut or gift loss. Visible anatomy/contact, character identities and the creature's foreground scale/crop are coherent. Candles remain out; broken panes, debris, slush and overturned furniture persist. Crisp contours, flat color/shadow shapes, white gutters, yellow narration and uppercase lettering otherwise follow the accepted GN rendering.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 013 `9b55da79b208ff8197ac5553ae1bf5f7af5cdbedc5890b064af384d688c40a07`.
- Actual attempt 03 target: attempt 02 `38181d8111d9f6f49e71aa401542462862bdfb04a73911e61a42faaaf286b9b3`, inspected as a superseded input, not passed. Attempt 03 also used R01/R03/R09; earlier generation/editing supplied R02/R07.
- R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`.
- Temporary QA `exec-6ce67580-e0e4-4b5c-9a6b-66854657ff9f-390.png` `f86a24c7a5a5cb6ed2d9c1bc8d2dd33101072a607b70057c386c55d97eed56b8`; corresponding `-768.png` `4bd7aaa9d6ea4df1e4fd590441290c28af22701ee936fca19367c64889bab3cc`, in the previously recorded temporary QA directory.

Page 014 needs the stated repair and independent recheck. Page 015 onward and the assembled PDF remain NOT REVIEWED; no whole-book PASS or user approval is implied.

## Page 014 independent corrected-page recheck — 2026-09-18

- **Verdict: PASS.** Selected `pages/page-014.png`, attempt 04, SHA-256 `ded787a930cf3a148c9198351474c12d977c5f507d36fbb827624fc82cf8d867`, 1024 × 1536. The prior attempt 03 REVISE above remains preserved.
- Reviewer: `/root/mercy_plan_review`, independent `graphic_novel_reviewer`; not the producer. Independently inspected the entire corrected page at native, 768 px and approximately 390 px, including all words and all four panels. Compared the reviewed target, approved Page 14/source 241–259, accepted page 013 and previously inspected R10 night palette. Source, plan, style and predecessor hashes are unchanged. This is only a page recheck.
- **R14.1 resolved.** Exterior sky and tree crowns in 14.1, 14.2 and 14.4 now read consistently as night. Daylight clouds and bright daytime foliage are gone; living trees, damaged threshold, char and smoke remain. The white magical fire core remains in 14.1 and disappears into ordinary low embers before the later ice release. No premature dawn or intact-orchard restoration is introduced.
- **Whole-page collateral gates: PASS.** All five exact blocks, punctuation, tails and 390 px legibility remain intact; panel 14.2 stays silent. Upper-left/right, middle and bottom reading order is clear. Evelyn retains the left glove before release, then displays the bare scorched left palm while holding the removed glove in her right hand. Marcus's left sleeve remains iced, right arm normal. The gallery stays blocked in 14.3; only in 14.4 do guests retreat left as Marcus lowers both palms and ice softens in channels. Adrian's hands remain at his sides without casting. The living stormhart gains footing toward the right threshold, preserving its native storm and foreign command. Hands, anatomy, identities, costumes, scale, damage, unlit candles, glass/slush and overturned furniture remain coherent. Crisp contours, flat fills, hard shadows, white gutters and uppercase lettering retain the established style. No new blocking change appears.

SHA-256 bindings:

- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Preceding page 013 `9b55da79b208ff8197ac5553ae1bf5f7af5cdbedc5890b064af384d688c40a07`.
- Actual attempt 04 inputs: reviewed attempt 03 target `14f39d2d8b97b6df800693e4c4849f5765bf0868a5ab610b50441bf38ef727e1`; R10 `c56eca8acdf1097a15e396d48b57f4f93d16964ecdd83bc4bf72ad5ef3eda272`, night palette only. Earlier identity/state inputs retain the versions bound in the preceding Page 014 review.
- Temporary QA `exec-a3006ef5-c533-4222-9fe9-04acd4b33caf-390.png` `1ebad40c23858348c3c01e35e3e31ca296f605a9efd56e2d26f72f59369c026e`; corresponding `-768.png` `6c446ddf4938b11293782e57a0ec9a99cce3cd3f40d4e7a95e0f81bc894f96c0`, in the previously recorded temporary QA directory.

This passes page 014 only for the corrected bytes. Page 015 onward and the assembled PDF remain NOT REVIEWED; this is not whole-book PASS or user approval.

## Page 015 independent pixel review — 2026-09-18

**PASS**, attempt 01. Reviewer `/root/mercy_plan_review` independently inspected the complete saved page at native, 768 px and 390 px against approved Page 15/source 261–281, accepted predecessor and actual references, including new R12 pixels.

All six exact text blocks and tails pass; the compact yellow question remains readable at 390 px. Four main frames and the simultaneous ledger inset have a clear reading path. Shoulder contact ends without an actual burn or retaliation. Correct identities, anatomy and injury laterality hold; Marcus's normal right hand retrieves one blank leaf, with no writing or enchantment yet. N4 night, receded ice/open routes, wet embers, damage and dark candles continue correctly. Ordinary ledger/pen/ink and crisp flat GN rendering match the accepted inputs. The inkpot beside the ledger, rather than beneath a chair, is a nonblocking placement compression; the ordinary-record cause remains clear. No material blocker found.

SHA-256 bindings:

- Candidate `dcf82963f573051da71d94972bf0d6d9a9e1a536eaf178508df6d369188715dd`; predecessor 014 `ded787a930cf3a148c9198351474c12d977c5f507d36fbb827624fc82cf8d867`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Actual inputs: R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`; R12 `0eb22591c5a99096068f9c2ae3dc64e385d18385b98a2444cdc1b5a81c8f35df`.
- QA `exec-0fe68db3-8f72-4486-b81a-a3f45e8af05c-390.png` `a4cc317ce03d4f7f8e573d23bebb9b21203138a507d90d275dea51e7d24092e0`; corresponding `-768.png` `9268888b5a602ee7af37748454b37e7a7689c43a915fb348221d4da1bbb3020e` in the previously recorded temporary QA directory.

Page-only PASS; page 016 onward/PDF NOT REVIEWED. No user approval implied.

## Page 016 independent pixel review — 2026-09-18

**PASS**, attempt 04. Reviewer `/root/mercy_plan_review` independently inspected the complete saved page at native, 768 px and 390 px against approved Page 16/source 283–295, predecessor, actual edit target and accepted references.

All three verbatim consent clauses, punctuation, signature `ADRIAN BELLWEATHER` and three witness balloons are correct and readable. The five-frame sequence completes Marcus's writing before Adrian signs, entirely before any active cut. Marcus uses his normal right hand; his left sleeve stays iced in all three writing frames. Evelyn's bare burned left hand steadies the leaf; Phoebe's hand rests alongside, without restraining the signer. Adrian's right signing hand, charcoal sleeve, nib beyond the final letter and tiny paper tear remain coherent; the name holds. Marcus's visible right sleeve is plain in the witness frame. Tails clearly assign Marcus, Evelyn/Phoebe together, then Rowena alone. Ordinary paper/ink, N4 night, unlit background, identities, anatomy and crisp flat GN style hold. No material blocker or collateral frost transfer remains.

SHA-256 bindings:

- Candidate `7c0b904a1c7104887571401f17a47e713280eae54ebbcc1cc522f5595f8e42fc`; predecessor 015 `dcf82963f573051da71d94972bf0d6d9a9e1a536eaf178508df6d369188715dd`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `67851ddacecb4333f03f49730225dcbb97465d3dae8c3cfd2082782ab2b7f55f`.
- Actual attempt 04 target `9219da8c150125196b33c7d39ae6afb431c549b9684af298316450f5836741c0` plus R03 below. Inherited character inputs: R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R02 `cea16d4e00e5411d6a8715ae2d1a98b5dc85a7f609b073a6c13ff4451558f6e5`; R03 `a73f3d92bcbef8224c8cac49f96dd9c7d4323675a87cea78a003b46adadfe38f`; R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`.
- QA `exec-8475a838-d4dd-477c-89fe-87b73602990e-390.png` `df6e1a27c2a3720efb793820a5b1a2f167a3f26929cc02f6b10c5171676d1bff`; corresponding `-768.png` `b2607140571c71e32aeebce1ef7e646700b3cee1d84bea8d8acbdb15b159cdd4` in the previously recorded temporary QA directory.

Page-only PASS; page 017 onward/PDF NOT REVIEWED. No user approval implied.

## Page 017 independent pixel review — 2026-09-18

**PASS**, attempt 04. Reviewer `/root/mercy_plan_review` independently inspected the complete saved page at native, 768 px and 390 px against approved Page 17/source 297–313, predecessor, actual edit target and accepted reference pixels.

All seven exact text blocks, punctuation, tails and reading order pass at reading size. Rowena's physical right-wrist pin is clear in panels 1 and 4. In panel 2, Garran's right forearm and dull bracelet remain traceable to his body; Rowena's silver sleeve continues behind it, with the gripping hand occluded. That crop preserves restraint continuity and introduces neither an extra Adrian arm nor a release. Bodies, hands, faces and costumes remain coherent. The exchange acknowledges irreversible harm and real grief while retaining Phoebe's abuse and the stormhart's pain; no restoration, further cut, spell or paper loss is depicted. N4/N5 night, slush, open routes, ordinary outside embers and dark candles hold. Graphic contours, flat color/shadows, gutters and uppercase lettering remain consistent. No material blocker found.

SHA-256 bindings:

- Candidate `f579e121ffa78885b0063372ef5fce3aef84b52d0f33b9c87cb9641a5b82cc8d`; predecessor 016/P16 `7c0b904a1c7104887571401f17a47e713280eae54ebbcc1cc522f5595f8e42fc`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; current STYLE.md `89d67a557063f89772ee6ef0d66adaa1ba1f7dedc803b1b48ecb94d267568464`; contract v0.7 `1997210900c9f6bb1f01969dad24d48c67f2c33b999ad704550c01d16474370f`.
- Actual attempt 04 target `4713bfa016030996c5f6536434bf22dd8a733326e52c1c69cd934392b83e5101`, plus R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`, R06 `e3d8e22d3b687e899d5eb79ebbe5876c456c5909c29078a65622bb17997494b0`, R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`. Inherited environment R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323` and P16 above.
- QA `exec-d146603c-d19d-448d-8813-b2beb17e6263-390.png` `061943498969cfb21f67862af0765542d802d88c86735516086e08dfdc93da5a`; corresponding `-768.png` `2825ef23668398db295d0f7c9720166ad7c7a29366a6e15d8c02ff37c06ac7a7` in the previously recorded temporary QA directory.

Delivery-only update acknowledged: no HTML previews; generate the PDF exactly once after all image work/reviews/order checks. It does not invalidate unaffected earlier art. Page-only PASS; page 018 onward/PDF NOT REVIEWED. No user approval implied.

## Page 018 independent pixel review — 2026-09-18

**PASS**, attempt 02. Reviewer `/root/mercy_plan_review` inspected the complete saved page at native, 768 px and 390 px against approved Page 18/source 315–329, predecessor, actual target and accepted reference pixels.

All three exact text units, punctuation, speaker/narrator roles and reading order pass. Adrian's empty hands remain separate from the throat and muzzle; Phoebe's light nostril bleed and voluntary presence do not become a restraint. The advancing beast retains coherent hoof contact, intrinsic silver lightning and the old narrow throat scar. The perceived dark command edge is subtle at 390 px but traceable along the scar; the identifying caption and established perception context preserve its distinction from the silver storm and detached gold marks. No material rope, collar, new wound, severed endpoint or early gift loss appears. The final profile remains poised before the active cut, with the open white space beneath it preserving the intended memory boundary. Night, melted ice/open footing, dark candles, ruined Hall, identities and GN rendering hold. No material blocker found.

SHA-256 bindings:

- Candidate `e100e9f56222c5c52ab6c3094dc8027c2ee49ffeb5db90bb32973fb0b5426c6d`; predecessor 017/P17 `f579e121ffa78885b0063372ef5fce3aef84b52d0f33b9c87cb9641a5b82cc8d`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `89d67a557063f89772ee6ef0d66adaa1ba1f7dedc803b1b48ecb94d267568464`; contract v0.7 `1997210900c9f6bb1f01969dad24d48c67f2c33b999ad704550c01d16474370f`.
- Actual attempt 02 target `7f71b063963ffdff1eb92d0baad97a8ae6b2217f7f44809d31c398fc681e89db` plus R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`. Inherited R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`, R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`, R09 `3a45d2b8f7e383ecf38d33e8145a0d38e2cd36bf2a83d54aac45a002a74ca323`, and P17 above.
- QA `exec-d043ddf7-4222-42dc-9a48-a8d582a2060e-390.png` `a52a8428abd56d5ebbf25b2e067805b95d58daff2b9f07814d517090e5ba2a46`; corresponding `-768.png` `6cd41b8b373c1f4a4a08ed5639fa55e4d4a65b85d61f3a3ddc547d4cc50d08b2` in the previously recorded temporary QA directory.

Page-only PASS; page 019 onward/PDF NOT REVIEWED. No user approval implied.

## Page 019 independent pixel review — 2026-09-18

**PASS**, attempt 01. Reviewer `/root/mercy_plan_review` inspected the complete saved page at native, 768 px and 390 px against approved Page 19/source 333–349, predecessor and actual R01/R04/R05/R11/R12 pixels.

All seven exact text units, punctuation, tails and four-panel reading order pass. The direct morning transition preserves remembered consent and the absent act; no recovered-cut imagery appears. Phoebe's account retains the beast's lightning and voluntary departure. Rowena reports confinement and the intact evidentiary bracelet, carrying one ordinary buckled leaf with no readable added wording or magic. Morning identities, Adrian's white shirt, Phoebe's tired smile/green tunic, Rowena's gray hair/unlit silver sleeves, hand contacts and bed-left/window-right geometry hold. Daylight, crisp contours, flat shadow shapes, white gutters and uppercase lettering match R11 and the edition. No material finding.

SHA-256 bindings:

- Candidate `b369f2e6965d35fdc84779cb4170a45269a9eef7e21b7759bc98d20357ba789e`; predecessor 018 `e100e9f56222c5c52ab6c3094dc8027c2ee49ffeb5db90bb32973fb0b5426c6d`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `89d67a557063f89772ee6ef0d66adaa1ba1f7dedc803b1b48ecb94d267568464`; contract v0.7 `1997210900c9f6bb1f01969dad24d48c67f2c33b999ad704550c01d16474370f`.
- Actual inputs: R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R11 `f5f2cd5b204e7c4b800c4906a06b0a2c227e87403887512da918848fcd17c998`; R12 `0eb22591c5a99096068f9c2ae3dc64e385d18385b98a2444cdc1b5a81c8f35df`.
- QA `exec-ad83d396-777e-41d8-997d-aaae9f4f2cbb-390.png` `5a3cc52b1bad9dc6cc6ac6be0ff3d9103aab0720ce2a49ef9e1e437c8a360444`; corresponding `-768.png` `0bb799ccc0737b7ca80ad4f73fb0b73678455c3ce01867dad70a5f5095799c40` in the previously recorded temporary QA directory.

Page-only PASS; page 020 onward/PDF NOT REVIEWED. No user approval implied.

## Page 020 independent pixel review — 2026-09-19

**PASS**, attempt 02. Reviewer `/root/mercy_plan_review` inspected the complete saved page at native, 768 px and 390 px against approved Page 20/source 345 and 351–355, predecessor, actual target and accepted anchors.

All three exact captions and punctuation are readable. Double black frames and explicit testimony in every panel clearly distinguish this night reconstruction from Adrian's memory. The sequence preserves the native bolt and unchanged scar, Adrian's safe limp collapse before escape, Phoebe's unforced guidance through melting ice, then the beast breaking the remaining wall and running free. No active cut is reconstructed. Damp char replaces upright flames; surviving trees do not restore the burned crescent. Night geography, pond/Hall/wall relationships, bodies/hooves, costumes and crisp GN rendering hold. No material blocker found.

SHA-256 bindings:

- Candidate `70a920c8f2029f7919fe55ab48c4abd65a73a6ebfefad175372f6defff14f0bf`; predecessor 019/P19 `b369f2e6965d35fdc84779cb4170a45269a9eef7e21b7759bc98d20357ba789e`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `89d67a557063f89772ee6ef0d66adaa1ba1f7dedc803b1b48ecb94d267568464`; contract v0.7 `1997210900c9f6bb1f01969dad24d48c67f2c33b999ad704550c01d16474370f`.
- Actual edit target `ab43fa2391ac9228d43b6a35a049784141f347e7d80017a46c348df9fa5492a1`. Inherited R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`, R04 `c7c76269c5a22f6c51d687132773e42ca0865e79548e102f3a468ecfbc12c251`, R07 `7240fcd4f5eff3d092be7e78eddb7b3ba542573695d29c366ed7289897b3d1f6`, R10 `c56eca8acdf1097a15e396d48b57f4f93d16964ecdd83bc4bf72ad5ef3eda272`, and P19 above.
- QA `exec-165cae80-8c8d-4d25-a5d7-fe29fd5df654-390.png` `3bdcfca9be9c71a25918dd63312cb631863dc71b96a424e1b59b70f6d354c79f`; corresponding `-768.png` `0d368ea49a0ad3fd3eeb939ca283d5766d8b2b04fe1e1f244e8d21323964ba93` in the previously recorded temporary QA directory.

Page-only PASS; page 021 onward/PDF NOT REVIEWED. No user approval implied.

## Page 021 independent pixel review — 2026-09-19

**PASS**, attempt 01. Reviewer `/root/mercy_plan_review` inspected the complete saved page at native, 768 px and 390 px against approved Page 21/source 357–371, preceding page 020 and actual morning/reference anchors.

All five exact dialogue/narration units, punctuation, tails and the five names read correctly, including at 390 px: ADRIAN BELLWEATHER, MARCUS, EVELYN, PHOEBE, ROWENA. The upper consent and lower account remain nonspecific ink strokes. Four ordinary single-framed panels clearly return to morning. The one buckled leaf passes between coherent hands; Adrian's two linked balloons preserve love and the refusal to call concealment honest. Rereading brings evidence without recovered memory or magic. Identities, morning clothes, bed/window geometry, warm light and graphic rendering hold. No material blocker; the prepared uncalled attempt 02 is not reviewed.

SHA-256 bindings:

- Candidate `ba947f227ddfd62fe7bf187acf47beb59df12773cd1284f41710671002036248`; predecessor 020 `70a920c8f2029f7919fe55ab48c4abd65a73a6ebfefad175372f6defff14f0bf`; morning P19 `b369f2e6965d35fdc84779cb4170a45269a9eef7e21b7759bc98d20357ba789e`.
- Plan `6d0de63c02ab634b149d267059d813fbda3c6304e6a08c0c839a1c61acaa9da2`; source `609f99af062dc6145cd12913114ed39bc0bdfa24bcbb674a10cad5ee69bea11a`; STYLE.md `89d67a557063f89772ee6ef0d66adaa1ba1f7dedc803b1b48ecb94d267568464`; contract v0.7 `1997210900c9f6bb1f01969dad24d48c67f2c33b999ad704550c01d16474370f`.
- Actual inputs: R01 `8707300daf02f64eb1707d4ac7ac82ccd497842511e2565cfb792a52204079d3`; R05 `89090d2e04f6ef9663b7ad92e23fb25122b5c8deaf4e9a75719c6c42e88c1e8f`; R11 `f5f2cd5b204e7c4b800c4906a06b0a2c227e87403887512da918848fcd17c998`; R12 `0eb22591c5a99096068f9c2ae3dc64e385d18385b98a2444cdc1b5a81c8f35df`; P19 above.
- QA `exec-94f3e07b-b070-4ecf-aaee-8daae74a39e1-390.png` `5681390139146851da51e285cdfd085a2c0ca8b8ba5a9d715498ca578e44d138`; corresponding `-768.png` `1e1ae9672e7ebde7bb144f363763a366c63611c8a9da762d393408f9569bf2c1` in the previously recorded temporary QA directory.

Page-only PASS; page 022 onward/PDF NOT REVIEWED. No user approval implied.
