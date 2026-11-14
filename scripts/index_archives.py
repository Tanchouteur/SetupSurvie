#!/usr/bin/env python3
"""Prepare missing ZIM text indexes locally, without any AI or downloads."""
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot import archive_index,durable
from delivery_paths import locked
from runtime_resources import index_workers,background_worker
import index_reader_probe
import index_locks
from setup import SetupError


def build_one(source,root,**options):
    with locked(index_locks.worker(root,source)):
        return archive_index.build_archive(source,root,**options)


def error_record(source,error):
    import errno
    reason='storage_reserve' if isinstance(error,archive_index.StorageReserve) else 'source_changed' if isinstance(error,archive_index.ArchiveChanged) else 'source_missing' if isinstance(error,FileNotFoundError) else 'permission_denied' if isinstance(error,PermissionError) else 'storage_full' if isinstance(error,OSError) and error.errno in (errno.ENOSPC,getattr(errno,'EDQUOT',-1)) else 'reader_import' if isinstance(error,(ImportError,ModuleNotFoundError)) else 'sqlite_error' if isinstance(error,archive_index.sqlite3.Error) else 'index_busy' if isinstance(error,SetupError) else 'archive_error'
    return {'archive':source.name,'status':'error','error':type(error).__name__,'reason':reason}


def run(zim_dir,state_dir,*,cancel=None,workers=None,force=False,reserve=15_000_000_000,selection=None,job_id=None):
    # Keep CPython's own executable selection. On Windows its venv-aware spawn
    # bypasses the redirector; substituting the venv's pythonw.exe bypasses that
    # fix and leaves ProcessPoolExecutor waiting for children which never start.
    root=Path(state_dir)/'archive-index';durable.mkdir(root)
    workers=index_workers(workers)
    files=[p for p in sorted(Path(zim_dir).glob('*.zim')) if not p.is_symlink()]
    if selection is not None:
        allowed=set(selection)
        if any(Path(name).name!=name or not name.endswith('.zim') for name in allowed):raise ValueError('Sélection d’archives non valide.')
        files=[p for p in files if p.name in allowed]
    manifest=archive_index.manifest(root)
    report={'job_id':job_id,'phase':'running','archives':len(files),'completed':0,'articles':0,'workers':workers,'results':[],'started':time.time()}
    def save():durable.write_bytes(root/'progress.json',json.dumps(report,ensure_ascii=False).encode(),private=True)
    with locked(root/'operation.lock'):
        save()
        report['reader_probe']=index_reader_probe.probe()
        if not report['reader_probe']['ok']:
            report['phase']='partial';report['error_summary']={report['reader_probe']['error']:1};save();return report
        try:index_locks.prepare(root,files)
        except SetupError:
            report['phase']='partial';report['error_summary']={'index_busy':1};save();return report
        with ProcessPoolExecutor(max_workers=workers,initializer=background_worker) as pool:
            pending={pool.submit(build_one,p,root,cancel=cancel,force=force,reserve=reserve):p for p in files}
            for future in as_completed(pending):
                try:result=future.result()
                except archive_index.Paused:result={'archive':pending[future].name,'status':'paused'}
                except Exception as exc:result=error_record(pending[future],exc)
                report['results'].append(result);report['completed']+=1;report['articles']+=result.get('articles',0)
                if result['status'] in ('ready','kiwix_index'):
                    manifest[result['archive']]=result
                    durable.write_bytes(root/'manifest.json',json.dumps({'schema':1,'archives':manifest},ensure_ascii=False).encode(),private=True)
                save()
        report['phase']='paused' if any(r['status']=='paused' for r in report['results']) else 'partial' if any(r['status']=='error' for r in report['results']) else 'completed'
        report['error_summary']={}
        for result in report['results']:
            if result.get('reason'):report['error_summary'][result['reason']]=report['error_summary'].get(result['reason'],0)+1
        save()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zim-dir',type=Path,required=True);parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--job-id')
    parser.add_argument('--selection',type=Path)
    parser.add_argument('--cancel',type=Path);parser.add_argument('--workers',type=int,choices=range(1,17));parser.add_argument('--include-indexed',action='store_true');parser.add_argument('--reserve-bytes',type=int,default=15_000_000_000)
    args=parser.parse_args()
    if args.reserve_bytes<1_000_000_000:parser.error('Marge disque minimale : 1 Go.')
    selection=json.loads(args.selection.read_text(encoding='utf-8')) if args.selection else None
    result=run(args.zim_dir,args.state_dir,cancel=args.cancel,workers=args.workers,force=args.include_indexed,reserve=args.reserve_bytes,selection=selection,job_id=args.job_id)
    print(json.dumps(result,ensure_ascii=False));sys.exit(1 if result['phase']=='partial' else 0)
