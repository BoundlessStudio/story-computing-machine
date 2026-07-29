# Story Computing Machine

This repository is a shared-universe fiction workspace, not an application.
Treat prose and universe notes as the product.

## Directories and authority

- `universe/` is the authoritative source for shared-universe facts.
- `stories/INDEX.md` lists story state and canon status.
- `stories/NAMES.md` is the production-memory registry mapping character-facing
  names and aliases to every story or legacy source that uses them.
- Each story lives in `stories/<story-slug>/` and uses the numbered artifacts
  defined by `stories/_template/`.
- `stories/_legacy/` records non-canon legacy-source provenance, research,
  deferred adaptation questions, and import readiness.
- `.agents/skills/` contains the required workflows.
- `.codex/agents/` contains specialist roles for delegation.

Read `universe/README.md` before interpreting setting facts. Never treat a
template, draft, outline, review, open question, or proposed canon delta as
established canon.

Before adapting an external legacy work, require the exact reviewed version to
meet the portability rule in `stories/_legacy/README.md`. A source import is
evidence, not canon promotion.

## `[WP]` means the full story workflow

When a request contains `[WP]`, use the `story-room` skill and carry the prompt
through a complete short story unless the user explicitly requests only one
stage. Do not stop after brainstorming or outlining.

Use this dependency order:

1. Create `stories/<story-slug>/` and preserve the verbatim prompt in
   `00-prompt.md` with explicit assumptions and acceptance criteria.
2. Delegate canon research to `canon_librarian`; save its evidence-backed brief
   in `01-canon-brief.md`.
3. Delegate planning to `story_architect`; it writes `02-story-plan.md`.
4. Use the `story-name-validation` skill to verify the plan's name check,
   register every planned character-facing name in `stories/NAMES.md`, and run
   `.agents/skills/story-name-validation/scripts/check-story-names.ps1` with
   `-Story <story-slug>`.
5. Delegate drafting to `prose_writer`; it writes `03-draft.md`.
6. Delegate draft review to `continuity_critic`; save the identified review pass
   in `04-review.md` without discarding earlier passes.
7. If the verdict is `REVISE` or `BLOCK`, revise and re-review until the draft
   earns `PASS`. Do not finalize with unresolved Critical or Major findings.
8. Delegate the final edit to `story_editor`; it writes `05-story.md` and
   `06-canon-delta.md`.
9. Delegate a final review of `05-story.md` to `continuity_critic`. Record that
   pass in `04-review.md`. If it does not earn `PASS`, revise the final story and
   canon delta, then re-review `05-story.md` until it does.
10. Reconcile `stories/NAMES.md` with the final story and canon delta using the
    `story-name-validation` skill, rerun its scoped check, and update
    `stories/INDEX.md`. Leave canon status `candidate` until the user explicitly
    approves promotion.

Independent research may run in parallel, but stages with dependencies must
not. Custom agents must perform only their assigned role and must not restart
or re-orchestrate the whole workflow. If a custom role is unavailable, the
primary agent performs that stage using the matching skill.

The primary agent owns `stories/<story-slug>/README.md`. After verifying each
stage, update its current stage and corresponding checklist item. At completion,
the record must identify the story as `candidate`, show both review gates as
complete, and agree with `stories/INDEX.md`. Specialist agents do not update the
production record.

## On-demand prompt calibration

When the user asks to improve or calibrate prompt recommendations, delegate to
`prompt_calibrator`. It uses the latest ranks 11–100 to select an informative
comparison set and asks the user for a most-to-least ordering. Preserve that
ordering as preference evidence using the `prompt-calibration` skill.

This role may write only under `data/prompt-scout/` through the supporting skill
scripts. It does not edit `stories/`, `universe/`, or canon state. It runs on
demand only; do not schedule it unless the user later asks for scheduling.

## Defaults and user control

- Default to a complete 2,500–4,000 word short story.
- Derive POV, tense, tone, genre, and content rating from the prompt; when
  ambiguous, choose coherent defaults and record them in `00-prompt.md`.
- Ask a question only when the answer would materially change the requested
  story and no safe assumption exists.
- The user may name any artifact or stage to request a partial run or revision.
- Never overwrite an existing story directory. Choose a distinct slug or ask.

## Character-name discipline

- Read `stories/NAMES.md` before proposing or introducing any character-facing
  name. This includes full names, given names, mononyms, nicknames, aliases,
  usernames, titles used as names, and named animals, companions, constructs,
  or person-like entities. A surname is reserved separately when prose uses it
  alone as a character label.
- Default to a unique, readily distinguishable name across canon, candidates,
  in-progress stories, and portable legacy sources. Check exact matches,
  aliases, close spellings, reversals, and other easily confused forms.
- Reuse is permitted only when it adds intentional meaning: the same recurring
  identity, an earned crossover, an in-world family or naming convention, a
  prompt-required collision, or a deliberate identity/theme device. Record
  whether the identities are the same or distinct, why the reuse matters, and
  how readers can distinguish them in both the plan's `Name check` and
  `stories/NAMES.md`. Convenience, genre familiarity, or failure to search is
  not a rationale.
- Treat an undocumented or accidental collision as a defect. Rename it before
  drafting when possible. If discovered later, update every current production
  artifact and repeat the applicable review gate; never imply a shared identity
  or continuity link merely because names match.
- The primary agent owns `stories/NAMES.md`. Specialist agents read it and
  report name decisions but do not edit it. Register planned names after
  verifying `02-story-plan.md`, then reconcile the registry after final review
  so it matches `05-story.md`, `06-canon-delta.md`, the story state, and any
  aliases actually used.
- A registry entry is production memory, not canon. Legacy and abandoned names
  remain searchable reservations unless the registry explicitly marks them
  released; canon promotion still requires the normal approval workflow.

## Canon discipline

- Cite relevant universe files and headings in `01-canon-brief.md`.
- Distinguish contradictions from omissions. Missing lore is not evidence for
  a fact, but it can be room for a clearly labeled invention.
- Prefer local, story-scale inventions over new global rules.
- Record every newly introduced reusable fact in `06-canon-delta.md`.
- Treat legacy sources as nonbinding adaptation inputs. Review or rebuild a
  legacy work through the full story workflow before promotion; importing or
  copying it does not create canon.
- Unresolved factual contradictions, chronology problems, identity conflicts,
  causal inconsistencies, and paradoxes block canon promotion. Copyediting
  defects may be repaired during final editing.
- Do not edit authoritative universe notes or mark a story canon unless the
  user explicitly asks to promote it. Then use `canon_steward` with the
  `canon-maintenance` and `story-name-validation` skills.
- If canon sources conflict, preserve the conflict, report it, and request a
  ruling rather than quietly choosing the convenient version.

## Completion standard

A full `[WP]` task is complete only when `05-story.md` contains polished prose;
the latest certification in `04-review.md` identifies `05-story.md`, has verdict
`PASS`, and has no unresolved Critical or Major findings; `06-canon-delta.md` is
filled out (including `none` where appropriate); `stories/NAMES.md` contains
every final character-facing name and passes the story-scoped name check; the
story production record is current; and `stories/INDEX.md` agrees with it. The
story remains a candidate unless the same request or a later user message
explicitly authorizes canon promotion.
