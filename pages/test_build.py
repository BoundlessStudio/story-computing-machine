from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import build


class SiteBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        (self.root / "stories").mkdir()

    def write_json(self, path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def add_story(
        self,
        slug: str,
        *,
        title: str = "The Fixture Story",
        status: str = "candidate",
        publish: bool | None = None,
        frontmatter_title: str | None = None,
    ) -> Path:
        story_directory = self.root / "stories" / slug
        story_directory.mkdir()
        states = {
            "in-progress": {
                "stage": "prompt",
                "canon": False,
                "userDisposition": "pending",
                "publish": False,
                "promotionDate": None,
            },
            "candidate": {
                "stage": "candidate",
                "canon": False,
                "userDisposition": "pending",
                "publish": True,
                "promotionDate": None,
            },
            "final": {
                "stage": "final",
                "canon": True,
                "userDisposition": "accepted",
                "publish": True,
                "promotionDate": "2026-08-01",
            },
            "abandoned": {
                "stage": "abandoned",
                "canon": False,
                "userDisposition": "rejected",
                "publish": False,
                "promotionDate": None,
            },
        }
        state = dict(states[status])
        if publish is not None:
            state["publish"] = publish
        metadata = {
            "schemaVersion": 1,
            "slug": slug,
            "title": title,
            "created": "2026-08-01",
            "stage": state["stage"],
            "status": status,
            "canon": state["canon"],
            "userDisposition": state["userDisposition"],
            "publish": state["publish"],
            "promotionDate": state["promotionDate"],
        }
        self.write_json(story_directory / "story.json", metadata)

        body = (
            "# The Fixture Story\n\n"
            + " ".join(f"word{index}" for index in range(130))
        )
        if status == "in-progress":
            body = "# The Fixture Story\n\nNo reader-facing final story yet."
        story_content = (
            "---\n"
            f'title: "{frontmatter_title or title}"\n'
            f'slug: "{slug}"\n'
            "created: 2026-08-01\n"
            "---\n\n"
            f"{body}\n"
        )
        (story_directory / "05-story.md").write_text(story_content, encoding="utf-8")
        (story_directory / "06-canon-delta.md").write_text(
            "# Proposed canon delta\n\nNone.\n", encoding="utf-8"
        )
        (story_directory / "00-prompt.md").write_text(
            "# Prompt\n\n## Verbatim writing prompt\n\n"
            "> [WP] Tell a story whose prompt remains visible.\n",
            encoding="utf-8",
        )
        if state["publish"] and status in build.PUBLISHABLE_STATUSES:
            self.write_release(story_directory, slug)
        return story_directory

    def write_release(self, story_directory: Path, slug: str) -> None:
        story_digest = hashlib.sha256(
            (story_directory / "05-story.md").read_bytes()
        ).hexdigest()
        delta_digest = hashlib.sha256(
            (story_directory / "06-canon-delta.md").read_bytes()
        ).hexdigest()
        release = {
            "schemaVersion": 1,
            "certified": True,
            "storySlug": slug,
            "certifiedAt": "2026-08-01T12:00:00Z",
            "artifacts": {
                "story": {"path": "05-story.md", "sha256": story_digest},
                "canonDelta": {
                    "path": "06-canon-delta.md",
                    "sha256": delta_digest,
                },
            },
            "review": {
                "artifact": "05-story.md",
                "pass": 2,
                "verdict": "PASS",
                "reviewer": "continuity_critic",
                "unresolvedCritical": 0,
                "unresolvedMajor": 0,
            },
            "nameCheck": {
                "story": slug,
                "passed": True,
                "checkedAt": "2026-08-01T12:00:00Z",
                "scopedRegistrySha256": "c" * 64,
            },
        }
        self.write_json(story_directory / "release.json", release)
        (story_directory / "04-review.md").write_text(
            "# Continuity and story review\n\n"
            "## Current certification\n\n"
            "- Reviewed artifact: `05-story.md`\n"
            f"- Artifact SHA-256: {story_digest}\n"
            f"- Canon delta SHA-256: {delta_digest}\n"
            "- Review pass: 2\n"
            "- Verdict: PASS\n"
            "- Reviewer: continuity_critic\n"
            "- Unresolved Critical findings: 0\n"
            "- Unresolved Major findings: 0\n"
            "- Updated: 2026-08-01\n\n"
            "## Review passes\n",
            encoding="utf-8",
        )

    def test_published_candidate_builds_normal_story_page(self) -> None:
        self.add_story("fixture-story")

        output = self.root / "_site-test"
        catalog = build.build(output, self.root, Path(build.__file__).parent)

        self.assertEqual(
            ("fixture-story",), tuple(story.slug for story in catalog.stories)
        )
        self.assertTrue(
            (output / "stories" / "fixture-story" / "index.html").is_file()
        )
        index = (output / "index.html").read_text(encoding="utf-8")
        self.assertIn("Reader-ready stories", index)
        self.assertNotIn("Tell a story whose prompt remains visible.", index)

    def test_prompt_bytes_cannot_change_catalog_cards_or_story_pages(self) -> None:
        story_directory = self.add_story("fixture-story")
        first_output = self.root / "_site-before-prompt-change"
        first_catalog = build.build(
            first_output, self.root, Path(build.__file__).parent
        )
        first_index = (first_output / "index.html").read_bytes()
        first_story = (
            first_output / "stories" / "fixture-story" / "index.html"
        ).read_bytes()

        (story_directory / "00-prompt.md").write_text(
            "# Prompt\n\n## Verbatim writing prompt\n\n"
            "> [WP] THIS TEXT MUST NEVER REACH THE READER SITE.\n",
            encoding="utf-8",
        )
        second_output = self.root / "_site-after-prompt-change"
        second_catalog = build.build(
            second_output, self.root, Path(build.__file__).parent
        )

        self.assertEqual(first_catalog, second_catalog)
        self.assertEqual(first_index, (second_output / "index.html").read_bytes())
        self.assertEqual(
            first_story,
            (
                second_output / "stories" / "fixture-story" / "index.html"
            ).read_bytes(),
        )

    def test_final_story_uses_same_reader_path(self) -> None:
        self.add_story("fixture-story", status="final")

        output = self.root / "_site-test"
        catalog = build.build(output, self.root, Path(build.__file__).parent)

        self.assertEqual("final", catalog.stories[0].metadata.status)
        self.assertTrue(
            (output / "stories" / "fixture-story" / "index.html").is_file()
        )

    def test_lifecycle_transition_does_not_change_final_artifact(self) -> None:
        story_directory = self.add_story("fixture-story")
        story_path = story_directory / "05-story.md"
        original_digest = hashlib.sha256(story_path.read_bytes()).hexdigest()
        metadata_path = story_directory / "story.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update(
            stage="final",
            status="final",
            canon=True,
            userDisposition="accepted",
            promotionDate="2026-08-01",
        )
        self.write_json(metadata_path, metadata)

        catalog = build.load_catalog(self.root)

        self.assertEqual("final", catalog.stories[0].metadata.status)
        self.assertEqual(
            original_digest, hashlib.sha256(story_path.read_bytes()).hexdigest()
        )

    def test_release_hash_change_blocks_published_story(self) -> None:
        story_directory = self.add_story("fixture-story")
        with (story_directory / "05-story.md").open("a", encoding="utf-8") as handle:
            handle.write("\nChanged after certification.\n")

        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            build.load_catalog(self.root)

    def test_uncertified_release_blocks_published_story(self) -> None:
        story_directory = self.add_story("fixture-story")
        release_path = story_directory / "release.json"
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release["certified"] = False
        self.write_json(release_path, release)

        with self.assertRaisesRegex(ValueError, "must be certified"):
            build.load_catalog(self.root)

    def test_review_receipt_must_match_current_certification(self) -> None:
        story_directory = self.add_story("fixture-story")
        review_path = story_directory / "04-review.md"
        review = review_path.read_text(encoding="utf-8").replace(
            "- Verdict: PASS", "- Verdict: REVISE"
        )
        review_path.write_text(review, encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "does not match release.json"):
            build.load_catalog(self.root)

    def test_unknown_release_fields_are_rejected_at_every_level(self) -> None:
        story_directory = self.add_story("fixture-story")
        release_path = story_directory / "release.json"
        baseline = json.loads(release_path.read_text(encoding="utf-8"))
        cases = (
            ("release", lambda value: value.__setitem__("sourceProvenance", {})),
            (
                "artifacts",
                lambda value: value["artifacts"].__setitem__("source", {}),
            ),
            (
                "artifact",
                lambda value: value["artifacts"]["story"].__setitem__(
                    "origin", "archive"
                ),
            ),
            (
                "review",
                lambda value: value["review"].__setitem__("provenance", "prompt"),
            ),
            (
                "name-check",
                lambda value: value["nameCheck"].__setitem__(
                    "sourceClass", "imported"
                ),
            ),
        )
        for context, mutate in cases:
            with self.subTest(context=context):
                release = json.loads(json.dumps(baseline))
                mutate(release)
                self.write_json(release_path, release)
                with self.assertRaisesRegex(ValueError, "unknown"):
                    build.load_catalog(self.root)

    def test_in_progress_story_is_not_published(self) -> None:
        self.add_story("fixture-story", status="in-progress")

        with self.assertRaisesRegex(ValueError, "No published stories"):
            build.load_catalog(self.root)

    def test_abandoned_story_is_not_auto_published(self) -> None:
        self.add_story("discarded-story", status="abandoned")
        self.add_story("fixture-story")

        catalog = build.load_catalog(self.root)

        self.assertEqual(
            ("fixture-story",), tuple(story.slug for story in catalog.stories)
        )

    def test_frontmatter_must_agree_with_story_metadata(self) -> None:
        self.add_story(
            "fixture-story", frontmatter_title="Wrong Title"
        )

        with self.assertRaisesRegex(ValueError, "disagrees with story.json"):
            build.load_catalog(self.root)

    def test_unknown_frontmatter_field_is_rejected(self) -> None:
        story_directory = self.add_story("fixture-story")
        story_path = story_directory / "05-story.md"
        content = story_path.read_text(encoding="utf-8").replace(
            "created: 2026-08-01\n", "created: 2026-08-01\nunexpected: value\n"
        )
        story_path.write_text(content, encoding="utf-8")
        self.write_release(story_directory, "fixture-story")

        with self.assertRaisesRegex(ValueError, "unknown unexpected"):
            build.load_catalog(self.root)

    def test_unknown_story_metadata_field_is_rejected(self) -> None:
        story_directory = self.add_story("fixture-story", publish=False)
        metadata_path = story_directory / "story.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["unexpected"] = []
        self.write_json(metadata_path, metadata)

        with self.assertRaisesRegex(ValueError, "unknown unexpected"):
            build.load_catalog(self.root)


if __name__ == "__main__":
    unittest.main()
