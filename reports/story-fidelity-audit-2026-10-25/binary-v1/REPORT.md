# Story fidelity audit — Yes/No update

Evaluated **268 of 268 current prose files** with the yes/no checkpoint. No outlines were rerun. The earlier score audit and all source packages are preserved.

| Outcome | Stories |
| --- | ---: |
| Would proceed | 68 |
| Would restart at initial attempt | 20 |
| Needs user judgment | 179 |
| Partial evidence | 1 |
| API errors | 0 |
| Pending | 0 |

Native answers: 155 Yes and 113 No. 175 confidence values are below 0.80; median native confidence is 0.58. Raw answers are separate from the workflow outcome.

## Meaning of honors and policy

The artifact must materially fulfill the requested premise, explicit requirements, intended experience, and relevant original-image features at its stage. Later user directions supersede earlier conflicts. Minor nonmaterial gaps and unspecified choices may still honor the prompt. Workflow metadata, art-edit duties, identified editorial defaults, and incidental image details are not automatically story requirements. A rejected example must not be copied as visual authority.

Use one native boolean choice and preserve its confidence and both probabilities. A reliable Yes with confidence >=0.80 proceeds; a reliable No at that confidence restarts the failed stage. Low confidence, conflicting evidence, unresolved source interpretation, missing inputs, refusals, and invalid answers ask the user. At most two automatic fresh starts per stage; persistent counts and pending questions cannot be cleared by changing stages, filenames, or the rubric.

This retrospective audit uses restarts=0 to describe the initial-attempt action. It does not revise or restart historical stories or write production halt/restart state. Native confidence has not been calibrated as judgment accuracy. Different confidence distributions under the two question designs do not demonstrate improved accuracy.

## Pilot cases

| Story | Native answer | Confidence | Outcome |
| --- | --- | ---: | --- |
| A Darkness Written Under Skin | No | 0.58 | Needs judgment |
| A Perfectly Normal Hobby | Yes | 0.32 | Needs judgment |
| Before She Paints the Ending | Yes | 0.92 | Would proceed |
| The Kill She Wouldn't Take | No | 0.94 | Needs judgment |
| The Old Percentage | No | 1.00 | Would restart |

- **A Darkness Written Under Skin:** Low earlier prose score on the invisible-tattoo/black-light premise. Targeted reading finds the UV reveal and a demonstrated magical faculty on the page; the uncertain No is not an established failure.
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
- Production helper: 32 local behavioral tests and all 9 independent forward-test groups passed, including persisting preparation-error halts across stages.
- Recorded API usage: 1,615,721 input tokens, including 34,443 cached; 268 attempts. The five pilot calls are included in this total. No billed monetary amount was inferred.

## Review files

- `binary/results.csv`: current yes/no decisions, native confidence, probabilities, workflow outcomes and old prose scores for context.
- `binary/results.json`: current native responses, assessments, full prose, timing, usage and source identifiers.
- `binary/manifest.json`: current complete prompts, original-image inventory, required continuity text and source hashes.
- `binary/fidelity_checkpoint.py`: pinned helper used for the audit.
- `results.json`, `results.csv`, `manifest.json`, `SCORE-REPORT.md`: preserved earlier 0–4 audit, including outlines.
- The same interactive report defaults to current prose and has an earlier-audit selector for all previous outline/prose results.

## Targeted reading notes

### The Kill She Wouldn't Take — confident No conflicts with a targeted reading

The coordinator and an independent reader found the requested later broadcaster viewpoint and sustained sportscaster energy, the demonstrated respawn followed by the superstar's plot-driving hesitation, and the reference's red fiber-optic mohawk, white horned mask, segmented white armor and oversized gun in the full prose. The API returned No at 0.94 without naming a violated requirement. These source-based readings conflict with that answer; obtain user direction before restarting.

### A Darkness Written Under Skin — uncertain No needs evidence review

The API returned No with confidence 0.58. A targeted whole-prose reading finds the apparently unmarked protagonist, the black-light reveal, the world of ink-based birth faculties, and a demonstration of the hidden mark rejecting magical warmth while ordinary heat still works. This supports the literal premise; the API has not identified a missing requirement. Its low-confidence answer remains a review question, not a proven failure.
