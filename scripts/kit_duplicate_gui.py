"""Graphical entry point for copying an exported public kit."""
import os
import queue
import shutil
import subprocess
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from kit_duplicate import duplicate, verify_support
from pilot_backup import protected_backup, verify_backup
import setup


def check_backup(kit, backup, report):
    """Check a backup; on Linux, ask for administrator rights if it is root-only."""
    if not protected_backup(backup) or sys.platform != 'linux' or not shutil.which('pkexec'):
        return verify_backup(backup, kit, report=report)
    report('Sauvegarde protégée : autorisation administrateur demandée…')
    admin = Path(kit) / 'app/scripts/linux_recovery_admin.sh'
    result = subprocess.run(['pkexec', '--disable-internal-agent', '/bin/bash', str(admin), 'verify-backup',
                             str(kit), str(backup)], capture_output=True, text=True)
    if result.returncode != 0:
        lines = (result.stderr or result.stdout).strip().splitlines()
        raise setup.SetupError(lines[-1].removeprefix('ERREUR : ') if lines else 'Autorisation refusée : sauvegarde non vérifiée.')
    return '\n'.join(line for line in result.stdout.splitlines() if not line.startswith('Sauvegarde : '))


def main():
    source = setup.safe_path(sys.argv[1])
    window = tk.Tk()
    window.withdraw()
    checking = '--verify' in sys.argv[2:]
    title = 'Vérifier le kit SetupSurvie' if checking else 'Dupliquer le kit SetupSurvie'
    target = source
    window.title(title)
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill='both', expand=True)
    folder = ttk.Label(frame, text=str(source), wraplength=460)
    folder.pack(anchor='w')
    status = ttk.Label(frame, text='En attente de votre choix…', wraplength=460)
    status.pack(anchor='w', pady=10)
    progress = ttk.Progressbar(frame, mode='indeterminate', length=460)
    progress.pack(fill='x')
    windows = sys.platform == 'win32'
    if windows:
        # The hidden PowerShell launcher can lose the foreground after installing Python.
        # Map the owner above Explorer before opening the native modal dialogs.
        window.attributes('-topmost', True)
        window.deiconify()
        window.update_idletasks()
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

    folder.configure(text=str(target))
    status.configure(text='Contrôle du kit…')
    if windows:
        window.attributes('-topmost', False)
    progress.start()
    window.protocol('WM_DELETE_WINDOW', lambda: None)
    messages = queue.SimpleQueue()

    def copy():
        try:
            report = lambda line: messages.put(('progress', line))
            if checking:
                result = verify_support(source, report=report)
                if backup:
                    result += '\n\n' + check_backup(source, backup, report)
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
