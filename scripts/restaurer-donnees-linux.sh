#!/bin/sh
set -eu

title='Restaurer mes données SetupSurvie'
mode=restore
case "${1:-}" in
    --open) mode=open; title='Ouvrir SetupSurvie'; shift ;;
    --install) mode=install; title='Installer SetupSurvie'; shift ;;
esac
show_error() {
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --title="$title" --text="$1"
    elif command -v kdialog >/dev/null 2>&1; then
        kdialog --title "$title" --error "$1"
    elif command -v notify-send >/dev/null 2>&1; then
        notify-send "$title" "$1"
    else
        printf '%s\n' "$1" >&2
    fi
}

base=$(CDPATH='' cd -- "$1" && pwd -P)
if [ "$mode" != open ] && [ ! -f "$base/manifest.json" ]; then
    show_error 'Ouvrez ce lanceur depuis le dossier app d’un kit SetupSurvie complet.'
    exit 1
fi
if ! python3 -c 'import sys, tkinter; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    show_error 'Cette fenêtre nécessite Python 3.11 ou ultérieur avec Tkinter. Utilisez un ordinateur équipé ou installez le paquet python3-tk de votre distribution.'
    exit 1
fi
if [ "$mode" = open ]; then
    set -- --open "$base"
    application="$base/application"
elif [ "$mode" = install ]; then
    set -- --install "$base"
    application="$base/app"
else
    set -- "$base"
    application="$base/app"
fi
export PYTHONDONTWRITEBYTECODE=1
if ! python3 "$application/scripts/pilot_restore_gui.py" "$@"; then
    show_error 'La fenêtre SetupSurvie ne s’est pas ouverte. Vérifiez que vous utilisez une session graphique.'
    exit 1
fi
