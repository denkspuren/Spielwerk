# Spielwerk – Quellcode-Wegweiser, Entwicklung und Tests

Dieses Dokument richtet sich an Entwicklerinnen und Entwickler, die **zum ersten Mal in die Codebasis einsteigen** oder eine Funktion hinzufügen möchten. Es ergänzt das [Architektur- und Konzepthandbuch](ENTWICKLERHANDBUCH.md) und die [technische Protokollreferenz](SCHNITTSTELLEN-UND-DATEN.md).

Ziel ist nicht, jede Quellcodezeile zu kommentieren. Stattdessen beantwortet der Wegweiser die entscheidenden Fragen: **Wo beginnt ein Ablauf? Welche Klasse besitzt welche Verantwortung? Welche Datei muss ich bei einer Änderung anfassen? Wie kann ich überprüfen, dass bestehende Spiele nicht beschädigt wurden?**

---

## 1. Entwicklungsumgebung aufsetzen

Voraussetzungen für die **Java-Servervariante**: JDK **17 oder neuer**, die Befehle `java` und `javac` im `PATH`, ein moderner Browser. Für die alternative Serverimplementierung oder die Python-Testprogramme ist **Python 3.10+** zweckmäßig. Für die Codegenerator-JavaScript-Tests ist **Node.js** nützlich, aber zum Spielen **nicht erforderlich**. Es werden weder Maven/Gradle noch pip/npm-Abhängigkeiten benötigt.

Die Befehle werden im Hauptverzeichnis des Projekts ausgeführt:

```sh
# Server in Java, Spiel in Java
java server-java/ArcadeServer.java games/space_invaders/SpaceInvaders.java

# Server in Java, Spiel in Python
java server-java/ArcadeServer.java games/python_demo/Hallo.py

# Nur Werkstatt; Verzeichnis bei Bedarf anlegen
java server-java/ArcadeServer.java mein-neues-projekt

# Alternativer Webserver in Python, Spiel weiterhin in Java
python3 server.py games/space_invaders/SpaceInvaders.java

# Andere Portnummer
java server-java/ArcadeServer.java games/sternenpfad/Sternenpfad.java --port 8766
```

**Im Browser:** `/` = Spielansicht, `/editor` = Figureneditor, `/editor/scene` = Szeneneditor, jeweils auf dem gewählten Port. Ein Projektordner ohne Hauptdatei leitet `/` nach `/editor` um.

Die kurzen `start-*.sh` bzw. `start-*.bat` verwenden in der aktuellen Korrektur den **Java-Webserver** als Standard. Die ausdrücklich mit `-python-server` benannten Varianten starten den alternativen **Python-Webserver**. Die Serversprache und die **Sprache des Spiels** sind voneinander unabhängig.

### Minimalprobe ohne Oberfläche zu bedienen

```sh
# Bei laufendem Server in einem zweiten Terminal
curl -i http://127.0.0.1:8765/health

# SSE-Nachrichten sichtbar machen (Abbruch mit Strg+C)
curl -N http://127.0.0.1:8765/events

# Ein Ereignis an ein laufendes Spiel schicken
curl -X POST http://127.0.0.1:8765/input \
  -H 'Content-Type: text/plain; charset=utf-8' \
  --data-binary 'KEYDOWN ArrowLeft'
```

Die Kommandos sind Diagnosewerkzeuge. Normale Studierende benötigen sie nicht, weil die Spielansicht die Kommunikation übernimmt.

---

## 2. Repository-Landkarte

```text
Spielwerk/
├── server-java/
│   ├── ArcadeServer.java        # Quellcode-Starter / kompiliert Servermodule
│   ├── SpielwerkHost.java       # Java-HTTP-Router, Ressourcen, SSE, POST
│   ├── GameModule.java         # Spielprozess, Watcher, Ticks, Spielzustand
│   ├── EditorModule.java       # Figuren-API, Export, Asset-Uploads
│   └── SceneModule.java        # Szenen-API, Layout-Validierung, Speichern
├── server.py                   # alternativer Python-Host samt GameManager
├── editor_module.py            # Python-Äquivalent des Figuren-/Dateimoduls
├── scene_module.py             # Python-Äquivalent des Szenenmoduls
├── web/
│   ├── index.html              # Browser-Spielseite mit Platzhaltern
│   ├── app.js                  # DOM-Befehle, Tastatur/Maus, SSE
│   ├── app.css                 # allgemeines Layout der Spielansicht
│   └── editor/
│       ├── index.html          # Figureneditor
│       ├── editor.js           # Entwurf, Vorschau, Export, Speichern
│       ├── editor.css          # Editor-Gestaltung
│       ├── codegen/
│       │   ├── registry.js     # Registrierungs-API
│       │   ├── java.js         # Java-Kopiervorlagen
│       │   └── python.js       # Python-Kopiervorlagen
│       └── scene/
│           ├── index.html      # Szeneneditor
│           ├── scene.js        # Browser-Editor, Interaktion, Laden/Speichern
│           ├── scene-model.js  # reine Validierung/IDs des Szenenformats
│           └── scene.css       # Szeneneditor-Gestaltung
├── games/
│   ├── sternenpfad/            # kleines rein ereignisgesteuertes Beispiel
│   ├── balllabor/              # kleines Tick-Beispiel
│   ├── space_invaders/         # umfangreicheres Tick-Spiel
│   ├── sokoban/                # umfangreicheres ereignisgesteuertes Spiel
│   ├── werkstatt_demo/         # Editor/Scene/Spiel miteinander demonstrieren
│   └── python_demo/            # einfache Python-Spielanwendung
├── tests/                      # Python-Integration und JS-Codegen-Tests
├── docs/                       # Studierenden- und Entwicklerdokumentation
└── start-*.sh / start-*.bat    # komfortable Beispiele für Terminal/Windows
```

**Grundregel für Beiträge:** Ändere zuerst diejenige Komponente, der die Funktion **gehört**. Du musst nicht alle Server, Browserdateien und Spiele gleichzeitig bearbeiten, wenn du nur eine CSS-Form ergänzen möchtest.

---

## 3. Der Java-Einstieg im Detail

### `ArcadeServer.java` – der kleine Vorstarter

**Startpunkt:** `main(String[] args)`.

Das Kommando `java server-java/ArcadeServer.java ...` nutzt den Java-Source-File-Modus, der zwar die angegebene Quelldatei ausführt, aber nicht automatisch das ganze Verzeichnis von Servermodulen baut. Deshalb verwendet der Starter `ToolProvider.getSystemJavaCompiler()` für **vier Klassen** (`SpielwerkHost`, `GameModule`, `EditorModule`, `SceneModule`), schreibt Klassen in ein temporäres Verzeichnis und startet dann mit `ProcessBuilder` die eigentliche Host-Klasse.

Zwei unterschiedliche Prozesse sind wichtig:

1. **Host-Prozess:** `SpielwerkHost` – aus den Servermodulen kompiliert.
2. **Spielprozess:** `SpaceInvaders`, `Sokoban` usw. – wird **vom Spielmodul** gestartet.

Der Vorstarter räumt sein temporäres Buildverzeichnis auf, wenn er endet.

### `SpielwerkHost.java` – HTTP-Einstieg

Wichtige Stellen:

| Code | Aufgabe |
|---|---|
| `Config.load(...)` | Optionale `game.ini` lesen und Grundwerte validieren. |
| `main(...)` | Argumente `.java` / `.py` / Projektordner und `--port` prüfen; lokale Adresse binden. |
| Konstruktor | `GameModule.Manager` und `EditorModule` anlegen, `HttpServer` konfigurieren. |
| `handle(HttpExchange)` | Zuerst Editor-Endpunkte delegieren, sonst Laufzeit-GET-/POST-Pfade behandeln. |
| `page()` | HTML-Platzhalter ersetzen; **nur vorhandene** Werkstattdateien optional einbinden. |
| `file(...)` | Statische Dateien unter ihren jeweiligen Ressourcenwurzeln sicher auflösen. |
| `post(...)` | `/input`, `/restart`, `/shutdown` – Ursprung und Payload prüfen. |
| `events(...)`, `sse(...)` | SSE-Abonnements und Nachrichten-Serialisierung. |
| `close()` | Spiel, HTTP-Server und Request-Executor beenden. |

Der Host sollte **keine** Funktionen enthalten, die Figuren zeichnen, Kollisionen berechnen oder `layout.json` interpretieren.

### `GameModule.java` – die eigentliche Laufzeit

| Typ / Methode | Zweck |
|---|---|
| `validCommand(String)` | Exakt die erlaubten `stdout`-Befehle validieren. |
| `validInput(String)` | `KEYDOWN`, `KEYUP`, `CLICK` von HTTP validieren. |
| `Scene` | Letzten DOM-relevanten Zustand kompakt ablegen; Wiederaufnahme für neue Browserclients. |
| `Manager` | Hauptdatei, aktiver Prozess, Status, Fehler, Clients, Restart und Watcher verwalten. |
| `Manager.subscribe()` | Neuen SSE-Client registrieren und Initialzustand zustellen. |
| `Manager.watch()` | Quelländerungen erkennen und Neubau/Neustart auslösen. |
| `Manager.compileAndLaunch()` | Java-Dateien kompilieren und Hauptklasse starten. |
| `Manager.launchPython()` | Python-Datei über verfügbaren Interpreter mit `-u` starten. |
| `Session` | Einen **konkreten** Spielprozess und dessen Threads/Queues kapseln. |
| `Session.writer()` | Queue → `stdin` mit Flush. |
| `Session.reader()` | `stdout` → Validator → Zustands-Update → SSE. |
| `Session.errors()` | `stderr` → Diagnosen. |
| `Session.ticks()` | Optional Nominal-Ticks erzeugen und bei Rückstau auslassen. |
| `Session.stop()` | Prozess kontrolliert und nötigenfalls zwangsweise beenden. |

Die wichtigste Schutzregel ist in `Manager.command(Session owner, ...)` sichtbar: **Befehle einer alten Sitzung** dürfen nach einem Restart nicht den Zustand des neuen Spiels verändern. Deshalb wird geprüft, ob der sendende Prozess noch `active` ist.

Die interne `Scene` speichert nicht das wirkliche DOM, sondern lediglich die **letzten validierten Befehle je Instanz**. Statische Templates werden bei jedem Browser-Reset aus HTML wieder aufgebaut; die dynamischen Instanzen folgen aus den gespeicherten Befehlen.

---

## 4. Derselbe Vertrag in Python

| Java | Python | Aufgabe |
|---|---|---|
| `SpielwerkHost.Config.load` | `load_config` | `game.ini`. |
| `SpielwerkHost.handle` | `handler_factory` / `Handler.do_GET`, `do_POST` | HTTP-Routing. |
| `GameModule.validCommand` | `parse_command` | stdout-Befehle prüfen. |
| `GameModule.validInput` | `parse_input` | Eingaben prüfen. |
| `GameModule.Scene` | `SceneState` | kompakter Darstellungszustand. |
| `GameModule.Manager` | `GameManager` | Watcher, Neustart, Abonnenten. |
| `GameModule.Session` | `GameSession` | Kindprozess, Pipes, Tick-Thread. |
| `SpielwerkHost.sse` | `sse_format` | SSE-Format. |
| `EditorModule` | `EditorFiles` | Figuren-API und Dateiablage. |
| `SceneModule` | `SceneFiles` + `checked` | JSON-Layout und Szenen-API. |

Die Python-Version verwendet `http.server.ThreadingHTTPServer` und die Standardbibliothek `subprocess`. Für ein Python-Spiel startet sie den Interpreter, mit dem `server.py` selbst läuft (`sys.executable -u`). Die Java-Servervariante sucht dagegen plattformabhängig nach `python3`/`python` im `PATH`. Das unterscheidet sich **intern**, nicht im Protokoll.

**Parität ist ein Entwicklungsziel:** Wer einen neuen HTTP-Endpunkt, eine Validierungsregel oder einen Laufzeitstatus einführt, sollte die andere Serverimplementierung und die gemeinsamen Tests mit aktualisieren.

---

## 5. Der Browser als reine Darstellungsinstanz

[`web/index.html`](../web/index.html) enthält ein Spielfeld `#field`, Fehler- und Diagnosefelder, Status und Bedienbuttons. Der Server ersetzt Platzhalter wie `{{TITLE}}`, `{{WIDTH}}`, `{{HEIGHT}}`, `{{TICK}}` und die drei Werkstatt-Platzhalter für optionales CSS, Templates und Layout.

[`web/app.js`](../web/app.js) ist klein genug, um **von oben nach unten** gelesen zu werden. Die zentralen Methoden sind:

| Funktion | Wirkung |
|---|---|
| `resetScene()` | `scene.html` laden, optional Werkstattvorlagen und statische Szenenobjekte ergänzen, Fokus setzen. |
| `applyCommand(line)` | Die sieben stdout-Kommandos in DOM-Operationen übersetzen. |
| `send(line)` | Browserereignis als HTTP-POST `/input` senden. |
| `statusUpdate(raw)` | Statuscode/-text darstellen. |
| `start()` | SSE-Stream mit `EventSource('/events')` öffnen und Handler registrieren. |

Die Browserseite merkt sich lokal gedrückte Tasten in einem `Set`, sendet keine automatischen Keydown-Wiederholungen und schickt beim Fokusverlust `KEYUP`. Das Spiel kann daher selbst einen Zustand wie `boolean leftPressed` oder `Set<String>` führen. Das `CLICK`-Ereignis wählt die nächstliegende DOM-ID unter dem Mauszeiger, andernfalls `NONE`.

**Achtung zur Reihenfolge:** `web/app.js` führt Reset- und Kommandonachrichten über eine Promise-Kette aus. So wird verhindert, dass ein `MOVE` verarbeitet wird, bevor nach `reset` die HTML-Templates geladen wurden. Eine Änderung an der Ereignisbehandlung muss diese Reihenfolge erhalten.

---

## 6. Figureneditor: Daten → Vorschau → HTML/CSS

[`web/editor/editor.js`](../web/editor/editor.js) enthält derzeit drei zusammengehörige Arbeitsschritte:

1. **Entwurfsmodell bearbeiten:** `project = {version:1, templates:[...]}`, ausgewählte Figur, Ebene, Geometrie, Eigenschaften, Bildliste.
2. **Vorschau aufbauen:** `shapeStyle(layer)` berechnet CSS-Eigenschaften; `renderCanvas()` setzt dieselben auf die Vorschau-Elemente.
3. **Export:** `generate()` erzeugt aus genau diesem Modell die CSS-Regeln und HTML-Templates; `save()` überträgt `design.json`, `scene.html`, `style.css` als Längenbündel.

Wichtige Funktionen: `part`, `robot`, `shapeStyle`, `renderCanvas`, `renderForms`, `generate`, `validate`, `save`, `load`, `uploadImage`, `updateCode`. Der Editor verwaltet selbst **dirty-state**, sodass ungespeicherte Änderungen erkennbar bleiben.

Wenn Du eine neue geometrische Form hinzufügst, überprüfe unbedingt **beide** Pfade: Live-Vorschau und Export. Weil sie den gemeinsamen Stilgenerator `shapeStyle` verwenden, können die CSS-Regeln konsistent bleiben – aber Eigenschaften, Bedienfelder, Validierung und Tests müssen ebenfalls ergänzt werden.

### Rendern einer Figur aus CSS

Eine typische generierte Struktur sieht so aus:

```html
<template id="sw-roboter">
  <div class="sw-sprite sw-root-sw-roboter" data-hitbox="5 7 54 62">
    <div class="sw-layer-0"></div>
    <div class="sw-layer-1"></div>
  </div>
</template>
```

Die zugehörigen Klassen stehen im generierten `spielwerk/style.css`. Dort definieren sie feste Breiten/Höhen, relative Positionen und rein visuelle Transformationen. Die **Spielposition** wird auf der geklonten äußeren Instanz über `translate3d(...)` gesetzt, während Ebenen ihre Rotation/Spiegelung behalten. Bilder werden über `/game/assets/<name>` eingebunden.

### Editor-Backend

[`server-java/EditorModule.java`](../server-java/EditorModule.java) und [`editor_module.py`](../editor_module.py) implementieren die gleichen Lese-/Schreibpfade. Sie nehmen **keine** Spielbefehle entgegen und starten **keine** Kindprozesse. Der Editor legt Ausgaben in `spielwerk/` und hochgeladene Bilder in `assets/` ab.

Beim Speichern ist `design.json` das editierbare Modell. Das generierte HTML/CSS ist ein **Export**, kein zweites manuell zu pflegendes Modell. Gezielte Änderungen an `scene.html`/`style.css` im Spiele-Hauptverzeichnis bleiben davon getrennt.

---

## 7. Szeneneditor: Layout ohne Spiellogik

Die Szenendaten leben in [`web/editor/scene/scene-model.js`](../web/editor/scene/scene-model.js) als reines Objekt `{version, width, height, background, objects}`. Das Modul enthält bewusst **keine DOM-Zugriffe** und kann daher leicht isoliert geprüft werden.

[`scene.js`](../web/editor/scene/scene.js) kümmert sich um Laden, Figurenpalette, Auswahl, Ziehen, Zoom, Raster und Kopiervorschläge. Für die Vorschau wird ein **Shadow Root** mit eigenem `#field` erzeugt; dort werden die Spiel-CSS-Dateien separat geladen. Vorlagen aus `scene.html` und `spielwerk/scene.html` stehen gleichermaßen zur Verfügung. Wenn die Vorlage aus dem Figureneditor stammt, kommen Abmessungen und Kollisionskasten aus `design.json`; andernfalls misst der Editor CSS-Größen einer unsichtbaren Probeinstanz.

Die Speicherung erfolgt mit `POST /editor/api/scene/save` in **eine** Datei: `spielwerk/layout.json`. Das Backend prüft Version, Abmessungen, eindeutige IDs, `static`/`dynamic` und Koordinaten. Die Spielansicht liest die Datei bei einem Reset und legt **nur statische Instanzen** an. Dynamische Einträge bleiben Vorschau/Codevorschlag und werden nicht automatisch mit der Spiellogik synchronisiert.

Die Trennung lässt sich sehr gut am Beispiel [`games/werkstatt_demo`](../games/werkstatt_demo) nachvollziehen:

- `spielwerk/design.json`: Definition des Roboters und der Formen.
- `spielwerk/layout.json`: statische Form und dynamisch geplanter Roboter.
- `SpielwerkDemo.java`: erzeugt und bewegt den Roboter unabhängig von dessen visueller Gestaltung.

---

## 8. Sprachgeneratoren erweitern

Die öffentliche Registrierungsstelle ist [`web/editor/codegen/registry.js`](../web/editor/codegen/registry.js). Ihre Einträge besitzen `id`, `label`, eine verpflichtende `generate({template})`-Funktion und optional `generateScene({scene})`.

Zum Hinzufügen einer weiteren Sprache:

1. Eine neue Datei `web/editor/codegen/meinesprache.js` anlegen, die `window.SpielwerkCodegen.register(...)` aufruft.
2. Das Skript **nach** `registry.js` in `web/editor/index.html` und (wenn Szenenschnipsel gewünscht sind) `web/editor/scene/index.html` einbinden.
3. `generate` implementieren und optional `generateScene`, die ausschließlich `mode === 'dynamic'` berücksichtigt.
4. An Beispielentwürfen prüfen, ob erzeugte Konstanten korrekt sind und Strings richtig escaped werden.
5. Eine Testprüfung nach dem Muster der bestehenden Java-/Python-Generatoren ergänzen.

**Nicht hinzufügen:** automatische Speicherung generierter Quelltexte. Das Verbot ist Teil des Architekturvertrags, damit Spielwerkstatt und Spielprogramm unabhängig bleiben.

Einen **ausführbaren** dritten Spielsprachtyp zu unterstützen, ist eine andere Aufgabe: `GameModule.Manager` und `GameManager` müssten einen Prozessstarter und einen passenden File-Watcher erhalten. Das Format der stdout-/stdin-Befehle soll dabei unverändert bleiben.

---

## 9. Typische Änderungsfälle: eine Checkliste

| Wunsch | An welcher Stelle anfangen? | Danach prüfen |
|---|---|---|
| Neue CSS-Form | `web/editor/editor.js` (`shapeStyle`, Formfelder, Validierung) | Vorschau, Export, beide Server, Editor-Tests |
| Neue Positionshilfe | `web/editor/editor.js` oder `web/editor/scene/scene.js` | Zoom, Raster, Pfeiltasten, Speichern |
| Andere statische Szenendarstellung | `web/app.js` (`resetScene`) | Layout, fehlende optionalen Ressourcen, Neustart |
| Neue Werkstatt-Datei-API | `EditorModule.java` + `editor_module.py` | gleiche Endpunkte, Zugriffsschutz, Dateipfade, Tests |
| Neue Szenen-JSON-Eigenschaft | `scene-model.js`, `scene.js`, `SceneModule.java`, `scene_module.py`, `app.js` | Validierung, Migration/Version, Tests |
| Neuer Spielbefehl | `GameModule.validCommand`, `server.py:parse_command`, `web/app.js:applyCommand` | Reconnect-Snapshot, Beispiel, Protokoll-Doku, Tests |
| Neues Eingabeereignis | `web/app.js`, beide Eingabevalidatoren | Queue, Tastaturzustand, Tests |
| Neuer Status / Compilerfehler-UI | `GameModule.Manager`, `server.py:GameManager`, `web/app.js` | Status-/Fehleranzeige, SSE, Neustart |
| Neue Spielsprache | Prozessstart in beiden Game-Managern | Watcher, stdout, stdin, stderr, Tests |
| Kompatibilitätsproblem Windows/macOS | `start-*.bat`/`.sh`, Java- und Python-Starter | JDK/Python im PATH, Zeilenenden, Port, Windows-Pfade |

Ein nützlicher Grundsatz ist, bei neuen Funktionen **zuerst eine kleine reproduzierbare Testaufgabe** zu formulieren: Welche Zeilen sendet ein Spiel? Welche DOM-Änderung muss erscheinen? Welche Datei wird vom Editor geschrieben – und welche muss unverändert bleiben?

---

## 10. Tests und konkrete Befehle

### Automatisierte Python-Tests

```sh
python3 -m unittest discover -s tests -v
```

Die Testdateien sind nach Verantwortlichkeiten gegliedert:

| Testdatei | Schwerpunkt |
|---|---|
| `tests/test_arcade.py` | Python-Server, Protokoll, HTTP und Spielverhalten. |
| `tests/test_java_server.py` | Java-Server, Prozesse, HTTP/SSE, Fehler. |
| `tests/test_student_examples.py` | Lernspiele Sternenpfad und Balllabor. |
| `tests/test_editor.py` | Editor-APIs, Dateien, Trennung. |
| `tests/test_workshop_codegen.py` | Export und sprachneutrale Codegeneratoren. |
| `tests/test_scene_editor.py` | Szenen-API, Validierung, statisch/dynamisch, Dateischutz. |
| `tests/test_simple_start.py` | Start nach Dateiendung und reiner Werkstattmodus. |
| `tests/test_optional_workshop_resources.py` | Fehlende optionale Werkstattdateien, Serverstartskripte. |

Einzelne Tests lassen sich isolieren, z. B.:

```sh
python3 -m unittest discover -s tests -p 'test_scene_editor.py' -v
python3 -m unittest discover -s tests -p 'test_optional_workshop_resources.py' -v
```

Für JavaScript-Codegeneratoren existiert zusätzlich [`tests/test_workshop_codegen.js`](../tests/test_workshop_codegen.js):

```sh
node tests/test_workshop_codegen.js
```

**Hinweis:** Diese Befehle setzen jeweils die nötigen Interpreter/Compiler voraus. Testläufe mit lokalen HTTP-Servern können Ports oder Prozessstarts benötigen. In einer früheren Prüfphase blieb ein älterer SSE-Integrationstest zeitweise hängen; deshalb bei langen Durchläufen den zuletzt ausgeführten Test notieren und bei Bedarf gezielt wiederholen. Ein grüner isolierter Test ersetzt keinen vollständig abgeschlossenen Gesamtlauf.

### Manuelle Regressionstests

1. `games/sokoban/Sokoban.java` ohne Ticks starten: Pfeiltasten-/Mausereignisse prüfen.
2. `games/balllabor/Balllabor.java` mit Ticks starten: fortlaufende Bewegung prüfen.
3. `.java` absichtlich fehlerhaft speichern: Fehlermeldung im Browser, anschließend korrigieren und Neustart kontrollieren.
4. `games/python_demo/Hallo.py` starten: Ein-/Ausgabe in derselben Syntax prüfen.
5. Ein Spiel **ohne** `spielwerk/` laden: kein ungewollter Abruf optionaler Ressourcen; Spiel funktioniert.
6. `games/werkstatt_demo/` öffnen: Figur speichern, Spielansicht neu laden, neue Gestaltung prüfen.
7. Im Szeneneditor ein **statisches** Objekt verschieben: Speichern + Browser-Neuladen verändert die Szene ohne Codeänderung.
8. Ein **dynamisches** Objekt verschieben: Nur Vorschau und Codeschnipsel ändern sich; Spiellogik bleibt unverändert.
9. Zweiten Spieltab öffnen: Zustand erscheint über den SSE-Snapshot; Sounds werden nicht wiederholt.
10. Browserbutton „Server beenden“ testen: Kindprozess und HTTP-Server werden beendet.

Testet die Änderungen nach Möglichkeit auf Java **und** Python als Server. Ein browserbasierter Editor kann auf der Implementierungsebene besonders leicht versehentlich einen Server-Sonderfall einführen.

---

## 11. Häufige Fehlerbilder und ihre Ursache

| Beobachtung | Erste Prüfschritte |
|---|---|
| Java-Kompilierung schlägt fehl | `java`/`javac` Version, Fehlermeldung im Browser, unbenutzte `.java`-Dateien im selben Spielordner, Packages (der einfache Starter nimmt eine Hauptklasse ohne Paket an). |
| Python-Spiel zeigt nichts | `.py`-Datei als Serverargument, ungepufferte Ausgabe, tatsächlich gültige `CREATE`/`MOVE`-Zeilen, Debug auf `stderr`. |
| `MOVE` hat keine Wirkung | Existiert die ID? Wurde `CREATE` gesendet? Liegt das Template in einer geladenen Szene? Stimmen Groß-/Kleinschreibung und Koordinaten? |
| Spiel nach Editoränderung unverändert | Wurde gespeichert? Spielbrowser **neu laden**; Spiel-Quellcode wird durch Editor nie geändert. |
| `404 /game/spielwerk/...` | Die konkrete Werkstattdatei kann fehlen; das ist bei Spielen ohne Editor normalerweise harmlos. Die aktuelle Spielseite fordert optionale Dateien nur bei Vorhandensein an. Direkte Editor-Vorschauen können fehlende Ressourcen probeweise anfordern. |
| `favicon.ico 404` | Kein funktionaler Spiel-Fehler; aktuelle Spielseite verwendet ein leeres Data-Icon. |
| `ConnectionResetError` im Python-Server | Browser-Verbindung vorzeitig geschlossen. Die neuere Handler-Version behandelt dies; bei älteren Versionen kann ein harmloser Traceback erscheinen. |
| Spiel reagiert nicht auf Tastendrücke | Fensterfokus, `event.code` statt `event.key`, `KEYDOWN`/`KEYUP`-Zustand, korrekter Server und offener Prozess. |
| Ticks sind unregelmäßig | Zu lange Berechnungen, volle Queue, Tick-Verwerfen bei Rückstau. Kein Echtzeitversprechen. |
| Kollisionsfläche scheint „falsch“ | Java-Konstanten vs. CSS-Maße vergleichen; `hit` ist relativ und bleibt bei Rotation/Spiegelung achsenparallel. |
| `git apply --check` schlägt fehl | Der Patch wurde für einen anderen Code-Stand erstellt; **nicht erzwingen**. Betroffene Dateien mit aktuellem Branch vergleichen, Änderungen gezielt übernehmen. |

---

## 12. Sicherheits- und Architektur-Check bei Pull Requests

- **Kein Spielcode überschrieben?** Besonders README, Lizenz, Beispielquellen und handgeschriebene Ressourcen bewusst prüfen.
- **Keine neue Kopplung?** Figuren-/Szeneneditor darf nicht `GameModule` direkt steuern; keine Java-/Python-Datei automatisch schreiben.
- **Dateizugriffe sicher?** Projektverzeichnisbegrenzung, Symlinks, Dateinamen, Dateigrößen, UTF-8, Ursprung und Schreibheader beachten.
- **Browserquellen vertrauenswürdig?** HTML/CSS aus lokalen Ressourcen kann erheblich mehr als reine Grafik. Keine fremden Projekte ohne Prüfung ausführen.
- **Protokoll rückwärtskompatibel?** Validatoren, Parser, SSE-Browser, Snapshot und Dokumentation gemeinsam prüfen.
- **Beide Server getestet?** Nicht nur die gerade bevorzugte Implementierung.
- **Git-Historie respektiert?** Auf aktuellem `dev` entwickeln, kleine gezielte Änderungen statt alte ZIP-Versionen über das Repository kopieren.
- **Unveränderlichkeit der Codevorlagen?** Sprache auswählen oder Schnipsel kopieren darf keine Spielquelle editieren.

### Empfohlener Beitragspfad

```sh
git fetch origin
git switch dev
git pull --ff-only origin dev
# Änderung in wenigen Dateien + passende Tests
python3 -m unittest discover -s tests -v
git status
git diff --check
git diff
git add <gezielt-geänderte-dateien>
git commit -m "Kurze, sachliche Beschreibung"
git push origin dev
```

Danach Pull Request nach `main`, **Files changed** prüfen (insbesondere README/Lizenz) und erst nach der Freigabe mergen. Anschließend `dev` wieder mit `main` synchronisieren. Dieser Ablauf ist kein Bestandteil der Spielruntime, hat sich aber für die Pflege der kleinen, getrennten Architektur als sinnvoll erwiesen.

---

## 13. Was als Nächstes zu pflegen ist

Bei jeder Schnittstellenänderung sollte mindestens eine der drei Entwicklerdateien aktualisiert werden:

- [ENTWICKLERHANDBUCH.md](ENTWICKLERHANDBUCH.md): Absicht, Architekturentscheidungen und Modulgrenzen.
- [SCHNITTSTELLEN-UND-DATEN.md](SCHNITTSTELLEN-UND-DATEN.md): überprüfbare Verträge, Daten- und HTTP-Formate.
- **Diese Datei:** tatsächliche Klassennamen, Änderungspfade, Testabdeckung und praktische Checklisten.

Die Anwenderdokumentation (`HANDBUCH.md`, `PROTOKOLL.md`, `SPIELWERKSTATT.md`, `SZENENEDITOR.md`) muss bei sichtbaren Verhaltensänderungen ebenfalls nachgezogen werden. Die technische Dokumentation ist nur dann nützlich, wenn sie **mit der Implementierung gemeinsam weiterentwickelt** wird.
