"""Prepare a stable, opt-out Windows login launcher with real tool locations."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import setup
from delivery_paths import destination
from pilot import durable


def prepare(app,config,*,python=None,find=shutil.which):
    if config['target']!='windows' or not config.get('app_dir'):return None
    application=setup.safe_path(config['app_dir']);base=application.parent
    stable=destination(base,'maintenance')
    stable.mkdir(parents=True,exist_ok=True)
    previous=stable/'startup-settings.json'
    if previous.exists():
        saved=json.loads(previous.read_text(encoding='utf-8'))
        if saved.get('schema')!=1 or saved.get('kind')!='SetupSurvie managed Windows startup' or setup.safe_path(saved['work_dir'])!=app.work.resolve():
            raise setup.SetupError('Un autre démarrage utilise déjà ce dossier de maintenance.')
    executable=Path(python or sys.executable).resolve()
    paths=[str(executable.parent)]
    if (executable.parent/'Scripts').is_dir():paths.append(str(executable.parent/'Scripts'))
    for command in ('docker','ollama'):
        value=find(command)
        if value:paths.append(str(Path(value).resolve().parent))
    data=setup.safe_path(config['data_dir'])
    for relative,command in (('tools/Ollama','ollama.exe'),('tools/DockerDesktop/resources/bin','docker.exe')):
        folder=data/relative
        if (folder/command).is_file():paths.append(str(folder.resolve()))
    # Persist the discovered Docker Desktop location, including portable D: installs.
    docker=find('docker');desktop=None
    if not docker and (data/'tools/DockerDesktop/resources/bin/docker.exe').is_file():docker=str(data/'tools/DockerDesktop/resources/bin/docker.exe')
    if docker:
        candidate=Path(docker).resolve().parent.parent.parent/'Docker Desktop.exe'
        if candidate.is_file():desktop=str(candidate)
    state={'schema':1,'kind':'SetupSurvie managed Windows startup','work_dir':str(app.work.resolve()),
           'python':str(executable),'ollama':find('ollama') or (str(data/'tools/Ollama/ollama.exe') if (data/'tools/Ollama/ollama.exe').is_file() else None),'paths':list(dict.fromkeys(paths)),'desktop':desktop,
           'task_name':'SetupSurvie-Demarrage-'+hashlib.sha256(str(app.work.resolve()).casefold().encode()).hexdigest()[:8]}
    setup.write_json(previous,state,private=True)
    config={**config,'inference_autostart':False}
    setup.write_json(app.settings_path,config,private=True)
    for name in ('startup-windows.ps1','stop-windows.ps1','windows-common.ps1','register-startup-windows.ps1','content-monitor.ps1','windows_resume.py','register-windows-resume.ps1','start-without-inference.ps1'):
        origin=setup.ROOT/'scripts'/name;target=destination(stable,name)
        if origin.resolve()==target.resolve():continue
        temporary=target.with_name(target.name+'.pending')
        shutil.copyfile(origin,temporary);durable.sync_file(temporary);durable.publish(temporary,target)
    return stable/'startup-windows.ps1'
