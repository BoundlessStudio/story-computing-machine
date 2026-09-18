"""Approval-bound comic captures and frozen PDF downloads in existing readers."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from pages import build, graphic_novels as comics
from pages.test_build import edition_fixture, story_fixture


PDF = b'%PDF-1.4\n% approved fixture PDF\n%%EOF\n'


def put_json(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def publication(root, slug='comic-story'):
    story = story_fixture()
    pages = root / 'pages'
    (pages / 'covers').mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (864, 1536), 'navy').save(pages / story.cover)
    build.save_catalog([story], pages / 'catalog.json')
    record = {
        'slug': slug, 'title': story.title,
        'source': {'slug': story.slug, 'title': story.title, 'layout': 'bundle',
                   'canon': True, 'proseSha256': 'a' * 64},
        'pdf': {'path': f'graphic-novels/{slug}/edition.pdf',
                'sha256': hashlib.sha256(PDF).hexdigest(), 'pages': 2},
    }
    target = pages / record['pdf']['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(PDF)
    snapshot = pages / 'graphic-novels.json'
    put_json(snapshot, {'schemaVersion': 1, 'editions': [record]})
    return story, record, snapshot


def production(root, slug='comic-story'):
    story, _, snapshot = publication(root, slug)
    snapshot.unlink()
    shutil.rmtree(root / 'pages/graphic-novels')
    directory = root / 'graphic-novels' / slug
    directory.mkdir(parents=True)
    (root / 'graphic-novels/STYLE.md').write_text('Comic art style.', encoding='utf-8')
    source_directory = root / 'stories' / story.slug
    source_directory.mkdir(parents=True)
    files = {
        'prose': ('05-story.md', '# Source Story\n\nA quiet beginning.'),
        'prompt': ('00-prompt.md', 'A published prompt.'),
        'state': ('story.json', json.dumps({'slug': story.slug, 'title': story.title, 'canon': True})),
        'cover': ('title-image.jpg', 'source cover'),
        'review': ('04-review.md', 'PASS'),
    }
    source = {'slug': story.slug, 'title': story.title, 'layout': 'bundle', 'canon': True}
    for key, (name, content) in files.items():
        path = source_directory / name
        path.write_text(content, encoding='utf-8')
        source[key] = {'path': path.relative_to(root).as_posix(), 'sha256': comics.digest(path)}
    (directory / 'plan.md').write_text('One comic page.', encoding='utf-8')
    (directory / 'review.md').write_text('Independent whole-book PASS.', encoding='utf-8')
    (directory / 'cover.png').write_bytes(b'cover image')
    (directory / 'pages').mkdir()
    (directory / 'pages/page-001.png').write_bytes(b'page image')
    (directory / 'edition.pdf').write_bytes(PDF)
    cover = {'path': 'cover.png', 'sha256': comics.digest(directory / 'cover.png'), 'inspection': {'verdict': 'PASS'}}
    page = {'id': 'page-001', 'number': 1, 'path': 'pages/page-001.png',
            'sha256': comics.digest(directory / 'pages/page-001.png'), 'status': 'independent-pass'}
    page['independentReview'] = {'verdict': 'PASS', 'role': 'graphic_novel_reviewer', 'reviewer': 'page-reviewer', 'pageSha256': page['sha256']}
    ordered = [{'pdfPage': number, 'path': a['path'], 'sha256': a['sha256']} for number, a in enumerate([cover, page], 1)]
    binding = {
        'pdfPath': 'edition.pdf', 'pdfSha256': comics.digest(directory / 'edition.pdf'), 'pdfPages': 2,
        'orderedImages': ordered, 'sourceProseSha256': source['prose']['sha256'],
        'planSha256': comics.digest(directory / 'plan.md'), 'styleSha256': comics.digest(root / 'graphic-novels/STYLE.md'),
        'contractSha256': 'c' * 64, 'independentReviewFileSha256': comics.digest(directory / 'review.md'),
    }
    manifest = {
        'format': 'graphic-novel-draft-manual', 'slug': slug, 'title': story.title, 'source': source,
        'plan': {'path': f'graphic-novels/{slug}/plan.md', 'sha256': binding['planSha256'], 'pages': 1},
        'style': {'path': 'graphic-novels/STYLE.md', 'sha256': binding['styleSha256']}, 'contract': {'sha256': binding['contractSha256']},
        'cover': cover, 'pages': [page],
        'outputs': {'pdf': 'edition.pdf', 'pdfPages': 2, 'expectedPdfPages': 2,
                    'pdfSha256': binding['pdfSha256'], 'order': ['cover', 'page-001']},
        'approvals': {'final': {'status': 'approved', 'userResponse': 'Publish this reviewed PDF.', 'binding': binding}},
        'wholeBookReview': {key: deepcopy(value) for key, value in binding.items() if key not in {'styleSha256', 'contractSha256', 'independentReviewFileSha256'}} | {
            'scope': 'complete-pdf-book', 'verdict': 'PASS', 'role': 'graphic_novel_reviewer',
            'reviewer': 'fresh-book-reviewer', 'freshReviewer': True, 'blockingFindings': [],
            'reviewFileSha256': binding['independentReviewFileSha256'],
        },
    }
    put_json(directory / 'edition.json', manifest)
    return manifest, directory, snapshot


class ComicReaderTests(unittest.TestCase):
    def test_plain_and_illustrated_links_and_pdf_coexistence(self):
        with TemporaryDirectory() as temporary:
            story, comic, _ = publication(Path(temporary))
            edition = edition_fixture(story)
            edition['pdf'] = {'path': 'illustrated/illustrated-story/edition.pdf'}
            for editions in ([], [edition]):
                with self.subTest(illustrated=bool(editions)):
                    before = build.render_story(story, editions)
                    after = build.render_story(story, editions, [comic])
                    self.assertEqual(after.replace(comics.download_link(comic), ''), before)
                    self.assertEqual(after.count('Download comic PDF'), 1)
                    self.assertIn('href="../graphic-novels/comic-story/edition.pdf" download', after)
                    self.assertNotIn('Download comic PDF', before)
                    self.assertIn(story.prompt, after)
                    if editions:
                        self.assertIn('href="../illustrated/illustrated-story/edition.pdf" download', after)
                        self.assertEqual(after.count('Download PDF'), 1)

    def test_unrelated_comic_has_no_link_and_duplicate_sources_fail(self):
        with TemporaryDirectory() as temporary:
            story, comic, _ = publication(Path(temporary))
            comic['source']['slug'] = 'unrelated-story'
            self.assertEqual(build.render_story(story, comics=[comic]), build.render_story(story))
            with self.assertRaisesRegex(ValueError, 'Multiple comic'):
                build.render_story(story, comics=[comic, comic])

    def test_frozen_build_copies_exact_pdf_without_production(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            story, record, snapshot = publication(root)
            before = snapshot.read_bytes()
            with patch.object(comics, 'validate_capture', side_effect=AssertionError('Production read')):
                catalog = build.build(root / 'site', snapshot.with_name('catalog.json'))
            self.assertEqual(catalog.stories, (story,))
            self.assertEqual((root / 'site' / record['pdf']['path']).read_bytes(), PDF)
            self.assertIn('Download comic PDF', (root / 'site/stories/source-story.html').read_text(encoding='utf-8'))
            self.assertEqual(len(list((root / 'site/stories').glob('*.html'))), 1)
            self.assertEqual((root / 'site/index.html').read_text(encoding='utf-8').count('<li class="story-card">'), 1)
            self.assertEqual(snapshot.read_bytes(), before)

    def test_output_cannot_delete_graphic_novel_production(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            for output in (root / 'graphic-novels', root / 'graphic-novels/comic-story'):
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, 'protected'):
                    build.prepare_output(output, root)


class ComicSnapshotTests(unittest.TestCase):
    def test_bad_snapshot_rejected(self):
        changes = {
            'duplicate edition': lambda records: records.append(deepcopy(records[0])),
            'duplicate source': lambda records: records.append(deepcopy(records[0]) | {'slug': 'another-edition'}),
            'orphan source': lambda records: records[0]['source'].update(slug='absent-story'),
            'unsafe path': lambda records: records[0]['pdf'].update(path='../outside.pdf'),
            'wrong asset': lambda records: records[0]['pdf'].update(path='graphic-novels/other/edition.pdf'),
            'wrong hash': lambda records: records[0]['pdf'].update(sha256='0' * 64),
            'bad page count': lambda records: records[0]['pdf'].update(pages=True),
            'unknown field': lambda records: records[0].update(body='unwanted prose'),
        }
        for label, mutate in changes.items():
            with self.subTest(label=label), TemporaryDirectory() as temporary:
                _, record, snapshot = publication(Path(temporary))
                records = [record]
                mutate(records)
                put_json(snapshot, {'schemaVersion': 1, 'editions': records})
                with self.assertRaises(ValueError):
                    comics.load_snapshot(snapshot)

    def test_invalid_signature_and_orphan_assets_rejected(self):
        for fault in ('signature', 'orphan', 'missing snapshot'):
            with self.subTest(fault=fault), TemporaryDirectory() as temporary:
                root = Path(temporary)
                _, record, snapshot = publication(root)
                target = root / 'pages' / record['pdf']['path']
                if fault == 'signature':
                    target.write_bytes(b'not a PDF')
                    record['pdf']['sha256'] = comics.digest(target)
                    put_json(snapshot, {'schemaVersion': 1, 'editions': [record]})
                elif fault == 'orphan':
                    (target.parent / 'unselected.pdf').write_bytes(PDF)
                else:
                    snapshot.unlink()
                with self.assertRaises(ValueError):
                    comics.load_snapshot(snapshot)


class ComicCaptureTests(unittest.TestCase):
    def capture(self, root, slug='comic-story'):
        with patch.object(comics, 'require_worktree'):
            return comics.capture_edition(root, slug)

    def test_capture_stores_only_pdf_and_does_not_change_catalog(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, snapshot = production(root)
            before = snapshot.with_name('catalog.json').read_bytes()
            record = self.capture(root)
            self.assertEqual(comics.load_snapshot(snapshot), [record])
            self.assertEqual((root / 'pages' / record['pdf']['path']).read_bytes(), PDF)
            self.assertEqual(list((root / 'pages/graphic-novels/comic-story').iterdir()), [root / 'pages' / record['pdf']['path']])
            self.assertEqual(snapshot.with_name('catalog.json').read_bytes(), before)

    def test_current_format_source_uses_its_frontmatter_canon_marker(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, directory, snapshot = production(root)
            source = manifest['source']
            source_directory = root / 'stories' / source['slug']
            (source_directory / 'story.json').unlink()
            (source_directory / '05-story.md').unlink()
            (source_directory / '00-prompt.md').rename(source_directory / 'prompt.md')
            (source_directory / '04-review.md').rename(source_directory / 'review.md')
            prose = source_directory / 'story.md'
            prose.write_text('---\nslug: source-story\ntitle: Source Story\ncanon: true\n---\n\nA quiet beginning.\n', encoding='utf-8')
            source['layout'] = 'current'
            for name, filename in {'prose': 'story.md', 'state': 'story.md', 'prompt': 'prompt.md', 'review': 'review.md'}.items():
                path = source_directory / filename
                source[name] = {'path': path.relative_to(root).as_posix(), 'sha256': comics.digest(path)}
            manifest['wholeBookReview']['sourceProseSha256'] = source['prose']['sha256']
            manifest['approvals']['final']['binding']['sourceProseSha256'] = source['prose']['sha256']
            put_json(directory / 'edition.json', manifest)
            record = self.capture(root)
            self.assertEqual(record['source']['layout'], 'current')
            self.assertEqual(comics.load_snapshot(snapshot), [record])

    def test_unapproved_stale_or_unreviewed_capture_rejected_before_mutation(self):
        changes = {
            'approval': lambda m, d: m['approvals']['final'].update(status='awaiting-user-response'),
            'empty response': lambda m, d: m['approvals']['final'].update(userResponse=''),
            'approval hash': lambda m, d: m['approvals']['final']['binding'].update(pdfSha256='0' * 64),
            'stale PDF': lambda m, d: (d / 'edition.pdf').write_bytes(PDF + b'changed'),
            'changed page': lambda m, d: (d / 'pages/page-001.png').write_bytes(b'changed'),
            'page review': lambda m, d: m['pages'][0]['independentReview'].update(verdict='REVISE'),
            'whole review': lambda m, d: m['wholeBookReview'].update(verdict='REVISE'),
            'reused reviewer': lambda m, d: m['wholeBookReview'].update(reviewer='page-reviewer'),
            'order': lambda m, d: m['outputs'].update(order=['page-001', 'cover']),
            'bound order': lambda m, d: m['wholeBookReview']['orderedImages'].reverse(),
            'review bytes': lambda m, d: (d / 'review.md').write_text('Changed review'),
            'source bytes': lambda m, d: (d.parents[1] / m['source']['prose']['path']).write_text('Changed prose'),
            'plan bytes': lambda m, d: (d / 'plan.md').write_text('Changed plan'),
            'style bytes': lambda m, d: (d.parent / 'STYLE.md').write_text('Changed style'),
            'source canon': lambda m, d: m['source'].update(canon=False),
        }
        for label, mutate in changes.items():
            with self.subTest(label=label), TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest, directory, snapshot = production(root)
                mutate(manifest, directory)
                put_json(directory / 'edition.json', manifest)
                with self.assertRaises(ValueError):
                    self.capture(root)
                self.assertFalse(snapshot.exists())
                self.assertFalse((root / 'pages/graphic-novels').exists())

    def test_catalog_canon_mismatch_and_unpublished_source_rejected(self):
        for catalog_stories in ([story_fixture(canon=False)], []):
            with self.subTest(catalog_stories=catalog_stories), TemporaryDirectory() as temporary:
                root = Path(temporary)
                _, _, snapshot = production(root)
                build.save_catalog(catalog_stories, snapshot.with_name('catalog.json'))
                with self.assertRaisesRegex(ValueError, 'canon|Publish the named'):
                    self.capture(root)
                self.assertFalse(snapshot.exists())

    def test_failed_install_restores_snapshot_and_asset_bytes(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, directory, snapshot = production(root)
            self.capture(root)
            old_snapshot = snapshot.read_bytes()
            old_pdf = (root / 'pages/graphic-novels/comic-story/edition.pdf').read_bytes()
            real_load = comics.load_snapshot
            calls = 0

            def fail_after_install(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise ValueError('Simulated post-install validation failure')
                return real_load(*args, **kwargs)

            with patch.object(comics, 'load_snapshot', side_effect=fail_after_install):
                with self.assertRaisesRegex(ValueError, 'Simulated'):
                    self.capture(root)
            self.assertEqual(snapshot.read_bytes(), old_snapshot)
            self.assertEqual((root / 'pages/graphic-novels/comic-story/edition.pdf').read_bytes(), old_pdf)
            self.assertEqual((directory / 'edition.pdf').read_bytes(), PDF)

    def test_second_capture_does_not_refresh_from_changed_production(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, directory, snapshot = production(root)
            record = self.capture(root)
            old_snapshot = snapshot.read_bytes()
            (directory / 'edition.pdf').write_bytes(PDF + b'new unapproved PDF')
            with self.assertRaises(ValueError):
                self.capture(root)
            self.assertEqual(snapshot.read_bytes(), old_snapshot)
            self.assertEqual((root / 'pages' / record['pdf']['path']).read_bytes(), PDF)
            build.build(root / 'site', snapshot.with_name('catalog.json'))
            self.assertEqual((root / 'site' / record['pdf']['path']).read_bytes(), PDF)

    def test_replacing_selected_edition_removes_old_assets_and_restores_on_failure(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest, directory, snapshot = production(root)
            old_record = self.capture(root)
            old_snapshot = snapshot.read_bytes()
            new_directory = directory.with_name('new-comic')
            shutil.copytree(directory, new_directory)
            manifest['slug'] = 'new-comic'
            manifest['plan']['path'] = 'graphic-novels/new-comic/plan.md'
            put_json(new_directory / 'edition.json', manifest)
            real_load = comics.load_snapshot

            def fail_new_snapshot(*args, **kwargs):
                loaded = real_load(*args, **kwargs)
                if loaded and loaded[0]['slug'] == 'new-comic':
                    raise ValueError('Simulated replacement failure')
                return loaded

            with patch.object(comics, 'load_snapshot', side_effect=fail_new_snapshot):
                with self.assertRaisesRegex(ValueError, 'Simulated'):
                    self.capture(root, 'new-comic')
            self.assertEqual(snapshot.read_bytes(), old_snapshot)
            self.assertEqual((root / 'pages' / old_record['pdf']['path']).read_bytes(), PDF)
            self.assertFalse((root / 'pages/graphic-novels/new-comic').exists())
            record = self.capture(root, 'new-comic')
            self.assertEqual(comics.load_snapshot(snapshot), [record])
            self.assertFalse((root / 'pages/graphic-novels/comic-story').exists())
            self.assertEqual((root / 'pages' / record['pdf']['path']).read_bytes(), PDF)


if __name__ == '__main__':
    unittest.main()
