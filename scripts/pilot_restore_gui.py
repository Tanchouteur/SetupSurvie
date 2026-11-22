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

from pilot_backup import RESTORE_JOURNAL, host_target, read_restore_job, restore, restore_inputs
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


def main():
    kit = setup.safe_path(sys.argv[1])
    window = tk.Tk()
    window.withdraw()
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

    window.title(TITLE)
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=str(destination), wraplength=460).pack(anchor='w')
    status = ttk.Label(frame, text='Vérification de la sauvegarde…', wraplength=460)
    status.pack(anchor='w', pady=10)
    bar = ttk.Progressbar(frame, mode='indeterminate', length=460)
    bar.pack(fill='x')
    bar.start()
    window.protocol('WM_DELETE_WINDOW', lambda: None)
    messages = queue.SimpleQueue()

    def run_restore():
        try:
            restore(snapshot, kit, destination/'private', destination/'data', target=target, resume=resume,
                    progress=lambda line: messages.put(('progress', line)))
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
                messagebox.showerror(TITLE, f'{body}\n\nPour reprendre, rouvrez le lanceur et choisissez la même sauvegarde et le même disque.', parent=window)
            elif messagebox.askyesno(TITLE, 'Restauration terminée. Ouvrir SetupSurvie ?', parent=window):
                webbrowser.open('http://127.0.0.1:8080')
            window.destroy()
            return
        window.after(150, poll)

    threading.Thread(target=run_restore, daemon=True).start()
    window.deiconify()
    window.after(150, poll)
    window.mainloop()


if __name__ == '__main__':
    main()
