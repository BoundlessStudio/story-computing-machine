"""Visual dependency checks and compact attempt evidence in the edition manifest.

These numbers describe recorded attempts, never account usage or image-tool billing.
No generation budget or attempt limit is imposed by this module.
"""
from collections import Counter
from datetime import datetime, timezone
from typing import Any


def assets(manifest: dict) -> list[dict]:
    return [manifest["cover"], *manifest["references"], *manifest["illustrations"]]


def dependency_ids(manifest: dict, roots: list[str]) -> set[str]:
    """Return generated dependencies, rejecting cycles even before pixels exist."""
    by_id = {asset["id"]: asset for asset in assets(manifest)}
    found: set[str] = set()

    def visit(asset_id: str, visiting: set[str]) -> None:
        if asset_id in visiting:
            raise ValueError(f"Circular visual dependency: {asset_id}")
        if asset_id not in by_id or asset_id in found:
            return
        for reference in by_id[asset_id].get("references", []):
            visit(reference, visiting | {asset_id})
            if reference in by_id:
                found.add(reference)

    for asset_id in roots:
        visit(asset_id, set())
    return found


def unused_references(manifest: dict) -> list[str]:
    roots = [asset["id"] for asset in manifest["illustrations"]]
    if not manifest["cover"].get("reused", True):
        roots.append("cover")
    used = dependency_ids(manifest, roots)
    return [asset["id"] for asset in manifest["references"] if asset["id"] not in used]


def pilot_references(manifest: dict) -> list[dict]:
    pilot_id = manifest["productionPolicy"]["pilotAssetId"]
    dependencies = dependency_ids(manifest, [pilot_id, "cover"])
    return [asset for asset in manifest["references"] if asset["id"] in dependencies]


def attempted_assets(manifest: dict) -> list[dict]:
    result = [*assets(manifest), *manifest.get("retiredAssets", [])]
    ids = [asset["id"] for asset in result]
    if len(ids) != len(set(ids)):
        raise ValueError("Active and retired asset IDs must remain unique")
    for asset in result:
        count = asset.get("attempts", 0)
        if type(count) is not int or count < 0:
            raise ValueError("Recorded attempt counts must be nonnegative integers")
    return result


def attempts_used(manifest: dict) -> int:
    return sum(asset.get("attempts", 0) for asset in attempted_assets(manifest))


def validate_policy(manifest: dict, *, complete: bool = False) -> None:
    if "productionPolicy" not in manifest:
        return
    policy = manifest["productionPolicy"]
    if not isinstance(policy, dict) or policy.get("version") != 1:
        raise ValueError("Unsupported illustrated production policy")
    attempted_assets(manifest)
    if not complete:
        return
    illustrations = {asset["id"]: asset for asset in manifest["illustrations"]}
    pilot_id = policy.get("pilotAssetId")
    if pilot_id not in illustrations:
        raise ValueError("Configure a centerpiece illustration before plan approval")
    if illustrations.keys() & dependency_ids(manifest, [pilot_id, "cover"]):
        raise ValueError("The centerpiece and cover must be generatable from references without another scene")
    later_scene_dependencies = (illustrations.keys() - {pilot_id}) & dependency_ids(
        manifest, [asset["id"] for asset in manifest["references"]]
    )
    if later_scene_dependencies:
        raise ValueError(
            "References must be completed before the remaining scenes; they cannot depend on non-centerpiece illustrations: "
            + ", ".join(sorted(later_scene_dependencies))
        )
    unused = unused_references(manifest)
    if unused:
        raise ValueError("Remove unneeded references before plan approval: " + ", ".join(unused))
    for asset in illustrations.values():
        if not isinstance(asset.get("sceneState"), str) or not asset["sceneState"].strip():
            raise ValueError(f"Record the exact visible source state for {asset['id']} with --state-file")
    for asset in assets(manifest):
        if asset.get("reused"):
            continue
        roles = asset.get("referenceRoles", {})
        if (not isinstance(roles, dict) or set(roles) != set(asset.get("references", []))
                or any(not isinstance(value, str) or not value.strip() for value in roles.values())):
            raise ValueError(f"Specify the content/style/state role of every input for {asset['id']} with --reference-role")


def record_attempt(asset: dict, status: str, *, evidence: str = "") -> None:
    """Update one flat attempt entry; absent historical times are never fabricated."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    history = asset.setdefault("attemptHistory", [])
    number = asset["attempts"]
    entry = next((item for item in history if item["attempt"] == number), None)
    if entry is None:
        entry = {"attempt": number}
        history.append(entry)
    candidate = asset.get("candidate", {})
    if status == "generating":
        entry.update(startedAt=now, backend=candidate.get("backend"),
                     operation="edit" if candidate.get("request", {}).get("editBase") else "generate")
    elif status in {"ready", "failed"} and not entry.get("resolvedAt"):
        entry["resolvedAt"] = now
        if entry.get("startedAt"):
            seconds = (datetime.fromisoformat(now) - datetime.fromisoformat(entry["startedAt"])).total_seconds()
            entry["generationSeconds"] = max(0, seconds)
    elif status in {"accepted", "rejected"}:
        entry["reviewedAt"] = now
    entry["status"] = status
    if candidate.get("sha256"):
        entry["outputSha256"] = candidate["sha256"]
    if evidence:
        entry["evidence"] = evidence


def statistics(manifest: dict) -> dict[str, Any]:
    active = assets(manifest)
    all_assets = attempted_assets(manifest)
    generated = [asset for asset in active if not asset.get("reused", False)]
    used = attempts_used(manifest)
    histories = [entry for asset in all_assets for entry in asset.get("attemptHistory", [])]
    timed = [entry for entry in histories if "generationSeconds" in entry]
    rows = [{"id": asset["id"], "kind": asset["kind"], "retired": asset not in active,
             "attempts": asset.get("attempts", 0), "selected": bool(asset.get("accepted")),
             "status": asset.get("candidate", {}).get("status", "accepted" if asset.get("accepted") else "planned")}
            for asset in all_assets]
    return {
        "slug": manifest["slug"],
        "planned": {"references": len(manifest["references"]), "illustrations": len(manifest["illustrations"]),
                    "generatedCovers": int(not manifest["cover"].get("reused", True)), "generatedAssets": len(generated)},
        "attempts": {"total": used, "active": sum(asset.get("attempts", 0) for asset in active),
                     "retired": sum(asset.get("attempts", 0) for asset in manifest.get("retiredAssets", [])),
                     "withoutRecordedOutcome": used - len(histories), "recordedOutcomes": dict(Counter(entry["status"] for entry in histories))},
        "timing": {"timedAttempts": len(timed), "generationSeconds": sum(entry["generationSeconds"] for entry in timed) if timed else None,
                   "basis": "Reservation to recorded completion/failure, including tool waits and recording delay; excludes unrecorded historical durations."},
        "unusedReferences": unused_references(manifest), "assets": rows,
        "usageNote": "Attempt counts and timings are not weekly usage percentages or image billing. Account-wide quota must be checked separately.",
    }
