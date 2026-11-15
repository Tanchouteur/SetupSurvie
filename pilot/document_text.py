"""Complete readable text snapshots, shared by translation and long summaries.

This extracts text, not illustrations or OCR. Missing text is explicit. The
caller stores the snapshot before inference; it must not mix originals on resume.
"""
import re
from fastapi import HTTPException
from . import library


def chunks(text,size=2200):
    """Preserve every source character; prefer line/word boundaries."""
    while text:
        end=min(size,len(text))
        if end<len(text):
            sentences=list(re.finditer(r'[.!?;:]\s+',text[:end]))
            boundary=max(text.rfind('\n',0,end),sentences[-1].end()-1 if sentences else -1)
            if boundary<=size//2:boundary=text.rfind(' ',0,end)
            if boundary>size//2:end=boundary+1
        yield text[:end];text=text[end:]


async def extract(identifier,first_page=1,last_page=None,*,purpose='traduction',chunk_size=2200):
    # A PDF search result is a page; this operation explicitly translates the whole PDF.
    base=identifier.split('#page=')[0] if identifier.startswith('guide:') else identifier
    source=await library.source(base)
    def read():
        if base.startswith('guide:') and base.lower().endswith('.pdf'):
            from pypdf import PdfReader
            path=library.GUIDES/base.removeprefix('guide:')
            if any(p.is_symlink() for p in [path,*path.parents]) or not path.resolve().is_relative_to(library.GUIDES.resolve()):
                raise HTTPException(400,'Chemin de document non valide.')
            if not path.is_file():raise HTTPException(404,'Document original indisponible.')
            if path.stat().st_size>300_000_000:raise HTTPException(413,'Ce PDF dépasse la taille prise en charge pour la traduction.')
            fingerprint=path.stat()
            try:reader=PdfReader(path)
            except Exception:raise HTTPException(422,'Impossible d’ouvrir ce PDF pour en extraire le texte.')
            if reader.is_encrypted:raise HTTPException(422,'Ce PDF est protégé. Utilisez une copie dont le texte est accessible.')
            if len(reader.pages)>1200:raise HTTPException(413,'Ce PDF dépasse 1 200 pages. Choisissez un document plus court.')
            end=last_page or len(reader.pages)
            if not 1<=first_page<=end<=len(reader.pages):raise HTTPException(422,'La plage demandée ne correspond pas aux pages de ce PDF.')
            texts=[];total=0
            for number in range(first_page,end+1):
                try:text=reader.pages[number-1].extract_text() or ''
                except Exception:text=''
                total+=len(text)
                if len(text)>100_000 or total>5_000_000:raise HTTPException(413,'Ce document contient trop de texte pour cette traduction. Aucune traduction partielle n’a été lancée.')
                texts.append((number,text))
            after=path.stat()
            if (fingerprint.st_size,fingerprint.st_mtime_ns,fingerprint.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
                raise HTTPException(409,'Le document a changé pendant la lecture. Reprenez une fois son enregistrement terminé.')
        else:
            if first_page!=1 or last_page is not None:raise HTTPException(422,'Le choix des pages est disponible pour les PDF uniquement.')
            text=source['text']
            if source.get('truncated') or source.get('text_truncated') or len(text)>=(100000 if not base.startswith('guide:') else 500000):
                raise HTTPException(413,'Cet aperçu est incomplet. La traduction intégrale de ce format n’est pas disponible.')
            texts=[(1,text)]
        parts=[]
        for page,text in texts:
            if not text.strip():parts.append((page,'','unreadable'))
            else:parts.extend((page,part,'pending') for part in chunks(text,chunk_size))
        if not any(status=='pending' for _,_,status in parts):
            raise HTTPException(422,'Aucun texte extractible. Le document peut être illustré ou nécessiter une reconnaissance de caractères (OCR).')
        return parts
    # Join the file reader on cancellation before a caller can delete its state.
    try:return source,await library.kiwix_queries.disk_io(read)
    except HTTPException as error:
        if purpose!='traduction':
            error.detail=str(error.detail).replace('la traduction','la lecture complète').replace('cette traduction','cette lecture complète').replace('traduction intégrale','lecture complète').replace('traduction partielle','lecture partielle')
        raise


