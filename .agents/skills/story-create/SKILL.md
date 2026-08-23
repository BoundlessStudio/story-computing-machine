---
name: story-create
description: "Create one new shared-universe short story from a fresh prompt through outline, prose, review, and cover."
---

# Story create

Use only for a new `[WP]` prompt or an explicitly requested CREATE stage. Never
use this skill to reopen an existing story. Read `../story-room/SKILL.md` for the
shared OUTLINE, REVIEW, and TITLE IMAGE responsibilities and use the repository's
`short-story-writing` adapter for prose.

## Workflow

1. Complete the required `main` update, `codex/story-<slug>` branch, and sibling
   worktree setup before story production. Work only in that worktree.
2. Resolve and visually inspect every supplied reference image. Run
   `../story-room/scripts/new-story.ps1`, preserving the verbatim prompt and
   passing every reference through `-ReferenceImage`. New scaffolds use
   `prospective-2026-08-23`.
3. Before OUTLINE, perform the periodic no-artifact collection audit required by
   `AGENTS.md` when the completed 08-23 CREATE count reaches a multiple of ten.
   Give the outliner only the compact anti-default result.
4. Delegate a fresh `story_outliner`. It writes only `outline.md`, derives the
   prompt's dialogue promise, chooses a deliberate dialogic medium and dialogue
   engine, and completes the six-field Voice capsule including Relationship
   movement. Follow the shared story-room OUTLINE responsibility.
5. Delegate a fresh `story_writer`. It writes the complete prose only to
   `story.md` through the project adapter and revises it in place. It must not
   open prior story prose; collection comparison belongs downstream.
6. Run targeted PreReview once. Delegate a fresh `story_reviewer`, including the
   six most recent passing current-story paths excluding the target, or all
   available when fewer than six exist. The reviewer first judges the target on
   its own, then performs the bounded interchangeability comparison required by
   the shared REVIEW responsibility.
7. Resolve a REVISE verdict through only its blocking findings, rerun PreReview,
   and use a fresh reviewer each time.
8. After PASS, use the shared TITLE IMAGE responsibility and six saved-pixel
   gates. Then run final validation, capture, catalog check, commit, push, and
   open the draft pull request.

The four Markdown files and final cover remain the only story artifacts. Do not
create briefs, draft copies, audit files, or lifecycle records.
