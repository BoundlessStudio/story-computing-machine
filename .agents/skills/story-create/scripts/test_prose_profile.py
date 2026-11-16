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
        self.assertIn("nobody speaks at length", notes)

    def test_voiced_draft_measures_range_and_senses(self):
        p = pp.profile(VOICED)
        self.assertGreaterEqual(p["longest_sentence"], 30)
        self.assertEqual(p["speeches_40_words_or_more"], 1)
        self.assertGreater(p["sense_words_per_1000"]["smell"], 0)
        self.assertNotIn("short and even", " ".join(pp.observations(p)))

    def test_speech_is_excluded_from_narration_rhythm(self):
        p = pp.profile("“No.” “Yes.” “No.” She crossed the whole length of the yard before she let herself look back at the house.\n")
        self.assertEqual(p["narration_sentence_mean"], 17)

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
