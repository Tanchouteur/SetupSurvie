#!/usr/bin/env bash
# Interface locale du support de secours ; les opérations privilégiées sont séparées.
set -u

if ! command -v zenity >/dev/null 2>&1; then
    exit 1
fi
if ! command -v pkexec >/dev/null 2>&1; then
    zenity --error --text="L'autorisation graphique d'administration (pkexec) est nécessaire."
    exit 1
fi

mode=${1:-}
base=${2:-}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || exit 1
admin="$script_dir/linux_recovery_admin.sh"
if [[ ! -f "$admin" || -z "$base" ]]; then
    zenity --error --text="Le support ou le programme d'installation est introuvable."
    exit 1
fi

case "$mode" in
    install)
        parent=$(zenity --file-selection --directory --title="Choisir le dossier où installer SetupSurvie" --filename="/srv/") || exit 0
        destination=$(zenity --entry --title="Dossier d'installation" --text="Indiquez le chemin du dossier à créer. Après une interruption, choisissez le même dossier pour reprendre :" --entry-text="${parent%/}/SetupSurvie") || exit 0
        if [[ "$destination" != /* || "$destination" == / ]]; then
            zenity --error --text="Indiquez un chemin absolu pour le nouveau dossier d'installation."
            exit 1
        fi
        selection=$(zenity --list --checklist --title="Point de récupération" --text="Un point de récupération permet de retrouver cette installation plus tard. Décochez la case si vous ne souhaitez pas en créer." --column="Créer" --column="Option" TRUE "Créer un point de récupération") || exit 0
        point=no
        [[ -n "$selection" ]] && point=yes
        action=install
        ;;
    maintenance)
        action=$(zenity --list --radiolist --title="Entretien de SetupSurvie" --text="Choisissez une opération :" --column="Choix" --column="Opération" --column="Action" --print-column=3 TRUE "Créer un point de récupération" point FALSE "Restaurer dans une nouvelle copie" restore) || exit 0
        case "$action" in
            point) ;;
            restore)
                zenity --question --title="Confirmer la restauration" --text="Une nouvelle copie sera créée à partir du point de récupération. Continuer ?" || exit 0
                ;;
            *) exit 0 ;;
        esac
        ;;
    *)
        zenity --error --text="Cette opération n'est pas reconnue."
        exit 1
        ;;
esac

tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/setupsurvie-gui.XXXXXXXX") || {
    zenity --error --text="Impossible de préparer l'opération."
    exit 1
}
trap 'rm -rf -- "$tmpdir"' EXIT
(
    case "$action" in
        install) pkexec /bin/bash "$admin" install "$base" "$destination" "$point" ;;
        point|restore) pkexec /bin/bash "$admin" "$action" "$base" ;;
    esac >"$tmpdir/resultat" 2>&1
    printf '%s\n' "$?" >"$tmpdir/statut"
) | zenity --progress --pulsate --auto-close --no-cancel --title="SetupSurvie" --text="Opération en cours. Autorisez l'administration si cela vous est demandé."

if [[ -f "$tmpdir/statut" ]] && [[ $(cat "$tmpdir/statut") == 0 ]]; then
    zenity --info --title="SetupSurvie" --text="Opération terminée. Pour ouvrir SetupSurvie, rendez-vous sur http://127.0.0.1:8080."
else
    # Afficher la sortie complète afin de faciliter le diagnostic sans terminal.
    if [[ ! -s "$tmpdir/resultat" ]]; then
        printf '%s\n' "L'opération n'a pas pu être terminée ou l'autorisation a été refusée." >"$tmpdir/resultat"
    fi
    zenity --text-info --title="SetupSurvie : opération interrompue" --width=700 --height=400 --filename="$tmpdir/resultat"
    exit 1
fi
