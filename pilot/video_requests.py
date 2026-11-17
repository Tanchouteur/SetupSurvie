"""Video requests for the assistant: intent, query, compact results and links.

The assistant receives titles and links of indexed videos. A title is not a
consulted transcript: subtitles are read with read_source like a document.
"""
import re
from urllib.parse import quote

from . import retrieval

INTENT=re.compile(r'\b(videos?|youtube)\b')
# Words that describe the request rather than its subject.
NOISE=set('''video videos tuto tutos tutoriel tutoriels youtube film films regarder voir montrer montre montrez trouve trouves trouver
cherche chercher recherche donne donner propose proposer affiche afficher liste lister mets mettre ouvre ouvrir lien liens
n importe nimporte quoi quelconque n'importe quelque chose bibliotheque biblioteque ok bah ben bon alors stp svp merci dispo disponible disponibles
il y en as avez ai existe une un des les la le de du sur pour qui me moi nous'''.split())
GUIDANCE=('Résultat find_videos : vidéos de la bibliothèque locale. Pour proposer une vidéo, écris son titre comme lien Markdown '
          'avec son open_url exact, par exemple [Titre](open_url). Ne fabrique aucun lien. Un titre ou une description ne sont pas '
          'des paroles consultées ; pour en résumer le contenu, lis ses sous-titres avec read_source quand has_subtitles=true. '
          'Si results est vide, lis coverage : un index absent ou en cours n’est pas une absence de vidéo. Si indexed_videos est '
          'supérieur à zéro, d’autres vidéos existent : propose une recherche plus large ou la liste sans mot-clé.')
LIMIT=8


def requested(question):
    return bool(INTENT.search(retrieval.normal(question or '')))


def query(question):
    """Subject words of a video request; empty means « list the videos »."""
    from . import library
    words=[word for word in retrieval.normal(question or '').split() if word not in NOISE and word not in library.STOPWORDS and len(word)>1]
    return ' '.join(words)[:200]


def open_url(identifier):
    return '/nouveau/#/bibliotheque/recherche?kind=videos&source='+quote(identifier,safe=':')


def compact(found):
    coverage=getattr(found,'coverage',{}) or {}
    videos=coverage.get('videos') or {}
    rows=[]
    for item in list(found)[:LIMIT]:
        tracks=[track for track in item.get('tracks') or [] if track.get('status')=='passed']
        row={'id':item['id'],'title':item.get('title','')[:200],'open_url':open_url(item['id']),'collection':(item.get('collection') or '')[:120],
             'language':item.get('language',''),'duration_seconds':item.get('duration_seconds'),'has_subtitles':bool(tracks),
             'subtitle_languages':sorted({track.get('language') or 'inconnue' for track in tracks}),
             'match':item.get('match','title'),'excerpt':(item.get('excerpt') or '')[:300]}
        if item.get('match')=='subtitle':row['position_seconds']=int(item.get('position_ms') or 0)//1000
        if item.get('archive_video'):row['archive']=item.get('archive_name')
        rows.append(row)
    return {'results':rows,'coverage':{'status':coverage.get('status','unavailable'),'warning':coverage.get('warning',''),
            'index_status':videos.get('status','unavailable'),'indexed_videos':videos.get('indexed_videos'),'more_results':max(0,len(found)-len(rows))}}


def appendix(answer,suggestions):
    """Deterministic links the model forgot; never removes its own text."""
    missing=[row for row in suggestions if row['open_url'] not in answer and row['id'] not in answer][:5]
    if not missing or any(row['open_url'] in answer for row in suggestions):return answer
    lines=['','','**Vidéos trouvées dans la bibliothèque :**']
    for row in missing:
        title=re.sub(r'[\[\]\n]',' ',row['title']).strip() or 'Vidéo sans titre'
        detail=' · sous-titres '+', '.join(row['subtitle_languages']) if row['has_subtitles'] else ' · sans sous-titres'
        lines.append('- ['+title+']('+row['open_url']+')'+detail)
    return answer.rstrip()+'\n'.join(lines)
