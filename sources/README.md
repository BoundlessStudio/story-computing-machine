# Evidence records

This directory preserves inert evidence and decision history so the repository
is self-contained. Every record has `authority: none`. Nothing here is a
production story, lifecycle state, naming reservation, publication source, or
canon authority. All production stories use the workflow and metadata defined
under `stories/`.

- `MANIFEST.json` is the machine-readable path and digest inventory. `sha256`
  binds current bytes; `reviewedSha256` preserves the originally reviewed byte
  digest when historical line endings differed.
- `MANIFEST.md` is its human-readable companion.
- `decisions/` preserves research and user rulings as history.
- `records/` contains exact snapshots.
- `externalRecords` in the JSON manifest preserves descriptive locators for
  evidence whose bytes are not stored in this checkout. A locator is not a
  runtime dependency or grant of authority.

## Referenced-input verification

Before any non-authoritative input is quoted or relied on for a reproducible
decision, its exact version must be available as a repository copy with a
SHA-256 digest or through a stable controlled locator with version, digest, and
access requirements. The rule is the same for every referenced input.
Recording evidence here grants no production status, canon authority, naming
reservation, publication eligibility, or reader-site inclusion. If the exact
input cannot be verified, treat claims drawn from it as unsupported.
