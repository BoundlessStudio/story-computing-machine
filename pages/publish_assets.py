"""Upload a built media manifest to R2 and verify every public CDN URL.

Only staged, hashed publication assets are uploaded. Existing objects are never
deleted, so a failed deployment or rollback cannot break earlier site versions.
Credentials are read from the environment, never from the manifest or arguments.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path, PurePosixPath
import re
import time
from urllib.error import URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

if __package__:
    from .media_assets import CACHE_CONTROL, CONTENT_TYPES, file_sha256, object_key, safe_asset_path, validate_base_url
else:
    from media_assets import CACHE_CONTROL, CONTENT_TYPES, file_sha256, object_key, safe_asset_path, validate_base_url


def load_manifest(path: Path) -> tuple[str, list[dict]]:
    """Validate the complete local input before any network writes."""
    data = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or data.get('schemaVersion') != 1
            or not isinstance(data.get('assets'), list)):
        raise ValueError('Invalid media manifest schema')
    base_url = validate_base_url(data.get('baseUrl', ''))
    seen_paths, unique_objects = set(), {}
    for entry in data['assets']:
        if not isinstance(entry, dict) or set(entry) != {'path', 'sha256', 'size', 'key', 'contentType'}:
            raise ValueError('Invalid media manifest entry')
        relative, digest = entry['path'], entry['sha256']
        if (not isinstance(relative, str) or not isinstance(digest, str)
                or not re.fullmatch(r'[a-f0-9]{64}', digest)
                or type(entry['size']) is not int or entry['size'] <= 0):
            raise ValueError('Invalid media path, hash, or size')
        source = safe_asset_path(path.parent, relative)
        if relative in seen_paths:
            raise ValueError(f'Duplicate media path: {relative}')
        seen_paths.add(relative)
        expected_type = CONTENT_TYPES.get(source.suffix.lower())
        if (not expected_type or entry['contentType'] != expected_type
                or entry['key'] != object_key(relative, digest)):
            raise ValueError(f'Invalid object key or content type: {relative}')
        if (not source.is_file() or source.stat().st_size != entry['size']
                or file_sha256(source) != digest):
            raise ValueError(f'Staged media missing or changed: {relative}')
        # Identical copies with the same basename share one immutable object.
        unique_objects.setdefault(entry['key'], entry)
    if not unique_objects:
        raise ValueError('Media manifest is empty')
    return base_url, list(unique_objects.values())


def object_headers(entry: dict) -> dict:
    headers = {
        'ContentType': entry['contentType'], 'CacheControl': CACHE_CONTROL,
        'Metadata': {'sha256': entry['sha256']},
    }
    if entry['contentType'] == 'application/pdf':
        name = PurePosixPath(entry['key']).name
        fallback = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
        # Cross-origin links cannot rely on the HTML download attribute.
        headers['ContentDisposition'] = f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(name, safe="")}'
    return headers


def verify_object(head: dict, entry: dict) -> None:
    expected = object_headers(entry) | {'ContentLength': entry['size']}
    if any(head.get(key) != value for key, value in expected.items()):
        raise ValueError(f'R2 object differs from the immutable manifest: {entry["path"]}')


def head_object(client, bucket: str, key: str):
    from botocore.exceptions import ClientError
    try:
        return client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 404:
            return None
        raise


def upload_object(client, bucket: str, root: Path, entry: dict) -> bool:
    from boto3.s3.transfer import TransferConfig
    existing = head_object(client, bucket, entry['key'])
    if existing is not None:
        verify_object(existing, entry)
        return False
    client.upload_file(
        str(safe_asset_path(root, entry['path'])), bucket, entry['key'],
        ExtraArgs=object_headers(entry), Config=TransferConfig(use_threads=False),
    )
    verify_object(head_object(client, bucket, entry['key']) or {}, entry)
    return True


def verify_public(base_url: str, entry: dict, attempts: int = 5) -> None:
    url = base_url + '/' + quote(entry['key'], safe='/')
    request = Request(url, method='HEAD', headers={'Accept-Encoding': 'identity'})
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=20) as response:
                expected = {
                    'Content-Type': entry['contentType'],
                    'Content-Length': str(entry['size']),
                    'Cache-Control': CACHE_CONTROL,
                }
                if entry['contentType'] == 'application/pdf':
                    expected['Content-Disposition'] = object_headers(entry)['ContentDisposition']
                if response.status != 200 or any(response.headers.get(k) != v for k, v in expected.items()):
                    raise ValueError('CDN response does not match the asset headers')
            return
        except (URLError, OSError, ValueError) as exc:
            if attempt + 1 == attempts:
                raise ValueError(f'Public CDN verification failed: {url}') from exc
            time.sleep(2 ** attempt)


def publish(manifest: Path, client, bucket: str, workers: int = 8) -> dict:
    base_url, entries = load_manifest(manifest)
    if not 1 <= workers <= 32:
        raise ValueError('Upload workers must be between 1 and 32')

    def upload_and_check(entry):
        uploaded = upload_object(client, bucket, manifest.parent, entry)
        verify_public(base_url, entry)
        return uploaded

    uploaded = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(upload_and_check, entry) for entry in entries]
        try:
            for count, future in enumerate(as_completed(futures), 1):
                uploaded += future.result()
                if count % 100 == 0 or count == len(entries):
                    print(f'R2/CDN verified {count}/{len(entries)} assets ({uploaded} uploaded)', flush=True)
        except Exception:
            for future in futures:
                future.cancel()
            raise
    return {'uploaded': uploaded, 'unchanged': len(entries) - uploaded, 'verified': len(entries)}


def r2_client():
    import boto3
    from botocore.config import Config
    names = ('R2_ENDPOINT', 'R2_BUCKET', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY')
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise ValueError('Missing R2 configuration: ' + ', '.join(missing))
    endpoint = urlsplit(validate_base_url(os.environ['R2_ENDPOINT']))
    if (not re.fullmatch(r'[a-f0-9]{32}\.r2\.cloudflarestorage\.com', endpoint.netloc)
            or endpoint.path not in {'', '/'}):
        raise ValueError('R2_ENDPOINT must be the account S3 API endpoint')
    client = boto3.client(
        's3', endpoint_url=os.environ['R2_ENDPOINT'], region_name='auto',
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        config=Config(
            signature_version='s3v4', retries={'mode': 'standard', 'max_attempts': 4},
            connect_timeout=10, read_timeout=60, max_pool_connections=32,
            request_checksum_calculation='when_required', response_checksum_validation='when_required',
        ),
    )
    return client, os.environ['R2_BUCKET']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('_assets/manifest.json'))
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    client, bucket = r2_client()
    result = publish(args.manifest, client, bucket, args.workers)
    print(f'R2 publication complete: {result["uploaded"]} uploaded, '
          f'{result["unchanged"]} reused, {result["verified"]} public URLs verified.')


if __name__ == '__main__':
    main()
