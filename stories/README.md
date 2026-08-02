# Stories

Every production story has its own `stories/<lowercase-kebab-slug>/` directory.
Directories beginning with `_` are support directories; `_template/` is the
transactional production template. Every story follows the same lifecycle and
uses the same records.

## Story artifacts

The numbered files form a durable chain from source prompt to final prose:

1. `00-prompt.md` — verbatim prompt plus explicit story contract.
2. `01-canon-brief.md` — researched constraints and safe invention space.
3. `02-story-plan.md` — causal, scene-level architecture and plan name check.
4. `03-draft.md` — complete working prose.
5. `04-review.md` — preserved, numbered draft and final-story review passes.
6. `05-story.md` — polished reader-facing story.
7. `06-canon-delta.md` — reusable facts proposed for canon promotion.

Machine and human records sit beside them:

- `story.json` is authoritative for stage, status, canon, user disposition,
  publication, and promotion date.
- `release.json` certifies exact final-story and delta hashes, the final PASS,
  zero unresolved Critical/Major findings, and the scoped name check.
- `README.md` is the primary agent's human production record.
- `stories/INDEX.md` is the checked repository-wide summary.

Only `05-story.md` is reader-facing. The site derives its catalog and story
pages from validated lifecycle records, release certificates, and final prose.

## Lifecycle

New stories start at stage `prompt`, status `in-progress`, canon false, user
disposition pending, and publish false. The full release gate advances a story
to `candidate`. Explicit canon promotion advances it to `final`, canon true,
accepted, with a promotion date. Rejected work is `abandoned`, non-canon, and
unpublished.

Publication is opt-in and does not establish canon. Candidate or final prose may
publish only while its content-bound certificate remains valid. Editing final
prose, the canon delta, relevant name-registry rows, or the certified review
requires revalidation and a new certificate.

`stories/NAMES.md` is production memory, not canon. `stories/INDEX.md`, each
production README, and the site must agree with `story.json`; repository checks
fail on missing directories, placeholders, invalid lifecycle combinations,
stale releases, or unregistered character-facing names.
