"""Regression checks for input limits, attempt history, and targeted edit provenance."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from illustrated import edition


class AssetConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.manifest = {
            "slug": "fixture", "backend": "codex-imagegen",
            "externalReferences": [{"id": f"external-{index}"} for index in range(1, 7)],
            "cover": {"id": "cover", "kind": "cover", "reused": True,
                      "prompt": "Reuse cover.", "size": "1024x1536", "references": ["source-cover"]},
            "references": [], "illustrations": [],
        }
        loader = patch.object(edition, "load_edition", return_value=self.manifest)
        source = patch.object(edition, "verify_source")
        saver = patch.object(edition, "save_edition")
        loader.start()
        source.start()
        self.save = saver.start()
        self.addCleanup(loader.stop)
        self.addCleanup(source.stop)
        self.addCleanup(saver.stop)

    def configure(self, asset_id="person", **kwargs):
        return edition.configure_asset(self.root, "fixture", asset_id,
                                       kind="character", prompt="One named character.", **kwargs)

    def test_over_limit_default_and_explicit_inputs_fail_before_saving(self):
        original = deepcopy(self.manifest)
        for refs in (None, [f"external-{index}" for index in range(1, 7)]):
            with self.subTest(references=refs), self.assertRaisesRegex(ValueError, "at most five"):
                self.configure(references=refs)
            self.assertEqual(self.manifest, original)
        self.save.assert_not_called()
        selected = ["source-cover", "external-1", "external-2", "external-3", "external-4"]
        result = self.configure(references=selected)
        self.assertEqual(result["references"][0]["references"], selected)
        self.save.assert_called_once()

    def test_plan_rejects_preexisting_over_limit_selection(self):
        self.manifest["references"] = [{
            "id": "person", "kind": "character", "prompt": "Character.",
            "size": "1536x1024", "references": [f"external-{index}" for index in range(1, 7)],
        }]
        self.manifest["illustrations"] = [{"id": "scene"}]
        with patch.object(edition, "_text", return_value="# Plan\nStatus: READY\n"):
            with self.assertRaisesRegex(ValueError, "select references explicitly for person"):
                edition._check_plan(self.root, self.manifest)
        self.save.assert_not_called()

    def test_retired_id_cannot_reset_attempt_history(self):
        retired = {
            "id": "combined-characters", "kind": "character", "attempts": 3,
            "candidate": {"attempt": 3, "status": "rejected", "evidence": "Incorrect names."},
            "supersessionReason": "User requested individually named character sheets.",
        }
        self.manifest["retiredAssets"] = [deepcopy(retired)]
        with self.assertRaisesRegex(ValueError, "Retired asset IDs remain reserved"):
            self.configure("combined-characters", references=["source-cover"])
        self.save.assert_not_called()
        result = self.configure("individual-character", references=["source-cover"])
        self.assertEqual(result["retiredAssets"], [retired])
        self.assertEqual(result["references"][0]["attempts"], 0)


class TargetedEditTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="illustrated-edit-test-")
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.root = self.temporary / "worktree"
        self.directory = self.root / "illustrated" / "fixture"
        (self.directory / "references").mkdir(parents=True)
        self.manifest = {
            "slug": "fixture", "backend": "codex-imagegen", "model": edition.TOOL_MODEL,
            "quality": edition.TOOL_MODEL, "visualReviewPolicy": "assistant",
            "source": {"files": {"fixture-source": "unchanged"}}, "approvals": {},
            "externalReferences": [], "cover": {"id": "cover"},
            "references": [], "illustrations": [],
        }
        for name, kwargs in (
            ("load_edition", {"return_value": self.manifest}),
            ("validate_edition", {"return_value": self.manifest}),
            ("_require_approval", {}), ("_check_visuals", {}), ("_require_visual_review", {}),
            ("_mutable", {}), ("verify_source", {}),
            ("_art_direction", {"return_value": "GLOBAL ART DIRECTION SENTINEL"}),
            ("save_edition", {}),
        ):
            patcher = patch.object(edition, name, **kwargs)
            mock = patcher.start()
            self.addCleanup(patcher.stop)
            if name == "save_edition":
                self.save = mock
        self.references = {}
        for index, name in enumerate(("cal", "tuck", "voss", "clinic", "objects", "unplanned")):
            reference_id = f"ref-{name}"
            path = self.directory / "references" / f"{reference_id}.png"
            Image.new("RGB", (6, 4), (index * 30, 90, 120)).save(path)
            reference = {
                "id": reference_id, "kind": "character", "prompt": "Fixture reference.",
                "path": f"references/{reference_id}.png", "references": [],
                "size": "1536x1024", "actualSize": "6x4", "attempts": 1,
                "sha256": edition.file_hash(path),
            }
            reference["accepted"] = {
                "sha256": reference["sha256"], "evidence": "Fixture accepted.",
                "inputsSha256": edition._asset_inputs(self.root, self.manifest, reference)[0],
                "generation": {"backend": "codex-imagegen", "model": edition.TOOL_MODEL,
                               "tool": "image_gen", "outputEvidence": "Fixture tool output."},
            }
            self.manifest["references"].append(reference)
            self.references[reference_id] = reference
        self.asset = {
            "id": "scene", "kind": "illustration", "prompt": "FULL ORIGINAL SCENE BRIEF SENTINEL",
            "size": "1536x1024", "path": "illustrations/scene.png", "attempts": 2,
            "references": ["ref-cal", "ref-tuck", "ref-voss", "ref-clinic", "ref-objects"],
        }
        self.manifest["illustrations"].append(self.asset)
        self.base = self.temporary / "rejected.png"
        self.output = self.temporary / "tool-output.png"
        Image.new("RGB", (6, 4), "white").save(self.base)
        Image.new("RGB", (6, 4), "ivory").save(self.output)
        self.asset["candidate"] = {
            "path": str(self.base), "sha256": edition.file_hash(self.base), "attempt": 2,
            "status": "rejected", "backend": "codex-imagegen", "model": edition.TOOL_MODEL,
            "tool": "image_gen", "outputEvidence": "Original fixture tool completion.",
            "evidence": "Only the evidence bag failed.", "promptSha256": "old-prompt-hash",
            "inputsSha256": edition._asset_inputs(self.root, self.manifest, self.asset)[0],
        }
        self.selected = ["ref-cal", "ref-tuck", "ref-voss", "ref-objects"]
        self.correction = "Correct only the evidence bag contents. Preserve every person and the room."

    def prepare(self, **kwargs):
        options = {"edit_last_rejected": True, "references": self.selected, "correction": self.correction}
        options.update(kwargs)
        return edition.prepare_tool(self.root, "fixture", "scene", **options)

    def test_focused_request_preserves_provenance_through_acceptance(self):
        previous = deepcopy(self.asset["candidate"])
        planned = list(self.asset["references"])
        response = self.prepare()
        candidate = self.asset["candidate"]
        self.assertEqual(self.asset["attempts"], 3)
        self.assertEqual(candidate["inputsSha256"], previous["inputsSha256"])
        self.assertEqual(self.asset["references"], planned)
        self.assertEqual(candidate["request"]["editBase"], previous)
        self.assertIsNot(candidate["request"]["editBase"], previous)
        self.assertEqual(candidate["request"]["prompt"], response["prompt"])
        self.assertEqual(candidate["requestSha256"], edition._digest(candidate["request"]))
        self.assertEqual(response["referenced_image_paths"], [str(self.base)] + [
            str(self.directory / self.references[reference_id]["path"]) for reference_id in self.selected])
        self.assertEqual(len(response["referenced_image_paths"]), 5)
        self.assertIn(self.correction, response["prompt"])
        self.assertIn("Image 1: exact rejected base", response["prompt"])
        self.assertIn("Image 5: ref-objects", response["prompt"])
        self.assertIn("same 6x4-pixel canvas", response["prompt"])
        self.assertNotIn("SCENE BRIEF SENTINEL", response["prompt"])
        self.assertNotIn("ART DIRECTION SENTINEL", response["prompt"])
        self.assertNotIn("Approved story art direction", response["prompt"])
        edition.record_tool_output(self.root, "fixture", "scene", self.output, "Fixture edit completed.")
        edition.accept_candidate(self.root, "fixture", "scene", "Fixture whole-image review passed.")
        generation = self.asset["accepted"]["generation"]
        self.assertEqual(generation["request"]["editBase"], previous)
        self.assertEqual(generation["requestSha256"], response["requestSha256"])
        self.assertEqual(self.asset["attempts"], 3)
        self.assertNotIn("candidate", self.asset)
        # Temporary edit inputs may be removed after acceptance; retained provenance still validates.
        self.base.unlink()
        edition._check_asset(self.root, self.manifest, self.asset)

    def test_dry_run_at_exhausted_cap_does_not_reserve_or_grant(self):
        self.asset["attempts"] = self.asset["candidate"]["attempt"] = 3
        original = deepcopy(self.manifest)
        response = self.prepare(dry_run=True)
        self.assertTrue(response["dryRun"])
        self.assertEqual(response["attempt"], 4)
        self.assertEqual(self.manifest, original)
        self.save.assert_not_called()
        with self.assertRaisesRegex(ValueError, "exhausted"):
            self.prepare()
        self.assertEqual(self.manifest, original)
        self.save.assert_not_called()

    def test_edit_target_counts_toward_cap_without_implicit_omissions(self):
        original = deepcopy(self.manifest)
        for selected in (None, list(self.asset["references"])):
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, "total at most five"):
                self.prepare(references=selected)
            self.assertEqual(self.manifest, original)
        self.save.assert_not_called()
        self.prepare(dry_run=True)
        self.assertEqual(self.manifest, original)

    def test_bag_only_edit_uses_base_and_object_reference(self):
        original = deepcopy(self.manifest)
        response = self.prepare(references=["ref-objects"], dry_run=True)
        self.assertEqual(response["referenced_image_paths"], [
            str(self.base), str(self.directory / "references/ref-objects.png")])
        self.assertIn("Image 2: ref-objects", response["prompt"])
        self.assertNotIn("ref-cal", response["prompt"])
        self.assertEqual(self.manifest, original)
        self.save.assert_not_called()

    def test_subset_requires_unique_accepted_planned_dependencies(self):
        original = deepcopy(self.manifest)
        for selected in (["external-001"], ["unknown"], ["ref-unplanned"], ["ref-cal", "ref-cal"]):
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, "accepted planned"):
                self.prepare(references=selected)
            self.assertEqual(self.manifest, original)
        self.references["ref-cal"]["accepted"] = None
        with self.assertRaisesRegex(ValueError, "Inspect and accept"):
            self.prepare()
        self.assertEqual(self.asset["attempts"], 2)
        self.save.assert_not_called()

    def test_planned_external_input_cannot_replace_an_accepted_edit_reference(self):
        self.manifest["externalReferences"] = [{"id": "external-001", "path": str(self.base), "sha256": edition.file_hash(self.base)}]
        self.asset["references"][3] = "external-001"
        self.asset["candidate"]["inputsSha256"] = edition._asset_inputs(self.root, self.manifest, self.asset)[0]
        original = deepcopy(self.manifest)
        with self.assertRaisesRegex(ValueError, "accepted planned"):
            self.prepare(references=["external-001"])
        self.assertEqual(self.manifest, original)
        self.save.assert_not_called()

    def test_edit_preconditions_and_changed_base_fail_before_reservation(self):
        original = deepcopy(self.manifest)
        with self.assertRaisesRegex(ValueError, "nonempty correction"):
            self.prepare(correction=" ")
        with self.assertRaisesRegex(ValueError, "require --edit-last-rejected"):
            self.prepare(edit_last_rejected=False)
        self.asset["candidate"]["status"] = "failed"
        with self.assertRaisesRegex(ValueError, "latest rejected actual"):
            self.prepare()
        self.asset["candidate"]["status"] = "rejected"
        self.asset["candidate"].pop("outputEvidence")
        with self.assertRaisesRegex(ValueError, "latest rejected actual"):
            self.prepare()
        self.asset["candidate"] = deepcopy(original["illustrations"][0]["candidate"])
        self.base.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Rejected candidate bytes"):
            self.prepare()
        self.assertEqual(self.manifest, original)
        self.save.assert_not_called()

    def test_omitted_edit_target_is_rejected_even_with_rehashed_request(self):
        self.prepare()
        candidate = self.asset["candidate"]
        candidate["request"]["images"].pop(0)
        candidate["requestSha256"] = edition._digest(candidate["request"])
        self.save.reset_mock()
        with self.assertRaisesRegex(ValueError, "omitted or changed its rejected edit target"):
            edition.record_tool_output(self.root, "fixture", "scene", self.output, "Fixture tool completion.")
        self.assertEqual(candidate["status"], "generating")
        self.save.assert_not_called()

    def test_new_request_cannot_lose_its_provenance_as_a_legacy_output(self):
        self.prepare()
        candidate = self.asset["candidate"]
        candidate.pop("request")
        candidate.pop("requestSha256")
        self.save.reset_mock()
        with self.assertRaisesRegex(ValueError, "provenance changed or is incomplete"):
            edition.record_tool_output(self.root, "fixture", "scene", self.output, "Fixture completion.")
        self.save.assert_not_called()

    def test_ordinary_generation_keeps_full_brief_and_records_all_inputs(self):
        response = self.prepare(edit_last_rejected=False, references=None)
        candidate = self.asset["candidate"]
        self.assertIn("FULL ORIGINAL SCENE BRIEF SENTINEL", response["prompt"])
        self.assertIn("GLOBAL ART DIRECTION SENTINEL", response["prompt"])
        self.assertNotIn("editBase", candidate["request"])
        self.assertEqual([item["id"] for item in candidate["request"]["images"]], self.asset["references"])
        self.assertEqual(len(response["referenced_image_paths"]), 5)

    def test_prompt_and_base_tamper_block_output_recording_and_acceptance(self):
        self.prepare()
        candidate = self.asset["candidate"]
        original_request = deepcopy(candidate["request"])
        candidate["request"]["prompt"] += " Redraw everything."
        with self.assertRaisesRegex(ValueError, "provenance changed"):
            edition.record_tool_output(self.root, "fixture", "scene", self.output, "Fixture completion.")
        candidate["request"] = original_request
        original_bytes = self.base.read_bytes()
        self.base.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "input bytes"):
            edition.record_tool_output(self.root, "fixture", "scene", self.output, "Fixture completion.")
        self.base.write_bytes(original_bytes)
        edition.record_tool_output(self.root, "fixture", "scene", self.output, "Fixture completion.")
        self.base.write_bytes(b"changed after recording")
        self.save.reset_mock()
        with self.assertRaisesRegex(ValueError, "input bytes"):
            edition.accept_candidate(self.root, "fixture", "scene", "Fixture review.")
        self.assertEqual(candidate["status"], "ready")
        self.assertNotIn("accepted", self.asset)
        self.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
