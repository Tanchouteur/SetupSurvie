#!/usr/bin/env python3
"""Explicit resumable video/track inventory; no network, media extraction or AI."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot import durable,zim_video_inventory as inventory
from delivery_paths import locked
from runtime_resources import index_workers,background_worker


def one(source,root,cancel,reserve):
    with locked(root/(source.name+'.lock')):return inventory.build(source,root,cancel=cancel,reserve=reserve)


def run(zim_dir,state_dir,*,cancel=None,workers=None,reserve=15_000_000_000):
    source=Path(zim_dir);root=Path(state_dir)/'zim-videos'
    if source.is_symlink() or not source.is_dir() or root.is_symlink():raise ValueError('Archive/inventory folder refused')
    durable.mkdir(root);files=sorted(p for p in source.glob('*.zim') if not p.is_symlink());workers=index_workers(workers)
    report={'schema':1,'kind':'SetupSurvie archive video inventory','phase':'running','archives':len(files),'completed':0,
        'workers':workers,'started':time.time(),'results':[],'media_extracted':False,'model_loaded':False,'network_requests':0,
        'limitations':['Décodage, audio, langue, fidélité et synchronisation non vérifiés.',
            'Liens et pistes explicitement présents dans le HTML seulement ; lecteurs générés uniquement par JavaScript non interprétés.',
            'La présence d’une piste ne prouve pas sa lisibilité ; aucune transcription ou traduction ne démarre.']}
    def save():durable.write_bytes(root/'progress.json',json.dumps(report,ensure_ascii=False).encode(),private=True)
    with locked(root/'operation.lock'):
        save()
        with ProcessPoolExecutor(max_workers=workers,initializer=background_worker) as pool:
            pending={pool.submit(one,path,root,cancel,reserve):path for path in files}
            for future in as_completed(pending):
                source=pending[future]
                try:result=future.result()
                except inventory.Paused:result={'archive':source.name,'status':'paused'}
                except inventory.ArchiveChanged:result={'archive':source.name,'status':'error','reason':'archive_changed'}
                except Exception as error:result={'archive':source.name,'status':'error','reason':type(error).__name__}
                report['results'].append(result);report['completed']+=1;save()
        report['phase']='paused' if any(r['status']=='paused' for r in report['results']) else 'partial' if any(r['status'] in ('error','partial') or r.get('skipped_html',0) for r in report['results']) else 'completed'
        report['finished']=time.time();save()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zim-dir',type=Path,required=True);parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--cancel',type=Path);parser.add_argument('--workers',type=int,choices=range(1,17));parser.add_argument('--reserve-bytes',type=int,default=15_000_000_000)
    args=parser.parse_args()
    if args.reserve_bytes<0:parser.error('Reserve must be non-negative')
    print(json.dumps(run(args.zim_dir,args.state_dir,cancel=args.cancel,workers=args.workers,reserve=args.reserve_bytes),ensure_ascii=False))
