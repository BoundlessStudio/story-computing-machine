---
name: story-room
description: "Run the complete shared-universe short-story workflow for prompts tagged [WP], from prompt capture through canon vetting, planning, drafting, review, final prose, and a canon delta. Do not use for a request limited to one named stage."
---

# Story room

Produce the whole story and its audit trail.

## Start

1. Read `AGENTS.md`, `universe/README.md`, and `stories/INDEX.md`.
2. Derive a lowercase kebab-case slug. Never reuse an existing story directory.
3. Create the story directory from `stories/_template/`. On Windows, prefer:
   `./scripts/new-story.ps1 -Slug <slug> -Title "<title>"`.
4. Put the user's verbatim prompt in `00-prompt.md`. Record target length,
   audience/rating, POV, tense, tone, required elements, prohibited elements,
   assumptions, and completion tests. Never silently remove a prompt promise.

## Run the stages

Use the custom agents in the order defined by `AGENTS.md`; dependencies matter.
If delegation is unavailable, invoke the corresponding skill locally.

At every handoff, name the story directory and the exact input/output artifact.
Do not ask a subagent to rediscover the workflow. After a subagent returns,
verify that its output exists and follows the template before continuing.

Save the continuity critic's response in `04-review.md`. A `BLOCK` verdict must
be resolved. A `REVISE` verdict requires the relevant fixes and a focused
recheck. `PASS` may still include optional polish notes.

## Finish

Verify that:

- `05-story.md` is polished, complete prose within the agreed length tolerance;
- the ending resolves the central dramatic question;
- there are no unresolved critical issues in `04-review.md`;
- every reusable invention is listed in `06-canon-delta.md`;
- `stories/INDEX.md` has one current row. Unless explicit promotion was already
  authorized, its status is `candidate` and canon is `no`.

Report the final story path, approximate word count, review verdict, and whether
the canon delta contains proposals. Do not promote canon without explicit user
approval.
