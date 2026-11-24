#!/usr/bin/env python3
"""Measure a story draft's rhythm, dialogue and texture against the collection.

This is a diagnostic for the writer, the line editor and the coordinator. It is
not a gate and its numbers are not targets: a draft can sit inside every range
and be lifeless, and a deliberate voice can sit outside them. It exists because
uniform sentence length and interchangeable dialogue are hard to hear in one's
own draft and easy to count. It also lists the habits by which this collection
avoids talk: bare acknowledgements, cut-off lines, narrated silences, and short
lines that point at something the listener has not been told.

Usage:
    python prose_profile.py stories/<slug>/story.md
    python prose_profile.py stories/<slug>/story.md --baseline stories --json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from itertools import groupby
from pathlib import Path

SCENE_BREAK = re.compile(r"^\s*(\*\s?\*\s?\*|-{3,}|#{2,}\s.*)\s*$")
# A newline here is a physical paragraph break. A quotation can cross it
# only when the next paragraph reopens the quote and a closing mark follows.
QUOTE_OR_BREAK = re.compile(r'[“"]([^”"\n]+(?:\n[“"][^”"\n]+)*)[”"]|\n')
SENTENCE_END = re.compile(r"(?<=[.!?…])[”\"’')\]]*\s+(?=[“\"‘'(\[]?[A-Z0-9])")

SENSES = {
    "smell": r"smell\w*|scent\w*|stink\w*|stank|reek\w*|odou?r\w*|whiff\w*|aroma\w*|fragran\w*|musty|acrid",
    "taste": r"tast\w*|flavou?r\w*|bitter|sour|salty|sweetness|savou?r\w*",
    "touch": r"rough|smooth|slick|sticky|damp|clammy|gritty|coarse|prickl\w*|itch\w*|warm\w*|cold|chill\w*|hot|heat|cool\w*|sweat\w*|numb|ache\w*|sting\w*|stung",
    "sound": r"sound\w*|nois\w*|rattl\w*|creak\w*|hum\w*|buzz\w*|clatter\w*|thud\w*|echo\w*|murmur\w*|whistl\w*|rang|ring\w*|roar\w*|hiss\w*|click\w*|silence|quiet",
}

MANNERISMS = {
    "for a moment": r"\bfor a (?:long )?moment\b",
    "seemed to": r"\bseem(?:ed|s) to\b",
    "something like": r"\bsomething like\b",
    "that was all": r"\bthat was all\b",
    "said nothing / did not answer": r"\bsaid nothing\b|\bdid(?: not|n't) answer\b",
    "it was not X. it was Y": r"\b(?:it|this|that) was(?: not|n't) [^.?!]{1,60}[.;] (?:it|this|that) was\b",
    "a breath (let out / held)": r"\b(?:let out|released|held) (?:a|her|his|their) breath\b",
    "very still": r"\bvery still\b",
    "almost / nearly smiled": r"\b(?:almost|nearly) smiled\b",
}

# Whole spoken turns that close an exchange without adding to it. None is wrong
# in itself; the collection leans on them where a conversation was owed.
ACKNOWLEDGEMENTS = {
    "i know", "i know that", "yes i know", "yes", "no", "oh", "good", "all right",
    "okay", "ok", "right", "fine", "of course", "i remember", "i see",
    "i understand", "so am i", "so do i", "i did", "i heard you",
}
I_KNOW = {"i know", "i know that", "yes i know"}
NON_ANSWER = re.compile(
    r"\bsaid nothing\b|\b(?:did(?: not|n't)|could(?: not|n't)) (?:answer|reply)\b"
    r"|\bhad no answer\b|\bmade no (?:answer|reply)\b|\b(?:no one|nobody) answered\b"
    r"|\bnothing to say\b|\bneither (?:of (?:us|them) )?spoke\b"
    r"|\btried to answer and could not\b"
)
# Kept for the narrator_glosses JSON field. These phrases can also describe
# plans and misunderstandings. The count cannot establish a dialogue fault.
GLOSS = re.compile(
    r"\b(?:he|she|they|i) meant (?!it\b|to\b|well\b|no\b)|\bunderstood (?:him|her|them|it) perfectly\b"
    r"|\bknew what (?:he|she|they) meant\b"
)
# A short line that opens on one of these points at something. Whether the
# listener knows what is a question only a reader can answer; the script lists
# the candidates.
POINTING_START = re.compile(
    r"^(?:he|she|they|it|him|her|them|that|this|these|those|their|his|its|the"
    r"|how|who|whom|whose|which|when)\b", re.I)
PRONOUN_START = re.compile(r"^(?:he|she|they|it|him|them|that|this|these|those)\b", re.I)


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text


def paragraphs_by_scene(text: str):
    """Return [(scene_index, paragraph)]. Headings and break markers are dropped."""
    body = strip_frontmatter(text).replace("\r\n", "\n")
    out, scene, seen_prose = [], 0, False
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        if SCENE_BREAK.match(block):
            if seen_prose:
                scene += 1
                seen_prose = False
            continue
        if block.startswith("#"):
            continue
        out.append((scene, re.sub(r"\s+", " ", block)))
        seen_prose = True
    return out


def paragraphs_and_scenes(text: str):
    """Return (paragraphs, scene_count)."""
    tagged = paragraphs_by_scene(text)
    return [p for _, p in tagged], len({s for s, _ in tagged}) or 1


def normal(speech: str) -> str:
    return re.sub(r"[^a-z' ]", "", speech.lower().replace("’", "'")).strip()


def split_sentences(paragraph: str):
    return [s for s in SENTENCE_END.split(paragraph) if s.strip()]


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9’'\-]+", text))


def share(values, predicate) -> float:
    values = list(values)
    return round(sum(1 for v in values if predicate(v)) / len(values), 3) if values else 0.0


def longest_run(flags, scene_ids=None) -> int:
    best = run = 0
    previous_scene = None
    for index, flag in enumerate(flags):
        if scene_ids is not None:
            scene = scene_ids[index]
            if scene != previous_scene:
                run = 0
            previous_scene = scene
        run = run + 1 if flag else 0
        best = max(best, run)
    return best


def quoted_turns_by_paragraph(tagged):
    """Yield each logical paragraph, with its narration and quoted fragments."""
    for scene, group in groupby(tagged, key=lambda row: row[0]):
        text = "\n".join(p for _, p in group) + "\n"
        start = previous_end = 0
        narration, quotes = [], []
        for match in QUOTE_OR_BREAK.finditer(text):
            narration.append(text[previous_end:match.start()])
            previous_end = match.end()
            if match[1] is not None:
                quotes.append(re.sub(r'\n[“"]', ' ', match[1]))
                narration.append(" " + "\n" * match[1].count("\n"))
            else:
                # A break outside quotation marks separates turns. Inside a
                # turn, narration such as a dialogue tag stays on its own line.
                yield scene, text[start:match.start()], "".join(narration).split("\n"), " ".join(quotes)
                start = previous_end
                narration, quotes = [], []


def profile(text: str) -> dict:
    tagged = paragraphs_by_scene(text)
    paragraphs = [p for _, p in tagged]
    scene_ids = [s for s, _ in tagged]
    scenes = len(set(scene_ids)) or 1
    body = "\n\n".join(paragraphs)
    total_words = words(body)
    para_lengths = [words(p) for p in paragraphs]

    narration, speeches, bare, exchange_scenes = [], [], [], []
    acknowledgements = i_know = cut_off = 0
    pointing: list[str] = []
    scenes_with_speech: set[int] = set()
    for scene_id, p, unquoted, speech in quoted_turns_by_paragraph(tagged):
        narration.extend(unquoted)
        bare.append(bool(speech) and words(p) <= 10)
        exchange_scenes.append(scene_id)
        speech = speech.strip()
        if not any(character.isalpha() for character in speech):
            continue
        speeches.append(speech)
        key = normal(speech)
        first_in_scene = scene_id not in scenes_with_speech
        scenes_with_speech.add(scene_id)
        if key in ACKNOWLEDGEMENTS:
            acknowledgements += 1
        if key in I_KNOW:
            i_know += 1
        if speech.endswith(("—", "–", "--")):
            cut_off += 1
        if key not in ACKNOWLEDGEMENTS and (
            (words(speech) <= 3 and POINTING_START.match(speech))
            or (first_in_scene and PRONOUN_START.match(speech))
        ):
            pointing.append(speech)
    speech_lengths = [words(s) for s in speeches]
    spoken_words = sum(speech_lengths)
    sentence_lengths = [n for p in narration for n in (words(s) for s in split_sentences(p)) if n]
    narration_lower = " ".join(narration).lower().replace("’", "'")
    non_answers = len(NON_ANSWER.findall(narration_lower))
    glosses = len(GLOSS.findall(narration_lower))

    lower = body.lower().replace("’", "'")
    senses = {name: len(re.findall(r"\b(?:" + pattern + r")\b", lower)) for name, pattern in SENSES.items()}
    mannerisms = {name: len(re.findall(pattern, lower)) for name, pattern in MANNERISMS.items()}
    mannerisms = {name: count for name, count in mannerisms.items() if count}

    names: dict[str, int] = {}
    for p in narration:
        for sentence in split_sentences(p):
            for token in re.findall(r"(?<!^)(?<![.!?] )\b[A-Z][a-z]{2,}\b", sentence.strip()):
                names[token] = names.get(token, 0) + 1
    recurring_names = sorted(n for n, c in names.items() if c >= 3)

    per_thousand = (lambda n: round(n * 1000 / total_words, 1)) if total_words else (lambda n: 0.0)
    return {
        "words": total_words,
        "scenes": scenes,
        "words_per_scene": round(total_words / scenes) if scenes else 0,
        "narration_sentence_mean": round(statistics.mean(sentence_lengths), 1) if sentence_lengths else 0,
        "narration_sentence_median": statistics.median(sentence_lengths) if sentence_lengths else 0,
        "narration_sentence_stdev": round(statistics.pstdev(sentence_lengths), 1) if sentence_lengths else 0,
        "sentences_6_words_or_fewer": share(sentence_lengths, lambda n: n <= 6),
        "sentences_25_words_or_more": share(sentence_lengths, lambda n: n >= 25),
        "longest_sentence": max(sentence_lengths, default=0),
        "paragraph_mean": round(statistics.mean(para_lengths), 1) if para_lengths else 0,
        "paragraphs_12_words_or_fewer": share(para_lengths, lambda n: n <= 12),
        "paragraphs_60_words_or_more": share(para_lengths, lambda n: n >= 60),
        "longest_run_of_short_paragraphs": longest_run((n <= 12 for n in para_lengths), scene_ids),
        "dialogue_share_of_words": round(spoken_words / total_words, 3) if total_words else 0,
        "speech_mean": round(statistics.mean(speech_lengths), 1) if speech_lengths else 0,
        "speeches_5_words_or_fewer": share(speech_lengths, lambda n: n <= 5),
        "speeches_40_words_or_more": sum(1 for n in speech_lengths if n >= 40),
        "longest_speech": max(speech_lengths, default=0),
        "one_or_two_word_spoken_questions": sum(1 for s in speeches if s.strip().endswith("?") and words(s) <= 2),
        "longest_run_of_bare_exchange": longest_run(bare, exchange_scenes),
        "speech_count": len(speeches),
        "bare_acknowledgements": acknowledgements,
        "bare_acknowledgement_share": round(acknowledgements / len(speeches), 3) if speeches else 0,
        "i_know_turns": i_know,
        "cut_off_lines": cut_off,
        "narrated_non_answers": non_answers,
        "narrator_glosses": glosses,
        "pointing_lines": pointing,
        "sense_words_per_1000": {name: per_thousand(count) for name, count in senses.items()},
        "mannerisms": mannerisms,
        "recurring_capitalized_names": recurring_names,
    }


BASELINE_KEYS = [
    "narration_sentence_mean", "narration_sentence_stdev",
    "sentences_6_words_or_fewer", "sentences_25_words_or_more",
    "paragraphs_12_words_or_fewer", "paragraphs_60_words_or_more",
    "longest_run_of_short_paragraphs", "speech_mean", "speeches_5_words_or_fewer",
    "speeches_40_words_or_more", "longest_speech", "longest_run_of_bare_exchange",
    "dialogue_share_of_words", "bare_acknowledgement_share", "narrated_non_answers",
]


def baseline(stories_dir: Path, exclude: Path | None = None) -> dict:
    rows = []
    for path in sorted(stories_dir.glob("*/story.md")) + sorted(stories_dir.glob("*/05-story.md")):
        if "_template" in path.parts or (exclude and path.resolve() == exclude.resolve()):
            continue
        try:
            row = profile(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if row["words"] >= 500:
            rows.append(row)
    if not rows:
        return {"stories": 0}
    out = {"stories": len(rows)}
    for key in BASELINE_KEYS:
        out[key] = round(statistics.median(r[key] for r in rows), 3)
    for sense in SENSES:
        out[f"sense_{sense}_per_1000"] = round(statistics.median(r["sense_words_per_1000"][sense] for r in rows), 1)
    return out


def observations(p: dict) -> list[str]:
    """Plain-language prompts for a closer look. Thresholds are loose on purpose."""
    notes = []
    if p["narration_sentence_mean"] and p["narration_sentence_mean"] < 12 and p["sentences_25_words_or_more"] < 0.05:
        notes.append("Narration runs short and even: few sentences carry a whole movement of thought or action. Read a middle page aloud for one-speed rhythm.")
    if p["paragraphs_12_words_or_fewer"] > 0.4 or p["longest_run_of_short_paragraphs"] >= 8:
        notes.append("Many very short paragraphs, or a long unbroken run of them. Check whether paragraphs develop or only tick.")
    if p["speech_mean"] and p["speeches_5_words_or_fewer"] > 0.5 and p["speeches_40_words_or_more"] == 0:
        notes.append("Most quoted turns are five words or fewer, and none reaches forty words. Cover the tags. Can you tell who is talking?")
    if p["longest_run_of_bare_exchange"] >= 8:
        notes.append("A long stretch of bare short lines in strict exchange. Look for the room, the bodies, and a speaker who wants to say more.")
    if p["one_or_two_word_spoken_questions"] >= 6:
        notes.append("Many one- or two-word spoken questions; these are often echoes of the previous line.")
    if p["i_know_turns"] >= 2 or (p["speech_count"] >= 30 and p["bare_acknowledgement_share"] > 0.08):
        notes.append("Several spoken turns are a bare acknowledgement (“I know.” “Yes.”). Each closes an exchange without anyone having to say anything. Reread them and ask what the character would say if not allowed to stop there.")
    if p["narrated_non_answers"] >= 2:
        notes.append("The narration reports more than once that someone did not or could not answer. Check whether the story is avoiding a conversation it owes its reader.")
    if p["cut_off_lines"] >= 2:
        notes.append("More than one spoken line is cut off with a dash. If one of them is the question or admission a scene was built for, write it out.")
    if len(p["pointing_lines"]) >= 4:
        notes.append("Several short lines point at something without naming it (listed under Dialogue). Read each from the listener's side: do they, and the reader, know what is meant?")
    if p["words"] >= 1500 and p["dialogue_share_of_words"] < 0.08:
        notes.append("Fewer than 8% of the words appear in quoted turns. If an exchange matters here, can the reader follow it through speech, signing, writing, gesture or silence?")
    if p["words"] and p["scenes"] > 1 and p["words_per_scene"] < 900:
        notes.append("Scenes average under about 900 words. Ask whether any scene has room, and which could be merged or cut.")
    if p["sense_words_per_1000"]["smell"] + p["sense_words_per_1000"]["taste"] < 0.5:
        notes.append("Almost nothing is smelled or tasted. Check each scene's opening for a sense other than sight.")
    if len(p["recurring_capitalized_names"]) > 10:
        notes.append("More than ten recurring proper names. Confirm the cast is small enough to know and that the rest are place names.")
    if sum(p["mannerisms"].values()) >= 6:
        notes.append("Several stock mannerisms recur; see the list and ask what plain claim each is standing in for.")
    return notes


def render(p: dict, base: dict | None, notes: list[str]) -> str:
    lines = ["# Prose profile", "",
             "A diagnostic, not a score. Numbers show where to look; only reading shows what is there.", ""]
    def row(label, key, fmt=str):
        value = fmt(p[key])
        if base and key in base:
            value += f"   (collection median {fmt(base[key])})"
        lines.append(f"- {label}: {value}")
    pct = lambda v: f"{round(v * 100)}%"
    lines.append(f"- Words: {p['words']}; scenes: {p['scenes']}")
    row("Words per scene", "words_per_scene")
    lines.append("")
    lines.append("## Narration (quoted words removed)")
    row("Mean sentence length", "narration_sentence_mean")
    lines.append(f"- Median sentence length: {p['narration_sentence_median']}")
    row("Spread of sentence length (st. dev.)", "narration_sentence_stdev")
    row("Sentences of 6 words or fewer", "sentences_6_words_or_fewer", pct)
    row("Sentences of 25 words or more", "sentences_25_words_or_more", pct)
    lines.append(f"- Longest sentence: {p['longest_sentence']} words")
    row("Paragraphs of 12 words or fewer", "paragraphs_12_words_or_fewer", pct)
    row("Paragraphs of 60 words or more", "paragraphs_60_words_or_more", pct)
    row("Longest run of short paragraphs", "longest_run_of_short_paragraphs")
    lines.append("")
    lines.append("## Dialogue")
    row("Share of words in quoted turns", "dialogue_share_of_words", pct)
    row("Mean words per quoted turn", "speech_mean")
    row("Quoted turns of 5 words or fewer", "speeches_5_words_or_fewer", pct)
    row("Quoted turns of 40 words or more", "speeches_40_words_or_more")
    row("Longest quoted turn (words)", "longest_speech")
    lines.append(f"- One- or two-word quoted questions: {p['one_or_two_word_spoken_questions']}")
    row("Longest run of bare short exchange", "longest_run_of_bare_exchange")
    lines.append(f"- Whole turns that are a bare acknowledgement: {p['bare_acknowledgements']} (“I know.”: {p['i_know_turns']})")
    row("Bare acknowledgements as a share of turns", "bare_acknowledgement_share", pct)
    lines.append(f"- Quoted turns cut off with a dash: {p['cut_off_lines']}")
    row("Times the narration says someone did not or could not answer", "narrated_non_answers")
    if p["pointing_lines"]:
        shown = " / ".join(f"“{s}”" for s in p["pointing_lines"][:12])
        more = " …" if len(p["pointing_lines"]) > 12 else ""
        lines.append(f"- Short lines that point at something ({len(p['pointing_lines'])}); read each from the listener's side: {shown}{more}")
    lines.append("")
    lines.append("## Texture")
    for sense, value in p["sense_words_per_1000"].items():
        extra = f"   (collection median {base[f'sense_{sense}_per_1000']})" if base and f"sense_{sense}_per_1000" in base else ""
        lines.append(f"- {sense.capitalize()} words per 1,000: {value}{extra}")
    names = p["recurring_capitalized_names"]
    lines.append(f"- Recurring proper names in narration, approximate ({len(names)}): {', '.join(names) if names else 'none'}")
    if p["mannerisms"]:
        lines.append("- Mannerisms: " + "; ".join(f"{k} ×{v}" for k, v in p["mannerisms"].items()))
    lines.append("")
    lines.append("## Worth a closer look")
    lines.extend(f"- {n}" for n in notes) if notes else lines.append("- Nothing flagged. That is not a finding that the prose is good.")
    if base and base.get("stories"):
        lines += ["", f"Collection medians are from {base['stories']} existing stories. They describe the house manner the craft standard asks writers to move beyond; matching them is not the aim."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("story", type=Path, help="path to a story.md (or any Markdown prose file)")
    parser.add_argument("--baseline", type=Path, help="stories directory to compare against")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    result = profile(args.story.read_text(encoding="utf-8"))
    base = baseline(args.baseline, exclude=args.story) if args.baseline else None
    notes = observations(result)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.json:
        print(json.dumps({"profile": result, "baseline": base, "observations": notes}, ensure_ascii=False, indent=2))
    else:
        print(render(result, base, notes), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
