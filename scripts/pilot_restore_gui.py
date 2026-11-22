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

from pilot_backup import host_target, restore
import setup


TITLE = 'Restaurer mes données SetupSurvie'


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
    destination = Path(parent)/datetime.now().strftime('SetupSurvie-Restaure-%Y%m%d-%H%M%S-%f')
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
            restore(snapshot, kit, destination/'private', destination/'data', target=target,
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
                messagebox.showerror(TITLE, f'{body}\n\nLa sauvegarde reste disponible.', parent=window)
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
