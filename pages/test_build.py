"""Publication checks for illustrated readers at existing story URLs."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import html
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from pages import build, illustrated_editions


def story_fixture(slug="source-story", **changes):
    story = build.Story(
        slug=slug, title="Source Story", created="2026-09-13",
        created_at="2026-09-13T12:00:00+00:00", edited="2026-09-13",
        rating="YA", canon=True, status="complete", prompt="A published prompt.",
        cover=f"covers/{slug}.jpg", body="# Source Story\n\nA quiet beginning.\n\nAn open door.\n",
    )
    return replace(story, **changes)


def edition_fixture(story):
    body = story.body
    return {
        "slug": "illustrated-story", "title": story.title, "mode": "classic",
        "source": {"slug": story.slug, "bodySha256": hashlib.sha256(body.encode()).hexdigest()},
        "body": body,
        "cover": {"id": "cover", "path": "illustrated/illustrated-story/cover.png", "sha256": ""},
        "illustrations": [{
            "id": "door", "path": "illustrated/illustrated-story/door.png", "sha256": "",
            "after": illustrated_editions.block_anchors(body, story.title)[0]["id"],
            "layout": "inline", "alt": "A door opening into a sunlit room.",
        }],
    }


class IllustratedPublicationTests(unittest.TestCase):
    def setUp(self):
        self.story = story_fixture()
        self.edition = edition_fixture(self.story)

    def test_cover_overlay_keeps_one_card_and_source_identity(self):
        older = story_fixture(
            "older-story", title="Older Story", created="2026-09-12",
            created_at="2026-09-12T12:00:00+00:00", edited="2026-09-12", canon=False,
        )
        catalog = build.Catalog((self.story, older))
        before = deepcopy(catalog)
        self.edition["title"] = "A Different Edition Label"
        result = build.render_index(catalog, [self.edition])
        self.assertEqual(result.count('<li class="story-card">'), 2)
        self.assertIn("2 stored publications.", result)
        self.assertLess(result.index('href="stories/source-story.html"'),
                        result.index('href="stories/older-story.html"'))
        self.assertEqual(result.count('href="stories/source-story.html"'), 1)
        self.assertIn('src="illustrated/illustrated-story/cover.png"', result)
        self.assertNotIn('src="covers/source-story.jpg"', result)
        self.assertIn('src="covers/older-story.jpg"', result)
        self.assertIn('<h2 class="story-title">Source Story</h2>', result)
        self.assertNotIn("A Different Edition Label", result)
        self.assertIn("Classic illustrated edition", result)
        for expected in (
            self.story.prompt, '<time datetime="2026-09-13">Sep 13, 2026</time>',
            '<span class="status status-canon">Canon</span>',
            f'<span class="word-count">{self.story.word_count}</span>',
            '<span class="rating rating-ya">YA</span>',
        ):
            self.assertIn(expected, result)
        self.assertEqual(catalog, before)

    def test_web_reader_uses_frozen_edition_without_pdf_or_original_link(self):
        newer_story = replace(self.story, body="# Source Story\n\nA newer catalog snapshot.\n",
                              prompt='Published *prompt*: "a <door> & a key".')
        result = build.render_story(newer_story, [self.edition])
        self.assertIn('class="edition-prose"', result)
        self.assertIn("A quiet beginning.", result)
        self.assertNotIn("A newer catalog snapshot.", result)
        self.assertIn('src="../illustrated/illustrated-story/door.png"', result)
        self.assertIn('href="../index.html"', result)
        self.assertIn('Writing Prompt</h2>', result)
        self.assertIn(f'<blockquote>{html.escape(newer_story.prompt)}</blockquote>', result)
        self.assertLess(result.index('class="edition-prompt"'), result.index('class="edition-prose"'))
        self.assertNotIn('<em>prompt</em>', result)
        self.assertNotIn("Original story", result)
        self.assertNotIn("Download PDF", result)
        self.assertNotIn('href="../stories/source-story.html"', result)

    def test_unillustrated_reader_and_cover_are_preserved(self):
        plain = build.render_story(self.story)
        unrelated = edition_fixture(story_fixture("another-story"))
        self.assertEqual(build.render_story(self.story, [unrelated]), plain)
        self.assertIn('class="story-prose"', plain)
        self.assertIn('src="../covers/source-story.jpg"', plain)
        self.assertNotIn('class="edition-prose"', plain)
        self.assertIn('src="covers/source-story.jpg"',
                      build.render_index(build.Catalog((self.story,))))

    def test_duplicate_and_orphan_source_selections_fail(self):
        duplicate = deepcopy(self.edition)
        duplicate["slug"] = "another-edition"
        for render in (
            lambda editions: build.render_index(build.Catalog((self.story,)), editions),
            lambda editions: build.render_story(self.story, editions),
        ):
            with self.subTest(render=render), self.assertRaisesRegex(ValueError, "Multiple illustrated"):
                render([self.edition, duplicate])
        with self.assertRaisesRegex(ValueError, "absent from the publication catalog"):
            build.render_index(build.Catalog(()), [self.edition])

    def test_build_uses_only_frozen_snapshots_at_canonical_story_route(self):
        with TemporaryDirectory(prefix="pages-publication-test-") as temporary:
            root = Path(temporary)
            pages = root / "pages"
            (pages / "covers").mkdir(parents=True)
            Image.new("RGB", (864, 1536), "navy").save(pages / self.story.cover)
            snapshot = pages / "catalog.json"
            build.save_catalog([self.story], snapshot)
            for asset in [self.edition["cover"], *self.edition["illustrations"]]:
                path = pages / asset["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (32, 48), "ivory").save(path)
                asset["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            illustrated = pages / "illustrated.json"
            illustrated.write_text(json.dumps({"schemaVersion": 1, "editions": [self.edition]}), encoding="utf-8")
            original_catalog = snapshot.read_bytes()
            original_illustrated = illustrated.read_bytes()
            output = root / "site"
            # There are no source-story or production-edition directories here.
            # Guard the source loader too, so a build cannot silently fall back to it.
            with patch.object(build, "load_story_source", side_effect=AssertionError("Production source read")):
                catalog = build.build(output, snapshot)
            self.assertEqual(catalog.stories, (self.story,))
            reader = output / "stories/source-story.html"
            self.assertTrue(reader.is_file())
            self.assertIn('class="edition-prose"', reader.read_text(encoding="utf-8"))
            self.assertEqual(len(list((output / "stories").glob("*.html"))), 1)
            self.assertFalse(list((output / "illustrated").glob("*.html")))
            self.assertFalse((output / "editions").exists())
            self.assertFalse(list(output.rglob("*.pdf")))
            self.assertEqual((output / "index.html").read_text(encoding="utf-8").count('<li class="story-card">'), 1)
            for asset in [self.edition["cover"], *self.edition["illustrations"]]:
                self.assertEqual((output / asset["path"]).read_bytes(), (pages / asset["path"]).read_bytes())
            self.assertEqual(snapshot.read_bytes(), original_catalog)
            self.assertEqual(illustrated.read_bytes(), original_illustrated)


if __name__ == "__main__":
    unittest.main()
