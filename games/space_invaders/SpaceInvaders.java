import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/** Dynamic example: the server supplies TICK 33; Java owns all game logic. */
public class SpaceInvaders {
    private final PrintWriter out = new PrintWriter(System.out, true);
    private static final int WIDTH = 640;
    private static final int HEIGHT = 480;
    private final List<Alien> aliens = new ArrayList<>();
    private final List<Shot> shots = new ArrayList<>();
    private double playerX;
    private double enemySpeed;
    private int score;
    private int shotCounter;
    private double cooldown;
    private boolean left, right, firing, gameOver;

    private static class Alien {
        String id;
        double x, y;
        Alien(String id, double x, double y) {
            this.id = id; this.x = x; this.y = y;
        }
    }

    private static class Shot {
        String id;
        double x, y;
        Shot(String id, double x, double y) {
            this.id = id; this.x = x; this.y = y;
        }
    }

    private void send(String command) {
        out.println(command); // one plain-text command per line, no JSON
    }

    private void move(String id, double x, double y) {
        send("MOVE " + id + " " + Math.round(x) + " " + Math.round(y));
    }

    private void setup() {
        for (Shot shot : shots) send("REMOVE " + shot.id);
        for (Alien alien : aliens) send("REMOVE " + alien.id);
        send("REMOVE player");
        aliens.clear();
        shots.clear();
        shotCounter = 0;
        score = 0;
        playerX = 300;
        enemySpeed = 62;
        cooldown = 0;
        left = right = firing = gameOver = false;
        send("CREATE player ship");
        move("player", playerX, 396);
        send("TEXT score Punkte: 0");
        send("TEXT life Gegner: 21");
        send("HIDE banner");
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 7; col++) {
                String id = "alien_" + row + "_" + col;
                Alien alien = new Alien(id, 57 + col * 72, 110 + row * 49);
                aliens.add(alien);
                send("CREATE " + id + " alien");
                move(id, alien.x, alien.y);
            }
        }
        System.err.println("Space Invaders gestartet: 21 Gegner, Tick-Ereignisse erwartet.");
    }

    private void fire() {
        if (gameOver || cooldown > 0 || shots.size() >= 3) return;
        Shot shot = new Shot("shot_" + shotCounter++, playerX + 21, 386);
        shots.add(shot);
        send("CREATE " + shot.id + " bullet");
        move(shot.id, shot.x, shot.y);
        send("SOUND laser");
        cooldown = 0.23;
    }

    private void keyDown(String key) {
        switch (key) {
            case "ArrowLeft": left = true; break;
            case "ArrowRight": right = true; break;
            case "Space": firing = true; fire(); break;
            case "KeyR": setup(); break;
            default: break;
        }
    }

    private void keyUp(String key) {
        switch (key) {
            case "ArrowLeft": left = false; break;
            case "ArrowRight": right = false; break;
            case "Space": firing = false; break;
            default: break;
        }
    }

    private void tick(int deltaMillis) {
        if (gameOver) return;
        double dt = Math.min(100, Math.max(1, deltaMillis)) / 1000.0;
        cooldown = Math.max(0, cooldown - dt);
        if (left && !right) playerX -= 280 * dt;
        if (right && !left) playerX += 280 * dt;
        playerX = Math.max(12, Math.min(WIDTH - 58, playerX));
        move("player", playerX, 396);
        if (firing) fire();

        boolean reverse = false;
        for (Alien alien : aliens) {
            if (alien.x + enemySpeed * dt < 18 || alien.x + enemySpeed * dt > 583) {
                reverse = true;
                break;
            }
        }
        if (reverse) {
            enemySpeed = -enemySpeed;
            for (Alien alien : aliens) alien.y += 14;
        }
        for (Alien alien : aliens) {
            alien.x += enemySpeed * dt;
            move(alien.id, alien.x, alien.y);
            if (alien.y >= 360) {
                finish(false);
                return;
            }
        }

        Iterator<Shot> shotIterator = shots.iterator();
        while (shotIterator.hasNext()) {
            Shot shot = shotIterator.next();
            shot.y -= 340 * dt;
            if (shot.y < 65) {
                send("REMOVE " + shot.id);
                shotIterator.remove();
                continue;
            }
            move(shot.id, shot.x, shot.y);
            Alien hit = null;
            for (Alien alien : aliens) {
                // Simple axis-aligned collision, calculated exclusively in Java.
                if (shot.x + 5 >= alien.x && shot.x <= alien.x + 40 &&
                        shot.y + 16 >= alien.y && shot.y <= alien.y + 30) {
                    hit = alien;
                    break;
                }
            }
            if (hit != null) {
                aliens.remove(hit);
                send("REMOVE " + hit.id);
                send("REMOVE " + shot.id);
                shotIterator.remove();
                score += 10;
                send("TEXT score Punkte: " + score);
                send("TEXT life Gegner: " + aliens.size());
                send("SOUND hit");
                enemySpeed += enemySpeed >= 0 ? 3 : -3;
            }
        }
        if (aliens.isEmpty()) finish(true);
    }

    private void finish(boolean won) {
        gameOver = true;
        send("TEXT banner " + (won ? "GEWONNEN!" : "GAME OVER") + "  ·  Punkte: " + score + "  ·  R = Neustart");
        send("SHOW banner");
    }

    private void run() throws Exception {
        setup();
        // Blocking readLine() is intentional: no busy waiting, no game thread.
        BufferedReader input = new BufferedReader(
                new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = input.readLine()) != null) {
            if (line.startsWith("KEYDOWN ")) {
                keyDown(line.substring(8));
            } else if (line.startsWith("KEYUP ")) {
                keyUp(line.substring(6));
            } else if (line.startsWith("TICK ")) {
                try {
                    tick(Integer.parseInt(line.substring(5)));
                } catch (NumberFormatException e) {
                    System.err.println("Ungültiger Tick: " + line);
                }
            }
        }
    }

    public static void main(String[] args) throws Exception {
        new SpaceInvaders().run();
    }
}
