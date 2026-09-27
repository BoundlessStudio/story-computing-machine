"""Shared URL and file validation for the independent R2 art publisher."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit


CONTENT_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".pdf": "application/pdf",
}
IMMUTABLE_CACHE = "public, max-age=31536000, immutable"
INDEX_KEY = "manifests/story-computing-machine-art-v1.json"


def base_url(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Media origin must be an HTTPS URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or any(character.isspace() for character in value) or "\\" in value):
        raise ValueError("Media origin must be an HTTPS URL without credentials, query, or fragment")
    return value.rstrip("/")


def source_file(root: Path, relative: str) -> Path:
    if (not isinstance(relative, str) or not relative or ":" in relative or "\\" in relative
            or PurePosixPath(relative).is_absolute()
            or any(part in {"", ".", ".."} for part in relative.split("/"))):
        raise ValueError(f"Unsafe source path: {relative}")
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    if resolved_root not in path.parents or not path.is_file():
        raise ValueError(f"Missing or escaping source file: {relative}")
    return path


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def object_key(relative: str, digest: str) -> str:
    return f"assets/{digest}/{PurePosixPath(relative).name}"


def public_url(origin: str, key: str) -> str:
    return base_url(origin) + "/" + quote(key, safe="/")
