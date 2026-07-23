---
name: canon-maintenance
description: "Promote an explicitly approved, final-reviewed story and its canon delta into the shared-universe notes with provenance. Never infer approval or promote drafts or unreviewed prose."
---

# Canon maintenance

Canon promotion is a controlled write operation.

1. Confirm explicit user approval and identify one story directory whose final
   story is approved for promotion.
2. Read `04-review.md`, `05-story.md`, `06-canon-delta.md`,
   `universe/README.md`, `stories/NAMES.md`, all affected universe files, and
   the story row in `stories/INDEX.md`.
3. Require the latest review certification to identify `05-story.md` and have
   verdict `PASS` with no unresolved Critical or Major findings. A reviewed
   candidate is eligible for explicit promotion; a draft or unreviewed
   candidate is not.
4. Check each proposed fact for duplicates, aliases, ambiguity, and conflict.
   Confirm every promoted character-facing name is registered and any repeated
   name has an explicit meaningful-reuse rationale.
5. If a contradiction requires changing existing canon, stop for a specific
   ruling. Never disguise a retcon as cleanup.
6. Add only reusable facts. Preserve story-only color in the story.
7. Add provenance in the form `First established: stories/<slug>/05-story.md`.
8. If an approved change supersedes canon, record it in `universe/retcons.md`
   with date, old fact, new fact, reason, and approval source.
9. Set the final story frontmatter to `status: final` and `canon: true`; update
   its production record and index row to status `final`, canon `yes`, and
   today's promotion date.
10. Update the story's entries in `stories/NAMES.md` from `candidate` to
    `canon`, preserve provenance and reuse rationale, and run
    `./scripts/check-story-names.ps1 -Story <slug>`.

Finish by listing every modified canon section and any delta item deliberately
left unpromoted.
