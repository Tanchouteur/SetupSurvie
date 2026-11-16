#!/usr/bin/env python3
"""Local desktop entry point: works without the portal or a web server."""
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import setup
import transfer


def discover(base):
    """Only documented adjacent locations; never scan unrelated user directories."""
    candidates=[base/'private',base/'prive',base/'.local',base/'application/.local',base/'moteur/.local']
    candidates += [setup.ROOT/'.local',setup.ROOT.parent/'prive']
    result=[]
    for path in candidates:
        if (path/'settings.json').is_file() and path.resolve() not in result:result.append(path.resolve())
    return result


class Wizard:
    def __init__(self, base, work=None):
        self.root=tk.Tk();self.root.title('Transférer SetupSurvie');self.root.geometry('760x660')
        self.base=base;self.events=queue.Queue();self.busy=False
        candidates=discover(base)
        if not work and (base/'transfer.json').is_file():
            source=Path(transfer.read(base/'transfer.json')['source']['private'])
            if (source/'settings.json').is_file():work=source
        self.work=tk.StringVar(value=str(work or (candidates[0] if len(candidates)==1 else '')))
        self.dest=tk.StringVar(value=str(base) if (base/'transfer.json').is_file() else '')
        panel=ttk.Frame(self.root,padding=20);panel.pack(fill='both',expand=True)
        ttk.Label(panel,text='Transférer SetupSurvie',font=('',20)).pack(anchor='w')
        ttk.Label(panel,text='Copier vers un SSD ou un disque de secours. La source est conservée.',wraplength=700).pack(anchor='w',pady=8)
        for label,var,callback in [('Installation source (dossier privé)',self.work,self.choose_source),('Nouveau dossier destination',self.dest,self.choose_dest)]:
            ttk.Label(panel,text=label).pack(anchor='w',pady=(8,2))
            row=ttk.Frame(panel);row.pack(fill='x');ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
            ttk.Button(row,text='Choisir…',command=callback).pack(side='left')
        self.actions=[]
        row=ttk.Frame(panel);row.pack(fill='x',pady=12)
        for label,callback in [('1. Examiner',self.examine),('2. Copier / reprendre',self.copy),('3. Préparer',lambda:self.destination_action(transfer.prepare)),('4. Activer',self.activate)]:
            button=ttk.Button(row,text=label,command=callback);button.pack(side='left',padx=2);self.actions.append(button)
        row=ttk.Frame(panel);row.pack(fill='x')
        for label,callback in [('Vérifier la copie',lambda:self.destination_action(transfer.verify_copy)),('Retour à la source',self.rollback),('Ouvrir le rapport',self.report)]:
            button=ttk.Button(row,text=label,command=callback);button.pack(side='left',padx=2);self.actions.append(button)
        self.status=tk.StringVar(value='Commencez par Examiner. Une destination existante ne sera pas remplacée.')
        ttk.Label(panel,textvariable=self.status,wraplength=700).pack(anchor='w',pady=12)
        self.bar=ttk.Progressbar(panel,mode='determinate');self.bar.pack(fill='x')
        self.log=tk.Text(panel,wrap='word',height=12,state='disabled');self.log.pack(fill='both',expand=True,pady=10)
        ttk.Label(panel,text='Sans Internet : Python avec Tk et Docker doivent être disponibles.\nDocker Desktop : vérifier séparément Settings → Resources → Advanced → Disk image location.',wraplength=700).pack(anchor='w')
        self.root.report_callback_exception=lambda cls,exc,tb:messagebox.showerror('Vérifier les choix',str(exc))
        self.root.protocol('WM_DELETE_WINDOW',self.close);self.root.after(150,self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('Opération en cours','Laissez cette fenêtre ouverte. En cas d’arrêt du PC, relancez le même transfert pour reprendre.');return
        self.root.destroy()

    def choose_source(self):
        path=filedialog.askdirectory(title='Dossier privé contenant settings.json')
        if path:self.work.set(path)

    def choose_dest(self):
        path=filedialog.askdirectory(title='Choisir le disque ou dossier parent')
        if path:self.dest.set(str(Path(path)/'SetupSurvie-SSD'))

    def destination(self):
        if not self.dest.get().strip():raise setup.SetupError('Choisissez la destination.')
        return setup.safe_path(self.dest.get())

    def app(self):
        if not self.work.get().strip():raise setup.SetupError('Choisissez le dossier privé de votre installation.')
        return setup.Installation(self.work.get())

    def append(self,text):
        self.log.configure(state='normal');self.log.insert('end',text+'\n');self.log.see('end');self.log.configure(state='disabled')

    def launch(self, action):
        if self.busy:return
        self.busy=True
        self.status.set('Opération en cours ; vérification des fichiers. Sur un gros disque, cela peut durer longtemps.')
        for button in self.actions:button.configure(state='disabled')
        # Read Tk variables only in the UI thread. Worker actions use frozen values.
        work=self.work.get();dest=self.dest.get()
        self.current_work=work;self.current_dest=dest
        def run():
            try:action();self.events.put(('done','Étape terminée. Consultez le rapport et les étapes restantes.'))
            except Exception as exc:
                import tempfile,traceback
                with tempfile.NamedTemporaryFile(prefix='setupsurvie-transfert-',suffix='.log',delete=False,mode='w',encoding='utf-8') as stream:traceback.print_exc(file=stream)
                # SetupError from Docker may include stderr. Never show raw subprocess output.
                detail=str(exc) if isinstance(exc,setup.SetupError) and not str(exc).startswith(('Échec de','Délai dépassé')) else 'Opération interrompue ; la copie reste non validée.'
                self.events.put(('error',detail+'\nDiagnostic privé : '+stream.name))
        threading.Thread(target=run,daemon=True).start()

    def destination_action(self,action):
        dest=self.destination()
        self.launch(lambda:action(dest))

    def examine(self):
        app=self.app();dest=self.destination()
        def action():
            report=transfer.plan(app,dest)
            gib=1024**3
            self.events.put(('text',f"Données et logiciel : {report['bytes']/gib:.2f} Gio. Libre : {report['free_bytes']/gib:.2f} Gio. Ajouter les images Docker et 256 Mio de marge.\nLe besoin exact est contrôlé avant l’arrêt. La copie peut prendre plusieurs heures.\nMême PC : conserver Docker et Python. Autre Windows : prérequis système à fournir séparément. Linux : conversion non qualifiée.\nLes téléchargements incomplets sont conservés, pas déclarés disponibles.\nVérifiez le disque physique et le format NTFS (Windows) : aucun formatage automatique."))
        self.launch(action)

    def copy(self):
        app=self.app();dest=self.destination()
        if not messagebox.askyesno('Copier et arrêter la source','Cette étape arrête seulement SetupSurvie et empêche son redémarrage automatique.\n\nLa source reste conservée jusqu’au retour explicite. Le disque Docker n’est pas déplacé. Continuer ?'):return
        self.launch(lambda:transfer.transfer(app,dest,progress=lambda phase,n,total:self.events.put(('progress',(phase,n,total)))))

    def activate(self):
        dest=self.destination()
        if not messagebox.askyesno('Activer la destination','Démarrer les services depuis la destination et recréer les raccourcis ?\n\nLa source restera bloquée. Aucun essai IA ne sera lancé. Sur un autre PC, les prérequis doivent déjà être installés.'):return
        self.launch(lambda:transfer.activate(dest))

    def rollback(self):
        dest=self.destination()
        if not messagebox.askyesno('Retour à la source','Arrêter la destination et débloquer la source ?\n\nLes données nouvelles sur le SSD restent sur le SSD et ne sont pas fusionnées. Utilisez ensuite le raccourci de la source.'):return
        self.launch(lambda:transfer.rollback(dest))

    def report(self):
        path=self.destination()/'Rapport-transfert.json'
        if not path.is_file():messagebox.showinfo('Rapport','Le rapport sera créé pendant la copie.');return
        self.append(json.dumps(transfer.read(path),ensure_ascii=False,indent=2))

    def poll(self):
        # Coalesce progress: hashing/copying can enqueue many updates.
        latest=None
        while True:
            try:kind,value=self.events.get_nowait()
            except queue.Empty:break
            if kind=='progress':latest=value
            elif kind=='text':self.append(value)
            else:
                self.busy=False
                for button in self.actions:button.configure(state='normal')
                self.status.set(value);self.append(value)
                if kind=='error':messagebox.showerror('Transfert interrompu',value)
        if latest:
            phase,n,total=latest;self.status.set(phase);self.bar['value']=100*n/max(total,1)
        self.root.after(150,self.poll)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default=str(setup.ROOT.parent));parser.add_argument('--work-dir')
    args=parser.parse_args();Wizard(setup.safe_path(args.base),args.work_dir).root.mainloop()


if __name__=='__main__':main()
