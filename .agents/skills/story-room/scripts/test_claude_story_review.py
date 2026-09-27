"""Safety checks for the two independent, read-only model invocations."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import claude_story_review as review


READING = {"strengths": [{"location": "opening", "evidence": "A spark.",
                          "assessment": "The image establishes the promise."}],
           "concerns": [], "overall": "A promising draft."}


class ReviewRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / "stories" / "test-story"
        self.package.mkdir(parents=True)
        (self.package / "prompt.md").write_text("A spark.\n", encoding="utf-8")
        (self.package / "outline.md").write_text("A spark.\n", encoding="utf-8")
        (self.package / "story.md").write_text(
            "---\ncanon: false\n---\nA spark.\n", encoding="utf-8")

    def args(self, stage):
        return argparse.Namespace(stage=stage, story="test-story", worktree=self.root,
                                  reference_image=[], claude_command="claude",
                                  codex_command="codex", timeout=10)

    def test_both_stages_return_readings_and_exact_hash_without_writing(self):
        with mock.patch.object(review, "claude_read", return_value=READING) as claude, \
             mock.patch.object(review, "sol_read", return_value=READING) as sol:
            for stage in ("outline", "prose"):
                result = review.run(self.args(stage))
                source = self.package / ("outline.md" if stage == "outline" else "story.md")
                expected = (source.read_bytes() if stage == "outline" else
                            source.read_bytes().split(b"---\r\n", 2)[-1])
                self.assertEqual(result["source_sha256"], hashlib.sha256(expected).hexdigest())
                self.assertEqual(result["claude"], READING)
                self.assertEqual(result["sol"], READING)
                self.assertNotIn("verdict", result)
            self.assertEqual(claude.call_count, 2)
            self.assertEqual(sol.call_count, 2)
        self.assertFalse((self.package / "review.md").exists())

    def test_changed_source_blocks_second_reading(self):
        def mutate(*args):
            (self.package / "outline.md").write_text("Changed.\n", encoding="utf-8")
            return READING
        with mock.patch.object(review, "claude_read", side_effect=mutate), \
             mock.patch.object(review, "sol_read") as sol:
            with self.assertRaisesRegex(RuntimeError, "changed"):
                review.run(self.args("outline"))
            sol.assert_not_called()

    def test_malformed_reading_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid reading"):
            review.validate_reading({"verdict": "PASS"}, "Claude")
        broken = {**READING, "concerns": [{"severity": "substantial"}]}
        with self.assertRaisesRegex(ValueError, "incomplete concerns"):
            review.validate_reading(broken, "Sol")

    def test_claude_authentication_and_model_failure_blocks(self):
        response = subprocess.CompletedProcess([], 0, json.dumps({
            "is_error": True, "structured_output": READING, "modelUsage": {}
        }), "")
        with mock.patch.object(review.subprocess, "run", return_value=response):
            with self.assertRaisesRegex(ValueError, "identity or authentication"):
                review.claude_read(self.package / "prompt.md", self.package / "outline.md",
                                   [], "outline", "claude", 10)

    def test_claude_child_does_not_inherit_api_key(self):
        response = subprocess.CompletedProcess([], 0, json.dumps({
            "is_error": False, "structured_output": READING,
            "modelUsage": {review.CLAUDE_MODEL: {}}
        }), "")
        with mock.patch.dict(review.os.environ, {"ANTHROPIC_API_KEY": "secret"}), \
             mock.patch.object(review.subprocess, "run", return_value=response) as command:
            review.claude_read(self.package / "prompt.md", self.package / "outline.md",
                               [], "outline", "claude", 10)
            self.assertNotIn("ANTHROPIC_API_KEY", command.call_args.kwargs["env"])

    def test_sol_failure_blocks_without_recording_a_verdict(self):
        response = subprocess.CompletedProcess([], 1, "", "authentication unavailable")
        with mock.patch.object(review.subprocess, "run", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "GPT-6 Sol failed"):
                review.sol_read(self.package / "prompt.md", self.package / "outline.md",
                                [], "outline", 10, "codex")


if __name__ == "__main__":
    unittest.main()
