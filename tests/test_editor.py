"""Architekturtests: Editor-Dateien und Spielprozess sind getrennt."""
import json
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@unittest.skipUnless(shutil.which('java') and shutil.which('javac'), 'JDK fehlt')
class EditorIntegrationTests(unittest.TestCase):
    def test_java_and_python_separation(self):
        for lang in ('java', 'python'):
            with self.subTest(server=lang), tempfile.TemporaryDirectory() as tmp:
                game=Path(tmp)/'game'
                shutil.copytree(ROOT/'games'/'sternenpfad',game)
                main=game/'Sternenpfad.java'
                original_scene=(game/'scene.html').read_bytes()
                original_css=(game/'style.css').read_bytes()
                p=port()
                cmd=(['java','server-java/ArcadeServer.java'] if lang=='java' else ['python3','server.py']) + [str(main),'--port',str(p)]
                with tempfile.TemporaryFile() as log:
                    proc=subprocess.Popen(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                    base=f'http://127.0.0.1:{p}'
                    try:
                        for i in range(140):
                            try:
                                with urlopen(base+'/health',timeout=.3) as response:
                                    if response.read()==b'OK\n': break
                            except (OSError,URLError):
                                if proc.poll() is not None: break
                                time.sleep(.1)
                        else: self.fail('Server nicht gestartet')
                        self.assertIsNone(proc.poll())
                        with urlopen(base+'/editor') as response:
                            self.assertIn(b'Spielwerkstatt',response.read())
                        with urlopen(base+'/editor/editor.js') as response:
                            self.assertIn(b'/editor/api/save',response.read())
                        for generator in ('registry', 'java', 'python'):
                            with urlopen(base+'/editor/codegen/'+generator+'.js', timeout=5) as response:
                                self.assertEqual(response.status, 200)
                                self.assertIn(b'SpielwerkCodegen', response.read())
                        with self.assertRaises(HTTPError) as err:
                            urlopen(base+'/editor/codegen/nonexistent.js',timeout=5)
                        self.assertEqual(err.exception.code,404)
                        with urlopen(base+'/editor/api/design') as response:
                            self.assertEqual(json.loads(response.read()),{'version':1,'templates':[]})
                        # Project export is isolated under <game>/spielwerk/.
                        design=b'{"version":1,"templates":[{"id":"sw-test"}]}'
                        html=b'<template id="sw-test"><div class="sw-sprite"></div></template>\n'
                        css=b'#field .sw-sprite{width:64px;height:64px;}\n'
                        body=(f'{len(design)}\n{len(html)}\n{len(css)}\n'.encode()+design+html+css)
                        req=lambda data,headers=None: Request(base+'/editor/api/save',data=data,method='POST',headers=headers or {})
                        with self.assertRaises(HTTPError) as err:
                            urlopen(req(body),timeout=4)
                        self.assertEqual(err.exception.code,403)
                        with self.assertRaises(HTTPError) as err:
                            urlopen(req(body,{'X-Spielwerk-Editor':'save','Origin':'https://evil.example'}),timeout=4)
                        self.assertEqual(err.exception.code,403)
                        with urlopen(req(body,{'X-Spielwerk-Editor':'save'}),timeout=4) as response:
                            self.assertEqual(response.status,200)
                        with urlopen(base+'/game/spielwerk/scene.html') as response:
                            self.assertEqual(response.read(),html)
                        with urlopen(base+'/game/spielwerk/style.css') as response:
                            self.assertEqual(response.read(),css)
                        self.assertEqual((game/'scene.html').read_bytes(),original_scene)
                        self.assertEqual((game/'style.css').read_bytes(),original_css)
                        with urlopen(base+'/') as response:
                            self.assertIn(b'/editor',response.read())
                        with urlopen(base+'/game/scene.html') as response:
                            self.assertEqual(response.read(),original_scene)
                        with urlopen(base+'/editor/api/assets') as response:
                            self.assertIn('stern.svg', json.loads(response.read()))
                        # Existing game input, compile and tick interface remain unaffected.
                        with urlopen(Request(base+'/input',data=b'KEYDOWN ArrowRight',method='POST'),timeout=5) as response:
                            self.assertEqual(response.status,200)
                        # reject arbitrary file write/traversal
                        with self.assertRaises(HTTPError) as err:
                            urlopen(Request(base+'/editor/api/assets/evil.txt',data=b'foo',method='POST',headers={'X-Spielwerk-Editor':'save'}),timeout=5)
                        self.assertEqual(err.exception.code,400)
                        with urlopen(Request(base+'/shutdown',data=b'',method='POST',headers={'X-Arcade-Action':'shutdown'}),timeout=5):pass
                        proc.wait(timeout=10)
                        self.assertEqual(proc.returncode,0)
                    finally:
                        if proc.poll() is None:
                            proc.terminate()
                            try:proc.wait(timeout=5)
                            except subprocess.TimeoutExpired:proc.kill()

if __name__=='__main__':unittest.main()
