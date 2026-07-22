---
name: canon-promotion
description: Finalize, promote, and export a reviewed outline without bypassing exact-hash canon and review gates.
---

# Canon Promotion and Export

Use this skill when finalizing, promoting, or exporting an outline.

1. Confirm the active `outline.final` belongs to the run and is pinned to the current shared-world revision.
2. Require active agent-authored `review.continuity`, `review.narrative`, and `review.theme-pacing` artifacts targeting its exact ID and hash with `pass` verdicts.
3. Call `finalize_outline` to validate canon references, scene structure, setup/payoff links, state transitions, and the proposed delta.
4. Wait for a separate explicit writer instruction before calling `promote_outline`.
5. Never auto-rebase a stale run.
6. Use `render_writer_packet` for Markdown; do not compose or edit the export manually.

Only promotion makes a story visible to future runs.
