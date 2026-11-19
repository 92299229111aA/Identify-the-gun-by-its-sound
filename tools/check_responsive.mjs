// Check horizontal overflow and key element sizes across viewport widths.
const PORT = process.env.CDP_PORT || "9347";
const WIDTHS = [320, 360, 390, 414, 480, 600, 768, 900, 1024, 1280, 1440, 1920];
const HEIGHTS = [640, 740, 844, 896, 900, 1080];

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
  if (!target) throw new Error("no page");

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
    if (r.result && r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
    return r.result.result.value;
  };

  await send("Runtime.enable");
  await sleep(400);
  await evaluate(`document.getElementById("begin").click()`);
  await sleep(400);

  const rows = [];
  for (const w of WIDTHS) {
    for (const h of HEIGHTS) {
      await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: w < 720 });
      await sleep(160);
      const r = await evaluate(`(function () {
        var doc = document.documentElement;
        var opt = document.querySelector(".opt");
        var h1 = document.querySelector("h1");
        return {
          overflowX: doc.scrollWidth - doc.clientWidth,
          optW: opt ? Math.round(opt.getBoundingClientRect().width) : 0,
          h1px: h1 ? Math.round(parseFloat(getComputedStyle(h1).fontSize)) : 0,
          cols: getComputedStyle(document.querySelector(".options")).gridTemplateColumns.split(" ").length
        };
      })()`);
      rows.push({ w, h, ...r });
    }
  }
  const bad = rows.filter((r) => r.overflowX > 1);
  console.log("checked:", rows.length, "overflow cases:", bad.length);
  if (bad.length) console.log(bad.slice(0, 12));
  const sample = [320, 390, 768, 1440];
  for (const w of sample) {
    const row = rows.find((r) => r.w === w);
    console.log(`w=${w}: optW=${row.optW} h1=${row.h1px}px cols=${row.cols} overflow=${row.overflowX}`);
  }
  ws.close();
}

main().catch((e) => { console.error("FAILED:", e.message); process.exit(1); });
