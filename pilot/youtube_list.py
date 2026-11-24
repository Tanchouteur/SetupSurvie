"""YouTube video lists: parsing and folder names, shared by the site and the host tool.

Standard library only; no network. A list has one YouTube video address per
line, optional « [thème] » sections and # comments.
"""
import re

from .provider_subtitles import video_id

MAX_TEXT = 300_000
INSTALLATION_LIST = 'youtube-installation.txt'

RESERVED=re.compile(r'(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?')
FORBIDDEN=re.compile(r'[<>:"/\\|?*\x00-\x1f]')
REASONS={
    'invalid_url':'adresse non reconnue comme une vidéo YouTube',
    'playlist_refused':'liste de lecture refusée : donner l’adresse de chaque vidéo',
    'duplicate_in_list':'déjà présente plus haut dans la liste',
    'already_present':'déjà dans la bibliothèque',
    'collection_excluded':'collection exclue du téléchargement',
    'private':'vidéo privée',
    'unavailable':'vidéo supprimée ou indisponible',
    'age_restricted':'vidéo réservée aux comptes connectés (limite d’âge) ; aucun compte n’est utilisé',
    'region_blocked':'vidéo bloquée dans ce pays',
    'members_only':'vidéo réservée aux abonnés payants',
    'live':'diffusion en direct non terminée',
    'too_large':'fichier plus gros que la limite choisie',
    'no_format':'aucun format compatible avec la qualité choisie',
    'rate_limited':'YouTube limite les téléchargements ; réessayer plus tard',
    'bot_check':'YouTube demande une vérification anti-robot ; réessayer plus tard, sans contournement',
    'network':'connexion Internet interrompue ; relancer la liste pour reprendre',
    'disk_space':'espace disque insuffisant',
    'timeout':'téléchargement trop long, arrêté ; relancer la liste pour reprendre',
    'provider_forbidden':'YouTube a refusé l’accès au fichier vidéo (HTTP 403)',
    'extractor':'yt-dlp n’a pas pu lire les informations de YouTube ; vérifiez sa version',
    'file_error':'le fichier n’a pas pu être enregistré ; vérifiez le dossier et ses droits',
    'tool_failed':'échec de yt-dlp ; voir le détail dans le rapport',
    'paused':'mise en pause ; reprendre pour continuer',
    'output_missing':'yt-dlp n’a produit aucun fichier vidéo terminé',
}
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
