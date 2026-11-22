#!/bin/sh
set -eu
# 3.8.1 takes files or an XML library, not a directory. An empty library is valid.
# Keep source archives read-only; rebuild only the small runtime catalogue.
printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?><library version="20110515"></library>' > /tmp/library.xml
for archive in /data/*.zim; do
  [ -f "$archive" ] || continue
  /usr/local/bin/kiwix-manage /tmp/library.xml add "$archive"
done
# Bound the archives and search engines kept open: with about 200 archives the
# defaults let Kiwix exceed 10 GB during searches (Bazzite lab, 22 November 2026);
# these values peaked at 6 GB on the same 136 queries without losing results.
export KIWIX_ARCHIVE_CACHE_SIZE="${KIWIX_ARCHIVE_CACHE_SIZE:-16}"
export KIWIX_SEARCHER_CACHE_SIZE="${KIWIX_SEARCHER_CACHE_SIZE:-8}"
export KIWIX_SUGGESTION_SEARCHER_CACHE_SIZE="${KIWIX_SUGGESTION_SEARCHER_CACHE_SIZE:-8}"
exec /usr/local/bin/kiwix-serve --port=8080 --library /tmp/library.xml
