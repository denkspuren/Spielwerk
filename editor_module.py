"""Spielwerkstatt-Dateiverwaltung: keine Abhängigkeit vom GameManager/Spielprotokoll.

Identische Endpunkte wie EditorModule.java, nur Python-Standardbibliothek.
Der HTTP-Router delegiert ausschließlich /editor* und /game/spielwerk/* an dieses Modul.
"""
from pathlib import Path
from urllib.parse import unquote
import json
import os
import re
import tempfile

NAME = re.compile(r'^[A-Za-z0-9_-]{1,64}\.(png|jpg|jpeg|gif|webp)$', re.I)
SVG_NAME = re.compile(r'^[A-Za-z0-9_-]{1,64}\.svg$', re.I)
MAX_BUNDLE = 900_000
MAX_ASSET = 2_000_000


class EditorFiles:
    def __init__(self, game_dir: Path, web: Path):
        self.game_dir = game_dir
        self.web = web / 'editor'
        self.output_dir = game_dir / 'spielwerk'

    def get(self, handler, path: str) -> bool:
        if path.startswith('/game/spielwerk/'):
            filename = path[len('/game/spielwerk/'):]
            if filename not in ('scene.html', 'style.css'):
                handler._send(b'Not found', 'text/plain', 404)
            else:
                self._file(handler, self.output_dir / filename)
            return True
        if not (path == '/editor' or path.startswith('/editor/')):
            return False
        files = {
            '/editor': self.web / 'index.html', '/editor/': self.web / 'index.html',
            '/editor/editor.js': self.web / 'editor.js',
            '/editor/editor.css': self.web / 'editor.css',
            '/editor/api/design': self.output_dir / 'design.json',
        }
        if re.fullmatch(r'/editor/codegen/[a-z][a-z0-9_-]*\.js',path):
            self._file(handler, self.web / path[len('/editor/'):])
        elif path == '/editor/api/design' and not files[path].is_file():
            handler._send(b'{"version":1,"templates":[]}', 'application/json; charset=utf-8')
        elif path == '/editor/api/assets':
            self._assets(handler)
        elif path in files:
            self._file(handler, files[path])
        else:
            handler._send(b'Not found', 'text/plain', 404)
        return True

    def post(self, handler, path: str) -> bool:
        if not path.startswith('/editor/'):
            return False
        if not self._trusted(handler):
            handler._send(b'Forbidden', 'text/plain', 403)
            return True
        if path == '/editor/api/save':
            self._save(handler)
        elif path.startswith('/editor/api/assets/'):
            self._upload(handler, path[len('/editor/api/assets/'):])
        else:
            handler._send(b'Not found', 'text/plain', 404)
        return True

    def _trusted(self, h) -> bool:
        port = h.server.server_port
        host = h.headers.get('Host')
        if host not in (f'127.0.0.1:{port}', f'localhost:{port}'):
            return False
        origin = h.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{port}', f'http://localhost:{port}'):
            return False
        return (h.headers.get('X-Spielwerk-Editor') == 'save' and
                h.headers.get('Sec-Fetch-Site', 'same-origin') in ('same-origin', 'none'))

    def _body(self, h, limit: int) -> bytes | None:
        try:
            length = int(h.headers.get('Content-Length', '-1'))
        except ValueError:
            length = -1
        if length < 0 or length > limit:
            h._send(b'Invalid content length', 'text/plain', 413)
            return None
        data = h.rfile.read(length)
        if len(data) != length:
            h._send(b'Incomplete request', 'text/plain', 400)
            return None
        return data

    def _save(self, h) -> None:
        data = self._body(h, MAX_BUNDLE)
        if data is None:
            return
        try:
            first, second, third, payload = data.split(b'\n', 3)
            lengths = [int(first), int(second), int(third)]
            if (len(first) > 9 or len(second) > 9 or len(third) > 9 or
                    any(n < 0 or n > 250_000 for n in lengths) or
                    lengths[0] < 2 or sum(lengths) != len(payload)):
                raise ValueError('invalid lengths')
            a, b, c = lengths
            values = [payload[:a], payload[a:a+b], payload[a+b:]]
            for value in values:
                value.decode('utf-8', 'strict')
        except (ValueError, UnicodeError):
            h._send(b'Invalid bundle', 'text/plain', 400)
            return
        self.output_dir.mkdir(exist_ok=True)
        if self.output_dir.is_symlink():
            h._send(b'Symlinks not allowed', 'text/plain', 403)
            return
        temporary = []
        try:
            for content in values:
                fd, filename = tempfile.mkstemp(prefix='.sw-', dir=self.output_dir)
                with os.fdopen(fd, 'wb') as f:
                    f.write(content)
                temporary.append(Path(filename))
            for source, name in zip(temporary, ('design.json', 'scene.html', 'style.css')):
                source.replace(self.output_dir / name)
        finally:
            for source in temporary:
                source.unlink(missing_ok=True)
        h._send(b'Saved', 'text/plain')

    def _upload(self, h, filename: str) -> None:
        if not NAME.fullmatch(filename):
            h._send(b'Bad filename', 'text/plain', 400)
            return
        data = self._body(h, MAX_ASSET)
        if data is None:
            return
        suffix = filename.rsplit('.', 1)[1].lower()
        valid = {
            'png': data.startswith(b'\x89PNG'),
            'jpg': data.startswith(b'\xff\xd8\xff'),
            'jpeg': data.startswith(b'\xff\xd8\xff'),
            'gif': data.startswith(b'GIF'),
            'webp': data.startswith(b'RIFF') and data[8:12] == b'WEBP',
        }[suffix]
        if not valid:
            h._send(b'Invalid image', 'text/plain', 415)
            return
        assets = self.game_dir / 'assets'
        assets.mkdir(exist_ok=True)
        if assets.is_symlink():
            h._send(b'Symlinks not allowed', 'text/plain', 403)
            return
        (assets / filename).write_bytes(data)
        h._send(b'Uploaded', 'text/plain')

    def _assets(self, h) -> None:
        assets = self.game_dir / 'assets'
        files = sorted(p.name for p in assets.iterdir()
                       if p.is_file() and (NAME.fullmatch(p.name) or SVG_NAME.fullmatch(p.name))) if assets.exists() else []
        h._send(json.dumps(files).encode('utf-8'), 'application/json; charset=utf-8')

    def _file(self, h, file: Path) -> None:
        if not file.is_file() or (not file.resolve().is_relative_to(self.game_dir.resolve()) and not file.resolve().is_relative_to(self.web.resolve())):
            h._send(b'Not found', 'text/plain', 404)
            return
        type_ = {
            '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
            '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
        }.get(file.suffix, 'application/octet-stream')
        h._send(file.read_bytes(), type_)
