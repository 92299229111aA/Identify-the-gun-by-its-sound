// Emulate no-preference reduced-motion, reload, then exercise the morph.
const PORT = process.env.CDP_PORT || "9402";
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
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result.exceptionDetails) return { error: JSON.stringify(r.result.exceptionDetails) };
    return r.result.result.value;
  };

  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setEmulatedMedia", {
    features: [{ name: "prefers-reduced-motion", value: "no-preference" }],
  });
  await send("Page.reload", { ignoreCache: true });
  await sleep(2500);

  console.log("reduced:", await ev(`matchMedia("(prefers-reduced-motion: reduce)").matches`));
  console.log("fx:", JSON.stringify(await ev(`FX.debug()`)));

  await ev(`document.getElementById("begin").click()`);
  await sleep(700);
  await ev(`FX.morphTo("P90")`);
  await sleep(1400);
  console.log("morph:", JSON.stringify(await ev(`FX.debug()`)));

  const shot = await send("Page.captureScreenshot", { format: "png" });
  const fs = await import("node:fs");
  fs.writeFileSync(process.env.SHOT_PATH, Buffer.from(shot.result.data, "base64"));
  console.log("shot:", process.env.SHOT_PATH);
  ws.close();
})();
