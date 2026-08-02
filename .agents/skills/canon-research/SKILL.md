---
name: canon-research
description: "Research and vet a story idea against this repository's shared-universe canon. Use before outlining, during continuity investigation, or when asked whether an idea contradicts established lore; do not invent missing canon."
---

# Canon research

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

## Referenced-input verification

Apply one verification rule whenever research relies on a non-authoritative
input referenced by the prompt, regardless of its provenance or storage:

- identify the exact version with either a repository path and lowercase
  SHA-256, or a stable controlled locator with version, digest, and access
  requirements;
- when the input has a `sources/MANIFEST.json` record, verify its `recordId`,
  ensure any recorded repository path resolves inside `sources/records/`,
  compare the current raw bytes with `sha256`, and require `authority: none`;
- treat descriptive and historical fields as provenance only, never as canon
  or as production metadata; and
- do not use Git history as a runtime dependency or reconstruct unavailable
  text from memory.

If a materially required input cannot be verified, state that under `Unknowns`.
When research cannot safely proceed without it, return `USER_RULING_REQUIRED`
and ask for the exact input or permission to proceed without relying on it.
Verification grants evidence value only; it does not alter lifecycle,
publication, review, or promotion rules.

## Persistence-ready result

Return exactly one `PERSISTENCE_HANDOFF` with, in order, `target:
stories/<slug>/01-canon-brief.md`, `sourcePrompt`, its raw-byte lowercase
`sourcePromptSha256`, `status: READY | COORDINATOR_REPAIR_REQUIRED |
USER_RULING_REQUIRED`,
`resolutionOwner: coordinator | user`, `rulingQuestion: none | <exact user
question>`, `BEGIN_FILE_CONTENT`, the complete file body, `END_FILE_CONTENT`,
and `changeReport: read-only; no files changed`. The file body has every heading
below in this order:

- after `# Canon brief`, durable lines for Research status, Resolution owner,
  and Prompt SHA-256 matching the handoff;
- `Hard constraints` — locked canon facts the story must obey, or `None.`
- `Useful established context` — canon that can enrich the story, or `None.`
- `Conflicts or ambiguity` — incompatible authority or unclear precedence, or
  `None.`
- `Unknowns` — unanswered matters that must not be stated as established.
- `Safe invention space` — narrow additions that do not alter global rules.
- `Name constraints` — reserved forms and documented-reuse requirements.
- `Required checks after drafting` — concrete continuity risks to search for.
- `Sources` — repository-relative paths plus exact headings and each source's
  authority status.

Cite every positive canon claim. Never infer that a missing fact is established;
label it `Unknown` and state whether a local invention appears safe. If canon
sources conflict, do not select a winner. Use `USER_RULING_REQUIRED` with
`resolutionOwner: user` and state the smallest exact question when the story
cannot safely proceed. The read-only researcher reports `changeReport:
read-only; no files changed`; the coordinator validates the prompt hash and
persists the bounded file-content payload.

If an index row and `story.json` disagree, do not choose one. Use
`COORDINATOR_REPAIR_REQUIRED`, `resolutionOwner: coordinator`, and no ruling
question; planning resumes only after the records are repaired and research is
rerun.
