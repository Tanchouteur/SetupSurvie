"""Complete readable text snapshots, shared by translation and long summaries.

This extracts text, not illustrations or OCR. Missing text is explicit. The
caller stores the snapshot before inference; it must not mix originals on resume.
"""
import os
from pathlib import Path
import re
from fastapi import HTTPException
from . import library
from .math_text import BLOCKS


def chunks(text,size=2200):
    """Preserve every source character; prefer line/word boundaries."""
    position=0;spans=[(m.start(),m.end()) for m in BLOCKS.finditer(text)];block=0
    while position<len(text):
        end=min(position+size,len(text))
        if end<len(text):
            sentences=list(re.finditer(r'[.!?;:]\s+',text[position:end]))
            boundary=max(text.rfind('\n',position,end),position+sentences[-1].end()-1 if sentences else -1)
            if boundary<=position+size//2:boundary=text.rfind(' ',position,end)
            if boundary>position+size//2:end=boundary+1
        while block<len(spans) and spans[block][1]<=position:block+=1
        for index in range(block,len(spans)):
            first,last=spans[index]
            if first>=end:break
            if first<end<last:
                # An equation is atomic. Oversized formulas still face the
                # ordinary model budget instead of being silently cut in half.
                end=first if first>position else last;break
        yield text[position:end];position=end


async def extract(identifier,first_page=1,last_page=None,*,purpose='traduction',chunk_size=2200):
    if identifier.startswith('video:'):
        message='Préparez les sous-titres français depuis Bibliothèque → Collections → Vidéos locales ; traduire cet aperçu ferait perdre les horodatages.' if purpose=='traduction' else 'La lecture intégrale des vidéos n’est pas encore préparée. La question ordinaire peut utiliser les passages de sous-titres indexés.'
        raise HTTPException(422,message)
    # A PDF search result is a page; this operation explicitly translates the whole PDF.
    base=identifier.split('#page=')[0] if identifier.startswith('guide:') else identifier
    revision=lambda:library.catalogue.revision(base,library.GUIDES,Path(os.environ.get('ZIM_DIR','/zim')))
    before=revision()
    source=await library.source(base)
    def read():
        if base.startswith('guide:') and base.lower().endswith('.pdf'):
            path=library.GUIDES/base.removeprefix('guide:')
            if any(p.is_symlink() for p in [path,*path.parents]) or not path.resolve().is_relative_to(library.GUIDES.resolve()):
                raise HTTPException(400,'Chemin de document non valide.')
            if not path.is_file():raise HTTPException(404,'Document original indisponible.')
            if path.stat().st_size>300_000_000:raise HTTPException(413,'Ce PDF dépasse la taille prise en charge pour la traduction.')
            texts=pdf_texts(path,first_page,last_page)
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
    try:
        parts=await library.kiwix_queries.disk_io(read)
        after=revision()
        if before and before!=after:raise HTTPException(409,'Le document a changé pendant la lecture. Reprenez après son enregistrement.')
        return {**source,'id':library.catalogue.canonical(base),'source_revision':before or ''},parts
    except HTTPException as error:
        if purpose!='traduction':
            error.detail=str(error.detail).replace('la traduction','la lecture complète').replace('cette traduction','cette lecture complète').replace('traduction intégrale','lecture complète').replace('traduction partielle','lecture partielle')
        raise


def pdf_texts(path,first_page=1,last_page=None):
    """Shared PDF extraction; callers validate the path and join their reader."""
    from pypdf import PdfReader
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
    return texts
