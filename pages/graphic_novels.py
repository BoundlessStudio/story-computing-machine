"""Capture approved comic PDFs and publish their frozen bytes beside story readers.

This is a publication adapter for the manual graphic-novel manifest, not an
art-generation or PDF-assembly workflow. Builds use stored snapshots only.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

if __package__:
    from .media_assets import asset_url, copy_asset
else:
    from media_assets import asset_url, copy_asset


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / 'pages/graphic-novels.json'
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root: Path, value: str) -> Path:
    if (not isinstance(value, str) or not value or ':' in value or '\\' in value
            or PurePosixPath(value).is_absolute()
            or any(part in {'', '.', '..'} for part in value.split('/'))):
        raise ValueError(f'Unsafe comic asset path: {value}')
    target = (root / value).resolve()
    if root.resolve() not in target.parents:
        raise ValueError(f'Comic asset escapes its root: {value}')
    return target


def _object(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f'Invalid {label} fields')


def _slug(value):
    return isinstance(value, str) and SLUG.fullmatch(value)


def _sha(value):
    return isinstance(value, str) and SHA256.fullmatch(value)


def _pdf(path: Path, expected: str):
    if not _sha(expected) or not path.is_file() or digest(path) != expected:
        raise ValueError(f'Comic PDF missing or changed: {path}')
    with path.open('rb') as stream:
        if stream.read(5) != b'%PDF-':
            raise ValueError(f'Invalid comic PDF signature: {path}')


def by_source(records) -> dict:
    selected = {}
    for record in records:
        slug = record['source']['slug']
        if slug in selected:
            raise ValueError(f'Multiple comic editions selected for source: {slug}')
        selected[slug] = record
    return selected


def download_link(record: dict | None, asset_prefix='../', media=None) -> str:
    if record is None:
        return ''
    href = html.escape(asset_url(record['pdf']['path'], asset_prefix, media), quote=True)
    return f'<p class="comic-download"><a href="{href}" download>Download comic PDF</a></p>'


def load_snapshot(path: Path = SNAPSHOT, catalog=None) -> list[dict]:
    """Validate publication bytes without opening a production package."""
    from pages.build import load_catalog
    if not path.exists():
        if (path.parent / 'graphic-novels').exists() and any((path.parent / 'graphic-novels').rglob('*')):
            raise ValueError('Orphan comic assets without a publication snapshot')
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Cannot read comic snapshot: {path}') from exc
    _object(data, {'schemaVersion', 'editions'}, 'comic snapshot')
    if type(data['schemaVersion']) is not int or data['schemaVersion'] != 1 or not isinstance(data['editions'], list):
        raise ValueError('Invalid comic snapshot schema')
    catalog = catalog if catalog is not None else load_catalog(path.with_name('catalog.json'))
    stories = {story.slug: story for story in catalog.stories}
    seen, sources, assets = set(), set(), set()
    for record in data['editions']:
        _object(record, {'slug', 'title', 'source', 'pdf'}, 'comic record')
        slug = record['slug']
        if not _slug(slug) or slug in seen or not isinstance(record['title'], str) or not record['title'].strip():
            raise ValueError('Duplicate or invalid comic edition')
        seen.add(slug)
        source = record['source']
        _object(source, {'slug', 'title', 'layout', 'canon', 'proseSha256'}, 'comic source')
        if (not _slug(source['slug']) or source['slug'] in sources
                or not isinstance(source['layout'], str) or source['layout'] not in {'current', 'bundle'}
                or not isinstance(source['title'], str) or not source['title'].strip()
                or type(source['canon']) is not bool or not _sha(source['proseSha256'])):
            raise ValueError('Duplicate or invalid comic source')
        sources.add(source['slug'])
        if source['slug'] not in stories:
            raise ValueError('Comic source is absent from the publication catalog')
        if source['title'] != stories[source['slug']].title:
            raise ValueError('Comic source title differs from the publication catalog')
        pdf = record['pdf']
        _object(pdf, {'path', 'sha256', 'pages'}, 'comic PDF')
        if pdf['path'] != f'graphic-novels/{slug}/edition.pdf' or type(pdf['pages']) is not int or pdf['pages'] < 2:
            raise ValueError('Invalid comic PDF path or page count')
        target = safe_path(path.parent, pdf['path'])
        _pdf(target, pdf['sha256'])
        assets.add(target)
    stored = path.parent / 'graphic-novels'
    if stored.exists():
        for asset in stored.rglob('*'):
            if asset.is_symlink() or (asset.is_file() and asset.resolve() not in assets):
                raise ValueError(f'Orphan or linked comic publication asset: {asset}')
    return data['editions']


def require_worktree(root: Path):
    def git(*args):
        result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError('Cannot verify graphic-novel worktree')
        return result.stdout.strip()
    if (Path(git('rev-parse', '--show-toplevel')).resolve() != root.resolve()
            or not (root / '.git').is_file()
            or not git('branch', '--show-current').startswith('codex/graphic-novel-')):
        raise ValueError('Use the assigned dedicated graphic-novel worktree for capture')


def _pin(root: Path, entry: dict, label: str, expected_path=None):
    if not isinstance(entry, dict) or not _sha(entry.get('sha256')):
        raise ValueError(f'Invalid {label} pin')
    if expected_path is not None and entry.get('path') != expected_path:
        raise ValueError(f'Unexpected {label} path')
    path = safe_path(root, entry.get('path'))
    if not path.is_file() or digest(path) != entry['sha256']:
        raise ValueError(f'Changed or missing {label}: {entry.get("path")}')
    return path


def validate_capture(root: Path, slug: str, catalog) -> dict:
    """Check the final manual review and approval against every delivered byte."""
    from pages.build import _source_canon_marker, parse_front_matter
    if not _slug(slug):
        raise ValueError('Invalid comic edition slug')
    directory = safe_path(root, f'graphic-novels/{slug}')
    try:
        manifest = json.loads((directory / 'edition.json').read_text(encoding='utf-8-sig'))
        if (manifest['format'] != 'graphic-novel-draft-manual' or manifest['slug'] != slug
                or not isinstance(manifest['title'], str) or not manifest['title'].strip()):
            raise ValueError('Invalid comic manifest identity')
        source = manifest['source']
        source_slug = source['slug']
        if not _slug(source_slug) or source['layout'] not in {'current', 'bundle'}:
            raise ValueError('Invalid comic source identity')
        published = next((s for s in catalog.stories if s.slug == source_slug), None)
        if published is None:
            raise ValueError('Publish the named original story before capturing its comic')
        prefix = f'stories/{source_slug}/'
        current = source['layout'] == 'current'
        required = {
            'prose': 'story.md' if current else '05-story.md',
            'prompt': 'prompt.md' if current else '00-prompt.md',
            'state': 'story.md' if current else 'story.json',
            'cover': 'title-image.jpg',
            'review': 'review.md' if current else '04-review.md',
        }
        for name, filename in required.items():
            _pin(root, source[name], f'source {name}', prefix + filename)
        source_directory = safe_path(root, prefix.rstrip('/'))
        if (source_directory / 'story.md').exists() == (source_directory / '05-story.md').exists():
            raise ValueError('Ambiguous comic source layout')
        state = _source_canon_marker(source_directory)
        if type(source['canon']) is not bool or state != source['canon'] or state != published.canon:
            raise ValueError('Reconcile the named source/catalog canon state before comic capture')
        if current:
            identity, _ = parse_front_matter((source_directory / 'story.md').read_text(encoding='utf-8'), source_directory / 'story.md')
        else:
            identity = json.loads((source_directory / 'story.json').read_text(encoding='utf-8-sig'))
        if identity.get('slug') != source_slug or identity.get('title') != source['title'] or source['title'] != published.title:
            raise ValueError('Comic source identity differs from the publication catalog')
        _pin(root, manifest['plan'], 'comic plan', f'graphic-novels/{slug}/plan.md')
        _pin(root, manifest['style'], 'comic style', 'graphic-novels/STYLE.md')
        pages = manifest['pages']
        if not isinstance(pages, list) or not pages or manifest['plan']['pages'] != len(pages):
            raise ValueError('Comic page inventory differs from its plan')
        cover = manifest['cover']
        if cover.get('inspection', {}).get('verdict') != 'PASS':
            raise ValueError('Comic cover needs a passing inspection')
        _pin(directory, cover, 'comic cover')
        images = [{'pdfPage': 1, 'path': cover['path'], 'sha256': cover['sha256']}]
        page_reviewers = set()
        for number, page in enumerate(pages, 1):
            review = page['independentReview']
            if (type(page['number']) is not int or page['number'] != number
                    or page['id'] != f'page-{number:03d}' or page['status'] != 'independent-pass'
                    or review['verdict'] != 'PASS' or review['pageSha256'] != page['sha256']
                    or review.get('role') != 'graphic_novel_reviewer' or not review.get('reviewer')):
                raise ValueError('Every selected comic page needs its own bound independent PASS')
            page_reviewers.add(review['reviewer'])
            _pin(directory, page, 'comic page', f'pages/page-{number:03d}.png')
            images.append({'pdfPage': number + 1, 'path': page['path'], 'sha256': page['sha256']})
        if len({a['path'] for a in images}) != len(images):
            raise ValueError('Duplicate comic image path')
        outputs = manifest['outputs']
        if (outputs['pdf'] != 'edition.pdf' or outputs['pdfPages'] != len(images)
                or outputs['expectedPdfPages'] != len(images)
                or outputs['order'] != ['cover', *[p['id'] for p in pages]]):
            raise ValueError('Comic PDF output order differs from selected images')
        _pdf(directory / 'edition.pdf', outputs['pdfSha256'])
        whole = manifest['wholeBookReview']
        if (whole.get('scope') != 'complete-pdf-book' or whole.get('verdict') != 'PASS'
                or whole.get('role') != 'graphic_novel_reviewer' or not whole.get('reviewer')
                or whole['reviewer'] in page_reviewers or whole.get('freshReviewer') is not True
                or whole.get('blockingFindings') != []):
            raise ValueError('Comic needs a fresh passing independent whole-book review')
        review_hash = digest(directory / 'review.md')
        expected = {
            'pdfPath': 'edition.pdf', 'pdfSha256': outputs['pdfSha256'],
            'pdfPages': len(images), 'orderedImages': images,
            'planSha256': manifest['plan']['sha256'], 'sourceProseSha256': source['prose']['sha256'],
        }
        if any(whole.get(key) != value for key, value in expected.items()) or whole.get('reviewFileSha256') != review_hash:
            raise ValueError('Whole-book review is stale for the PDF, image order, source, plan, or review file')
        approval = manifest['approvals']['final']
        if approval.get('status') != 'approved' or not isinstance(approval.get('userResponse'), str) or not approval['userResponse'].strip():
            raise ValueError('Comic needs final user approval of the exact reviewed PDF')
        binding = approval['binding']
        expected.update({
            'styleSha256': manifest['style']['sha256'],
            'contractSha256': manifest['contract']['sha256'],
            'independentReviewFileSha256': review_hash,
        })
        # The contract is the recorded production version. Publication-only
        # instruction edits do not alter the approved art or invalidate its PDF.
        if not _sha(expected['styleSha256']) or not _sha(expected['contractSha256']) or any(binding.get(k) != v for k, v in expected.items()):
            raise ValueError('Final comic approval is stale for its selected inputs')
        return manifest
    except (KeyError, TypeError, AttributeError, OSError) as exc:
        raise ValueError(f'Incomplete comic capture evidence for {slug}: {exc}') from exc


def _record(manifest: dict) -> dict:
    source = manifest['source']
    return {
        'slug': manifest['slug'], 'title': manifest['title'],
        'source': {key: source[key] for key in ('slug', 'title', 'layout', 'canon')} | {'proseSha256': source['prose']['sha256']},
        'pdf': {'path': f'graphic-novels/{manifest["slug"]}/edition.pdf',
                'sha256': manifest['outputs']['pdfSha256'], 'pages': manifest['outputs']['pdfPages']},
    }


def capture_edition(root: Path, slug: str, snapshot: Path | None = None) -> dict:
    from pages.build import load_catalog
    require_worktree(root)
    snapshot = snapshot or root / 'pages/graphic-novels.json'
    catalog = load_catalog(snapshot.with_name('catalog.json'))
    previous = load_snapshot(snapshot, catalog)
    manifest = validate_capture(root, slug, catalog)
    record = _record(manifest)
    replaced = [r for r in previous if r['slug'] == slug or r['source']['slug'] == record['source']['slug']]
    records = sorted([r for r in previous if r not in replaced] + [record], key=lambda r: r['slug'])
    target = safe_path(snapshot.parent, f'graphic-novels/{slug}')
    previous_bytes = snapshot.read_bytes() if snapshot.exists() else None
    # Validate before mutating publication. Back up both same-slug replacements
    # and a formerly selected different edition; restore all on install failure.
    with tempfile.TemporaryDirectory(prefix='.comic-capture-', dir=snapshot.parent) as temporary:
        staging = Path(temporary)
        assets = staging / 'assets'
        assets.mkdir()
        shutil.copyfile(root / 'graphic-novels' / slug / 'edition.pdf', assets / 'edition.pdf')
        _pdf(assets / 'edition.pdf', record['pdf']['sha256'])
        if validate_capture(root, slug, load_catalog(snapshot.with_name('catalog.json'))) != manifest:
            raise ValueError('Comic changed during capture')
        staged_snapshot = staging / 'snapshot.json'
        staged_snapshot.write_text(json.dumps({'schemaVersion': 1, 'editions': records}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        target.parent.mkdir(parents=True, exist_ok=True)
        backups = []
        installed = False
        try:
            directories = {safe_path(snapshot.parent, f'graphic-novels/{r["slug"]}') for r in replaced} | {target}
            for index, directory in enumerate(sorted(directories)):
                if directory.exists():
                    backup = staging / f'previous-{index}'
                    os.replace(directory, backup)
                    backups.append((directory, backup))
            os.replace(assets, target)
            installed = True
            os.replace(staged_snapshot, snapshot)
            load_snapshot(snapshot, catalog)
        except Exception:
            if installed:
                shutil.rmtree(target)
            for directory, backup in reversed(backups):
                os.replace(backup, directory)
            if previous_bytes is None:
                snapshot.unlink(missing_ok=True)
            else:
                snapshot.write_bytes(previous_bytes)
            raise
    return record


def build_editions(output: Path, snapshot: Path, records=None, media=None) -> list[dict]:
    records = load_snapshot(snapshot) if records is None else records
    for record in records:
        pdf = record['pdf']
        source = safe_path(snapshot.parent, pdf['path'])
        _pdf(source, pdf['sha256'])
        copy_asset(source, output, pdf['path'], media)
    return records
