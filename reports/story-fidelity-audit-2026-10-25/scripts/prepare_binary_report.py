"""Update the existing report with a prose-only binary audit and its baseline."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys

OUT=Path(__file__).resolve().parents[1]
APP=OUT/'report-app'
current=json.loads((OUT/'binary/results.json').read_text(encoding='utf-8'))
manifest=json.loads((OUT/'binary/manifest.json').read_text(encoding='utf-8'))
baseline=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
old_manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
prior_binary=json.loads((OUT/'binary-v1/results.json').read_text(encoding='utf-8'))
prior_binary_manifest=json.loads((OUT/'binary-v1/manifest.json').read_text(encoding='utf-8'))
controls_document=json.loads((OUT/'binary/controls.json').read_text(encoding='utf-8')) if (OUT/'binary/controls.json').exists() else {'cases':[]}
controls=controls_document['cases']
rows=current['rows'];packages=manifest['packages'];old_rows=baseline['rows']
old_prose=[r for r in old_rows if r['stage']=='final']
native=[r for r in rows if r.get('response',{}).get('answers')]
counts=Counter(r['status'] for r in rows)
def rollup(label,records):
    c=Counter(r['status'] for r in records)
    return {'audit':label,'artifacts':len(records),'evaluated':sum(bool(r.get('response',{}).get('answers')) for r in records),'would_proceed':c['Would proceed'],'would_restart':c['Would restart'],'needs_judgment':c['Needs judgment'],'partial_evidence':c['Partial evidence'],'unavailable':c['Unavailable'],'api_error':c['API error'],'pending':c['Pending']}

summary={
 'stories':len(rows),'api_results':len(native),'pending':counts['Pending'],'proceed':counts['Would proceed'],'restart':counts['Would restart'],'judgment':counts['Needs judgment'],'partial':counts['Partial evidence'],'unavailable':counts['Unavailable'],'errors':counts['API error'],
 'raw_yes':sum(r.get('honors_request') is True for r in rows),'raw_no':sum(r.get('honors_request') is False for r in rows),
 'low_confidence':sum(r.get('confidence') is not None and r['confidence']<.8 for r in rows),
 'median_confidence':statistics.median(r['confidence'] for r in rows if r.get('confidence') is not None) if native else None,
 'original_images':sum(p['reference_count'] for p in packages),'image_packages':sum(p['reference_count']>0 for p in packages),'image_evaluations':sum(r['reference_count'] for r in native),
 'input_tokens':sum(r['response'].get('usage',{}).get('input_tokens',0) for r in native),'cached_tokens':sum(r['response'].get('usage',{}).get('input_tokens_details',{}).get('cached_tokens',0) for r in native),'api_attempts':sum(len(r.get('attempts',[])) for r in rows),
 'source_changes':len(current['manifest'].get('changed_source_files',[])),'baseline_sources_match':sum(r.get('baseline_sources_match') for r in rows),
 'reader_conflicts':sum(bool(r.get('reader_conflict')) for r in rows),
 'control_cases':len(controls),'control_native_no':sum(r['honors_request'] is False for r in controls),'control_automatic_proceeds':sum(r['action']=='proceed' for r in controls),
}
example=next(r for r in rows if r['slug']=='the-kill-she-wouldnt-take')
old_example=next(r for r in prior_binary['rows'] if r['slug']=='the-kill-she-wouldnt-take')
summary.update(example_current_answer=example['honors_request'],example_current_confidence=example['confidence'],example_current_outcome=example['status'],example_previous_answer=old_example['honors_request'],example_previous_confidence=old_example['confidence'])
comparison=[rollup('Earlier 0–4 audit · prose',old_prose),rollup('Earlier broad Yes/No · prose',prior_binary['rows']),rollup('Current [WP] Yes/No · prose',rows)]
histogram=[{'confidence_band':f'{i*10}–{(i+1)*10}%','artifacts':sum(i/10<=r['confidence']<(i+1)/10 or (i==9 and r['confidence']==1) for r in rows if r.get('confidence') is not None)} for i in range(10)]
pilot_reasons={
 'the-kill-she-wouldnt-take':'Low earlier score; later directions require broadcaster viewpoint, sustained sportscaster energy and a binding character image.',
 'the-old-percentage':'Low earlier score; required continuation context was previously unexpanded. The new request includes the full named prior story.',
 'a-darkness-written-under-skin':'Questionable earlier No on the invisible-tattoo/black-light premise. Targeted reading finds the UV reveal and demonstrated magical faculty; the current question asks whether that story promise is played out.',
 'a-perfectly-normal-hobby':'The supplied image is expressly a rejected depiction. The rubric must use it as a problem example rather than require copying it.',
 'before-she-paints-the-ending':'Comparison case with a high earlier score, original image, and later plot/scale directions. It is not a gold-standard accuracy label.',
}
pilot=[{**r,'selection_reason':pilot_reasons[r['slug']]} for r in rows if r['slug'] in pilot_reasons]
notes_path=OUT/'binary/reading-notes.json'
reading_notes=json.loads(notes_path.read_text(encoding='utf-8')) if notes_path.exists() else []
definitions=[
 {'label':'Honors the [WP]','definition':'One native boolean choice: does the outline/story deliver the story the [WP] asks for? Its defining premise and narrative promise must drive the story, as refined by explicit later story directions and relevant image guidance. No means a material contradiction, omission or displacement. Creative elaboration and minor nonmaterial gaps are allowed. Production history, workflow duties, defaults and invented motives are not a checklist.','componentIds':['audit-results','audit-detail','audit-summary','pilot-results']},
 {'label':'Native confidence','definition':'The confidence returned by the single honors_request choice question, preserved separately from P(Yes) and P(No). The floor is 0.80 inclusive. This statistic is not empirically calibrated judgment accuracy.','componentIds':['audit-results','audit-detail','confidence-distribution','audit-summary','pilot-results']},
 {'label':'Workflow action','definition':'Pure production assessor with restarts=0: unresolved evidence, confidence below 0.80, a tied/contradictory distribution, source_ambiguity probability above 0.20, or missing/refused/invalid answers ask the user. Otherwise Yes proceeds; No restarts. After two unsuccessful restarts, No asks the user. Historical stories are never restarted by this audit.','componentIds':['audit-results','audit-detail','audit-summary','stage-coverage','pilot-results']},
 {'label':'Earlier scores','definition':'Unchanged 0–4 estimates from the first audit. Earlier prose and outline results remain available; neither was recomputed using the old rubric. Earlier confidence was the minimum of multiple score confidences. Different question designs do not establish a change in accuracy.','componentIds':['stage-coverage','audit-results','audit-detail','pilot-results']},
]
source={
 'label':'Current repository prose and live Decisions answers to the [WP] story-promise question',
 'tables':['reports/story-fidelity-audit-2026-10-25/binary/results.json','reports/story-fidelity-audit-2026-10-25/binary/manifest.json'],
 'filters':['All 268 current prose files; no outlines re-evaluated','Complete saved prompts and later directions; all 91 saved original images in 82 packages','One named prior-story text included for required continuity; generated art and editorial reviews excluded'],
 'metricDefinitions':definitions,
 'evidenceFlow':[
  {'title':'Capture current sources','detail':f"Provider: local filesystem. Tool: Python pathlib. Root: {manifest['source_root']}/stories. Canonical and historical numbered layouts map to their full saved prose files. Exact file paths, byte sizes, SHA-256 digests, prompt text and continuity text are in binary/manifest.json. No source package edits."},
  {'title':'Live API calls','detail':f"Provider: OpenAI; tool: global Decisions create_decision. Endpoint: {manifest['endpoint']}; model: {manifest['model']}. Rubric: {manifest['rubric_version']}. Exact non-secret requests: tmp/fidelity-audit-wp-focused-2026-10-25/bundles/<slug>/final.json. Native responses and request digests retained in binary/results.json and tmp/.../responses. The user refined the question to focus on the [WP], requiring fresh evaluations. Five pilot requests were reused in the 268-story run. Four concurrent full-batch calls; at most one retry for a transient error; no unchanged-question uncertainty resampling."},
  {'title':'Assess without story actions','detail':'Use binary/fidelity_checkpoint.py assess_response(bundle,response,restarts=0,conflict=missing_original_or_recorded_reader_evidence). Pinned helper digest: '+manifest['helper_sha256']+'. Boolean confidence >=0.80 is required for automatic action; the two-restart production limit remains. This audit never invokes the production run or restart ledger.'},
  {'title':'Input integrity','detail':'The original prompt sent to the API is verbatim; a temporary reference inventory is used solely to adapt historical file formats. Images are actual original bytes at original detail. Explicitly named continuity text is read in full and included. Source changes at completion: '+json.dumps(current['manifest'].get('changed_source_files',[]))},
 ]}
old_source={**source,'label':'Preserved earlier 0–4 audit; not rerun','tables':['reports/story-fidelity-audit-2026-10-25/results.json','reports/story-fidelity-audit-2026-10-25/manifest.json'],'filters':['268 packages; 267 saved outlines/plans and 268 prose files; one absent outline'],'evidenceFlow':[{'title':'Prior observed results','detail':'These are the first audit results, retained unchanged. Full raw answers, source text, digests and usage remain in results.json. The original assessor is preserved at scripts/score_gate_v1.py. One missing image was flagged; linked prior prose for The Old Percentage was not expanded in that audit.'}]}
prior_source={**source,'label':'Preserved broader Yes/No audit before the user centered the [WP]','tables':['reports/story-fidelity-audit-2026-10-25/binary-v1/results.json','reports/story-fidelity-audit-2026-10-25/binary-v1/manifest.json'],'evidenceFlow':[{'title':'Previous boolean question','detail':'The broader honors-request-binary-v1 question evaluated premise, requirements, intended experience and reference fidelity together. These 268 native responses are preserved, including the No at 0.94 and the recorded reader conflict. They are not the current WP-focused answers.'}]}
prior_source['metricDefinitions']=[{'label':'Earlier boolean question','definition':'The broader v1 question combined premise, explicit requirements, intended experience and reference features. Its boolean answer, native confidence and probabilities remain as observed. The 0.80 floor, ambiguity checks and reader-conflict policy applied.'}]
old_source['metricDefinitions']=[{'label':'Earlier score','definition':'Minimum of applicable prompt/experience/reference weighted level indices on a 0–4 scale.'},{'label':'Earlier minimum confidence','definition':'Minimum native score-question confidence; distinct from current single boolean confidence.'},{'label':'Earlier action','definition':'Uncertainty or conflicting evidence asks the user. Otherwise a minimum score below 3 restarts; 3 or more proceeds. Confidence floor 0.80.'}]
control_source={**source,'label':'Two intentionally mismatched temporary copies; original stories unchanged','tables':['reports/story-fidelity-audit-2026-10-25/binary/controls.json'],'evidenceFlow':[{'title':'Negative-control requests','detail':'Tool: scripts/run_wp_controls.py with the same pinned WP-focused rubric. One full deathmatch story was paired with the tattoo writing prompt; one goth/witchcraft story received an added ending stating both parents had always known. These modified request copies exist only under tmp/fidelity-wp-controls-2026-10-25. Expected answer No was recorded outside the model input. Native responses, request digests, confidence and actions are preserved. Controls are excluded from the 268-story counts and usage totals.'}]}
comparison_source={**source,'label':'Three observed audits of the same saved prose','tables':['reports/story-fidelity-audit-2026-10-25/results.json','reports/story-fidelity-audit-2026-10-25/binary-v1/results.json','reports/story-fidelity-audit-2026-10-25/binary/results.json'],'evidenceFlow':[{'title':'Comparable artifact scope','detail':'Count statuses independently for the earlier score audit restricted to final prose, the broader v1 boolean audit, and the current WP-focused v2 audit. Each contains the same 268 prose sources. The original files are unchanged; question designs differ. These counts are not an accuracy or story-quality benchmark.'}]}
summary_source={**source,'tables':source['tables']+['reports/story-fidelity-audit-2026-10-25/binary-v1/results.json','reports/story-fidelity-audit-2026-10-25/binary/controls.json']}
def query(data,method,metadata=None): return {'rows':data,'source':metadata or source,'methods':[{'language':'text','code':method}]}
existing=json.loads((APP/'src/data.json').read_text(encoding='utf-8'))
dataset={
 'id':existing['id'],'surface':'report','title':existing.get('title','Story fidelity audit'),'generatedAt':datetime.now(timezone.utc).isoformat(),'buildStatus':'complete' if '--complete' in sys.argv else 'updating','status':'observed','filters':[], 'report':{'asOf':'2026-10-25'},
 'audit':{'sourceRevision':manifest['git_revision'],'capturedAt':manifest['created_at'],'completedAt':current['manifest'].get('completed_at'),'rubricVersion':manifest['rubric_version'],'summary':summary,'readingNotes':reading_notes,'imagePreviews':json.loads((OUT/'image-previews.json').read_text(encoding='utf-8'))},
 'queries':{
  'artifacts':query(rows,'One row per current prose file; binary/results.json rows verbatim. Keep native booleans, confidence, both probabilities, source ambiguity, reader conflicts, raw answers, usage and full prose. Null is unavailable, never false or zero.'),
  'packages':query(packages,'One row per current package. Preserve the complete prompt, image source records, explicitly named continuity text and source digests from binary/manifest.json. Thumbnails are separate report-only previews indexed by original SHA-256.'),
  'baseline_artifacts':query(old_rows,'Use the unchanged first-audit rows, including outline and prose. Never treat an old score as a current yes/no answer.',old_source),
  'baseline_packages':query(old_manifest['packages'],'Unchanged first-audit prompt and source inventory from manifest.json.',old_source),
  'previous_binary_artifacts':query(prior_binary['rows'],'Preserved broader Yes/No audit rows from binary-v1/results.json; no native answer changes.',prior_source),
  'previous_binary_packages':query(prior_binary_manifest['packages'],'Preserved broader Yes/No prompt and input inventory from binary-v1/manifest.json.',prior_source),
  'summary':query([summary],'Count exclusive current statuses across 268 prose files. Raw yes/no counts use strict native boolean values regardless of action. Median confidence excludes null values; low-confidence count uses <0.80. Sum native input/cached token usage and attempts. The example compares the same slug with binary-v1; control counts use controls.json and are separate from corpus totals. Exact executable aggregation is scripts/prepare_binary_report.py.',summary_source),
  'comparison':query(comparison,'Restrict the 0–4 audit to final prose; independently roll up statuses for that set, binary-v1 rows, and current WP-focused rows. All three contain 268 prose slots. Different questions and the earlier addition of continuity evidence do not establish improved accuracy.',comparison_source),
  'confidence':query(histogram,'Count non-null current native choice confidence into [0,.1),...,[.9,1]. Include 1 in the final bin. No imputation.'),
  'pilot':query(pilot,'Select exactly the five named pilot stories evaluated before the full batch. Reuse their original native results; no second API sampling. Selection reasons describe case coverage, not known ground-truth labels.'),
  'controls':query(controls,'Use both observed negative-control results verbatim. Expected No is separate from the native answer. A semantic mismatch is not relabeled as a pass merely because the confidence gate safely asks the user.',control_source),
 }}
# Keep the separately reviewed live-trial slice when regenerating the frozen corpus report.
for query_name in ('checkpoint_trials', 'checkpoint_trial_summary'):
    if query_name in existing['queries']:
        dataset['queries'][query_name] = existing['queries'][query_name]

(OUT/'report-data.json').write_text(json.dumps(dataset,ensure_ascii=False,indent=2),encoding='utf-8')
(APP/'src/data.json').write_text(json.dumps(dataset,ensure_ascii=False,indent=2),encoding='utf-8')
prior_report=OUT/'REPORT.md';preserved=OUT/'SCORE-REPORT.md'
if not preserved.exists(): preserved.write_bytes(prior_report.read_bytes())
md=['# Story fidelity audit — [WP]-focused Yes/No','',f"Evaluated **{len(native)} of {len(rows)} current prose files** with the [WP]-focused yes/no checkpoint. No outlines were rerun. The earlier score audit and all source packages are preserved.",'','| Outcome | Stories |','| --- | ---: |',f"| Would proceed | {summary['proceed']} |",f"| Would restart at initial attempt | {summary['restart']} |",f"| Needs user judgment | {summary['judgment']} |",f"| Partial evidence | {summary['partial']} |",f"| API errors | {summary['errors']} |",f"| Pending | {summary['pending']} |",'',f"Native answers: {summary['raw_yes']} Yes and {summary['raw_no']} No. {summary['low_confidence']} confidence values are below 0.80; median native confidence is {summary['median_confidence']}. Raw answers are separate from the workflow outcome.",'','## Meaning of honors and policy','','The question is: **Does this outline or story deliver the story the [WP] asks for?** Its defining premise and narrative promise must drive the actual story: the requested situation, characters or relationship, event or turn, and payoff if specified. Explicit later user story directions refine or change that promise, with reference images used in their intended role. No means a material contradiction, omission or displacement of that promise. Creative elaboration and minor nonmaterial gaps are allowed. Do not invent a motive, emotional arc, moral or ending left open by the user. This is not a grade for literary quality, production history, workflow duties, art tasks or default editorial targets.','', 'Use one native boolean choice and preserve its confidence and both probabilities. A reliable Yes with confidence >=0.80 proceeds; a reliable No at that confidence restarts the failed stage. Low confidence, conflicting evidence, unresolved source interpretation, missing inputs, refusals, and invalid answers ask the user. At most two automatic fresh starts per stage; persistent counts and pending questions cannot be cleared by changing stages, filenames, or the rubric.','', 'This retrospective audit uses restarts=0 to describe the initial-attempt action. It does not revise or restart historical stories or write production halt/restart state. Native confidence has not been calibrated as judgment accuracy. Different confidence distributions under the two question designs do not demonstrate improved accuracy.','','## Pilot cases with the revised WP question','','| Story | Native answer | Confidence | Outcome |','| --- | --- | ---: | --- |']
for r in pilot: md.append(f"| {r['title']} | {'—' if r['honors_request'] is None else 'Yes' if r['honors_request'] else 'No'} | {r['confidence']:.2f} | {r['status']} |")
md+=['',*[f"- **{r['title']}:** {r['selection_reason']}" for r in pilot], '', '## Evidence and verification','',f"- {summary['original_images']} saved original images across {summary['image_packages']} packages were supplied as actual image bytes at original detail.",'- A Seat for the Sun still lacks its named original image; its result is partial evidence and cannot pass the gate.','- The Old Percentage now receives the full explicitly named prior story, Nobody Spends Her Name, as continuity evidence.','- The First Year includes art-edit directions in its prompt; this audit evaluates prose fulfillment, not whether the generated sheet was edited.',f"- Source files changed during evaluation: {summary['source_changes']}. Sources matching the earlier snapshot: {summary['baseline_sources_match']}/{len(rows)}.",'- Production helper: 34 local behavioral tests and all 9 independent forward-test groups passed, including persisting preparation-error halts across stages.',f"- Recorded API usage: {summary['input_tokens']:,} input tokens, including {summary['cached_tokens']:,} cached; {summary['api_attempts']} attempts. The five pilot calls are included in this total. No billed monetary amount was inferred.",'','## Review files','','- `binary/results.csv`: current yes/no decisions, native confidence, probabilities, workflow outcomes and old prose scores for context.','- `binary/results.json`: current native responses, assessments, full prose, timing, usage and source identifiers.','- `binary/manifest.json`: current complete prompts, original-image inventory, required continuity text and source hashes.','- `binary/fidelity_checkpoint.py`: pinned helper used for the audit.','- `binary-v1/`: preserved broader Yes/No audit and its reader conflict.','- `results.json`, `results.csv`, `manifest.json`, `SCORE-REPORT.md`: preserved earlier 0–4 audit, including outlines.','- The same interactive report defaults to the current WP-focused prose audit and has selectors for the earlier broader Yes/No audit and the earlier score audit, including outlines.','']
if reading_notes:
    md+=['## Targeted reading notes','']
    for note in reading_notes: md+=[f"### {note['title']}",'',note['text'],'']
md += ['## Controlled mismatches', '', 'Two temporary modified copies test rejection of a different story or a directly contradicted WP fact; original story files were unchanged.', '', '| Control | Expected | Native answer | Confidence | Action |', '| --- | --- | --- | ---: | --- |']
for control in controls:
    md.append(f"| {control['description']} | No | {'Yes' if control['honors_request'] else 'No'} | {control['confidence']:.2f} | {control['action']} |")
md += ['', 'One control returned the expected confident No. The explicit parents-always-knew contradiction returned Yes at 0.44: a semantic miss, caught by the confidence gate as ask_user. Neither control automatically proceeded. This is not proof of corpus-wide accuracy.', '']
# The corpus evidence is a historical snapshot; retain the separately authored trial notes.
md[2] = (f"Evaluated **{summary['api_results']} saved prose files** captured at source revision "
         f"`{manifest['git_revision']}` with the [WP]-focused yes/no checkpoint. This is a frozen snapshot, "
         "not a claim about subsequent edits on main. No outlines were rerun in this corpus audit. "
         "Earlier evaluations remain preserved. Story rewrites are excluded from the checkpoint PR.")
extra_marker = '## Live outline checkpoint observations'
previous_markdown = prior_report.read_text(encoding='utf-8')
if extra_marker in previous_markdown:
    md.extend(['', extra_marker + previous_markdown.split(extra_marker, 1)[1]])
prior_report.write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(summary,indent=2))
