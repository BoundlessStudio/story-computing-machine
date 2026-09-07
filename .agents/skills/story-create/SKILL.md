---
name: story-create
description: "Create one new or explicitly requested replacement shared-universe short story through outline, prose, review, and cover."
---

# Story create

Coordinate new `[WP]` stories and explicitly named whole-story replacements.
Before acting, read [AGENTS.md](../../../AGENTS.md) for authority, editability,
artifacts, and mandatory branch/worktree setup. Use
[story-room](../story-room/SKILL.md) for stage requirements and
[short-story-writing](../short-story-writing/SKILL.md) for prose.
Choose reasonable low-impact defaults; ask only for missing required inputs,
canon/retcon rulings, or material prompt reinterpretation.

## Workflow

1. Complete AGENTS' branch/worktree sequence before production. Retain the
   absolute worktree path and include it in every assignment. For a replacement,
   complete [Replacement](#replacement) before scaffolding.
2. Identify, resolve, and visually inspect every supplied reference original.
   Keep originals outside the story directory; if one is inaccessible, restore
   access or request reattachment. Preserve the request verbatim and scaffold
   with `../story-room/scripts/new-story.ps1`, passing every original through
   `-ReferenceImage`. Every new scaffold uses `prospective-2026-08-23`.
   The prompt inventories display names, or `None supplied`.
   Use one `[WP]` marker for the reader-facing blockquote paragraph and keep
   surrounding user context in separate paragraphs. Default to 2,500–4,000
   words unless the prompt specifies otherwise.
3. Resolve [Collection context](#collection-context). Delegate a fresh
   `story_outliner` to write only `outline.md`. Include every reference as a
   resolvable path or unambiguous attachment identifier, its requested role,
   and any compact collection anti-default brief.
4. Delegate a fresh `story_writer` to write and revise only `story.md` through
   the prose adapter. Do not expose prior prose or Voice capsules.
5. Run `Test-Stories.ps1 -Story <slug> -Phase PreReview` once. Give its concise
   result, without another file, to a fresh independent `story_reviewer`.
   Include the resolved comparison paths required below. It writes only
   `review.md` under the REVIEW contract.
6. On `REVISE`, return only blocking findings to that story's writer, allowing
   the smallest surrounding action/narration needed for repair. Repeat
   PreReview and assign a fresh reviewer every time. Do not broaden the rewrite.
7. After `PASS`, delegate `story_title_illustrator` under the TITLE IMAGE
   contract. Include every inventoried reference from every retained request
   block. Both illustrator and coordinator inspect the exact saved JPEG and
   independently apply all seven gates. Send the contract's regeneration brief
   on failure and repeat until accepted; do not capture a rejected image.
8. Complete [Publication](#publication). The four authored Markdown files and
   accepted title image remain the only current story artifacts.

## Replacement

A replacement starts with an absent target, not an edited copy. After worktree
setup, inspect only the named source's authoritative canon marker first and
apply AGENTS' lock/reconciliation rules. A replacement request never unlocks a
canon story; any separately authorized unlock must already be its own verified
marker-only commit.

Before removal, preserve every verbatim user-authored prompt or request block,
the new request, and every associated reference-image display name.
Discard only machine-owned selections, cover policy, constraints, and workflow
metadata. Resolve and inspect every original; display names alone cannot
recover images. Do not open the old outline, prose, review, cover, or historical
process artifacts for creative reuse.

Verify exact absolute paths, then remove only the explicitly named source
package and its catalog entry, captured cover, chronology placement, and bundle
`stories/INDEX.md` row when present. Preserve frozen `stories/NAMES.md` and all
universe facts. Confirm the target directory is absent. Scaffold a clean
`prospective-2026-08-23` package with all retained and new user text verbatim in
one Prompt section under minimal labels, and all originals via `-ReferenceImage`.

Continue the ordinary workflow with fresh agents, fresh cover, and collection
comparison. Do not carry forward old creative artifacts or create a backup,
replacement-history file, or managed rewrite section. Git preserves history.
Add the final slug to chronology; commit the named removal and creation together.

## Collection context

Comparison is production memory, never canon or a model to imitate.

- Before OUTLINE, resolve up to five recent passing current outlines. The
  outliner may read only their `## Story` design sections, never prior Voice
  capsules or prose.
- For an 08-23 CREATE or replacement review, resolve the six most recent passing
  current-story paths excluding the target, or all available if fewer exist.
  Give these paths only to the reviewer, which follows the bounded comparison
  procedure in [REVIEW](../story-room/SKILL.md#review).
- Before an 08-23 outline, count completed passing current stories whose base
  `## Constraints` profile is 08-23 and whose prompt has no historical
  `## Rewrite request`. At a nonzero multiple of ten, the coordinator audits
  the ten most recent qualifying stories without saving an artifact. Examine
  dialogic media, articulate competence, workplace triads, reasoning patterns,
  humor levels, and ending gestures. Give the outliner only a compact
  anti-default brief; never expose the sampled prose or Voice capsules to the
  outliner or writer.

## Publication

After the review and both saved-pixel cover reviews pass, run from the worktree:

```powershell
pwsh -NoProfile -File .agents/skills/story-room/scripts/Test-Stories.ps1 -Phase Final
python pages/build.py capture <slug>
python pages/build.py check
```

Keep the chronology placement complete before the catalog check. Capture is the
final prose-and-cover handoff. Stage the four story Markdown files,
`title-image.jpg`, `pages/catalog.json`, the captured
`pages/covers/<slug>.jpg`, and any required chronology/removal changes. Commit,
push the current branch to `origin` with upstream tracking, and open a draft
pull request against the repository's default branch. These steps are required
for completion; do not merge automatically.

Publication-state rules, prompt preservation, timestamp order, and snapshot-only
CI are defined in [AGENTS: Pages](../../../AGENTS.md#pages). Read that contract
before capture; it also governs source/catalog canon reconciliation.
