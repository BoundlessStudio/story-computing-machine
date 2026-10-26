# Story fidelity audit

Source snapshot: 2026-10-25T05:46:49.330417+00:00 · repository commit `0a21ccb50b782129748bb8c97cd4cfe3cd534efc`.

Evaluated 535 of 535 available artifacts across 268 stories: 267 outlines/plans and 268 prose files. There are 536 requested stage slots, including one missing outline. The original-image inventory contains 91 images across 82 packages.

## Checkpoint outcomes

| Stage | Scored | Would proceed | Would restart | Needs judgment | Partial evidence | Unavailable | API errors | Pending |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Outline / plan | 267 | 0 | 0 | 266 | 1 | 1 | 0 | 0 |
| Final prose | 268 | 0 | 0 | 267 | 1 | 0 | 0 | 0 |

377 raw checkpoint scores are below 3/4; 535 assessments have minimum confidence below 0.80. Low scores with uncertainty are review findings, not reliable restart decisions. Native confidence is not measured judgment accuracy.

## Evidence gaps

- `after-the-party`: no saved outline or story plan; final prose evaluated.
- `a-seat-for-the-sun`: the saved prompt names an original image that is absent. Both stages receive partial text-based evaluation and cannot receive a complete multimodal pass.
- `the-first-year`: later requests to edit the generated table sheet are preserved as context. The sheet is explicitly an art-edit target; this audit covers outline and prose, not whether art edits were performed.

## Method and limits

The production checkpoint rubric and pure assessor were reused with restarts=0. Complete saved prompts, later directions, and each full current candidate were submitted. All saved original references were supplied as image bytes at original detail, respecting each prompt's intended use. A temporary filename/inventory adapter handled historical layouts; it did not change the prompt sent to the API. Generated covers, character sheets, location art, reviews, and notes were excluded as evaluation authority.

This retrospective batch continues through uncertain findings so all packages can be reviewed together. No outlines, stories, prompts, notes, art, canon flags, or checkpoint restart ledgers were changed. Existing historical restart budgets were not inferred. A missing old outline cannot be reconstructed, and later prompt directions may postdate a saved outline. Score differences between stages are exploratory, not proof that the prose regressed.

The Decisions API returns probabilities and confidence but no explanatory critique in these checkpoint answers. The report's reasons describe gate logic. They must not be treated as a diagnosis of which passage failed. No independent close reading of the entire corpus or empirical calibration was performed.

Source changes found after evaluation: [].

Recorded API usage: 2,659,978 input tokens, including 66,435 cached tokens; 535 attempts. Usage is reported without estimating a billed monetary amount.

## Files

- `results.csv`: all artifact outcomes and numeric dimensions.
- `results.json`: full source text, gate assessments, native answers, probabilities, timing, attempts and API usage.
- `manifest.json`: full writing prompts, image inventory and source hashes.
- `scripts/audit.py`: reproducible inventory/evaluation driver; uses the globally installed Decisions client.
- `scripts/prepare_report.py`: exact report aggregation and export.

The interactive report supports searching, stage/outcome/image/canon filters, and selecting any artifact to inspect its saved request, full text and probability distributions.

Additional scope limit: `the-old-percentage` requires continuity with `stories/empire-within/story.md` (*Nobody Spends Her Name*). The checkpoint received the saved prompt's continuity description, but did not expand that linked prior prose. Full continuity fidelity remains unverified; the raw score does not explain its cause.
