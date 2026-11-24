/* Spielwerk: Java-Quellcode-Starter (JDK 17+, ohne Build-Tool).
 * java server-java/ArcadeServer.java <Spiel.java | Spiel.py | Projektordner>
 * Kompiliert die getrennten Server-Module in ein temporäres Verzeichnis.
 */
import java.io.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;
public class ArcadeServer {
    public static void main(String[] args) throws Exception {
        Path sources = Path.of("server-java").toAbsolutePath();
        Path build = Files.createTempDirectory("spielwerk-server-");
        Process child = null;
        int exitCode = 0;
        try {
            JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
            if (compiler == null) throw new IllegalStateException("JDK 17+ (mit javac) benötigt");
            int status = compiler.run(null, System.err, System.err,
                "-encoding", "UTF-8", "-d", build.toString(),
                sources.resolve("SpielwerkHost.java").toString(),
                sources.resolve("GameModule.java").toString(),
                sources.resolve("EditorModule.java").toString(),
                sources.resolve("SceneModule.java").toString());
            if (status != 0) throw new IllegalStateException("Servermodule konnten nicht kompiliert werden");
            List<String> cmd = new ArrayList<>(List.of("java", "-cp", build.toString(), "SpielwerkHost"));
            cmd.addAll(List.of(args));
            child = new ProcessBuilder(cmd).inheritIO().start();
            Process process = child;
            Runtime.getRuntime().addShutdownHook(new Thread(process::destroy));
            exitCode = child.waitFor();
        } finally {
            if (child != null && child.isAlive()) child.destroy();
            try (var files = Files.walk(build)) {
                for (Path path : files.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(path);
            }
        }
        System.exit(exitCode);
    }
}
