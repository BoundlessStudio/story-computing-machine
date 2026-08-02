---
name: story-name-validation
description: "Validate and reconcile character-facing names in stories/NAMES.md for story production or canon promotion, including aliases, collisions, and deliberate-reuse documentation."
---

# Story name validation

Use this shared workflow when a story plan is ready for name registration, when
final prose and its canon delta must be reconciled, or when an approved
candidate's registry entries are promoted to canon.

## Ownership and inputs

1. Read `AGENTS.md` — **Character-name discipline**, `stories/NAMES.md`, and the
   target story's current `story.json`, `02-story-plan.md`, `05-story.md`, and
   `06-canon-delta.md` as applicable to the requested phase.
2. During story production, only the primary story-room coordinator edits
   `stories/NAMES.md`; specialist agents report name decisions instead.
3. During explicitly approved canon promotion, the primary coordinator still
   owns the named story's registry state. The `canon_steward` reports the
   required change in `STEWARDSHIP_HANDOFF` but does not edit the registry.

## Reconcile and validate

1. Inventory every character-facing full name, shortened form, alias, nickname,
   title used as a name, and named animal or person-like entity.
2. Check exact matches, aliases, close spellings, reversals, and easily confused
   forms across all rows in `stories/NAMES.md`, using the same rules for every
   production-story lifecycle state.
3. Prefer a unique name. Permit reuse only when the plan and registry both
   document the identities, intentional meaning, and reader-disambiguation
   strategy required by `AGENTS.md`. Every one of the plan's four `Name check`
   columns is required. A target-touching exact, punctuation/spacing-confusable,
   reversed, or close-spelling collision fails unless every participating
   registry identity is marked `deliberate` and the target plan row independently
   documents that deliberate reuse. A target `unresolved` row always fails.
4. At the authorized stage, reconcile the target story's registry rows with its
   plan or final story and canon delta. Do not remove unrelated or abandoned
   reservations.
5. Run the exact phase-appropriate command:

   ```powershell
   pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 -Story <slug> -Phase Plan -OutputFormat Json
   ```

   or:

   ```powershell
   pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 -Story <slug> -Phase Final -OutputFormat Json
   ```

6. Treat a story-scoped collision or unregistered final-delta character as a
   failure. Report unrelated global warnings, but do not misattribute them to
   the target story. Use `-Strict` only for an explicitly requested
   registry-wide cleanup. `-SkipConfusable` is a global diagnostic option and
   is rejected by every story-scoped gate.
7. During Final validation, reconcile the explicit inventory with the
   independent prose-derived candidate audit. The checker strips frontmatter,
   headings, comments, and known inventoried forms before conservatively
   extracting character-like capitalized or label forms. Every extracted form
   must be inventoried and registered, or appear in the exact three-column
   `Reviewed prose name-audit allowlist` in `06-canon-delta.md` with an allowed
   classification and a human review rationale. Never use the allowlist to
   excuse a character-facing name.

## Receipts are gates

Success requires both process exit code 0 and parseable schema-version-1 JSON
with `checkerVersion: story-names/2`, `receiptId`, the requested `story`, exact
`phase: Plan | Final`, `passed: true`, `checkedAt`, `warnings`,
`scopedRegistrySha256` over the script's canonical scoped rows, and
`activeRegistrySha256` over every active comparison row. Plan receipts must
include the current raw-byte lowercase `planSha256`. Final receipts must include
the current raw-byte lowercase `storySha256` and `canonDeltaSha256`. The receipt
also includes and binds `planSha256` when deliberate collision evidence is read
from the plan. The receipt ID binds the checker version, phase, artifact
digest(s), scoped registry digest,
whole-active-registry digest, and sorted warnings. Capture the exact JSON as the
name-check receipt; prose may not begin on a console summary, uncaptured exit code, failed
receipt, mismatched slug, stale artifact hash, or stale registry hash.

The Plan receipt is handed to `prose_writer`. The Final receipt is embedded in
`release.json.nameCheck` only after final prose and the canon delta are stable.
It must contain `story`, `passed`, `checkedAt`, and
`scopedRegistrySha256` matching current rows; its story and delta hashes must
also match the artifact entries in the release bundle.

If final reconciliation discovers a missing, colliding, or inconsistent name,
repair the appropriate final artifact/inventory and registry, invalidate the
current final certification and release bundle, rerun the final review, then
rerun Final name validation. A repair found after final review never bypasses
that review loop.

The registry is production memory, not canon. Passing this validation does not
promote a story or establish any identity in the shared universe.
