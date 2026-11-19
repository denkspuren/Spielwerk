# Spiele mit Java und einem Browser entwickeln

## Ein Handbuch für das erste Semester Informatik

Ein Spiel muss nicht mit einer großen Grafikbibliothek beginnen. Oft reicht schon eine Figur, die sich auf Tastendruck bewegt, ein Ziel, das erreicht werden soll, und eine sichtbare Rückmeldung. Mit **Java Browser Arcade** lässt sich diese Idee direkt umsetzen: **Java enthält die Spielregeln, der Browser zeichnet die Bilder.** Eine kleine, vorbereitete Infrastruktur verbindet beides.

Dieses Handbuch führt von der ersten Programmausführung bis zum eigenen Spiel. Es setzt lediglich grundlegende Kenntnisse von Java voraus. Sie müssen weder JavaScript noch HTML oder CSS programmieren können; die nötigen Teile werden an den Beispielen erklärt. Für eigene Spiele ist es allerdings sinnvoll, die Gestaltungsmöglichkeiten dieser Dateien nach und nach kennenzulernen.

Sie lernen anhand von zwei bewusst kleinen Projekten:

- **Sternenpfad:** Ein Roboter sammelt Sterne ein. Er bewegt sich nur, wenn Sie eine Taste drücken. Dieses Spiel ist **ereignisgesteuert**.
- **Balllabor:** Ein Ball bewegt sich kontinuierlich. Mit den Pfeiltasten wird ein Schläger gesteuert, der den Ball zurückwirft. Dieses Spiel ist **zeitgesteuert** und verarbeitet zusätzlich Tastaturereignisse.

Beide Projekte sind vollständig im Verzeichnis `games/` enthalten. Ihre Dateien können Sie jederzeit öffnen, verändern und als Ausgangspunkt für ein eigenes Spiel kopieren.

> **Lernziel:** Einfache Regeln, Zustände und Bewegungen in Java modellieren, die Darstellung über ein kleines Textprotokoll steuern und verstehen, wie grafische Objekte, Ereignisse und Kollisionen zusammenhängen.

---

## Inhalt

1. [In wenigen Minuten zum ersten Spiel](#1-in-wenigen-minuten-zum-ersten-spiel)
2. [Wie Java, Server und Browser zusammenarbeiten](#2-wie-java-server-und-browser-zusammenarbeiten)
3. [Welche Dateien zu einem Spiel gehören](#3-welche-dateien-zu-einem-spiel-gehören)
4. [Die Sprache zwischen Java und Browser](#4-die-sprache-zwischen-java-und-browser)
5. [Beispiel A: Sternenpfad – ein Spiel ohne Ticks](#5-beispiel-a-sternenpfad--ein-spiel-ohne-ticks)
6. [Wie aus HTML und CSS Grafiken entstehen](#6-wie-aus-html-und-css-grafiken-entstehen)
7. [Eigene Bilder, Kacheln und Sounds verwenden](#7-eigene-bilder-kacheln-und-sounds-verwenden)
8. [Koordinaten, Größen und Kollisionen](#8-koordinaten-größen-und-kollisionen)
9. [Beispiel B: Balllabor – Animation mit Ticks](#9-beispiel-b-balllabor--animation-mit-ticks)
10. [Ereignisgesteuert oder zeitgesteuert?](#10-ereignisgesteuert-oder-zeitgesteuert)
11. [Fehler suchen, Dateien ändern und neu starten](#11-fehler-suchen-dateien-ändern-und-neu-starten)
12. [Ein eigenes Spiel planen](#12-ein-eigenes-spiel-planen)
13. [Häufige Fragen und wichtige Begriffe](#13-häufige-fragen-und-wichtige-begriffe)

Ein kompakter Überblick über sämtliche Nachrichten steht zusätzlich im [Protokoll-Nachschlagewerk](PROTOKOLL.md). Weiterführende Ideen enthält die [Aufgabensammlung](AUFGABEN.md).

---

## 1. In wenigen Minuten zum ersten Spiel

### Was Sie benötigen

- Ein **Java Development Kit (JDK) ab Version 17**. Eine Java-Laufzeitumgebung allein genügt nicht, weil der Server `javac` zum Kompilieren benötigt.
- Einen Texteditor oder eine Entwicklungsumgebung, beispielsweise VS Code, IntelliJ IDEA oder einen anderen Java-fähigen Editor.
- Einen aktuellen Browser, zum Beispiel Firefox, Chrome oder Edge.
- Das entpackte Projekt **Java Browser Arcade**.

Öffnen Sie ein Terminal und prüfen Sie Ihre Installation:

```bash
java -version
javac -version
```

Bei beiden Befehlen sollte eine Versionsnummer erscheinen. Andernfalls muss das JDK installiert oder der Suchpfad (`PATH`) angepasst werden.

### Beispiel A starten

Öffnen Sie das **Hauptverzeichnis des Projekts** im Terminal. In diesem Verzeichnis befinden sich unter anderem `server-java/`, `games/` und `web/`.

```bash
java server-java/ArcadeServer.java games/sternenpfad/Sternenpfad.java
```

Öffnen Sie anschließend im Browser:

**http://127.0.0.1:8765/**

Nun sollte das Spielfeld **Sternenpfad** erscheinen. Bewegen Sie den Roboter mit den **Pfeiltasten** zu den drei Sternen. Ein eingesammelter Stern verschwindet, und die Punktanzeige verändert sich. Mit **R** oder dem Button **Neu beginnen** starten Sie das Spiel erneut. Alternativ lässt sich das Beispiel mit dem beigefügten Skript `start-sternenpfad-java.sh` (Linux/macOS) beziehungsweise `start-sternenpfad-java.bat` (Windows) starten.

### Die erste eigene Änderung

Öffnen Sie `games/sternenpfad/Sternenpfad.java` und suchen Sie:

```java
private static final int SCHRITT = 48;
```

Ändern Sie testweise den Wert auf `24`, speichern Sie die Datei und drücken Sie eine Pfeiltaste. Der Server bemerkt die geänderte Java-Datei, kompiliert sie neu und startet das Spiel. Der Roboter bewegt sich nun in kleineren Schritten. **Die Sterne liegen aber weiterhin auf dem ursprünglichen 48-Pixel-Raster.** Dadurch entsteht eine interessante Frage: Wie müssen Schrittweite und Zielkoordinaten zusammenpassen, damit ein Spiel korrekt funktioniert?

Setzen Sie `SCHRITT` anschließend wieder auf `48`. Weitere Aufgaben finden Sie in [AUFGABEN.md](AUFGABEN.md).

### Beispiel B starten

Beenden Sie zuerst den Server über **Server beenden** im Browser (oder mit `Strg+C` im Terminal). Starten Sie dann:

```bash
java server-java/ArcadeServer.java games/balllabor/Balllabor.java
```

Laden Sie die Browserseite neu. Der Ball bewegt sich von allein. Mit **←** und **→** verschieben Sie den Schläger; mit der **Leertaste** pausieren Sie. **R** oder der Button **Neu** setzt das Spiel zurück.

**Alternative:** Wenn Sie den Python-Server verwenden möchten, lautet der erste Startbefehl `python3 server.py games/sternenpfad/Sternenpfad.java`; die zweite Variante funktioniert entsprechend. Die Spielprogramme selbst ändern sich dadurch nicht.

---

## 2. Wie Java, Server und Browser zusammenarbeiten

Die Architektur besteht aus drei getrennten Teilen:

```text
      Browser
      zeigt HTML/CSS-Grafiken an
      erfasst Tastatur und Maus
          ↑            ↓
    Darstellungs-   Eingabeereignisse
      befehle
          │            │
          └── Server ──┘
              ↑    ↓
            stdout stdin
              ↑    ↓
          Java-Spiel
          speichert alle Positionen,
          Spielregeln und Punkte
```

**Java** kennt beispielsweise die Position des Roboters `x = 88`, `y = 272`. Wenn eine Taste gedrückt wird, berechnet Java eine neue Position und sendet den Befehl:

```text
MOVE spieler 136 272
```

**Der Server** liest diese Zeile aus der **Standardausgabe** (`stdout`) des Java-Prozesses und reicht sie an den Browser weiter. In die Gegenrichtung schreibt er Nachrichten wie `KEYDOWN ArrowRight` auf die **Standardeingabe** (`stdin`) des Prozesses. Der Server kümmert sich außerdem um die Kompilierung und den Start des Programms.

**Der Browser** führt bereits vorbereitetes JavaScript aus. Dieses sucht das HTML-Element mit der ID `spieler` und setzt dessen CSS-Position. Er berechnet keine Spielregeln und entscheidet nicht selbst, ob ein Stern eingesammelt wurde.

Die Verbindung vom Server zum Browser verwendet **Server-Sent Events (SSE)**, die Eingaben werden als **HTTP-POST** gesendet. Diese technischen Details müssen Sie für die Java-Programmierung nicht behandeln. Wichtig ist die klare Grenze: **Java schreibt Befehlszeilen und liest Ereigniszeilen.**

### Warum ist das Protokoll sprachunabhängig?

Eine Zeile wie `MOVE spieler 136 272` kann jede Programmiersprache erzeugen. Sie könnte also genauso gut aus Python, C oder einer anderen Sprache stammen. Der mitgelieferte Server ist in dieser Version darauf spezialisiert, **Java-Dateien** zu kompilieren und **Java-Prozesse** zu starten. Das Textprotokoll selbst ist jedoch nicht an Java gebunden.

---

## 3. Welche Dateien zu einem Spiel gehören

Das erste Beispiel hat diesen Aufbau:

```text
games/
  sternenpfad/
    Sternenpfad.java        Programm und Spiellogik
    game.ini               Grundeinstellungen
    scene.html             Texte, Vorlagen und Audioelemente
    style.css              Aussehen und Abmessungen
    assets/
      stern.svg             Vektorgrafik eines Sterns
      pling.wav             kurzer Klang beim Einsammeln
```

Zum Vergleich liegt das zweite Beispiel in `games/balllabor/`. Auch dort finden Sie eine Java-Datei, die drei Konfigurations- und Darstellungsdateien sowie eine Audiodatei.

### `game.ini`: Größe und Zeitsteuerung

```ini
[game]
title = Sternenpfad – mein erstes Spiel
width = 640
height = 400
tick_ms = 0
```

Das Spielfeld ist **640 Pixel breit** und **400 Pixel hoch**. Das sind feste CSS-Pixelgrößen. Auf kleinen Bildschirmen kann die Webseite horizontal scrollen; das Koordinatensystem wird dadurch nicht verändert.

Die Zeile `tick_ms = 0` bedeutet: **Keine automatischen Zeitereignisse.** Das Java-Programm erhält lediglich Nachrichten über Benutzereingaben. Für das zweite Beispiel steht dort `tick_ms = 33`: Der Server versucht dann, ungefähr alle 33 Millisekunden ein `TICK 33` zu liefern.

> **Wichtig:** Nach einer Änderung der `game.ini` muss der **gesamte Server** neu gestartet werden. Das automatische Neukompilieren beobachtet dagegen die Java-Dateien.

### `scene.html`: Was grundsätzlich auf dem Spielfeld existiert

Beispielsweise:

```html
<div id="punkte">Sterne: 0 / 3</div>
<template id="stern">
  <div class="stern"></div>
</template>
```

Das `<div id="punkte">` existiert bereits beim Laden der Seite. Java kann seinen Text mit `TEXT punkte ...` verändern.

Das `<template>` ist eine **Vorlage**. Ihr Inhalt wird zunächst nicht sichtbar angezeigt. Erst der Befehl `CREATE gold_0 stern` macht aus der Vorlage ein neues Objekt mit der ID `gold_0`.

### `style.css`: Wie etwas aussehen soll

Die CSS-Regeln legen Farben, Abmessungen, Verläufe, Abstände und Schatten fest. `style.css` enthält beispielsweise die Größe `40px × 40px` eines Sterns. Die Java-Logik verwendet die gleichen Maße, wenn sie Kollisionen berechnet.

### `assets/`: Eigene Dateien

Hier liegen optionale Bilddateien (`.svg`, `.png`, `.webp` usw.) und Audiodateien (`.wav`, `.mp3` usw.). Sie werden vom Server unter dem Pfad `/game/assets/…` angeboten.

### Der Dateiname der Java-Klasse

Wenn Ihre Hauptklasse `MeinSpiel` heißt, verwenden Sie eine Datei `MeinSpiel.java` mit:

```java
public class MeinSpiel {
    public static void main(String[] args) throws Exception {
        // Hier beginnt das Programm.
    }
}
```

Der Server kompiliert automatisch alle `.java`-Dateien, die **direkt im selben Spielordner** liegen. Gestartet wird die Klasse der im Startbefehl genannten Hauptdatei. **Java-Packages** werden in dieser ersten Projektversion nicht unterstützt.

---

## 4. Die Sprache zwischen Java und Browser

Die Nachrichten sind absichtlich unkompliziert. Es gibt keine geschachtelten Datenstrukturen und keine JSON-Syntax. Jede Nachricht besteht aus einem Befehlswort und wenigen Argumenten, getrennt durch **genau ein Leerzeichen**.

### Befehle, die Java ausgeben kann

| Nachricht | Zweck |
|---|---|
| `CREATE figur roboter` | Eine Figur mit der ID `figur` aus der Vorlage `roboter` erzeugen |
| `MOVE figur 100 120` | Die linke obere Ecke der Figur auf (100, 120) setzen |
| `SHOW figur` | Figur sichtbar machen |
| `HIDE figur` | Figur verbergen, aber behalten |
| `REMOVE figur` | Figur vollständig entfernen |
| `TEXT punkte Sterne: 2 / 3` | Den Text des HTML-Elements `punkte` verändern |
| `SOUND pling` | Eine vorbereitete Audiodatei abspielen |

**Drei Begriffe auseinanderhalten:** Die *Vorlage* `roboter` beschreibt den grafischen Typ. Die *Objekt-ID* `figur` identifiziert eine konkrete Figur. Die *Java-Variable* `x` speichert ihre Position für die Spielregeln. Diese drei Dinge erfüllen unterschiedliche Aufgaben.

Ein kleiner Java-Helfer kann das Senden vereinfachen:

```java
private final PrintWriter ausgabe = new PrintWriter(System.out, true);

private void senden(String befehl) {
    ausgabe.println(befehl);
}
```

Danach genügt:

```java
senden("CREATE figur roboter");
senden("MOVE figur " + x + " " + y);
senden("TEXT punkte Sterne: " + punkte + " / 3");
```

Das `true` beim `PrintWriter` bewirkt, dass nach jedem `println()` die Nachricht sofort aus dem Java-Ausgabepuffer weitergereicht wird.

### Ereignisse, die Java einliest

| Nachricht | Bedeutung |
|---|---|
| `KEYDOWN ArrowUp` | Pfeiltaste nach oben wurde gedrückt |
| `KEYUP ArrowUp` | Pfeiltaste nach oben wurde losgelassen |
| `KEYDOWN Space` | Leertaste wurde gedrückt |
| `KEYDOWN KeyR` | Die Taste R wurde gedrückt |
| `CLICK neu 540 365` | Auf das Element `neu` wurde geklickt; Mausposition im Spielfeld |
| `TICK 33` | Der Server fordert einen weiteren Simulationsschritt an |

Beachten Sie die Schreibweise der Tasten: `KeyR` bezeichnet die physische Buchstabentaste R, `Space` die Leertaste. **`KEYDOWN` wird beim erstmaligen Herunterdrücken gesendet, `KEYUP` beim Loslassen.** Das automatische Wiederholen einer gehaltenen Taste wird im Browser unterdrückt.

Eine blockierende Leseschleife genügt:

```java
BufferedReader eingabe = new BufferedReader(
        new InputStreamReader(System.in, StandardCharsets.UTF_8));
String zeile;
while ((zeile = eingabe.readLine()) != null) {
    if (zeile.equals("KEYDOWN ArrowRight")) {
        x += 48;
        senden("MOVE figur " + x + " " + y);
    }
}
```

**Was bedeutet „blockierend“?** Solange kein Ereignis vorliegt, wartet `readLine()` einfach. Das Programm verbraucht dabei praktisch keine Rechenleistung. Der Browser bleibt dennoch vollständig bedienbar, denn er läuft unabhängig vom Java-Prozess. Bei Zeitsteuerung trifft regelmäßig ein `TICK` ein; ohne Zeitsteuerung läuft das Programm erst beim nächsten Tastendruck weiter. Ein eigener Thread oder eine Endlosschleife mit `Thread.sleep()` ist nicht nötig.

Eine vollständige Referenz mit Grenzwerten und Hinweisen zu zulässigen IDs steht in [PROTOKOLL.md](PROTOKOLL.md).

---

## 5. Beispiel A: Sternenpfad – ein Spiel ohne Ticks

Öffnen Sie parallel die Dateien `games/sternenpfad/Sternenpfad.java` und `games/sternenpfad/scene.html`. Der Sternenpfad ist absichtlich ein überschaubares Spiel: **drei Sterne einsammeln, ohne automatische Bewegung**.

### Schritt 1: Den Zustand speichern

Am Anfang der Java-Klasse stehen die wichtigen Werte:

```java
private static final int SCHRITT = 48;
private static final int[] STERN_X = {184, 328, 472};
private static final int[] STERN_Y = {176, 224, 128};

private int x, y, punkte;
private final boolean[] eingesammelt = new boolean[STERN_X.length];
```

`x` und `y` sind die aktuellen Koordinaten des Roboters, `punkte` ist die Anzahl gefundener Sterne. Die beiden Arrays enthalten die Koordinaten aller Sterne. Das `boolean`-Array merkt sich, welche Sterne bereits gefunden wurden.

**Der Zustand liegt in Java, nicht in der Grafik.** Der Browser zeigt lediglich das an, was Java mit seinen Befehlen vorgibt.

### Schritt 2: Die Szene zu Spielbeginn aufbauen

Die Methode `neu()` legt zunächst Werte fest:

```java
x = 88;
y = 272;
punkte = 0;
```

Dann erzeugt sie die drei Sterne. Der entsprechende Teil der Methode lautet:

```java
for (int i = 0; i < STERN_X.length; i++) {
    eingesammelt[i] = false;
    senden("CREATE gold_" + i + " stern");
    senden("MOVE gold_" + i + " " + STERN_X[i] + " " + STERN_Y[i]);
    senden("SHOW gold_" + i);
}
```

Der Browser erhält etwa:

```text
CREATE gold_0 stern
MOVE gold_0 184 176
SHOW gold_0
```

Hier sehen Sie, warum zwischen **Vorlage** und **ID** unterschieden wird: Drei Sterne verwenden dasselbe grafische Template `stern`, haben aber unterschiedliche IDs (`gold_0`, `gold_1`, `gold_2`).

Danach entsteht der Roboter:

```java
senden("CREATE spieler roboter");
senden("MOVE spieler " + x + " " + y);
```

### Schritt 3: Auf Tastaturereignisse reagieren

Das Programm wartet in der Methode `laufen()` auf Nachrichten. Beginnt eine Zeile mit `KEYDOWN `, ruft es `taste(...)` auf:

```java
if (zeile.startsWith("KEYDOWN ")) {
    taste(zeile.substring(8));
}
```

`substring(8)` entfernt die ersten acht Zeichen – also `KEYDOWN ` – und übergibt nur `ArrowLeft`, `ArrowRight` usw. Eine JSON-Bibliothek oder ein eigener Parser wird nicht benötigt.

In `taste` wird die Position verändert:

```java
switch (code) {
    case "ArrowLeft"  -> x = Math.max(LINKS, x - SCHRITT);
    case "ArrowRight" -> x = Math.min(RECHTS, x + SCHRITT);
    case "ArrowUp"    -> y = Math.max(OBEN, y - SCHRITT);
    case "ArrowDown"  -> y = Math.min(UNTEN, y + SCHRITT);
    case "KeyR"      -> { neu(); return; }
    default          -> { return; }
}
zeichnen();
```

`Math.max` und `Math.min` verhindern, dass der Roboter das vorgesehene Spielfeld verlässt. Die Methode `zeichnen()` sendet nur die neue Position. **Für jede Pfeiltastenaktion wird genau ein Schritt berechnet.** Damit bewegt sich der Roboter nicht von allein.

### Schritt 4: Die Kollision mit einem Stern prüfen

Da Roboter und Sterne **auf demselben Raster** liegen, genügt hier ein einfacher Koordinatenvergleich:

```java
if (!eingesammelt[i] && x == STERN_X[i] && y == STERN_Y[i]) {
    eingesammelt[i] = true;
    punkte++;
    senden("HIDE gold_" + i);
    senden("SOUND pling");
    senden("TEXT punkte Sterne: " + punkte + " / " + STERN_X.length);
}
```

Das Spiel prüft zuerst, ob der Stern noch vorhanden ist, und vergleicht anschließend die Rasterpositionen. Wenn sie übereinstimmen, verschwindet der Stern, ein Ton erklingt und der Punktestand verändert sich.

Diese einfache Kollision funktioniert, **weil** beide Objekte die gleichen Rasterkoordinaten verwenden. Für frei bewegliche Figuren benötigt man eine andere Methode – dazu später mehr.

### Schritt 5: Einen Button anklicken

In der HTML-Szene gibt es:

```html
<button id="neu" type="button">Neu beginnen</button>
```

Die tatsächliche Datei enthält zusätzlich die CSS-Klasse für die Gestaltung. Ein Klick auf den Button führt beispielsweise zu `CLICK neu 540 365`. Das Java-Programm prüft:

```java
else if (zeile.startsWith("CLICK neu ")) {
    neu();
}
```

Hier sind die genauen Klickkoordinaten nicht wichtig. Sie könnten jedoch für ein anderes Spiel ausgewertet werden, etwa um die angeklickte Rasterzelle zu bestimmen.

### Was Sie bereits gelernt haben

Ohne selbst eine grafische Bibliothek einzusetzen, haben Sie ein Programm mit **Attributen, Methoden, Arrays, Bedingungen, einer Schleife, Tastensteuerung, Kollisionen und Sound** vor sich. Es ist ein gewöhnliches Java-Programm, das Nachrichten schreibt und liest.

**Versuch:** Verändern Sie die Position des ersten Sterns von `(184, 176)` auf `(232, 176)` und speichern Sie. Finden Sie den Stern noch? Wie hängen Schrittweite und Positionen zusammen?

---

## 6. Wie aus HTML und CSS Grafiken entstehen

Der Roboter besteht nicht aus einer Bilddatei. Seine gesamte Darstellung wird durch **HTML-Elemente und CSS-Regeln** erzeugt. Das ist besonders nützlich für einfache Spiele, weil man Formen und Farben schnell verändern kann.

### HTML: die Struktur

In `scene.html` steht sinngemäß:

```html
<template id="roboter">
  <div class="roboter">
    <span class="roboter-auge auge-links"></span>
    <span class="roboter-auge auge-rechts"></span>
    <span class="roboter-mund"></span>
  </div>
</template>
```

Das äußere `<div>` wird zum Körper. Die beiden `<span>`-Elemente werden Augen, das dritte Element wird ein Mund. Ohne CSS wären das zunächst kaum erkennbare Elemente.

### CSS: Formen, Farben und Lichteffekte

Die wesentlichen Bestandteile des Roboterkörpers sind:

```css
#field .roboter {
    width: 40px;
    height: 40px;
    border: 3px solid #b1e8ff;
    border-radius: 13px;
    background: linear-gradient(145deg, #85dcf6, #26a5d4 68%, #14719e);
    box-shadow: inset 2px 3px #ffffff77, 0 0 18px #31c6f68c;
}
```

Diese wenigen Zeilen bewirken sehr viel:

| CSS-Eigenschaft | Was Sie sehen |
|---|---|
| `width` und `height` | Die **40 × 40 Pixel** große Grundfläche der Figur |
| `border` | Einen hellen Rand um den Körper |
| `border-radius` | Abgerundete Ecken statt eines kantigen Quadrats |
| `linear-gradient(...)` | Einen sanften Farbverlauf, der dem Körper Tiefe gibt |
| `box-shadow: inset …` | Einen Lichtreflex **im Inneren** der Figur |
| `box-shadow: 0 0 18px …` | Ein weiches Leuchten **außerhalb** des Körpers |

Die Augen werden als kleine, dunkle, abgerundete Rechtecke erzeugt. Der Mund entsteht durch eine gekrümmte untere Rahmenlinie. Sie müssen also für einen einfachen Spielcharakter **keine Grafik zeichnen oder herunterladen**.

Es gibt weitere besonders nützliche CSS-Werkzeuge:

- **`radial-gradient(...)`** erzeugt kreisförmige Verläufe, beispielsweise eine glänzende Kugel.
- **`border-radius: 50%`** macht aus einem quadratischen Element einen Kreis.
- **`filter: drop-shadow(...)`** legt einen Schatten um den sichtbaren Inhalt, beispielsweise einen SVG-Stern.
- **`background-size: 48px 48px`** kann ein Hintergrundmuster aus regelmäßig wiederholten Kacheln erzeugen.
- **`opacity`** steuert die Deckkraft; **`z-index`** die Reihenfolge übereinanderliegender Objekte.

### Wie entsteht das Raster, obwohl kein Kachelbild existiert?

In `style.css` finden Sie:

```css
background-image:
    linear-gradient(#69b6cc19 1px, transparent 1px),
    linear-gradient(90deg, #69b6cc19 1px, transparent 1px);
background-size: 48px 48px;
```

Der erste Verlauf erzeugt eine **waagerechte Linie von einem Pixel Höhe**, der zweite eine **senkrechte Linie von einem Pixel Breite**. Der Browser wiederholt beide Muster alle 48 Pixel. So entsteht ein Raster, ohne dass dafür eine Bilddatei benötigt wird. Es ist ein reiner **Hintergrundeffekt**: Java muss keine 60 Rasterlinien zeichnen.

### Wie bewegt Java ein HTML-Element?

Wenn Java `CREATE spieler roboter` ausgibt, erstellt das vorbereitete Browser-JavaScript eine Kopie der Vorlage. Sie erhält die CSS-Klasse `game-object`, die im zentralen Stylesheet ungefähr so definiert ist:

```css
#field { position: relative; }
#field .game-object {
    position: absolute;
    top: 0;
    left: 0;
}
```

Der Befehl `MOVE spieler 136 272` bewirkt vereinfacht:

```javascript
spieler.style.transform = "translate3d(136px, 272px, 0)";
```

Sie müssen diesen JavaScript-Code **nicht selbst schreiben**. Wichtig ist nur die Bedeutung: Der Browser verschiebt das vorhandene Element relativ zur linken oberen Ecke des Spielfelds. Das Element muss nicht bei jedem Schritt neu erzeugt werden. Die Bewegung ist deshalb einfach und in diesem Umfang sehr flüssig.

**Achtung bei eigenem CSS:** Für dynamische Spielobjekte sollten Sie nicht zusätzlich eine feste `left`- oder `top`-Position setzen. Das würde zu der `MOVE`-Verschiebung hinzukommen. Vermeiden Sie auch äußere `margin`-Abstände an bewegten Elementen; diese machen die Kollisionskoordinaten unnötig kompliziert.

### Ein einfaches Experiment

Öffnen Sie `games/sternenpfad/style.css` und ersetzen Sie beim Roboter `border-radius: 13px;` durch `border-radius: 50%;`. Laden Sie **die Browserseite neu**. Aus dem abgerundeten Roboter wird ein kreisförmiger Körper. Der Java-Code bleibt unverändert. Versuchen Sie anschließend eine andere Farbe und einen größeren Schatten.

> **Merksatz:** HTML legt die Struktur fest. CSS legt das Aussehen und die Größen fest. Java legt die Regeln, Positionen und Zustände fest.

---

## 7. Eigene Bilder, Kacheln und Sounds verwenden

Ein selbst erzeugtes CSS-Objekt ist für viele Figuren ausreichend. Für detailreichere Darstellungen eignen sich Bilddateien. Die Plattform erlaubt beides – auch im selben Spiel.

### 7.1 SVG-Bilder: scharf bei jeder Größe

Der Stern im ersten Beispiel liegt als **SVG-Datei** unter `games/sternenpfad/assets/stern.svg`.

![Stern aus einer SVG-Datei](../games/sternenpfad/assets/stern.svg)

SVG steht für *Scalable Vector Graphics*: Formen werden durch Linien, Flächen und Kurven beschrieben. SVG ist eine Textdatei, die man in einem Editor bearbeiten oder mit einem Grafikprogramm exportieren kann.

Der Anfang einer solchen Datei kann so aussehen:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     width="40" height="40" viewBox="0 0 40 40">
  <!-- Hier stehen beispielsweise die Punkte und Farben des Sterns. -->
</svg>
```

Die Werte `width="40"` und `height="40"` bezeichnen die bevorzugte Anzeigegröße der Grafik. `viewBox="0 0 40 40"` bezeichnet ihr **internes Koordinatensystem**. Wird das SVG später in einem 80 × 80 Pixel großen Element angezeigt, skaliert der Browser die Zeichnung entsprechend. Dadurch bleibt sie in der Regel scharf.

Die CSS-Regel des Sterns lautet sinngemäß:

```css
#field .stern {
    width: 40px;
    height: 40px;
    background: url('/game/assets/stern.svg') center / contain no-repeat;
    filter: drop-shadow(0 0 9px #ffcf55c8);
}
```

Entscheidend ist der Unterschied:

- **`width: 40px; height: 40px`** bestimmt die **Boxgröße des Spielobjekts**, die Java für Kollisionen verwenden sollte.
- **`background: url(...)`** lädt nur die Zeichnung in diese Box.
- **`contain`** passt das vollständige Bild proportional in die Box ein. Ein rechteckiges Bild kann dabei unbemalte Bereiche erhalten.
- **`drop-shadow(...)`** lässt den sichtbaren Stern leuchten, ohne seine rechnerische Kollisionsfläche zu vergrößern.

### 7.2 PNG und andere Rasterbilder

Ein PNG besteht aus Bildpunkten (Pixeln). Es kann zum Beispiel 64 × 64 Bildpunkte enthalten. Diese **Dateiauflösung** muss nicht mit der **Anzeigegröße im Spiel** übereinstimmen:

```css
#field .figur {
    width: 48px;
    height: 48px;
    background: url('/game/assets/figur.png') center / contain no-repeat;
}
```

Java sollte hier die **48 × 48 CSS-Pixel** des Objekts verwenden, nicht automatisch die 64 × 64 Bildpunkte aus der Datei. Für bewusst grobe Pixelgrafiken kann `image-rendering: pixelated` hilfreich sein.

**Empfehlung:** Wählen Sie bei einem ersten Spiel möglichst für jedes bewegliche Objekt feste CSS-Breiten und -Höhen und schreiben Sie dieselben Werte als Java-Konstanten auf. Das vereinfacht jede spätere Kollision.

### 7.3 Hintergrundbilder und Kacheln

Eine Kachel ist ein kleines Bild, das wiederholt wird. Beispiel:

```css
#field {
    background-image: url('/game/assets/gras.png');
    background-repeat: repeat;
    background-size: 32px 32px;
}
```

So kann eine kleine Grasgrafik das gesamte Spielfeld ausfüllen. Bei einem Kachelraster können Sie Java-Positionen mithilfe der Formel berechnen:

```java
int x = startX + spalte * kachelBreite;
int y = startY + zeile * kachelHoehe;
```

Es ist also nicht erforderlich, die Pixelposition jeder Kachel von Hand anzugeben. Wenn die Kacheln selbst unterschiedlich aussehen sollen, können Sie mehrere `<template>`-Vorlagen definieren und bei Spielbeginn mit `CREATE` positionieren.

### 7.4 Sounds

In der Szene steht beispielsweise:

```html
<audio id="pling" src="/game/assets/pling.wav" preload="auto"></audio>
```

Der Java-Befehl

```java
senden("SOUND pling");
```

startet die Wiedergabe. Das Audioelement kann genauso gut eine passende `.mp3`-Datei referenzieren, sofern der Browser das Format unterstützt.

**Besonderheit:** Browser erlauben Ton oft erst nach einer bewussten Benutzeraktion (beispielsweise einem Tastendruck oder Klick). Das ist eine Browserschutzregel, kein Fehler Ihres Java-Programms. Die mitgelieferten kurzen Töne sind selbst erzeugt; für eigene Spiele können Sie eigene Aufnahmen oder rechtmäßig nutzbare Sounddateien verwenden.

### 7.5 Ressourcen selbst erstellen und organisieren

Für den Einstieg eignen sich drei Vorgehensweisen:

1. **Nur CSS:** Rechtecke, Kreise, Verläufe, Schatten und Raster benötigen gar keine Bilddatei.
2. **SVG:** Eine einfache Zeichnung als Vektorgrafik speichern, den `viewBox` kontrollieren und die Datei im `assets`-Ordner ablegen.
3. **PNG:** Eine kleine Rastergrafik zeichnen oder exportieren, transparente Hintergründe nutzen und die Anzeigegröße ausdrücklich im CSS festlegen.

Verwenden Sie sprechende Namen wie `spieler.svg`, `ball.png` oder `treffer.wav`. Achten Sie bei fremden Grafiken und Sounds auf die Nutzungsrechte und die erforderliche Quellenangabe. Für Lehrprojekte sind selbst erstellte Ressourcen besonders gut geeignet.

---

## 8. Koordinaten, Größen und Kollisionen

Dies ist einer der wichtigsten Teile beim Entwurf eines Spiels. **Wenn Java eine Kollision berechnen soll, muss Java die Positionen und Größen der beteiligten Objekte kennen.** Der Browser liefert diese Informationen in der aktuellen Protokollversion **nicht zurück**.

### 8.1 Das Koordinatensystem

Die linke obere Ecke des Spielfelds ist der Ausgangspunkt:

```text
(0,0) ─────────────────────────────→ x
  │
  │       (x,y) ●─────── Breite ───┐
  │             │                  │
  │             │       Objekt     │ Höhe
  │             │                  │
  │             └──────────────────┘
  ▼
  y
```

- **x** wird nach rechts größer.
- **y** wird nach unten größer.
- `MOVE figur 100 120` setzt die **linke obere Ecke** der Objektbox auf (100, 120).
- Bei einem Spielfeld von 640 × 400 Pixeln liegt der rechte Rand bei x = 640, der untere bei y = 400.

Eine 40 Pixel breite Figur darf mit ihrer linken oberen Ecke also höchstens bis x = 600 bewegt werden, wenn sie vollständig sichtbar bleiben soll (`640 - 40 = 600`). Entsprechend gilt bei 400 Pixel Höhe: y höchstens 360.

> Das sichtbare Bild kann Transparenz oder einen Leuchteffekt besitzen. Für einfache Kollisionen verwendet man gewöhnlich trotzdem die **rechteckige CSS-Box**, nicht die genaue Kontur der leuchtenden Bildpunkte.

### 8.2 Woher kennt Java Breite und Höhe?

Aus der vorher vereinbarten **Spieldefinition**:

```css
#field .kugel {
    width: 22px;
    height: 22px;
}
```

Dazu steht im Java-Programm:

```java
private static final int BALL = 22;
```

Das ist keine automatische Synchronisation, sondern eine **bewusste Vereinbarung**. Ändern Sie die CSS-Größe auf `30px`, müssen Sie die Java-Konstante ebenfalls auf `30` setzen. Andernfalls können sichtbare Darstellung und Kollisionsrechnung auseinanderlaufen.

**Wichtig zur CSS-Größenberechnung:** Das zentrale Browser-CSS verwendet `box-sizing: border-box`. Deshalb enthält ein festgelegtes `width: 40px` bereits den Rand (`border`). Die 40 × 40 Pixel gelten als gesamte Box. Die früher übliche Addition von Rand und Innenabstand ist hier für solche Elemente nicht erforderlich. Dagegen können **äußere Margins und zusätzliche Transformations-/Skalierungseffekte** die Zuordnung erschweren; vermeiden Sie sie bei ersten beweglichen Objekten.

### 8.3 Rasterkollision: gleiche Zelle

Im Sternenpfad bewegen sich alle Figuren in einem 48-Pixel-Raster. Ein Stern bei `(184, 176)` wird eingesammelt, wenn der Roboter ebenfalls bei `(184, 176)` steht:

```java
if (x == sternX && y == sternY) {
    // Beide stehen in derselben Rasterposition.
}
```

Diese Methode ist besonders einfach und zuverlässig, wenn alle Bewegungen genau in ganzen Rasterzellen erfolgen. Sie würde bei einer frei beweglichen Kugel jedoch nicht mehr ausreichen.

### 8.4 Rechteckkollision: überlappende Flächen

Für zwei achsenparallele Rechtecke (also nicht gedrehte Boxen) reichen folgende Daten:

- Objekt A: `ax`, `ay`, `aw`, `ah`.
- Objekt B: `bx`, `by`, `bw`, `bh`.

Eine Überlappung liegt vor, wenn **alle vier Bedingungen** erfüllt sind:

```java
boolean beruehrt =
        ax < bx + bw &&
        ax + aw > bx &&
        ay < by + bh &&
        ay + ah > by;
```

Warum? Die linke Kante von A muss links von der rechten Kante von B liegen. Umgekehrt muss seine rechte Kante rechts von der linken Kante von B liegen. Dasselbe gilt für oben und unten. **Nur wenn sich die Bereiche in beiden Richtungen überschneiden, liegt eine Kollision vor.**

Beispiel:

```text
Ball:     x=110, y=320, Breite=22, Höhe=22
Schläger: x= 90, y=340, Breite=96, Höhe=18

Horizontal: 110 < 90+96   und   110+22 > 90    → ja
Vertikal:   320 < 340+18  und   320+22 > 340   → ja
Kollision: ja
```

Die Formel verwendet `<` und `>`. Berühren sich die Boxen genau an der Kante, ohne eine gemeinsame Fläche zu haben, zählt das in dieser Variante **nicht** als Überlappung. Mit `<=` und `>=` ließe sich die Definition ändern.

### 8.5 Warum kann eine Kollision manchmal falsch aussehen?

Prüfen Sie in dieser Reihenfolge:

1. Sind die **Java-Koordinaten** wirklich die linke obere Ecke?
2. Stimmen die **CSS-Breiten und -Höhen** mit den Java-Konstanten überein?
3. Enthält das Bild **transparente Ränder** oder gibt es große Schatten? Diese verändern die Box nicht.
4. Hat das Objekt zusätzliche `margin`, `left`, `top`, eine Skalierung oder eine Rotation?
5. Wurde die Position zuletzt tatsächlich mit `MOVE` aktualisiert?
6. Reicht die Schrittweite aus, um bei schneller Bewegung durch ein dünnes Hindernis zu springen? Für schnelle Objekte braucht man eventuell kleinere Zeitschritte oder eine genauere Kollisionsprüfung.

Das Balllabor verwendet bewusst rechteckige Boxen, obwohl die sichtbare Kugel rund ist. Diese Näherung ist für ein erstes Spiel zweckmäßig und sehr einfach zu berechnen.

---

## 9. Beispiel B: Balllabor – Animation mit Ticks

Öffnen Sie `games/balllabor/Balllabor.java`. In diesem Spiel soll die Welt auch dann weiterlaufen, wenn niemand eine Taste drückt.

### Schritt 1: Ticks einschalten

In `game.ini` steht:

```ini
[game]
title = Balllabor – Bewegung mit Ticks
width = 640
height = 400
tick_ms = 33
```

Das Java-Programm erhält regelmäßig eine Zeile wie:

```text
TICK 33
```

Die Zahl 33 bedeutet 33 Millisekunden, also ungefähr **30 Aktualisierungen pro Sekunde**. Der Server kann bei hoher Auslastung Ticks auslassen. Die Zahl ist daher eine einfache **Simulationszeitstufe**, keine präzise Messung der Zeit seit dem letzten Ereignis.

### Schritt 2: Zustand für die Animation speichern

Die Java-Klasse besitzt Felder für die Positionen, Geschwindigkeiten und Tastenzustände:

```java
private double ballX, ballY;
private double geschwindigkeitX, geschwindigkeitY;
private double schlaegerX;
private boolean links, rechts, pause;
private int treffer;
```

Warum `double` statt `int`? Eine Bewegung von beispielsweise 175 Pixeln **pro Sekunde** entspricht in 33 Millisekunden ungefähr 5,775 Pixeln. Mit `double` gehen diese Zwischenwerte nicht verloren. Für den Browser werden die Positionen anschließend auf ganze Zahlen gerundet:

```java
senden("MOVE ball " + Math.round(ballX) + " " + Math.round(ballY));
```

### Schritt 3: „Taste ist gedrückt“ von „Taste wurde gedrückt“ unterscheiden

Beim ersten Beispiel bewirkt ein `KEYDOWN` einen einzelnen Schritt. Für eine gleichmäßige Bewegung soll der Schläger hingegen **so lange weiterfahren, wie die Taste gehalten wird**.

Dafür verwendet das Programm `boolean`-Variablen:

```java
if (zeile.equals("KEYDOWN ArrowLeft")) links = true;
if (zeile.equals("KEYUP ArrowLeft"))   links = false;
```

Die tatsächliche Quelldatei verteilt die Verarbeitung auf die Methoden `tasteUnten(...)` und `tasteOben(...)`.

Bei jedem Tick prüft Java den Zustand:

```java
if (links && !rechts) schlaegerX -= 300 * dt;
if (rechts && !links) schlaegerX += 300 * dt;
```

Der Schläger bewegt sich mit einer Geschwindigkeit von 300 Pixeln **pro Sekunde**. Wenn keine Pfeiltaste gehalten wird, bleibt er stehen.

### Schritt 4: Die Zeitstufe verstehen

In der Methode `tick(...)` steht:

```java
double dt = Math.max(1, Math.min(millisekunden, 50)) / 1000.0;
ballX += geschwindigkeitX * dt;
ballY += geschwindigkeitY * dt;
```

`dt` steht für *delta time*, also die bei diesem Schritt verwendete Zeitdauer in **Sekunden**. Zum Beispiel ergibt `33 / 1000.0` den Wert `0.033`. Daraus folgt:

```text
Weg = Geschwindigkeit × Zeit
175 Pixel/Sekunde × 0,033 Sekunden ≈ 5,775 Pixel
```

Die Begrenzung auf maximal 50 Millisekunden schützt die Simulation vor sehr großen, versehentlichen Sprüngen. Bei diesem Prototyp wird die **konfigurierte** Tickdauer verwendet. Das genügt für den Einstieg; eine anspruchsvollere Simulation könnte später mit gemessenen Zeitstempeln oder einem festen Simulationsschritt arbeiten.

### Schritt 5: An den Rändern abprallen

Erreicht der Ball den rechten Rand, wird seine horizontale Geschwindigkeit negativ:

```java
if (ballX + BALL > FELD_BREITE) {
    ballX = FELD_BREITE - BALL;
    geschwindigkeitX = -Math.abs(geschwindigkeitX);
}
```

`Math.abs(...)` liefert den Betrag der Geschwindigkeit; das negative Vorzeichen bedeutet Bewegung nach links. Die Korrektur der Position verhindert, dass der Ball außerhalb des Spielfelds bleibt. Entsprechende Regeln gibt es für den linken Rand und die obere Begrenzung.

### Schritt 6: Den Schläger treffen

Im Quelltext folgt die Rechteckkollision:

```java
boolean beruehrt = geschwindigkeitY > 0
        && ballX < schlaegerX + SCHLAEGER_BREITE
        && ballX + BALL > schlaegerX
        && ballY < SCHLAEGER_Y + SCHLAEGER_HOEHE
        && ballY + BALL > SCHLAEGER_Y;
```

Der zusätzliche Test `geschwindigkeitY > 0` sorgt dafür, dass nur ein Ball, der **nach unten** fliegt, vom Schläger zurückgeworfen wird. Bei einem Treffer kehrt das Programm die vertikale Bewegungsrichtung um, erhöht den Punktestand und sendet `SOUND ping`.

Die Abmessungen von Ball und Schläger sind in Java als Konstanten vorhanden und stimmen mit `style.css` überein:

| Objekt | Java-Konstante | CSS |
|---|---|---|
| Ball | `BALL = 22` | `width: 22px; height: 22px` |
| Schläger | `SCHLAEGER_BREITE = 96`, `SCHLAEGER_HOEHE = 18` | `width: 96px; height: 18px` |

### Schritt 7: Pausieren und neu beginnen

Die Leertaste schaltet den Zustand `pause` um. Die Tick-Methode prüft ganz am Anfang:

```java
if (pause) return;
```

Solange `pause` wahr ist, verändert ein Tick keine Positionen. Auf Tastendrücke kann das Programm trotzdem reagieren. **Das ist eine wichtige Unterscheidung zwischen Eingabe und Simulation.**

Mit `R` oder einem Klick auf **Neu** wird `neu()` aufgerufen und der Startzustand wiederhergestellt.

### Ein erstes Experiment

Ändern Sie `geschwindigkeitX = 175` auf `geschwindigkeitX = 260`. Speichern Sie und beobachten Sie die Bewegung. Probieren Sie danach `tick_ms = 50` aus (dafür den Server vollständig neu starten). Warum ist der Ball nicht einfach bei jedem Tick um denselben festen Pixelbetrag verschoben worden?

---

## 10. Ereignisgesteuert oder zeitgesteuert?

Viele Spiele bestehen aus beiden Arten von Aktionen. Die Unterscheidung hilft aber beim Entwurf eines ersten Programms.

| Eigenschaft | Ereignisgesteuert: Sternenpfad | Zeitgesteuert: Balllabor |
|---|---|---|
| Konfiguration | `tick_ms = 0` | `tick_ms = 33` |
| Was löst Änderungen aus? | Tastendruck oder Klick | Ticks **und** Tasten/Klicks |
| Bewegung ohne Benutzereingabe | Nein | Ja |
| Typische Daten | Rasterkoordinaten, Punktestand | Positionen, Geschwindigkeiten, Tastenzustände |
| Typische Aufgaben | Rätsel, Brettspiele, Schachzüge, Menüs | Ballspiele, Geschicklichkeitsspiele, laufende Animationen |
| Java-Eingabeschleife | Blockierendes `readLine()` | Genau dasselbe blockierende `readLine()` |

**Bei beiden Varianten ist die Eingabeschleife gleich.** Unterschiedlich ist nur, ob der Server regelmäßig `TICK`-Zeilen in den Eingabestrom schreibt und ob das Java-Programm diese Zeilen verarbeitet.

### Ein häufiger Irrtum: „Für Ticks braucht Java einen eigenen Thread“

Nein. Die Infrastruktur erzeugt die Zeitereignisse. Das Java-Programm verarbeitet sie **nacheinander** in einer einzigen Schleife. Das hat für Anfängerinnen und Anfänger einen großen Vorteil: Es gibt zunächst keine konkurrierenden Zugriffe auf die Spielvariablen.

Auch `KEYDOWN`, `KEYUP` und `CLICK` werden in genau dieser Reihenfolge über dieselbe Eingabeschleife verarbeitet. Die Zustände `links` und `rechts` bleiben zwischen zwei Nachrichten erhalten, weil sie **Attribute eines Java-Objekts** sind.

### Wie schnell sollten Ticks sein?

- **`tick_ms = 0`:** Nur Ereignisse; ideal für erste Programme ohne Animation.
- **`tick_ms = 50`:** Ungefähr 20 Aktualisierungen pro Sekunde; für einfache Animationen oft ausreichend.
- **`tick_ms = 33`:** Ungefähr 30 Aktualisierungen pro Sekunde; ein guter Ausgangspunkt.
- **`tick_ms = 16`:** Ungefähr 60 Aktualisierungen pro Sekunde; etwas mehr Ausgaben und Rechenarbeit.

Das sind **Zielintervalle**, keine garantierten Bildwiederholraten. Der Browser kann anders schnell zeichnen und die Server können bei Überlast Ticks verwerfen. Für den Einstieg zählt eine stabile und verständliche Simulation mehr als eine möglichst hohe Tickrate.

---

## 11. Fehler suchen, Dateien ändern und neu starten

### Java-Dateien: automatisches Übersetzen und Neustarten

Der Server überwacht die `.java`-Dateien direkt im Spielordner. Nach dem Speichern kompiliert er sie mit `javac` neu. Wenn die Übersetzung gelingt, beendet er den alten Java-Spielprozess und startet einen neuen. Das Spiel beginnt dabei **von vorn**; alte Variablenwerte bleiben nicht erhalten.

Entsteht ein Syntaxfehler, erscheint die **Compilerfehlermeldung direkt im Browser**. Nach einer Korrektur und erneutem Speichern erfolgt ein weiterer Kompilierungsversuch. Es ist nicht erforderlich, den Browser zu schließen.

### CSS, HTML, Bilder und Konfiguration

| Was wurde geändert? | Was ist zu tun? |
|---|---|
| `.java` | Speichern; der Server kompiliert und startet das Java-Spiel automatisch neu. |
| `style.css` oder `scene.html` | Browserseite neu laden (gegebenenfalls Cache umgehen). |
| Bild-/Sounddatei im `assets/`-Ordner | Browserseite neu laden; gegebenenfalls Cache umgehen. |
| `game.ini` | Gesamten Server beenden und erneut starten. |

Mit dem Webseiten-Button **Java neu starten** starten Sie nur den Spielprozess neu. **Server beenden** schließt den Spielprozess und den lokalen Server. Sie können auch `Strg+C` im Terminal verwenden.

### Debugging: Verwenden Sie `System.err`

Die Standardausgabe ist für Spielbefehle reserviert:

```java
senden("MOVE spieler 120 240");            // richtig: Protokoll
System.err.println("Position: " + x);     // richtig: Diagnose
```

Das wäre dagegen ein Fehler:

```java
System.out.println("Position: " + x);     // kein gültiger Spielbefehl!
```

Öffnen Sie auf der Webseite bei Bedarf das **Diagnoseprotokoll**. Dort sehen Sie Ausgaben von `System.err` und Warnungen über ungültige Protokollzeilen. Der Java-Prozess bleibt auch bei normalen Warnungen zunächst eigenständig; ein schwerer Laufzeitfehler kann ihn jedoch beenden.

### Wenn nichts sichtbar wird

Prüfen Sie systematisch:

1. Meldet die Browseroberfläche **„Spiel läuft“** oder einen Compilerfehler?
2. Hat die Java-Klasse eine `main`-Methode und stimmt ihr Name mit dem Dateinamen überein?
3. Wird eine `CREATE`-Nachricht für die Objekt-ID gesendet?
4. Existiert in `scene.html` die passende `<template id="…">`-Vorlage?
5. Sind in `style.css` **Breite und Höhe** für das Objekt definiert?
6. Ist das Objekt eventuell mit `HIDE` verborgen oder liegt es außerhalb des Spielfelds?
7. Ist die Meldung korrekt formatiert und wurde sie auf `stdout` ausgegeben?
8. Ist die Browserseite nach einer Änderung von CSS oder HTML neu geladen worden?

### Einige technische Grenzen des Lernprototyps

Protokoll und Server sind bewusst einfach gehalten. Es gibt noch keine Abfrage der DOM-Abmessungen von Java aus, keine vollständige Physikengine und keine Unterstützung für verschachtelte Java-Packages. Der Server ist für die **lokale Arbeit auf dem eigenen Rechner** gedacht. Er führt gewöhnlichen Java-Code aus und sollte **nicht ungeschützt im Internet oder als gemeinsamer Ausführungsserver für fremde Programme** angeboten werden.

---

## 12. Ein eigenes Spiel planen

Beginnen Sie nicht mit einer möglichst aufwendigen Grafik. Formulieren Sie zuerst die Regel: **Was kann die Spielfigur tun, was ist das Ziel, wann ist das Spiel vorbei?**

Ein guter erster Entwurf passt auf eine halbe Seite:

1. **Spielidee:** Beispielsweise ein Gegenstand, den eine Figur erreichen soll, ohne ein Hindernis zu berühren.
2. **Spielfeld:** `width`, `height`, gegebenenfalls Kachelgröße und Abstände festlegen.
3. **Objekte:** Für jede Figur eine Vorlage und eine feste CSS-Größe bestimmen.
4. **Datenmodell:** Welche Variablen braucht Java? Mindestens Positionen, gegebenenfalls Geschwindigkeit, Punkte und Spielzustand.
5. **Eingaben:** Reichen einzelne `KEYDOWN`-Ereignisse oder sollen Tasten gehalten werden?
6. **Zeitsteuerung:** Muss etwas ohne Eingabe weiterlaufen? Wenn ja, `tick_ms` auf 33 oder 50 setzen.
7. **Kollision:** Rastergleichheit oder Rechtecküberlappung verwenden? Sind die Größen in Java bekannt?
8. **Darstellung:** Bei jeder Änderung gezielt `MOVE`, `TEXT`, `HIDE` oder andere Befehle senden.
9. **Rückmeldung:** Neue Punkte, ein Sound oder eine sichtbare Gewinnmeldung machen eine Regel verständlich.
10. **Testen:** Mit wenigen Objekten beginnen und das Spiel Schritt für Schritt erweitern.

### Einen neuen Spielordner anlegen

Kopieren Sie als Ausgangspunkt beispielsweise `games/sternenpfad/` nach `games/mein_spiel/`. Benennen Sie die Java-Datei und die darin enthaltene öffentliche Klasse in `MeinSpiel.java` und `MeinSpiel` um. Wählen Sie einen Titel in `game.ini`. Starten Sie dann:

```bash
java server-java/ArcadeServer.java games/mein_spiel/MeinSpiel.java
```

**Wichtig:** Den Befehl weiterhin im **Hauptverzeichnis des Gesamtprojekts** ausführen, da der Server von dort die allgemeinen Browserdateien in `web/` sucht. Starten Sie nicht aus dem kopierten Unterordner heraus.

### Ein sinnvolles erstes eigenes Programm

Ein vollständiges Spiel muss nicht sofort mehrere Hundert Zeilen umfassen. Beginnen Sie mit einer einzigen Figur und zwei Tastaturbefehlen. Ergänzen Sie eine zweite Figur, die ein Ziel darstellt. Danach erst folgen die Regeln für den Punktestand und den Neustart.

Damit bietet das Spiel einen unmittelbaren Anlass, die grundlegenden Java-Konzepte weiterzuentwickeln: **Aus einzelnen Variablen werden Attribute, aus wiederholten Anweisungen Methoden, aus ähnlichen Figuren Klassen und später aus mehreren Objekten Listen.**

---

## 13. Häufige Fragen und wichtige Begriffe

**Wird Java im Browser ausgeführt?** Nein. Der Browser führt nur das vorbereitete HTML/CSS/JavaScript aus. Das eigene Java-Programm läuft als **separater lokaler Prozess** und kommuniziert über Textzeilen.

**Muss ich HTML und CSS beherrschen?** Nein, um die ersten Java-Spiele zu programmieren, genügen die mitgelieferten Vorlagen. Für eigene Figuren, neue Größen und Grafikeffekte ist es hilfreich, wenige HTML- und CSS-Grundlagen kennenzulernen. Abschnitt 6 erklärt die wichtigsten davon.

**Warum wird kein JSON verwendet?** Die Nachrichten enthalten nur sehr wenige Werte. `MOVE figur 100 120` lässt sich ohne Zusatzbibliothek schreiben, lesen und prüfen. Für komplexere Daten könnte man das Protokoll später erweitern.

**Warum verwende ich im Java-Programm `readLine()`?** Weil jede eingehende Nachricht genau eine Zeile ist. Das blockierende Lesen sorgt dafür, dass das Programm auf ein Ereignis wartet, statt permanent selbst nach Eingaben zu suchen.

**Warum braucht ein tickgesteuertes Spiel keine Threads im studentischen Programm?** Der Server liefert die Ticks bereits über denselben Eingabestrom wie die Tastaturereignisse. Java verarbeitet die Nachrichten nacheinander.

**Woher kennt Java die Abmessungen der Bilder?** Die Größe der **Anzeige- und Kollisionsbox** steht fest im CSS und als passende Konstante im Java-Programm. Die ursprüngliche Dateiauflösung eines PNGs oder der `viewBox` eines SVG ist nicht automatisch die Kollisionsgröße.

**Was ist eine HTML-ID?** Eine eindeutige Bezeichnung eines Elements, etwa `spieler` oder `punkte`. Über diese ID kann der Browser das Element finden. Bei `CREATE spieler roboter` erhält die neu erzeugte Figur die ID `spieler`.

**Was ist ein Template?** Ein HTML-Muster, das zunächst nicht angezeigt wird. Der Befehl `CREATE` erstellt daraus eine sichtbare oder später positionierbare Kopie.

**Was ist ein Tick?** Ein regelmäßig erzeugtes Ereignis, mit dem das Java-Programm die Spielwelt einen kleinen Schritt weiterberechnet.

**Was bedeutet „Kollision“?** Eine Regel, die überprüft, ob sich Objekte treffen. Für Rasterspiele genügt oft ein Vergleich der Zellen; für frei bewegliche, nicht gedrehte Objekte ist die Rechtecküberlappung ein sinnvoller Einstieg.

**Warum reagieren mehrere Browser-Tabs auf dasselbe Spiel?** Der Server verwaltet jeweils einen Java-Spielprozess und kann den Darstellungszustand an verbundene Browseransichten weitergeben. Das sind keine getrennten Spielinstanzen.

**Kann man später mehr machen?** Ja. Die Protokollbefehle sind bewusst klein. Sie können zusätzliche Objektarten, komplexere Java-Klassen, Menüs, weitere Sounds und aufwendigere Regeln nutzen, ohne die grundlegende Architektur zu ändern.

---

## Zum Weiterlesen und Weiterentwickeln

- **[Protokoll – vollständige Befehle und Ereignisse](PROTOKOLL.md)**: die technische Referenz mit Formatregeln und Fehlersuche.
- **[Übungs- und Erweiterungsideen](AUFGABEN.md)**: Aufgaben zu Grafiken, Zuständen, Kollisionen und Objektorientierung.
- **[Sternenpfad – Java-Quelltext](../games/sternenpfad/Sternenpfad.java)** und **[Sternenpfad – CSS](../games/sternenpfad/style.css)**.
- **[Balllabor – Java-Quelltext](../games/balllabor/Balllabor.java)** und **[Balllabor – CSS](../games/balllabor/style.css)**.

**Der wichtigste Gedanke zum Abschluss:** Die grafische Oberfläche ist nur eine Darstellung Ihres Java-Modells. Wenn Sie die Spielregeln und Daten sauber in Klassen und Methoden ausdrücken können, reichen oft schon wenige Textbefehle, um daraus ein sichtbares und interaktives Spiel zu machen.
