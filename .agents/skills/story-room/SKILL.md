---
name: story-room
description: "Run the complete shared-universe short-story workflow for prompts tagged [WP], from prompt capture through canon vetting, planning, drafting, review, final prose, and a canon delta. Do not use for a request limited to one named stage."
---

# Story room

Produce one complete story and its durable audit trail. Custom agent model
fields are intentionally omitted so specialists inherit the coordinator's
current model; do not add an implicit model pin during delegation.

## Coordinator ownership and start

1. Read `AGENTS.md`, `universe/README.md`, `stories/INDEX.md`, and
   `stories/NAMES.md`.
2. Derive a lowercase kebab-case slug and prove the target directory does not
   exist. Never overwrite or recycle a story directory.
3. On Windows, run
   `.agents/skills/story-room/scripts/new-story.ps1 -Slug <slug> -Title
   "<title>"`. Verify the complete template, `story.json`, `release.json`,
   `authority.json`, and `handoffs.json` before treating bootstrap as
   successful. Capture the raw-byte scaffold hashes of `02-story-plan.md`,
   `03-draft.md`, `05-story.md`, and `06-canon-delta.md`; these exact values,
   not placeholder heuristics, gate CREATE modes.
4. Persist the user's verbatim prompt in `00-prompt.md` plus target length,
   audience/rating, POV, tense, tone, required/prohibited elements, assumptions,
   and completion tests. Never silently remove a prompt promise.
5. Keep `story.json`, the story `README.md`, and the one `stories/INDEX.md` row
   synchronized. A new story begins `stage: prompt`, `status: in-progress`,
   `canon: false`, `userDisposition: pending`, and `publish: false`.
6. Generate and verify the current story-scoped authority snapshot before
   research:

   ```powershell
   pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1 -Story <slug> -OutputFormat Json
   pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1 -Story <slug> -Verify -OutputFormat Json
   ```

   Use the raw-byte SHA-256 of `stories/<slug>/authority.json` as
   `authorityManifestSha256`. Never synthesize a second authority inventory in a
   handoff.

The primary coordinator alone writes `00-prompt.md`, the librarian payload in
`01-canon-brief.md`, `04-review.md`, `story.json`, `release.json` through its
issuer, the story production record, `stories/INDEX.md`, and
`stories/NAMES.md` during production. Specialists may write only their
explicit allowlists and must return a change report. The primary retains those
central-record writes during later canon promotion; stewardship returns a
verified manifest rather than editing them.

Only after a verified READY handoff also satisfies that stage's acceptance
condition does the coordinator advance `story.json.stage` and the production
record through `canon-research`, `planning`, `drafting`,
`draft-review`, `final-edit`, and `final-review`, keeping the one index row
consistent. Check a production checklist item only when its artifact exists and
its applicable gate has actually passed; a stage label is not a certificate.

## Guarded handoffs and ledger

Every specialist delegation has an explicit mode and runs inside a repository
mutation guard created with
`.agents/skills/story-integrity/scripts/New-StoryHandoffGuard.ps1`. Supply the
specialist's exact actor name, mode, complete write allowlist (for a read-only
role, the coordinator-persisted `01-canon-brief.md` or `04-review.md` target),
and every exact contract input path whose hash must be bound. Retain both the
returned guard ID and `guardSha256`, then pass both values and the exact
complete specialist response to `Complete-StoryHandoffGuard.ps1` via
`-ReportText`, with the report's discriminated status:
`READY`, `HANDOFF_ERROR`, `USER_RULING_REQUIRED`, or
`NAME_REGISTRATION_REQUIRED`. Repair any unauthorized mutation before aborting
or completing a guard. Abort succeeds only after every captured path is
restored and otherwise leaves the lock active. `-RecoverCommittedGuard` is
reserved for strict verification and lock cleanup after a crash following a
durable append.

The schema-version-2 ledger records the specialist `actor` separately from the
actual `persister` (`coordinator` for librarian/critic payloads), stores the
complete text as `report`, and stores its UTF-8 digest as
`reportSha256`; the guard canonicalizes only CRLF/CR line endings to LF before
both storage and hashing. Never summarize, otherwise normalize, or reconstruct
it. This makes
no-write name proposals, handoff errors, and user-ruling handoffs durably
recoverable as well as READY write reports.

Completion appends the accepted handoff to the hash-chained
`stories/<slug>/handoffs.json`. Recompute its raw-byte
`handoffLedgerSha256` and read its `chainHead` after every completion. Never
advance stage, invoke a dependent role, update Current certification, or issue
a release until the accepted report is in that ledger. Each next handoff binds
the current ledger path/hash, so a stale concurrent report is a
`HANDOFF_ERROR`, not usable work.

For REVIEW modes, the payload's `handoffLedgerSha256` and
`handoffLedgerChainHead` are explicitly the pre-review snapshot. Start the
guard with `stories/<slug>/handoffs.json` as an input; on completion, require
the new ledger entry's recorded input hash to equal that payload digest and its
`previousEntrySha256` to equal that payload head. The append necessarily
changes both current values. `release.json` binds the post-acceptance current
ledger digest, never the pre-review payload digest.

## Exact specialist handoffs

Name the story slug, mode, exact input paths and hashes, expected output, and
allowed writes at every handoff. Never ask a specialist to rediscover or run the
whole workflow. Verify returned paths, hashes, and payload shape before
persisting anything or advancing state. A coordinator may use an allowed local
write skill when its artifact specialist is unavailable, but certification
always requires the independent `continuity_critic`; the coordinator may never
self-review or forge reviewer identity. Canon promotion always requires the
independent `canon_steward`; there is no coordinator/steward fallback.

1. **Canon research (read-only).** Give `canon_librarian` mode
   `RESEARCH_CANON`, the slug, current `00-prompt.md` hash, and current
   `stories/<slug>/authority.json` path/hash. It returns a
   `PERSISTENCE_HANDOFF` bounded by
   `BEGIN_FILE_CONTENT` / `END_FILE_CONTENT`. Verify the prompt SHA-256 and
   authority-manifest SHA-256 and persist exactly that body to
   `01-canon-brief.md` before completing/ledgering the guard. Its Sources lines
   must use exact `path; heading; authority` form. On `HANDOFF_ERROR`, repair
   the named prerequisite, regenerate/verify the manifest when authority
   records changed, and rerun `RESEARCH_CANON`; on
   `USER_RULING_REQUIRED`, stop for the user. Do not invoke the architect on
   any non-READY brief.
2. **Architecture.** Give `story_architect` mode `CREATE_PLAN`, verified prompt
   and brief hashes, exact `beforePlanSha256` and `planScaffoldSha256`, and the
   current ledger path/hash. It may write only `02-story-plan.md` and returns
   `PLAN_CHANGE_REPORT`. `REVISE_PLAN` additionally requires a hash-bound
   critic or accepted name-proposal authorization. Never infer mode. A
   `NAME_REGISTRATION_REQUIRED` plan is ledgered, its exact proposals are
   reconciled by the coordinator, and `REVISE_PLAN` must record the verified
   registry results and return READY before the Plan name gate. Hard-stop on a
   user-ruling status.
3. **Plan name gate.** Reconcile every planned character-facing form in
   `stories/NAMES.md`, including deliberate-reuse meaning and reader
   disambiguation. Run:

   ```powershell
   pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 -Story <slug> -Phase Plan -OutputFormat Json
   ```

   Require exit code 0 and schema-version-1 JSON for this slug with
   `phase: Plan`, `passed: true`, `receiptId`, current raw-byte lowercase
   `planSha256`, and `scopedRegistrySha256` for current canonical scoped rows.
   Capture this successful receipt and include it in the writer handoff. A
   console summary or stale receipt is not a gate pass.
   Any later `NAME_REGISTRATION_REQUIRED` from the writer/editor returns first
   to `REVISE_PLAN`, coordinator registry reconciliation, and this Plan gate;
   do not register a form while leaving the plan stale.
4. **Draft create/revise.** Invoke `prose_writer` in `CREATE_DRAFT` mode with
   exact `beforeDraftSha256`, `draftScaffoldSha256`, current ledger path/hash,
   and the successful Plan receipt. It may write only `03-draft.md`. For a
   later draft repair, use
   `REVISE_DRAFT` only when the latest hash-matched review assigns a repairable
   draft finding to it, and bind the before hash to that review. Verify
   `DRAFT_CHANGE_REPORT`. A `NAME_REGISTRATION_REQUIRED` response changes no
   draft bytes; ledger it and run the plan/name flow above. A CREATE handoff can
   then be re-delegated with the unchanged before hash. For REVISE, first run a
   new `REVIEW_DRAFT` against the unchanged draft and revised plan; re-delegate
   only if that current pass assigns `prose_writer`.
5. **Draft review (read-only).** Assign independent `continuity_critic` mode
   `REVIEW_DRAFT`, the next unique pass, `03-draft.md` and its exact hash,
   current canon-brief/plan/registry hashes, current authority manifest
   path/hash, and current ledger path/hash/`chainHead`. The critic reads all review history and returns one
   bounded `REVIEW_PASS_PAYLOAD`. Verify hashes, append it to `04-review.md`,
   preserve prior passes, and update Current certification with this pass's
   `Artifact SHA-256`, `Canon delta SHA-256`, reviewer, verdict, and unresolved
   counts inside the guard; then complete/ledger the guard. `REVISE` returns to
   `REVISE_DRAFT`; repairable `BLOCK` returns to the same owner;
   `USER_RULING_REQUIRED` stops for the user. A repair assigned to
   `coordinator`, `canon_librarian`, or `story_architect` routes to that owner,
   then invalidates and reruns every downstream gate before review resumes.
   Repeat until a current draft PASS records zero Critical and Major findings.
6. **Final create/revise.** Invoke `story_editor` with the `final-edit` skill in
   `CREATE_FINAL` mode only from that current draft PASS, supplying exact
   plan, draft, and scoped-registry hashes plus `beforeStorySha256`,
   `beforeCanonDeltaSha256`, `storyScaffoldSha256`,
   `canonDeltaScaffoldSha256`, and current ledger path/hash. It may write only
   `05-story.md` and `06-canon-delta.md`. A final review `REVISE`, or repairable
   `BLOCK` assigned to the editor, authorizes `REVISE_FINAL`; a user-ruling
   block or old PASS never does. Verify and ledger `FINAL_EDIT_CHANGE_REPORT`.
   A `NAME_REGISTRATION_REQUIRED` response changes no final bytes; ledger it,
   then complete the plan/name and invalidated draft review/repair sequence. For
   CREATE, re-delegate only while both targets still match scaffold hashes. For
   REVISE, reconcile the unchanged existing final artifacts, obtain a new
   `REVIEW_FINAL`, and re-delegate only if that current pass assigns
   `story_editor`.
7. **Pre-review registry reconciliation.** Before every final review, reconcile
   the editor's `finalNameInventory`, `06-canon-delta.md`, final prose, and any
   accepted proposals with `stories/NAMES.md`. If any editor proposal remains
   unresolved, do not review. A registry change stales any prior review
   evidence. This step is mandatory before, not after, the critic handoff.
8. **Final review (read-only).** Assign independent `continuity_critic` mode
   `REVIEW_FINAL`, the next unique pass, current story/delta hashes,
   canon-brief/plan/reconciled-registry hashes, current authority manifest
   path/hash, and current ledger path/hash/`chainHead`. Verify and persist its bounded
   payload and update Current certification exactly as at the draft gate inside
   the guard; then complete/ledger the guard. Route coordinator/librarian/architect repair ownership
   to the named upstream stage and rerun all invalidated downstream gates.
   Repeat editor/reviewer turns until the
   current final hashes have a final PASS with zero Critical/Major findings.

Pass numbers are monotonic across both gates. Count only completed passes; the
untouched `Pass 1 — pending` scaffold is replaced by the first real pass and is
not itself history. The coordinator supplies one plus the highest completed
pass (or 1 when none exists); when omitted, the critic computes it from the
entire history. A duplicate or malformed completed history is a handoff error,
not permission to guess. Every retry must disposition previous Critical/Major
finding IDs.

## Downstream invalidation map

Treat a changed dependency as invalidating gates, not necessarily forcing a
text edit. Rerun in dependency order and use a repair mode only when the new
review assigns that artifact owner:

- changed `01-canon-brief.md` or authority snapshot: `REVISE_PLAN`, Plan
  registry/name gate, `REVIEW_DRAFT` (then writer/re-review if needed), final
  registry reconciliation, `REVIEW_FINAL` (then editor/re-review if needed),
  Final name gate, authority verify, release issuance, story and repository
  integrity;
- changed `02-story-plan.md` or relevant registry rows: Plan name gate,
  `REVIEW_DRAFT`/repair loop, final reconciliation and `REVIEW_FINAL`/repair
  loop, Final name gate, authority verify, release and integrity;
- changed `03-draft.md`: `REVIEW_DRAFT`, final registry reconciliation,
  `REVIEW_FINAL`/repair loop, Final name gate, authority verify, release and
  integrity;
- changed `05-story.md` or `06-canon-delta.md`: final registry reconciliation,
  `REVIEW_FINAL`, Final name gate, authority verify, release and integrity;
- changed relevant registry rows after final review, changed current authority
  after PASS, or a failed Final name receipt: reopen with a new
  `REVIEW_FINAL`, then continue through Final name, authority, release, and
  integrity gates; and
- changed certified review history or handoff ledger: recalculate its binding,
  rerun the affected independent review when certification evidence changed,
  then Final name, authority, release, and integrity gates.

Invalidate/remove no audit history. Mark old receipts/certificates stale by
hash and append new evidence; do not relabel an old PASS as current.

## Final name loop and release certification

After a final PASS obtained against the already reconciled registry, run:

```powershell
pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 -Story <slug> -Phase Final -OutputFormat Json
```

If the Final name gate fails after PASS, the old PASS cannot directly authorize
an edit. Capture the failed JSON receipt/evidence and legally reopen with the next
independent `REVIEW_FINAL` against the same current artifact hashes. Route its
`resolutionOwner`: coordinator-only registry repair returns through
pre-review reconciliation and another review; architect/research repairs rerun
their complete downstream sequence; an editor repair authorizes
`REVISE_FINAL`. Obtain a new final PASS, then rerun the Final name gate. Never
patch final names while retaining the old PASS.

Immediately before candidate completion, verify the authority snapshot:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1 -Story <slug> -Verify -OutputFormat Json
```

If verification fails because current authority changed, regenerate the
story-scoped manifest and reopen with the next independent `REVIEW_FINAL` bound
to its new `authorityManifestSha256`. Route repairs as above, obtain a new PASS,
rerun the Final name gate, then verify the manifest again. This is the only
legal post-PASS authority-recheck path.

If this failure is discovered after the story already reached `candidate`, do
not edit terminal artifacts in place. Before a new review or specialist write,
the coordinator performs one atomic reopen transaction: preserve review and
handoff history; return `story.json`, README, index, and this story's registry
projection to `status: in-progress`, `stage: final-review`, `canon: false`,
`userDisposition: pending`, `publish: false`, and no promotion date; reset the
old release to an uncertified state through the repository transaction helper;
and close/roll back any prepared promotion transaction. A published candidate
requires explicit authority to unpublish/reopen; otherwise return
`USER_RULING_REQUIRED`. Regenerate/verify the authority manifest, then use the
new-review route above. Changed reader-facing bytes require fresh candidate
certification and renewed user acceptance before promotion.

Before release, prove the following while lifecycle state still identifies the
current production stage:

- complete polished `05-story.md` satisfies the prompt and length tolerance;
- the latest review names `05-story.md`, is PASS, and has zero unresolved
  Critical/Major;
- every reusable invention and final character-facing form is accounted for in
  `06-canon-delta.md`;
- the final name receipt passes and matches the current scoped registry;
- `authorityManifestSha256` equals the currently verified
  `stories/<slug>/authority.json` raw hash;
- `handoffLedgerSha256` equals the current validated ledger containing READY
  entries for every required mode;
- `story.json`, production record, and exactly one index row agree;
- no placeholders remain in required candidate artifacts.

Complete lifecycle projection and release issuance through the atomic candidate
finalizer; never hand-edit hashes or set `certified` true:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Complete-StoryCandidate.ps1 -Story <slug>
```

Use `-Publish` only when separately authorized. The finalizer verifies the
authority manifest and required READY handoff chain, projects candidate
metadata/README/index/registry state, reruns Final name validation, issues the
current schema-version-2 `release.json`, and rolls back its production writes
on failure. Verify that the release binds current story/delta hashes, zero-
blocker independent review, scoped registry receipt,
`authorityManifestSha256`, and `handoffLedgerSha256`. On failure continue the
applicable repair loop; do not claim candidate completion.

## Completion proof

Run all executable gates:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryHandoffs.ps1 -Story <slug> -RequireReleaseChain -OutputFormat Json
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
```

Require zero exit status from all three and confirm the candidate release hashes
and provenance still match current bytes. Any later change to either final
artifact, relevant registry rows, authority manifest, accepted handoff ledger,
or certified review invalidates `release.json` and demands the applicable
reconciliation/review/name/authority/release sequence again.

Report final path, approximate word count, release/review evidence,
delta-proposal status, and deliberate name reuse. Do not promote canon without a
separate explicit authorization.
Promotion must be delegated to `canon_steward`; if that independent role is
unavailable, stop rather than having the coordinator act as steward.
