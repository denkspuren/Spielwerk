# Spielwerkstatt: Szenen gestalten

Mit dem **Szeneneditor** können Sie die Figuren aus dem Figureneditor zu einem Spielfeld zusammensetzen. Die Spielwerkstatt gestaltet das Aussehen und die Ausgangsanordnung. Die **Spiellogik schreiben Sie weiterhin vollständig selbst** – beispielsweise in Java oder Python.

## 1. Start

Aus dem Projektverzeichnis mit dem Java-Server:

```sh
java server-java/ArcadeServer.java games/werkstatt_demo/SpielwerkDemo.java
```

Dann im Browser öffnen:

- Figureneditor: http://127.0.0.1:8765/editor
- **Szeneneditor:** http://127.0.0.1:8765/editor/scene
- Spielansicht: http://127.0.0.1:8765/

Der Python-Server wird alternativ mit `python3 server.py games/werkstatt_demo/SpielwerkDemo.java` gestartet. Beide Server bieten denselben Szeneneditor an. Die Werkstatt kann auch ohne Spielprogramm geöffnet werden: `java server-java/ArcadeServer.java mein-neues-spiel` legt bei Bedarf einen Projektordner an. Gestalten Sie zunächst Figuren, dann die Szene.

## 2. Figuren auswählen, positionieren und duplizieren

Im Figureneditor unter `/editor` erstellen Sie eine Figur mit einer eindeutigen Template-ID, z. B. `sw-roboter`. Speichern Sie diese. Öffnen Sie den Szeneneditor oder laden Sie ihn erneut.

1. Klicken Sie links auf die gewünschte Figur. Sie wird in die Mitte des Spielfelds eingefügt.
2. Ziehen Sie die Figur mit der Maus an eine andere Stelle. Raster und Zoom helfen beim Ausrichten.
3. Über die Eingabefelder rechts können Sie die Position exakt eingeben.
4. Mit den Pfeiltasten verschieben Sie das ausgewählte Objekt um 1 Pixel, mit **Umschalt + Pfeiltaste** um 10 Pixel.
5. Duplizieren Sie Objekte bei Bedarf. Jede Instanz bekommt eine **eigene Objekt-ID**.
6. Speichern Sie die Szene über „Szene speichern“ und laden Sie die Spielansicht neu.

Das **Raster** ist nur eine Zeichenhilfe und wird nicht im Spiel dargestellt. Die Ausgangsgröße des Spielfelds stammt aus `game.ini` (`width` und `height`). Ohne eine `game.ini` gilt 640 × 480 Pixel. Der Szeneneditor verändert diese Konfigurationsdatei nicht.

## 3. Der wichtigste Unterschied: statisch oder dynamisch

**Statisch:** Ein Hintergrundobjekt, ein Baum oder eine Wand erscheint automatisch, wenn die Spielansicht geladen wird. Im Java- oder Python-Programm ist dafür kein `CREATE` erforderlich.

**Dynamisch:** Eine Figur, die sich bewegen soll, wird zunächst **nur im Szeneneditor als Planung angezeigt**. In der laufenden Spielansicht erscheint sie erst, wenn Ihr Programm sie erzeugt. Für eine dynamische Figur `roboter` mit dem Template `sw-roboter`:

```java
System.out.println("CREATE roboter sw-roboter");
System.out.println("MOVE roboter 260 175");
System.out.println("SHOW roboter");
```

Oder in Python:

```python
print("CREATE roboter sw-roboter", flush=True)
print("MOVE roboter 260 175", flush=True)
print("SHOW roboter", flush=True)
```

Der Szeneneditor bietet einen **kopierbaren Codeschnipsel** an, in dem die dynamischen Objekte aufgeführt sind. Die Spielwerkstatt **fügt niemals automatisch Code in ein Spielprogramm ein**. Auch beim Speichern werden `.java`- und `.py`-Dateien nicht geändert.

## 4. Datenformat

Eine Szene liegt ausschließlich in `spielwerk/layout.json`:

```json
{
  "version": 1,
  "width": 600,
  "height": 380,
  "background": "#0b1730",
  "objects": [
    {"id":"baum1", "template":"sw-baum", "x":80, "y":100, "mode":"static"},
    {"id":"spieler", "template":"sw-roboter", "x":260, "y":175, "mode":"dynamic"}
  ]
}
```

Das Format ist **sprachunabhängig**. Die Template-ID verweist auf ein HTML-Template entweder aus der von Ihnen gestalteten `spielwerk/scene.html` oder aus einer handgeschriebenen `scene.html` im Spielverzeichnis. Beim Laden der Spielseite liest der Browser `layout.json` und erzeugt daraus nur die statischen Objekte. Für dynamische Objekte bleibt das vorhandene Zeilenprotokoll unverändert.

Dateien des Figureneditors (`design.json`, `scene.html`, `style.css`), Ihre handgeschriebenen Dateien (`scene.html`, `style.css`, `game.ini`) und sämtliche Programmdateien werden vom Szeneneditor **nicht überschrieben**.

## 5. Objektgröße und Kollision

Die Figurengröße wird durch das HTML-/CSS-Template festgelegt; eine auf dem Spielfeld platzierte Instanz übernimmt dieselbe Größe. Bei Figuren aus dem Figureneditor kennt der Szeneneditor Breite und Höhe aus `design.json` und zeigt auch die dort eingestellte Kollisionsfläche an.

Beispiel: Eine Figur besitzt 64 × 72 Pixel, liegt bei `(260,175)` und hat relativ zur Figur die Kollisionsfläche `(5,7,54,62)`. Das Kollisionsrechteck beginnt damit im Spiel bei **(265,182)** und ist 54 × 62 Pixel groß. Die Kollisionsprüfung findet im Spielprogramm statt.

Bei handgeschriebenen Templates kann der Szeneneditor die sichtbaren CSS-Maße messen. Eine gesonderte Kollisionsfläche muss Ihr Programm selbst festlegen. Drehung, Schatten oder transparente Teile führen **nicht automatisch** zu einer veränderten Kollision.

## 6. Gestaltung und Programmierung sind getrennt

```text
Figureneditor  -> spielwerk/design.json, scene.html, style.css
Szeneneditor   -> spielwerk/layout.json
Spielprogramm  -> stdin/stdout-Textprotokoll -> Browser
```

Der HTTP-Host leitet Dateioperationen an das Editormodul und Ereignisse an das Spielmodul. Der Szeneneditor besitzt keine Abhängigkeit vom Java- oder Python-Prozess. Java- und Python-Codeschnipsel werden durch austauschbare Generatoren im Ordner `web/editor/codegen/` erzeugt.

## 7. Ein kleines Experiment

Öffnen Sie die Demo und verschieben Sie das **statische** Objekt `formenLinks` von `(56,145)` auf `(100,130)`. Speichern und laden Sie die Spielansicht neu: Das Objekt steht jetzt an der neuen Position, obwohl die Java-Datei unverändert geblieben ist.

Verschieben Sie anschließend im Editor den **dynamischen** Roboter. Die neue Position erscheint zunächst nur im Codevorschlag und in der Editorvorschau. In der Spielansicht startet der Roboter weiterhin an der im Java-Programm festgelegten Position. Erst wenn Sie den Beispielcode bewusst übernehmen, beginnt er an der neuen Stelle. Genau diese Trennung ist beabsichtigt.

## 8. Grenzen der ersten Fassung

- Bis zu 200 Objekte mit eindeutigen IDs; Positionen und Instanzen, noch keine Gruppen oder Szenenanimationen.
- Die Reihenfolge der Objekte im JSON bestimmt die Einfügereihenfolge; eine eigene Ebenenverwaltung für komplette Szenen ist noch nicht enthalten.
- Figuren werden im Browser über HTML/CSS dargestellt. Der Szeneneditor verändert keine bestehende Grafikvorlage, sondern nur ihre Position in der Szene.
- Für das Anzeigen einer geänderten Szene ist momentan ein Neuladen der Spielansicht erforderlich.
- Die Spielfeldgröße in `layout.json` sollte zu `game.ini` passen. Bei abweichenden Werten muss die Konfiguration manuell angeglichen werden.
