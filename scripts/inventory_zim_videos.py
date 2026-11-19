#!/usr/bin/env python3
"""Explicit resumable video/track inventory; no network, media extraction or AI."""
import argparse
import hashlib
from concurrent.futures import FIRST_COMPLETED,ProcessPoolExecutor,as_completed,wait
from functools import partial
import json
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pilot import durable,zim_video_inventory as inventory
from delivery_paths import locked
from runtime_resources import index_workers,background_worker

LARGE_ARCHIVE=4*1024**3
RANGE_SIZE=250_000
CHECKPOINT=512


def one(source,root,cancel,reserve,scan=None):
    key=hashlib.sha256(source.name.encode()).hexdigest()[:24]
    with locked(root/(key+'.lock')):
        return inventory.build(source,root,cancel=cancel,reserve=reserve,scan=scan)


def scan_range(source,building,revision,start,stop,cursor,cancel,reserve):
    from libzim.reader import Archive

    def check():
        if cancel and Path(cancel).exists():
            raise inventory.Paused()
        if shutil.disk_usage(building.parent).free<reserve:
            raise OSError('Inventory storage reserve unavailable')

    check()
    archive=Archive(source)
    if inventory.fingerprint(source,archive)!=revision:
        raise inventory.ArchiveChanged()
    entry_by_id=inventory.entry_reader(archive)
    writes=[]
    subtitle_written=False

    def write(sql,row):
        writes.append((sql,(row,)))

    def write_many(sql,rows):
        nonlocal subtitle_written
        subtitle_written=True
        writes.append((sql,rows))

    with inventory.connect(building) as db:
        while cursor<stop:
            check()
            next_cursor=cursor
            subtitle_written=False
            for index in range(cursor,min(stop,cursor+CHECKPOINT)):
                inventory.scan_entry(entry_by_id(index),write,write_many)
                next_cursor=index+1
                # Subtitle cues can be large. Flush immediately after a subtitle.
                if len(writes)>=CHECKPOINT or subtitle_written:
                    break
            with db:
                db.execute('UPDATE scan_ranges SET cursor=? WHERE start=?',(next_cursor,start))
                for sql,rows in writes:
                    db.executemany(sql,rows)
                prefix=db.execute('SELECT min(cursor) FROM scan_ranges WHERE cursor<stop').fetchone()[0]
                if prefix is not None:
                    db.execute("UPDATE metadata SET value=? WHERE key='cursor' AND CAST(value AS INTEGER)<?",(str(prefix),prefix))
            writes.clear()
            cursor=next_cursor
    if inventory.fingerprint(source,archive)!=revision:
        raise inventory.ArchiveChanged()


def scan_parallel(pool,source,cancel,reserve,report,save,db,building,revision,cursor,total):
    if cursor>=total:
        return
    db.execute('CREATE TABLE IF NOT EXISTS scan_ranges(start INTEGER PRIMARY KEY,stop INTEGER NOT NULL,cursor INTEGER NOT NULL)')
    if not db.execute('SELECT 1 FROM scan_ranges LIMIT 1').fetchone():
        db.executemany('INSERT INTO scan_ranges VALUES(?,?,?)',
                       ((start,min(start+RANGE_SIZE,total),start) for start in range(cursor,total,RANGE_SIZE)))
    # A previous version may have advanced the original contiguous cursor.
    db.execute('UPDATE scan_ranges SET cursor=min(stop,?) WHERE cursor<?',(cursor,cursor))
    db.commit()
    pending=set()
    errors=[]

    def progress():
        remaining=db.execute('SELECT sum(stop-cursor) FROM scan_ranges').fetchone()[0] or 0
        report['active_archive']={'archive':source.name,'entries_examined':total-remaining,'entries':total}
        save()

    try:
        progress()
        for start,stop,saved in db.execute('SELECT start,stop,cursor FROM scan_ranges WHERE cursor<stop ORDER BY start').fetchall():
            pending.add(pool.submit(scan_range,source,building,revision,start,stop,saved,cancel,reserve))
        while pending:
            done,pending=wait(pending,timeout=5,return_when=FIRST_COMPLETED)
            for future in done:
                try:
                    future.result()
                except Exception as error:
                    errors.append(error)
            if errors:
                break
            progress()
        if errors:
            raise next((error for error in errors if not isinstance(error,inventory.Paused)),errors[0])
    finally:
        # Keep the archive lease until all writers have closed the database.
        for future in pending:
            future.cancel()
        if pending:
            wait(pending)
        progress()


def run(zim_dir,state_dir,*,cancel=None,workers=None,reserve=15_000_000_000,job_id=None):
    source=Path(zim_dir);root=Path(state_dir)/'zim-videos'
    if source.is_symlink() or not source.is_dir() or root.is_symlink():raise ValueError('Archive/inventory folder refused')
    durable.mkdir(root);candidates=sorted(source.glob('*.zim'));files=[p for p in candidates if not p.is_symlink() and p.is_file()];workers=index_workers(workers)
    report={'schema':1,'job_id':job_id,'kind':'SetupSurvie archive video inventory','phase':'running','archives':len(candidates),'completed':0,
        'unexamined':[{'archive':p.name,'reason':'link_or_not_file'} for p in candidates if p not in files],
        'workers':workers,'started':time.time(),'results':[],'media_extracted':False,'model_loaded':False,'network_requests':0,
        'limitations':['Décodage, audio, langue, fidélité et synchronisation non vérifiés.',
            'Liens et pistes explicitement présents dans le HTML seulement ; lecteurs générés uniquement par JavaScript non interprétés.',
            'La présence d’une piste ne prouve pas sa lisibilité ; aucune transcription ou traduction ne démarre.']}
    def save():durable.write_bytes(root/'progress.json',json.dumps(report,ensure_ascii=False).encode(),private=True)

    def record(result,source):
        try:row=result()
        except inventory.Paused:row={'archive':source.name,'status':'paused'}
        except inventory.ArchiveChanged:row={'archive':source.name,'status':'error','reason':'archive_changed'}
        except Exception as error:row={'archive':source.name,'status':'error','reason':type(error).__name__}
        report['results'].append(row)
        if row['status'] in inventory.EXAMINED_STATUSES:
            report['completed']+=1
            report.pop('active_archive',None)
        save()

    with locked(root/'operation.lock'):
        save()
        large=[];regular=[]
        for path in files:
            try:
                oversized=path.stat().st_size>=LARGE_ARCHIVE
            except OSError:
                oversized=False  # Let the normal worker report the source error.
            (large if oversized else regular).append(path)
        with ProcessPoolExecutor(max_workers=workers,initializer=background_worker) as pool:
            pending={pool.submit(one,path,root,cancel,reserve):path for path in regular}
            for future in as_completed(pending):
                record(future.result,pending[future])
        if large:
            # Concurrent readers of one compressed file share its SSD bandwidth.
            with ProcessPoolExecutor(max_workers=min(workers,4),initializer=background_worker) as pool:
                for path in large:
                    report.pop('active_archive',None)
                    scan=partial(scan_parallel,pool,path,cancel,reserve,report,save)
                    record(partial(one,path,root,cancel,reserve,scan),path)
        report['phase']='paused' if any(r['status']=='paused' for r in report['results']) else 'partial' if report['unexamined'] or any(r['status'] in ('error','partial') or r.get('issues_count',0) for r in report['results']) else 'completed'
        report['finished']=time.time();save()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zim-dir',type=Path,required=True);parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--cancel',type=Path);parser.add_argument('--workers',type=int,choices=range(1,17));parser.add_argument('--reserve-bytes',type=int,default=15_000_000_000)
    parser.add_argument('--job-id')
    args=parser.parse_args()
    if args.reserve_bytes<0:parser.error('Reserve must be non-negative')
    print(json.dumps(run(args.zim_dir,args.state_dir,cancel=args.cancel,workers=args.workers,reserve=args.reserve_bytes,job_id=args.job_id),ensure_ascii=False))
