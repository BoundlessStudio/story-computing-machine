"""Stage published media separately from Pages, using immutable content URLs."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit


CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.webp': 'image/webp', '.gif': 'image/gif', '.avif': 'image/avif',
    '.svg': 'image/svg+xml', '.pdf': 'application/pdf',
}
CACHE_CONTROL = 'public, max-age=31536000, immutable'


def validate_base_url(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or any(c.isspace() for c in value) or '\\' in value):
        raise ValueError('Asset base URL must be an HTTPS URL without credentials, query, or fragment')
    return value.rstrip('/')


def safe_asset_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if (not relative or path.is_absolute() or ':' in relative or '\\' in relative
            or any(part in {'', '.', '..'} for part in relative.split('/'))):
        raise ValueError(f'Unsafe media path: {relative}')
    target = (root / relative).resolve()
    if root.resolve() not in target.parents:
        raise ValueError(f'Media path escapes its root: {relative}')
    return target


def file_sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def object_key(relative: str, digest: str) -> str:
    # Keep the basename for readable image URLs and PDF downloads.
    return f'assets/{digest}/{PurePosixPath(relative).name}'


class MediaAssets:
    def __init__(self, root: Path, base_url: str):
        self.root = root.resolve()
        self.base_url = validate_base_url(base_url)
        self.entries: dict[str, dict] = {}

    def add(self, source: Path, relative: str) -> None:
        target = safe_asset_path(self.root, relative)
        content_type = CONTENT_TYPES.get(target.suffix.lower())
        if content_type is None:
            raise ValueError(f'Unsupported published media: {relative}')
        if relative in self.entries:
            raise ValueError(f'Duplicate published media path: {relative}')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        digest = file_sha256(target)
        self.entries[relative] = {
            'path': relative, 'sha256': digest, 'size': target.stat().st_size,
            'key': object_key(relative, digest), 'contentType': content_type,
        }

    def url(self, relative: str) -> str:
        if relative not in self.entries:
            raise ValueError(f'Media referenced before staging: {relative}')
        return self.base_url + '/' + quote(self.entries[relative]['key'], safe='/')

    def write_manifest(self) -> None:
        data = {
            'schemaVersion': 1, 'baseUrl': self.base_url,
            'assets': [self.entries[path] for path in sorted(self.entries)],
        }
        (self.root / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def asset_url(relative: str, prefix: str = '', media: MediaAssets | None = None) -> str:
    return media.url(relative) if media is not None else prefix + relative


def copy_asset(source: Path, destination: Path, relative: str, media: MediaAssets | None = None) -> None:
    if media is not None:
        media.add(source, relative)
    else:
        target = safe_asset_path(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
