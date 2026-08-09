# Shared-universe notes

This directory is the sole authority for shared-universe facts. Stories provide
evidence and examples, but a fact becomes reusable canon only when it is written
into the relevant topical file here.

## Authority order

When sources disagree, use this order:

1. Entries marked `LOCKED`.
2. Entries marked `CANON`.
3. Entries marked `PROVISIONAL`, as nonbinding guidance.
4. Everything else, including prompts, outlines, stories, reviews, source notes,
   and retired pipeline records.

Never silently reconcile conflicting authoritative entries. Ask the user for a
ruling and record an approved correction in `retcons.md`.

## Entry format

```markdown
## Name

- Status: LOCKED | CANON | PROVISIONAL | RETIRED
- Summary: One precise statement.
- First established: user decision, date, or story path.
- Aliases: None
- Notes: Costs, exceptions, relationships, or boundaries.
```

`LOCKED` requires an explicit user retcon to contradict. `CANON` is
established but may be deliberately expanded. `PROVISIONAL` is design
guidance. `RETIRED` is retained only for historical traceability.

## Files

- `premise.md` — foundational truths, themes, genre, and cosmology.
- `rules.md` — magic, technology, biology, economics, and costs.
- `timeline.md` — dated or ordered events.
- `characters.md` — recurring people and relationships.
- `locations.md` — geography and recurring places.
- `factions.md` — organizations, cultures, powers, and agendas.
- `glossary.md` — canonical terms, spellings, and aliases.
- `style-guide.md` — narrative craft, tone, and content boundaries.
- `retcons.md` — approved changes to authoritative facts.

The initial decision record remains in
`sources/decisions/2026-07-22-universe-grill.md` as provenance only.
`stories/NAMES.md` is the frozen people-name baseline for locked legacy
stories; current stories inventory people and places in their own `review.md`.
