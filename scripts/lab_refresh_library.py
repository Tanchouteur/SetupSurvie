#!/usr/bin/env python3
"""Refresh only the lab's stateless library services, preserving all mounted data."""
import shutil
import linux_lab as lab
import setup


def refresh():
    lab.checked_mount()
    app=setup.Installation(lab.MOUNT/'private');c=app.load()
    app.catalog(c)
    for folder in ('pilot','portal'):
        shutil.copytree(setup.ROOT/folder,lab.MOUNT/'runtime'/folder,dirs_exist_ok=True)
    policy=lab.MOUNT/'runtime/deploy/assistant-system.fr.txt'
    policy.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(setup.ROOT/'deploy/assistant-system.fr.txt',policy)
    shutil.copyfile(setup.ROOT/'deploy/kiwix-themes.json',policy.parent/'kiwix-themes.json')
    for name in ('kiwix','pilot'):
        # Rootless Podman can report a stale monitor on the first stop after
        # a parent service exits. Retry before touching the stateless container.
        for _ in range(2):
            stopped=lab.podman('stop','-t','10',lab.PREFIX+name,capture=True,check=False)
            if stopped.returncode==0:break
        if stopped.returncode:raise setup.SetupError('Arrêt du service impossible : '+name)
        lab.podman('rm',lab.PREFIX+name,capture=True)
        common=['run','-d','--pull=never','--name',lab.PREFIX+name,
                '--label','project=setupsurvie-lab','--security-opt=label=disable',
                '--log-driver=k8s-file','--log-opt=max-size=10mb',
                f'--log-opt=path={lab.MOUNT}/logs/{name}.log',
                '--network','setupsurvie-lab','--network-alias',name]
        if name=='kiwix':
            args=['-p',f'{c["bind"]}:8081:8080','-v',f'{lab.MOUNT}/runtime/deploy/kiwix-entrypoint.sh:/config/kiwix-entrypoint.sh:ro',
                  '-v',f'{lab.MOUNT}/data/library/zim:/data:ro','--memory=1g','--entrypoint','/bin/sh',
                  lab.reference('kiwix'),'/config/kiwix-entrypoint.sh']
        else:
            args=['--env-file',str(lab.MOUNT/'private/pilot.env'),'--workdir','/srv','--memory=2g']
            mounts=[('runtime/pilot','/srv/pilot:ro'),('runtime/deploy/assistant-system.fr.txt','/srv/system.fr.txt:ro'),
                    ('runtime/deploy/model-profiles.json','/srv/model-profiles.json:ro'),('runtime/deploy/kiwix-themes.json','/srv/kiwix-themes.json:ro'),('data/state/pilot','/pilot-data'),
                    ('data/state/openwebui','/webui-data:ro'),('data/library/zim','/zim:ro'),('data/models','/models:ro'),
                    ('data/catalog','/catalog:ro'),('data/library/guides','/guides'),('data/library/maps','/maps:ro')]
            for source,target in mounts:args+=['-v',str(lab.MOUNT/source)+':'+target]
            args+=['--entrypoint','python',lab.reference('open-webui'),'-m','uvicorn','pilot.app:app','--host','0.0.0.0','--port','8000','--timeout-graceful-shutdown','5']
        lab.podman(*common,*args,capture=True)
        print('Actualisé :',name,flush=True)
    # A library-only recovery may follow a reboot, when containers survived but
    # the host-side controller did not. Restore controls without starting Ollama.
    import routing_prepare
    if (lab.MOUNT/'data/library/maps/routing/current/manifest.json').is_file():routing_prepare.start_services(app,c,'lab')
    import control
    control.start(app,c,'lab')
    # Refresh shared policies too, without starting Ollama or loading a model.
    configured=lab.podman('exec',lab.PREFIX+'pilot','python','-m','pilot.configure',capture=True,check=False)
    if configured.returncode:
        print('Profils Open WebUI non actualisés : relancer cette commande lorsque le service est disponible.',flush=True)


if __name__=='__main__':refresh()
