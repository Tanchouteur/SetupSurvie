#!/usr/bin/env bash
# Interface locale du support de secours ; les opérations privilégiées sont séparées.
set -u

if ! command -v zenity >/dev/null 2>&1; then
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --error "Le bureau doit disposer de Zenity. Ouvrez le guide LISEZ-MOI.html du SSD."
    fi
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

free_space() {
    df -h --output=avail -- "$1" 2>/dev/null | tail -n 1 | tr -d ' '
}

choose_disk() {
    local location device fs label
    local -a disks=(TRUE "Disque système" "$(free_space /srv)" /srv)
    while read -r location device fs; do
        case "$fs" in ext4|btrfs|xfs) ;; *) continue ;; esac
        location=$(printf '%b' "$location")
        case "$location" in /mnt/*|/media/*|/run/media/*) ;; *) continue ;; esac
        [[ -d "$location" && $(stat -c %u -- "$location") == 0 ]] || continue
        [[ $((8#$(stat -c %a -- "$location") & 8#22)) == 0 ]] || continue
        label=$(lsblk -dno LABEL -- "${device%%[*}" 2>/dev/null)
        disks+=(FALSE "${label:-${location##*/}}" "$(free_space "$location")" "$location")
    done < <(findmnt --noheadings --raw --real --output TARGET,SOURCE,FSTYPE)
    disks+=(FALSE "Choisir un autre dossier…" "" autre)
    location=$(zenity --list --radiolist --title="Choisir le disque de destination" \
        --text="Le nouveau dossier SetupSurvie sera créé sur le disque choisi." \
        --width=560 --height=330 --column="Choix" --column="Disque" \
        --column="Espace libre" --column="Dossier" --hide-column=4 --print-column=4 \
        "${disks[@]}") || return 1
    if [[ "$location" == autre ]]; then
        zenity --file-selection --directory --title="Choisir le dossier de destination" --filename="/srv/"
    else
        printf '%s\n' "$location"
    fi
}

case "$mode" in
    install)
        parent=$(choose_disk) || exit 0
        [[ "$parent" == /* ]] || exit 0
        destination="${parent%/}/SetupSurvie"
        selection=$(zenity --list --checklist --title="Point de restauration" --text="Un point de restauration permet de retrouver cette installation plus tard. Décochez la case si vous ne souhaitez pas en créer." --column="Créer" --column="Option" TRUE "Créer un point de restauration") || exit 0
        point=no
        [[ -n "$selection" ]] && point=yes
        action=install
        ;;
    maintenance|maintenance-select)
        if [[ "$mode" == maintenance-select ]]; then
            base=$(zenity --file-selection --directory --title="Choisir le dossier SetupSurvie déjà installé" --filename="/srv/") || exit 0
            base=${base%/}
        fi
        action=$(zenity --list --radiolist --title="Entretien de SetupSurvie" --text="Choisissez une opération :" --column="Choix" --column="Opération" --column="Action" --print-column=3 TRUE "Créer un point de restauration" point FALSE "Restaurer dans une nouvelle copie" restore) || exit 0
        case "$action" in
            point) ;;
            restore)
                zenity --question --title="Confirmer la restauration" --text="SetupSurvie sera arrêté et remplacé par une nouvelle copie du point de restauration. Les données récentes seront gardées dans l'ancien dossier, sans être remises automatiquement dans la nouvelle copie. Continuer ?" || exit 0
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
    esac 2>&1
    printf '%s\n' "$?" >"$tmpdir/statut"
) | (
    while IFS= read -r line; do
        printf '%s\n' "$line" >>"$tmpdir/resultat"
        case "$line" in
            'Copie vérifiée '*|'Copie en cours '*|'Protection du point '*|'Préparation de la copie '*|            'Installation des outils '*|'Préparation du point '*|'Vérification et copie '*|            'Mise à l’abri '*)
                printf '# %s\n' "$line" ;;
        esac
    done
    printf '100\n'
) | zenity --progress --pulsate --auto-close --no-cancel --title="SetupSurvie" --text="Opération en cours. Autorisez l'administration si cela vous est demandé."

if [[ -f "$tmpdir/statut" ]] && [[ $(cat "$tmpdir/statut") == 0 ]]; then
    if [[ "$action" == point ]]; then
        zenity --info --title="SetupSurvie" --text="Le point de restauration a été vérifié et protégé."
    elif zenity --question --title="SetupSurvie" --text="Opération terminée. Ouvrir SetupSurvie ?" --ok-label="Ouvrir SetupSurvie" --cancel-label="Fermer"; then
        xdg-open http://127.0.0.1:8080 >/dev/null 2>&1 ||
            zenity --info --text="Ouvrez http://127.0.0.1:8080 dans votre navigateur."
    fi
else
    # Afficher la sortie complète afin de faciliter le diagnostic sans terminal.
    if [[ ! -s "$tmpdir/resultat" ]]; then
        printf '%s\n' "L'opération n'a pas pu être terminée ou l'autorisation a été refusée." >"$tmpdir/resultat"
    fi
    zenity --text-info --title="SetupSurvie : opération interrompue" --width=700 --height=400 --filename="$tmpdir/resultat"
    exit 1
fi
