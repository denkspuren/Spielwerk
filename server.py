#!/usr/bin/env python3
"""Local, dependency-free Java-to-browser game server.

Java and server speak a documented, newline-delimited plain-text protocol.
Browser uses SSE for display updates and HTTP POST for input events.
"""
from __future__ import annotations

import argparse
import configparser
from collections import OrderedDict
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import html
import mimetypes
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
from editor_module import EditorFiles

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"
VALID_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
VALID_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
MAX_LINE = 8192


@dataclass(frozen=True)
class GameConfig:
    title: str
    tick_ms: int
    width: int
    height: int


def load_config(game_dir: Path) -> GameConfig:
    ini = configparser.ConfigParser()
    ini.read(game_dir / "game.ini", encoding="utf-8")
    sec = ini["game"] if "game" in ini else {}
    config = GameConfig(
        title=sec.get("title", game_dir.name),
        tick_ms=int(sec.get("tick_ms", 0)),
        width=int(sec.get("width", 640)),
        height=int(sec.get("height", 480)),
    )
    if config.tick_ms < 0 or config.tick_ms and config.tick_ms < 15:
        raise ValueError("tick_ms must be 0 or >= 15")
    if not (200 <= config.width <= 2048 and 200 <= config.height <= 2048):
        raise ValueError("width and height must be between 200 and 2048")
    return config


def parse_command(line: str) -> tuple[str, ...] | None:
    """Validate one Java->browser message without JSON or generic serialization."""
    if not line or len(line) > MAX_LINE or "\x00" in line or "\r" in line:
        return None
    name, _, rest = line.partition(" ")
    if name in ("SHOW", "HIDE", "REMOVE"):
        if not VALID_ID.fullmatch(rest):
            return None
        return (name, rest)
    if name == "SOUND":
        if not VALID_ID.fullmatch(rest):
            return None
        return (name, rest)
    if name in ("CREATE", "MOVE"):
        items = rest.split(" ")
        if name == "CREATE" and len(items) == 2 and all(VALID_ID.fullmatch(i) for i in items):
            return (name, *items)
        if name == "MOVE" and len(items) == 3 and VALID_ID.fullmatch(items[0]):
            try:
                x, y = int(items[1]), int(items[2])
            except ValueError:
                return None
            if abs(x) <= 10000 and abs(y) <= 10000:
                return (name, items[0], str(x), str(y))
        return None
    if name == "TEXT":
        obj_id, sep, content = rest.partition(" ")
        if VALID_ID.fullmatch(obj_id) and sep and len(content) <= 4000:
            return (name, obj_id, content)
    return None


def parse_input(line: str) -> bool:
    if not line or len(line) > 200 or "\n" in line or "\r" in line or "\x00" in line:
        return False
    cmd, _, rest = line.partition(" ")
    if cmd in ("KEYDOWN", "KEYUP"):
        return bool(VALID_KEY.fullmatch(rest))
    if cmd == "CLICK":
        parts = rest.split(" ")
        if len(parts) != 3 or not VALID_ID.fullmatch(parts[0]):
            return False
        try:
            return all(abs(int(n)) <= 10000 for n in parts[1:])
        except ValueError:
            return False
    return False


class SceneState:
    """Latest DOM state, so a new browser tab can join an already running game."""
    def __init__(self) -> None:
        self.created: dict[str, str] = {}
        self.positions: dict[str, str] = {}
        self.texts: dict[str, str] = {}
        self.visibility: dict[str, str] = {}
        self.removed: dict[str, str] = {}

    def clear(self) -> None:
        self.__init__()

    def apply(self, parsed: tuple[str, ...]) -> None:
        cmd, obj_id = parsed[:2]
        if cmd == "SOUND":
            return
        if cmd == "CREATE":
            self.created[obj_id] = " ".join(parsed)
            self.removed.pop(obj_id, None)
            self.positions.pop(obj_id, None)
            self.texts.pop(obj_id, None)
            self.visibility.pop(obj_id, None)
        elif cmd == "REMOVE":
            self.created.pop(obj_id, None)
            self.positions.pop(obj_id, None)
            self.texts.pop(obj_id, None)
            self.visibility.pop(obj_id, None)
            self.removed[obj_id] = " ".join(parsed)
        elif cmd == "MOVE":
            self.positions[obj_id] = " ".join(parsed)
        elif cmd == "TEXT":
            self.texts[obj_id] = " ".join(parsed)
        elif cmd in ("SHOW", "HIDE"):
            self.visibility[obj_id] = " ".join(parsed)

    def snapshot(self) -> list[str]:
        return (list(self.created.values()) + list(self.positions.values()) +
                list(self.texts.values()) + list(self.visibility.values()) +
                list(self.removed.values()))


@dataclass(eq=False)
class Client:
    messages: queue.Queue[tuple[str, str]] = field(default_factory=lambda: queue.Queue(maxsize=2000))


class GameSession:
    def __init__(self, manager: GameManager, process: subprocess.Popen[str]):
        self.manager = manager
        self.process = process
        self.inputs: queue.Queue[str] = queue.Queue(maxsize=1000)
        self.stopping = threading.Event()
        self.threads: list[threading.Thread] = []

    def launch(self, tick_ms: int) -> None:
        tasks = [(self._write, "stdin"), (self._read, "stdout"),
                 (self._stderr, "stderr"), (self._wait, "exit")]
        if tick_ms:
            tasks.append((lambda: self._ticks(tick_ms), "ticks"))
        for fn, name in tasks:
            t = threading.Thread(target=fn, name=f"java-{name}", daemon=True)
            self.threads.append(t)
            t.start()

    def put(self, value: str) -> None:
        if not self.stopping.is_set() and self.process.poll() is None:
            try:
                self.inputs.put_nowait(value)
            except queue.Full:
                self.manager.log("Eingabe-Warteschlange voll; Ereignis verworfen")

    def _write(self) -> None:
        try:
            assert self.process.stdin is not None
            while not self.stopping.is_set():
                try:
                    line = self.inputs.get(timeout=0.2)
                except queue.Empty:
                    continue
                self.process.stdin.write(line + "\n")
                self.process.stdin.flush()
        except (BrokenPipeError, ValueError, OSError):
            pass

    def _read(self) -> None:
        try:
            assert self.process.stdout is not None
            for raw in self.process.stdout:
                if self.stopping.is_set():
                    break
                line = raw.rstrip("\n")
                parsed = parse_command(line)
                if parsed is None:
                    self.manager.log(f"Ungültige stdout-Zeile (verwenden Sie stderr für Debugging): {line[:250]}")
                else:
                    self.manager.command(self, parsed)
        except (ValueError, OSError) as e:
            if not self.stopping.is_set():
                self.manager.log(f"stdout-Fehler: {e}")

    def _stderr(self) -> None:
        try:
            assert self.process.stderr is not None
            for line in self.process.stderr:
                if self.stopping.is_set():
                    break
                self.manager.log(line.rstrip("\n"))
        except (ValueError, OSError):
            pass

    def _ticks(self, ms: int) -> None:
        interval = ms / 1000.0
        next_tick = time.monotonic() + interval
        while not self.stopping.is_set() and self.process.poll() is None:
            if self.stopping.wait(max(0.0, next_tick - time.monotonic())):
                return
            # Drop ticks if Java is slow; never build an unbounded backlog.
            if self.inputs.qsize() < 8:
                self.put(f"TICK {ms}")
            next_tick += interval
            if next_tick < time.monotonic() - interval:
                next_tick = time.monotonic() + interval

    def _wait(self) -> None:
        code = self.process.wait()
        if not self.stopping.is_set():
            self.manager.finished(self, code)

    def stop(self) -> None:
        self.stopping.set()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
            try:
                if pipe:
                    pipe.close()
            except OSError:
                pass


class GameManager:
    def __init__(self, main_file: Path, config: GameConfig):
        self.main_file = main_file.resolve()
        self.editor_only = self.main_file.is_dir()
        self.game_dir = self.main_file if self.editor_only else self.main_file.parent
        self.language = "python" if self.main_file.suffix == ".py" else "java"
        self.config = config
        self.lock = threading.RLock()
        self.clients: set[Client] = set()
        self.state = SceneState()
        self.status = (("EDITOR", "Nur Spielwerkstatt") if self.editor_only else ("STARTING", "Programm wird gestartet …"))
        self.error = ""
        self.active: GameSession | None = None
        self.stop_event = threading.Event()
        self.force_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.build_dir: Path | None = None

    def start(self) -> None:
        if self.editor_only:
            return
        self.thread = threading.Thread(target=self._watch, name="file-watcher", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.force_event.set()
        with self.lock:
            session = self.active
            self.active = None
        if session:
            session.stop()
        if self.thread:
            self.thread.join(timeout=5)
        if self.build_dir:
            shutil.rmtree(self.build_dir, ignore_errors=True)

    def subscribe(self, client: Client) -> None:
        with self.lock:
            self.clients.add(client)
            self._offer(client, "reset", "")
            self._offer(client, "status", "\t".join(self.status))
            if self.error:
                self._offer(client, "compile", self.error)
            for cmd in self.state.snapshot():
                self._offer(client, "cmd", cmd)

    def unsubscribe(self, client: Client) -> None:
        with self.lock:
            self.clients.discard(client)

    @staticmethod
    def _offer(client: Client, kind: str, data: str) -> None:
        try:
            client.messages.put_nowait((kind, data))
        except queue.Full:
            # A disconnected/stuck client is removed on its next send attempt.
            pass

    def _broadcast(self, kind: str, data: str) -> None:
        with self.lock:
            for client in self.clients.copy():
                self._offer(client, kind, data)

    def log(self, text: str) -> None:
        self._broadcast("log", text[:3000])
        print(f"[game] {text[:500]}", file=sys.stderr)

    def command(self, session: GameSession, parsed: tuple[str, ...]) -> None:
        with self.lock:
            if self.active is not session:
                return
            self.state.apply(parsed)
            self._broadcast("cmd", " ".join(parsed))

    def finished(self, session: GameSession, exit_code: int) -> None:
        with self.lock:
            if self.active is not session:
                return
            self.status = ("STOPPED", f"Spielprozess beendet (Exit-Code {exit_code}).")
            self._broadcast("status", "\t".join(self.status))

    def input(self, line: str) -> bool:
        if not parse_input(line):
            return False
        with self.lock:
            session = self.active
        if session:
            session.put(line)
        return True

    def restart(self) -> None:
        if not self.editor_only:
            self.force_event.set()

    def _files_signature(self) -> tuple:
        # Only Java changes require a recompile. HTML/CSS are fetched on browser reload.
        try:
            paths = sorted(self.game_dir.glob("*.py" if self.language == "python" else "*.java"))
            return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
        except FileNotFoundError:
            return ()

    def _watch(self) -> None:
        previous = None
        changed_at = time.monotonic() - 1
        while not self.stop_event.is_set():
            signature = self._files_signature()
            force = self.force_event.is_set()
            if signature != previous or force:
                previous = signature
                changed_at = time.monotonic()
                self.force_event.clear()
            if changed_at and time.monotonic() - changed_at >= 0.35:
                changed_at = 0
                self._compile_and_launch()
            self.stop_event.wait(0.1)

    def _compile_and_launch(self) -> None:
        with self.lock:
            old = self.active
            self.active = None
            self.state.clear()
            self.error = ""
            self.status = ("STARTING", "Programm wird gestartet …")
            self._broadcast("reset", "")
            self._broadcast("compile", "")
            self._broadcast("status", "\t".join(self.status))
        if old:
            old.stop()
        if not self.main_file.exists():
            self._compile_error(f"Hauptdatei nicht gefunden: {self.main_file.name}")
            return
        if self.language == "python":
            command = [sys.executable, "-u", self.main_file.name]
        else:
            sources = sorted(self.game_dir.glob("*.java"))
            if not sources:
                self._compile_error("Keine Java-Quelldateien gefunden.")
                return
            build = Path(tempfile.mkdtemp(prefix="arcade-classes-"))
            try:
                result = subprocess.run(
                    ["javac", "-encoding", "UTF-8", "-d", str(build), *map(str, sources)],
                    cwd=self.game_dir, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=30, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as e:
                shutil.rmtree(build, ignore_errors=True)
                self._compile_error(f"javac konnte nicht ausgeführt werden: {e}")
                return
            if result.returncode != 0:
                shutil.rmtree(build, ignore_errors=True)
                self._compile_error((result.stdout + "\n" + result.stderr).strip())
                return
            if self.stop_event.is_set():
                shutil.rmtree(build, ignore_errors=True)
                return
            if self.build_dir:
                shutil.rmtree(self.build_dir, ignore_errors=True)
            self.build_dir = build
            command = ["java", "-cp", str(build), self.main_file.stem]
        if self.stop_event.is_set():
            return
        try:
            process = subprocess.Popen(
                command, cwd=self.game_dir, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                bufsize=1, text=True, encoding="utf-8", errors="replace",
            )
        except OSError as e:
            self._compile_error(f"Spiel konnte nicht gestartet werden: {e}")
            return
        session = GameSession(self, process)
        with self.lock:
            self.active = session
            self.status = ("RUNNING", "Spiel läuft")
            self._broadcast("status", "\t".join(self.status))
        session.launch(self.config.tick_ms)
        print(f"[server] Started {self.main_file.name} (PID {process.pid}, tick {self.config.tick_ms} ms)")

    def _compile_error(self, detail: str) -> None:
        with self.lock:
            self.error = detail or "Unbekannter Compilerfehler"
            self.status = ("COMPILE_ERROR", "Kompilierung fehlgeschlagen")
            self._broadcast("compile", self.error)
            self._broadcast("status", "\t".join(self.status))
        print(f"[compiler]\n{detail}", file=sys.stderr)


def sse_format(kind: str, message: str) -> bytes:
    # Every SSE data line must be separately prefixed; multiline compiler errors work.
    lines = message.replace("\r", "").split("\n")
    return (f"event: {kind}\n" + "".join(f"data: {line}\n" for line in lines) + "\n").encode("utf-8")


def handler_factory(manager: GameManager):
    editor = EditorFiles(manager.game_dir, WEB)
    class Handler(BaseHTTPRequestHandler):
        server_version = "JavaArcade/1.0"
        protocol_version = "HTTP/1.1"

        def handle(self) -> None:
            # Browser tabs may close an idle keep-alive connection abruptly.
            # The default socketserver prints a long traceback for this normal case.
            try:
                super().handle()
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if editor.get(self, path):
                return
            if path == "/events":
                self._events()
                return
            if path == "/health":
                self._send(b"OK\n", "text/plain; charset=utf-8")
                return
            if path == "/" and manager.editor_only:
                self.send_response(302)
                self.send_header("Location", "/editor")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if path == "/":
                template = (WEB / "index.html").read_text(encoding="utf-8")
                workshop = manager.game_dir / "spielwerk"

                def has_workshop_file(name: str) -> bool:
                    candidate = workshop / name
                    return (not workshop.is_symlink() and not candidate.is_symlink() and
                            candidate.is_file() and
                            candidate.resolve().is_relative_to(manager.game_dir.resolve()))

                for key, value in {
                    "TITLE": html.escape(manager.config.title, quote=True),
                    "WIDTH": str(manager.config.width),
                    "HEIGHT": str(manager.config.height),
                    "TICK": str(manager.config.tick_ms),
                    "MAIN": html.escape(manager.main_file.name, quote=True),
                    "LANGUAGE": "Python" if manager.language == "python" else "Java",
                    "EXTENSION": ".py" if manager.language == "python" else ".java",
                    "WORKSHOP_CSS_LINK": ('<link rel="stylesheet" href="/game/spielwerk/style.css">'
                                          if has_workshop_file("style.css") else ""),
                    "WORKSHOP_TEMPLATES": "true" if has_workshop_file("scene.html") else "false",
                    "WORKSHOP_LAYOUT": "true" if has_workshop_file("layout.json") else "false",
                }.items():
                    template = template.replace("{{" + key + "}}", value)
                self._send(template.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path.startswith("/static/"):
                self._file(WEB, path[len("/static/"):])
                return
            if path == "/game/scene.html":
                self._file(manager.game_dir, "scene.html")
                return
            if path == "/game/style.css":
                self._file(manager.game_dir, "style.css")
                return
            if path.startswith("/game/assets/"):
                self._file(manager.game_dir / "assets", path[len("/game/assets/"):])
                return
            self.send_error(404)

        def _file(self, directory: Path, name: str) -> None:
            parent = directory.resolve()
            target = (parent / name).resolve()
            if not target.is_relative_to(parent) or not target.is_file():
                self.send_error(404)
                return
            try:
                data = target.read_bytes()
            except OSError:
                self.send_error(404)
                return
            mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if mime.startswith("text/") or mime in ("image/svg+xml", "application/javascript"):
                mime += "; charset=utf-8"
            self._send(data, mime)

        def _send(self, data: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _events(self) -> None:
            client = Client()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            manager.subscribe(client)
            try:
                while not manager.stop_event.is_set():
                    try:
                        kind, data = client.messages.get(timeout=12)
                        self.wfile.write(sse_format(kind, data))
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                manager.unsubscribe(client)

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            if editor.post(self, path):
                return
            if path not in ("/input", "/restart", "/shutdown"):
                self.send_error(404)
                return
            # Avoid cross-site pages issuing commands to an open local game server.
            if path == "/shutdown":
                if (self.headers.get("X-Arcade-Action") != "shutdown" or
                        self.headers.get("Sec-Fetch-Site", "same-origin") not in
                        ("same-origin", "none")):
                    self._send(b"Forbidden\n", "text/plain", 403)
                    return
            origin = self.headers.get("Origin")
            if origin:
                parsed_origin = urlsplit(origin)
                allowed_hosts = {"127.0.0.1", "localhost"}
                if (parsed_origin.scheme != "http" or
                        parsed_origin.hostname not in allowed_hosts or
                        parsed_origin.port != self.server.server_port):
                    self._send(b"Forbidden origin\n", "text/plain", 403)
                    return
            try:
                length = int(self.headers.get("Content-Length", "-1"))
            except ValueError:
                length = -1
            if not 0 <= length <= 500:
                self._send(b"Bad request\n", "text/plain", 400)
                return
            data = self.rfile.read(length)
            try:
                message = data.decode("utf-8")
            except UnicodeDecodeError:
                self._send(b"Bad UTF-8\n", "text/plain", 400)
                return
            if path == "/shutdown":
                with manager.lock:
                    manager.status = ("STOPPED", "Server wird beendet …")
                    manager._broadcast("status", "\t".join(manager.status))
                self._send(b"Shutdown scheduled\n", "text/plain")
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            elif path == "/restart":
                manager.restart()
                self._send(b"Restart scheduled\n", "text/plain")
            elif manager.input(message):
                self._send(b"OK\n", "text/plain")
            else:
                self._send(b"Invalid game event\n", "text/plain", 400)

        def log_message(self, fmt: str, *args: object) -> None:
            # Avoid flooding the terminal with 30 key event requests per second.
            if self.path not in ("/input", "/events"):
                print(f"[http] {fmt % args}")

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Spielwerk (ohne zusätzliche Python-Pakete)")
    parser.add_argument("main_file", type=Path, help=".java- oder .py-Hauptdatei; ein Ordner startet nur die Werkstatt")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    main_file = args.main_file.resolve()
    if not main_file.exists() and not main_file.suffix:
        main_file.mkdir(parents=True, exist_ok=True)
    if not (main_file.is_dir() or (main_file.is_file() and main_file.suffix in (".java", ".py"))):
        parser.error(f"Erwartet: .java, .py oder Projektordner: {main_file}")
    if main_file.suffix == ".java" and (shutil.which("java") is None or shutil.which("javac") is None):
        parser.error("Java JDK nicht gefunden. 'java' und 'javac' müssen im PATH liegen.")
    config = load_config(main_file if main_file.is_dir() else main_file.parent)
    manager = GameManager(main_file, config)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory(manager))
    server.daemon_threads = True
    manager.start()
    print(f"[server] {config.title}: http://127.0.0.1:{args.port}")
    print(f"[server] {'Spielwerkstatt-Verzeichnis' if main_file.is_dir() else 'Hauptdatei'}: {main_file}")
    print("[server] Strg+C zum Beenden.")
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        print("\n[server] Stopping …")
    finally:
        manager.stop()
        server.server_close()


if __name__ == "__main__":
    main()
