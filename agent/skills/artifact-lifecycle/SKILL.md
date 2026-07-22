---
name: artifact-lifecycle
description: Inspect, edit, and regenerate immutable story artifacts using exact versions, hashes, JSON Patch, and transitive invalidation.
---

# Artifact Lifecycle

Use this skill for artifact inspection, writer edits, and regeneration.

- Resolve an artifact by exact UUID and verify that it is active.
- For edits, require the current SHA-256 hash and RFC 6902 operations under `/content`.
- Call `patch_story_artifact`; do not hand-edit, overwrite, or mutate an envelope.
- Report the replacement ID/hash and new run status.
- Do not trigger model work automatically after an edit.
- On explicit regeneration, call `regenerate_from_artifact` and rebuild only invalidated descendants.
- Preserve superseded and stale artifacts indefinitely.
- Treat human-edited reviews as commentary that must be replaced by a fresh critic review before promotion.

Committed canon, provenance, execution records, and rendered exports are immutable.
