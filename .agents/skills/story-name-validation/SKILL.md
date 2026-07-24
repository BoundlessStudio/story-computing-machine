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
   target story's current `02-story-plan.md`, `05-story.md`, and
   `06-canon-delta.md` as applicable to the current stage.
2. During story production, only the primary story-room coordinator edits
   `stories/NAMES.md`; specialist agents report name decisions instead.
3. During explicitly approved canon promotion, the `canon_steward` may update
   the named story's registry state as authorized by `canon-maintenance`.

## Reconcile and validate

1. Inventory every character-facing full name, shortened form, alias, nickname,
   title used as a name, and named animal or person-like entity.
2. Check exact matches, aliases, close spellings, reversals, and easily confused
   forms across canon, candidates, in-progress stories, and portable legacy
   sources.
3. Prefer a unique name. Permit reuse only when the plan and registry both
   document the identities, intentional meaning, and reader-disambiguation
   strategy required by `AGENTS.md`.
4. At the authorized stage, reconcile the target story's registry rows with its
   plan or final story and canon delta. Do not remove unrelated, legacy, or
   abandoned reservations.
5. Run
   `.agents/skills/story-name-validation/scripts/check-story-names.ps1` with
   `-Story <slug>`.
6. Treat a story-scoped collision or unregistered final-delta character as a
   failure. Report unrelated global warnings, but do not misattribute them to
   the target story. Use `-Strict` only for an explicitly requested
   registry-wide cleanup.

The registry is production memory, not canon. Passing this validation does not
promote a story or establish any identity in the shared universe.
