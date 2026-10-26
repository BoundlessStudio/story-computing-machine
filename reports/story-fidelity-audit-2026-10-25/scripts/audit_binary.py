"""Audit current prose with the production yes/no gate, without production actions."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parents[1]
OUT=REPORT/"binary"
TEMP=ROOT/"tmp/fidelity-audit-wp-focused-2026-10-25"

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

GATE=load_module("binary_gate",OUT/"fidelity_checkpoint.py" if (OUT/"fidelity_checkpoint.py").exists() else ROOT/".agents/skills/story-create/scripts/fidelity_checkpoint.py")
CLIENT=load_module("binary_client",Path.home()/".codex/skills/decisions/scripts/decisions.py")

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def file_record(path): return {"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path),"bytes":path.stat().st_size}
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)
    temporary=path.with_suffix(path.suffix+".writing");temporary.write_text(text,encoding="utf-8")
    for attempt in range(10):
        try: temporary.replace(path);return
        except OSError:
            if attempt==9: raise
            time.sleep(.1*(attempt+1))

def summary(rows):
    return {"stories":len(rows),"api_results":sum(bool(r.get('response',{}).get('answers')) for r in rows),"by_status":dict(Counter(r['status'] for r in rows)),"updated_at":utc()}

def export(rows,metadata):
    save(OUT/"results.json",{"manifest":metadata,"rows":rows,"summary":summary(rows)})

def inventory():
    if (OUT/"results.json").exists(): raise ValueError("An inventory already exists; resume it rather than replacing evidence.")
    previous=json.loads((REPORT/"results.json").read_text(encoding="utf-8"))
    baseline={r['slug']:r for r in previous['rows'] if r['stage']=='final'}
    old_packages={p['slug']:p for p in json.loads((REPORT/"manifest.json").read_text(encoding="utf-8"))['packages']}
    packages=[];rows=[]
    for directory in sorted((ROOT/"stories").iterdir()):
        if not directory.is_dir() or directory.name=='_template': continue
        legacy=not (directory/"prompt.md").exists()
        prompt_path=directory/('00-prompt.md' if legacy else 'prompt.md')
        candidate_path=directory/('05-story.md' if legacy else 'story.md')
        prompt=prompt_path.read_text(encoding='utf-8-sig')
        candidate=candidate_path.read_text(encoding='utf-8-sig') if candidate_path.exists() else None
        references=sorted(p for p in (directory/'art/references').rglob('*') if p.is_file())
        missing=[]
        for filename in sorted(set(re.findall(r'`([^`\n]+\.(?:png|jpe?g|webp|gif))`',prompt,re.I))):
            if directory.name=='the-first-year' and filename=='wheel-of-ages.webp': continue
            if not any(p.name==Path(filename).name for p in references) and not (directory/filename).is_file(): missing.append(filename)
        text_refs=GATE.text_reference_paths(prompt,directory)
        meta=json.loads((directory/'story.json').read_text(encoding='utf-8-sig')) if (directory/'story.json').exists() else {}
        title_match=re.search(r'(?m)^title:\s*["\']?(.+?)["\']?\s*$',candidate or '')
        title=meta.get('title') or (title_match.group(1) if title_match else next((line[2:] for line in (candidate or '').splitlines() if line.startswith('# ')),directory.name))
        canon=meta.get('canon',bool(re.search(r'(?mi)^canon:\s*true\s*$',candidate or '')))
        package={'slug':directory.name,'title':title,'canon':canon,'layout':'legacy' if legacy else 'current','prompt_path':prompt_path.relative_to(ROOT).as_posix(),'prompt_text':prompt,'reference_count':len(references),'reference_files':[file_record(p) for p in references],'missing_references':missing,'text_references':[{**file_record(p),'text':p.read_text(encoding='utf-8-sig')} for p in text_refs],'sources':[file_record(p) for p in [prompt_path,*([candidate_path] if candidate_path.exists() else []),*references,*text_refs]]}
        packages.append(package)
        row={'id':directory.name+':final','slug':directory.name,'title':title,'canon':canon,'stage':'final','layout':package['layout'],'candidate_path':candidate_path.relative_to(ROOT).as_posix(),'reference_count':len(references),'missing_references':missing,'honors_request':None,'confidence':None,'probability_yes':None,'probability_no':None,'source_ambiguity_probability':None,'action':None,'status':'Pending','reasons':[], 'candidate_text':candidate}
        old=baseline.get(directory.name,{})
        row.update(previous_score=old.get('score'),previous_confidence=old.get('minimum_confidence'),previous_outcome=old.get('status'))
        if candidate is None:
            row.update(status='Unavailable',reasons=['No saved prose file exists.']);rows.append(row);continue
        snapshot=TEMP/'snapshots'/directory.name;snapshot.mkdir(parents=True,exist_ok=True)
        compatible_prompt=prompt
        if not re.search(r'(?m)^## Supplied reference images[ \t]*$',prompt):
            compatible_prompt+='\n\n## Supplied reference images\n\n'+('\n'.join('- `'+p.relative_to(directory/'art/references').as_posix()+'`' for p in references) if references else '- None')+'\n'
        (snapshot/'prompt.md').write_text(compatible_prompt,encoding='utf-8');(snapshot/'story.md').write_text(candidate,encoding='utf-8')
        for ref in references:
            destination=snapshot/'art/references'/ref.relative_to(directory/'art/references');destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ref,destination)
        bundle=GATE.build_bundle(snapshot,'final')
        bundle['request']['input'][1]['content'][0]['text']=GATE.PROMPT_PREFIX+prompt
        row['candidate_sha256']=sha(candidate_path)
        row['request_sha256']=hashlib.sha256(json.dumps(bundle['request'],sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
        old_package=old_packages.get(directory.name,{})
        row['baseline_sources_match']=row['candidate_sha256']==old.get('candidate_sha256') and prompt==old_package.get('prompt_text') and [r['sha256'] for r in package['reference_files']]==[r['sha256'] for r in old_package.get('reference_files',[])]
        row['added_continuity_context']=bool(text_refs)
        save(TEMP/'bundles'/directory.name/'final.json',bundle);rows.append(row)
    metadata={'audit_id':'story-fidelity-wp-focused-2026-10-25','created_at':utc(),'source_root':str(ROOT),'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'rubric_version':GATE.RUBRIC_VERSION,'helper_sha256':sha(ROOT/'.agents/skills/story-create/scripts/fidelity_checkpoint.py'),'model':CLIENT.MODEL,'endpoint':CLIENT.ENDPOINT,'minimum_confidence':.8,'maximum_restarts':2,'stages_evaluated':['final']}
    save(OUT/'manifest.json',{**metadata,'packages':packages});export(rows,metadata)
    print(json.dumps({'inventory':len(rows),'original_images':sum(p['reference_count'] for p in packages),'continuity_packages':[p['slug'] for p in packages if p['text_references']],'missing_originals':[p['slug'] for p in packages if p['missing_references']]}),flush=True)

def evaluate(row):
    bundle=json.loads((TEMP/'bundles'/row['slug']/'final.json').read_text(encoding='utf-8'))
    response_file=TEMP/'responses'/row['slug']/'final.json'
    if response_file.exists():
        saved=json.loads(response_file.read_text(encoding='utf-8'))
        if saved['request_sha256']!=row['request_sha256']: raise ValueError('Cached response has different evidence.')
        response=saved['response'];attempts=saved['attempts'];evaluated_at=saved['evaluated_at']
    else:
        attempts=[]
        for attempt in range(2):
            begin=time.monotonic()
            try:
                response=CLIENT.create_decision(bundle['request'],timeout=120);attempts.append({'attempt':attempt+1,'success':True,'seconds':round(time.monotonic()-begin,3)});break
            except CLIENT.DecisionsError as exc:
                response=exc.as_dict();attempts.append({'attempt':attempt+1,'success':False,'seconds':round(time.monotonic()-begin,3),**response})
                if attempt==0 and response['error'].get('retryable'): time.sleep(4)
                else: break
        evaluated_at=utc();save(response_file,{'request_sha256':row['request_sha256'],'response':response,'attempts':attempts,'evaluated_at':evaluated_at})
    conflicts=[]
    if row['missing_references']: conflicts.append('Unavailable original image: '+', '.join(row['missing_references']))
    if row.get('reader_conflict'): conflicts.append(row['reader_conflict'])
    conflict='; '.join(conflicts) or None
    assessment=GATE.assess_response(bundle,response,restarts=0,conflict=conflict)
    status='API error' if 'error' in response else ('Partial evidence' if row['missing_references'] else {'proceed':'Would proceed','restart_story':'Would restart','ask_user':'Needs judgment'}[assessment['action']])
    return {**row,**{k:assessment.get(k) for k in ('honors_request','confidence','probability_yes','probability_no','source_ambiguity_probability')},'status':status,'action':assessment['action'],'reasons':assessment['reasons'],'assessment':assessment,'response':response,'attempts':attempts,'evaluated_at':evaluated_at}

def run(workers,slugs):
    d=json.loads((OUT/'results.json').read_text(encoding='utf-8'));rows=d['rows'];metadata=d['manifest']
    wanted=set(slugs or []);pending=[(i,r) for i,r in enumerate(rows) if r['status']=='Pending' and (not wanted or r['slug'] in wanted)]
    print(json.dumps({'starting':len(pending),'workers':workers,'slugs':slugs}),flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(evaluate,r):i for i,r in pending}
        for job in as_completed(jobs):
            i=jobs[job]
            try: rows[i]=job.result()
            except Exception as exc: rows[i].update(status='API error',reasons=[f'Adapter error: {type(exc).__name__}: {exc}'])
            export(rows,metadata)
            print(json.dumps({'last':rows[i]['slug'],'honors':rows[i]['honors_request'],'confidence':rows[i]['confidence'],**summary(rows)}),flush=True)
    packages=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))['packages']
    changed=sorted(set(f['path'] for p in packages for f in p['sources'] if not (ROOT/f['path']).exists() or sha(ROOT/f['path'])!=f['sha256']))
    for row in rows: row['source_changed']=any(f.startswith('stories/'+row['slug']+'/') for f in changed)
    metadata.update(changed_source_files=changed)
    if not any(r['status']=='Pending' for r in rows): metadata['completed_at']=utc()
    export(rows,metadata)
    fields=['id','title','status','honors_request','confidence','probability_yes','probability_no','source_ambiguity_probability','reference_count','action','previous_score','previous_confidence','previous_outcome','baseline_sources_match','added_continuity_context','source_changed','candidate_path','reasons']
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader()
    for row in rows: writer.writerow({**row,'reasons':'; '.join(row['reasons'])})
    (OUT/'results.csv').write_text(stream.getvalue(),encoding='utf-8-sig',newline='')
    print(json.dumps({'finished':utc(),**summary(rows),'changed_sources':changed}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['inventory','run']);parser.add_argument('--workers',type=int,default=4);parser.add_argument('--slugs',nargs='*');args=parser.parse_args()
    inventory() if args.command=='inventory' else run(args.workers,args.slugs)
