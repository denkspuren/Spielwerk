/*
 * Java Browser Arcade – lokaler HTTP/SSE-Server, nur JDK 17+.
 * Start: java server-java/ArcadeServer.java games/sokoban/Sokoban.java
 *
 * Studentenprogramme laufen als eigene Java-Prozesse. stdin/stdout enthalten
 * ausschließlich das zeilenbasierte Spielprotokoll; stderr ist für Debugging.
 */
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Pattern;

public class SpielwerkHost {
    static final Path ROOT = Path.of("").toAbsolutePath().normalize();
    static final Path WEB = ROOT.resolve("web");

    private final GameModule.Manager manager;
    private final EditorModule editor;
    private final HttpServer server;
    private final ExecutorService requests = Executors.newCachedThreadPool();
    private final AtomicBoolean closed = new AtomicBoolean();
    private final int port;

    record Config(String title, int tickMs, int width, int height) {
        static Config load(Path directory) throws IOException {
            Map<String, String> entries = new LinkedHashMap<>();
            Path path = directory.resolve("game.ini");
            if (Files.exists(path)) {
                boolean inGame = false;
                for (String raw : Files.readAllLines(path, StandardCharsets.UTF_8)) {
                    String line = raw.strip();
                    if (line.startsWith("[") && line.endsWith("]")) {
                        inGame = line.equals("[game]");
                    } else if (inGame && !line.startsWith("#") && !line.startsWith(";")
                            && line.contains("=")) {
                        int i = line.indexOf('=');
                        entries.put(line.substring(0, i).strip(), line.substring(i + 1).strip());
                    }
                }
            }
            int tick = Integer.parseInt(entries.getOrDefault("tick_ms", "0"));
            int width = Integer.parseInt(entries.getOrDefault("width", "640"));
            int height = Integer.parseInt(entries.getOrDefault("height", "480"));
            if (tick < 0 || (tick > 0 && tick < 15))
                throw new IllegalArgumentException("tick_ms muss 0 oder mindestens 15 sein");
            if (width < 200 || width > 2048 || height < 200 || height > 2048)
                throw new IllegalArgumentException("Spielfeldgröße muss zwischen 200 und 2048 liegen");
            return new Config(entries.getOrDefault("title", directory.getFileName().toString()),
                    tick, width, height);
        }
    }

    private SpielwerkHost(Path mainFile, Config config, int port) throws IOException {
        this.port = port;
        manager = new GameModule.Manager(mainFile, config);
        editor = new EditorModule(mainFile.getParent(), WEB.resolve("editor"), port);
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", port), 0);
        server.createContext("/", this::handle);
        server.setExecutor(requests);
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 1 || args.length > 3 ||
                (args.length == 3 && !args[1].equals("--port"))) {
            System.err.println("Aufruf: java server-java/ArcadeServer.java <Hauptdatei.java> [--port 8765]");
            System.exit(2);
        }
        Path mainFile = Path.of(args[0]).toAbsolutePath().normalize();
        if (!Files.isRegularFile(mainFile) || !mainFile.toString().endsWith(".java")) {
            System.err.println("Java-Hauptdatei nicht gefunden: " + mainFile);
            System.exit(2);
        }
        int port = args.length == 3 ? Integer.parseInt(args[2]) : 8765;
        if (port < 1 || port > 65535) throw new IllegalArgumentException("Ungültiger Port: " + port);
        if (!Files.isRegularFile(WEB.resolve("index.html"))) {
            System.err.println("Bitte im Projektverzeichnis starten (web/index.html fehlt).");
            System.exit(2);
        }
        Config config = Config.load(mainFile.getParent());
        SpielwerkHost app = new SpielwerkHost(mainFile, config, port);
        Runtime.getRuntime().addShutdownHook(new Thread(app::close, "arcade-shutdown-hook"));
        app.manager.start();
        app.server.start();
        System.out.println("[server] " + config.title() + ": http://127.0.0.1:" + port);
        System.out.println("[server] Java-Hauptdatei: " + mainFile);
        System.out.println("[server] Browser-Button 'Server beenden' oder Strg+C zum Beenden.");
    }

    private void close() {
        if (!closed.compareAndSet(false, true)) return;
        manager.stop();
        server.stop(0);
        requests.shutdownNow();
        System.out.println("[server] Beendet.");
    }

    private void handle(HttpExchange ex) throws IOException {
        try {
            if (editor.handle(ex)) return;
            String path = ex.getRequestURI().getPath();
            String method = ex.getRequestMethod();
            if (method.equals("GET")) {
                switch (path) {
                    case "/" -> send(ex, 200, page(), "text/html; charset=utf-8");
                    case "/health" -> send(ex, 200, "OK\n", "text/plain; charset=utf-8");
                    case "/events" -> events(ex);
                    case "/game/scene.html" -> file(ex, manager.gameDir, "scene.html");
                    case "/game/style.css" -> file(ex, manager.gameDir, "style.css");
                    default -> {
                        if (path.startsWith("/static/")) file(ex, WEB, path.substring(8));
                        else if (path.startsWith("/game/assets/"))
                            file(ex, manager.gameDir.resolve("assets"), path.substring(13));
                        else send(ex, 404, "Not found\n", "text/plain");
                    }
                }
            } else if (method.equals("POST") &&
                    (path.equals("/input") || path.equals("/restart") || path.equals("/shutdown"))) {
                post(ex, path);
            } else {
                send(ex, 404, "Not found\n", "text/plain");
            }
        } catch (Exception exception) {
            System.err.println("[http] " + exception);
            try { send(ex, 500, "Internal error\n", "text/plain"); }
            catch (IOException | IllegalStateException ignored) { }
        } finally {
            // For SSE, events() owns its stream and closes it after disconnect.
            if (!ex.getRequestURI().getPath().equals("/events")) ex.close();
        }
    }

    private String page() throws IOException {
        String html = Files.readString(WEB.resolve("index.html"), StandardCharsets.UTF_8);
        Config cfg = manager.config;
        return html.replace("{{TITLE}}", escapeHtml(cfg.title()))
                .replace("{{WIDTH}}", Integer.toString(cfg.width()))
                .replace("{{HEIGHT}}", Integer.toString(cfg.height()))
                .replace("{{TICK}}", Integer.toString(cfg.tickMs()))
                .replace("{{MAIN}}", escapeHtml(manager.mainFile.getFileName().toString()));
    }

    private static String escapeHtml(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&#39;");
    }

    private void file(HttpExchange ex, Path directory, String name) throws IOException {
        if (!Files.isDirectory(directory)) {
            send(ex, 404, "Not found\n", "text/plain");
            return;
        }
        Path base = directory.toRealPath();
        Path target = base.resolve(name).normalize();
        if (!target.startsWith(base) || !Files.isRegularFile(target) ||
                !target.toRealPath().startsWith(base)) {
            send(ex, 404, "Not found\n", "text/plain");
            return;
        }
        byte[] bytes = Files.readAllBytes(target);
        String lower = target.getFileName().toString().toLowerCase();
        String type = lower.endsWith(".html") ? "text/html; charset=utf-8" :
                lower.endsWith(".css") ? "text/css; charset=utf-8" :
                lower.endsWith(".js") ? "text/javascript; charset=utf-8" :
                lower.endsWith(".svg") ? "image/svg+xml" :
                lower.endsWith(".png") ? "image/png" :
                lower.endsWith(".jpg") || lower.endsWith(".jpeg") ? "image/jpeg" :
                lower.endsWith(".gif") ? "image/gif" :
                lower.endsWith(".webp") ? "image/webp" :
                lower.endsWith(".wav") ? "audio/wav" :
                lower.endsWith(".mp3") ? "audio/mpeg" : "application/octet-stream";
        send(ex, 200, bytes, type);
    }

    private static void send(HttpExchange ex, int code, String data, String type) throws IOException {
        send(ex, code, data.getBytes(StandardCharsets.UTF_8), type);
    }

    private static void send(HttpExchange ex, int code, byte[] data, String type) throws IOException {
        ex.getResponseHeaders().set("Content-Type", type);
        ex.getResponseHeaders().set("Cache-Control", "no-cache");
        ex.getResponseHeaders().set("X-Content-Type-Options", "nosniff");
        ex.sendResponseHeaders(code, data.length);
        try (OutputStream out = ex.getResponseBody()) { out.write(data); }
    }

    private void post(HttpExchange ex, String path) throws IOException {
        // Browser-übergreifende lokale CSRF-Angriffe verhindern: kein CORS,
        // Origin prüfen; zum Herunterfahren zusätzlich einen eigenen Header fordern.
        String origin = ex.getRequestHeaders().getFirst("Origin");
        if (origin != null) {
            URI uri;
            try { uri = URI.create(origin); }
            catch (IllegalArgumentException ignored) {
                send(ex, 403, "Forbidden origin\n", "text/plain"); return;
            }
            if (!"http".equals(uri.getScheme()) || uri.getPort() != port ||
                    !("127.0.0.1".equals(uri.getHost()) || "localhost".equals(uri.getHost()))) {
                send(ex, 403, "Forbidden origin\n", "text/plain"); return;
            }
        }
        if (path.equals("/shutdown")) {
            String fetchSite = ex.getRequestHeaders().getFirst("Sec-Fetch-Site");
            if (!"shutdown".equals(ex.getRequestHeaders().getFirst("X-Arcade-Action")) ||
                    (fetchSite != null && !fetchSite.equals("same-origin") && !fetchSite.equals("none"))) {
                send(ex, 403, "Forbidden\n", "text/plain"); return;
            }
        }
        String header = ex.getRequestHeaders().getFirst("Content-Length");
        int size;
        try { size = header == null ? -1 : Integer.parseInt(header); }
        catch (NumberFormatException ignored) { size = -1; }
        if (size < 0 || size > 500) {
            send(ex, 400, "Bad request\n", "text/plain"); return;
        }
        byte[] content = ex.getRequestBody().readNBytes(size);
        if (content.length != size) {
            send(ex, 400, "Incomplete request\n", "text/plain"); return;
        }
        String message;
        try {
            message = StandardCharsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(content)).toString();
        } catch (java.nio.charset.CharacterCodingException e) {
            send(ex, 400, "Bad UTF-8\n", "text/plain"); return;
        }
        switch (path) {
            case "/input" -> {
                if (manager.input(message)) send(ex, 200, "OK\n", "text/plain");
                else send(ex, 400, "Invalid game event\n", "text/plain");
            }
            case "/restart" -> {
                manager.restart();
                send(ex, 200, "Restart scheduled\n", "text/plain");
            }
            case "/shutdown" -> {
                manager.updateStatus("STOPPED", "Server wird beendet …");
                send(ex, 200, "Shutdown scheduled\n", "text/plain");
                new Thread(() -> {
                    try { Thread.sleep(150); } catch (InterruptedException ignored) { }
                    close();
                }, "arcade-browser-shutdown").start();
            }
            default -> throw new AssertionError(path);
        }
    }

    private void events(HttpExchange ex) throws IOException {
        ex.getResponseHeaders().set("Content-Type", "text/event-stream; charset=utf-8");
        ex.getResponseHeaders().set("Cache-Control", "no-store");
        ex.getResponseHeaders().set("X-Accel-Buffering", "no");
        ex.sendResponseHeaders(200, 0); // Chunked streaming.
        GameModule.Client client = manager.subscribe();
        try (OutputStream out = ex.getResponseBody()) {
            while (!manager.stopping.get() && !closed.get()) {
                GameModule.Message message = client.messages.poll(12, TimeUnit.SECONDS);
                String serialized = message == null ? ": ping\n\n" : sse(message);
                out.write(serialized.getBytes(StandardCharsets.UTF_8));
                out.flush();
            }
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        } catch (IOException ignored) {
            // Browser tab has disconnected.
        } finally {
            manager.unsubscribe(client);
            ex.close();
        }
    }

    private static String sse(GameModule.Message message) {
        StringBuilder sb = new StringBuilder("event: ").append(message.kind()).append('\n');
        for (String part : message.data().replace("\r", "").split("\n", -1))
            sb.append("data: ").append(part).append('\n');
        return sb.append('\n').toString();
    }

    static void removeDirectory(Path path) {
        if (path == null) return;
        try (Stream<Path> stream = Files.walk(path)) {
            for (Path p : stream.sorted(Comparator.reverseOrder()).toList())
                Files.deleteIfExists(p);
        } catch (IOException e) { System.err.println("[server] Aufräumen fehlgeschlagen: " + e); }
    }
}
