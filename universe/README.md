# Shared-universe notes

This directory is the setting's authoritative reference. Only entries carrying
the statuses defined below establish setting or production facts.

## Authority order

When sources disagree, use this order:

1. Entries marked `LOCKED` in this directory.
2. Entries marked `CANON` in this directory.
3. Final stories whose row in `stories/INDEX.md` says canon `yes`.
4. Entries marked `PROVISIONAL`, which are guidance but may change.
5. Archived decisions, open questions, story plans, drafts, reviews, and canon
   deltas, which are not canon unless promoted into a topical entry above.

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
- `retcons.md` — approved changes to previously authoritative facts.

The complete initial decision and source-research record is preserved at
`stories/_legacy/2026-07-22-universe-grill.md`. It supplies provenance and
adaptation backlog but does not override topical `LOCKED` or `CANON` entries.

`stories/NAMES.md` is persistent production memory for character-name use
across canon, candidates, in-progress work, and legacy sources. It prevents
accidental reuse but does not establish that a listed character or name is
canon.
