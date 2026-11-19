"""Tests der Dokumentationsbeispiele, einschließlich echter Java-Server-Prozesse."""
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [('sternenpfad', 'Sternenpfad'), ('balllabor', 'Balllabor')]


def unused_port():
    with socket.socket(socket.AF_INET) as conn:
        conn.bind(('127.0.0.1', 0))
        return conn.getsockname()[1]


def read_sse(stream):
    kind = ''
    lines = []
    while True:
        line = stream.readline().decode('utf-8').rstrip('\r\n')
        if line.startswith('event: '):
            kind = line[7:]
        elif line.startswith('data: '):
            lines.append(line[6:])
        elif not line:
            if kind:
                return kind, '\n'.join(lines)
            raise EOFError('Server-SSE-Verbindung unerwartet beendet')


class StudentExamplesTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'JDK fehlt')
    def test_direct_java_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            for slug, classname in EXAMPLES:
                with self.subTest(game=slug):
                    source = ROOT / 'games' / slug / f'{classname}.java'
                    target = Path(tmp) / slug
                    target.mkdir()
                    subprocess.run(['javac', '-encoding', 'UTF-8', '-d', str(target), str(source)],
                                   check=True, capture_output=True, timeout=20)
                    proc = subprocess.run(['java', '-cp', str(target), classname],
                                          input=('KEYDOWN ArrowRight\n'
                                                 + ('TICK 33\n' if slug == 'balllabor' else '')
                                                 + 'KEYUP ArrowRight\n'
                                                 + 'KEYDOWN KeyR\nCLICK neu 550 360\n'
                                                 + 'CLICK neustart 550 360\n'),
                                          text=True, capture_output=True, timeout=8)
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    output = proc.stdout
                    if slug == 'sternenpfad':
                        self.assertIn('CREATE spieler roboter', output)
                        self.assertIn('MOVE spieler 136 272', output)
                        self.assertIn('TEXT punkte Sterne: 0 / 3', output)
                        self.assertNotIn('TICK ', output)
                    else:
                        self.assertIn('CREATE ball kugel', output)
                        self.assertIn('CREATE paddle schlaeger', output)
                        self.assertIn('MOVE paddle 282 344', output)
                    self.assertNotIn('Ungültige stdout-Zeile', proc.stderr)

    @unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'JDK fehlt')
    def test_servers_and_browser_resources(self):
        for server in ['java', 'python']:
            if server == 'python' and not shutil.which('python3'):
                continue
            for slug, classname in EXAMPLES:
                with self.subTest(server=server, game=slug):
                    port = unused_port()
                    gamefile = ROOT / 'games' / slug / f'{classname}.java'
                    args = (['java', 'server-java/ArcadeServer.java'] if server == 'java'
                            else ['python3', 'server.py']) + [str(gamefile), '--port', str(port)]
                    with tempfile.TemporaryFile() as logfile:
                        proc = subprocess.Popen(args, cwd=ROOT, stdout=logfile,
                                                stderr=subprocess.STDOUT)
                        base = f'http://127.0.0.1:{port}'
                        try:
                            for _ in range(160):
                                try:
                                    with urlopen(base + '/health', timeout=.2) as res:
                                        if res.read() == b'OK\n':
                                            break
                                except (URLError, OSError):
                                    if proc.poll() is not None:
                                        break
                                    time.sleep(.1)
                            else:
                                self.fail(f'{server}/{slug}: Server nicht bereit')
                            if proc.poll() is not None:
                                logfile.seek(0)
                                self.fail(logfile.read().decode(errors='replace'))
                            with urlopen(base + '/') as res:
                                html = res.read().decode('utf8')
                                self.assertIn(f'{classname if slug == "balllabor" else "Sternenpfad"}', html)
                                self.assertIn('id="shutdown"', html)
                            with urlopen(base + '/game/scene.html') as res:
                                self.assertIn('template id=', res.read().decode())
                            with urlopen(base + '/game/style.css') as res:
                                self.assertIn('#field', res.read().decode())
                            with urlopen(base + '/game/assets/' + ('stern.svg' if slug == 'sternenpfad' else 'ping.wav')) as res:
                                self.assertTrue(res.read())
                            with urlopen(base + '/events', timeout=12) as events:
                                initial = []
                                goal = ('CREATE spieler roboter' if slug == 'sternenpfad'
                                        else 'CREATE paddle schlaeger')
                                for _ in range(70):
                                    event = read_sse(events)
                                    initial.append(event)
                                    if event == ('cmd', goal):
                                        break
                                self.assertIn(('cmd', goal), initial)
                                if slug == 'sternenpfad':
                                    with urlopen(Request(base + '/input', method='POST', data=b'KEYDOWN ArrowRight')):
                                        pass
                                    expected = 'MOVE spieler 136 272'
                                else:
                                    # Die Simulation läuft ohne Tastendruck weiter.
                                    expected = 'MOVE ball '
                                seen = False
                                for _ in range(160):
                                    typ, value = read_sse(events)
                                    if typ == 'cmd' and value.startswith(expected):
                                        seen = True
                                        break
                                self.assertTrue(seen, f'{server}/{slug}: erwarteter Spielbefehl fehlt')
                            with urlopen(Request(base + '/shutdown', method='POST', data=b'',
                                                 headers={'X-Arcade-Action': 'shutdown'}), timeout=6):
                                pass
                            proc.wait(timeout=9)
                            self.assertEqual(proc.returncode, 0)
                        finally:
                            if proc.poll() is None:
                                proc.terminate()
                                try:
                                    proc.wait(timeout=5)
                                except subprocess.TimeoutExpired:
                                    proc.kill()
                                    proc.wait(timeout=5)

    def test_docs_links_exist_and_svg_is_valid(self):
        import re
        import xml.etree.ElementTree as et
        docs = ROOT / 'docs'
        for doc in docs.glob('*.md'):
            text = doc.read_text(encoding='utf-8')
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if target.startswith(('http:', 'https:', '#')):
                    continue
                rel = target.split('#', 1)[0]
                self.assertTrue((doc.parent / rel).exists(), f'{doc.name}: Verweis fehlt: {rel}')
        et.parse(ROOT / 'games/sternenpfad/assets/stern.svg')


if __name__ == '__main__':
    unittest.main()
