---
name: canon-research
description: "Research and vet a story idea against this repository's shared-universe canon. Use before outlining, during continuity investigation, or when asked whether an idea contradicts established lore; do not invent missing canon."
---

# Canon research

1. Read `universe/README.md` for authority and status rules.
2. Search all Markdown files under `universe/` for prompt entities, concepts,
   places, dates, factions, technologies, powers, and thematic constraints.
3. Check `stories/INDEX.md`. Consult `05-story.md` only for rows explicitly
   marked canon `yes`, and only when relevant.
4. Trace names and aliases through `universe/glossary.md` before declaring an
   apparent mismatch.
5. Never infer that a missing fact is established. Label it `Unknown` and state
   whether a local invention appears safe.

Produce these sections:

- `Hard constraints` — locked or canon facts the story must obey.
- `Useful established context` — canon that can enrich the story.
- `Conflicts or ambiguity` — incompatible sources or unclear precedence.
- `Unknowns` — unanswered matters that should not be stated as canon.
- `Safe invention space` — narrow additions that do not alter global rules.
- `Required checks after drafting` — continuity risks to search for.
- `Sources` — repository-relative file paths plus heading names.

If sources conflict, do not select a winner. Return `BLOCKED ON CANON RULING`
when the story cannot proceed without resolving the conflict.
