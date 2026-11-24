import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import index_reader_probe  # noqa: E402
import linux_host  # noqa: E402
import setup  # noqa: E402


class LinuxHostTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def fake_proc(self, *arguments):
        proc = self.root / 'proc'
        (proc / 'self').mkdir(parents=True)
        for number, args in enumerate(arguments, 100):
            (proc / str(number)).mkdir()
            (proc / str(number) / 'cmdline').write_bytes(b'\0'.join(a.encode() for a in args) + b'\0')
        return proc

    @unittest.skipUnless(sys.platform == "linux", "Chemins natifs de RootlessKit ou systemd sous Linux.")
    def test_socket_and_rootlesskit_detection(self):
        socket, custom = linux_host.docker_socket({'DOCKER_HOST': 'unix:///run/user/1000/essai/docker.sock'})
        self.assertTrue(custom)
        proc = self.fake_proc(['/usr/bin/rootlesskit', '--state-dir=/run/user/1000/autre/dockerd-rootless', '--disable-host-loopback'],
                              ['/usr/bin/rootlesskit', '--state-dir=/run/user/1000/essai/dockerd-rootless', '--net=pasta'])
        self.assertNotIn('--disable-host-loopback', linux_host.rootlesskit_arguments(socket, proc))
        self.assertIsNone(linux_host.rootlesskit_arguments(Path('/ailleurs/docker.sock'), proc))

    @unittest.skipUnless(sys.platform == "linux", "Chemins natifs de RootlessKit ou systemd sous Linux.")
    def test_loopback_disabled_on_custom_daemon_explains_the_remedy(self):
        proc = self.fake_proc(['rootlesskit', '--state-dir=/run/user/1000/essai/dockerd-rootless', '--disable-host-loopback'])
        with mock.patch.dict(os.environ, {'DOCKER_HOST': 'unix:///run/user/1000/essai/docker.sock'}):
            with self.assertRaisesRegex(setup.SetupError, linux_host.LOOPBACK_ENV):
                linux_host.ensure_host_loopback(proc)

    @unittest.skipUnless(sys.platform == "linux", "Chemins natifs de RootlessKit ou systemd sous Linux.")
    def test_loopback_disabled_on_user_service_is_reconfigured(self):
        proc = self.fake_proc(['rootlesskit', '--state-dir=/run/user/1000/dockerd-rootless', '--disable-host-loopback'])
        config = self.root / 'config'
        (config / 'systemd/user').mkdir(parents=True)
        (config / 'systemd/user/docker.service').write_text('[Service]\n')
        calls = []
        with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': str(config), 'XDG_RUNTIME_DIR': '/run/user/1000'}, clear=False), \
                mock.patch.dict(os.environ, {}, clear=False) as environ, \
                mock.patch.object(linux_host, 'systemctl', side_effect=lambda *a, **k: calls.append(a)), \
                mock.patch.object(linux_host, 'docker_rootless', return_value=True):
            environ.pop('DOCKER_HOST', None)
            status = linux_host.ensure_host_loopback(proc)
        dropin = config / 'systemd/user/docker.service.d/setupsurvie-host-loopback.conf'
        self.assertIn(linux_host.LOOPBACK_ENV + '=false', dropin.read_text())
        self.assertIn(('restart', 'docker.service'), calls)
        self.assertIn('reconfiguré', status)

    @unittest.skipUnless(sys.platform == "linux", "Chemins natifs de RootlessKit ou systemd sous Linux.")
    def test_unit_keeps_docker_host_and_runs_up_and_down(self):
        app = mock.Mock(work=Path('/srv/essai/prive'))
        with mock.patch('shutil.which', return_value='/home/louis/bin/docker'):
            text = linux_host.unit_text(app, {'project': 'survie-abc'},
                                        {'PATH': '/home/louis/bin', 'DOCKER_HOST': 'unix:///run/user/1000/essai/docker.sock',
                                         'DOCKER_CONFIG': '/srv/Outils SetupSurvie/docker-cli'})
        self.assertIn('Environment="DOCKER_HOST=unix:///run/user/1000/essai/docker.sock"', text)
        self.assertIn('Environment="PATH=/home/louis/bin:', text)
        self.assertIn('Environment="DOCKER_CONFIG=/srv/Outils SetupSurvie/docker-cli"', text)
        self.assertIn('--work-dir "/srv/essai/prive" up', text)
        self.assertIn('--work-dir "/srv/essai/prive" down', text)
        self.assertIn('RemainAfterExit=yes', text)
        self.assertIn('Type=oneshot', text)
        self.assertIn('Restart=on-failure', text)
        self.assertIn('RestartSec=15', text)
        self.assertIn('StartLimitIntervalSec=0', text)
        self.assertEqual(linux_host.unit_name({'project': 'survie-abc'}), 'setupsurvie-survie-abc.service')

    def test_unit_quotes_special_characters_in_arguments_and_environment(self):
        root = Path('/srv/dépôt "test" \\ % $HOME')
        work = Path('/srv/travail "test" \\ % $HOME')
        docker = '/home/bin "test" \\ % $HOME/docker'
        host = 'unix:///run/socket "test" \\ % $HOME'
        with mock.patch.object(setup, 'ROOT', root), mock.patch('shutil.which', return_value=docker):
            text = linux_host.unit_text(mock.Mock(work=work), {}, {'PATH': '/ignored', 'DOCKER_HOST': host})
        values = dict(line.split('=', 1) for line in text.splitlines() if '=' in line)
        for directive, action in [('ExecStart', 'up'), ('ExecStop', 'down')]:
            words = shlex.split(values[directive])
            words = [word.replace('%%', '%').replace('$$', '$') for word in words]
            self.assertEqual(words, [str(root / 'scripts/survie.sh'), '--work-dir', str(work), action])
        environments = [shlex.split(line.split('=', 1)[1])[0].replace('%%', '%')
                        for line in text.splitlines() if line.startswith('Environment=')]
        self.assertEqual(environments, ['PATH=' + str(Path(docker).parent) + ':/usr/local/bin:/usr/bin:/bin',
                                        'DOCKER_HOST=' + host])

    def test_unit_rejects_control_characters(self):
        with mock.patch('shutil.which', return_value='/usr/bin/docker'):
            for value in ('/tmp/a\nb', '/tmp/a\rb', '/tmp/a\x00b'):
                with self.subTest(value=value), self.assertRaises(setup.SetupError):
                    linux_host.unit_text(mock.Mock(work=value), {}, {})
                with self.subTest(host=value), self.assertRaises(setup.SetupError):
                    linux_host.unit_text(mock.Mock(work='/tmp'), {}, {'DOCKER_HOST': value})

    def test_install_wrapper_accepts_a_private_directory_with_spaces(self):
        if sys.platform != 'linux':
            self.skipTest('Lanceur Bash sous Linux.')
        private = self.root / 'Réglages privés'
        data = self.root / 'Données locales'
        result = subprocess.run(
            ['bash', str(ROOT / 'scripts/install.sh'), '--work-dir', str(private),
             '--data-dir', str(data), '--offline', '--content-pack', 'health'],
            capture_output=True, encoding='utf-8', timeout=20,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('Choisir le kit hors ligne', result.stderr)
        self.assertFalse(private.exists())
        self.assertFalse(data.exists())

    def test_install_rejects_unknown_pack_without_creating_directories(self):
        private = self.root / 'private'
        data = self.root / 'data'
        with self.assertRaisesRegex(setup.SetupError, 'Lots inconnus : absent'):
            setup.main(['--work-dir', str(private), 'install', '--target', 'linux',
                        '--data-dir', str(data), '--content-pack', 'absent'])
        self.assertFalse(private.exists())
        self.assertFalse(data.exists())

    def test_install_preserves_global_work_dir(self):
        args = setup.parser().parse_args(
            ['--work-dir', str(self.root), 'install', '--target', 'linux'])
        self.assertEqual(args.work_dir, str(self.root))

    def test_offline_installers_match_the_installation_python_minor(self):
        import linux_offline_tools
        version = mock.Mock(major=3, minor=13)
        with mock.patch.object(linux_offline_tools.platform, 'machine', return_value='x86_64'), \
                mock.patch.object(linux_offline_tools.sys, 'version_info', version), \
                mock.patch.object(linux_offline_tools.content, 'check_capacity'), \
                mock.patch.object(linux_offline_tools.content, 'transfer') as download:
            self.assertTrue(linux_offline_tools.prepare(self.root))
        names = [call.args[1]['id'] for call in download.call_args_list]
        self.assertEqual(names[:3], ['docker.tar.gz', 'docker-compose', 'python-3.13.tar.gz'])
        self.assertTrue(any(name.startswith('nftables_') for name in names[3:]))
        self.assertTrue(all(name.endswith('.deb') for name in names[3:]))
        receipt = self.root / linux_offline_tools.FOLDER / 'python-archive.txt'
        self.assertEqual(receipt.read_text(), 'python-3.13.tar.gz\n')

    @unittest.skipUnless(sys.platform == 'linux' and os.uname().machine == 'x86_64',
                         'Bootstrap Bash pour Linux x86-64.')
    def test_offline_bootstrap_refuses_a_tampered_archive_before_installing(self):
        import linux_offline_tools
        cache = self.root / linux_offline_tools.FOLDER
        cache.mkdir(parents=True)
        (cache / 'python-archive.txt').write_text('python-3.13.tar.gz\n')
        (cache / 'docker.tar.gz').write_bytes(b'archive alteree')
        target = self.root / 'Outils restaurés'
        result = subprocess.run(
            ['bash', str(ROOT / 'scripts/installer-outils-linux-hors-ligne.sh'),
             str(self.root), str(target)], capture_output=True, encoding='utf-8', timeout=20)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Empreinte incorrecte', result.stderr)
        self.assertFalse(target.exists())

    def test_reader_version_follows_python(self):
        self.assertEqual(index_reader_probe.expected_version((3, 14, 2)), '3.13.1')
        self.assertEqual(index_reader_probe.expected_version((3, 15, 2)), '4.1.0')

    def test_rootless_gateway_and_controller_address(self):
        import control
        app = setup.Installation(str(self.root / 'prive'))
        c = app.init('linux', str(self.root / 'donnees'), False, True)
        self.assertIn("HOST_GATEWAY='host-gateway'", app.env_path.read_text())
        c['docker_rootless'] = True
        app.render(c)
        self.assertIn("HOST_GATEWAY='10.0.2.2'", app.env_path.read_text())
        with mock.patch.object(control.ThreadingHTTPServer, '__init__', return_value=None) as init, \
                mock.patch.object(control.library_tasks, 'Manager'):
            control.Server(app, c, 'compose')
            self.assertEqual(init.call_args.args[0], ('127.0.0.1', 11436))
            control.Server(app, {**c, 'docker_rootless': False}, 'compose')
            self.assertEqual(init.call_args.args[0], ('0.0.0.0', 11436))
            with mock.patch.dict(os.environ, {'SURVIE_SYSTEM_DOCKER_GATEWAY': '172.29.0.1'}):
                control.Server(app, {**c, 'docker_rootless': False}, 'compose')
            self.assertEqual(init.call_args.args[0], ('172.29.0.1', 11436))
            # A second installation on the same PC chooses its own port; an
            # invalid value keeps the default instead of failing to start.
            control.Server(app, {**c, 'docker_rootless': False, 'control_port': 21436}, 'lab')
            self.assertEqual(init.call_args.args[0], ('0.0.0.0', 21436))
            self.assertEqual(control.control_port({'control_port': 'x'}), 11436)
            self.assertEqual(control.control_port({'control_port': 80}), 11436)
        import linux_lab
        with mock.patch.object(setup, 'control_key', return_value='fixture'):
            env = linux_lab.container_specifications({**c, 'bind': '127.0.0.1', 'secret': 's', 'admin_email': 'a', 'admin_password': 'p', 'control_port': 21436})['pilot'][1]
        self.assertEqual(env['PILOT_CONTROL_URL'], 'http://host.containers.internal:21436')


if __name__ == '__main__':
    unittest.main()
