"""Frozen gallery publication, safe paths and original-image preservation."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from pages import build, landscape_gallery as gallery
from pages.test_build import story_fixture


class LandscapeGalleryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="landscape-gallery-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.pages = self.root / "pages"
        self.pages.mkdir()
        self.story = story_fixture(title='The Valley & "Morning"')
        self.catalog = build.save_catalog([self.story], self.pages / "catalog.json")
        (self.pages / "covers").mkdir()
        Image.new("RGB", (864, 1536), "navy").save(self.pages / self.story.cover)
        self.art = self.root / "stories" / self.story.slug / "art" / "landscapes"
        self.art.mkdir(parents=True)
        self.source = self.art / "01-the-bright-valley.png"
        Image.new("RGB", (96, 64), "seagreen").save(self.source)
        self.snapshot = self.pages / "landscapes.json"

    def capture(self):
        return gallery.capture_landscapes(self.root, self.snapshot)

    def test_capture_preserves_source_and_catalog_and_records_web_copies(self):
        original, catalog = self.source.read_bytes(), (self.pages / "catalog.json").read_bytes()
        data = self.capture()
        image = data["stories"][0]["images"][0]
        self.assertEqual(image["sourceSha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual((self.pages / "catalog.json").read_bytes(), catalog)
        self.assertEqual(image["title"], "The bright valley")
        self.assertEqual(gallery.check_assets(data, self.pages), 1)
        with Image.open(self.pages / image["full"]["path"]) as rendition:
            self.assertEqual(rendition.size, (96, 64))
            self.assertEqual(rendition.format, "WEBP")

    def test_build_uses_snapshot_when_production_is_absent(self):
        data = self.capture()
        (self.root / "stories").rename(self.root / "offline-stories")
        output = self.root / "site"
        output.mkdir()
        with patch.object(gallery, "capture_landscapes", side_effect=AssertionError("Capture during build")), \
                patch.object(build, "load_story_source", side_effect=AssertionError("Source read during build")):
            self.assertEqual(gallery.build_gallery(output, self.snapshot, self.catalog), 1)
        image = data["stories"][0]["images"][0]
        self.assertEqual((output / image["full"]["path"]).read_bytes(), (self.pages / image["full"]["path"]).read_bytes())
        self.assertTrue((output / "gallery.html").is_file())
        self.assertFalse(list(output.rglob("*.png")))

    def test_changing_source_does_not_refresh_stored_gallery(self):
        data = self.capture()
        old_hash = data["stories"][0]["images"][0]["sourceSha256"]
        Image.new("RGB", (96, 64), "indigo").save(self.source)
        self.assertNotEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), old_hash)
        self.assertEqual(gallery.load_snapshot(self.snapshot), data)
        self.assertEqual(gallery.check_assets(data, self.pages), 1)

    def test_recapture_reuses_unchanged_web_copies(self):
        first = self.capture()
        with patch.object(Image.Image, "save", side_effect=AssertionError("Re-encoded unchanged image")):
            self.assertEqual(self.capture(), first)

    def test_failed_recapture_leaves_selected_assets_and_snapshot_usable(self):
        selected = self.capture()
        snapshot_bytes = self.snapshot.read_bytes()
        Image.new("RGB", (96, 64), "red").save(self.source)
        Image.new("RGB", (64, 96), "gold").save(self.art / "02-invalid-portrait.png")
        with self.assertRaisesRegex(ValueError, "horizontal landscape"):
            self.capture()
        self.assertEqual(self.snapshot.read_bytes(), snapshot_bytes)
        self.assertEqual(gallery.check_assets(selected, self.pages), 1)

    def test_renderer_escapes_text_and_has_direct_image_fallback(self):
        data = self.capture()
        image = data["stories"][0]["images"][0]
        image["title"] = '<script>alert("x")</script>'
        document = gallery.render_gallery(data)
        self.assertNotIn('<script>alert("x")</script>', document)
        self.assertIn('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;', document)
        self.assertIn('The Valley &amp; &quot;Morning&quot;', document)
        self.assertIn(f'href="{image["full"]["path"]}"', document)
        self.assertIn('href="gallery.html" aria-current="page">Image Gallery', document)
        self.assertIn('id="gallery-viewer"', document)
        self.assertIn('loading="lazy"', document)
        self.assertIn('width="96" height="64"', document)
        self.assertNotIn('src="/', document)

    def test_missing_snapshot_has_a_valid_empty_gallery_and_reader_navigation(self):
        empty = gallery.load_snapshot(self.snapshot)
        self.assertEqual(empty["stories"], [])
        self.assertIn("coming soon", gallery.render_gallery(empty))
        self.assertIn('href="../gallery.html">Image Gallery', build.render_story(self.story))

    def test_duplicate_identity_and_path_traversal_are_rejected(self):
        original = self.capture()
        for mutation in ("duplicate", "traversal", "wrong-reader"):
            with self.subTest(mutation=mutation):
                data = deepcopy(original)
                story = data["stories"][0]
                if mutation == "duplicate":
                    story["images"].append(deepcopy(story["images"][0]))
                elif mutation == "traversal":
                    story["images"][0]["full"]["path"] = "../private.webp"
                else:
                    story["reader"] = "https://example.test/"
                self.snapshot.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    gallery.load_snapshot(self.snapshot)

    def test_tampered_or_missing_web_image_fails_publication(self):
        data = self.capture()
        asset = self.pages / data["stories"][0]["images"][0]["full"]["path"]
        asset.write_bytes(b"changed bytes")
        with self.assertRaisesRegex(ValueError, "Missing or changed"):
            gallery.check_assets(data, self.pages)
        asset.unlink()
        with self.assertRaisesRegex(ValueError, "Missing or changed"):
            gallery.check_assets(data, self.pages)

    def test_unpublished_story_cannot_create_a_broken_reader_link(self):
        self.capture()
        original = self.snapshot.read_bytes()
        unknown = self.root / "stories" / "not-published" / "art" / "landscapes"
        unknown.mkdir(parents=True)
        Image.new("RGB", (96, 64), "gold").save(unknown / "01-valley.png")
        with self.assertRaisesRegex(ValueError, "absent from the publication catalog"):
            self.capture()
        self.assertEqual(self.snapshot.read_bytes(), original)

    def add_interior(self):
        interior = self.art.with_name("interiors") / self.source.name
        interior.parent.mkdir(parents=True)
        Image.new("RGB", (96, 64), "sienna").save(interior)
        return interior

    def test_interior_capture_is_independent_of_landscapes_and_prose(self):
        self.capture()
        landscape_bytes = self.snapshot.read_bytes()
        catalog_bytes = (self.pages / "catalog.json").read_bytes()
        source = self.add_interior()
        original = source.read_bytes()
        data = gallery.capture_interiors(self.root)
        image = data["stories"][0]["images"][0]
        self.assertEqual(self.snapshot.read_bytes(), landscape_bytes)
        self.assertEqual((self.pages / "catalog.json").read_bytes(), catalog_bytes)
        self.assertEqual(source.read_bytes(), original)
        self.assertIn("/art/interiors/", image["source"])
        self.assertTrue(image["full"]["path"].startswith("interiors/"))
        self.assertIn("oil interior study", image["alt"])
        self.assertEqual(gallery.load_snapshot(self.pages / "interiors.json", "interiors"), data)
        with patch.object(Image.Image, "save", side_effect=AssertionError("Re-encoded unchanged interior")):
            self.assertEqual(gallery.capture_interiors(self.root), data)

    def test_combined_build_keeps_one_story_and_distinct_image_identities(self):
        landscapes = self.capture()
        self.add_interior()
        interiors = gallery.capture_interiors(self.root)
        (self.root / "stories").rename(self.root / "offline-stories")
        output = self.root / "site"
        output.mkdir()
        with patch.object(gallery, "_capture_collection", side_effect=AssertionError("Capture during build")):
            self.assertEqual(gallery.build_gallery(output, self.snapshot, self.catalog), 2)
        document = (output / "gallery.html").read_text(encoding="utf-8")
        self.assertEqual(document.count('class="gallery-story"'), 1)
        self.assertEqual(document.count('data-gallery-image '), 2)
        self.assertIn(f'data-image-id="{self.story.slug}/{self.source.stem}"', document)
        self.assertIn(f'data-image-id="{self.story.slug}/interiors/{self.source.stem}"', document)
        self.assertIn('id="gallery-type"', document)
        self.assertIn('data-collection="interiors"', document)
        self.assertIn("1 landscapes · 1 interiors · 1 stories", document)
        self.assertNotIn("collection", landscapes["stories"][0]["images"][0])
        for data in (landscapes, interiors):
            for role in ("full", "thumbnail"):
                asset = data["stories"][0]["images"][0][role]["path"]
                self.assertEqual((output / asset).read_bytes(), (self.pages / asset).read_bytes())

    def test_interior_snapshot_cannot_reference_other_collection_assets(self):
        self.add_interior()
        data = gallery.capture_interiors(self.root)
        image = data["stories"][0]["images"][0]
        image["full"]["path"] = image["full"]["path"].replace("interiors/", "landscapes/", 1)
        snapshot = self.pages / "interiors.json"
        snapshot.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "path"):
            gallery.load_snapshot(snapshot, "interiors")

    def test_interior_only_story_is_present_and_tampering_blocks_build(self):
        self.add_interior()
        data = gallery.capture_interiors(self.root)
        output = self.root / "site"
        output.mkdir()
        self.assertEqual(gallery.build_gallery(output, self.snapshot, self.catalog), 1)
        image = data["stories"][0]["images"][0]
        (self.pages / image["full"]["path"]).write_bytes(b"changed interior")
        with self.assertRaisesRegex(ValueError, "Missing or changed"):
            gallery.build_gallery(output, self.snapshot, self.catalog)


if __name__ == "__main__":
    unittest.main()
