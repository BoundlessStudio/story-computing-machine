"""Character publication requires current visual review and stays frozen in builds."""
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CharacterGalleryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix="character-gallery-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.pages = self.root / "pages"
        self.pages.mkdir()
        self.story = story_fixture(title='A Story & "Its People"')
        build.save_catalog([self.story], self.pages / "catalog.json")
        (self.pages / "covers").mkdir()
        Image.new("RGB", (864, 1536), "navy").save(self.pages / self.story.cover)
        self.source = self.root / "stories" / self.story.slug / "story.md"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("The finished story, kept unchanged.", encoding="utf-8")
        self.reference = self.root / "external-style.png"
        Image.new("RGB", (96, 64), "#cc7722").save(self.reference)
        self.output = self.source.parent / "art" / "characters" / "ira-vale.png"
        self.output.parent.mkdir(parents=True)
        Image.new("RGB", (96, 64), "navy").save(self.output)
        self.character = {
            "id": "ira-vale", "name": 'Ira "Ivy" Vale', "status": "completed",
            "appearance": "Dark hair and work clothes.",
            "output": self.output.relative_to(self.root).as_posix(),
            "outputSha256": digest(self.output),
            "generation": {"prompt": "One Sculpted Impasto character sheet of Ira Vale.",
                           "attempts": [], "references": [{"path": str(self.reference),
                               "sha256": digest(self.reference), "role": "Primary paint style",
                               "inspected": True}]},
        }
        self.specification = {
            "schemaVersion": 1, "slug": self.story.slug, "title": self.story.title,
            "source": self.source.relative_to(self.root).as_posix(), "sourceSha256": digest(self.source),
            "readComplete": True, "assessment": "complete", "characters": [self.character],
        }
        self.specification_path = self.pages / "character-specs" / f"{self.story.slug}.json"
        self.specification_path.parent.mkdir()
        self.snapshot = self.pages / "characters.json"
        self.review()

    def review(self):
        self.character["validation"] = {
            "status": "PASS", "evidence": ["Inspected the complete saved sheet: identity, paint and labels pass."],
            "sourceSha256": self.specification["sourceSha256"],
            "specificationSha256": gallery.character_specification_sha256(self.specification, self.character),
            "outputSha256": self.character["outputSha256"],
            "references": deepcopy(self.character["generation"]["references"]),
        }
        self.save()

    def save(self):
        self.specification_path.write_text(json.dumps(self.specification), encoding="utf-8")

    def capture(self, slugs=None):
        return gallery.capture_characters(self.root, slugs=slugs)

    def test_capture_names_reviewed_characters_and_preserves_inputs(self):
        untouched = [self.source, self.reference, self.output, self.specification_path, self.pages / "catalog.json"]
        for collection in ("landscapes", "interiors"):
            path = self.pages / f"{collection}.json"
            path.write_text('{"schemaVersion":1,"stories":[]}', encoding="utf-8")
            untouched.append(path)
        before = {path: path.read_bytes() for path in untouched}
        data = self.capture([self.story.slug])
        self.assertEqual(before, {path: path.read_bytes() for path in untouched})
        image = data["stories"][0]["images"][0]
        self.assertEqual(image["title"], self.character["name"])
        self.assertIn(self.character["name"], image["alt"])
        self.assertIn(self.story.title, image["alt"])
        self.assertIn("Sculpted Impasto", image["alt"])
        self.assertEqual(image["sourceSha256"], digest(self.output))
        self.assertTrue(image["full"]["path"].startswith(f"characters/{self.story.slug}/ira-vale-"))
        with patch.object(Image.Image, "save", side_effect=AssertionError("Unchanged image encoded")):
            self.assertEqual(self.capture(), data)

    def test_pending_and_unlisted_images_are_not_selected(self):
        self.character["status"] = "pending"
        self.save()
        Image.new("RGB", (96, 64), "red").save(self.output.with_name("unlisted.png"))
        self.assertEqual(self.capture(), {"schemaVersion": 1, "stories": []})
        self.assertFalse((self.pages / "characters").exists())

    def test_source_specification_references_and_output_must_match_review(self):
        mutations = {
            "source bytes": lambda: self.source.write_text("Changed source", encoding="utf-8"),
            "specification": lambda: self.character.update(appearance="Changed face"),
            "prompt": lambda: self.character["generation"].update(prompt="Changed prompt"),
            "reference bytes": lambda: self.reference.write_bytes(b"changed reference"),
            "reference pin": lambda: self.character["validation"]["references"][0].update(role="Changed role"),
            "output bytes": lambda: self.output.write_bytes(b"changed output"),
            "review status": lambda: self.character["validation"].update(status="REVISE"),
            "source pin": lambda: self.character["validation"].update(sourceSha256="a" * 64),
        }
        original = deepcopy(self.specification)
        source_bytes, reference_bytes, output_bytes = self.source.read_bytes(), self.reference.read_bytes(), self.output.read_bytes()
        selected = self.capture()
        snapshot_bytes = self.snapshot.read_bytes()
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                self.specification = deepcopy(original)
                self.character = self.specification["characters"][0]
                self.source.write_bytes(source_bytes)
                self.reference.write_bytes(reference_bytes)
                self.output.write_bytes(output_bytes)
                mutate()
                self.save()
                with self.assertRaises(ValueError):
                    self.capture([self.story.slug])
                self.assertEqual(self.snapshot.read_bytes(), snapshot_bytes)
                self.assertEqual(gallery.check_assets(selected, self.pages), 1)

    def test_uninspected_reference_is_rejected_even_when_repinned(self):
        self.character["generation"]["references"][0]["inspected"] = False
        self.review()
        with self.assertRaisesRegex(ValueError, "uninspected character reference"):
            self.capture()

    def test_failed_encoding_leaves_previous_snapshot_and_assets_usable(self):
        selected = self.capture()
        snapshot_bytes = self.snapshot.read_bytes()
        Image.new("RGB", (64, 96), "red").save(self.output)
        self.character["outputSha256"] = digest(self.output)
        self.review()
        with self.assertRaisesRegex(ValueError, "horizontal landscape"):
            self.capture()
        self.assertEqual(self.snapshot.read_bytes(), snapshot_bytes)
        self.assertEqual(gallery.check_assets(selected, self.pages), 1)

    def test_character_sheet_requires_three_by_two_canvas(self):
        Image.new("RGB", (128, 64), "navy").save(self.output)
        self.character["outputSha256"] = digest(self.output)
        self.review()
        with self.assertRaisesRegex(ValueError, "3:2 character sheet"):
            self.capture()

    def test_named_capture_preserves_other_stories_without_reading_their_specs(self):
        first = self.capture()
        other = story_fixture("another-story")
        build.save_catalog([self.story, other], self.pages / "catalog.json")
        Image.new("RGB", (864, 1536), "navy").save(self.pages / other.cover)
        self.specification_path.write_text("offline invalid data", encoding="utf-8")
        (self.specification_path.parent / f"{other.slug}.json").write_text(json.dumps({
            "slug": other.slug, "characters": [{"status": "pending"}]}), encoding="utf-8")
        self.assertEqual(self.capture([other.slug]), first)
        with self.assertRaisesRegex(ValueError, "Cannot read character specification"):
            self.capture([self.story.slug])

    def test_build_uses_only_frozen_character_snapshot_and_has_filter_and_reader(self):
        selected = self.capture()
        (self.root / "stories").rename(self.root / "offline-stories")
        self.reference.unlink()
        self.specification_path.unlink()
        destination = self.root / "site"
        destination.mkdir()
        catalog = build.load_catalog(self.pages / "catalog.json")
        with patch.object(gallery, "capture_characters", side_effect=AssertionError("Capture during build")), \
                patch.object(gallery, "_reviewed_character_source", side_effect=AssertionError("Production read")):
            self.assertEqual(gallery.build_gallery(destination, self.pages / "landscapes.json", catalog), 1)
        document = (destination / "gallery.html").read_text(encoding="utf-8")
        image = selected["stories"][0]["images"][0]
        self.assertIn('option value="characters">Character sheets', document)
        self.assertIn('data-collection="characters"', document)
        self.assertIn(f'data-image-id="{self.story.slug}/characters/ira-vale"', document)
        self.assertIn(f'data-reader="stories/{self.story.slug}.html"', document)
        self.assertIn('Ira &quot;Ivy&quot; Vale', document)
        self.assertIn('1 character sheets', document)
        self.assertIn(f'href="{image["full"]["path"]}"', document)
        self.assertEqual((destination / image["full"]["path"]).read_bytes(),
                         (self.pages / image["full"]["path"]).read_bytes())

    def test_status_and_attempt_history_do_not_reopen_creative_specification(self):
        before = gallery.character_specification_sha256(self.specification, self.character)
        self.character["status"] = "reused"
        self.character["generation"]["attempts"].append({"status": "completed"})
        self.assertEqual(gallery.character_specification_sha256(self.specification, self.character), before)
        self.save()
        self.assertEqual(len(self.capture()["stories"]), 1)


if __name__ == "__main__":
    unittest.main()
