"""Score independently adjudicated findings, never infer detection from PASS/REVISE.

Runs are a list of {id, slug, version, output, source} records. Adjudications cover
every candidate in both arms; they are made after blind runs, using source text.
The rubric and adjudications are never supplied to the reviewer being measured.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re


def candidates(result):
    return {
        "claude_alone": {f"observation:{i}": row for i, row in
                         enumerate(result["discussion"]["claude_initial"]["observations"], 1)},
        "combined": {**{f"blocking:{i}": row for i, row in enumerate(result["findings"], 1)},
                     **{f"editorial:{i}": row for i, row in enumerate(result["editorial"], 1)}},
    }


def body_hash(source):
    front = re.match(rb"\A---\r?\n.*?\r?\n---\r?\n", source, re.DOTALL)
    return hashlib.sha256(source[front.end():] if front else source).hexdigest()


def score(rubric, runs, adjudications):
    expected = {}
    inputs = {}
    candidate_rows = {}
    controls = {}
    for run in runs:
        case = rubric["stories"][run["slug"]]
        if case["split"] != "withheld":
            raise ValueError("Teaching stories cannot count toward withheld results")
        source = Path(run["source"]).read_bytes()
        result = json.loads(Path(run["output"]).read_text(encoding="utf-8"))
        pinned = case["versions"][run["version"]]["source_sha256"]
        if body_hash(source) != pinned or result["source_sha256"] != pinned:
            raise ValueError("Calibration source hash mismatch")
        if not result.get("calibration_only"):
            raise ValueError("Expected a blind calibration result")
        if run["id"] in inputs:
            raise ValueError("Duplicate run")
        inputs[run["id"]] = source.decode("utf-8")
        expected[run["id"]] = set(case["versions"][run["version"]]["expected_issues"])
        controls[run["id"]] = {row["id"] for row in case["preserve"]}
        for arm, rows in candidates(result).items():
            for identifier, row in rows.items():
                candidate_rows[(run["id"], arm, identifier)] = row
    totals = {arm: {"detected": set(), "partial": set(), "false_alarms": 0,
                    "supported_findings": 0, "optional_preferences": 0,
                    "useful_repairs": 0, "harmful_repairs": 0, "preserve_damage": 0}
              for arm in ("claude_alone", "combined")}
    seen = set()
    for row in adjudications:
        key = (row["run"], row["arm"], row["candidate"])
        if key in seen or key not in candidate_rows:
            raise ValueError("Unknown or duplicate candidate adjudication")
        seen.add(key)
        if row["judgment"] not in {"supported", "partial", "false_alarm", "preference", "duplicate"}:
            raise ValueError("Invalid finding judgment")
        if row["repair"] not in {"useful", "harmful", "neutral"} or not row["reason"].strip():
            raise ValueError("Missing repair judgment or explanation")
        if not row["source_evidence"] or any(q not in inputs[row["run"]] for q in row["source_evidence"]):
            raise ValueError("Adjudication needs exact source evidence")
        issue = row.get("issue")
        if issue is not None and issue not in expected[row["run"]]:
            raise ValueError("A repaired or unknown issue cannot earn a detection")
        total = totals[row["arm"]]
        if row["judgment"] == "supported":
            total["supported_findings"] += 1
            if issue:
                total["detected"].add((row["run"], issue))
        elif row["judgment"] == "partial" and issue:
            total["partial"].add((row["run"], issue))
        elif row["judgment"] == "false_alarm":
            total["false_alarms"] += 1
        elif row["judgment"] == "preference":
            total["optional_preferences"] += 1
        total["useful_repairs"] += row["repair"] == "useful" and row["judgment"] == "supported"
        total["harmful_repairs"] += row["repair"] == "harmful"
        if row.get("damaged_control"):
            if row["damaged_control"] not in controls[row["run"]] or row["repair"] != "harmful":
                raise ValueError("Invalid preserved-passage damage claim")
            total["preserve_damage"] += 1
    if seen != set(candidate_rows):
        raise ValueError("Every candidate in both arms needs independent adjudication")
    all_expected = {(run_id, issue) for run_id, issues in expected.items() for issue in issues}
    added = totals["combined"]["detected"] - totals["claude_alone"]["detected"]
    lost = totals["claude_alone"]["detected"] - totals["combined"]["detected"]
    for total in totals.values():
        total["missed"] = sorted(all_expected - total["detected"])
        total["partial"] = sorted(total["partial"] - total["detected"])
        total["detected"] = sorted(total["detected"])
        total["expected_count"] = len(all_expected)
    return {"arms": totals, "added_by_combination": sorted(added),
            "lost_in_combination": sorted(lost), "runs": len(runs),
            "note": "Claude alone is its unrestricted blind first reading. Combined is accepted final craft findings/advice; authority and verdict agreement earn no detection credit. Repair scores assess proposed interventions against the source; no generated repair was applied or reader-tested."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("rubric", "runs", "adjudications"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(score(load(args.rubric), load(args.runs), load(args.adjudications)), indent=2))


if __name__ == "__main__":
    main()
