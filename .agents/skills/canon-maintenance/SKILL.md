---
name: canon-maintenance
description: "Promote one explicitly approved, release-certified story after a current-authority recheck, with per-delta dispositions and provenance. Never infer approval or batch transactions."
---

# Canon maintenance

Canon promotion is one controlled, named-story transaction. Never batch
promotions: each successful promotion changes the authority used to vet the
next story.

## Authorization and write ownership

Require explicit user approval for the exact story slug. Approval to promote a
set is executed as separate ordered transactions; approval to promote does not
authorize a retcon.

Direct lifecycle finalization is forbidden. The primary must persist a
schema-version-1 `stories/<slug>/promotion.json` for the exact slug and
promotion date before invoking the finalizer. The scaffold's `not-prepared`
manifest is deliberately inert. A `ready` manifest is the executable
authorization boundary: it records the exact user-approval reference, the raw
stewardship handoff and its UTF-8 SHA-256, current-authority manifest, certified
candidate bundle, complete stable delta inventory and dispositions, verified
universe pre/post images, and any separately authorized retcon evidence.
Its normative schema is
`.agents/skills/canon-maintenance/schemas/promotion.schema.json`; do not infer
or relax fields from an example manifest.

Ownership remains consistent throughout promotion:

- `canon_steward` may write only affected `universe/*.md` files and
  `universe/retcons.md` for a separately explicit approved retcon. It returns a
  `STEWARDSHIP_HANDOFF`; it never edits story or central production records.
- The primary coordinator owns `story.json`, `release.json` through the issuer,
  the story README, the one index row, and only the named story's registry rows.
  It verifies the handoff and performs finalization.

Neither role edits `00-prompt.md` through `06-canon-delta.md`, another story,
archived source snapshots, templates, scripts, or publication code. Promotion
never mutates reviewed story bytes merely to change frontmatter.

The primary alone writes `promotion.json`. The steward returns the raw handoff
payload; it does not persist or complete the manifest. Preserve that payload
byte-for-byte as `stewardship.handoffText`, identify the role in
`stewardship.identity`, and hash the UTF-8 payload bytes into
`stewardship.handoffSha256`. Never manufacture a handoff on the steward's
behalf.

Immediately before stewardship, generate and verify the story-scoped authority
record with:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1 -Story <slug> -OutputFormat Json
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1 -Story <slug> -Verify -OutputFormat Json
```

Require the candidate release provenance to bind that exact raw
`authority.json` hash. Store its project-relative path, raw-file SHA-256, and
internal `authoritySetSha256` in the promotion manifest. The handoff field
`authorityManifestSha256` is the raw `authority.json` hash, not the internal set
digest or the promotion transaction-inventory digest.

## Release-bundle preflight

1. Read `story.json`, `release.json`, all of `04-review.md`, `05-story.md`,
   `06-canon-delta.md`, `universe/README.md`, the current index and registry,
   every affected universe file, and relevant stories only when their index row
   says canon `yes` and `story.json` says `canon: true`, with those records
   agreeing.
2. Require `story.json` to identify the same slug and an eligible candidate
   state. Require `release.json.schemaVersion` supported by the repository,
   `certified: true`, and the same `storySlug`.
3. Require `release.json.artifacts.story.path` to be `05-story.md` and
   `release.json.artifacts.canonDelta.path` to be `06-canon-delta.md`.
   Recompute raw-byte lowercase SHA-256 for both files and require them to match
   the corresponding nested `sha256` values.
4. Verify `release.json.review` names `05-story.md`, matches the latest current
   certification in `04-review.md`, records `PASS`, and records zero unresolved
   Critical and Major findings. Require the certification's exact `Artifact
   SHA-256` and `Canon delta SHA-256` values to match `release.json.artifacts`;
   a verdict without
   matching review hashes does not certify the bytes.
5. Run
   `pwsh -NoProfile -File
   .agents/skills/story-name-validation/scripts/check-story-names.ps1 -Story
   <slug> -Phase Final -OutputFormat Json`. Require its story-scoped
   JSON receipt to name this slug, report `phase: Final` and `passed: true`, have
   `storySha256` and `canonDeltaSha256` matching the release artifacts, and have
   a current `scopedRegistrySha256`; update the release receipt only as part of
   a complete re-certification.
6. Recheck the story and every proposed delta item against the authority that
   exists now, including promotions made after the original canon brief. If
   authority has changed in a way that needs story or delta edits, stop and send
   the story through final edit, final review, final name validation, and release
   certification again. Do not certify stale bytes.

Any failed hash, review, name, metadata, or current-authority check yields no
writes. A contradiction that would change established canon yields
`USER_RULING_REQUIRED`; never disguise a retcon as cleanup.

## Delta decisions and atomic promotion

Give every concrete item in `06-canon-delta.md` a stable identifier and exactly
one disposition:

- `promote` — add the reusable fact to a named universe heading;
- `story-local` — valid color that remains in the story only;
- `defer` — potentially reusable, but awaiting evidence or a later decision;
- `reject` — contradicted, unsuitable, or explicitly declined.

Record a rationale for every disposition and a target for every promoted item.
Add provenance in the form `First established:
stories/<slug>/05-story.md`. For a separately approved retcon, record date, old
fact, new fact, reason, and approval source in `universe/retcons.md`.

Before delegation, the primary populates the manifest's current-authority
inventory with every Markdown file below `universe/`, `stories/INDEX.md`, and
`story.json` plus `05-story.md` for every story currently classified canon by
both records. Sort the project-relative paths ordinally. Hash each raw file as
lowercase SHA-256, serialize each record as `<path><TAB><sha256><LF>`, and hash
that UTF-8 record stream into `authority.manifestSha256`. Record its exact item
count. This additional transaction inventory binds `stories/INDEX.md` and the
raw classification records used for compare-and-swap; it does not replace the
persisted story-scoped `authority.json`. For each possible steward target,
retain the raw pre-transaction bytes; the ready manifest stores those bytes as
Base64 plus their SHA-256. The
finalizer reconstructs this pre-steward authority view even though approved
universe post-images are already present.

The stable disposition digest uses the same ordinal/LF rule, one record per
item: `<id><TAB><disposition><TAB><target-or-none><TAB><rationale><LF>`. Record
the count and digest in `deltaInventory`, and bind it to the current raw
`06-canon-delta.md` hash. Every `promote` ID must appear exactly once in the
`deltaIds` of the universe file it targets. Non-promote items have a null
target. An empty inventory is allowed only when the delta contains no concrete
items; it uses the SHA-256 of the empty byte stream.

Before delegation, the primary captures the exact pre-transaction bytes of
every possible universe and production target. After all preflight and delta
decisions succeed, the steward applies only approved universe facts and returns
`STEWARDSHIP_HANDOFF` with pre/post hashes, every delta disposition, and the
required primary writes. The primary verifies that handoff, persists the
schema-valid ready manifest, and does not revise its facts. A
`CANON_APPLIED_AWAITING_PRIMARY` result is not yet a completed promotion.

Do not hand-edit the lifecycle records. After the steward's universe changes
and the ready manifest are both persisted, the primary invokes the sole
finalization entry point:

```powershell
pwsh -NoProfile -File .agents/skills/canon-maintenance/scripts/Complete-CanonPromotion.ps1 -Story <slug> -PromotionDate <YYYY-MM-DD>
```

The script schema-validates the exact story's persisted manifest, rechecks its
authorization and raw handoff digest, verifies the candidate release/story/
delta bytes, reconstructs the current-authority digest, and verifies every
universe file is at the declared steward post-image with a valid rollback
pre-image. It uses compare-and-swap before every production mutation. It then
updates `story.json` to stage/status `final`, `canon: true`, accepted
disposition and promotion date; updates the production README, the one index
row, and only this story's registry rows; and preserves publish state.
Archived-source provenance remains solely in the source archive and never
classifies this production story.

The finalizer regenerates and verifies `authority.json` after the lifecycle,
index, and universe state make the story canon, then reissues the now-final
bundle so changed authority and scoped registry rows are re-certified. It
completes `promotion.json` as durable, content-bound transaction provenance,
then runs both validators:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-StoryRelease.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
```

Never hand-edit release hashes or set `certified` true. If manifest/handoff
verification, primary writes, issuance, or either validator fails after the
steward transaction can be safely identified, the finalizer restores every
captured universe and production transaction file, including steward-written
universe files, the ready manifest, and candidate `release.json`, and reports
`NO_CHANGES`; do not leave a partial promotion. A malformed, missing, stale, or
wrong-story manifest authorizes no write. A promotion is successful only after
all files agree, both validators exit zero, and `promotion.json.state` is
`completed` with candidate/final release hashes, pre/post authority digests,
the authorization and handoff identity, the modified paths, and a transaction
digest.

The steward finishes its phase with exactly:

```text
STEWARDSHIP_HANDOFF
story: <slug>
authorization: <approval reference>
steward: <stable steward identity>
candidateRelease: <VERIFIED|FAILED>
candidateReleaseSha256: <lowercase raw-byte SHA-256>
authorityRecheck: <PASS|USER_RULING_REQUIRED|FAILED>
authorityManifestSha256: <lowercase raw authority.json SHA-256>
resolutionQuestion: <none|exact user question>
nameCheckReceipt: <VERIFIED|FAILED>
storySha256: <lowercase raw-byte SHA-256>
canonDeltaSha256: <lowercase raw-byte SHA-256>
deltaDispositionsSha256: <lowercase canonical disposition-manifest SHA-256>
retconEvidenceSha256: <none|lowercase UTF-8 evidence SHA-256>
modifiedCanonFiles: <paths plus pre/post sha256, or none>
deltaDispositions: <every stable item id, disposition, target, and rationale>
retcon: <none|approved retcon record>
primaryWritesRequired: <exact production records, release, and validators>
result: <CANON_APPLIED_AWAITING_PRIMARY|NO_CANON_CHANGES_AWAITING_PRIMARY|NO_CHANGES>
```

Only after primary finalization and validation, the primary finishes with:

```text
PROMOTION_CHANGE_REPORT
story: <slug>
authorization: <concise user-approval reference>
releaseBundle: <VERIFIED|FAILED>
authorityRecheck: <PASS|USER_RULING_REQUIRED|FAILED>
resolutionQuestion: <none|exact user question>
nameCheckReceipt: <VERIFIED|FAILED>
stewardshipHandoff: <VERIFIED|FAILED>
modifiedFiles: <complete canon and production path list or none>
deltaDispositions: <every stable item id, disposition, target, and rationale>
retcon: <none|approved retcon record>
result: <PROMOTED|NO_CHANGES>
```
