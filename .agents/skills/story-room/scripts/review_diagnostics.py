"""Verdict-free readings and auditable source coverage for story review."""

import re


CATEGORIES = ["contradiction", "craft", "preference"]


def record(fields):
    return {"type": "object", "additionalProperties": False,
            "properties": fields, "required": list(fields)}


TEXT = {"type": "string", "minLength": 1}
QUOTES = {"type": "array", "items": TEXT, "minItems": 1,
          "description": "Each item is ONE exact source excerpt, without line labels, separators or ellipses. Put explanations in other fields."}
OBSERVATION = record({key: TEXT for key in ("location", "impact", "fix")}
                     | {"evidence": QUOTES}
                     | {"category": {"type": "string", "enum": CATEGORIES}})
STRENGTH = record({"evidence": QUOTES, "reason": TEXT})
SCENE = record({"start_line": {"type": "integer", "minimum": 1},
                "end_line": {"type": "integer", "minimum": 1}}
               | {key: TEXT for key in ("scene", "state_before", "state_after", "knowledge",
                                        "emotional_movement", "evidence")})
EXCHANGE = record({"start_line": {"type": "integer", "minimum": 1},
                   "mode": {"type": "string", "enum": ["dialogue", "quoted_text"]}}
                  | {key: TEXT for key in ("setup", "literal_intent",
                                           "listener_uptake", "next_response", "assessment")})
PATTERN = record({"evidence": {"type": "array", "items": TEXT, "minItems": 1},
                  "assessment": TEXT})


def diagnostic_schema(stage, role="causal"):
    fields = {"observations": {"type": "array", "items": OBSERVATION},
              "strengths": {"type": "array", "items": STRENGTH}, "notes": {"type": "string"}}
    if role != "challenge":
        fields["scenes"] = {"type": "array", "items": SCENE, "minItems": 1}
    if stage == "prose" and role == "editorial":
        fields["exchanges"] = {"type": "array", "items": EXCHANGE}
        fields["patterns"] = record({key: PATTERN for key in
                                     ("voice_under_pressure", "correction_routines", "ending_repetition")})
    return record(fields)


def source_map(text):
    """Line numbers refer to the unchanged source, including metadata and headings."""
    lines = text.splitlines()
    paragraphs = []
    start = None
    for number, line in enumerate(lines + [""], 1):
        if line.strip() and start is None:
            start = number
        if not line.strip() and start is not None:
            value = "\n".join(lines[start - 1:number - 1])
            # These are candidates, not a claim that quoted narration is dialogue.
            if re.search(r'["\u201c\u2018]', value) or re.match(r"^\s*'", value):
                paragraphs.append({"start_line": start, "end_line": number - 1, "text": value})
            start = None
    return {"line_count": len(lines), "quoted_passages": paragraphs}


def validate_shape(value, shape, label="diagnostic"):
    kind = shape["type"]
    if kind == "object":
        if not isinstance(value, dict) or set(value) != set(shape["required"]):
            raise ValueError(f"{label}: invalid fields")
        for key, child in shape["properties"].items():
            validate_shape(value[key], child, f"{label}.{key}")
    elif kind == "array":
        if not isinstance(value, list) or len(value) < shape.get("minItems", 0):
            raise ValueError(f"{label}: invalid array")
        for item in value:
            validate_shape(item, shape["items"], label)
    elif kind == "integer":
        if type(value) is not int or value < shape.get("minimum", 0):
            raise ValueError(f"{label}: invalid line number")
    elif not isinstance(value, str) or (shape.get("minLength") and not value.strip()):
        raise ValueError(f"{label}: empty or invalid text")
    if "enum" in shape and value not in shape["enum"]:
        raise ValueError(f"{label}: invalid category")


def exact_evidence(quote, source, label):
    if not quote.strip() or quote not in source:
        raise ValueError(f"{label}: evidence is not an exact source quote: {quote[:160]!r}")


def validate_diagnostic(value, stage, role, source, prompt=""):
    validate_shape(value, diagnostic_schema(stage, role))
    for observation in value["observations"]:
        for quote in observation["evidence"]:
            exact_evidence(quote, source + "\n" + prompt, "observation")
    for strength in value["strengths"]:
        for quote in strength["evidence"]:
            exact_evidence(quote, source, "strength")
    if role == "challenge":
        return
    lines = source.splitlines()
    next_line = 1
    for scene in value["scenes"]:
        start, end = scene["start_line"], scene["end_line"]
        if start != next_line or end < start or end > len(lines):
            raise ValueError("Scene coverage has a gap, overlap, or invalid boundary")
        exact_evidence(scene["evidence"], "\n".join(lines[start - 1:end]), "scene")
        next_line = end + 1
    if next_line != len(lines) + 1:
        raise ValueError("Scene coverage omits the end of the source")
    if stage == "prose" and role == "editorial":
        passages = {item["start_line"]: item for item in source_map(source)["quoted_passages"]}
        seen = []
        for exchange in value["exchanges"]:
            number = exchange["start_line"]
            if number not in passages:
                raise ValueError("Exchange check does not identify a quoted passage")
            seen.append(number)
        if len(set(seen)) != len(seen) or set(seen) != set(passages):
            raise ValueError("Editorial reading omitted or repeated a quoted passage")
        for pattern in value["patterns"].values():
            for quote in pattern["evidence"]:
                exact_evidence(quote, source, "pattern")


def reading_instructions(stage, role):
    common = """
Do not issue PASS or REVISE in this reading. First report supported observations and
specific strengths worth preserving. Classify observations as contradiction (facts,
causality, knowledge or literal uptake conflict), craft (a substantial reader-facing
weakness in otherwise possible prose), or preference (a genuinely optional alternative).
These categories are diagnoses, not automatic publication thresholds. Do not hide a
useful editorial finding because it might not block. There is no defect quota. Quote
exact source text without ellipses or normalized punctuation. Use separate evidence array
items for separate excerpts; no line labels, slash separators or commentary inside quotes.
Keep observations distinct.
"""
    if role == "challenge":
        return common + """
Cross-examine both independent readings. Recheck each proposed problem and the strongest
claim of success against its scene and earlier setup. Test Claude's dialogue and pattern
claims as well as your own causal reconstruction. Explain withdrawals in notes with source
support; retain or add supported observations. Do not repeat the coverage records or
silently treat absent objections as agreement. The final Claude turn decides severity.
"""
    common += """
Partition the COMPLETE numbered source into actual scenes (outline beats for outline
mode). Give contiguous inclusive start_line/end_line spans from 1 through line_count,
including metadata in the first span and trailing material in the last. Split on genuine
changes of time, place or dramatic activity; never label the entire multi-scene story one
scene. For each scene record consequential state before/after, knowledge available to each
participant, emotional movement, and an exact quote inside that span. Trace transitions
back to the last established state; distinguish an ordinary inference from an invented
rescue of a contradiction. Coverage records are diagnostic working notes, not plot recaps.
"""
    if role == "causal":
        return common + """
Read the story independently and without domain restrictions. Assess prompt fulfillment,
dialogue, voices, emotional movement, repetition, and causal continuity. Use the scene
records to reconstruct action, time, positions, possession, equipment states, rule limits,
entrances/exits and who learned what when. State what changes and what on-page event
permits it. Test claimed completion against the later action that actually completes it.
Track dependencies across scene boundaries, including deadlines. Report editorial and
dialogue problems wherever you find them, not just physical contradictions.
For outlines, identify only missing decisions that force consequential invention; allow
flexible scene execution, unscripted dialogue and open ending choices.
"""
    if stage == "outline":
        return common + """
Give an unrestricted editorial reading: prompt promise, causality, agency, knowledge,
physical setup, dialogue engine, emotional movement and repetition across proposed beats.
Identify missing causal choices without
requiring exact dialogue, a compulsory conflict shape, or a predetermined ending.
"""
    return common + """
Give an unrestricted, story-focused editorial reading. You own no exclusive domain:
find problems in causality, physical continuity, timing, knowledge, speculative rules,
prompt delivery, dialogue, voice, emotional movement or repetition. The diagnostic
fields are evidence aids, not limits on your judgment. Inspect EVERY quoted passage
identified in source-map.json with adjacent
action and the preceding/following response. Classify mere quoted terms as quoted_text;
The start_line identifies the exact source paragraph; do not copy that paragraph again.
for those explain why listener uptake is inapplicable. For dialogue record its actual
setup, literal question/intent, what the listener can recover, and whether the NEXT
response follows. Do not repair a pronoun mentally to match later narration. Include
meaningful unquoted/nonverbal exchanges in scene knowledge and emotional_movement.
In patterns, compare the SAME person's comfortable and pressured speech, then compare
speakers in the decisive exchange. Cite both sides; differences of job/topic alone are
not distinct voices. Locate recurring correction routines across exchanges and assess
their cumulative effect without banning comic rhythm. Compare the last action, dialogue
and narration for repeated meaning: say what each adds or merely explains again. A
plausible line can weaken a scene through repetition. Preserve patterns that serve it.
"""
