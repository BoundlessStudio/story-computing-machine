# Decisions prompt-fidelity gates

Use the installed `$decisions` skill for two required checkpoints in new story
generation. Send the complete current `prompt.md`, including later user
directions, the complete target artifact, and every supplied original image in
`art/references/`. Inspect the originals and check that the folder matches the
reference inventory in the prompt before preparing a request. A missing original
is an unresolved input, never permission to omit the image or invent its contents.

Append a factual inventory after the verbatim request, using exactly this heading
and one original filename per bullet. Use `- None` when there are no supplied
images. The helper requires this inventory and rejects missing or unlisted files
before calling the API. Keep the original request and later directions intact.

```markdown
## Supplied reference images
- `Red signal.png`
- `Blue signal.png`
```

The checkpoints supplement the existing independent readings and discussion.
They judge fulfillment of this request, not literary merit, general taste, or
whether a story should become canon. They do not reopen finished stories.
Automatic fresh starts apply to the active, authorized generation task; they
never unlock a canon package or expand a localized edit into a rewrite.

## When to run

- **Outline:** after the independent request readings and outline round-robin,
  before the coordinator authorizes drafting. Judge concrete planned beats,
  agency, conflict, and payoff at outline granularity; polished prose is not
  expected yet.
- **Final story:** after the fresh whole-story readings, discussion, and resulting
  prose revisions, before generating story art or proceeding to rating/handoff.
  Send the current whole prose, without the outline, author explanations, earlier
  scores, or editorial notes. Judge what the story actually delivers.

Keep checkpoint results away from cold readers until their independent first findings are
recorded. If later directions, a changed reference, or a substantive revision
changes fulfillment, repeat the affected checkpoint on the complete new artifact.
Do not rerun unchanged work or rephrase the rubric to obtain a more favorable
sample. A final prose change after the checkpoint invalidates it when that change
could affect prompt or reference fidelity; a mechanical correction does not.

## Meaning of “honors” and the yes/no decision

Use one boolean `choice` question, `honors_request`, with values `true` (Yes)
and `false` (No). Preserve its native `confidence` and both answer probabilities.
This is a fulfillment decision; it has no rating or score threshold. Native
confidence is distinct from `P(Yes)` and is not measured judgment accuracy.

The central question is: **Does this outline or story deliver the story the
[WP] asks for?** Read the [WP] first and identify its defining premise and
narrative promise: the requested situation, characters or relationship, event
or turn, and payoff if specified. Those elements must drive the actual planned
or enacted story, rather than appear as incidental mentions in a different one.

Explicit later user story directions refine or change that promise, and relevant
reference-image features clarify the story the user asks for. Follow an explicit
change of viewpoint, tone or plot where it supersedes the original wording.
Do not invent a required motive for a hesitation, emotional arc, mechanism,
genre, moral, scale or ending that the user leaves open. A rejected image shows
the problem to avoid; incidental appearance is not a separate matching test.

“Yes” means the candidate meaningfully plays out that story promise. “No” means
a material contradiction, omission or displacement of it. Creative elaboration,
unspecified choices and minor nonmaterial gaps are allowed. Honor actual user
constraints that shape the story, but do not grade file metadata, workflow or
art-production duties, default editorial targets, or whether an earlier draft
was discarded. This is not a literary-quality grade or an archival process
checklist. Judge an outline's concrete planned beats, choices, turn and ending;
judge the final story by what the complete prose actually delivers.

The helper includes story prose explicitly named by repository path in the
request as continuity evidence. It checks that text for changes before applying
an answer. Missing required context cannot be guessed or treated as a “No”.
A separate `source_ambiguity` predicate detects consequential ambiguity, conflict,
or missing evidence; its probability above 0.20 requires clarification. Ordinary
creative freedom is not ambiguity. Predicates have no separate confidence field.

Apply the user's selected policy in this order:

1. **Halt and ask:** native choice confidence below **0.80**, unresolved source
   interpretation, conflicting evidence, a tied or contradictory answer
   distribution, refusal, malformed/incomplete output, missing inputs, or an
   unavailable API result. Uncertainty takes precedence over restarting.
2. **Restart:** a reliable **No** with confidence at least **0.80** automatically
   starts a fresh outline or story at the failed stage. Do not patch in token
   mentions to obtain a Yes.
3. **Proceed:** a reliable **Yes** with confidence at least **0.80**, no unresolved
   source or evidence conflict, and the ordinary editorial checks satisfied.

Confidence exactly 0.80 meets the numerical boundary. Old score-based responses
cannot satisfy this gate; prepare a fresh yes/no request. Existing restart counts
and pending user questions continue to apply when the rubric changes.

Allow at most **two automatic fresh starts per stage**. The first evaluation uses
`--restarts 0`; evaluations after the first and second fresh starts use 1 and 2.
If the version after the second restart still fails, halt and ask the user for
direction. Counts persist when returning to an earlier stage. An API retry is
not a fresh start, and changing a filename or output directory does not reset
the count. The helper persists a minimum restart count for each story and stage
under `tmp/story-fidelity-state/`; passing `--restarts 0` or changing the output
folder cannot lower a recorded count. The coordinator remains the sole checkpoint
caller and records actual fresh starts in `notes.md`. Do not delete or reset the
state during production; if temporary state is lost, restore the count from notes.
An `ask_user` result also blocks subsequent evaluations at either stage until
the pending question receives a new recorded reply. Changing stage or output
folder cannot bypass the halt.

Before restarting, preserve the failed artifact in Git and briefly record its
Yes/No answer, native confidence, concrete mismatches, and restart count in `notes.md`. Keep
the user's prompt, original reference files, and editorial memory. Ask the writer
for a new approach from those inputs and the documented failure, with freedom to
choose a better structure. An outline restart returns to outline discussion. A
story restart produces a new complete draft, then receives genuinely cold and
fresh readings as required by the main workflow. Keep a sound outline if it
still serves the request; if the mismatch originates in the plan, return to the
outline checkpoint before redrafting. Preserve the story package and its history.

On `ask_user`, **stop production and end the turn with one focused question**.
Include the specific prompt wording or reference feature, the relevant candidate
evidence, and the conflicting or uncertain result. Use the helper's question as
a diagnostic starting point, not a substitute for this concrete comparison.
Offer meaningful interpretations when possible. Do not restart, revise, make art,
or authorize the next stage while waiting. Record the answer verbatim as a later
direction in `prompt.md` when it concerns story content, update the keeper
independently, and assess the affected artifact again. Operational setup details
do not belong in the writing prompt; record a non-secret operational reply in
`notes.md` instead. Credentials stay in the configured environment. Save the
reply under `tmp/` and pass `--user-direction-file` to the next `run` or `assess`
when resuming. Build a fresh bundle and obtain a new API result that includes
the ruling; an older bundle/result pair cannot renew a budget. The helper checks
the prompt, candidate text, and original image bytes against the saved request
before applying it. A ruling that changes the plan can return production to the
outline checkpoint without first grading an obsolete final draft. A new content
ruling recorded in `prompt.md` renews the halted stage's
bounded restart budget; an operational reply does not. A previously consumed
reply cannot resume another halt or renew the budget repeatedly. The original
counts and actions remain in the history and notes.

## Running the checkpoint

Read the global Decisions skill for authentication and multimodal support. Prefer
its MCP tool when available. The repository helper constructs stage-specific
questions and applies the same deterministic policy; it does not duplicate the
API client and never rewrites or deletes story files.

From the worktree root, prepare a bundle for MCP:

```powershell
python .agents/skills/story-create/scripts/fidelity_checkpoint.py build --story-dir stories/<slug> --stage outline --output tmp/<slug>/outline-0/bundle.json
```

Pass the bundle's **`request` object**, not its metadata wrapper, to
`decisions_create`. It includes the full text and labelled original image paths;
the Decisions adapter sends the actual image bytes. Save the returned native
`structuredContent` as `response.json`, then apply the gate:

```powershell
python .agents/skills/story-create/scripts/fidelity_checkpoint.py assess --bundle tmp/<slug>/outline-0/bundle.json --response tmp/<slug>/outline-0/response.json --restarts 0 --output tmp/<slug>/outline-0/decision.json
```

When the MCP tool is not loaded, one command invokes the installed global client
through stdin and records the bundle, native response, and decision:

```powershell
python .agents/skills/story-create/scripts/fidelity_checkpoint.py run --story-dir stories/<slug> --stage outline --restarts 0 --output-dir tmp/<slug>/outline-0-cli
python .agents/skills/story-create/scripts/fidelity_checkpoint.py run --story-dir stories/<slug> --stage final --restarts 0 --output-dir tmp/<slug>/final-0-cli
```

Use a fresh output location for each actual evaluation. Outputs stay under the
active worktree's ignored `tmp/`; the helper refuses to overwrite existing files.
Only the compact Yes/No answer, confidence, action, useful evidence, restart count, and
user rulings belong in `notes.md`. Do not add a scorecard or raw API files to the
story package. Outline and final decisions remain separate.

Exit codes are **0 = proceed**, **10 = restart**, and **20 = ask the user**.
`build` only prepares evidence; its success is not a fidelity decision. Always
read the action JSON. Use `--conflict "<specific evidence>"` with `assess` or
`run` when the coordinator or readers find a contradiction the API overlooks;
this produces `ask_user` even if the native confidence would otherwise permit proceeding.

For legacy layouts, preserve the authorized package and construct the equivalent
MCP request from its actual full prompt/prose files rather than renaming them.
The bundled preparation commands target current-format packages. For a legacy
revision, the coordinator applies the same policy to the native MCP result;
a fresh whole-story restart still requires authorization for that scope.

Decisions uses the configured API key and API billing. No subscription-token
extraction, fabricated fallback decisions, silent image omission, or repeated paid
sampling is part of this checkpoint. Restore missing inputs or access, or report
the incomplete checkpoint in the question to the user. In particular, uncertain
visual judgments must not automatically destroy a valid draft.
