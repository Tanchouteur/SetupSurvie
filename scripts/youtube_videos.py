#!/usr/bin/env python3
"""Télécharger une liste de vidéos YouTube dans la bibliothèque (préparation avec Internet).

Le fichier texte contient une adresse YouTube par ligne. Les lignes vides et
celles qui commencent par # sont ignorées ; « [thème] » range les vidéos qui
suivent dans un sous-dossier. Chaque vidéo est téléchargée dans un dossier de
travail, puis déplacée terminée dans library/video/youtube/<thème ou chaîne>/
avec son .info.json et ses sous-titres français/anglais disponibles.

  python scripts/youtube_videos.py prepare             # facultatif : déjà fait par l’installation
  python scripts/youtube_videos.py check liste.txt     # relit la liste, sans réseau
  python scripts/youtube_videos.py download liste.txt  # télécharge et range

Aucun cookie, compte, proxy ni contournement de blocage. Relancer la même
liste reprend les vidéos inachevées et passe celles déjà présentes. Le pilote
répertorie ensuite les nouvelles vidéos tout seul (0.40.0).
"""
import argparse
import errno
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import setup
from delivery_paths import locked
from pilot import collection_sort, durable
from pilot.youtube_list import REASONS,folder_name,parse_list
from pilot.video_inventory import INCOMPLETE,SUBTITLE_EXTENSIONS,VIDEO_EXTENSIONS
import youtube_tools

SUBTITLE_LANGUAGES='fr,fr-FR,fr-CA,en,en-US,en-GB'
VIDEO_TIMEOUT=4*3600
PATTERNS=[
    ('private',r'private video'),('members_only',r'members[- ]only|join this channel'),
    ('age_restricted',r'sign in to confirm your age|age[- ]restricted|inappropriate for some users'),
    ('bot_check',r'sign in to confirm you.?re not a bot|confirm you are not a robot'),
    ('region_blocked',r'available in your country|geo[- ]?restrict|blocked it in your country'),
    ('live',r'live event will begin|is live|premieres in'),
    ('too_large',r'larger than max-filesize|file is larger than'),
    ('no_format',r'requested format is not available|no video formats found'),
    ('rate_limited',r'http error 429|too many requests'),
    ('provider_forbidden',r'http error 403|403 forbidden'),
    ('extractor',r'signature extraction failed|failed to extract|unable to extract|challenge solving failed'),
    ('unavailable',r'video unavailable|video is unavailable|video is not available|has been removed|account associated with this video has been terminated|this video does not exist'),
    ('disk_space',r'no space left on device|not enough space'),
    ('network',r'unable to download webpage|connection (?:reset|refused|aborted)|timed? ?out|temporary failure in name resolution|getaddrinfo failed|network is unreachable'),
]


SUBTITLE_FAILURE=re.compile(r'unable to download video subtitles|unable to download subtitles|error.*writing (?:the )?subtitle',re.I)


def existing_videos(library):
    """YouTube identifiers already present as finished files (« Titre [id].ext »)."""
    found={}
    if not library.is_dir():return found
    for directory,folders,files in os.walk(library,followlinks=False):
        for name in files:
            path=Path(directory)/name
            if path.suffix.lower() not in VIDEO_EXTENSIONS or INCOMPLETE.search(name) or path.is_symlink():continue
            for identifier in re.findall(r'\[([A-Za-z0-9_-]{11})\]',name):found.setdefault(identifier,path)
    return found


def classify(output,returncode):
    text=output.lower()
    for reason,pattern in PATTERNS:
        if re.search(pattern,text):return reason
    return 'tool_failed' if returncode else 'output_missing'


def free_bytes(path):
    path=Path(path)
    while not path.exists():path=path.parent
    return shutil.disk_usage(path).free


def downloader(data,override=None,*,log=print,run=subprocess.run):
    """yt-dlp of the prepared environment, repaired or installed when needed."""
    if override:return [sys.executable,str(override)] if str(override).endswith('.py') else [str(override)]
    youtube_tools.ensure(data,log=log,run=run)
    if not youtube_tools.installed_version(data,run=run):
        raise setup.SetupError('yt-dlp n’a pas pu être préparé. Une connexion Internet est nécessaire la première fois ; relancez la même commande.')
    return [str(youtube_tools.python(data)),'-m','yt_dlp']


def upgrade(data,*,run=subprocess.run):
    """Newest yt-dlp in the prepared environment, when YouTube broke the pinned one."""
    youtube_tools.ensure(data,run=run)
    hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    run([str(youtube_tools.python(data)),'-m','pip','install','--upgrade','--disable-pip-version-check','yt-dlp[default]'],check=True,timeout=900,**hidden)
    return youtube_tools.installed_version(data,run=run)


def command(base,entry,staging,*,max_height,max_bytes,ffmpeg,js_runtime='deno',subtitles=True):
    # H.264 first: AV1 or VP9 may not play on older phones and computers.
    if ffmpeg:fmt=f'bv*[height<={max_height}][vcodec^=avc1]+ba[ext=m4a]/bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/bv*[height<={max_height}]+ba/b[height<={max_height}]'
    else:fmt=f'b[height<={max_height}][ext=mp4]/b[height<={max_height}]'
    args=[*base,'--ignore-config','--no-playlist','--newline','--no-colors','--no-mtime',
          '-f',fmt,'--max-filesize',str(max_bytes),'--write-info-json',
          *(['--write-subs','--write-auto-subs','--sub-langs',SUBTITLE_LANGUAGES,'--sub-format','vtt/srt/best','--sleep-subtitles','3'] if subtitles else []),
          '--windows-filenames','--trim-filenames','160',
          '--continue','--no-overwrites','--retries','5','--fragment-retries','5','--socket-timeout','30',
          '-P',str(staging),'-o','%(title).120B [%(id)s].%(ext)s']
    if js_runtime in ('node','bun'):args+=['--js-runtimes',js_runtime]
    if ffmpeg:args+=['--merge-output-format','mp4']+(['--ffmpeg-location',str(ffmpeg)] if ffmpeg is not True else [])
    return args+['--',entry['url']]


def finished_files(staging,identifier):
    media=[p for p in staging.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS and not INCOMPLETE.search(p.name) and '['+identifier+']' in p.name]
    if len(media)!=1:return None,[]
    stem=media[0].name[:-len(media[0].suffix)]
    sidecars=[p for p in staging.iterdir() if p.is_file() and p!=media[0] and p.name.startswith(stem+'.') and not INCOMPLETE.search(p.name)
              and (p.name.endswith('.info.json') or p.suffix.lower() in SUBTITLE_EXTENSIONS)]
    return media[0],sidecars


def free_stem(folder,stem,suffixes):
    """One free name for the media and all its sidecars, so they stay associated."""
    for number in range(1,1000):
        candidate=stem if number==1 else f'{stem} ({number})'
        if not any((folder/(candidate+suffix)).exists() for suffix in suffixes):return candidate
    raise setup.SetupError('Trop de fichiers du même nom dans '+str(folder))


def publish(media,sidecars,library,entry,*,sorting=None):
    """Move finished files into the library: sidecars first, media last.

    The pilot ignores a video until its media file appears, so it never sees
    a video without its title and subtitles."""
    info={}
    for path in sidecars:
        if path.name.endswith('.info.json'):
            try:info=json.loads(path.read_text(encoding='utf-8'))
            except (OSError,ValueError):info={}
    folder=library/'youtube'/(entry['theme'] or folder_name(info.get('channel') or info.get('uploader'),'Sans chaîne'))
    if sorting is not None:
        key=collection_sort.video({'source':{'channel':info.get('channel')},'collection':folder.relative_to(library).as_posix()})
        if not sorting.permits(key,'all'):
            return None,[],info
    durable.mkdir(folder)
    original=media.name[:-len(media.suffix)]
    suffixes=[media.suffix,*[path.name[len(original):] for path in sidecars]]
    stem=free_stem(folder,original,suffixes)
    moved=[]
    for path in sidecars:
        destination=folder/(stem+path.name[len(original):])
        durable.publish(path,destination);moved.append(destination)
    target=folder/(stem+media.suffix)
    durable.publish(media,target)
    return target,moved,info


def execute(args,*,cancel=None,run=subprocess.run,popen=subprocess.Popen,on_progress=None):
    """Run yt-dlp; with a cancel file, stop it cooperatively (partial files kept).

    Returns (returncode, output, paused)."""
    hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    options=dict(stdin=subprocess.DEVNULL,env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'},**hidden)
    if cancel is None:
        result=run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=VIDEO_TIMEOUT,**options)
        return result.returncode,(result.stdout or '')+'\n'+(result.stderr or ''),False
    import tempfile
    with tempfile.TemporaryDirectory() as scratch:
        output=Path(scratch)/'progress.log'
        with output.open('wb') as stream:
            process=popen(args,stdout=stream,stderr=subprocess.STDOUT,**options)
        deadline=time.monotonic()+VIDEO_TIMEOUT;paused=False
        next_update=0;percent=None
        try:
            while process.poll() is None:
                now=time.monotonic()
                if Path(cancel).exists() or now>deadline:
                    paused=Path(cancel).exists()
                    break
                if on_progress and now>=next_update:
                    with output.open('rb') as reader:
                        size=reader.seek(0,2)
                        reader.seek(max(0,size-32768))
                        matches=re.findall(rb'\[download\]\s+(\d{1,3}(?:\.\d+)?)%',reader.read())
                    if matches:percent=min(100,float(matches[-1]))
                    on_progress(percent)
                    next_update=now+3
                time.sleep(.5)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=15)
                except subprocess.TimeoutExpired:process.kill();process.wait()
        text=output.read_text(encoding='utf-8',errors='replace')
    if not paused and process.returncode and time.monotonic()>deadline:raise subprocess.TimeoutExpired(args,VIDEO_TIMEOUT)
    return process.returncode,text,paused


def download(entry,data,library,base,*,max_height,max_bytes,reserve,ffmpeg,js_runtime='deno',run=subprocess.run,cancel=None,popen=subprocess.Popen,on_progress=None):
    staging=data/'state'/'video-downloads'/'en-cours'/entry['id']
    durable.mkdir(staging)
    if free_bytes(staging)<max_bytes+reserve:return {'status':'error','reason':'disk_space'}
    started=time.monotonic()
    try:
        def attempt(subtitles=True):
            return execute(command(base,entry,staging,max_height=max_height,max_bytes=max_bytes,ffmpeg=ffmpeg,js_runtime=js_runtime,subtitles=subtitles),
                           cancel=cancel,run=run,popen=popen,on_progress=on_progress)
        returncode,output,paused=attempt();subtitles_skipped=False
        if returncode and not paused and SUBTITLE_FAILURE.search(output):
            # Subtitles can be fetched or created later: keep the video.
            returncode,output,paused=attempt(False);subtitles_skipped=True
    except subprocess.TimeoutExpired:return {'status':'error','reason':'timeout'}
    if paused:return {'status':'paused','reason':'paused'}
    warnings=[line.strip()[:300] for line in output.splitlines() if line.startswith('WARNING')][:10]
    media,sidecars=finished_files(staging,entry['id'])
    if returncode or media is None:
        detail=[line.strip()[:300] for line in output.splitlines() if line.startswith('ERROR')][-3:]
        return {'status':'error','reason':classify(output,returncode),'detail':detail,'warnings':warnings}
    with locked(data/'catalog/content.lock'):
        sorting=collection_sort.load(data/'catalog')
        target,moved,info=publish(media,sidecars,library,entry,sorting=sorting)
    shutil.rmtree(staging,ignore_errors=True)
    if target is None:return {'status':'refused','reason':'collection_excluded'}
    subtitles=sorted(p.name for p in moved if p.suffix.lower() in SUBTITLE_EXTENSIONS)
    return {'status':'downloaded','subtitles_skipped':subtitles_skipped,'path':target.relative_to(library).as_posix(),'title':str(info.get('title') or '')[:300],
            'channel':str(info.get('channel') or info.get('uploader') or '')[:200],'duration_seconds':info.get('duration'),
            'height':info.get('height'),'bytes':target.stat().st_size,'subtitles':subtitles,
            'info_json':any(p.name.endswith('.info.json') for p in moved),'seconds':round(time.monotonic()-started),'warnings':warnings}


def find_js_runtime(data=None):
    """YouTube needs a JavaScript runtime in recent yt-dlp; Deno is its default."""
    if data is not None and youtube_tools.deno(data):return 'deno'
    for name in ('deno','node','bun'):
        if shutil.which(name):return name
    return None


def find_ffmpeg(value,data=None):
    if value:return Path(value)
    prepared=youtube_tools.ffmpeg(data) if data is not None else None
    if prepared:return prepared
    return True if shutil.which('ffmpeg') else None


def data_root(args):
    if args.lab:
        import linux_lab as lab
        lab.checked_mount();return lab.MOUNT/'data'
    if args.data_dir:return setup.safe_path(args.data_dir)
    return setup.safe_path(setup.Installation(args.work_dir or find_work_dir()).load()['data_dir'])


def find_work_dir(application=ROOT):
    """Same private folders as the Windows update launcher; one must match."""
    base=application.parent
    found=[path for path in (base/'prive',application/'.local',base/'moteur'/'.local') if (path/'settings.json').is_file()]
    if len(found)!=1:raise setup.SetupError('Installation introuvable ou ambiguë : indiquez --work-dir (dossier privé de l’installation) ou --data-dir.')
    return found[0]


def run_list(args,*,run=subprocess.run,log=print):
    raw=Path(args.list).read_bytes()
    text=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
    entries,line_errors=parse_list(text)
    if args.action=='check':
        for item in entries:log(f'ligne {item["line"]} : {item["id"]}'+(f' → [{item["theme"]}]' if item['theme'] else ''))
        for item in line_errors:log(f'ligne {item["line"]} : {REASONS[item["reason"]]} — {item["text"]}')
        log(f'{len(entries)} vidéo(s) à traiter, {len(line_errors)} ligne(s) écartée(s).')
        return 2 if line_errors else 0
    data=data_root(args);library=data/'library'/'video'
    if library.is_symlink():raise setup.SetupError('Le dossier library/video est un lien ; téléchargement refusé.')
    durable.mkdir(library)
    work=data/'state'/'video-downloads';durable.mkdir(work)
    base=downloader(data,args.yt_dlp,log=log,run=run)
    ffmpeg=find_ffmpeg(args.ffmpeg,data);js_runtime=find_js_runtime(data)
    max_bytes=int(args.max_size_gb*1_000_000_000);reserve=int(args.reserve_gb*1_000_000_000)
    version=''
    try:version=run([*base,'--version'],capture_output=True,text=True,timeout=60).stdout.strip()
    except (OSError,subprocess.SubprocessError):pass
    report={'schema':1,'started':datetime.now(timezone.utc).isoformat(),'list':Path(args.list).name,'yt_dlp':version,
            'ffmpeg':bool(ffmpeg),'js_runtime':js_runtime,'max_height':args.max_height,'max_bytes':max_bytes,'items':list(line_errors)}
    cancel=Path(args.cancel) if getattr(args,'cancel',None) else None
    progress_path=Path(args.progress) if getattr(args,'progress',None) else None
    def progress(phase,current=None):
        if progress_path is None:return
        done=[item for item in report['items'] if item['status'] not in ('paused',)]
        value={'schema':1,'phase':phase,'total':len(entries)+len(line_errors),'videos':len(entries),'done':len(done),'current':current,
               'counts':{key:sum(1 for item in report['items'] if item['status']==key) for key in ('downloaded','skipped','refused','error')},
               'tools':{'yt_dlp':version,'ffmpeg':bool(ffmpeg),'js_runtime':js_runtime},
               'items':[{key:item[key] for key in ('line','id','status','reason','title','path','theme','subtitles_skipped') if key in item}|({'message':REASONS[item['reason']]} if item.get('reason') in REASONS else {}) for item in (report['items'] if phase!='running' else report['items'][-300:])]}
        if 'unattempted_lines' in report:value['remaining']=len(report['unattempted_lines'])
        if report.get('path'):value['report']=report['path']
        setup.write_json(progress_path,value,private=True)
    if not js_runtime:log('Deno absent : YouTube peut refuser des vidéos ou limiter les formats. Relancer avec Internet pour terminer la préparation.')
    if not ffmpeg:log('FFmpeg absent : seuls les formats déjà complets sont utilisés, souvent en 360p. Relancer avec Internet pour terminer la préparation.')
    with locked(work/'download.lock'):
        present=existing_videos(library);progress('running')
        for index,entry in enumerate(entries,1):
            if cancel is not None and cancel.exists():report['paused']=True;break
            item={'line':entry['line'],'id':entry['id'],'url':entry['url'],'theme':entry['theme']}
            current={'index':index,'line':entry['line'],'url':entry['url']}
            progress('running',current)
            def heartbeat(percent):
                progress('running',{**current,'percent':percent})
            if entry['id'] in present:
                item.update(status='skipped',reason='already_present',path=present[entry['id']].relative_to(library).as_posix())
            else:
                log(f'[{index}/{len(entries)}] {entry["url"]} …')
                try:
                    item.update(download(entry,data,library,base,max_height=args.max_height,max_bytes=max_bytes,reserve=reserve,ffmpeg=ffmpeg,js_runtime=js_runtime,run=run,cancel=cancel,on_progress=heartbeat if progress_path else None))
                except OSError as error:
                    reason='disk_space' if error.errno==errno.ENOSPC else 'file_error'
                    item.update(status='error',reason=reason,detail=[type(error).__name__])
                if item['status']=='downloaded':present[entry['id']]=library/item['path']
                if item['status']=='paused':
                    report['paused']=True;log('Pause demandée : la vidéo en cours reprendra au même endroit.');break
            log(f'[{index}/{len(entries)}] '+(f'téléchargée : {item["path"]}' if item['status']=='downloaded' else f'{REASONS[item["reason"]]} — {entry["url"]}'))
            report['items'].append(item)
            if item.get('reason')=='disk_space':
                log('Arrêt : espace disque insuffisant. Les vidéos déjà rangées sont conservées.');break
    if not report.get('paused') and any(item.get('reason')=='disk_space' for item in report['items']):
        seen={item['line'] for item in report['items']}
        report['unattempted_lines']=[entry['line'] for entry in entries if entry['line'] not in seen]
    report['items']=sorted((item for item in report['items'] if item['status']!='paused'),key=lambda value:value['line'])
    report['finished']=datetime.now(timezone.utc).isoformat()
    counts={key:sum(1 for item in report['items'] if item['status']==key) for key in ('downloaded','skipped','refused','error')}
    report['counts']=counts
    path=work/'rapports'/('rapport-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
    setup.write_json(path,report,private=True)
    report['path']=str(path);progress('paused' if report.get('paused') else 'completed')
    if report.get('paused'):
        log(f'En pause : {counts["downloaded"]} téléchargée(s) jusqu’ici. Relancez la même liste pour reprendre. Rapport : {path}');return 3
    log(f'Terminé : {counts["downloaded"]} téléchargée(s), {counts["skipped"]} déjà présente(s) ou en double, '
        f'{counts["refused"]} ligne(s) refusée(s), {counts["error"]} erreur(s). Rapport : {path}')
    if counts['downloaded']:log('Le site répertorie les nouvelles vidéos tout seul (au démarrage ou à la prochaine recherche).')
    return 0 if not counts['error'] and not counts['refused'] else 2


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action',choices=('prepare','check','download'))
    parser.add_argument('list',nargs='?',help='fichier texte : une adresse YouTube par ligne')
    parser.add_argument('--work-dir',help='dossier de l’installation (par défaut celle de ce dossier)')
    parser.add_argument('--data-dir',help='dossier des données, si différent')
    parser.add_argument('--lab',action='store_true',help='laboratoire Linux de Louis (volume dédié contrôlé)')
    parser.add_argument('--max-height',type=int,default=480,choices=(360,480,720,1080),help='hauteur maximale (480 par défaut)')
    parser.add_argument('--max-size-gb',type=float,default=1.5,help='taille maximale par vidéo (1,5 Go par défaut)')
    parser.add_argument('--reserve-gb',type=float,default=10,help='espace libre à garder sur le disque (10 Go par défaut)')
    parser.add_argument('--ffmpeg',help='chemin de ffmpeg s’il n’est pas dans le PATH')
    parser.add_argument('--latest',action='store_true',help='avec prepare : passer à la toute dernière version de yt-dlp si YouTube bloque')
    parser.add_argument('--progress',help=argparse.SUPPRESS)
    parser.add_argument('--cancel',help=argparse.SUPPRESS)
    parser.add_argument('--yt-dlp',help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    if args.action!='prepare' and not args.list:parser.error('Indiquez le fichier texte de la liste.')
    if args.lab and (args.data_dir or args.work_dir):parser.error('--lab utilise les données du volume dédié.')
    if args.max_size_gb<=0 or args.reserve_gb<0:parser.error('Tailles positives attendues.')
    try:
        if args.action=='prepare':
            data=data_root(args)
            if args.latest:print('yt-dlp mis à jour : version '+str(upgrade(data)));return 0
            ready=youtube_tools.prepare(data,force=True)
            state=youtube_tools.status(data)
            print(f"yt-dlp {state['yt_dlp']}, Deno {'prêt' if state['deno'] else 'absent'}, FFmpeg {'prêt' if state['ffmpeg'] else 'absent'}.")
            return 0 if ready else 1
        return run_list(args)
    except (setup.SetupError,OSError,subprocess.CalledProcessError) as error:
        print('Erreur : '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
