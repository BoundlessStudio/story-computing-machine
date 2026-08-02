---
name: final-edit
description: "Create 05-story.md and 06-canon-delta.md from a currently passed draft, or revise both after a repairable final review. Enforces certification invalidation and final name inventory."
---

# Final edit

This is the local fallback for the `story_editor` role. It owns the paired
final artifacts only; it does not perform review, registry reconciliation,
release certification, publication, or canon promotion.

## Required mode and inputs

The coordinator must name one story and one mode: `CREATE_FINAL` or
`REVISE_FINAL`. Read `00-prompt.md`, `01-canon-brief.md`,
`02-story-plan.md`, `03-draft.md`, all of `04-review.md`,
`stories/NAMES.md`, and the current final artifacts when they exist. Hard-stop
without edits if any current gate says `HANDOFF_ERROR` or
`USER_RULING_REQUIRED`. The delegation must bind the exact current bytes and
the originally captured scaffold bytes:

```text
inputPlanSha256: <raw-byte lowercase sha256>
inputDraftSha256: <raw-byte lowercase sha256>
inputScopedRegistrySha256: <raw-byte lowercase sha256>
beforeStorySha256: <raw-byte lowercase sha256>
beforeCanonDeltaSha256: <raw-byte lowercase sha256>
storyScaffoldSha256: <raw-byte lowercase sha256>
canonDeltaScaffoldSha256: <raw-byte lowercase sha256>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <pre-handoff raw-byte lowercase sha256>
```

A mismatch is `HANDOFF_ERROR`; never infer mode from placeholder-looking text.
If the story is already `candidate`, no final edit is legal until the
coordinator atomically reopens it to non-canon `in-progress`/`final-review`,
pending/unpublished state, invalidates the old release, and synchronizes the
production projections while preserving review/ledger history. Return
`HANDOFF_ERROR` with `resolutionOwner: coordinator` until that prerequisite is
met; a published candidate needs explicit unpublish/reopen authority.

### `CREATE_FINAL`

Require the latest draft certification to:

- name `03-draft.md`;
- contain the raw-byte lowercase SHA-256 of the current draft;
- have verdict `PASS`;
- record zero unresolved Critical and Major findings.

Create both `05-story.md` and `06-canon-delta.md` only when their current hashes
equal `beforeStorySha256`/`beforeCanonDeltaSha256` and those values equal
`storyScaffoldSha256`/`canonDeltaScaffoldSha256`. Stop rather than overwrite a
changed target. Do not use an old PASS after the draft bytes have changed.

### `REVISE_FINAL`

Require the latest review to name the current `05-story.md` and match both its
story hash and current `06-canon-delta.md` hash. It must be either `REVISE`, or
`BLOCK` with `blockType: REPAIRABLE` and `resolutionOwner: story_editor`.
The current file hashes must also equal the delegated before hashes.
Revise the existing `05-story.md` and `06-canon-delta.md` together. Do not
regenerate them from the draft, use a draft review to authorize the revision,
or revise on a user-ruling block.

A prior final `PASS` does not directly authorize `REVISE_FINAL`. A failed Final
name gate or changed `authorityManifestSha256`/failed current-authority recheck
legally reopens the gate only when the coordinator delegates a new
independent `REVIEW_FINAL` against the same current artifact hashes and the
failed receipt/current `stories/<slug>/authority.json`. Only the resulting hash-matched
`REVISE` or repairable `BLOCK` assigned to `story_editor` authorizes this mode.

## Editing contract

- Resolve each assigned finding at its cause and report its disposition.
- Preserve effective voice, POV, story promise, causal climax, and scope.
- Keep every established canon constraint; label new reusable facts as
  proposals, not canon.
- Make `05-story.md` complete polished prose with a title, not notes or a
  synopsis.
- Keep its YAML frontmatter to the exact immutable identity fields `title`,
  `slug`, and `created`. Lifecycle state belongs only in `story.json` and must
  never be copied into final-story frontmatter.
- Complete every `06-canon-delta.md` category using explicit `None.` where
  there is no proposal. Account for every reusable new character fact,
  location, faction/cultural fact, rule/capability/cost, timeline event,
  glossary term/alias, possible conflict/retcon, and recommended promotion.
- Complete `Final character-facing name inventory` with every full name,
  short form, nickname, alias, username, title-as-name, named animal,
  construct, companion, or person-like entity actually used in final prose.
  The section is a strict machine-readable inventory: use exactly one physical
  line per identity in the template shape
  `- **Display name** — Reserved forms: `Display name`; `Alias`` and no other
  prose in that section. Put identity explanation and registry disposition in
  `New characters or character facts` or `Name registry updates`, never in the
  inventory row. Use `None.` only when the final story truly has no
  character-facing names.
- Preserve `## Reviewed prose name-audit allowlist` in `06-canon-delta.md`.
  Use `None.` when every conservative prose-derived candidate is an inventoried
  registered form. Otherwise use exactly the template's three columns
  `Candidate label`, `Classification`, and `Review rationale`, one row per
  exact extracted non-character label. Classification is only `common-word`,
  `formatting-artifact`, `non-character`, `organization`, `place`,
  `quoted-text`, or `setting-term`, and every row needs a human review
  rationale. Never allowlist a character-facing name to evade registration.
- Never silently add, remove, rename, shorten, retitle, or repurpose a form.
  If the requested edit needs an unregistered or changed form, do not write.
  Return `status: NAME_REGISTRATION_REQUIRED`, `errorCode: none`,
  `resolutionOwner: coordinator`, `modifiedFiles: none`, and exact
  `nameProposals`. The coordinator routes accepted proposals through the
  architect's `REVISE_PLAN`, registry reconciliation, Plan name validation,
  and a fresh draft review/repair loop. In CREATE mode, re-delegate only while
  both final targets still match their scaffold hashes. In REVISE mode,
  reconcile the unchanged final artifacts, obtain a new `REVIEW_FINAL` against
  the revised dependencies, and re-delegate only if that pass assigns
  `story_editor`.

## Write boundary and invalidation

The complete write allowlist is:

- `stories/<slug>/05-story.md`
- `stories/<slug>/06-canon-delta.md`

Do not edit review history, `story.json`, `release.json`, the production record,
the registry, index, universe notes, source archive, templates, scripts, or any
other story. Do not mark the story final/canon or orchestrate another role.

Every write in either mode invalidates a prior final PASS and any release bundle
whose artifact hashes refer to the old bytes. A final edit of any size,
including a name repair, must be followed in this order: accept and ledger the
change report; reconcile `finalNameInventory` and any registry proposals with
`stories/NAMES.md`; run independent final review against that reconciled
registry and the current authority manifest; run Final name validation; recheck
the current authority manifest hash; issue a new release; run story/repository
integrity. Registry reconciliation is always before final review. If it changes
a previously reviewed registry snapshot, that review is stale and must be
rerun.

## Exact change report

Return `FINAL_EDIT_CHANGE_REPORT` containing:

```text
story: <slug>
mode: <CREATE_FINAL|REVISE_FINAL>
status: <READY|HANDOFF_ERROR|USER_RULING_REQUIRED|NAME_REGISTRATION_REQUIRED>
resolutionOwner: <coordinator|story_editor|user>
errorCode: <none|INVALID_MODE|STALE_INPUT|INVALID_CREATE_TARGET|STALE_CERTIFICATION|MISSING_REPAIR_AUTHORIZATION>
resolutionQuestion: <none|exact prerequisite or user decision>
modifiedFiles:
- stories/<slug>/05-story.md
- stories/<slug>/06-canon-delta.md
inputPlanSha256: <raw-byte lowercase sha256>
inputDraftSha256: <raw-byte lowercase sha256>
inputScopedRegistrySha256: <raw-byte lowercase sha256>
beforeStorySha256: <raw-byte lowercase sha256>
beforeCanonDeltaSha256: <raw-byte lowercase sha256>
storyScaffoldSha256: <raw-byte lowercase sha256>
canonDeltaScaffoldSha256: <raw-byte lowercase sha256>
sourceCertification: <pass id, artifact, and hash>
newStorySha256: <post-write hash for READY|unchanged beforeStorySha256 otherwise>
newCanonDeltaSha256: <post-write hash for READY|unchanged beforeCanonDeltaSha256 otherwise>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <delegated pre-handoff raw-byte lowercase sha256>
findingDispositions: <each finding ID, disposition, and current evidence>
finalNameInventory: <every form or none>
proseNameAuditAllowlist: <every exact label/classification/rationale or none>
nameProposals: <exact forms/identity/rationale for NAME_REGISTRATION_REQUIRED|none>
invalidatedFinalCertification: <true when revision stales an old PASS/release|false when none existed|not-applicable for create>
requiresRegistryReconciliationBeforeReview: <true for READY|false otherwise>
requiresFinalReview: <true for READY|false otherwise>
requiresFinalNameCheck: <true for READY|false otherwise>
invalidatesDownstream: <ordered full sequence for READY|none otherwise>
```

`READY` uses `resolutionOwner: coordinator` and `errorCode: none`. If a gate
fails, preserve all exact before/scaffold hashes, report `modifiedFiles: none`,
and use `HANDOFF_ERROR` with the responsible `coordinator` or `story_editor`.
A needed name change uses `status: NAME_REGISTRATION_REQUIRED`, `errorCode:
none`, and supplies exact `nameProposals`/rationale. A user decision uses
`USER_RULING_REQUIRED`, `resolutionOwner: user`, and the exact
`resolutionQuestion`. The coordinator records every accepted report in the
hash-chained ledger before stage advancement.
It passes the exact complete `FINAL_EDIT_CHANGE_REPORT` as `-ReportText`; ledger
`report`/`reportSha256` preserve READY, proposal, and error responses.
