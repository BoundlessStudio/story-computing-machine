# Story Computing Machine

This repository is a shared-universe fiction workspace, not an application.
Treat prose and universe notes as the product.

## Directories and authority

- `universe/` is the authoritative source for shared-universe facts.
- `stories/<story-slug>/story.json` is the machine authority for one story's
  lifecycle, canon, acceptance, and publication metadata.
- `stories/INDEX.md` is the checked human index of those story records.
- `stories/NAMES.md` is production memory mapping character-facing names and
  aliases to every story that uses them, plus released reservations.
- Each story uses the numbered artifacts and machine records defined by
  `stories/_template/`.
- `sources/` preserves inert evidence and decision history. Every record there
  has `authority: none`; nothing there classifies a production story.
- `.agents/skills/` contains the required workflows and integrity scripts.
- `.codex/agents/` contains specialist roles for delegation.

Read `universe/README.md` before interpreting setting facts. Never treat a
template, prompt, draft, outline, review, open question, proposed canon delta,
or material marked `authority: none` as established canon. Any referenced
input used for a reproducible decision must meet the verification rule in
`sources/README.md`. Evidence does not establish canon.

## Lifecycle model

Keep these axes independent in `story.json`:

- `stage`: `prompt`, `canon-research`, `planning`, `drafting`, `draft-review`,
  `final-edit`, `final-review`, `candidate`, `final`, or `abandoned`.
- `status`: `in-progress`, `candidate`, `final`, or `abandoned`.
- `canon`: a boolean; it becomes `true` only through explicit promotion.
- `userDisposition`: `pending`, `accepted`, or `rejected`.
- `publish`: a boolean independent of canon.

Allowed terminal combinations are:

| Status | Stage | Canon | Disposition | Promotion date | Publication |
| --- | --- | --- | --- | --- | --- |
| `candidate` | `candidate` | `false` | `pending` or `accepted` | `null` | optional after a valid release |
| `final` | `final` | `true` | `accepted` | required | optional after a valid release |
| `abandoned` | `abandoned` | `false` | `rejected` | `null` | `false` |

An `in-progress` story uses a nonterminal stage, remains non-canon with pending
disposition, has no promotion date, and is not published. `README.md` and
`stories/INDEX.md` must agree with `story.json`, but they do not override it.

## Release integrity

`release.json` is a content-bound certificate, not an editable status marker.
A certified release must bind all of the following:

- the SHA-256 digests of `05-story.md` and `06-canon-delta.md`;
- the latest identified review pass for `05-story.md`, with verdict `PASS`;
- reviewer identity and zero unresolved Critical and Major findings;
- a passing story-scoped name check and its scoped registry digest; and
- the certification timestamp and story slug.

Changing final prose, the canon delta, relevant name-registry rows, or the
certified review invalidates the certificate. Re-run the affected review/name
gate and issue a new certificate; never hand-edit hashes to make a check pass.
Only a candidate or final story with a currently valid certificate may publish
its reader-facing final.

## `[WP]` means the full story workflow

When a request contains `[WP]`, use the `story-room` skill and carry the prompt
through a complete short story unless the user explicitly requests only one
stage. Do not stop after brainstorming or outlining.

Use this dependency order:

1. Scaffold `stories/<story-slug>/` transactionally with `new-story.ps1` and
   preserve the verbatim prompt in `00-prompt.md` with assumptions and
   acceptance criteria. New stories start `in-progress`, non-canon, pending,
   and unpublished.
2. Delegate canon research to `canon_librarian`. The primary agent persists its
   evidence-backed handoff in `01-canon-brief.md` and verifies the write.
3. Delegate planning to `story_architect`; it writes `02-story-plan.md`.
4. Use `story-name-validation` to verify the plan's `Name check`, register every
   planned character-facing name in `stories/NAMES.md`, and run the scoped name
   checker for the story.
5. Delegate initial drafting or draft revision to `prose_writer`; it writes
   `03-draft.md` in the explicitly assigned mode.
6. Delegate draft review to `continuity_critic`. The primary agent appends its
   identified pass to `04-review.md` without discarding earlier passes.
7. For `REVISE`, return the findings to the prose writer, then re-review. For a
   repairable `BLOCK`, revise the named production artifact and re-review. For a
   `BLOCK` that requires a canon ruling, prompt reinterpretation, or new user
   authority, stop and ask the user; do not invent the ruling. Never proceed
   with unresolved Critical or Major findings.
8. Delegate the final edit to `story_editor`; it writes `05-story.md` and
   `06-canon-delta.md`. If that role is unavailable, the primary agent uses the
   local `final-edit` skill with the same preconditions and file ownership.
9. Delegate review of `05-story.md` to `continuity_critic` and append that
   separately numbered pass. If it does not earn `PASS`, use final-revision mode
   to update `05-story.md` and the canon delta, then re-review.
10. Reconcile `stories/NAMES.md` against the final story and delta, repeat any
    review invalidated by name changes, and run the strict scoped name check.
11. Issue `release.json`, update `story.json` to `candidate`, synchronize the
    story README and index, and run the repository validator. Leave `canon`
    false unless this request explicitly authorizes promotion.

Independent research may run in parallel, but dependent stages may not.
Specialist agents perform only the assigned role and must not restart or
re-orchestrate the workflow. If a custom role is unavailable, the primary agent
uses the matching skill.

## Ownership and handoffs

The primary agent owns coordination, persistence of read-only handoffs,
`story.json`, `release.json`, each story's `README.md`, `stories/INDEX.md`, and
`stories/NAMES.md`. Specialist write scopes are deliberately narrow:

| Role | Writes | Does not write |
| --- | --- | --- |
| `canon_librarian` | nothing; returns a persistence payload | story or universe files |
| `story_architect` | `02-story-plan.md` | prose, registry, production record |
| `prose_writer` | `03-draft.md` | final story, registry, production record |
| `continuity_critic` | nothing; returns one numbered review payload | story artifacts |
| `story_editor` | `05-story.md`, `06-canon-delta.md` | registry, metadata, index |
| `canon_steward` | approved universe notes and promotion provenance | production README, index, registry, lifecycle metadata |

Every delegation names the slug, source artifact, mode, required inputs,
allowed outputs, current pass/certificate state, and acceptance condition.
Read-only payloads identify their intended destination; the primary agent
persists and verifies them. A specialist must report a missing or stale
precondition rather than silently broadening its scope.

## Defaults and user control

- Default to a complete 2,500–4,000 word short story.
- Derive POV, tense, tone, genre, and content rating from the prompt; when
  ambiguous, choose coherent defaults and record them in `00-prompt.md`.
- Ask a question only when the answer would materially change the requested
  story and no safe assumption exists.
- The user may name any artifact or stage to request a partial run or revision.
- Never overwrite an existing story directory. Choose a distinct slug or ask.
- A partial run does not advance status past the last validated gate.

## Character-name discipline

- Read `stories/NAMES.md` before proposing or introducing any character-facing
  name. This includes full names, given names, mononyms, nicknames, aliases,
  usernames, titles used as names, and named animals, companions, constructs,
  or person-like entities. Reserve a surname separately when prose uses it
  alone as a character label.
- Default to a unique, readily distinguishable name across every production
  story lifecycle state and all active registry reservations. Check exact
  matches, aliases, close spellings, reversals, and confusable forms.
- Reuse is permitted only when it adds intentional meaning: the same recurring
  identity, an earned crossover, an in-world family or naming convention, a
  prompt-required collision, or a deliberate identity/theme device. Record
  whether identities are the same or distinct, why reuse matters, and how
  readers distinguish them in the plan and registry.
- Treat undocumented or accidental collision as a defect. Rename it before
  drafting when possible. If discovered later, update every current production
  artifact and repeat any invalidated review and release gate.
- The primary agent alone edits `stories/NAMES.md`. Register planned names after
  verifying the plan, then reconcile it after final review against the final
  story, delta, lifecycle state, and aliases actually used.
- Registry entries are production memory, not canon. Rows for abandoned work
  remain searchable reservations unless explicitly released.

## Canon discipline and promotion

- Cite relevant universe files and headings in `01-canon-brief.md`.
- Distinguish contradictions from omissions. Missing lore is not evidence for
  a fact, but it can be room for a clearly labeled local invention.
- Prefer local, story-scale inventions over new global rules.
- Record every newly introduced reusable fact in `06-canon-delta.md`.
- Every production story follows the same workflow and promotion gates.
  Material marked `authority: none` cannot establish a universe fact.
- Factual contradictions, chronology problems, identity conflicts, causal
  inconsistencies, and paradoxes block promotion. Copyediting defects may be
  repaired during final editing, followed by recertification.
- Do not edit authoritative universe notes or mark a story canon unless the
  user explicitly authorizes promotion. Then use `canon_steward` with
  `canon-maintenance` and `story-name-validation`, one named story at a time.
- Recheck each story against everything promoted before it. Record every delta
  item as `promote`, `story-local`, `defer`, or `reject`; do not copy a delta
  wholesale into universe notes.
- After stewardship succeeds, the primary agent revalidates names and release,
  sets status/stage to `final`, canon true, disposition accepted, and records
  the promotion date in metadata, README, registry, and index.
- If authoritative sources conflict, preserve the conflict and request a
  ruling rather than selecting the convenient version.

## Completion standard

A full `[WP]` task is complete only when `05-story.md` contains polished prose;
the latest identified final-story review is `PASS` with no unresolved Critical
or Major findings; `06-canon-delta.md` is complete (including `none` where
appropriate); every final character-facing name is registered and the strict
scoped check passes; `release.json` validly binds those results; and
`story.json`, the production README, and index agree. The completed story is a
candidate unless explicit promotion authority is part of the request.

Run the repository integrity suite before declaring workflow completion or
canon promotion complete. A published site must also build solely from the
current checkout, without depending on Git history.
