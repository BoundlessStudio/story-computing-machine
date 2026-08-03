# Continuity and story review

## Current certification

- Reviewed artifact: stories/the-healers-measure/03-draft.md
- Review pass: 2
- Verdict: PASS
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 0
- Updated: 2026-08-03T22:20:05.5587047Z

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

### Pass 2 — draft re-review

REVIEW_PASS_PAYLOAD
{
  "story": "the-healers-measure",
  "mode": "REVIEW_DRAFT",
  "status": "READY",
  "pass": 2,
  "reviewedArtifact": "stories/the-healers-measure/03-draft.md",
  "authorityManifest": "stories/the-healers-measure/authority.json",
  "handoffLedger": "stories/the-healers-measure/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T22:20:05.5587047Z",
  "reviewBasis": "Independent read-only complete draft re-review under guard bddfb638669245eeb1879d6ff6e57cc7 against the captured prompt, in-progress lifecycle record, canon brief, scene-ready plan, revised 3,858-word draft, review history through pass 1, authority inventory captured at base commit c84db9d381f804d4b7ab4e09c9d49c7345c08ba2, ordered handoff ledger through completed sequence 5, and current complete character-name registry. Verified each prior finding against the revised prose and then re-audited the complete draft for prompt fulfillment, chronology, spatial and causal clarity, partial-brace and full-load behavior, sixty-heartbeat tracking, false-branch timing, courtyard clearance, living magical agency, non-agentic foci, local scope and costs, healing limits, consent, attacker personhood and custody, Teen injury treatment, close-third past-tense control, pacing, dialogue distinction and tactic changes, prose readiness, and exact registered name use. The captured universe authority and admitted canon-story inventory remain unchanged. No final delta applies to REVIEW_DRAFT.",
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
      "id": "THM-DRAFT-001",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/the-healers-measure/03-draft.md:115-181, the revised prose identifies Vekran's initial working as a lower-load partial brace that carries only the sliding beam while intact posts and the divided knot continue bearing most roof pressure. Lines 227 and 259 explicitly defer the approximately sixty-heartbeat crisis limit until the final map. Lines 303-361 then begin the full four-line load at sixty and track it through forty-six, thirty-four, twenty-eight, and eighteen heartbeats before the immediate final redirection. The examination, consent negotiations, interruption, and failed apprentice hold therefore occur before the declared full-load countdown, while the mapped cut and release fit coherently inside it."
    },
    {
      "id": "THM-DRAFT-002",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/the-healers-measure/03-draft.md:243, the caster now defines one exact cycle: the false branch begins crossing on beat one, covers the living line on beats two and three, clears on four, and leaves a gap until the next tightening. Lines 325-355 follow that rule exactly: tightening begins, the caster calls one and movement, calls two and stops Ruva as the branch crosses, holds her through three, then calls four, clear, and now. Ruva's abort and subsequent safe parting are causally legible, and the caster's cooperation remains indispensable."
    },
    {
      "id": "THM-DRAFT-003",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/the-healers-measure/03-draft.md:95, Ruva and the two mobile patients rock the wedged wheel free, move the driver and injured passenger through the rear gate, shove the cart behind the stone wall, and explicitly leave the strip from the infirmary doorway past the trough empty. Lines 361-365 direct the released roof load into that previously cleared strip and show the debris stopping short of the cart behind the wall. The cracked axle remains accounted for in the aftermath."
    }
  ],
  "findings": [],
  "certificationEligible": false,
  "changeReport": "Read-only re-review passed; no files changed. All three pass-1 findings are resolved without regression. The revised draft distinguishes Vekran's draining partial brace from the final full crisis load, starts and tracks the sixty-heartbeat limit at the exact transition to all four roof lines, and completes the map, turn, abort, parting, and redirection with eighteen heartbeats remaining. Its false-branch rule and performed count now align exactly, preserving both Ruva's refusal of a blind cut and the caster's consequential agency. The medicine cart, injured evacuees, and redirection path are established before the climax. The complete story remains prompt-complete, canon-compatible, locally bounded, causally coherent, Teen, and ready for final editing. Vekran's martial and magical mastery remains credible and costly; Ruva succeeds through integrated healing judgment and narrow apprentice skills rather than effortless combat mastery; living practitioners supply every magical act while iron, chalk, blades, braces, the clasp, and architecture remain inert foci. Healing remains limited and requires ordinary care, consent is active and revisited, the attacker survives without absolution and enters custody, injuries and property damage persist, dialogue strategies remain distinct under pressure, and the ending preserves Ruva's vocation within her continuing apprenticeship. Only the registered character-facing forms Ruva and Vekran appear. No unresolved finding or user ruling remains; certification eligibility remains false because this is a draft review rather than the release-facing final gate."
}
END_REVIEW_PASS_PAYLOAD
