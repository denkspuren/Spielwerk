"""Integrationstest für beide Servervarianten, kein Browserautomationspaket nötig."""
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def eventually(test, seconds=12):
    limit = time.monotonic() + seconds
    while time.monotonic() < limit:
        if test():
            return True
        time.sleep(.1)
    return False


def next_event(stream):
    """Read one whole SSE event; support multi-line compiler diagnostics."""
    kind = None
    data = []
    while True:
        row = stream.readline().decode('utf-8').rstrip('\r\n')
        if row.startswith('event: '):
            kind = row[7:]
        elif row.startswith('data: '):
            data.append(row[6:])
        elif not row:
            if kind:
                return kind, '\n'.join(data)
        if not row and not kind:
            raise EOFError('SSE disconnected')


class ServerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = tempfile.TemporaryFile()
        self.addCleanup(self.log.close)
        self.proc = None
        self.port = free_port()
        self.base = f'http://127.0.0.1:{self.port}'
        self.addCleanup(self.terminate)

    def terminate(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)

    def start(self, game, server='java'):
        game_path = ROOT / 'games' / game
        dst = Path(self.tmp.name) / game
        shutil.copytree(game_path, dst)
        main = dst / ('Sokoban.java' if game == 'sokoban' else 'SpaceInvaders.java')
        if server == 'java':
            command = ['java', 'server-java/ArcadeServer.java', str(main), '--port', str(self.port)]
        else:
            command = ['python3', 'server.py', str(main), '--port', str(self.port)]
        self.proc = subprocess.Popen(command, cwd=ROOT, stdout=self.log,
                                     stderr=subprocess.STDOUT)
        def healthy():
            if self.proc.poll() is not None:
                self.log.seek(0)
                raise AssertionError(f'Server ended: {self.log.read().decode(errors="replace")}')
            try:
                with urlopen(self.base + '/health', timeout=.4) as response:
                    return response.read() == b'OK\n'
            except (URLError, TimeoutError, OSError):
                return False
        self.assertTrue(eventually(healthy, 15), 'Server did not become healthy')
        return main

    def post(self, path, data=b'', headers=None):
        return urlopen(Request(self.base + path, method='POST', data=data,
                               headers=headers or {}), timeout=6)

    @unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'Java JDK fehlt')
    def test_java_sokoban_sse_compile_recovery_and_shutdown(self):
        main = self.start('sokoban')
        with urlopen(self.base + '/') as response:
            html = response.read().decode('utf-8')
            self.assertIn('Sokoban', html)
            self.assertIn('id="shutdown"', html)
            self.assertIn('Tick-Intervall: 0 ms', html)
        with urlopen(self.base + '/game/scene.html') as response:
            self.assertIn(b'template id="crate"', response.read())
        with urlopen(self.base + '/static/app.js') as response:
            self.assertIn(b'/shutdown', response.read())
        with urlopen(self.base + '/events', timeout=12) as sse:
            kinds = []
            for _ in range(150):
                event = next_event(sse)
                kinds.append(event)
                if event == ('cmd', 'CREATE player hero'):
                    break
            self.assertIn(('cmd', 'CREATE player hero'), kinds)
            with self.post('/input', b'KEYDOWN ArrowUp') as response:
                self.assertEqual(response.status, 200)
            found_move = False
            for _ in range(100):
                kind, data = next_event(sse)
                if kind == 'cmd' and data == 'TEXT moves Züge: 1':
                    found_move = True
                    break
            self.assertTrue(found_move, 'Sokoban keydown not processed')
            main.write_text('public class Sokoban { this is not Java! }', encoding='utf-8')
            found_error = False
            for _ in range(150):
                kind, data = next_event(sse)
                if kind == 'compile' and 'error:' in data:
                    found_error = True
                    break
            self.assertTrue(found_error, 'Compiler diagnostics not sent through SSE')
            main.write_text((ROOT / 'games/sokoban/Sokoban.java').read_text(encoding='utf-8'),
                            encoding='utf-8')
            found_running = False
            for _ in range(150):
                kind, data = next_event(sse)
                if kind == 'status' and data.startswith('RUNNING\t'):
                    found_running = True
                    break
            self.assertTrue(found_running, 'No recovery after correcting Java')
        with self.assertRaises(HTTPError) as err:
            self.post('/shutdown')
        self.assertEqual(err.exception.code, 403)
        with self.assertRaises(HTTPError) as err:
            self.post('/shutdown', headers={'X-Arcade-Action': 'shutdown',
                                            'Origin': 'https://evil.example'})
        self.assertEqual(err.exception.code, 403)
        # Auch mit noch offener Browser-SSE-Verbindung muss der Server enden.
        ongoing_sse = urlopen(self.base + '/events', timeout=8)
        next_event(ongoing_sse)
        try:
            with self.post('/shutdown', headers={'X-Arcade-Action': 'shutdown'}) as response:
                self.assertEqual(response.status, 200)
            self.assertTrue(eventually(lambda: self.proc.poll() is not None, 9),
                            'Java server did not exit after shutdown')
        finally:
            ongoing_sse.close()

    @unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'Java JDK fehlt')
    def test_java_space_invaders_ticks(self):
        self.start('space_invaders')
        with urlopen(self.base + '/events', timeout=12) as sse:
            first = None
            moved = False
            for _ in range(300):
                kind, value = next_event(sse)
                if kind == 'cmd' and value.startswith('MOVE alien_0_0 '):
                    if first is None:
                        first = value
                    elif value != first:
                        moved = True
                        break
            self.assertTrue(moved, 'No alien movement from tick scheduler')
        with self.post('/shutdown', headers={'X-Arcade-Action': 'shutdown'}):
            pass
        self.assertTrue(eventually(lambda: self.proc.poll() is not None, 9))

    @unittest.skipUnless(shutil.which('python3') and shutil.which('java') and
                         shutil.which('javac'), 'Python/JDK fehlen')
    def test_python_shutdown(self):
        self.start('sokoban', server='python')
        with self.assertRaises(HTTPError) as err:
            self.post('/shutdown')
        self.assertEqual(err.exception.code, 403)
        ongoing_sse = urlopen(self.base + '/events', timeout=8)
        next_event(ongoing_sse)
        try:
            with self.post('/shutdown', headers={'X-Arcade-Action': 'shutdown'}) as response:
                self.assertEqual(response.status, 200)
            self.assertTrue(eventually(lambda: self.proc.poll() is not None, 8),
                            'Python server did not exit after shutdown')
        finally:
            ongoing_sse.close()


if __name__ == '__main__':
    unittest.main()
