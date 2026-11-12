"""Bibliographic facts supplied by metadata, never guessed from file timestamps."""
from datetime import date, datetime
import re

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
