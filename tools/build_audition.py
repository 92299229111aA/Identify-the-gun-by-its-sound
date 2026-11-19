"""Build the audition page (audition.html) as fully static markup.

Cards are emitted by Python rather than generated in the browser, so the page
still lists every gun and keeps a native <audio> player per clip when scripts
are blocked (embedded viewers, sandboxed iframes, file:// restrictions).
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")
OUT = os.path.join(PROJECT, "audition.html")

guns = json.load(open(MANIFEST, encoding="utf-8"))
clips_total = sum(len(g["clips"]) for g in guns)

CSS = """
  :root {
    --bg: #0a0c0b; --panel: #111413; --panel-2: #161a18;
    --line: rgba(255,255,255,.09); --text: #e8ece9; --muted: #8b948f;
    --olive: #9aa86a; --sand: #d9c9a3;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: radial-gradient(1200px 600px at 50% -10%, #1a211d 0%, var(--bg) 60%);
    color: var(--text);
    font-family: -apple-system, "SF Pro Text", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  header {
    position: sticky; top: 0; z-index: 10; backdrop-filter: blur(18px);
    background: rgba(10,12,11,.78); border-bottom: 1px solid var(--line);
  }
  .bar { max-width: 1080px; margin: 0 auto; padding: 16px 24px; display: flex; align-items: center; gap: 18px; }
  .brand { font-size: 13px; letter-spacing: .18em; text-transform: uppercase; color: var(--olive); }
  .brand b { color: var(--text); font-weight: 600; letter-spacing: .02em; }
  .spacer { flex: 1; }
  .count { font-variant-numeric: tabular-nums; color: var(--muted); font-size: 13px; }
  .count b { color: var(--sand); font-size: 15px; }
  button {
    font: inherit; color: var(--text); cursor: pointer;
    background: rgba(255,255,255,.06); border: 1px solid var(--line);
    border-radius: 999px; padding: 8px 16px; transition: .18s ease;
  }
  button:hover { background: rgba(255,255,255,.11); }
  button.primary { background: var(--sand); color: #14130f; border-color: transparent; font-weight: 600; }
  button.primary:hover { filter: brightness(1.06); }
  main { max-width: 1080px; margin: 0 auto; padding: 44px 24px 120px; }
  h1 { font-size: 44px; line-height: 1.08; letter-spacing: -.02em; margin: 0 0 10px; font-weight: 600; }
  .lede { color: var(--muted); font-size: 15px; line-height: 1.6; margin: 0 0 16px; max-width: 620px; }
  .warn {
    display: none; border: 1px solid rgba(217,201,163,.35); background: rgba(217,201,163,.07);
    color: var(--sand); border-radius: 12px; padding: 12px 16px; font-size: 13px; line-height: 1.6;
    margin: 0 0 32px; max-width: 660px;
  }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
  .card {
    background: linear-gradient(180deg, var(--panel-2), var(--panel));
    border: 1px solid var(--line); border-radius: 16px; padding: 18px 18px 14px;
    transition: .2s ease;
  }
  .card:hover { border-color: rgba(255,255,255,.18); }
  .card.keep { border-color: rgba(154,168,106,.55); box-shadow: 0 0 0 1px rgba(154,168,106,.18) inset; }
  .head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 4px; }
  .name { font-size: 20px; font-weight: 600; letter-spacing: -.01em; }
  .cal { font-size: 11px; color: var(--sand); border: 1px solid rgba(217,201,163,.28); border-radius: 6px; padding: 2px 7px; letter-spacing: .04em; }
  .meta { color: var(--muted); font-size: 12px; margin-bottom: 12px; font-variant-numeric: tabular-nums; }
  .samples { display: flex; flex-direction: column; gap: 6px; }
  .row { display: flex; align-items: center; gap: 8px; }
  .play {
    flex: 1; text-align: left; display: flex; align-items: center; gap: 10px;
    border-radius: 10px; padding: 7px 10px; font-size: 12px; color: var(--muted);
  }
  .play .tag { color: var(--text); font-variant-numeric: tabular-nums; }
  .play .dot { width: 20px; height: 20px; border-radius: 50%; border: 1px solid var(--line); display: grid; place-items: center; flex: none; }
  .play .dot::before { content: ""; border-left: 6px solid var(--olive); border-top: 4px solid transparent; border-bottom: 4px solid transparent; margin-left: 2px; }
  .play.playing { background: rgba(154,168,106,.14); color: var(--sand); }
  .samples audio { display: block; width: 100%; height: 30px; margin-top: 2px; }
  html.js .samples audio { display: none; }
  .keepbox { display: flex; align-items: center; gap: 7px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; cursor: pointer; user-select: none; }
  .keepbox input { accent-color: var(--olive); width: 15px; height: 15px; }
  .hint { color: var(--muted); font-size: 12px; line-height: 1.7; margin-top: 28px; }
  #toast {
    position: fixed; left: 50%; bottom: 32px; transform: translate(-50%, 20px);
    background: var(--sand); color: #14130f; padding: 10px 18px; border-radius: 999px;
    font-size: 13px; font-weight: 600; opacity: 0; pointer-events: none; transition: .25s ease; z-index: 50;
  }
  #toast.show { opacity: 1; transform: translate(-50%, 0); }
"""

JS = """
(function () {
  document.documentElement.classList.add("js");
  var store = {
    read: function () {
      try { return JSON.parse(window.localStorage.getItem("grillPicked") || "[]"); }
      catch (e) { return []; }
    },
    write: function (list) {
      try { window.localStorage.setItem("grillPicked", JSON.stringify(list)); } catch (e) {}
    }
  };
  var picked = new Set(store.read());
  var counter = document.getElementById("picked");

  function refreshCounter() {
    if (counter) counter.textContent = picked.size;
    document.querySelectorAll(".card").forEach(function (card) {
      var id = card.getAttribute("data-id");
      card.classList.toggle("keep", picked.has(id));
      var box = card.querySelector(".keepbox input");
      if (box) box.checked = picked.has(id);
    });
  }

  document.querySelectorAll(".card").forEach(function (card) {
    var audio = null;
    card.querySelectorAll(".play").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-audio");
        var el = document.getElementById(id);
        if (!el) return;
        if (audio && audio !== el) { audio.pause(); audio.currentTime = 0; }
        audio = el;
        el.currentTime = 0;
        var playing = el.play();
        if (playing && playing.catch) playing.catch(function () {});
        card.querySelectorAll(".play").forEach(function (other) { other.classList.remove("playing"); });
        btn.classList.add("playing");
        el.onended = function () { btn.classList.remove("playing"); };
      });
    });
    var box = card.querySelector(".keepbox input");
    if (box) {
      box.addEventListener("change", function () {
        var id = card.getAttribute("data-id");
        if (box.checked) picked.add(id); else picked.delete(id);
        store.write(Array.from(picked));
        refreshCounter();
      });
    }
  });

  var copyBtn = document.getElementById("copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var names = [];
      document.querySelectorAll(".card").forEach(function (card) {
        if (picked.has(card.getAttribute("data-id"))) {
          var name = card.querySelector(".name");
          if (name) names.push(name.textContent);
        }
      });
      var text = names.length ? names.join(", ") : "（还没选）";
      var done = function () {
        var toast = document.getElementById("toast");
        if (!toast) return;
        toast.textContent = "已复制：" + names.length + " 把";
        toast.classList.add("show");
        setTimeout(function () { toast.classList.remove("show"); }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { window.prompt("复制这行枪名：", text); });
      } else {
        window.prompt("复制这行枪名：", text);
      }
    });
  }

  refreshCounter();
  // Prove the script ran: hide the no-JS notice.
  document.querySelectorAll(".warn").forEach(function (el) { el.style.display = "none"; });
})();
"""


def card_html(gun: dict) -> str:
    gid = html.escape(gun["id"])
    rows = []
    for index, clip in enumerate(gun["clips"]):
        audio_id = f"{gid}-{index}"
        rows.append(
            f"""      <div class="row">
        <button class="play" data-audio="{audio_id}">
          <span class="dot"></span>
          <span class="tag">{index + 1:02d}</span>
          <span>{clip["duration"]:.2f}s</span>
        </button>
        <audio id="{audio_id}" preload="none" controls src="{html.escape(clip["file"])}"></audio>
      </div>"""
        )
    return f"""  <div class="card" data-id="{gid}">
    <div class="head"><span class="name">{html.escape(gun["name"])}</span><span class="cal">{html.escape(gun["caliber"])}</span></div>
    <div class="meta">{len(gun["clips"])} 个采样 · {gid}</div>
    <div class="samples">
{os.linesep.join(rows)}
    </div>
    <label class="keepbox"><input type="checkbox" data-id="{gid}"> 保留这把</label>
  </div>"""


def main() -> None:
    cards = os.linesep.join(card_html(gun) for gun in guns)
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>枪声试听 · 候选枪池</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="bar">
    <div class="brand"><b>声纹识别</b> · 候选枪池</div>
    <div class="spacer"></div>
    <div class="count">已保留 <b id="picked">0</b> / {len(guns)} 把 · 建议 12–16</div>
    <button id="copy" class="primary">生成保留清单</button>
  </div>
</header>
<main>
  <h1>先听一遍，再决定<br>题库放哪几把枪。</h1>
  <p class="lede">每张卡是一把枪，下面是它在游戏里的原始开火采样（室外近距离，未消音）。同枪多条可以对比音色浮动。听完勾选你觉得「能听出来、也值得考」的枪。</p>
  <p class="warn">当前环境没有执行页面脚本：勾选状态不会自动记录，卡片里的播放器会直接显示出来供你试听。选好后把这些枪名告诉我就行。</p>
  <div class="grid">
{cards}
  </div>
  <p class="hint">数据来自本机游戏资源，只读提取并转码为 OGG（共 {len(guns)} 把 / {clips_total} 条）；此页仅用于挑选，不是最终游戏。</p>
</main>
<div id="toast"></div>
<script>{JS}</script>
<noscript><style>.warn {{ display: block; }}</style></noscript>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(page)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.1f} KB), guns={len(guns)}, clips={clips_total}")


if __name__ == "__main__":
    main()
