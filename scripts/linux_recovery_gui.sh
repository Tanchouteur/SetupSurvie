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

case "$mode" in
    install)
        parent=$(zenity --file-selection --directory --title="Choisir le dossier où installer SetupSurvie" --filename="/srv/") || exit 0
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
