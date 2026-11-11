#!/usr/bin/env python3
"""Summarize reproducible cases; preserve strict scores and distinguish formatting."""
import collections
import json
from pathlib import Path
import statistics
import sys


def summarize(root):
    reports=[]
    for folder in sorted(root.iterdir()):
        if not (folder/'protocol.json').exists() or not (folder/'summary.json').exists():continue
        protocol=json.loads((folder/'protocol.json').read_text())
        cases={c['id']:c for c in protocol['cases']}
        groups=collections.defaultdict(list)
        for row in json.loads((folder/'summary.json').read_text()):groups[row['model'],str(row['mode']),row['context']].append(row)
        for (model,mode,context),rows in groups.items():
            failures=[];normalized=0
            for row in rows:
                parsed=row['grade'].get('parsed');expected=cases[row['case']]['expected']
                adjusted=dict(parsed) if isinstance(parsed,dict) else None
                if adjusted and isinstance(adjusted.get('source'),str):adjusted['source']=adjusted['source'].strip('[] ')
                if adjusted==expected:normalized+=1
                if not row['grade']['passed']:
                    failures.append({'case':row['case'],'repetition':row['repetition'],'reason':row['grade']['reason'],
                                     'parsed':parsed,'expected':expected,'brackets_only':adjusted==expected})
            reports.append({'run':folder.name,'model':model,'mode':mode,'context':context,'trials':len(rows),
                'strict_pass':sum(r['grade']['passed'] for r in rows),'pass_ignoring_source_brackets':normalized,
                'median_seconds':round(statistics.median(r['elapsed_seconds'] for r in rows),2),
                'max_seconds':round(max(r['elapsed_seconds'] for r in rows),2),
                'truncated_inputs':sum(bool(r.get('input_truncation_warnings')) for r in rows),'failures':failures})
    return reports


if __name__=='__main__':
    root=Path(sys.argv[1]);data=summarize(root)
    (root/'comparison-report.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    for row in data:print(row['run'],row['model'],row['mode'],row['context'],f"{row['strict_pass']}/{row['trials']}",f"crochets tolérés {row['pass_ignoring_source_brackets']}/{row['trials']}",str(row['median_seconds'])+'s')
