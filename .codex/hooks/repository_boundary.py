"""Reject file-tool paths outside this worktree; shell writes use the sandbox."""

import json
import ntpath
import os
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
PATCH_PATH = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.*)$")


class BoundaryError(ValueError):
    pass


def inside(raw, base, root):
    """Resolve existing ancestors too, so symlinks and junctions cannot escape."""
    if not isinstance(raw, str) or not raw or any(c in raw for c in "\0\r\n"):
        raise BoundaryError("Missing or invalid file path.")
    path = Path(raw)
    if (path.anchor and not path.is_absolute()) or (
        os.name != "nt" and ntpath.splitdrive(raw)[0]
    ):
        raise BoundaryError(f"Ambiguous or foreign-platform path: {raw!r}.")
    resolved = (path if path.is_absolute() else base / path).resolve()
    if not resolved.is_relative_to(root):
        raise BoundaryError(f"Path is outside the active worktree: {raw!r}.")
    return resolved


def check(event, root=ROOT):
    if not isinstance(event, dict) or event.get("hook_event_name") != "PreToolUse":
        raise BoundaryError("Expected a PreToolUse hook event.")
    root = root.resolve()
    cwd = event.get("cwd")
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        raise BoundaryError("Hook cwd must be an absolute worktree path.")
    base = inside(cwd, root, root)
    name = event.get("tool_name")
    args = event.get("tool_input")
    if not isinstance(args, dict):
        raise BoundaryError("Expected structured tool input.")

    if name == "apply_patch":
        patch = args.get("command")
        if not isinstance(patch, str):
            raise BoundaryError("Expected the patch in tool_input.command.")
        lines = patch.strip().splitlines()
        if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
            raise BoundaryError("Unrecognized patch format; cannot check its paths.")
        paths = [match[1] for line in lines if (match := PATCH_PATH.fullmatch(line))]
        if not paths:
            raise BoundaryError("Patch contains no file paths to check.")
        for path in paths:
            inside(path, base, root)
    elif name in {"Write", "Edit", "MultiEdit"}:
        inside(args.get("file_path"), base, root)
    elif name == "Bash":
        # Arbitrary programs can construct paths at runtime. Do not pretend a
        # shell-command regex can replace the workspace-write OS sandbox.
        if event.get("permission_mode") == "bypassPermissions":
            raise BoundaryError("Shell execution requires the workspace-write sandbox.")
        if args.get("sandbox_permissions") == "require_escalated":
            raise BoundaryError("Unsandboxed shell execution is disabled for this worktree.")
        for field in ("workdir", "cwd"):
            if args.get(field) is not None:
                inside(args[field], base, root)
        if not isinstance(args.get("command"), str):
            raise BoundaryError("Expected the shell command in tool_input.command.")
    else:
        raise BoundaryError(f"Unsupported tool for the repository boundary: {name!r}.")


def main():
    try:
        check(json.load(sys.stdin))
    except (ValueError, OSError, RuntimeError) as error:
        reason = f"Repository write boundary: {error} Use {ROOT / 'tmp'} for temporary files."
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}))
        print(reason, file=sys.stderr)
        return 2
    # Abstain on allowed paths rather than overriding normal tool permissions.
    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
