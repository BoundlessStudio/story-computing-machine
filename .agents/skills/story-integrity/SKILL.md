---
name: story-integrity
description: "Validate story metadata, production records, review and name gates, inert evidence records, and content-bound release certificates; issue a release certificate only for a completed candidate or final bundle."
---

# Story integrity

Use this skill before declaring a story candidate, before canon promotion, and
whenever repository story records or evidence records change. `story.json` is
the authoritative lifecycle record. The production README and
`stories/INDEX.md` are derived lifecycle views that must agree with it.
`05-story.md` frontmatter contains only immutable identity fields (`title`,
`slug`, and `created`) so lifecycle transitions never invalidate reviewed prose
bytes.

## Metadata contract

Every story has schema-version-1 `story.json` with `slug`, `title`, `created`,
`stage`, `status`, boolean `canon`, `userDisposition`, boolean `publish`, a
nullable `promotionDate`. `sources/MANIFEST.json` describes inert evidence with
`authority: none`; those records are independent of production metadata and do
not classify stories or control publication.

Allowed stages are `prompt`, `canon-research`, `planning`, `drafting`,
`draft-review`, `final-edit`, `final-review`, `candidate`, `final`, and
`abandoned`. Allowed statuses are `in-progress`, `candidate`, `final`, and
`abandoned`. The integrity validator enforces the permitted combinations.

## Name gates

Run the plan gate after the plan and registry rows are current:

```powershell
pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 `
  -Story <slug> -Phase Plan
```

Run the final gate after final prose, the canon delta, and the registry are
reconciled. `06-canon-delta.md` must contain the explicit final name inventory;
every inventoried form must occur in final prose and have an exact story-scoped
registry reservation.

Use `-OutputFormat Json` when another workflow needs a machine receipt. A plan
receipt contains the plan hash; a final receipt contains story and canon-delta
hashes. Both bind the exact scoped registry rows and report exact, reversed,
close, and punctuation-confusable forms.

## Issue a release

After the story metadata is `candidate` or `final`, the current certification
in `04-review.md` must identify `05-story.md`, record a positive pass number,
name the reviewer, say `PASS`, and record zero unresolved Critical and Major
findings. Then run:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-StoryRelease.ps1 `
  -Story <slug>
```

The issuer reruns the final scoped name gate and writes schema-version-1
`release.json`. Its SHA-256 values cover the raw bytes of `05-story.md` and
`06-canon-delta.md`; editing either artifact invalidates the certificate.

## Validate

Validate one story while working:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 `
  -Story <slug>
```

Run the repository mode before completion, promotion, or publication:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
```

Both modes return a nonzero exit status for defects. Repository mode additionally
enforces the story-directory/index bijection and validates the inert evidence
manifest independently. Never hand-edit hashes or mark `certified` true.
