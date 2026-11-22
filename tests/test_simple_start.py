"""Start einer Python-Datei oder einer reinen Grafikwerkstatt – ohne Startkonfiguration."""
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class SimpleStartTests(unittest.TestCase):
    def launch(self, tool, target, address):
        command = (['java', 'server-java/ArcadeServer.java'] if tool == 'java'
                   else ['python3', 'server.py']) + [str(target), '--port', str(address)]
        log = tempfile.TemporaryFile()
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        self.addCleanup(log.close)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        for _ in range(180):
            if process.poll() is not None:
                log.seek(0)
                raise AssertionError(log.read().decode(errors='replace'))
            try:
                with urlopen(f'http://127.0.0.1:{address}/health', timeout=.25) as reply:
                    if reply.status == 200:
                        return process
            except (OSError, URLError):
                pass
            time.sleep(.1)
        raise AssertionError('Server did not start')

    @unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'JDK fehlt')
    def test_python_program_and_editor_only_on_both_servers(self):
        for server in ('java', 'python'):
            with self.subTest(server=server), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                folder = root / 'frisches-projekt'
                address = port()
                process = self.launch(server, folder, address)
                self.assertTrue(folder.is_dir())
                with urlopen(f'http://127.0.0.1:{address}/') as r:
                    self.assertEqual(r.url, f'http://127.0.0.1:{address}/editor')
                    self.assertIn('Spielwerkstatt', r.read().decode())
                with urlopen(f'http://127.0.0.1:{address}/editor/api/design') as r:
                    self.assertIn(b'"templates":[]', r.read())
                process.terminate(); process.wait(timeout=8)
                shutil.copytree(ROOT / 'games/python_demo', root/'python_demo')
                main = root/'python_demo/Hallo.py'
                address = port()
                process = self.launch(server, main, address)
                with urlopen(f'http://127.0.0.1:{address}/') as r:
                    self.assertIn('Python', r.read().decode())
                with urlopen(f'http://127.0.0.1:{address}/events', timeout=15) as r:
                    data=b''
                    for _ in range(50):
                        data += r.readline()
                        if b'CREATE kugel farbkugel' in data: break
                    self.assertIn(b'CREATE kugel farbkugel', data)
                    with urlopen(Request(f'http://127.0.0.1:{address}/input',data=b'KEYDOWN ArrowRight',method='POST'),timeout=5) as reply:
                        self.assertEqual(reply.status,200)
                    moved=b''
                    for _ in range(60):
                        moved += r.readline()
                        if b'MOVE kugel 110 120' in moved: break
                    self.assertIn(b'MOVE kugel 110 120', moved)
                process.terminate(); process.wait(timeout=8)
