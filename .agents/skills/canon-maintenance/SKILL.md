---
name: canon-maintenance
description: "Promote one explicitly approved story after a current-authority recheck, with complete delta dispositions, local scope, provenance, and transactional rollback."
---

# Canon maintenance

Promote one named story per transaction. Require the user's explicit authorization; promotion authority does not imply retcon authority.

## Preconditions

- Work on a non-`main` branch from current `main`.
- The story is a certified pipeline candidate, or an explicitly listed legacy correction authorized by the user.
- The newest final review is `PASS` with zero unresolved Critical/Major findings.
- Strict final names pass.
- Current `LOCKED` and `CANON` entries have been rechecked.
- Every concrete `06-canon-delta.md` item has a stable ID, disposition, target, rationale, and local-scope note.

Any conflict with `LOCKED` authority stops before writing and returns one precise question. Never infer a retcon.

## Ownership

The `canon_steward` may edit only the authorized topical `universe/*.md` files. It promotes facts into the smallest appropriate entries, preserves limitations and local qualifiers, and cites `stories/<slug>/05-story.md` as provenance. The steward returns the exact `STEWARDSHIP_HANDOFF` and never edits story records, registry, index, release, or promotion metadata.

The coordinator captures raw preimages for rollback, validates the changed-path allowlist, persists `promotion.json` v2, updates lifecycle projections and names transactionally, and runs full validation.

## Steward report

Return:

```text
STEWARDSHIP_HANDOFF
story: <slug>
authorization: <user approval reference>
steward: canon_steward
candidateRelease: VERIFIED | FAILED
authorityRecheck: PASS | USER_RULING_REQUIRED | FAILED
resolutionQuestion: none | <question>
nameCheck: VERIFIED | FAILED
modifiedFiles: <comma-separated repository paths or none>
deltaDispositions: <complete ordered JSON array>
changeReport: <precise summary>
END_STEWARDSHIP_HANDOFF
```

The coordinator stores this text verbatim in `promotion.json`. A ready promotion records explicit authorization, steward identity/report, complete dispositions, modified files, promotion date, and rollback state. Standard pipeline promotion completes through `Complete-CanonPromotion.ps1`. A successful transaction ends with `state: completed` and `result: PROMOTED`.
