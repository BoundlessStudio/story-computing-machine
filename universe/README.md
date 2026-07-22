# Shared-universe notes

This directory is the setting's authoritative reference. It begins deliberately
empty: headings and examples are templates, not facts.

## Authority order

When sources disagree, use this order:

1. Entries marked `LOCKED` in this directory.
2. Entries marked `CANON` in this directory.
3. Final stories whose row in `stories/INDEX.md` says canon `yes`.
4. Entries marked `PROVISIONAL`, which are guidance but may change.
5. Open questions, story plans, drafts, reviews, and canon deltas, which are not
   canon.

Never silently reconcile two authoritative sources. Record the conflict and ask
for a ruling. An approved correction or retcon belongs in `retcons.md`.

## Entry format

Use this shape in the topical files:

```markdown
## Name

- Status: LOCKED | CANON | PROVISIONAL | RETIRED
- Summary: One precise statement.
- First established: user decision, date, or stories/<slug>/05-story.md
- Aliases: None
- Notes: Costs, exceptions, relationships, or boundaries.
```

`LOCKED` means stories may not contradict the entry without an explicit user
retcon. `CANON` is established but can be deliberately expanded. `PROVISIONAL`
is a design direction. `RETIRED` is retained only for historical traceability.

## Files

- `premise.md` — foundational truths, themes, genre, cosmology.
- `rules.md` — magic, technology, biology, economics, and their costs.
- `timeline.md` — dated or ordered events.
- `characters.md` — recurring people and relationships.
- `locations.md` — geography and recurring places.
- `factions.md` — organizations, cultures, powers, and agendas.
- `glossary.md` — canonical terms, spellings, and aliases.
- `style-guide.md` — narrative tone and content boundaries for this universe.
- `open-questions.md` — deliberately unresolved matters; not canon answers.
- `retcons.md` — approved changes to previously authoritative facts.
