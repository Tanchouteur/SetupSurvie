#!/bin/sh
set -eu
# 3.8.1 takes files or an XML library, not a directory. An empty library is valid.
# Keep source archives read-only; rebuild only the small runtime catalogue.
printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?><library version="20110515"></library>' > /tmp/library.xml
for archive in /data/*.zim; do
  [ -f "$archive" ] || continue
  /usr/local/bin/kiwix-manage /tmp/library.xml add "$archive"
done
exec /usr/local/bin/kiwix-serve --port=8080 --library /tmp/library.xml
