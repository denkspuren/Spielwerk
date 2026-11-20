# Architektur: Spielwerk und Spielwerkstatt getrennt halten

## Ziel

Die **Spielausführung** und das **Bearbeiten grafischer Ressourcen** sind zwei unabhängige Verantwortlichkeiten. Sie teilen sich ausschließlich den lokalen HTTP-Server als Transport- und Dateizugriffsschicht.

```text
                        Browser
               ┌──────────┴───────────┐
               │                      │
           / (Spiel)              /editor (Editor)
               │                      │
        /events, /input        /editor/api/*
               │                      │
        ┌──────▼──────┐       ┌───────▼────────┐
        │ GameModule  │       │  EditorModule  │
        │ Prozesse    │       │ Entwurfsdatei  │
        │ Ticks       │       │ HTML-/CSS-Export│
        │ stdout/SSE  │       │ Bild-Upload    │
        └──────┬──────┘       └───────┬────────┘
               │                      │
      Java-Spielprozess       spielwerk/*, assets/*
               │                      │
               └────── Spielverzeichnis ───────┘
```

## Komponenten

- `server-java/ArcadeServer.java` ist ein kleiner **Starter**. Da die direkte Java-Quellcodeausführung (`java Datei.java`) nicht automatisch weitere `.java`-Dateien kompiliert, kompiliert er die Servermodule beim Start mit dem JDK-Compiler in ein temporäres Verzeichnis und startet `SpielwerkHost` als eigenen Java-Prozess. Die bekannte Startzeile funktioniert weiterhin, ohne Gradle oder Maven.
- `server-java/SpielwerkHost.java` ist der **HTTP-Einstiegspunkt**. Er leitet `/editor*` und `/game/spielwerk/*` an das Editormodul weiter; Spiel-Ereignisse, Status und Standardressourcen gehören dem Spielmodul. Er enthält keine Gestaltungsvorgaben oder Editor-Dateiverarbeitung.
- `server-java/GameModule.java` kapselt **Spielzustand, Java-Prozessstart, Ticks, stdin/stdout und das Abonnement der Spielereignisse**. Es kennt die Editor-API nicht.
- `server-java/EditorModule.java` kapselt **Editor-HTTP-Endpunkte, Entwurfsspeicherung, generierte Ressourcen und Bild-Upload**. Es kennt weder `GameModule` noch Java-Prozesse.
- `web/app.js`, `web/app.css`, `web/index.html` sind die reine **Spielansicht**. Sie laden die optionalen Editor-Templates als zusätzliche Ressourcen.
- `web/editor/*` ist die unabhängige **Editoroberfläche**, die aus ihrem eigenen Entwurfsmodell HTML und CSS erzeugt.
- Die Python-Variante behält dieselbe Trennung: `server.py` ist Spielserver und Router; `editor_module.py` verwaltet Editorressourcen.

## Dateigrenze statt gemeinsamer Programmlogik

Die einzige Schnittstelle vom Editor zur Spielansicht besteht aus zwei generierten Dateien (`spielwerk/scene.html`, `spielwerk/style.css`). Der Editor überschreibt **niemals** die ursprünglichen `scene.html` und `style.css`.

Der Browser lädt beim Start die normalen Ressourcen und, falls vorhanden, die Editorressourcen zusätzlich. Instanzen werden weiter ausschließlich über `CREATE`, `MOVE` und die übrigen Spielbefehle gesteuert. Die Editoroberfläche sendet **keine** Befehle direkt in den Java-Spielprozess.

Der Editor speichert seinen Zustand als JSON. **Das Spielprotokoll bleibt unverändert zeilenorientierter Klartext.** Beide Formate haben bewusst verschiedene Aufgaben.

## HTTP-Endpunkte

| Pfad | Zuständigkeit | Bedeutung |
|---|---|---|
| `/`, `/events`, `/input`, `/restart`, `/shutdown` | Spielserver | Spiel, Prozess, Ereignisse |
| `/game/scene.html`, `/game/style.css`, `/game/assets/*` | Spielserver | Klassische Ressourcen |
| `/editor` | Editor | Grafische Oberfläche |
| `/editor/api/design` (GET) | Editor | Editierbaren Entwurf lesen |
| `/editor/api/save` (POST) | Editor | Entwurf + HTML + CSS zusammen speichern |
| `/editor/api/assets` (GET) | Editor | Verfügbare Bilder auflisten |
| `/editor/api/assets/<Datei>` (POST) | Editor | PNG/JPG/GIF/WebP hochladen |
| `/game/spielwerk/scene.html`, `/game/spielwerk/style.css` | Editor | Generierte Vorlagen für die Spielansicht |

Die API ist eine interne, kleine Schnittstelle; bei `save` werden drei UTF-8-Dateien in einem einfachen längenkodierten Bündel übertragen. Der HTTP-Server parst weder die Spielbefehle als JSON noch die grafischen Elemente.

## Grenzen und Sicherheit

Beide Server binden ausschließlich an `127.0.0.1`. Schreibzugriffe fordern einen eigens gesetzten Header und prüfen `Origin`, `Host` und `Sec-Fetch-Site`. Hochgeladene Bilder sind auf unterstützte Typen und 2 MB begrenzt. Die generierten Dateien werden nur im Spielordner abgelegt; der Editor ist **nicht** für einen öffentlich erreichbaren Server konzipiert.

Die drei gespeicherten Dateien werden zuerst einzeln temporär geschrieben und danach ersetzt. Bei einem abrupten Ausfall **während** der drei Dateiumbenennungen ist noch keine vollständig transaktionale Speicherung garantiert. Für ein lokales Lehrwerkzeug ist dies ein bewusster Kompromiss.

In der ersten Version ist die Spielwerkstatt ein **Figureneditor**. Erweiterungen wie Szenenlayout, zeitliche Animationen oder zusätzliche Zeichenwerkzeuge gehören in `web/editor/*` und `EditorModule`, nicht in `GameModule`. Ebenso gehören Änderungen am Spielprotokoll allein in das Spielmodul und die Spielansicht, niemals in den Editor.

## Tests

`python3 -m unittest discover -s tests -v` prüft beide Server, die alten Spielbeispiele, Dateitrennung, die Editor-Endpoints und die Abwehr fremder Schreibzugriffe. Die Browseroberfläche kann außerdem ohne echten Java-Prozess durch simulierte Fetch-Antworten getestet werden.

## Figurenformen und austauschbare Codegeneratoren

Die Editor-Vorschau und der HTML-/CSS-Export verwenden **dieselbe** Abbildung von den geometrischen Ebenen aus `design.json` auf CSS-Eigenschaften. Rechtecke, Ellipsen, Dreiecke (`clip-path`) und Kreisbögen (`conic-gradient` mit `mask-image`) bleiben reine **Editorressourcen**. An der Spielprozesssteuerung, am Textprotokoll und am `GameModule` wurde dafür nichts geändert.

Die Anzeige von Programmschnipseln ist zusätzlich als eigenständige **Lese- und Kopierfunktion** organisiert:

```text
spielwerk/design.json  (sprachneutrale Figur + Kollisionsrechteck)
           │
           ├─► HTML/CSS-Export ─► spielwerk/scene.html, style.css
           │
           └─► Codegen-Registry (nur lesend, im Browser)
                       ├─► java.js   ─► Textvorschlag zum Kopieren
                       ├─► python.js ─► Textvorschlag zum Kopieren
                       └─► weitere Sprache als eigenes Skript
```

Die Werkstatt **schreibt niemals in `.java`- oder `.py`-Dateien**. Beim Speichern werden wie bisher nur `spielwerk/design.json`, `spielwerk/scene.html` und `spielwerk/style.css` aktualisiert, gegebenenfalls zusätzlich vom Benutzer hochgeladene Bilddateien. Der Java- und der Python-Server liefern unter `/editor/codegen/<sprache>.js` lediglich lokal mitgelieferte, lesbare Skripte aus. Diese besitzen keine eigene HTTP-Schreibschnittstelle.

Sprachneutralität umfasst zwei unabhängig erweiterbare Bereiche: **(a)** grafische Ressourcen und Schnipselvorschläge in der Werkstatt, **(b)** Start und Überwachung der eigentlichen Spielprozesse. Zurzeit startet das Spielmodul Java-Programme. Ein Python-Spielprozess wäre künftig über einen separaten Startadapter im **GameModule** zu ergänzen. Das vorhandene `stdin`/`stdout`-Protokoll müsste dazu nicht verändert werden.
