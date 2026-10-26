"""Two deliberately mismatched copies test that the WP gate can reject failures."""
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('wp_audit',OUT/'scripts/audit_binary.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
TEMP=ROOT/'tmp/fidelity-wp-controls-2026-10-25'
TEMP.mkdir(parents=True,exist_ok=True)

def original(slug):
    return json.loads((audit.TEMP/'bundles'/slug/'final.json').read_text(encoding='utf-8'))

cases=[]
swapped=original('a-darkness-written-under-skin')
other=original('the-kill-she-wouldnt-take')['request']['input'][1]['content'][-1]['text']
swapped['request']['input'][1]['content'][-1]['text']=other
cases.append(('wrong-story','Full deathmatch prose evaluated against the invisible-tattoo [WP]',swapped))
contradiction=original('a-perfectly-normal-hobby')
contradiction['request']['input'][1]['content'][-1]['text']+='\n\nThat night his mother told him she had known about his witchcraft from the first lesson. His father had watched every ritual with her; both parents had always been fully aware and had only pretended to be oblivious.\n'
cases.append(('parents-always-knew','Original goth/witchcraft prose plus an explicit ending that contradicts the completely-oblivious-parents requirement',contradiction))

def run(case):
    name,description,bundle=case
    request_file=TEMP/(name+'-request.json');response_file=TEMP/(name+'-response.json')
    audit.save(request_file,bundle['request'])
    request_sha=hashlib.sha256(json.dumps(bundle['request'],sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
    if response_file.exists():
        saved=json.loads(response_file.read_text(encoding='utf-8'))
        assert saved['request_sha256']==request_sha
        response=saved['response']
    else:
        response=audit.CLIENT.create_decision(bundle['request'],timeout=120)
        audit.save(response_file,{'request_sha256':request_sha,'response':response})
    result=audit.GATE.assess_response(bundle,response,0)
    return {'id':name,'description':description,'expected_honors':False,'honors_request':result.get('honors_request'),'confidence':result.get('confidence'),'probability_yes':result.get('probability_yes'),'action':result['action'],'passed':result.get('honors_request') is False and result['action']=='restart_story','assessment':result,'response':response,'request_sha256':request_sha,'request_file':str(request_file)}

with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(run,cases))
audit.save(OUT/'binary/controls.json',{'rubric_version':audit.GATE.RUBRIC_VERSION,'cases':results,'original_story_files_modified':False})
print(json.dumps([{k:v for k,v in r.items() if k not in ('response','assessment')} for r in results],indent=2))
