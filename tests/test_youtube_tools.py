"""yt-dlp, Deno and FFmpeg preparation with fake wheels/archives: no network."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import youtube_tools as tools  # noqa: E402
import setup  # noqa: E402

VERSION='2026.10.26'


def offline_opener(*args,**kwargs):raise AssertionError('Aucun accès réseau attendu')


class PinnedFilesTests(unittest.TestCase):
    def test_real_manifest_and_requirements_are_consistent(self):
        manifest=tools.manifest();pinned=tools.pinned()
        self.assertEqual(pinned['yt-dlp'],manifest['yt_dlp']['version'])
        for name in ('yt-dlp','yt-dlp-ejs','deno','certifi','requests','urllib3','websockets','brotli','pycryptodomex','mutagen','idna','charset-normalizer'):
            self.assertIn(name,pinned)
        self.assertIn('LGPL',manifest['ffmpeg']['licence'])
        for system in ('windows','linux'):
            entry=manifest['ffmpeg'][system]
            self.assertRegex(entry['sha256'],r'^[0-9a-f]{64}$');self.assertGreater(entry['bytes'],10_000_000)
            self.assertTrue(entry['url'].startswith('https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-'))
            self.assertTrue(entry['url'].endswith('/'+entry['file']));self.assertIn('lgpl',entry['file'])
            self.assertIn(manifest['ffmpeg']['version'],entry['file'])


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.data=self.root/'data';self.data.mkdir()
        requirements=self.root/'requirements.txt';requirements.write_text('# test\nyt-dlp=='+VERSION+'\ndeno==2.9.8\n')
        self.system=tools.host();binary='ffmpeg.exe' if self.system=='windows' else 'ffmpeg'
        self.archive_bytes=self.make_archive()
        archive_name='ffmpeg-test-'+('win64-lgpl.zip' if self.system=='windows' else 'linux64-lgpl.tar.xz')
        entry={'file':archive_name,'url':'https://example.invalid/'+archive_name,'sha256':hashlib.sha256(self.archive_bytes).hexdigest(),'bytes':len(self.archive_bytes)}
        manifest=self.root/'manifest.json'
        manifest.write_text(json.dumps({'schema':1,'yt_dlp':{'version':VERSION},'ffmpeg':{'version':'n-test','licence':'LGPL','windows':entry,'linux':entry}}))
        self.bundled=self.root/'vendor-youtube'
        for key,value in [('MANIFEST',manifest),('REQUIREMENTS',requirements),('BUNDLED',self.bundled)]:
            p=patch.object(tools,key,value);p.start();self.addCleanup(p.stop)
        p=patch.object(tools.venv.EnvBuilder,'create',lambda builder,folder:self.fake_python(Path(folder)));p.start();self.addCleanup(p.stop)
        self.entry=entry;self.binary=binary;self.commands=[]

    def make_archive(self):
        payload={'ffmpeg-test/bin/ffmpeg':b'ff','ffmpeg-test/bin/ffprobe':b'fp','ffmpeg-test/bin/ffplay':b'no','ffmpeg-test/LICENSE.txt':b'LGPL','ffmpeg-test/doc/x.html':b'no'}
        buffer=io.BytesIO()
        if os.name=='nt':
            with zipfile.ZipFile(buffer,'w') as bundle:
                for name,body in payload.items():bundle.writestr(name.replace('bin/ffmpeg','bin/ffmpeg.exe').replace('bin/ffprobe','bin/ffprobe.exe'),body)
        else:
            with tarfile.open(fileobj=buffer,mode='w:xz') as bundle:
                for name,body in [*payload.items(),('../evil/bin/ffmpeg',b'evil')]:
                    info=tarfile.TarInfo(name);info.size=len(body);bundle.addfile(info,io.BytesIO(body))
        return buffer.getvalue()

    def fake_python(self,folder):
        python=folder/('Scripts/python.exe' if os.name=='nt' else 'bin/python');python.parent.mkdir(parents=True,exist_ok=True);python.write_text('')

    def wheels(self,folder):
        folder.mkdir(parents=True,exist_ok=True)
        for name in ('yt_dlp-'+VERSION+'-py3-none-any.whl','deno-2.9.8-py3-none-any.whl'):(folder/name).write_bytes(name.encode())

    def fake_run(self,args,**options):
        """Fake pip/yt-dlp: installation creates deno, --version answers if python exists."""
        args=[str(a) for a in args];self.commands.append(args)
        if 'download' in args:self.wheels(Path(args[args.index('--dest')+1]))
        if args[1:4]==['-m','pip','install'] and '--no-index' in args:
            scripts=Path(args[0]).parent;(scripts/('deno.exe' if os.name=='nt' else 'deno')).write_text('')
        if args[1:]==['-m','pip','--version']:
            return subprocess.CompletedProcess(args,0 if Path(args[0]).is_file() else 1,stdout='pip',stderr='')
        if args[-1]=='--version':
            ok=Path(args[0]).is_file()
            return subprocess.CompletedProcess(args,0 if ok else 1,stdout=VERSION+'\n' if ok else '',stderr='')
        return subprocess.CompletedProcess(args,0,stdout='',stderr='')

    def opener(self,url,timeout):
        self.assertEqual(url,self.entry['url']);return io.BytesIO(self.archive_bytes)

    def test_online_install_downloads_verifies_and_makes_all_three_ready(self):
        self.assertFalse(tools.status(self.data,run=self.fake_run)['ready'])
        self.assertTrue(tools.prepare(self.data,run=self.fake_run,opener=self.opener,log=lambda *_:None))
        state=tools.status(self.data,run=self.fake_run)
        self.assertEqual(state,{'yt_dlp':VERSION,'expected_yt_dlp':VERSION,'deno':True,'ffmpeg':True,'ready':True})
        folder=tools.paths(self.data)['ffmpeg']
        self.assertEqual(sorted(p.name for p in folder.iterdir()),sorted(['LICENSE.txt',self.binary,self.binary.replace('ffmpeg','ffprobe')]))
        if os.name!='nt':self.assertTrue(os.access(folder/'ffmpeg',os.X_OK))
        self.assertFalse((self.data/'tools'/'evil').exists())
        install=next(c for c in self.commands if c[1:4]==['-m','pip','install'])
        self.assertIn('--no-index',install);self.assertEqual(install[install.index('--find-links')+1],str(tools.paths(self.data)['wheels']))
        records=json.loads((tools.paths(self.data)['wheels']/'manifest.json').read_text())['files']
        self.assertEqual(len(records),2)
        # Already ready: nothing is redone.
        count=len(self.commands)
        self.assertTrue(tools.prepare(self.data,run=self.fake_run,opener=offline_opener))
        self.assertEqual([c for c in self.commands[count:] if 'install' in c],[])

    def test_offline_kit_install_uses_bundled_files_only(self):
        self.wheels(self.bundled/'wheels');tools.record_wheels(self.bundled/'wheels')
        (self.bundled/'ffmpeg').mkdir();(self.bundled/'ffmpeg'/self.entry['file']).write_bytes(self.archive_bytes)
        self.assertTrue(tools.prepare(self.data,offline=True,run=self.fake_run,opener=offline_opener))
        self.assertFalse([c for c in self.commands if 'download' in c])
        self.assertTrue(tools.ffmpeg(self.data))

    def test_copy_to_another_disk_rebuilds_the_environment_offline(self):
        tools.prepare(self.data,run=self.fake_run,opener=self.opener)
        copy=self.root/'autre-disque'/'data';shutil.copytree(self.data,copy)
        # The copied environment points to the source disk: simulate it broken.
        tools.python(copy).unlink()
        self.assertFalse(tools.status(copy,run=self.fake_run)['ready'])
        self.assertTrue(tools.ensure(copy,run=self.fake_run,opener=offline_opener,log=lambda *_:None))
        self.assertTrue(tools.status(copy,run=self.fake_run)['ready'])

    def test_tampered_cache_or_archive_is_refused(self):
        tools.prepare(self.data,run=self.fake_run,opener=self.opener)
        wheels=tools.paths(self.data)['wheels']
        (wheels/('deno-2.9.8-py3-none-any.whl')).write_bytes(b'altered')
        with self.assertRaises(setup.SetupError):tools.validate_wheels(wheels)
        (wheels/('deno-2.9.8-py3-none-any.whl')).write_bytes(b'deno-2.9.8-py3-none-any.whl')
        (wheels/'requests-2.0-py3-none-any.whl').write_bytes(b'x')
        with self.assertRaises(setup.SetupError):tools.validate_wheels(wheels)
        archive=tools.paths(self.data)['archives']/self.entry['file'];archive.write_bytes(self.archive_bytes[:-1]+b'!')
        with self.assertRaises(setup.SetupError):tools.extract_ffmpeg(self.data,archive)
        with self.assertRaises(setup.SetupError):tools.download_ffmpeg(self.root/'other',opener=lambda url,timeout:io.BytesIO(b'wrong'))
        self.assertFalse(list((self.root/'other').rglob('*.zip'))+list((self.root/'other').rglob('*.xz')))

    def test_cache_target_downloads_wheels_for_another_platform(self):
        tools.cache_target(self.data,'windows','3.13',run=self.fake_run,opener=self.opener)
        command=next(c for c in self.commands if 'download' in c)
        self.assertEqual(command[command.index('--platform')+1],'win_amd64');self.assertIn('cp313',command)
        self.assertIn('--only-binary=:all:',command)
        tools.cache_target(self.data,'linux','3.12',run=self.fake_run,opener=self.opener)
        command=[c for c in self.commands if 'download' in c][-1]
        self.assertIn('manylinux_2_27_x86_64',command)
        with self.assertRaises(setup.SetupError):tools.cache_target(self.data,'mac',run=self.fake_run)

    def test_installation_never_fails_because_of_this_optional_tool(self):
        output=[]
        with patch.object(tools,'prepare',side_effect=setup.SetupError('panne')),patch('builtins.print',lambda *a,**k:output.append(' '.join(map(str,a)))):
            setup.prepare_youtube_tools({'data_dir':str(self.data)},False)
        self.assertIn('premier téléchargement',output[0])

    def test_kit_export_lists_verified_files(self):
        import pilot_kit
        tools.prepare(self.data,run=self.fake_run,opener=self.opener)
        exported=[relative for _,relative in pilot_kit.youtube_vendor(self.data)]
        self.assertIn('app/vendor/youtube/wheels/manifest.json',exported)
        self.assertIn('app/vendor/youtube/ffmpeg/'+self.entry['file'],exported)
        self.assertTrue(any(re.match(r'app/vendor/youtube/wheels/yt_dlp-.*\.whl$',value) for value in exported))
        output=[]
        with patch.object(tools,'cache_target',side_effect=OSError('hors ligne')),patch('builtins.print',lambda *a,**k:output.append(' '.join(map(str,a)))):
            pilot_kit.complete_youtube_caches(self.data)
        self.assertIn('premier téléchargement',output[0])


if __name__=='__main__':unittest.main()
