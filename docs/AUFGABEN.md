# Übungs- und Erweiterungsideen

Diese Aufgaben bauen auf den im [Handbuch](HANDBUCH.md) erklärten Beispielen **Sternenpfad** (ereignisgesteuert) und **Balllabor** (zeitgesteuert) auf. Beginnen Sie mit kleinen Änderungen, speichern Sie die Java-Datei und beobachten Sie die neue Version im Browser.

## Einstieg – die Oberfläche verstehen

1. **Farben und Formen:** Ändern Sie im Sternenpfad die Farbe des Roboters und seine Augen in `style.css`. Welche CSS-Deklaration erzeugt den Leuchteffekt? Ändern Sie diese.
2. **Grafik ersetzen:** Ersetzen Sie `assets/stern.svg` durch ein selbst gestaltetes SVG. Belassen Sie die CSS-Größe zunächst bei `40px × 40px`.
3. **Neuer Text:** Erweitern Sie `scene.html` um ein `<div id="begrueszung">` und verändern Sie es mit `TEXT begrueszung ...` aus Java.

## Ereignisgesteuertes Programmieren

4. **Weitere Sterne:** Fügen Sie im Sternenpfad zwei Sternpositionen hinzu. Passen Sie die Punktanzeige so an, dass die Anzahl nicht fest auf drei eingestellt ist.
5. **Hindernis:** Fügen Sie mit einem neuen `<template>` ein Hindernis hinzu, das eine Rasterzelle besetzt. Der Roboter darf diese Zelle nicht betreten. Entscheiden Sie vor dem Ändern von `x` oder `y`, ob der Zielort frei ist.
6. **Begrenzte Züge:** Zählen Sie Tastaturbewegungen und zeigen Sie nach beispielsweise 20 Zügen eine Meldung an. Was muss bei einem Neustart zurückgesetzt werden?
7. **Mausspiel:** Ersetzen Sie die Pfeiltastensteuerung probeweise durch `CLICK NONE x y`. Bei jedem Klick soll der Roboter auf die nächstgelegene Rasterposition springen. Die Koordinaten des Klicks müssen auf 48-Pixel-Schritte gerundet werden.

## Zeitgesteuertes Programmieren

8. **Andere Geschwindigkeit:** Ändern Sie im Balllabor die Bewegungsgeschwindigkeit des Balls. Warum sollte die Positionsänderung mit `dt` multipliziert werden?
9. **Schwierigkeitsgrad:** Erhöhen Sie nach jedem Schlägertreffer die Geschwindigkeit des Balls geringfügig. Begrenzen Sie die Geschwindigkeit auf einen sinnvollen Maximalwert.
10. **Leben statt automatischem Neustart:** Geben Sie drei Leben vor. Verliert der Ball den unteren Spielfeldrand, verringert sich der Lebenszähler. Nach dem dritten Verlust soll das Spiel pausieren.
11. **Gezielte Steuerung:** Verändern Sie beim Schlägertreffer die horizontale Bewegungsrichtung abhängig davon, wo der Ball den Schläger trifft.
12. **Weitere Objekte:** Erzeugen Sie ein zweites bewegliches Objekt und untersuchen Sie die Kollision mit dem Ball. Verwenden Sie zunächst fest definierte Breiten und Höhen.

## Objektorientierung

13. **Eine eigene Klasse:** Extrahieren Sie im Balllabor Position und Geschwindigkeit in eine Klasse `Ball`. Halten Sie diese Klasse zunächst in derselben Datei (ohne `public`). Später können Sie sie in eine eigene `Ball.java` im selben Spielordner verschieben. Der Server kompiliert alle `.java`-Dateien auf der obersten Ebene dieses Ordners.
14. **Mehrere Objekte:** Erzeugen Sie mehrere Bälle aus einer Klasse. Speichern Sie sie in einer `ArrayList<Ball>` und aktualisieren Sie ihre Positionen bei jedem Tick.
15. **Methoden und Zustände:** Unterscheiden Sie ausdrücklich die Zustände `START`, `LAEUFT`, `PAUSE`, `ENDE`. Welche Methoden dürfen in welchem Zustand eine Änderung auslösen?

## Fragen zur Selbstkontrolle

- Warum liest das Java-Programm `stdin` blockierend, ohne dadurch das Spiel anzuhalten?
- Warum muss der Browser keine Kenntnis über die Spielregeln besitzen?
- Weshalb sind `KEYDOWN` und `KEYUP` für gleichmäßige Bewegungen hilfreich, ein einzelner Tastendruck für eine Rasterbewegung dagegen ausreichend?
- Was ist der Unterschied zwischen `HIDE` und `REMOVE`?
- Woher kennt Java die Breite einer grafischen Figur?
- Warum kann eine Figur **sichtbar** kleiner wirken als ihre rechnerische Kollisionsfläche?
- Was würde passieren, wenn man `System.out.println("Position: " + x)` zum Debuggen verwendete?

**Abschlussidee:** Entwerfen Sie ein eigenes kleines Spiel mit einer klaren Regel, mindestens zwei sichtbaren Objekten und einem eindeutigen Spielende. Erstellen Sie zunächst eine Skizze und legen Sie danach die Daten (Koordinaten, Größen, Zustände) fest. Erst anschließend schreiben Sie die Darstellungsbefehle.
