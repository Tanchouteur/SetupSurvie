"""Graphical entry point for copying an exported public kit."""
import queue
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from kit_duplicate import duplicate, verify_support
from pilot_backup import verify_backup
import setup


def main():
    source = setup.safe_path(sys.argv[1])
    window = tk.Tk()
    window.withdraw()
    checking = '--verify' in sys.argv[2:]
    title = 'Vérifier le kit SetupSurvie' if checking else 'Dupliquer le kit SetupSurvie'
    target = source
    backup = None
    if checking and messagebox.askyesno(
            title, 'Vérifier aussi une sauvegarde personnelle ?\n\n'
            'Choisissez ensuite son dossier daté, sur ce SSD ou un autre disque. Rien ne sera modifié.',
            parent=window):
        backup = filedialog.askdirectory(parent=window, title='Choisir le dossier de la sauvegarde personnelle',
                                         mustexist=True) or None
    if not checking:
        parent = filedialog.askdirectory(parent=window, title='Choisir un dossier sur le second disque',
                                         mustexist=True)
        if not parent:
            window.destroy()
            return
        target = Path(parent) / 'SetupSurvie-Kit'
        if not messagebox.askokcancel(
                'Dupliquer le kit SetupSurvie',
                f'Copier le kit vers ce dossier ?\n\n{target}\n\n'
                'Pour reprendre une copie interrompue, choisissez le même dossier sur le second disque.',
                parent=window):
            window.destroy()
            return

    window.title(title)
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=str(target), wraplength=460).pack(anchor='w')
    status = ttk.Label(frame, text='Contrôle du kit…', wraplength=460)
    status.pack(anchor='w', pady=10)
    progress = ttk.Progressbar(frame, mode='indeterminate', length=460)
    progress.pack(fill='x')
    progress.start()
    window.protocol('WM_DELETE_WINDOW', lambda: None)
    messages = queue.SimpleQueue()

    def copy():
        try:
            report = lambda line: messages.put(('progress', line))
            if checking:
                result = verify_support(source, report=report)
                if backup:
                    result += '\n\n' + verify_backup(backup, source, report=report)
            else:
                duplicate(source, target, report=report)
                result = 'Le second kit est vérifié. Vous pouvez éjecter le support.'
        except (OSError, ValueError, KeyError, TypeError, setup.SetupError) as error:
            messages.put(('error', str(error)))
        else:
            messages.put(('done', result))

    def poll():
        while not messages.empty():
            state, line = messages.get()
            if state == 'progress':
                status.configure(text=line)
                continue
            if state == 'error':
                messagebox.showerror(title, line, parent=window)
            else:
                messagebox.showinfo(title, line, parent=window)
            window.destroy()
            return
        window.after(150, poll)

    threading.Thread(target=copy, daemon=True).start()
    window.deiconify()
    window.after(150, poll)
    window.mainloop()


if __name__ == '__main__':
    main()
