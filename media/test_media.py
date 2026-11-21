"""Focused checks for public selection, immutable URLs, and publication ordering."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from .assets import INDEX_KEY, object_key
from .manifest import build, selected_paths
from .publish import (delete_retired_assets, load_manifest, load_retired_assets,
                      object_headers, publish, verify_public_removed)


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
            "stories/s/art/landscapes/valley.png",
            "stories/s/art/interiors/room.png",
            "stories/s/art/references/supplied.png",
        }
        for relative in self.files:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(relative.encode())

    def manifest(self):
        return build(self.root, ORIGIN, self.files, COMMIT)


class SelectionTests(MediaFixture):
    def test_only_story_covers_and_direct_art_are_public(self):
        chosen = selected_paths(self.files)
        self.assertEqual(len(chosen), 4)
        self.assertFalse(any("references" in path for path in chosen))
        self.assertIn("stories/s/art/landscapes/valley.png", chosen)
        self.assertIn("stories/s/art/interiors/room.png", chosen)
        manifest = self.manifest()
        self.assertEqual(manifest["indexUrl"], ORIGIN + "/" + INDEX_KEY)
        for entry in manifest["assets"]:
            self.assertEqual(entry["key"], object_key(entry["path"], entry["sha256"]))
            self.assertEqual(entry["url"], ORIGIN + "/" + entry["key"])

    def test_missing_tracked_art_fails(self):
        (self.root / "stories/s/art/landscapes/valley.png").unlink()
        with self.assertRaisesRegex(ValueError, "Missing or escaping source file"):
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

        def remove(*args):
            events.append("remove")

        with patch("media.publish.tracked_paths", return_value=self.files), \
             patch("media.publish.upload_object", side_effect=upload), \
             patch("media.publish.verify_public", side_effect=verify), \
             patch("media.publish.delete_retired_assets", side_effect=remove), \
             patch("media.publish.publish_index", side_effect=index):
            result = publish(path, self.root, client, "bucket", workers=1, update_index=True)
        self.assertEqual(result["assets"], 4)
        self.assertEqual(result["uploaded"], 4)
        self.assertEqual(events[-1], "index")
        self.assertEqual(events[-2], "remove")
        self.assertEqual(events.count("verify"), 4)

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


class RetirementTests(MediaFixture):
    def record(self):
        return {"path": "stories/removed/art/interiors/retired.webp", "sha256": "b" * 64,
                "size": 123, "contentType": "image/webp"}

    def entries(self, record=None):
        path = self.root / "media" / "retired-assets.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps([record or self.record()]), encoding="utf-8")
        return load_retired_assets(self.root, self.manifest())

    def test_live_paths_and_shared_objects_cannot_be_retired(self):
        live = self.manifest()["assets"][0]
        record = {key: live[key] for key in ("path", "sha256", "size", "contentType")}
        with self.assertRaisesRegex(ValueError, "still selected"):
            self.entries(record)
        record["path"] = "stories/removed/art/characters/" + Path(live["path"]).name
        with self.assertRaisesRegex(ValueError, "still selected"):
            self.entries(record)

    def test_delete_checks_exact_identity_and_verifies_absence(self):
        entry = self.entries()[0]
        client = Mock()
        head = object_headers(entry) | {"ContentLength": entry["size"]}
        with patch("media.publish.head_object", side_effect=[head, None]), \
             patch("media.publish.verify_public_removed") as verify:
            delete_retired_assets(client, "bucket", [entry])
        client.delete_object.assert_called_once_with(Bucket="bucket", Key=entry["key"])
        verify.assert_called_once_with(entry)

    def test_mismatched_object_is_never_deleted(self):
        entry = self.entries()[0]
        client = Mock()
        with patch("media.publish.head_object", return_value={}):
            with self.assertRaisesRegex(ValueError, "differs"):
                delete_retired_assets(client, "bucket", [entry])
        client.delete_object.assert_not_called()

    def test_retirement_is_idempotent(self):
        entry = self.entries()[0]
        client = Mock()
        with patch("media.publish.head_object", return_value=None), \
             patch("media.publish.verify_public_removed") as verify:
            delete_retired_assets(client, "bucket", [entry])
        client.delete_object.assert_not_called()
        verify.assert_called_once_with(entry)

    def test_only_public_404_confirms_removal(self):
        entry = self.entries()[0]
        with patch("media.publish.urlopen", side_effect=HTTPError(entry["url"], 404, "missing", {}, None)):
            verify_public_removed(entry, attempts=1)
        with patch("media.publish.urlopen", side_effect=HTTPError(entry["url"], 403, "denied", {}, None)):
            with self.assertRaisesRegex(ValueError, "still available"):
                verify_public_removed(entry, attempts=1)


if __name__ == "__main__":
    unittest.main()
