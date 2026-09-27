"""Get two independent editorial readings of an outline or story.

This runner handles file access, model identity, structured output, and byte pins.
It never decides PASS/REVISE or writes a story package. The coordinator reads
both assessments, investigates disagreements, and records the stage decision.
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

CLAUDE_MODEL = "claude-opus-5-5"
SOL_MODEL = "gpt-6-sol"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TEXT = {"type": "string"}
POINT = {
    "type": "object", "additionalProperties": False,
    "properties": {"location": TEXT, "evidence": TEXT, "assessment": TEXT},
    "required": ["location", "evidence", "assessment"],
}
CONCERN = {
    "type": "object", "additionalProperties": False,
    "properties": {**POINT["properties"], "severity": {
        "type": "string", "enum": ["contradiction", "substantial", "optional"]
    }, "possible_repair": TEXT},
    "required": [*POINT["required"], "severity", "possible_repair"],
}
READING = {
    "type": "object", "additionalProperties": False,
    "properties": {"strengths": {"type": "array", "items": POINT},
                   "concerns": {"type": "array", "items": CONCERN},
                   "overall": TEXT},
    "required": ["strengths", "concerns", "overall"],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reviewed_digest(source: Path, stage: str, current: bool) -> str:
    data = source.read_bytes()
    if stage == "prose" and current:
        front = re.match(rb"\A---\r?\n.*?\r?\n---\r?\n", data, re.DOTALL)
        if not front:
            raise ValueError("Current story lacks valid frontmatter")
        data = data[front.end():]
    return hashlib.sha256(data).hexdigest()


def validate_reading(value: object, model: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(READING["required"]):
        raise ValueError(f"{model} returned an invalid reading")
    if not isinstance(value["overall"], str) or not value["overall"].strip():
        raise ValueError(f"{model} returned an empty assessment")
    for field, keys in (("strengths", set(POINT["required"])),
                        ("concerns", set(CONCERN["required"]))):
        rows = value[field]
        if not isinstance(rows, list):
            raise ValueError(f"{model} returned invalid {field}")
        for row in rows:
            if not isinstance(row, dict) or set(row) != keys or any(
                not isinstance(item, str) or not item.strip() for item in row.values()
            ):
                raise ValueError(f"{model} returned an incomplete {field} item")
            if field == "concerns" and row["severity"] not in (
                "contradiction", "substantial", "optional"
            ):
                raise ValueError(f"{model} returned an invalid concern severity")
    return value


def instructions(stage: str) -> str:
    common = (
        "Read the complete prompt and target independently. Give an unrestricted, "
        "story-focused editorial reading. Identify supported strengths and problems "
        "before any publication decision; this reading has no PASS/REVISE verdict. "
        "Read every scene or outline movement. For prose, reconstruct consequential "
        "action, timing, object positions, speaker knowledge, literal dialogue intent, "
        "listener uptake, distinct voices, emotional movement, and repetition across "
        "scenes. Preserve passages that work. A transition may occur off page when "
        "the text allows it. Cite short exact source evidence and explain the mechanism "
        "and reader impact of each concern. Separate contradictions, substantial craft "
        "problems, and optional preferences. Do not manufacture faults to fill a quota. "
        "Do not consult prior versions, target reviews, outline verdicts, canon files, "
        "or name inventories; the coordinator checks authority after story quality. "
    )
    if stage == "outline":
        common += (
            "Assess whether the design can be drafted without guessing about a material "
            "prompt requirement: central promise, causal movement, agency, knowledge, "
            "time, space, speculative limits, and dialogue engine. Leave room for "
            "discovery; do not demand scripted dialogue or a predetermined ending. "
        )
    return common + "Return only the requested JSON object."


def verify(pins: dict[Path, str]) -> None:
    for path, expected in pins.items():
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError(f"Review input bytes changed: {path}")


def claude_read(prompt: Path, source: Path, images: list[Path], stage: str,
                executable: str, timeout: int) -> dict:
    with tempfile.TemporaryDirectory(prefix="story-claude-read-") as tmp:
        root = Path(tmp)
        shutil.copyfile(prompt, root / "prompt.md")
        shutil.copyfile(source, root / source.name)
        request = (instructions(stage) + "\nRead prompt.md and " + source.name +
                   ". Reference originals: " + ", ".join(str(p) for p in images))
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        cmd = [executable, "-p", "--model", CLAUDE_MODEL, "--effort", "high",
               "--no-session-persistence", "--restricted", "--tools", "Read,Glob,Grep",
               "--output-format", "json", "--json-schema", json.dumps(READING)]
        for parent in sorted({p.parent for p in images}):
            cmd.extend(["--add-dir", str(parent)])
        result = subprocess.run(cmd, cwd=root, env=env, input=request, text=True,
                                encoding="utf-8", errors="replace", capture_output=True,
                                timeout=timeout)
        if result.returncode:
            raise RuntimeError(f"Claude failed (exit {result.returncode}): {result.stderr[-600:]}")
        try:
            envelope = json.loads(result.stdout)
            if envelope.get("is_error") or CLAUDE_MODEL not in envelope.get("modelUsage", {}):
                raise ValueError("Claude Opus 5.5 identity or authentication not verified")
            return validate_reading(envelope["structured_output"], "Claude")
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Claude returned malformed structured output") from exc


def sol_read(prompt: Path, source: Path, images: list[Path], stage: str,
             timeout: int, executable: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="story-sol-read-") as tmp:
        root = Path(tmp)
        schema = root / "schema.json"
        schema.write_text(json.dumps(READING), encoding="utf-8")
        request = (instructions(stage) + "\nThe exact prompt and target follow. "
                   "Use only these bytes and the attached image originals; no tools or "
                   "other files.\n\nPROMPT:\n" + prompt.read_text(encoding="utf-8") +
                   "\n\nTARGET:\n" + source.read_text(encoding="utf-8"))
        cmd = [executable, "-a", "never", "exec", "-c", "model_reasoning_effort=high",
               "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check",
               "--ephemeral", "--json", "-m", SOL_MODEL, "-s", "read-only", "-C",
               str(root), "--output-schema", str(schema)]
        for image in images:
            cmd.extend(["-i", str(image)])
        cmd.append("-")
        result = subprocess.run(cmd, cwd=root, input=request, text=True,
                                encoding="utf-8", errors="replace", capture_output=True,
                                timeout=timeout)
        if result.returncode:
            raise RuntimeError(f"GPT-6 Sol failed (exit {result.returncode}): "
                               f"{result.stderr[-600:]} {result.stdout[-600:]}")
        try:
            events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
            messages = [event["item"]["text"] for event in events if
                        event.get("type") == "item.completed" and
                        event.get("item", {}).get("type") == "agent_message"]
            if not messages or not any(e.get("type") == "turn.completed" for e in events):
                raise ValueError("GPT-6 Sol did not complete a structured reading")
            return validate_reading(json.loads(messages[-1]), "GPT-6 Sol")
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("GPT-6 Sol returned malformed structured output") from exc


def run(args: argparse.Namespace) -> dict:
    root = args.worktree.resolve()
    if not SLUG.fullmatch(args.story):
        raise ValueError("Invalid story slug")
    directory = root / "stories" / args.story
    current = (directory / "story.md").is_file()
    bundle = (directory / "05-story.md").is_file()
    if current == bundle or (args.stage == "outline" and bundle):
        raise ValueError("Unsupported or ambiguous story layout")
    prompt = directory / ("prompt.md" if current else "00-prompt.md")
    source = directory / ("outline.md" if args.stage == "outline" else
                          ("story.md" if current else "05-story.md"))
    if not prompt.is_file() or not source.is_file():
        raise ValueError("Missing prompt or target")
    images = [(Path(p) if Path(p).is_absolute() else root / p).resolve()
              for p in args.reference_image]
    if any(not image.is_file() for image in images):
        raise ValueError("Missing reference original")
    pins = {path: digest(path) for path in (prompt, source, *images)}
    source_hash = reviewed_digest(source, args.stage, current)
    # These sessions are independent: neither model sees the other's reading.
    claude = claude_read(prompt, source, images, args.stage, args.claude_command, args.timeout)
    verify(pins)
    sol = sol_read(prompt, source, images, args.stage, args.timeout, args.codex_command)
    verify(pins)
    if reviewed_digest(source, args.stage, current) != source_hash:
        raise RuntimeError("Target changed during review")
    return {"stage": args.stage, "story": args.story, "layout": "current" if current else "bundle",
            "source_sha256": source_hash, "prompt_sha256": pins[prompt],
            "claude": claude, "sol": sol}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("outline", "prose"))
    parser.add_argument("--story", required=True)
    parser.add_argument("--worktree", type=Path, default=Path.cwd())
    parser.add_argument("--reference-image", action="append", default=[])
    parser.add_argument("--claude-command", default="claude", help=argparse.SUPPRESS)
    parser.add_argument("--codex-command", default="codex", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=True))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Story review blocked: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
