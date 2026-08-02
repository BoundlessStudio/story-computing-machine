---
name: canon-research
description: "Research and vet a story idea against this repository's shared-universe canon. Use before outlining, during continuity investigation, or when asked whether an idea contradicts established lore; do not invent missing canon."
---

# Canon research

The coordinator must delegate exactly one story in mode `RESEARCH_CANON`. The
delegation names `stories/<slug>/00-prompt.md`,
`stories/<slug>/authority.json`, and their
current raw-byte lowercase SHA-256 digests. A different or omitted mode is a
`HANDOFF_ERROR`; research never guesses the intended operation.

## Required inputs and authority

1. Require one named story slug and read its complete
   `stories/<slug>/00-prompt.md`. The prompt contract, not a paraphrase in the
   handoff, defines the research question.
2. Read `universe/README.md` for authority and status rules, then search all
   relevant Markdown under `universe/` for prompt entities, concepts, places,
   dates, factions, technologies, powers, and thematic constraints.
3. Read `stories/INDEX.md` and the relevant `story.json` records. A final story
   is continuity authority only when its index row says canon `yes` and its
   `story.json` says `canon: true`, with those records agreeing. Do not
   use candidate, in-progress, or abandoned prose to establish a
   shared-universe fact.
4. Read `stories/NAMES.md` as non-canon production memory. Report reserved
   names, aliases, close matches, and reversals relevant to the prompt or
   likely invention space.
5. Trace setting terms through `universe/glossary.md` and character-facing
   forms through `stories/NAMES.md` before declaring a mismatch.
6. Read `stories/<slug>/authority.json`, require its internal inventory to validate, and
   require its current raw-byte digest to equal the delegated
   `authorityManifestSha256`. The manifest's deterministic universe and
   release-valid canon-story inventory is the authority snapshot for this
   handoff. A missing, malformed, stale, or hash-mismatched manifest is a
   `HANDOFF_ERROR` with `resolutionOwner: coordinator`; do not construct an
   unofficial replacement snapshot.
7. Read `stories/<slug>/handoffs.json`, validate its exact identity and hash
   chain, and require its raw digest and `chainHead` to match the delegated
   pre-research snapshot. A stale or malformed ledger is a `HANDOFF_ERROR`;
   research never guesses the current causal position.

## Referenced-input verification

Apply one verification rule whenever research relies on a non-authoritative
input referenced by the prompt, regardless of its provenance or storage:

- identify the exact version with either a repository path and lowercase
  SHA-256, or an `externalRecords` stable controlled locator whose
  `verificationStatus` is `verified` and which has non-null `version`,
  lowercase `sha256`, and explicit `accessRequirements`;
- when the input has a `sources/MANIFEST.json` record, verify its `recordId`,
  ensure any recorded repository path resolves inside `sources/records/`,
  compare the current raw bytes with `sha256`, and require `authority: none`;
- treat an external record with `verificationStatus: descriptive-only` as
  provenance or a request for the missing input only. Its null version/digest
  cannot support a quotation, inference, or reproducible decision;
- treat descriptive and historical fields as provenance only, never as canon
  or as production metadata; and
- do not use Git history as a runtime dependency or reconstruct unavailable
  text from memory.

If a materially required input cannot be verified, state that under `Unknowns`.
When exact evidence is missing but the prompt can be interpreted in more than
one materially different way, return `USER_RULING_REQUIRED` and ask the
smallest exact question. A merely unavailable or `descriptive-only` input is a
`HANDOFF_ERROR` owned by the coordinator when supplying/verifying that input is
the mechanical prerequisite; never ask the user to bless unsupported claims.
Verification grants evidence value only; it does not alter lifecycle,
publication, review, or promotion rules.

## Persistence-ready result

Return exactly one `PERSISTENCE_HANDOFF`. Its discriminant is `status`; use only
these legal combinations:

- `READY` with `resolutionOwner: coordinator`, a complete bounded file body,
  and `errorCode: none`;
- `HANDOFF_ERROR` with `resolutionOwner: coordinator`, `modifiedFiles: none`,
  an exact mechanical prerequisite in `errorCode`/`resolutionQuestion`, and no
  speculative file body; or
- `USER_RULING_REQUIRED` with `resolutionOwner: user`, `modifiedFiles: none`,
  and the smallest exact user decision in `resolutionQuestion`.

Use this field order:

```text
PERSISTENCE_HANDOFF
story: <slug>
mode: RESEARCH_CANON
status: <READY|HANDOFF_ERROR|USER_RULING_REQUIRED>
resolutionOwner: <coordinator|user>
errorCode: <none|INVALID_MODE|STALE_INPUT|UNVERIFIED_INPUT|AUTHORITY_MANIFEST_INVALID>
resolutionQuestion: <none|exact prerequisite or user question>
target: stories/<slug>/01-canon-brief.md
sourcePrompt: stories/<slug>/00-prompt.md
sourcePromptSha256: <raw-byte lowercase sha256>
authorityManifest: stories/<slug>/authority.json
authorityManifestSha256: <raw-byte lowercase sha256>
handoffLedger: stories/<slug>/handoffs.json
handoffLedgerSha256: <delegated pre-handoff raw-byte lowercase sha256>
handoffLedgerChainHead: <delegated pre-handoff chainHead or none>
BEGIN_FILE_CONTENT
<complete file body for READY; omitted for other statuses>
END_FILE_CONTENT
modifiedFiles: none
changeReport: read-only; no files changed
```

The READY file body has every heading below in this order:

- after `# Canon brief`, durable lines for Research status, Resolution owner,
  Prompt SHA-256, and Authority manifest SHA-256 matching the handoff;
- `Hard constraints` — locked canon facts the story must obey, or `None.`
- `Useful established context` — canon that can enrich the story, or `None.`
- `Conflicts or ambiguity` — incompatible authority or unclear precedence, or
  `None.`
- `Unknowns` — unanswered matters that must not be stated as established.
- `Safe invention space` — narrow additions that do not alter global rules.
- `Name constraints` — reserved forms and documented-reuse requirements.
- `Required checks after drafting` — concrete continuity risks to search for.
- `Sources` — one validator-friendly physical line per cited source in this
  exact form (the output itself must not wrap the line):
  `- path: <repo-relative>; heading: <exact heading>; authority: <LOCKED|CANON|evidence-none>`.
  Use `None.` only when the brief makes no positive canon claim.

Cite every positive canon claim. Never infer that a missing fact is established;
label it `Unknown` and state whether a local invention appears safe. If canon
sources conflict, do not select a winner. Use `USER_RULING_REQUIRED` with
`resolutionOwner: user` and state the smallest exact question when the story
cannot safely proceed. The read-only researcher reports `changeReport:
read-only; no files changed`; the coordinator validates the prompt hash and
authority-manifest hash, persists the bounded file-content payload, then records
the accepted report in `stories/<slug>/handoffs.json` before advancing state.
It passes the exact complete returned `PERSISTENCE_HANDOFF` as `-ReportText` so
the ledger stores `report` and `reportSha256`; never reconstruct the response
from the persisted brief.

If an index row and `story.json` disagree, do not choose one. Use
`HANDOFF_ERROR`, `resolutionOwner: coordinator`, and the exact record repair in
`resolutionQuestion`; planning resumes only after the records and
`stories/<slug>/authority.json` are repaired/regenerated and `RESEARCH_CANON`
is rerun.
