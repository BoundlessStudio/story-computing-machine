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
   "<title>"`. Verify the complete template, `story.json`, and `release.json`
   before treating bootstrap as successful.
4. Persist the user's verbatim prompt in `00-prompt.md` plus target length,
   audience/rating, POV, tense, tone, required/prohibited elements, assumptions,
   and completion tests. Never silently remove a prompt promise.
5. Keep `story.json`, the story `README.md`, and the one `stories/INDEX.md` row
   synchronized. A new story begins `stage: prompt`, `status: in-progress`,
   `canon: false`, `userDisposition: pending`, and `publish: false`.

The primary coordinator alone writes `00-prompt.md`, the librarian payload in
`01-canon-brief.md`, `04-review.md`, `story.json`, `release.json` through its
issuer, the story production record, `stories/INDEX.md`, and
`stories/NAMES.md` during production. Specialists may write only their
explicit allowlists and must return a change report. The primary retains those
central-record writes during later canon promotion; stewardship returns a
verified manifest rather than editing them.

After each verified handoff, the coordinator advances `story.json.stage` and
the production record through `canon-research`, `planning`, `drafting`,
`draft-review`, `final-edit`, and `final-review`, keeping the one index row
consistent. Check a production checklist item only when its artifact exists and
its applicable gate has actually passed; a stage label is not a certificate.

## Exact specialist handoffs

Name the story slug, mode, exact input paths and hashes, expected output, and
allowed writes at every handoff. Never ask a specialist to rediscover or run the
whole workflow. Verify returned paths, hashes, and payload shape before
persisting anything or advancing state. If delegation is unavailable, the
primary uses the matching skill and identifies itself explicitly in every
review/persistence payload.

1. **Canon research (read-only).** Give `canon_librarian` the slug and
   `00-prompt.md`. It returns a `PERSISTENCE_HANDOFF` bounded by
   `BEGIN_FILE_CONTENT` / `END_FILE_CONTENT`. Verify the prompt SHA-256 and
   persist exactly that body to `01-canon-brief.md`. If status is
   `COORDINATOR_REPAIR_REQUIRED`, repair the named records and rerun research.
   If it is `USER_RULING_REQUIRED`, stop for the user. Do not invoke the
   architect on any non-READY brief.
2. **Architecture.** Give `story_architect` the verified prompt and brief hashes.
   It may write only `02-story-plan.md` and returns `PLAN_CHANGE_REPORT`.
   Hard-stop on a user-ruling block.
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
4. **Draft create/revise.** Invoke `prose_writer` in `CREATE_DRAFT` mode. It may
   write only `03-draft.md`. For a later draft `REVISE`, use
   `REVISE_DRAFT` only when the latest hash-matched review assigns a repairable
   draft finding to it. Verify `DRAFT_CHANGE_REPORT`.
5. **Draft review (read-only).** Assign `continuity_critic` the next unique pass
   and `03-draft.md`. The critic reads all review history and returns one
   bounded `REVIEW_PASS_PAYLOAD`. Verify hashes, append it to `04-review.md`,
   preserve prior passes, and update Current certification with this pass's
   `Artifact SHA-256`, `Canon delta SHA-256`, reviewer, verdict, and unresolved
   counts. `REVISE` returns to
   `REVISE_DRAFT`; repairable `BLOCK` returns to the same owner;
   `USER_RULING_REQUIRED` stops for the user. Repeat until a current draft PASS
   records zero Critical and Major findings.
6. **Final create/revise.** Invoke `story_editor` with the `final-edit` skill in
   `CREATE_FINAL` mode only from that current draft PASS. It may write only
   `05-story.md` and `06-canon-delta.md`. A final review `REVISE`, or repairable
   `BLOCK` assigned to the editor, authorizes `REVISE_FINAL`; a user-ruling
   block never does. Verify `FINAL_EDIT_CHANGE_REPORT`.
7. **Final review (read-only).** Assign the next unique pass and `05-story.md`
   to the critic; include `06-canon-delta.md`. Verify and persist its bounded
   payload and Current certification exactly as at the draft gate. Repeat
   editor/reviewer turns until the
   current final hashes have a final PASS with zero Critical/Major findings.

Pass numbers are monotonic across both gates. Count only completed passes; the
untouched `Pass 1 — pending` scaffold is replaced by the first real pass and is
not itself history. The coordinator supplies one plus the highest completed
pass (or 1 when none exists); when omitted, the critic computes it from the
entire history. A duplicate or malformed completed history is a handoff error,
not permission to guess. Every retry must disposition previous Critical/Major
finding IDs.

## Final name loop and release certification

After final PASS, reconcile the final prose and `Final character-facing name
inventory` in `06-canon-delta.md` with `stories/NAMES.md`, then run:

```powershell
pwsh -NoProfile -File .agents/skills/story-name-validation/scripts/check-story-names.ps1 -Story <slug> -Phase Final -OutputFormat Json
```

If reconciliation requires any name repair, invalidate the final
certification/release, apply the repair through `REVISE_FINAL`, and repeat final
review before rerunning this check. Never patch final names after review and
retain the old PASS.

Before release, prove the following while lifecycle state still identifies the
current production stage:

- complete polished `05-story.md` satisfies the prompt and length tolerance;
- the latest review names `05-story.md`, is PASS, and has zero unresolved
  Critical/Major;
- every reusable invention and final character-facing form is accounted for in
  `06-canon-delta.md`;
- the final name receipt passes and matches the current scoped registry;
- `story.json`, production record, and exactly one index row agree;
- no placeholders remain in required candidate artifacts.

Set `story.json` and matching records to stage/status `candidate` in one
coordinator patch, keep `canon: false`, `publish: false` unless the user
separately requested publication, and leave promotion date empty. Then issue the
certificate only through the repository issuer; never hand-edit hashes or set
`certified` true:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/New-StoryRelease.ps1 -Story <slug>
```

The issuer reruns Final name validation and atomically writes schema-version-1
`release.json`. Verify that it binds current raw-byte hashes for `05-story.md`
and `06-canon-delta.md`, the current zero-blocker final review, and the current
scoped registry receipt. If issuance fails, restore the pre-candidate lifecycle
records and continue the applicable repair loop; do not claim candidate
completion.

## Completion proof

Run both executable gates:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1 -Story <slug>
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1
```

Require zero exit status from both and confirm the candidate release hashes
still match current bytes. Any later change to either final artifact invalidates
`release.json` and demands final review, Final name validation, and issuance
again.

Report final path, approximate word count, release/review evidence,
delta-proposal status, and deliberate name reuse. Do not promote canon without a
separate explicit authorization.
