#!/usr/bin/env python3
"""Behavior tests for the prose profile diagnostic."""

import unittest

import prose_profile as pp

STACCATO = """---
title: "T"
created: 2026-01-01
canon: false
---

# T

She opened the door. The room was dark. Nobody was there.

“Hello?”

“Here.”

“Where?”

“Here.”

***

He stood up. He looked at her. That was all.
"""

VOICED = """The kitchen smelled of scorched milk and of the dog, who had been asleep against the stove since before anyone living could remember and who lifted one ear, not the head, when she came in with the rain still on her coat.

“Now you'll sit,” said her aunt, “and you'll not say a word about the roof until you have eaten something, because I have had the roof from your uncle since Tuesday and from the priest since Wednesday and I will not have it from you.”

“It's only that—”

“Sit.”
"""

AVOIDED = """She came in from the yard.

“He found me,” she said.

“Who?”

“The king.” She sat down. He meant the old one.

“I know.”

“I wanted to tell you, but I—”

“I know.”

She did not answer. For a while neither of them spoke.

“I haven't asked properly. I didn't mean—”

“Their hands,” he said.
"""


class ProseProfileTests(unittest.TestCase):
    def test_frontmatter_headings_and_breaks_are_not_prose(self):
        p = pp.profile(STACCATO)
        self.assertEqual(p["scenes"], 2)
        self.assertNotIn("canon", " ".join(p["recurring_capitalized_names"]).lower())
        self.assertEqual(p["words"], 25)

    def test_staccato_draft_is_flagged(self):
        p = pp.profile(STACCATO)
        self.assertLessEqual(p["narration_sentence_mean"], 5)
        self.assertEqual(p["speeches_40_words_or_more"], 0)
        self.assertEqual(p["speeches_5_words_or_fewer"], 1.0)
        self.assertEqual(p["mannerisms"].get("that was all"), 1)
        notes = " ".join(pp.observations(p))
        self.assertIn("short and even", notes)
        self.assertIn("five words or fewer", notes)

    def test_voiced_draft_measures_range_and_senses(self):
        p = pp.profile(VOICED)
        self.assertGreaterEqual(p["longest_sentence"], 30)
        self.assertEqual(p["speeches_40_words_or_more"], 1)
        self.assertGreater(p["sense_words_per_1000"]["smell"], 0)
        self.assertNotIn("short and even", " ".join(pp.observations(p)))

    def test_speech_is_excluded_from_narration_rhythm(self):
        p = pp.profile("“No.” “Yes.” “No.” She crossed the whole length of the yard before she let herself look back at the house.\n")
        self.assertEqual(p["narration_sentence_mean"], 17)

    def test_reopened_speech_matches_a_single_paragraph_turn(self):
        lines = [
            "Ask Ada. She said nothing.",
            "At noon Ada took down the bell and I went out to find another length of rope in the shed.",
            "On Sunday Ada put it up again with both hands as if the whole tower already belonged to her.",
            "Who?",
        ]
        for opening, closing in (("“", "”"), ('"', '"')):
            with self.subTest(opening=opening):
                lead = "Two bells rang.\n\n"
                single = pp.profile(lead + opening + " ".join(lines) + closing)
                spread = pp.profile(lead + "\n\n".join(opening + line for line in lines) + closing)
                expected = {
                    "speech_count": 1,
                    "longest_speech": 45,
                    "speeches_40_words_or_more": 1,
                    "dialogue_share_of_words": round(45 / 48, 3),
                    "narration_sentence_mean": 3,
                    "narrated_non_answers": 0,
                    "recurring_capitalized_names": [],
                    "one_or_two_word_spoken_questions": 0,
                    "pointing_lines": [],
                }
                for key, value in expected.items():
                    self.assertEqual(single[key], value, key)
                    self.assertEqual(spread[key], single[key], key)
                self.assertEqual(single["paragraph_mean"], 24)
                self.assertEqual(spread["paragraph_mean"], 9.6)
                self.assertEqual(spread["paragraphs_12_words_or_fewer"], 0.6)

    def test_eight_short_paragraphs_can_be_one_turn_or_an_exchange(self):
        lines = ["One more.", "Again?"] * 4
        continued = pp.profile("\n\n".join("“" + line for line in lines) + "”")
        exchange = pp.profile("\n\n".join(f"“{line}”" for line in lines))
        self.assertEqual(continued["longest_run_of_short_paragraphs"], 8)
        self.assertEqual(continued["longest_speech"], 12)
        self.assertLessEqual(continued["longest_run_of_bare_exchange"], 1)
        self.assertEqual(exchange["speech_count"], 8)
        self.assertEqual(exchange["longest_run_of_bare_exchange"], 8)

    def test_tag_and_action_stay_outside_a_continued_speech(self):
        for opening, closing in (("“", "”"), ('"', '"')):
            for greeting, beat in (("Here,", "she said."), ("Here.", "She tipped the tray.")):
                with self.subTest(opening=opening, beat=beat):
                    text = "\n\n".join([
                        f"{opening}{greeting}{closing} {beat} {opening}The red cup is yours.",
                        f"{opening}The blue one—{closing}",
                        f"{opening}Which?{closing}",
                        f"{opening}I know.{closing}",
                    ])
                    p = pp.profile(text)
                    narration_words = len(beat.split())
                    self.assertEqual(p["narration_sentence_mean"], narration_words)
                    self.assertEqual(p["dialogue_share_of_words"], round(12 / (12 + narration_words), 3))
                    self.assertEqual(p["speech_count"], 3)
                    self.assertEqual(p["longest_speech"], 9)
                    self.assertEqual(p["cut_off_lines"], 1)
                    self.assertEqual(p["one_or_two_word_spoken_questions"], 1)
                    self.assertEqual(p["i_know_turns"], 1)

    def test_abandoned_opener_does_not_reach_a_later_turn(self):
        for opening, closing in (("“", "”"), ('"', '"')):
            for boundary in ("***", "She said nothing."):
                with self.subTest(opening=opening, boundary=boundary):
                    text = f"Unfinished chalk marks.\n\n{boundary}\n\n{opening}Who?{closing}"
                    plain = pp.profile(text)
                    abandoned = pp.profile(opening + text)
                    self.assertEqual(abandoned["speech_count"], 1)
                    self.assertEqual(abandoned["longest_speech"], 1)
                    self.assertEqual(abandoned["dialogue_share_of_words"], plain["dialogue_share_of_words"])
                    self.assertEqual(abandoned["narration_sentence_mean"], plain["narration_sentence_mean"])
                    self.assertEqual(abandoned["narrated_non_answers"], plain["narrated_non_answers"])
                    self.assertEqual(abandoned["pointing_lines"], ["Who?"])

    def test_unquoted_signing_keeps_zero_quoted_words(self):
        passage = "She signed the question with both hands. Her brother signed back across the kitchen table."
        p = pp.profile("\n\n".join([passage] * 100))
        self.assertGreaterEqual(p["words"], 1500)
        self.assertEqual(p["speech_count"], 0)
        self.assertEqual(p["dialogue_share_of_words"], 0)
        self.assertNotIn("central conversation happens aloud", " ".join(pp.observations(p)).lower())

    def test_avoided_talk_is_counted_and_listed(self):
        p = pp.profile(AVOIDED)
        self.assertEqual(p["i_know_turns"], 2)
        self.assertEqual(p["bare_acknowledgements"], 2)
        self.assertEqual(p["cut_off_lines"], 2)
        self.assertEqual(p["narrated_non_answers"], 2)
        self.assertEqual(p["narrator_glosses"], 1)
        self.assertIn("He found me,", p["pointing_lines"])
        self.assertIn("Their hands,", p["pointing_lines"])
        self.assertNotIn("I know.", p["pointing_lines"])
        notes = " ".join(pp.observations(p))
        self.assertIn("bare acknowledgement", notes)
        self.assertIn("did not or could not answer", notes)
        self.assertIn("cut off with a dash", notes)
        self.assertIn("listener's side", notes)
        self.assertIn("explains what a spoken line meant", notes)
        self.assertIn("“Their hands,”", pp.render(p, None, pp.observations(p)))

    def test_voiced_draft_raises_no_avoided_talk_notes(self):
        notes = " ".join(pp.observations(pp.profile(VOICED)))
        self.assertNotIn("bare acknowledgement", notes)
        self.assertNotIn("listener's side", notes)

    def test_uppercase_speech_counts_toward_dialogue_and_avoided_talk(self):
        p = pp.profile("“I KNOW.”\n\n“I—”\n\n“WHO?”\n")
        self.assertEqual(p["speech_count"], 3)
        self.assertEqual(p["dialogue_share_of_words"], 1.0)
        self.assertEqual(p["i_know_turns"], 1)
        self.assertEqual(p["bare_acknowledgements"], 1)
        self.assertEqual(p["cut_off_lines"], 1)
        self.assertEqual(p["one_or_two_word_spoken_questions"], 1)
        self.assertIn("WHO?", p["pointing_lines"])

    def test_curly_apostrophes_preserve_non_answers_and_mannerisms(self):
        text = "She didn't answer. He couldn't reply. It wasn't anger. It was fear."
        plain = pp.profile(text)
        curly = pp.profile(text.replace("'", "’"))
        self.assertEqual(plain["narrated_non_answers"], 2)
        self.assertEqual(curly["narrated_non_answers"], plain["narrated_non_answers"])
        self.assertEqual(curly["mannerisms"], plain["mannerisms"])

    def test_paragraph_and_exchange_runs_stop_at_scene_breaks(self):
        scene = "\n\n".join(["“Fine.”"] * 4)
        p = pp.profile(f"{scene}\n\n***\n\n{scene}")
        self.assertEqual(p["scenes"], 2)
        self.assertEqual(p["longest_run_of_short_paragraphs"], 4)
        self.assertEqual(p["longest_run_of_bare_exchange"], 4)
        self.assertNotIn("long stretch of bare short lines", " ".join(pp.observations(p)))

    def test_meaning_it_or_meaning_to_is_not_a_gloss(self):
        p = pp.profile("“Go,” she said. She meant it. She had meant to say more.\n")
        self.assertEqual(p["narrator_glosses"], 0)

    def test_scene_count_matches_tagged_paragraphs(self):
        tagged = pp.paragraphs_by_scene(STACCATO)
        self.assertEqual(len({scene for scene, _ in tagged}), 2)
        self.assertEqual(pp.paragraphs_and_scenes("")[1], 1)

    def test_render_mentions_baseline_when_given(self):
        p = pp.profile(VOICED)
        text = pp.render(p, {"stories": 3, "narration_sentence_mean": 8.0}, pp.observations(p))
        self.assertIn("collection median 8.0", text)
        self.assertIn("not a score", text)


if __name__ == "__main__":
    unittest.main()
