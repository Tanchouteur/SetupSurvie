#!/usr/bin/env python3
"""Prepare missing ZIM text indexes locally, without any AI or downloads."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot import archive_index,durable
from delivery_paths import locked


def run(zim_dir,state_dir,*,cancel=None,workers=None,force=False,reserve=15_000_000_000):
    if os.name=='nt':
        windowless=Path(sys.executable).with_name('pythonw.exe')
        if windowless.is_file():multiprocessing.set_executable(str(windowless))
    root=Path(state_dir)/'archive-index';durable.mkdir(root)
    workers=workers or min(8,max(1,(os.cpu_count() or 2)-1))
    files=[p for p in sorted(Path(zim_dir).glob('*.zim')) if not p.is_symlink()]
    report={'phase':'running','archives':len(files),'completed':0,'articles':0,'workers':workers,'results':[],'started':time.time()}
    def save():durable.write_bytes(root/'progress.json',json.dumps(report,ensure_ascii=False).encode(),private=True)
    with locked(root/'operation.lock'):
        save()
        with ProcessPoolExecutor(max_workers=workers) as pool:
            pending={pool.submit(archive_index.build_archive,p,root,cancel=cancel,force=force,reserve=reserve):p for p in files}
            for future in as_completed(pending):
                try:result=future.result()
                except archive_index.Paused:result={'archive':pending[future].name,'status':'paused'}
                except Exception as exc:result={'archive':pending[future].name,'status':'error','error':type(exc).__name__}
                report['results'].append(result);report['completed']+=1;report['articles']+=result.get('articles',0);save()
        report['phase']='paused' if any(r['status']=='paused' for r in report['results']) else 'partial' if any(r['status']=='error' for r in report['results']) else 'completed';save()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zim-dir',type=Path,required=True);parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--cancel',type=Path);parser.add_argument('--workers',type=int,choices=range(1,17));parser.add_argument('--include-indexed',action='store_true');parser.add_argument('--reserve-bytes',type=int,default=15_000_000_000)
    args=parser.parse_args()
    if args.reserve_bytes<1_000_000_000:parser.error('Marge disque minimale : 1 Go.')
    result=run(args.zim_dir,args.state_dir,cancel=args.cancel,workers=args.workers,force=args.include_indexed,reserve=args.reserve_bytes)
    print(json.dumps(result,ensure_ascii=False));sys.exit(1 if result['phase']=='partial' else 0)
