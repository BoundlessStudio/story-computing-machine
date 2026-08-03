---
name: story-room
description: "Run the complete shared-universe short-story workflow for prompts tagged [WP], from branch/scaffold through candidate release."
---

# Story room

Use for `[WP]` unless the user requests one named stage. Default to a coherent 2,500–4,000 word story and record safe assumptions rather than stopping for low-impact ambiguity.

The planning, drafting, reviewing, and final-edit skills load the shared craft package through `../../writing-guides/README.md`. Keep those repository-level instructions outside guarded story inputs and authority manifests.

1. Update `main`, create `codex/story-<slug>`, and scaffold with `new-story.ps1` without overwriting an existing directory.
2. Capture the verbatim prompt and acceptance criteria.
3. Generate authority v2.
4. Checkpoint; delegate canon research; persist its exact brief.
5. Checkpoint; delegate plan creation; validate/register names.
6. Checkpoint; delegate draft creation.
7. Checkpoint; delegate draft review; persist the exact review payload; revise/re-review as required.
8. Checkpoint; delegate final edit.
9. Checkpoint; delegate final review; revise/re-review until `PASS` with no unresolved Critical/Major findings.
10. Reconcile final names and run the strict gate.
11. Complete the candidate transaction and run fast local integrity.
12. Push a pull request; full PR policy, repository, source, universe, test, and reader-site checks must pass.

The candidate remains non-canon unless the user separately authorizes promotion. Never work directly on `main`, skip a dependent gate, fabricate a specialist report, or run the deferred disposable canary unless explicitly requested.
