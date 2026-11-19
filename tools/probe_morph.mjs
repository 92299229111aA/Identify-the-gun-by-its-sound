// Probe the particle morph: font availability, point sampling, and a forced morph.
const PORT = process.env.CDP_PORT || "9396";

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function main() {
  let target = null;
  for (let i = 0; i < 40 && !target; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      target = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl && t.url.indexOf("game.html") > -1);
    } catch (e) {}
    if (!target) await sleep(250);
  }
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 1;
  const pending = new Map();
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  ws.addEventListener("message", (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  const send = (method, params = {}) => new Promise((res) => {
    const n = id++; pending.set(n, res); ws.send(JSON.stringify({ id: n, method, params }));
  });
  const evaluate = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { error: r.result.exceptionDetails };
    return r.result.result.value;
  };

  await send("Runtime.enable");
  await sleep(500);
  console.log("font check:", await evaluate(`document.fonts.check("600 200px NSerif")`));
  console.log("fx ok:", await evaluate(`FX.ok`));

  await evaluate(`document.getElementById("begin").click()`);
  await sleep(600);

  const probe = await evaluate(`(function () {
    var c = document.createElement("canvas");
    var ctx = c.getContext("2d");
    ctx.font = "600 200px 'NSerif', serif";
    c.width = 400; c.height = 280;
    ctx = c.getContext("2d");
    ctx.font = "600 200px 'NSerif', serif";
    ctx.fillStyle = "#fff";
    ctx.fillText("P90", 20, 180);
    var data = ctx.getImageData(0, 0, 400, 280).data;
    var n = 0;
    for (var i = 3; i < data.length; i += 4) if (data[i] > 128) n++;
    return { inkPixels: n, width: Math.round(ctx.measureText("P90").width) };
  })()`);
  console.log("text sampling:", JSON.stringify(probe));

  await evaluate(`FX.morphTo("P90")`);
  await sleep(1200);
  const shot = await send("Page.captureScreenshot", { format: "png" });
  const fs = await import("node:fs");
  fs.writeFileSync(process.env.SHOT_PATH, Buffer.from(shot.result.data, "base64"));
  console.log("screenshot:", process.env.SHOT_PATH);
  ws.close();
}

main().catch((e) => { console.error("FAILED:", e.message); process.exit(1); });
