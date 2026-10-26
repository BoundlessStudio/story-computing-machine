#!/usr/bin/env python3
"""Behavior tests for fidelity inputs and proceed/restart/ask decisions; no API calls."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import fidelity_checkpoint as checkpoint


def result_for(bundle, honors=True, confidence=0.95, ambiguity=0.0, probability_yes=None):
    yes = (0.95 if honors else 0.05) if probability_yes is None else probability_yes
    return {"model": "gpt-6-luna", "answers": [
        {"type": "choice", "name": "honors_request", "choice": honors, "confidence": confidence,
         "probabilities": [{"value": True, "probability": yes}, {"value": False, "probability": 1-yes}]},
        {"type": "predicate", "name": "source_ambiguity", "probability": ambiguity},
    ]}


class FidelityCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
        self.temporary = tempfile.TemporaryDirectory(prefix="fidelity-test-", dir=self.root / "tmp")
        self.addCleanup(self.temporary.cleanup)
        self.story = Path(self.temporary.name)
        self.prompt = "[WP] A clockmaker opens the sea.\n\nLater direction: the sea stays open.\n\n## Supplied reference images\n- None\n"
        (self.story / "prompt.md").write_text(self.prompt, encoding="utf-8")
        (self.story / "outline.md").write_text("She opens the sea, chooses a route, and leaves it open.", encoding="utf-8")
        (self.story / "story.md").write_text("---\ncanon: false\n---\nShe opened the sea. It stayed open.", encoding="utf-8")
        self.bundle = checkpoint.build_bundle(self.story, "outline")

    def inventory(self, *names):
        value = "\n".join(f"- `{name}`" for name in names) if names else "- None"
        (self.story / "prompt.md").write_text(self.prompt.replace("- None", value), encoding="utf-8")

    def test_complete_prompt_and_target_are_preserved_without_editorial_history(self):
        parts = self.bundle["request"]["input"][1]["content"]
        self.assertTrue(parts[0]["text"].endswith(self.prompt))
        self.assertTrue(parts[-1]["text"].endswith((self.story / "outline.md").read_text()))
        (self.story / "notes.md").write_text("Biased praise: give this four points.")
        self.assertNotIn("Biased praise", json.dumps(checkpoint.build_bundle(self.story, "final")))
        self.assertNotIn("chooses a route", json.dumps(checkpoint.build_bundle(self.story, "final")))

    def test_all_original_images_are_labelled_and_attached(self):
        references = self.story / "art/references"
        references.mkdir(parents=True)
        (references / "character one.png").write_bytes(b"first original")
        (references / "place.webp").write_bytes(b"second original")
        self.inventory("character one.png", "place.webp")
        bundle = checkpoint.build_bundle(self.story, "outline")
        self.assertEqual([r["name"] for r in bundle["reference_images"]], ["character one.png", "place.webp"])
        images = [p for p in bundle["request"]["input"][1]["content"] if p["type"] == "input_image"]
        self.assertEqual(len(images), 2)
        self.assertEqual({Path(p["image_path"]).read_bytes() for p in images}, {b"first original", b"second original"})
        self.assertTrue(all(p["detail"] == "original" for p in images))
        self.assertEqual({q["name"] for q in bundle["request"]["questions"]}, {"honors_request", "source_ambiguity"})

    def test_text_only_checkpoint_uses_one_boolean_decision_and_ambiguity_check(self):
        questions = self.bundle["request"]["questions"]
        self.assertEqual([(q["name"],q["type"]) for q in questions], [("honors_request","choice"),("source_ambiguity","predicate")])
        self.assertEqual([c["value"] for c in questions[0]["choices"]],[True,False])
        result = checkpoint.assess_response(self.bundle,result_for(self.bundle))
        self.assertIs(result["honors_request"],True)
        self.assertNotIn("score",result)


    def test_point_eight_is_an_inclusive_confidence_boundary(self):
        result=checkpoint.assess_response(self.bundle,result_for(self.bundle,confidence=.8))
        self.assertEqual(result["action"],"proceed")
        self.assertEqual(result["confidence"],.8)
        self.assertEqual(checkpoint.assess_response(self.bundle,result_for(self.bundle,honors=False,confidence=.8))["action"],"restart_outline")


    def test_confident_no_outline_restarts_the_outline(self):
        result=checkpoint.assess_response(self.bundle,result_for(self.bundle,honors=False))
        self.assertEqual(result["action"],"restart_outline")


    def test_confident_no_final_restarts_the_story(self):
        bundle=checkpoint.build_bundle(self.story,"final")
        self.assertEqual(checkpoint.assess_response(bundle,result_for(bundle,honors=False))["action"],"restart_story")


    def test_low_confidence_overrides_both_yes_and_no(self):
        for honors in (True,False):
            result=checkpoint.assess_response(self.bundle,result_for(self.bundle,honors=honors,confidence=.79))
            self.assertEqual(result["action"],"ask_user")
            self.assertTrue(result["question"])


    def test_failed_third_attempt_asks_user_but_a_successful_one_can_proceed(self):
        for restarts, expected in ((0, "restart_outline"), (1, "restart_outline"), (2, "ask_user")):
            with self.subTest(restarts=restarts):
                self.assertEqual(checkpoint.assess_response(self.bundle, result_for(self.bundle, honors=False), restarts)["action"], expected)
        self.assertEqual(checkpoint.assess_response(self.bundle, result_for(self.bundle), 2)["action"], "proceed")

    def test_image_request_and_any_material_no_cannot_be_averaged_into_yes(self):
        references=self.story/"art/references"
        references.mkdir(parents=True)
        (references/"original.png").write_bytes(b"original")
        self.inventory("original.png")
        bundle=checkpoint.build_bundle(self.story,"final")
        self.assertEqual(len([q for q in bundle["request"]["questions"] if q["type"]=="choice"]),1)
        self.assertEqual(checkpoint.assess_response(bundle,result_for(bundle,honors=False))["action"],"restart_story")


    def test_ambiguous_request_asks_user_for_yes_and_no(self):
        for honors in (True,False):
            for ambiguity in (.21,1):
                self.assertEqual(checkpoint.assess_response(self.bundle,result_for(self.bundle,honors=honors,ambiguity=ambiguity))["action"],"ask_user")
        self.assertEqual(checkpoint.assess_response(self.bundle,result_for(self.bundle,ambiguity=.2))["action"],"proceed")


    def test_conflicting_reader_evidence_or_selected_answer_asks_user(self):
        self.assertEqual(checkpoint.assess_response(self.bundle,result_for(self.bundle),conflict="The reader cites a required ending contradicted by the text.")["action"],"ask_user")
        for yes in (.4,.5):
            self.assertEqual(checkpoint.assess_response(self.bundle,result_for(self.bundle,probability_yes=yes))["action"],"ask_user")


    def test_refused_missing_duplicate_and_wrong_type_answers_ask_user(self):
        complete=result_for(self.bundle)
        variants=[copy.deepcopy(complete) for _ in range(4)]
        variants[0]["answers"][0]={"type":"refusal","name":"honors_request"}
        variants[1]["answers"].pop()
        variants[2]["answers"][1]=variants[2]["answers"][0]
        variants[3]["answers"][0]["type"]="score"
        for response in variants:
            self.assertEqual(checkpoint.assess_response(self.bundle,response)["action"],"ask_user")


    def test_nonfinite_values_invalid_booleans_and_bad_distributions_cannot_pass(self):
        for field,value in (("confidence",float("nan")),("confidence",True),("confidence",1.01),("choice","true"),("choice",1)):
            response=result_for(self.bundle)
            response["answers"][0][field]=value
            self.assertEqual(checkpoint.assess_response(self.bundle,response)["action"],"ask_user")
        for mutation in ("duplicate","string","integer","sum","missing"):
            response=result_for(self.bundle)
            ps=response["answers"][0]["probabilities"]
            if mutation=="duplicate": ps[1]["value"]=True
            elif mutation=="string": ps[0]["value"]="true"
            elif mutation=="integer": ps[0]["value"]=1
            elif mutation=="sum": ps[0]["probability"]=.1
            else: ps.pop()
            self.assertEqual(checkpoint.assess_response(self.bundle,response)["action"],"ask_user")


    def test_api_and_mcp_errors_ask_user_and_mcp_success_can_be_unwrapped(self):
        for response in ({"error": {"code": "missing_api_key"}}, {"isError": True, "structuredContent": {"error": {"code": "api_error"}}}):
            self.assertEqual(checkpoint.assess_response(self.bundle, response)["action"], "ask_user")
        wrapped = {"isError": False, "structuredContent": result_for(self.bundle)}
        self.assertEqual(checkpoint.assess_response(self.bundle, wrapped)["action"], "proceed")

    def test_choice_distribution_and_distinct_native_confidence_are_preserved(self):
        response=result_for(self.bundle,confidence=.85,probability_yes=.98)
        result=checkpoint.assess_response(self.bundle,response)
        self.assertEqual(result["answer"],response["answers"][0])
        self.assertEqual(result["confidence"],.85)
        self.assertEqual(result["probability_yes"],.98)

    def test_legacy_score_bundle_cannot_be_reused(self):
        bundle=copy.deepcopy(self.bundle)
        bundle["request"]["questions"][0]["type"]="score"
        self.assertEqual(checkpoint.assess_response(bundle,result_for(self.bundle))["action"],"ask_user")

    def test_earlier_boolean_rubric_cannot_be_reused_for_wp_focused_gate(self):
        bundle=copy.deepcopy(self.bundle)
        bundle["rubric_version"]="honors-request-binary-v1"
        self.assertEqual(checkpoint.assess_response(bundle,result_for(self.bundle))["action"],"ask_user")

    def test_named_continuity_text_is_supplied_and_changes_invalidate_bundle(self):
        subprocess.run(["git","init","-q",str(self.story)],check=True)
        previous=self.story/"stories/previous"
        previous.mkdir(parents=True)
        source=previous/"story.md"
        source.write_text("The prior protagonist is a clockmaker.",encoding="utf-8")
        with (self.story/"prompt.md").open("a",encoding="utf-8") as stream:
            stream.write("\n## Continuation\nContinue stories/previous/story.md.\n")
        bundle=checkpoint.build_bundle(self.story,"outline")
        self.assertEqual(len(bundle["text_references"]),1)
        self.assertIn("The prior protagonist is a clockmaker.",json.dumps(bundle["request"]))
        checkpoint.validate_current_sources(bundle)
        source.write_text("The prior protagonist changed.",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"continuity text changed"):
            checkpoint.validate_current_sources(bundle)

    def test_missing_named_continuity_text_cannot_be_guessed(self):
        with (self.story/"prompt.md").open("a",encoding="utf-8") as stream:
            stream.write("\n## Continuation\nContinue stories/missing/story.md.\n")
        with self.assertRaisesRegex(ValueError,"story text is unavailable"):
            checkpoint.build_bundle(self.story,"final")


    def test_output_cannot_be_written_into_the_story_package(self):
        with self.assertRaises(ValueError):
            checkpoint.output_path(self.root / "stories/unwanted-checkpoint.json", self.story)
        self.assertEqual(checkpoint.output_path(self.story / "bundle.json", self.story), self.story / "bundle.json")

    def test_existing_checkpoint_files_are_not_overwritten(self):
        target = self.story / "bundle.json"
        checkpoint.write_json(target, self.bundle)
        with self.assertRaises(FileExistsError):
            checkpoint.write_json(target, {})

    def test_named_missing_and_unlisted_originals_are_rejected_before_scoring(self):
        references = self.story / "art/references"
        references.mkdir(parents=True)
        (references / "first.png").write_bytes(b"first")
        self.inventory("first.png", "missing.png")
        with self.assertRaisesRegex(ValueError, "missing originals"):
            checkpoint.build_bundle(self.story, "outline")
        self.inventory()
        with self.assertRaisesRegex(ValueError, "unlisted files"):
            checkpoint.build_bundle(self.story, "outline")

    def test_reference_inventory_is_explicit_and_unambiguous(self):
        for prompt in ("No inventory section", "## Supplied reference images\n", "## Supplied reference images\n- `a.png`\n- `a.png`\n", "## Supplied reference images\n- None\n## Supplied reference images\n- None\n"):
            with self.subTest(prompt=prompt), self.assertRaises(ValueError):
                checkpoint.reference_inventory(prompt)

    def test_persisted_counts_cannot_be_reset_with_a_new_output_or_zero_argument(self):
        for expected_used in (0, 1):
            state_file, state, used = checkpoint.restart_state(self.bundle, 0)
            self.assertEqual(used, expected_used)
            decision = checkpoint.assess_response(self.bundle, result_for(self.bundle, honors=False), used)
            self.assertEqual(decision["action"], "restart_outline")
            checkpoint.record_restart_state(state_file, state, decision, self.story / f"different-output-{expected_used}/decision.json")
        state_file, state, used = checkpoint.restart_state(self.bundle, 0)
        self.assertEqual(used, 2)
        decision = checkpoint.assess_response(self.bundle, result_for(self.bundle, honors=False), used)
        self.assertEqual(decision["action"], "ask_user")
        checkpoint.record_restart_state(state_file, state, decision, self.story / "last/decision.json")

    def test_user_direction_renews_a_halted_budget_once_and_must_be_recorded(self):
        state_file, state, used = checkpoint.restart_state(self.bundle, 2)
        halted = checkpoint.assess_response(self.bundle, result_for(self.bundle, honors=False), used)
        checkpoint.record_restart_state(state_file, state, halted, self.story / "halted.json")
        direction = "Make the clockmaker open the sea with a different mechanism."
        direction_file = self.story / "user-direction.txt"
        direction_file.write_text(direction, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Record the user's exact"):
            checkpoint.restart_state(self.bundle, 0, direction_file)
        with (self.story / "prompt.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Later user direction\n" + direction + "\n")
        with self.assertRaisesRegex(ValueError, "saved request is stale"):
            checkpoint.restart_state(self.bundle, 0, direction_file)
        updated_bundle = checkpoint.build_bundle(self.story, "outline")
        state_file, state, used = checkpoint.restart_state(updated_bundle, 0, direction_file)
        self.assertEqual(used, 0)
        decision = checkpoint.assess_response(updated_bundle, result_for(updated_bundle, honors=False), used)
        checkpoint.record_restart_state(state_file, state, decision, self.story / "renewed.json")
        self.assertEqual(checkpoint.restart_state(updated_bundle, 0, direction_file)[2], 1)

    def test_corrupt_restart_state_cannot_silently_reset_the_limit(self):
        state_file, _, _ = checkpoint.restart_state(self.bundle, 0)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "restart state is invalid"):
            checkpoint.restart_state(self.bundle, 0)

    def test_uncertain_result_blocks_resampling_and_the_other_stage_until_user_answers(self):
        state_file, state, used = checkpoint.restart_state(self.bundle, 0)
        halted = checkpoint.assess_response(self.bundle, result_for(self.bundle, confidence=0.4), used)
        checkpoint.record_restart_state(state_file, state, halted, self.story / "uncertain.json")
        for bundle in (self.bundle, checkpoint.build_bundle(self.story, "final")):
            with self.subTest(stage=bundle["stage"]), self.assertRaisesRegex(ValueError, "halted awaiting"):
                checkpoint.restart_state(bundle, 0)

    def test_operational_user_reply_resumes_without_renewing_restart_budget(self):
        state_file, state, used = checkpoint.restart_state(self.bundle, 1)
        halted = checkpoint.assess_response(self.bundle, result_for(self.bundle, confidence=0.4), used)
        checkpoint.record_restart_state(state_file, state, halted, self.story / "uncertain.json")
        reply = "API access is restored; retry this checkpoint."
        (self.story / "notes.md").write_text(reply, encoding="utf-8")
        reply_file = self.story / "reply.txt"
        reply_file.write_text(reply, encoding="utf-8")
        self.assertEqual(checkpoint.restart_state(self.bundle, 0, reply_file)[2], 1)

    def test_changed_candidate_or_reference_cannot_use_an_old_result(self):
        (self.story / "outline.md").write_text("An entirely different outline.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outline or story changed"):
            checkpoint.restart_state(self.bundle, 0)
        references = self.story / "art/references"
        references.mkdir(parents=True)
        image = references / "original.png"
        image.write_bytes(b"original pixels")
        self.inventory("original.png")
        bundle = checkpoint.build_bundle(self.story, "outline")
        image.write_bytes(b"replacement pixels")
        with self.assertRaisesRegex(ValueError, "reference original original.png changed"):
            checkpoint.restart_state(bundle, 0)

    def test_final_user_ruling_can_return_to_outline_without_regrading_stale_prose(self):
        final = checkpoint.build_bundle(self.story, "final")
        state_file, state, used = checkpoint.restart_state(final, 2)
        halted = checkpoint.assess_response(final, result_for(final, honors=False), used)
        checkpoint.record_restart_state(state_file, state, halted, self.story / "final-halted.json")
        direction = "Choose a new mechanism for opening the sea."
        reply_file = self.story / "new-direction.txt"
        reply_file.write_text(direction, encoding="utf-8")
        with (self.story / "prompt.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Later user direction\n" + direction + "\n")
        outline = checkpoint.build_bundle(self.story, "outline")
        _, resumed, used = checkpoint.restart_state(outline, 0, reply_file)
        self.assertEqual(used, 0)
        self.assertEqual(resumed["final"]["last_action"], "user_answered")
        self.assertEqual(resumed["final"]["minimum_restarts"], 0)

    def test_same_user_reply_cannot_resume_a_later_halt_at_the_other_stage(self):
        state_file, state, used = checkpoint.restart_state(self.bundle, 0)
        halted = checkpoint.assess_response(self.bundle, result_for(self.bundle, confidence=0.4), used)
        checkpoint.record_restart_state(state_file, state, halted, self.story / "outline-halted.json")
        direction = "Keep the sea open through the final scene."
        reply_file = self.story / "reply.txt"
        reply_file.write_text(direction, encoding="utf-8")
        with (self.story / "prompt.md").open("a", encoding="utf-8") as stream:
            stream.write("\n## Later user direction\n" + direction + "\n")
        outline = checkpoint.build_bundle(self.story, "outline")
        state_file, state, used = checkpoint.restart_state(outline, 0, reply_file)
        passed = checkpoint.assess_response(outline, result_for(outline), used)
        checkpoint.record_restart_state(state_file, state, passed, self.story / "outline-passed.json")
        final = checkpoint.build_bundle(self.story, "final")
        state_file, state, used = checkpoint.restart_state(final, 0)
        halted = checkpoint.assess_response(final, result_for(final, confidence=0.4), used)
        checkpoint.record_restart_state(state_file, state, halted, self.story / "final-halted.json")
        with self.assertRaisesRegex(ValueError, "halted awaiting"):
            checkpoint.restart_state(final, 0, reply_file)

    def test_reference_cannot_be_removed_from_the_request_but_left_in_metadata(self):
        references = self.story / "art/references"
        references.mkdir(parents=True)
        (references / "original.png").write_bytes(b"original")
        self.inventory("original.png")
        bundle = checkpoint.build_bundle(self.story, "outline")
        parts = bundle["request"]["input"][1]["content"]
        parts[:] = [part for part in parts if part["type"] != "input_image"]
        with self.assertRaisesRegex(ValueError, "include every inventoried"):
            checkpoint.validate_current_sources(bundle)

    def test_preparation_failure_persists_halt_before_another_stage_can_run(self):
        (self.story / "outline.md").unlink()
        completed = subprocess.run([sys.executable, str(Path(checkpoint.__file__)), "run", "--story-dir", str(self.story), "--stage", "outline", "--restarts", "0", "--output-dir", str(self.story / "failed-run")], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 20)
        self.assertEqual(json.loads(completed.stdout)["action"], "ask_user")
        with self.assertRaisesRegex(ValueError, "halted awaiting"):
            checkpoint.restart_state(checkpoint.build_bundle(self.story, "final"), 0)

    def test_invalid_stage_budget_blocks_both_stages_without_resetting_it(self):
        state_file, state, _ = checkpoint.restart_state(self.bundle, 0)
        state["outline"]["minimum_restarts"] = -1
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(state), encoding="utf-8")
        for bundle in (self.bundle, checkpoint.build_bundle(self.story, "final")):
            with self.assertRaisesRegex(ValueError, "restart state is invalid"):
                checkpoint.restart_state(bundle, 0)
        with self.assertRaises(ValueError):
            checkpoint.record_input_halt(self.story, "final", 0, checkpoint.ask_user("final", ["Invalid input"]))
        self.assertEqual(json.loads(state_file.read_text())["outline"]["minimum_restarts"], -1)


if __name__ == "__main__":
    unittest.main()
