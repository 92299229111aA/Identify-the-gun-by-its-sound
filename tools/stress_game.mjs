// Stress-run the game: answer 40 questions randomly and surface page errors.
const PORT = process.env.CDP_PORT || "9338";

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function target() {
  for (let i = 0; i < 40; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await res.json();
      const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl && t.url.indexOf("game.html") > -1);
      if (page) return page;
    } catch (e) {}
    await sleep(250);
  }
  throw new Error("no page target");
}

async function main() {
  const page = await target();
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 1;
  const pending = new Map();
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  });
  function send(method, params = {}) {
    const n = id++;
    return new Promise((res) => { pending.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
  }
  async function evaluate(expression) {
    const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
    return r.result && r.result.result ? r.result.result.value : undefined;
  }

  await send("Runtime.enable");
  await sleep(500);
  await evaluate(`window.__errors = []; window.onerror = function (m) { window.__errors.push(String(m)); };`);
  await evaluate(`document.getElementById("begin").click()`);
  await sleep(500);

  const result = await evaluate(`(function () {
    var picks = 0, answered = 0, variants = {};
    for (var round = 0; round < 40; round++) {
      if (!state.answered) {
        var opts = document.querySelectorAll(".opt");
        if (opts.length !== 4) return { error: "options=" + opts.length, round: round };
        variants[state.question.group.key] = (variants[state.question.group.key] || 0) + 1;
        opts[Math.floor(Math.random() * 4)].click();
        picks++;
        answered++;
        if (!state.answered) return { error: "click did not register", round: round };
        if (!state.question.clip.file) return { error: "missing clip", round: round };
      }
      document.getElementById("next").click();
      if (state.answered) return { error: "next did not reset", round: round };
    }
    return {
      picks: picks,
      total: state.total,
      correct: state.correct,
      best: state.best,
      variants: variants,
      errors: window.__errors,
      audioError: audio.error ? audio.error.code : null,
      srcTail: audio.src.split("/").slice(-2).join("/")
    };
  })()`);

  console.log(JSON.stringify(result, null, 1));
  ws.close();
}

main().catch((e) => { console.error("FAILED:", e.message); process.exit(1); });
