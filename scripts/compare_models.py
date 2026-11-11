#!/usr/bin/env python3
"""Same local cases on Windows/Linux, with model, runtime and hardware recorded."""
import argparse
import datetime
import json
from pathlib import Path
import platform
import statistics
import subprocess
import time

import setup
from lab_eval import grade


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work-dir',required=True);p.add_argument('--profiles',nargs='+',default=['rapide','moyenne','approfondie'])
    p.add_argument('--cases',nargs='+',default=['reserve','energy','units','english_source','pump','missing','injection','harness'])
    p.add_argument('--repetitions',type=int,choices=range(1,4),default=1)
    args=p.parse_args();app=setup.Installation(args.work_dir);c=app.load()
    profiles={x['id']:x for x in json.loads((setup.ROOT/'deploy/model-profiles.json').read_text())['profiles']}
    if not set(args.profiles).issubset(profiles):p.error('Profil inconnu.')
    cases=[x for x in json.loads((setup.ROOT/'fixtures/evaluation/cases.json').read_text()) if x['id'] in args.cases]
    system=(setup.ROOT/'fixtures/evaluation/system.fr.txt').read_text()
    folder=app.work/'comparaisons'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');folder.mkdir(parents=True)
    try:gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True,capture_output=True,timeout=15).stdout.strip()
    except (OSError,subprocess.TimeoutExpired):gpu='Non relevé'
    hardware={'platform':platform.platform(),'processor':platform.processor(),'gpu':gpu,'ollama':app.request('http://localhost:11435/api/version')}
    setup.write_json(folder/'hardware.json',hardware)
    available={m['name']:m for m in app.request('http://localhost:11435/api/tags')['models']}
    rows=[]
    try:
        for identifier in args.profiles:
            profile=profiles[identifier];model=profile['model']
            if model not in available:print('Absent, ignoré :',model);continue
            for case in cases:
                for repetition in range(args.repetitions):
                    if (app.work/'inference-paused.json').exists():raise setup.SetupError('Calcul suspendu : résultats terminés conservés.')
                    print('ESSAI',profile['name'],case['id'],repetition+1,flush=True)
                    start=time.monotonic();error=None
                    try:
                        result=app.request('http://localhost:11435/api/generate',{'model':model,'system':system,'prompt':case['prompt'],
                            'think':profile['think'],'stream':False,'keep_alive':'5m',
                            'options':{'num_ctx':8192,'num_predict':4096,'temperature':0,'seed':42}},timeout=900)
                    except (OSError,ValueError) as exc:error=type(exc).__name__;result={'error':error}
                    result.pop('context',None);result.pop('thinking',None)
                    row={'profile':identifier,'model':model,'digest':available[model]['digest'],'think':profile['think'],'case':case['id'],
                         'repetition':repetition,'seconds':round(time.monotonic()-start,2),'result':result,'grade':grade(case,result),
                         'placement':app.request('http://localhost:11435/api/ps')}
                    rows.append(row);setup.write_json(folder/'results.json',rows)
                    print('RÉSULTAT',row['grade']['passed'],row['seconds'],'s',flush=True)
    finally:
        try:loaded={m['name'] for m in app.request('http://localhost:11435/api/ps')['models']}
        except (OSError,ValueError):loaded=set()
        for model in loaded & {r['model'] for r in rows}:
            try:app.request('http://localhost:11435/api/generate',{'model':model,'keep_alive':0},timeout=30)
            except OSError:pass
    print('Résultats et caractéristiques du PC :',folder)


if __name__=='__main__':
    try:main()
    except (setup.SetupError,OSError,ValueError) as exc:raise SystemExit(str(exc))
