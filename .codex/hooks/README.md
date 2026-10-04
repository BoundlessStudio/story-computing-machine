# Repository write boundary

Put every task-created temporary file and directory under the active worktree's
`tmp/`. Only `tmp/.gitkeep` is tracked. Use an explicit `dir=` with Python's
temporary-file APIs, and set subprocess `TMPDIR`, `TMP`, and `TEMP` to the
absolute `<worktree>/tmp/` when a program chooses its own scratch directory.
Read-only access to external inputs is allowed.

Use Codex's built-in worktree workflow and the worktree attached to the current
chat. Codex manages session permissions; the repository does not require a
particular sandbox profile, another checkout, or an update from `main` before
production. Git and agent applications still manage their own metadata outside
the worktree when their runtime requires it; task-created files belong here.

The `PreToolUse` hook checks every add, update, delete, and move destination in
`apply_patch`, plus `Write`, `Edit`, and `MultiEdit` file paths. It resolves paths
against the session directory and checks them against the worktree containing
the hook, resolving symlinks and Windows junctions as well. Malformed inputs and
paths outside that root are denied before the edit runs. For shell tools, it
rejects an external working directory and malformed input, while leaving
permission decisions to Codex. It does not parse arbitrary shell programs.

## Activation

Python 3.9+ and Git must be on `PATH` (`python` on Windows, `python3` elsewhere).
Use `/hooks` in the CLI to confirm that the repository write boundary is listed,
then review, trust, and enable it; Codex skips new or changed hook definitions
until they are trusted. If it is absent, resolve project hook discovery before
relying on the guard. The launcher finds the Git root so it also works when the
session starts in a repository subdirectory or a Codex-managed worktree.

Hooks are a guardrail, not a complete filesystem security boundary: some
specialized or hosted tools do not run local tool hooks, and this hook does not
cover every MCP tool. Follow `AGENTS.md` for task files created through shell or
other tools, using the permissions configured in Codex. A Git commit hook cannot block
filesystem writes that happen before a commit.

See the official [Codex hook protocol](https://developers.openai.com/codex/hooks/)
and [sandbox configuration](https://developers.openai.com/codex/config-reference/).

## Checks

From the worktree root, run:

```text
python -B -m unittest discover -s .codex/hooks -p "test_*.py"
codex doctor --summary
```

The tests create all fixtures under this worktree's `tmp/`. They check traversal,
absolute and sibling paths, move destinations, links, malformed requests, shell
working directories, and the hook's denial protocol without writing outside the
repository.
