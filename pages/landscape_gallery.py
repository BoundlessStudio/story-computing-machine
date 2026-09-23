"""Capture landscape and interior studies; build from their frozen snapshots."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
from io import BytesIO
import json
from pathlib import Path
import re
import shutil

from PIL import Image, ImageOps

if __package__:
    from .media_assets import asset_url, copy_asset
else:
    from media_assets import asset_url, copy_asset

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
ASSET_NAMES = ("landscape-gallery.css", "landscape-gallery.js")
COLLECTIONS = {"landscapes": "Landscape", "interiors": "Interior"}
REPLACEMENT_ROOTS = {
    "landscapes": "pages/landscape-replacements",
    "interiors": "pages/interior-replacements",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _asset(root: Path, path: str) -> Path:
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Landscape asset escapes its snapshot: {path}")
    return resolved


def load_snapshot(path: Path, collection: str = "landscapes") -> dict:
    if collection not in COLLECTIONS:
        raise ValueError(f"Unknown art collection: {collection}")
    if not path.exists():
        return {"schemaVersion": 1, "stories": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read landscape snapshot: {path}") from exc
    if not isinstance(data, dict) or data.get("schemaVersion") != 1 or not isinstance(data.get("stories"), list):
        raise ValueError("Invalid landscape snapshot schema")
    exclusions = data.get("excludedSources", [])
    if not isinstance(exclusions, list):
        raise ValueError("Invalid landscape exclusions")
    excluded = set()
    for exclusion in exclusions:
        source = exclusion.get("source", "") if isinstance(exclusion, dict) else ""
        parts = source.split("/") if isinstance(source, str) else []
        if (len(parts) != 5 or parts[0] != "stories" or not SLUG.fullmatch(parts[1])
                or parts[2:4] != ["art", collection]
                or Path(parts[4]).suffix not in {".png", ".jpg", ".jpeg", ".webp"}
                or not SLUG.fullmatch(Path(parts[4]).stem) or source in excluded):
            raise ValueError(f"Invalid or duplicate excluded landscape source: {source}")
        if not isinstance(exclusion.get("sourceSha256"), str) or not DIGEST.fullmatch(exclusion["sourceSha256"]):
            raise ValueError(f"Invalid excluded landscape source hash: {source}")
        if not isinstance(exclusion.get("reason"), str) or not exclusion["reason"].strip():
            raise ValueError(f"Missing landscape exclusion reason: {source}")
        excluded.add(source)
    exclusions_by_source = {entry["source"]: entry for entry in exclusions}
    slugs = set()
    for story in data["stories"]:
        if not isinstance(story, dict):
            raise ValueError("Invalid landscape story")
        slug = story.get("slug", "")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug in slugs:
            raise ValueError(f"Invalid or duplicate landscape story: {slug}")
        slugs.add(slug)
        if not isinstance(story.get("title"), str) or not story["title"].strip():
            raise ValueError(f"Missing landscape story title: {slug}")
        if story.get("reader") != f"stories/{slug}.html":
            raise ValueError(f"Invalid landscape story reader: {slug}")
        if not isinstance(story.get("images"), list) or not story["images"]:
            raise ValueError(f"Missing landscape images: {slug}")
        ids = set()
        for image in story["images"]:
            image_id = image.get("id", "") if isinstance(image, dict) else ""
            if not isinstance(image_id, str) or not SLUG.fullmatch(image_id) or image_id in ids:
                raise ValueError(f"Invalid or duplicate landscape image: {slug}/{image_id}")
            ids.add(image_id)
            for key in ("title", "alt"):
                if not isinstance(image.get(key), str) or not image[key].strip():
                    raise ValueError(f"Missing landscape {key}: {slug}/{image_id}")
            if not isinstance(image.get("sourceSha256"), str) or not DIGEST.fullmatch(image["sourceSha256"]):
                raise ValueError(f"Invalid landscape source hash: {slug}/{image_id}")
            source = image.get("source", "")
            original_sources = {f"stories/{slug}/art/{collection}/{image_id}{ext}" for ext in (".png", ".jpg", ".jpeg", ".webp")}
            replacement_source = f"{REPLACEMENT_ROOTS[collection]}/{slug}/{image_id}.png"
            allowed_sources = original_sources | {replacement_source}
            if not isinstance(source, str) or source not in allowed_sources:
                raise ValueError(f"Invalid landscape source path: {source}")
            revision = image.get("revision")
            if source == replacement_source:
                if not isinstance(revision, dict):
                    raise ValueError(f"Missing replacement provenance: {source}")
                reference = revision.get("originalSource")
                if not isinstance(reference, str) or reference not in original_sources or reference not in excluded:
                    raise ValueError(f"Replacement requires its excluded original: {source}")
                if revision.get("originalSha256") != exclusions_by_source[reference]["sourceSha256"]:
                    raise ValueError(f"Replacement reference hash differs from the reviewed original: {source}")
                if any(not isinstance(revision.get(key), str) or not revision[key].strip()
                       for key in ("correction", "prompt", "generator")):
                    raise ValueError(f"Incomplete replacement provenance: {source}")
            elif revision is not None:
                raise ValueError(f"Replacement provenance requires separate replacement artwork: {source}")
            if source in excluded:
                raise ValueError(f"Excluded landscape is still selected: {source}")
            for role, suffix in (("full", ""), ("thumbnail", "-thumb")):
                asset = image.get(role)
                expected = f"{collection}/{slug}/{image_id}{suffix}.webp"
                versioned = f"{collection}/{slug}/{image_id}-{image['sourceSha256'][:16]}{suffix}.webp"
                if not isinstance(asset, dict) or asset.get("path") not in (expected, versioned):
                    raise ValueError(f"Invalid landscape {role} path: {slug}/{image_id}")
                if not isinstance(asset.get("sha256"), str) or not DIGEST.fullmatch(asset["sha256"]):
                    raise ValueError(f"Invalid landscape asset hash: {expected}")
                if any(type(asset.get(key)) is not int or asset[key] <= 0 for key in ("width", "height")):
                    raise ValueError(f"Invalid landscape dimensions: {expected}")
                if asset["width"] <= asset["height"]:
                    raise ValueError(f"Expected horizontal landscape: {expected}")
                _asset(path.parent, asset["path"])
    return data


def _encode(job: tuple[Path, Path, Path, str, str, dict | None, str]) -> dict:
    source, repository_root, pages_root, slug, story_title, previous, collection = job
    image_id = source.stem
    if not SLUG.fullmatch(image_id):
        raise ValueError(f"Landscape filename must use lowercase words and hyphens: {source.name}")
    relative_source = source.resolve().relative_to(repository_root.resolve()).as_posix()
    source_bytes = source.read_bytes()
    caption = re.sub(r"^\d+-", "", image_id).replace("-", " ").capitalize()
    result = {
        "id": image_id, "title": caption,
        "alt": f"{caption} — oil {COLLECTIONS[collection].lower()} study for {story_title}",
        "source": relative_source, "sourceSha256": hashlib.sha256(source_bytes).hexdigest(),
    }
    if previous and previous["sourceSha256"] == result["sourceSha256"]:
        if all(
            (asset := _asset(pages_root, previous[role]["path"])).is_file()
            and _sha256(asset) == previous[role]["sha256"]
            for role in ("full", "thumbnail")
        ):
            return {**result, **{role: previous[role] for role in ("full", "thumbnail")}}
    with Image.open(BytesIO(source_bytes)) as opened:
        opened.load()
        image = ImageOps.exif_transpose(opened).convert("RGB")
    if image.width <= image.height:
        raise ValueError(f"Expected a horizontal landscape: {source}")
    for role, suffix, quality in (("full", "", 80), ("thumbnail", "-thumb", 70)):
        rendition = image
        if role == "thumbnail":
            rendition = image.copy()
            rendition.thumbnail((480, 320), Image.Resampling.LANCZOS)
        # New source bytes receive new paths, keeping the selected snapshot usable
        # even if a later image in this capture fails validation or encoding.
        relative = f"{collection}/{slug}/{image_id}-{result['sourceSha256'][:16]}{suffix}.webp"
        destination = _asset(pages_root, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        rendition.save(destination, format="WEBP", quality=quality, method=5)
        result[role] = {"path": relative, "sha256": _sha256(destination),
                        "width": rendition.width, "height": rendition.height}
    return result


def capture_landscapes(repository_root: Path, snapshot_path: Path | None = None) -> dict:
    return _capture_collection(repository_root, "landscapes", snapshot_path)


def capture_interiors(repository_root: Path, snapshot_path: Path | None = None, slugs: list[str] | None = None) -> dict:
    return _capture_collection(repository_root, "interiors", snapshot_path, slugs)


def _capture_collection(repository_root: Path, collection: str, snapshot_path: Path | None,
                        slugs: list[str] | None = None) -> dict:
    from pages import build

    repository_root = repository_root.resolve()
    snapshot_path = snapshot_path or repository_root / "pages" / f"{collection}.json"
    catalog = build.load_catalog(snapshot_path.with_name("catalog.json"))
    published = {story.slug: story for story in catalog.stories}
    requested = set(slugs) if slugs else None
    if requested and any(slug not in published for slug in requested):
        raise ValueError("An art study story is absent from the publication catalog")
    prior = load_snapshot(snapshot_path, collection)
    previous = {(story["slug"], image["id"]): image
                for story in prior["stories"] for image in story["images"]}
    excluded = {entry["source"] for entry in prior.get("excludedSources", [])}
    groups = [story for story in prior["stories"] if requested and story["slug"] not in requested]
    jobs = []
    found = set()
    for directory in sorted((repository_root / "stories").glob(f"*/art/{collection}")):
        slug = directory.parents[1].name
        if slug == "_template" or (requested and slug not in requested):
            continue
        if slug not in published:
            raise ValueError(f"Landscape story is absent from the publication catalog: {slug}")
        sources = sorted(p for p in directory.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and p.is_file())
        if not sources:
            raise ValueError(f"No landscape images in {directory}")
        if len({p.stem for p in sources}) != len(sources):
            raise ValueError(f"Repeated landscape filename stem in {directory}")
        found.add(slug)
        # Curatorial removals remain excluded even when source artwork is kept
        # inside a locked story package or later receives different bytes.
        sources = [source for source in sources
                   if source.relative_to(repository_root).as_posix() not in excluded]
        if not sources:
            continue
        story = published[slug]
        groups.append({"slug": slug, "title": story.title, "reader": f"stories/{slug}.html", "images": []})
        jobs.extend((source, repository_root, snapshot_path.parent, slug, story.title,
                     previous.get((slug, source.stem)), collection) for source in sources)
    if requested and requested - found:
        raise ValueError(f"No {collection} source directory for: {', '.join(sorted(requested - found))}")
    selected = {story["slug"]: story for story in groups}
    # Replacement originals live outside locked story packages. Only explicitly
    # selected replacements are captured; directory scans never select candidates.
    for (slug, _), image in previous.items():
        if "revision" not in image or (requested and slug not in requested):
            continue
        if slug not in published:
            raise ValueError(f"Landscape story is absent from the publication catalog: {slug}")
        source = _asset(repository_root, image["source"])
        if not source.is_file() or _sha256(source) != image["sourceSha256"]:
            raise ValueError(f"Replacement artwork changed since review: {image['source']}")
        if slug not in selected:
            story = published[slug]
            selected[slug] = {"slug": slug, "title": story.title, "reader": f"stories/{slug}.html", "images": []}
            groups.append(selected[slug])
        jobs.append((source, repository_root, snapshot_path.parent, slug,
                     published[slug].title, image, collection))
    # Resolve and create shared folders before parallel encoders access them.
    for slug in sorted({job[3] for job in jobs}):
        _asset(snapshot_path.parent, f"{collection}/{slug}").mkdir(parents=True, exist_ok=True)
    # Only this explicit capture operation reads production art or encodes web copies.
    with ThreadPoolExecutor(max_workers=8) as executor:
        for job, image in zip(jobs, executor.map(_encode, jobs)):
            if job[5] and "revision" in job[5]:
                image.update({key: job[5][key] for key in ("title", "alt", "revision")})
            selected[job[3]]["images"].append(image)
    for group in groups:
        group["images"].sort(key=lambda image: image["id"])
    groups.sort(key=lambda story: (story["title"].casefold(), story["slug"]))
    data = {"schemaVersion": 1, "stories": groups}
    if prior.get("excludedSources"):
        data["excludedSources"] = prior["excludedSources"]
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    pending = snapshot_path.with_suffix(".json.tmp")
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_snapshot(pending, collection)
    check_assets(data, snapshot_path.parent)
    pending.replace(snapshot_path)
    old_assets = {image[role]["path"] for image in previous.values() for role in ("full", "thumbnail")}
    selected_assets = {image[role]["path"] for story in groups for image in story["images"] for role in ("full", "thumbnail")}
    for obsolete in old_assets - selected_assets:
        _asset(snapshot_path.parent, obsolete).unlink(missing_ok=True)
    return data


def check_assets(data: dict, pages_root: Path) -> int:
    count = 0
    for story in data["stories"]:
        for image in story["images"]:
            for role in ("full", "thumbnail"):
                asset = image[role]
                source = _asset(pages_root, asset["path"])
                if not source.is_file() or _sha256(source) != asset["sha256"]:
                    raise ValueError(f"Missing or changed landscape snapshot asset: {asset['path']}")
            count += 1
    return count


def _combine_collections(landscapes: dict, interiors: dict | None = None) -> dict:
    stories = {}
    for collection, data in (("landscapes", landscapes), ("interiors", interiors or {"stories": []})):
        for story in data["stories"]:
            group = stories.setdefault(story["slug"], {**story, "images": []})
            group["images"].extend({**image, "collection": collection} for image in story["images"])
    return {"stories": sorted(stories.values(), key=lambda story: (story["title"].casefold(), story["slug"]))}


def render_gallery(landscapes: dict, interiors: dict | None = None, media=None) -> str:
    from pages import build

    data = _combine_collections(landscapes, interiors)
    escape = lambda value: html.escape(str(value), quote=True)
    count = sum(len(story["images"]) for story in data["stories"])
    landscape_count = sum(len(story["images"]) for story in landscapes["stories"])
    interior_count = count - landscape_count
    options = []
    groups = []
    for story in data["stories"]:
        slug, title, reader = (escape(story[key]) for key in ("slug", "title", "reader"))
        options.append(f'<option value="{slug}">{title}</option>')
        cards = []
        for index, image in enumerate(story["images"], 1):
            caption, alt = escape(image["title"]), escape(image["alt"])
            full = escape(asset_url(image["full"]["path"], media=media))
            collection = image["collection"]
            label = COLLECTIONS[collection]
            image_id = f'{slug}/{escape(image["id"])}' if collection == "landscapes" else f'{slug}/interiors/{escape(image["id"])}'
            thumb = image["thumbnail"]
            cards.append(
                f'<li class="landscape-card" data-search="{title} {caption} {label}">'
                f'<a class="landscape-link" data-gallery-image data-full="{full}" data-title="{caption}" '
                f'data-story-title="{title}" data-story-slug="{slug}" data-image-id="{image_id}" data-collection="{collection}" '
                f'data-reader="{reader}" href="{full}"><figure>'
                f'<img src="{escape(asset_url(thumb["path"], media=media))}" alt="{alt}" width="{thumb["width"]}" height="{thumb["height"]}" loading="lazy" decoding="async">'
                f'<figcaption><span class="landscape-number">{index:02}</span><span>{caption}'
                f'<span class="painting-kind">{label}</span></span></figcaption></figure></a></li>'
            )
        groups.append(
            f'<section class="gallery-story" id="story-{slug}" data-story="{slug}" data-title="{title}">'
            f'<header class="gallery-story-heading"><h2>{title}</h2><a href="{reader}">Read story →</a></header>'
            f'<ul class="landscape-grid">{"".join(cards)}</ul></section>'
        )
    introduction = (
        '<section class="gallery-intro"><p class="gallery-eyebrow">Studies of the story world</p>'
        '<h1>Image Gallery</h1><p class="gallery-lede">Art from across our stories, gathered in one gallery.</p>'
        '<p class="gallery-study">Explore the collection and discover another side of the story world. '
        'Follow any piece back to its story to read more.</p>'
        f'<p class="gallery-summary">{landscape_count:,} landscapes · {interior_count:,} interiors · {len(groups):,} stories</p></section>'
    )
    controls = (
        '<form id="gallery-filters" class="gallery-controls" role="search" hidden>'
        '<div class="gallery-field"><label for="gallery-search">Search paintings</label>'
        '<input id="gallery-search" type="search" name="q" placeholder="A place, a mood, a story…"></div>'
        '<div class="gallery-field"><label for="gallery-story">Story</label>'
        '<select id="gallery-story" name="story"><option value="">All stories</option>'
        f'{"".join(options)}</select></div>'
        '<div class="gallery-field"><label for="gallery-type">Study</label>'
        '<select id="gallery-type" name="type"><option value="">All paintings</option>'
        '<option value="landscapes">Landscapes</option><option value="interiors">Interiors</option></select></div>'
        '<button id="gallery-reset" type="button">Clear filters</button></form>'
        f'<p id="gallery-count" class="gallery-count" role="status" aria-live="polite">{count:,} paintings across {len(groups):,} stories</p>'
        '<p id="gallery-empty" class="gallery-empty" hidden>No paintings found. Try another search or clear your filters.</p>'
    )
    empty = '<p class="gallery-empty">The art collection is coming soon.</p>' if not groups else ""
    viewer = (
        '<dialog id="gallery-viewer" class="gallery-viewer" aria-labelledby="viewer-title">'
        '<div class="viewer-toolbar"><p id="viewer-story"></p><button id="viewer-close" type="button" aria-label="Close image viewer">Close ×</button></div>'
        '<div class="viewer-stage"><button id="viewer-prev" type="button" aria-label="Previous painting">←</button>'
        '<img id="viewer-image" alt=""><button id="viewer-next" type="button" aria-label="Next painting">→</button></div>'
        '<div class="viewer-footer"><h2 id="viewer-title"></h2><p id="viewer-position"></p>'
        '<a id="viewer-full" target="_blank" rel="noopener">Open image ↗</a><a id="viewer-read-story">Read story →</a>'
        '<p id="viewer-error" role="status" hidden>This image could not load. Try opening it directly.</p></div></dialog>'
    )
    return build._page(
        "Image Gallery — Story Computing Machine", introduction + controls + empty
        + f'<div class="gallery-collection">{"".join(groups)}</div>' + viewer,
        "index.html", "styles.css", "theme.js", current="landscapes",
        script_href="landscape-gallery.js", extra_stylesheet_hrefs=("landscape-gallery.css",),
        main_class="landscape-gallery", page_path="gallery.html",
        description=f"Explore {count:,} works of art from {len(groups):,} stories, together in one gallery.",
        media=media,
    )


def build_gallery(destination: Path, snapshot_path: Path, catalog, media=None) -> int:
    landscapes = load_snapshot(snapshot_path)
    interiors = load_snapshot(snapshot_path.with_name("interiors.json"), "interiors")
    data = _combine_collections(landscapes, interiors)
    published = {story.slug for story in catalog.stories}
    if any(story["slug"] not in published for story in data["stories"]):
        raise ValueError("An art study reader is absent from the publication catalog")
    count = check_assets(data, snapshot_path.parent)
    for story in data["stories"]:
        for image in story["images"]:
            for role in ("full", "thumbnail"):
                relative = image[role]["path"]
                copy_asset(_asset(snapshot_path.parent, relative), destination, relative, media)
    for filename in ASSET_NAMES:
        shutil.copyfile(Path(__file__).with_name(filename), destination / filename)
    (destination / "gallery.html").write_text(render_gallery(landscapes, interiors, media), encoding="utf-8")
    return count
