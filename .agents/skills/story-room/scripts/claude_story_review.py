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

from review_diagnostics import (OBSERVATION, STRENGTH, QUOTES, diagnostic_schema, reading_instructions,
                                source_map, validate_diagnostic, validate_shape, exact_evidence)


MODEL = "claude-opus-5-5"
CODEX_MODEL = "gpt-6-sol"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FINDING = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "location": {"type": "string"},
        "evidence": QUOTES,
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
        "decision": {"type": "string", "enum": ["retained", "editorial", "preference", "rejected"]},
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
        "editorial": {"type": "array", "items": OBSERVATION},
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


def discussion_schema(stage: str, role: str = "causal") -> dict:
    return diagnostic_schema(stage, role)


def quality_schema(stage: str, objections: list[dict] | None = None) -> dict:
    properties = {
        "verdict": {"type": "string", "enum": ["PASS", "REVISE"]},
        "findings": {"type": "array", "items": FINDING},
        "editorial": {"type": "array", "items": OBSERVATION},
        "strengths": {"type": "array", "items": STRENGTH},
        "notes": {"type": "string"},
        "resolutions": {"type": "array", "items": RESOLUTION,
                        "minItems": len(objections or []), "maxItems": len(objections or [])},
    }
    if stage == "prose":
        properties.update({key: {"type": "string", "enum": ["PASS", "REVISE", "N/A"]
                                 if key == "dialogue" else ["PASS", "REVISE"]}
                           for key in ("prompt", "internal", "dialogue")})
    return {"type": "object", "additionalProperties": False, "properties": properties,
            "required": list(properties)}


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
        if any(not isinstance(v, str) or not v.strip() for k, v in finding.items() if k != "evidence"):
            raise ValueError("Claude returned an empty finding field")
        validate_shape(finding["evidence"], QUOTES)
    validate_shape(result["editorial"], {"type": "array", "items": OBSERVATION})
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


def validate_discussion(result: dict, stage: str, role: str = "causal",
                        source_text: str = "", prompt_text: str = "") -> None:
    validate_diagnostic(result, stage, role, source_text, prompt_text)


def provisional_objections(*rounds: tuple[str, dict]) -> list[dict]:
    return [{"id": f"{name}:{index}", "finding": finding}
            for name, response in rounds
            for index, finding in enumerate(response["observations"], 1)]


def validate_quality(result: dict, stage: str, objections: list[dict] | None = None,
                     source_text: str = "", prompt_text: str = "") -> None:
    objections = objections or []
    if not isinstance(result, dict) or set(result) != set(quality_schema(stage, objections)["required"]):
        raise ValueError("Claude quality verdict has invalid fields")
    validate_shape(result, quality_schema(stage, objections))
    for item in result["findings"] + result["editorial"] + result["strengths"]:
        for quote in item["evidence"]:
            exact_evidence(quote, source_text + "\n" + prompt_text, "final quality")
    if (result["verdict"] == "PASS") != (len(result["findings"]) == 0):
        raise ValueError("Claude quality verdict and blocking findings disagree")
    resolutions = result["resolutions"]
    if not isinstance(resolutions, list) or len(resolutions) != len(objections):
        raise ValueError("Claude did not resolve every provisional blocker")
    expected_ids = {objection["id"] for objection in objections}
    by_id = {objection["id"]: objection["finding"] for objection in objections}
    ids = []
    for resolution in resolutions:
        if (not isinstance(resolution, dict) or set(resolution) != set(RESOLUTION["required"])
                or resolution["decision"] not in ("retained", "editorial", "preference", "rejected")
                or any(not isinstance(value, str) or not value.strip()
                       for value in resolution.values())):
            raise ValueError("Claude returned an invalid blocker resolution")
        ids.append(resolution["id"])
        observation = by_id.get(resolution["id"])
        if observation is not None:
            decision = resolution["decision"]
            if decision == "retained" and observation["category"] == "preference":
                raise ValueError("An optional preference cannot become a publication blocker")
            retained = result["findings"] if decision == "retained" else result["editorial"]
            if decision != "rejected" and not any(
                item["evidence"] == observation["evidence"] for item in retained
            ):
                raise ValueError("Accepted observation is missing from the final findings or editorial advice")
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
            not isinstance(value, str) or not value.strip() for key, value in finding.items() if key != "evidence"
        ):
            raise ValueError("Claude authority finding is invalid")
        validate_shape(finding["evidence"], QUOTES)
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
                + f"{clean(finding['location'])} — {clean(' / '.join(finding['evidence']))} "
                + f"Impact: {clean(finding['impact'])} "
                + f"Smallest fix: {clean(finding['fix'])}"
            )
    else:
        lines.append("- Blocking: none")
    for item in result["editorial"]:
        lines.append(f"- Editorial ({item['category']}): {md(item['location'])} — "
                     f"{md(' / '.join(item['evidence']))} Impact: {md(item['impact'])} "
                     f"Suggested change: {md(item['fix'])}")
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
    common = f"""You are reviewing {slug} at the {stage} stage.
Read the COMPLETE recorded prompt at {prompt_path} and COMPLETE target at {source_path}.
{scope}
The prompt governs acceptance; the outline is advisory intent. Preserve strengths and
intentional ambiguity. Do not impose formulaic conflict, compulsory subtext or a fixed
ending. Quotes must be exact source substrings. No file writes. Return the structured result.
"""
    if quality_final:
        specific = """Only now decide PASS/REVISE and apply the active publication threshold.
Classifications from diagnosis are not automatic blockers. Keep supported nonblocking
contradictions/craft advice and optional preferences in editorial, even on PASS. Do not
turn preferences into requirements. Findings contains material blockers only; PASS has
no blocking findings. Complete strengths identifies what a repair must preserve.
Resolve every numbered observation: retained means a blocker in findings; editorial or
preference means preserved advice in editorial; rejected needs exact on-page evidence
and reasoning that answers the actual claim, not merely a quote on the same topic.
Keep an accepted observation's evidence array unchanged so its disposition is traceable.
Each evidence item must be one exact excerpt without line labels, separators or commentary.
Finish all distinct findings; do not stop after the first or impose a finding quota.
For outlines, block missing causal decisions that force consequential invention, while
leaving scene execution, dialogue and ending choices flexible. For prose, judge action,
knowledge and uptake locally and voice/repetition across scenes, including nonverbal
contact. Dialogue N/A applies only when there is essentially no meaningful dialogic action.
"""
    else:
        specific = "Do not decide publication readiness yet; follow your assigned reading role.\n"
    extras = ""
    if args.reference_image:
        extras += "Original reference images to inspect: " + ", ".join(args.reference_image) + "\n"
    if args.comparison and final:
        extras += "Bounded collection comparisons after standalone story judgment: " + ", ".join(args.comparison) + "\n"
    if args.pre_review:
        extras += f"Mechanical PreReview result: {args.pre_review}\n"
    if stage == "prose":
        examples_path = Path(__file__).with_name("review-examples.md")
        extras += ("\nRead review-examples.md for diagnostic operations and valid counterexamples.\n"
                   if diagnostic_file else "\n" + examples_path.read_text(encoding="utf-8"))
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
                       " turn. Preserve lesser stylistic observations in editorial.\n")
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


def codex_round(root: Path, stage: str, instructions: str, images: list[Path], timeout: int, *, role: str = "causal",
                source_text: str = "", prompt_text: str = "", output_path: Path | None = None) -> dict:
    with tempfile.TemporaryDirectory(prefix="story-review-schema-") as temporary:
        schema_path = Path(temporary) / "discussion.json"
        schema_path.write_text(json.dumps(discussion_schema(stage, role)), encoding="utf-8")
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
    if output_path is not None:
        output_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    try:
        validate_discussion(result, stage, role, source_text, prompt_text)
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
    examples_path = Path(__file__).with_name("review-examples.md")
    examples_copy = destination / examples_path.name
    shutil.copyfile(examples_path, examples_copy)
    copied[examples_copy] = digest(examples_copy)
    source_text = source.read_text(encoding="utf-8")
    manifest = source_map(source_text)
    manifest["numbered_source"] = "\n".join(
        f"{number}: {line}" for number, line in enumerate(source_text.splitlines(), 1))
    manifest_path = destination / "source-map.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    copied[manifest_path] = digest(manifest_path)
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
    if getattr(args, "calibration", False) and not args.no_write:
        raise ValueError("Calibration requires --no-write and cannot authorize publication")
    diagnostic_root = getattr(args, "diagnostics_dir", None)
    if diagnostic_root is not None:
        diagnostic_root = Path(diagnostic_root).resolve()
        if not getattr(args, "calibration", False) or diagnostic_root.is_relative_to(root):
            raise ValueError("Diagnostic persistence is only for calibration outside its source workspace")
        diagnostic_root.mkdir(parents=True, exist_ok=True)

    def diagnostic_output_path(name):
        return diagnostic_root / f"{name}.json" if diagnostic_root is not None else None

    def record_diagnostic(name, result):
        path = diagnostic_output_path(name)
        if path is not None:
            path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
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
    source_text = source_path.read_text(encoding="utf-8")
    prompt_text = prompt_path.read_text(encoding="utf-8")
    coverage_map = source_map(source_text)
    coverage_map["numbered_source"] = "\n".join(
        f"{number}: {line}" for number, line in enumerate(source_text.splitlines(), 1))
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
    examples_path = Path(__file__).with_name("review-examples.md")
    input_hashes[examples_path] = digest(examples_path)
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
        claude_initial = claude_round(
            quality_root, claude_common + reading_instructions(args.stage, "editorial")
            + "\nRead source-map.json for exact line numbers and quoted passage candidates."
            " Keep diagnostic fields concise; expand only when a suspected problem needs it."
            " This is the first reading; you have not seen any Sol assessment.",
            discussion_schema(args.stage, "editorial"), args, images, include_comparisons=False,
        )
        verify_inputs(quality_hashes)
        record_diagnostic("claude_initial", claude_initial)
        validate_discussion(claude_initial, args.stage, "editorial", source_text, prompt_text)
        initial = codex_round(
            empty_workspace, args.stage, common + reading_instructions(args.stage, "causal")
            + "\nSOURCE MAP:\n" + json.dumps(coverage_map, ensure_ascii=False) + "\n" + packet,
            images, args.timeout, role="causal", source_text=source_text, prompt_text=prompt_text,
            output_path=diagnostic_output_path("gpt_initial"),
        )
        verify_inputs(input_hashes)
        codex_reply = codex_round(
            empty_workspace, args.stage, common + reading_instructions(args.stage, "challenge")
            + "\n" + json.dumps({"your_initial": initial, "claude_initial": claude_initial}, ensure_ascii=False)
            + "\n" + packet,
            images, args.timeout, role="challenge", source_text=source_text, prompt_text=prompt_text,
            output_path=diagnostic_output_path("gpt_rejoinder"),
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
            " to consensus. Resolve EVERY numbered provisional observation in the resolutions"
            " array, including any repeated in the rejoinder. For a rejected observation,"
            " evidence must be an exact substring from the target showing why the objection"
            " fails; explain the inference in reason. Retain a real blocker in findings and preserve nonblocking advice in editorial."
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
        record_diagnostic("claude_quality_final", quality)
        validate_quality(quality, args.stage, objections, source_path.read_text(encoding="utf-8"), prompt_text)
        if getattr(args, "calibration", False):
            if not args.no_write:
                raise ValueError("Calibration requires --no-write and cannot authorize publication")
            verify_inputs(input_hashes)
            return {"calibration_only": True, "stage": args.stage, "story": args.story,
                    "source_sha256": before, "quality_verdict": quality["verdict"],
                    "findings": quality["findings"], "editorial": quality["editorial"],
                    "discussion": {"claude_initial": claude_initial, "gpt_initial": initial,
                                   "gpt_rejoinder": codex_reply, "claude_quality_final": quality}}
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
            "editorial": quality["editorial"],
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
    parser.add_argument("--calibration", action="store_true",
                        help="Compare independent Claude with discussion; --no-write required; no publication verdict")
    parser.add_argument("--diagnostics-dir", type=Path,
                        help="Optional temporary calibration outputs outside the source workspace")
    parser.add_argument("--claude-command", default="claude", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=True))
        if result.get("verdict") == "REVISE":
            return 2
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        message = f"Story review blocked: {exc}".encode("ascii", "backslashreplace").decode("ascii")
        print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
