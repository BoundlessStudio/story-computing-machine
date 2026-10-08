# Story Computing Machine

A shared-universe home for short stories. Its main job is to turn a writing prompt into prose worth reading. Characters, continuity, and art serve that job.

## Start with `[WP]`

Give Codex a prompt such as:

```text
[WP] Every city has a ghost assigned to it. Tonight, ours resigns.

About 3,000 words. Close third person. Melancholy but hopeful.
```

Codex keeps your request intact. A writer makes a brief, provisional outline and independent readers challenge its story choice before drafting. New readers then read the complete draft separately, talk with the writer about what worked or failed, and read the revision. When the room thinks the prose is ready, fresh readers see the whole story without that discussion and can surface what everyone else missed. Character sheets and references for the story's important locations normally come next, covering multiple distinct places when the story has them. After those references are finished and inspected, they guide the cover. [The story workshop skill](.agents/skills/story-create/SKILL.md) explains the practice.

New stories start with a General audience target unless the prompt says otherwise. Each finished story's `ratings.md` records its reviewed General, Teen, Mature, or Explicit classification and content notes under the [shared content boundaries](universe/style-guide.md#audience-and-content-boundaries).

The story's `notes.md` keeps the useful editorial memory from outline, draft, and final readings: what readers experienced, what caused a problem, what was changed, whether it worked, and which objections were deliberately left open. Git records substantial draft and revision rounds. There are no scores, file hashes, scripted approvals, or required number of rounds.

## Where things live

- [stories/](stories/README.md) — prompts, prose, editorial notes, and selected story art. Older packages retain their previous layout.
- [universe/](universe/README.md) — shared facts and the small set of narrative boundaries. A story becomes canon only with your explicit approval.
- [universe/art.md](universe/art.md) — collection visual direction and art provenance guidance.
- [AGENTS.md](AGENTS.md) — permissions, worktree rule, and the few repository boundaries.
- [tmp/](tmp/) — temporary task files and directories. Its `.gitkeep` is tracked; all other contents are ignored. Keep scratch work here inside the active worktree. [Codex boundary setup](.codex/hooks/README.md) explains the write guard.

The former GitHub Pages site, galleries, and publication captures have been retired from this repository. A separate media-only CI workflow publishes selected artwork to Cloudflare R2 for downstream use; it does not render or publish story pages. Read stories directly in Markdown or through the files in a pull request. Future presentation can be built as a separate project without shaping how stories are written here.

## Revising a story

Name the story and the change you want. Non-canon stories can be edited within that scope; a substantial revision benefits from fresh readers and discussion. A canon story must be explicitly unlocked by name before its package changes. No review or general invitation to improve the collection unlocks it.

Work uses the worktree attached to your chat through Codex's built-in workflow, then a pull request for your review. Nothing merges automatically.
