"""Exercise the write guard using fixtures confined to repository tmp/."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import tomllib
except ImportError:
    tomllib = None


HOOK = Path(__file__).with_name("repository_boundary.py").resolve()
REPO = HOOK.parents[2]
spec = importlib.util.spec_from_file_location("repository_boundary", HOOK)
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)


class RepositoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="boundary-", dir=REPO / "tmp")
        self.fixture = Path(self.temp.name).resolve()
        self.root = self.fixture / "workspace"
        self.root.mkdir()
        self.subdir = self.root / "nested"
        self.subdir.mkdir()
        self.sibling = self.fixture / "workspace-other"
        self.sibling.mkdir()

    def tearDown(self):
        # Verify the cleanup target before recursive removal on Windows.
        self.assertTrue(self.fixture.is_relative_to((REPO / "tmp").resolve()))
        self.temp.cleanup()

    def event(self, name, args, cwd=None, **extra):
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": name,
            "tool_input": args,
            "cwd": str(cwd or self.root),
            "permission_mode": "default",
            **extra,
        }

    def patch(self, body, cwd=None):
        return self.event("apply_patch", {
            "command": "*** Begin Patch\n" + body + "\n*** End Patch\n",
        }, cwd)

    def allowed(self, event):
        boundary.check(event, self.root)

    def denied(self, event):
        with self.assertRaises(boundary.BoundaryError):
            boundary.check(event, self.root)

    def test_add_update_delete_and_move_inside(self):
        self.allowed(self.patch(
            "*** Add File: tmp/note.txt\n+hello\n"
            "*** Update File: story.md\n*** Move to: renamed.md\n@@\n-old\n+new\n"
            "*** Delete File: obsolete.txt"
        ))

    def test_absolute_path_inside(self):
        self.allowed(self.patch(f"*** Add File: {self.root / 'note.txt'}\n+ok"))

    def test_relative_path_uses_session_directory(self):
        self.allowed(self.patch("*** Add File: ../note.txt\n+ok", self.subdir))
        self.denied(self.patch("*** Add File: ../../note.txt\n+bad", self.subdir))

    def test_patch_content_is_not_a_file_header(self):
        self.allowed(self.patch(
            "*** Add File: note.txt\n+*** Add File: ../../outside.txt"
        ))

    def test_each_patch_operation_cannot_escape(self):
        for operation in ("Add File", "Update File", "Delete File"):
            with self.subTest(operation=operation):
                self.denied(self.patch(f"*** {operation}: ../outside.txt\n+bad"))

    def test_move_destination_cannot_escape(self):
        self.denied(self.patch(
            "*** Update File: inside.txt\n*** Move to: ../outside.txt\n@@\n-a\n+b"
        ))

    def test_move_source_cannot_escape(self):
        self.denied(self.patch(
            "*** Update File: ../outside.txt\n*** Move to: inside.txt\n@@\n-a\n+b"
        ))

    def test_absolute_sibling_is_not_inside_by_prefix(self):
        self.denied(self.patch(f"*** Add File: {self.sibling / 'note.txt'}\n+bad"))

    def test_one_external_file_denies_whole_patch(self):
        self.denied(self.patch(
            "*** Add File: inside.txt\n+ok\n*** Add File: ../outside.txt\n+bad"
        ))

    def test_structured_file_tools(self):
        for name in ("Write", "Edit", "MultiEdit"):
            with self.subTest(tool=name):
                self.allowed(self.event(name, {"file_path": "nested/note.txt"}))
                self.denied(self.event(name, {"file_path": "../outside.txt"}))
                self.denied(self.event(name, {}))

    def test_external_cwd_does_not_change_boundary(self):
        self.denied(self.patch("*** Add File: note.txt\n+bad", self.sibling))

    def test_missing_or_relative_cwd_denied(self):
        for cwd in (None, "nested", 42):
            with self.subTest(cwd=cwd):
                event = self.patch("*** Add File: note.txt\n+ok")
                event["cwd"] = cwd
                self.denied(event)

    def test_foreign_or_drive_relative_paths_denied(self):
        for path in ("C:note.txt", r"Z:\outside\note.txt", r"\\server\share\note.txt"):
            with self.subTest(path=path):
                self.denied(self.patch(f"*** Add File: {path}\n+bad"))

    def test_malformed_requests_denied(self):
        events = [None, [], {}, self.event("Unknown", {}),
                  self.event("apply_patch", "raw patch"),
                  self.event("apply_patch", {"command": None}),
                  self.event("apply_patch", {"command": "unrecognized"}),
                  self.patch(""), self.patch("*** Add File: "),
                  self.patch("*** Add File: bad\0path\n+bad")]
        for event in events:
            with self.subTest(event=event):
                self.denied(event)

    def test_shell_working_directory(self):
        self.allowed(self.event("Bash", {"command": "git status"}))
        self.allowed(self.event("Bash", {"command": "pwd", "workdir": "nested"}))
        for field in ("cwd", "workdir"):
            with self.subTest(field=field):
                self.denied(self.event("Bash", {"command": "pwd", field: "../"}))

    def test_shell_permissions_are_managed_by_codex(self):
        for mode in ("default", "bypassPermissions"):
            with self.subTest(mode=mode):
                self.allowed(self.event("Bash", {"command": "pwd"},
                                        permission_mode=mode))
                self.denied(self.event("Bash", {"command": "pwd", "workdir": "../"},
                                       permission_mode=mode))

    def test_shell_missing_command_denied(self):
        self.denied(self.event("Bash", {}))

    def test_shell_command_text_is_not_a_path_check(self):
        # A hook cannot prove arbitrary program writes safe by inspecting text.
        self.allowed(self.event("Bash", {"command": "python program.py"}))

    def test_external_symlink_parent_denied(self):
        link = self.root / "link"
        try:
            link.symlink_to(self.sibling, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Symlink creation is unavailable: {error}")
        try:
            self.denied(self.patch("*** Add File: link/new/note.txt\n+bad"))
            self.denied(self.event("Write", {"file_path": "link/note.txt"}))
        finally:
            link.unlink()

    def test_internal_symlink_allowed(self):
        link = self.root / "link"
        try:
            link.symlink_to(self.subdir, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"Symlink creation is unavailable: {error}")
        try:
            self.allowed(self.patch("*** Add File: link/note.txt\n+ok"))
        finally:
            link.unlink()

    @unittest.skipUnless(os.name == "nt", "Windows junction check")
    def test_external_junction_parent_denied(self):
        link = self.root / "junction"
        env = dict(os.environ, TMPDIR=str(REPO / "tmp"),
                   TMP=str(REPO / "tmp"), TEMP=str(REPO / "tmp"))
        # cmd's mklink is used only to create this explicitly scoped fixture.
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(self.sibling)],
                                capture_output=True, text=True, env=env, check=False)
        if result.returncode:
            self.skipTest(f"Junction creation is unavailable: {result.stderr}")
        try:
            self.denied(self.patch("*** Add File: junction/new/note.txt\n+bad"))
        finally:
            # Remove the link itself, never recurse into its target.
            link.rmdir()

    def test_cli_denial_protocol_without_external_writes(self):
        event = self.event("Write", {"file_path": str(REPO.parent / "never-written.txt")},
                           cwd=REPO)
        result = subprocess.run([sys.executable, "-B", str(HOOK)], input=json.dumps(event),
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("outside the active worktree", output["permissionDecisionReason"])

    def test_cli_success_abstains(self):
        result = subprocess.run([sys.executable, "-B", str(HOOK)],
                                input=json.dumps(self.event("Write", {"file_path": "tmp/check.txt"},
                                                            cwd=REPO)),
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {})

    def test_cli_invalid_json_denied(self):
        result = subprocess.run([sys.executable, "-B", str(HOOK)], input="not json",
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
                         "deny")

    @unittest.skipUnless(tomllib, "Configuration checks require Python 3.11+")
    def test_project_defers_permissions_to_codex(self):
        config = tomllib.loads((REPO / ".codex/config.toml").read_text(encoding="utf-8"))
        self.assertNotIn("sandbox_mode", config)
        self.assertNotIn("approval_policy", config)
        self.assertNotIn("sandbox_workspace_write", config)

    def test_configured_launcher_from_root_and_subdirectory(self):
        config = json.loads((REPO / ".codex/hooks.json").read_text(encoding="utf-8"))
        group = config["hooks"]["PreToolUse"][0]
        self.assertTrue(boundary.re.search(group["matcher"], "apply_patch"))
        hook = group["hooks"][0]
        command = hook["commandWindows"] if os.name == "nt" else hook["command"]
        shell = (["powershell", "-NoProfile", "-NonInteractive", "-Command"]
                 if os.name == "nt" else ["sh", "-c"])
        env = dict(os.environ, TMPDIR=str(REPO / "tmp"),
                   TMP=str(REPO / "tmp"), TEMP=str(REPO / "tmp"))
        for cwd in (REPO, REPO / ".codex/hooks"):
            for external in (False, True):
                with self.subTest(cwd=cwd, external=external):
                    path = (REPO.parent if external else REPO / "tmp") / "never-written.txt"
                    event = self.patch(f"*** Add File: {path}\n+test", cwd=cwd)
                    result = subprocess.run(shell + [command], cwd=cwd, env=env,
                                            input=json.dumps(event), capture_output=True,
                                            text=True, timeout=15, check=False)
                    self.assertEqual(result.returncode, 2 if external else 0, result.stderr)
                    output = json.loads(result.stdout)
                    if external:
                        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"],
                                         "deny")
                    else:
                        self.assertEqual(output, {})


if __name__ == "__main__":
    unittest.main()
