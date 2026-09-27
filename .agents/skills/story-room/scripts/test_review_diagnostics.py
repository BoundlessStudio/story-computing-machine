import copy
import unittest

from review_diagnostics import source_map, validate_diagnostic


SOURCE = 'At the station.\n\n"I locked it," Ada said.\n\nAt home, she locked it.\n'


def reading(role="editorial"):
    result = {"observations": [], "strengths": [{"evidence": ["At the station."], "reason": "Clear place."}],
              "notes": "No publication verdict.", "scenes": []}
    for start, end, quote in [(1, 4, "At the station."), (5, 5, "At home, she locked it.")]:
        result["scenes"].append({"start_line": start, "end_line": end, "scene": quote,
                                 "state_before": "Unlocked", "state_after": "Locked",
                                 "knowledge": "Ada observes the lock", "emotional_movement": "Relief",
                                 "evidence": quote})
    if role == "editorial":
        result["exchanges"] = [{"start_line": 3, "mode": "dialogue",
                                "setup": "At station", "literal_intent": "Claims completion",
                                "listener_uptake": "Believes lock is shut", "next_response": "Later lock action",
                                "assessment": "Test whether same lock"}]
        result["patterns"] = {key: {"evidence": ['"I locked it,"'], "assessment": "Too short for a pattern"}
                              for key in ("voice_under_pressure", "correction_routines", "ending_repetition")}
    return result


class CoverageTests(unittest.TestCase):
    def test_complete_reading_has_no_verdict(self):
        validate_diagnostic(reading(), "prose", "editorial", SOURCE)
        bad = reading()
        bad["verdict"] = "PASS"
        with self.assertRaisesRegex(ValueError, "invalid fields"):
            validate_diagnostic(bad, "prose", "editorial", SOURCE)

    def test_scene_gap_overlap_and_missing_end_block(self):
        for start, end in [(6, 5), (4, 5), (5, 4)]:
            with self.subTest(start=start, end=end):
                bad = reading()
                bad["scenes"][-1].update(start_line=start, end_line=end)
                with self.assertRaisesRegex(ValueError, "Scene coverage"):
                    validate_diagnostic(bad, "prose", "editorial", SOURCE)
        bad = reading()
        bad["scenes"].pop()
        with self.assertRaisesRegex(ValueError, "omits the end"):
            validate_diagnostic(bad, "prose", "editorial", SOURCE)

    def test_middle_dialogue_cannot_be_skipped_or_repeated(self):
        for exchanges in [[], reading()["exchanges"] * 2]:
            bad = reading()
            bad["exchanges"] = exchanges
            with self.assertRaisesRegex(ValueError, "omitted or repeated"):
                validate_diagnostic(bad, "prose", "editorial", SOURCE)

    def test_scene_quote_must_come_from_that_scene(self):
        bad = reading()
        bad["scenes"][-1]["evidence"] = "At the station."
        with self.assertRaisesRegex(ValueError, "exact source quote"):
            validate_diagnostic(bad, "prose", "editorial", SOURCE)

    def test_quoted_term_is_a_candidate_not_automatically_dialogue(self):
        self.assertEqual(len(source_map("She wasn't ready.\n\nHer \u2018plan\u2019 failed.\n")["quoted_passages"]), 1)
        bad = reading()
        bad["exchanges"][0]["mode"] = "quoted_text"
        validate_diagnostic(bad, "prose", "editorial", SOURCE)

    def test_separate_exact_excerpts_are_supported(self):
        value = reading()
        value["strengths"][0]["evidence"] = ["At the station.", '"I locked it,"']
        validate_diagnostic(value, "prose", "editorial", SOURCE)
        value["strengths"][0]["evidence"] = ['At the station. / "I locked it,"']
        with self.assertRaises(ValueError):
            validate_diagnostic(value, "prose", "editorial", SOURCE)

    def test_evidence_and_category_are_validated(self):
        for category, evidence in [("blocking", "At the station."), ("craft", "invented")]:
            bad = reading()
            bad["observations"] = [{"category": category, "evidence": [evidence], "location": "line 1",
                                     "impact": "Reader confusion", "fix": "Clarify"}]
            with self.assertRaises(ValueError):
                validate_diagnostic(bad, "prose", "editorial", SOURCE)


if __name__ == "__main__":
    unittest.main()
