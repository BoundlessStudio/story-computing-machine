# Continuity and story review

## Current certification

- Reviewed artifact: stories/the-healers-measure/03-draft.md
- Review pass: 1
- Verdict: REVISE
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 2
- Updated: 2026-08-03T22:11:34.1634329Z

This summary must match the newest completed payload. A completed story requires a passing draft review followed by a later passing review of `05-story.md`.

## Review passes

### Pass 1 — draft review

REVIEW_PASS_PAYLOAD
{
  "story": "the-healers-measure",
  "mode": "REVIEW_DRAFT",
  "status": "READY",
  "pass": 1,
  "reviewedArtifact": "stories/the-healers-measure/03-draft.md",
  "authorityManifest": "stories/the-healers-measure/authority.json",
  "handoffLedger": "stories/the-healers-measure/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T22:11:34.1634329Z",
  "reviewBasis": "Independent read-only complete-draft review under guard 4b0bb3bdf99441d48418778df493df89 against the captured prompt, in-progress lifecycle record, canon brief, scene-ready plan, pending pass-1 review scaffold, authority inventory captured at base commit c84db9d381f804d4b7ab4e09c9d49c7345c08ba2, ordered handoff ledger through completed sequence 3, and current complete character-name registry. Verified that the captured universe authority and admitted canon-story inventory remain unchanged and that witchknights remain a new locally bounded invention. Rechecked current LOCKED/CANON authority governing the persistent physical world, cultural system categories, living magical agency, local costs and consent behavior, personhood, evidence discipline, and Teen content limits. Audited prompt fulfillment, close-third past-tense control, chronology, spatial and causal clarity, Vekran's martial and magical credibility, Ruva's healer-centered apprenticeship, measurework access and costs, nonliving foci, consent, attacker personhood and custody, injuries, pacing, prose readiness, dialogue distinction and tactic changes, exact name use, and the climax's hold and false-branch timing. No prior completed finding disposition or final delta applies to REVIEW_DRAFT.",
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
      "id": "THM-DRAFT-001",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "hold-duration chronology and cost consistency",
      "locations": [
        "stories/the-healers-measure/02-story-plan.md:26",
        "stories/the-healers-measure/03-draft.md:113-125",
        "stories/the-healers-measure/03-draft.md:129-227",
        "stories/the-healers-measure/03-draft.md:229-353"
      ],
      "evidence": "The controlling plan limits Vekran's crisis hold to roughly sixty heartbeats. He establishes the fixed ward at lines 113-125, but before line 227 the story stages an examination, two consent negotiations, mundane pressure, a healing working, mapping, withdrawal, reassessment of Vekran's wound, a second live map, and a three-party bargain. Vekran then says the original limit was about sixty heartbeats with fewer remaining, after which Ruva warms her hands, renews consent, cleans and dresses the wound, fights an attacker, attempts and releases a failed hold, resets, remaps for three counted beats, turns a lash, aborts a cut, waits through another count, and finally parts the knot. This quantity of embodied action and dialogue cannot credibly fit inside the declared approximately one-minute hold, so the central cost ceiling and danger countdown contradict the on-page chronology.",
      "requiredResolution": "Make the complete ward sequence obey one credible declared limit. Preserve the bounded rising cost and Vekran's inability to hold and perform delicate parting simultaneously, but either stage the roughly sixty-heartbeat crisis load much nearer the decisive sequence or coordinate an explicit longer local limit and track its remaining time consistently. Ensure the examination, consent, attack, failed hold, reset, cut, and final redirection all fit the revised chronology without silently extending Vekran's power.",
      "owner": "prose_writer"
    },
    {
      "id": "THM-DRAFT-002",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "wound-knot timing and climax causality",
      "locations": [
        "stories/the-healers-measure/03-draft.md:229-245",
        "stories/the-healers-measure/03-draft.md:315-347"
      ],
      "evidence": "The caster defines the rule as a false branch thrown on the fourth beat after each tightening. After the working tightens at line 319, however, the caster counts one and two, warns that the branch has already moved, and Ruva sees it sliding toward living tissue. The caster then counts three and four and says 'Now,' after which the branch has passed and the safe line appears. The fourth beat therefore functions as the safe opening rather than the stated moment when the false branch is thrown. Because Ruva's abort, the caster's indispensable cooperation, and the survivable cut all depend on this exact timing, the contradiction obscures the climax's causal mechanism.",
      "requiredResolution": "Define one exact false-branch cycle and make the warning, count, visible movement, abort, safe interval, and cut follow it. Preserve the caster's truthful technical contribution and Ruva's refusal of a blind cut, but make clear whether the branch begins, crosses, or clears on the fourth beat and place 'Now' at the resulting safe moment.",
      "owner": "prose_writer"
    },
    {
      "id": "THM-DRAFT-003",
      "severity": "Minor",
      "status": "UNRESOLVED",
      "category": "courtyard clearance and object continuity",
      "locations": [
        "stories/the-healers-measure/03-draft.md:57",
        "stories/the-healers-measure/03-draft.md:83-95",
        "stories/the-healers-measure/03-draft.md:349-355",
        "stories/the-healers-measure/03-draft.md:385"
      ],
      "evidence": "The medicine cart begins crooked with one wheel wedged against the trough. Ruva sends the four injured evacuees toward the rear wall with the cart still between them and the yard, but no later action moves the cart. The climax nevertheless calls the courtyard empty and retroactively says patients dragged the cart back before Vekran redirects the released roof load into its former position. Because the cart is damaged, later shown with a split axle, and its clearance makes the redirection safe, this necessary movement should not first appear after the force has already been sent there.",
      "requiredResolution": "Establish before Vekran's final redirection that the cart and evacuees have been moved clear of the selected courtyard path, with movement credible for the cart's wedged wheel, damaged axle, and available people, or redirect the load into another already established empty area. Preserve the rear-route evacuation and the visible property damage.",
      "owner": "prose_writer"
    }
  ],
  "certificationEligible": false,
  "changeReport": "Read-only review; no files changed. The complete approximately 3,600-word draft otherwise fulfills the prompt strongly: Vekran demonstrates disciplined martial and magical mastery at visible cost; Ruva remains a healer whose triage, anatomy, stabilization, consent practice, and preservation instinct become tactically indispensable; her six weeks of narrow martial training support rather than replace that vocation; and the selection rationale is proved through consequential action before Vekran names it. The local measurework remains living-powered, its iron, chalk, clasp, blade, bracer, and architecture remain non-agentic foci, and healing retains concrete limits and ordinary aftercare. The injured attacker chooses cooperation, survives without absolution, and enters ordinary custody. Violence remains non-graphic and Teen, close-third past tense is controlled, Ruva, Vekran, and the knot-caster retain distinct conversational strategies and material tactic changes, the aftermath preserves injury and rebuilding costs, and the ending earns the integrated apprenticeship without instant mastery or universal reform. Only the registered forms Ruva and Vekran appear as character-facing names. Production revision is required for the contradictory sixty-heartbeat hold chronology and false-branch count, plus one Minor courtyard-clearance continuity gap; no canon ruling, retcon, or material prompt reinterpretation is required."
}
END_REVIEW_PASS_PAYLOAD
