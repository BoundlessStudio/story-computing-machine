# Story Computing Machine

This repository is a shared-universe fiction workspace, not an application.
Treat prose and universe notes as the product.

## Directories and authority

- `universe/` is the authoritative source for shared-universe facts.
- `stories/INDEX.md` lists story state and canon status.
- Each story lives in `stories/<story-slug>/` and uses the numbered artifacts
  defined by `stories/_template/`.
- `.agents/skills/` contains the required workflows.
- `.codex/agents/` contains specialist roles for delegation.

Read `universe/README.md` before interpreting setting facts. Never treat a
template, draft, outline, review, open question, or proposed canon delta as
established canon.

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
4. Delegate drafting to `prose_writer`; it writes `03-draft.md`.
5. Delegate review to `continuity_critic`; save its report in `04-review.md`.
6. If the verdict is `REVISE` or `BLOCK`, revise and re-review. Do not finalize
   with unresolved critical canon or story-logic defects.
7. Delegate the final edit to `story_editor`; it writes `05-story.md` and
   `06-canon-delta.md`.
8. Update `stories/INDEX.md`. Leave canon status `candidate` until the user
   explicitly approves promotion.

Independent research may run in parallel, but stages with dependencies must
not. Custom agents must perform only their assigned role and must not restart
or re-orchestrate the whole workflow. If a custom role is unavailable, the
primary agent performs that stage using the matching skill.

## Defaults and user control

- Default to a complete 2,500–4,000 word short story.
- Derive POV, tense, tone, genre, and content rating from the prompt; when
  ambiguous, choose coherent defaults and record them in `00-prompt.md`.
- Ask a question only when the answer would materially change the requested
  story and no safe assumption exists.
- The user may name any artifact or stage to request a partial run or revision.
- Never overwrite an existing story directory. Choose a distinct slug or ask.

## Canon discipline

- Cite relevant universe files and headings in `01-canon-brief.md`.
- Distinguish contradictions from omissions. Missing lore is not evidence for
  a fact, but it can be room for a clearly labeled invention.
- Prefer local, story-scale inventions over new global rules.
- Record every newly introduced reusable fact in `06-canon-delta.md`.
- Do not edit authoritative universe notes or mark a story canon unless the
  user explicitly asks to promote it. Then use `canon_steward` and the
  `canon-maintenance` skill.
- If canon sources conflict, preserve the conflict, report it, and request a
  ruling rather than quietly choosing the convenient version.

## Completion standard

A full `[WP]` task is complete only when `05-story.md` contains polished prose,
`04-review.md` has no unresolved critical issues, `06-canon-delta.md` is filled
out (including `none` where appropriate), and `stories/INDEX.md` is current.
The story remains a candidate unless the same request or a later user message
explicitly authorizes canon promotion.
