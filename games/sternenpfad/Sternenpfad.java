import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

/** Erstes Beispiel: ausschließlich Tasten- und Klickereignisse, kein TICK. */
public class Sternenpfad {
    // Die Koordinaten sind die linke obere Ecke der 40 x 40 Pixel großen Figuren.
    private static final int SCHRITT = 48;
    private static final int LINKS = 40, RECHTS = 568;
    private static final int OBEN = 80, UNTEN = 320;
    private static final int[] STERN_X = {184, 328, 472};
    private static final int[] STERN_Y = {176, 224, 128};

    private final PrintWriter ausgabe = new PrintWriter(System.out, true);
    private final boolean[] eingesammelt = new boolean[STERN_X.length];
    private int x, y, punkte;

    private void senden(String befehl) {
        ausgabe.println(befehl); // Ein Befehl pro Zeile; Auto-Flush ist eingeschaltet.
    }

    private void neu() {
        x = 88;
        y = 272;
        punkte = 0;
        for (int i = 0; i < STERN_X.length; i++) {
            eingesammelt[i] = false;
            senden("CREATE gold_" + i + " stern");
            senden("MOVE gold_" + i + " " + STERN_X[i] + " " + STERN_Y[i]);
            senden("SHOW gold_" + i);
        }
        senden("CREATE spieler roboter");
        zeichnen();
        senden("TEXT punkte Sterne: 0 / 3");
        senden("TEXT hinweis Bewege den Roboter mit den Pfeiltasten.");
    }

    private void zeichnen() {
        senden("MOVE spieler " + x + " " + y);
    }

    private void taste(String code) {
        switch (code) {
            case "ArrowLeft"  -> x = Math.max(LINKS, x - SCHRITT);
            case "ArrowRight" -> x = Math.min(RECHTS, x + SCHRITT);
            case "ArrowUp"    -> y = Math.max(OBEN, y - SCHRITT);
            case "ArrowDown"  -> y = Math.min(UNTEN, y + SCHRITT);
            case "KeyR"      -> { neu(); return; }
            default          -> { return; }
        }
        zeichnen();
        for (int i = 0; i < STERN_X.length; i++) {
            if (!eingesammelt[i] && x == STERN_X[i] && y == STERN_Y[i]) {
                eingesammelt[i] = true;
                punkte++;
                senden("HIDE gold_" + i);
                senden("SOUND pling");
                senden("TEXT punkte Sterne: " + punkte + " / " + STERN_X.length);
                if (punkte == STERN_X.length)
                    senden("TEXT hinweis Alle Sterne gefunden! R startet erneut.");
            }
        }
    }

    private void laufen() throws Exception {
        neu();
        BufferedReader eingabe = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String zeile;
        // readLine wartet, bis ein Ereignis eintrifft. Das ist beabsichtigt.
        while ((zeile = eingabe.readLine()) != null) {
            if (zeile.startsWith("KEYDOWN ")) {
                taste(zeile.substring(8));
            } else if (zeile.startsWith("CLICK neu ")) {
                neu();
            }
        }
    }

    public static void main(String[] args) throws Exception {
        new Sternenpfad().laufen();
    }
}
