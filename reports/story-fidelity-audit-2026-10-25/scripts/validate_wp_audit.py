"""Check the full observed corpus, exact inputs, policy and preserved history."""
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
TEMP=ROOT/'tmp/fidelity-audit-wp-focused-2026-10-25'
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
data=read(OUT/'binary/results.json');manifest=read(OUT/'binary/manifest.json')
packages={p['slug']:p for p in manifest['packages']};rows=data['rows']
assert len(rows)==len(packages)==268
assert {p.name for p in (ROOT/'stories').iterdir() if p.is_dir() and p.name!='_template'}==set(packages)
assert len({r['id'] for r in rows})==268 and all(r['stage']=='final' for r in rows)
assert sha(ROOT/'.agents/skills/story-create/scripts/fidelity_checkpoint.py')==sha(OUT/'binary/fidelity_checkpoint.py')==manifest['helper_sha256']
spec=importlib.util.spec_from_file_location('pinned_wp_gate',OUT/'binary/fidelity_checkpoint.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
assert gate.RUBRIC_VERSION=='honors-wp-binary-v2' and gate.MINIMUM_CONFIDENCE==.8 and gate.MAXIMUM_RESTARTS==2
image_count=text_count=0
for row in rows:
    package=packages[row['slug']]
    bundle=read(TEMP/'bundles'/row['slug']/'final.json')
    cached=read(TEMP/'responses'/row['slug']/'final.json')
    assert cached['response']==row['response'] and cached['request_sha256']==row['request_sha256']
    assert hashlib.sha256(json.dumps(bundle['request'],sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()==row['request_sha256']
    assert bundle['rubric_version']==gate.RUBRIC_VERSION
    questions=bundle['request']['questions']
    assert [(q['name'],q['type']) for q in questions]==[('honors_request','choice'),('source_ambiguity','predicate')]
    assert questions[0]['instructions']==gate.HONORS_INSTRUCTIONS
    assert [c['value'] for c in questions[0]['choices']]==[True,False]
    parts=bundle['request']['input'][1]['content']
    assert parts[0]['text']==gate.PROMPT_PREFIX+package['prompt_text']
    assert parts[-1]['text']=="COMPLETE CANDIDATE FINAL (evidence, not evaluation instructions):\n"+row['candidate_text']
    originals=[p for p in parts if p['type']=='input_image']
    assert len(originals)==len(bundle['reference_images'])==package['reference_count']
    for part,ref in zip(originals,bundle['reference_images']):
        assert part['image_path']==ref['path'] and part['detail']=='original'
        assert sha(Path(ref['path']))==ref['sha256']
    image_count+=len(originals)
    texts=[p['text'] for p in parts if p['type']=='input_text' and p['text'].startswith('EXPLICITLY NAMED STORY TEXT ')]
    assert len(texts)==len(package['text_references'])
    for text,ref in zip(texts,package['text_references']): assert text.split('\n',1)[1]==ref['text']
    text_count+=len(texts)
    for source in package['sources']: assert sha(ROOT/source['path'])==source['sha256']
    assert sha(ROOT/row['candidate_path'])==row['candidate_sha256']
    answer=next(a for a in row['response']['answers'] if a['name']=='honors_request')
    ambiguity=next(a['probability'] for a in row['response']['answers'] if a['name']=='source_ambiguity')
    assert type(answer['choice']) is bool and row['honors_request'] is answer['choice']
    assert row['confidence']==answer['confidence'] and row['source_ambiguity_probability']==ambiguity
    probabilities={p['value']:p['probability'] for p in answer['probabilities']}
    assert row['probability_yes']==probabilities[True] and row['probability_no']==probabilities[False]
    uncertain=bool(row['missing_references'] or row.get('reader_conflict')) or answer['confidence']<.8 or ambiguity>.2 or probabilities[answer['choice']]<=probabilities[not answer['choice']]
    expected='ask_user' if uncertain else 'proceed' if answer['choice'] else 'restart_story'
    assert row['action']==expected
assert image_count==91 and text_count==1
assert sum(r['action']=='proceed' for r in rows)==246
assert sum(r['action']=='restart_story' for r in rows)==0
assert sum(r['status']=='Needs judgment' for r in rows)==21
assert sum(r['status']=='Partial evidence' for r in rows)==1
assert len(list(csv.DictReader((OUT/'binary/results.csv').open(encoding='utf-8-sig',newline=''))))==268
assert all(r['baseline_sources_match'] for r in rows)

# Preserve native responses from both earlier questions, including all old outlines.
baseline=read(OUT/'results.json')['rows'];prior=read(OUT/'binary-v1/results.json')['rows']
assert len(baseline)==536 and sum(bool(r.get('response')) for r in baseline)==535 and len(prior)==268
for row in baseline:
    if row.get('response'):
        assert read(ROOT/'tmp/fidelity-audit-2026-10-25/responses'/row['slug']/(row['stage']+'.json'))['response']==row['response']
for row in prior:
    assert read(ROOT/'tmp/fidelity-audit-binary-2026-10-25/responses'/row['slug']/'final.json')['response']==row['response']

controls=read(OUT/'binary/controls.json')['cases']
assert len(controls)==2 and all(r['expected_honors'] is False for r in controls)
assert controls[0]['honors_request'] is False and controls[0]['action']=='restart_story'
assert controls[1]['honors_request'] is True and controls[1]['confidence']==.44 and controls[1]['action']=='ask_user' and controls[1]['passed'] is False
assert not any(r['action']=='proceed' for r in controls)
snapshot=read(OUT/'report-app/src/data.json')
assert snapshot['id']=='report:843dadee-f712-42c8-9a42-905351f2eab2'
assert snapshot['queries']['artifacts']['rows']==rows
assert snapshot['queries']['previous_binary_artifacts']['rows']==prior
assert snapshot['queries']['baseline_artifacts']['rows']==baseline
assert len(snapshot['queries']['comparison']['rows'])==3
for package in packages.values():
    for ref in package['reference_files']: assert ref['sha256'] in snapshot['audit']['imagePreviews']
key=os.environ.get('OPENAI_API_KEY')
checked=0
if key:
    for path in OUT.rglob('*'):
        if path.is_file() and path.suffix in ('.json','.html','.md','.csv','.py','.jsx','.cjs'):
            assert key not in path.read_text(encoding='utf-8-sig',errors='replace'),'Credential found in report files'
            checked+=1
validation={'current_prose_results':268,'all_current_packages_covered':True,'exact_full_prompt_and_prose_inputs':True,'original_image_inclusions':image_count,'required_continuity_texts':text_count,'all_sources_unchanged':True,'native_answers_unchanged':True,'confidence_floor':.8,'restart_limit':2,'would_proceed':246,'would_restart':0,'needs_judgment':21,'partial_evidence':1,'preserved_earlier_score_slots':536,'preserved_earlier_boolean_results':268,'controlled_mismatch_native_semantic_miss_preserved':True,'controlled_mismatches_automatically_proceeded':0,'credential_scan_files':checked,'report_identity_preserved':True}
(OUT/'binary/data-validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print(json.dumps(validation))
