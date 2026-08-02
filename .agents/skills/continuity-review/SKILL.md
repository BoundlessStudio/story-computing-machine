---
name: continuity-review
description: "Review a draft or final story for canon, chronology, causality, prompt fulfillment, pacing, prose readiness, and name issues without silently rewriting it."
---

# Continuity review

Use `REVIEW_DRAFT` for `03-draft.md` or `REVIEW_FINAL` for `05-story.md`. This role is read-only. Require current prompt, brief, plan, authority inventory, handoff ledger, registry, reviewed artifact, and final delta when reviewing final prose.

Return exactly one canonical 20-field JSON payload between `REVIEW_PASS_PAYLOAD` markers, using `schemas/pipeline-contract.json`. Findings have stable IDs, severity, location, evidence, required resolution, and owner. Preserve prior finding dispositions.

Verdicts:

- `PASS`: prompt fulfilled; no unresolved Critical/Major findings; ready for the next gate.
- `REVISE`: production artifacts can resolve the findings without new authority.
- `BLOCK`: canon ruling, retcon, material prompt reinterpretation, or missing required input prevents safe progress.

Do not rewrite prose or persist the review. The coordinator appends the returned payload verbatim and updates the current certification summary.
