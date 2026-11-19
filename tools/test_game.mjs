// Drive the built game page through CDP to verify it actually works.

const PORT = process.env.CDP_PORT || "9333";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function targets() {
  for (let i = 0; i < 40; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      const list = await res.json();
      const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl && t.url.indexOf("game.html") > -1);
      if (page) return page;
    } catch (e) {
      // not up yet
    }
    await sleep(250);
  }
  throw new Error("no CDP page target");
}

async function main() {
  const target = await targets();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let nextId = 1;
  const pending = new Map();

  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve);
    ws.addEventListener("error", reject);
  });

  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  });

  function send(method, params = {}) {
    const id = nextId++;
    return new Promise((resolve) => {
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async function evaluate(expression) {
    const res = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (res.result && res.result.exceptionDetails) {
      throw new Error(JSON.stringify(res.result.exceptionDetails));
    }
    return res.result && res.result.result ? res.result.result.value : undefined;
  }

  await send("Page.enable");
  await send("Runtime.enable");
  await sleep(600);

  const boot = await evaluate(`({
    title: document.title,
    overlay: !!document.getElementById("start"),
    options: document.querySelectorAll(".opt").length,
    hasState: typeof state !== "undefined"
  })`);
  console.log("boot:", JSON.stringify(boot));

  await evaluate(`document.getElementById("begin").click()`);
  await sleep(900);

  const afterStart = await evaluate(`({
    qnum: document.getElementById("qnum").textContent,
    variant: document.getElementById("variant").textContent,
    options: Array.from(document.querySelectorAll(".opt .nm")).map(function (n) { return n.textContent; }),
    gun: state.question.gun.name,
    clip: state.question.clip.file,
    audioSrc: audio.src.split("/").slice(-3).join("/"),
    audioError: audio.error ? audio.error.code : null,
    answered: state.answered
  })`);
  console.log("afterStart:", JSON.stringify(afterStart));

  // Answer correctly.
  await evaluate("window.__WRONG = " + (process.env.WRONG === "1" ? "true" : "false"));
  const answered = await evaluate(`(function () {
    var correct = state.question.gun.id;
    var buttons = Array.from(document.querySelectorAll(".opt"));
    var wrong = window.__WRONG === true;
    var target = buttons.find(function (b) {
      var id = b.dataset.id;
      return wrong ? id !== correct : id === correct;
    });
    target.click();
    return {
      feedback: document.getElementById("verdict").textContent,
      correctMarks: document.querySelectorAll(".opt.correct").length,
      wrongMarks: document.querySelectorAll(".opt.wrong").length,
      profiles: document.querySelectorAll(".prof").length,
      streak: state.streak,
      total: state.total,
      resultShown: document.getElementById("result").classList.contains("show")
    };
  })()`);
  console.log("answered:", JSON.stringify(answered));

  await sleep(400);
  const shotAnswered = await send("Page.captureScreenshot", { format: "png" });
  if (shotAnswered.result && shotAnswered.result.data) {
    const fsA = await import("node:fs");
    fsA.writeFileSync(process.env.SHOT_ANSWERED, Buffer.from(shotAnswered.result.data, "base64"));
    console.log("answered screenshot:", process.env.SHOT_ANSWERED);
  }
  const nextQ = await evaluate(`(function () {
    document.getElementById("next").click();
    return {
      qnum: document.getElementById("qnum").textContent,
      answered: state.answered,
      options: document.querySelectorAll(".opt").length
    };
  })()`);
  console.log("next:", JSON.stringify(nextQ));

  await sleep(600);
  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (shot.result && shot.result.data) {
    const fs = await import("node:fs");
    fs.writeFileSync(process.env.SHOT_PATH, Buffer.from(shot.result.data, "base64"));
    console.log("screenshot:", process.env.SHOT_PATH);
  }

  ws.close();
}

main().catch((err) => {
  console.error("FAILED:", err.message);
  process.exit(1);
});
