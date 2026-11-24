---
name: story-create
description: Develop or substantially revise a short story through scene experiments, cold reading, structural revision, and line editing.
---

# Story workshop

Use this skill for new `[WP]` stories and substantial authorized revisions. [AGENTS.md](../../../AGENTS.md) governs scope, canon, and the worktree. [The craft standard](references/craft-standard.md) describes the level of work and the collection's recurring habits. Use [the reader briefs](references/reader-briefs.md) to assign readings.

## 1. Understand the request

Save the complete prompt and later directions verbatim. Inspect the supplied originals and check shared facts the story relies on. The coordinator and writer each read the request before discussing a plot. Identify the experience someone would be disappointed to miss, including its scale and any specified relationship or ending. Distinguish that from choices the writer can make. Resolve genuine uncertainty about a requirement with the user when the answer would materially change the story.

Assign one `story_writer` agent to own the prose. The coordinator protects the request, arranges independent readings, and makes editorial decisions with the writer. Give the writer the full request and relevant sources.

## 2. Try the story on the page

Imagine distinct ways the premise could become a story. Find the scene each approach would make someone want to read. It may be a confrontation, a shared joke, a discovery, or an action that takes the place of conversation. Draft two short versions of a decisive scene before settling the outline. Vary the plot, point of view, or how someone tries to get what they want. If the request specifies the event, keep it and try different ways to arrive at it. Keep the trials under `tmp/`.

When dialogue carries the scene, give each speaker a concrete want, a reason to speak now, and a sense of what the listener knows. Give allies things to want from each other too. Try different ways to ask, bargain, joke, deflect, or answer. Let the action, what goes unsaid, and chosen moments of directness affect the next turn. Write the trial in prose, with the room and bodies in it. Hear how the exchange builds and how each person responds to the other.

Compare the versions on the evidence of the pages. Quote where the story took on life, where a speaker felt interchangeable, and what each version made a reader want next. For a close choice, ask an independent reader to compare the samples without the writer's preference or rationale. Capture the choice and why in the outline or notes. If both versions falter, change who can act, what they can risk, or what the setting makes possible before trying again. [Story development](references/story-development.md) gives ways to find that change.

## 3. Build the complete draft

Write a short provisional outline from the approach with the strongest scene and clearest claim to the request. Follow choices and their consequences from the opening to the ending. Put the most space where a reader needs to inhabit the story. Use summary and omissions to concentrate attention. Let the requested form determine cast, scope, and length.

Draft in scenes and let discoveries in the prose change the plan. Give the narrator a stance and the setting a particular effect on the action. Check what each listener can recover from this scene and earlier prose. Give an important account or refusal the space it deserves. Keep a reference character's presence and temperament alive at the turn and in the ending. Reread the whole draft in the writer's own voice and commit the first complete version.

## 4. Read cold, then rewrite

Assign an independent `story_reader` agent or an available reader who has seen neither the plan nor the writer's intentions. Give them the whole draft and capture their first impression from the prose alone. Then give them the complete request and relevant originals to check what the story delivers. [Use the reading brief](references/reader-briefs.md#cold-draft-or-fresh-revision).

The coordinator, writer, and reader discuss the strongest effects and most consequential problems. Test each against the page. Look for the cause in scene construction, the order of information, voice, agency, or the ending. If the distinctive premise has slipped away, rebuild the scenes that determine what actually happens. If a reply seems wrong, hear it from the listener's side and test the staging before changing the words. A reader's confusion can matter even when the chronology holds.

Rewrite the draft as needed and commit substantial revisions. Reread changed passages in context. After a change to the central choice, revelation, relationship, or ending, read the resulting whole. Use more readers where the scale of the work or an unresolved objection benefits from them.

## 5. Edit the prose

Once the structure holds, the coordinator or a line editor reads the whole settled draft and marks passages where voice, rhythm, specificity, dialogue, or the intensity of attention falls away. Preserve the strongest passages and give the writer concrete points to work from. The writer rewrites in the story's voice and checks the surrounding paragraphs for the effects of local repairs. Read the crucial exchange aloud when possible. Use [a focused dialogue check](references/reader-briefs.md#focused-dialogue-check) when an exchange remains in doubt.

Use `scripts/prose_profile.py` when a suspected rhythm or speech pattern needs a closer look. Its observations point to passages. The prose and the reader's experience decide what to change.

## 6. Read fresh and finish

Assign a new independent reader who has seen neither the draft, trials, nor revision discussion. Capture their experience of the whole current prose, then give them the request for the fulfillment reading. The coordinator checks the prose against the request, the material findings, and relevant confirmed facts. Decide where the premise shapes events, why the decisive scene holds, and what earns the ending. A material remaining issue sends the story back to revision and a reread at the right scale.

Record the experiment, reader effects, substantial rewrites, and reasons in a short `notes.md`. Preserve useful dissent. Assign the finished prose its AO3 rating and content notes using [the shared boundaries](../../../universe/style-guide.md#audience-and-content-boundaries). Deliver the text package for review in the active worktree. [The package guide](../../../stories/README.md#visualization-handoff) defines the separate publication handoff.

## Testing changes to the workshop

Use this workshop as a baseline for comparing ways of writing. State what improvement you expect to see on the page. When comparing approaches, use the same prompt, sources, model, and roughly the same writing budget where possible. Record important differences. Keep both versions. Give readers the excerpts or whole stories in varied order without identifying how they were made. Ask for a preference, a quoted reason, and what each version does better. Test a proposed craft improvement on more than one relevant prompt before treating it as a collection-wide finding. Track substantial rework as well as reader response. Human readings, when available, give evidence about the intended audience. Model readings give hypotheses to check in the text.

Keep the findings that change the writing in `notes.md`. Preserve a workflow experiment's method and results if they support a new default. Research on [outline control](https://aclanthology.org/2023.acl-long.190/) motivates testing a short causal plan, and the [Dramatron study](https://arxiv.org/html/2209.14958) suggests checking motivation, subtext, and voice in the dialogue itself. The [earlier Decisions audit](../../../reports/story-fidelity-audit-2026-10-25/REPORT.md) records model judgments on saved prose.
