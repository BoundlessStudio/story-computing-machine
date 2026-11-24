# Optional Decisions research

The [workshop](../SKILL.md) uses close reading of the scenes and ending to assess prompt fulfillment. The Decisions helper is retained for reproducing or extending the [fidelity audit](../../../../reports/story-fidelity-audit-2026-10-25/REPORT.md). Use the installed Decisions skill when the user requests that evaluation. A model answer can raise a question for a reader to check against the page.

## Evidence

Use the complete saved request and later directions, the complete target outline or prose, and every supplied original. The helper checks the `## Supplied reference images` inventory in `prompt.md`, which uses one original filename per bullet or `- None`. It includes story texts explicitly named by repository path in the request. Keep results with the version of the text, rubric, model, and sources that produced them.

The yes/no question concerns the requested premise, experience, and explicit story directions. The native confidence has no measured relationship to correctness in this collection. Read the passages before inferring what the model may have missed. Use the same response when examining its consequences and a new response when the actual input changes.

## Reproduce the earlier procedure

Prepare the request from the worktree root and keep artifacts under `tmp/`.

```powershell
python .agents/skills/story-create/scripts/fidelity_checkpoint.py build --story-dir stories/<slug> --stage final --output tmp/<slug>/fidelity/bundle.json
```

Submit the bundle's `request` object through Decisions and save the native response. `outline` is the other stage. The following command exercises the earlier stateful decision logic. Use an isolated fixture when testing restart and halt behavior.

```powershell
python .agents/skills/story-create/scripts/fidelity_checkpoint.py assess --bundle tmp/<slug>/fidelity/bundle.json --response tmp/<slug>/fidelity/response.json --restarts 0 --output tmp/<slug>/fidelity/decision.json
```

The earlier procedure applied a 0.80 confidence boundary and allowed two restarts per stage. Exit codes from `assess` and `run` are 0 for proceed, 10 for restart, 20 for user judgment, and 30 for evidence review of a confident No. Pass `--mismatch` with a material mismatch confirmed against the request and artifact. Use `--conflict` when the reading and result disagree or the No lacks support. An evidence review can apply the same bundle and response without another call. The helper's state and outcomes describe that procedure. Editorial decisions for the workshop use the actual story, the request, and the readings.
