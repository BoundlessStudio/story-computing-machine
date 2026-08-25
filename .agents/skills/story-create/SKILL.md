---
name: story-create
description: "Create one new or explicitly requested replacement shared-universe short story through outline, prose, review, and cover."
---

# Story create

Use for a new `[WP]` prompt, an explicitly requested remove-then-create
replacement of one named story, or an explicitly requested CREATE stage. Never
reopen or transform an existing package in place. Read
`../story-room/SKILL.md` for the shared OUTLINE, REVIEW, and TITLE IMAGE
responsibilities and use the repository's `short-story-writing` adapter for
prose.

## Workflow

1. Complete the required `main` update, `codex/story-<slug>` branch, and sibling
   worktree setup before story production. Work only in that worktree.
2. For a replacement, inspect the named story's authoritative canon marker
   before reading for production. If it is missing or ambiguous, stop for user
   direction. If it is `true`, stop unless the user has
   authorized an independent marker-only unlock; complete and commit that
   unlock before any content action. Before removal, retain every verbatim
   user-authored prompt or request block, the verbatim new request, and every
   associated reference-image display name. Discard only machine-owned
   selection, cover-policy, constraint, and workflow metadata. Resolve and visually inspect every retained and newly supplied
   external reference; if any original cannot be accessed, ask the user to
   attach it again.
3. For a replacement, remove only the explicitly named source package and its
   publication, cover, timeline, and bundle-index remnants. Do not retain or
   read its outline, prose, review, or cover as creative input. Confirm the
   target directory is absent. Run `../story-room/scripts/new-story.ps1` with a
   single CREATE prompt that preserves all retained user-authored text and the
   new request verbatim, inventories every associated and new reference display
   name, and passes every retained and newly supplied reference through
   `-ReferenceImage`. For a new story,
   preserve the fresh prompt and handle references the same way. Do not create
   new amendment or selection sections. All new scaffolds use
   `prospective-2026-08-23`.
4. Before OUTLINE, perform the periodic no-artifact collection audit required by
   `AGENTS.md` when the completed 08-23 CREATE count reaches a multiple of ten.
   Give the outliner only the compact anti-default result.
5. Delegate a fresh `story_outliner`. It writes only `outline.md`, derives the
   prompt's dialogue promise, chooses a deliberate dialogic medium and dialogue
   engine, and completes the six-field Voice capsule including Relationship
   movement. Follow the shared story-room OUTLINE responsibility.
6. Delegate a fresh `story_writer`. It writes the complete prose only to
   `story.md` through the project adapter and revises it in place. It must not
   open prior story prose; collection comparison belongs downstream.
7. Run targeted PreReview once. Delegate a fresh `story_reviewer`, including the
   six most recent passing current-story paths excluding the target, or all
   available when fewer than six exist. The reviewer first judges the target on
   its own, then performs the bounded interchangeability comparison required by
   the shared REVIEW responsibility.
8. Resolve a REVISE verdict through only its blocking findings, rerun PreReview,
   and use a fresh reviewer each time.
9. After PASS, use the shared TITLE IMAGE responsibility and seven saved-pixel
   gates. Then run final validation, capture, catalog check, commit, push, and
   open the draft pull request.

Replacement is ordinary CREATE: it receives the same full recent-story
comparison, independent review, cover gates, capture, and publication checks as
a fresh story. The four Markdown files and final cover remain the only story
artifacts. Do not create briefs, draft copies, migration records, audit files,
or lifecycle records.
