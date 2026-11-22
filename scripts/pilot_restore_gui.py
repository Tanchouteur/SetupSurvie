"""Restore a private snapshot from an offline kit on a prepared computer."""
from datetime import datetime
from pathlib import Path
import queue
import sys
import tarfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from pilot_backup import RESTORE_JOURNAL, host_target, read_restore_job, restore, restore_inputs, start_restored
import setup


TITLE = 'Restaurer mes données SetupSurvie'


def find_pending(disk, inputs):
    for folder in sorted(disk.glob('SetupSurvie-Restaure-*'), reverse=True):
        journal = folder/RESTORE_JOURNAL
        if folder.is_symlink() or journal.is_symlink():
            continue
        try:
            job = read_restore_job(journal)
        except (OSError, ValueError, TypeError, setup.SetupError):
            continue
        if job and job['phase'] != 'complete' and job.get('inputs') == inputs:
            return folder


def install_kit(window, kit):
    from pilot_kit import install
    title = 'Installer SetupSurvie'
    if host_target() != 'linux' or not (kit/'manifest.json').is_file():
        messagebox.showerror(title, 'Ouvrez le lanceur Linux depuis le dossier app du kit.', parent=window)
        window.destroy()
        return
    parent = filedialog.askdirectory(parent=window, title='Choisir où installer SetupSurvie', mustexist=True)
    if not parent:
        window.destroy()
        return
    destination = Path(parent)/datetime.now().strftime('SetupSurvie-%Y%m%d-%H%M%S-%f')
    if not messagebox.askokcancel(
        title, f'Installer SetupSurvie dans ce nouveau dossier ?\n\n{destination}\n\n'
        'Python et Docker doivent être prêts. Après la copie, le site s’ouvrira avec le moteur IA en pause.',
        parent=window,
    ):
        window.destroy()
        return

    def action(progress):
        install(kit, 'linux', destination/'data', destination/'private', cpu=True,
                graphical=True, progress=progress)

    show_operation(window, destination, 'Vérification du kit…', action, title=title)


def open_local(base, *, progress=None):
    if (base/RESTORE_JOURNAL).exists():
        start_restored(base, progress=progress)
    else:
        from pilot_kit import start_installed
        start_installed(base, progress=progress)


def main():
    window = tk.Tk()
    window.withdraw()
    if sys.argv[1] == '--install':
        install_kit(window, setup.safe_path(sys.argv[2]))
        return
    if sys.argv[1] == '--open':
        base = setup.safe_path(sys.argv[2])
        show_operation(window, base, 'Démarrage de SetupSurvie…',
                       lambda progress: open_local(base, progress=progress))
        return
    kit = setup.safe_path(sys.argv[1])
    target = host_target()
    if target is None:
        messagebox.showerror(TITLE, 'Utilisez ce lanceur sur Linux ou Windows.', parent=window)
        window.destroy()
        return
    if not (kit/'manifest.json').is_file():
        messagebox.showerror(TITLE, 'Ouvrez ce lanceur depuis le dossier app du kit hors ligne.', parent=window)
        window.destroy()
        return
    snapshot = filedialog.askdirectory(parent=window, title='Choisir le dossier de la sauvegarde personnelle',
                                       initialdir=kit.parent, mustexist=True)
    if not snapshot:
        window.destroy()
        return
    snapshot = Path(snapshot)
    if not (snapshot/'backup.json').is_file():
        messagebox.showerror(TITLE, 'Choisissez le dossier qui contient le fichier backup.json.', parent=window)
        window.destroy()
        return
    parent = filedialog.askdirectory(parent=window, title='Choisir le disque de destination', mustexist=True)
    if not parent:
        window.destroy()
        return
    disk = Path(parent)
    try:
        pending = find_pending(disk, restore_inputs(snapshot, kit, target))
    except (OSError, ValueError, setup.SetupError) as error:
        messagebox.showerror(TITLE, str(error), parent=window)
        window.destroy()
        return
    resume = False
    if pending:
        resume = messagebox.askyesnocancel(
            TITLE, f'Une restauration est en attente dans ce dossier :\n\n{pending}\n\n'
            'Choisissez Oui pour la reprendre, ou Non pour créer une nouvelle copie.',
            parent=window,
        )
        if resume is None:
            window.destroy()
            return
    if resume:
        destination = pending
    else:
        destination = disk/datetime.now().strftime('SetupSurvie-Restaure-%Y%m%d-%H%M%S-%f')
        if not messagebox.askokcancel(
            TITLE, f'Restaurer les données dans ce nouveau dossier ?\n\n{destination}\n\n'
            'La sauvegarde et le kit resteront intacts. Fermez toute autre installation sur ce PC.',
            parent=window,
        ):
            window.destroy()
            return

    def action(progress):
        restore(snapshot, kit, destination/'private', destination/'data', target=target,
                resume=resume, progress=progress)

    show_operation(window, destination, 'Vérification de la sauvegarde…', action,
                   restoring=True)


def show_operation(window, destination, initial_status, action, *, restoring=False, title='Ouvrir SetupSurvie'):
    if restoring:
        title = TITLE
    window.title(title)
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=str(destination), wraplength=460).pack(anchor='w')
    status = ttk.Label(frame, text=initial_status, wraplength=460)
    status.pack(anchor='w', pady=10)
    bar = ttk.Progressbar(frame, mode='indeterminate', length=460)
    bar.pack(fill='x')
    bar.start()
    window.protocol('WM_DELETE_WINDOW', lambda: None)
    messages = queue.SimpleQueue()

    def run_operation():
        try:
            action(lambda line: messages.put(('progress', line)))
        except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, setup.SetupError) as error:
            messages.put(('error', str(error)))
        else:
            messages.put(('done', None))

    def poll():
        while not messages.empty():
            kind, body = messages.get()
            if kind == 'progress':
                status.configure(text=body)
                continue
            if kind == 'error':
                if restoring:
                    body += '\n\nPour reprendre, rouvrez le lanceur et choisissez la même sauvegarde et le même disque.'
                messagebox.showerror(title, body, parent=window)
            elif not restoring or messagebox.askyesno(title, 'Restauration terminée. Ouvrir SetupSurvie ?', parent=window):
                webbrowser.open('http://127.0.0.1:8080')
            window.destroy()
            return
        window.after(150, poll)

    threading.Thread(target=run_operation, daemon=True).start()
    window.deiconify()
    window.after(150, poll)
    window.mainloop()


if __name__ == '__main__':
    main()
