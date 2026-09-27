---
name: story-create
description: Write or substantially revise a [WP] short story through agent conversation, independent reading, and evidence-led revision.
---

# Story workshop

The aim is a story a reader wants to finish and remember. Establish the dedicated worktree from updated `main` before production, then read [AGENTS.md](../../../AGENTS.md) for permission and files. Use this as a practice, not a sequence of verdicts. Make room for discovery and revise the underlying scene or premise when a line edit cannot solve the problem.

## Begin with the story

Keep the user's `[WP]` request verbatim in `prompt.md`, including later user-authored constraints. Record the audience, intensity, and content note required by the style guide. List every supplied reference-image display name and inspect every original before creative work. If one cannot be accessed, restore access or ask for reattachment; never silently omit it. Read relevant [universe authority](../../../universe/README.md) and the short [style guide](../../../universe/style-guide.md); search only facts the story will use. For an existing story, verify its canon marker before reading it for an edit.

The writer and coordinator should talk briefly about the prompt's live possibility: who or what matters, what could change, what form might reveal it, and the most obvious version worth avoiding. Invite Claude or another reader to challenge a premise when that could save a weak draft. An outline is available when it helps; it is not a contract or a gate. Let the writer choose length, voice, structure, and ending from this prompt. A draft may depart from the plan when the story improves.

Give a Codex writer agent ownership of the prose and room to make substantive choices. The coordinator owns editorial judgment, not the sentences. The writer may use `creative-writing-craft` for a specific craft need and `dialogue`, `story-sense`, or `prose-style` to diagnose a problem. Use those references only for the problem at hand; they do not add stages or separate reports. The writer reads the complete story aloud or skeptically in mind before handoff, watching reader knowledge, scene consequences, dialogue uptake, and whether the ending earns its effect. Commit the first complete draft before review so later changes can be understood.

## Read independently, then talk

For a new complete story or a substantial rewrite of a non-canon story, obtain a cold Codex reader subagent and a cold Claude reading. If Claude cannot be used, recruit another independent reader and say what changed. Give each only the full prompt and current story, without the outline, `notes.md`, prior reviews, the writer's explanation, or the other reader's response. For Claude's first read, start a fresh Claude Code session in bare mode with tools disabled; pass the complete prompt and prose text directly, not repository paths. Keep its session ID and resume that session for later discussion. Do not expose other files or feedback until the first reading is delivered. Preserve short, attributed excerpts of each reader's first observations in their own words in `notes.md` before discussion; keep the coordinator's interpretation separate and do not rewrite those observations when opinions change.

Ask each reader what held attention or feeling, where the story lost them, what they believed happened, and which passages created those effects. Ask for the most consequential weakness even when the story is broadly successful. Have them distinguish a demonstrated problem from a taste preference, and identify what is already working and should survive revision. A checklist, number, or PASS is not a substitute for a reader's account.

Then convene an actual exchange. Relay each participant's own words to the others instead of replacing them with the coordinator's summary. Resume Claude's same session for follow-up; if that session is lost, record the break honestly. Let the writer explain intent, challenge a reading, and propose or reject repairs. Ask the readers to clarify their evidence, respond to each other, and test proposed changes. The coordinator returns to the text to decide which concerns deserve action. Do not settle disagreements by vote. An explanation of authorial intent can clarify a deliberate effect; it does not erase an effect a cold reader experienced. Keep reasoned dissent visible when the choice is to preserve the passage.

Focus first on the issues with the greatest effect on the story: attachment and desire, causal movement, scene purpose, point of view, dialogue, revelation, and ending. Use specific passages. Widen a revision when the cause is structural; protect strong scenes and lines that a proposed fix would damage. If a repair repeatedly fails, reconsider the scene's job or the story's premise instead of polishing the same surface.

## Revise and remember

The writer revises `story.md` directly. Commit each substantial editorial round with a plain description of the change. Continue the conversation with readers to find whether the reported effect has changed and what the revision may have broken. After a structural rewrite, a new cold reading is useful because returning readers know the intended repair. After the last substantial revision, require an independent reader to read the entire current prose from beginning to end, not just the diff. Repeat discussion and revision while there is a material issue the coordinator would act on; there is no required round count.

Use `notes.md` as a compact, dated memory for the next writer or editor. Keep the original reader effects, the passages that caused them, the writer's response, the coordinator's reasoning, what changed, what rereading showed, and important unresolved disagreement. Include short before/after excerpts where Git's eventual merge style might otherwise hide the actual repair. Record decisions and lessons, not a full transcript or a form full of empty fields. A later round can correct an earlier diagnosis without erasing it.

Once the prose works, check the prompt, relevant shared facts, names that might confuse readers, and internal time, space, knowledge, and object continuity. Resolve a canon conflict with the user; do not distort the story to satisfy a routine check. The coordinator states why the current version is ready, including any deliberate dissent, in `notes.md` and the pull request. No SHA-256 pin, script, test suite, or numeric review verdict certifies the story.

## Art and handoff

After the prose is ready, create a cover for a new `[WP]` story by default unless the user asks for prose only. Other story art is optional and should serve the finished story. Use the built-in image-generation skill, attach relevant inspected originals and accepted story art, and inspect the saved pixels for story fidelity, coherent objects and anatomy, readable title if present, and an image that invites the right story. Before reusing legacy story art, consult `art/selection-notes.json`; prefer a selected correction over an excluded original. Keep only selected art in the story package. No reference-sheet quota, gallery capture, or site build is part of `[WP]`.

Commit the story, notes, and selected art on the story branch. Push and open a draft pull request for the user to review. Do not merge it automatically. A localized non-canon edit can use a smaller version of this conversation, while a substantive rewrite deserves fresh whole-story reading. Preserve legacy package layouts and prior reviews as history.
