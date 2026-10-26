# Story fidelity audit — [WP]-focused Yes/No

Evaluated **268 saved prose files** captured at source revision `0a21ccb50b782129748bb8c97cd4cfe3cd534efc` with the [WP]-focused yes/no checkpoint. This is a frozen snapshot, not a claim about subsequent edits on main. No outlines were rerun in this corpus audit. Earlier evaluations remain preserved. Story rewrites are excluded from the checkpoint PR.

| Outcome | Stories |
| --- | ---: |
| Would proceed | 246 |
| Would restart at initial attempt | 0 |
| Needs user judgment | 21 |
| Partial evidence | 1 |
| API errors | 0 |
| Pending | 0 |

Native answers: 267 Yes and 1 No. 21 confidence values are below 0.80; median native confidence is 0.98. Raw answers are separate from the workflow outcome.

## Meaning of honors and policy

The question is: **Does this outline or story deliver the story the [WP] asks for?** Its defining premise and narrative promise must drive the actual story: the requested situation, characters or relationship, event or turn, and payoff if specified. Explicit later user story directions refine or change that promise, with reference images used in their intended role. No means a material contradiction, omission or displacement of that promise. Creative elaboration and minor nonmaterial gaps are allowed. Do not invent a motive, emotional arc, moral or ending left open by the user. This is not a grade for literary quality, production history, workflow duties, art tasks or default editorial targets.

Use one native boolean choice and preserve its confidence and both probabilities. A reliable Yes with confidence >=0.80 proceeds; a reliable No at that confidence restarts the failed stage. Low confidence, conflicting evidence, unresolved source interpretation, missing inputs, refusals, and invalid answers ask the user. At most two automatic fresh starts per stage; persistent counts and pending questions cannot be cleared by changing stages, filenames, or the rubric.

This retrospective audit uses restarts=0 to describe the initial-attempt action. It does not revise or restart historical stories or write production halt/restart state. Native confidence has not been calibrated as judgment accuracy. Different confidence distributions under the two question designs do not demonstrate improved accuracy.

## Pilot cases with the revised WP question

| Story | Native answer | Confidence | Outcome |
| --- | --- | ---: | --- |
| A Darkness Written Under Skin | Yes | 0.90 | Would proceed |
| A Perfectly Normal Hobby | Yes | 0.38 | Needs judgment |
| Before She Paints the Ending | Yes | 1.00 | Would proceed |
| The Kill She Wouldn't Take | Yes | 0.72 | Needs judgment |
| The Old Percentage | No | 0.56 | Needs judgment |

- **A Darkness Written Under Skin:** Questionable earlier No on the invisible-tattoo/black-light premise. Targeted reading finds the UV reveal and demonstrated magical faculty; the current question asks whether that story promise is played out.
- **A Perfectly Normal Hobby:** The supplied image is expressly a rejected depiction. The rubric must use it as a problem example rather than require copying it.
- **Before She Paints the Ending:** Comparison case with a high earlier score, original image, and later plot/scale directions. It is not a gold-standard accuracy label.
- **The Kill She Wouldn't Take:** Low earlier score; later directions require broadcaster viewpoint, sustained sportscaster energy and a binding character image.
- **The Old Percentage:** Low earlier score; required continuation context was previously unexpanded. The new request includes the full named prior story.

## Evidence and verification

- 91 saved original images across 82 packages were supplied as actual image bytes at original detail.
- A Seat for the Sun still lacks its named original image; its result is partial evidence and cannot pass the gate.
- The Old Percentage now receives the full explicitly named prior story, Nobody Spends Her Name, as continuity evidence.
- The First Year includes art-edit directions in its prompt; this audit evaluates prose fulfillment, not whether the generated sheet was edited.
- Source files changed during evaluation: 0. Sources matching the earlier snapshot: 268/268.
- Production helper: 34 local behavioral tests and all 9 independent forward-test groups passed, including persisting preparation-error halts across stages.
- Recorded API usage: 1,637,161 input tokens, including 49,205 cached; 269 attempts. The five pilot calls are included in this total. No billed monetary amount was inferred.

## Review files

- `binary/results.csv`: current yes/no decisions, native confidence, probabilities, workflow outcomes and old prose scores for context.
- `binary/results.json`: current native responses, assessments, full prose, timing, usage and source identifiers.
- `binary/manifest.json`: current complete prompts, original-image inventory, required continuity text and source hashes.
- `binary/fidelity_checkpoint.py`: pinned helper used for the audit.
- `binary-v1/`: preserved broader Yes/No audit and its reader conflict.
- `results.json`, `results.csv`, `manifest.json`, `SCORE-REPORT.md`: preserved earlier 0–4 audit, including outlines.
- The same interactive report defaults to the current WP-focused prose audit and has selectors for the earlier broader Yes/No audit and the earlier score audit, including outlines.

## Targeted reading notes

### The Kill She Wouldn't Take — the [WP] promise drives the story

The earlier broader question returned No at 0.94. The WP-focused question now returns Yes at 0.72, so it still requires user judgment under the unchanged confidence floor. The unchanged prose uses the requested broadcasters' viewpoint and sustained commentary, demonstrates respawn, then makes the superstar's hesitation drive the medical stoppage. Its red mohawk, horned white mask, white armor and oversized gun preserve the reference's recognizable features. The coordinator and independent reader inspected the same full prose and original image; neither identified a material contradiction of this story promise. Native answers from both questions are preserved.

### A Darkness Written Under Skin — the tattoo and black-light hook is played out

The earlier broader question returned an uncertain No at 0.58. The WP-focused question returns Yes at 0.90. The apparently unmarked protagonist is revealed under violet light, and a controlled test demonstrates the hidden mark's faculty. That is the defining premise of the saved WP. This is a targeted source-based reading, not an independent accuracy label for the full corpus.

## Controlled mismatches

Two temporary modified copies test rejection of a different story or a directly contradicted WP fact; original story files were unchanged.

| Control | Expected | Native answer | Confidence | Action |
| --- | --- | --- | ---: | --- |
| Full deathmatch prose evaluated against the invisible-tattoo [WP] | No | No | 0.90 | restart_story |
| Original goth/witchcraft prose plus an explicit ending that contradicts the completely-oblivious-parents requirement | No | Yes | 0.44 | ask_user |

One control returned the expected confident No. The explicit parents-always-knew contradiction returned Yes at 0.44: a semantic miss, caught by the confidence gate as ask_user. Neither control automatically proceeded. This is not proof of corpus-wide accuracy.


## Live outline checkpoint observations

Five subsequent outline calls are preserved in `checkpoint-trials.json`, without candidate rewrite text. The mafia outline returned Yes at 0.90 confidence; the goth outline returned Yes at 1.00. The sky outlines returned uncertain Yes at 0.20, No at 0.28, and Yes at 0.26. The assessor allowed two outlines to proceed and referred all three uncertain results to the user. No final-story gate ran and no automatic restart was triggered; one fresh start was explicitly user-directed.

The later sky request clarified that outside others must provide the bridge making magic possible in the magicless world. That change of evaluation input limits comparisons across its attempts. These observations show the halt policy operating; they do not measure literary improvement or classifier accuracy. Candidate rewrites remain on a separate local branch and are not merged.

## Source and build files

The interactive report source is in `report-app/`. Its stable artifact identity is preserved, and all three original audit versions remain available. Generated split builds and portable offline exports are ignored by Git and can be rebuilt with the installed Data plugin. The runtime authoring guide inside the app records the build command. Credentials and temporary live-request/production-state files are not committed; saved native results and snapshot input records provide the audit evidence.
