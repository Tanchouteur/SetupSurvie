#!/bin/sh
set -eu

title='Dupliquer le kit SetupSurvie'
mode=duplicate
if [ "${2:-}" = --verify ]; then
    title='Vérifier le kit SetupSurvie'
    mode=verify-support
fi
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
if [ ! -f "$base/manifest.json" ]; then
    show_error "Ouvrez ce lanceur depuis le dossier app d’un kit SetupSurvie complet."
    exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
if python3 -c 'import sys, tkinter; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    shift
    if ! python3 "$base/app/scripts/kit_duplicate_gui.py" "$base" "$@"; then
        show_error "La fenêtre de copie ne s’est pas ouverte. Vérifiez que vous utilisez une session graphique."
        exit 1
    fi
    exit 0
fi

if ! command -v zenity >/dev/null 2>&1; then
    show_error 'Pour copier ce kit, ouvrez une session graphique avec Zenity ou Python 3.11 avec Tkinter.'
    exit 1
fi
python=python3
bundle="$base/installateurs-linux"
if ! "$python" -c 'import sqlite3, sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    if [ ! -f "$bundle/tools/linux-offline-installers/python-archive.txt" ]; then
        show_error 'Python manque sur ce PC et dans le kit. Consultez LISEZ-MOI.html pour préparer les installateurs Linux.'
        exit 1
    fi
    python=
fi

if [ "$mode" = duplicate ]; then
    parent=$(zenity --file-selection --directory --title='Choisir un dossier sur le second disque') || exit 0
    [ -n "$parent" ] || exit 0
    target="${parent%/}/SetupSurvie-Kit"
    zenity --question --title="$title" --text="Copier le kit vers ce dossier ?
$target

Pour reprendre, choisissez le même dossier." ||
        exit 0

    set -- "$target"
else
    set --
fi
backup=
if [ "$mode" = verify-support ] && zenity --question --title="$title" --ok-label=Oui --cancel-label=Non \
        --text="Vérifier aussi une sauvegarde personnelle ?

Choisissez ensuite son dossier daté, sur ce SSD ou un autre disque. Rien ne sera modifié."; then
    backup=$(zenity --file-selection --directory --title='Choisir le dossier de la sauvegarde personnelle') || backup=
fi

scratch=$(mktemp -d "${TMPDIR:-/tmp}/setupsurvie-copie.XXXXXXXX") || {
    show_error 'Impossible de créer un dossier temporaire pour la copie.'
    exit 1
}
trap 'rm -rf -- "$scratch"' EXIT
(
    # Keep writing the result even if the progress window closes.
    trap '' PIPE
    set +e
    if [ -z "$python" ]; then
        printf '%s
' 'Installation temporaire de Python depuis le SSD…'
        /bin/bash "$base/app/scripts/installer-outils-linux-hors-ligne.sh" --python-seul "$bundle" "$scratch/outils"
        code=$?
        if [ "$code" -ne 0 ]; then
            printf '%s
' "$code" > "$scratch/statut"
            exit "$code"
        fi
        python="$scratch/outils/bin/python3"
    fi
    "$python" "$base/app/scripts/pilot_kit.py" "$mode" "$base" "$@"
    code=$?
    if [ "$code" -eq 0 ] && [ -n "$backup" ]; then
        printf '\n'
        if { [ ! -r "$backup" ] || [ ! -x "$backup" ] || { [ -e "$backup/backup.json" ] && [ ! -r "$backup/backup.json" ]; }; } &&
                command -v pkexec >/dev/null 2>&1; then
            printf '%s\n' 'Sauvegarde protégée : autorisation administrateur demandée…'
            pkexec --disable-internal-agent /bin/bash "$base/app/scripts/linux_recovery_admin.sh" verify-backup "$base" "$backup"
        else
            "$python" "$base/app/scripts/pilot_backup.py" verify "$backup" --kit "$base"
        fi
        code=$?
    fi
    printf '%s
' "$code" > "$scratch/statut"
) 2>&1 | (
    trap '' PIPE
    while IFS= read -r line; do
        printf '%s
' "$line" >> "$scratch/resultat"
        printf '# %s
' "$line" 2>/dev/null || :
    done
    printf '100
' 2>/dev/null || :
) | zenity --progress --pulsate --auto-close --no-cancel --title="$title" --text='Préparation de la copie…' || :

if [ -f "$scratch/statut" ] && [ "$(cat "$scratch/statut")" = 0 ]; then
    if [ "$mode" = verify-support ]; then
        zenity --text-info --title="$title" --filename="$scratch/resultat" || :
    else
        zenity --info --title="$title" --text='Le second kit est vérifié. Vous pouvez éjecter le support.' || :
    fi
else
    failure='Copie interrompue'
    message='La copie a été interrompue. Rouvrez le lanceur pour reprendre.'
    if [ "$mode" = verify-support ]; then
        failure='Vérification non réussie'
        message='La vérification a été interrompue. Rouvrez le lanceur pour recommencer.'
    fi
    if [ ! -s "$scratch/resultat" ]; then
        printf '%s
' "$message" > "$scratch/resultat"
    fi
    zenity --text-info --title="$failure" --filename="$scratch/resultat" || :
    exit 1
fi
