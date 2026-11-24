"""Regression: optional Werkstatt assets must not cause requests in a plain game."""
from __future__ import annotations

import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class ResourcePresenceTests(unittest.TestCase):
    def _check_server(self, language: str):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory) / 'testspiel'
            game.mkdir()
            (game / 'Mini.java').write_text(
                'public class Mini { public static void main(String[] args) throws Exception {'
                ' while (System.in.read() != -1) {} } }', encoding='utf-8')
            (game / 'scene.html').write_text('<template id="dot"><div></div></template>', encoding='utf-8')
            (game / 'style.css').write_text('.game-object { position: absolute; }', encoding='utf-8')
            port = free_port()
            command = ([sys.executable, 'server.py'] if language == 'python' else
                       ['java', 'server-java/ArcadeServer.java'])
            command += [str(game / 'Mini.java'), '--port', str(port)]
            proc = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            try:
                base = f'http://127.0.0.1:{port}'
                for _ in range(180):
                    if proc.poll() is not None:
                        self.fail(f'{language}: server exited unexpectedly ({proc.returncode})')
                    try:
                        with urlopen(base + '/health', timeout=0.5) as response:
                            if response.read() == b'OK\n':
                                break
                    except (OSError, TimeoutError):
                        time.sleep(0.1)
                else:
                    self.fail(f'{language}: server did not become ready')

                with urlopen(base + '/', timeout=3) as response:
                    page = response.read().decode('utf-8')
                self.assertIn('data-workshop-templates="false"', page)
                self.assertIn('data-workshop-layout="false"', page)
                self.assertNotIn('href="/game/spielwerk/style.css"', page)
                self.assertNotIn('{{WORKSHOP_', page)

                # Creating optional files while server is running must enable them
                # on the next page load, without touching game source code.
                output = game / 'spielwerk'
                output.mkdir()
                (output / 'scene.html').write_text('<template id="sw-test"><div></div></template>', encoding='utf-8')
                (output / 'style.css').write_text('.sw-test { background: blue; }', encoding='utf-8')
                (output / 'layout.json').write_text(
                    '{"version":1,"width":640,"height":480,'
                    '"background":"#12243b","objects":[]}', encoding='utf-8')
                with urlopen(base + '/', timeout=3) as response:
                    page = response.read().decode('utf-8')
                self.assertIn('data-workshop-templates="true"', page)
                self.assertIn('data-workshop-layout="true"', page)
                self.assertIn('href="/game/spielwerk/style.css"', page)
                for asset in ('scene.html', 'style.css', 'layout.json'):
                    with urlopen(base + '/game/spielwerk/' + asset, timeout=3) as response:
                        self.assertEqual(response.status, 200)
            finally:
                if proc.poll() is None:
                    try:
                        req = Request(base + '/shutdown', b'', method='POST', headers={
                            'X-Arcade-Action': 'shutdown', 'Sec-Fetch-Site': 'same-origin'})
                        with urlopen(req, timeout=2):
                            pass
                    except (OSError, TimeoutError):
                        pass
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    proc.wait(timeout=4)

    @unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'JDK fehlt')
    def test_java_server(self):
        self._check_server('java')

    @unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'JDK fehlt')
    def test_python_server(self):
        self._check_server('python')

    def test_short_scripts_use_java_server(self):
        for name in ('space-invaders', 'sokoban', 'sternenpfad', 'balllabor', 'werkstatt'):
            with self.subTest(name=name):
                sh = (ROOT / f'start-{name}.sh').read_text()
                bat = (ROOT / f'start-{name}.bat').read_text()
                self.assertIn('java server-java/ArcadeServer.java', sh)
                self.assertIn('java server-java/ArcadeServer.java', bat)
                self.assertIn('python3 server.py', (ROOT / f'start-{name}-python-server.sh').read_text())
