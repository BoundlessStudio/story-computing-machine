"""Focused checks for public selection, immutable URLs, and publication ordering."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from .assets import INDEX_KEY, object_key
from .manifest import build, selected_paths, selection_notes
from .publish import load_manifest, publish


ORIGIN = "https://art.example.com"
COMMIT = "a" * 40


class MediaFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.files = {
            "stories/s/title-image.jpg",
            "stories/s/art/characters/hero.png",
            "stories/s/art/landscapes/old.png",
            "stories/s/art/landscapes/selected/old.png",
            "stories/s/art/interiors/rejected.png",
            "stories/s/art/references/supplied.png",
            "illustrated/i/cover.jpg",
            "illustrated/i/edition.pdf",
            "illustrated/i/illustrations/scene.png",
            "illustrated/i/references/supplied.png",
            "graphic-novels/g/cover.png",
            "graphic-novels/g/edition.pdf",
            "graphic-novels/g/pages/01.png",
            "graphic-novels/g/references/supplied.png",
        }
        for relative in self.files:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())
        notes = {
            "excluded": [{"file": "stories/s/art/interiors/rejected.png", "reason": "Rejected"}],
            "selectedCorrections": [{
                "original": "stories/s/art/landscapes/old.png",
                "selected": "stories/s/art/landscapes/selected/old.png",
            }],
        }
        path = self.root / "art" / "selection-notes.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(notes), encoding="utf-8")
        self.files.add("art/selection-notes.json")

    def manifest(self):
        return build(self.root, ORIGIN, self.files, COMMIT)


class SelectionTests(MediaFixture):
    def test_only_approved_final_media_is_public(self):
        excluded, corrections = selection_notes(self.root, self.files)
        chosen = selected_paths(self.files, excluded, corrections)
        self.assertEqual(len(chosen), 9)
        self.assertIn("stories/s/art/landscapes/selected/old.png", chosen)
        self.assertFalse(any("references" in path for path in chosen))
        self.assertNotIn("stories/s/art/landscapes/old.png", chosen)
        self.assertNotIn("stories/s/art/interiors/rejected.png", chosen)
        manifest = self.manifest()
        self.assertEqual(manifest["indexUrl"], ORIGIN + "/" + INDEX_KEY)
        for entry in manifest["assets"]:
            self.assertEqual(entry["key"], object_key(entry["path"], entry["sha256"]))
            self.assertEqual(entry["url"], ORIGIN + "/" + entry["key"])

    def test_missing_selected_correction_fails(self):
        self.files.remove("stories/s/art/landscapes/selected/old.png")
        with self.assertRaisesRegex(ValueError, "Invalid selected correction"):
            self.manifest()

    def test_changed_bytes_rejected_before_upload(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        with patch("media.publish.tracked_paths", return_value=self.files):
            load_manifest(path, self.root)
        (self.root / "stories/s/title-image.jpg").write_bytes(b"changed")
        with patch("media.publish.tracked_paths", return_value=self.files):
            with self.assertRaisesRegex(ValueError, "Source media changed"):
                load_manifest(path, self.root)


class PublicationTests(MediaFixture):
    def test_index_waits_for_every_public_verification(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        client = Mock()
        client.meta.endpoint_url = "https://account.r2.cloudflarestorage.com"
        events = []

        def upload(*args):
            events.append("upload")
            return True

        def verify(*args):
            events.append("verify")

        def index(*args):
            events.append("index")

        with patch("media.publish.tracked_paths", return_value=self.files), \
             patch("media.publish.upload_object", side_effect=upload), \
             patch("media.publish.verify_public", side_effect=verify), \
             patch("media.publish.publish_index", side_effect=index):
            result = publish(path, self.root, client, "bucket", workers=1, update_index=True)
        self.assertEqual(result["assets"], 9)
        self.assertEqual(result["uploaded"], 9)
        self.assertEqual(events[-1], "index")
        self.assertEqual(events.count("verify"), 9)

    def test_failed_public_url_leaves_index_untouched(self):
        path = self.root / "manifest.json"
        path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        client = Mock()
        client.meta.endpoint_url = "https://account.r2.cloudflarestorage.com"
        with patch("media.publish.tracked_paths", return_value=self.files), \
             patch("media.publish.upload_object", return_value=True), \
             patch("media.publish.verify_public", side_effect=ValueError("CDN failed")), \
             patch("media.publish.publish_index") as index:
            with self.assertRaisesRegex(ValueError, "CDN failed"):
                publish(path, self.root, client, "bucket", workers=1, update_index=True)
        index.assert_not_called()


if __name__ == "__main__":
    unittest.main()
