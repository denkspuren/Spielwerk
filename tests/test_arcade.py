import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

from server import GameManager, GameConfig, SceneState, handler_factory, parse_command, parse_input, sse_format, load_config

ROOT = Path(__file__).resolve().parents[1]


def wait_for(predicate, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False


class ProtocolTests(unittest.TestCase):
    def test_outputs(self):
        self.assertEqual(parse_command('MOVE frog -15 203'), ('MOVE', 'frog', '-15', '203'))
        self.assertEqual(parse_command('TEXT label Hallo Welt mit Umlauten ä'),
                         ('TEXT', 'label', 'Hallo Welt mit Umlauten ä'))
        for line in ['print hi', 'MOVE f 1.5 2', 'MOVE f 1000000 2', 'CREATE f',
                     'SHOW bad id', 'SOUND other name', 'TEXT 9abc hello',
                     'HIDE x\nREMOVE y']:
            self.assertIsNone(parse_command(line), msg=line)

    def test_input(self):
        for message in ['KEYDOWN ArrowUp', 'KEYUP Space', 'CLICK box_2 100 200']:
            self.assertTrue(parse_input(message))
        for message in ['TICK 2', 'CLICK bad name 1 2', 'KEYDOWN x\nREMOVE a', 'CLICK a x y']:
            self.assertFalse(parse_input(message))

    def test_scene_snapshot(self):
        state = SceneState()
        for line in ('CREATE c crate', 'MOVE c 4 10', 'TEXT message Hello World',
                     'HIDE c', 'SOUND hit'):
            state.apply(parse_command(line))
        self.assertEqual(state.snapshot(), ['CREATE c crate', 'MOVE c 4 10',
                                            'TEXT message Hello World', 'HIDE c'])
        state.apply(parse_command('REMOVE c'))
        self.assertNotIn('MOVE c 4 10', state.snapshot())
        self.assertIn('REMOVE c', state.snapshot())

    def test_sse_errors_preserve_newlines(self):
        value = sse_format('compile', 'Zeile 1\nZeile 2').decode()
        self.assertIn('data: Zeile 1\ndata: Zeile 2\n', value)


@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'JDK fehlt')
class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game_dir = Path(self.temp.name) / 'sokoban'
        shutil.copytree(ROOT / 'games' / 'sokoban', self.game_dir)
        self.main = self.game_dir / 'Sokoban.java'
        self.manager = GameManager(self.main, load_config(self.game_dir))
        self.manager.start()
        self.addCleanup(self.manager.stop)
        self.assertTrue(wait_for(lambda: self.manager.status[0] == 'RUNNING'),
                        f'Java start: {self.manager.status}')
        self.assertTrue(wait_for(lambda: 'CREATE player hero' in self.manager.state.snapshot()))

    def test_sokoban_works_without_ticks(self):
        self.assertEqual(self.manager.config.tick_ms, 0)
        for key in ['ArrowUp', 'ArrowRight', 'ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowLeft']:
            self.assertTrue(self.manager.input('KEYDOWN ' + key))
        self.assertTrue(wait_for(lambda: any('Geschafft' in c for c in self.manager.state.snapshot())))
        self.assertTrue(any('Züge: 6' in c for c in self.manager.state.snapshot()))
        self.manager.input('KEYDOWN KeyZ')
        self.assertTrue(wait_for(lambda: any('Züge: 5' in c for c in self.manager.state.snapshot())))
        self.manager.input('CLICK resetTiles 600 165')
        self.assertTrue(wait_for(lambda: any('TEXT moves Züge: 0' == c
                                              for c in self.manager.state.snapshot())))

    def test_compile_error_and_recovery(self):
        self.main.write_text('public class Sokoban { this is not Java! }', encoding='utf-8')
        self.assertTrue(wait_for(lambda: self.manager.status[0] == 'COMPILE_ERROR', 12))
        self.assertTrue('error' in self.manager.error.lower())
        self.main.write_text((ROOT / 'games' / 'sokoban' / 'Sokoban.java').read_text(), encoding='utf-8')
        self.assertTrue(wait_for(lambda: self.manager.status[0] == 'RUNNING', 12))
        self.assertTrue(wait_for(lambda: 'CREATE player hero' in self.manager.state.snapshot()))

    def test_http_and_sse(self):
        httpd = ThreadingHTTPServer(('127.0.0.1', 0), handler_factory(self.manager))
        httpd.daemon_threads = True
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (httpd.shutdown(), httpd.server_close()))
        base = f'http://127.0.0.1:{httpd.server_port}'
        with urlopen(base + '/health') as response:
            self.assertEqual(response.read(), b'OK\n')
        with urlopen(base + '/') as response:
            content = response.read().decode()
            self.assertIn('Sokoban', content)
            self.assertIn('480px', content)
        with urlopen(base + '/game/scene.html') as response:
            self.assertIn(b'template id="crate"', response.read())
        with urlopen(base + '/events', timeout=5) as sse:
            collected = []
            for _ in range(30):
                line = sse.readline().decode().strip()
                collected.append(line)
                if 'CREATE' in line:
                    break
            self.assertTrue(any('CREATE' in x for x in collected), collected)
        req = Request(base + '/input', data=b'KEYDOWN ArrowUp', method='POST')
        with urlopen(req) as response:
            self.assertEqual(response.status, 200)
        self.assertTrue(wait_for(lambda: 'Züge: 1' in self.manager.state.snapshot()[0] or
                                 any('Züge: 1' in x for x in self.manager.state.snapshot())))
        with self.assertRaises(HTTPError) as context:
            urlopen(Request(base + '/input', data=b'TICK 300', method='POST'))
        self.assertEqual(context.exception.code, 400)
        with self.assertRaises(HTTPError) as context:
            urlopen(Request(base + '/restart', data=b'', method='POST',
                            headers={'Origin': 'https://example.org'}))
        self.assertEqual(context.exception.code, 403)


@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'JDK fehlt')
class TickIntegrationTests(unittest.TestCase):
    def test_space_invaders_ticks_and_keyboard(self):
        with tempfile.TemporaryDirectory() as folder:
            game_dir = Path(folder) / 'invaders'
            shutil.copytree(ROOT / 'games' / 'space_invaders', game_dir)
            manager = GameManager(game_dir / 'SpaceInvaders.java', load_config(game_dir))
            try:
                manager.start()
                self.assertTrue(wait_for(lambda: 'CREATE alien_0_0 alien' in manager.state.snapshot()))
                def alien_position():
                    return next((s for s in manager.state.snapshot()
                                 if s.startswith('MOVE alien_0_0 ')), None)
                initial = alien_position()
                self.assertIsNotNone(initial)
                self.assertTrue(wait_for(lambda: alien_position() != initial, timeout=4),
                                'Alien should move without keyboard input')
                self.assertTrue(manager.input('KEYDOWN Space'))
                self.assertTrue(wait_for(lambda: any('CREATE shot_' in s
                                                   for s in manager.state.snapshot()), timeout=3))
                self.assertTrue(manager.input('KEYUP Space'))
                self.assertEqual(manager.config.tick_ms, 33)
            finally:
                manager.stop()


if __name__ == '__main__':
    unittest.main()
