# Spiele in Java – Einstieg und Handbuch

**Ein Spiel in Java schreiben und im Browser sehen:** Dafür benötigt man weder ein Grafikframework noch HTML- oder JavaScript-Kenntnisse. Java entscheidet, *was* geschieht. Eine vorbereitete Webseite zeigt die Spielobjekte an und übermittelt Tastatur- und Mausereignisse.

Dieses Lernmaterial richtet sich an Studierende im ersten Semester Informatik mit ersten Kenntnissen in Java (Klassen, Variablen, Methoden, `if` und Schleifen). Die Beispiele verwenden ausschließlich Java und die Dateien, die im Projekt enthalten sind.

## Hier beginnen

1. **[Handbuch lesen](HANDBUCH.md)** – vom ersten Start bis zum eigenen Spiel, mit schrittweisen Erklärungen zu zwei vollständigen Beispielen, Grafikressourcen, CSS und Kollisionen.
2. **[Protokoll nachschlagen](PROTOKOLL.md)** – alle Ausgabebefehle, Eingabeereignisse, zulässigen IDs und typische Fehler.
3. **[Ideen und Übungen](AUFGABEN.md)** – kleine, aufeinander aufbauende Aufgaben zum Experimentieren und selbstständigen Entwerfen.

## Die zwei Lernbeispiele

| Beispiel | Startbefehl im **Projekt-Hauptverzeichnis** | Was wird gelernt? |
|---|---|---|
| **Sternenpfad** | `java server-java/ArcadeServer.java games/sternenpfad/Sternenpfad.java` | Auf Tastendrücke warten, Figuren bewegen, Sterne einsammeln, Kollision auf einem Raster, SVG, CSS, Sound, Mausklick |
| **Balllabor** | `java server-java/ArcadeServer.java games/balllabor/Balllabor.java` | Regelmäßige `TICK`-Ereignisse, Geschwindigkeit, Tasten gedrückt halten, Rechteckkollision, Animation und Pausieren |

Für die neuen Beispiele liegen auch Startskripte im Hauptverzeichnis: `start-sternenpfad-java.sh`/`.bat` und `start-balllabor-java.sh`/`.bat` (für den Python-Server entsprechend ohne `-java`).

Anschließend **http://127.0.0.1:8765/** im Browser öffnen. Vor dem Wechsel zum anderen Beispiel den ersten Server mit **„Server beenden“** auf der Webseite schließen.

**Voraussetzung:** Java **JDK 17 oder neuer**; `java` und `javac` müssen verfügbar sein. Beide Beispiele laufen auch mit dem alternativen Python-Server (`python3 server.py games/sternenpfad/Sternenpfad.java` bzw. `games/balllabor/Balllabor.java`). Python wird bei Verwendung des Java-Servers **nicht** benötigt.

Die beiden umfangreicheren Spiele in `games/space_invaders/` und `games/sokoban/` sind **separate Anwendungen** und werden in diesem Handbuch nicht behandelt.
