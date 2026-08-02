
# Continuity and story review

## Current certification

- Reviewed artifact: `05-story.md`
- Review pass: 6
- Artifact SHA-256: `21a2190ca8a4caaf494646a1f4e9d5dcb1637143ea29a36d0352b834cd0facf0`
- Canon delta SHA-256: `e04689f8e9f9488bef29106dd698ca3b932b7fd0e27722302da1539e4ebfbd13`
- Verdict: PASS
- Reviewer: primary_continuity_fallback
- Unresolved Critical findings: 0
- Unresolved Major findings: 0
- Updated: 2026-08-02T03:48:19.5150496+00:00

This certification applies only to the exact artifact hashes above. The prose
body and canon-delta bytes are unchanged from the preceding PASS; this pass
certifies only removal of mutable lifecycle fields from YAML frontmatter.
## Review passes

### Pass 1 — draft review

- Reviewed artifact: `03-draft.md`
- Review date: 2026-07-27
- Verdict: REVISE
- Findings: 0 Critical, 1 Major, 1 Minor, 1 Optional

#### Canon

- Clear. Copperwell's lattice is local, bounded, technological, non-sentient,
  fallible, and unconnected to named eras or other systems. No authoritative
  universe contradiction was found.

#### Continuity

- **Major — individual consent is contradicted during Common Cause.**
  - Location: original draft lines 341–345, 371–373, 384–403, and 481–498.
  - Evidence: The protocol promises accepted positions and individual
    acceptance/refusal/withdrawal, but Edda publishes Copperwell defenders'
    positions before Common Cause acceptances. Harven alone severs his beacon
    while his squad disappears, and Harven alone later accepts while the squad
    resolves with him.
  - Why it matters: Individual consent is the story's ethical and mechanical
    promise. Refusal cannot be meaningful if live data is published before
    opt-in or a commander controls a squad's participation.
  - Smallest effective fix: Before acceptance, publish only the objective,
    structural hazards, static routes/control locations, uncertainty, and
    strategic cost. Reveal live positions only after each beacon accepts.
    State that Harven and the relevant squad members each withdraw and later
    each accept, while preserving Harven as the decisive final holdout.
- The clock, pressure cascade, chamber position, gate brace, injuries, object
  state, and withdrawal sequence otherwise track coherently.

#### Names

- Clear. `Edda Rook`/`Edda`, `Harven Coil`/`Harven`, and `Sula
  Brant`/`Sula` match the plan and registry without collision.
- `watch captain`, `League signal lead`, and `signal lead` remain lowercase
  descriptive roles. `Host`, `Controller`, `Combat Controller`, `Command
  Thirteen`, and `Common Cause` remain interface or protocol terms rather than
  character-facing aliases.

#### Causality and character

- Strong apart from the individual-link contradiction. Edda's floodworks
  experience, Sula's current measurements, Harven's physical courage, fallible
  sensors, and difficult coordinated labor all materially cause the resolution.

#### Prompt fulfillment

- Complete. The awakening chain is literal, all thirteen levels derive from
  concrete prior experience, Level 13 resolves the crisis without domination,
  and Edda makes the consequential command choice.

#### Pacing and prose

- Approximately 3,534 words; tense, close-third, tactically clear, humane, and
  Teen-appropriate.
- **Minor — the manual spillwheel is introduced only when the climax requires
  it.**
  - Location: original draft lines 360–364, paid off at lines 481–540.
  - Evidence: The wheel becomes one of three indispensable components during
    Edda's failed search for a private solution, although the plan calls for it
    to appear before the crisis.
  - Why it matters: The late introduction makes the otherwise physical climax
    feel slightly constructed.
  - Smallest effective fix: Mention the manual spillwheel once during the
    first map scan or early east-stair routing.
- **Optional — the current-battle casualty count is slightly ambiguous.**
  - Location: original draft lines 180–183 and 573–577.
  - Evidence: The mesh reports one body, while the final log lists plural
    people who died.
  - Smallest effective fix: Use singular in the log, or seed additional deaths.

#### Canon-delta coverage

- The final delta should capture Copperwell and the Drouth League; the named
  cast; Edda's surge history; lattice provenance, records, permissions, limits,
  retention/discard behavior, and incident export; Common Cause; cistern
  infrastructure; current casualties and ceasefire; and the proposed civilian
  board. No invention is presently treated as promoted canon.

#### Required fixes

1. Preserve individual opt-in and data privacy consistently during Common
   Cause, including Harven's squad.
2. Seed the manual spillwheel before the crisis.
3. Make the current casualty count exact.

**Verdict: REVISE**

### Pass 2 — draft recheck

- Reviewed artifact: `03-draft.md`
- Review date: 2026-07-27
- Verdict: PASS
- Findings: 0 Critical, 0 Major, 0 Minor, 0 Optional
- Scope: Draft gate only; this does not certify `05-story.md`.

#### Canon

- No regression. The lattice remains local, technological, non-sentient,
  bounded, and fallible.

#### Continuity

- Individual opt-in and data privacy are resolved. Revised lines 346–352 limit
  pre-acceptance invitations to the objective and structural data; lines
  394–404 publish only structural maps, infrastructure locations, uncertainty,
  and costs; lines 408–415 show Sula, both workers, watch members, and League
  members accepting individually before appearing.
- Harven and the squad now withdraw and reaccept separately. Revised lines
  378–383 give each a separate withdrawal; lines 493–514 give the three squad
  members and Harven separate acceptances and positions. Harven remains the
  decisive final holdout without controlling anyone else's link.
- Timers, locations, pressure mechanics, injuries, and delegated actions
  remain coherent.

#### Names

- No new character-facing form or collision. All names and descriptive roles
  match the plan and `stories/NAMES.md`.

#### Causality and character

- The manual spillwheel is now established at revised lines 126–129 with its
  service history and lift-before-pulling remedy, then paid off causally at
  lines 367–371 and 493–545.
- The edits preserve individual agency and introduce no causal regression.

#### Prompt fulfillment

- The literal awakening sequence, concrete prior experience, Level 13 crisis
  use, voluntary coordination, and consequential resolution remain intact.

#### Pacing and prose

- Approximately 3,685 words, within contract. The added consent mechanics are
  clear and do not stall the climax.
- The casualty ledger is exact: revised line 187 establishes one current-battle
  body, and lines 589–593 record one person who died.

#### Canon-delta coverage

- No new coverage gap introduced. The Pass 1 inventory remains applicable to
  final editing.

#### Required fixes

- None. No unresolved Critical, Major, Minor, or Optional finding remains in
  `03-draft.md`.

**Verdict: PASS**

### Pass 3 — final-story review

- Reviewed artifact: `05-story.md`
- Companion artifact checked: `06-canon-delta.md`
- Review date: 2026-07-27
- Verdict: PASS
- Findings: 0 Critical, 0 Major, 1 Minor, 0 Optional
- Unresolved Critical or Major findings: None.

#### Canon

- Clear. The lattice remains local, bounded, technological, non-sentient,
  fallible, and unrelated to named eras, the Glass Gate, or other systems.

#### Continuity and editing regressions

- No editing regression. The final edit preserves the passed draft's consent
  protections, individual withdrawals and acceptances, early spillwheel setup,
  singular current casualty, pressure mechanics, clocks, injuries, and outcome.
- Chronology and object state are coherent. The eleven-minute cell limit,
  cascade windows, chamber seal, gate brace, spillwheel, beacon shadows,
  nineteen-second reserve, and post-stabilization export remain consistent.

#### Names

- Complete and collision-free. Final forms are `Edda Rook`/`Edda`, `Harven
  Coil`/`Harven`, and `Sula Brant`/`Sula`; no surname is used alone.
- `watch captain`, `League signal lead`, and `signal lead` remain descriptive
  roles. Interface and protocol terms never become personal aliases.

#### Causality and character

- Clear. Edda's prior experience, Sula's corrections and delegated timing,
  Harven's voluntary return, individual link control, fallible information,
  and coordinated physical work all remain causal.

#### Prompt fulfillment

- Complete. The literal awakening sequence, Combat Controller assignment,
  experience-based advancement to Level 13, bounded coordination ability,
  consequential choice, and complete immediate resolution are preserved.

#### Pacing and prose

- Approximately 3,688 words, within both budgets. Close-third past tense,
  tactical clarity, humane tone, Teen boundary, and complete resolution remain
  intact.
- YAML metadata is correct at `05-story.md` lines 1–7: matching title and slug,
  `status: candidate`, `canon: false`, and creation date.

#### Canon-delta coverage

- Otherwise comprehensive and accurately framed as local, non-canon, and
  pending approval. It captures the final names, factions, locations,
  mechanics, consent rules, costs, errors, current and historical deaths,
  ceasefire limits, incident log, and civilian-board proposal without implying
  promotion.
- **Minor — two plan-only descriptors appear in the delta.**
  - Location: `06-canon-delta.md` original lines 10–14 and 44–47.
  - Evidence: The delta calls Edda a former **chief** floodworks dispatcher and
    Copperwell a **basin** city. Those details appear in the plan but are not
    established in `05-story.md`.
  - Why it matters: Plan-only details should not be promoted through a delta
    that inventories final-story facts.
  - Smallest effective fix: Remove `chief` and `basin`, leaving “former
    floodworks dispatcher” and “city.” No prose revision is required.

#### Required fixes

- No Critical or Major fix. Remove the two unsupported delta descriptors before
  production reconciliation.

**Verdict: PASS**

### Pass 4 — final-story recheck

- Reviewed artifact: `05-story.md`
- Companion artifact checked: `06-canon-delta.md`
- Review date: 2026-07-27
- Verdict: PASS
- Findings: 0 Critical, 0 Major, 0 Minor, 0 Optional
- Unresolved Critical or Major findings: None.

#### Canon

- The descriptor correction introduces no regression. The delta remains
  explicitly local, non-canon, and pending approval.

#### Continuity and editing regressions

- `05-story.md` is unchanged from Pass 3 (SHA-256
  `04BE5FA6AFEB08E46AB1DDC02941F8DBBC18F317709D3545A4AB5095A1C88251`).
- Individual opt-in, data privacy, independent squad links, fallible inputs,
  spillwheel setup/payoff, resource limits, casualty ledger, and local
  resolution remain intact.

#### Names

- Final forms remain collision-free and consistent with `stories/NAMES.md`; no
  new alias or surname-only label appears.

#### Causality and character

- No change. The passed causal and agency chain remains intact.

#### Prompt fulfillment

- The awakening sequence, prior-experience advancement, Level 13 coordination,
  consequential choice, and complete resolution remain within contract.

#### Pacing and prose

- The final prose remains approximately 3,688 words and within the agreed
  3,200–3,800 final-edit budget.
- Candidate YAML metadata remains correct.

#### Canon-delta coverage

- The two plan-only descriptors are resolved: `06-canon-delta.md` now says
  “former floodworks dispatcher” and “city”; neither `chief` nor `basin`
  remains.
- Complete character, location, faction, mechanics, consent, costs, error,
  chronology, casualty, ceasefire, glossary, and name inventories remain
  present.

#### Required fixes

- None. No unresolved Critical, Major, Minor, or Optional finding remains.

**Verdict: PASS**

### Pass 5 — final-story migration certification

REVIEW_PASS_PAYLOAD

- story: `the-thirteenth-command`
- pass: 5
- reviewedArtifact: `05-story.md`
- artifactSha256: `dd13f8b5b832554af46bac3f1671fce6b774aef8be84dc87434cae2b0e7937f7`
- canonDeltaSha256: `e04689f8e9f9488bef29106dd698ca3b932b7fd0e27722302da1539e4ebfbd13`
- reviewer: primary_continuity_fallback
- reviewedAt: `2026-08-01T22:45:00-04:00`
- reviewBasis: Prior specialist draft/final PASS history; current universe
  LOCKED/CANON authority; the independent 17-story combined promotion audit;
  exact current final/delta bytes; and successful strict Final name receipt
  `14c8c0ee84a626009d07502b82e5814333e697ec8765d7b40568b0ebe2a33774`.
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

### Pass 6 — immutable-frontmatter migration certification

- Reviewed artifact: `05-story.md`
- Previous artifact SHA-256: `dd13f8b5b832554af46bac3f1671fce6b774aef8be84dc87434cae2b0e7937f7`
- Artifact SHA-256: `21a2190ca8a4caaf494646a1f4e9d5dcb1637143ea29a36d0352b834cd0facf0`
- Canon delta SHA-256: `e04689f8e9f9488bef29106dd698ca3b932b7fd0e27722302da1539e4ebfbd13`
- Review date: 2026-08-02T03:48:19.5150496+00:00
- Verdict: PASS
- Reviewer: primary_continuity_fallback
- Findings: 0 Critical, 0 Major, 0 Minor

#### Migration evidence

- Reconstructing the former frontmatter from current immutable identity fields
  plus the prior lifecycle values reproduces the prior release hash exactly:
  `dd13f8b5b832554af46bac3f1671fce6b774aef8be84dc87434cae2b0e7937f7`.
- The prose body beginning after the closing frontmatter delimiter is byte-for-byte
  unchanged. `06-canon-delta.md` is also unchanged at `e04689f8e9f9488bef29106dd698ca3b932b7fd0e27722302da1539e4ebfbd13`.
- The only story-byte change removes `status`, `canon`, `userDisposition`,
  `publish`, and `promotionDate` from frontmatter. Those mutable fields remain
  authoritative in `story.json` and checked projections.

#### Required fixes

- None.
