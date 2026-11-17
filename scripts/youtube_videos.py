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
from pilot import durable
from pilot.provider_subtitles import video_id
from pilot.video_inventory import INCOMPLETE,SUBTITLE_EXTENSIONS,VIDEO_EXTENSIONS
import youtube_tools

SUBTITLE_LANGUAGES='fr,fr-FR,fr-CA,en,en-US,en-GB'
RESERVED=re.compile(r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?')
FORBIDDEN=re.compile(r'[<>:"/\\|?*\x00-\x1f]')
VIDEO_TIMEOUT=4*3600
REASONS={
    'invalid_url':'adresse non reconnue comme une vidéo YouTube',
    'playlist_refused':'liste de lecture refusée : donner l’adresse de chaque vidéo',
    'duplicate_in_list':'déjà présente plus haut dans la liste',
    'already_present':'déjà dans la bibliothèque',
    'private':'vidéo privée',
    'unavailable':'vidéo supprimée ou indisponible',
    'age_restricted':'vidéo réservée aux comptes connectés (limite d’âge) ; aucun compte n’est utilisé',
    'region_blocked':'vidéo bloquée dans ce pays',
    'members_only':'vidéo réservée aux abonnés payants',
    'live':'diffusion en direct non terminée',
    'too_large':'fichier plus gros que la limite choisie',
    'no_format':'aucun format compatible ; installer FFmpeg peut aider',
    'rate_limited':'YouTube limite les téléchargements ; réessayer plus tard',
    'bot_check':'YouTube demande une vérification anti-robot ; réessayer plus tard, sans contournement',
    'network':'connexion Internet interrompue ; relancer la liste pour reprendre',
    'disk_space':'espace disque insuffisant',
    'timeout':'téléchargement trop long, arrêté ; relancer la liste pour reprendre',
    'tool_failed':'échec de yt-dlp ; voir le détail dans le rapport',
    'output_missing':'yt-dlp n’a produit aucun fichier vidéo terminé',
}
PATTERNS=[
    ('private',r'private video'),('members_only',r'members[- ]only|join this channel'),
    ('age_restricted',r'sign in to confirm your age|age[- ]restricted|inappropriate for some users'),
    ('bot_check',r'sign in to confirm you.?re not a bot|confirm you are not a robot'),
    ('region_blocked',r'available in your country|geo[- ]?restrict|blocked it in your country'),
    ('live',r'live event will begin|is live|premieres in'),
    ('too_large',r'larger than max-filesize|file is larger than'),
    ('no_format',r'requested format is not available|no video formats found'),
    ('rate_limited',r'http error 429|too many requests'),
    ('unavailable',r'video unavailable|has been removed|account associated with this video has been terminated|this video does not exist'),
    ('disk_space',r'no space left on device|not enough space'),
    ('network',r'unable to download webpage|connection (?:reset|refused|aborted)|timed? ?out|temporary failure in name resolution|getaddrinfo failed|network is unreachable'),
]


class ListError(ValueError):pass


def parse_list(text):
    """Entries and line errors of a list file; never touches the network."""
    entries=[];errors=[];seen={};theme=''
    for number,raw in enumerate(text.lstrip('﻿').splitlines(),1):
        line=raw.strip()
        if not line or line.startswith('#'):continue
        heading=re.fullmatch(r'\[(.*)\]',line)
        if heading:theme=folder_name(heading[1]) if heading[1].strip() else '';continue
        address=line.split()[0]
        try:identifier=video_id(address)
        except ValueError:
            reason='playlist_refused' if re.search(r'[?&]list=|/playlist\b|/@|/channel/|/c/|/user/',address) else 'invalid_url'
            errors.append({'line':number,'text':address[:300],'status':'refused','reason':reason});continue
        if identifier in seen:
            errors.append({'line':number,'text':address[:300],'status':'skipped','reason':'duplicate_in_list','first_line':seen[identifier]});continue
        seen[identifier]=number
        entries.append({'line':number,'id':identifier,'url':'https://www.youtube.com/watch?v='+identifier,'theme':theme})
    return entries,errors


def folder_name(value,fallback=''):
    """A short folder name valid on Windows and Linux."""
    text=FORBIDDEN.sub(' ',str(value or ''))
    text=re.sub(r'\s+',' ',text).strip().rstrip('. ')[:80].rstrip('. ')
    if RESERVED.fullmatch(text):text='_'+text
    return text or fallback


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


def command(base,entry,staging,*,max_height,max_bytes,ffmpeg,js_runtime='deno'):
    if ffmpeg:fmt=f'bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/bv*[height<={max_height}]+ba/b[height<={max_height}]'
    else:fmt=f'b[height<={max_height}][ext=mp4]/b[height<={max_height}]'
    args=[*base,'--ignore-config','--no-playlist','--newline','--no-colors','--no-mtime',
          '-f',fmt,'--max-filesize',str(max_bytes),'--write-info-json','--write-subs','--write-auto-subs',
          '--sub-langs',SUBTITLE_LANGUAGES,'--sub-format','vtt/srt/best','--windows-filenames','--trim-filenames','160',
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


def publish(media,sidecars,library,entry):
    """Move finished files into the library: sidecars first, media last.

    The pilot ignores a video until its media file appears, so it never sees
    a video without its title and subtitles."""
    info={}
    for path in sidecars:
        if path.name.endswith('.info.json'):
            try:info=json.loads(path.read_text(encoding='utf-8'))
            except (OSError,ValueError):info={}
    folder=library/'youtube'/(entry['theme'] or folder_name(info.get('channel') or info.get('uploader'),'Sans chaîne'))
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


def download(entry,data,library,base,*,max_height,max_bytes,reserve,ffmpeg,js_runtime='deno',run=subprocess.run):
    staging=data/'state'/'video-downloads'/'en-cours'/entry['id']
    durable.mkdir(staging)
    if free_bytes(staging)<max_bytes+reserve:return {'status':'error','reason':'disk_space'}
    hidden={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    started=time.monotonic()
    try:
        result=run(command(base,entry,staging,max_height=max_height,max_bytes=max_bytes,ffmpeg=ffmpeg,js_runtime=js_runtime),
                   capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=VIDEO_TIMEOUT,stdin=subprocess.DEVNULL,
                   env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'},**hidden)
    except subprocess.TimeoutExpired:return {'status':'error','reason':'timeout'}
    output=(result.stdout or '')+'\n'+(result.stderr or '')
    warnings=[line.strip()[:300] for line in output.splitlines() if line.startswith('WARNING')][:10]
    media,sidecars=finished_files(staging,entry['id'])
    if result.returncode or media is None:
        detail=[line.strip()[:300] for line in output.splitlines() if line.startswith('ERROR')][-3:]
        return {'status':'error','reason':classify(output,result.returncode),'detail':detail,'warnings':warnings}
    target,moved,info=publish(media,sidecars,library,entry)
    shutil.rmtree(staging,ignore_errors=True)
    subtitles=sorted(p.name for p in moved if p.suffix.lower() in SUBTITLE_EXTENSIONS)
    return {'status':'downloaded','path':target.relative_to(library).as_posix(),'title':str(info.get('title') or '')[:300],
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
    text=Path(args.list).read_text(encoding='utf-8-sig')
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
    if not js_runtime:log('Deno absent : YouTube peut refuser des vidéos ou limiter les formats. Relancer avec Internet pour terminer la préparation.')
    if not ffmpeg:log('FFmpeg absent : seuls les formats déjà complets sont utilisés, souvent en 360p. Relancer avec Internet pour terminer la préparation.')
    with locked(work/'download.lock'):
        present=existing_videos(library)
        for index,entry in enumerate(entries,1):
            item={'line':entry['line'],'id':entry['id'],'url':entry['url'],'theme':entry['theme']}
            if entry['id'] in present:
                item.update(status='skipped',reason='already_present',path=present[entry['id']].relative_to(library).as_posix())
            else:
                log(f'[{index}/{len(entries)}] {entry["url"]} …')
                item.update(download(entry,data,library,base,max_height=args.max_height,max_bytes=max_bytes,reserve=reserve,ffmpeg=ffmpeg,js_runtime=js_runtime,run=run))
                if item['status']=='downloaded':present[entry['id']]=library/item['path']
            log(f'[{index}/{len(entries)}] '+(f'téléchargée : {item["path"]}' if item['status']=='downloaded' else f'{REASONS[item["reason"]]} — {entry["url"]}'))
            report['items'].append(item)
            if item.get('reason')=='disk_space':
                log('Arrêt : espace disque insuffisant. Les vidéos déjà rangées sont conservées.');break
    report['items'].sort(key=lambda value:value['line'])
    report['finished']=datetime.now(timezone.utc).isoformat()
    counts={key:sum(1 for item in report['items'] if item['status']==key) for key in ('downloaded','skipped','refused','error')}
    report['counts']=counts
    path=work/'rapports'/('rapport-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
    setup.write_json(path,report,private=True)
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
