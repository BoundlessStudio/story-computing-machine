"""Tests for the required, read-only GPT/Claude story review discussion."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import claude_story_review as review


def finding() -> dict:
    return {
        "location": "line 4",
        "evidence": "A short exact quote",
        "impact": "The listener cannot infer the answer.",
        "fix": "Supply the missing question.",
    }


def response(stage: str, verdict: str) -> dict:
    result = {"verdict": verdict, "findings": [] if verdict == "PASS" else [finding()], "notes": "Grounded review."}
    if stage == "prose":
        result.update(
            prompt="PASS",
            universe="PASS",
            internal="PASS",
            dialogue="PASS" if verdict == "PASS" else "REVISE",
            people=[],
            places=[],
        )
    return result


def discussion_response(stage: str, verdict: str) -> dict:
    kinds = ("promise", "causality", "knowledge_rules") if stage == "outline" else (
        "opening", "decisive", "final", "weakest_turn", "voice_pattern", "ending_effect")
    return {
        "verdict": verdict,
        "findings": [] if verdict == "PASS" else [finding()],
        "checks": {kind: {"location": "line 4", "evidence": "A short exact quote",
                          "assessment": "The exchange is grounded."} for kind in kinds},
        "notes": "Grounded discussion.",
    }


def quality_response(stage: str, final: dict, objections: list[dict] | None = None) -> dict:
    result = discussion_response(stage, final["verdict"])
    result["findings"] = final["findings"]
    result["resolutions"] = [
        {"id": objection["id"], "decision": "rejected",
         "evidence": "A causal plan." if stage == "outline" else "A short exact quote",
         "reason": "The exact source text resolves this provisional concern."}
        for objection in (objections or [])
    ]
    if stage == "prose":
        result.update({key: final[key] for key in ("prompt", "internal", "dialogue")})
    return result


def authority_response(stage: str, verdict: str) -> dict:
    result = {"verdict": verdict, "findings": [] if verdict == "PASS" else [finding()],
              "notes": "Authority checked."}
    if stage == "prose":
        result.update(universe=verdict, people=[], places=[])
    return result


def codex_events(result: dict) -> str:
    return "\n".join((
        json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(result)}}),
        json.dumps({"type": "turn.completed"}),
    ))


class ReviewRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "universe").mkdir()
        (self.root / "universe" / "README.md").write_text("# Universe\n", encoding="utf-8")
        (self.root / "stories").mkdir()
        (self.root / "stories" / "NAMES.md").write_text("# Names\n", encoding="utf-8")
        self.package = self.root / "stories" / "test-story"
        self.package.mkdir(parents=True)
        (self.package / "prompt.md").write_text("# Prompt\n\n> [WP] Test\n", encoding="utf-8")
        (self.package / "outline.md").write_text("# Outline\n\n## Story\n\nA causal plan.\n", encoding="utf-8")
        (self.package / "story.md").write_text(
            "---\ntitle: Test\nslug: test-story\ncreated: 2026-09-26\ncanon: false\n---\n\nA short exact quote.\n",
            encoding="utf-8",
        )

    def args(self, stage: str, **overrides) -> argparse.Namespace:
        values = dict(
            stage=stage,
            story="test-story",
            worktree=self.root,
            reference_image=[],
            comparison=[],
            pre_review="PASS",
            no_write=False,
            claude_command="claude",
            timeout=10,
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def conversation(self, result: dict, *, failure_at: int = 0, failure_message="CLI failed",
                     mutate=None, initial_discussion=None, model_usage=None,
                     authority_override=None, quality_override=None,
                     claude_initial_discussion=None, rejoinder_discussion=None):
        stage = "prose" if "prompt" in result else "outline"
        envelope = {
            "is_error": False,
            "modelUsage": {review.MODEL: {}} if model_usage is None else model_usage,
        }
        calls = 0

        def fake_run(*args, **kwargs):
            nonlocal calls
            calls += 1
            command = args[0]
            if calls in (1, 3):
                self.assertEqual(command[0], "codex")
                self.assertIn(review.CODEX_MODEL, command)
                self.assertIn("model_reasoning_effort=high", command)
                self.assertIn("--ephemeral", command)
                self.assertIn("read-only", command)
                output = codex_events(
                    initial_discussion if initial_discussion is not None and calls == 1 else
                    rejoinder_discussion if rejoinder_discussion is not None and calls == 3 else
                    discussion_response(stage, "PASS"))
            else:
                self.assertNotIn("ANTHROPIC_API_KEY", kwargs["env"])
                self.assertIn("--restricted", command)
                self.assertIn("--effort", command)
                self.assertIn("high", command)
                self.assertIn("--no-session-persistence", command)
                self.assertIn("Read,Glob,Grep", command)
                if calls == 2:
                    self.assertNotIn('"your_initial"', kwargs["input"])
                    self.assertNotIn('"gpt_initial"', kwargs["input"])
                    self.assertIn("Canon, policy, and names are a later final check", kwargs["input"])
                elif calls == 4:
                    self.assertIn("FINAL STORY-QUALITY verdict", kwargs["input"])
                    self.assertIn('"objections"', kwargs["input"])
                else:
                    self.assertIn("final authority check", kwargs["input"])
                self.assertNotIn(kwargs["input"], command)
                first = initial_discussion or discussion_response(stage, "PASS")
                claude_first = claude_initial_discussion or discussion_response(stage, "PASS")
                reply = rejoinder_discussion or discussion_response(stage, "PASS")
                objections = review.provisional_objections(("gpt_initial", first),
                                                            ("claude_initial", claude_first),
                                                            ("gpt_rejoinder", reply))
                structured = (claude_first if calls == 2 else
                              quality_override or quality_response(stage, result, objections) if calls == 4 else
                              authority_override or authority_response(stage, "PASS"))
                output = json.dumps({**envelope, "structured_output": structured})
            if mutate and calls == 5:
                mutate()
            return subprocess.CompletedProcess(command, 1 if calls == failure_at else 0,
                                               output, failure_message)

        return mock.patch.object(review.subprocess, "run", side_effect=fake_run)

    def test_outline_pass_is_hash_bound_and_writes_no_file(self):
        with mock.patch.dict(review.os.environ, {"ANTHROPIC_API_KEY": "test"}), self.conversation(response("outline", "PASS")):
            result = review.run(self.args("outline"))
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["source_sha256"], review.digest(self.package / "outline.md"))
        self.assertFalse((self.package / "review.md").exists())

    def test_story_first_packet_excludes_authority_and_prior_reviews(self):
        (self.package / "review.md").write_text("Verdict: PASS\nSECRET TARGET CRITIQUE\n", encoding="utf-8")
        other = self.root / "stories" / "other-story"
        other.mkdir()
        (other / "review.md").write_text(
            "Verdict: PASS\n## People\n| Noun | Status | Continuity note |\n"
            "| --- | --- | --- |\n| Mira | new | Inventor. |\n"
            "## Findings\nSECRET OTHER CRITIQUE\n", encoding="utf-8",
        )
        packet, hashes = review.codex_packet(
            self.root, "test-story", self.package / "story.md", self.package / "prompt.md", [], [],
        )
        self.assertIn("A short exact quote.", packet)
        self.assertNotIn("Mira", packet)
        self.assertNotIn("# Universe", packet)
        self.assertNotIn("SECRET TARGET CRITIQUE", packet)
        self.assertNotIn("SECRET OTHER CRITIQUE", packet)
        authority = review.final_authority_inputs(self.root, "test-story", [])
        self.assertIn(other / "review.md", authority)
        self.assertNotIn(self.package / "review.md", authority)
        review.verify_inputs(hashes)

    def test_claude_snapshots_read_files_without_prior_target_review(self):
        (self.package / "review.md").write_text("Verdict: PASS\nSECRET TARGET CRITIQUE\n", encoding="utf-8")
        other = self.root / "stories" / "other-story"
        other.mkdir()
        (other / "review.md").write_text(
            "Verdict: PASS\n## People\n| Noun | Status | Continuity note |\n"
            "| --- | --- | --- |\n| Mira | new | Inventor. |\n"
            "## Findings\nSECRET OTHER CRITIQUE\n", encoding="utf-8",
        )
        with tempfile.TemporaryDirectory() as temporary:
            quality = Path(temporary) / "quality"
            final = Path(temporary) / "final"
            quality_hashes = review.review_snapshot(
                self.root, quality, "test-story", self.package / "prompt.md",
                self.package / "story.md", final=False, comparisons=[], diagnostic="Dialogue check.\n",
            )
            final_hashes = review.review_snapshot(
                self.root, final, "test-story", self.package / "prompt.md",
                self.package / "story.md", final=True, comparisons=[], diagnostic="Dialogue check.\n",
            )
            self.assertFalse((quality / "universe").exists())
            self.assertFalse((quality / "stories" / "other-story").exists())
            self.assertFalse((final / "stories" / "test-story" / "review.md").exists())
            self.assertTrue((final / "universe" / "README.md").exists())
            inventory = (final / "stories" / "other-story" / "review.md").read_text(encoding="utf-8")
            self.assertIn("Mira", inventory)
            self.assertNotIn("SECRET OTHER CRITIQUE", inventory)
            review.verify_inputs(quality_hashes)
            review.verify_inputs(final_hashes)

    def test_comparison_cannot_expose_target_or_a_prior_review(self):
        (self.package / "review.md").write_text("Verdict: PASS\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Invalid comparison source"):
            review.run(self.args("prose", comparison=[str(self.package / "review.md")]))
        with self.assertRaisesRegex(ValueError, "Invalid comparison source"):
            review.run(self.args("prose", comparison=[str(self.package / "story.md")]))

    def test_prose_prompt_uses_dialogue_diagnostic_without_output_instructions(self):
        prompt = review.prompt_for("prose", "test-story", Path("stories/test-story/prompt.md"),
                                   Path("stories/test-story/story.md"), self.args("prose"))
        self.assertIn("The Setup-Delivery Contract", prompt)
        self.assertNotIn("## Output Persistence", prompt)

    def test_outline_revise_blocks_writer_handoff(self):
        with self.conversation(response("outline", "REVISE")):
            result = review.run(self.args("outline"))
        self.assertEqual(result["verdict"], "REVISE")
        self.assertFalse((self.package / "review.md").exists())
        with mock.patch.object(sys, "argv", ["runner", "--stage", "outline", "--story", "test-story", "--worktree", str(self.root)]):
            with self.conversation(response("outline", "REVISE")), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(review.main(), 2)

    def test_prose_pass_writes_only_review(self):
        original = (self.package / "story.md").read_bytes()
        with self.conversation(response("prose", "PASS")):
            result = review.run(self.args("prose"))
        rendered = (self.package / "review.md").read_text(encoding="utf-8")
        self.assertIn("Verdict: PASS", rendered)
        self.assertIn(f"Reviewed prose SHA-256: {result['source_sha256']}", rendered)
        self.assertEqual(result["source_sha256"], review.reviewed_digest(self.package / "story.md", "prose", True))
        self.assertEqual((self.package / "story.md").read_bytes(), original)

    def test_review_keeps_complete_claude_notes(self):
        result = response("prose", "PASS")
        result["notes"] = " ".join(["evidence"] * 85) + " Final qualification."
        rendered = review.review_markdown(result, "0" * 64)
        self.assertIn("Final qualification.", rendered)
        self.assertNotIn("evidence ...", rendered)

    def test_prose_hash_survives_canon_marker_promotion(self):
        source = self.package / "story.md"
        before = review.reviewed_digest(source, "prose", True)
        source.write_bytes(source.read_bytes().replace(b"canon: false", b"canon: true"))
        self.assertEqual(review.reviewed_digest(source, "prose", True), before)

    def test_locked_story_review_is_read_only(self):
        source = self.package / "story.md"
        source.write_bytes(source.read_bytes().replace(b"canon: false", b"canon: true"))
        with self.conversation(response("prose", "PASS")):
            with self.assertRaisesRegex(ValueError, "canon-locked"):
                review.run(self.args("prose"))
        self.assertFalse((self.package / "review.md").exists())

    def test_prose_revise_cannot_become_pass(self):
        with self.conversation(response("prose", "REVISE")):
            result = review.run(self.args("prose"))
        self.assertEqual(result["verdict"], "REVISE")
        self.assertIn("Verdict: REVISE", (self.package / "review.md").read_text(encoding="utf-8"))

    def test_claude_final_verdict_owns_a_disagreement(self):
        with self.conversation(response("prose", "PASS"),
                               initial_discussion=discussion_response("prose", "REVISE")):
            result = review.run(self.args("prose"))
        self.assertEqual(result["discussion"]["gpt_initial"]["verdict"], "REVISE")
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["discussion"]["claude_quality_final"]["resolutions"][0]["id"],
                         "gpt_initial:1")
        self.assertIn("Verdict: PASS", (self.package / "review.md").read_text(encoding="utf-8"))

    def test_unresolved_or_unsupported_disagreement_blocks_pass(self):
        initial = discussion_response("prose", "REVISE")
        missing = quality_response("prose", response("prose", "PASS"))
        with self.conversation(response("prose", "PASS"), initial_discussion=initial,
                               quality_override=missing):
            with self.assertRaisesRegex(ValueError, "resolve every provisional blocker"):
                review.run(self.args("prose"))
        unsupported = quality_response("prose", response("prose", "PASS"),
                                       [{"id": "gpt_initial:1"}])
        unsupported["resolutions"][0]["evidence"] = "an invented sentence"
        with self.conversation(response("prose", "PASS"), initial_discussion=initial,
                               quality_override=unsupported):
            with self.assertRaisesRegex(ValueError, "exact on-page evidence"):
                review.run(self.args("prose"))
        self.assertFalse((self.package / "review.md").exists())

    def test_every_rounds_objections_get_distinct_resolutions(self):
        revised = discussion_response("prose", "REVISE")
        with self.conversation(response("prose", "PASS"), initial_discussion=revised,
                               claude_initial_discussion=revised,
                               rejoinder_discussion=revised):
            result = review.run(self.args("prose"))
        self.assertEqual([row["id"] for row in result["discussion"]["claude_quality_final"]["resolutions"]],
                         ["gpt_initial:1", "claude_initial:1", "gpt_rejoinder:1"])

    def test_invalid_output_and_cli_failure_do_not_write(self):
        bad = response("prose", "PASS")
        bad["findings"] = [finding()]
        with self.conversation(bad):
            with self.assertRaisesRegex(ValueError, "disagree"):
                review.run(self.args("prose"))
        with self.conversation(response("prose", "PASS"), failure_at=5,
                               failure_message="Authentication required"):
            with self.assertRaisesRegex(RuntimeError, "Authentication required"):
                review.run(self.args("prose"))
        with self.conversation(response("prose", "PASS"), model_usage={"claude-other": {}}):
            with self.assertRaisesRegex(ValueError, "model identity"):
                review.run(self.args("prose"))
        self.assertFalse((self.package / "review.md").exists())

    def test_discussion_failure_blocks_final_verdict(self):
        with self.conversation(response("prose", "PASS"), failure_at=1):
            with self.assertRaisesRegex(RuntimeError, "GPT-6 Sol review failed"):
                review.run(self.args("prose"))
        bad = discussion_response("prose", "PASS")
        bad["findings"] = [finding()]
        with self.conversation(response("prose", "PASS"), initial_discussion=bad):
            with self.assertRaisesRegex(ValueError, "disagree"):
                review.run(self.args("prose"))
        self.assertFalse((self.package / "review.md").exists())

    def test_authority_can_add_a_blocker_without_erasing_quality(self):
        with self.conversation(response("prose", "PASS"),
                               authority_override=authority_response("prose", "REVISE")):
            result = review.run(self.args("prose"))
        self.assertEqual(result["verdict"], "REVISE")
        self.assertEqual(result["dialogue"], "PASS")
        self.assertEqual(result["universe"], "REVISE")
        self.assertEqual(len(result["findings"]), 1)

    def test_source_changed_during_review_does_not_write(self):
        def mutate():
            with (self.package / "story.md").open("a", encoding="utf-8") as handle:
                handle.write("Changed.\n")

        with self.conversation(response("prose", "PASS"), mutate=mutate):
            with self.assertRaisesRegex(RuntimeError, "changed during"):
                review.run(self.args("prose"))
        self.assertFalse((self.package / "review.md").exists())


if __name__ == "__main__":
    unittest.main()
