// Capture true mobile rendering through CDP device emulation.
const PORT = process.env.CDP_PORT || "9422";
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
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
    return r.result.result.value;
  };

  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: 390, height: 844, deviceScaleFactor: 2, mobile: true,
  });
  await send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: "no-preference" }],
  });
  await send("Page.reload", { ignoreCache: true });
  await sleep(3000);

  const metrics = await ev(`({ vw: innerWidth, vh: innerHeight, scroll: document.body.scrollWidth })`);
  console.log("mobile metrics:", JSON.stringify(metrics));

  let shot = await send("Page.captureScreenshot", { format: "png" });
  const fs = await import("node:fs");
  fs.writeFileSync(process.env.SHOT_START, Buffer.from(shot.result.data, "base64"));

  await ev(`document.getElementById("begin").click()`);
  await sleep(1200);
  shot = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(process.env.SHOT_GAME, Buffer.from(shot.result.data, "base64"));

  await ev(`document.querySelectorAll(".opt")[0].click()`);
  await sleep(900);
  shot = await send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(process.env.SHOT_ANSWER, Buffer.from(shot.result.data, "base64"));
  console.log("saved 3 shots");
  ws.close();
})();
