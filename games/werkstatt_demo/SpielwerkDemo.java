import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;

/** Werkstatt-Demo: Java steuert die im Browser-Editor gestaltete Figur. */
public class SpielwerkDemo {
    static final int FELD_BREITE = 600;
    static final int FELD_HOEHE = 380;
    static final int FIGUR_BREITE = 64; // siehe Spielwerkstatt
    static final int FIGUR_HOEHE = 72;
    static int x = 260, y = 175;

    public static void main(String[] args) throws Exception {
        PrintWriter out = new PrintWriter(System.out, true);
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        out.println("CREATE roboter sw-roboter");
        out.println("MOVE roboter " + x + " " + y);
        out.println("TEXT info Pfeiltasten: Roboter bewegen · R: Neustart");
        String line;
        while ((line = in.readLine()) != null) {
            if (!line.startsWith("KEYDOWN ")) continue;
            String key = line.substring(8);
            if (key.equals("ArrowLeft")) x -= 16;
            if (key.equals("ArrowRight")) x += 16;
            if (key.equals("ArrowUp")) y -= 16;
            if (key.equals("ArrowDown")) y += 16;
            if (key.equals("KeyR")) { x = 260; y = 175; }
            x = Math.max(0, Math.min(FELD_BREITE - FIGUR_BREITE, x));
            y = Math.max(0, Math.min(FELD_HOEHE - FIGUR_HOEHE, y));
            out.println("MOVE roboter " + x + " " + y);
        }
    }
}
