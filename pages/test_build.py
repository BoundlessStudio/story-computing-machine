import importlib.util
import shutil
import tempfile
import unittest
import sys
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("story_site", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = build
SPEC.loader.exec_module(build)
REPO = Path(__file__).resolve().parents[1]


class SiteBuildTests(unittest.TestCase):
    def make_current_story(self, root: Path) -> Path:
        stories = root / "stories"
        shutil.copytree(REPO / "stories" / "_template", stories / "_template")
        story = stories / "sample"
        story.mkdir()
        (root / "universe").mkdir()
        (story / "prompt.md").write_text(
            "# Prompt\n\n## Prompt\n\n> [WP] A small test.\n",
            encoding="utf-8",
        )
        (story / "outline.md").write_text(
            "# Outline\n\n"
            "## Story\n\n- Premise: Mira returns.\n\n"
            "## Beats\n\n1. Mira crosses the gate.\n\n"
            "## People\n\n| Name | Role |\n| --- | --- |\n| Mira | Traveler |\n\n"
            "## Places\n\n| Name | Role |\n| --- | --- |\n| Alder Gate | Crossing |\n\n"
            "## Continuity\n\n- Canon used: none.\n",
            encoding="utf-8",
        )
        (story / "story.md").write_text(
            "---\ntitle: Sample\nslug: sample\ncreated: 2026-08-06\ncanon: false\n---\n\n"
            "# Sample\n\nMira walked through Alder Gate and returned.\n",
            encoding="utf-8",
        )
        (story / "review.md").write_text(
            "# Review\n\nVerdict: PASS\n\n"
            "## People\n\n| Noun | Status | Continuity note |\n"
            "| --- | --- | --- |\n| Mira | new | Unique in the checked baseline. |\n\n"
            "## Places\n\n| Noun | Status | Continuity note |\n"
            "| --- | --- | --- |\n| Alder Gate | new | Local to this story. |\n\n"
            "## Continuity\n\n- Prompt: PASS\n- Universe: PASS\n- Internal: PASS\n\n"
            "## Findings\n\n- Blocking: none\n- Notes: none\n",
            encoding="utf-8",
        )
        return story

    def test_stored_catalog_is_valid_and_newest_first(self):
        catalog = build.load_catalog()
        self.assertGreater(len(catalog.stories), 0)
        dates = [story.created for story in catalog.stories]
        self.assertEqual(sorted(dates, reverse=True), dates)
        self.assertEqual(len({story.slug for story in catalog.stories}), len(catalog.stories))

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
            self.assertEqual(
                len(catalog.stories),
                len(list((output / "stories").glob("*.html"))),
            )
            self.assertIn(
                f"{len(catalog.stories)} stored publications",
                (output / "index.html").read_text(encoding="utf-8"),
            )

    def test_capture_current_story_updates_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_current_story(root)
            snapshot = root / "catalog.json"
            catalog = build.capture_story("sample", root, snapshot)
            self.assertEqual(("sample",), tuple(item.slug for item in catalog.stories))
            self.assertEqual(catalog, build.load_catalog(snapshot))

    def test_capture_rejects_missing_nouns_failed_continuity_and_name_collisions(self):
        cases = ("missing nouns", "failed continuity", "legacy name collision")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                story = self.make_current_story(root)
                review_path = story / "review.md"
                if case == "missing nouns":
                    review = review_path.read_text(encoding="utf-8")
                    start = review.index("## People")
                    end = review.index("## Continuity")
                    review_path.write_text(review[:start] + review[end:], encoding="utf-8")
                elif case == "failed continuity":
                    review = review_path.read_text(encoding="utf-8")
                    review_path.write_text(
                        review.replace("- Universe: PASS", "- Universe: PENDING"),
                        encoding="utf-8",
                    )
                else:
                    (root / "stories" / "NAMES.md").write_text(
                        "| Identity | Reserved forms | Story |\n"
                        "| --- | --- | --- |\n"
                        "| Earlier Mira | `Mira` | locked-story |\n",
                        encoding="utf-8",
                    )
                with self.assertRaisesRegex(ValueError, "validation failed"):
                    build.capture_story("sample", root, root / "catalog.json")

    def test_rendering_keeps_one_visible_story_title(self):
        story = build.load_catalog().stories[0]
        rendered = build.render_story(story)
        self.assertEqual(1, rendered.count("<h1>"))
        self.assertIn('<span class="prompt-label">Prompt</span>', rendered)

    def test_output_cannot_replace_repository_root(self):
        with self.assertRaises(ValueError):
            build.prepare_output(REPO)


if __name__ == "__main__":
    unittest.main()
