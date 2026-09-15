"""End-to-end lifecycle checks using synthetic pixels, never image generation."""
from copy import deepcopy
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from illustrated import edition, production
from pages.illustrated_editions import block_anchors


class ProductionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix="illustrated-production-test-")
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.root = self.temp / "worktree"
        source = self.root / "stories/source"
        source.mkdir(parents=True)
        (source / "05-story.md").write_text(
            '---\ntitle: "Source"\nslug: source\ncreated: 2026-09-15\n---\n'
            '# Source\n\nThe pin is removed.\n\nThe companion opens the door.\n', encoding="utf-8")
        (source / "story.json").write_text(json.dumps({"title": "Source", "slug": "source", "created": "2026-09-15", "canon": False}), encoding="utf-8")
        (source / "00-prompt.md").write_text("A physical release and a later arrival.\n", encoding="utf-8")
        Image.new("RGB", (18, 32), "black").save(source / "title-image.jpg")
        for name, kwargs in [("_mutable", {}), ("_git", {"return_value": "a" * 40}),
                             ("_renderer_hashes", {"return_value": {"renderer": "version-one"}})]:
            mocker = patch.object(edition, name, **kwargs)
            mocker.start()
            self.addCleanup(mocker.stop)
        edition.create_edition(self.root, "source", "Illustrate the physical release.", slug="fixture")
        self.directory = self.root / "illustrated/fixture"
        self.plan = self.directory / "plan.md"
        self.plan.write_text("# Plan\n\nStatus: READY\n\n## Coverage\n\nRelease: pilot. Arrival: later.\n\n## Art direction\n\nInk contours and restrained washes.\n", encoding="utf-8")
        edition.inspect_original(self.root, "fixture", "source-cover", "Synthetic original inspected.")
        edition.configure_asset(self.root, "fixture", "person", kind="character", prompt="One person.",
                                references=["source-cover"], reference_roles={"source-cover": "Rendering only."})
        edition.configure_asset(self.root, "fixture", "room", kind="location", prompt="One room.",
                                references=["person"], reference_roles={"person": "Style only; no person in the room reference."})
        body = edition.get_source_body(self.root, self.manifest())
        anchors = block_anchors(body, "Source")
        for index, (name, refs) in enumerate([("pilot", ["person"]), ("later", ["person", "room"])]):
            edition.configure_asset(self.root, "fixture", name, kind="illustration", prompt="Show one source moment.",
                                    references=refs, reference_roles={key: "Identity or room geometry only; source state controls." for key in refs},
                                    after=anchors[index]["id"], alt="A physical action.",
                                    scene_state="Pin absent. Six empty sockets. No later arrivals.")
        edition.configure_production(self.root, "fixture", "pilot")
        edition.approve(self.root, "fixture", "plan", "Approve this coverage and centerpiece-first workflow.")

    def manifest(self):
        return edition.load_edition(self.root, "fixture")

    def complete(self, asset_id, *, accept=True, correction=""):
        request = edition.prepare_tool(self.root, "fixture", asset_id, correction=correction)
        output = self.temp / f"{asset_id}-{request['attempt']}.png"
        Image.new("RGB", (6, 4), (request["attempt"] * 20 % 255, sum(asset_id.encode()) % 255, 120)).save(output)
        edition.record_tool_output(self.root, "fixture", asset_id, output, "Synthetic tool completion for lifecycle test.")
        if accept:
            edition.accept_candidate(self.root, "fixture", asset_id, "Synthetic image meets the fixture.")
        else:
            edition.reject_candidate(self.root, "fixture", asset_id, "Wrong pin state; change the conflicting reference strategy.")
        return request

    def sample(self, asset_id):
        asset = edition._asset(self.manifest(), asset_id)
        preview = self.temp / "preview.html"
        relative = os.path.relpath(self.directory / asset["path"], self.temp).replace(os.sep, "/")
        preview.write_text(f'<html><body><img src="{relative}"></body></html>', encoding="utf-8")
        edition.record_layout_preview(self.root, "fixture", preview, "Synthetic layout inspected.")

    def prepare_pilot(self):
        self.complete("person")
        self.sample("person")
        edition.review_visuals(self.root, "fixture", "coordinator", "Initial cover, person and layout inspected.", pilot=True)

    def finish_pilot(self):
        self.prepare_pilot()
        self.complete("pilot")
        self.sample("pilot")
        edition.review_pilot(self.root, "fixture", "coordinator", "Correct source state; release reads at page size.")

    def test_centerpiece_before_remaining_art_then_complete_render_inputs(self):
        with self.assertRaisesRegex(ValueError, "centerpiece"):
            edition.prepare_tool(self.root, "fixture", "room")
        self.prepare_pilot()
        self.complete("pilot")
        with self.assertRaisesRegex(ValueError, "fresh layout-sample"):
            edition.review_pilot(self.root, "fixture", "coordinator", "Wrong sample: still shows reference.")
        self.sample("pilot")
        edition.review_pilot(self.root, "fixture", "coordinator", "The release has the required impact and state.")
        self.complete("room")
        # Finishing the reference set and changing the full preview do not erase
        # the already reviewed pilot layout or demand another generation.
        self.sample("room")
        edition.review_visuals(self.root, "fixture", "coordinator", "All selected references, cover and shared layout pass.")
        self.complete("later")
        edition.validate_edition(self.root, "fixture", "render")
        stats = production.statistics(self.manifest())
        self.assertEqual(stats["attempts"]["total"], 4)
        self.assertEqual(stats["attempts"]["recordedOutcomes"], {"accepted": 4})
        self.assertEqual(stats["timing"]["timedAttempts"], 4)
        self.assertNotIn("budget", stats)

    def test_source_state_and_selected_roles_survive_targeted_corrections(self):
        self.prepare_pilot()
        self.complete("pilot", accept=False)
        request = edition.prepare_tool(self.root, "fixture", "pilot", edit_last_rejected=True,
                                       references=["person"], correction="Remove the retaining pin. Preserve face and framing.", dry_run=True)
        self.assertIn("Pin absent. Six empty sockets.", request["prompt"])
        self.assertIn("source state controls", request["prompt"])
        self.assertNotIn("Approved story art direction", request["prompt"])
        self.assertEqual(len(request["referenced_image_paths"]), 2)

    def test_new_workflow_corrects_past_three_attempts_and_resumes_without_reset(self):
        self.prepare_pilot()
        for number in range(1, 5):
            self.complete("pilot", accept=False, correction="Reframe to remove misleading mechanism geometry." if number > 1 else "")
        before = (self.directory / "edition.json").read_bytes()
        request = edition.prepare_tool(self.root, "fixture", "pilot", correction="Use the state-correct composition.", dry_run=True)
        self.assertEqual(request["attempt"], 5)
        self.assertEqual((self.directory / "edition.json").read_bytes(), before)
        self.complete("pilot", correction="Use the state-correct composition.")
        pilot = edition._asset(self.manifest(), "pilot")
        self.assertEqual(pilot["attempts"], 5)
        self.assertEqual([entry["status"] for entry in pilot["attemptHistory"]], ["rejected"] * 4 + ["accepted"])

    def test_rejected_replacement_cannot_reuse_old_pilot_approval(self):
        self.finish_pilot()
        # The new sample changed the initial prerequisite layout; refresh that
        # assistant review before requesting a further pilot correction.
        edition.review_visuals(self.root, "fixture", "coordinator", "Current pilot references still pass.", pilot=True)
        self.complete("pilot", accept=False, correction="Correct the missed pin state.")
        with self.assertRaisesRegex(ValueError, "centerpiece"):
            edition.prepare_tool(self.root, "fixture", "room")
        with self.assertRaisesRegex(ValueError, "current centerpiece candidate"):
            edition.review_pilot(self.root, "fixture", "coordinator", "Do not accept older pixels.")

    def test_changed_state_and_role_invalidate_existing_image_inputs(self):
        self.finish_pilot()
        manifest = self.manifest()
        pilot = edition._asset(manifest, "pilot")
        for key, value in [("sceneState", "The pin is still inserted."), ("referenceRoles", {"person": "Clothing only."})]:
            changed = deepcopy(manifest)
            edition._asset(changed, "pilot")[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "stale"):
                edition._check_asset(self.root, changed, edition._asset(changed, "pilot"))

    def test_plan_rejects_unused_reference_missing_coverage_and_role(self):
        manifest = self.manifest()
        manifest["references"].append({**deepcopy(manifest["references"][0]), "id": "unused"})
        with self.assertRaisesRegex(ValueError, "unneeded references"):
            production.validate_policy(manifest, complete=True)
        manifest = self.manifest()
        manifest["illustrations"][0]["referenceRoles"] = {}
        with self.assertRaisesRegex(ValueError, "every input"):
            production.validate_policy(manifest, complete=True)
        self.plan.write_text("# Plan\n\n## Art direction\n\nInk.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Coverage"):
            edition.approve(self.root, "fixture", "plan", "Incomplete plan must not pass.")

    def test_custom_cover_dependencies_are_available_before_pilot(self):
        edition.configure_asset(self.root, "fixture", "cover-place", kind="location", prompt="One place.",
                                references=["source-cover"], reference_roles={"source-cover": "Style only."})
        edition.configure_asset(self.root, "fixture", "cover", kind="cover", prompt="New cover without lettering.",
                                references=["cover-place"], reference_roles={"cover-place": "Place geometry and style."})
        edition.approve(self.root, "fixture", "plan", "Approve the requested new cover and its necessary reference.")
        self.complete("cover-place")
        self.complete("cover")
        self.prepare_pilot()
        self.complete("pilot")

    def test_reference_dependencies_follow_the_centerpiece_then_reference_stage_order(self):
        manifest = self.manifest()
        later = edition._asset(manifest, "later")
        later.update(references=["person"], referenceRoles={"person": "Identity."})
        manifest["illustrations"].append({
            **deepcopy(later), "id": "finale", "references": ["room"],
            "referenceRoles": {"room": "Room geometry."},
        })
        # The graph stays acyclic and every reference has a downstream consumer,
        # but room cannot wait for a scene that requires full reference review.
        for transitive in (False, True):
            with self.subTest(transitive=transitive):
                changed = deepcopy(manifest)
                room = edition._asset(changed, "room")
                dependency = "later"
                if transitive:
                    changed["references"].append({
                        **deepcopy(room), "id": "room-state", "references": ["later"],
                        "referenceRoles": {"later": "Room state."},
                    })
                    dependency = "room-state"
                room.update(references=[dependency], referenceRoles={dependency: "Room geometry."})
                with self.assertRaisesRegex(ValueError, "non-centerpiece illustrations: later"):
                    production.validate_policy(changed, complete=True)
        # The accepted centerpiece exists before remaining reference development.
        room = edition._asset(manifest, "room")
        room.update(references=["pilot", "person"],
                    referenceRoles={"pilot": "Room state after the release.", "person": "Rendering style."})
        production.validate_policy(manifest, complete=True)

    def test_legacy_stats_are_read_only_and_preserve_unrecorded_history(self):
        manifest = self.manifest()
        manifest.pop("productionPolicy")
        manifest["retiredAssets"] = [{"id": "retired-pair", "kind": "character", "attempts": 7}]
        before = deepcopy(manifest)
        stats = production.statistics(manifest)
        self.assertEqual(stats["attempts"]["total"], 7)
        self.assertEqual(stats["attempts"]["withoutRecordedOutcome"], 7)
        self.assertIsNone(stats["timing"]["generationSeconds"])
        self.assertEqual(manifest, before)
        edition.save_edition(self.root, manifest)
        with self.assertRaisesRegex(ValueError, "user direction to migrate"):
            edition.configure_production(self.root, "fixture", "pilot")
        edition.configure_production(self.root, "fixture", "pilot", "Use the updated visual workflow for this edition.")
        self.assertEqual(production.statistics(self.manifest())["attempts"]["total"], 7)
        with self.assertRaisesRegex(ValueError, "stale"):
            edition._require_approval(self.root, self.manifest(), "plan")

    def test_failed_call_retains_one_attempt_and_blocks_old_reference_selection(self):
        self.finish_pilot()
        edition.prepare_tool(self.root, "fixture", "person", correction="Correct the clothing.")
        edition.resolve_generation(self.root, "fixture", "person", "failed", "Synthetic tool handle is terminal and failed.")
        manifest = self.manifest()
        with self.assertRaisesRegex(ValueError, "latest requested correction"):
            edition._check_asset(self.root, manifest, edition._asset(manifest, "person"))
        self.assertEqual(edition._asset(manifest, "person")["attempts"], 2)
        self.assertEqual(production.statistics(manifest)["attempts"]["recordedOutcomes"]["failed"], 1)


if __name__ == "__main__":
    unittest.main()
