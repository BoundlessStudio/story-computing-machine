"""Upload selected immutable art to Cloudflare R2, then verify its public URLs."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import time
from urllib.error import URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .assets import CONTENT_TYPES, IMMUTABLE_CACHE, INDEX_KEY, base_url, object_key, public_url, sha256, source_file
from .manifest import ROOT, selected_paths, selection_notes, tracked_paths


MAX_CACHE_AGE = 7 * 24 * 60 * 60
USER_AGENT = "StoryComputingMachine-MediaPublisher/1.0"


def load_manifest(path: Path, root: Path) -> tuple[dict, list[dict]]:
    """Validate every input and source byte before making a network write."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict)
            or set(manifest) != {"schemaVersion", "sourceCommit", "baseUrl", "indexUrl", "assets"}
            or manifest["schemaVersion"] != 1 or not isinstance(manifest["assets"], list)
            or not re.fullmatch(r"[a-f0-9]{40}", manifest["sourceCommit"])):
        raise ValueError("Invalid public media manifest")
    origin = base_url(manifest["baseUrl"])
    if manifest["indexUrl"] != public_url(origin, INDEX_KEY):
        raise ValueError("Invalid public index URL")
    tracked = tracked_paths(root)
    excluded, corrections = selection_notes(root, tracked)
    expected_paths = selected_paths(tracked, excluded, corrections)
    seen = set()
    unique = {}
    for entry in manifest["assets"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "size", "key", "contentType", "url"}:
            raise ValueError("Invalid media entry")
        relative, digest = entry["path"], entry["sha256"]
        if (not isinstance(relative, str) or relative in seen or not isinstance(digest, str)
                or not re.fullmatch(r"[a-f0-9]{64}", digest)
                or type(entry["size"]) is not int or entry["size"] <= 0):
            raise ValueError(f"Duplicate or invalid media: {relative}")
        seen.add(relative)
        file = source_file(root, relative)
        key = object_key(relative, digest)
        if (entry["size"] != file.stat().st_size or entry["sha256"] != sha256(file)
                or entry["key"] != key or entry["url"] != public_url(origin, key)
                or entry["contentType"] != CONTENT_TYPES.get(file.suffix.lower())):
            raise ValueError(f"Source media changed or URL mismatch: {relative}")
        unique.setdefault(key, entry)
    if sorted(seen) != expected_paths or not unique:
        raise ValueError("Media manifest does not exactly match selected source art")
    return manifest, list(unique.values())


def object_headers(entry: dict) -> dict:
    headers = {
        "ContentType": entry["contentType"], "CacheControl": IMMUTABLE_CACHE,
        "Metadata": {"sha256": entry["sha256"]},
    }
    if entry["contentType"] == "application/pdf":
        name = PurePosixPath(entry["key"]).name
        fallback = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
        headers["ContentDisposition"] = (
            f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(name, safe="")}'
        )
    return headers


def head_object(client, bucket: str, key: str):
    from botocore.exceptions import ClientError
    try:
        return client.head_object(Bucket=bucket, Key=key)
    except ClientError as error:
        if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
            return None
        raise


def verify_object(head: dict, entry: dict) -> None:
    expected = object_headers(entry) | {"ContentLength": entry["size"]}
    if any(head.get(field) != value for field, value in expected.items()):
        raise ValueError(f"R2 object differs from content-addressed source: {entry['path']}")


def upload_object(client, bucket: str, root: Path, entry: dict) -> bool:
    from boto3.s3.transfer import TransferConfig
    existing = head_object(client, bucket, entry["key"])
    if existing is not None:
        verify_object(existing, entry)
        return False
    client.upload_file(
        str(source_file(root, entry["path"])), bucket, entry["key"],
        ExtraArgs=object_headers(entry), Config=TransferConfig(use_threads=False),
    )
    verify_object(head_object(client, bucket, entry["key"]) or {}, entry)
    return True


def verify_public(entry: dict, attempts: int = 5) -> None:
    request = Request(entry["url"], method="HEAD", headers={
        "Accept-Encoding": "identity", "User-Agent": USER_AGENT,
    })
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=20) as response:
                expected = {
                    "Content-Type": entry["contentType"],
                    "Content-Length": str(entry["size"]),
                    "Cache-Control": IMMUTABLE_CACHE,
                }
                if entry["contentType"] == "application/pdf":
                    expected["Content-Disposition"] = object_headers(entry)["ContentDisposition"]
                if response.status != 200 or any(response.headers.get(k) != v for k, v in expected.items()):
                    raise ValueError("Public asset headers differ from R2")
            return
        except (URLError, OSError, ValueError) as error:
            if attempt + 1 == attempts:
                raise ValueError(f"Public URL verification failed: {entry['url']}") from error
            time.sleep(2 ** attempt)


def verification_record(entry: dict) -> dict:
    return {"size": entry["size"], "headers": object_headers(entry)}


def load_cache(path: Path | None, scope: dict) -> dict:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if (not isinstance(data, dict) or data.get("schemaVersion") != 1
            or data.get("scope") != scope or not isinstance(data.get("objects"), dict)):
        return {}
    return data["objects"]


def save_cache(path: Path, scope: dict, records: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "schemaVersion": 1, "scope": scope, "objects": records,
    }, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def publish_index(client, bucket: str, manifest_path: Path, manifest: dict) -> None:
    payload = manifest_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    headers = {
        "ContentType": "application/json", "CacheControl": "public, max-age=60, must-revalidate",
        "Metadata": {"sha256": digest},
    }
    client.put_object(Bucket=bucket, Key=INDEX_KEY, Body=payload, **headers)
    head = head_object(client, bucket, INDEX_KEY) or {}
    if any(head.get(field) != value for field, value in (headers | {"ContentLength": len(payload)}).items()):
        raise ValueError("R2 public index differs from the verified manifest")
    # A versioned query bypasses an older cached copy while retaining one stable index URL.
    url = manifest["indexUrl"] + "?v=" + digest[:16]
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200 or response.read() != payload:
            raise ValueError(f"Public media index verification failed: {manifest['indexUrl']}")


def publish(manifest_path: Path, root: Path, client, bucket: str, *, workers: int = 12,
            cache_path: Path | None = None, verify_all: bool = False,
            update_index: bool = False) -> dict:
    manifest, entries = load_manifest(manifest_path, root)
    if not 1 <= workers <= 32:
        raise ValueError("Workers must be between 1 and 32")
    now = time.time()
    scope = {"endpoint": client.meta.endpoint_url, "bucket": bucket, "baseUrl": manifest["baseUrl"]}
    previous = {} if verify_all else load_cache(cache_path, scope)
    records, cached, pending = {}, [], []
    for entry in entries:
        record = previous.get(entry["key"])
        if (isinstance(record, dict) and type(record.get("verifiedAt")) in (int, float)
                and 0 <= now - record["verifiedAt"] < MAX_CACHE_AGE
                and record == verification_record(entry) | {"verifiedAt": record["verifiedAt"]}):
            cached.append(entry)
            records[entry["key"]] = record
        else:
            pending.append(entry)
    if cached:
        verify_public(cached[int(now) % len(cached)])
    print(f"R2/CDN: {len(cached)} cached, {len(pending)} require full verification", flush=True)

    def upload_and_check(entry):
        was_uploaded = upload_object(client, bucket, root, entry)
        verify_public(entry)
        return entry, was_uploaded

    uploaded = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(upload_and_check, entry) for entry in pending]
        try:
            for count, future in enumerate(as_completed(futures), 1):
                entry, was_uploaded = future.result()
                uploaded += was_uploaded
                records[entry["key"]] = verification_record(entry) | {"verifiedAt": now}
                if count % 100 == 0 or count == len(pending):
                    print(f"R2/CDN verified {count}/{len(pending)} assets ({uploaded} uploaded)", flush=True)
        except Exception:
            for future in futures:
                future.cancel()
            raise
    if update_index:
        publish_index(client, bucket, manifest_path, manifest)
    if cache_path:
        save_cache(cache_path, scope, records)
    return {
        "assets": len(manifest["assets"]), "uploaded": uploaded,
        "verified": len(pending) + bool(cached), "cached": len(cached),
        "indexUrl": manifest["indexUrl"] if update_index else None,
    }


def r2_client():
    import boto3
    from botocore.config import Config
    names = ("R2_ENDPOINT", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise ValueError("Missing R2 configuration: " + ", ".join(missing))
    endpoint = urlsplit(base_url(os.environ["R2_ENDPOINT"]))
    if (not re.fullmatch(r"[a-f0-9]{32}\.r2\.cloudflarestorage\.com", endpoint.netloc)
            or endpoint.path not in {"", "/"}):
        raise ValueError("R2_ENDPOINT must be the account S3 API endpoint")
    client = boto3.client(
        "s3", endpoint_url=os.environ["R2_ENDPOINT"], region_name="auto",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(
            signature_version="s3v4", retries={"mode": "standard", "max_attempts": 4},
            connect_timeout=10, read_timeout=60, max_pool_connections=32,
            request_checksum_calculation="when_required", response_checksum_validation="when_required",
        ),
    )
    return client, os.environ["R2_BUCKET"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("_media/manifest.json"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--verification-cache", type=Path)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--verify-all", action="store_true")
    parser.add_argument("--publish-index", action="store_true")
    args = parser.parse_args()
    client, bucket = r2_client()
    result = publish(
        args.manifest, args.root, client, bucket, workers=args.workers,
        cache_path=args.verification_cache, verify_all=args.verify_all,
        update_index=args.publish_index,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
