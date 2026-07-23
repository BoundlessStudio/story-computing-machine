---
name: prompt-scout
description: "Scan the newest 100 previously unscanned r/WritingPrompts [WP] posts, rank all of them for this user's tastes, return the top 10, and learn from explicit feedback."
---

# Prompt Scout

Use this skill only for on-demand discovery or feedback about Reddit writing
prompts. It does not start the story-room workflow and never changes canon.

## Scan mode

1. Read `prompt-scout/README.md`, `prompt-scout/taste-profile.md`,
   `prompt-scout/data/preferences.json`, and recent entries in
   `prompt-scout/data/feedback.jsonl` when present.
2. Calibrate against the current starting-set prompt contracts and portable
   seeds named in the taste profile. Treat those as taste evidence, not canon.
3. Run `scripts/get-writing-prompts.ps1`. Its default and maximum batch is the
   newest 100 `[WP]` posts whose Reddit IDs are absent from
   `prompt-scout/data/scanned-ids.txt`.
4. Read `prompt-scout/data/pending-scan.json` and score every prompt from 0–100:
   - 0–45: demonstrated personal fit;
   - 0–25: strength of the story engine (choice, conflict, consequence);
   - 0–15: fit with the project's broad thematic interests;
   - 0–10: novelty or productive subversion;
   - 0–5: compatibility with the project's accessible content ceiling.
5. Reddit score and comments may break a close tie but may not replace taste
   judgment. Do not infer preferences from popularity.
6. Write `prompt-scout/data/pending-rankings.json` with this shape:

   ```json
   {
     "scanId": "copied exactly from pending-scan.json",
     "rankings": [
       {
         "postId": "Reddit post ID",
         "score": 0,
         "reason": "One concrete sentence explaining fit or lack of fit.",
         "tags": ["two", "to-five", "concise-tags"]
       }
     ]
   }
   ```

   Include exactly one entry for every candidate and no extra IDs.
7. Run `scripts/record-prompt-scan.ps1`. It validates completeness, generates
   ranks, appends all results to the durable ledger, marks the IDs scanned,
   archives the scan, and writes `prompt-scout/latest.md`.
8. Return the top ten in rank order with links and one-line reasons. End with
   the scan-specific feedback syntax, for example:
   `Prompt scout [20260723T014038Z]: like 1, 4; dislike 7; 4 because ...`.

If fewer than 100 unscanned `[WP]` posts can be reached after the script's
pagination limit, report the exact count and rank all of them. Never reintroduce
already-scanned IDs merely to fill the batch.

## Feedback mode

1. Interpret `like`, `dislike`, and `neutral` rank numbers against the archived
   scan named by the user. If the user omitted a scan ID in the same task that
   displayed a ranking, use that displayed scan ID explicitly; never silently
   substitute a newer scan.
2. Run `scripts/record-prompt-feedback.ps1 -ScanId <id>` with those rank numbers
   and any supplied note. The script logs immutable feedback events and updates
   learned token weights.
3. Review the new signals alongside prior feedback. Update
   `prompt-scout/taste-profile.md` only for semantic preferences supported by
   explicit evidence. Record confidence and contradictory evidence.
4. Do not run a new Reddit scan unless the user also asks for one.

## Boundaries

- Read Reddit only. Never vote, post, comment, message, or log in.
- Do not copy response stories or comments; only prompt-post metadata is kept.
- Do not edit `universe/`, `stories/`, or `stories/INDEX.md`.
- Do not turn a selected prompt into a story unless a later user request invokes
  the appropriate story workflow.
- Run on demand only. Scheduling remains outside this workflow.
