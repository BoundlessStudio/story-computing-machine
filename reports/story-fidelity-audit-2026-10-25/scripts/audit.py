"""Read-only retrospective audit; never invokes the production restart ledger."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
TEMP = ROOT / "tmp/fidelity-audit-2026-10-25"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


GATE = module("fidelity_gate", OUT / "scripts/score_gate_v1.py")
CLIENT = module("decisions_client", Path.home() / ".codex/skills/decisions/scripts/decisions.py")


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    intermediate = path.with_suffix(path.suffix + ".writing")
    intermediate.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    for attempt in range(10):
        try:
            intermediate.replace(path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(.1 * (attempt + 1))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size}


def inventory():
    TEMP.mkdir(parents=True, exist_ok=True)
    packages = []
    rows = []
    for package in sorted((ROOT / "stories").iterdir()):
        if not package.is_dir() or package.name == "_template":
            continue
        legacy = not (package / "prompt.md").exists()
        prompt_path = package / ("00-prompt.md" if legacy else "prompt.md")
        if not prompt_path.exists():
            raise ValueError(f"Missing writing request: {package.name}")
        prompt = prompt_path.read_text(encoding="utf-8-sig")
        final = package / ("05-story.md" if legacy else "story.md")
        outline = package / ("02-story-plan.md" if legacy else "outline.md")
        prose = final.read_text(encoding="utf-8-sig") if final.exists() else ""
        title_match = re.search(r'(?m)^title:\s*["\']?(.+?)["\']?\s*$', prose)
        meta = json.loads((package / "story.json").read_text(encoding="utf-8-sig")) if (package / "story.json").exists() else {}
        title = meta.get("title") or (title_match.group(1) if title_match else next((x[2:] for x in prose.splitlines() if x.startswith("# ")), package.name))
        canon = meta.get("canon", bool(re.search(r"(?mi)^canon:\s*true\s*$", prose)))
        references = sorted(p for p in (package / "art/references").rglob("*") if p.is_file())
        missing = []
        for filename in sorted(set(re.findall(r'`([^`\n]+\.(?:png|jpe?g|webp|gif))`', prompt, re.I))):
            # The first-year sheet is expressly an art-edit target, not a story reference.
            if package.name == "the-first-year" and filename == "wheel-of-ages.webp":
                continue
            if not any(p.name == Path(filename).name for p in references) and not (package / filename).is_file():
                missing.append(filename)
        sources = [describe(p) for p in [prompt_path, outline, final, *references] if p.exists()]
        snapshot = TEMP / "snapshots" / package.name
        snapshot.mkdir(parents=True, exist_ok=True)
        inventory_prompt = prompt
        if not re.search(r"(?m)^## Supplied reference images[ \t]*$", prompt):
            inventory_prompt += "\n\n## Supplied reference images\n\n" + ("\n".join("- `" + p.relative_to(package / "art/references").as_posix() + "`" for p in references) if references else "- None") + "\n"
        (snapshot / "prompt.md").write_text(inventory_prompt, encoding="utf-8")
        for ref in references:
            target = snapshot / "art/references" / ref.relative_to(package / "art/references")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ref, target)
        package_record = {"slug": package.name, "title": title, "canon": canon, "layout": "legacy" if legacy else "current", "prompt_path": prompt_path.relative_to(ROOT).as_posix(), "prompt_text": prompt, "reference_count": len(references), "reference_files": [describe(p) for p in references], "missing_references": missing, "sources": sources}
        if package.name == "the-first-year":
            package_record["scope_note"] = "The saved request includes directions for editing a generated table sheet; that sheet is explicitly excluded as a story reference. Only outline/prose fidelity is evaluated."
        packages.append(package_record)
        for stage, source in (("outline", outline), ("final", final)):
            base = {"id": package.name + ":" + stage, "slug": package.name, "title": title, "canon": canon, "stage": stage, "layout": package_record["layout"], "candidate_path": source.relative_to(ROOT).as_posix(), "reference_count": len(references), "missing_references": missing, "score": None, "minimum_confidence": None, "prompt_score": None, "experience_score": None, "reference_score": None, "material_violation_probability": None, "source_ambiguity_probability": None, "action": None, "reasons": [], "status": "Pending"}
            if not source.exists():
                base.update(status="Unavailable", reasons=["No saved outline or plan exists in the package."])
                rows.append(base)
                continue
            text = source.read_text(encoding="utf-8-sig")
            (snapshot / GATE.STAGES[stage]).write_text(text, encoding="utf-8")
            bundle = GATE.build_bundle(snapshot, stage)
            # The factual compatibility inventory must not become a new user instruction.
            bundle["request"]["input"][1]["content"][0]["text"] = GATE.PROMPT_PREFIX + prompt
            base["candidate_text"] = text
            base["candidate_sha256"] = digest(source)
            base["request_sha256"] = hashlib.sha256(json.dumps(bundle["request"], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
            save(TEMP / "bundles" / package.name / (stage + ".json"), bundle)
            rows.append(base)
    manifest = {"audit_id": "story-fidelity-audit-2026-10-25", "created_at": utc(), "source_root": str(ROOT), "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "model": CLIENT.MODEL, "endpoint": CLIENT.ENDPOINT, "minimum_score": 3, "minimum_confidence": .8, "packages": packages}
    save(OUT / "manifest.json", manifest)
    save(OUT / "results.json", {"manifest": {k: v for k, v in manifest.items() if k != "packages"}, "rows": rows, "summary": summarize(rows)})
    print(json.dumps({"inventory": len(packages), "stage_slots": len(rows), "available": sum(r['status'] == 'Pending' for r in rows), "references": sum(p['reference_count'] for p in packages), "missing_references": [(p['slug'],p['missing_references']) for p in packages if p['missing_references']] }), flush=True)


def summarize(rows):
    return {"stage_slots": len(rows), "by_status": dict(Counter(r["status"] for r in rows)), "by_stage": {stage: dict(Counter(r["status"] for r in rows if r["stage"] == stage)) for stage in ("outline", "final")}, "api_results": sum(r.get("response") is not None for r in rows), "updated_at": utc()}


def export(rows, metadata, write_csv=False):
    save(OUT / "results.json", {"manifest": metadata, "rows": rows, "summary": summarize(rows)})
    if not write_csv:
        return
    columns = ["id", "title", "stage", "canon", "layout", "status", "score", "minimum_confidence", "prompt_score", "experience_score", "reference_score", "material_violation_probability", "source_ambiguity_probability", "reference_count", "action", "candidate_path", "source_changed", "reasons"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "reasons": "; ".join(row["reasons"])})
    temporary = OUT / "results.csv.writing"
    temporary.write_text(stream.getvalue(), encoding="utf-8-sig", newline="")
    for attempt in range(10):
        try:
            temporary.replace(OUT / "results.csv")
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(.1 * (attempt + 1))


def evaluate(row):
    bundle = json.loads((TEMP / "bundles" / row["slug"] / (row["stage"] + ".json")).read_text(encoding="utf-8"))
    started = utc()
    attempts = []
    raw_path = TEMP / "responses" / row["slug"] / (row["stage"] + ".json")
    if raw_path.exists():
        saved = json.loads(raw_path.read_text(encoding="utf-8"))
        if saved.get("request_sha256") == row["request_sha256"]:
            response = saved["response"]
            attempts = saved.get("attempts", [])
        else:
            raise ValueError("Saved API result has different source evidence.")
    else:
        response = None
        for attempt in range(2):
            begin = time.monotonic()
            try:
                response = CLIENT.create_decision(bundle["request"], timeout=120)
                attempts.append({"attempt": attempt + 1, "seconds": round(time.monotonic()-begin, 3), "success": True})
                break
            except CLIENT.DecisionsError as exc:
                response = exc.as_dict()
                attempts.append({"attempt": attempt + 1, "seconds": round(time.monotonic()-begin, 3), "success": False, **response})
                if attempt == 0 and response["error"].get("retryable"):
                    time.sleep(4)
                else:
                    break
        save(raw_path, {"request_sha256": row["request_sha256"], "response": response, "attempts": attempts})
    conflict = "The saved prompt names unavailable original reference images: " + ", ".join(row["missing_references"]) if row["missing_references"] else None
    assessment = GATE.assess_response(bundle, response, restarts=0, conflict=conflict)
    scores = assessment.get("scores", {})
    status = "API error" if "error" in response else ("Partial evidence" if conflict else {"proceed": "Would proceed", "restart_outline": "Would restart", "restart_story": "Would restart", "ask_user": "Needs judgment"}[assessment["action"]])
    return {**row, "status": status, "action": assessment["action"], "reasons": assessment["reasons"], "score": assessment.get("score"), "minimum_confidence": assessment.get("minimum_confidence"), "prompt_score": scores.get("prompt_fidelity", {}).get("score"), "experience_score": scores.get("experience_fidelity", {}).get("score"), "reference_score": scores.get("reference_fidelity", {}).get("score"), "material_violation_probability": assessment.get("material_violation_probability"), "source_ambiguity_probability": assessment.get("source_ambiguity_probability"), "assessment": assessment, "response": response, "attempts": attempts, "started_at": started, "finished_at": utc()}


def run(workers):
    current = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    rows, metadata = current["rows"], current["manifest"]
    pending = [(i,r) for i,r in enumerate(rows) if r["status"] == "Pending"]
    print(json.dumps({"start": utc(), "remaining":len(pending), "workers":workers}), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate, row): index for index,row in pending}
        for future in as_completed(futures):
            index = futures[future]
            try:
                rows[index] = future.result()
            except Exception as exc:
                rows[index] = {**rows[index], "status":"API error", "reasons":[f"Audit adapter error: {type(exc).__name__}: {exc}"]}
            completed = sum(r["status"] != "Pending" for r in rows)
            if completed % 10 == 0 or completed == len(rows):
                export(rows, metadata)
                print(json.dumps({"completed":completed,"total":len(rows),"last":rows[index]["id"],"status":rows[index]["status"],"score":rows[index]["score"],"confidence":rows[index]["minimum_confidence"],"counts":summarize(rows)["by_status"]}),flush=True)
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    changed = []
    for package in manifest["packages"]:
        for source in package["sources"]:
            path = ROOT / source["path"]
            if not path.exists() or digest(path) != source["sha256"]:
                changed.append(source["path"])
    for row in rows:
        row["source_changed"] = any(p.startswith("stories/"+row["slug"]+"/") for p in changed)
    metadata.update(completed_at=utc(), changed_source_files=changed)
    export(rows, metadata, write_csv=True)
    print(json.dumps({"finished":utc(), **summarize(rows),"changed_sources":changed}),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command", choices=["inventory","run"])
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args()
    inventory() if args.command=="inventory" else run(args.workers)
