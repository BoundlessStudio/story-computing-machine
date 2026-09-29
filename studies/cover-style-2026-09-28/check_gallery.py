"""Check that the local comparison gallery links to every selected image."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


STUDY_DIR = Path(__file__).resolve().parent


class ImageCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []
        self.cards = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and values.get("src"):
            self.sources.append(values["src"])
        if tag == "article" and values.get("class") == "card":
            self.cards += 1


def main() -> None:
    parser = ImageCollector()
    parser.feed((STUDY_DIR / "gallery.html").read_text(encoding="utf-8"))
    missing = [source for source in parser.sources if not (STUDY_DIR / source).exists()]
    print({"cards": parser.cards, "images": len(parser.sources), "broken": len(missing)})
    for source in missing:
        print(f"MISSING {source}")
    if parser.cards != 200 or len(parser.sources) != 393 or missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
