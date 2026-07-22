---
name: story-room-orchestration
description: Run the fixed prompt-to-pitches and selected-pitch-to-outline story room while preserving branch isolation and artifact lineage.
---

# Story Room Orchestration

Use this skill when starting, resuming, or regenerating a story run.

1. Pin the run with `begin_story`; use the returned snapshot artifact throughout.
2. Persist every subagent result before any downstream call.
3. Supply artifact envelopes verbatim and cite every input as a lineage parent.
4. Keep pitch branches A, B, and C isolated until `story_editor` creates the slate.
5. Extract content from wrapper outputs exactly as described in the root instructions.
6. Use `/scenes` logical keys for pre-revision reviews and `/final` keys for reviews of `outline.final`.
7. Call `finalize_outline` only after three final reviews target the exact final artifact ID and hash.
8. After a writer clarification, supersede only the brief, keep the snapshot-derived dossier active, then rerun canon preflight sequentially. The clarification is an input rooted in the original prompt, not a descendant of the stale conflict report.

Never synthesize creatively in the root, skip persistence, or select a pitch on the writer's behalf.
