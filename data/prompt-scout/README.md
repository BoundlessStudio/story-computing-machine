# Writing Prompt Scout

This directory is the durable memory for the on-demand `prompt_scout` agent.
Each scan examines the newest 100 r/WritingPrompts posts tagged `[WP]` whose
Reddit IDs are not already in the ledger. It ranks every prompt, presents the
best ten, and retains the remaining rankings instead of silently discarding
them.

## Run it

Ask Codex:

> Run the prompt scout.

The agent fetches candidates, scores all of them, writes `latest.md`, and returns
the top ten in the task. It is not scheduled and does not interact with Reddit
beyond reading public listing pages.

## Calibrate it

Ask Codex:

> Run the prompt calibrator.

The separate `prompt_calibrator` agent examines ranks 11–100 and chooses ten
informative comparisons: near-cutoff alternatives, ambiguous matches, diverse
genres, and a small lower-ranked exploration sample. It will ask you to order
those ten from most to least interesting. The order is stored as comparative
preference evidence and influences later scout runs.

Include the calibration ID shown with the set when you reply, so an answer to
an older task can never be applied to a newer set by mistake.

## Teach it

Reply using the rank numbers from `latest.md`, for example:

> Prompt scout [scan ID]: like 1, 4, and 8; dislike 3; 4 because the impossible
> premise is grounded in a relationship.

Explicit feedback is stored in `feedback.jsonl`. The feedback recorder also
updates `preferences.json`, whose token weights give later scans a modest
quantitative prior. The agent maintains higher-level, evidence-labeled semantic
preferences in `taste-profile.md`.

## Durable files

- `taste-profile.md` — human-readable preferences and confidence.
- `latest.md` — current top ten plus ranks 11–100.
- `scanned-ids.txt` — deduplication ledger.
- `rankings.jsonl` — one immutable ranking record per scanned prompt.
- `feedback.jsonl` — explicit like/dislike/neutral events.
- `preferences.json` — learned token weights and signal totals.
- `calibration-asked.jsonl` — prompts already used for calibration.
- `calibration-responses.jsonl` — recorded most-to-least orderings.
- `latest-ranked.json` — structured form of the latest complete ranking.
- `calibration/latest.md` — current user-facing calibration set.
- `calibration/sets/<calibration-id>.json` — archived calibration sets for
  delayed responses.
- `scans/<scan-id>.json` — archived candidates and rankings for each run.

`work/pending-scan.json`, `work/pending-rankings.json`, and
`work/pending-calibration.json` are ignored transactional files. A scan or
calibration is not complete until its recorder validates the transaction and
writes the durable archive, ledger, and latest outputs.

## Ranking priority

1. Explicit user feedback.
2. Inference from the user's selected starting stories and universe direction.
3. Story-engine quality and novelty.
4. Reddit engagement, used only as a close tie-breaker.

No prompt becomes a story or canon merely because the scout recommends it.
