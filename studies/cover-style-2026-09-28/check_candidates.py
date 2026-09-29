"""Validate study candidate files without changing story packages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


STUDY_DIR = Path(__file__).resolve().parent
REPO_ROOT = STUDY_DIR.parents[1]
MANIFEST = STUDY_DIR / "manifest.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    counts = {"source": len(data["entries"]), "skipped": 0, "ready": 0, "missing": 0, "invalid": 0}
    issues = []
    for entry in data["entries"]:
        slug = entry["slug"]
        if entry["style_status"] == "skip_already_painted":
            counts["skipped"] += 1
            continue
        candidate = REPO_ROOT / entry["candidate_path"]
        source = REPO_ROOT / entry["source_cover_path"]
        if not candidate.exists():
            counts["missing"] += 1
            issues.append(f"MISSING {slug}: {candidate.relative_to(REPO_ROOT)}")
            continue
        try:
            candidate.resolve().relative_to(STUDY_DIR.resolve())
            with Image.open(candidate) as image:
                if image.format != "JPEG" or image.size != (864, 1536):
                    raise ValueError(f"{image.format} {image.size}")
                image.verify()
            if digest(candidate) == digest(source):
                raise ValueError("candidate is byte-identical to source")
        except (ValueError, OSError) as exc:
            counts["invalid"] += 1
            issues.append(f"INVALID {slug}: {exc}")
            continue
        counts["ready"] += 1
    print(json.dumps(counts, indent=2))
    for issue in issues:
        print(issue)
    if counts["invalid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
