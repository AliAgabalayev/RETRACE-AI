"""Score saved C2 predictions only; frozen labels never enter inference. No API calls."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO/'artifacts/c2-openrouter-20261009'


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()] if path.exists() else []


def metrics(rows, labels):
    cm={truth:{d:0 for d in ('PASS','FAIL','NEEDS_REVIEW')} for truth in ('D1','A1')}
    for row in rows:
        cm[labels[row['sample_id']]][row['decision']]+=1
    n=len(rows)
    return {'completed':n,'counts':dict(Counter(r['decision'] for r in rows)),
            'decision_coverage':sum(r['decision']!='NEEDS_REVIEW' for r in rows)/n if n else None,
            'bug_count':sum(cm['D1'].values()),'bug_FAIL':cm['D1']['FAIL'],
            'bug_REVIEW':cm['D1']['NEEDS_REVIEW'],'bug_false_PASS':cm['D1']['PASS'],
            'clean_count':sum(cm['A1'].values()),'clean_PASS':cm['A1']['PASS'],
            'clean_REVIEW':cm['A1']['NEEDS_REVIEW'],'clean_false_FAIL':cm['A1']['FAIL'],'confusion':cm}


def main():
    labels={r['sample_id']:r['rule_allowed_or_forbidden (A1/D1)']
            for r in csv.DictReader((REPO/'docs/ali/labels_ali.csv').open(encoding='utf-8'))}
    sensitivity=dict(labels); sensitivity['vr_330651ed']='A1'
    ids=[r['sample_id'] for r in json.loads((REPO/'artifacts/c1-demo-20261009/inventory.json').read_text())['samples']]
    scores={}
    for arm in ('C','B'):
        rows=read(ROOT/arm/'predictions.jsonl')
        seen=[r['sample_id'] for r in rows]
        assert len(seen)==len(set(seen)), 'Duplicate predictions refused'
        review=[r for r in rows if r['decision']=='NEEDS_REVIEW']
        causes={
            'unreliable_alignment':[r['sample_id'] for r in review if r.get('alignment_status') in ('unreliable','failed',None)],
            'global_change_collapse':[r['sample_id'] for r in review if r.get('global_collapse')],
            'actual_region_cap':[r['sample_id'] for r in review if r.get('max_region_cap_hit')],
            'uncertain_region_judgment':[r['sample_id'] for r in review if any(j['verdict']=='uncertain' for j in r.get('regions',[]))],
            'scene_uncertainty_or_invalid':[r['sample_id'] for r in review if r.get('audit') and (r['audit']['verdict']=='uncertain' or not r['audit']['validated'])],
            'scene_extra_changes':[r['sample_id'] for r in review if r.get('extra_changes_reported')],
            'provider_error':[r['sample_id'] for r in review if r.get('error') or any('provider error' in e for e in r.get('errors',[]))]}
        scores[arm]={'frozen':metrics(rows,labels),'subtitle_clean_sensitivity':metrics(rows,sensitivity),
             'missing_ids':[sid for sid in ids if sid not in seen],
             'per_source':{source:metrics([r for r in rows if r['media_source']==source],labels)
                           for source in sorted({r['media_source'] for r in rows})},
             'review_causes_nonexclusive':causes,'error_rows':[r['sample_id'] for r in rows if r.get('error') or r.get('errors')],
             'median_seconds':median([r['seconds'] for r in rows]) if rows else None,
             'attempts':sum(r['attempts'] for r in rows),'reported_cost_usd':sum(r['reported_cost_usd'] for r in rows),
             'cache_hits':sum(r['cache']['hits'] for r in rows),'stages':sum(r['cache']['stages'] for r in rows),
             'smoke_reused_ids':[r['sample_id'] for r in rows if r.get('smoke')]}
    calls=read(ROOT/'calls.jsonl'); stages=read(ROOT/'stages.jsonl')
    usage={'attempts':len(calls),'reported_cost_usd':sum(c.get('cost_usd') or 0 for c in calls),
           'unknown_cost_calls':[c['attempt'] for c in calls if c.get('cost_usd') is None],
           'retry_attempts':sum(max(0,s['attempts']-1) for s in stages),
           'prompt_tokens':sum((c.get('usage') or {}).get('prompt_tokens',0) for c in calls),
           'completion_tokens':sum((c.get('usage') or {}).get('completion_tokens',0) for c in calls),
           'reasoning_tokens':sum(((c.get('usage') or {}).get('completion_tokens_details') or {}).get('reasoning_tokens',0) for c in calls),
           'upstream_cached_prompt_tokens':sum(((c.get('usage') or {}).get('prompt_tokens_details') or {}).get('cached_tokens',0) for c in calls),
           'providers':dict(Counter(c.get('provider') for c in calls)),
           'returned_models':dict(Counter(c.get('model_returned') for c in calls)),
           'http_status':dict(Counter(c.get('status_code') for c in calls))}
    result={'arms':scores,'usage':usage,'warning':'Development diagnostic; incomplete rows/missing IDs explicit; observation correctness requires human review.'}
    (ROOT/'score.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
