---
name: story-architecture
description: "Design a scene-ready short-story plan from a captured prompt and canon brief. Use for plot, character arc, scene structure, stakes, and ending design; do not use to draft final prose."
---

# Short-story architecture

Read `00-prompt.md`, `01-canon-brief.md`, and `stories/NAMES.md` before
planning. Require the coordinator to name those exact inputs and their current
hashes. Accept only a canon brief with status `READY`. On
`COORDINATOR_REPAIR_REQUIRED` or `USER_RULING_REQUIRED`, stop without writing
and return the repair prerequisite or the smallest exact question for the user.
Do not plan around unresolved authority or inconsistent records.

Build `02-story-plan.md` around one central dramatic question and one meaningful
change. The protagonist needs a concrete desire, pressure that makes delay
costly, a blind spot or internal tension, and a final choice that causes the
ending. Each scene must change the situation and cause or constrain the next.

Include:

- one-sentence premise and story promise;
- POV, tense, tone, length budget, and content boundaries;
- protagonist, desire, stakes, opposition, internal movement, and key cast;
- beginning state, inciting disruption, escalating turns, crisis, climax, and
  resonant aftermath;
- a scene table with purpose, conflict, turn, canon used, and word budget;
- seeded details and their payoffs;
- canon constraints and clearly labeled proposed inventions;
- a `Name check` section containing only the exact four-column table from
  `stories/_template/02-story-plan.md`: `Character/entity`, `Reserved forms
  used in prose`, `Registry result`, and `Reuse rationale and reader
  disambiguation`. Put the table immediately after the heading, put every
  planned character-facing form in its second column separated by semicolons,
  and begin any commentary after it under a new level-two heading. Do not add,
  remove, rename, or merge columns;
- failure modes the writer and critic should watch.

Fit the plan to short fiction. Avoid subplots that cannot pay off within the
word budget, lore tours, delayed inciting incidents, and endings solved by new
information or unseeded powers.

Default to names absent from the registry and readily distinguishable from
reserved aliases and close variants. Reuse a name only when it has clear
narrative meaning, and state whether it is the same identity or a distinct
identity. Never infer a crossover from a matching name. The primary coordinator,
not the architect, updates `stories/NAMES.md` after verifying the plan.

The only permitted write is `stories/<slug>/02-story-plan.md`. Do not edit the
prompt, canon brief, prose, review, final artifacts, metadata, production
record, registry, index, universe notes, source archive, or another story.

Return exactly:

```text
PLAN_CHANGE_REPORT
story: <slug>
modifiedFiles:
- stories/<slug>/02-story-plan.md
inputPromptSha256: <raw-byte lowercase sha256>
inputCanonBriefSha256: <raw-byte lowercase sha256>
newPlanSha256: <raw-byte lowercase sha256>
plannedNameForms: <complete list or none>
requiresNameRegistrationAndCheck: true
requiresUserRuling: false
requiresCoordinatorRepair: false
rulingQuestion: none
```

On a record-integrity block, keep the header, report `modifiedFiles: none` and
`requiresCoordinatorRepair: true`. On a user block, report `modifiedFiles:
none`, `requiresUserRuling: true`, and the exact `rulingQuestion`.
