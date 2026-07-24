---
name: prompt-calibration
description: "Select informative prompts from the latest scout ranks 11–100, ask the user to order them, and record the ordering as comparative taste evidence."
---

# Prompt Calibration

Use this skill for on-demand taste calibration after at least one complete
prompt-scout scan. It does not fetch Reddit or start story production.

## Create a calibration set

1. Read `data/prompt-scout/latest-ranked.json`,
   `data/prompt-scout/taste-profile.md`,
   `data/prompt-scout/preferences.json`, recent feedback, and
   `data/prompt-scout/calibration-asked.jsonl` when present.
2. Consider only prompts ranked 11 or lower in the latest scan. Exclude every
   post ID already present in the calibration-asked ledger.
3. Select ten prompts for information value, not predicted quality alone:
   - include near-cutoff prompts that could plausibly enter the top ten;
   - include uncertain matches where positive and negative signals compete;
   - cover different genres, tones, stakes, and premise structures;
   - include a small exploration sample from lower ranks to detect blind spots.
4. Write `data/prompt-scout/work/pending-calibration.json`:

   ```json
   {
     "scanId": "copied from latest-ranked.json",
     "prompts": [
       {
         "postId": "Reddit post ID",
         "selectionReason": "Why this comparison would teach us something."
       }
     ]
   }
   ```

5. Run
   `.agents/skills/prompt-calibration/scripts/record-prompt-calibration-set.ps1`.
   It validates the selection, appends the asked ledger, and creates
   `data/prompt-scout/calibration/latest.md`.
6. Present all ten and ask for a complete most-to-least ordering using the
   calibration numbers, for example:
   `Calibrator [20260723T014038Z-014828] order: 3, 1, 8, 6, 2, 10, 4, 7, 5, 9`.

If fewer than ten eligible prompts remain, select and ask about every remaining
eligible prompt. Never recycle a previously asked post merely to reach ten.

## Record an ordering

1. Resolve the user's complete ordering against the archived calibration set
   named by its calibration ID. If the user omitted the ID in the same task that
   displayed the set, use that displayed ID explicitly; never substitute a
   newer set.
2. Run
   `.agents/skills/prompt-calibration/scripts/record-prompt-calibration-response.ps1`
   with `-CalibrationId <id> -Order ...`.
3. The recorder logs every comparative position and applies a centered weight:
   the most interesting prompt receives +1, the least receives -1, and prompts
   between them are interpolated. These weights influence but do not dictate
   later semantic ranking.
4. Review the new ordering with earlier explicit feedback. Update
   `data/prompt-scout/taste-profile.md` only with evidence-backed patterns,
   including support count, contradictions, and confidence.

## Boundaries

- Do not fetch Reddit; calibrate only against a completed scout batch.
- Do not select any current top-ten prompt or previously asked calibration ID.
- Do not edit `universe/`, `stories/`, or story indexes.
- Do not infer a permanent dislike from a single relative ordering.
- Run on demand only; do not create or modify schedules.
