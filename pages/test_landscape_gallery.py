"""Frozen gallery publication, safe paths and original-image preservation."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
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

    def test_excluded_art_cannot_return_on_recapture_even_after_source_changes(self):
        selected = self.capture()
        original = self.source.read_bytes()
        catalog = (self.pages / "catalog.json").read_bytes()
        image = selected["stories"][0]["images"][0]
        curated = {"schemaVersion": 1, "stories": [], "excludedSources": [{
            "source": image["source"], "sourceSha256": image["sourceSha256"],
            "reason": "The story takes place entirely indoors; this exterior is invented.",
        }]}
        self.snapshot.write_text(json.dumps(curated), encoding="utf-8")
        with patch.object(Image.Image, "save", side_effect=AssertionError("Encoded excluded art")):
            self.assertEqual(self.capture(), curated)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual((self.pages / "catalog.json").read_bytes(), catalog)
        Image.new("RGB", (96, 64), "purple").save(self.source)
        self.assertEqual(self.capture(), curated)
        self.assertEqual(gallery.check_assets(curated, self.pages), 0)
        output = self.root / "curated-site"
        output.mkdir()
        self.assertEqual(gallery.build_gallery(output, self.snapshot, self.catalog), 0)
        self.assertFalse(list(output.rglob("*.webp")))

    def test_exclusions_reject_unsafe_duplicate_or_still_selected_sources(self):
        original = self.capture()
        image = original["stories"][0]["images"][0]
        entry = {"source": image["source"], "sourceSha256": image["sourceSha256"],
                 "reason": "Unsupported outdoor setting."}
        for mutation in ("unsafe", "duplicate", "selected", "missing-reason"):
            with self.subTest(mutation=mutation):
                data = deepcopy(original)
                data["excludedSources"] = [deepcopy(entry)]
                if mutation != "selected":
                    data["stories"] = []
                if mutation == "unsafe":
                    data["excludedSources"][0]["source"] = "stories/../../private.png"
                elif mutation == "duplicate":
                    data["excludedSources"].append(deepcopy(entry))
                elif mutation == "missing-reason":
                    data["excludedSources"][0]["reason"] = ""
                self.snapshot.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
                    gallery.load_snapshot(self.snapshot)

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
        self.assertIn('href="gallery.html" aria-current="page">Gallery', document)
        self.assertIn('id="gallery-viewer"', document)
        self.assertIn('loading="lazy"', document)
        self.assertIn('width="96" height="64"', document)
        self.assertNotIn('src="/', document)

    def replacement_fixture(self, collection="landscapes"):
        data = self.capture() if collection == "landscapes" else gallery.capture_interiors(self.root)
        original = data["stories"][0]["images"][0]
        replacement = self.pages / f"{collection[:-1]}-replacements" / self.story.slug / self.source.name
        replacement.parent.mkdir(parents=True)
        Image.new("RGB", (96, 64), "midnightblue").save(replacement)
        selected = gallery._encode((replacement, self.root, self.pages, self.story.slug, self.story.title, None, collection))
        setting = "valley" if collection == "landscapes" else "room"
        selected["title"] = f"The {setting} at the correct hour"
        selected["revision"] = {
            "originalSource": original["source"], "originalSha256": original["sourceSha256"],
            "correction": "The source scene occurs after dark.",
            "prompt": f"Preserve the {setting}; replace sunlight with night.",
            "generator": "image_gen",
        }
        data["stories"][0]["images"] = [selected]
        data["excludedSources"] = [{
            "source": original["source"], "sourceSha256": original["sourceSha256"],
            "reason": selected["revision"]["correction"],
        }]
        (self.pages / f"{collection}.json").write_text(json.dumps(data), encoding="utf-8")
        return replacement, data

    def test_replacement_recapture_preserves_original_and_selected_provenance(self):
        replacement, data = self.replacement_fixture()
        original_bytes = self.source.read_bytes()
        catalog_bytes = (self.pages / "catalog.json").read_bytes()
        with patch.object(Image.Image, "save", side_effect=AssertionError("Re-encoded reviewed replacement")):
            self.assertEqual(self.capture(), data)
        self.assertEqual(self.source.read_bytes(), original_bytes)
        self.assertEqual((self.pages / "catalog.json").read_bytes(), catalog_bytes)
        selected = data["stories"][0]["images"][0]
        self.assertEqual(selected["source"], replacement.relative_to(self.root).as_posix())
        (self.pages / selected["thumbnail"]["path"]).unlink()
        self.assertEqual(self.capture(), data)

    def test_changed_replacement_source_blocks_recapture_but_not_frozen_build(self):
        replacement, data = self.replacement_fixture()
        before = self.snapshot.read_bytes()
        Image.new("RGB", (96, 64), "pink").save(replacement)
        with self.assertRaisesRegex(ValueError, "changed since review"):
            self.capture()
        self.assertEqual(self.snapshot.read_bytes(), before)
        (self.root / "stories").rename(self.root / "offline-stories")
        replacement.unlink()
        output = self.root / "frozen-site"
        output.mkdir()
        self.assertEqual(gallery.build_gallery(output, self.snapshot, self.catalog), 1)
        self.assertFalse(list(output.rglob("*.png")))

    def test_replacement_requires_safe_source_and_matching_excluded_reference(self):
        self.add_interior()
        for collection in ("landscapes", "interiors"):
            _, original = self.replacement_fixture(collection)
            snapshot = self.pages / f"{collection}.json"
            for mutation in ("unsafe", "wrong-collection", "wrong-story", "missing-exclusion", "wrong-hash", "missing-prompt"):
                with self.subTest(collection=collection, mutation=mutation):
                    data = deepcopy(original)
                    image = data["stories"][0]["images"][0]
                    if mutation == "unsafe":
                        image["source"] = f"pages/{collection[:-1]}-replacements/../../private.png"
                    elif mutation == "wrong-collection":
                        other = "interior" if collection == "landscapes" else "landscape"
                        image["source"] = f"pages/{other}-replacements/{self.story.slug}/{self.source.name}"
                    elif mutation == "wrong-story":
                        image["revision"]["originalSource"] = f"stories/another/art/{collection}/{self.source.name}"
                    elif mutation == "missing-exclusion":
                        data["excludedSources"] = []
                    elif mutation == "wrong-hash":
                        image["revision"]["originalSha256"] = "0" * 64
                    else:
                        image["revision"]["prompt"] = ""
                    snapshot.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        gallery.load_snapshot(snapshot, collection)

    def test_missing_snapshot_has_a_valid_empty_gallery_and_reader_navigation(self):
        empty = gallery.load_snapshot(self.snapshot)
        self.assertEqual(empty["stories"], [])
        self.assertIn("coming soon", gallery.render_gallery(empty))
        self.assertIn('href="../gallery.html">Gallery', build.render_story(self.story))

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
        _, landscapes = self.replacement_fixture()
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
            self.assertEqual(self.capture(), landscapes)
        self.assertEqual(gallery.load_snapshot(self.pages / "interiors.json", "interiors"), data)

    def test_interior_replacement_recapture_preserves_original_catalog_and_landscapes(self):
        landscape_replacement, landscapes = self.replacement_fixture()
        source = self.add_interior()
        replacement, data = self.replacement_fixture("interiors")
        protected = [self.source, source, landscape_replacement, replacement,
                     self.snapshot, self.pages / "catalog.json"]
        protected.extend(self.pages / image[role]["path"]
                         for story in landscapes["stories"] for image in story["images"]
                         for role in ("full", "thumbnail"))
        original_bytes = {path: path.read_bytes() for path in protected}
        with patch.object(Image.Image, "save", side_effect=AssertionError("Re-encoded reviewed interior")):
            self.assertEqual(gallery.capture_interiors(self.root), data)
            self.assertEqual(gallery.capture_interiors(self.root, slugs=[self.story.slug]), data)
        selected = data["stories"][0]["images"][0]
        self.assertEqual(selected["source"], f"pages/interior-replacements/{self.story.slug}/{source.name}")
        self.assertEqual(selected["revision"]["originalSource"], source.relative_to(self.root).as_posix())
        (self.pages / selected["thumbnail"]["path"]).unlink()
        self.assertEqual(gallery.capture_interiors(self.root, slugs=[self.story.slug]), data)
        self.assertEqual({path: path.read_bytes() for path in protected}, original_bytes)

    def test_changed_interior_replacement_blocks_recapture_but_not_frozen_build(self):
        self.add_interior()
        replacement, data = self.replacement_fixture("interiors")
        snapshot = self.pages / "interiors.json"
        before = snapshot.read_bytes()
        Image.new("RGB", (96, 64), "pink").save(replacement)
        with self.assertRaisesRegex(ValueError, "changed since review"):
            gallery.capture_interiors(self.root, slugs=[self.story.slug])
        self.assertEqual(snapshot.read_bytes(), before)
        (self.root / "stories").rename(self.root / "offline-stories")
        replacement.unlink()
        output = self.root / "frozen-site"
        output.mkdir()
        with patch.object(gallery, "_capture_collection", side_effect=AssertionError("Capture during build")):
            self.assertEqual(gallery.build_gallery(output, self.snapshot, self.catalog), 1)
        for role in ("full", "thumbnail"):
            asset = data["stories"][0]["images"][0][role]["path"]
            self.assertEqual((output / asset).read_bytes(), (self.pages / asset).read_bytes())
        self.assertFalse(list(output.rglob("*.png")))

    def test_named_interior_capture_accepts_all_excluded_originals_but_requires_source_directory(self):
        source = self.add_interior()
        data = gallery.capture_interiors(self.root)
        image = data["stories"][0]["images"][0]
        curated = {"schemaVersion": 1, "stories": [], "excludedSources": [{
            "source": image["source"], "sourceSha256": image["sourceSha256"],
            "reason": "The room contains unsupported furnishings.",
        }]}
        snapshot = self.pages / "interiors.json"
        snapshot.write_text(json.dumps(curated), encoding="utf-8")
        with patch.object(Image.Image, "save", side_effect=AssertionError("Encoded excluded interior")):
            self.assertEqual(gallery.capture_interiors(self.root, slugs=[self.story.slug]), curated)
        saved = snapshot.read_bytes()
        source.parent.rename(source.parent.with_name("offline-interiors"))
        with self.assertRaisesRegex(ValueError, "No interiors source directory"):
            gallery.capture_interiors(self.root, slugs=[self.story.slug])
        self.assertEqual(snapshot.read_bytes(), saved)

    def test_combined_build_keeps_one_story_and_distinct_image_identities(self):
        replacement, landscapes = self.replacement_fixture()
        self.add_interior()
        interiors = gallery.capture_interiors(self.root)
        (self.root / "stories").rename(self.root / "offline-stories")
        replacement.unlink()
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
        original = gallery.capture_interiors(self.root)
        snapshot = self.pages / "interiors.json"
        for mutation in ("asset", "replacement", "exclusion"):
            with self.subTest(mutation=mutation):
                data = deepcopy(original)
                image = data["stories"][0]["images"][0]
                if mutation == "asset":
                    image["full"]["path"] = image["full"]["path"].replace("interiors/", "landscapes/", 1)
                elif mutation == "replacement":
                    image["source"] = f"pages/landscape-replacements/{self.story.slug}/{self.source.name}"
                else:
                    data["excludedSources"] = [{
                        "source": self.source.relative_to(self.root).as_posix(),
                        "sourceSha256": image["sourceSha256"], "reason": "A landscape-only exclusion.",
                    }]
                snapshot.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError):
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

    def test_named_interior_capture_preserves_other_stored_sets(self):
        self.add_interior()
        first = gallery.capture_interiors(self.root)
        other = story_fixture(slug="another-story", title="Another Story")
        build.save_catalog([self.story, other], self.pages / "catalog.json")
        Image.new("RGB", (864, 1536), "navy").save(self.pages / other.cover)
        other_art = self.root / "stories" / other.slug / "art" / "interiors"
        other_art.mkdir(parents=True)
        Image.new("RGB", (96, 64), "gold").save(other_art / "01-the-room.png")
        # The first source may be offline; a named capture must retain its snapshot.
        self.art.parent.rename(self.art.parent.with_name("offline-art"))
        second = gallery.capture_interiors(self.root, slugs=[other.slug])
        self.assertEqual(len(second["stories"]), 2)
        retained = next(story for story in second["stories"] if story["slug"] == self.story.slug)
        self.assertEqual(retained, first["stories"][0])
        self.assertEqual(gallery.check_assets(second, self.pages), 2)
        saved = (self.pages / "interiors.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "No interiors source directory"):
            gallery.capture_interiors(self.root, slugs=[self.story.slug])
        self.assertEqual((self.pages / "interiors.json").read_bytes(), saved)

    def test_named_landscape_capture_preserves_unrelated_art_and_rejects_missing_sources(self):
        first = self.capture()
        retained_assets = {
            image[role]["path"]: (self.pages / image[role]["path"]).read_bytes()
            for image in first["stories"][0]["images"] for role in ("full", "thumbnail")
        }
        other = story_fixture(slug="another-story", title="Another Story")
        build.save_catalog([self.story, other], self.pages / "catalog.json")
        Image.new("RGB", (864, 1536), "navy").save(self.pages / other.cover)
        other_art = self.root / "stories" / other.slug / "art" / "landscapes"
        other_art.mkdir(parents=True)
        Image.new("RGB", (96, 64), "gold").save(other_art / "01-outside-the-gate.png")
        # An unrelated original may be offline, and unpublished drafts must be ignored.
        self.art.rename(self.art.with_name("offline-landscapes"))
        unpublished = self.root / "stories" / "draft" / "art" / "landscapes"
        unpublished.mkdir(parents=True)
        Image.new("RGB", (96, 64), "red").save(unpublished / "01-draft.png")
        protected = {self.pages / "catalog.json": (self.pages / "catalog.json").read_bytes()}
        for collection in ("characters", "interiors"):
            snapshot = self.pages / f"{collection}.json"
            snapshot.write_text('{"schemaVersion":1,"stories":[]}', encoding="utf-8")
            protected[snapshot] = snapshot.read_bytes()
        second = gallery.capture_landscapes(self.root, slugs=[other.slug])
        self.assertEqual({story["slug"] for story in second["stories"]}, {self.story.slug, other.slug})
        retained = next(story for story in second["stories"] if story["slug"] == self.story.slug)
        self.assertEqual(retained, first["stories"][0])
        self.assertEqual(gallery.check_assets(second, self.pages), 2)
        self.assertEqual({path: (self.pages / path).read_bytes() for path in retained_assets}, retained_assets)
        self.assertEqual({path: path.read_bytes() for path in protected}, protected)
        saved = self.snapshot.read_bytes()
        for slug, error in ((self.story.slug, "No landscapes source directory"),
                            ("draft", "absent from the publication catalog")):
            with self.subTest(slug=slug), self.assertRaisesRegex(ValueError, error):
                gallery.capture_landscapes(self.root, slugs=[slug])
            self.assertEqual(self.snapshot.read_bytes(), saved)

    def test_landscape_cli_forwards_named_slugs(self):
        # Run the real parser/dispatch with capture mocked; never touch repository snapshots.
        script = """
import runpy
import sys
from unittest.mock import patch
sys.argv = ['pages/build.py', 'capture-landscapes', 'first-story', 'second-story']
with patch('pages.landscape_gallery.capture_landscapes', return_value={'stories': []}) as capture:
    runpy.run_module('pages.build', run_name='__main__')
    assert capture.call_count == 1
    assert capture.call_args.kwargs == {'slugs': ['first-story', 'second-story']}
"""
        result = subprocess.run([sys.executable, "-c", script],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
