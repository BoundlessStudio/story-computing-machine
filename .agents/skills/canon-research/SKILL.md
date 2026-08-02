---
name: canon-research
description: "Research and vet a story idea against current shared-universe authority without inventing missing canon."
---

# Canon research

Use before planning or when investigating continuity. Read `universe/README.md`, the story prompt, `story.json`, current `authority.json`, admitted canon stories, and relevant source records.

Treat only current `LOCKED`/`CANON` universe entries and admitted final canon stories as authority. `PROVISIONAL`, evidence, drafts, reviews, plans, and proposed deltas are nonbinding.

Return an evidence-backed `01-canon-brief.md` payload containing hard constraints, useful context, conflicts, unknowns, safe local invention space, name constraints, required later checks, and exact source paths/headings. Distinguish a contradiction from an omission. Missing lore is not evidence for a new global rule.

If authority conflicts or a user ruling is required, return that state without inventing an answer. This role is read-only; the coordinator persists the exact report inside the open handoff.
