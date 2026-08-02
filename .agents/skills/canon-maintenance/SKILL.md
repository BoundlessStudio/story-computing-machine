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

Before delegation, the primary captures the exact pre-transaction bytes of
every possible universe and production target. After all preflight and delta
decisions succeed, the steward applies only approved universe facts and returns
`STEWARDSHIP_HANDOFF` with pre/post hashes, every delta disposition, and the
required primary writes. `CANON_APPLIED_AWAITING_PRIMARY` is not yet a completed
promotion.

The primary verifies that handoff and then updates `story.json` to stage/status
`final`, `canon: true`, accepted disposition and promotion date; updates the
production README, the one index row, and only this story's registry rows; and
preserves publish state. Archived-source provenance remains solely in the
source archive and never classifies this production story.

The primary reissues the now-final bundle so changed scoped registry rows are
re-certified, then runs both validators:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-StoryRelease.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
```

Never hand-edit release hashes or set `certified` true. If handoff verification,
primary writes, issuance, or either validator fails, the primary restores every
captured pre-transaction file, including steward-written universe files and the
candidate `release.json`, and reports `NO_CHANGES`; do not leave a partial
promotion. A promotion is successful only after all files agree and both
validators exit zero.

The steward finishes its phase with exactly:

```text
STEWARDSHIP_HANDOFF
story: <slug>
authorization: <approval reference>
candidateRelease: <VERIFIED|FAILED>
authorityRecheck: <PASS|USER_RULING_REQUIRED|FAILED>
resolutionQuestion: <none|exact user question>
nameCheckReceipt: <VERIFIED|FAILED>
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
