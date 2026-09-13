"""End-to-end edition approval/capture tests, using only synthetic workspaces."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from illustrated import edition
from pages import illustrated_editions as reader
from pages import build
from pages import test_build as story_fixtures


def workspace(root: Path):
    case=story_fixtures.StorySystemTests()
    source=case.make_current_story(root)
    build.capture_story('sample',root,root/'pages/catalog.json')
    for args in [('init','-q','-b','codex/illustrated-fixture'),('config','user.email','fixture@example.invalid'),('config','user.name','Test Fixture'),('add','.'),('commit','-qm','Synthetic source')]:
        subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True)
    return source


def prepare(root: Path,slug='sample',mode='Classic'):
    manifest=edition.create_edition(root,'sample','[IL] "Sample"',slug=slug,mode=mode)
    directory=root/'illustrated'/slug
    (directory/'plan.md').write_text('# Illustration plan\n\n## Art direction\n\nQuiet blue and gold fixture artwork.\n\n## Counts\n\nOne character sheet and one interior scene. Reuse the cover.\n',encoding='utf-8')
    edition.inspect_original(root,slug,'source-cover','Fixture cover visually inspected.')
    anchors=reader.block_anchors(edition.get_source_body(root,manifest),manifest['title'])
    edition.configure_asset(root,slug,'person',kind='character',prompt='A fixture reference sheet.',size='1024x1024')
    edition.configure_asset(root,slug,'arrival',kind='illustration',prompt='The fixture arrival.',size='1536x1024',references=['person'],after=anchors[-1]['id'],alt='A figure under a pale morning sky.')
    edition.approve(root,slug,'plan','Synthetic user approves this exact fixture plan and count.')
    cli=root/'fake_imagegen.py';cli.write_text('# never executed: mocked image transport',encoding='utf-8')
    def generate(command,**kwargs):
        size=tuple(map(int,command[command.index('--size')+1].split('x')))
        Image.new('RGB',size,(36,62,71)).save(command[command.index('--out')+1])
    edition.generate_asset(root,slug,'person',root/(slug+'-person.png'),imagegen_cli=cli,runner=generate)
    edition.accept_candidate(root,slug,'person','Fixture reference inspected at saved size.')
    preview=reader.layout_sample(root,slug,root/(slug+'-layout'))
    edition.record_layout_preview(root,slug,preview,'Fixture typography, proportions and image placement inspected.')
    edition.approve(root,slug,'visuals','Synthetic user approves references, cover and layout.')
    edition.generate_asset(root,slug,'arrival',root/(slug+'-arrival.png'),imagegen_cli=cli,runner=generate)
    edition.accept_candidate(root,slug,'arrival','Fixture scene checked against its source and reference.')
    return edition.load_edition(root,slug)


def approve_final(root: Path,slug='sample',real_pdf=False):
    if real_pdf:
        reader.render_edition(root,slug)
    else:
        (root/'illustrated'/slug/'edition.pdf').write_bytes(b'%PDF-1.7\nsynthetic export transport fixture')
        edition.record_render(root,slug)
    (root/'illustrated'/slug/'review.md').write_text('# Review\n\nVerdict: PASS\nReviewer: independent-fixture\n\n- Source fidelity: PASS\n- Visual continuity: PASS\n- Web readability: PASS\n- Every PDF page: PASS\n\n## Findings\n\n- Blocking: none\n',encoding='utf-8')
    edition.record_review(root,slug,'independent-fixture','Synthetic review of all fixture assets and pages.')
    edition.approve(root,slug,'final','Synthetic user approves the final fixture edition.')


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=workspace(self.root)
    def tearDown(self): self.temp.cleanup()

    def test_full_lifecycle_capture_and_snapshot_only_build(self):
        before={p.name:p.read_bytes() for p in self.source.iterdir() if p.is_file()}
        prepare(self.root)
        approve_final(self.root)
        result=reader.capture_edition(self.root,'sample')
        self.assertEqual(result['body'],edition.get_source_body(self.root,edition.load_edition(self.root,'sample')))
        self.assertEqual(result['mode'],'classic')
        self.assertNotIn('coverInspection',result['source'])
        with patch('illustrated.edition.get_source_body',side_effect=AssertionError('Live source read')),patch.object(build,'load_story_source',side_effect=AssertionError('Live source read')):
            build.build(self.root/'_site',self.root/'pages/catalog.json')
        self.assertTrue((self.root/'_site/illustrated/sample.html').is_file())
        self.assertIn('Illustrated edition available',(self.root/'_site/index.html').read_text(encoding='utf-8'))
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.source.iterdir() if p.is_file()})
        self.assertEqual(reader.check_snapshot(self.root),[])

    def test_capture_requires_final_approval_and_reconciled_canon(self):
        prepare(self.root)
        with self.assertRaises(ValueError): reader.capture_edition(self.root,'sample')
        approve_final(self.root)
        catalog=self.root/'pages/catalog.json';data=json.loads(catalog.read_text(encoding='utf-8'))
        data['stories'][0]['canon']=not data['stories'][0]['canon']
        data['stories'][0]['status']='canon' if data['stories'][0]['canon'] else 'reviewed'
        catalog.write_text(json.dumps(data),encoding='utf-8')
        with self.assertRaises(ValueError): reader.capture_edition(self.root,'sample')

    def test_two_editions_and_ordinary_capture_do_not_refresh_them(self):
        for slug,mode in [('sample','Classic'),('sample-cinematic','Cinematic')]:
            prepare(self.root,slug,mode);approve_final(self.root,slug);reader.capture_edition(self.root,slug)
        snapshot=self.root/'pages/illustrated.json';before=snapshot.read_bytes()
        build.capture_story('sample',self.root,self.root/'pages/catalog.json')
        build.capture_all(self.root,self.root/'pages/catalog.json')
        self.assertEqual(before,snapshot.read_bytes())
        self.assertEqual(len(reader.load_snapshot(snapshot)),2)
        source_file=self.source/'story.md';source_file.write_text(source_file.read_text(encoding='utf-8')+'\nChanged source.\n',encoding='utf-8')
        with self.assertRaises(ValueError): reader.capture_edition(self.root,'sample')
        out=self.root/'frozen';out.mkdir();reader.build_editions(out,snapshot)
        self.assertNotIn('Changed source.',(out/'illustrated/sample.html').read_text(encoding='utf-8'))

    def test_failed_recapture_restores_published_bytes(self):
        prepare(self.root);approve_final(self.root);reader.capture_edition(self.root,'sample')
        snapshot=self.root/'pages/illustrated.json';before=snapshot.read_bytes()
        old_assets={p.relative_to(self.root/'pages').as_posix():p.read_bytes() for p in (self.root/'pages/illustrated').rglob('*') if p.is_file()}
        real_load=reader.load_snapshot
        calls=0
        def fail_second(path):
            nonlocal calls
            calls+=1
            if calls==2: raise ValueError('Injected validation failure after replacement')
            return real_load(path)
        with patch.object(reader,'load_snapshot',side_effect=fail_second):
            with self.assertRaises(ValueError): reader.capture_edition(self.root,'sample')
        self.assertEqual(before,snapshot.read_bytes())
        for path,data in old_assets.items(): self.assertEqual(data,(self.root/'pages'/path).read_bytes())

    def test_production_commands_on_main_fail_before_writing(self):
        prepare(self.root);approve_final(self.root)
        before={p.relative_to(self.root):p.read_bytes() for parent in ['stories','illustrated','pages'] for p in (self.root/parent).rglob('*') if p.is_file()}
        subprocess.run(['git','-C',str(self.root),'branch','-m','main'],check=True,capture_output=True)
        output=self.root/'untouched-preview';output.mkdir()
        marker=output/'keep.txt';marker.write_text('Keep this preview',encoding='utf-8')
        for operation in [lambda:reader.render_edition(self.root,'sample'),lambda:reader.capture_edition(self.root,'sample'),lambda:reader.preview_edition(self.root,'sample',output),lambda:reader.layout_sample(self.root,'sample',output)]:
            with self.assertRaisesRegex(ValueError,'non-main'):operation()
        self.assertEqual(marker.read_text(encoding='utf-8'),'Keep this preview')
        self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for parent in ['stories','illustrated','pages'] for p in (self.root/parent).rglob('*') if p.is_file()})

    def test_snapshot_checks_complete_inventory_identity_and_placement(self):
        prepare(self.root);approve_final(self.root);reader.capture_edition(self.root,'sample')
        snapshot=self.root/'pages/illustrated.json';original=json.loads(snapshot.read_text(encoding='utf-8'))
        edits=[lambda r:r.update(illustrations=[]),lambda r:r['illustrations'][0].update(alt='Different description'),lambda r:r.update(title='Different title'),lambda r:r['source'].update(commit='0'*40)]
        for edit in edits:
            changed=copy.deepcopy(original);edit(changed['editions'][0]);snapshot.write_text(json.dumps(changed),encoding='utf-8')
            with self.assertRaises(ValueError):reader.check_snapshot(self.root)
        snapshot.write_text(json.dumps(original),encoding='utf-8')
        self.assertEqual(reader.check_snapshot(self.root),[])

    def test_production_asset_tampering_fails_but_new_draft_keeps_snapshot(self):
        prepare(self.root);approve_final(self.root);reader.capture_edition(self.root,'sample')
        for relative in ['edition.pdf','illustrations/arrival.png']:
            path=self.root/'illustrated/sample'/relative;original=path.read_bytes();path.write_bytes(original+b'tampered')
            with self.assertRaisesRegex(ValueError,'Production/capture'):reader.check_snapshot(self.root)
            path.write_bytes(original)
        source=self.source/'story.md';source.write_text(source.read_text(encoding='utf-8')+'\nNew prose.\n',encoding='utf-8')
        self.assertIn('source has changed',reader.check_snapshot(self.root)[0])
        plan=self.root/'illustrated/sample/plan.md';plan.write_text(plan.read_text(encoding='utf-8')+'\nA proposed later revision.\n',encoding='utf-8')
        self.assertIn('earlier edition',reader.check_snapshot(self.root)[0])

    @unittest.skipUnless(os.environ.get('ILLUSTRATED_PDF_TESTS')=='1','Enable real Chromium export')
    def test_real_export_through_approval_and_capture(self):
        from pypdf import PdfReader
        prepare(self.root);approve_final(self.root,real_pdf=True)
        record=reader.capture_edition(self.root,'sample')
        pdf=self.root/'pages'/record['pdf']['path']
        self.assertGreaterEqual(len(PdfReader(pdf).pages),2)
        self.assertEqual(reader.digest(pdf),record['pdf']['sha256'])


if __name__=='__main__':unittest.main()
