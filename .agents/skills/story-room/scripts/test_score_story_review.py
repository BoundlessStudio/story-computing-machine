import copy
import json
from pathlib import Path
import tempfile
import unittest

from score_story_review import body_hash, score


class FindingScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "story.md"
        self.source.write_text("The key is in the drawer.\n", encoding="utf-8")
        self.output = self.root / "review.json"
        self.pin = body_hash(self.source.read_bytes())
        self.rubric = {"stories": {"sample": {"split": "withheld", "preserve": [{"id": "good-joke"}],
                        "versions": {"original": {"source_sha256": self.pin, "expected_issues": ["key"]}}}}}
        self.runs = [{"id": "sample-original", "slug": "sample", "version": "original",
                      "source": str(self.source), "output": str(self.output)}]
        self.result = {"calibration_only": True, "source_sha256": self.pin, "quality_verdict": "PASS",
                       "discussion": {"claude_initial": {"observations": [{"evidence": "key"}]}},
                       "findings": [], "editorial": [{"evidence": "key"}]}

    def save(self):
        self.output.write_text(json.dumps(self.result), encoding="utf-8")

    def adjudication(self, arm, candidate, **changes):
        row = {"run": "sample-original", "arm": arm, "candidate": candidate, "issue": "key",
               "judgment": "supported", "repair": "useful", "reason": "Explains the same missing handoff.",
               "source_evidence": ["The key is in the drawer."], "damaged_control": None}
        return row | changes

    def test_same_pass_can_contain_a_detected_editorial_problem(self):
        self.save()
        result = score(self.rubric, self.runs, [self.adjudication("claude_alone", "observation:1"),
                                               self.adjudication("combined", "editorial:1")])
        self.assertEqual(len(result["arms"]["claude_alone"]["detected"]), 1)
        self.assertEqual(result["added_by_combination"], [])

    def test_lost_finding_and_harmful_false_alarm_are_counted(self):
        self.save()
        result = score(self.rubric, self.runs, [self.adjudication("claude_alone", "observation:1"),
                        self.adjudication("combined", "editorial:1", issue=None, judgment="false_alarm",
                                          repair="harmful", damaged_control="good-joke")])
        self.assertEqual(len(result["lost_in_combination"]), 1)
        self.assertEqual(result["arms"]["combined"]["false_alarms"], 1)
        self.assertEqual(result["arms"]["combined"]["preserve_damage"], 1)

    def test_verdict_does_not_earn_detection_credit(self):
        self.result["discussion"]["claude_initial"]["observations"] = []
        self.result["editorial"] = []
        self.result["quality_verdict"] = "REVISE"
        self.save()
        result = score(self.rubric, self.runs, [])
        self.assertEqual(result["arms"]["combined"]["detected"], [])
        self.assertEqual(len(result["arms"]["combined"]["missed"]), 1)

    def test_incomplete_adjudications_and_stale_sources_block(self):
        self.save()
        with self.assertRaisesRegex(ValueError, "Every candidate"):
            score(self.rubric, self.runs, [])
        self.source.write_text("Changed.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            score(self.rubric, self.runs, [])

    def test_repaired_and_teaching_cases_cannot_inflate_detection(self):
        self.save()
        self.rubric["stories"]["sample"]["versions"]["original"]["expected_issues"] = []
        with self.assertRaisesRegex(ValueError, "repaired or unknown"):
            score(self.rubric, self.runs, [self.adjudication("claude_alone", "observation:1")])
        self.rubric["stories"]["sample"]["split"] = "teaching"
        with self.assertRaisesRegex(ValueError, "Teaching"):
            score(self.rubric, self.runs, [])


if __name__ == "__main__":
    unittest.main()
