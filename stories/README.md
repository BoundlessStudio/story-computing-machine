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
- `authority.json` snapshots the exact authoritative universe files and
  promoted stories used by research and all downstream gates.
- `handoffs.json` is a schema-version-2 append-only hash chain of guarded
  specialist work. Each entry binds exact inputs, actual output changes, the
  specialist actor, the coordinator or specialist who persisted the output,
  the exact returned report text, and the preceding entry.
- `promotion.json` moves only through `not-prepared`, `ready`, and `completed`.
  A ready manifest binds explicit authorization and verified stewardship; a
  completed manifest is durable canon-transaction provenance.
- schema-version-2 `release.json` certifies exact prompt-through-final artifact
  hashes, current and reviewed authority provenance, handoff records, the identified draft and final
  review passes, zero unresolved Critical/Major findings, and the strict scoped
  name receipt.
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

The primary coordinator performs coordinated transitions through the provided
transaction scripts, not by editing projections independently:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Set-StoryLifecycle.ps1 -Story <slug> -Action <Accept|Reject|Publish|Unpublish|Reopen>
```

Both commands take the repository mutation lock, compare the captured inputs
before writing, update `story.json`, the story README, the exact index row and
the story's registry rows as one unit, then validate the postcondition. Any
failure after mutation restores the captured files byte-for-byte. Reopening a
published candidate additionally requires `-AuthorizePublishedReopen`; final
canon stories require an explicitly authorized retcon workflow.

Every specialist write is opened with `New-StoryHandoffGuard.ps1` and closed
with `Complete-StoryHandoffGuard.ps1 -GuardId <id> -GuardSha256 <sha>
-ReportText <exact-returned-payload>` (or explicitly aborted with both retained
guard values after all captured bytes are restored). A dirty abort is refused.
`-RecoverCommittedGuard` is only for strict verification and cleanup after a
crash following a durable append. A READY completion with no allowed output change fails, as
does any modification outside the declared paths. Draft and final continuity
passes use the exact 28-field review contract in
`schemas/pipeline-contract.json`; the review ledger entry's report must equal
that canonical payload and bind the pre-review ledger digest and chain head.

Plan and Final name gates produce `story-names/2` receipts. They bind artifact
and registry hashes and reject target-story collisions or missing registrations.
The Final gate also requires every prose-derived candidate to be registered and
inventoried or explicitly classified in the reviewed non-character allowlist;
the allowlist cannot excuse a character-facing name.

Canon promotion requires exact user approval and a current candidate bundle.
After the steward applies only approved universe changes and returns its raw
handoff, the primary persists the schema-valid ready manifest and runs:

```powershell
pwsh -NoProfile -File .agents/skills/canon-maintenance/scripts/Complete-CanonPromotion.ps1 -Story <slug> -PromotionDate <YYYY-MM-DD>
```

The command verifies the handoff, dispositions, pre/post universe images,
authority, release, and name receipt; then it atomically synchronizes final
lifecycle records, reissues provenance, marks `promotion.json` completed, and
runs story and repository validation.

Legacy candidate/final records must repeat the live gates they cannot prove.
The migration assessor may inventory that work, but it never synthesizes a
librarian, critic, steward, authorization, or promotion receipt.

`stories/NAMES.md` is production memory, not canon. `stories/INDEX.md`, each
production README, and the site must agree with `story.json`; repository checks
fail on missing directories, placeholders, invalid lifecycle combinations,
stale authority/release/review/handoff/promotion provenance, or unregistered
character-facing names. CI runs that full repository check for every pull
request and every push, including documentation-only changes.
