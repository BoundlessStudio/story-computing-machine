# Story Computing Machine

A shared-universe home for short stories. Its main job is to turn a writing prompt into prose worth reading. Characters, continuity, and art serve that job.

## Start with `[WP]`

Give Codex a prompt such as:

```text
[WP] Every city has a ghost assigned to it. Tonight, ours resigns.

About 3,000 words. Close third person. Melancholy but hopeful.
```

Codex keeps your request intact, develops a story with a writer agent, and brings in independent readers, including Claude when available. The first readings happen separately. Then the writer, readers, and editor discuss what actually worked or failed in the prose; the writer revises and they read again. A cover normally follows once the prose is ready; extra reference or location art is made when it helps the finished story. [The story workshop skill](.agents/skills/story-create/SKILL.md) explains the practice.

The story's `notes.md` keeps the useful editorial memory: what readers experienced, what caused a problem, what was changed, whether it worked, and which objections were deliberately left open. Git records substantial draft and revision rounds. There are no scores, file hashes, scripted approvals, or required number of rounds.

## Where things live

- [stories/](stories/README.md) — prompts, prose, editorial notes, and selected story art. Older packages retain their previous layout.
- [universe/](universe/README.md) — shared facts and the small set of narrative boundaries. A story becomes canon only with your explicit approval.
- [art/](art/README.md) — earlier character and location art that existed only in the retired site snapshot.
- [illustrated/](illustrated/README.md) and [graphic-novels/](graphic-novels/README.md) — existing editions, preserved as authored artifacts.
- [AGENTS.md](AGENTS.md) — permissions, worktree rule, and the few repository boundaries.

The GitHub Pages site, galleries, publication captures, CI, and their scripts have been retired from this repository. Read stories directly in Markdown or through the files in a pull request. Future presentation can be built as a separate project without shaping how stories are written here.

## Revising a story

Name the story and the change you want. Non-canon stories can be edited within that scope; a substantial revision benefits from fresh readers and discussion. A canon story must be explicitly unlocked by name before its package changes. No review or general invitation to improve the collection unlocks it.

Work happens in a branch and dedicated worktree, then a pull request for your review. Nothing merges automatically.

The pre-cleanup backup branch `codex/backup-main-2026-09-27` at `d9c6d293` preserves the former site, scripts, and publication snapshots for recovery.
