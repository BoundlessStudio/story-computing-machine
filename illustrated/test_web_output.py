"""Web output integrity and publication replacement regression checks."""

import hashlib
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from illustrated import edition
from pages import build, illustrated_editions
from pages.test_build import story_fixture


class WebOutputTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="illustrated-web-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.manifests = {}
        self.verify_source = edition.verify_source
        self.check_render = edition._check_render
        # Art generation, upstream approvals, and source pinning are outside this
        # fixture. Output hashes, review checks, final approvals, and capture run
        # through their real implementations against disposable files.
        patches = (
            (edition, "require_worktree", {}),
            (edition, "load_edition", {"side_effect": lambda root, slug: self.manifests[slug]}),
            (edition, "verify_source", {}),
            (edition, "_check_originals", {}),
            (edition, "_check_plan", {}),
            (edition, "_check_render", {}),
            (edition, "save_edition", {}),
            (edition, "get_source_body", {"side_effect": lambda root, manifest: manifest["fixtureBody"]}),
            (edition, "_renderer_hashes", {"return_value": {"renderer": "fixture-v1"}}),
        )
        for target, name, kwargs in patches:
            patcher = patch.object(target, name, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.manifest = self.make_manifest("new-edition", "source-story")

    def make_manifest(self, slug, source_slug, *, legacy_pdf=False):
        directory = self.root / "illustrated" / slug
        directory.mkdir(parents=True)
        (directory / "prompt.md").write_text("Create an illustrated edition.\n", encoding="utf-8")
        (directory / "plan.md").write_text("A cover and one interior scene.\n", encoding="utf-8")
        Image.new("RGB", (32, 48), "ivory").save(directory / "cover.png")
        Image.new("RGB", (48, 32), "navy").save(directory / "scene.png")
        body = "# Source Story\n\nA quiet beginning.\n\nAn open door.\n"
        manifest = {
            "slug": slug, "title": "Source Story", "mode": "Classic",
            "model": edition.MODEL, "quality": edition.QUALITY,
            "source": {"slug": source_slug, "bodySha256": hashlib.sha256(body.encode()).hexdigest()},
            "fixtureBody": body, "externalReferences": [], "references": [],
            "approvals": {}, "layoutPreview": None,
            "cover": {"id": "cover", "path": "cover.png", "sha256": edition.file_hash(directory / "cover.png")},
            "illustrations": [{
                "id": "scene", "path": "scene.png", "sha256": edition.file_hash(directory / "scene.png"),
                "after": illustrated_editions.block_anchors(body, "Source Story")[0]["id"],
                "layout": "inline", "alt": "An open door in a quiet room.",
            }],
        }
        if not legacy_pdf:
            manifest["outputFormat"] = "web"
        self.manifests[slug] = manifest
        return manifest

    def report(self, manifest, pdf_verdict="NOT REQUESTED"):
        path = self.root / "illustrated" / manifest["slug"] / "review.md"
        path.write_text(
            "# Independent review\n\nVerdict: PASS\n\n"
            "- Source fidelity: PASS\n- Visual continuity: PASS\n- Web readability: PASS\n"
            f"- Every PDF page: {pdf_verdict}\n- Blocking: none\n", encoding="utf-8",
        )

    def finalize(self, manifest, *, legacy_pdf=False):
        directory = self.root / "illustrated" / manifest["slug"]
        if legacy_pdf:
            pdf = directory / "edition.pdf"
            pdf.write_bytes(b"%PDF-1.7\nFixture PDF bytes.\n")
            manifest["render"] = {
                "inputsSha256": edition.stage_digest(self.root, manifest, "render"),
                "pdfSha256": edition.file_hash(pdf),
            }
        else:
            illustrated_editions.render_edition(self.root, manifest["slug"])
        self.report(manifest, "PASS" if legacy_pdf else "NOT REQUESTED")
        edition.record_review(self.root, manifest["slug"], "independent-fixture-reviewer", "Inspected every requested output.")
        edition.approve(self.root, manifest["slug"], "final", "Approve this exact reviewed fixture edition.")
        edition.validate_edition(self.root, manifest["slug"], "final")

    def artwork_report(self, manifest, *, web="PASS", pdf="NOT REQUESTED"):
        path = self.root / "illustrated" / manifest["slug"] / "review.md"
        path.write_text(
            "# Independent review\n\nVerdict: REVISE\nReviewer: independent-fixture-reviewer\n\n"
            "- Source fidelity: REVISE\n- Visual continuity: REVISE\n"
            f"- Web readability: {web}\n- Every PDF page: {pdf}\n\n"
            "## Findings\n\n- Blocking — scene.png depicts the door open before its release.\n",
            encoding="utf-8",
        )
        return path

    def accept_artwork(self, manifest):
        return edition.accept_review_findings(
            self.root, manifest["slug"], "Publish current images as-is; accept the documented artwork issues.",
            "independent-fixture-reviewer", "Reviewed the exact reader and documented the open door artwork mismatch.",
        )

    def test_artwork_acceptance_preserves_revise_and_requires_separate_final_approval(self):
        illustrated_editions.render_edition(self.root, "new-edition")
        report = self.artwork_report(self.manifest)
        report_bytes = report.read_bytes()
        with self.assertRaisesRegex(ValueError, "independent passing review"):
            edition.approve(self.root, "new-edition", "final", "Publish this reader.")
        with self.assertRaisesRegex(ValueError, "independent passing review"):
            edition.validate_edition(self.root, "new-edition", "final")
        self.accept_artwork(self.manifest)
        self.assertEqual(report.read_bytes(), report_bytes)
        self.assertIsNone(self.manifest.get("review"))
        self.assertEqual(self.manifest["reviewFindingsAcceptance"]["verdict"], "REVISE")
        with self.assertRaisesRegex(ValueError, "explicit user final approval"):
            edition.validate_edition(self.root, "new-edition", "final")
        edition.approve(self.root, "new-edition", "final", "Publish this exact reader with the accepted artwork issues.")
        edition.validate_edition(self.root, "new-edition", "final")
        edition.validate_edition(self.root, "new-edition", "capture")
        with self.assertRaisesRegex(ValueError, "independent passing review"):
            edition.validate_edition(self.root, "new-edition", "review")
        with self.assertRaisesRegex(ValueError, "Verdict: PASS"):
            edition.record_review(self.root, "new-edition", "independent-fixture-reviewer", "Artwork issues accepted by user.")
        self.manifest["reviewFindingsAcceptance"]["decision"] += " Changed decision."
        with self.assertRaisesRegex(ValueError, "stale explicit user final approval"):
            edition.validate_edition(self.root, "new-edition", "final")

    def test_artwork_acceptance_rejects_blank_or_non_user_decisions_and_wrong_reviewer(self):
        illustrated_editions.render_edition(self.root, "new-edition")
        self.artwork_report(self.manifest)
        for decision, actor, reviewer, evidence in (
            (" ", "user", "independent-fixture-reviewer", "Evidence"),
            ("Accept issues", "assistant", "independent-fixture-reviewer", "Evidence"),
            ("Accept issues", "user", "different-reviewer", "Evidence"),
            ("Accept issues", "user", "independent-fixture-reviewer", " "),
        ):
            with self.subTest(decision=decision, actor=actor, reviewer=reviewer, evidence=evidence):
                with self.assertRaises(ValueError):
                    edition.accept_review_findings(self.root, "new-edition", decision, reviewer, evidence, actor=actor)
                self.assertNotIn("reviewFindingsAcceptance", self.manifest)

    def test_artwork_acceptance_cannot_waive_missing_review_web_or_pdf_failures(self):
        illustrated_editions.render_edition(self.root, "new-edition")
        with self.assertRaisesRegex(ValueError, "independent REVISE review.md"):
            self.accept_artwork(self.manifest)
        self.report(self.manifest)
        with self.assertRaisesRegex(ValueError, "Verdict: REVISE"):
            self.accept_artwork(self.manifest)
        report = self.artwork_report(self.manifest)
        report.write_text(report.read_text(encoding="utf-8").split("## Findings")[0], encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "document its blocking artwork findings"):
            self.accept_artwork(self.manifest)
        for web, pdf in (("REVISE", "NOT REQUESTED"), ("PENDING", "NOT REQUESTED"), ("PASS", "PASS")):
            with self.subTest(web=web, pdf=pdf):
                self.artwork_report(self.manifest, web=web, pdf=pdf)
                with self.assertRaises(ValueError):
                    self.accept_artwork(self.manifest)
        legacy = self.make_manifest("legacy-edition", "legacy-story", legacy_pdf=True)
        self.finalize(legacy, legacy_pdf=True)
        for verdict in ("PENDING", "REVISE", "NOT REQUESTED"):
            with self.subTest(requested_pdf_verdict=verdict):
                self.artwork_report(legacy, pdf=verdict)
                with self.assertRaisesRegex(ValueError, "PDF review must declare PASS"):
                    self.accept_artwork(legacy)

    def test_artwork_acceptance_invalidates_on_changed_review_html_or_recorded_assets(self):
        illustrated_editions.render_edition(self.root, "new-edition")
        report = self.artwork_report(self.manifest)
        self.accept_artwork(self.manifest)
        edition.approve(self.root, "new-edition", "final", "Publish the accepted current reader.")
        report_bytes = report.read_bytes()
        report.write_bytes(report_bytes + b"\nAn additional finding.\n")
        with self.assertRaisesRegex(ValueError, "acceptance of artwork findings is stale"):
            edition.validate_edition(self.root, "new-edition", "final")
        report.write_bytes(report_bytes)
        document = report.with_name("edition.html")
        document_bytes = document.read_bytes()
        document.write_bytes(document_bytes + b"<!-- changed -->")
        with self.assertRaisesRegex(ValueError, "changed rendered web reader"):
            edition.validate_edition(self.root, "new-edition", "final")
        self.manifest["render"]["htmlSha256"] = edition.file_hash(document)
        with self.assertRaisesRegex(ValueError, "acceptance of artwork findings is stale"):
            edition.validate_edition(self.root, "new-edition", "final")
        document.write_bytes(document_bytes)
        self.manifest["render"]["htmlSha256"] = edition.file_hash(document)
        self.manifest["illustrations"][0]["sha256"] = "changed selected artwork"
        with self.assertRaisesRegex(ValueError, "stale rendered edition"):
            edition.validate_edition(self.root, "new-edition", "final")

    def test_artwork_acceptance_keeps_actual_source_and_asset_byte_checks(self):
        source = self.root / "stories/source-story/story.md"
        source.parent.mkdir(parents=True)
        source.write_text("---\ntitle: Source Story\nslug: source-story\ncreated: 2026-09-14\ncanon: false\n---\n" + self.manifest["fixtureBody"], encoding="utf-8")
        self.manifest["source"].update(title="Source Story", layout="current", prose="stories/source-story/story.md", files={"stories/source-story/story.md": edition.file_hash(source, text=True)})
        scene = self.manifest["illustrations"][0]
        scene.update(size="48x32", accepted={"sha256": scene["sha256"], "inputsSha256": "fixture-inputs", "evidence": "Inspected scene."})
        illustrated_editions.render_edition(self.root, "new-edition")
        self.artwork_report(self.manifest)
        self.accept_artwork(self.manifest)
        edition.approve(self.root, "new-edition", "final", "Publish the accepted current reader.")
        with patch.object(edition, "verify_source", wraps=self.verify_source):
            edition.validate_edition(self.root, "new-edition", "final")
            original = source.read_bytes()
            source.write_bytes(original + b"Changed source prose.\n")
            with self.assertRaisesRegex(ValueError, "Source changed"):
                edition.validate_edition(self.root, "new-edition", "final")
            source.write_bytes(original)
        with (patch.object(edition, "_check_render", wraps=self.check_render),
              patch.object(edition, "_check_visuals"), patch.object(edition, "_require_visual_review"),
              patch.object(edition, "_asset_inputs", return_value=("fixture-inputs", []))):
            edition.validate_edition(self.root, "new-edition", "final")
            image = self.root / "illustrated/new-edition/scene.png"
            Image.new("RGB", (48, 32), "red").save(image)
            with self.assertRaisesRegex(ValueError, "changed selected asset"):
                edition.validate_edition(self.root, "new-edition", "final")

    def test_user_accepted_artwork_capture_replaces_the_existing_reader(self):
        pages = self.root / "pages"
        (pages / "covers").mkdir(parents=True)
        story = story_fixture()
        Image.new("RGB", (864, 1536), "navy").save(pages / story.cover)
        build.save_catalog([story], pages / "catalog.json")
        source = self.root / "stories/source-story/story.md"
        source.parent.mkdir(parents=True)
        source.write_text("---\ncanon: true\n---\n" + story.body, encoding="utf-8")
        original_catalog, original_source = (pages / "catalog.json").read_bytes(), source.read_bytes()
        illustrated_editions.render_edition(self.root, "new-edition")
        self.artwork_report(self.manifest)
        with self.assertRaisesRegex(ValueError, "independent passing review"):
            illustrated_editions.capture_edition(self.root, "new-edition")
        self.accept_artwork(self.manifest)
        with self.assertRaisesRegex(ValueError, "explicit user final approval"):
            illustrated_editions.capture_edition(self.root, "new-edition")
        edition.approve(self.root, "new-edition", "final", "Publish the exact current reader with the accepted artwork findings.")
        illustrated_editions.capture_edition(self.root, "new-edition")
        output = self.root / "site"
        build.build(output, pages / "catalog.json")
        reader = (output / "stories/source-story.html").read_text(encoding="utf-8")
        self.assertIn('src="../illustrated/new-edition/scene.png"', reader)
        self.assertEqual(len(list((output / "stories").glob("*.html"))), 1)
        self.assertEqual((pages / "catalog.json").read_bytes(), original_catalog)
        self.assertEqual(source.read_bytes(), original_source)

    def test_web_render_never_exports_pdf_and_invalidates_old_review(self):
        self.manifest["review"] = {"verdict": "PASS"}
        self.manifest["approvals"]["final"] = {"decision": "Earlier output"}
        with patch.object(illustrated_editions.subprocess, "run", side_effect=AssertionError("PDF exporter invoked")) as exporter:
            target = illustrated_editions.render_edition(self.root, self.manifest["slug"])
        exporter.assert_not_called()
        self.assertEqual(target.name, "edition.html")
        self.assertEqual(self.manifest["render"]["htmlSha256"], edition.file_hash(target))
        self.assertNotIn("pdfSha256", self.manifest["render"])
        self.assertNotIn("review", self.manifest)
        self.assertNotIn("final", self.manifest["approvals"])
        self.assertFalse(target.with_suffix(".pdf").exists())
        edition._check_output(self.root, self.manifest)

    def test_changed_or_missing_html_and_stale_inputs_block_final_validation(self):
        self.finalize(self.manifest)
        target = self.root / "illustrated/new-edition/edition.html"
        original = target.read_bytes()
        target.write_bytes(original + b"changed")
        with self.assertRaisesRegex(ValueError, "changed rendered web reader"):
            edition.validate_edition(self.root, "new-edition", "final")
        target.unlink()
        with self.assertRaisesRegex(ValueError, "changed rendered web reader"):
            edition.validate_edition(self.root, "new-edition", "final")
        target.write_bytes(original)
        self.manifest["illustrations"][0]["alt"] = "A changed scene description."
        with self.assertRaisesRegex(ValueError, "stale rendered edition"):
            edition.validate_edition(self.root, "new-edition", "final")

    def test_web_review_requires_not_requested_pdf_and_exact_final_approval(self):
        illustrated_editions.render_edition(self.root, "new-edition")
        self.report(self.manifest, "PASS")
        with self.assertRaisesRegex(ValueError, "NOT REQUESTED"):
            edition.record_review(self.root, "new-edition", "reviewer", "Inspected the reader.")
        self.report(self.manifest)
        edition.record_review(self.root, "new-edition", "reviewer", "Inspected the reader.")
        with self.assertRaisesRegex(ValueError, "explicit user final approval"):
            edition.validate_edition(self.root, "new-edition", "final")
        edition.approve(self.root, "new-edition", "final", "Approve this exact reader.")
        edition.validate_edition(self.root, "new-edition", "final")
        self.manifest["review"]["evidence"] = "Different review evidence."
        with self.assertRaisesRegex(ValueError, "stale explicit user final approval"):
            edition.validate_edition(self.root, "new-edition", "final")

    def test_published_prompt_change_invalidates_reviewed_render(self):
        pages = self.root / 'pages'
        pages.mkdir()
        story = story_fixture()
        (pages / 'covers').mkdir()
        Image.new('RGB', (864, 1536), 'navy').save(pages / story.cover)
        build.save_catalog([story], pages / 'catalog.json')
        self.finalize(self.manifest)
        document = self.root / 'illustrated/new-edition/edition.html'
        self.assertIn(story.prompt, document.read_text(encoding='utf-8'))
        build.save_catalog([replace(story, prompt='An explicitly revised public prompt.')], pages / 'catalog.json')
        with self.assertRaisesRegex(ValueError, 'stale rendered edition'):
            edition.validate_edition(self.root, 'new-edition', 'final')

    def test_legacy_pdf_contract_stays_valid_and_requires_its_bytes(self):
        legacy = self.make_manifest("legacy-edition", "legacy-story", legacy_pdf=True)
        self.finalize(legacy, legacy_pdf=True)
        self.assertTrue(edition.pdf_requested(legacy))
        record = illustrated_editions._record(self.root, legacy)
        self.assertIn("Download PDF", illustrated_editions.render_document(record))
        pdf = self.root / "illustrated/legacy-edition/edition.pdf"
        pdf.write_bytes(b"changed PDF")
        with self.assertRaisesRegex(ValueError, "changed requested PDF"):
            edition.validate_edition(self.root, "legacy-edition", "final")

    def test_named_web_capture_replaces_one_source_and_preserves_legacy_other_source(self):
        pages = self.root / "pages"
        (pages / "covers").mkdir(parents=True)
        stories = [story_fixture(), story_fixture("other-story")]
        for story in stories:
            Image.new("RGB", (864, 1536), "navy").save(pages / story.cover)
            source = self.root / "stories" / story.slug / "story.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\ncanon: true\n---\n" + story.body, encoding="utf-8")
        build.save_catalog(stories, pages / "catalog.json")
        source_bytes = {path: path.read_bytes() for path in (self.root / "stories").rglob("*") if path.is_file()}
        catalog_bytes = (pages / "catalog.json").read_bytes()
        previous = self.make_manifest("previous-edition", "source-story", legacy_pdf=True)
        other = self.make_manifest("other-edition", "other-story", legacy_pdf=True)
        for manifest in (previous, other):
            self.finalize(manifest, legacy_pdf=True)
            illustrated_editions.capture_edition(self.root, manifest["slug"])
        before = illustrated_editions.load_snapshot(pages / "illustrated.json")
        other_before = next(item for item in before if item["slug"] == "other-edition")
        before_bytes = (pages / "illustrated.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "stale rendered edition"):
            illustrated_editions.capture_edition(self.root, "new-edition")
        self.assertEqual((pages / "illustrated.json").read_bytes(), before_bytes)
        self.finalize(self.manifest)
        document = self.root / "illustrated/new-edition/edition.html"
        reviewed_bytes = document.read_bytes()
        document.write_bytes(reviewed_bytes + b"changed after approval")
        with self.assertRaisesRegex(ValueError, "changed rendered web reader"):
            illustrated_editions.capture_edition(self.root, "new-edition")
        self.assertEqual((pages / "illustrated.json").read_bytes(), before_bytes)
        document.write_bytes(reviewed_bytes)
        illustrated_editions.capture_edition(self.root, "new-edition")
        selected = illustrated_editions.load_snapshot(pages / "illustrated.json")
        self.assertEqual({item["slug"] for item in selected}, {"new-edition", "other-edition"})
        self.assertEqual(sum(item["source"]["slug"] == "source-story" for item in selected), 1)
        self.assertNotIn("pdf", next(item for item in selected if item["slug"] == "new-edition"))
        self.assertEqual(next(item for item in selected if item["slug"] == "other-edition"), other_before)
        self.assertEqual((pages / "catalog.json").read_bytes(), catalog_bytes)
        self.assertEqual({path: path.read_bytes() for path in source_bytes}, source_bytes)
        output = self.root / "site"
        build.build(output, pages / "catalog.json")
        self.assertTrue((output / "stories/source-story.html").is_file())
        self.assertNotIn("Download PDF", (output / "stories/source-story.html").read_text(encoding="utf-8"))
        self.assertFalse((output / "illustrated/previous-edition").exists())
        self.assertTrue((output / "illustrated/other-edition/edition.pdf").is_file())
        self.assertEqual(len(list((output / "stories").glob("*.html"))), 2)


if __name__ == "__main__":
    unittest.main()
