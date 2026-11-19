# Spielwerk -- Wenig Code. Viel Spiel.

> Das Programmieren macht oft mehr Spaß und ist motivierender, wenn man Spiele programmiert. Spielwerk macht es Ihnen sehr leicht, Ihr erstes Spiel zu entwerfen und zu realisieren. Viel Spaß! 

Zwei vollständige Spiele in **normalem Java**, die ihre Grafiken in einem Browser ausgeben. **Zwei austauschbare Server** sind enthalten: ein Server in reinem **Java (JDK 17+)** und einer in der **Python-Standardbibliothek**. Beide verwenden dieselbe Browseroberfläche und dasselbe sprachunabhängige Zeilenprotokoll. **Kein pip, npm, Node, Framework, JSON oder zusätzliche Java-Bibliothek** erforderlich.

**Hinweis**: Spielwerk basiert auf Ideen und Konzepten, die bei der Entwicklung einer Umgebung für das [Live View Programming](https://github.com/denkspuren/LiveViewProgramming) entstanden sind. Die Umsetzung und Dokumentation von Spielwerk hat ChatGPT übernommen.

## Handbuch für Studierende und zwei kleine Lernspiele

Im Verzeichnis **[`docs/`](docs/README.md)** liegt ein deutschsprachiges, schrittweise aufgebautes [**Studierendenhandbuch**](docs/HANDBUCH.md) für Programmieren 1. Es erklärt das Zeilenprotokoll, die Eingabeverarbeitung, den Unterschied zwischen ereignis- und zeitgesteuerten Spielen, HTML/CSS-Vorlagen, die Erstellung von SVG-/PNG-Ressourcen, Sounds sowie die wichtige Frage nach Objektgrößen und Kollisionsberechnung. Ergänzend gibt es die [Protokollreferenz](docs/PROTOKOLL.md) und [Übungsaufgaben](docs/AUFGABEN.md).

Zwei **zusätzliche**, bewusst kleine Lernprojekte gehören zum Handbuch (unabhängig von den beiden umfangreicheren Beispielen):

```bash
# Sternenpfad: Tastatur und Mausklick; keine Ticks
java server-java/ArcadeServer.java games/sternenpfad/Sternenpfad.java

# Balllabor: mit Ticks; Animation, Schläger, Kollision
java server-java/ArcadeServer.java games/balllabor/Balllabor.java
```

Die beiden Befehle sind **Alternativen**: vor einem Spielwechsel den laufenden Server beenden. Danach `http://127.0.0.1:8765/` öffnen. Wer Python verwendet, kann die Java-Server-Aufrufe durch `python3 server.py games/.../Datei.java` ersetzen.

## Voraussetzungen

- **Java JDK 17+**, sowohl `java` als auch `javac` im `PATH`.
- **Python 3.10+** nur, wenn Du den alternativen Python-Server verwenden möchtest (`python3` unter Linux/macOS, oft `python` oder `py -3` unter Windows).
- Ein moderner Browser. Alles läuft **lokal** auf `127.0.0.1`.

## Sofort ausprobieren

Im entpackten **Projektverzeichnis** ein Terminal öffnen. **Java ist jetzt die empfohlene, vollständig Java-basierte Startmöglichkeit**. Die Befehle funktionieren mit einem JDK 17 oder neuer, ohne vorheriges Kompilieren des Servers (Java-Source-File-Modus).

### Java-Server (kein Python nötig)

**Space Invaders** (33-ms-Ticks, Pfeiltasten und Leertaste):

```bash
java server-java/ArcadeServer.java games/space_invaders/SpaceInvaders.java
```

**Sokoban** (keine Ticks; Pfeiltasten, `Z` für Rückgängig, `R` bzw. Klick auf **Neu** für Neustart):

```bash
java server-java/ArcadeServer.java games/sokoban/Sokoban.java
```

Passende Startskripte sind `start-space-invaders-java.sh`, `start-sokoban-java.sh` sowie die gleichnamigen `.bat`-Dateien für Windows. Wer den Server zunächst explizit kompilieren will, kann stattdessen `javac -d server-java/build server-java/ArcadeServer.java` und anschließend `java -cp server-java/build ArcadeServer games/sokoban/Sokoban.java` ausführen (das Build-Verzeichnis wird bei Bedarf automatisch von `javac` erstellt).

### Alternativ: Python-Server

```bash
python3 server.py games/space_invaders/SpaceInvaders.java
python3 server.py games/sokoban/Sokoban.java
```

Diese beiden Befehle sind **Alternativen**; bitte nicht gleichzeitig auf demselben Port ausführen. Windows: `py -3 server.py ...`. Auch dafür existieren `.sh`- und `.bat`-Startskripte ohne den Zusatz `-java`.

Anschließend im Browser **http://127.0.0.1:8765/** öffnen. Mit dem roten Button **⏻ Server beenden** rechts oben lassen sich **sowohl Server als auch Java-Spielprozess** nach einer Bestätigung herunterfahren. Alternativ **Strg+C** im Terminal. Um das Spiel zu wechseln, erneut mit der anderen Hauptdatei starten. Beide Server unterstützen `--port 8766`, wenn zwei Spiele gleichzeitig laufen sollen.

**Live-Neustart:** Die `.java`-Datei verändern und speichern. Der Server überwacht alle `.java`-Dateien im Spielordner, kompiliert sie und startet den Java-Prozess neu. Ein Compilerfehler erscheint als lesbare Meldung direkt über dem Spielfeld; nach der Korrektur startet das Spiel automatisch. Der Browser selbst bleibt geöffnet. Das Terminal und das ausklappbare Diagnoseprotokoll zeigen Java-`stderr`.

> Hinweis: Änderungen an `scene.html` oder `style.css` werden beim manuellen Neuladen des Browserfensters sichtbar. Der automatische Java-Neustart reagiert auf `.java`-Änderungen. Die Schaltfläche **↻ Java neu starten** startet nur das Spiel neu; **⏻ Server beenden** fährt auch den Server herunter. Die Browserseite bleibt danach offen und zeigt „Server beendet“ an.

## Technischer Aufbau

```text
 Browser (HTML/CSS/JavaScript)
    │  ↑  Display: Server-Sent Events (SSE)
    │  ↓  Eingabe: HTTP POST /input
    ▼
 Python 3 server.py  ODER  Java 17+ server-java/ArcadeServer.java
    │  ↑  Java stdout: EIN Textbefehl pro Zeile
    │  ↓  Java stdin:  EIN Textereignis pro Zeile
    ▼
 Java-Prozess (javac/java, vom Server gestartet)
```

**Warum SSE und POST statt WebSockets?** Beide sind native Browsertechniken, mit den Standardbibliotheken von Python und Java ohne weitere Abhängigkeiten verfügbar. Für lokale Arcade-Spiele ist der Mehraufwand pro Tastendruck unproblematisch. Ein WebSocket-Transport wäre später austauschbar, ohne das Protokoll mit dem Java-Spiel zu ändern.

### Mini-Protokoll v1, keine Serialisierungsbibliothek

**Java → Server → Browser** (`System.out.println`):

| Ausgabe | Effekt |
|---|---|
| `CREATE foo ship` | Neues Objekt `foo` aus `<template id="ship">` der `scene.html` erzeugen |
| `MOVE foo 120 200` | Position von `foo` auf `x=120`, `y=200` Pixel setzen |
| `SHOW foo` | Objekt sichtbar machen |
| `HIDE foo` | Objekt verstecken |
| `REMOVE foo` | Objekt entfernen |
| `TEXT score Punkte: 100` | Text von `score` setzen; **der gesamte Rest nach `score`** ist der Text |
| `SOUND laser` | `<audio id="laser">` von `scene.html` abspielen |

**Browser → Server → Java** (mit `BufferedReader.readLine()` lesen):

| Eingabe | Bedeutung |
|---|---|
| `KEYDOWN ArrowLeft` | Taste heruntergedrückt (ohne automatische Wiederholungen) |
| `KEYUP ArrowLeft` | Taste losgelassen |
| `KEYDOWN Space` | Leertaste heruntergedrückt |
| `CLICK foo 123 100` | Mausklick auf DOM-Objekt `foo`, Position relativ zum Spielfeld |
| `TICK 33` | Periodisches Simulationsereignis, **nur bei `tick_ms > 0`** |

IDs/Template-Namen/Keycodes: `[A-Za-z][A-Za-z0-9_-]*`, maximal 64 Zeichen. Trennung durch **ein ASCII-Leerzeichen**. Der Server akzeptiert maximal 8192 Zeichen je Ausgabezeile, X/Y ganzzahlig zwischen -10000 und 10000. Texte dürfen Leerzeichen, Doppelpunkte, Umlaute enthalten, aber keinen Zeilenumbruch. Für studentische Spiele muss nichts escaped werden. Java-`stdout` ist für Steuerbefehle reserviert. Für Debugging **`System.err.println`** benutzen.

Ein Spiel benötigt **keinen zusätzlichen Thread**:

```java
BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
String line;
while ((line = in.readLine()) != null) {
    if (line.equals("KEYDOWN ArrowUp")) {
        System.out.println("MOVE frog 120 160");
    }
    if (line.startsWith("TICK ")) {
        // Bewegung simulieren, optional
    }
}
```

Dieses `readLine()` **darf und soll blockieren**. Der Server liefert Ticks auf Wunsch. Ohne Ticks ist die Schleife inaktiv, solange niemand eine Taste drückt. Es gibt im studentischen Programm weder Busy-Waiting noch Nebenläufigkeit. `PrintWriter(System.out, true)` ist ebenfalls geeignet; dafür sorgt der Auto-Flush nach jedem `println()`.

### Spielverzeichnis

```text
games/mein_spiel/
  MeinSpiel.java    # öffentliche Klasse mit main(String[] args)
  game.ini          # Konfiguration
  scene.html        # HTML-Fragmente / <template>s / Audioelemente
  style.css         # Aussehen der Spielobjekte
  assets/           # Bilder, Sounds (freiwillig)
```

Beispiel `game.ini`:

```ini
[game]
title = Mein Spiel
width = 640
height = 480
tick_ms = 0
```

`tick_ms = 0` schaltet die Ticks ab. `tick_ms = 33` sendet circa 30 Ticks pro Sekunde. Wenn Java zu langsam ist, lässt der Server Ticks aus statt sie unbegrenzt aufzustauen. Mehrere Java-Dateien im selben Spielverzeichnis werden zusammen kompiliert (`javac -d`); gestartet wird die per Kommandozeile angegebene Hauptklasse, deren Name dem Java-Dateinamen entspricht. **Packages werden in diesem ersten Prototyp nicht unterstützt.**

Die Spielobjekte gehören vollständig der Java-Logik: Positionen und Kollisionen werden in Java berechnet. Browser-JavaScript kennt nur die sieben Ausgabebefehle und die Erfassung von Maus und Tastatur. `CREATE` klont das erste Wurzelelement eines `<template>` und vergibt seine ID. `MOVE` nutzt `transform: translate3d(...)`, `TEXT` nutzt `textContent` (kein beliebiges HTML aus Java).

### Fehler und Debugging

- **Compile-Fehler:** `javac`-Ausgabe wird im Browser über dem Spiel angezeigt. Änderungen lösen neue Versuche aus.
- **Laufzeitfehler:** Ausgabe auf `stderr` ist im Diagnoseprotokoll und im Terminal sichtbar; Prozessende wird als Status dargestellt.
- **Versehentliche `System.out.println("Hallo")`:** wird als ungültige Protokollzeile angezeigt und nicht als Befehl ausgeführt.
- **Neue Browser-Tabs:** Der Server merkt sich den letzten Zustand der Objekte und spielt ihn nach dem Verbinden erneut aus. Sounds werden nicht erneut abgespielt.
- **Neustart:** vorherigen Prozess stoppen, DOM-Zustand zurücksetzen, neu kompilieren, neuen Java-Prozess starten.
- **Server beenden:** `/shutdown` wird ausschließlich für lokale, explizit bestätigte Browseraktionen angeboten (eigener Header und Origin-Prüfung); Spiel und HTTP-Server werden kontrolliert beendet.

## Grenzen und Weiterentwicklung

Dies ist ein bewusst kleiner, lauffähiger lokaler Lehrprototyp – kein Produktions-Gameserver. Beide Varianten nutzen HTTP/1.1 + SSE/POST statt WebSockets, kompilieren nur Java-Dateien auf oberster Ebene des Spielordners, stellt eine feste Pixelauflösung dar und lässt beliebigen lokalen Java-Code laufen. **Nicht öffentlich im Internet bereitstellen** oder auf einem gemeinsamen Hochschulserver mit unvertrauenswürdigen Studierendeneinsendungen ausführen. Für zentrale Ausführung wären Isolation, Authentifizierung, Limits und Prozess-Sandboxing notwendig.

Mögliche spätere Erweiterungen: `CLASS`/`ROTATE`/`SIZE` als neue Befehle, Multiplayer/Spielstände, Wiederholungen, WebSocket statt SSE/POST, allgemeine Java-Komfortbibliothek, besseres Soundmanagement und ein Aufgabenpaket für Programmieren 1.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Die Tests prüfen Protokollvalidierung, Zustandssynchronisation, HTTP/SSE, laufende Java-Prozesse, automatisches Neukompilieren, Ticks und den Ausschaltknopf **für beide Server**. Java JDK wird für Integrationstests vorausgesetzt.

Die eigentliche Lehrschnittstelle (`CREATE`, `MOVE`, `TEXT`, `KEYDOWN`, `TICK`, usw.) ist für beide Implementierungen identisch; kein Beispielspiel muss angepasst werden. Der Java-Server ist in `server-java/ArcadeServer.java` als **eine überschaubare Datei** realisiert und verwendet `com.sun.net.httpserver.HttpServer`, `ProcessBuilder`, Threads und die üblichen JDK-I/O-Klassen. Er ist etwas ausführlicher als Python, benötigt aber ebenso keinerlei externe Bibliothek.

## Lizenzen

Die Implementierung und die SVG/Sound-Assets sind eigens für dieses Beispiel erstellt. Frei veränderbar und für die Lehre wiederverwendbar (CC0-Lizenz, siehe `LICENSE`).
