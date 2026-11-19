import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Slow example: no TICKs at all, only KEYDOWN events. */
public class Sokoban {
    private static final int TILE = 56;
    private static final int X0 = 94;
    private static final int Y0 = 24;
    private static final String[] LEVEL = {
            "########",
            "#      #",
            "#  .   #",
            "#  $   #",
            "# .@$  #",
            "#      #",
            "#      #",
            "########"
    };

    private final PrintWriter out = new PrintWriter(System.out, true);
    private final Set<Integer> walls = new HashSet<>();
    private final Set<Integer> goals = new HashSet<>();
    private final List<Integer> boxes = new ArrayList<>();
    private final ArrayDeque<Snapshot> history = new ArrayDeque<>();
    private int player, steps;
    private boolean won;

    private static class Snapshot {
        int player, steps;
        List<Integer> boxes;
        Snapshot(int player, int steps, List<Integer> boxes) {
            this.player = player;
            this.steps = steps;
            this.boxes = new ArrayList<>(boxes);
        }
    }

    private int at(int x, int y) { return y * 8 + x; }
    private int x(int pos) { return pos % 8; }
    private int y(int pos) { return pos / 8; }
    private void send(String line) { out.println(line); }
    private void place(String id, int position) {
        send("MOVE " + id + " " + (X0 + TILE * x(position)) + " " + (Y0 + TILE * y(position)));
    }

    private void setup() {
        walls.clear();
        goals.clear();
        boxes.clear();
        history.clear();
        steps = 0;
        won = false;
        for (int row = 0; row < LEVEL.length; row++) {
            for (int col = 0; col < LEVEL[row].length(); col++) {
                int pos = at(col, row);
                char symbol = LEVEL[row].charAt(col);
                if (symbol == '#') {
                    walls.add(pos);
                    String id = "wall_" + row + "_" + col;
                    send("CREATE " + id + " wall");
                    place(id, pos);
                }
                if (symbol == '.') {
                    goals.add(pos);
                    String id = "goal_" + row + "_" + col;
                    send("CREATE " + id + " goal");
                    place(id, pos);
                }
                if (symbol == '$') boxes.add(pos);
                if (symbol == '@') player = pos;
            }
        }
        for (int i = 0; i < boxes.size(); i++) {
            send("CREATE crate_" + i + " crate");
            place("crate_" + i, boxes.get(i));
        }
        send("CREATE player hero");
        place("player", player);
        updateStatus();
        System.err.println("Sokoban gestartet: keine Tick-Ereignisse, nur Tasten.");
    }

    private void updateStatus() {
        send("TEXT moves Züge: " + steps);
        if (won) {
            send("TEXT message Geschafft in " + steps + " Zügen! R = Neustart");
        } else {
            send("TEXT message Pfeiltasten: Schieben · Z: zurück · R: neu starten");
        }
    }

    private void renderPositions() {
        place("player", player);
        for (int i = 0; i < boxes.size(); i++) place("crate_" + i, boxes.get(i));
        updateStatus();
    }

    private void undo() {
        if (history.isEmpty()) return;
        Snapshot previous = history.pop();
        player = previous.player;
        steps = previous.steps;
        boxes.clear();
        boxes.addAll(previous.boxes);
        won = false;
        renderPositions();
    }

    private void movePlayer(int dx, int dy) {
        if (won) return;
        int px = x(player) + dx;
        int py = y(player) + dy;
        if (px < 0 || px >= 8 || py < 0 || py >= 8) return;
        int next = at(px, py);
        if (walls.contains(next)) return;
        int boxIndex = boxes.indexOf(next);
        if (boxIndex >= 0) {
            int bx = px + dx;
            int by = py + dy;
            if (bx < 0 || bx >= 8 || by < 0 || by >= 8) return;
            int destination = at(bx, by);
            if (walls.contains(destination) || boxes.contains(destination)) return;
            history.push(new Snapshot(player, steps, boxes));
            boxes.set(boxIndex, destination);
            place("crate_" + boxIndex, destination);
        } else {
            history.push(new Snapshot(player, steps, boxes));
        }
        player = next;
        steps++;
        place("player", player);
        send("SOUND step");
        if (goals.containsAll(boxes)) {
            won = true;
            send("SOUND won");
        }
        updateStatus();
    }

    private void keyDown(String key) {
        switch (key) {
            case "ArrowLeft": movePlayer(-1, 0); break;
            case "ArrowRight": movePlayer(1, 0); break;
            case "ArrowUp": movePlayer(0, -1); break;
            case "ArrowDown": movePlayer(0, 1); break;
            case "KeyZ": undo(); break;
            case "KeyR": setup(); break;
            default: break;
        }
    }

    private void run() throws Exception {
        setup();
        BufferedReader input = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        // readLine blocks until the browser delivers a key; no timer and no polling.
        while ((line = input.readLine()) != null) {
            if (line.startsWith("KEYDOWN ")) keyDown(line.substring(8));
            if (line.startsWith("CLICK resetTiles ")) setup();
        }
    }

    public static void main(String[] args) throws Exception {
        new Sokoban().run();
    }
}
