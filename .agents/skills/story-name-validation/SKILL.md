---
name: story-name-validation
description: "Validate and reconcile character-facing names in stories/NAMES.md for planning, final release, and canon promotion."
---

# Story name validation

Read `stories/NAMES.md` before proposing or approving any name. Character-facing names include full names, given names, surnames used alone, mononyms, aliases, usernames, titles used as names, named animals, constructs, and person-like entities.

At the plan gate, inventory all proposed names, check exact/alias/reversal/close/confusable collisions, document deliberate reuse, then let the coordinator register them. At the final gate, compare the final prose and delta with the plan and story-scoped registry rows. Every actual character-facing name must be registered; a non-character candidate may appear only in the reviewed three-column delta allowlist.

Run:

```powershell
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryNames.ps1 -Story <slug> -Phase Plan -OutputFormat Json
pwsh -NoProfile -File .agents/skills/story-integrity/scripts/Test-StoryNames.ps1 -Story <slug> -Phase Final -OutputFormat Json
```

Receipts use `checkerVersion: story-names/3` and record checked paths, time, warnings, and pass/fail result. They do not duplicate file identities. The coordinator alone edits `stories/NAMES.md`.
