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
without edits if any current gate says `USER_RULING_REQUIRED`.

### `CREATE_FINAL`

Require the latest draft certification to:

- name `03-draft.md`;
- contain the raw-byte lowercase SHA-256 of the current draft;
- have verdict `PASS`;
- record zero unresolved Critical and Major findings.

Create both `05-story.md` and `06-canon-delta.md` only when each target is absent
or still its unchanged scaffold placeholder. Stop rather than overwrite
substantive unreviewed final work. Do not use an old PASS after the draft bytes
have changed.

### `REVISE_FINAL`

Require the latest review to name the current `05-story.md` and match both its
story hash and current `06-canon-delta.md` hash. It must be either `REVISE`, or
`BLOCK` with `blockType: REPAIRABLE` and `resolutionOwner: story_editor`.
Revise the existing `05-story.md` and `06-canon-delta.md` together. Do not
regenerate them from the draft, use a draft review to authorize the revision,
or revise on a user-ruling block.

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
- Never silently add, remove, rename, shorten, retitle, or repurpose a form.
  Return every proposed registry change to the coordinator.

## Write boundary and invalidation

The complete write allowlist is:

- `stories/<slug>/05-story.md`
- `stories/<slug>/06-canon-delta.md`

Do not edit review history, `story.json`, `release.json`, the production record,
the registry, index, universe notes, source archive, templates, scripts, or any
other story. Do not mark the story final/canon or orchestrate another role.

Every write in either mode invalidates a prior final PASS and any release bundle
whose artifact hashes refer to the old bytes. A final edit of any size,
including a name repair, must be followed by a new final review, registry
reconciliation, Final name validation, and release certification.

## Exact change report

Return `FINAL_EDIT_CHANGE_REPORT` containing:

```text
story: <slug>
mode: <CREATE_FINAL|REVISE_FINAL>
modifiedFiles:
- stories/<slug>/05-story.md
- stories/<slug>/06-canon-delta.md
sourceCertification: <pass id, artifact, and hash>
newStorySha256: <raw-byte lowercase sha256>
newCanonDeltaSha256: <raw-byte lowercase sha256>
findingDispositions: <each finding ID, disposition, and current evidence>
finalNameInventory: <every form or none>
proposedRegistryChanges: <exact changes and rationale or none>
invalidatedFinalCertification: <true for post-PASS revision|not-applicable for create>
requiresFinalReview: true
requiresFinalNameCheck: true
```

If a gate fails, report `modifiedFiles: none`, result
`USER_RULING_REQUIRED | STALE_CERTIFICATION | INVALID_MODE`, and the exact
prerequisite. A user-ruling result also includes the exact `rulingQuestion`.
