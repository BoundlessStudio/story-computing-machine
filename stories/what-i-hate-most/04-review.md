# Continuity and story review

## Current certification

- Reviewed artifact: `stories/what-i-hate-most/05-story.md`
- Review pass: 3
- Verdict: REVISE
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 1
- Updated: 2026-08-03T14:31:16.9517334Z

This summary must match the newest completed payload. A completed story requires a passing draft review followed by a later passing review of `05-story.md`.

## Review passes

### Pass 1 — draft review

REVIEW_PASS_PAYLOAD
{
  "story": "what-i-hate-most",
  "mode": "REVIEW_DRAFT",
  "status": "READY",
  "pass": 1,
  "reviewedArtifact": "stories/what-i-hate-most/03-draft.md",
  "authorityManifest": "stories/what-i-hate-most/authority.json",
  "handoffLedger": "stories/what-i-hate-most/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T14:00:00.7256033Z",
  "reviewBasis": "Independent read-only complete-draft review under guard 4f54c081c48643259503ba11a0c67615 against the captured prompt, in-progress lifecycle record, canon brief, scene-ready plan, pending pass-1 review scaffold, authority inventory captured at base commit 11a9362c21a65c76478b083177d6b39d7b13154d, ordered handoff ledger through completed sequence 3, and current complete character-name registry. Verified that the captured universe files and admitted canon-story artifacts remain unchanged; the only INDEX change adds this in-progress story. Rechecked current LOCKED/CANON authority governing the one physical world, living magical agency, bounded costs, divinity, consent, personhood, content limits, and cited sovereign, dragon-alliance, command-bond, and courtesy-bout precedents. Compared the draft in full against the closest structural precedent, The Courtesy of Blades, and against the authoritative distinctions for Solstice Evening Bell, the Sleepless Majesty, Ersene, Kharost, and Garran's command-bonds. Audited exact prompt fulfillment, adult status, fighting/flirting ambiguity, the concrete sharing conflict, consent and separate political/romantic choices, close-third past-tense control, chronology, scene causality, physical staging, local magic access/cost/limit/failure/withdrawal rules, non-agentic infrastructure, dialogue profiles and competing aims, pacing, prose readiness, name use, originality, and non-explicit/non-graphic boundaries. No prior completed finding disposition or final delta applies to REVIEW_DRAFT.",
  "verdict": "REVISE",
  "blockType": null,
  "resolutionOwner": "prose_writer",
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 2,
    "Minor": 1
  },
  "priorFindingDispositions": [],
  "findings": [
    {
      "id": "WHM-DRAFT-001",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "local magic cost and duration consistency",
      "locations": [
        "stories/what-i-hate-most/02-story-plan.md:44-45",
        "stories/what-i-hate-most/03-draft.md:17",
        "stories/what-i-hate-most/03-draft.md:91-109",
        "stories/what-i-hate-most/03-draft.md:145-195",
        "stories/what-i-hate-most/03-draft.md:281"
      ],
      "evidence": "The controlling plan limits Ombria's fifth plane to an emergency reach she cannot safely hold for more than a few breaths. The draft opens with five active planes, confirms during the contest that two planes constrain Draxenne while three other districts remain intact through at least breath twenty, continues to describe all five after the thirty-breath contest and eleven-breath channel attempt, and explicitly carries five planes down to the bridge. Line 281 then reiterates that a fifth plane might stop Ombria's heart. This sustained use materially exceeds the established ceiling while preserving only progressive cold, weakening the credibility of the cost system and the later danger of offering a fifth plane.",
      "requiredResolution": "Make the complete plane-count sequence obey the planned cost ceiling. Keep Ombria at a sustainable but costly count through ordinary ward work, show any fifth plane being raised only for a genuinely brief emergency interval and released or replaced within a few breaths, and preserve the civilian pulse that costs her the contest, the transition to three collaborative baffles, her living agency, and the later lethal-risk meaning of a fifth plane. Ensure every active district and contest plane can be accounted for without exceeding five or silently extending the fifth-plane limit.",
      "owner": "prose_writer"
    },
    {
      "id": "WHM-DRAFT-002",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "contest adjudication and causal continuity",
      "locations": [
        "stories/what-i-hate-most/02-story-plan.md:19",
        "stories/what-i-hate-most/03-draft.md:43-53",
        "stories/what-i-hate-most/03-draft.md:73",
        "stories/what-i-hate-most/03-draft.md:121-141"
      ],
      "evidence": "The agreed contest rule says spoken yield, spoken withdrawal, or loss of housing contact ends a claim. Line 73 explicitly keeps Ombria's hand in contact. At the deciding feint, Draxenne closes both hands around the rim, but the prose never shows Ombria releasing or losing her own contact before breath thirty; it moves directly to declaring that Draxenne holds the Ninth and Ombria accepts her command. Because command of the conduit and the failed winning plan drive the next reversal, the missing adjudicating action leaves the tactical victory asserted rather than physically earned under the story's own rule.",
      "requiredResolution": "Show the exact safe physical action by which Ombria's choice to answer the eastern roofs makes her release or lose housing contact before breath thirty, or otherwise establish an equally explicit outcome permitted by the already-agreed rules. Preserve Ombria's voluntary civic choice, Draxenne's clean feint, the prohibition on bodily strikes, Draxenne's immediate venting instead of exploitation, and the rule that victory grants only temporary conduit command.",
      "owner": "prose_writer"
    },
    {
      "id": "WHM-DRAFT-003",
      "severity": "Minor",
      "status": "UNRESOLVED",
      "category": "physical object inventory",
      "locations": [
        "stories/what-i-hate-most/03-draft.md:13",
        "stories/what-i-hate-most/03-draft.md:29",
        "stories/what-i-hate-most/03-draft.md:57-59",
        "stories/what-i-hate-most/03-draft.md:121",
        "stories/what-i-hate-most/03-draft.md:277-289"
      ],
      "evidence": "Draxenne brings twelve prepared plates and installs at least one on the conduit housing for repeated use during the contest. The climax later presents all twelve as stacked on the bridge and melts every one, without showing the installed plate being recovered and moved or reducing the remaining count. The intended sacrifice of her entire defensive stock is clear, but the object count momentarily breaks physical continuity.",
      "requiredResolution": "Reconcile the plate inventory by showing the housing plate recovered and added to the bridge stack, or by correcting the later remaining count and the quantity melted. Preserve the established total stock, its earlier venting function, the loss of the March's fitted defenses, and the causal necessity of bracing the final outlet.",
      "owner": "prose_writer"
    }
  ],
  "certificationEligible": false,
  "changeReport": "Initial draft review requires production revision for two Major mechanism/causality findings and one Minor object-continuity finding; no user ruling or canon change is needed. The complete approximately 3,627-word draft otherwise fulfills the prompt strongly: Draxenne and Ombria are unambiguously adult, powerful, distinct rivals; the required exchange lands naturally during a dangerous mutually bounded contest; sharing means Ombria's divided civic attention and labor; both women retain independent political duties, vetoes, withdrawal rights, and bodily agency; and political cooperation, courtship, and the kiss are requested and accepted separately. Close-third past tense remains controlled through Draxenne, the dialogue profiles and incompatible aims are distinct, banter yields to clipped operational speech under pressure, the plot resolves beyond flirtation, and the ending converts possessiveness into chosen time and shared labor. The story remains non-explicit and non-graphic, uses only the registered forms Queen Draxenne, Draxenne, Night-Sovereign Ombria, and Ombria, reproduces no song lyric, creates no autonomous object magic or universal consent fuel, and is materially distinct from the cited courtesy bout, Solstice battle, shared-sovereign identities, Ersene renewal, hidden dragon monarchy, and command-bond precedent. Certification eligibility remains false for this draft review, and no repository files were changed."
}
END_REVIEW_PASS_PAYLOAD

### Pass 2 — draft re-review

REVIEW_PASS_PAYLOAD
{
  "story": "what-i-hate-most",
  "mode": "REVIEW_DRAFT",
  "status": "READY",
  "pass": 2,
  "reviewedArtifact": "stories/what-i-hate-most/03-draft.md",
  "authorityManifest": "stories/what-i-hate-most/authority.json",
  "handoffLedger": "stories/what-i-hate-most/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T14:09:13.0774378Z",
  "reviewBasis": "Independent read-only complete draft re-review under guard 31a0a3fcc0f34370b26ab79502940baa against the current captured prompt, in-progress lifecycle record, canon brief, scene-ready plan, revised 3,787-word draft, review history through pass 1, authority inventory captured at base commit 11a9362c21a65c76478b083177d6b39d7b13154d, ordered handoff ledger through completed sequence 5, and current complete character-name registry. Verified each prior finding against the revised prose and checkpoint change set, then audited the complete draft for regression in prompt fulfillment, chronology, causality, physical staging, local magic counts, costs, limits, failure and withdrawal behavior, living agency, non-agentic infrastructure, contest boundaries, consent and personhood, close-third past-tense control, dialogue distinction and competing aims, pacing, prose readiness, name use, originality, and content limits. The captured universe files and all admitted canon-story artifacts remain unchanged. Rechecked the draft against current LOCKED/CANON authority and the cited distinctions from The Courtesy of Blades, Solstice Evening Bell, the Sleepless Majesty, Ersene, Kharost, and Garran's command-bonds. No final delta applies to REVIEW_DRAFT.",
  "verdict": "PASS",
  "blockType": null,
  "resolutionOwner": null,
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 0,
    "Minor": 0
  },
  "priorFindingDispositions": [
    {
      "id": "WHM-DRAFT-001",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "The revised draft now establishes four active planes at stories/what-i-hate-most/03-draft.md:17, accounts for two contesting and two district planes at lines 73 and 109, and retains an explicit four-plane total at lines 147 and 195. Lines 203-241 identify the fifth as a maximum-three-breath emergency reach, raise it only to catch the lower-eastern load, release it on the second breath, show the immediate additional cold, and settle Ombria at three collaborative baffles by lines 247-249. The complete sequence now obeys the planned ceiling while preserving the civilian pulse, contest loss, costs, withdrawal, and later lethal-risk meaning."
    },
    {
      "id": "WHM-DRAFT-002",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/what-i-hate-most/03-draft.md:123-135, Ombria deliberately tears her housing hand free to answer the eastern roofs; the prose explicitly states that her claim ends when her palm leaves iron, then shows her release the western contesting plane, raise district protection, and leave Draxenne holding the rim before breath thirty. The tactical result now follows the agreed contact rule without a bodily strike or romantic entitlement."
    },
    {
      "id": "WHM-DRAFT-003",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/what-i-hate-most/03-draft.md:183, Draxenne removes and carries the cooled housing plate. Line 195 places that recovered plate atop the eleven waiting on the bridge, restoring the twelve-plate inventory later identified at line 281 and exhausted through the last plate at line 293. The venting use, recovery, total stock, and climactic sacrifice now form one continuous object chain."
    }
  ],
  "findings": [],
  "certificationEligible": false,
  "changeReport": "Draft re-review passed with all three pass-1 findings resolved and no material regression or new finding. The 3,787-word story remains within target length and fulfills the prompt through two unambiguously adult, dangerously competent magical rivals; the exact fighting/flirting exchange; a consequential conflict over Ombria's divided civic attention; and decisive political, tactical, and romantic resolutions. Plane counts, costs, transfer timing, contest adjudication, plate inventory, spatial action, and withdrawal behavior are now explicit and internally consistent. The prose sustains close-third past tense through Draxenne, preserves distinct dialogue profiles and tactic changes, grounds dark-queen glamour in labor and bodily cost, and ends on shared public burden plus freely chosen touch. Contest victory grants only temporary conduit command; the renewable civic compact, courtship, and kiss remain separate and revocable choices. The story introduces no autonomous object magic, universal consent fuel, objective godhood claim, crossover, copied song lyric, name collision, explicit sexual content, or graphic violence, and it remains materially distinct from the cited precedents. The draft is ready for final editing; release certification remains ineligible at the draft-review stage, and no repository files were changed."
}
END_REVIEW_PASS_PAYLOAD

### Pass 3 — final review

REVIEW_PASS_PAYLOAD
{
  "story": "what-i-hate-most",
  "mode": "REVIEW_FINAL",
  "status": "READY",
  "pass": 3,
  "reviewedArtifact": "stories/what-i-hate-most/05-story.md",
  "authorityManifest": "stories/what-i-hate-most/authority.json",
  "handoffLedger": "stories/what-i-hate-most/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T14:31:16.9517334Z",
  "reviewBasis": "Independent read-only final review under guard c4b217af9a014e299586fc23df76ad5c against the captured prompt, in-progress lifecycle record, canon brief, scene-ready plan, passing revised draft, complete review history through pass 2, final prose, 26-item proposed canon delta, authority inventory captured at base commit 11a9362c21a65c76478b083177d6b39d7b13154d, ordered handoff ledger through completed sequence 7, and current complete character-name registry. Verified that the captured universe files and all admitted canon-story artifacts remain unchanged from the authority base. Compared final prose with the passing draft and found only frontmatter normalization plus two immaterial sentence-level refinements; all prior continuity repairs remain intact. Audited prompt fulfillment, chronology, causality, physical staging, local magic access, costs, limits, failures and withdrawal, living agency, non-agentic infrastructure, dialogue distinction, consent, personhood, originality, prose readiness, content limits, immutable frontmatter, complete character-facing inventory, reviewed non-character allowlist, every concrete delta item, local qualifiers, provenance, targets, dependencies, conflicts, registry updates, and promotion recommendations. The strict final name check passed without warnings or errors.",
  "verdict": "REVISE",
  "blockType": null,
  "resolutionOwner": "story_editor",
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 1,
    "Minor": 0
  },
  "priorFindingDispositions": [
    {
      "id": "WHM-DRAFT-001",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "The final prose preserves the corrected capacity sequence: four active planes at stories/what-i-hate-most/05-story.md:17, four throughout the contest and initial defense at lines 73, 109, 147, and 195, a fifth plane raised only for the two-breath emergency transfer at lines 203-241, and three collaborative baffles thereafter at lines 247-249. Delta items WHM-10 and WHM-23 accurately preserve that corrected sequence."
    },
    {
      "id": "WHM-DRAFT-002",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/what-i-hate-most/05-story.md:123-137, Ombria deliberately removes her housing hand to answer the eastern roofs, the prose explicitly applies the agreed contact rule, and Draxenne holds the housing through breath thirty before extinguishing her flame. Delta item WHM-21 accurately records the adjudication."
    },
    {
      "id": "WHM-DRAFT-003",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/what-i-hate-most/05-story.md:183 and 195, Draxenne recovers the housing plate and places it atop the eleven waiting plates; lines 281-293 then account for and exhaust all twelve. Delta items WHM-18 and WHM-23 preserve the continuous inventory."
    }
  ],
  "findings": [
    {
      "id": "WHM-FINAL-001",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "canon-delta evidence and dependency integrity",
      "locations": [
        "stories/what-i-hate-most/06-canon-delta.md:128-140",
        "stories/what-i-hate-most/06-canon-delta.md:145-155",
        "stories/what-i-hate-most/06-canon-delta.md:171-180",
        "stories/what-i-hate-most/06-canon-delta.md:182-204",
        "stories/what-i-hate-most/05-story.md:21-53",
        "stories/what-i-hate-most/05-story.md:57-79",
        "stories/what-i-hate-most/05-story.md:145-175",
        "stories/what-i-hate-most/05-story.md:209-317"
      ],
      "evidence": "The proposed delta exceeds or misaddresses its final-prose evidence in several material places. WHM-08 states that Draxenne and Ombria negotiate the contest because simultaneous opposed casting could destroy the junction, but the final prose moves from their conflicting defense plans directly to Draxenne's proposal and never establishes that causal belief; the later street-burst danger belongs to Draxenne's failed exclusive channel plan. WHM-13 imports the plan's thirst and collapse-risk language even though the final story demonstrates body-water and oxygen consumption, cracked fingertips, visual halos, tremor, and severe post-crisis exhaustion without establishing thirst or a defined collapse risk. Three dependency references are also concretely wrong: WHM-09 locates ward anchors under WHM-17, which defines stormglass rather than the apparatus; WHM-11 locates coordinated withdrawal under WHM-20, which defines the breach and evacuation rather than the withdrawal procedure; and WHM-12 assigns mineral material to WHM-19, which defines joint withdrawal rather than stormglass, ceramic, or ward materials. These overclaims and broken references make the proposed promotion inventory unsafe to disposition as written even though the final prose itself is release-ready.",
      "requiredResolution": "Revise the canon delta so every assertion and dependency is supported by the final story. In WHM-08, remove or narrow the unsupported causal claim about opposed casting destroying the junction. In WHM-13, limit costs to those actually established in final prose unless the final story is deliberately revised to establish thirst and collapse risk. Correct WHM-09's anchor reference to the applicable ward-apparatus or office item, WHM-11's coordination reference to the joint-withdrawal procedure and relevant spillway infrastructure, and WHM-12's mineral-material references to the applicable stormglass, ceramic, or apparatus items. Re-audit all affected dependency ranges after those corrections without widening any fact beyond this incident.",
      "owner": "story_editor"
    }
  ],
  "certificationEligible": false,
  "changeReport": "The approximately 3,790-word final prose is publication-ready and preserves every passing-draft correction without regression. It fulfills the prompt through two unambiguously adult, dangerously competent rivals; the exact fighting/flirting exchange; a concrete conflict over divided civic attention; and separate, freely revocable tactical, political, courtship, and touch choices. Plane counts, contest adjudication, plate inventory, spatial causality, costs, withdrawal, dialogue profiles, close-third control, originality, names, and content boundaries pass. The final frontmatter is valid, the four character-facing forms match the registry and delta inventory, and the reviewed place and setting-term allowlist is complete. Release certification remains ineligible only because the proposed canon delta contains one material cluster of unsupported claims and incorrect dependency references that the story editor can resolve without user authority. No repository files were changed."
}
END_REVIEW_PASS_PAYLOAD

