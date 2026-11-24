/* Spielwerkstatt: eigenständiges Datei-/Editor-Modul.
 * Keine Referenz auf GameModule, Java-Prozesse oder das Spielprotokoll.
 * Alle Änderungen liegen ausschließlich unter <spiel>/spielwerk/ bzw. assets/.
 */
import com.sun.net.httpserver.HttpExchange;
import java.io.*;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;

final class EditorModule {
    private static final int MAX_BUNDLE = 900_000;
    private static final int MAX_ASSET = 2_000_000;
    private static final Pattern ASSET_NAME = Pattern.compile("[A-Za-z0-9_-]{1,64}\\.(png|jpg|jpeg|gif|webp)", Pattern.CASE_INSENSITIVE);
    private final Path gameDir, editorWeb, outputDir;
    private final SceneModule scene;
    private final int port;

    EditorModule(Path gameDir, Path editorWeb, int port) {
        this.gameDir = gameDir.toAbsolutePath().normalize();
        this.editorWeb = editorWeb.toAbsolutePath().normalize();
        this.outputDir = this.gameDir.resolve("spielwerk");
        this.port = port;
        this.scene = new SceneModule(this.gameDir, this.editorWeb);
    }

    /** True: request owned by EditorModule, even when rejected with 404/403. */
    boolean handle(HttpExchange ex) throws IOException {
        String path = ex.getRequestURI().getPath();
        String method = ex.getRequestMethod();
        if (method.equals("GET") && scene.get(ex, path)) return true;
        if (method.equals("GET") && path.startsWith("/game/spielwerk/")) {
            String name = path.substring("/game/spielwerk/".length());
            if (name.equals("scene.html") || name.equals("style.css")) serveFile(ex, outputDir.resolve(name));
            else send(ex, 404, "Nicht gefunden");
            return true;
        }
        if (!path.equals("/editor") && !path.startsWith("/editor/")) return false;
        if (method.equals("GET")) {
            if (path.matches("/editor/codegen/[a-z][a-z0-9_-]*\\.js")) {
                serveFile(ex, editorWeb.resolve(path.substring("/editor/".length())));
                return true;
            }
            switch (path) {
                case "/editor", "/editor/" -> serveFile(ex, editorWeb.resolve("index.html"));
                case "/editor/editor.js" -> serveFile(ex, editorWeb.resolve("editor.js"));
                case "/editor/editor.css" -> serveFile(ex, editorWeb.resolve("editor.css"));
                case "/editor/api/design" -> {
                    Path file = outputDir.resolve("design.json");
                    if (Files.isRegularFile(file)) serveFile(ex, file);
                    else send(ex, 200, "{\"version\":1,\"templates\":[]}", "application/json; charset=utf-8");
                }
                case "/editor/api/assets" -> assets(ex);
                default -> send(ex, 404, "Nicht gefunden");
            }
        } else if (method.equals("POST")) {
            if (!trusted(ex)) { send(ex, 403, "Unzulässiger Ursprung"); return true; }
            if (scene.post(ex, path)) return true;
            if (path.equals("/editor/api/save")) save(ex);
            else if (path.startsWith("/editor/api/assets/")) upload(ex, path.substring("/editor/api/assets/".length()));
            else send(ex, 404, "Nicht gefunden");
        } else send(ex, 405, "Methode nicht erlaubt");
        return true;
    }

    private boolean trusted(HttpExchange ex) {
        String host = ex.getRequestHeaders().getFirst("Host");
        if (host == null || !(host.equals("127.0.0.1:" + port) || host.equals("localhost:" + port))) return false;
        String origin = ex.getRequestHeaders().getFirst("Origin");
        if (origin != null && !(origin.equals("http://127.0.0.1:" + port) || origin.equals("http://localhost:" + port))) return false;
        String site = ex.getRequestHeaders().getFirst("Sec-Fetch-Site");
        return (site == null || site.equals("same-origin") || site.equals("none")) &&
                "save".equals(ex.getRequestHeaders().getFirst("X-Spielwerk-Editor"));
    }

    private void save(HttpExchange ex) throws IOException {
        byte[] bytes = body(ex, MAX_BUNDLE);
        if (bytes == null) return;
        int[] lineEnds = new int[3];
        int from = 0;
        for (int i = 0; i < 3; i++) {
            int next = -1;
            for (int j = from; j < Math.min(bytes.length, from + 10); j++) if (bytes[j] == '\n') {next = j; break;}
            if (next < 0) { send(ex, 400, "Ungültiges Paketformat"); return; }
            lineEnds[i] = next;
            from = next + 1;
        }
        try {
            int a = Integer.parseInt(new String(bytes, 0, lineEnds[0], StandardCharsets.US_ASCII));
            int b = Integer.parseInt(new String(bytes, lineEnds[0]+1, lineEnds[1]-lineEnds[0]-1, StandardCharsets.US_ASCII));
            int c = Integer.parseInt(new String(bytes, lineEnds[1]+1, lineEnds[2]-lineEnds[1]-1, StandardCharsets.US_ASCII));
            int start = lineEnds[2] + 1;
            if (a < 2 || b < 0 || c < 0 || a > 250_000 || b > 250_000 || c > 250_000 ||
                    (long)start+a+b+c != bytes.length) {send(ex, 400, "Ungültige Längen"); return;}
            Files.createDirectories(outputDir);
            if (Files.isSymbolicLink(outputDir)) {send(ex,403,"Symbolische Links nicht erlaubt"); return;}
            synchronized(this) {
                // Zusammengehörige Dateien werden erst vollständig staged und dann ersetzt.
                Path d = stage("design.json", Arrays.copyOfRange(bytes, start, start+a));
                Path h = stage("scene.html", Arrays.copyOfRange(bytes, start+a, start+a+b));
                Path s = stage("style.css", Arrays.copyOfRange(bytes, start+a+b, start+a+b+c));
                try {
                    publish(d, outputDir.resolve("design.json"));
                    publish(h, outputDir.resolve("scene.html"));
                    publish(s, outputDir.resolve("style.css"));
                } finally { Files.deleteIfExists(d); Files.deleteIfExists(h); Files.deleteIfExists(s); }
            }
            send(ex, 200, "Gespeichert");
        } catch (NumberFormatException e) {send(ex, 400, "Ungültiges Paketformat");}
    }

    private Path stage(String name, byte[] bytes) throws IOException {
        Path file = Files.createTempFile(outputDir, "sw-", "-" + name);
        Files.write(file, bytes);
        return file;
    }
    private void publish(Path from, Path to) throws IOException {
        try { Files.move(from, to, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
        catch (AtomicMoveNotSupportedException e) { Files.move(from, to, StandardCopyOption.REPLACE_EXISTING); }
    }

    private void upload(HttpExchange ex, String name) throws IOException {
        if (!ASSET_NAME.matcher(name).matches()) {send(ex, 400, "Nur PNG, JPG, GIF oder WebP mit sicherem Dateinamen"); return;}
        byte[] data = body(ex, MAX_ASSET);
        if (data == null) return;
        String suffix = name.substring(name.lastIndexOf('.')+1).toLowerCase(Locale.ROOT);
        boolean valid = switch(suffix) {
            case "png" -> data.length > 8 && data[0]==(byte)0x89 && data[1]==0x50 && data[2]==0x4e && data[3]==0x47;
            case "jpg", "jpeg" -> data.length > 3 && data[0]==(byte)0xff && data[1]==(byte)0xd8 && data[2]==(byte)0xff;
            case "gif" -> data.length > 6 && new String(data,0,3,StandardCharsets.US_ASCII).equals("GIF");
            case "webp" -> data.length > 12 && new String(data,0,4,StandardCharsets.US_ASCII).equals("RIFF") && new String(data,8,4,StandardCharsets.US_ASCII).equals("WEBP");
            default -> false;
        };
        if (!valid) {send(ex, 415, "Bildformat passt nicht zur Dateiendung"); return;}
        Path assets = gameDir.resolve("assets");
        Files.createDirectories(assets);
        if (Files.isSymbolicLink(assets)) {send(ex,403,"Symbolische Links nicht erlaubt");return;}
        Files.write(assets.resolve(name), data, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        send(ex, 200, "Bild hochgeladen");
    }

    private void assets(HttpExchange ex) throws IOException {
        Path assets = gameDir.resolve("assets");
        List<String> names = new ArrayList<>();
        if (Files.isDirectory(assets)) try (var paths = Files.list(assets)) {
            for (Path p: paths.sorted().toList()) {
                String name = p.getFileName().toString();
                if (Files.isRegularFile(p) && (ASSET_NAME.matcher(name).matches() || name.matches("[A-Za-z0-9_-]{1,64}\\.svg")))
                    names.add("\""+name+"\"");
            }
        }
        send(ex,200,"["+String.join(",",names)+"]","application/json; charset=utf-8");
    }

    private byte[] body(HttpExchange ex, int limit) throws IOException {
        int length;
        try {length=Integer.parseInt(ex.getRequestHeaders().getFirst("Content-Length"));}
        catch(Exception e) {send(ex,411,"Content-Length erforderlich");return null;}
        if (length < 0 || length > limit) {send(ex,413,"Datei zu groß");return null;}
        byte[] bytes=ex.getRequestBody().readNBytes(length);
        if(bytes.length!=length) {send(ex,400,"Unvollständige Anfrage");return null;}
        return bytes;
    }
    private void serveFile(HttpExchange ex, Path target) throws IOException {
        if (!Files.isRegularFile(target) || (!target.toRealPath().startsWith(gameDir.toRealPath()) && !target.toRealPath().startsWith(editorWeb.toRealPath()))) {send(ex,404,"Nicht gefunden");return;}
        String name=target.getFileName().toString();
        String type=name.endsWith(".css")?"text/css; charset=utf-8":
                name.endsWith(".js")?"text/javascript; charset=utf-8":
                name.endsWith(".json")?"application/json; charset=utf-8":"text/html; charset=utf-8";
        send(ex,200,Files.readAllBytes(target),type);
    }
    private static void send(HttpExchange ex, int status, String data) throws IOException {send(ex,status,data,"text/plain; charset=utf-8");}
    private static void send(HttpExchange ex, int status, String data,String type) throws IOException {send(ex,status,data.getBytes(StandardCharsets.UTF_8),type);}
    private static void send(HttpExchange ex, int status, byte[] data, String type) throws IOException {
        ex.getResponseHeaders().set("Content-Type",type);
        ex.getResponseHeaders().set("Cache-Control","no-store");
        ex.getResponseHeaders().set("X-Content-Type-Options","nosniff");
        ex.sendResponseHeaders(status,data.length);
        try(OutputStream out=ex.getResponseBody()){out.write(data);}
    }
}
