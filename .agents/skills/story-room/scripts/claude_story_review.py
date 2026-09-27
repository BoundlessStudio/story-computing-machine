"""Run a fresh GPT-6 Sol / Claude Opus 5.5 review discussion of story work.

Only current-format prose reviews write a package file: the existing review.md.
Outline and bundle verdicts are returned to the coordinator on stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


MODEL = "claude-opus-5-5"
CODEX_MODEL = "gpt-6-sol"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FINDING = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "location": {"type": "string"},
        "evidence": {"type": "string"},
        "impact": {"type": "string"},
        "fix": {"type": "string"},
    },
    "required": ["location", "evidence", "impact", "fix"],
}
NOUN = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "status": {"type": "string", "enum": ["new", "recurring"]},
        "note": {"type": "string"},
    },
    "required": ["name", "status", "note"],
}
RESOLUTION = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "decision": {"type": "string", "enum": ["retained", "rejected"]},
        "evidence": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["id", "decision", "evidence", "reason"],
}


def schema(stage: str) -> dict:
    properties = {
        "verdict": {"type": "string", "enum": ["PASS", "REVISE"]},
        "findings": {"type": "array", "items": FINDING},
        "notes": {"type": "string"},
    }
    required = list(properties)
    if stage == "prose":
        properties.update(
            {
                "prompt": {"type": "string", "enum": ["PASS", "REVISE"]},
                "universe": {"type": "string", "enum": ["PASS", "REVISE"]},
                "internal": {"type": "string", "enum": ["PASS", "REVISE"]},
                "dialogue": {"type": "string", "enum": ["PASS", "REVISE", "N/A"]},
                "people": {"type": "array", "items": NOUN},
                "places": {"type": "array", "items": NOUN},
            }
        )
        required.extend(["prompt", "universe", "internal", "dialogue", "people", "places"])
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def discussion_schema(stage: str) -> dict:
    kinds = ["promise", "causality", "knowledge_rules"] if stage == "outline" else [
        "opening", "decisive", "final", "weakest_turn", "voice_pattern", "ending_effect"]
    check = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "location": {"type": "string"},
            "evidence": {"type": "string"},
            "assessment": {"type": "string"},
        },
        "required": ["location", "evidence", "assessment"],
    }
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "verdict": {"type": "string", "enum": ["PASS", "REVISE"]},
            "findings": {"type": "array", "items": FINDING},
            "checks": {"type": "object", "additionalProperties": False,
                       "properties": {kind: check for kind in kinds}, "required": kinds},
            "notes": {"type": "string"},
        },
        "required": ["verdict", "findings", "checks", "notes"],
    }


def quality_schema(stage: str, objections: list[dict] | None = None) -> dict:
    result = discussion_schema(stage)
    result["properties"]["resolutions"] = {
        "type": "array", "items": RESOLUTION,
        "minItems": len(objections or []), "maxItems": len(objections or []),
    }
    result["required"].append("resolutions")
    if stage == "prose":
        result["properties"].update({
            "prompt": {"type": "string", "enum": ["PASS", "REVISE"]},
            "internal": {"type": "string", "enum": ["PASS", "REVISE"]},
            "dialogue": {"type": "string", "enum": ["PASS", "REVISE", "N/A"]},
        })
        result["required"].extend(("prompt", "internal", "dialogue"))
    return result


def authority_schema(stage: str) -> dict:
    properties = {
        "verdict": {"type": "string", "enum": ["PASS", "REVISE"]},
        "findings": {"type": "array", "items": FINDING},
        "notes": {"type": "string"},
    }
    if stage == "prose":
        properties.update({
            "universe": {"type": "string", "enum": ["PASS", "REVISE"]},
            "people": {"type": "array", "items": NOUN},
            "places": {"type": "array", "items": NOUN},
        })
    return {"type": "object", "additionalProperties": False, "properties": properties,
            "required": list(properties)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_prose_bytes(path: Path) -> bytes:
    source = path.read_bytes()
    front = re.match(rb"\A---\r?\n.*?\r?\n---\r?\n", source, re.DOTALL)
    if not front:
        raise ValueError(f"{path} lacks valid current-story frontmatter")
    return source[front.end():]


def reviewed_digest(path: Path, stage: str, current: bool) -> str:
    if stage == "prose" and current:
        return hashlib.sha256(current_prose_bytes(path)).hexdigest()
    return digest(path)


def clean(value: str) -> str:
    return " ".join(value.strip().split())


def md(value: str) -> str:
    return clean(value).replace("|", "\\|")


def validate(result: dict, stage: str) -> None:
    expected = set(schema(stage)["required"])
    if not isinstance(result, dict) or set(result) != expected:
        raise ValueError("Claude returned fields outside the review schema")
    if result["verdict"] not in ("PASS", "REVISE"):
        raise ValueError("Claude returned an invalid verdict")
    findings = result["findings"]
    if not isinstance(findings, list):
        raise ValueError("Claude findings must be a list")
    if (result["verdict"] == "PASS") != (len(findings) == 0):
        raise ValueError("Claude verdict and blocking findings disagree")
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != set(FINDING["required"]):
            raise ValueError("Claude returned an invalid finding")
        if any(not isinstance(v, str) or not v.strip() for v in finding.values()):
            raise ValueError("Claude returned an empty finding field")
    if not isinstance(result["notes"], str):
        raise ValueError("Claude notes must be text")
    if stage == "prose":
        for key in ("prompt", "universe", "internal", "dialogue"):
            allowed = ("PASS", "REVISE", "N/A") if key == "dialogue" else ("PASS", "REVISE")
            if result[key] not in allowed:
                raise ValueError(f"Claude returned an invalid {key} gate")
        gates = (result[k] for k in ("prompt", "universe", "internal", "dialogue"))
        if result["verdict"] == "PASS" and any(v == "REVISE" for v in gates):
            raise ValueError("Claude PASS contradicts a failed prose gate")
        if result["verdict"] == "REVISE" and not any(
            result[k] == "REVISE" for k in ("prompt", "universe", "internal", "dialogue")
        ):
            raise ValueError("Claude REVISE lacks a failed prose gate")
        for key in ("people", "places"):
            if not isinstance(result[key], list):
                raise ValueError(f"Claude {key} inventory must be a list")
            for noun in result[key]:
                if not isinstance(noun, dict) or set(noun) != set(NOUN["required"]):
                    raise ValueError(f"Claude returned an invalid {key} row")
                if noun["status"] not in ("new", "recurring") or any(
                    not isinstance(v, str) or not v.strip() for v in noun.values()
                ):
                    raise ValueError(f"Claude returned an incomplete {key} row")


def validate_discussion(result: dict, stage: str) -> None:
    discussion = discussion_schema(stage)
    if not isinstance(result, dict) or set(result) != set(discussion["required"]):
        raise ValueError("Discussion returned fields outside its schema")
    if result["verdict"] not in ("PASS", "REVISE") or not isinstance(result["findings"], list):
        raise ValueError("Discussion returned an invalid verdict or findings")
    if (result["verdict"] == "PASS") != (len(result["findings"]) == 0):
        raise ValueError("Discussion verdict and blocking findings disagree")
    for finding in result["findings"]:
        if not isinstance(finding, dict) or set(finding) != set(FINDING["required"]):
            raise ValueError("Discussion returned an invalid finding")
        if any(not isinstance(value, str) or not value.strip() for value in finding.values()):
            raise ValueError("Discussion returned an empty finding field")
    if not isinstance(result["notes"], str):
        raise ValueError("Discussion notes must be text")
    checks = result["checks"]
    expected = {"promise", "causality", "knowledge_rules"} if stage == "outline" else {
        "opening", "decisive", "final", "weakest_turn", "voice_pattern", "ending_effect"}
    if not isinstance(checks, dict) or set(checks) != expected:
        raise ValueError(f"Discussion source checks must be exactly {sorted(expected)}")
    for check in checks.values():
        if not isinstance(check, dict) or set(check) != {"location", "evidence", "assessment"}:
            raise ValueError("Discussion returned an invalid source check")
        if any(not isinstance(value, str) or not value.strip() for value in check.values()):
            raise ValueError("Discussion returned an empty source check")


def provisional_objections(*rounds: tuple[str, dict]) -> list[dict]:
    return [{"id": f"{name}:{index}", "finding": finding}
            for name, response in rounds
            for index, finding in enumerate(response["findings"], 1)]


def validate_quality(result: dict, stage: str, objections: list[dict] | None = None,
                     source_text: str = "") -> None:
    objections = objections or []
    if not isinstance(result, dict) or set(result) != set(quality_schema(stage, objections)["required"]):
        raise ValueError("Claude quality verdict has invalid fields")
    validate_discussion({key: result[key] for key in discussion_schema(stage)["required"]}, stage)
    resolutions = result["resolutions"]
    if not isinstance(resolutions, list) or len(resolutions) != len(objections):
        raise ValueError("Claude did not resolve every provisional blocker")
    expected_ids = {objection["id"] for objection in objections}
    ids = []
    for resolution in resolutions:
        if (not isinstance(resolution, dict) or set(resolution) != set(RESOLUTION["required"])
                or resolution["decision"] not in ("retained", "rejected")
                or any(not isinstance(value, str) or not value.strip()
                       for value in resolution.values())):
            raise ValueError("Claude returned an invalid blocker resolution")
        ids.append(resolution["id"])
        if resolution["decision"] == "rejected" and resolution["evidence"] not in source_text:
            raise ValueError("Claude rejected a blocker without exact on-page evidence")
    if len(set(ids)) != len(ids) or set(ids) != expected_ids:
        raise ValueError("Claude did not address every provisional blocker by id")
    if result["verdict"] == "PASS" and any(row["decision"] == "retained" for row in resolutions):
        raise ValueError("Claude PASS retained a provisional blocker")
    if stage == "prose":
        for key in ("prompt", "internal", "dialogue"):
            allowed = ("PASS", "REVISE", "N/A") if key == "dialogue" else ("PASS", "REVISE")
            if result[key] not in allowed:
                raise ValueError(f"Claude quality verdict has invalid {key} gate")
        failed = any(result[key] == "REVISE" for key in ("prompt", "internal", "dialogue"))
        if (result["verdict"] == "REVISE") != failed:
            raise ValueError("Claude quality verdict and gates disagree")


def validate_authority(result: dict, stage: str) -> None:
    if not isinstance(result, dict) or set(result) != set(authority_schema(stage)["required"]):
        raise ValueError("Claude authority verdict has invalid fields")
    if result["verdict"] not in ("PASS", "REVISE") or not isinstance(result["findings"], list):
        raise ValueError("Claude authority verdict or findings are invalid")
    if (result["verdict"] == "PASS") != (len(result["findings"]) == 0):
        raise ValueError("Claude authority verdict and findings disagree")
    for finding in result["findings"]:
        if not isinstance(finding, dict) or set(finding) != set(FINDING["required"]) or any(
            not isinstance(value, str) or not value.strip() for value in finding.values()
        ):
            raise ValueError("Claude authority finding is invalid")
    if not isinstance(result["notes"], str):
        raise ValueError("Claude authority notes must be text")
    if stage == "prose":
        if result["universe"] != result["verdict"]:
            raise ValueError("Claude authority universe gate and verdict disagree")
        for key in ("people", "places"):
            if not isinstance(result[key], list):
                raise ValueError(f"Claude authority {key} inventory is invalid")
            for noun in result[key]:
                if not isinstance(noun, dict) or set(noun) != set(NOUN["required"]) or any(
                    not isinstance(value, str) or not value.strip() for value in noun.values()
                ) or noun["status"] not in ("new", "recurring"):
                    raise ValueError(f"Claude authority {key} row is invalid")


def review_markdown(result: dict, story_hash: str) -> str:
    lines = [
        "# Review",
        "",
        f"Verdict: {result['verdict']}",
        f"Reviewed prose SHA-256: {story_hash}",
        "",
    ]
    for key in ("people", "places"):
        lines.extend([f"## {key.title()}", "", "| Noun | Status | Continuity note |", "| --- | --- | --- |"])
        rows = result[key]
        if rows:
            lines.extend(f"| {md(n['name'])} | {n['status']} | {md(n['note'])} |" for n in rows)
        else:
            lines.append("| None | none | No story-facing names in this category. |")
        lines.append("")
    lines.extend(
        [
            "## Continuity",
            "",
            f"- Prompt: {result['prompt']}",
            f"- Universe: {result['universe']}",
            f"- Internal: {result['internal']}",
            "",
            "## Craft",
            "",
            f"- Dialogue: {result['dialogue']}",
            "",
            "## Findings",
            "",
        ]
    )
    if result["findings"]:
        for finding in result["findings"]:
            lines.append(
                "- Blocking: "
                + f"{clean(finding['location'])} — {clean(finding['evidence'])} "
                + f"Impact: {clean(finding['impact'])} "
                + f"Smallest fix: {clean(finding['fix'])}"
            )
    else:
        lines.append("- Blocking: none")
    lines.extend([f"- Notes: {md(result['notes']) or 'none'}", ""])
    return "\n".join(lines)


def prompt_for(stage: str, slug: str, prompt_path: Path, source_path: Path,
               args: argparse.Namespace, *, final: bool = False,
               diagnostic_file: Path | None = None, quality_final: bool = False) -> str:
    scope = ("Issue the final story-quality verdict now, before any canon, name, or broad policy check."
             if quality_final else
             "Resolve story quality first; then check canon, policy, and names. Do not open "
             "any prior review of the target, earlier prose, or the target outline during prose review."
             if final else
             "For this discussion, concentrate on the reader's experience of this exact story. Do not "
             "read universe files, name inventories, repository rules, prior reviews, earlier prose, "
             "or the target outline during prose review. Canon, policy, and names are a later final check.")
    common = f"""You are reviewing the story quality of {slug} at the {stage} stage.
Read the COMPLETE recorded prompt at {prompt_path} and the COMPLETE {stage} at {source_path}.
{scope}
The prompt governs acceptance. The outline is advisory and is not an acceptance authority.
Judge the actual text skeptically, from a reader's available knowledge, without inventing
missing transitions. A materially broken line or scene can block despite an appealing voice.
Do not impose formulaic conflict, compulsory subtext, an aphorism ban, or a fixed ending.
Findings must name an exact location, quote a short exact piece of source evidence, explain
its reader-facing impact, and specify the smallest useful repair. Use REVISE only for material
failures. The findings array contains BLOCKING findings only. For PASS, set findings to an
empty array and put any nonblocking observations in notes. For REVISE, every finding must
be a material reason to block this stage. No writing or editing files. Return only the
structured result. Finish the full review even after finding one blocker; report every
distinct material failure, up to six. Keep notes source-focused, with no plot summary.
"""
    if stage == "outline":
        specific = """Check whether this plan is draftable before prose begins: prompt promise,
causal movement, character agency, time and space, knowledge limits, operative speculative
rules, dialogue engine, and source-supported use of reference images.
Flag contradictions or missing decisions that would force the writer to guess about a
material requirement. Preserve flexibility: do not demand scripted dialogue, a specific
climax, or a predetermined ending. A PASS permits writing; REVISE blocks writer handoff.
For discussion checks, cite exact outline evidence for its promise, causal movement, and
knowledge/rule boundary. A deliberate open choice may pass if the writer can draft it.
"""
    else:
        specific = """This is a fresh finished-prose review. Do not read the target outline
or its outline verdict. First judge prompt fulfillment and complete-story effect; then scan
every meaningful exchange with adjacent action for object/action fit, referents, speaker
knowledge, listener uptake, distinct voices, needed exposition, and earned emotional turns.
Check physical staging, causality, chronology, capabilities, and an ending
that does not needlessly explain an already clear action. Inspect decisive and final exchanges
closely. For a PASS,
all required gates must pass and there must be no blocking findings. For REVISE, identify the
failed gate and give actionable blocking findings. N/A dialogue is only for essentially no
meaningful dialogic action, including non-spoken contact.
At every exchange, privately paraphrase each turn's setup and what the listener can
reasonably understand or do next. Test referents, staging, knowledge, and response logic
before accepting a witty line. Compare speaker sentence shapes under pressure, not only
their roles or topics; repeated clipped corrections can erase distinct voices. Check
whether the ending explains the same consequence again in dialogue and narration. Do not
stop after a first blocker. For the discussion checks, cite exact short evidence from an
opening, decisive, and final exchange with adjacent action, even when the verdict is PASS.
Each check's assessment must state the literal action, what the speaker can know, what the
listener reasonably takes the line to mean, and whether the next response follows.
When there is meaningful dialogue, notes must contrast the main speakers' actual sentence
shapes, directness, and reactions to pressure with short source examples. If several voices
share one corrective or aphoristic pattern, judge its scene-wide effect. Inspect even the
apparently successful exchanges for manufactured setup lines and repetition at the ending.
The discussion must include a voice_pattern check comparing exact lines from at least two
speakers across major exchanges. Ask whether their reasoning and response shapes could be
swapped without changing character or relationship, and whether a correction/qualification
routine dominates more than one exchange. It must include an ending_effect check comparing
the final meaningful exchange with the narration around it: identify what new action or
knowledge the ending delivers and any restatement of a consequence already visible.
The discussion must also include a weakest_turn check for the most suspect turn anywhere,
including a middle scene. Trace its setup, literal referent, speaker knowledge, listener
uptake, and next action. If it passes, explain what the actual prose establishes.
"""
    extras = ""
    if args.reference_image:
        extras += "Original reference images to inspect: " + ", ".join(args.reference_image) + "\n"
    if args.comparison and final:
        extras += "Bounded collection comparisons after standalone story judgment: " + ", ".join(args.comparison) + "\n"
    if args.pre_review:
        extras += f"Mechanical PreReview result: {args.pre_review}\n"
    if stage == "prose":
        if diagnostic_file is not None:
            extras += ("\nRead the local dialogue-diagnostic.txt file as a story-quality diagnostic."
                       " The binding story profile controls thresholds; do not create output files.\n")
        else:
            diagnostic_path = Path(__file__).resolve().parents[2] / "dialogue" / "SKILL.md"
            diagnostic = diagnostic_path.read_text(encoding="utf-8").split("## Available Tools", 1)[0]
            extras += ("\nDiagnostic reference for this review (through its Diagnostic Process only;"
                       " binding story profile controls thresholds; do not run scripts or create its"
                       " suggested output files):\n" + diagnostic)
        if quality_final and getattr(args, "active_profile", "") == "prospective-2026-08-08":
            extras += ("\nUnder the active 08-08 profile, a craft defect blocks only when it"
                       " materially breaks the prompt's central promise or reader-facing"
                       " causality. Broad binding policy is checked in the later authority"
                       " turn. Put lesser stylistic observations in notes.\n")
        if quality_final and getattr(args, "active_profile", "") in (
            "prospective-2026-08-18", "prospective-2026-08-21", "prospective-2026-08-23"
        ):
            extras += ("\nThe active profile's shared-reality gate can block on one materially"
                       " incoherent line, even if the wider plot and voices work. Test each critical"
                       " referent, object state, speaker knowledge, and listener uptake. Do not"
                       " dismiss a provisional blocker by inventing unshown placement, equipment"
                       " state, timing, or a speaker's observation. Cite the on-page support"
                       " that actually resolves it, or retain the blocker.\n")
    return common + specific + extras


def codex_round(root: Path, stage: str, instructions: str, images: list[Path], timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="story-review-schema-") as temporary:
        schema_path = Path(temporary) / "discussion.json"
        schema_path.write_text(json.dumps(discussion_schema(stage)), encoding="utf-8")
        command = [
            "codex", "-a", "never", "exec", "-c", "model_reasoning_effort=high",
            "--ignore-user-config", "--ignore-rules",
            "--skip-git-repo-check", "--ephemeral", "--json", "-m", CODEX_MODEL,
            "-s", "read-only", "-C", str(root), "--output-schema", str(schema_path),
        ]
        for image in images:
            command.extend(["-i", str(image)])
        command.append("-")
        completed = subprocess.run(command, cwd=root, text=True, encoding="utf-8",
                                   errors="replace", capture_output=True, input=instructions,
                                   timeout=timeout)
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-500:] + " " + completed.stdout.strip()[-800:]
        raise RuntimeError(f"GPT-6 Sol review failed (exit {completed.returncode}): {detail.strip()}")
    try:
        events = [json.loads(line) for line in completed.stdout.splitlines() if line.startswith("{")]
        messages = [event["item"]["text"] for event in events
                    if event.get("type") == "item.completed" and event.get("item", {}).get("type") == "agent_message"]
        if not any(event.get("type") == "turn.completed" for event in events) or not messages:
            raise ValueError("GPT-6 Sol did not complete one structured response: "
                             + completed.stdout[-1000:])
        result = json.loads(messages[-1])
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("GPT-6 Sol returned malformed structured output") from exc
    try:
        validate_discussion(result, stage)
    except ValueError as exc:
        raise ValueError(f"GPT-6 Sol discussion: {exc}; response: {str(result)[:800]}") from exc
    return result


def codex_packet(root: Path, story: str, source: Path, prompt: Path,
                 comparisons: list[str], images: list[Path]) -> tuple[str, dict[Path, str]]:
    """Embed exact story bytes for Sol before the separate authority check."""
    paths = [prompt, source]
    sections = []
    hashes = {}
    for path in paths:
        hashes[path] = digest(path)
        sections.append(f"\n===== BEGIN {path.relative_to(root) if path.is_relative_to(root) else path} "
                        f"SHA-256 {hashes[path]} =====\n{path.read_text(encoding='utf-8')}\n===== END =====")
    for image in images:
        hashes[image] = digest(image)
    return ("All source text below is copied from the exact reviewed files. Do not use tools,"
            " search the internet, or infer different remote copies. Read the complete prompt and target."
            " Judge story quality before the later canon and policy check.\n"
            + "\n".join(sections), hashes)


def final_authority_inputs(root: Path, story: str, comparisons: list[str]) -> dict[Path, str]:
    """Pin files available for the final canon, policy, and name check."""
    paths = [*sorted((root / "universe").rglob("*.md")), root / "stories" / "NAMES.md"]
    for value in comparisons:
        candidate = Path(value)
        paths.append(candidate if candidate.is_absolute() else root / candidate)
    for review in (root / "stories").glob("*/review.md"):
        if review.parent.name != story and re.search(
            r"(?m)^Verdict: PASS\s*$", review.read_text(encoding="utf-8")
        ):
            paths.append(review)
    for record in (root / "stories").glob("*/story.json"):
        if record.parent.name != story and json.loads(record.read_text(encoding="utf-8")).get("canon") is True:
            paths.extend((record, record.parent / "05-story.md"))
    return {path: digest(path) for path in paths}


def review_snapshot(root: Path, destination: Path, story: str, prompt: Path, source: Path,
                    *, final: bool, comparisons: list[str], diagnostic: str | None) -> dict[Path, str]:
    """Expose only permitted exact files to each independent Claude session."""
    copied: dict[Path, str] = {}

    def copy_file(path: Path) -> None:
        target = destination / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        copied[target] = digest(target)

    copy_file(prompt)
    copy_file(source)
    if diagnostic is not None:
        target = destination / "dialogue-diagnostic.txt"
        target.write_text(diagnostic, encoding="utf-8")
        copied[target] = digest(target)
    if not final:
        return copied
    for path in sorted((root / "universe").rglob("*.md")):
        copy_file(path)
    copy_file(root / "stories" / "NAMES.md")
    for review in (root / "stories").glob("*/review.md"):
        if review.parent.name == story:
            continue
        content = review.read_text(encoding="utf-8")
        if not re.search(r"(?m)^Verdict: PASS\s*$", content):
            continue
        sections = []
        for heading in ("People", "Places"):
            match = re.search(rf"(?ms)^## {heading}\s*\n(.*?)(?=^## |\Z)", content)
            if match:
                sections.append(f"## {heading}\n{match.group(1).strip()}\n")
        target = destination / "stories" / review.parent.name / "review.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Verdict: PASS\n\n" + "\n".join(sections), encoding="utf-8")
        copied[target] = digest(target)
    for record in (root / "stories").glob("*/story.json"):
        if record.parent.name != story and json.loads(record.read_text(encoding="utf-8")).get("canon") is True:
            copy_file(record)
            copy_file(record.parent / "05-story.md")
    for value in comparisons:
        candidate = Path(value)
        path = (candidate if candidate.is_absolute() else root / candidate).resolve()
        if path.is_relative_to(root) and path != prompt and path != source:
            copy_file(path)
    return copied


def verify_inputs(hashes: dict[Path, str]) -> None:
    if any(not path.is_file() or digest(path) != expected for path, expected in hashes.items()):
        raise RuntimeError("Review input bytes changed during model discussion")


def claude_round(root: Path, instructions: str, output_schema: dict, args: argparse.Namespace,
                 images: list[Path], *, include_comparisons: bool = True) -> dict:
    environment = os.environ.copy()
    environment.pop("ANTHROPIC_API_KEY", None)
    command = [
        args.claude_command, "-p", "--model", MODEL, "--effort", "high",
        "--no-session-persistence",
        "--restricted", "--tools", "Read,Glob,Grep", "--output-format", "json",
        "--json-schema", json.dumps(output_schema, separators=(",", ":")),
    ]
    external_directories = {path.parent for path in images if not path.is_relative_to(root)}
    for value in (args.comparison if include_comparisons else []):
        candidate = Path(value)
        comparison = (candidate if candidate.is_absolute() else root / candidate).resolve()
        if not comparison.is_relative_to(root):
            external_directories.add(comparison.parent)
    for directory in sorted(external_directories):
        command.extend(["--add-dir", str(directory)])
    completed = subprocess.run(command, cwd=root, env=environment, text=True,
                               encoding="utf-8", errors="replace",
                               capture_output=True, input=instructions, timeout=args.timeout)
    if completed.returncode != 0:
        raise RuntimeError(f"Claude review failed (exit {completed.returncode}): {completed.stderr.strip()[-500:]}")
    try:
        envelope = json.loads(completed.stdout)
        if envelope.get("is_error") or not isinstance(envelope.get("structured_output"), dict):
            raise ValueError("Claude did not return a successful structured result")
        usage = envelope.get("modelUsage")
        if not isinstance(usage, dict) or MODEL not in usage:
            raise ValueError("Claude model identity could not be verified as Opus 5.5")
        return envelope["structured_output"]
    except (json.JSONDecodeError, AttributeError) as exc:
        raise ValueError("Claude returned malformed JSON") from exc


def run(args: argparse.Namespace) -> dict:
    root = args.worktree.resolve()
    if not SLUG.fullmatch(args.story):
        raise ValueError("Invalid story slug")
    directory = root / "stories" / args.story
    current = (directory / "story.md").is_file()
    bundle = (directory / "05-story.md").is_file()
    if current == bundle:
        raise ValueError("Story must have exactly one supported prose layout")
    if args.stage == "outline" and bundle:
        raise ValueError("Outline review applies to current-format CREATE stories")
    prompt_path = directory / ("prompt.md" if current else "00-prompt.md")
    source_path = directory / ("outline.md" if args.stage == "outline" else ("story.md" if current else "05-story.md"))
    if not prompt_path.is_file() or not source_path.is_file():
        raise ValueError("Missing prompt or review source")
    def input_path(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else root / path

    for path in args.reference_image + args.comparison:
        if not input_path(path).is_file():
            raise ValueError(f"Missing review input: {path}")
    allowed_comparisons = {"outline.md"} if args.stage == "outline" else {"story.md", "05-story.md"}
    for value in args.comparison:
        path = input_path(value).resolve()
        if (not path.is_relative_to(root / "stories") or path.parent.name == args.story
                or path.name not in allowed_comparisons):
            raise ValueError(f"Invalid comparison source: {value}")
    images = [input_path(value).resolve() for value in args.reference_image]
    profiles = re.findall(r"(?m)^-[ \t]+Craft profile:[ \t]*([^\r\n]+)",
                          prompt_path.read_text(encoding="utf-8"))
    args.active_profile = profiles[-1].strip() if profiles else ""
    before = reviewed_digest(source_path, args.stage, current)
    diagnostic_path = Path(__file__).resolve().parents[2] / "dialogue" / "SKILL.md"
    diagnostic_hash = digest(diagnostic_path) if args.stage == "prose" else None
    diagnostic_text = (diagnostic_path.read_text(encoding="utf-8").split("## Available Tools", 1)[0]
                       if args.stage == "prose" else None)
    common = prompt_for(args.stage, args.story, prompt_path.relative_to(root), source_path.relative_to(root), args)
    claude_common = prompt_for(args.stage, args.story, prompt_path.relative_to(root),
                               source_path.relative_to(root), args,
                               diagnostic_file=Path("dialogue-diagnostic.txt") if diagnostic_text else None)
    packet, input_hashes = codex_packet(root, args.story, source_path, prompt_path,
                                        args.comparison, images)
    input_hashes.update(final_authority_inputs(root, args.story, args.comparison))
    if diagnostic_hash is not None:
        input_hashes[diagnostic_path] = diagnostic_hash
    with tempfile.TemporaryDirectory(prefix="story-review-inputs-") as temporary:
        empty_workspace = Path(temporary) / "sol"
        empty_workspace.mkdir()
        quality_root = Path(temporary) / "quality"
        final_root = Path(temporary) / "final"
        quality_hashes = review_snapshot(root, quality_root, args.story, prompt_path, source_path,
                                         final=False, comparisons=[], diagnostic=diagnostic_text)
        final_hashes = review_snapshot(root, final_root, args.story, prompt_path, source_path,
                                       final=True, comparisons=args.comparison, diagnostic=diagnostic_text)
        initial = codex_round(
            empty_workspace, args.stage, common + "\nIndependently propose only material blockers. This is the first discussion turn.\n"
            "Return a provisional verdict and source-grounded findings in the given schema."
            " For prose, complete all six source checks, compare the main voices with exact"
            " examples, and explain"
            " at least two suspicious lines you tested even if you PASS; do not recap the plot.\n"
            + packet, images, args.timeout,
        )
        verify_inputs(input_hashes)
        claude_initial = claude_round(
            quality_root, claude_common + "\nThis is your independent first assessment. You have not seen"
            " GPT-6 Sol's assessment. Make the required source checks and return your own"
            " provisional verdict with blocking findings only. For prose, inspect every"
            " meaningful exchange with the diagnostic reference. Use notes to contrast main"
            " voices using exact lines, and discuss at least two suspicious setup-delivery"
            " turns even if you PASS. Do not recap the plot.",
            discussion_schema(args.stage), args, images, include_comparisons=False,
        )
        verify_inputs(quality_hashes)
        try:
            validate_discussion(claude_initial, args.stage)
        except ValueError as exc:
            raise ValueError(f"Claude initial discussion: {exc}; response: {str(claude_initial)[:800]}") from exc
        codex_reply = codex_round(
            empty_workspace, args.stage, common + "\nYour independent proposal and Claude Opus 5.5's independent proposal follow."
            " Recheck points of disagreement against the source. Challenge any shared PASS by"
            " testing the strongest plausible counterexample in a decisive exchange, voice"
            " pattern, or ending. Explain what you retain or withdraw in notes, and return"
            " your revised provisional verdict with blocking findings only.\n"
            + json.dumps({"your_initial": initial, "claude_initial": claude_initial}, ensure_ascii=False)
            + "\n" + packet,
            images, args.timeout,
        )
        verify_inputs(input_hashes)
        objections = provisional_objections(
            ("gpt_initial", initial), ("claude_initial", claude_initial),
            ("gpt_rejoinder", codex_reply),
        )
        quality = claude_round(
            quality_root, prompt_for(args.stage, args.story, prompt_path.relative_to(root),
                                     source_path.relative_to(root), args, quality_final=True,
                                     diagnostic_file=Path("dialogue-diagnostic.txt") if diagnostic_text else None)
            + "\nThe complete story-quality discussion follows. Resolve its disputed craft"
            " and causal claims against the target and issue the FINAL STORY-QUALITY verdict."
            " Do not open canon, name, or broad policy files. You own this verdict; do not defer"
            " to consensus. Resolve EVERY numbered provisional objection in the resolutions"
            " array, including any repeated in the rejoinder. For a rejected objection,"
            " evidence must be an exact substring from the target showing why the objection"
            " fails; explain the inference in reason. Retain a real blocker in findings."
            " Do not invent placement, object state, elapsed time, or a"
            " speaker's observation. Apply the active craft profile's threshold. For prose,"
            " report prompt, internal, and dialogue gates, including N/A only for essentially"
            " no meaningful dialogic action. A PASS has no blocking findings.\n"
            + json.dumps({"objections": objections, "gpt_initial": initial,
                          "claude_initial": claude_initial,
                          "gpt_rejoinder": codex_reply}, ensure_ascii=False),
            quality_schema(args.stage, objections), args, images, include_comparisons=False,
        )
        verify_inputs(quality_hashes)
        validate_quality(quality, args.stage, objections, source_path.read_text(encoding="utf-8"))
        authority = claude_round(
            final_root, f"You are Claude Opus 5.5 conducting the final authority check for"
            f" {args.story}. The story-quality verdict below is already final and cannot be"
            " withdrawn in this turn. Read the complete prompt and target, then read"
            " universe/README.md, universe/style-guide.md, relevant universe entries,"
            " stories/NAMES.md, passing review name inventories, and relevant canon bundle"
            " prose. Check binding canon, broad narrative policy, chronology, and name"
            " confusion only now. For an active 08-23 CREATE profile, compare bounded"
            " recent-story passages only when a standalone dialogue PASS permits it."
            " Add only concrete authority/name blockers, with exact source evidence;"
            " do not repeat or reconsider the locked story-quality findings. Do not"
            " open prior reviews of the target, prior target prose, or its outline"
            " during prose review. Return the authority verdict, findings, and final"
            " people/place inventory in the schema. The authority verdict, and the universe"
            " gate for prose, are REVISE exactly when at least one blocking authority finding"
            " is supplied; otherwise both are PASS and findings is empty. Put only"
            " nonblocking observations in notes. No file writes.\n"
            + ("Bounded comparison paths: " + ", ".join(args.comparison) + "\n"
               if args.comparison else "")
            + "Locked story-quality verdict: " + json.dumps(quality, ensure_ascii=False),
            authority_schema(args.stage), args, images,
        )
        verify_inputs(final_hashes)
        try:
            validate_authority(authority, args.stage)
        except ValueError as exc:
            raise ValueError(f"{exc}; response: {str(authority)[:1200]}") from exc
        result = {
            "verdict": "REVISE" if "REVISE" in (quality["verdict"], authority["verdict"]) else "PASS",
            "findings": quality["findings"] + authority["findings"],
            "notes": f"Story quality: {quality['notes']} Authority: {authority['notes']}",
        }
        if args.stage == "prose":
            result.update({key: quality[key] for key in ("prompt", "internal", "dialogue")})
            result.update({key: authority[key] for key in ("universe", "people", "places")})
    validate(result, args.stage)
    verify_inputs(input_hashes)
    if args.stage == "prose" and current and not args.no_write:
        source_text = source_path.read_text(encoding="utf-8")
        frontmatter = source_text.split("---", 2)[1] if source_text.startswith("---") else ""
        if re.findall(r"(?m)^canon:[ \t]*(true|false)[ \t]*$", frontmatter) != ["false"]:
            raise ValueError("Cannot write a review inside a canon-locked story")
        (directory / "review.md").write_text(review_markdown(result, before), encoding="utf-8", newline="\n")
    return {"stage": args.stage, "story": args.story, "source_sha256": before,
            "layout": "current" if current else "bundle", "discussion": {
                "gpt_initial": initial, "claude_initial": claude_initial, "gpt_rejoinder": codex_reply,
                "claude_quality_final": quality, "claude_authority": authority,
            }, **result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("outline", "prose"), required=True)
    parser.add_argument("--story", required=True)
    parser.add_argument("--worktree", type=Path, default=Path.cwd())
    parser.add_argument("--reference-image", action="append", default=[])
    parser.add_argument("--comparison", action="append", default=[])
    parser.add_argument("--pre-review", default="")
    parser.add_argument("--no-write", action="store_true", help="Only emit the verdict; useful for calibration")
    parser.add_argument("--claude-command", default="claude", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=True))
        if result["verdict"] == "REVISE":
            return 2
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        message = f"Story review blocked: {exc}".encode("ascii", "backslashreplace").decode("ascii")
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
