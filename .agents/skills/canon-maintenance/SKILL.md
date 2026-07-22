---
name: canon-maintenance
description: "Promote an explicitly approved final story and its canon delta into the shared-universe notes with provenance. Use only after the user clearly approves canon promotion; never use on drafts or candidate stories."
---

# Canon maintenance

Canon promotion is a controlled write operation.

1. Confirm explicit user approval and identify one final story directory.
2. Read `05-story.md`, `06-canon-delta.md`, `universe/README.md`, all affected
   universe files, and relevant canon-story rows in `stories/INDEX.md`.
3. Check each proposed fact for duplicates, aliases, ambiguity, and conflict.
4. If a contradiction requires changing existing canon, stop for a specific
   ruling. Never disguise a retcon as cleanup.
5. Add only reusable facts. Preserve story-only color in the story.
6. Add provenance in the form `First established: stories/<slug>/05-story.md`.
7. If an approved change supersedes canon, record it in `universe/retcons.md`
   with date, old fact, new fact, reason, and approval source.
8. Set the final story frontmatter to `status: final` and `canon: true`; update
   its index row to status `final`, canon `yes`, and today's promotion date.

Finish by listing every modified canon section and any delta item deliberately
left unpromoted.
