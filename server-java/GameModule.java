/* Spielwerk: Spiellogik-Backend (Prozesse, stdin/stdout, Ticks, SSE-Zustand).
 * Keine Editordateien, keine Editor-HTTP-Routen. */
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Stream;
import java.util.regex.Pattern;

final class GameModule {
    private static final Pattern ID = Pattern.compile("[A-Za-z][A-Za-z0-9_-]{0,63}");
    private static final int MAX_LINE = 8192;
    static boolean validId(String value) { return ID.matcher(value).matches(); }

    static boolean boundedNumber(String str) {
        try { return Math.abs(Long.parseLong(str)) <= 10000; }
        catch (NumberFormatException e) { return false; }
    }

    static boolean validCommand(String line) {
        if (line == null || line.isEmpty() || line.length() > MAX_LINE ||
                line.indexOf('\0') >= 0 || line.indexOf('\r') >= 0) return false;
        int sep = line.indexOf(' ');
        if (sep < 0) return false;
        String cmd = line.substring(0, sep);
        String rest = line.substring(sep + 1);
        String[] parts = rest.split(" ", -1);
        return switch (cmd) {
            case "SHOW", "HIDE", "REMOVE", "SOUND" -> validId(rest);
            case "CREATE" -> parts.length == 2 && validId(parts[0]) && validId(parts[1]);
            case "MOVE" -> parts.length == 3 && validId(parts[0]) &&
                    boundedNumber(parts[1]) && boundedNumber(parts[2]);
            case "TEXT" -> {
                int at = rest.indexOf(' ');
                yield at > 0 && validId(rest.substring(0, at)) && rest.length() - at - 1 <= 4000;
            }
            default -> false;
        };
    }

    static boolean validInput(String line) {
        if (line == null || line.isEmpty() || line.length() > 200 ||
                line.indexOf('\0') >= 0 || line.indexOf('\r') >= 0 || line.indexOf('\n') >= 0) return false;
        int sep = line.indexOf(' ');
        if (sep < 0) return false;
        String cmd = line.substring(0, sep);
        String rest = line.substring(sep + 1);
        return switch (cmd) {
            case "KEYDOWN", "KEYUP" -> validId(rest);
            case "CLICK" -> {
                String[] parts = rest.split(" ", -1);
                yield parts.length == 3 && validId(parts[0]) &&
                        boundedNumber(parts[1]) && boundedNumber(parts[2]);
            }
            default -> false;
        };
    }


    record Message(String kind, String data) { }

    static final class Client {
        final BlockingQueue<Message> messages = new ArrayBlockingQueue<>(2000);
        void offer(String kind, String data) { messages.offer(new Message(kind, data)); }
    }

    static final class Scene {
        final Map<String, String> created = new LinkedHashMap<>();
        final Map<String, String> positions = new LinkedHashMap<>();
        final Map<String, String> texts = new LinkedHashMap<>();
        final Map<String, String> visible = new LinkedHashMap<>();
        final Map<String, String> removed = new LinkedHashMap<>();
        void clear() {
            created.clear(); positions.clear(); texts.clear(); visible.clear(); removed.clear();
        }
        void apply(String line) {
            int first = line.indexOf(' ');
            String cmd = line.substring(0, first);
            String rest = line.substring(first + 1);
            String id = rest.split(" ", 2)[0];
            if (cmd.equals("SOUND")) return;
            if (cmd.equals("CREATE")) {
                created.put(id, line); removed.remove(id);
                positions.remove(id); texts.remove(id); visible.remove(id);
            } else if (cmd.equals("REMOVE")) {
                created.remove(id); positions.remove(id); texts.remove(id); visible.remove(id);
                removed.put(id, line);
            } else if (cmd.equals("MOVE")) positions.put(id, line);
            else if (cmd.equals("TEXT")) texts.put(id, line);
            else if (cmd.equals("SHOW") || cmd.equals("HIDE")) visible.put(id, line);
        }
        List<String> snapshot() {
            List<String> result = new ArrayList<>();
            result.addAll(created.values()); result.addAll(positions.values());
            result.addAll(texts.values()); result.addAll(visible.values());
            result.addAll(removed.values());
            return result;
        }
    }

    static final class Manager {
        final Path mainFile;
        final Path gameDir;
        final SpielwerkHost.Config config;
        final Object lock = new Object();
        final Set<Client> clients = new HashSet<>();
        final Scene scene = new Scene();
        final AtomicBoolean stopping = new AtomicBoolean();
        final AtomicBoolean force = new AtomicBoolean();
        volatile Process compiler;
        volatile Thread watcher;
        String code = "STARTING", detail = "Java wird kompiliert …", error = "";
        Session active;
        Path buildDir;

        Manager(Path mainFile, SpielwerkHost.Config config) {
            this.mainFile = mainFile;
            this.gameDir = mainFile.getParent();
            this.config = config;
        }
        void start() {
            watcher = new Thread(this::watch, "arcade-file-watcher");
            watcher.setDaemon(true);
            watcher.start();
        }
        void stop() {
            if (!stopping.compareAndSet(false, true)) return;
            force.set(true);
            Process compiling = compiler;
            if (compiling != null) compiling.destroyForcibly();
            Session old;
            synchronized (lock) { old = active; active = null; }
            if (old != null) old.stop();
            if (watcher != null && watcher != Thread.currentThread()) {
                watcher.interrupt();
                try { watcher.join(3000); } catch (InterruptedException ex) {
                    Thread.currentThread().interrupt();
                }
            }
            SpielwerkHost.removeDirectory(buildDir);
        }
        Client subscribe() {
            Client c = new Client();
            synchronized (lock) {
                clients.add(c);
                c.offer("reset", "");
                c.offer("status", code + "\t" + detail);
                if (!error.isEmpty()) c.offer("compile", error);
                for (String cmd : scene.snapshot()) c.offer("cmd", cmd);
            }
            return c;
        }
        void unsubscribe(Client c) {
            synchronized (lock) { clients.remove(c); }
        }
        void broadcast(String kind, String data) {
            synchronized (lock) { for (Client c : clients) c.offer(kind, data); }
        }
        void updateStatus(String newCode, String newDetail) {
            synchronized (lock) {
                code = newCode; detail = newDetail;
                broadcast("status", code + "\t" + detail);
            }
        }
        void log(String text) {
            broadcast("log", text.length() <= 3000 ? text : text.substring(0, 3000));
            System.err.println("[java] " + text.substring(0, Math.min(500, text.length())));
        }
        void command(Session owner, String cmd) {
            synchronized (lock) {
                if (active != owner) return;
                scene.apply(cmd);
                broadcast("cmd", cmd);
            }
        }
        void finished(Session owner, int exit) {
            synchronized (lock) {
                if (active == owner)
                    updateStatus("STOPPED", "Java-Prozess beendet (Exit-Code " + exit + ").");
            }
        }
        boolean input(String line) {
            if (!validInput(line)) return false;
            Session current;
            synchronized (lock) { current = active; }
            if (current != null) current.put(line);
            return true;
        }
        void restart() { force.set(true); }

        List<String> signature() {
            try (Stream<Path> entries = Files.list(gameDir)) {
                List<String> sig = new ArrayList<>();
                for (Path p : entries.filter(f -> f.getFileName().toString().endsWith(".java"))
                        .sorted().toList()) {
                    sig.add(p + ":" + Files.getLastModifiedTime(p).to(TimeUnit.NANOSECONDS) + ":" + Files.size(p));
                }
                return sig;
            } catch (IOException e) { return List.of(); }
        }
        void watch() {
            List<String> previous = null;
            long changedAt = 0;
            while (!stopping.get()) {
                List<String> current = signature();
                if (!current.equals(previous) || force.getAndSet(false)) {
                    previous = current;
                    changedAt = System.nanoTime();
                }
                if (changedAt != 0 && System.nanoTime() - changedAt >= 350_000_000L) {
                    changedAt = 0;
                    compileAndLaunch();
                }
                try { Thread.sleep(100); }
                catch (InterruptedException interrupted) { if (stopping.get()) return; }
            }
        }
        void compileError(String message) {
            synchronized (lock) {
                error = message.isBlank() ? "Unbekannter Compilerfehler" : message;
                updateStatus("COMPILE_ERROR", "Kompilierung fehlgeschlagen");
                broadcast("compile", error);
            }
            System.err.println("[compiler]\n" + message);
        }
        void compileAndLaunch() {
            Session prior;
            synchronized (lock) {
                prior = active;
                active = null;
                scene.clear();
                error = "";
                broadcast("reset", "");
                broadcast("compile", "");
                updateStatus("STARTING", "Java wird kompiliert …");
            }
            if (prior != null) prior.stop();
            if (stopping.get()) return;
            List<Path> files;
            try (Stream<Path> stream = Files.list(gameDir)) {
                files = stream.filter(p -> p.getFileName().toString().endsWith(".java"))
                        .sorted().toList();
            } catch (IOException ex) { compileError(ex.toString()); return; }
            if (files.isEmpty() || !Files.isRegularFile(mainFile)) {
                compileError("Keine Java-Quelldateien bzw. Hauptdatei nicht gefunden."); return;
            }
            Path build;
            try { build = Files.createTempDirectory("arcade-classes-"); }
            catch (IOException e) { compileError(e.toString()); return; }
            List<String> compileArgs = new ArrayList<>(List.of("javac", "-encoding", "UTF-8",
                    "-d", build.toString()));
            for (Path source : files) compileArgs.add(source.toString());
            try {
                Process process = new ProcessBuilder(compileArgs).directory(gameDir.toFile())
                        .redirectErrorStream(true).start();
                compiler = process;
                StringBuilder output = new StringBuilder();
                Thread collector = new Thread(() -> {
                    try (BufferedReader in = new BufferedReader(new InputStreamReader(
                            process.getInputStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = in.readLine()) != null) {
                            synchronized (output) {
                                if (output.length() < 200_000) output.append(line).append('\n');
                            }
                        }
                    } catch (IOException ignored) { }
                }, "arcade-javac-output");
                collector.setDaemon(true);
                collector.start();
                boolean exited = process.waitFor(30, TimeUnit.SECONDS);
                if (!exited) {
                    process.destroyForcibly();
                    process.waitFor();
                }
                collector.join(1500);
                compiler = null;
                if (stopping.get()) { SpielwerkHost.removeDirectory(build); return; }
                if (!exited || process.exitValue() != 0) {
                    compileError(!exited ? "javac: Zeitlimit von 30 Sekunden überschritten" : output.toString());
                    SpielwerkHost.removeDirectory(build);
                    return;
                }
            } catch (IOException ex) {
                compiler = null;
                SpielwerkHost.removeDirectory(build);
                if (!stopping.get()) compileError("javac konnte nicht ausgeführt werden: " + ex);
                return;
            } catch (InterruptedException ex) {
                compiler = null;
                SpielwerkHost.removeDirectory(build);
                if (!stopping.get()) compileError("javac wurde unterbrochen: " + ex);
                Thread.currentThread().interrupt();
                return;
            }
            if (stopping.get()) { SpielwerkHost.removeDirectory(build); return; }
            SpielwerkHost.removeDirectory(buildDir);
            buildDir = build;
            try {
                Process game = new ProcessBuilder("java", "-cp", build.toString(),
                        mainFile.getFileName().toString().replaceFirst("\\.java$", ""))
                        .directory(gameDir.toFile()).start();
                Session session = new Session(this, game);
                synchronized (lock) {
                    active = session;
                    updateStatus("RUNNING", "Spiel läuft");
                }
                session.launch(config.tickMs());
                System.out.println("[server] Started " + mainFile.getFileName() +
                        " (PID " + game.pid() + ", tick " + config.tickMs() + " ms)");
            } catch (IOException e) { compileError("Java konnte nicht gestartet werden: " + e); }
        }
    }

    static final class Session {
        final Manager manager;
        final Process process;
        final BlockingQueue<String> inputs = new ArrayBlockingQueue<>(1000);
        final AtomicBoolean stopping = new AtomicBoolean();
        final List<Thread> threads = new ArrayList<>();
        Session(Manager manager, Process process) { this.manager = manager; this.process = process; }
        void launch(int tickMs) {
            spawn("stdin", this::writer);
            spawn("stdout", this::reader);
            spawn("stderr", this::errors);
            spawn("exit", this::waitForExit);
            if (tickMs > 0) spawn("ticks", () -> ticks(tickMs));
        }
        void spawn(String name, Runnable job) {
            Thread t = new Thread(job, "arcade-java-" + name);
            t.setDaemon(true);
            threads.add(t);
            t.start();
        }
        void put(String message) {
            if (!stopping.get() && process.isAlive() && !inputs.offer(message))
                manager.log("Eingabe-Warteschlange voll; Ereignis verworfen");
        }
        void writer() {
            try (BufferedWriter out = new BufferedWriter(new OutputStreamWriter(
                    process.getOutputStream(), StandardCharsets.UTF_8))) {
                while (!stopping.get()) {
                    String line = inputs.poll(200, TimeUnit.MILLISECONDS);
                    if (line != null) { out.write(line); out.newLine(); out.flush(); }
                }
            } catch (IOException ignored) {
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
        }
        void reader() {
            try (BufferedReader in = new BufferedReader(new InputStreamReader(
                    process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = in.readLine()) != null && !stopping.get()) {
                    if (validCommand(line)) manager.command(this, line);
                    else manager.log("Ungültige stdout-Zeile (stderr für Debugging): " +
                            line.substring(0, Math.min(250, line.length())));
                }
            } catch (IOException ignored) { }
        }
        void errors() {
            try (BufferedReader in = new BufferedReader(new InputStreamReader(
                    process.getErrorStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = in.readLine()) != null && !stopping.get()) manager.log(line);
            } catch (IOException ignored) { }
        }
        void waitForExit() {
            try { int code = process.waitFor();
                if (!stopping.get()) manager.finished(this, code);
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
        }
        void ticks(int ms) {
            long nanos = ms * 1_000_000L;
            long next = System.nanoTime() + nanos;
            while (!stopping.get() && process.isAlive()) {
                long delay = next - System.nanoTime();
                if (delay > 0) {
                    try { TimeUnit.NANOSECONDS.sleep(delay); }
                    catch (InterruptedException interrupted) { return; }
                }
                if (stopping.get()) break;
                if (inputs.size() < 8) put("TICK " + ms);
                next += nanos;
                if (next < System.nanoTime() - nanos) next = System.nanoTime() + nanos;
            }
        }
        void stop() {
            if (!stopping.compareAndSet(false, true)) return;
            process.destroy();
            try {
                if (!process.waitFor(2, TimeUnit.SECONDS)) {
                    process.destroyForcibly();
                    process.waitFor(2, TimeUnit.SECONDS);
                }
            } catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
            for (Thread t : threads) t.interrupt();
            try { process.getOutputStream().close(); } catch (IOException ignored) { }
            try { process.getInputStream().close(); } catch (IOException ignored) { }
            try { process.getErrorStream().close(); } catch (IOException ignored) { }
        }
    }

}
