# Continuity and story review

## Current certification

- Reviewed artifact: `stories/what-i-hate-most/03-draft.md`
- Review pass: 1
- Verdict: REVISE
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 2
- Updated: 2026-08-03T14:00:00.7256033Z

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
