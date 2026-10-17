# Story Computing Machine

A shared-universe home for short stories. Its main job is to turn a writing prompt into prose worth reading. Characters, continuity, and art serve that job.

## Start with `[WP]`

Give Codex a prompt such as:

```text
[WP] Every city has a ghost assigned to it. Tonight, ours resigns.

About 3,000 words. Close third person. Melancholy but hopeful.
```

Codex keeps your complete request intact, including later directions, and assesses the experience it promises before choosing a plot. One existing outline reader acts as a continuing promise keeper: it records its own understanding of your request before seeing an outline or editorial interpretation. The writer begins a brief, provisional outline with the distinctive pleasure, tone, scale, central relationship, and anticipated payoff, separating your explicit requirements from interpretations, then proposes concrete scenes that deliver them. Independent outline readings lead to discussion with the writer before drafting.

The keeper follows the story through production, asking whether the distinctive premise drives events, revelations change possibilities, and the ending delivers the promised experience. Separate cold readers read the complete draft, discuss their actual experience with the writer, and read the revision. Fresh final readers see the whole story without the earlier discussion. Material promise failures need changes to scenes or structure before polish; editorial preference or majority approval cannot override your explicit requirements. The outline remains provisional, and local repairs receive contextual checks rather than restarting every review stage. [The story workshop skill](.agents/skills/story-create/SKILL.md) explains the practice.

Separate character sheets, with one character per sheet, and references for the story's important locations normally come next, covering multiple distinct places when the story has them. After those references are finished and inspected, they guide the cover.

New stories start with a General audience target unless the prompt says otherwise. General limits content intensity, not ambition or scale; adventure, conflict, spectacle, and grandeur belong when the request calls for them. Familiar tropes can work through specific, satisfying results. The collection also watches for repeated defaults toward humble work, therapeutic conversations, or maintenance without forcing spectacle or novelty onto every story. Each finished story's `ratings.md` records its reviewed General, Teen, Mature, or Explicit classification and content notes under the [shared content boundaries](universe/style-guide.md#audience-and-content-boundaries).

The story's `notes.md` keeps concise editorial memory: the keeper's independent understanding, useful findings from outline, draft, and final readings, what readers experienced, what changed, whether it worked, and the reasons for resolving objections or preserving dissent. Git records substantial draft and revision rounds. There are no scores, file hashes, scripted approvals, or required number of rounds.

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
