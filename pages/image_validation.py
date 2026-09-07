"""The shared technical cover check; visual editorial review remains separate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFile
except ImportError as exc:
    print(
        "Cover validation requires Pillow. Install dependencies with "
        "python -m pip install -r pages/requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc

TITLE_IMAGE_WIDTH = 864
TITLE_IMAGE_HEIGHT = 1536
ImageFile.LOAD_TRUNCATED_IMAGES = False


def validate_title_image(path: Path) -> None:
    try:
        with Image.open(path) as image:
            if image.format != "JPEG":
                raise ValueError(f"{path} is not a JPEG")
            if image.size != (TITLE_IMAGE_WIDTH, TITLE_IMAGE_HEIGHT):
                raise ValueError(
                    f"{path} must be exactly {TITLE_IMAGE_WIDTH}x{TITLE_IMAGE_HEIGHT}; "
                    f"found {image.width}x{image.height}"
                )
            image.load()
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError(f"{path} is not a readable JPEG: {exc}") from exc


def main() -> int:
    """Validate a JSON path array from stdin in one PowerShell subprocess."""
    try:
        paths = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
            raise ValueError("Expected a JSON array of image paths")
    except (ValueError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    errors = []
    for path in paths:
        try:
            validate_title_image(Path(path))
        except ValueError as exc:
            errors.append(str(exc))
    print(json.dumps(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
