"""Rendering and publication tests use synthetic stories and fixture artwork only."""
import copy
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pages import illustrated_editions as editions
from pages import build

ROOT = Path(__file__).resolve().parents[1]
BODY = '''# Test Edition

"Stay," she said. It wasn't a command -- it was a question. Café, naïve, and the long dash — remain exactly as written.

The same sentence.

The same sentence.

## The Lantern

A **bright** lamp and an *unopened* letter waited beside the door.[^note]

> "Are you coming?"
>
> She left the question unanswered.

- First she opened the window.
- Then she watched the street.

---

She followed [the narrow road][road] until the rain stopped.

[road]: https://example.com/path
[^note]: The letter still carried its original seal.
'''


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag == 'figure': self.skip += 1
    def handle_endtag(self, tag):
        if tag == 'figure': self.skip -= 1
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)


def prose_text(value):
    parser = Text(); parser.feed(value)
    return re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()


def write_art(path, portrait=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (1024, 1536) if portrait else (1536, 1024), '#243e47')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, int(image.height*.7), image.width, image.height), fill='#a7b9b2')
    draw.ellipse((image.width*.4, image.height*.2, image.width*.6, image.height*.4), fill='#efc986')
    image.save(path)


def fixture_record(folder, mode='classic'):
    cover = folder / 'illustrated/sample/cover.jpg'
    scene = folder / 'illustrated/sample/illustrations/lantern.png'
    write_art(cover, True); write_art(scene)
    anchor = editions.block_anchors(BODY, 'Test Edition')[5]['id']
    return {'slug':'sample','title':'Test Edition','mode':mode,
            'source':{'slug':'original','commit':'a'*40,'bodySha256':hashlib.sha256(BODY.encode()).hexdigest()},
            'body':BODY, 'cover':{'id':'cover','path':'illustrated/sample/cover.jpg','sha256':editions.digest(cover)},
            'illustrations':[{'id':'lantern','after':anchor,'layout':'full-page' if mode=='cinematic' else 'inline',
                             'path':'illustrated/sample/illustrations/lantern.png','sha256':editions.digest(scene),
                             'alt':'A golden lantern above a pale, rain-soaked road.'}],
            'pdf':{'path':'illustrated/sample/edition.pdf','sha256':''}}


class RenderingTests(unittest.TestCase):
    def test_whole_document_preserves_text_and_reference_semantics(self):
        anchors = editions.block_anchors(BODY, 'Test Edition')
        entry = {'id':'one','after':anchors[2]['id'],'layout':'inline','path':'one.png','alt':'An illustration'}
        original = editions.render_prose(BODY, 'Test Edition', [])
        illustrated = editions.render_prose(BODY, 'Test Edition', [entry])
        self.assertEqual(prose_text(original), prose_text(illustrated))
        self.assertIn('https://example.com/path', illustrated)
        self.assertIn('original seal.', illustrated)
        self.assertIn("It wasn't a command -- it was a question.", prose_text(illustrated))
        self.assertIn('—', prose_text(illustrated))
        self.assertEqual(prose_text(illustrated).count('The same sentence.'), 2)
        self.assertIn('<strong>bright</strong>', illustrated)
        self.assertIn('<em>unopened</em>', illustrated)
        self.assertEqual(illustrated.count('<hr'), 2)  # Scene break plus footnote separator.
        self.assertEqual(len({a['id'] for a in anchors}), len(anchors))

    def test_only_exact_duplicate_title_is_removed(self):
        self.assertNotIn('<h1', editions.render_prose(BODY, 'Test Edition', []))
        self.assertIn('<h1', editions.render_prose(BODY, 'Different title', []))

    def test_indented_code_that_looks_like_title_is_preserved(self):
        for indent in ['    ', '\t']:
            body='\n'+indent+'# Test Edition\n\nActual prose.\n'
            rendered=editions.render_prose(body,'Test Edition',[])
            self.assertIn('<code># Test Edition',rendered)
        self.assertNotIn('<h1',editions.render_prose('\n   # Test Edition\n\nActual prose.','Test Edition',[]))

    def test_stale_anchor_missing_alt_and_duplicate_ids_fail(self):
        anchor = editions.block_anchors(BODY, 'Test Edition')[0]['id']
        good = {'id':'one','after':anchor,'layout':'inline','path':'one.png','alt':'Lamp'}
        for entries in [[good | {'after':'stale'}], [good | {'alt':''}], [good,good]]:
            with self.assertRaises(ValueError): editions.render_prose(BODY, 'Test Edition', entries)
        with self.assertRaises(ValueError):
            editions.render_prose(BODY.replace('Stay', 'Go'), 'Test Edition', [good])

    def test_layout_and_caption_are_separate_from_source(self):
        for mode in editions.MODES:
            with tempfile.TemporaryDirectory() as tmp:
                record = fixture_record(Path(tmp), mode)
                record['illustrations'][0]['caption'] = '<not markup>'
                document = editions.render_document(record)
                self.assertIn('mode-'+mode, document)
                self.assertIn('&lt;not markup&gt;', document)
                self.assertIn('Original story</a>', document)
                self.assertIn('Download PDF</a>', document)
                self.assertNotIn('edition-author', document)

    def test_output_protects_production_root_and_descendants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in [root/'illustrated', root/'illustrated/sample', root]:
                with self.assertRaises(ValueError): build.prepare_output(path, root)

    def test_snapshot_build_is_independent_of_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); pages = root/'pages'; pages.mkdir()
            record = fixture_record(pages)
            pdf = pages / record['pdf']['path']; pdf.write_bytes(b'%PDF-1.7\nfixture')
            record['pdf']['sha256'] = editions.digest(pdf)
            snapshot = pages/'illustrated.json'
            snapshot.write_text(json.dumps({'schemaVersion':1,'editions':[record]}),encoding='utf-8')
            out = root/'site'; out.mkdir()
            with patch('illustrated.edition.get_source_body',side_effect=AssertionError('source accessed')), patch.object(build,'load_story_source',side_effect=AssertionError('source accessed')):
                editions.build_editions(out, snapshot)
            self.assertTrue((out/'illustrated/sample.html').is_file())
            self.assertEqual((out/record['pdf']['path']).read_bytes(), pdf.read_bytes())
            (pages/record['illustrations'][0]['path']).write_bytes(b'changed')
            with self.assertRaises(ValueError): editions.load_snapshot(snapshot)

    def test_snapshot_rejects_path_traversal_and_duplicate_editions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); record=fixture_record(root)
            (root/record['pdf']['path']).write_bytes(b'%PDF-1.7\nfixture')
            record['pdf']['sha256']=editions.digest(root/record['pdf']['path'])
            snapshot=root/'illustrated.json'
            for records in [[record,record],[record | {'cover': record['cover'] | {'path':'illustrated/sample/../../outside.jpg'}}]]:
                snapshot.write_text(json.dumps({'schemaVersion':1,'editions':records}),encoding='utf-8')
                with self.assertRaises(ValueError): editions.load_snapshot(snapshot)

    def test_story_links_do_not_change_original_reading_destination(self):
        story=build.Story('original','Original','2026-09-13','2026-09-13T12:00:00Z','2026-09-13','PG',False,'reviewed','Prompt','covers/original.jpg','Prose')
        entry={'slug':'sample','source':{'slug':'original'},'mode':'classic','pdf':{'path':'illustrated/sample/edition.pdf'}}
        index=build.render_index(build.Catalog((story,)),[entry])
        self.assertIn('href="stories/original.html"',index)
        self.assertIn('Illustrated edition available',index)
        self.assertIn('../illustrated/sample.html',build.render_story(story,[entry]))


class PDFExportTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ILLUSTRATED_PDF_TESTS') == '1', 'Enable ILLUSTRATED_PDF_TESTS=1 after installing export dependencies')
    def test_real_responsive_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); web=folder/'web'; web.mkdir()
            record=fixture_record(web)
            (web/record['pdf']['path']).write_bytes(b'%PDF-1.7\nreader-link-fixture')
            (web/'illustrated/sample.html').write_text(editions.render_document(record),encoding='utf-8')
            shutil.copyfile(ROOT/'pages/illustrated.css',web/'illustrated.css')
            shutil.copyfile(ROOT/'pages/theme.js',web/'theme.js')
            shutil.copytree(ROOT/'pages/fonts',web/'fonts')
            subprocess.run(['node',str(ROOT/'illustrated/test-reader.mjs'),str(folder)],check=True,capture_output=True,text=True)

    @unittest.skipUnless(os.environ.get('ILLUSTRATED_PDF_TESTS') == '1', 'Enable ILLUSTRATED_PDF_TESTS=1 after installing export dependencies')
    def test_real_offline_export_all_modes(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            shutil.copyfile(ROOT/'pages/illustrated.css',folder/'illustrated.css')
            shutil.copytree(ROOT/'pages/fonts',folder/'fonts')
            for mode in sorted(editions.MODES):
                record=fixture_record(folder,mode)
                document=folder/f'{mode}.html'
                document.write_text(editions.render_document(record,stylesheet='illustrated.css',asset_prefix='',navigation=False),encoding='utf-8')
                pdf=folder/f'{mode}.pdf'
                subprocess.run(['node',str(ROOT/'illustrated/export.mjs'),str(document),str(pdf)],check=True,capture_output=True,text=True)
                reader=PdfReader(pdf)
                self.assertGreaterEqual(len(reader.pages),2)
                text=' '.join(page.extract_text() for page in reader.pages)
                text=re.sub(r'\s+',' ',text)
                for phrase in ['Stay,', "It wasn't a command -- it was a question.", 'Café, naïve', 'The same sentence.', 'original seal.']:
                    self.assertIn(phrase.replace('Stay,','Stay'),text)
                self.assertEqual(text.count('The same sentence.'),2)
                self.assertIn('—',text)
                for page in reader.pages:
                    self.assertAlmostEqual(float(page.mediabox.width),432,delta=.5)
                    self.assertAlmostEqual(float(page.mediabox.height),648,delta=.5)
                preserve=os.environ.get('ILLUSTRATED_VISUAL_OUTPUT')
                if preserve:
                    dest=Path(preserve);dest.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(pdf,dest/pdf.name)
                    shutil.copyfile(document,dest/document.name)
            preserve=os.environ.get('ILLUSTRATED_VISUAL_OUTPUT')
            if preserve:
                dest=Path(preserve)
                shutil.copyfile(folder/'illustrated.css',dest/'illustrated.css')
                shutil.copytree(folder/'fonts',dest/'fonts',dirs_exist_ok=True)
                shutil.copytree(folder/'illustrated',dest/'illustrated',dirs_exist_ok=True)


if __name__ == '__main__': unittest.main()
