# Spielwerk – Schnittstellen, Protokolle und Datenformate

**Technische Referenz zur aktuellen Implementierung.** Diese Beschreibung gehört zum [Entwicklerhandbuch](ENTWICKLERHANDBUCH.md). Sie behandelt die drei Verträge, die bei der Entwicklung auseinandergehalten werden müssen:

1. **Spielprotokoll:** `stdout`/`stdin` zwischen Spielprozess und Server – zeilenbasiert, UTF-8, **kein JSON**.
2. **Browsertransport:** HTTP, Server-Sent Events (SSE) und HTTP-POST zwischen Browser und lokalem Host.
3. **Werkstattdaten:** HTTP-Speicher-APIs sowie `design.json`, `layout.json`, exportiertes HTML/CSS und Bilder – sprachneutral, teilweise JSON.

**Konventionen:** `id` bezeichnet eine DOM-Instanz oder ein vorhandenes Element; `template` die ID eines unsichtbaren HTML-Templates. Eine `id` ist **nicht** die Java-Variable eines Objekts. Pfade beginnen relativ zum **Repository-Hauptverzeichnis**, sofern ausdrücklich nichts anderes angegeben wird.

---

## 1. Spielprozess → Server: Darstellungsbefehle

- Medium: Standardausgabe (`stdout`) des getrennten Prozesses.
- Kodierung: **UTF-8**; eine Nachricht ist eine Zeile mit abschließendem Zeilenumbruch (`\n`; typische Plattform-Zeilenenden werden durch zeilenweises Lesen verarbeitet).
- Befehlsnamen: Großbuchstaben; Trennung der Felder durch einzelne Leerzeichen.
- IDs und Template-Namen: `[A-Za-z][A-Za-z0-9_-]{0,63}`, also **1–64** Zeichen.
- X/Y: ganze Zahlen von **−10000 bis 10000**.
- Maximale Länge einer Ausgabelinie: **8192 Zeichen** (Grenzprüfung im Validator); `TEXT`-Inhalt maximal **4000 Zeichen**.
- Keine komplexen Datenstrukturen, Objektserialisierung oder Kommandos mit eingebetteten Zeilenumbrüchen.

| Befehl | Beispiel | Semantik im Browser |
|---|---|---|
| `CREATE id template` | `CREATE ball1 ball` | Erstes Wurzelelement aus `<template id="ball">` klonen, `id="ball1"` setzen und ins Spielfeld einfügen. Eine gleichnamige bisherige Instanz wird ersetzt. |
| `MOVE id x y` | `MOVE ball1 120 90` | Instanz über `transform: translate3d(120px, 90px, 0)` relativ zum Spielfeld positionieren. |
| `SHOW id` | `SHOW ball1` | `hidden = false`. |
| `HIDE id` | `HIDE ball1` | `hidden = true`, Element bleibt vorhanden. |
| `REMOVE id` | `REMOVE ball1` | DOM-Instanz entfernen; erneutes Erscheinen benötigt `CREATE`. |
| `TEXT id text...` | `TEXT score Punkte: 7` | `textContent` der vorhandenen ID setzen. Der gesamte Rest hinter `id` ist Text; HTML wird **nicht** interpretiert. |
| `SOUND id` | `SOUND ping` | Ein existierendes `<audio id="ping">` von Beginn an abspielen (Browser kann Autoplay bis zur Interaktion sperren). |

Ein minimales Java-Spiel sendet beispielsweise:

```java
System.out.println("CREATE ball1 ball");
System.out.println("MOVE ball1 120 90");
System.out.println("SHOW ball1");
System.out.flush();
```

Das Python-Pendant:

```python
print("CREATE ball1 ball", flush=True)
print("MOVE ball1 120 90", flush=True)
print("SHOW ball1", flush=True)
```

**Verbindliche Praxis:** `stdout` ist **ausschließlich** für Steuerbefehle reserviert. Diagnoseausgaben gehören nach `stderr` (`System.err.println(...)` bzw. `print(..., file=sys.stderr)`). Ungültige Zeilen werden nicht ausgeführt, sondern als Diagnose protokolliert. Bei unbekannten Vorlagen/Objekten kann ein gültiger Befehl wirkungslos bleiben; einige Fälle werden im Browser-Diagnosefenster angezeigt.

### Was das Protokoll bewusst nicht enthält

Keine Abfrage von Bildgrößen, keine Verwaltung von Java-Klassen, keine Kollisionsberechnung, keine allgemeine CSS-Manipulation, keine beliebigen HTML-Nachrichten, keine Canvas-Zeichenoperationen. Die Form liegt **in den Ressourcen**, der Spielzustand **im Spiel**. Ein `MOVE` setzt lediglich eine Position.

---

## 2. Server → Spielprozess: Eingabeereignisse

Der Server schreibt ebenfalls UTF-8-Zeilen auf **`stdin`** des Spielprozesses. Die Ereignisse können ohne zusätzliche Bibliothek mit `readLine()` eingelesen werden.

| Ereignis | Beispiel | Herkunft |
|---|---|---|
| `KEYDOWN code` | `KEYDOWN ArrowLeft` | Tastendruck im Browser; keine Wiederholung bei dauerhaft gedrückter Taste. |
| `KEYUP code` | `KEYUP ArrowLeft` | Loslassen einer Taste; auch beim Verlassen des Browserfensters werden gedrückte Tasten freigegeben. |
| `CLICK id x y` | `CLICK start 40 210` | Mausklick auf die nächste DOM-ID im Spielfeld; X/Y relativ zum Spielfeld. Bei keinem passenden Element `id = NONE`. |
| `TICK ms` | `TICK 33` | Serverinterner Timer, nur bei `tick_ms > 0` in der `game.ini`. |

`code` ist **`KeyboardEvent.code`**, also beispielsweise `ArrowLeft`, `Space`, `KeyA`, `Digit1` – **nicht** notwendigerweise das angezeigte Zeichen (`event.key`). IDs und Tasten-Codes unterliegen derselben Namensregel. Die Länge einer Browser-Eingabezeile ist auf **200 Zeichen** begrenzt.

Beispiel für ein sequenzielles Java-Spiel:

```java
try (var reader = new java.io.BufferedReader(
        new java.io.InputStreamReader(System.in, java.nio.charset.StandardCharsets.UTF_8))) {
    String line;
    while ((line = reader.readLine()) != null) {
        if (line.equals("KEYDOWN Space")) {
            System.out.println("SOUND ping");
        } else if (line.startsWith("TICK ")) {
            // Simulationsschritt; freiwillig
        }
    }
}
```

`readLine()` **darf blockieren**. Das Lesen ist die Ereignisschleife; sie braucht weder Busy-Wait noch einen selbst gestarteten Thread. Ein Tick ist ein **Arbeitsauftrag**, keine hochpräzise Uhr: bei Überlast oder voller Eingabewarteschlange können Ticks ausfallen. Der Wert in `TICK 33` ist der konfigurierte Nominalwert, keine Messung der tatsächlich vergangenen Zeit.

### Serverinternes Weiterleiten

Das Spielmodul nimmt HTTP-Eingaben validiert entgegen, legt sie in eine begrenzte Queue und schreibt sie über einen dedizierten Schreiberthread auf die `stdin`-Pipe des Kindes. Der Tick-Erzeuger schreibt in **dieselbe Queue**, wenn genügend Kapazität frei ist. Die Java-Implementierung verwendet für die Eingabequeue 1000 Einträge, für einen SSE-Client 2000 Nachrichten; das sind technische Kapazitätsgrenzen, keine Zusage unbegrenzter Pufferung.

---

## 3. Browsertransport: HTTP und SSE

Der Browser kommuniziert **nicht direkt** mit dem Spielprozess. Der Server bietet standardmäßig `http://127.0.0.1:8765` an. Ein anderer Port ist über `--port` möglich.

### 3.1 Laufzeit-HTTP-Endpunkte

| Methode | Pfad | Inhalt / Verhalten |
|---|---|---|
| `GET` | `/` | Spielseite, konfiguriert mit Titel, Breite, Höhe, Tick und optionalen Werkstattressourcen. Im reinen Editormodus Umleitung nach `/editor`. |
| `GET` | `/static/app.js`, `/static/app.css` | Darstellungs-JavaScript und CSS der Spieloberfläche. |
| `GET` | `/game/scene.html`, `/game/style.css` | Handgeschriebene Spielressourcen. |
| `GET` | `/game/assets/<name>` | Bild- und Audiodateien aus `assets/`. |
| `GET` | `/game/spielwerk/scene.html`, `/game/spielwerk/style.css`, `/game/spielwerk/layout.json` | Werkstatt-Export und Szenenlayout, **nur wenn vorhanden**. |
| `GET` | `/events` | Lang laufender SSE-Stream der Spielzustände und Befehle. |
| `GET` | `/health` | Einfache Erreichbarkeitsprüfung (`OK`). |
| `POST` | `/input` | Eine einzelne Textzeile `KEYDOWN`, `KEYUP` oder `CLICK` als Request-Body. |
| `POST` | `/restart` | Geplanter Spielneustart (kein Serverneustart); leere Body-Zeile/0 Byte zulässig. |
| `POST` | `/shutdown` | Kontrolliertes Beenden von Spielprozess und HTTP-Server; zusätzlicher Schutzheader. |

**Eingabebeispiel (HTTP, nicht das Spielprotokoll selbst):**

```http
POST /input HTTP/1.1
Content-Type: text/plain; charset=utf-8
Content-Length: 17

KEYDOWN ArrowLeft
```

Der Body enthält die **Textnachricht ohne zusätzliche JSON-Hülle**; der HTTP-Request transportiert sie lediglich. (Das Beispiel enthält 17 ASCII-Bytes.) HTTP-Eingaben werden vor dem Weiterreichen validiert.

### 3.2 SSE-Ereignisse

SSE verwendet den MIME-Typ `text/event-stream`. Der Stream enthält Ereignis-Typen, die **nicht** mit den Spielbefehlen verwechselt werden dürfen:

| SSE-Typ | Nutzdaten | Browserreaktion |
|---|---|---|
| `reset` | leer | Ursprüngliche HTML-Szene und vorhandene Werkstattressourcen erneut laden; bisherigen DOM-Zustand ersetzen. |
| `cmd` | **genau ein** validierter Spielbefehl (`CREATE ...`, `MOVE ...` usw.) | `applyCommand` in `web/app.js`. |
| `status` | `CODE<TAB>Beschreibung` | Statusanzeige aktualisieren, z. B. `RUNNING`, `STARTING`, `COMPILE_ERROR`, `STOPPED`, `EDITOR`. |
| `compile` | Diagnose-Text, ggf. mehrzeilig; leere Nachricht löscht die Anzeige | Compiler-/Startfehler anzeigen. |
| `log` | `stderr` oder Protokollwarnung | Diagnosefenster und Serverprotokoll. |

Beispiel:

```text
event: status
data: RUNNING\tSpiel läuft

event: cmd
data: MOVE ball1 120 90

: ping

```

Die Darstellung `\t` im Beispiel steht für ein tatsächliches **Tabulatorzeichen** zwischen Statuscode und Beschreibung. Die Zeile `: ping` ist ein SSE-Kommentar ohne Nutzdaten, um die Verbindung bei Ruhe offen zu halten; sie wird nach rund 12 Sekunden ohne Nachricht gesendet.

### 3.3 Zustand und Wiederverbinden

Der Server merkt sich einen **kompakten letzten Darstellungszustand**: erzeugte Instanzen, letzte Positionen, Texte, Sichtbarkeit und Entfernung. Beim neuen `/events`-Abonnement werden `reset`, aktueller Status, ggf. Compilerfehler und danach die gespeicherten Befehle gesendet. **`SOUND` wird nicht wiederholt**. So kann ein zweiter Browsertab den aktuellen Zustand übernehmen, ohne das Spiel neu zu starten.

Dies ist kein vollständiges Event-Sourcing und kein Spielstands-Speichersystem. Nicht jede historische Bewegung wird erneut abgespielt; der Server hält nur den aktuellen für die Darstellung relevanten Zustand.

### 3.4 Warum SSE und POST?

Beides ist ohne zusätzliche Laufzeitpakete mit Browsern sowie JDK- und Python-Standardbibliothek nutzbar. WebSockets wären möglich, sind aber für kurze lokale Lernspiele nicht erforderlich. **Der Browsertransport ist austauschbar, solange die Semantik des stdin/stdout-Vertrags erhalten bleibt.**

---

## 4. Figureneditor: HTTP-Schnittstelle

Die Browseroberfläche liegt unter **`/editor`**, ihre Ressourcen in `web/editor/`.

| Methode | Pfad | Bedeutung |
|---|---|---|
| `GET` | `/editor`, `/editor/` | Figureneditor-Seite. |
| `GET` | `/editor/editor.js`, `/editor/editor.css` | Oberflächenlogik und Stil. |
| `GET` | `/editor/codegen/<sprache>.js` | Statische JavaScript-Datei eines registrierten Sprachgenerators. |
| `GET` | `/editor/api/design` | Gespeichertes `design.json`; falls nicht vorhanden, `{"version":1,"templates":[]}`. |
| `GET` | `/editor/api/assets` | JSON-Array der vorhandenen unterstützten Bilddateien. |
| `POST` | `/editor/api/save` | Komplettes Längenbündel aus `design.json`, generiertem `scene.html` und `style.css`. |
| `POST` | `/editor/api/assets/<dateiname>` | Upload eines Bildes nach `assets/` (PNG/JPG/GIF/WebP, bis 2 MB). |

### 4.1 Speichern des Figurenentwurfs: das Längenbündel

Der Editor sendet an `/editor/api/save` **kein multipart/form-data und kein einzelnes JSON**. Der Body ist:

```text
<bytes-design>\n
<bytes-html>\n
<bytes-css>\n
<genau bytes-design UTF-8-Bytes>
<genau bytes-html UTF-8-Bytes>
<genau bytes-css UTF-8-Bytes>
```

Die ersten drei Zeilen sind **ASCII-Dezimalzahlen** und geben Byte-Längen an. Direkt danach folgen die drei Binärabschnitte **ohne Trenner**. Das ist notwendig, weil HTML und CSS selbst Zeilenumbrüche enthalten dürfen. Die Dateien werden als `spielwerk/design.json`, `spielwerk/scene.html` und `spielwerk/style.css` gespeichert. Das Gesamtpaket darf höchstens **900 000 Bytes**, jeder Abschnitt höchstens **250 000 Bytes** umfassen.

Der Server prüft Rahmen und Längen, aber **interpretiert das Figuren-JSON nicht als Spielbefehle**. Der Browsereditor ist für die Erstellung und die fachliche Validierung des Entwurfs zuständig. Beim Speichern werden zunächst temporäre Dateien geschrieben und dann ersetzt. **Die drei Ersetzungen bilden keine echte gemeinsame Transaktion:** Ein abruptes Ende zwischen Ersetzungen kann einen gemischten Zwischenstand hinterlassen.

### 4.2 Bild-Upload

Bilder liegen in `assets/`, nicht in `spielwerk/`. Zulässig sind sichere Dateinamen aus `[A-Za-z0-9_-]{1,64}` plus `.png`, `.jpg`, `.jpeg`, `.gif` oder `.webp`. Der Server prüft zusätzlich einen grundlegenden Format-Header. **Vorhandene SVG-Dateien** können als Assets ausgewählt werden; der Editor erlaubt aktuell **keinen SVG-Upload**. Dies ist ein bewusst kleiner Bildimport, keine vollständige Dateiformat- oder Sicherheitsprüfung für beliebige Webinhalte.

---

## 5. Figurenentwurf: `spielwerk/design.json`

Ein schematischer Entwurf (gekürzt):

```json
{
  "version": 1,
  "templates": [
    {
      "id": "sw-ball",
      "w": 40,
      "h": 40,
      "hit": { "x": 0, "y": 0, "w": 40, "h": 40 },
      "layers": [
        {
          "type": "ellipse", "x": 0, "y": 0, "w": 40, "h": 40,
          "color": "#39afd5", "color2": "#164e8d", "gradient": true,
          "border": 0, "borderColor": "#e8f7ff", "radius": 8,
          "shadow": 8, "opacity": 100, "rotation": 0,
          "flipX": false, "flipY": false, "fontSize": 14,
          "text": "", "image": "", "direction": "up",
          "arcStart": 35, "arcSweep": 270, "arcThickness": 8
        }
      ]
    }
  ]
}
```

Der Editor speichert auch Eigenschaften, die für einen bestimmten Ebenentyp gerade keine Wirkung haben. Die wichtigsten Entitätsregeln sind:

| Feld | Bedeutung / Regel |
|---|---|
| `version` | Formatversion, derzeit `1`. |
| `templates[]` | Liste benannter, wiederverwendbarer Figuren. |
| `id` | Figuren-Template-ID mit Präfix `sw-`, im Editor nach `sw-[A-Za-z][A-Za-z0-9_-]{0,40}` geprüft. |
| `w`, `h` | Gesamtabmessungen der Figur, derzeit jeweils 8 bis 640 px. |
| `hit` | Relative, bewusst festgelegte achsenparallele Kollisionsfläche. |
| `layers[]` | Geordnete Ebenen. Spätere Ebenen liegen visuell über früheren. |
| `type` | `rect`, `ellipse`, `triangle`, `arc`, `text` oder `image`. |
| `x`, `y`, `w`, `h` pro Ebene | Lokale Position und Größe innerhalb der Figur. |
| `color`, `color2`, `gradient`, `border`, `radius`, `shadow`, `opacity` | CSS-Gestaltung. |
| `rotation`, `flipX`, `flipY` | Rein visuelle Transformation der jeweiligen Ebene. |
| `direction` | Dreieck: `up`, `down`, `left`, `right`. |
| `arcStart`, `arcSweep`, `arcThickness` | Kreisbogen: Startwinkel, Winkelspanne, Dicke. |
| `text`, `fontSize`, `image` | Text-/Bild-Eigenschaften. Bilder referenzieren einen Dateinamen aus `assets/`. |

**Drei getrennte Repräsentationen:** `design.json` ist editierbar, `scene.html` beschreibt die Templates, `style.css` stellt deren visuelle Eigenschaften dar. Das generierte HTML enthält u. a. `data-hitbox="x y w h"` als Hinweis auf die Entwurfsgeometrie; die Spielruntime berechnet dadurch **noch keine** Kollisionen.

### Stile und Transformationen

- Ellipse: `border-radius: 50%`; Rechteck: gewöhnlicher `div` mit Rahmen und Rundung.
- Dreieck: `clip-path: polygon(...)`.
- Bogen: `conic-gradient(...)` und radiale Maske (`mask-image`, WebKit-Variante).
- Drehung/Spiegelung: `transform: rotate(...) scale(...)` auf der **inneren Ebene**. Die äußere Instanz wird unabhängig davon durch das Spiel mit `translate3d(...)` bewegt.

Damit sind **Gestaltungstransformation und Spielpositionierung** voneinander getrennt.

---

## 6. Szeneneditor: HTTP-API und `layout.json`

Die Browseroberfläche liegt unter **`/editor/scene`**. Ihre eigenen Skripte sind `scene.js`, `scene-model.js` und `scene.css`.

| Methode | Pfad | Bedeutung |
|---|---|---|
| `GET` | `/editor/scene`, `/editor/scene/` | Szeneneditor öffnen. |
| `GET` | `/editor/api/scene` | Gespeicherte Szene oder leere Standardszene mit den Abmessungen aus `game.ini`. |
| `POST` | `/editor/api/scene/save` | Validierte JSON-Szene als `spielwerk/layout.json` speichern. |
| `GET` | `/game/spielwerk/layout.json` | Gespeicherte Szene für die **Spielansicht**; ohne Datei `404` (anders als `/editor/api/scene`). |

Beispiel:

```json
{
  "version": 1,
  "width": 640,
  "height": 480,
  "background": "#12243b",
  "objects": [
    {"id": "baum1", "template": "sw-baum", "x": 70, "y": 95, "mode": "static"},
    {"id": "held", "template": "sw-roboter", "x": 260, "y": 175, "mode": "dynamic"}
  ]
}
```

| Feld | Regel |
|---|---|
| `version` | Aktuell `1`. |
| `width`, `height` | Ganze Zahlen, je **200–2048**. Die Spielansicht erhält ihre tatsächliche Größe weiterhin aus `game.ini`. |
| `background` | Farbe als `#RRGGBB`. |
| `objects` | Liste mit höchstens **200** Einträgen. |
| `id` | Eindeutige Instanz-ID; Namensregel wie im Spielprotokoll. |
| `template` | ID einer HTML-Vorlage; muss im geladenen HTML vorhanden sein. |
| `x`, `y` | Ganze Zahlen innerhalb −10000 bis 10000. |
| `mode` | `static` oder `dynamic`. |

**Keine Kopplung an den Code:** Ein `dynamic`-Objekt ist nur in der **Editorvorschau** sichtbar. In der Spielansicht erzeugt der Browser automatisch **nur `static`-Einträge**. Die dynamische Figur erscheint erst nach den Befehlen des Spielprogramms:

```text
CREATE held sw-roboter
MOVE held 260 175
SHOW held
```

`width`/`height` aus `layout.json` und `game.ini` sollten übereinstimmen. Der Szeneneditor zeigt die Maße aus `game.ini` an und ändert diese Datei **nicht**. Die Reihenfolge der Einträge im Array wirkt als Einfügereihenfolge, aber eine allgemeine Szenen-Ebenenverwaltung gibt es derzeit nicht.

Die Browser-Spielansicht liest die Szene selbst (`web/app.js`); sie fragt den Server **nicht**, welche Objekte statisch sind. Damit kennt das Spielmodul weder `layout.json` noch die Editorsemantik.

---

## 7. Sprachgeneratoren: eine eigene, lesende Schnittstelle

Die Generatoren liegen unter `web/editor/codegen/`. Die Registrierung geschieht im Browser:

```javascript
window.SpielwerkCodegen.register({
  id: 'meinesprache',
  label: 'Meine Sprache',
  generate({template}) {
    return `/* Figur ${template.id} */`;
  },
  generateScene({scene}) {
    return scene.objects
      .filter(o => o.mode === 'dynamic')
      .map(o => `CREATE ${o.id} ${o.template}`)
      .join('\n');
  }
});
```

`generate` für einen Figuren-Kopiervorschlag ist erforderlich, `generateScene` für dynamische Szenenobjekte optional. Registrierte Generatoren werden unter einer **Sprach-ID** ausgewählt. Die Editoroberfläche übergibt eine Kopie des aktuellen Entwurfs. Das Ergebnis ist **nur Text**, der als Vorschlag angezeigt und auf Wunsch in die Zwischenablage kopiert wird.

**Es existiert kein Schreibpfad vom Generator zu `.java`-/`.py`-Quelldateien.** Eine weitere Sprache als Generator ist unabhängig davon, ob der Laufzeitserver diese Sprache starten kann.

---

## 8. Sicherheitsgrenzen der lokalen HTTP-API

Spielwerk lauscht standardmäßig nur auf `127.0.0.1`. Für Werkstatt-Schreibanfragen erwartet der Server den Header `X-Spielwerk-Editor: save`, prüft einen lokalen Host/Origin sowie `Sec-Fetch-Site`, sofern vorhanden. Für `/shutdown` ist `X-Arcade-Action: shutdown` erforderlich. Dateinamen und Dateipfade werden eingeschränkt; Bildgrößen und Paketlängen sind begrenzt. Die Szenendaten werden zusätzlich strukturell geprüft, bevor sie geschrieben werden.

Das ist **Schutz gegen versehentliche oder einfache fremde Browseranfragen**, keine vollständige Authentifizierung oder sichere Isolation von untrusted code. HTML/CSS können Skripte, Bilder oder andere Ressourcen referenzieren, und der eigentliche Spielprozess wird mit lokalen Nutzerrechten ausgeführt. Spielwerk deshalb **nicht ohne zusätzliche Sicherheitsarchitektur** öffentlich ins Netzwerk hängen und keine unbekannten Projekte unkontrolliert starten.

---

## 9. Verträge, die bei Änderungen gemeinsam geprüft werden müssen

| Änderung | Gemeinsam zu prüfende Stellen |
|---|---|
| Neues Spielkommando | `server-java/GameModule.java` / `server.py` Validator + Zustandsabbildung, `web/app.js`, Tests, `docs/PROTOKOLL.md`. |
| Neuer Browser-Eingabetyp | `web/app.js`, `/input`-Validator und Eingabequeue beider Server, Beispielspiel, Tests. |
| Neuer SSE-Typ | Server-Publisher, `web/app.js`, SSE-Tests. |
| Neuer Figurentyp | `web/editor/editor.js` Vorschau/Export/Validierung, Design-Beispieldaten, Tests. Normalerweise **keine** Änderung am Spielprotokoll. |
| Geändertes `design.json` | Editor-Import/Export, Versionierung, Java-/Python-Schnipselgeneratoren, Werkstatt-API, Tests. |
| Geändertes `layout.json` | `scene-model.js`, `scene.js`, `SceneModule.java`, `scene_module.py`, `web/app.js`, Tests. |
| Neuer ausführbarer Spielsprachtyp | Java- und Python-Spielstarter, Watcher, Fehlermeldungen, Tests; **nicht** automatisch ein neuer Codegenerator. |
| Neue Editor-HTTP-Route | Java- und Python-Editormodule, Browser, Zugriffskontrolle, Endpoint-Tests. |

**Quellcode ist maßgeblich:** Der Text beschreibt den gegenwärtigen Stand und ist nicht als von der Implementierung unabhängige formale Norm gedacht. Bei einer Protokolländerung sollten zuerst eine Versionierungs- und Kompatibilitätsentscheidung und anschließend die Tests getroffen werden.
