import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

/** Zweites Beispiel: kontinuierliche Simulation, Tastenzustände und TICK. */
public class Balllabor {
    private static final int FELD_BREITE = 640;
    private static final int BALL = 22;
    private static final int SCHLAEGER_BREITE = 96;
    private static final int SCHLAEGER_HOEHE = 18;
    private static final int SCHLAEGER_Y = 344;

    private final PrintWriter ausgabe = new PrintWriter(System.out, true);
    private double ballX, ballY, geschwindigkeitX, geschwindigkeitY, schlaegerX;
    private boolean links, rechts, pause;
    private int treffer;

    private void senden(String befehl) {
        ausgabe.println(befehl);
    }

    private void neu() {
        schlaegerX = 272;
        ballX = 306;
        ballY = 170;
        geschwindigkeitX = 175; // Pixel pro Sekunde
        geschwindigkeitY = 205;
        links = rechts = pause = false;
        treffer = 0;
        senden("CREATE ball kugel");
        senden("CREATE paddle schlaeger");
        senden("TEXT anzeige Treffer: 0");
        senden("TEXT nachricht Pfeiltasten: Schläger · Leertaste: Pause");
        zeichnen();
    }

    private void zeichnen() {
        senden("MOVE ball " + Math.round(ballX) + " " + Math.round(ballY));
        senden("MOVE paddle " + Math.round(schlaegerX) + " " + SCHLAEGER_Y);
    }

    private void tasteUnten(String code) {
        switch (code) {
            case "ArrowLeft"  -> links = true;
            case "ArrowRight" -> rechts = true;
            case "Space" -> {
                pause = !pause;
                senden(pause ? "TEXT nachricht PAUSE – Leertaste setzt fort"
                             : "TEXT nachricht Das Spiel läuft wieder.");
            }
            case "KeyR" -> neu();
            default -> { }
        }
    }

    private void tasteOben(String code) {
        if (code.equals("ArrowLeft")) links = false;
        if (code.equals("ArrowRight")) rechts = false;
    }

    private void tick(int millisekunden) {
        if (pause) return;
        // Ein Server kann einen verspäteten Tick liefern. Deshalb begrenzen wir dt.
        double dt = Math.max(1, Math.min(millisekunden, 50)) / 1000.0;
        if (links && !rechts) schlaegerX -= 300 * dt;
        if (rechts && !links) schlaegerX += 300 * dt;
        schlaegerX = Math.max(0, Math.min(FELD_BREITE - SCHLAEGER_BREITE, schlaegerX));

        ballX += geschwindigkeitX * dt;
        ballY += geschwindigkeitY * dt;
        if (ballX < 0) { ballX = 0; geschwindigkeitX = Math.abs(geschwindigkeitX); }
        if (ballX + BALL > FELD_BREITE) {
            ballX = FELD_BREITE - BALL;
            geschwindigkeitX = -Math.abs(geschwindigkeitX);
        }
        if (ballY < 62) { ballY = 62; geschwindigkeitY = Math.abs(geschwindigkeitY); }

        // Rechteck-Kollision: Positionen entsprechen den CSS-Abmessungen.
        boolean beruehrt = geschwindigkeitY > 0
                && ballX < schlaegerX + SCHLAEGER_BREITE
                && ballX + BALL > schlaegerX
                && ballY < SCHLAEGER_Y + SCHLAEGER_HOEHE
                && ballY + BALL > SCHLAEGER_Y;
        if (beruehrt) {
            ballY = SCHLAEGER_Y - BALL;
            geschwindigkeitY = -Math.abs(geschwindigkeitY);
            treffer++;
            senden("TEXT anzeige Treffer: " + treffer);
            senden("SOUND ping");
        }
        if (ballY > 400) {
            senden("TEXT nachricht Daneben! Der Ball beginnt erneut. R: Neustart");
            ballX = 306;
            ballY = 170;
            geschwindigkeitY = 205;
        }
        zeichnen();
    }

    private void laufen() throws Exception {
        neu();
        BufferedReader eingabe = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String zeile;
        while ((zeile = eingabe.readLine()) != null) {
            if (zeile.startsWith("KEYDOWN ")) tasteUnten(zeile.substring(8));
            else if (zeile.startsWith("KEYUP ")) tasteOben(zeile.substring(6));
            else if (zeile.startsWith("TICK ")) {
                try { tick(Integer.parseInt(zeile.substring(5))); }
                catch (NumberFormatException e) { System.err.println("Ungültiger Tick: " + zeile); }
            }
            else if (zeile.startsWith("CLICK neustart ")) neu();
        }
    }

    public static void main(String[] args) throws Exception {
        new Balllabor().laufen();
    }
}
