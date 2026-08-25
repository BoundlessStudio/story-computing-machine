import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("story_site", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = build
SPEC.loader.exec_module(build)

REPO = Path(__file__).resolve().parents[1]
STORY_VALIDATOR = REPO / ".agents/skills/story-room/scripts/Test-Stories.ps1"
NEW_STORY = REPO / ".agents/skills/story-room/scripts/new-story.ps1"
PREPARE_REWRITE = REPO / ".agents/skills/story-room/scripts/prepare-rewrite.ps1"
STORY_CREATE_SKILL = REPO / ".agents/skills/story-create/SKILL.md"
STORY_REWRITE_SKILL = REPO / ".agents/skills/story-rewrite/SKILL.md"


class StorySystemTests(unittest.TestCase):
    def write_title_image(self, story: Path, width: int = 864, height: int = 1536) -> None:
        # Minimal JPEG structure sufficient for the story validator's dimension check.
        story.joinpath("title-image.jpg").write_bytes(
            bytes.fromhex("ffd8ffc0001108")
            + height.to_bytes(2, "big")
            + width.to_bytes(2, "big")
            + bytes.fromhex("03011100021100031100ffd9")
        )

    def write_review(self, story: Path, passing: bool) -> None:
        if not passing:
            shutil.copy2(REPO / "stories/_template/review.md", story / "review.md")
            return

        (story / "review.md").write_text(
            "# Review\n\nVerdict: PASS\n\n"
            "## People\n\n| Noun | Status | Continuity note |\n"
            "| --- | --- | --- |\n| Mira | new | Unique in the checked baseline. |\n\n"
            "## Places\n\n| Noun | Status | Continuity note |\n"
            "| --- | --- | --- |\n| Alder Gate | new | Local to this story. |\n\n"
            "## Continuity\n\n- Prompt: PASS\n- Universe: PASS\n- Internal: PASS\n\n"
            "## Craft\n\n- Dialogue: PASS\n\n"
            "## Findings\n\n- Blocking: none\n- Notes: none\n",
            encoding="utf-8",
        )

    def make_current_story(self, root: Path, passing_review: bool = True) -> Path:
        stories = root / "stories"
        shutil.copytree(REPO / "stories/_template", stories / "_template")
        story = stories / "sample"
        story.mkdir()
        universe = root / "universe"
        universe.mkdir()
        (universe / "characters.md").write_text("# Characters\n", encoding="utf-8")
        (universe / "locations.md").write_text("# Locations\n", encoding="utf-8")
        (story / "prompt.md").write_text(
            "# Prompt\n\n## Prompt\n\n> [WP] A traveler returns through a gate.\n\n"
            "## Constraints\n\n- Craft profile: prospective-2026-08-18\n",
            encoding="utf-8",
        )
        (story / "outline.md").write_text(
            "# Outline\n\n"
            "## Story\n\n- Premise: Mira returns.\n- Ending: She chooses to stay.\n\n"
            "## Beats\n\n1. Mira crosses the gate.\n\n"
            "## People\n\n| Noun | Status | Role / recurrence note |\n"
            "| --- | --- | --- |\n| Mira | new | Returning traveler. |\n\n"
            "## Places\n\n| Noun | Status | Role / recurrence note |\n"
            "| --- | --- | --- |\n| Alder Gate | new | Local crossing. |\n\n"
            "## Continuity\n\n- Canon used: none.\n- Boundaries and unknowns: none.\n",
            encoding="utf-8",
        )
        (story / "story.md").write_text(
            "---\ntitle: Sample\nslug: sample\ncreated: 2026-08-06\ncanon: false\n---\n\n"
            "# Sample\n\nMira walked through Alder Gate and chose to stay.\n",
            encoding="utf-8",
        )
        self.write_review(story, passing_review)
        self.write_title_image(story)
        return story

    def use_create_dialogue_profile(self, story: Path) -> None:
        prompt_path = story / "prompt.md"
        prompt_path.write_text(
            prompt_path.read_text(encoding="utf-8").replace(
                "prospective-2026-08-18", "prospective-2026-08-23"
            ),
            encoding="utf-8",
        )
        (story / "outline.md").write_text(
            "# Outline\n\n"
            "## Story\n\n"
            "- Premise and central promise: Mira returns and must decide whether home can answer her.\n"
            "- Focal pressure or attachment: She wants recognition without admitting she needs it.\n"
            "- Counterforce or complication: The gate answers literally while its keeper answers indirectly.\n"
            "- POV, distance, and information limit: Close third with Mira; the keeper's motives remain inferred.\n"
            "- Governing movement and time shape: One crossing, one delayed recognition, one chosen return.\n"
            "- Speculative rule or ordinary-world constraint: Alder Gate records arrivals but cannot interpret them.\n"
            "- Dialogue promise: Estranged familiarity moves from guarded testing toward an imperfect welcome.\n"
            "- Dialogic medium: Sparse speech, gate signals, and pauses that each participant reads differently.\n"
            "- Dialogue engine: Mira needs directions but uses each question to test whether the keeper remembers her.\n\n"
            "## Voice\n\n"
            "- Narrative texture: Close observation tracks what Mira touches before what she admits.\n"
            "- Conversational texture: Practical questions carry old familiarity; answers arrive unevenly and sometimes late.\n"
            "- Rhetorical ownership: Mira owns dry deflection; the keeper owns literal care and hesitant humor.\n"
            "- Pressure behavior: Mira shortens requests while the keeper overexplains, then both leave one silence intact.\n"
            "- Relationship movement: Mira seeks recognition she cannot request; the keeper risks naming their shared past, restoring limited trust.\n"
            "- Anti-default: Do not turn reunion into two fluent experts solving the gate and returning to maintenance.\n\n"
            "## Beats\n\n"
            "1. Mira crosses the gate and tests the keeper's recognition.\n\n"
            "## People\n\n| Noun | Status | Role / recurrence note |\n"
            "| --- | --- | --- |\n| Mira | new | Returning traveler. |\n\n"
            "## Places\n\n| Noun | Status | Role / recurrence note |\n"
            "| --- | --- | --- |\n| Alder Gate | new | Local crossing. |\n\n"
            "## Continuity\n\n- Canon used: none.\n- Boundaries and unknowns: none.\n",
            encoding="utf-8",
        )

    def strip_create_dialogue_fields(self, story: Path) -> None:
        outline_path = story / "outline.md"
        create_only = (
            "- Dialogue promise:",
            "- Dialogic medium:",
            "- Dialogue engine:",
            "- Relationship movement:",
        )
        lines = outline_path.read_text(encoding="utf-8").splitlines()
        outline_path.write_text(
            "\n".join(line for line in lines if not line.startswith(create_only)) + "\n",
            encoding="utf-8",
        )

    def make_rewrite_worktree(self, temporary_root: Path) -> Path:
        source = temporary_root / "source"
        source.mkdir()
        story = self.make_current_story(source)
        self.use_create_dialogue_profile(story)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=source,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=source,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Story Tests",
                "-c",
                "user.email=story-tests@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
            cwd=source,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "branch", "codex/rewrite-sample"],
            cwd=source,
            text=True,
            capture_output=True,
            check=True,
        )
        worktree = temporary_root / "rewrite-worktree"
        subprocess.run(
            ["git", "worktree", "add", str(worktree), "codex/rewrite-sample"],
            cwd=source,
            text=True,
            capture_output=True,
            check=True,
        )
        return worktree

    def validate(self, root: Path, phase: str, story: str | None = None) -> subprocess.CompletedProcess:
        command = [
            "pwsh",
            "-NoProfile",
            "-File",
            str(STORY_VALIDATOR),
            "-ProjectRoot",
            str(root),
            "-Phase",
            phase,
        ]
        if story is not None:
            command.extend(("-Story", story))
        return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)

    def test_create_and_rewrite_have_distinct_entry_skills(self):
        create = STORY_CREATE_SKILL.read_text(encoding="utf-8")
        rewrite = STORY_REWRITE_SKILL.read_text(encoding="utf-8")

        self.assertIn("name: story-create", create)
        self.assertIn("Never\nuse this skill to reopen an existing story", create)
        self.assertIn("name: story-rewrite", rewrite)
        for scope in ("REBUILD", "RESHAPE", "SELECTIVE"):
            self.assertIn(f"`{scope}`", rewrite)
        for selection in (
            "Keep exact",
            "Keep in substance",
            "Change or replace",
            "Remove",
        ):
            self.assertIn(selection, rewrite)

    def test_scaffold_creates_exactly_four_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "stories").mkdir()
            shutil.copytree(REPO / "stories/_template", root / "stories/_template")
            completed = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(NEW_STORY),
                    "-ProjectRoot",
                    str(root),
                    "-Slug",
                    "sample",
                    "-Title",
                    "Sample",
                    "-Prompt",
                    "[WP] A small test.",
                    "-Date",
                    "2026-08-06",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertEqual(
                {"prompt.md", "outline.md", "story.md", "review.md"},
                {path.name for path in (root / "stories/sample").iterdir()},
            )
            self.assertRegex(
                (root / "stories/sample/story.md").read_text(encoding="utf-8"),
                r"(?m)^created-at: 2026-08-06T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$",
            )
            prompt = (root / "stories/sample/prompt.md").read_text(encoding="utf-8")
            outline = (root / "stories/sample/outline.md").read_text(encoding="utf-8")
            review = (root / "stories/sample/review.md").read_text(encoding="utf-8")
            self.assertIn(
                "Craft profile: prospective-2026-08-23",
                prompt,
            )
            self.assertIn("## Craft\n\n- Dialogue: PENDING", review)
            for field in (
                "Premise and central promise:",
                "Focal pressure or attachment:",
                "Counterforce or complication:",
                "POV, distance, and information limit:",
                "Governing movement and time shape:",
                "Speculative rule or ordinary-world constraint:",
                "Dialogue promise:",
                "Dialogic medium:",
                "Dialogue engine:",
                "Narrative texture:",
                "Conversational texture:",
                "Rhetorical ownership:",
                "Pressure behavior:",
                "Relationship movement:",
                "Anti-default:",
            ):
                self.assertIn(field, outline)

    def test_scaffold_defaults_to_invocation_git_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source_checkout = temporary_root / "source-checkout"
            target_worktree = temporary_root / "target-worktree"
            copied_script = source_checkout / ".agents/skills/story-room/scripts/new-story.ps1"
            copied_script.parent.mkdir(parents=True)
            shutil.copy2(NEW_STORY, copied_script)
            for checkout in (source_checkout, target_worktree):
                (checkout / "stories").mkdir(parents=True)
                shutil.copytree(REPO / "stories/_template", checkout / "stories/_template")
            subprocess.run(
                ["git", "init", "-b", "codex/test-worktree"],
                cwd=target_worktree,
                text=True,
                capture_output=True,
                check=True,
            )

            completed = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(copied_script),
                    "-Slug",
                    "worktree-sample",
                    "-Title",
                    "Worktree Sample",
                    "-Prompt",
                    "[WP] A portable scaffold test.",
                    "-Date",
                    "2026-08-06",
                ],
                cwd=target_worktree,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertTrue((target_worktree / "stories/worktree-sample/prompt.md").is_file())
            self.assertFalse((source_checkout / "stories/worktree-sample").exists())

    def test_pre_review_accepts_pending_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_current_story(root, passing_review=False)
            completed = self.validate(root, "PreReview", "sample")
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn("2 declared person/place nouns", completed.stdout)

    def test_pre_review_accepts_pending_title_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            (story / "title-image.jpg").unlink()
            completed = self.validate(root, "PreReview", "sample")
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_pre_review_accepts_create_dialogue_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)

            completed = self.validate(root, "PreReview", "sample")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_pre_review_rejects_incomplete_create_dialogue_fields(self):
        values = {
            "Dialogue promise": "Estranged familiarity moves from guarded testing toward an imperfect welcome.",
            "Dialogic medium": "Sparse speech, gate signals, and pauses that each participant reads differently.",
            "Dialogue engine": "Mira needs directions but uses each question to test whether the keeper remembers her.",
            "Relationship movement": "Mira seeks recognition she cannot request; the keeper risks naming their shared past, restoring limited trust.",
        }
        for field, value in values.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root, passing_review=False)
                self.use_create_dialogue_profile(story)
                outline_path = story / "outline.md"
                outline_path.write_text(
                    outline_path.read_text(encoding="utf-8").replace(
                        f"- {field}: {value}", f"- {field}:"
                    ),
                    encoding="utf-8",
                )

                completed = self.validate(root, "PreReview", "sample")

                self.assertNotEqual(0, completed.returncode)
                self.assertIn(field, completed.stdout + completed.stderr)
                self.assertIn("actionable", completed.stdout + completed.stderr)

    def test_pre_review_preserves_0821_five_field_voice_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8").replace(
                    "prospective-2026-08-23", "prospective-2026-08-21"
                ),
                encoding="utf-8",
            )
            self.strip_create_dialogue_fields(story)

            completed = self.validate(root, "PreReview", "sample")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_rewrite_constraints_override_base_create_profile_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            self.strip_create_dialogue_fields(story)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8")
                + "\n## Rewrite request\n\n> Retell the story through a colder lens.\n\n"
                "## Rewrite reference images\n\n- None supplied for this rewrite.\n\n"
                "## Rewrite constraints\n\n- Cover: AUTO\n"
                "- Craft profile: prospective-2026-08-21\n"
                "- Authority: the rewrite request controls where it conflicts with the original prompt; all unaffected original requirements remain binding.\n",
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_new_rewrite_profile_requires_selection_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8")
                + "\n## Rewrite request\n\n> Replace the ending.\n\n"
                "## Rewrite reference images\n\n- None supplied for this rewrite.\n\n"
                "## Rewrite constraints\n\n- Cover: AUTO\n"
                "- Craft profile: prospective-2026-08-23\n"
                "- Authority: the rewrite request and selections control where they conflict with the original prompt; outside named selections follows the recorded preservation policy.\n",
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("requires exactly one 'Rewrite selections'", completed.stdout + completed.stderr)

    def test_pre_review_accepts_selection_contract_rewrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8")
                + "\n## Rewrite request\n\n> Replace the ending while preserving the reunion.\n\n"
                "## Rewrite reference images\n\n- None supplied for this rewrite.\n\n"
                "## Rewrite selections\n\n- Scope: SELECTIVE\n"
                "- Outside named selections: KEEP EXACT\n"
                "- Keep exact: none specified\n"
                "- Keep in substance: the reunion\n"
                "- Change or replace: the ending\n"
                "- Remove: none specified\n\n"
                "## Rewrite constraints\n\n- Cover: AUTO\n"
                "- Craft profile: prospective-2026-08-23\n"
                "- Authority: the rewrite request and selections control where they conflict with the original prompt; outside named selections follows the recorded preservation policy.\n",
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_pre_review_rejects_scope_with_contradictory_outside_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8")
                + "\n## Rewrite request\n\n> Replace the ending.\n\n"
                "## Rewrite reference images\n\n- None supplied for this rewrite.\n\n"
                "## Rewrite selections\n\n- Scope: SELECTIVE\n"
                "- Outside named selections: FLEXIBLE\n"
                "- Keep exact: none specified\n"
                "- Keep in substance: none specified\n"
                "- Change or replace: the ending\n"
                "- Remove: none specified\n\n"
                "## Rewrite constraints\n\n- Cover: AUTO\n"
                "- Craft profile: prospective-2026-08-23\n"
                "- Authority: the rewrite request and selections control where they conflict with the original prompt; outside named selections follows the recorded preservation policy.\n",
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertNotEqual(0, completed.returncode)
            normalized_output = " ".join((completed.stdout + completed.stderr).split())
            self.assertIn(
                "Rewrite scope SELECTIVE requires Outside named selections: KEEP",
                normalized_output,
            )
            self.assertIn("EXACT.", normalized_output)

    def test_prepare_rewrite_rebuild_records_selection_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            worktree = self.make_rewrite_worktree(Path(temporary))

            completed = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(PREPARE_REWRITE),
                    "-ProjectRoot",
                    str(worktree),
                    "-Story",
                    "sample",
                    "-Title",
                    "Sample",
                    "-Request",
                    "Retell the story with a colder lens.",
                    "-Scope",
                    "Rebuild",
                    "-Keep",
                    "Mira's attachment to Alder Gate",
                    "-Change",
                    "the returning-traveler plot",
                    "-Remove",
                    "the decision to stay",
                    "-Cover",
                    "Keep",
                ],
                cwd=worktree,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            prompt = (worktree / "stories/sample/prompt.md").read_text(encoding="utf-8")
            outline = (worktree / "stories/sample/outline.md").read_text(encoding="utf-8")
            story = (worktree / "stories/sample/story.md").read_text(encoding="utf-8")
            self.assertIn("Craft profile: prospective-2026-08-23", prompt)
            self.assertIn("## Rewrite selections", prompt)
            self.assertIn("- Scope: REBUILD", prompt)
            self.assertIn("- Outside named selections: FLEXIBLE", prompt)
            self.assertIn("- Keep in substance: Mira's attachment to Alder Gate", prompt)
            self.assertIn("- Change or replace: the returning-traveler plot", prompt)
            self.assertIn("- Remove: the decision to stay", prompt)
            self.assertIn("## Rewrite constraints", prompt)
            for field in (
                "Dialogue promise",
                "Dialogic medium",
                "Dialogue engine",
                "Relationship movement",
            ):
                self.assertIn(f"- {field}:", outline)
            self.assertIn("Complete reader-facing prose goes here", story)
            self.assertNotIn("Mira walked through Alder Gate", story)

    def test_prepare_rewrite_selective_preserves_existing_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            worktree = self.make_rewrite_worktree(Path(temporary))

            completed = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(PREPARE_REWRITE),
                    "-ProjectRoot",
                    str(worktree),
                    "-Story",
                    "sample",
                    "-Title",
                    "Sample",
                    "-Request",
                    "Replace the ending but preserve the opening prose.",
                    "-Scope",
                    "Selective",
                    "-KeepExact",
                    "the opening sentence",
                    "-Change",
                    "the final decision",
                    "-Cover",
                    "Keep",
                ],
                cwd=worktree,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            prompt = (worktree / "stories/sample/prompt.md").read_text(encoding="utf-8")
            story = (worktree / "stories/sample/story.md").read_text(encoding="utf-8")
            self.assertIn("- Scope: SELECTIVE", prompt)
            self.assertIn("- Outside named selections: KEEP EXACT", prompt)
            self.assertIn("- Keep exact: the opening sentence", prompt)
            self.assertIn("- Change or replace: the final decision", prompt)
            self.assertIn("Mira walked through Alder Gate and chose to stay.", story)
            self.assertNotIn("Complete reader-facing prose goes here", story)

    def test_prepare_rewrite_reshape_uses_substantive_preservation_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            worktree = self.make_rewrite_worktree(Path(temporary))

            completed = subprocess.run(
                [
                    "pwsh",
                    "-NoProfile",
                    "-File",
                    str(PREPARE_REWRITE),
                    "-ProjectRoot",
                    str(worktree),
                    "-Story",
                    "sample",
                    "-Title",
                    "Sample",
                    "-Request",
                    "Keep the emotional throughline but reshape the plot.",
                    "-Scope",
                    "Reshape",
                    "-Keep",
                    "Mira's attachment to Alder Gate",
                    "-Change",
                    "the sequence of events",
                    "-Cover",
                    "Keep",
                ],
                cwd=worktree,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            prompt = (worktree / "stories/sample/prompt.md").read_text(encoding="utf-8")
            story = (worktree / "stories/sample/story.md").read_text(encoding="utf-8")
            self.assertIn("- Scope: RESHAPE", prompt)
            self.assertIn("- Outside named selections: KEEP", prompt)
            self.assertIn("Complete reader-facing prose goes here", story)
            self.assertNotIn("Mira walked through Alder Gate", story)

    def test_pre_review_rejects_0823_voice_over_220_words(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            outline_path = story / "outline.md"
            outline_path.write_text(
                outline_path.read_text(encoding="utf-8").replace(
                    "- Relationship movement:",
                    "- Relationship movement: " + ("overflow " * 221),
                ),
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("220-word limit", completed.stdout + completed.stderr)

    def test_pre_review_rejects_new_profile_outline_over_1200_words(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            outline_path = story / "outline.md"
            outline_path.write_text(
                outline_path.read_text(encoding="utf-8") + "\n\n" + ("excess " * 1201),
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertNotEqual(0, completed.returncode)
            self.assertIn("outline.md exceeds the 1200-word limit", completed.stdout + completed.stderr)

    def test_pre_review_does_not_apply_new_outline_limit_retroactively(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8").replace(
                    "prospective-2026-08-18", "prospective-2026-08-08"
                ),
                encoding="utf-8",
            )
            outline_path = story / "outline.md"
            outline_path.write_text(
                outline_path.read_text(encoding="utf-8") + "\n\n" + ("legacy " * 1201),
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_pre_review_allows_advisory_outline_deviation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            story_path = story / "story.md"
            content = story_path.read_text(encoding="utf-8")
            story_path.write_text(
                content.replace("Mira walked through Alder Gate", "Nessa walked through Willow Door"),
                encoding="utf-8",
            )
            completed = self.validate(root, "PreReview", "sample")
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn("Advisory outline noun", completed.stdout)

    def test_pre_review_rejects_exact_collisions_and_unknown_recurrence(self):
        cases = ("legacy person", "current person", "universe place", "unknown recurrence")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root, passing_review=False)
                if case == "legacy person":
                    (root / "stories/NAMES.md").write_text(
                        "| Identity | Reserved forms | Story |\n"
                        "| --- | --- | --- |\n| Earlier Mira | `Mira` | locked-story |\n",
                        encoding="utf-8",
                    )
                elif case == "current person":
                    prior = root / "stories/prior"
                    prior.mkdir()
                    self.write_review(prior, passing=True)
                elif case == "universe place":
                    (root / "universe/locations.md").write_text(
                        "# Locations\n\n## Alder Gate\n\n- Aliases: None\n",
                        encoding="utf-8",
                    )
                else:
                    outline_path = story / "outline.md"
                    outline_path.write_text(
                        outline_path.read_text(encoding="utf-8").replace(
                            "| Mira | new |", "| Mira | recurring |"
                        ),
                        encoding="utf-8",
                    )
                completed = self.validate(root, "PreReview", "sample")
                self.assertNotEqual(0, completed.returncode)
                self.assertIn("Pre-review validation failed", completed.stdout + completed.stderr)

    def test_pre_review_accepts_known_recurrence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            (root / "stories/NAMES.md").write_text(
                "| Identity | Reserved forms | Story |\n"
                "| --- | --- | --- |\n| Earlier Mira | `Mira` | locked-story |\n",
                encoding="utf-8",
            )
            outline_path = story / "outline.md"
            outline_path.write_text(
                outline_path.read_text(encoding="utf-8").replace(
                    "| Mira | new |", "| Mira | recurring |"
                ),
                encoding="utf-8",
            )
            completed = self.validate(root, "PreReview", "sample")
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_pre_review_rejects_bad_metadata_and_missing_prose(self):
        cases = ("bad metadata", "missing prose")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root, passing_review=False)
                story_path = story / "story.md"
                content = story_path.read_text(encoding="utf-8")
                if case == "bad metadata":
                    content = content.replace("created: 2026-08-06", "created: someday")
                else:
                    content = content[: content.index("# Sample")] + "# Sample\n\n<!-- No prose. -->\n"
                story_path.write_text(content, encoding="utf-8")
                completed = self.validate(root, "PreReview", "sample")
                self.assertNotEqual(0, completed.returncode)
                self.assertIn("Pre-review validation failed", completed.stdout + completed.stderr)

    def test_final_validation_accepts_passing_story(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_current_story(root)
            completed = self.validate(root, "Final")
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn("1 current stories", completed.stdout)

    def test_final_validation_accepts_create_dialogue_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            self.use_create_dialogue_profile(story)

            completed = self.validate(root, "Final")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_final_validation_accepts_dialogue_na_for_story_without_dialogue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            review_path = story / "review.md"
            review_path.write_text(
                review_path.read_text(encoding="utf-8").replace(
                    "- Dialogue: PASS", "- Dialogue: N/A"
                ),
                encoding="utf-8",
            )

            completed = self.validate(root, "Final")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_final_validation_rejects_bad_new_profile_dialogue_verdict(self):
        cases = ("missing", "invalid", "duplicate", "revise")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root)
                review_path = story / "review.md"
                review = review_path.read_text(encoding="utf-8")
                if case == "missing":
                    review = review.replace("## Craft\n\n- Dialogue: PASS\n\n", "")
                elif case == "invalid":
                    review = review.replace("- Dialogue: PASS", "- Dialogue: MAYBE")
                elif case == "duplicate":
                    review = review.replace(
                        "- Dialogue: PASS", "- Dialogue: PASS\n- Dialogue: N/A"
                    )
                else:
                    review = review.replace("- Dialogue: PASS", "- Dialogue: REVISE")
                review_path.write_text(review, encoding="utf-8")

                completed = self.validate(root, "Final")

                self.assertNotEqual(0, completed.returncode)
                self.assertIn("Final story validation failed", completed.stdout + completed.stderr)
                self.assertIn("Dialogue", completed.stdout + completed.stderr)

    def test_final_validation_does_not_require_dialogue_verdict_retroactively(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8").replace(
                    "prospective-2026-08-18", "prospective-2026-08-08"
                ),
                encoding="utf-8",
            )
            review_path = story / "review.md"
            review_path.write_text(
                review_path.read_text(encoding="utf-8").replace(
                    "## Craft\n\n- Dialogue: PASS\n\n", ""
                ),
                encoding="utf-8",
            )

            completed = self.validate(root, "Final")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_final_validation_rejects_inventory_continuity_and_blockers(self):
        cases = (
            "missing inventory",
            "failed continuity",
            "blocking finding",
            "missing title image",
            "wrong title image size",
        )
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root)
                review_path = story / "review.md"
                review = review_path.read_text(encoding="utf-8")
                if case == "missing inventory":
                    start = review.index("## Places")
                    end = review.index("## Continuity")
                    review = review[:start] + review[end:]
                elif case == "failed continuity":
                    review = review.replace("- Universe: PASS", "- Universe: PENDING")
                elif case == "blocking finding":
                    review = review.replace("- Blocking: none", "- Blocking: repair the ending")
                elif case == "missing title image":
                    (story / "title-image.jpg").unlink()
                else:
                    self.write_title_image(story, 1024, 768)
                review_path.write_text(review, encoding="utf-8")
                completed = self.validate(root, "Final")
                self.assertNotEqual(0, completed.returncode)
                self.assertIn("Final story validation failed", completed.stdout + completed.stderr)

    def test_capture_requires_pass_but_does_not_repeat_full_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            snapshot = root / "catalog.json"
            with self.assertRaisesRegex(ValueError, "not a passing review"):
                build.capture_story("sample", root, snapshot)

            self.write_review(story, passing=True)
            self.assertFalse(hasattr(build, "validate_current_stories"))
            catalog = build.capture_story("sample", root, snapshot)
            self.assertEqual(("sample",), tuple(item.slug for item in catalog.stories))
            self.assertEqual(catalog, build.load_catalog(snapshot))
            self.assertEqual("covers/sample.jpg", catalog.stories[0].cover)
            self.assertRegex(catalog.stories[0].edited, r"^\d{4}-\d{2}-\d{2}$")
            self.assertEqual("PG", catalog.stories[0].rating)
            self.assertTrue((root / "covers/sample.jpg").is_file())

    def test_content_rating_maps_to_supported_card_symbols(self):
        cases = {
            "- Tone and audience: broadly accessible unless specified": "PG",
            "- Audience/content rating: Teen / PG-13; non-graphic peril.": "YA",
            "- Audience/content rating: Adult characters; suggestive but non-explicit.": "YA",
            "- Tone and audience: adult, hard-R crime noir.": "R+",
            "- Explicit user ruling: explicit consensual sexual content may remain on the page.": "R+",
            "# Prompt\n\n## Prompt\n\n> A quiet walk.": "PG",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(expected, build._content_rating(source))

    def test_prompt_parser_strips_wp_marker_with_optional_markdown_heading(self):
        cases = (
            "> [WP] A traveler returns through a gate.",
            "> # [WP] A traveler returns through a gate.",
            "> # **[WP] A traveler returns through a gate.**",
            "> # WP] A traveler returns through a gate.",
        )
        for source in cases:
            with self.subTest(source=source):
                prompt = f"# Prompt\n\n## Prompt\n\n{source}\n\n## Constraints\n\n- None\n"
                self.assertEqual(
                    "A traveler returns through a gate.",
                    build.parse_writing_prompt(prompt, Path("prompt.md")),
                )

    def test_same_day_catalog_order_uses_source_file_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            later = self.make_current_story(root)
            snapshot = root / "catalog.json"
            later_story_path = later / "story.md"
            os.utime(later_story_path, (1_800_000_000, 1_800_000_000))
            build.capture_story("sample", root, snapshot)

            earlier = root / "stories" / "earlier"
            shutil.copytree(later, earlier)
            earlier_story_path = earlier / "story.md"
            earlier_story_path.write_text(
                earlier_story_path.read_text(encoding="utf-8")
                .replace("title: Sample", "title: Earlier")
                .replace("slug: sample", "slug: earlier")
                .replace("# Sample", "# Earlier"),
                encoding="utf-8",
            )
            os.utime(earlier_story_path, (1_799_996_400, 1_799_996_400))

            catalog = build.capture_story("earlier", root, snapshot)

            self.assertEqual(("sample", "earlier"), tuple(item.slug for item in catalog.stories))
            self.assertGreater(catalog.stories[0].created_at, catalog.stories[1].created_at)
            self.assertEqual(catalog, build.load_catalog(snapshot))

    def test_source_created_at_overrides_filesystem_time(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            story_path = story / "story.md"
            story_path.write_text(
                story_path.read_text(encoding="utf-8").replace(
                    "created: 2026-08-06",
                    "created: 2026-08-06\ncreated-at: 2026-08-06T21:43:12-04:00",
                ),
                encoding="utf-8",
            )

            loaded = build.load_story_source("sample", root)

            self.assertEqual("2026-08-06T21:43:12-04:00", loaded.created_at)

    def test_stored_catalog_is_valid_and_newest_first(self):
        catalog = build.load_catalog()
        self.assertGreater(len(catalog.stories), 0)
        dates = [story.created for story in catalog.stories]
        self.assertEqual(sorted(dates, reverse=True), dates)
        timestamps = [build._parse_created_at(story.created_at, story.slug) for story in catalog.stories]
        self.assertEqual(sorted(timestamps, reverse=True), timestamps)
        self.assertEqual(len({story.slug for story in catalog.stories}), len(catalog.stories))
        self.assertTrue(all(story.cover == f"covers/{story.slug}.jpg" for story in catalog.stories))
        self.assertTrue(all(build.DATE.fullmatch(story.edited) for story in catalog.stories))
        self.assertTrue(all(story.rating in build.RATINGS for story in catalog.stories))
        self.assertFalse(
            any(re.match(r"^(?:#{1,6}\s*)?\[?WP\]", story.prompt) for story in catalog.stories)
        )

    def test_stored_timeline_places_every_story_once(self):
        catalog = build.load_catalog()
        timeline = build.load_timeline(catalog)
        placements = [
            slug
            for chapter in timeline.chapters
            for slug in (
                *chapter.stories,
                *(slug for group in chapter.constellations for slug in group.stories),
            )
        ]

        self.assertEqual(len(catalog.stories), len(placements))
        self.assertEqual({story.slug for story in catalog.stories}, set(placements))
        self.assertTrue(all(count == 1 for count in Counter(placements).values()))
        self.assertEqual(set(placements), set(timeline.story_confidence))
        self.assertEqual(
            {"the-first-wound", "the-first-kingdom-was-late-on-taxes"},
            set(timeline.story_spans),
        )

        chapter_ids = [chapter.id for chapter in timeline.chapters]
        self.assertEqual("first-wonders", chapter_ids[0])
        self.assertEqual("joined-sky", chapter_ids[-1])
        self.assertLess(chapter_ids.index("modern-like-trough"), chapter_ids.index("glass-sea"))
        self.assertLess(chapter_ids.index("terminal-convergence"), chapter_ids.index("long-zero"))
        self.assertLess(chapter_ids.index("long-zero"), chapter_ids.index("joined-sky"))

        placements_by_chapter = {
            chapter.id: [
                *chapter.stories,
                *(slug for group in chapter.constellations for slug in group.stories),
            ]
            for chapter in timeline.chapters
        }
        self.assertLess(
            placements_by_chapter["arcane-industry"].index("voice-of-silence"),
            placements_by_chapter["arcane-industry"].index("a-lock-on-the-inside"),
        )
        self.assertIn(
            "solstice-evening-bell",
            placements_by_chapter["modern-like-trough"],
        )
        self.assertEqual(
            ["the-count-was-131072"],
            placements_by_chapter["bay-museum-age"],
        )

    def test_timeline_rejects_duplicate_story_placement(self):
        catalog = build.load_catalog()
        value = json.loads(build.TIMELINE_PATH.read_text(encoding="utf-8"))
        duplicated_slug = value["chapters"][0]["stories"][0]
        value["chapters"][1]["stories"].append(duplicated_slug)

        with tempfile.TemporaryDirectory() as temporary:
            timeline_path = Path(temporary) / "timeline.json"
            timeline_path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "repeats already placed stories"):
                build.load_timeline(catalog, timeline_path)

    def test_timeline_render_is_cover_led_universal_chronology(self):
        catalog = build.load_catalog()
        timeline = build.load_timeline(catalog)
        rendered = build.render_timeline(catalog, timeline)

        story_links = re.findall(r'href="stories/([^"/]+)\.html"', rendered)
        self.assertEqual(len(catalog.stories), len(story_links))
        self.assertEqual({story.slug for story in catalog.stories}, set(story_links))
        self.assertTrue(all(count == 1 for count in Counter(story_links).values()))
        self.assertGreaterEqual(
            rendered.count('<img src="timeline-covers/'),
            len(catalog.stories),
        )
        self.assertIn("A chronology of the shared universe", rendered)
        self.assertIn("The Modern-like Low-Magic Trough", rendered)
        self.assertIn("Off-Axis Realms", rendered)
        self.assertIn("The Long Zero", rendered)
        self.assertIn('class="timeline-chapter chapter-interval" id="long-zero"', rendered)
        self.assertIn("≈01", rendered)
        self.assertIn("Era fixed", rendered)
        self.assertIn("era membership is established", rendered)
        self.assertIn('class="timeline-span"', rendered)
        self.assertIn('data-story-state="candidate"', rendered)
        self.assertIn('<span class="timeline-story-state">Candidate</span>', rendered)
        self.assertIn('aria-label="Approximate position 1 in this era band"', rendered)
        self.assertIn('aria-label="Position unresolved within this era band"', rendered)
        self.assertNotIn('aria-label="Read ', rendered)
        self.assertIn('data-placement-confidence="fixed"', rendered)
        self.assertIn('data-placement-confidence="inferred"', rendered)
        self.assertIn('data-placement-confidence="speculative"', rendered)
        self.assertIn('data-placement-confidence="unresolved"', rendered)
        self.assertIn("not a publication or reading sequence", rendered.casefold())
        self.assertIn('<script src="timeline.js" defer></script>', rendered)
        self.assertIn('<a href="timeline.html" aria-current="page">Chronology</a>', rendered)

    def test_build_uses_stored_catalog(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            original_loader = build.load_story_source
            build.load_story_source = lambda *_args, **_kwargs: self.fail(
                "Pages build reopened a production story"
            )
            try:
                catalog = build.build(output)
            finally:
                build.load_story_source = original_loader
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "timeline.html").is_file())
            self.assertTrue((output / "timeline.js").is_file())
            self.assertTrue((output / "styles.css").is_file())
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "stories").glob("*.html"))),
            )
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "covers").glob("*.jpg"))),
            )
            timeline_covers = list((output / "timeline-covers").glob("*.jpg"))
            self.assertEqual(len(catalog.stories), len(timeline_covers))
            with build.Image.open(timeline_covers[0]) as timeline_cover:
                self.assertEqual(
                    (build.TIMELINE_COVER_WIDTH, build.TIMELINE_COVER_HEIGHT),
                    timeline_cover.size,
                )
            self.assertIn(
                f"{len(catalog.stories)} stored publications",
                (output / "index.html").read_text(encoding="utf-8"),
            )
            self.assertIn('class="story-grid"', (output / "index.html").read_text(encoding="utf-8"))
            self.assertIn(
                f"All {len(catalog.stories)} published stories are accounted for below",
                (output / "timeline.html").read_text(encoding="utf-8"),
            )

    def test_rendering_places_cover_below_title_and_prompt(self):
        story = build.load_catalog().stories[0]
        rendered = build.render_story(story)
        self.assertEqual(1, rendered.count("<h1>"))
        self.assertIn('<span class="prompt-label">Prompt</span>', rendered)
        self.assertIn(f'src="../{story.cover}"', rendered)
        self.assertLess(rendered.index("<h1>"), rendered.index('class="prompt"'))
        self.assertLess(rendered.index('class="prompt"'), rendered.index('class="story-cover"'))
        self.assertIn('<a href="../timeline.html">Chronology</a>', rendered)

    def test_index_cards_include_prompt_and_requested_metadata(self):
        story = build.load_catalog().stories[0]
        rendered = build.render_index(build.Catalog((story,)))
        self.assertEqual(1, rendered.count("<h1>"))
        self.assertIn("<title>Shared-Universe Fiction</title>", rendered)
        self.assertIn("<h1>Shared-Universe Fiction</h1>", rendered)
        self.assertNotIn('<p class="eyebrow">', rendered)
        self.assertNotIn("<h1>Stories</h1>", rendered)
        self.assertIn('class="story-card"', rendered)
        self.assertIn(f'src="{story.cover}"', rendered)
        self.assertIn(f'alt="Cover art for {build.html.escape(story.title)}"', rendered)
        self.assertIn(f'<h2 class="story-title">{build.html.escape(story.title)}</h2>', rendered)
        self.assertIn('<span class="card-prompt"><span class="prompt-label">Prompt</span>', rendered)
        self.assertIn(build.html.escape(story.prompt), rendered)
        self.assertIn("<dt>Date created</dt>", rendered)
        self.assertIn(f'datetime="{story.created}"', rendered)
        self.assertIn("<dt>Date edited</dt>", rendered)
        self.assertIn(f'datetime="{story.edited}"', rendered)
        self.assertIn("<dt>State</dt>", rendered)
        self.assertNotIn("Status / tag", rendered)
        self.assertIn(build._story_label(story), rendered)
        self.assertIn("<dt>Word count</dt>", rendered)
        self.assertIn(f'<span class="word-count">{story.word_count:,}</span>', rendered)
        self.assertIn("<dt>Rating</dt>", rendered)
        self.assertIn(f'>{story.rating}</span>', rendered)

    def test_output_cannot_replace_repository_root(self):
        with self.assertRaises(ValueError):
            build.prepare_output(REPO)


if __name__ == "__main__":
    unittest.main()
