# Continuity and story review

## Current certification

- Reviewed artifact: `stories/clerics-infernal-ex/05-story.md`
- Review pass: 2
- Verdict: REVISE
- Reviewer: continuity_critic
- Unresolved Critical findings: 0
- Unresolved Major findings: 1
- Updated: 2026-08-03T19:13:03.3621296Z

This summary must match the newest completed payload. A completed story requires a passing draft review followed by a later passing review of `05-story.md`.

## Review passes

### Pass 1 — draft review

REVIEW_PASS_PAYLOAD
{
  "story": "clerics-infernal-ex",
  "mode": "REVIEW_DRAFT",
  "status": "READY",
  "pass": 1,
  "reviewedArtifact": "stories/clerics-infernal-ex/03-draft.md",
  "authorityManifest": "stories/clerics-infernal-ex/authority.json",
  "handoffLedger": "stories/clerics-infernal-ex/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T18:56:23.4865540Z",
  "reviewBasis": "Independent read-only complete-draft review against the captured prompt, lifecycle record, canon brief, scene-ready plan, pending prior-review scaffold, authority manifest, ordered handoff ledger through completed sequence 3, full character-name registry, unchanged LOCKED/CANON universe authority, and the two directly relevant admitted canon stories identified by canon research, The Friends I Built and The Station Between. Checked prompt fulfillment, chronology, courtesy-hinge access and shutdown causality, living magical supply and nonliving foci, locally bounded demon and clerical framing, adult consensual history and present consent boundaries, party competence, close-third past-tense control, pacing, dialogue distinction, prose readiness, Teen/PG-13 treatment, physical object continuity, and registered names. No prior completed review exists, and a final delta is not applicable to REVIEW_DRAFT.",
  "verdict": "PASS",
  "blockType": null,
  "resolutionOwner": null,
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 0,
    "Minor": 2
  },
  "priorFindingDispositions": [],
  "findings": [
    {
      "id": "CIE-DRAFT-001",
      "severity": "Minor",
      "status": "UNRESOLVED",
      "category": "courtesy-hinge activation continuity",
      "locations": [
        "stories/clerics-infernal-ex/03-draft.md:9-11",
        "stories/clerics-infernal-ex/03-draft.md:69",
        "stories/clerics-infernal-ex/03-draft.md:89",
        "stories/clerics-infernal-ex/03-draft.md:205"
      ],
      "evidence": "The opening establishes that Emet discovers his stolen leaf already bolted into the fence's scaffold, and his later accounts say the party followed the components there and that his culpable present action was recognizing and powering the rig. Line 69 instead says a stolen leaf remains inert until its bearer mounts it in a new frame and supplies a new opening, then states that Emet did both. This briefly assigns Emet a physical mounting action contradicted by the surrounding chronology and obscures the intended division between the fence's construction and Emet's living activation.",
      "requiredResolution": "During final editing, state the activation conditions without claiming Emet mounted the leaf: preserve that the fence or its operation mounted the stolen leaf, that mounting alone remained inert, and that Emet knowingly supplied the fresh living opening that completed the rig's usable conditions.",
      "owner": "story_editor"
    },
    {
      "id": "CIE-DRAFT-002",
      "severity": "Minor",
      "status": "UNRESOLVED",
      "category": "endpoint object continuity",
      "locations": [
        "stories/clerics-infernal-ex/03-draft.md:347-367",
        "stories/clerics-infernal-ex/03-draft.md:389"
      ],
      "evidence": "Emet removes and bends his leaf on the sanctuary side while Lacrixa removes and melts her separate leaf after she has crossed into the kiln court; the window then closes between the two locations. The final paragraph nevertheless says the party leaves both ruined leaves fused into the sanctuary's iron scaffold for local authorities. Lacrixa's far-side leaf is never transferred back through the narrowing passage, so the two-leaf evidence inventory is spatially impossible as written.",
      "requiredResolution": "Keep each destroyed leaf on its established endpoint, or explicitly and safely transfer Lacrixa's leaf before closure. Ensure the sanctuary evidence inventory names only objects physically present there while preserving bilateral destruction, final revocation, and usable evidence for local authorities.",
      "owner": "story_editor"
    }
  ],
  "certificationEligible": false,
  "changeReport": "Read-only review; no files changed. The complete approximately 3,400-word draft fulfills the required comic reversal verbatim, grounds the party's glance in Bosk's theatrical history rather than sexuality, makes Emet and Lacrixa's consensual adult relationship and unresolved keyed access causal to the breach, and resolves both the populated-site danger and their unfinished relationship without killing, absolution, or reunion. Emet and Lacrixa remain accountable living agents; every consequential magical act is supplied by one or both of them while the leaves, loops, reservoirs, medallion, scaffold, and stone remain nonliving foci. The Cauterized Reach, demon identity, shelter practice, and crossing system stay locally bounded and unconnected to established infernal or afterlife systems. Bosk and Udren are tactically indispensable, the four speakers remain distinguishable under pressure, the countdown and costs are legible, injuries and intimacy remain Teen/PG-13, close-third past tense is controlled, and all character-facing forms match the unique registry reservations for Emet Sarn, Emet, Lacrixa, Bosk, and Udren. Two Minor continuity defects remain for final editing: the activation summary incorrectly credits Emet with mounting the fence-built leaf, and the ending relocates Lacrixa's destroyed far-side leaf into the sanctuary evidence. No Critical or Major findings remain, and no user ruling is required."
}
END_REVIEW_PASS_PAYLOAD

### Pass 2 — final review

REVIEW_PASS_PAYLOAD
{
  "story": "clerics-infernal-ex",
  "mode": "REVIEW_FINAL",
  "status": "READY",
  "pass": 2,
  "reviewedArtifact": "stories/clerics-infernal-ex/05-story.md",
  "authorityManifest": "stories/clerics-infernal-ex/authority.json",
  "handoffLedger": "stories/clerics-infernal-ex/handoffs.json",
  "reviewer": "continuity_critic",
  "reviewedAt": "2026-08-03T19:13:03.3621296Z",
  "reviewBasis": "Independent read-only joint review of the release-facing story and all 18 proposed canon-delta items against the captured prompt, lifecycle record, canon brief, scene-ready plan, source draft, pass-1 review history, unchanged authority inventory captured at base commit 8c4f2cf44e9da943711a7df4f1bc5df505bbc4a2, ordered handoff ledger through completed sequence 5, full character-name registry, and the directly relevant admitted canon stories The Friends I Built and The Station Between. Audited immutable title, slug, and creation-date frontmatter; exact prompt fulfillment; chronology; courtesy-hinge activation, escalation, shutdown, and endpoint causality; living magical supply and nonliving foci; locally bounded demon, clerical, and crossing claims; adult consensual history and present consent; party competence; close-third past-tense control; pacing; dialogue distinction; prose readiness; Teen/PG-13 boundaries; both prior finding resolutions; every delta fact, qualifier, dependency, provenance statement, disposition, and smallest topical target; the exhaustive final character-facing inventory; and the exact two-row, three-column reviewed-prose non-character allowlist. The strict Final story-names/3 gate passed at 2026-08-03T19:09:30.8946365+00:00 with zero warnings and zero errors.",
  "verdict": "REVISE",
  "blockType": null,
  "resolutionOwner": null,
  "resolutionQuestion": null,
  "errorCode": null,
  "unresolvedCounts": {
    "Critical": 0,
    "Major": 1,
    "Minor": 0
  },
  "priorFindingDispositions": [
    {
      "id": "CIE-DRAFT-001",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/clerics-infernal-ex/05-story.md:69, the final prose now distinguishes the fence's physical mounting from Emet's living activation: mounting alone leaves the work inert, and Emet knowingly completes the required condition only by recognizing and powering the keyed leaf while Lacrixa answers from her side. Delta items CIE-11 and CIE-16 preserve the same division."
    },
    {
      "id": "CIE-DRAFT-002",
      "priorPass": 1,
      "resolvedInPass": 2,
      "disposition": "RESOLVED",
      "evidence": "At stories/clerics-infernal-ex/05-story.md:349, Lacrixa melts her leaf and leaves it on the kiln court's red tile beside its hearthframe. At line 389, the sanctuary evidence inventory now contains only Emet's folded leaf, the three warped loops, spent salt-glass, and the dead scaffold. Delta items CIE-06, CIE-14, and CIE-17 preserve those separate endpoint inventories."
    }
  ],
  "findings": [
    {
      "id": "CIE-FINAL-001",
      "severity": "Major",
      "status": "UNRESOLVED",
      "category": "canon-delta evidence boundary",
      "locations": [
        "stories/clerics-infernal-ex/06-canon-delta.md:86-107",
        "stories/clerics-infernal-ex/06-canon-delta.md:167-183",
        "stories/clerics-infernal-ex/06-canon-delta.md:293-310",
        "stories/clerics-infernal-ex/05-story.md:19-21",
        "stories/clerics-infernal-ex/05-story.md:185-219",
        "stories/clerics-infernal-ex/05-story.md:281"
      ],
      "evidence": "Three delta claims exceed or blur the release-facing evidence. CIE-05 says both ex-partners retained keyed leaves for partly technical and partly personal reasons, but Emet explicitly admits that calling his retained access a safety precaution was a respectable cover for wanting the door, while Lacrixa alone identifies a genuine dangerous-echo reason alongside pride; the narration expressly says her admission does not divide fault equally. CIE-08 states that the House previously maintained a refuge near a Cauterized Reach road endpoint, a plan-only history never established in final prose, and groups broader institutional characteristics under House practice beyond what Emet directly demonstrates or reports. CIE-15 says Emet's ward-light can pass through an inert medallion, but line 21 explicitly uses the medallion only for its shelter-count while sending ward-light through the stolen leaf; no medallion-conduit capability is shown. These claims could carry unsupported relationship, institutional, and mechanism facts into later promotion.",
      "requiredResolution": "Revise the delta without requiring a prose rewrite. In CIE-05, preserve the asymmetry established by the story: Emet retained his leaf under a self-serving safety rationalization and unresolved desire, while Lacrixa states both a genuine dangerous-echo concern and a personal motive. In CIE-08, remove the unshown Reach-adjacent refuge history and narrow institutional practice to facts directly demonstrated or reported in final prose. In CIE-15, remove the claim that ward-light passes through the medallion and distinguish the inert shelter-count aid from the leaf and scaffold paths that actually carry Emet's supplied power. Recheck the affected constraints and dependencies against the unchanged final story.",
      "owner": "story_editor"
    }
  ],
  "certificationEligible": false,
  "changeReport": "Read-only review; no files changed. The complete 3,450-word final story is prompt-complete, canon-compatible, causally coherent, Teen/PG-13, and prose-ready. Its immutable frontmatter matches story.json; the required greeting, bard glance, and cleric-ex reversal occur exactly; the former adult consensual relationship materially causes the breach and its solution; both populated endpoints and the unfinished relationship receive earned resolution without killing, absolution, or reunion. Living supply, nonliving focus behavior, eighty-heartbeat limit, three-loop escalation, costs, discharge order, synchronized revocation, and endpoint-local leaf destruction remain legible and consistent. Bosk and Udren are indispensable, speaker strategies remain distinct, and the Cauterized Reach, demon identity, House practice, and crossing system remain locally framed. Both pass-1 findings are resolved without regression. The final character inventory is exhaustive, the two-entry three-column allowlist is exact, all five character-facing forms match unique registry reservations, and the strict Final name gate passes cleanly. All 18 delta items have explicit scope, constraints, dependencies, provenance, dispositions, and targets, and the remaining fifteen are prose-supported and suitably bounded. Certification is withheld because CIE-05 blurs the exes' unequal reasons for retaining access, CIE-08 imports an unshown refuge history and overstates institutional evidence, and CIE-15 invents a medallion-conduit capability. These are delta-only production repairs requiring no user ruling, retcon, or prose change."
}
END_REVIEW_PASS_PAYLOAD
