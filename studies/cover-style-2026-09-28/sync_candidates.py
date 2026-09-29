"""Copy the latest checked batch outputs into the study manifest."""

from __future__ import annotations

import json
from pathlib import Path


STUDY_DIR = Path(__file__).resolve().parent
MANIFEST = STUDY_DIR / "manifest.json"
PILOT_SLUGS = {
    "all-accounts-due", "apes-in-orbit", "daughter-of-the-sun",
    "what-the-town-owed-her",
}


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {entry["slug"]: entry for entry in data["entries"]}
    updated = 0
    prompt_dir = STUDY_DIR / "prompts"
    logs = sorted(prompt_dir.glob("group*.jsonl"))
    logs += [prompt_dir / name for name in (
        "remaining_a.jsonl", "remaining_b.jsonl", "crown_repair.jsonl"
    ) if (prompt_dir / name).exists()]
    for log in logs:
        for line in log.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            slug = row["slug"]
            if slug in PILOT_SLUGS or row.get("status") in {"approved_skip", "skipped_existing"}:
                continue
            if slug not in entries:
                raise ValueError(f"Unknown slug in {log}: {slug}")
            version = row.get("version", "painted-v1.jpg")
            if not version.endswith(".jpg"):
                version += ".jpg"
            path = row.get("output_path") or (
                f"studies/cover-style-2026-09-28/candidates/{slug}/{version}"
            )
            if not (STUDY_DIR.parents[1] / path).exists():
                continue
            entry = entries[slug]
            entry["candidate_path"] = path
            status = row.get("status")
            entry["candidate_status"] = (
                "candidate_review" if status == "candidate_review"
                else "review_needed" if status in {"review_needed", "needs_revision"}
                else "candidate_checked"
            )
            if row.get("qa_concern"):
                entry["candidate_notes"] = row["qa_concern"]
            else:
                entry.pop("candidate_notes", None)
            updated += 1
    MANIFEST.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Synced {updated} log entries")


if __name__ == "__main__":
    main()
