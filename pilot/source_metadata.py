"""Bibliographic facts supplied by metadata, never guessed from file timestamps."""
from datetime import date, datetime
import re
import json
import sqlite3

TRANSLATION_NOTICE='Traduction IA non vérifiée. Comparez les nombres, unités, tableaux et consignes avec le document original. Les illustrations ne sont pas traduites.'


def translation_metadata(db,path):
    if not path.startswith('TRAD-'):return {'is_ai_translation':False}
    result={'is_ai_translation':True,'translation_notice':TRANSLATION_NOTICE}
    try:
        row=db.execute('SELECT source_id,title,source_meta FROM translation_publications WHERE published_path=?',(path,)).fetchone()
        if row:
            meta=json.loads(row['source_meta'])
            result.update(original_id=row['source_id'],original_title=row['title'],original_document_date=meta.get('document_date',''),original_edition=meta.get('edition',''))
    except (sqlite3.Error,ValueError,TypeError,AttributeError):pass
    return result

DATE_FIELDS=('document_date','collected_at','archive_date')
FIELDS=('document_date','edition','collected_at','archive_date')


def date_value(value, *, timestamp=False):
    if not isinstance(value,str):return ''
    value=value.strip()
    try:
        if re.fullmatch(r'\d{4}',value):date(int(value),1,1)
        elif re.fullmatch(r'\d{4}-\d{2}',value):date.fromisoformat(value+'-01')
        elif re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):date.fromisoformat(value)
        elif timestamp and 'T' in value:return datetime.fromisoformat(value.replace('Z','+00:00')).date().isoformat()
        else:return ''
        return value
    except ValueError:return ''


def metadata(item):
    result={key:date_value(item.get(key,'')) for key in DATE_FIELDS}
    edition=item.get('edition','')
    # Older downloads explicitly stored their edition in provenance. Preserve
    # that declaration as an edition, without turning it into a document date.
    if not edition and isinstance(item.get('provenance'),str) and ' — édition ' in item['provenance']:
        edition=item['provenance'].split(' — édition ',1)[1].split(' — ',1)[0]
    result['edition']=edition.strip()[:300] if isinstance(edition,str) else ''
    return result
