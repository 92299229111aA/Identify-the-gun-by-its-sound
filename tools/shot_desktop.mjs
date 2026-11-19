// Capture desktop start / question / morph / answered states.
const PORT = process.env.CDP_PORT || "9426";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  let target = null;
  for (let i = 0; i < 40 && !target; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      target = list.find((x) => x.type === "page" && x.url.includes("game.html"));
    } catch (e) {}
    if (!target) await sleep(250);
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  let id = 1;
  await new Promise((res) => ws.addEventListener("open", res));
  ws.addEventListener("message", (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  const send = (method, params = {}) => new Promise((res) => {
    const n = id++;
    pending.set(n, res);
    ws.send(JSON.stringify({ id: n, method, params }));
  });
  const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true })).result.result.value;
  const fs = await import("node:fs");
  const shoot = async (path) => {
    const s = await send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path, Buffer.from(s.result.data, "base64"));
  };

  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "no-preference" }] });
  await send("Page.reload", { ignoreCache: true });
  await sleep(3200);
  await shoot(process.env.SHOT_START);

  await ev(`document.getElementById("begin").click()`);
  await sleep(1300);
  await shoot(process.env.SHOT_GAME);

  const ok = await ev(`(function(){
    var correct = state.question.gun.id;
    var btn = Array.from(document.querySelectorAll(".opt")).find(function(b){ return b.dataset.id === correct; });
    btn.click();
    return state.question.gun.nick;
  })()`);
  console.log("answered:", ok);
  await sleep(800);
  await shoot(process.env.SHOT_MORPH);
  await sleep(1600);
  await shoot(process.env.SHOT_ANSWER);
  console.log("shots saved");
  ws.close();
})();
