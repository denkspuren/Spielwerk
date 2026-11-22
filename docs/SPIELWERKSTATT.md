# Spielwerkstatt – Grafiken für Spielwerk gestalten

Die **Spielwerkstatt** ist ein kleiner grafischer Editor, mit dem Sie Spielfiguren aus Formen, Texten und Bildern zusammensetzen können. Sie sehen sofort, wie eine Figur aussieht. Beim Speichern entstehen HTML-Templates und CSS-Dateien, die **Spielwerk** direkt im Browser verwendet.

Sie brauchen für den Einstieg keine HTML- oder CSS-Kenntnisse. Wer sich dafür interessiert, kann den erzeugten Quellcode im Editor ansehen und die Zusammenhänge kennenlernen.

## 1. In drei Minuten zur ersten Spielfigur

Starten Sie das vorbereitete Werkstatt-Beispiel im Hauptverzeichnis:

```bash
java server-java/ArcadeServer.java games/werkstatt_demo/SpielwerkDemo.java
```

Öffnen Sie <http://127.0.0.1:8765>. Sie sehen einen kleinen Roboter, den Sie mit den Pfeiltasten bewegen können. Wählen Sie **„Spielwerkstatt“** oben rechts oder öffnen Sie <http://127.0.0.1:8765/editor>.

Probieren Sie Folgendes aus:

1. Wählen Sie links die Ebene **„Rechteck“** des Roboters.
2. Ändern Sie rechts die Körperfarbe, den Schatten oder den Eckenradius.
3. Verschieben Sie ein Auge in der Vorschau mit der Maus.
4. Klicken Sie **„Speichern“**. Wechseln Sie anschließend zum Spiel und **laden Sie den Spiel-Tab neu**.
5. Der Roboter sieht anders aus und wird weiterhin von demselben Java-Programm bewegt.

Die Java-Datei wurde dabei nicht geändert. Sie haben ausschließlich die grafischen Ressourcen bearbeitet.

## 2. Figuren und Ebenen

**Figur:** Eine wiederverwendbare Vorlage, etwa `sw-roboter`, mit bekannter Breite und Höhe. Jede Figur besteht aus mehreren **Ebenen**. Mögliche Ebenentypen sind **Rechteck**, **Ellipse**, **Dreieck**, **Kreisbogen**, **Text** und **Bild**.

**Ebenen:** Jede Ebene besitzt eine Position X/Y relativ zur linken oberen Ecke der Figur. Bei Rechtecken und Ellipsen legen Sie Breite, Höhe, Farben, Rahmen, Schatten und gegebenenfalls Farbverläufe fest. Die Reihenfolge der Ebenen bestimmt, welche Form davor oder dahinter liegt.

**Bild:** Wählen Sie eine bereits im Spielordner unter `assets/` liegende PNG-, JPG-, GIF-, WebP- oder SVG-Datei. PNG, JPG, GIF und WebP können Sie über **„Bild hochladen“** einfügen. SVG-Dateien werden in dieser ersten Version über den Spielordner bereitgestellt; einen SVG-Zeicheneditor enthält die Spielwerkstatt noch nicht.

**Text:** Über die Textebene können Sie kurze Beschriftungen einfügen. Inhalte werden sicher als Text und nicht als HTML eingefügt.

In der Vorschau lassen sich Ebenen anklicken und verschieben. Mit dem Zoom sehen Sie kleine Details größer. Die Schaltfläche **„Bewegung testen“** zeigt eine einfache Vorschau-Bewegung; sie erzeugt **keine** Spielereignisse oder Animation im Java-Programm.

## 3. Breite, Höhe und die Kollisionsfläche

Spielwerk verwendet ganzzahlige Pixelkoordinaten. Der **Ursprung (0, 0)** liegt links oben im Spielfeld, die X-Achse wächst nach rechts und die Y-Achse nach unten.

Die Spielwerkstatt kennt drei verschiedene Rechtecke:

- Die **Figurgröße** ist die Breite und Höhe des äußersten HTML-Elements, beispielsweise 64 × 72 px.
- Jede **Ebene** liegt an einer Position relativ zur Figur. Sie kann kleiner sein und über den Figurenrand hinausragen.
- Die **Kollisionsfläche** ist ein unabhängig einstellbares Rechteck, das in der Vorschau gelb gestrichelt erscheint. Ihre Koordinaten sind relativ zur Figur.

Beispiel: Eine Figur ist 64 × 72 Pixel groß. Ihre Kollisionsfläche beginnt bei (5, 7) und misst 54 × 62 Pixel. Wenn die Java-Spiellogik die Figur bei (100, 150) positioniert, liegt die Kollisionsfläche absolut bei **(105, 157)** und reicht bis (159, 219).

Die Spielwerkstatt zeigt die passenden Java- oder Python-Konstanten zum Kopieren an, abhängig von der gewählten Sprache. Eine einfache Kollisionsprüfung zweier Rechtecke kann so aussehen:

```java
static boolean treffen(int ax, int ay, int aw, int ah,
                       int bx, int by, int bw, int bh) {
    return ax < bx + bw && ax + aw > bx &&
           ay < by + bh && ay + ah > by;
}
```

**Wichtig:** Spielwerk berechnet Kollisionen nicht automatisch. Die Spiellogik in Java verwendet die geometrischen Daten. Schlagschatten zählen standardmäßig **nicht** zur Kollisionsfläche. Rotation wird in der ersten Editorversion nicht angeboten; die Kollisionsfläche bleibt achsenparallel.

## 4. Eine gespeicherte Figur in Java verwenden

Jede Figur hat eine eindeutige **Template-ID**, beispielsweise `sw-roboter`. Die `sw-`-Vorsilbe kennzeichnet Editorfiguren und verhindert Kollisionen mit den von Hand angelegten Templates. Die ID darf Buchstaben, Ziffern, Bindestriche und Unterstriche enthalten und muss mit `sw-` beginnen.

In Ihrem Java-Spiel geben Sie aus:

```java
System.out.println("CREATE meinRoboter sw-roboter");
System.out.println("MOVE meinRoboter 100 150");
```

`CREATE` erzeugt aus der Vorlage `sw-roboter` ein konkretes Spielobjekt mit der **Instanz-ID** `meinRoboter`. `MOVE` positioniert dieses Objekt. Sie können mit derselben Vorlage beliebig viele Instanzen anlegen, sofern deren Instanz-IDs verschieden sind.

Das Spielprogramm liest Tastatur- und Timerereignisse weiterhin von `stdin`, wie im [Handbuch](HANDBUCH.md) und in der [Protokollreferenz](PROTOKOLL.md) beschrieben. An diesem Protokoll hat sich durch den Editor **nichts geändert**.

## 5. Wo werden die Ergebnisse gespeichert?

Beim Speichern legt die Spielwerkstatt **nur** die folgenden Dateien im aktiven Spielverzeichnis an:

```text
games/mein_spiel/
├── MeinSpiel.java          ← Java-Programm (unverändert)
├── game.ini               ← Spielfeldgröße, Ticks (unverändert)
├── scene.html             ← Ihre bestehenden Vorlagen (unverändert)
├── style.css              ← Ihr bestehendes CSS (unverändert)
├── assets/                ← hochgeladene Bilddateien
└── spielwerk/
    ├── design.json        ← editierbarer Entwurf
    ├── scene.html         ← automatisch erzeugte HTML-Templates
    └── style.css          ← automatisch erzeugte CSS-Regeln
```

Der Spiel-Browser lädt **beide** `scene.html`-Dateien und **beide** `style.css`-Dateien. Der Editor verwaltet ausschließlich Dateien in `spielwerk/` und Bildressourcen in `assets/`.

**Bitte die generierten HTML- und CSS-Dateien nicht von Hand verändern:** Beim nächsten Speichern werden sie neu erzeugt. Wenn Sie eigene HTML-/CSS-Elemente ergänzen möchten, verwenden Sie die **ursprünglichen** `scene.html` und `style.css` des Spiels. Das JSON in `spielwerk/design.json` ist **nur ein internes Speicherformat des Editors**; es ändert nichts am einfachen Textprotokoll zwischen Java und Spielwerk.

## 6. HTML und CSS verstehen

Die Figur `sw-roboter` wird grob in dieser Art gespeichert:

```html
<template id="sw-roboter">
  <div class="sw-sprite sw-root-sw-roboter">
    <div class="sw-layer-0"></div>
    <div class="sw-layer-1"></div>
  </div>
</template>
```

Ein `<template>` ist zunächst **unsichtbar**. Erst der Befehl `CREATE meinRoboter sw-roboter` klont daraus eine tatsächlich sichtbare Figur. CSS bestimmt das Aussehen der Bestandteile, beispielsweise:

```css
#field .sw-root-sw-roboter {
    width: 64px;
    height: 72px;
}
#field .sw-root-sw-roboter .sw-layer-0 {
    position: absolute;
    left: 3px;
    top: 4px;
    width: 58px;
    height: 64px;
    border-radius: 17px;
    background: linear-gradient(145deg, #53caec, #1576a4);
    box-shadow: 0 0 12px #53caec99;
}
```

Die `width`- und `height`-Eigenschaften setzen die Größe. `border-radius` rundet die Ecken ab. `linear-gradient` füllt eine Fläche mit einem Farbverlauf, `box-shadow` erzeugt einen Leuchteffekt. Für den Roboter benötigt man keine Bilddatei: Er besteht nur aus ein paar Formen!

## 7. Was die erste Version bewusst noch nicht kann

Die Spielwerkstatt ist **ein Figuren- und Ebeneneditor**, noch kein allgemeiner HTML/CSS-Editor und kein kompletter Szeneneditor. Man kann beispielsweise keine beliebigen handgeschriebenen CSS-Dateien importieren und vollständig grafisch zurückübersetzen. Funktionen wie Keyframe-Animationen, Vektorkurven, Gruppentransformationen, freies Drehen oder komplexe Szenenanordnung sind mögliche spätere Erweiterungen.

Sie können aber bereits eigene Bilder verwenden, Figuren aus Formen zusammensetzen und diese in **allen bisherigen Spielwerk-Spielen** mit den bekannten Befehlen steuern.

## 8. Drei Ideen zum Ausprobieren

1. **Ein anderes Gesicht:** Ändern Sie den Roboter: größere Augen, andere Mundform, Farbverlauf, Schatten. Der Java-Code soll unverändert weiterlaufen.
2. **Ein eigenes Fahrzeug:** Legen Sie `sw-auto` an. Bauen Sie Karosserie, Fenster und Räder aus Ebenen. Erstellen Sie in Java mit `CREATE auto sw-auto` ein neues Objekt und bewegen Sie es über das Spielfeld.
3. **Die Kollision verkleinern:** Erstellen Sie ein Objekt mit einem breiten Schatten. Definieren Sie eine kleinere Kollisionsfläche und zeigen Sie im Java-Code, warum sich die sichtbaren Grafiken berühren können, ohne dass die Rechtecke überlappen.

## 9. Dreiecke und Kreisbögen

Zusätzlich zu Rechtecken, Ellipsen, Text und Bilddateien enthält die Ebenenpalette jetzt **Dreieck** und **Kreisbogen**. Das Beispielprojekt `werkstatt_demo` enthält die zusätzliche Figur `sw-formen`: einen Ringbogen mit einem Dreieck. In der Figurenliste können Sie zwischen Roboter und Formenbeispiel wechseln.

**Dreieck:** Mit der Eigenschaft **Richtung** bestimmen Sie, ob die Spitze nach oben, unten, links oder rechts zeigt. Breite und Höhe geben weiterhin das umfassende Rechteck vor. Im Hintergrund entsteht CSS wie `clip-path: polygon(50% 0%, 100% 100%, 0% 100%)`. Ein Farbverlauf ist möglich. **Ein Rahmen entlang der Dreieckskanten wird derzeit nicht angeboten.**

**Kreisbogen:** Legen Sie **Startwinkel** (0–359°), **Bogenwinkel** (1–359°) und **Linienstärke** fest. Die Zählung beginnt oben bei 0° und nimmt im Uhrzeigersinn zu. Breite und Höhe definieren die umfassende Ellipse; bei gleicher Breite und Höhe entsteht ein Kreisbogen. Der Editor erzeugt dafür einen `conic-gradient` und eine ringförmige CSS-Maske (`mask-image`). Die Linienstärke kann höchstens die halbe kürzere Formabmessung betragen. Bei Kreisbögen gibt es derzeit nur eine einfarbige Linie; keine unterschiedlichen Farbverläufe entlang des Bogens.

**Kollisionen:** Der Kollisionsrahmen einer Figur ist weiterhin ein **achsenparalleles Rechteck**, unabhängig von der tatsächlichen Dreiecksfläche oder der gebogenen Linie. Wenn das Spiel besonders präzise Kollisionen benötigt, müssen Sie diese selbst im Spielprogramm berechnen. Im Einführungspraktikum sind rechteckige Annäherungen meist ausreichend.

## 10. Codevorlagen für Java und Python

In der rechten Seitenleiste können Sie jetzt zwischen **Java** und **Python** wählen. Für beide Sprachen gibt es ein Beispiel mit Template-ID, Abmessungen, Kollisionskoordinaten und den Befehlen `CREATE` und `MOVE`.

Diese Schnipsel sind **ausdrücklich nur Kopiervorlagen**. Die Sprachwahl beeinflusst weder die Figur noch den HTML-/CSS-Export. Die Werkstatt fügt **niemals** Code in eine Programmdatei ein und aktualisiert keine vorhandenen Konstanten automatisch.

Die Codeschnipsel stammen aus demselben sprachneutralen `spielwerk/design.json`. Beispielsweise wird die Kollisionsbreite `54` in Java zu `static final int ROBOTER_KOLLISION_BREITE = 54;` und in Python zu `ROBOTER_KOLLISION_BREITE = 54`.

Die **Spielausführung** unterstützt Java (`.java`: automatisch kompilieren und starten) und Python (`.py`: direkt mit Python 3 starten). Die Wahl der Programmiersprache ist **keine Einstellung in der Werkstatt**: Sie ergibt sich nur aus der übergebenen Hauptdatei. Das Textprotokoll `CREATE`, `MOVE`, `KEYDOWN` usw. ist für beide Sprachen identisch.

## 11. Eine zusätzliche Programmiersprache ergänzen

Die Sprachadapter liegen unter `web/editor/codegen/`. `registry.js` stellt die Registrierung bereit; `java.js` und `python.js` sind vollständige, getrennte Beispiele. Ein weiterer Generator kann in einer eigenen Datei registriert werden:

```js
window.SpielwerkCodegen.register({
  id: 'beispiel',
  label: 'Beispielsprache',
  generate({template, designVersion}) {
    const h = template.hit;
    return `// Figur: ${template.id}, Breite: ${template.w}, Kollision: ${h.w} x ${h.h}`;
  }
});
```

Die neue JavaScript-Datei unter `web/editor/codegen/` ablegen und **vor `editor.js`** als `<script defer src="/editor/codegen/beispiel.js"></script>` in `web/editor/index.html` einbinden. Beide lokalen Server liefern die einzelnen Codegeneratordateien über `/editor/codegen/` aus, ohne das Spielmodul zu berühren. Das Sprachmodul bekommt von der Registrierungsfunktion nur eine Kopie der gewählten Figur aus dem JSON-Modell. Die vorgesehenen Generatoren verwenden diese ausschließlich lesend und liefern Text zurück. **Hinweis für Erweiternde:** Wie andere Seitenskripte werden solche Generatoren im Browserkontext ausgeführt. Es dürfen daher nur vertrauenswürdige Skripte eingebunden werden; die Registrierung ist keine Sicherheits-Sandbox.

Die Kopiervorlagen sind Beispiele und keine vollständigen Spielprogramme. Die weitere Ereignisverarbeitung (blockierendes Lesen von `stdin`, Reaktion auf `KEYDOWN` und gegebenenfalls `TICK`) beschreiben das [Handbuch](HANDBUCH.md) und die [Protokollreferenz](PROTOKOLL.md).

## Drehen, Spiegeln und Positionieren

Wählen Sie eine Ebene aus. Unter **Drehung** können Sie Winkel in Grad eingeben,
mit **Horizontal spiegeln** und **Vertikal spiegeln** lässt sich die Ebene
umkehren. Drehung und Spiegelung ändern nicht das Koordinatensystem der Figur;
`MOVE` bewegt weiterhin deren linke obere Ecke. Die Kollisionsfläche bleibt
ein achsenparalleles Rechteck und muss gegebenenfalls manuell angepasst werden.

Zur genauen Platzierung dienen **Hilfslinien** (Mittelachsen), **Einrasten** in ein
Raster von 1, 5 oder 10 Pixeln, **Ebene zentrieren** und die Pfeiltasten:
Ein Pfeiltastendruck verschiebt die ausgewählte Ebene um ein Pixel; mit
Umschalttaste sind es zehn Pixel. Die Eingaben funktionieren, wenn gerade
kein Text- oder Zahlenfeld bearbeitet wird.

Die Werkstatt kann auch ganz ohne Spielprogramm gestartet werden: Geben Sie beim
Serverstart ein Verzeichnis statt einer `.java`- oder `.py`-Datei an. Wird der
Ordner neu angelegt, öffnet sich eine leere Werkstatt mit einer ersten Figur.
Beim späteren Start mit einer Quelldatei im selben Ordner bleiben die Entwürfe
erhalten. Es gibt keine zusätzliche Projektdatei für Startbefehle.
