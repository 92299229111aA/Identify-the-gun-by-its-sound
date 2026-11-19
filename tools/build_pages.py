"""Build the audition pages (folder + single-file) for the grouped variants.

Emits fully static markup, so the list renders even when scripts are blocked.
  audition.html           references sounds/ by relative path
  audition-embedded.html  inlines every clip as a data URI (sandbox-proof)
"""
import base64
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")

guns = json.load(open(MANIFEST, encoding="utf-8"))
clip_total = sum(len(g["clips"]) for gun in guns for g in gun["groups"])

CSS = """
  :root { --bg:#0a0c0b; --panel:#111413; --panel-2:#161a18; --line:rgba(255,255,255,.09);
          --text:#e8ece9; --muted:#8b948f; --olive:#9aa86a; --sand:#d9c9a3; }
  * { box-sizing: border-box; }
  body { margin:0; background:radial-gradient(1200px 600px at 50% -10%, #1a211d 0%, var(--bg) 60%);
         color:var(--text); font-family:-apple-system,"SF Pro Text","Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
         -webkit-font-smoothing:antialiased; }
  header { position:sticky; top:0; z-index:10; backdrop-filter:blur(18px);
           background:rgba(10,12,11,.78); border-bottom:1px solid var(--line); }
  .bar { max-width:1080px; margin:0 auto; padding:16px 24px; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .brand { font-size:13px; letter-spacing:.18em; text-transform:uppercase; color:var(--olive); }
  .brand b { color:var(--text); font-weight:600; letter-spacing:.02em; }
  .spacer { flex:1; }
  .count { font-variant-numeric:tabular-nums; color:var(--muted); font-size:13px; }
  .count b { color:var(--sand); font-size:15px; }
  button { font:inherit; color:var(--text); cursor:pointer; background:rgba(255,255,255,.06);
           border:1px solid var(--line); border-radius:999px; padding:8px 16px; transition:.18s ease; }
  button:hover { background:rgba(255,255,255,.11); }
  button.primary { background:var(--sand); color:#14130f; border-color:transparent; font-weight:600; }
  button.primary:hover { filter:brightness(1.06); }
  main { max-width:1080px; margin:0 auto; padding:44px 24px 120px; }
  h1 { font-size:42px; line-height:1.08; letter-spacing:-.02em; margin:0 0 10px; font-weight:600; }
  .lede { color:var(--muted); font-size:15px; line-height:1.6; margin:0 0 16px; max-width:640px; }
  .warn { display:none; border:1px solid rgba(194,91,78,.5); background:rgba(194,91,78,.09);
          color:#e6a89f; border-radius:12px; padding:12px 16px; font-size:13px; line-height:1.6;
          margin:0 0 24px; max-width:760px; white-space:pre-wrap; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(340px,1fr)); gap:16px; }
  .card { background:linear-gradient(180deg,var(--panel-2),var(--panel)); border:1px solid var(--line);
          border-radius:16px; padding:18px 18px 14px; transition:.2s ease; }
  .card:hover { border-color:rgba(255,255,255,.18); }
  .card.keep { border-color:rgba(154,168,106,.55); box-shadow:0 0 0 1px rgba(154,168,106,.18) inset; }
  .head { display:flex; align-items:baseline; gap:10px; margin-bottom:4px; }
  .name { font-size:20px; font-weight:600; letter-spacing:-.01em; }
  .cal { font-size:11px; color:var(--sand); border:1px solid rgba(217,201,163,.28); border-radius:6px; padding:2px 7px; letter-spacing:.04em; }
  .meta { color:var(--muted); font-size:12px; margin-bottom:10px; font-variant-numeric:tabular-nums; }
  .group { margin-top:10px; }
  .glabel { font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--olive); margin-bottom:6px; }
  .samples { display:flex; flex-direction:column; gap:6px; }
  .row { display:flex; align-items:center; gap:8px; }
  .play { flex:1; text-align:left; display:flex; align-items:center; gap:10px; border-radius:10px;
          padding:7px 10px; font-size:12px; color:var(--muted); }
  .play .tag { color:var(--text); font-variant-numeric:tabular-nums; }
  .play .dot { width:20px; height:20px; border-radius:50%; border:1px solid var(--line); display:grid; place-items:center; flex:none; }
  .play .dot::before { content:""; border-left:6px solid var(--olive); border-top:4px solid transparent; border-bottom:4px solid transparent; margin-left:2px; }
  .play.playing { background:rgba(154,168,106,.14); color:var(--sand); }
  .samples audio { display:block; width:100%; height:30px; margin-top:2px; }
  html.js .samples audio { display:none; }
  .keepbox { display:flex; align-items:center; gap:7px; margin-top:12px; padding-top:12px;
             border-top:1px solid var(--line); color:var(--muted); font-size:12px; cursor:pointer; user-select:none; }
  .keepbox input { accent-color:var(--olive); width:15px; height:15px; }
  .hint { color:var(--muted); font-size:12px; line-height:1.7; margin-top:28px; }
  #toast { position:fixed; left:50%; bottom:32px; transform:translate(-50%,20px); background:var(--sand);
           color:#14130f; padding:10px 18px; border-radius:999px; font-size:13px; font-weight:600;
           opacity:0; pointer-events:none; transition:.25s ease; z-index:50; }
  #toast.show { opacity:1; transform:translate(-50%,0); }
"""

JS = """
(function () {
  document.documentElement.classList.add("js");
  var banner = document.getElementById("warn");
  var failures = [];
  function report(msg) {
    failures.push(msg);
    if (banner) {
      banner.style.display = "block";
      banner.textContent = "有音频没能播放：\\n" + failures.slice(0, 6).join("\\n");
    }
  }
  var store = {
    read: function () { try { return JSON.parse(localStorage.getItem("grillPicked") || "[]"); } catch (e) { return []; } },
    write: function (list) { try { localStorage.setItem("grillPicked", JSON.stringify(list)); } catch (e) {} }
  };
  var picked = new Set(store.read());

  function refresh() {
    var counter = document.getElementById("picked");
    if (counter) counter.textContent = picked.size;
    document.querySelectorAll(".card").forEach(function (card) {
      var id = card.getAttribute("data-id");
      card.classList.toggle("keep", picked.has(id));
      var box = card.querySelector(".keepbox input");
      if (box) box.checked = picked.has(id);
    });
  }

  document.querySelectorAll(".card").forEach(function (card) {
    var current = null;
    card.querySelectorAll(".play").forEach(function (btn) {
      var el = document.getElementById(btn.getAttribute("data-audio"));
      if (el) {
        el.addEventListener("error", function () {
          report("无法解码：" + card.getAttribute("data-id") + " / " + btn.querySelector(".tag").textContent);
        });
      }
      btn.addEventListener("click", function () {
        if (!el) { report("找不到元素：" + btn.getAttribute("data-audio")); return; }
        if (current && current !== el) { current.pause(); }
        current = el;
        el.currentTime = 0;
        var p = el.play();
        if (p && p.catch) p.catch(function (err) { report("播放被拒绝：" + (err && err.name ? err.name : "unknown")); });
        card.querySelectorAll(".play").forEach(function (o) { o.classList.remove("playing"); });
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
        refresh();
      });
    }
  });

  var copyBtn = document.getElementById("copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var names = [];
      document.querySelectorAll(".card").forEach(function (card) {
        if (picked.has(card.getAttribute("data-id"))) names.push(card.querySelector(".name").textContent);
      });
      var text = names.length ? names.join(", ") : "（还没选）";
      var done = function () {
        var toast = document.getElementById("toast");
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

  var testBtn = document.getElementById("test-tone");
  if (testBtn) {
    testBtn.addEventListener("click", function () {
      try {
        var Ctx = window.AudioContext || window.webkitAudioContext;
        var ctx = new Ctx();
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = 660;
        gain.gain.value = 0.08;
        osc.connect(gain).connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.45);
        if (ctx.resume) ctx.resume();
      } catch (e) {
        report("测试音失败：" + (e && e.message ? e.message : e));
      }
    });
  }

  refresh();
  var nojs = document.querySelector(".warn-nojs");
  if (nojs) nojs.style.display = "none";
})();
"""


def group_html(gun_id: str, group: dict, embed: bool) -> str:
    rows = []
    for index, clip in enumerate(group["clips"]):
        audio_id = f"{gun_id}-{group['key']}-{index}"
        if embed:
            path = os.path.join(PROJECT, clip["file"].replace("/", os.sep))
            with open(path, "rb") as handle:
                src = "data:audio/ogg;base64," + base64.b64encode(handle.read()).decode("ascii")
        else:
            src = html.escape(clip["file"])
        rows.append(
            f"""        <div class="row">
          <button class="play" data-audio="{audio_id}">
            <span class="dot"></span>
            <span class="tag">{index + 1:02d}</span>
            <span>{clip["duration"]:.2f}s</span>
          </button>
          <audio id="{audio_id}" preload="{'auto' if embed else 'metadata'}" controls src="{src}"></audio>
        </div>"""
        )
    return f"""    <div class="group">
      <div class="glabel">{html.escape(group["label"])}</div>
      <div class="samples">
{os.linesep.join(rows)}
      </div>
    </div>"""


def card_html(gun: dict, embed: bool) -> str:
    gid = html.escape(gun["id"])
    groups = os.linesep.join(group_html(gid, group, embed) for group in gun["groups"])
    count = sum(len(group["clips"]) for group in gun["groups"])
    return f"""  <div class="card" data-id="{gid}">
    <div class="head"><span class="name">{html.escape(gun["name"])}</span><span class="cal">{html.escape(gun["caliber"])}</span></div>
    <div class="meta">{count} 条 · 标准 / 消音 / 连发 · {gid}</div>
{groups}
    <label class="keepbox"><input type="checkbox" data-id="{gid}"> 保留这把</label>
  </div>"""


def build(embed: bool, out_name: str) -> None:
    cards = os.linesep.join(card_html(gun, embed) for gun in guns)
    title = "单文件版" if embed else "候选枪池"
    lede = (
        "所有采样已内嵌在这个文件里，不依赖任何外部路径：放到哪、怎么打开都能播。先点右上角「测试音」确认能出声，再逐条听。"
        if embed
        else "每把枪分三组：标准（室外近距未消音）、消音、连发（按真实射速拼接官方尾音）。听完勾选你觉得「能听出来、也值得考」的枪。"
    )
    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>枪声试听 · {title}</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="bar">
    <div class="brand"><b>声纹识别</b> · {title}</div>
    <div class="spacer"></div>
    <button id="test-tone">测试音</button>
    <div class="count">已保留 <b id="picked">0</b> / {len(guns)} 把 · 建议 12–16</div>
    <button id="copy" class="primary">生成保留清单</button>
  </div>
</header>
<main>
  <h1>先听一遍，再决定<br>题库放哪几把枪。</h1>
  <p class="lede">{lede}</p>
  <p class="warn" id="warn"></p>
  <p class="warn warn-nojs" style="display:block">脚本没跑起来：每行下方会露出浏览器自带播放器，直接用那个播；勾选请直接把枪名告诉我。</p>
  <div class="grid">
{cards}
  </div>
  <p class="hint">音频来自本机游戏资源，只读提取；共 {len(guns)} 把 / {clip_total} 条。此页仅用于挑选，不是最终游戏。</p>
</main>
<div id="toast"></div>
<script>{JS}</script>
</body>
</html>
"""
    out_path = os.path.join(PROJECT, out_name)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(page)
    print(f"wrote {out_name} ({os.path.getsize(out_path) / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    build(False, "audition.html")
    build(True, "audition-embedded.html")
    print(f"guns={len(guns)} clips={clip_total}")
