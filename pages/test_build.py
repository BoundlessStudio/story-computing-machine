import importlib.util
import json
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
    def test_real_catalog_contains_every_story(self):
        catalog = build.load_catalog(REPO)
        expected = {
            directory.name
            for directory in (REPO / "stories").iterdir()
            if directory.is_dir()
            and not directory.name.startswith("_")
        }
        actual = {story.metadata.slug for story in catalog.stories}
        self.assertEqual(expected, actual)
        self.assertTrue(any(not story.metadata.publish for story in catalog.stories))
        crown = next(item for item in catalog.stories if item.metadata.slug == "a-crown-of-quiet-hours")
        self.assertTrue(crown.metadata.canon)
        self.assertEqual("final", crown.metadata.status)
        self.assertTrue(crown.prompt.startswith("The benevolent monarchy"))

    def test_real_catalog_lists_newest_stories_first(self):
        catalog = build.load_catalog(REPO)
        dates = [story.metadata.created for story in catalog.stories]
        self.assertEqual(sorted(dates, reverse=True), dates)
        self.assertEqual(max(dates), catalog.stories[0].metadata.created)
        addition_order = build._story_addition_order(REPO)
        for date in set(dates):
            same_day = [addition_order[story.metadata.slug] for story in catalog.stories if story.metadata.created == date]
            self.assertEqual(sorted(same_day), same_day)

    def test_real_build_writes_index_and_every_story(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            catalog = build.build(output, REPO, require_integrity_validator=False)
            self.assertTrue((output / "index.html").is_file())
            self.assertEqual(len(catalog.stories), len(list((output / "stories").glob("*.html"))))
            self.assertIn("A Crown of Quiet Hours", (output / "index.html").read_text(encoding="utf-8"))

    def test_release_schema_is_simplified_v3(self):
        release = json.loads((REPO / "stories" / "a-crown-of-quiet-hours" / "release.json").read_text(encoding="utf-8"))
        self.assertEqual(3, release["schemaVersion"])
        self.assertEqual({"schemaVersion", "certified", "storySlug", "certifiedAt", "certificationBasis", "artifacts", "review", "nameCheck", "dependencies"}, set(release))

    def test_final_frontmatter_matches_machine_identity(self):
        catalog = build.load_catalog(REPO)
        for story in catalog.stories:
            front, _ = build.parse_front_matter((story.metadata.directory / "05-story.md").read_text(encoding="utf-8"), story.metadata.directory / "05-story.md")
            self.assertEqual(story.metadata.slug, front["slug"])
            self.assertEqual(story.metadata.title, front["title"])
            self.assertEqual(story.metadata.created, front["created"])

    def test_legacy_attestation_matches_catalog(self):
        acceptance = json.loads((REPO / "stories" / "legacy-acceptance.json").read_text(encoding="utf-8"))
        accepted = {item["slug"] for item in acceptance["stories"]}
        catalog = build.load_catalog(REPO)
        legacy = {item.metadata.slug for item in catalog.stories if item.metadata.provenance == "legacy-user-attested"}
        self.assertEqual(accepted, legacy)

    def test_contract_uses_git_pr_trust_model(self):
        contract = build.load_pipeline_contract(REPO / "schemas" / "pipeline-contract.json")
        self.assertEqual("git-pr-human-review", contract["trustModel"])
        self.assertEqual(2, contract["story"]["schemaVersion"])
        self.assertEqual(3, contract["release"]["schemaVersion"])

    def test_output_cannot_replace_repository_root(self):
        with self.assertRaises(ValueError):
            build.prepare_output(REPO, REPO)

    def test_index_labels_canon(self):
        catalog = build.load_catalog(REPO)
        rendered = build.render_index(catalog)
        self.assertIn("Canon", rendered)
        self.assertIn(f"{len(catalog.stories)} stories", rendered)
        self.assertEqual(len(catalog.stories), rendered.count('<span class="prompt-label">Prompt</span>'))
        self.assertEqual(len(catalog.stories), rendered.count("<time datetime="))
        self.assertIn(
            f'<time datetime="{catalog.stories[0].metadata.created}">{catalog.stories[0].metadata.created}</time>',
            rendered,
        )

    def test_pages_link_to_repository_with_github_icon(self):
        catalog = build.load_catalog(REPO)
        for rendered in (build.render_index(catalog), build.render_story(catalog.stories[0])):
            self.assertIn(f'href="{build.REPOSITORY_URL}"', rendered)
            self.assertIn('class="repository-link"', rendered)
            self.assertIn('aria-label="View BoundlessStudio/story-computing-machine on GitHub"', rendered)
            self.assertIn('<svg ', rendered)

    def test_story_has_one_visible_title_and_displays_prompt(self):
        catalog = build.load_catalog(REPO)
        for story in catalog.stories:
            rendered = build.render_story(story)
            self.assertEqual(1, rendered.count("<h1>"), story.metadata.slug)
        crown = next(item for item in catalog.stories if item.metadata.slug == "a-crown-of-quiet-hours")
        rendered = build.render_story(crown)
        self.assertIn('<span class="prompt-label">Prompt</span>', rendered)
        self.assertIn("The benevolent monarchy", rendered)

    def test_pages_follow_the_system_color_scheme(self):
        rendered = build.render_index(build.load_catalog(REPO))
        self.assertIn("color-scheme:light dark", rendered)
        self.assertIn("prefers-color-scheme:dark", rendered)


if __name__ == "__main__":
    unittest.main()
