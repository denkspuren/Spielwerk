# Das Spielprotokoll – Nachschlagewerk

**Version:** Mini-Protokoll v1. Das Protokoll besteht aus gewöhnlichem UTF-8-Text. Jede Nachricht nimmt **genau eine Zeile** ein und wird durch einen Zeilenumbruch abgeschlossen. Für die Steuerung sind **keine** JSON-Bibliothek, Netzwerkbibliothek oder Java-Grafikbibliothek erforderlich.

## 1. Java sendet Darstellungsbefehle (Standardausgabe)

| Befehl | Beispiel | Wirkung |
|---|---|---|
| `CREATE <id> <vorlage>` | `CREATE figur roboter` | Erzeugt ein DOM-Objekt durch Klonen des ersten Elements in `<template id="roboter">…</template>` aus `scene.html`. Die neue ID lautet `figur`. |
| `MOVE <id> <x> <y>` | `MOVE figur 128 240` | Setzt die Position der linken oberen Ecke auf x = 128, y = 240 Pixel, relativ zum Spielfeld (mittels CSS-`transform`). |
| `SHOW <id>` | `SHOW figur` | Macht das Objekt sichtbar. |
| `HIDE <id>` | `HIDE figur` | Blendet das Objekt aus; es bleibt vorhanden. |
| `REMOVE <id>` | `REMOVE figur` | Entfernt das Objekt aus dem DOM. Soll es wieder erscheinen, ist ein erneutes `CREATE` notwendig. |
| `TEXT <id> <text>` | `TEXT punkte Treffer: 12` | Setzt den **Textinhalt** eines bereits vorhandenen HTML-Elements (z. B. `<div id="punkte">`). Der gesamte Rest der Zeile nach `<id> ` ist der Text. Es wird **kein HTML** interpretiert. |
| `SOUND <id>` | `SOUND ping` | Spielt das `<audio id="ping" …>` aus `scene.html` ab. Eine erneute Ausgabe startet den Sound wieder von vorn. |

Die Vorlagen und die mit `TEXT` angesprochenen Felder müssen in der Szene vorhanden sein. `MOVE`, `SHOW`, `HIDE`, `REMOVE` funktionieren für ein erzeugtes Objekt; `TEXT` kann zusätzlich bestehende statische Elemente ändern. Ein unbekannter Objektname führt nicht zu einer automatisch erzeugten Figur.

**Ausgabe aus Java:**

```java
PrintWriter ausgabe = new PrintWriter(System.out, true);
ausgabe.println("CREATE figur roboter");
ausgabe.println("MOVE figur 128 240");
ausgabe.println("TEXT punkte Sterne: 1 / 3");
```

Der zweite Parameter von `PrintWriter` (`true`) schaltet das automatische Flushen nach `println()` ein. Falls Sie stattdessen `System.out.println()` verwenden, wird die Zeile bei der üblichen Java-Standardausgabe ebenfalls direkt ausgegeben. Für Fehlersuche und eigene Meldungen **`System.err.println(...)`** verwenden.

## 2. Java empfängt Ereignisse (Standardeingabe)

| Ereignis | Beispiel | Bedeutung |
|---|---|---|
| `KEYDOWN <code>` | `KEYDOWN ArrowLeft` | Eine Taste wurde gedrückt; automatische Browser-Tastenwiederholungen werden unterdrückt. |
| `KEYUP <code>` | `KEYUP ArrowLeft` | Die Taste wurde losgelassen; beim Verlassen des Browserfensters werden gehaltene Tasten ebenfalls freigegeben. |
| `CLICK <id> <x> <y>` | `CLICK neustart 540 367` | Klick auf das Element mit dieser ID; x/y sind die Position des Mauszeigers **relativ zum Spielfeld**, nicht relativ zum Element. |
| `TICK <ms>` | `TICK 33` | Ein periodischer Aufruf. Nur bei `tick_ms > 0` in `game.ini`. Die Zahl ist das konfigurierte Intervall, **keine garantierte gemessene Echtzeit**. |

Häufige Tastencodes: `ArrowLeft`, `ArrowRight`, `ArrowUp`, `ArrowDown`, `Space`, `Enter`, `Escape`, `KeyR`, `KeyA`, `KeyD`, `Digit1`. Es handelt sich um die Browser-Bezeichner `KeyboardEvent.code`, **nicht** um die mit der Tastatur erzeugten Zeichen. Die Buchstabentaste R heißt daher `KeyR`, nicht `R` oder `r`.

Klickt man auf eine Fläche ohne eigene Element-ID, wird `CLICK NONE x y` gesendet. Bei verschachteltem HTML wird die nächstgelegene ID des angeklickten Elements verwendet.

**Eingabe in Java:**

```java
BufferedReader eingabe = new BufferedReader(
        new InputStreamReader(System.in, StandardCharsets.UTF_8));
String zeile;
while ((zeile = eingabe.readLine()) != null) {
    if (zeile.equals("KEYDOWN ArrowLeft")) {
        // Auf einen Tastendruck reagieren.
    } else if (zeile.startsWith("TICK ")) {
        int ms = Integer.parseInt(zeile.substring(5));
        // Einen Simulationsschritt ausführen.
    }
}
```

`readLine()` **darf blockieren**. Die Spielschleife braucht keine selbst erzeugten Threads und kein `Thread.sleep()`; sie reagiert auf das jeweils nächste Ereignis. Ohne Ticks verbraucht das Warten praktisch keine CPU-Zeit.

## 3. Konfiguration

Ein Ordner enthält eine `game.ini`, etwa:

```ini
[game]
title = Mein Spiel
width = 640
height = 400
tick_ms = 0
```

- `width`, `height`: Maße des Spielfeldes in **CSS-Pixeln**. Zulässig: 200 bis 2048 Pixel.
- `tick_ms = 0`: keine regelmäßigen Ticks; nur Eingaben.
- `tick_ms = 33`: ungefähr 30 Simulationsschritte pro Sekunde, sofern der Prozess die Nachrichten zeitnah verarbeitet. Werte von 1 bis 14 sind nicht zulässig; positive Werte beginnen bei 15.
- `title`: Überschrift der Webseite.

Änderungen an `game.ini` wirken **erst nach einem Neustart des gesamten Servers**. Java-Quelldateien werden dagegen automatisch neu kompiliert, wenn sie gespeichert werden.

## 4. Technische Grenzen der Protokollversion 1

- IDs, Vorlagen und Tastencodes entsprechen `[A-Za-z][A-Za-z0-9_-]*` (1 bis 64 Zeichen). Beginnen Sie einen Namen mit einem Buchstaben und verwenden Sie danach nur Buchstaben, Zahlen, `_` und `-`.
- Zwischen Argumenten steht **genau ein normales Leerzeichen**. Befehlsnamen werden großgeschrieben. Zusätzliche Leerzeichen in `TEXT` gehören zum Text.
- X- und Y-Koordinaten sind **ganze Zahlen** von −10 000 bis +10 000. Für Zwischenwerte in Java `double` verwenden und beim Senden mit `Math.round()` in ganze Zahlen umwandeln.
- Maximale Länge einer Ausgabezeile: 8192 Zeichen; der Textteil von `TEXT` maximal 4000 Zeichen. Keine Zeilenumbrüche im Text.
- Es gibt in v1 **keinen** Befehl, um die Größe eines Objekts abzufragen oder festzulegen. Die Abmessungen werden in `style.css` definiert und als Konstanten in Java verwendet.
- Es gibt **keine** Kollisionserkennung im Browser. Die Spiellogik berechnet Treffer selbst.
- Ein `TICK 33` bedeutet **nicht**, dass seit dem letzten Tick garantiert exakt 33 ms vergangen sind. Bei Überlast können Ticks übersprungen werden. Für Spiele im ersten Semester ist eine einfache feste Zeitstufe meist ausreichend.
- Das Protokoll ist sprachunabhängig. Der mitgelieferte Server startet in dieser Version Java-Programme; andere Sprachen benötigen einen entsprechend angepassten Prozessstarter, nicht jedoch ein anderes Spielprotokoll.

## 5. Fehlersuche

| Symptom | Mögliche Ursache / Vorgehen |
|---|---|
| Kein Objekt sichtbar | `CREATE` vergessen, Vorlagenname falsch, CSS-Abmessungen fehlen oder Objekt außerhalb des Spielfelds. |
| Befehle erscheinen nicht | `System.err` statt `System.out` verwendet oder Ausgabe nicht geflusht. |
| „Ungültige stdout-Zeile“ im Diagnoseprotokoll | `System.out.println("Debug …")` oder ein falsch formatiertes Kommando. Debugtexte über `System.err` ausgeben. |
| Text wird nicht geändert | Statische oder erzeugte ID existiert nicht (Groß-/Kleinschreibung beachten). |
| Keine Reaktion auf Pfeiltasten | Spielfeld anklicken, `KEYDOWN ArrowLeft` statt nur `ArrowLeft` prüfen. |
| Kein Sound | Browser hat vor einer bewussten Interaktion noch keine Audiowiedergabe freigegeben; ID und `<audio>` prüfen. |
| Neue CSS-/HTML-Version erscheint nicht | Browserfenster neu laden. |
| Java kompiliert nicht | Compilerfehlerfeld über dem Spielfeld lesen, `.java` ändern und erneut speichern. |

Ausführlichere Erklärungen und die beiden Lernbeispiele stehen im [Handbuch](HANDBUCH.md).
