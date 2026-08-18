import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("story_site", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = build
SPEC.loader.exec_module(build)

REPO = Path(__file__).resolve().parents[1]
STORY_VALIDATOR = REPO / ".agents/skills/story-room/scripts/Test-Stories.ps1"
NEW_STORY = REPO / ".agents/skills/story-room/scripts/new-story.ps1"


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
                "Craft profile: prospective-2026-08-18",
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
                "Dialogue pressure (optional, at most 75 words):",
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
            self.assertTrue((root / "covers/sample.jpg").is_file())

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
            self.assertTrue((output / "styles.css").is_file())
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "stories").glob("*.html"))),
            )
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "covers").glob("*.jpg"))),
            )
            self.assertIn(
                f"{len(catalog.stories)} stored publications",
                (output / "index.html").read_text(encoding="utf-8"),
            )
            self.assertIn('class="story-grid"', (output / "index.html").read_text(encoding="utf-8"))

    def test_rendering_places_cover_below_title_and_prompt(self):
        story = build.load_catalog().stories[0]
        rendered = build.render_story(story)
        self.assertEqual(1, rendered.count("<h1>"))
        self.assertIn('<span class="prompt-label">Prompt</span>', rendered)
        self.assertIn(f'src="../{story.cover}"', rendered)
        self.assertLess(rendered.index("<h1>"), rendered.index('class="prompt"'))
        self.assertLess(rendered.index('class="prompt"'), rendered.index('class="story-cover"'))

    def test_index_cards_include_title_cover_and_prompt(self):
        story = build.load_catalog().stories[0]
        rendered = build.render_index(build.Catalog((story,)))
        self.assertIn('class="story-card"', rendered)
        self.assertIn(f'src="{story.cover}"', rendered)
        self.assertIn(f'<span class="story-title">{build.html.escape(story.title)}</span>', rendered)
        self.assertIn(build.html.escape(story.prompt), rendered)

    def test_output_cannot_replace_repository_root(self):
        with self.assertRaises(ValueError):
            build.prepare_output(REPO)


if __name__ == "__main__":
    unittest.main()
