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
from dataclasses import replace
from pathlib import Path

from PIL import Image

# Support both unittest discovery and direct module loading of the Pages script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

SPEC = importlib.util.spec_from_file_location("story_site", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = build
SPEC.loader.exec_module(build)

REPO = Path(__file__).resolve().parents[1]
STORY_VALIDATOR = REPO / ".agents/skills/story-room/scripts/Test-Stories.ps1"
NEW_STORY = REPO / ".agents/skills/story-room/scripts/new-story.ps1"
STORY_CREATE_SKILL = REPO / ".agents/skills/story-create/SKILL.md"
FRIENDS_NAME_EXCEPTION_HEADING = (
    "## 2026-09-03 — Friends of the Night name-conflict exception"
)
FRIENDS_NAME_EXCEPTION_ROWS = (
    ("friends-of-the-night", "People", "Crooktail", "universe/characters.md#Crooktail"),
    ("friends-of-the-night", "People", "Denek", "universe/characters.md#Denek"),
    ("friends-of-the-night", "People", "Drost", "universe/characters.md#Marshal Drost"),
    ("friends-of-the-night", "People", "Tavik", "universe/characters.md#Tavik"),
    ("friends-of-the-night", "People", "Torma", "universe/characters.md#Torma"),
    ("friends-of-the-night", "Places", "Shalegate", "universe/locations.md#Shalegate"),
)


class StorySystemTests(unittest.TestCase):
    def write_title_image(self, story: Path, width: int = 864, height: int = 1536) -> None:
        Image.new("RGB", (width, height), (40, 60, 90)).save(
            story / "title-image.jpg", format="JPEG"
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

    def validate(
        self, root: Path, phase: str, story: str | None = None,
        *, validator: Path = STORY_VALIDATOR,
    ) -> subprocess.CompletedProcess:
        command = [
            "pwsh",
            "-NoProfile",
            "-File",
            str(validator),
            "-ProjectRoot",
            str(root),
            "-Phase",
            phase,
        ]
        if story is not None:
            command.extend(("-Story", story))
        return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)

    def validate_with_decoder(self, root: Path, decoder_source: str) -> subprocess.CompletedProcess:
        """Exercise the native decoder protocol without changing checkout files."""
        validator = root / STORY_VALIDATOR.relative_to(REPO)
        validator.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STORY_VALIDATOR, validator)
        helper = root / "pages/image_validation.py"
        helper.parent.mkdir(exist_ok=True)
        helper.write_text(decoder_source, encoding="utf-8")
        return self.validate(root, "Final", validator=validator)

    def make_friends_name_fixture(
        self, root: Path, slug: str = "friends-of-the-night"
    ) -> Path:
        """Synthetic prose and inventories; never open the real story package."""
        original = self.make_current_story(root)
        story = original.rename(root / "stories" / slug)
        for path in story.glob("*.md"):
            content = path.read_text(encoding="utf-8")
            content = content.replace("slug: sample", f"slug: {slug}")
            content = content.replace("canon: false", "canon: true")
            content = content.replace("Mira", "Crooktail").replace("Alder Gate", "Shalegate")
            if path.name in ("outline.md", "review.md"):
                additional_people = "".join(
                    f"| {name} | new | Synthetic person for the collision test. |\n"
                    for name in ("Denek", "Drost", "Tavik", "Torma")
                )
                content = content.replace("\n## Places", additional_people + "\n## Places")
            elif path.name == "story.md":
                content = content.replace(
                    "Crooktail walked", "Crooktail, Denek, Drost, Tavik, and Torma walked"
                )
            path.write_text(content, encoding="utf-8")
        (root / "universe/characters.md").write_text(
            "# Characters\n\n"
            + "".join(
                f"## {name}\n\n- Aliases: None\n\n"
                for name in ("Crooktail", "Denek", "Tavik", "Torma")
            )
            + "## Marshal Drost\n\n- Aliases: Drost\n",
            encoding="utf-8",
        )
        (root / "universe/locations.md").write_text(
            "# Locations\n\n## Shalegate\n\n- Aliases: None\n", encoding="utf-8"
        )
        return story

    def write_friends_name_exception(
        self, root: Path, rows: tuple = FRIENDS_NAME_EXCEPTION_ROWS
    ) -> None:
        (root / "universe/retcons.md").write_text(
            "# Retcons\n\n"
            + FRIENDS_NAME_EXCEPTION_HEADING
            + "\n\n| Story | Kind | Noun | Conflicting source |\n"
            + "| --- | --- | --- | --- |\n"
            + "".join("| " + " | ".join(row) + " |\n" for row in rows),
            encoding="utf-8",
        )

    def test_story_create_documents_remove_then_create_replacement(self):
        create = " ".join(STORY_CREATE_SKILL.read_text(encoding="utf-8").split())

        self.assertIn("name: story-create", create)
        self.assertIn("remove only the explicitly named source package", create)
        self.assertIn("user-authored prompt or request block", create)
        self.assertIn("reference-image", create)
        self.assertIn("display name", create)
        self.assertIn("Discard only machine-owned", create)
        self.assertNotIn("story-rewrite", create)

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

    def test_last_recorded_craft_profile_is_active(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root, passing_review=False)
            self.use_create_dialogue_profile(story)
            self.strip_create_dialogue_fields(story)
            prompt_path = story / "prompt.md"
            prompt_path.write_text(
                prompt_path.read_text(encoding="utf-8")
                + "\n## Historical production context\n\n"
                "- Craft profile: prospective-2026-08-21\n",
                encoding="utf-8",
            )

            completed = self.validate(root, "PreReview", "sample")

            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

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
                outline_path.read_text(encoding="utf-8") + "\n\n" + ("earlier " * 1201),
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
        cases = ("bundle person", "current person", "universe place", "unknown recurrence")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root, passing_review=False)
                if case == "bundle person":
                    (root / "stories/NAMES.md").write_text(
                        "| Identity | Reserved forms | Story |\n"
                        "| --- | --- | --- |\n| Earlier Mira | `Mira` | locked-story |\n",
                        encoding="utf-8",
                    )
                elif case == "current person":
                    prior = root / "stories/prior"
                    prior.mkdir()
                    shutil.copy2(story / "prompt.md", prior / "prompt.md")
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

    def test_friends_name_exception_accepts_only_the_six_approved_source_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_friends_name_fixture(root)
            self.write_friends_name_exception(root)
            for phase in ("PreReview", "Final"):
                with self.subTest(phase=phase):
                    completed = self.validate(
                        root, phase, story.name if phase == "PreReview" else None
                    )
                    self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_friends_name_exception_requires_an_explicit_complete_approval(self):
        cases = ("missing file", "wrong section", "missing row")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_friends_name_fixture(root)
                if case == "missing row":
                    self.write_friends_name_exception(root, FRIENDS_NAME_EXCEPTION_ROWS[:-1])
                elif case == "wrong section":
                    self.write_friends_name_exception(root)
                    path = root / "universe/retcons.md"
                    path.write_text(
                        path.read_text(encoding="utf-8").replace(
                            FRIENDS_NAME_EXCEPTION_HEADING, "## An unrelated historical ruling"
                        ),
                        encoding="utf-8",
                    )
                for phase in ("PreReview", "Final"):
                    with self.subTest(phase=phase):
                        completed = self.validate(
                            root, phase, story.name if phase == "PreReview" else None
                        )
                        self.assertNotEqual(0, completed.returncode)

    def test_friends_name_exception_rejects_invalid_or_out_of_scope_rows(self):
        cases = {
            "wrong story": ("another-story", "People", "Crooktail", "universe/characters.md#Crooktail"),
            "wrong kind": ("friends-of-the-night", "Places", "Crooktail", "universe/characters.md#Crooktail"),
            "wrong noun": ("friends-of-the-night", "People", "Someone Else", "universe/characters.md#Crooktail"),
            "wrong source": ("friends-of-the-night", "People", "Crooktail", "universe/characters.md#Someone Else"),
            "wildcard source": ("friends-of-the-night", "People", "Crooktail", "universe/characters.md#*"),
            "missing cell": ("friends-of-the-night", "People", "Crooktail"),
            "extra cell": (*FRIENDS_NAME_EXCEPTION_ROWS[0], "unbounded approval"),
            "duplicate": FRIENDS_NAME_EXCEPTION_ROWS[0],
        }
        for case, invalid_row in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_friends_name_fixture(root)
                # Append to a fully valid approval: ignoring the invalid row must not pass.
                self.write_friends_name_exception(
                    root, (*FRIENDS_NAME_EXCEPTION_ROWS, invalid_row)
                )
                for phase in ("PreReview", "Final"):
                    with self.subTest(phase=phase):
                        completed = self.validate(
                            root, phase, story.name if phase == "PreReview" else None
                        )
                        self.assertNotEqual(0, completed.returncode)

    def test_friends_name_exception_rejects_ambiguous_or_malformed_tables(self):
        header = "| Story | Kind | Noun | Conflicting source |\n"
        divider = "| --- | --- | --- | --- |\n"
        for case in ("duplicate section", "missing header", "missing divider", "repeated header"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_friends_name_fixture(root)
                self.write_friends_name_exception(root)
                path = root / "universe/retcons.md"
                content = path.read_text(encoding="utf-8")
                if case == "duplicate section":
                    content += "\n" + content[content.index(FRIENDS_NAME_EXCEPTION_HEADING):]
                elif case == "missing header":
                    content = content.replace(header, "")
                elif case == "missing divider":
                    content = content.replace(divider, "")
                else:
                    content = content.replace(header, header + header)
                path.write_text(content, encoding="utf-8")
                for phase in ("PreReview", "Final"):
                    with self.subTest(phase=phase):
                        completed = self.validate(
                            root, phase, story.name if phase == "PreReview" else None
                        )
                        self.assertNotEqual(0, completed.returncode)

    def test_friends_name_exception_does_not_cover_additional_collision_sources(self):
        for source in ("NAMES", "universe", "bundle", "current"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_friends_name_fixture(root)
                self.write_friends_name_exception(root)
                if source == "NAMES":
                    (root / "stories/NAMES.md").write_text(
                        "| Identity | Reserved forms | Story |\n| --- | --- | --- |\n"
                        "| Other Crooktail | `Crooktail` | earlier-story |\n",
                        encoding="utf-8",
                    )
                elif source == "universe":
                    path = root / "universe/characters.md"
                    path.write_text(
                        path.read_text(encoding="utf-8")
                        + "\n## Another Person\n\n- Aliases: Crooktail\n",
                        encoding="utf-8",
                    )
                elif source == "bundle":
                    prior = root / "stories/earlier-story"
                    prior.mkdir()
                    (prior / "05-story.md").write_text(
                        "# Earlier Story\n\nCrooktail waited.\n", encoding="utf-8"
                    )
                    (prior / "story.json").write_text('{"canon": false}\n', encoding="utf-8")
                else:
                    prior = root / "stories/another-story"
                    shutil.copytree(story, prior)
                    path = prior / "story.md"
                    path.write_text(
                        path.read_text(encoding="utf-8").replace(
                            "slug: friends-of-the-night", "slug: another-story"
                        ),
                        encoding="utf-8",
                    )
                for phase in ("PreReview", "Final"):
                    with self.subTest(phase=phase):
                        completed = self.validate(
                            root, phase, story.name if phase == "PreReview" else None
                        )
                        self.assertNotEqual(0, completed.returncode)
                        output = completed.stdout + completed.stderr
                        self.assertIn("Crooktail", output)
                        if source == "current" and phase == "Final":
                            self.assertIn("independently marked new", output)

    def test_friends_name_exception_never_exempts_a_different_story(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_friends_name_fixture(root, "another-story")
            self.write_friends_name_exception(root)
            for phase in ("PreReview", "Final"):
                with self.subTest(phase=phase):
                    completed = self.validate(
                        root, phase, story.name if phase == "PreReview" else None
                    )
                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn("Crooktail", completed.stdout + completed.stderr)

    def test_friends_name_exception_does_not_survive_unlocking_or_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_friends_name_fixture(root)
            self.write_friends_name_exception(root)
            path = story / "story.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("canon: true", "canon: false"),
                encoding="utf-8",
            )
            for phase in ("PreReview", "Final"):
                with self.subTest(phase=phase):
                    completed = self.validate(
                        root, phase, story.name if phase == "PreReview" else None
                    )
                    self.assertNotEqual(0, completed.returncode)
                    self.assertIn("Crooktail", completed.stdout + completed.stderr)

    def test_friends_name_exception_keeps_sources_visible_for_recurrence(self):
        for slug in ("friends-of-the-night", "another-story"):
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_friends_name_fixture(root, slug)
                self.write_friends_name_exception(root)
                for name in ("outline.md", "review.md"):
                    path = story / name
                    path.write_text(
                        path.read_text(encoding="utf-8").replace(" | new | ", " | recurring | "),
                        encoding="utf-8",
                    )
                for phase in ("PreReview", "Final"):
                    with self.subTest(phase=phase):
                        completed = self.validate(
                            root, phase, story.name if phase == "PreReview" else None
                        )
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
            self.assertIn("1 current-format stories", completed.stdout)

    def test_final_validation_rejects_orphan_story_directory(self):
        for slug in ("orphan-package", "_trash"):
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                self.make_current_story(root)
                orphan = root / "stories" / slug
                orphan.mkdir()
                (orphan / "notes.txt").write_text("orphan", encoding="utf-8")

                completed = self.validate(root, "Final")

                self.assertNotEqual(0, completed.returncode)
                normalized = " ".join((completed.stdout + completed.stderr).split())
                self.assertIn(
                    f"stories/{slug} is neither a current-format package",
                    normalized,
                )
                self.assertIn("bundle-format package.", normalized)

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

    def test_review_declarations_must_be_unique_and_in_their_sections(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            path = story / "review.md"
            original = path.read_text(encoding="utf-8")
            cases = {
                "conflicting verdict": original + "\nVerdict: REVISE\n",
                "duplicate pass": original + "\nVerdict: PASS\n",
                "conflicting continuity": original + "\n- Prompt: REVISE\n",
                "duplicate continuity": original + "\n- Universe: PASS\n",
                "unresolved blocker": original + "\n- Blocking: Repair the ending.\n",
                "empty verdict": original.replace("Verdict: PASS", "Verdict:\nPASS"),
                "empty continuity": original.replace("- Internal: PASS", "- Internal:\nPASS"),
                "misplaced verdict": original.replace("Verdict: PASS\n", "") + "\nVerdict: PASS\n",
                "misplaced continuity": original.replace("- Prompt: PASS\n", "") + "\n- Prompt: PASS\n",
                "misplaced blocker": original.replace("- Blocking: none\n", "").replace(
                    "## Continuity", "- Blocking: none\n\n## Continuity"
                ),
                "duplicate section": original + "\n## Continuity\n\nA second section.\n",
                "misplaced dialogue": original.replace("- Dialogue: PASS\n", "") + "\n- Dialogue: PASS\n",
                "failed dialogue": original.replace("- Dialogue: PASS", "- Dialogue: REVISE"),
                "duplicate dialogue": original + "\n- Dialogue: PASS\n",
            }
            for label, review in cases.items():
                with self.subTest(case=label):
                    path.write_text(review, encoding="utf-8")
                    result = self.validate(root, "Final")
                    self.assertNotEqual(0, result.returncode, label)
                    self.assertIn("review.md", result.stdout + result.stderr)
                    with self.assertRaisesRegex(ValueError, "not a passing review"):
                        build.capture_story("sample", root, root / "catalog.json")
                    self.assertFalse((root / "catalog.json").exists())
                    self.assertFalse((root / "covers/sample.jpg").exists())

    def test_ambiguous_prior_review_does_not_establish_name_memory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            prior = root / "stories/prior"
            shutil.copytree(story, prior)
            prior_review = prior / "review.md"
            prior_review.write_text(
                prior_review.read_text(encoding="utf-8") + "\nVerdict: REVISE\n",
                encoding="utf-8",
            )
            result = self.validate(root, "PreReview", "sample")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_bundle_name_search_uses_whole_words(self):
        cases = (
            ("Mira", "A distant mirage shimmered.", False),
            ("Mira", "The admiral departed.", False),
            ("Mira", "Mira arrived.", True),
            ("Mira", "MIRA arrived.", True),
            ("Mira", "Mira's map lay open.", True),
            ("Mira", "(Mira) waited.", True),
            ("Mira", "Miranda arrived.", False),
            ("Éva", "Évasion was written on the sign.", False),
            ("Éva", "Éva arrived.", True),
            ("Mira+", "Mira arrived.", False),
            ("Mira+", "Mira+ arrived.", True),
            ("Mira Gate", "Mira Gateway opened.", False),
            ("Mira Gate", "Mira Gate opened.", True),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            originals = {p: p.read_text(encoding="utf-8") for p in story.glob("*.md")}
            bundle = root / "stories/prior"
            bundle.mkdir()
            (bundle / "story.json").write_text('{"canon": true}', encoding="utf-8")
            for name, text, collision in cases:
                with self.subTest(name=name, text=text):
                    for path, source in originals.items():
                        path.write_text(source.replace("Mira", name), encoding="utf-8")
                    (bundle / "05-story.md").write_text(text, encoding="utf-8")
                    for phase in ("PreReview", "Final"):
                        result = self.validate(root, phase, "sample" if phase == "PreReview" else None)
                        self.assertEqual(collision, result.returncode != 0, result.stdout + result.stderr)
                        if collision:
                            self.assertIn("exact", result.stdout + result.stderr)

    def test_documented_variant_preserves_reviewed_recurrence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            for filename in ("outline.md", "review.md"):
                path = story / filename
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "| Mira | new |", "| Mira | recurring |"
                    ),
                    encoding="utf-8",
                )
            review = story / "review.md"
            baseline = review.read_text(encoding="utf-8")
            bundle = root / "stories/prior"
            bundle.mkdir()
            (bundle / "story.json").write_text('{"canon": true}', encoding="utf-8")
            (bundle / "05-story.md").write_text("The Miran coast was quiet.", encoding="utf-8")
            cases = (
                ("Intentional geographic recurrence via the prior bundle's " + chr(96) + "Miran" + chr(96) + " descriptor.", True),
                ("A nonempty note without a cited form.", False),
                ("Prior " + chr(96) + "Miranda" + chr(96) + " is absent.", False),
                ("Prior " + chr(96) + "Mir" + chr(96) + " is only a substring.", False),
            )
            for note, accepted in cases:
                with self.subTest(note=note):
                    review.write_text(
                        baseline.replace("Unique in the checked baseline.", note), encoding="utf-8",
                    )
                    for phase in ("PreReview", "Final"):
                        result = self.validate(root, phase, "sample" if phase == "PreReview" else None)
                        self.assertEqual(accepted, result.returncode == 0, result.stdout + result.stderr)
            # A pending/contradictory review cannot supply variant provenance.
            review.write_text(
                baseline.replace("Unique in the checked baseline.", cases[0][0])
                + "\nVerdict: REVISE\n",
                encoding="utf-8",
            )
            result = self.validate(root, "PreReview", "sample")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("no exact prior use", result.stdout + result.stderr)

    def test_title_image_requires_a_complete_jpeg_decode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            path = story / "title-image.jpg"
            valid = path.read_bytes()
            header_only = (
                bytes.fromhex("ffd8ffc0001108") + (1536).to_bytes(2, "big")
                + (864).to_bytes(2, "big") + bytes.fromhex("03011100021100031100ffd9")
            )
            path.write_bytes(valid)
            build._validate_title_image(path)
            for case in ("header-only", "truncated", "disguised-png", "wrong-size"):
                with self.subTest(case=case):
                    if case == "header-only":
                        path.write_bytes(header_only)
                    elif case == "truncated":
                        path.write_bytes(valid[:-30])
                    elif case == "disguised-png":
                        Image.new("RGB", (864, 1536)).save(path, format="PNG")
                    else:
                        self.write_title_image(story, 400, 600)
                    with self.assertRaises(ValueError):
                        build._validate_title_image(path)
                    with self.assertRaises(ValueError):
                        build.capture_story("sample", root, root / "catalog.json")
                    result = self.validate(root, "Final")
                    self.assertNotEqual(0, result.returncode, result.stdout + result.stderr)
                    self.assertIn("title-image.jpg", result.stdout + result.stderr)

    def test_title_image_decoder_reports_missing_pillow_as_tooling_failure(self):
        result = subprocess.run(
            [sys.executable, "-I", "-S", str(REPO / "pages/image_validation.py")],
            input="[]", text=True, capture_output=True, check=False,
        )
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stdout)
        self.assertIn("Pillow", result.stderr)
        self.assertIn("python -m pip install -r pages/requirements.txt", result.stderr)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell is required")
    def test_final_rejects_invalid_cover_when_pillow_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            story = self.make_current_story(root)
            (story / "title-image.jpg").write_bytes(b"not a JPEG")
            # -I also excludes ambient PYTHONPATH; -S hides installed Pillow.
            command = [sys.executable, "-I", "-S", str(REPO / "pages/image_validation.py")]
            result = self.validate_with_decoder(
                root, f"import os\nos.execv({sys.executable!r}, {command!r})\n"
            )
            output = result.stdout + result.stderr
            self.assertNotEqual(0, result.returncode, output)
            self.assertIn("Title-image decoder failed", output)
            self.assertIn("Pillow", output)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell is required")
    def test_final_rejects_invalid_title_image_decoder_responses(self):
        cases = (
            ("empty-success", "", 0),
            ("empty-failure", "", 1),
            ("whitespace-success", " \n\t ", 0),
            ("whitespace-failure", " \n\t ", 1),
            ("invalid-json", "[", 0),
            ("null", "null", 0),
            ("object", "{}", 0),
            ("string", '"error"', 1),
            ("number", "0", 0),
            ("boolean", "false", 0),
            ("null-member", "[null]", 1),
            ("number-member", "[1]", 1),
            ("object-member", '[{"error": "invalid cover"}]', 1),
            ("nested-array", '[[]]', 1),
            ("empty-error", '[""]', 1),
            ("whitespace-error", '["  "]', 1),
            ("mixed-members", '["invalid cover", null]', 1),
            ("errors-with-success", '["invalid cover"]', 0),
            ("no-errors-with-failure", "[]", 1),
            ("unexpected-exit", "[]", 2),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_current_story(root)
            for case, stdout, exit_code in cases:
                with self.subTest(case=case):
                    result = self.validate_with_decoder(
                        root,
                        f"import sys\nsys.stdout.write({stdout!r})\nraise SystemExit({exit_code})\n",
                    )
                    output = result.stdout + result.stderr
                    self.assertNotEqual(0, result.returncode, output)
                    self.assertIn("Title-image decoder failed", output)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell is required")
    def test_final_accepts_valid_title_image_decoder_responses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_current_story(root)
            for errors in ([], ["first invalid cover"], ["first invalid cover", "second invalid cover"]):
                with self.subTest(errors=errors):
                    exit_code = 1 if errors else 0
                    result = self.validate_with_decoder(
                        root,
                        f"import sys\nsys.stdout.write({json.dumps(errors)!r})\nraise SystemExit({exit_code})\n",
                    )
                    output = result.stdout + result.stderr
                    self.assertEqual(not errors, result.returncode == 0, output)
                    self.assertNotIn("Title-image decoder failed", output)
                    for error in errors:
                        self.assertIn(error, output)

    def test_capture_preserves_editorial_prompt_while_refreshing_prose(self):
        for operation in ("capture", "capture-all"):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root)
                snapshot = root / "catalog.json"
                first = build.capture_story("sample", root, snapshot).stories[0]
                self.assertEqual("A traveler returns through a gate.", first.prompt)
                editorial = "The approved public premise."
                build.save_catalog((replace(first, prompt=editorial),), snapshot)
                prompt = story / "prompt.md"
                prompt.write_text(
                    prompt.read_text(encoding="utf-8").replace(
                        "A traveler returns through a gate.", "A changed production premise."
                    ),
                    encoding="utf-8",
                )
                prose = story / "story.md"
                prose.write_text(
                    prose.read_text(encoding="utf-8") + "\nShe closed the gate.\n",
                    encoding="utf-8",
                )
                result = (
                    build.capture_story("sample", root, snapshot)
                    if operation == "capture" else build.capture_all(root, snapshot)
                )
                self.assertEqual(editorial, result.stories[0].prompt)
                self.assertIn("She closed the gate.", result.stories[0].body)
                self.assertEqual(4, json.loads(snapshot.read_text())["schemaVersion"])

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

    def test_capture_all_refreshes_only_existing_publications(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            published = self.make_current_story(root)
            snapshot = root / "catalog.json"
            build.capture_story("sample", root, snapshot)

            unpublished = root / "stories/unpublished"
            shutil.copytree(published, unpublished)
            story_path = unpublished / "story.md"
            story_path.write_text(
                story_path.read_text(encoding="utf-8")
                .replace("title: Sample", "title: Unpublished")
                .replace("slug: sample", "slug: unpublished")
                .replace("# Sample", "# Unpublished"),
                encoding="utf-8",
            )

            catalog = build.capture_all(root, snapshot)

            self.assertEqual(("sample",), tuple(story.slug for story in catalog.stories))
            self.assertFalse((root / "covers/unpublished.jpg").exists())

    def test_capture_refuses_to_demote_published_canon(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_current_story(root)
            snapshot = root / "catalog.json"
            captured = build.capture_story("sample", root, snapshot)
            build.save_catalog(
                (replace(captured.stories[0], canon=True, status="canon"),), snapshot
            )

            conflicts = build.published_canon_marker_conflicts(
                build.load_catalog(snapshot), root
            )
            self.assertEqual(("sample",), conflicts)
            for operation in (
                lambda: build.capture_story("sample", root, snapshot),
                lambda: build.capture_all(root, snapshot),
            ):
                with self.subTest(operation=operation), self.assertRaisesRegex(
                    ValueError, "Refusing to demote published canon"
                ):
                    operation()

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
            "> [wp] A traveler returns through a gate.",
        )
        for source in cases:
            with self.subTest(source=source):
                prompt = f"# Prompt\n\n## Prompt\n\n{source}\n\n## Constraints\n\n- None\n"
                self.assertEqual(
                    "A traveler returns through a gate.",
                    build.parse_writing_prompt(prompt, Path("prompt.md")),
                )

    def test_prompt_parser_uses_only_wp_paragraph_for_pages(self):
        prompt = (
            "# Prompt\n\n## Prompt\n\n"
            "> [WP] The stars turn to the first people. Humanity!\n"
            ">\n"
            "> Some context to think about: Earth may simply be first.\n\n"
            "## Constraints\n\n- None\n"
        )

        self.assertEqual(
            "The stars turn to the first people. Humanity!",
            build.parse_writing_prompt(prompt, Path("prompt.md")),
        )

    def test_prompt_parser_starts_at_inline_wp_marker(self):
        prompt = (
            "# Prompt\n\n## Prompt\n\n"
            "> Replacement and production context remains in this file.\n\n"
            "> The title suggests [WP] The sky remembers us from both directions.\n\n"
            "## Constraints\n\n- None\n"
        )

        self.assertEqual(
            "The sky remembers us from both directions.",
            build.parse_writing_prompt(prompt, Path("prompt.md")),
        )

    def test_prompt_parser_preserves_legacy_untagged_prompt_section(self):
        prompt = (
            "# Prompt\n\n## Prompt\n\n"
            "> A quiet walk.\n> The rain follows.\n\n"
            "## Constraints\n\n- None\n"
        )

        self.assertEqual(
            "A quiet walk. The rain follows.",
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

    def test_repository_story_and_publication_inventory_is_reconciled(self):
        catalog = build.load_catalog()
        timeline = build.load_timeline(catalog)

        source_count, published_count, canon_count = build.validate_repository_inventory(
            catalog, timeline
        )

        self.assertEqual(len(catalog.stories), source_count)
        self.assertEqual(len(catalog.stories), published_count)
        self.assertEqual(sum(story.canon for story in catalog.stories), canon_count)

    def test_superseded_sky_source_is_removed_but_return_bookend_remains(self):
        catalog = build.load_catalog()
        timeline = build.load_timeline(catalog)
        published = {story.slug for story in catalog.stories}
        placements = {slug for cycle in timeline.cycles for slug in cycle.stories}

        self.assertFalse((REPO / "stories/the-sky-remembers-us").exists())
        self.assertTrue((REPO / "stories/the-sky-remembers-us-return/story.md").is_file())
        self.assertNotIn("the-sky-remembers-us", published)
        self.assertIn("the-sky-remembers-us-return", published)
        self.assertIn("the-sky-remembers-us-return", placements)
        self.assertTrue((REPO / "pages/covers/the-sky-remembers-us-return.jpg").is_file())

    def test_bundle_index_rejects_duplicate_story_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            index = Path(temporary) / "INDEX.md"
            index.write_text(
                "| Story | Title |\n"
                "| --- | --- |\n"
                "| `duplicate` | *First* |\n"
                "| `duplicate` | *Second* |\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "repeats story rows"):
                build._bundle_index_slugs(index)

    def test_stored_timeline_places_every_story_once(self):
        catalog = build.load_catalog()
        timeline = build.load_timeline(catalog)
        placements = [slug for cycle in timeline.cycles for slug in cycle.stories]
        self.assertEqual(len(catalog.stories), len(placements))
        self.assertEqual({story.slug for story in catalog.stories}, set(placements))
        self.assertEqual(len(placements), len(set(placements)))
        self.assertEqual(set(placements), set(timeline.story_confidence))
        self.assertEqual(set(placements), set(timeline.story_placements))
        self.assertGreater(len(timeline.cycles), 4)
        states = {slug: cycle.magic_state for cycle in timeline.cycles for slug in cycle.stories}
        self.assertEqual("old-magic", states["all-accounts-due"])
        self.assertEqual("old-magic", states["strength-of-ten"])
        self.assertEqual("long-dark", states["the-names-on-the-cups"])
        self.assertEqual("new-magic", states["the-sky-remembers-us-return"])
        # Instruments, contemporary settings, or quiet scenes do not establish
        # a magicless mechanism for these observed effects.
        for slug in ("the-upward-rain", "the-kingdom-was-the-easy-part",
                     "the-morning-her-hand-moved", "the-night-harvest"):
            with self.subTest(slug=slug):
                self.assertNotEqual("long-dark", states[slug])
        self.assertIn("daughter-of-the-sun", timeline.story_spans)
        self.assertIn("the-count-was-131072", timeline.story_spans)
        self.assertIn("the-small-moon-rose-first", timeline.story_spans)

    def test_temporal_placement_separates_the_bay_arc_without_breaking_local_intervals(self):
        timeline = build.load_timeline(build.load_catalog())
        location = {slug: (index, timeline.story_placements[slug].position)
                    for index, cycle in enumerate(timeline.cycles) for slug in cycle.stories}
        early = location["not-about-that"]
        attendance = location["the-attendance-ledger"]
        help_network = location["the-help-network"]
        bay = location["solstice-evening-bell"]
        dress = location["the-dress-they-brought-her"]
        museum = location["the-count-was-131072"]
        self.assertLess(early[0], attendance[0])
        self.assertEqual(attendance[0], help_network[0])
        self.assertLess(attendance, help_network)
        self.assertLess(help_network[0], bay[0])
        self.assertEqual(bay[0], dress[0])
        self.assertEqual(bay[0], museum[0])
        self.assertLess(bay, dress)
        self.assertLess(dress, museum)
        self.assertLess(bay, location["daughter-of-the-sun"])
        self.assertLess(location["the-small-moon-rose-first"], location["daughter-of-the-sun"])
        self.assertLess(location["all-accounts-due"], location["the-names-on-the-cups"])
        self.assertLess(location["the-names-on-the-cups"], location["the-sky-remembers-us-return"])
        old = [slug for cycle in timeline.cycles if cycle.magic_state == "old-magic" for slug in cycle.stories]
        new = [slug for cycle in timeline.cycles if cycle.magic_state == "new-magic" for slug in cycle.stories]
        self.assertEqual("all-accounts-due", old[-1])
        self.assertEqual("the-sky-remembers-us-return", new[0])
        order = {"old-magic": 0, "long-dark": 1, "new-magic": 2}
        states = [order[cycle.magic_state] for cycle in timeline.cycles if cycle.magic_state in order]
        self.assertEqual(sorted(states), states)
        self.assertEqual(location["voice-of-silence"][0], location["a-lock-on-the-inside"][0])
        self.assertLess(location["voice-of-silence"], location["a-lock-on-the-inside"])

    def test_timeline_accepts_collection_growth_without_fixed_totals(self):
        catalog = build.load_catalog()
        extra = replace(catalog.stories[0], slug="additional-story")
        expanded = build.Catalog((*catalog.stories, extra))
        value = json.loads(build.TIMELINE_PATH.read_text(encoding="utf-8"))
        last_position = value["storyPlacements"][value["cycles"][-1]["eras"][-1]["stories"][-1]]["position"]
        value["cycles"][-1]["eras"].append({
            "id": "additional-era", "title": "Another inhabited horizon",
            "description": "A later society has another history to tell.",
            "context": ["A distinct civic setting.", "An inherited local technology."],
            "sequenceNote": "A proposed later period.", "stories": [extra.slug],
        })
        value["storyPlacements"][extra.slug] = {"position": (last_position + 100) / 2, "note": "A later proposed story position."}
        value["storyConfidence"][extra.slug] = "speculative"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "timeline.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            timeline = build.load_timeline(expanded, path)
        self.assertEqual(len(expanded.stories), len(timeline.story_placements))
        self.assertIn(extra.slug, timeline.cycles[-1].stories)
        self.assertIn('id="era-additional-era"', build.render_timeline(expanded, timeline))
        self.assertIn(f'id="story-{extra.slug}"', build.render_timeline(expanded, timeline))

    def test_timeline_rejects_duplicate_story_placement(self):
        catalog = build.load_catalog()
        value = json.loads(build.TIMELINE_PATH.read_text(encoding="utf-8"))
        value["cycles"][1]["eras"][0]["stories"].append(value["cycles"][0]["eras"][0]["stories"][0])
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "timeline.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "repeats already placed stories"):
                build.load_timeline(catalog, path)

    def test_atlas_renders_individual_chronological_events_and_resolvable_connections(self):
        catalog = build.load_catalog()
        timeline = build.load_timeline(catalog)
        rendered = build.render_timeline(catalog, timeline)
        self.assertEqual(len(catalog.stories), rendered.count('class="worldline-event '))
        self.assertEqual(len(catalog.stories), rendered.count('<img src="covers/'))
        self.assertEqual(len(timeline.cycles), rendered.count("data-cycle-section="))
        self.assertEqual(sum(len(cycle.eras) for cycle in timeline.cycles), rendered.count("data-era-section="))
        self.assertEqual(len(timeline.connections), rendered.count("data-thread-kind="))
        self.assertNotIn("atlas-story-grid", rendered)
        self.assertNotIn("data-era-stop", rendered)
        self.assertNotIn("reading cycle", rendered)
        rendered_order = re.findall(r'<article class="worldline-event [^>]+id="story-([^" ]+)"', rendered)
        self.assertEqual([slug for cycle in timeline.cycles for slug in cycle.stories], rendered_order)
        for story in catalog.stories:
            self.assertIn(f'href="stories/{story.slug}.html"', rendered)
        ids = re.findall(r'\bid="([^" ]+)"', rendered)
        self.assertEqual(len(ids), len(set(ids)))
        for target in re.findall(r'href="#([^" ]+)"', rendered):
            self.assertIn(target, ids, f"Broken atlas fragment: {target}")
        for label in ("Galactic Cycle", "spacing is schematic", "Direct connection", "Thematic echo", "Date unresolved"):
            self.assertIn(label, rendered)
        self.assertIn('role="status"', rendered)
        self.assertIn('aria-label="Orbital cycle navigator"', rendered)
        self.assertIn('href="atlas.css"', rendered)
        self.assertIn("Life in this era", rendered)
        self.assertIn("regional stories may overlap in time", rendered)

    def test_contextual_eras_preserve_cohorts_and_separate_incompatible_rules(self):
        timeline = build.load_timeline(build.load_catalog())
        location = {slug: (cycle.id, era.id) for cycle in timeline.cycles
                    for era in cycle.eras for slug in era.stories}
        for cohort in (
            ("the-mercy-circuit", "sakura-hearted", "a-little-more-room"),
            ("the-warmest-person-in-the-room", "captive-couples", "the-name-i-kept"),
            ("the-attendance-ledger", "the-help-network"),
        ):
            with self.subTest(cohort=cohort):
                self.assertEqual(1, len({location[slug] for slug in cohort}))
        self.assertNotEqual(location["a-darkness-written-under-skin"][0],
                            location["what-turned-eighteen"][0])

    def test_atlas_rejects_missing_story_invalid_positions_and_broken_connections(self):
        catalog = build.load_catalog()
        original = json.loads(build.TIMELINE_PATH.read_text(encoding="utf-8"))
        cycle_index, era_index = next((ci, ei) for ci, cycle in enumerate(original["cycles"])
                                     for ei, era in enumerate(cycle["eras"]) if len(era["stories"]) > 1)
        def members(value):
            return value["cycles"][cycle_index]["eras"][era_index]["stories"]
        first, second = members(original)[:2]
        mutations = (
            ("missing story", lambda v: members(v).pop(), "missing published stories"),
            ("no eras", lambda v: v["cycles"][0].update(eras=[]), "eras must be a non-empty list"),
            ("duplicate era", lambda v: v["cycles"][-1]["eras"][-1].update(id=v["cycles"][0]["eras"][0]["id"]), "duplicate id"),
            ("empty context", lambda v: v["cycles"][0]["eras"][0].update(context=[]), "two to four historical observations"),
            ("blank context", lambda v: v["cycles"][0]["eras"][0].update(context=["", "A place."]), "non-empty string"),
            ("missing position", lambda v: v["storyPlacements"].pop(first), "cover every published story"),
            ("empty rationale", lambda v: v["storyPlacements"][first].update(note=""), "non-empty string"),
            ("non-finite position", lambda v: v["storyPlacements"][first].update(position=float("nan")), "must be finite"),
            ("out of cycle", lambda v: v["storyPlacements"][first].update(position=100), "must be finite"),
            ("overlapping positions", lambda v: v["storyPlacements"][second].update(position=v["storyPlacements"][first]["position"]), "increase strictly"),
            ("reversed order", lambda v: members(v).reverse(), "increase strictly"),
            ("unknown connection", lambda v: v["connections"][0].update(to="nonexistent-story"), "Connection endpoints"),
            ("self connection", lambda v: v["connections"][0].update(to=v["connections"][0]["from"]), "Connection endpoints"),
            ("unknown kind", lambda v: v["connections"][0].update(kind="sequel-maybe"), "Connection kind"),
        )
        for name, mutate, error in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                value = json.loads(json.dumps(original))
                mutate(value)
                path = Path(temporary) / "timeline.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, error):
                    build.load_timeline(catalog, path)

    def test_every_page_renders_shared_theme_controls_and_prepaint_bootstrap(self):
        catalog = build.load_catalog()
        story = catalog.stories[0]
        rendered_pages = {
            "library": (build.render_index(build.Catalog((story,))), "theme.js"),
            "chronology": (
                build.render_timeline(catalog, build.load_timeline(catalog)),
                "theme.js",
            ),
            "story": (build.render_story(story), "../theme.js"),
        }

        for page_name, (rendered, script_href) in rendered_pages.items():
            with self.subTest(page=page_name):
                self.assertEqual(1, rendered.count('class="theme-toggle"'))
                self.assertIn(
                    '<button class="theme-toggle" type="button" data-theme-toggle',
                    rendered,
                )
                self.assertIn('data-theme-label="light"', rendered)
                self.assertIn('data-theme-label="dark"', rendered)
                self.assertEqual(
                    1,
                    rendered.count(f'<script src="{script_href}" defer></script>'),
                )
                self.assertIn('<meta name="color-scheme" content="light dark">', rendered)
                self.assertIn('<meta name="theme-color"', rendered)

                bootstrap_start = rendered.index("<script>(function()")
                bootstrap_end = rendered.index("</script>", bootstrap_start)
                bootstrap = rendered[bootstrap_start:bootstrap_end]
                self.assertIn("story-computing-machine-theme", bootstrap)
                self.assertIn("localStorage.getItem", bootstrap)
                self.assertIn("prefers-color-scheme: dark", bootstrap)
                self.assertIn("document.documentElement.dataset.theme", bootstrap)
                self.assertLess(bootstrap_start, rendered.index('<link rel="stylesheet"'))

    def test_theme_script_implements_persistent_accessible_toggle(self):
        script = (REPO / "pages/theme.js").read_text(encoding="utf-8")

        for expected in (
            'var STORAGE_KEY = "story-computing-machine-theme"',
            'document.querySelector("[data-theme-toggle]")',
            'document.querySelector(\'meta[name="theme-color"]\')',
            "window.localStorage.getItem(STORAGE_KEY)",
            "window.localStorage.setItem(STORAGE_KEY, theme)",
            'toggle.addEventListener("click"',
            'mediaQuery.addEventListener("change", followSystemPreference)',
            'mediaQuery.addListener(followSystemPreference)',
            'root.setAttribute("data-theme", nextTheme)',
            "root.style.colorScheme = nextTheme",
            'getPropertyValue("--paper")',
            'toggle.setAttribute("aria-label", action)',
            'toggle.setAttribute("title", action)',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, script)

        self.assertGreaterEqual(script.count("try {"), 5)
        self.assertIn('value === "light" || value === "dark"', script)
        self.assertIn("if (!hasExplicitPreference)", script)

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
            self.assertTrue((output / "theme.js").is_file())
            self.assertTrue((output / "timeline.js").is_file())
            self.assertTrue((output / "styles.css").is_file())
            self.assertTrue((output / "atlas.css").is_file())
            self.assertEqual(
                (REPO / "pages/theme.js").read_bytes(),
                (output / "theme.js").read_bytes(),
            )
            hero_art = output / build.WORLDLINE_HERO_ART_PATH.name
            self.assertTrue(hero_art.is_file())
            self.assertEqual(build.WORLDLINE_HERO_ART_PATH.read_bytes(), hero_art.read_bytes())
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "stories").glob("*.html"))),
            )
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "covers").glob("*.jpg"))),
            )
            self.assertFalse((output / "timeline-icons").exists())
            self.assertIn(
                f"{len(catalog.stories)} stored publications",
                (output / "index.html").read_text(encoding="utf-8"),
            )
            self.assertIn('class="story-grid"', (output / "index.html").read_text(encoding="utf-8"))
            timeline_page = (output / "timeline.html").read_text(encoding="utf-8")
            self.assertNotIn("data-timeline-filter", timeline_page)
            self.assertNotIn("data-timeline-search", timeline_page)

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
