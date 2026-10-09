"""Bounded serial C2 pilot. Reuses pinned Ali A1 arm functions without rewriting vision.

Smoke must be human-inspected before pilot. Labels are opened only by separate scoring.
All calls (including retries) share a durable 120-call/$5 budget and UTC 13:00 cutoff.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / 'artifacts/c2-openrouter-20261009'
CUTOFF = datetime(2026, 10, 9, 13, 0, tzinfo=timezone.utc)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=['smoke', 'C', 'B'], required=True)
    args = ap.parse_args()
    from gameqa.config import load_config, config_hash
    from gameqa.pipeline import analyze, build_engines
    from gameqa.vision.judge import Judge
    from gameqa.storage import load_run, run_dir_for, export_report

    key = os.environ.get('OPENROUTER_API_KEY', '')
    if not key:
        raise RuntimeError('OPENROUTER_API_KEY missing')
    def safe(s):
        for name in ('OPENROUTER_API_KEY', 'GEMINI_API_KEY'):
            value = os.environ.get(name)
            if value:
                s = s.replace(value, '[REDACTED]')
        return s
    def save(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(safe(json.dumps(obj, indent=2, ensure_ascii=False)), encoding='utf-8')
    def append(path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as f:
            f.write(safe(json.dumps(obj, ensure_ascii=False))+'\n')
            f.flush()
    def rows(path):
        return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()] if path.exists() else []

    ali_path = OUT / 'Ali_a1_run.py'
    if not ali_path.exists():
        ali_path.write_bytes(subprocess.check_output(['git', 'show', 'cac62c7:scripts/ali_a1_run.py'], cwd=REPO))
    spec = importlib.util.spec_from_file_location('ali_pinned', ali_path)
    ali = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ali)
    ali.REPO = REPO
    cfg = load_config(REPO/'configs/openrouter_gemini_pilot.yaml')
    arm = 'B' if args.mode == 'B' else 'C'
    if arm == 'B':
        cfg['run']['cache_dir'] = 'artifacts/c2-openrouter-20261009/cache-B'
        cfg['run']['artifacts_dir'] = 'artifacts/c2-openrouter-20261009/runs-B'
    cfgid = config_hash(cfg)
    calls_file, stages_file = OUT/'calls.jsonl', OUT/'stages.jsonl'
    calls = rows(calls_file)
    stopped = False
    current = {'arm': arm, 'sample_id': None, 'region_id': 'na'}
    metadata = json.loads((OUT/'model-metadata.json').read_text())
    # Conservative reserve: entire context priced as prompt PLUS max output tokens.
    # Actual response usage.cost is measured independently; key has server-enforced $5 cap.
    reserve = (float(metadata['pricing']['prompt'])*metadata['top_provider']['context_length'] +
               float(metadata['pricing']['completion'])*metadata['top_provider']['max_completion_tokens'])
    original_post = httpx.post
    original_ask, original_region, original_audit = Judge._ask, Judge.judge_region, Judge.audit_scene

    def post(url, *pos, **kw):
        nonlocal stopped
        if str(url) != 'https://openrouter.ai/api/v1/chat/completions':
            return original_post(url, *pos, **kw)
        if stopped or len(calls) >= 120 or datetime.now(timezone.utc) >= CUTOFF:
            raise RuntimeError('C2 budget/cutoff stop; no network request')
        budget = httpx.get('https://openrouter.ai/api/v1/key', headers={'Authorization':'Bearer '+key}, timeout=15)
        if budget.status_code != 200:
            stopped = True
            raise RuntimeError('C2 key-budget lookup failed; stopped before generation')
        data = budget.json()['data']
        spent = sum(c.get('cost_usd') or 0 for c in calls)
        remaining = data.get('limit_remaining')
        if remaining is None or min(float(remaining), 5-spent) < reserve:
            stopped = True
            raise RuntimeError('C2 conservative next-call reserve exceeds remaining $5 budget')
        index = len(calls)+1
        request = copy.deepcopy(kw.get('json', {}))
        capture = OUT/'capture'/f'call-{index:03d}'
        capture.mkdir(parents=True, exist_ok=False)
        for mi, message in enumerate(request.get('messages', [])):
            for ii, item in enumerate(message.get('content', [])):
                if item.get('type') == 'image_url':
                    raw = base64.b64decode(item['image_url']['url'].split(',',1)[1])
                    name = f'message-{mi}-image-{ii}.png'
                    (capture/name).write_bytes(raw)
                    item['image_url']['url'] = {'path':name,'sha256':hashlib.sha256(raw).hexdigest()}
        save(capture/'request.json', request)
        record = {**current,'attempt':index,'cache_hit':False,'model_requested':request['model'],
                  'capture':str(capture.relative_to(OUT)), 'cost_usd':None}
        calls.append(record)
        start = time.perf_counter()
        try:
            response = original_post(url, *pos, **kw)
            response._content = safe(response.text).encode('utf-8')
            body = response.json()
            save(capture/'response.json', body)
            record.update(status_code=response.status_code, model_returned=body.get('model'),
                          provider=body.get('provider'), generation_id=body.get('id'),usage=body.get('usage'))
            usage = body.get('usage') or {}
            record['cost_usd'] = usage.get('cost')
            if response.status_code >= 400 or 'error' in body:
                stopped = True
            elif record['cost_usd'] is None:
                # No more paid requests until unknown prior cost has been resolved.
                stopped = True
            return response
        except Exception as exc:
            stopped = True
            record['error_type'] = type(exc).__name__
            raise RuntimeError(safe(str(exc))) from None
        finally:
            record['seconds'] = round(time.perf_counter()-start,4)
            append(calls_file,record)
            save(OUT/'usage-summary.json',{'attempts':len(calls),'reported_cost_usd':sum(c.get('cost_usd') or 0 for c in calls),
                 'unknown_cost_calls':sum(c.get('cost_usd') is None for c in calls),'reserve_per_call_usd':reserve,
                 'stopped':stopped,'max_attempts':120,'max_spend_usd':5})

    def ask(judge, images, prompt, schema, rules, audit, *stage_args, **stage_kwargs):
        before = len(calls)
        raw, errors, latency = original_ask(judge,images,prompt,schema,rules,audit,
                                          *stage_args, **stage_kwargs)
        append(stages_file,{**current,'stage':'observation' if images else 'rule_judgment',
                'cache_hit':judge.last_cache_hit,'attempts':len(calls)-before,'seconds':latency,'errors':errors})
        return raw, errors, latency
    def region(judge,*a,**kw):
        current['region_id']=a[0].id
        return original_region(judge,*a,**kw)
    def audit(judge,*a,**kw):
        current['region_id']='SCENE'
        return original_audit(judge,*a,**kw)

    httpx.post = post
    Judge._ask, Judge.judge_region, Judge.audit_scene = ask, region, audit
    try:
        inventory=json.loads((REPO/'artifacts/c1-demo-20261009/inventory.json').read_text())['samples']
        by_id={s['sample_id']:s for s in inventory}
        selected=json.loads(subprocess.check_output(['git','show','cf861f1:configs/ali_dev12.json'],cwd=REPO))
        ids=[s['sample_id'] for s in selected['dev12']]
        pred=OUT/arm/'predictions.jsonl'
        existing=rows(pred)
        done={r['sample_id'] for r in existing}
        if args.mode=='smoke':
            todo=['vr_4b921c5d']
            if done:
                raise RuntimeError('Smoke already exists; refusing duplicate inference')
        else:
            todo=[sid for sid in ids if sid not in done]
        extractor, _ = build_engines(cfg) if arm=='C' else (None,None)
        ctx={'cfg':cfg,'analyze':analyze,'extractor':extractor,'build_judge':Judge,'b_input':'aligned'}
        save(OUT/arm/'identity.json',{'code_sha':ali.git_commit(),'cfg':cfg,'config_hash':cfgid,'arm':arm,
             'ali_tooling_commit':'cac62c7693abdf74b8b9e2b6455c82f148ee0493',
             'ali_tooling_sha256':hashlib.sha256(ali_path.read_bytes()).hexdigest(),
             'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'ids':ids,
             'smoke_reused':arm=='C' and args.mode!='smoke' and 'vr_4b921c5d' in done})
        for sid in todo:
            if stopped or datetime.now(timezone.utc)>=CUTOFF or len(calls)>=120:
                break
            current.update(sample_id=sid,region_id='na')
            sample=by_id[sid]
            rec={'sample_id':sid,'reference_path':str(REPO/'artifacts/c1-demo-20261009/bundle'/sid/'reference.png'),
                 'candidate_path':str(REPO/'artifacts/c1-demo-20261009/bundle'/sid/'candidate.png'),'rules':sample['rules']}
            for side in ['reference','candidate']:
                assert hashlib.sha256(Path(rec[side+'_path']).read_bytes()).hexdigest()==sample['images'][side]['sha256']
            start=time.perf_counter(); first=len(calls)
            row={'sample_id':sid,'arm':arm,'media_source':sample['source'],'config_hash':cfgid,
                 'started_at':datetime.now(timezone.utc).isoformat(),'error':None,'smoke':args.mode=='smoke'}
            try:
                row.update(ali.run_C(rec,ctx) if arm=='C' else ali.run_B(rec,ctx))
                if arm=='C':
                    result=load_run(row['run_id'],cfg); rd=run_dir_for(row['run_id'],cfg)
                    export_report(result,rd)
                    row['run_dir']=str(rd)
            except Exception as exc:
                row.update(decision='NEEDS_REVIEW',error=safe(f'{type(exc).__name__}: {exc}'))
                stopped=True
            stage=[x for x in rows(stages_file) if x['arm']==arm and x['sample_id']==sid]
            row.update(seconds=round(time.perf_counter()-start,4),attempts=len(calls)-first,
                 reported_cost_usd=sum(c.get('cost_usd') or 0 for c in calls[first:]),
                 cache={'stages':len(stage),'hits':sum(x['cache_hit'] for x in stage),'status':'fresh' if not any(x['cache_hit'] for x in stage) else 'mixed/cached'})
            append(pred,row)
            print(json.dumps(row,ensure_ascii=False),flush=True)
            if stopped:
                break
    finally:
        httpx.post=original_post
        Judge._ask,Judge.judge_region,Judge.audit_scene=original_ask,original_region,original_audit


if __name__=='__main__':
    main()
