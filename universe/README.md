# Shared-universe notes

This directory is the setting's authoritative reference. Only current entries
marked `LOCKED` or `CANON`, plus release-valid promoted stories whose
`story.json` and checked index row agree, establish current setting facts.
`PROVISIONAL` is nonbinding design guidance and `RETIRED` is history only.

## Authority order

When sources disagree, use this order:

1. Entries marked `LOCKED` in this directory.
2. Entries marked `CANON` in this directory.
3. Release-valid final stories whose `story.json` says `status: final` and
   `canon: true`, and whose checked `stories/INDEX.md` row agrees. `story.json`
   is the machine authority; the index is a validated projection.
4. Entries marked `PROVISIONAL`, which are guidance but may change.
5. All other materials, including decisions, open questions, story plans,
   drafts, reviews, and canon deltas, which are not canon unless promoted into
   a topical entry above.

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
is a nonbinding design direction and does not establish a fact. `RETIRED` is
retained only for historical traceability and is not current authority.

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
`sources/decisions/2026-07-22-universe-grill.md`. It records provenance only
and does not override topical `LOCKED` or `CANON` entries.

`stories/NAMES.md` is persistent production memory for character-name use
across every production-story lifecycle state. It prevents accidental reuse
but does not establish that a listed character or name is canon.
