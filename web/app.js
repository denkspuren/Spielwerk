/* Pure presentation layer. No game logic is implemented here. */
(() => {
  "use strict";
  const field = document.getElementById("field");
  const status = document.getElementById("status");
  const errorPanel = document.getElementById("error-panel");
  const errorText = document.getElementById("error-text");
  const logOutput = document.getElementById("log-output");
  const instructions = document.getElementById("instructions");
  let chain = Promise.resolve();
  let source;
  const down = new Set();
  let shuttingDown = false;

  function enqueue(fn) {
    chain = chain.then(fn).catch((err) => appendLog("Browserfehler: " + err.message));
  }

  function appendLog(message) {
    const lines = (logOutput.textContent + message + "\n").split("\n");
    logOutput.textContent = lines.slice(-70).join("\n");
  }

  function statusUpdate(raw) {
    const [code, ...rest] = raw.split("\t");
    const text = rest.join("\t") || code;
    status.textContent = text;
    status.className = "status" + (code === "RUNNING" ? " running" :
      code === "COMPILE_ERROR" || code === "STOPPED" ? " problem" : "");
  }

  async function resetScene() {
    const response = await fetch("/game/scene.html", {cache:"no-store"});
    if (!response.ok) throw new Error("scene.html fehlt (HTTP " + response.status + ")");
    field.innerHTML = await response.text();
    instructions.textContent = field.querySelector("[data-instructions]")?.dataset.instructions || "Pfeiltasten / Leertaste";
    field.focus({preventScroll:true});
  }

  function getElement(id) {
    return document.getElementById(id);
  }

  function applyCommand(line) {
    const op = line.split(" ", 1)[0];
    const rest = line.substring(op.length + 1);
    if (op === "CREATE") {
      const [id, templateId] = rest.split(" ");
      const template = getElement(templateId);
      if (!(template instanceof HTMLTemplateElement)) {
        appendLog("Unbekanntes Template: " + templateId);
        return;
      }
      const element = template.content.firstElementChild?.cloneNode(true);
      if (!element) return;
      getElement(id)?.remove();
      element.id = id;
      element.classList.add("game-object");
      field.appendChild(element);
      return;
    }
    if (op === "SOUND") {
      const audio = getElement(rest);
      if (audio instanceof HTMLAudioElement) {
        audio.currentTime = 0;
        audio.play().catch(() => {}); // Browser may block sound until first user gesture.
      }
      return;
    }
    const [id, ...params] = rest.split(" ");
    const element = getElement(id);
    if (!element || !field.contains(element)) return;
    switch (op) {
      case "MOVE": {
        const [x, y] = params;
        element.style.transform = `translate3d(${Number(x)}px, ${Number(y)}px, 0)`;
        break;
      }
      case "SHOW": element.hidden = false; break;
      case "HIDE": element.hidden = true; break;
      case "REMOVE": element.remove(); break;
      case "TEXT": element.textContent = rest.substring(id.length + 1); break;
      default: appendLog("Unbekannter Befehl: " + line);
    }
  }

  async function send(line) {
    if (shuttingDown) return;
    try {
      const response = await fetch("/input", {
        method:"POST", headers:{"Content-Type":"text/plain; charset=utf-8"}, body:line
      });
      if (!response.ok) appendLog("Ereignis abgewiesen: " + line);
    } catch (err) { appendLog("Verbindungsfehler: " + err.message); }
  }

  function keyAllowed(code) {
    return /^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(code);
  }

  window.addEventListener("keydown", (event) => {
    if (!keyAllowed(event.code)) return;
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Space"].includes(event.code)) {
      event.preventDefault();
    }
    if (!down.has(event.code)) {
      down.add(event.code);
      send("KEYDOWN " + event.code);
    }
  });
  window.addEventListener("keyup", (event) => {
    if (!keyAllowed(event.code)) return;
    down.delete(event.code);
    send("KEYUP " + event.code);
  });
  window.addEventListener("blur", () => {
    for (const key of down) send("KEYUP " + key);
    down.clear();
  });
  field.addEventListener("click", (event) => {
    const nearest = event.target.closest("[id]");
    const id = nearest && nearest !== field && field.contains(nearest) ? nearest.id : "NONE";
    if (!/^[A-Za-z][A-Za-z0-9_-]{0,63}$/.test(id)) return;
    const box = field.getBoundingClientRect();
    const x = Math.round(event.clientX - box.left);
    const y = Math.round(event.clientY - box.top);
    send(`CLICK ${id} ${x} ${y}`);
    field.focus({preventScroll:true});
  });
  document.getElementById("restart").addEventListener("click", async () => {
    try { await fetch("/restart", {method:"POST", body:""}); }
    catch (e) { appendLog("Neustart fehlgeschlagen: " + e.message); }
  });
  document.getElementById("shutdown").addEventListener("click", async () => {
    if (shuttingDown || !confirm("Den lokalen Server und das Java-Spiel wirklich beenden?")) return;
    const button = document.getElementById("shutdown");
    button.disabled = true;
    try {
      const response = await fetch("/shutdown", {
        method: "POST",
        headers: {"Content-Type":"text/plain; charset=utf-8", "X-Arcade-Action":"shutdown"},
        body: ""
      });
      if (!response.ok) throw new Error("HTTP " + response.status);
      shuttingDown = true;
      source?.close();
      status.className = "status";
      status.textContent = "Server beendet";
      document.getElementById("restart").disabled = true;
      down.clear();
      appendLog("Server heruntergefahren. Zum Spielen den Server erneut starten.");
    } catch (err) {
      button.disabled = false;
      appendLog("Herunterfahren fehlgeschlagen: " + err.message);
    }
  });
  document.getElementById("toggle-log").addEventListener("click", (event) => {
    const logPanel = document.getElementById("log-panel");
    logPanel.hidden = !logPanel.hidden;
    event.currentTarget.setAttribute("aria-expanded", String(!logPanel.hidden));
    event.currentTarget.textContent = logPanel.hidden ? "Diagnoseprotokoll anzeigen" : "Diagnoseprotokoll ausblenden";
  });

  async function start() {
    await resetScene();
    source = new EventSource("/events");
    source.addEventListener("reset", () => enqueue(resetScene));
    source.addEventListener("cmd", (event) => enqueue(() => applyCommand(event.data)));
    source.addEventListener("status", (event) => statusUpdate(event.data));
    source.addEventListener("compile", (event) => {
      errorText.textContent = event.data;
      errorPanel.hidden = !event.data;
    });
    source.addEventListener("log", (event) => appendLog(event.data));
    source.onerror = () => {
      if (shuttingDown) return;
      status.className = "status problem";
      status.textContent = "Serververbindung unterbrochen – verbinde erneut …";
    };
  }
  start().catch((err) => {
    errorText.textContent = "Browser konnte die Szene nicht laden: " + err.message;
    errorPanel.hidden = false;
  });
})();
