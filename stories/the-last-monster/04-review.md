# Continuity and story review

## Current certification

- Reviewed artifact: `stories/the-last-monster/05-story.md`
- Review pass: 2
- Verdict: REVISE
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 1
- Updated: 2026-08-03T08:59:26.0618769Z

This summary must match the newest completed payload. A completed story requires a passing draft review followed by a later passing review of `05-story.md`.

## Review passes

<!-- Preserve every completed pass in ascending contiguous order. Replace this pending scaffold for the first review. Under each pass heading, persist exactly one complete block bounded by REVIEW_PASS_PAYLOAD and END_REVIEW_PASS_PAYLOAD, exactly as returned by the reviewer. -->

### Pass 1 — draft review

REVIEW_PASS_PAYLOAD
{
  "story": "the-last-monster",
  "mode": "REVIEW_DRAFT",
  "status": "READY",
  "pass": 1,
  "reviewedArtifact": "stories/the-last-monster/03-draft.md",
  "authorityManifest": "stories/the-last-monster/authority.json",
  "handoffLedger": "stories/the-last-monster/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T08:37:57.1989247Z",
  "reviewBasis": "Independent read-only complete-draft review under guard 76f65c1e3b63428d907edfa2417c670b against the captured prompt, drafting-stage lifecycle record, canon brief, revised scene-ready plan, pending pass-1 review scaffold, authority inventory captured at base commit a4c69f8211a7df39c364c6a720723d0b1c1e3e0b, ordered handoff ledger through completed sequence 4, and current full character-name registry. Rechecked current LOCKED/CANON universe authority and the five material admitted precedents identified by the brief: Realms, The Small Moon Rose First, The Shape of Mercy, The Gentlest Terror, and Daughter of the Sun. The audit covered prompt fulfillment, close-second present narration, elapsed-time evidence, scene causality, learned creature fear, physical escape mechanics, observable evidence versus unstable interpretation, nonmagical local scope, mature-teen violence boundaries, moral agency and accountability, exact single use of Salken, prose and pacing readiness, and exclusion of crossover, dream, simulation, and unreal-victim devices.",
  "verdict": "PASS",
  "blockType": null,
  "resolutionOwner": null,
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 0,
    "Minor": 1
  },
  "priorFindingDispositions": [],
  "findings": [
    {
      "id": "TLM-DRAFT-001",
      "severity": "Minor",
      "status": "UNRESOLVED",
      "category": "physical action continuity",
      "locations": [
        "stories/the-last-monster/03-draft.md:19",
        "stories/the-last-monster/03-draft.md:139",
        "stories/the-last-monster/03-draft.md:153-159"
      ],
      "evidence": "Line 19 fastens the protagonist's lantern strap at their shoulder. During the spillway attack, line 139 has the escaping figure snatch up that lantern without showing the strap breaking, the lantern falling, or the figure taking it from the protagonist. Lines 153-159 then depend on the lantern having been abandoned beside the small opening so the protagonist can recover its failing light. The intended transfer is inferable but the physical action is momentarily discontinuous.",
      "requiredResolution": "During final editing, add a brief mechanically explicit beat showing how the shoulder-fastened lantern becomes loose or is taken during the struggle and reaches the small opening, while preserving the destroyed brighter lantern, failing-light pressure, and non-graphic pacing.",
      "owner": "story_editor"
    }
  ],
  "certificationEligible": false,
  "changeReport": "Initial draft review passed with one Minor physical-staging finding. The complete approximately 3,275-word story fulfills the prompt in sustained close second person and present tense: material wear, overlapping wounds, failed counting, and contradictory remembered yesterdays establish prolonged time loss without an altered chronology mechanism; repeated airflow tests produce a concrete route; coordinated warnings, rear-facing barricades, abandoned shelters, converging tracks, and protected dependents demonstrate that varied dungeon inhabitants have learned to flee the protagonist; and the cistern recognition, spillway relapse, guardian pause, cooperative grate ascent, explicit emergence into daylight, restraint, confession, and offer to guide rescuers form a coherent causal and moral arc. Observable behavior repeatedly precedes or corrects frightened interpretation, while victim identities remain uncertain but real. Deprivation, injury, sleep loss, isolation, tinnitus, and trauma supply the entirely nonmagical deterioration; no established crossing, location, faculty, terminology, or mechanism is borrowed. Violence is sustained but non-graphic and consequential, impairment explains without compelling or absolving, and the ending resolves escape while preserving accountability. Salken appears exactly once in direct address, no other character-facing name or alias appears, and the title remains title-only. No dream, simulation, unreal-victim reveal, innate-evil mental-illness framing, or prohibited crossover occurs. No Critical or Major findings remain, no user ruling is required, certification eligibility remains false for this draft review, and no repository files were changed."
}
END_REVIEW_PASS_PAYLOAD

### Pass 2 — final review

REVIEW_PASS_PAYLOAD
{
  "story": "the-last-monster",
  "mode": "REVIEW_FINAL",
  "status": "READY",
  "pass": 2,
  "reviewedArtifact": "stories/the-last-monster/05-story.md",
  "authorityManifest": "stories/the-last-monster/authority.json",
  "handoffLedger": "stories/the-last-monster/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T08:59:26.0618769Z",
  "reviewBasis": "Independent read-only joint review under guard 1f2cb19ded8d464380a579f2abb45c08 of the release-facing story and all 23 proposed canon-delta items against the captured prompt, final-edit lifecycle record, canon brief, revised scene-ready plan, source draft, pass-1 review history, authority manifest captured at base commit a4c69f8211a7df39c364c6a720723d0b1c1e3e0b, ordered handoff ledger through completed sequence 6, and current full name registry. Reverified the unchanged LOCKED/CANON universe inventory and the five material admitted precedents: Realms, The Small Moon Rose First, The Shape of Mercy, The Gentlest Terror, and Daughter of the Sun. Audited immutable frontmatter, prompt fulfillment, close-second present narration, elapsed-time evidence, perception discipline, chronology, causality, learned fear, physical escape mechanics, nonmagical local scope, mature-teen boundaries, agency and accountability, prose readiness, exact single Salken use, exhaustive character inventory, reviewed-prose allowlist, every delta disposition, qualifier, dependency, and target, and absence of promotion, crossover, dream, simulation, or unreal-victim devices. Authority verification and the six-entry handoff-ledger check passed. The strict Final story-names/3 gate passed at 2026-08-03T08:53:38.6658029+00:00 with zero warnings and zero errors.",
  "verdict": "REVISE",
  "blockType": null,
  "resolutionOwner": null,
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 1,
    "Minor": 1
  },
  "priorFindingDispositions": [
    {
      "id": "TLM-DRAFT-001",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/the-last-monster/05-story.md:139, the thrown rope now catches the shoulder-hung lantern, tears its strap at the iron loop, and sends the still-burning lantern toward the moss-hung opening before the escaping figure takes it. Line 153 then locates the abandoned failing light beside that opening. This explicitly connects the shoulder fastening at line 19 to the lantern's recovery at line 159 while preserving the destroyed brighter lantern and last-light pressure."
    }
  ],
  "findings": [
    {
      "id": "TLM-FINAL-001",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "canon-delta evidence boundary",
      "locations": [
        "stories/the-last-monster/06-canon-delta.md:34",
        "stories/the-last-monster/06-canon-delta.md:54",
        "stories/the-last-monster/05-story.md:23-25",
        "stories/the-last-monster/05-story.md:91",
        "stories/the-last-monster/05-story.md:139-159",
        "stories/the-last-monster/05-story.md:235-253"
      ],
      "evidence": "TLM-03 attributes Salken's deterioration partly to sleep disruption, but its own evidence column does not identify sleep disruption and the final prose establishes only that Salken once slept beside the cistern soot; it never establishes disrupted sleep as a cause. TLM-23 then says the story establishes no technological mechanism for the dungeon or escape even though its evidence calls the operative causes mechanical and the final story materially depends on designed architecture, lanterns, rope, grates, a map, and a sword used as a lever. The intended boundary is no magical, extraordinary established-system, universal, or crossover mechanism, not an absence of ordinary technology. These two claims exceed or conflict with the release-facing prose and could carry unsupported mechanism facts into a later promotion.",
      "requiredResolution": "Revise TLM-03 to remove sleep disruption from the proposed fact unless the final prose is deliberately changed to establish it; the smallest safe repair is delta-only. Revise TLM-23 to preserve the demonstrated ordinary mechanical tools and architecture while excluding only magical, divine, extraordinary established-system, universal, and crossover explanations. Recheck all wording and dependencies in both rows against the unchanged final prose.",
      "owner": "story_editor"
    },
    {
      "id": "TLM-FINAL-002",
      "severity": "Minor",
      "status": "UNRESOLVED",
      "category": "canon-delta disposition and target alignment",
      "locations": [
        "stories/the-last-monster/06-canon-delta.md:45"
      ],
      "evidence": "TLM-14 proposes retaining the lantern transfer as a story-causal detail, which denotes a story-local disposition, but assigns universe/timeline.md as its suggested topical target. The same delta uses No universe write for other facts proposed to remain unresolved or excluded, so this row leaves the intended future disposition ambiguous.",
      "requiredResolution": "Align TLM-14's disposition and target: use No universe write if the transfer is to remain story-local, or change the proposed disposition to an explicit topical addition if timeline promotion is genuinely intended. Preserve its precise local qualifiers and ordinary physical mechanics.",
      "owner": "story_editor"
    }
  ],
  "certificationEligible": false,
  "changeReport": "Final prose is prompt-complete, canon-compatible, causally coherent, non-graphic, and prose-ready. Its valid release frontmatter matches the title, slug, and creation date; its approximately 3,307 prose words preserve close second person and present tense; material wear and wounds establish unmeasured duration without altered chronology; observable behavior repeatedly corrects unstable interpretation; varied inhabitants demonstrate learned fear through warnings, evacuation, barricades, and protected dependents; and the airflow, spillway, bypass, guardian pause, levered grate, explicit daylight exit, restraint, confession, and offer of assistance form a complete physical and moral chain. TLM-DRAFT-001 is precisely resolved without regression. Salken appears exactly once, no other character-facing form exists, the final inventory is exhaustive, None is the correct empty reviewed-prose allowlist, and story-names/3 passes cleanly. The delta remains proposed-only, unpromoted, locally bounded, non-taxonomic, and conflict-free; its other twenty items are prose-supported with explicit dependencies and suitable smallest targets. Certification is withheld because TLM-03 imports an unestablished sleep-disruption cause, TLM-23 inaccurately denies ordinary technological mechanics, and TLM-14 does not align its story-local disposition with its suggested target. These are production-artifact repairs requiring no user ruling, retcon, or prose rewrite. No repository files were changed."
}
END_REVIEW_PASS_PAYLOAD
