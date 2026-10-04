# Repository write boundary

Put every task-created temporary file and directory under the active worktree's
`tmp/`. Only `tmp/.gitkeep` is tracked. Use an explicit `dir=` with Python's
temporary-file APIs, and set subprocess `TMPDIR`, `TMP`, and `TEMP` to the
absolute `<worktree>/tmp/` when a program chooses its own scratch directory.
Read-only access to external inputs is allowed.

The project configuration selects `workspace-write`, excludes the system `/tmp`
and inherited `TMPDIR` writable roots, and disables approval-based escalation.
The filesystem sandbox handles writes from shell commands, including scripts
whose destinations cannot be determined from the command text. Network access
remains enabled. Do not add external writable roots or launch with a sandbox
bypass. Git and agent applications still manage their own metadata outside the
worktree when their runtime requires it; task-created files belong here.

The `PreToolUse` hook checks every add, update, delete, and move destination in
`apply_patch`, plus `Write`, `Edit`, and `MultiEdit` file paths. It resolves paths
against the session directory and checks them against the worktree containing
the hook, resolving symlinks and Windows junctions as well. Malformed inputs and
paths outside that root are denied before the edit runs. For shell tools, it
also rejects an external working directory, bypass permission mode, and explicit
unsandboxed execution. It does not parse arbitrary shell programs.

## Activation

Python 3.9+ and Git must be on `PATH` (`python` on Windows, `python3` elsewhere).
Open a new Codex session in this trusted project after the configuration changes.
Use `/hooks` in the CLI to confirm that the repository write boundary is listed,
then review, trust, and enable it; Codex skips new or changed hook definitions
until they are trusted. If it is absent, resolve project hook discovery before
relying on the guard. The launcher finds the Git root so it
also works when the session starts in a repository subdirectory. Repository
configuration does not change the permissions of an already-running session;
command-line or desktop permission overrides can also supersede its defaults.
If the host cannot provision its filesystem sandbox, report that failure and
repair the host setup before running shell tasks; do not switch to full access
as a workaround.

Hooks are a guardrail, not a complete filesystem security boundary: some
specialized or hosted tools do not run local tool hooks, and this hook does not
cover every MCP tool. Keep the OS sandbox enabled for shell writes and follow
`AGENTS.md` for task files created by other tools. A Git commit hook cannot block
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
