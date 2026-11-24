"""Unabhängige Szenen-Dateiverwaltung der Spielwerkstatt.

Nur layout.json, keine Änderungen an Spiellogik, design.json, scene.html, style.css
oder Quellcode. Der Editor-HTTP-Router delegiert passende Routen hierher.
"""
from pathlib import Path
import json
import os
import re
import tempfile

IDENT = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{0,63}$')
COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')
MAX_SCENE = 64_000


def checked(scene):
    if not isinstance(scene, dict) or scene.get('version') != 1:
        raise ValueError('Unbekanntes Szenenformat')
    if not all(isinstance(scene.get(k), int) and not isinstance(scene.get(k), bool)
               and 200 <= scene[k] <= 2048 for k in ('width', 'height')):
        raise ValueError('Spielfeldgröße muss zwischen 200 und 2048 liegen')
    if not isinstance(scene.get('background'), str) or not COLOR.fullmatch(scene['background']):
        raise ValueError('Ungültige Hintergrundfarbe')
    objects = scene.get('objects')
    if not isinstance(objects, list) or len(objects) > 200:
        raise ValueError('Maximal 200 Objekte erlaubt')
    ids = set()
    for o in objects:
        if not isinstance(o, dict) or not IDENT.fullmatch(str(o.get('id', ''))) or o['id'] in ids:
            raise ValueError('Ungültige oder doppelte Objekt-ID')
        ids.add(o['id'])
        if not IDENT.fullmatch(str(o.get('template', ''))):
            raise ValueError('Ungültige Template-ID')
        if o.get('mode') not in ('static', 'dynamic'):
            raise ValueError('Modus muss static oder dynamic sein')
        if any(not isinstance(o.get(k), int) or isinstance(o.get(k), bool) or
               abs(o[k]) > 10000 for k in ('x', 'y')):
            raise ValueError('Koordinaten außerhalb des zulässigen Bereichs')
    # Normalisiertes, eng definiertes und sprachneutrales Format.
    return {
        'version': 1, 'width': scene['width'], 'height': scene['height'],
        'background': scene['background'],
        'objects': [dict(id=o['id'], template=o['template'],
                         x=o['x'], y=o['y'], mode=o['mode']) for o in objects]
    }


class SceneFiles:
    def __init__(self, game_dir: Path, editor_web: Path):
        self.game_dir = game_dir
        self.web = editor_web / 'scene'
        self.output = game_dir / 'spielwerk'
        self.layout = self.output / 'layout.json'

    def _default(self):
        width, height = 640, 480
        ini = self.game_dir / 'game.ini'
        if ini.is_file():
            section = ''
            for raw in ini.read_text(encoding='utf-8').splitlines():
                line = raw.strip()
                if line.startswith('[') and line.endswith(']'):
                    section = line.lower()
                elif section == '[game]' and '=' in line:
                    key, value = [s.strip() for s in line.split('=', 1)]
                    if key in ('width', 'height'):
                        try:
                            n = int(value)
                            if 200 <= n <= 2048:
                                if key == 'width': width = n
                                else: height = n
                        except ValueError: pass
        return {'version': 1, 'width':width, 'height':height,
                'background':'#12243b', 'objects':[]}

    def get(self, handler, path):
        files = {
            '/editor/scene':self.web/'index.html',
            '/editor/scene/':self.web/'index.html',
            '/editor/scene/scene.js':self.web/'scene.js',
            '/editor/scene/scene.css':self.web/'scene.css',
            '/editor/scene/scene-model.js':self.web/'scene-model.js',
        }
        if path in files:
            file = files[path]
            kind = ('text/javascript; charset=utf-8' if file.suffix == '.js' else
                    'text/css; charset=utf-8' if file.suffix == '.css' else
                    'text/html; charset=utf-8')
            handler._send(file.read_bytes(), kind)
            return True
        if path in ('/editor/api/scene', '/game/spielwerk/layout.json'):
            if (self.layout.is_file() and not self.layout.is_symlink() and
                    not self.output.is_symlink() and
                    self.layout.resolve().is_relative_to(self.game_dir.resolve())):
                result = self.layout.read_bytes()
            elif path == '/editor/api/scene':
                result = json.dumps(self._default()).encode('utf-8')
            else:
                handler._send(b'Not found', 'text/plain', 404)
                return True
            handler._send(result, 'application/json; charset=utf-8')
            return True
        return False

    def post(self, handler, path):
        if path != '/editor/api/scene/save':
            return False
        try:
            length = int(handler.headers.get('Content-Length', '-1'))
        except ValueError:
            length = -1
        if length < 2 or length > MAX_SCENE:
            handler._send(b'Invalid content length', 'text/plain', 413)
            return True
        content = handler.rfile.read(length)
        if len(content) != length:
            handler._send(b'Incomplete request', 'text/plain', 400)
            return True
        try:
            normalized = checked(json.loads(content.decode('utf-8', 'strict')))
        except (ValueError, UnicodeError, TypeError, KeyError, RecursionError) as err:
            handler._send(str(err).encode('utf-8'), 'text/plain', 400)
            return True
        if self.output.is_symlink() or self.layout.is_symlink() or not self.output.resolve().is_relative_to(self.game_dir.resolve()):
            handler._send(b'Symlinks not allowed', 'text/plain', 403)
            return True
        self.output.mkdir(exist_ok=True)
        data = (json.dumps(normalized, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        fd, name = tempfile.mkstemp(prefix='.sw-layout-', dir=self.output)
        try:
            with os.fdopen(fd, 'wb') as out: out.write(data)
            os.replace(name, self.layout)
        finally:
            Path(name).unlink(missing_ok=True)
        handler._send(b'Saved', 'text/plain')
        return True
