# Prompt Ranking and Calibration Archive

This directory retains historical prompt rankings, preference evidence, and
calibration state. The prompt scout that originally produced the ranking scans
is no longer part of the project.

## Calibrate it

Ask Codex:

> Run the prompt calibrator.

The separate `prompt_calibrator` agent examines ranks 11–100 and chooses ten
informative comparisons: near-cutoff alternatives, ambiguous matches, diverse
genres, and a small lower-ranked exploration sample. It will ask you to order
those ten from most to least interesting. The order is stored as comparative
preference evidence for future use.

Include the calibration ID shown with the set when you reply, so an answer to
an older task can never be applied to a newer set by mistake.

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

`work/pending-calibration.json` is an ignored transactional file. A calibration
is not complete until its recorder validates the transaction and writes the
durable archive, ledger, and latest outputs. Any old pending scan files are
historical remnants and are not consumed by an active workflow.

## Ranking priority

1. Explicit user feedback.
2. Inference from the user's selected starting stories and universe direction.
3. Story-engine quality and novelty.
4. Reddit engagement, used only as a close tie-breaker.

No archived prompt becomes a story or canon merely because it was ranked.
