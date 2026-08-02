
# Continuity and story review

## Current certification

- Reviewed artifact: `05-story.md`
- Review pass: 5
- Artifact SHA-256: `68516b768a27f61a27f39f881465a0a9f5dfcb0a2e77ca00df619faec75cb5c0`
- Canon delta SHA-256: `d8284f2507e36b25369e66b372207b664a36df0285f2976fd51dba55ca759827`
- Verdict: PASS
- Reviewer: primary_continuity_fallback
- Unresolved Critical findings: 0
- Unresolved Major findings: 0
- Updated: 2026-08-02T03:48:19.5150496+00:00

This certification applies only to the exact artifact hashes above. The prose
body and canon-delta bytes are unchanged from the preceding PASS; this pass
certifies only removal of mutable lifecycle fields from YAML frontmatter.
## Review passes

<!-- Preserve every pass. Duplicate the structure below for later passes, and
update Current certification to match the newest pass. -->

### Pass 1 — draft gate

- Reviewed artifact: `03-draft.md`
- Verdict: REVISE

#### Canon

- None. The draft keeps the magical-girl system and handler arrangement local,
  identifies the Rollcaller as living, locates magical agency in living users,
  treats names and records as ordinary evidence, and preserves the
  modern-like era's public-disbelief baseline. No unsupported crossover or
  global magical authority appears.

#### Continuity

- **Finding 1**
  - **Severity:** Major
  - **Location:** `03-draft.md`, crisis and blackout sequence, from “I can give
    you darkness, close the fire partition, and hold an evacuation route” to
    Gideon pulling the breaker and dragging the partition closed; contradicted
    by the next-morning assertion that the girls have not connected Mr.
    Tolland with Night Clerk.
  - **Evidence:** Night Clerk makes a first-person promise to perform three
    specific on-site actions. Immediately afterward, the girls can observe Mr.
    Tolland pull the local breaker, open the service route, drag the acoustic
    partition, and hold it while Kiteglass guards the same opening. The ending
    states that none of them recognizes the connection, but supplies no
    competing explanation for this exact match.
  - **Why it matters:** Bryn is explicitly a skeptical systems thinker, and all
    three girls know Night Clerk is following the crisis live. The only visible
    adult carrying out Night Clerk's announced choreography is their teacher.
    That makes their continued ignorance feel asserted rather than earned and
    risks an accidental reveal of both Gideon's handler identity and his
    knowledge of their civilian identities. It breaks a required prompt
    boundary.
  - **Smallest effective fix:** Decouple Night Clerk's relay language from Mr.
    Tolland's visible actions. Have the relay provide neutral facts and the
    blackout option without claiming that Night Clerk personally will close
    or hold the route; let the girls request darkness, while Mr. Tolland's
    partition and evacuation work reads as an ordinary teacher's independent
    emergency response. Preserve the voice scrambling and avoid any
    handler-only phrase in Mr. Tolland's hearing.

#### Names

- None. Every character-facing form in the draft is present in the plan's
  `Name check` and in `stories/NAMES.md`: `Gideon Tolland`, `Gideon`, `Mr.
  Tolland`, `Night Clerk`; `Drita Ademi`, `Drita`, `Kiteglass`; `Bryn Ahn`,
  `Bryn`, `Pulsewire`; `Cassia Dominguez`, `Cassia`, `Mothlight`; `the
  Rollcaller`, `Rollcaller`. No surname is used alone, `Clerk` is not used
  alone, role nouns remain common descriptions, and no exact, close, reversed,
  unresolved, or Solstice-adjacent collision appears.

#### Causality and character

- **Finding 2**
  - **Severity:** Major
  - **Location:** `03-draft.md`, morning attendance through the forged
    midafternoon PA summons.
  - **Evidence:** The narration says the Rollcaller “had watched him protect
    exactly one reaction,” and Gideon reports that only one student nearly
    reacted when the creature paired the spoken civilian name with
    `Kiteglass`. Before any further observation or inference is shown, the
    creature correctly summons `Drita Ademi, Bryn Ahn, and Cassia Dominguez`
    as one group. “Every name had been on the stolen sightline” explains access
    to the roster, but not why it selected Bryn and Cassia from the rest of the
    class.
  - **Why it matters:** The antagonist's acquisition of all three civilian
    identities drives the livestream crisis. Leaving two selections
    unexplained makes the Rollcaller effectively know what the story and canon
    say it must learn through observation, evidence, and inference; it also
    weakens the intended consequence of Gideon's protective behavior.
  - **Smallest effective fix:** Before or during the false summons, identify
    the concrete mundane basis that makes Bryn and Cassia candidates. One local
    sentence can frame the three-name summons as a limited roster probe and
    explain why those three names, with their shared stillness and Gideon's
    intervention then supplying confirmation. Do not give the Rollcaller
    automatic truth from the ledger or a new magical recognition ability.

#### Prompt fulfillment

- No additional finding. The draft dramatizes teacher and covert-handler work,
  physical/emotional/academic/operational care, a classroom/battle collision,
  the girls' informed choices, and an immediate contained threat. Finding 1
  must be fixed for the required “girls remain unaware” promise to be
  fulfilled.

#### Pacing and prose

- None. At approximately 3,450 words, the draft is within the contracted range.
  Its six movements escalate cleanly, the blackout stays in Gideon's close
  third-person access through sound and narrow visual fragments, and the
  aftermath resolves the operational, academic, and emotional threads without
  overextending the ending.

#### Canon-delta coverage

- None at this draft gate; `06-canon-delta.md` is not the reviewed artifact.
  The final delta will need to capture:
  - the modern-like placement and local Northbridge Secondary incident;
  - the three civilian/magical identity mappings and Gideon/Night Clerk
    mapping, plus the complete final name inventory listed under `Names`;
  - the voluntary focus-token transformations, living-user powers, local
    costs, and bounded refraction veil;
  - the informal anonymous handler arrangement, opt-in telemetry, no-orders
    consent rule, and negotiated darkness protocol;
  - the Rollcaller's living nature, evidence-based identity hunting, voice
    mimicry, network-filament behavior, attention-seeking mechanism, severance,
    and short-term containment in an unplugged equipment case; and
  - the incident outcome, including the stopped stream, preserved identities,
    recovery choice, and unresolved later disposition of the contained
    Rollcaller.

#### Required fixes

1. Remove the on-relay first-person claim that makes Night Clerk's promised
   actions visibly identical to Mr. Tolland's crisis actions, so the girls'
   continued ignorance is causally credible.
2. Supply the missing mundane observation or explicitly bounded probe that
   explains why the Rollcaller selects Bryn and Cassia along with Drita.

### Pass 2 — draft gate focused recheck

- Reviewed artifact: `03-draft.md`
- Verdict: PASS

#### Prior-finding disposition

- **Pass 1 Finding 1 — RESOLVED.** Night Clerk now states the network and
  blackout facts without claiming that he personally will pull the breaker,
  open the service exit, or hold the acoustic partition. Mr. Tolland's visible
  actions are independently grounded in ordinary school procedure: the nearest
  adult kills power to hijacked electrical equipment, uses the designated
  exit when the main doors are bound, and closes the fire partition while
  students evacuate. The girls therefore have a credible school-facing
  explanation and are not given proof that their teacher is Night Clerk or
  knows their identities.
- **Pass 1 Finding 2 — RESOLVED.** The revised showcase setup shows a living
  filament follow Drita, Bryn, and Cassia as they converge over one cue sheet.
  The narration explicitly limits the Rollcaller to one strong candidate
  (Drita), treats Bryn and Cassia as an observable guess, and makes the PA
  summons a test. Their shared stillness and Gideon's intervention then provide
  the mundane confirmation used in the livestream. The ledger supplies
  spellings rather than truth.

#### Canon

- None. The revisions add no universal rule or nonliving magic user. The
  Rollcaller's inference remains observation-based, and the local electrical
  and evacuation procedures remain mundane.

#### Continuity

- None. Gideon's teacher/handler information boundary is now causally
  credible, the girls remain unaware of his dual role and covert knowledge,
  and the blackout sequence retains Gideon's limited access through observed
  sound, light, and later volunteered reports.

#### Names

- None. No character-facing name or alias was added or changed. The complete
  draft inventory still matches the plan and `stories/NAMES.md`, with no
  accidental or undocumented collision.

#### Causality and character

- None. The Rollcaller's selection of all three civilians is now a bounded
  probe with setup and confirmation. Drita, Bryn, and Cassia retain the
  consequential choices that determine engagement, blackout, battle roles,
  severance consent, containment, and recovery.

#### Prompt fulfillment

- None. The revision preserves the teacher/handler premise, all four lanes of
  care, the classroom/battle collision, the girls' agency, the contained
  identity threat, and the unrevealed teacher/handler connection.

#### Pacing and prose

- None. The revised draft remains within the contracted range at approximately
  3,581 words. The added inference and procedural explanations are brief,
  legible in Gideon's close-third perspective, and do not materially slow the
  escalation or aftermath.

#### Canon-delta coverage

- None. The anticipated final coverage recorded in Pass 1 remains complete.
  The revision adds causal clarification about a local probe and ordinary
  school emergency procedure, not a new reusable magical rule, identity,
  faction, or global institution.

#### Required fixes

- None.

### Pass 3 — final gate

- Reviewed artifact: `05-story.md`
- Canon delta reviewed: `06-canon-delta.md`
- Verdict: PASS

#### Final-edit regression check

- None. The final edit preserves the passed draft's bounded PA probe and
  teacher/handler information boundary. Its prose changes are limited to
  frontmatter, small usage and sentence-flow edits, and line wrapping; none
  changes chronology, character knowledge, agency, consent, magic, secrecy, or
  outcome.

#### Canon

- None. The final story keeps the modern-like setting local and low-magic,
  treats the Rollcaller and the girls as the living sources of anomalous
  action, leaves tokens and equipment nonliving, and gives names and records
  ordinary evidentiary rather than automatic magical power. It establishes no
  global magical authority, universal system, unsupported crossover, or
  promoted canon.

#### Continuity

- None. The story runs coherently from the post-battle school morning through
  the afternoon showcase, evening recovery check, and next-morning attendance.
  Gideon's identity inference remains cumulative and mundane. Night Clerk does
  not use civilian names or claim Mr. Tolland's visible emergency actions, so
  the girls have no conclusive bridge between his two roles. After the breaker
  kills the relay, Gideon learns only through sounds, narrow-window glimpses,
  and facts the girls later volunteer.

#### Names

- None. Every character-facing form used in `05-story.md` appears in the
  plan's `Name check`, `stories/NAMES.md`, and the delta's complete final
  inventory: `Gideon Tolland`, `Gideon`, `Mr. Tolland`, `Night Clerk`; `Drita
  Ademi`, `Drita`, `Kiteglass`; `Bryn Ahn`, `Bryn`, `Pulsewire`; `Cassia
  Dominguez`, `Cassia`, `Mothlight`; `the Rollcaller`, `Rollcaller`. No surname
  or `Clerk` is used alone, no new proper-name form appears, and no exact,
  close, reversed, unresolved, or falsely connective collision is present.

#### Causality and character

- None. The Rollcaller has one evidence-backed civilian candidate, observes
  her two presentation partners, tests that bounded guess through the PA, and
  gains confirmation from the shared reaction and Gideon's intervention.
  Gideon supplies information, blackout cover, and evacuation rather than the
  magical victory. Drita chooses defense, Bryn identifies and consensually
  severs the connections, and Cassia requests a breath before creating the
  decisive decoys. The trio also chooses engagement and recovery terms.

#### Prompt fulfillment

- None. The final story fully dramatizes a teacher moonlighting as an
  anonymous magical-girl handler, with physical, emotional, academic, and
  operational care crossing classroom and battle. The immediate threat is
  contained without a transformation reaching witnesses, the girls retain
  decisive agency, and Gideon's identity and covert knowledge remain
  unrevealed to them.

#### Pacing and prose

- None. At approximately 3,584 words, `05-story.md` is within the contracted
  3,200–3,800-word range. Its six movements escalate and resolve cleanly,
  maintain past-tense close third through Gideon, keep violence non-graphic,
  and preserve the tender, dry, suspenseful tone without romanticizing the
  teacher/student relationship.

#### Canon-delta coverage

- None. `06-canon-delta.md` accurately captures the five identity mappings and
  full final alias inventory; Northbridge Secondary and the modern-like era;
  the local transformation, power, cost, refraction, communications, consent,
  and containment rules; the Rollcaller's living, observation-based
  capabilities and limits; Gideon's asymmetrical knowledge; the incident
  chronology and public-secrecy outcome; the recovery and darkness protocols;
  and the unresolved long-term disposition of the Rollcaller.
- The delta consistently limits these facts to this trio, antagonist,
  arrangement, school, and incident. Its header, conflict section, promotion
  boundary, and conditional recommendations clearly state that it is proposed
  rather than canon and require explicit approval before promotion. It neither
  overclaims a universal rule nor silently promotes any fact.

#### Required fixes

- None.

## Verdict

PASS

### Pass 4 — final-story migration certification

REVIEW_PASS_PAYLOAD

- story: `the-attendance-ledger`
- pass: 4
- reviewedArtifact: `05-story.md`
- artifactSha256: `b0bbaf91b2cddf5ef963b673d4441462284e1bb9ba93d3a1d3c6be959ea2744f`
- canonDeltaSha256: `d8284f2507e36b25369e66b372207b664a36df0285f2976fd51dba55ca759827`
- reviewer: primary_continuity_fallback
- reviewedAt: `2026-08-01T22:45:00-04:00`
- reviewBasis: Prior specialist draft/final PASS history; current universe
  LOCKED/CANON authority; the independent 17-story combined promotion audit;
  exact current final/delta bytes; and successful strict Final name receipt
  `b5109a9a3de2e31a08b4b8c9e58feacea8f6a5961348ff363ddef50f21d1e061`.
- verdict: PASS
- blockType: NONE
- resolutionOwner: none
- resolutionQuestion: none
- unresolvedCounts: `{ critical: 0, major: 0, minor: 0 }`
- certificationEligible: true
- changeReport: read-only review; reviewed artifacts unchanged

#### Prior finding dispositions

No prior Critical or Major finding remained open in the preceding PASS.
The migration review found no previously resolved blocker reopened by the
frontmatter, exact-name-inventory, or LF normalization backfill.

#### Findings

None.

END_REVIEW_PASS_PAYLOAD

### Pass 5 — immutable-frontmatter migration certification

- Reviewed artifact: `05-story.md`
- Previous artifact SHA-256: `b0bbaf91b2cddf5ef963b673d4441462284e1bb9ba93d3a1d3c6be959ea2744f`
- Artifact SHA-256: `68516b768a27f61a27f39f881465a0a9f5dfcb0a2e77ca00df619faec75cb5c0`
- Canon delta SHA-256: `d8284f2507e36b25369e66b372207b664a36df0285f2976fd51dba55ca759827`
- Review date: 2026-08-02T03:48:19.5150496+00:00
- Verdict: PASS
- Reviewer: primary_continuity_fallback
- Findings: 0 Critical, 0 Major, 0 Minor

#### Migration evidence

- Reconstructing the former frontmatter from current immutable identity fields
  plus the prior lifecycle values reproduces the prior release hash exactly:
  `b0bbaf91b2cddf5ef963b673d4441462284e1bb9ba93d3a1d3c6be959ea2744f`.
- The prose body beginning after the closing frontmatter delimiter is byte-for-byte
  unchanged. `06-canon-delta.md` is also unchanged at `d8284f2507e36b25369e66b372207b664a36df0285f2976fd51dba55ca759827`.
- The only story-byte change removes `status`, `canon`, `userDisposition`,
  `publish`, and `promotionDate` from frontmatter. Those mutable fields remain
  authoritative in `story.json` and checked projections.

#### Required fixes

- None.
