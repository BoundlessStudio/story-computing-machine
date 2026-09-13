"""Synthetic lifecycle tests. No repository story is opened and no image API is called."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image

from illustrated import edition as ed
from pages.illustrated_editions import block_anchors


BODY = '\n# Sample\n\n"Hello," she said -- *exactly*.\n\nSame paragraph.\n\nSame paragraph.\n\n---\n\nA door opened.\n'


class EditionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.make_source('sample', 'Sample')
        self.git('init', '-b', 'codex/illustrated-test')
        self.git('add', 'stories')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Synthetic source')
        self.cli = self.root / 'fake_image_gen.py'
        self.cli.write_text('# Never executed: tests inject a runner.\n', encoding='utf-8')
        self.before = {path.relative_to(self.root): path.read_bytes() for path in (self.root / 'stories').rglob('*') if path.is_file()}

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True, text=True).stdout.strip()

    def make_source(self, slug, title, bundle=False, canon=True):
        path = self.root / 'stories' / slug
        path.mkdir(parents=True)
        fields = f'---\ntitle: {json.dumps(title)}\nslug: {slug}\ncreated: 2026-09-13\n'
        if not bundle:
            fields += f'canon: {str(canon).lower()}\n'
        (path / ('05-story.md' if bundle else 'story.md')).write_text(fields + '---\n' + BODY.replace('# Sample', f'# {title}'), encoding='utf-8')
        (path / ('00-prompt.md' if bundle else 'prompt.md')).write_text('# Prompt\n\n[WP] A traveler enters.\n\n## Reference images\n\n- None supplied.\n', encoding='utf-8')
        if not bundle:
            (path / 'review.md').write_text('# Review\n\nVerdict: PASS\n\n## Continuity\n\n- Prompt: PASS\n- Universe: PASS\n- Internal: PASS\n\n## Findings\n\n- Blocking: none\n', encoding='utf-8')
        if bundle:
            (path / 'story.json').write_text(json.dumps(dict(title=title, slug=slug, created='2026-09-13', canon=canon)), encoding='utf-8')
        Image.new('RGB', (864, 1536), '#463950').save(path / 'title-image.jpg')
        return path

    def create(self, references=None):
        return ed.create_edition(self.root, 'Sample', '[IL] "Sample"\nPreserve every word.', references=references)

    def plan(self, references=None):
        manifest = self.create(references)
        ed.inspect_original(self.root, 'sample', 'source-cover', 'Viewed original: violet door and pale robe; original title remains legible.')
        for item in manifest['externalReferences']:
            ed.inspect_original(self.root, 'sample', item['id'], 'Viewed original and confirmed the blue sleeve and profile.')
        ed.configure_asset(self.root, 'sample', 'traveler', kind='character', prompt='A consistent traveler reference sheet.', size='1024x1024')
        ed.configure_asset(self.root, 'sample', 'gate', kind='location', prompt='Location sheet: the same stone gate.', size='1024x1024')
        anchor = block_anchors(ed.get_source_body(self.root, manifest), manifest['title'])[0]['id']
        ed.configure_asset(self.root, 'sample', 'arrival', kind='illustration', prompt='Traveler arrives through the gate.', references=['traveler', 'gate'], after=anchor, alt='The traveler stands inside the open gate.')
        directory = self.root / 'illustrated/sample'
        (directory / 'plan.md').write_text('# Plan\n\n## Story analysis\n\nThe traveler enters; no new story events.\n\n## Art direction\n\nViolet ink, pale robes and weathered stone.\n\n## Moments\n\nOne arrival illustration after the opening.\n\n## Counts\n\nTwo reference sheets, one reused cover, one interior illustration.\n', encoding='utf-8')
        return ed.load_edition(self.root, 'sample')

    @staticmethod
    def runner(command, check=True):
        output = Path(command[command.index('--out') + 1])
        size = tuple(map(int, command[command.index('--size') + 1].split('x')))
        Image.new('RGB', size, '#38587b').save(output)
        return subprocess.CompletedProcess(command, 0)

    def produce(self, asset_id):
        output = self.root / f'{asset_id}-candidate.png'
        ed.generate_asset(self.root, 'sample', asset_id, output, imagegen_cli=self.cli, runner=self.runner)
        return ed.accept_candidate(self.root, 'sample', asset_id, 'Viewed exact saved pixels: identity, costume, architecture, event and palette match.')

    def visuals(self):
        self.plan()
        ed.approve(self.root, 'sample', 'plan', 'I approve the one-illustration plan and separate reference counts.')
        self.produce('traveler')
        self.produce('gate')
        preview = self.root / 'layout.html'
        preview.write_text('<html><p>Selectable sample prose and approved reference layout.</p></html>', encoding='utf-8')
        ed.record_layout_preview(self.root, 'sample', preview, 'Viewed readable layout, preserved cover proportions and margins.')
        return ed.approve(self.root, 'sample', 'visuals', 'I approve these references, the original cover and this layout.')

    def complete(self):
        self.visuals()
        self.produce('arrival')
        directory = self.root / 'illustrated/sample'
        (directory / 'edition.pdf').write_bytes(b'%PDF-1.7\nSynthetic lifecycle-only PDF bytes.\n%%EOF')
        ed.record_render(self.root, 'sample')
        (directory / 'review.md').write_text('# Review\n\nVerdict: PASS\n\n- Source fidelity: PASS\n- Visual continuity: PASS\n- Web readability: PASS\n- Every PDF page: PASS\n- Blocking: none\n', encoding='utf-8')
        ed.record_review(self.root, 'sample', 'independent-test-reviewer', 'Every synthetic page and all prose compared against source; visual/reader gates checked.')
        return ed.approve(self.root, 'sample', 'final', 'I approve this completed edition and PDF for capture.')

    def test_source_resolution_current_bundle_ambiguous_and_invalid(self):
        self.assertEqual('sample', ed.resolve_source(self.root, 'Sample')['slug'])
        self.make_source('legacy', 'Legacy', bundle=True)
        manifest = ed.create_edition(self.root, 'legacy', '[Illustrate] Legacy')
        self.assertEqual('bundle', manifest['source']['layout'])
        self.assertIn('stories/legacy/story.json', manifest['source']['files'])
        self.make_source('other', 'Sample')
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            ed.resolve_source(self.root, 'Sample')
        self.assertEqual('sample', ed.resolve_source(self.root, 'sample')['slug'])
        (self.source / 'story.md').write_text('No marker', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'frontmatter'):
            ed.resolve_source(self.root, 'sample')

    def test_scaffold_does_not_copy_prose_or_modify_canon_source(self):
        manifest = self.create()
        self.assertEqual(BODY, ed.get_source_body(self.root, manifest))
        directory = self.root / 'illustrated/sample'
        self.assertEqual({'prompt.md', 'plan.md', 'review.md', 'edition.json', 'cover.jpg', 'references', 'illustrations'}, {path.name for path in directory.iterdir()})
        self.assertEqual(self.before, {path.relative_to(self.root): path.read_bytes() for path in (self.root / 'stories').rglob('*') if path.is_file()})
        self.assertTrue(manifest['cover']['reused'])

    def test_main_duplicate_and_traversal_refused(self):
        self.create()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.create()
        with self.assertRaisesRegex(ValueError, 'kebab'):
            ed.create_edition(self.root, 'sample', 'Request', slug='../source')
        self.git('checkout', '-b', 'main')
        with self.assertRaisesRegex(ValueError, 'non-main'):
            ed.create_edition(self.root, 'sample', 'Request', slug='second')

    def test_source_hash_normalizes_line_endings_but_rejects_real_changes(self):
        manifest = self.create()
        path = self.source / 'story.md'
        path.write_bytes(ed._text(path).encode('utf-8').replace(b'\n', b'\r\n'))
        self.assertEqual(BODY, ed.source_body(self.root, manifest))
        path.write_text(path.read_text(encoding='utf-8') + 'New sentence.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            ed.validate_edition(self.root, 'sample')
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            ed.get_source_body(self.root, manifest)

    def test_missing_originals_and_original_inspection(self):
        prompt = self.source / 'prompt.md'
        prompt.write_text('# Prompt\n\n## Reference images\n\n- `original.png`\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'reattach'):
            self.create()
        original = self.root / 'original.png'
        Image.new('RGB', (32, 32), 'blue').save(original)
        self.plan([original])
        original.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or changed original'):
            ed.validate_edition(self.root, 'sample', 'plan')

    def test_approval_is_explicit_and_plan_changes_invalidate_it(self):
        self.plan()
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            ed.approve(self.root, 'sample', 'plan', '')
        with self.assertRaisesRegex(ValueError, 'actual user'):
            ed.approve(self.root, 'sample', 'plan', 'Approve', actor='agent')
        runner = Mock(side_effect=self.runner)
        with self.assertRaisesRegex(ValueError, 'plan approval'):
            ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'candidate.png', imagegen_cli=self.cli, runner=runner)
        runner.assert_not_called()
        manifest = ed.approve(self.root, 'sample', 'plan', 'Approved the exact displayed plan.')
        self.assertIn('decision', manifest['approvals']['plan'])
        plan = self.root / 'illustrated/sample/plan.md'
        plan.write_text(plan.read_text(encoding='utf-8') + '\nA different placement.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'stale.*plan approval'):
            ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'candidate.png', imagegen_cli=self.cli, runner=runner)
        runner.assert_not_called()

    def test_mocked_generation_requires_visuals_for_scenes_and_includes_all_refs(self):
        self.plan()
        ed.approve(self.root, 'sample', 'plan', 'Approved the plan.')
        with self.assertRaises(ValueError):
            ed.generate_asset(self.root, 'sample', 'arrival', self.root / 'arrival.png', imagegen_cli=self.cli, runner=self.runner)
        manifest = self.produce('traveler')
        self.assertEqual(1, manifest['references'][0]['attempts'])
        self.produce('gate')
        ed.validate_edition(self.root, 'sample', 'references')  # Preview is produced at this point.
        preview = self.root / 'preview.html'; preview.write_text('Sample', encoding='utf-8')
        ed.record_layout_preview(self.root, 'sample', preview, 'Viewed layout.')
        ed.approve(self.root, 'sample', 'visuals', 'Approved exact references, cover, layout.')
        runner = Mock(side_effect=self.runner)
        ed.generate_asset(self.root, 'sample', 'arrival', self.root / 'arrival.png', imagegen_cli=self.cli, runner=runner)
        command = runner.call_args.args[0]
        self.assertEqual(ed.MODEL, command[command.index('--model') + 1])
        self.assertEqual('high', command[command.index('--quality') + 1])
        self.assertEqual(2, command.count('--image'))
        self.assertIn(str(self.root / 'illustrated/sample/references/traveler.png'), command)
        self.assertIn(str(self.root / 'illustrated/sample/references/gate.png'), command)

    def test_initial_plus_two_corrections_persist_and_require_user_extension(self):
        self.plan(); ed.approve(self.root, 'sample', 'plan', 'Approve plan.')
        for attempt in range(3):
            ed.generate_asset(self.root, 'sample', 'traveler', self.root / f'candidate-{attempt}.png', imagegen_cli=self.cli, runner=self.runner, correction='Fix the sleeve.' if attempt else '')
            self.assertEqual(attempt + 1, ed.load_edition(self.root, 'sample')['references'][0]['attempts'])
        runner = Mock(side_effect=self.runner)
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'fourth.png', imagegen_cli=self.cli, runner=runner, correction='Fix the sleeve.')
        runner.assert_not_called()
        ed.allow_extra_attempt(self.root, 'sample', 'traveler', 'Please try one more time with the corrected sleeve.')
        ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'fourth.png', imagegen_cli=self.cli, runner=runner, correction='Fix the sleeve.')
        self.assertEqual(4, ed.load_edition(self.root, 'sample')['references'][0]['attempts'])

    def test_failure_and_interruption_recovery_preserve_count(self):
        self.plan(); ed.approve(self.root, 'sample', 'plan', 'Approve plan.')
        with self.assertRaisesRegex(ValueError, 'persisted attempt'):
            ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'missing.png', imagegen_cli=self.cli, runner=Mock(side_effect=RuntimeError('failed')))
        manifest = ed.load_edition(self.root, 'sample')
        self.assertEqual(1, manifest['references'][0]['attempts'])
        manifest['references'][0]['candidate']['status'] = 'generating'
        ed.save_edition(self.root, manifest)
        with self.assertRaisesRegex(ValueError, 'outstanding'):
            ed.generate_asset(self.root, 'sample', 'gate', self.root / 'gate.png', imagegen_cli=self.cli, runner=self.runner)
        ed.resolve_generation(self.root, 'sample', 'traveler', 'failed', 'Verified process exit code 1 in the terminal; no process remains.')
        self.assertEqual(1, ed.load_edition(self.root, 'sample')['references'][0]['attempts'])
        self.produce('gate')

    def test_dry_run_neither_invokes_runner_nor_changes_attempts(self):
        self.plan(); ed.approve(self.root, 'sample', 'plan', 'Approve plan.')
        before = (self.root / 'illustrated/sample/edition.json').read_bytes()
        runner = Mock()
        result = ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'dry.png', imagegen_cli=self.cli, dry_run=True, runner=runner)
        self.assertIn('--dry-run', result['command'])
        self.assertIn(ed.MODEL, result['command'])
        runner.assert_not_called()
        self.assertEqual(before, (self.root / 'illustrated/sample/edition.json').read_bytes())
        self.assertFalse((self.root / 'dry.png').exists())

    def test_candidate_tampering_and_reference_changes_block_acceptance(self):
        self.plan(); ed.approve(self.root, 'sample', 'plan', 'Approve plan.')
        output = self.root / 'candidate.png'
        ed.generate_asset(self.root, 'sample', 'traveler', output, imagegen_cli=self.cli, runner=self.runner)
        Image.new('RGB', (1024, 1024), 'red').save(output)
        with self.assertRaisesRegex(ValueError, 'Candidate bytes changed'):
            ed.accept_candidate(self.root, 'sample', 'traveler', 'Viewed changed pixels.')

    def test_complete_edition_review_final_approval_and_source_immutability(self):
        manifest = self.complete()
        self.assertEqual('sample', ed.validate_edition(self.root, 'sample', 'final')['slug'])
        self.assertEqual(BODY, ed.source_body(self.root, manifest))
        self.assertEqual(self.before, {path.relative_to(self.root): path.read_bytes() for path in (self.root / 'stories').rglob('*') if path.is_file()})
        (self.root / 'illustrated/sample/review.md').write_text('Verdict: PASS\nAn unbound replacement review.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'fresh independent'):
            ed.validate_edition(self.root, 'sample', 'final')

    def test_moving_illustration_and_alt_does_not_invalidate_generated_art(self):
        self.visuals(); self.produce('arrival')
        previous = ed.load_edition(self.root, 'sample')
        before = {asset['id']: (asset['sha256'], asset['attempts']) for asset in ed._assets(previous)}
        moved_anchor = block_anchors(ed.get_source_body(self.root, previous), previous['title'])[1]['id']
        ed.configure_asset(self.root, 'sample', 'arrival', kind='illustration', prompt='Traveler arrives through the gate.', references=['traveler', 'gate'], after=moved_anchor, layout='full-page', alt='The open gate frames the traveler.')
        ed.approve(self.root, 'sample', 'plan', 'Approve the moved illustration and corrected description.')
        preview = self.root / 'layout-2.html'; preview.write_text('Moved layout', encoding='utf-8')
        ed.record_layout_preview(self.root, 'sample', preview, 'Inspected moved illustration layout.')
        ed.approve(self.root, 'sample', 'visuals', 'Approve the unchanged references and this updated layout.')
        current = ed.validate_edition(self.root, 'sample', 'render')
        self.assertEqual(before, {asset['id']: (asset['sha256'], asset['attempts']) for asset in ed._assets(current)})
        ed.configure_asset(self.root, 'sample', 'arrival', kind='illustration', prompt='A closer view of arrival.', references=['traveler', 'gate'], after=moved_anchor, alt='A closer view.')
        current = ed.load_edition(self.root, 'sample')
        for asset in current['references']:
            ed._check_asset(self.root, current, asset)
        with self.assertRaisesRegex(ValueError, 'stale generation'):
            ed._check_asset(self.root, current, current['illustrations'][0])

    def test_visual_approval_binds_renderer_and_copied_preview_resources(self):
        self.visuals()
        preview = self.root / 'layout.html'
        css = self.root / 'sample.css'
        font = self.root / 'sample.woff2'
        font.write_bytes(b'synthetic-font-resource')
        css.write_text('@font-face { font-family: Sample; src: url("sample.woff2"); }', encoding='utf-8')
        preview.write_text('<html><head><link rel="stylesheet" href="sample.css"></head><body>Sample</body></html>', encoding='utf-8')
        ed.record_layout_preview(self.root, 'sample', preview, 'Viewed this complete preview and loaded resources.')
        font.write_bytes(b'changed-font-resource')
        with self.assertRaisesRegex(ValueError, 'preview resources.*changed'):
            ed.approve(self.root, 'sample', 'visuals', 'Approve the displayed preview.')
        font.write_bytes(b'synthetic-font-resource')
        with patch.object(ed, '_renderer_hashes', return_value={'new-renderer': 'changed'}):
            with self.assertRaisesRegex(ValueError, 'rendering resources changed'):
                ed.approve(self.root, 'sample', 'visuals', 'Approve the displayed preview.')
        ed.approve(self.root, 'sample', 'visuals', 'Approve the unchanged preview and resources.')

    def test_pending_current_source_review_is_not_a_finished_source(self):
        (self.source / 'review.md').write_text('Verdict: PENDING\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'source review is not passing'):
            self.create()
        self.assertFalse((self.root / 'illustrated/sample').exists())

    def test_plan_rejects_stale_anchor_before_any_image_call(self):
        manifest = self.plan()
        manifest['illustrations'][0]['after'] = 'invented-anchor'
        ed.save_edition(self.root, manifest)
        with self.assertRaisesRegex(ValueError, 'stale illustration anchor'):
            ed.approve(self.root, 'sample', 'plan', 'Approve this plan.')
        self.assertEqual(0, ed.load_edition(self.root, 'sample')['references'][0]['attempts'])

    def test_generation_cannot_write_a_candidate_into_a_story(self):
        self.plan(); ed.approve(self.root, 'sample', 'plan', 'Approve plan.')
        runner = Mock()
        with self.assertRaisesRegex(ValueError, 'protected production'):
            ed.generate_asset(self.root, 'sample', 'traveler', self.source / 'candidate.png', imagegen_cli=self.cli, runner=runner)
        runner.assert_not_called()
        self.assertFalse((self.source / 'candidate.png').exists())

    def test_display_title_and_missing_source_pins_are_validated(self):
        manifest = self.plan()
        previous = ed.stage_digest(self.root, manifest, 'plan')
        manifest['title'] = 'A new title'
        self.assertNotEqual(previous, ed.stage_digest(self.root, manifest, 'plan'))
        manifest['source']['files'].pop('stories/sample/review.md')
        ed.save_edition(self.root, manifest)
        with self.assertRaisesRegex(ValueError, 'Pin exactly'):
            ed.load_edition(self.root, 'sample')

    def test_a_candidate_is_reviewed_before_starting_the_next_image(self):
        self.plan(); ed.approve(self.root, 'sample', 'plan', 'Approve plan.')
        ed.generate_asset(self.root, 'sample', 'traveler', self.root / 'first.png', imagegen_cli=self.cli, runner=self.runner)
        with self.assertRaisesRegex(ValueError, 'accept or reject'):
            ed.generate_asset(self.root, 'sample', 'gate', self.root / 'next.png', imagegen_cli=self.cli, runner=self.runner)
        ed.reject_candidate(self.root, 'sample', 'traveler', 'Viewed pixels; the sleeve is on the wrong arm. Return a targeted correction.')
        self.produce('gate')

    def test_repin_requires_direction_and_invalidates_downstream_without_resetting_attempts(self):
        self.visuals()
        path = self.source / 'story.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nMore source prose.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Source changed'):
            ed.validate_edition(self.root, 'sample')
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            ed.repin_source(self.root, 'sample', '')
        manifest = ed.repin_source(self.root, 'sample', 'Use this updated source version and ask me to approve the revised plan.')
        self.assertEqual({}, manifest['approvals'])
        self.assertEqual(1, manifest['references'][0]['attempts'])
        self.assertIsNone(manifest['references'][0]['accepted'])
        self.assertIn('More source prose.', ed.source_body(self.root, manifest))


if __name__ == '__main__':
    unittest.main()
