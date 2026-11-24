# Spielwerk starten: Java- und Python-Webserver

**Standard ist der Java-Webserver.** Die Endung des Spielprogramms bestimmt
weiterhin, ob ein Java- oder Python-Spielprozess gestartet wird. Die Sprache
des Servers ist davon unabhängig.

Beispiel im Projektverzeichnis (macOS/Linux):

```sh
sh start-space-invaders.sh
```

Das startet den **Java-Webserver** und darin das Java-Spiel *Space Invaders*.
Die anderen kurzen Startskripte (`start-sokoban.sh`, `start-sternenpfad.sh`,
`start-balllabor.sh`, `start-werkstatt.sh`) verhalten sich entsprechend.
Unter Windows heißen die Kurzskripte `.bat` statt `.sh`.

Wer bewusst den **alternativen Python-Webserver** verwenden möchte, wählt
beispielsweise:

```sh
sh start-space-invaders-python-server.sh
```

Direktaufrufe bleiben wie bisher möglich:

```sh
java server-java/ArcadeServer.java games/space_invaders/SpaceInvaders.java
python3 server.py games/space_invaders/SpaceInvaders.java
```

**Werkstattressourcen sind optional:** Nur wenn im Spielverzeichnis unter
`spielwerk/` tatsächlich die Dateien `style.css`, `scene.html` oder
`layout.json` vorhanden sind, bindet die Spielseite sie ein. Spiele ohne
Werkstattdateien funktionieren unverändert. Nach dem Speichern neuer
Werkstattdateien die Spielseite einmal neu laden.

Wenn ein Browser eine noch offene HTTP-Verbindung schließt, ignoriert der
Python-Webserver den daraus entstehenden üblichen `ConnectionResetError`.
Andere Serverfehler werden weiterhin angezeigt.
