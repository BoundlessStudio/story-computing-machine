# Legacy story sources and development archive

This support directory preserves non-canon source provenance, research,
adaptation questions, and historical decisions. It is not a story directory and
does not use the numbered production artifacts in `stories/_template/`.

- `2026-07-22-universe-grill.md` is the complete historical grill: source
  survey, answered rulings, deferred adaptation decisions, rejected or
  not-applicable branches, collisions, and creative possibilities.
- `MANIFEST.md` is the portable inventory of external legacy source versions.

The grill is provenance, not an authority layer. Its promoted global rulings
are expressed in the topical files under `universe/`; those `LOCKED` and `CANON`
entries govern if summary wording differs. Deferred and not-applicable material
remains non-canon.

## Import rule

Before a legacy work is adapted, quoted, or relied on for a reproducible canon
decision, make the exact reviewed version available to collaborators in one of
these ways:

1. Add an approved snapshot beneath `stories/_legacy/imports/<source-id>/` and
   record its repository-relative path and SHA-256 digest in `MANIFEST.md`.
2. If the text cannot be stored in the repository, record a stable controlled-
   archive locator, version date, SHA-256 digest, and access requirements in the
   manifest.

Until one of those steps is complete, the manifest entry remains `external` and
prior research is an audit record rather than independently reproducible source
evidence. Importing a file never promotes its contents to canon.
