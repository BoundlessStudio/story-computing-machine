"""CDN publication preserves frozen content and fails before deploying bad media."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

from botocore.exceptions import ClientError
from PIL import Image

from pages import build, illustrated_editions, media_assets, publish_assets
from pages.test_build import edition_fixture, story_fixture
from pages.test_graphic_novels import PDF, publication, put_json


BASE = 'https://art.example.com'


class Elements(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.elements = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def gallery_fixture(pages, story, collection):
    image = {'id': '01-room', 'title': 'A room', 'alt': 'A quiet room.',
             'source': f'stories/{story.slug}/art/{collection}/01-room.png',
             'sourceSha256': 'a' * 64}
    sizes = ((96, 64), (48, 32)) if collection == 'characters' else ((128, 64), (64, 32))
    for role, suffix, size in [('full', '', sizes[0]), ('thumbnail', '-thumb', sizes[1])]:
        relative = f'{collection}/{story.slug}/01-room{suffix}.webp'
        target = pages / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', size, 'olive' if collection == 'interiors' else 'teal').save(target)
        image[role] = {'path': relative, 'sha256': media_assets.file_sha256(target),
                       'width': size[0], 'height': size[1]}
    put_json(pages / f'{collection}.json', {'schemaVersion': 1, 'stories': [{
        'slug': story.slug, 'title': story.title, 'reader': f'stories/{story.slug}.html', 'images': [image],
    }]})
    return image


class CdnBuildTests(unittest.TestCase):
    def test_all_publication_media_use_cdn_without_changing_snapshots_or_navigation(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            story, comic, snapshot = publication(root)
            pages = snapshot.parent
            plain = story_fixture('plain-story')
            Image.new('RGB', (864, 1536), 'indigo').save(pages / plain.cover)
            build.save_catalog([story, plain], pages / 'catalog.json')
            edition = edition_fixture(story)
            edition['pdf'] = {'path': 'illustrated/illustrated-story/edition.pdf'}
            for asset in illustrated_editions.published_assets(edition):
                target = pages / asset['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.suffix == '.pdf':
                    target.write_bytes(PDF)
                else:
                    Image.new('RGB', (32, 48), 'ivory').save(target)
                asset['sha256'] = media_assets.file_sha256(target)
            put_json(pages / 'illustrated.json', {'schemaVersion': 1, 'editions': [edition]})
            landscapes = gallery_fixture(pages, story, 'landscapes')
            interiors = gallery_fixture(pages, story, 'interiors')
            characters = gallery_fixture(pages, story, 'characters')
            before = {p: p.read_bytes() for p in pages.rglob('*') if p.is_file()}
            local, cdn, staged = root / 'local', root / 'cdn', root / 'assets'
            with patch.object(build, 'load_story_source', side_effect=AssertionError('Production read')):
                build.build(local, pages / 'catalog.json')
                build.build(cdn, pages / 'catalog.json', asset_base_url=BASE, asset_output=staged)
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            self.assertFalse(any(p.suffix in media_assets.CONTENT_TYPES for p in cdn.rglob('*')))
            manifest = json.loads((staged / 'manifest.json').read_text())
            entries = {entry['path']: entry for entry in manifest['assets']}
            self.assertEqual(len(entries), 13)
            urls = {BASE + '/' + entry['key'] for entry in entries.values()}
            for relative, entry in entries.items():
                self.assertEqual((staged / relative).read_bytes(), (local / relative).read_bytes())
                self.assertEqual(entry['sha256'], media_assets.file_sha256(local / relative))
            for document in cdn.rglob('*.html'):
                for tag, attrs in Elements(document.read_text(encoding='utf-8')).elements:
                    for value in attrs.values():
                        if value and value.startswith(BASE):
                            self.assertIn(value, urls)
                    if tag == 'img' and attrs.get('src'):
                        self.assertIn(attrs['src'], urls)
                    if tag == 'a' and attrs.get('href', '').endswith('.pdf'):
                        self.assertIn(attrs['href'], urls)
                    if 'data-full' in attrs:
                        self.assertIn(attrs['data-full'], urls)
                    if attrs.get('property') == 'og:image':
                        self.assertIn(attrs['content'], urls)
            reader = (cdn / f'stories/{story.slug}.html').read_text(encoding='utf-8')
            self.assertIn('href="../index.html"', reader)
            self.assertIn('href="../illustrated.css"', reader)
            self.assertIn('src="../theme.js"', reader)
            self.assertIn(story.prompt, reader)
            self.assertIn('A quiet beginning.', reader)
            self.assertIn('Download comic PDF', reader)
            self.assertIn('Download PDF', reader)
            plain_reader = (cdn / 'stories/plain-story.html').read_text(encoding='utf-8')
            self.assertIn(BASE + '/' + entries[plain.cover]['key'], plain_reader)
            gallery = (cdn / 'gallery.html').read_text(encoding='utf-8')
            for image in (landscapes, interiors, characters):
                self.assertIn(f'data-full="{BASE}/{entries[image["full"]["path"]]["key"]}"', gallery)
            self.assertIn(f'data-reader="stories/{story.slug}.html"', gallery)
            self.assertIn('href="stories/plain-story.html"', (cdn / 'index.html').read_text(encoding='utf-8'))

    def test_cdn_requires_separate_safe_outputs_and_complete_options(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            sentinel = root / 'keep.txt'
            sentinel.write_text('keep')
            for site, assets, base in [(root, root, BASE), (root, root / 'assets', BASE),
                                       (root / 'site', root, BASE), (root, None, BASE),
                                       (root / 'site', root / 'assets', None)]:
                with self.subTest(site=site, assets=assets), self.assertRaises(ValueError):
                    build.build(site, asset_base_url=base, asset_output=assets)
            self.assertEqual(sentinel.read_text(), 'keep')


class FakeR2:
    def __init__(self):
        self.meta = SimpleNamespace(endpoint_url='https://r2.example.com')
        self.objects = {}
        self.uploads = []
        self.heads = []

    def head_object(self, *, Bucket, Key):
        self.heads.append(Key)
        if Key not in self.objects:
            raise ClientError({'Error': {'Code': '404'}, 'ResponseMetadata': {'HTTPStatusCode': 404}}, 'HeadObject')
        return deepcopy(self.objects[Key])

    def upload_file(self, path, bucket, key, *, ExtraArgs, Config):
        self.uploads.append(key)
        self.objects[key] = deepcopy(ExtraArgs) | {'ContentLength': Path(path).stat().st_size}


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        source = self.root / 'source.pdf'
        source.write_bytes(PDF)
        self.media = media_assets.MediaAssets(self.root / 'staged', BASE)
        self.media.add(source, 'graphic-novels/one/edition.pdf')
        self.media.add(source, 'illustrated/two/edition.pdf')
        self.media.write_manifest()
        self.manifest = self.media.root / 'manifest.json'
        self.entry = next(iter(self.media.entries.values()))

    def test_upload_is_idempotent_deduplicates_and_retains_previous_objects(self):
        client = FakeR2()
        client.objects['old/version.pdf'] = {'old': True}
        with patch.object(publish_assets, 'verify_public') as public:
            first = publish_assets.publish(self.manifest, client, 'bucket')
            second = publish_assets.publish(self.manifest, client, 'bucket')
        self.assertEqual(first, {'uploaded': 1, 'unchanged': 0, 'verified': 1, 'cached': 0})
        self.assertEqual(second, {'uploaded': 0, 'unchanged': 1, 'verified': 1, 'cached': 0})
        self.assertEqual(len(client.uploads), 1)
        self.assertEqual(public.call_count, 2)
        self.assertIn('old/version.pdf', client.objects)
        uploaded = client.objects[self.entry['key']]
        self.assertEqual(uploaded['ContentType'], 'application/pdf')
        self.assertEqual(uploaded['CacheControl'], 'public, max-age=31536000, immutable')
        self.assertTrue(uploaded['ContentDisposition'].startswith('attachment; filename="edition.pdf"'))

    def seed_verification_cache(self):
        client = FakeR2()
        cache = self.root / 'cache' / 'verified.json'
        with patch.object(publish_assets, 'verify_public'):
            publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache, verify_all=True)
        client.heads.clear()
        client.uploads.clear()
        return client, cache

    def test_warm_cache_skips_r2_and_keeps_one_public_probe(self):
        source = self.root / 'other.pdf'
        source.write_bytes(PDF + b'% other content\n')
        self.media.add(source, 'graphic-novels/other/edition.pdf')
        self.media.write_manifest()
        client, cache = self.seed_verification_cache()
        before = cache.read_bytes()
        with patch.object(publish_assets, 'verify_public') as public:
            result = publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache)
        self.assertEqual(result, {'uploaded': 0, 'unchanged': 2, 'verified': 1, 'cached': 2})
        self.assertFalse(client.heads)
        self.assertFalse(client.uploads)
        public.assert_called_once()
        self.assertEqual(public.call_args.args[0], BASE)
        self.assertIn(public.call_args.args[1], self.media.entries.values())
        self.assertEqual(cache.read_bytes(), before)  # A probe must not extend expiry.

    def test_incremental_manifest_checks_only_new_content(self):
        client, cache = self.seed_verification_cache()
        source = self.root / 'new.pdf'
        source.write_bytes(PDF + b'% newly approved\n')
        self.media.add(source, 'graphic-novels/new/edition.pdf')
        self.media.write_manifest()
        new_entry = self.media.entries['graphic-novels/new/edition.pdf']
        with patch.object(publish_assets, 'verify_public') as public:
            result = publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache)
        self.assertEqual(result, {'uploaded': 1, 'unchanged': 1, 'verified': 2, 'cached': 1})
        self.assertEqual(client.uploads, [new_entry['key']])
        self.assertEqual(set(client.heads), {new_entry['key']})
        self.assertEqual(public.call_count, 2)
        self.assertEqual(len(json.loads(cache.read_text())['objects']), 2)

    def test_scope_changes_force_full_checks(self):
        for field in ('endpoint', 'bucket', 'baseUrl'):
            with self.subTest(field=field):
                client, cache = self.seed_verification_cache()
                data = json.loads(cache.read_text())
                data['scope'][field] += '-other'
                put_json(cache, data)
                with patch.object(publish_assets, 'verify_public') as public:
                    result = publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache)
                self.assertEqual(result['cached'], 0)
                self.assertEqual(client.heads, [self.entry['key']])
                public.assert_called_once()

    def test_expired_future_and_malformed_records_are_rechecked(self):
        mutations = [None, {}, {'verifiedAt': 'yesterday'},
                     {'verifiedAt': 0}, {'verifiedAt': 10**20},
                     {'size': 1}, {'headers': {}}, {'extra': True}]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                client, cache = self.seed_verification_cache()
                data = json.loads(cache.read_text())
                record = data['objects'][self.entry['key']]
                data['objects'][self.entry['key']] = record | mutation if mutation else mutation
                put_json(cache, data)
                with patch.object(publish_assets, 'verify_public'):
                    result = publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache)
                self.assertEqual(result['cached'], 0)
                self.assertEqual(client.heads, [self.entry['key']])

    def test_cache_expiry_boundary_and_forced_audit(self):
        for age, forced in [(publish_assets.VERIFICATION_MAX_AGE, False), (1, True)]:
            with self.subTest(age=age, forced=forced):
                client, cache = self.seed_verification_cache()
                verified_at = json.loads(cache.read_text())['objects'][self.entry['key']]['verifiedAt']
                with patch.object(publish_assets.time, 'time', return_value=verified_at + age), \
                        patch.object(publish_assets, 'verify_public'):
                    result = publish_assets.publish(self.manifest, client, 'bucket',
                                                    verification_cache=cache, verify_all=forced)
                self.assertEqual(result['cached'], 0)
                self.assertEqual(client.heads, [self.entry['key']])
                self.assertEqual(json.loads(cache.read_text())['objects'][self.entry['key']]['verifiedAt'],
                                 verified_at + age)

    def test_invalid_cache_is_a_safe_miss(self):
        for content in ('{broken', '[]', '{}', '{"schemaVersion": 99}',
                        '{"schemaVersion": 1, "objects": []}'):
            with self.subTest(content=content):
                client, cache = self.seed_verification_cache()
                cache.write_text(content)
                with patch.object(publish_assets, 'verify_public'):
                    result = publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache)
                self.assertEqual(result['cached'], 0)
                self.assertEqual(client.heads, [self.entry['key']])

    def test_failed_probe_or_audit_never_updates_cache(self):
        for forced in (False, True):
            with self.subTest(forced=forced):
                client, cache = self.seed_verification_cache()
                before = cache.read_bytes()
                with patch.object(publish_assets, 'verify_public', side_effect=ValueError('CDN unavailable')):
                    with self.assertRaisesRegex(ValueError, 'CDN unavailable'):
                        publish_assets.publish(self.manifest, client, 'bucket',
                                               verification_cache=cache, verify_all=forced)
                self.assertEqual(cache.read_bytes(), before)

    def test_warm_cache_does_not_bypass_local_integrity_checks(self):
        client, cache = self.seed_verification_cache()
        before = cache.read_bytes()
        (self.media.root / self.entry['path']).write_bytes(b'tampered')
        with patch.object(publish_assets, 'verify_public') as public:
            with self.assertRaisesRegex(ValueError, 'missing or changed'):
                publish_assets.publish(self.manifest, client, 'bucket', verification_cache=cache)
        self.assertFalse(client.heads)
        public.assert_not_called()
        self.assertEqual(cache.read_bytes(), before)

    def test_changed_bytes_get_a_new_url(self):
        old = self.media.url(self.entry['path'])
        source = self.root / 'source.pdf'
        source.write_bytes(PDF + b'% new approved edition\n')
        updated = media_assets.MediaAssets(self.root / 'new', BASE)
        updated.add(source, self.entry['path'])
        self.assertNotEqual(updated.url(self.entry['path']), old)

    def test_tampered_files_manifest_keys_and_paths_fail_before_any_upload(self):
        original = json.loads(self.manifest.read_text())
        for field, value in [('path', '../source.pdf'), ('key', 'assets/wrong/edition.pdf'),
                             ('sha256', '0' * 64), ('size', 999), ('contentType', 'text/html')]:
            with self.subTest(field=field):
                changed = deepcopy(original)
                changed['assets'][0][field] = value
                put_json(self.manifest, changed)
                client = Mock()
                with self.assertRaises(ValueError):
                    publish_assets.publish(self.manifest, client, 'bucket')
                self.assertFalse(client.mock_calls)
        put_json(self.manifest, original)
        (self.media.root / self.entry['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            publish_assets.load_manifest(self.manifest)

    def test_remote_mismatch_or_denied_access_does_not_overwrite(self):
        client = FakeR2()
        client.objects[self.entry['key']] = {'ContentLength': 1}
        with self.assertRaisesRegex(ValueError, 'differs from the immutable manifest'):
            publish_assets.upload_object(client, 'bucket', self.media.root, self.entry)
        self.assertFalse(client.uploads)
        denied = ClientError({'Error': {'Code': 'AccessDenied'}, 'ResponseMetadata': {'HTTPStatusCode': 403}}, 'HeadObject')
        client = Mock()
        client.head_object.side_effect = denied
        with self.assertRaises(ClientError):
            publish_assets.upload_object(client, 'bucket', self.media.root, self.entry)
        client.upload_file.assert_not_called()

    def test_upload_and_cdn_failures_abort_publication(self):
        client = FakeR2()
        with patch.object(client, 'upload_file', side_effect=RuntimeError('Upload failed')), \
                patch.object(publish_assets, 'verify_public') as public:
            with self.assertRaisesRegex(RuntimeError, 'Upload failed'):
                publish_assets.publish(self.manifest, client, 'bucket')
            public.assert_not_called()
        with patch.object(publish_assets, 'verify_public', side_effect=ValueError('CDN unavailable')):
            with self.assertRaisesRegex(ValueError, 'CDN unavailable'):
                publish_assets.publish(self.manifest, client, 'bucket')

    def test_public_verification_retries_and_checks_type_length_and_pdf_download(self):
        response = Mock(status=200, headers={
            'Content-Type': 'application/pdf', 'Content-Length': str(self.entry['size']),
            'Cache-Control': media_assets.CACHE_CONTROL,
            'Content-Disposition': publish_assets.object_headers(self.entry)['ContentDisposition'],
        })
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        with patch.object(publish_assets, 'urlopen', side_effect=[URLError('retry'), context]) as request, \
                patch.object(publish_assets.time, 'sleep') as sleep:
            publish_assets.verify_public(BASE, self.entry)
            self.assertEqual(request.call_count, 2)
            self.assertEqual(request.call_args.args[0].method, 'HEAD')
            self.assertEqual(request.call_args.args[0].get_header('User-agent'), 'StoryComputingMachine-Publisher/1.0')
            sleep.assert_called_once_with(1)
        for header, wrong in [('Content-Type', 'text/html'), ('Content-Length', '1'),
                               ('Cache-Control', 'no-store'), ('Content-Disposition', 'inline')]:
            with self.subTest(header=header), patch.dict(response.headers, {header: wrong}), \
                    patch.object(publish_assets, 'urlopen', return_value=context):
                with self.assertRaisesRegex(ValueError, 'Public CDN verification failed'):
                    publish_assets.verify_public(BASE, self.entry, attempts=1)

    def test_invalid_base_urls_are_rejected(self):
        for value in ('http://art.example.com', 'https://user:secret@art.example.com',
                      'https://art.example.com?token=secret', 'https://art.example.com/#frag',
                      'https://art.example.com/with space'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                media_assets.validate_base_url(value)


if __name__ == '__main__':
    unittest.main()
