---
name: story-rewrite
description: "Rewrite one completed non-canon current story with explicit keep, change, remove, and outside-scope selections."
---

# Story rewrite

Use only when the user explicitly names one completed current-format,
non-canon story to rewrite. A legacy bundle containing `05-story.md` cannot use
this selection-contract workflow or its preparation script. Route an explicit
request for a named legacy story through `AGENTS.md`'s **Canon lock and legacy editing**
contract: proceed directly when `story.json` has `canon: false`. When it has
`canon: true`, no story or bundle file may be directly edited; perform the
independent canon-marker-only unlock first when authorized, verify and commit
it separately, and begin the rewrite afterward. Legacy layout alone is never
grounds to refuse an authorized edit. Read `../story-room/SKILL.md` for the
shared OUTLINE, REVIEW, and TITLE IMAGE responsibilities; use the same fresh
outliner, writer, reviewer, production adapter, and cover gates as CREATE.

## Rewrite selection contract

Translate the user's request into one scope and four selection categories. Ask
only when an ambiguity would materially change what survives.

- `REBUILD` — write a new whole story. Outside named selections is
  `FLEXIBLE`.
- `RESHAPE` — re-outline and rewrite the whole story while keeping its unnamed
  material in substance. Outside named selections is `KEEP`.
- `SELECTIVE` — edit named targets and the smallest necessary seams while
  preserving all other prose exactly. Outside named selections is
  `KEEP EXACT` and at least one Change or Remove target is required.

The outside rule is fixed by scope so the contract cannot contradict its own
editing mode. Use the four named categories below for deliberate exceptions.

Selections have distinct force:

- `Keep exact` preserves the named wording, fact, scene, name, or other element
  exactly as identified.
- `Keep in substance` preserves identity, function, relationship, fact, or
  effect while allowing new execution.
- `Change or replace` must be materially rewritten according to the request.
- `Remove` must not survive, including renamed or cosmetically disguised forms.

The rewrite request and selections amend the original prompt. They control
conflicts with it. Unnamed prior material follows `Outside named selections`.
If the same element receives conflicting selection verbs and the conflict is
not merely wording, stop for the user.

## Workflow

1. Complete the required `main` update, `codex/rewrite-<slug>` branch, and
   sibling worktree setup before reading story files. Work only in that
   worktree. Verify the prior PASS, non-canon status, and current-format layout.
2. Resolve and inspect original and new reference images. Read prior material
   according to scope:
   - REBUILD: retrieve only passages needed for named selections;
   - RESHAPE: read the prior prose for its throughline and named selections;
   - SELECTIVE: use the complete current prose as the editing base.
   Prior outline and review are production history, not creative authority.
3. Run `../story-room/scripts/prepare-rewrite.ps1` with `-Scope` and the
   applicable `-KeepExact`, `-Keep`, `-Change`, and `-Remove` values, plus the
   cover policy and new references. The script
   records `## Rewrite selections` in `prompt.md`, resets outline and review,
   and uses `prospective-2026-08-23`. REBUILD and RESHAPE reset prose to a clean
   scaffold; SELECTIVE retains the existing prose and updates only package title
   metadata when needed.
4. Delegate a fresh `story_outliner`. It reads the amended prompt and only the
   prior material allowed by scope, then writes one outline that marks retained,
   changed, removed, and seam-sensitive story functions through the existing
   Story, Voice, and Beats sections. It creates no comparison artifact.
5. Delegate a fresh `story_writer`:
   - REBUILD writes a new whole-story pass constrained by named keeps;
   - RESHAPE writes a whole-story pass preserving unnamed material in substance;
   - SELECTIVE edits the retained prose only at named targets and the smallest
     necessary causal, continuity, and language seams.
   The current craft profile governs changed prose. It does not authorize
   modernization of protected text outside scope.
6. Run PreReview and delegate a fresh independent reviewer. The reviewer judges
   the rewritten story first, then compares it with the prior version only for
   selection compliance. Exact keeps must be exact, substantive keeps must
   retain their function, Change targets must materially change, Remove targets
   must be absent, and outside-scope preservation must match the recorded mode.
   The old PASS is not evidence. Collection-level CREATE comparison does not
   apply to rewrites.
7. Resolve blocking findings through the smallest scope-compatible revision and
   use a fresh reviewer after every rerun.
8. After PASS, apply AUTO, KEEP, or REGENERATE through the shared seven cover
   gates. Run final validation, recapture, catalog check, commit, push, and open
   the draft pull request.

Git preserves the previous version. Create no backup prose, rewrite brief,
comparison report, or selection artifact outside the managed prompt section.
