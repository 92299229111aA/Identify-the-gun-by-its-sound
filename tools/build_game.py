"""Build game.html: immersive Lattice-style particle quiz with Overture typography."""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")
HINTS = os.path.join(HERE, "hints.json")
FONT_B64 = os.path.join(PROJECT, "fonts", "subset.b64")
OUT = os.path.join(PROJECT, "game-standalone.html" if os.environ.get("EMBED_AUDIO") == "1" else "game.html")

EMBED = os.environ.get("EMBED_AUDIO") == "1"
manifest = json.load(open(MANIFEST, encoding="utf-8"))
ACH_JS = open(os.path.join(HERE, "achievements.js"), encoding="utf-8").read()
hints = json.load(open(HINTS, encoding="utf-8"))
font_b64 = open(FONT_B64, encoding="utf-8").read().strip() if os.path.exists(FONT_B64) else ""

CATEGORIES = [
    ("all", "全部"),
    ("rifle", "步枪"),
    ("smg", "冲锋枪"),
    ("pistol", "手枪"),
    ("shotgun", "霰弹枪"),
    ("sniper", "狙击"),
]

NICK = {
    "ak74": "74", "ak74m": "74M", "ak101": "101", "ak102": "102", "akm": "AKM",
    "aksu": "AKS-74U", "avt": "AVT", "mutant": "Mk47 Mutant", "mdr": "MDR-556",
    "mdr308": "MDR-762", "mcx": "MCX", "scar": "SCAR", "fal": "FAL", "hk416": "416",
    "m4a1": "M4", "aug": "AUG", "adar": "ADAR", "tx15": "TX15", "rfb": "RFB",
    "rsass": "RSASS", "m1a": "M1A", "sks": "SKS", "ash12": "ASH12", "svd": "SVD",
    "vss": "VSS", "ppsh": "波波沙", "mp5": "MP5", "ump": "UMP", "vector": "维克托",
    "vityaz": "勇士冲锋枪", "mp7": "MP7", "mpx": "MPX", "mp9": "MP9", "p90": "P90",
    "kedr": "雪松", "stm9": "STM9", "aps": "斯捷奇金", "glock18": "G18", "pl": "PL15",
    "m9a3": "M9A3", "1911": "1911", "deagle": "沙鹰", "fiveseven": "FN57", "rhino": "犀牛",
    "rsh": "RSh12", "mosin": "莫辛", "rem700": "M700", "t5000": "T5000", "vpo215": "215",
    "mts255": "短喷", "moss500": "莫斯伯格", "m3": "M3", "ks23": "闪光喷", "toz": "TOZ",
    "rem870": "870", "utes": "UTS15", "rpk16": "RPK16",
}

FULL = {
    "mdr": "MDR 5.56x45", "mdr308": "MDR 7.62x51", "mcx": "MCX .300 BLK",
    "fal": "SA-58 OSW", "vss": "VSS Vintorez", "rsh": "RSh-12", "utes": "UTS-15",
}

FOLD = {"mg": "rifle", "special": "sniper"}

def clip_src(clip):
    if not EMBED:
        return clip["file"]
    path = os.path.join(PROJECT, clip["file"].replace("/", os.sep))
    with open(path, "rb") as handle:
        return "data:audio/ogg;base64," + base64.b64encode(handle.read()).decode("ascii")

data = []
for gun in manifest:
    data.append({
        "id": gun["id"],
        "nick": NICK.get(gun["id"], gun["name"]),
        "name": FULL.get(gun["id"], gun["name"]),
        "caliber": gun["caliber"],
        "type": gun["type"],
        "category": FOLD.get(gun["category"], gun["category"]),
        "rpm": gun.get("rpm"),
        "hint": hints.get(gun["id"], {}).get("hint", ""),
        "groups": [
            {"key": g["key"], "label": g["label"].split("（")[0],
             "clips": [{"file": clip_src(c), "duration": c["duration"]} for c in g["clips"]]}
            for g in gun["groups"]
        ],
    })

if len({g["nick"] for g in data}) != len(data):
    raise SystemExit("duplicate nicknames")

counts = {k: sum(1 for g in data if k == "all" or g["category"] == k) for k, _ in CATEGORIES}
chips = [(k, label, counts[k]) for k, label in CATEGORIES if counts[k] >= 5]
TOTAL = len(data)

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>听声辨枪 · Tarkov</title>
<style>
  @font-face {
    font-family: 'NSerif';
    src: url(data:font/woff2;base64,__FONT__) format('woff2');
    font-weight: 600; font-style: normal; font-display: block;
  }
  :root {
    --ink: #050505;
    --paper: #ece6d8;
    --paper-dim: #b9b2a3;
    --muted: #8d867a;
    --faint: #5a554c;
    --line: rgba(236,230,216,.14);
    --line-soft: rgba(236,230,216,.08);
    --ok: #9db183;
    --bad: #c25b4e;
    --serif: 'NSerif', 'Songti SC', 'STSong', 'Noto Serif CJK SC', serif;
    --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    --mono: ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace;
    --ease: cubic-bezier(.22,.61,.36,1);
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html, body { height: 100%; }
  body {
    margin: 0; background: var(--ink); color: var(--paper);
    font-family: var(--sans); -webkit-font-smoothing: antialiased;
    overflow: hidden;
  }
  #fx {
    position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0;
    display: block; pointer-events: none;
  }
  .vignette {
    position: fixed; inset: 0; z-index: 1; pointer-events: none;
    background: radial-gradient(120% 80% at 50% 40%, rgba(5,5,5,0) 30%, rgba(5,5,5,.55) 72%, rgba(5,5,5,.92) 100%);
  }
  .shade {
    position: fixed; inset: 0; z-index: 2; pointer-events: none;
    background: radial-gradient(56% 54% at 50% 44%, rgba(5,5,5,.88) 0%, rgba(5,5,5,.7) 42%, rgba(5,5,5,0) 74%);
    transition: opacity .45s var(--ease);
  }
  body.morphing .shade { opacity: .15; }

  body.at-start .shell { opacity: 0; }
  .shell { position: relative; z-index: 3; transition: opacity .5s var(--ease); height: 100dvh; display: grid; grid-template-rows: auto 1fr auto; }

  /* top bar */
  .top {
    display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 16px;
    padding: 18px clamp(16px, 3.4vw, 44px);
  }
  .brand { display: flex; align-items: baseline; gap: 10px; }
  .brand b { font-family: var(--serif); font-size: 17px; letter-spacing: .06em; font-weight: 600; }
  .brand span { font: 500 9px/1 var(--mono); letter-spacing: .34em; color: var(--faint); text-transform: uppercase; }
  .cat {
    justify-self: center; display: inline-flex; align-items: center; gap: 10px;
    font: 500 10px/1 var(--mono); letter-spacing: .28em; text-transform: uppercase; color: var(--muted);
    border: 1px solid var(--line-soft); border-radius: 999px; padding: 8px 16px; cursor: pointer;
    background: rgba(5,5,5,.3); transition: .2s var(--ease);
  }
  .cat:hover { color: var(--paper); border-color: var(--line); }
  .cat i { width: 5px; height: 5px; border-radius: 50%; background: var(--paper); opacity: .7; }
  .stats { justify-self: end; display: flex; gap: clamp(14px, 2.6vw, 34px); }
  .stat { text-align: right; }
  .stat .k { display: block; font: 500 8px/1 var(--mono); letter-spacing: .24em; color: var(--faint); text-transform: uppercase; margin-bottom: 6px; }
  .stat .v { font: 500 15px/1 var(--mono); font-variant-numeric: tabular-nums; }

  /* question */
  .stage { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 0 clamp(16px, 4vw, 48px); min-height: 0; }
  .q-meta {
    display: flex; align-items: center; gap: 14px; margin-bottom: clamp(10px, 2vh, 22px);
    font: 500 10px/1 var(--mono); letter-spacing: .3em; text-transform: uppercase; color: var(--paper-dim);
    text-shadow: 0 1px 12px rgba(5,5,5,.9);
  }
  .q-meta b { color: var(--paper-dim); font-weight: 500; }
  .q-meta .dot { width: 3px; height: 3px; border-radius: 50%; background: var(--faint); }
  h1.q {
    font-family: var(--serif); font-weight: 600;
    font-size: clamp(40px, 7.6vw, 104px); line-height: .98; letter-spacing: -.01em;
    margin: 0 0 clamp(18px, 4vh, 42px); color: var(--paper);
    text-shadow: 0 4px 44px rgba(5,5,5,.9);
  }
  .play-wrap { display: flex; flex-direction: column; align-items: center; gap: 16px; }
  .aperture {
    position: relative; width: clamp(84px, 10vw, 116px); height: clamp(84px, 10vw, 116px);
    border-radius: 50%; border: 1px solid rgba(236,230,216,.32); background: rgba(5,5,5,.45);
    -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);
    box-shadow: 0 0 60px rgba(5,5,5,.7);
    display: grid; place-items: center; cursor: pointer; transition: .28s var(--ease);
  }
  .aperture::before, .aperture::after {
    content: ""; position: absolute; border-radius: 50%; border: 1px solid var(--line-soft);
    inset: -14px; transition: .35s var(--ease);
  }
  .aperture::after { inset: -28px; opacity: .5; }
  .aperture:hover { border-color: var(--line); }
  .aperture:hover::before { inset: -20px; }
  .aperture:hover::after { inset: -38px; }
  .aperture .tri {
    width: 0; height: 0; margin-left: 5px;
    border-left: clamp(18px, 2vw, 24px) solid var(--paper);
    border-top: clamp(11px, 1.2vw, 14px) solid transparent;
    border-bottom: clamp(11px, 1.2vw, 14px) solid transparent;
  }
  .aperture.on { animation: pulse 1.5s var(--ease) infinite; }
  @keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(236,230,216,.14); }
    50% { box-shadow: 0 0 0 22px rgba(236,230,216,0); }
  }
  .keyhint { font: 500 9px/1 var(--mono); letter-spacing: .26em; color: var(--faint); text-transform: uppercase; }

  /* dock */
  .dock {
    position: relative; z-index: 3;
    border-top: 1px solid var(--line-soft);
    background: linear-gradient(180deg, rgba(5,5,5,.55), rgba(5,5,5,.92));
    -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px);
    padding: 18px clamp(16px, 3.4vw, 44px) max(18px, env(safe-area-inset-bottom));
  }
  .dock-inner { max-width: 1180px; margin: 0 auto; }
  .options { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
  .opt {
    position: relative; display: flex; align-items: baseline; gap: 12px; text-align: left;
    padding: 16px 16px 15px; border: 1px solid rgba(236,230,216,.12); background: rgba(236,230,216,.045);
    color: var(--paper); font: inherit; cursor: pointer; overflow: hidden;
    transition: .2s var(--ease);
  }
  .opt::after {
    content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 1px;
    background: var(--paper); transform: scaleX(0); transform-origin: left; transition: transform .3s var(--ease);
  }
  .opt:hover:not(:disabled) { background: rgba(236,230,216,.05); border-color: var(--line); }
  .opt:hover:not(:disabled)::after { transform: scaleX(1); }
  .opt:disabled { cursor: default; }
  .opt .idx { font: 500 9px/1 var(--mono); letter-spacing: .1em; color: var(--faint); flex: none; }
  .opt .names { min-width: 0; }
  .opt .nm { display: block; font-size: 17px; font-weight: 600; letter-spacing: -.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .opt .en { display: block; margin-top: 5px; font: 500 9.5px/1 var(--mono); letter-spacing: .08em; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .opt.correct { border-color: rgba(157,177,131,.6); background: rgba(157,177,131,.08); }
  .opt.correct::after { background: var(--ok); transform: scaleX(1); }
  .opt.wrong { border-color: rgba(194,91,78,.55); background: rgba(194,91,78,.07); }
  .opt.wrong::after { background: var(--bad); transform: scaleX(1); }
  .opt.dim { opacity: .4; }

  .result { display: grid; grid-template-rows: 0fr; opacity: 0; transition: grid-template-rows .42s var(--ease), opacity .3s var(--ease); }
  .result.show { grid-template-rows: 1fr; opacity: 1; }
  .result > .inner { overflow: hidden; }
  .verdict {
    display: flex; align-items: baseline; gap: 14px; padding: 16px 2px 0;
    font-family: var(--serif); font-size: clamp(17px, 2vw, 21px); color: var(--paper);
  }
  .verdict .tag { font: 500 9px/1 var(--mono); letter-spacing: .26em; text-transform: uppercase; padding: 5px 8px; border: 1px solid currentColor; }
  .verdict.ok { color: var(--ok); }
  .verdict.no { color: var(--bad); }
  .verdict .streak { margin-left: auto; font: 500 10px/1 var(--mono); letter-spacing: .18em; color: var(--muted); text-transform: uppercase; }
  .profiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 14px; }
  .prof { border-top: 1px solid var(--line-soft); padding: 12px 2px 0; }
  .prof.hit { border-top-color: rgba(157,177,131,.55); }
  .prof .n { font-family: var(--serif); font-size: 15px; }
  .prof .n em { font: 500 9px/1 var(--mono); letter-spacing: .06em; color: var(--muted); margin-left: 6px; font-style: normal; }
  .prof .m { margin-top: 5px; font: 500 9px/1.5 var(--mono); letter-spacing: .06em; color: var(--muted); }
  .prof .t { margin-top: 6px; font-size: 11px; line-height: 1.6; color: var(--faint); }
  .actions { display: flex; justify-content: center; padding: 18px 0 2px; }
  .next {
    font: 500 12px/1 var(--mono); letter-spacing: .22em; text-transform: uppercase; cursor: pointer;
    padding: 14px 34px; border: 1px solid var(--line); background: transparent; color: var(--paper);
    transition: .2s var(--ease);
  }
  .next:hover { background: var(--paper); color: var(--ink); border-color: var(--paper); }

  /* start overlay */
  .overlay {
    position: fixed; inset: 0; z-index: 40; display: grid; place-items: center;
    background: radial-gradient(70% 60% at 50% 45%, rgba(5,5,5,.55), rgba(5,5,5,.82)); -webkit-backdrop-filter: blur(3px); backdrop-filter: blur(3px);
    transition: opacity .6s var(--ease), visibility .6s;
  }
  .overlay.hidden { opacity: 0; visibility: hidden; }
  .overlay .inner { text-align: center; width: 100%; max-width: 660px; padding: 24px; box-sizing: border-box; }
  .overlay .eyebrow { font: 500 9px/1 var(--mono); letter-spacing: .34em; color: var(--faint); text-transform: uppercase; margin-bottom: 26px; }
  .overlay h2 {
    font-family: var(--serif); font-weight: 600;
    font-size: clamp(46px, 9.4vw, 108px); line-height: .96; letter-spacing: -.01em; margin: 0 0 22px;
  }
  .overlay p { color: var(--muted); font-size: 14px; line-height: 1.9; margin: 0 auto 32px; max-width: 420px; }
  .chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 34px; }
  .chip {
    font: 500 10px/1 var(--mono); letter-spacing: .16em; text-transform: uppercase;
    padding: 10px 16px; border: 1px solid var(--line-soft); background: transparent; color: var(--muted);
    cursor: pointer; transition: .2s var(--ease);
  }
  .chip:hover { color: var(--paper); border-color: var(--line); }
  .chip.active { background: var(--paper); color: var(--ink); border-color: var(--paper); }
  .chip small { margin-left: 7px; opacity: .55; }
  .overlay .start {
    font: 500 12px/1 var(--mono); letter-spacing: .3em; text-transform: uppercase; cursor: pointer;
    padding: 17px 46px; border: 1px solid var(--paper); background: var(--paper); color: var(--ink);
    transition: .2s var(--ease);
  }
  .overlay .start:hover { background: transparent; color: var(--paper); }
  .overlay .fine { margin-top: 26px; font: 500 9px/1.8 var(--mono); letter-spacing: .2em; color: #3f3b34; text-transform: uppercase; }

  /* aperture veil */
  .veil {
    position: fixed; inset: 0; z-index: 60; background: var(--ink); pointer-events: none;
    clip-path: circle(150% at 50% 50%);
  }
  .veil.open { animation: iris 1.5s var(--ease) forwards; }
  @keyframes iris {
    from { clip-path: circle(150% at 50% 50%); }
    to { clip-path: circle(0% at 50% 50%); }
  }
  .veil .ring {
    position: absolute; left: 50%; top: 50%; width: 10vmax; height: 10vmax; margin: -5vmax 0 0 -5vmax;
    border: 1px solid rgba(236,230,216,.5); border-radius: 50%; opacity: 0;
  }
  .veil.open .ring { animation: ring 1.5s var(--ease) forwards; }
  @keyframes ring {
    from { transform: scale(.2); opacity: .9; }
    to { transform: scale(26); opacity: 0; }
  }

  .morphing .q, .morphing .q-meta, .morphing .play-wrap { opacity: .1; transition: opacity .45s var(--ease); }
  .q, .q-meta, .play-wrap { transition: opacity .45s var(--ease); }

  /* achievements */
  .badges {
    display: inline-flex; align-items: baseline; gap: 6px; cursor: pointer;
    background: transparent; border: 1px solid var(--line-soft); padding: 7px 12px;
    color: var(--paper-dim); font: 500 10px/1 var(--mono); letter-spacing: .14em;
    transition: .2s var(--ease);
  }
  .badges:hover { color: var(--paper); border-color: var(--line); }
  .badges .ico { opacity: .7; }
  .badges b { color: var(--paper); font-weight: 600; }
  .badges .tot { opacity: .45; }

  .toasts { position: fixed; top: 74px; right: clamp(14px, 3vw, 44px); z-index: 50; display: flex; flex-direction: column; gap: 8px; pointer-events: none; }
  .toast {
    min-width: 240px; max-width: 300px; padding: 12px 16px; border: 1px solid rgba(236,230,216,.35);
    background: rgba(5,5,5,.88); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
    transform: translateX(20px); opacity: 0; transition: .35s var(--ease);
  }
  .toast.on { transform: translateX(0); opacity: 1; }
  .toast .k { font: 500 8px/1 var(--mono); letter-spacing: .26em; color: var(--muted); text-transform: uppercase; margin-bottom: 6px; }
  .toast .n { font-family: var(--serif); font-size: 17px; }
  .toast .e { font: 500 9px/1.6 var(--mono); letter-spacing: .12em; color: var(--muted); margin-top: 4px; text-transform: uppercase; }

  .panel { position: fixed; inset: 0; z-index: 55; display: grid; place-items: center; padding: 20px;
           background: rgba(5,5,5,.72); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);
           transition: opacity .4s var(--ease), visibility .4s; }
  .panel.hidden { opacity: 0; visibility: hidden; }
  .panel .sheet {
    width: 100%; max-width: 720px; max-height: 84dvh; overflow-y: auto;
    border: 1px solid var(--line); background: rgba(8,8,8,.96); padding: 28px clamp(18px, 3vw, 34px);
  }
  .panel h3 { font-family: var(--serif); font-weight: 600; font-size: clamp(26px, 4vw, 38px); margin: 0 0 6px; }
  .panel .sub { font: 500 9px/1 var(--mono); letter-spacing: .26em; color: var(--faint); text-transform: uppercase; margin-bottom: 22px; }
  .rows { display: flex; flex-direction: column; }
  .row-a { display: grid; grid-template-columns: 26px 1fr auto; gap: 12px; align-items: baseline; padding: 12px 0; border-top: 1px solid var(--line-soft); }
  .row-a .mark { font: 500 11px/1 var(--mono); color: var(--faint); }
  .row-a .nm { font-family: var(--serif); font-size: 16px; }
  .row-a .nm em { font: 500 9px/1 var(--mono); letter-spacing: .1em; color: var(--faint); margin-left: 8px; font-style: normal; text-transform: uppercase; }
  .row-a .ds { margin-top: 4px; font-size: 11px; color: var(--muted); }
  .row-a .pg { font: 500 10px/1 var(--mono); color: var(--faint); font-variant-numeric: tabular-nums; }
  .row-a.done .mark, .row-a.done .nm { color: var(--paper); }
  .row-a.done .pg { color: var(--olive); }
  .row-a:not(.done) { opacity: .55; }
  .panel .foot { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 22px; padding-top: 18px; border-top: 1px solid var(--line); }
  .panel .foot .hint { font: 500 9px/1.6 var(--mono); letter-spacing: .16em; color: var(--faint); text-transform: uppercase; }
  .panel button { font: 500 10px/1 var(--mono); letter-spacing: .2em; text-transform: uppercase; cursor: pointer;
                  padding: 11px 18px; border: 1px solid var(--line); background: transparent; color: var(--paper-dim); }
  .panel button:hover { color: var(--paper); border-color: var(--paper-dim); }

  @media (max-width: 980px) {
    .options { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .profiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }
  @media (max-width: 640px) {
    .top { grid-template-columns: 1fr auto; padding: 14px 16px; }
    .cat { display: none; }
    .stats { gap: 12px; }
    .s-best { display: none; }
    .stat .k { display: none; }
    .s-streak .v::before { content: "×"; opacity: .45; margin-right: 1px; }
    .options { grid-template-columns: minmax(0, 1fr); }
    .dock { padding: 14px 14px max(14px, env(safe-area-inset-bottom)); }
    .opt { padding: 13px 14px; }
    .opt .nm { font-size: 16px; }
    h1.q { font-size: clamp(34px, 11vw, 52px); }
    .profiles { grid-template-columns: minmax(0, 1fr); }
    .keyhint { display: none; }
    .toasts { top: 68px; right: 14px; left: 14px; align-items: flex-end; }
    body { overflow-y: auto; }
    .shell { height: auto; min-height: 100dvh; }
    .stage { min-height: 54vh; }
  }
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration: .001ms !important; transition-duration: .001ms !important; }
  }
</style>
</head>
<body class="at-start">
<canvas id="fx"></canvas>
<div class="vignette"></div>
<div class="shade"></div>

<div class="shell">
  <header class="top">
    <div class="brand"><b>听声辨枪</b><span>Tarkov</span></div>
    <button class="cat" id="catBtn"><i></i><span id="catLabel">全部</span> · 换枪族</button>
    <div class="stats">
      <button class="badges" id="badgeBtn" title="成就"><span class="ico">◈</span><b id="badgeCount">0</b><span class="tot">/15</span></button>
      <div class="stat s-acc"><span class="k">Acc</span><span class="v" id="acc">—</span></div>
      <div class="stat s-streak"><span class="k">Streak</span><span class="v" id="streak">0</span></div>
      <div class="stat s-best"><span class="k">Best</span><span class="v" id="best">0</span></div>
    </div>
  </header>

  <main class="stage">
    <div class="q-meta"><span>第 <b id="qnum">1</b> 题</span><span class="dot"></span><span id="variant">标准</span></div>
    <h1 class="q">这是什么枪？</h1>
    <div class="play-wrap">
      <button class="aperture" id="play" aria-label="播放枪声"><span class="tri"></span></button>
      <div class="keyhint">Space 重放 · 1–4 选择</div>
    </div>
  </main>

  <section class="dock">
    <div class="dock-inner">
      <div class="options" id="options"></div>
      <div class="result" id="result">
        <div class="inner">
          <div class="verdict" id="verdict"></div>
          <div class="profiles" id="profiles"></div>
          <div class="actions"><button class="next" id="next">下一题</button></div>
        </div>
      </div>
    </div>
  </section>
</div>

<div class="overlay" id="start">
  <div class="inner">
    <div class="eyebrow">__TOTAL__ weapons · 3 variants</div>
    <h2>听声辨枪</h2>
    <p>全部枪械的原始开火声，标准、消音、连发随机。<br>先选一个枪族，再听出四个选项里的那一把。</p>
    <div class="chips" id="chips"></div>
    <button class="start" id="begin">开始</button>
    <div class="fine">Audio from your local game files</div>
  </div>
</div>

<div class="toasts" id="toasts"></div>

<div class="panel hidden" id="achPanel">
  <div class="sheet">
    <h3>成就</h3>
    <div class="sub" id="achSub">0 / 15 unlocked</div>
    <div class="rows" id="achRows"></div>
    <div class="foot">
      <span class="hint">进度自动保存 · 刷新不丢</span>
      <button id="achReset">重置进度</button>
    </div>
  </div>
</div>

<div class="veil" id="veil"><div class="ring"></div></div>

<script>
var GUNS = __DATA__;
var CATEGORIES = __CHIPS__;
var WEIGHTS = { standard: 0.55, suppressed: 0.30, auto: 0.15 };
var audio = new Audio();
audio.preload = "auto";

/* ---------- particles ---------- */
var FX = (function () {
  var canvas = document.getElementById("fx");
  var gl = canvas.getContext("webgl2", { antialias: false, alpha: false, premultipliedAlpha: false });
  var COUNT = 9000;
  var prog = null, buf = null, targets = null, base = null, seeds = null, rands = null;
  var uTime, uMix, uShock, uColor, uSize, uAspect;
  var start = performance.now();
  var shock = 0, mix = 0, mixTarget = 0;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function shader(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.error(gl.getShaderInfoLog(s)); }
    return s;
  }

  var VS = [
    "#version 300 es",
    "in vec2 aPos;",
    "in vec2 aTarget;",
    "in float aSeed;",
    "in float aRand;",
    "uniform float uTime, uMix, uShock, uSize, uAspect;",
    "out float vA;",
    "void main() {",
    "  vec2 p = aPos;",
    "  float t = uTime;",
    "  p.x += 0.028 * sin(t * 0.45 + aSeed * 6.2831) * (0.4 + aRand);",
    "  p.y += 0.028 * cos(t * 0.37 + aSeed * 4.7123) * (0.4 + aRand);",
    "  p += normalize(p + 0.0001) * uShock * 0.22 * (0.3 + aRand);",
    "  vec2 q = mix(p, aTarget, uMix);",
    
    "  gl_Position = vec4(q, 0.0, 1.0);",
    "  gl_PointSize = uSize * (1.0 + 0.5 * uMix) * (0.6 + aRand * 0.8);",
    "  vA = 0.22 + 0.5 * aRand + 0.75 * uMix;",
    "}"
  ].join("\n");

  var FS = [
    "#version 300 es",
    "precision mediump float;",
    "in float vA;",
    "uniform vec3 uColor;",
    "out vec4 outColor;",
    "void main() {",
    "  vec2 d = gl_PointCoord - 0.5;",
    "  float r = dot(d, d);",
    "  if (r > 0.25) discard;",
    "  float a = smoothstep(0.25, 0.02, r);",
    "  outColor = vec4(uColor, a * vA);",
    "}"
  ].join("\n");

  function layout() {
    var aspect = innerWidth / Math.max(1, innerHeight);
    var spread = Math.max(1, aspect) * 1.02;
    for (var i = 0; i < COUNT; i++) {
      base[i * 2] = (Math.random() * 2 - 1) * spread;
      base[i * 2 + 1] = (Math.random() * 2 - 1) * 1.02;
    }
  }

  function upload() {
    if (!buf) return;
    var data = new Float32Array(COUNT * 6);
    for (var i = 0; i < COUNT; i++) {
      data[i * 6] = base[i * 2];
      data[i * 6 + 1] = base[i * 2 + 1];
      data[i * 6 + 2] = targets[i * 2];
      data[i * 6 + 3] = targets[i * 2 + 1];
      data[i * 6 + 4] = seeds[i];
      data[i * 6 + 5] = rands[i];
    }
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, data);
  }

  function init() {
    if (!gl) return false;
    prog = gl.createProgram();
    gl.attachShader(prog, shader(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(prog)); return false; }
    gl.useProgram(prog);

    base = new Float32Array(COUNT * 2);
    targets = new Float32Array(COUNT * 2);
    seeds = new Float32Array(COUNT);
    rands = new Float32Array(COUNT);
    for (var s = 0; s < COUNT; s++) { seeds[s] = Math.random(); rands[s] = Math.random(); }
    layout();

    buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(COUNT * 6), gl.DYNAMIC_DRAW);
    upload();

    var stride = 6 * 4;
    var aPos = gl.getAttribLocation(prog, "aPos");
    var aTarget = gl.getAttribLocation(prog, "aTarget");
    var aSeed = gl.getAttribLocation(prog, "aSeed");
    var aRand = gl.getAttribLocation(prog, "aRand");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, stride, 0);
    gl.enableVertexAttribArray(aTarget);
    gl.vertexAttribPointer(aTarget, 2, gl.FLOAT, false, stride, 8);
    gl.enableVertexAttribArray(aSeed);
    gl.vertexAttribPointer(aSeed, 1, gl.FLOAT, false, stride, 16);
    gl.enableVertexAttribArray(aRand);
    gl.vertexAttribPointer(aRand, 1, gl.FLOAT, false, stride, 20);

    uTime = gl.getUniformLocation(prog, "uTime");
    uMix = gl.getUniformLocation(prog, "uMix");
    uShock = gl.getUniformLocation(prog, "uShock");
    uColor = gl.getUniformLocation(prog, "uColor");
    uSize = gl.getUniformLocation(prog, "uSize");
    uAspect = gl.getUniformLocation(prog, "uAspect");
    gl.uniform3f(uColor, 0.925, 0.902, 0.847);
    gl.uniform1f(uSize, 2.3);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    resize();
    return true;
  }

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(innerWidth * dpr);
    canvas.height = Math.floor(innerHeight * dpr);
    if (gl) {
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.uniform1f(uAspect, innerWidth / innerHeight);
      if (base && seeds) { layout(); upload(); }
    }
  }

  /* sample text into particle targets */
  function morphTo(text) {
    if (!gl || reduced) return;
    var font = "600 200px 'NSerif', 'Songti SC', serif";
    var c = document.createElement("canvas");
    var ctx = c.getContext("2d");
    ctx.font = font;
    var w = Math.ceil(ctx.measureText(text).width) + 40;
    var h = 280;
    c.width = w; c.height = h;
    ctx = c.getContext("2d");
    ctx.font = font;
    ctx.fillStyle = "#fff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, w / 2, h / 2);
    var img = ctx.getImageData(0, 0, w, h).data;
    var pts = [];
    for (var y = 0; y < h; y += 2) {
      for (var x = 0; x < w; x += 2) {
        if (img[(y * w + x) * 4 + 3] > 128) pts.push([x, y]);
      }
    }
    if (!pts.length) return;
    var arr = new Float32Array(COUNT * 2);
    var textW = 0.62;
    var textH = textW * (h / w);
    for (var i = 0; i < COUNT; i++) {
      var p = pts[Math.floor(Math.random() * pts.length)];
      arr[i * 2] = (p[0] / w - 0.5) * textW;
      arr[i * 2 + 1] = -(p[1] / h - 0.5) * textH;
    }
    for (var k = 0; k < COUNT; k++) {
      targets[k * 2] = arr[k * 2];
      targets[k * 2 + 1] = arr[k * 2 + 1];
    }
    upload();
    mixTarget = 1;
    document.body.classList.add("morphing");
    setTimeout(function () { document.body.classList.remove("morphing"); }, 1550);
    setTimeout(function () { mixTarget = 0; }, 1800);
  }

  function kick() {
    if (reduced) return;
    shock = 1;
  }

  function frame(now) {
    if (!gl) return;
    var t = (now - start) / 1000;
    shock *= 0.94;
    mix += (mixTarget - mix) * 0.08;
    gl.uniform1f(uTime, t);
    gl.uniform1f(uMix, mix);
    gl.uniform1f(uShock, shock);
    gl.clearColor(0.02, 0.02, 0.02, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.POINTS, 0, COUNT);
    requestAnimationFrame(frame);
  }

  var ok = init();
  if (ok) requestAnimationFrame(frame);
  addEventListener("resize", resize);
  return { ok: ok, kick: kick, pulse: function (strength) { if (!reduced) shock = Math.max(shock, strength || 0.6); }, morphTo: morphTo, resize: resize, debug: function () { return { mix: mix, mixTarget: mixTarget, reduced: reduced, t: [targets[0], targets[1], targets[2], targets[3]] }; } };
})();

/* ---------- game ---------- */
var state = {
  total: 0, correct: 0, streak: 0, best: 0, answered: false,
  question: null, lastGun: null, category: "all", pool: GUNS.slice()
};
try {
  var saved = parseInt(localStorage.getItem("tarkovQuizBest") || "0", 10);
  if (!isNaN(saved)) state.best = saved;
  var life = JSON.parse(localStorage.getItem("tarkovQuizStatsV1") || "null");
  if (life) {
    state.total = life.answered || 0;
    state.correct = life.correct || 0;
  }
} catch (e) {}

function pick(a) { return a[Math.floor(Math.random() * a.length)]; }
function shuffle(a) {
  for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
  return a;
}
function poolFor(key) { return key === "all" ? GUNS.slice() : GUNS.filter(function (g) { return g.category === key; }); }
function chooseGroup(gun) {
  var groups = gun.groups, total = 0, weighted = [];
  for (var i = 0; i < groups.length; i++) { var w = WEIGHTS[groups[i].key] || 0.1; total += w; weighted.push({ g: groups[i], w: w }); }
  var r = Math.random() * total;
  for (var k = 0; k < weighted.length; k++) { r -= weighted[k].w; if (r <= 0) return weighted[k].g; }
  return groups[0];
}

var variantBag = [];
function nextPreferredKey() {
  if (!variantBag.length) {
    variantBag = [];
    for (var i = 0; i < 5; i++) variantBag.push("standard");
    for (var i = 0; i < 3; i++) variantBag.push("suppressed");
    for (var i = 0; i < 2; i++) variantBag.push("auto");
    shuffle(variantBag);
  }
  return variantBag.pop();
}

function newQuestion() {
  var preferred = nextPreferredKey();
  var candidates = state.pool.filter(function (g) {
    return g.groups.some(function (x) { return x.key === preferred; });
  });
  if (!candidates.length) {
    preferred = "standard";
    candidates = state.pool.slice();
  }
  var gun, guard = 0;
  do { gun = pick(candidates); guard++; } while (gun.id === state.lastGun && candidates.length > 1 && guard < 20);
  state.lastGun = gun.id;
  var group = gun.groups.filter(function (x) { return x.key === preferred; })[0] || chooseGroup(gun);
  var clip = pick(group.clips);
  var others = shuffle(state.pool.filter(function (g) { return g.id !== gun.id; })).slice(0, 3);
  if (others.length < 3) {
    shuffle(GUNS).forEach(function (g) { if (others.length < 3 && g.id !== gun.id && others.indexOf(g) < 0) others.push(g); });
  }
  state.question = { gun: gun, group: group, clip: clip, options: shuffle([gun].concat(others)) };
  state.answered = false;

  document.getElementById("qnum").textContent = state.total + 1;
  document.getElementById("variant").textContent = group.label;
  document.getElementById("result").classList.remove("show");
  document.getElementById("profiles").innerHTML = "";
  document.getElementById("verdict").textContent = "";

  var box = document.getElementById("options");
  box.innerHTML = "";
  state.question.options.forEach(function (opt, index) {
    var btn = document.createElement("button");
    btn.className = "opt";
    btn.dataset.id = opt.id;
    btn.innerHTML = '<span class="idx">0' + (index + 1) + '</span><span class="names">' +
      '<span class="nm">' + opt.nick + '</span>' +
      (opt.nick === opt.name ? "" : '<span class="en">' + opt.name + '</span>') + "</span>";
    btn.addEventListener("click", function () { answer(opt.id); });
    box.appendChild(btn);
  });
}

function playClip() {
  var q = state.question;
  if (!q) return;
  audio.pause();
  audio.src = q.clip.file;
  audio.currentTime = 0;
  var p = audio.play();
  document.getElementById("play").classList.add("on");
  FX.kick();
  audio.onended = function () { document.getElementById("play").classList.remove("on"); };
  if (p && p.catch) p.catch(function () { document.getElementById("play").classList.remove("on"); });
}

function answer(id) {
  if (state.answered) return;
  state.answered = true;
  var q = state.question;
  var ok = id === q.gun.id;
  state.total++;
  if (ok) {
    state.correct++; state.streak++;
    if (state.streak > state.best) { state.best = state.streak; try { localStorage.setItem("tarkovQuizBest", String(state.best)); } catch (e) {} }
  } else state.streak = 0;

  var buttons = document.querySelectorAll(".opt");
  for (var i = 0; i < buttons.length; i++) {
    var idAttr = buttons[i].dataset.id;
    buttons[i].disabled = true;
    if (idAttr === q.gun.id) buttons[i].classList.add("correct");
    else if (idAttr === id) buttons[i].classList.add("wrong");
    else buttons[i].classList.add("dim");
  }

  var verdict = document.getElementById("verdict");
  verdict.className = "verdict " + (ok ? "ok" : "no");
  verdict.innerHTML = '<span class="tag">' + (ok ? "hit" : "miss") + "</span>" +
    "<span>" + (ok ? "答对了" : "是 " + q.gun.nick) + "</span>" +
    '<span class="streak">streak ' + state.streak + "</span>";

  var box = document.getElementById("profiles");
  box.innerHTML = "";
  q.options.forEach(function (opt) {
    var d = document.createElement("div");
    d.className = "prof" + (opt.id === q.gun.id ? " hit" : "");
    d.innerHTML = '<div class="n">' + opt.nick + (opt.nick === opt.name ? "" : "<em>" + opt.name + "</em>") + "</div>" +
      '<div class="m">' + opt.caliber + " · " + opt.type + (opt.rpm ? " · " + opt.rpm + "rpm" : "") + "</div>" +
      '<div class="t">' + opt.hint + "</div>";
    box.appendChild(d);
  });

  document.getElementById("result").classList.add("show");
  updateStats();
  Ach.record(q, ok);
  if (ok) FX.morphTo(q.gun.nick);
}

function updateStats() {
  document.getElementById("acc").textContent = state.total ? Math.round((state.correct / state.total) * 100) + "%" : "—";
  document.getElementById("streak").textContent = state.streak;
  document.getElementById("best").textContent = state.best;
  try {
    localStorage.setItem("tarkovQuizStatsV1", JSON.stringify({ answered: state.total, correct: state.correct }));
  } catch (e) {}
}

function next() {
  if (!state.answered) { playClip(); return; }
  newQuestion();
  playClip();
}

__ACH__
document.getElementById("play").addEventListener("click", playClip);
document.getElementById("next").addEventListener("click", next);

function buildChips() {
  var box = document.getElementById("chips");
  box.innerHTML = "";
  CATEGORIES.forEach(function (entry) {
    var key = entry[0], label = entry[1], count = entry[2];
    var chip = document.createElement("button");
    chip.className = "chip" + (key === state.category ? " active" : "");
    chip.innerHTML = label + "<small>" + count + "</small>";
    chip.addEventListener("click", function () {
      state.category = key;
      state.pool = poolFor(key);
      document.querySelectorAll(".chip").forEach(function (c) { c.classList.remove("active"); });
      chip.classList.add("active");
      document.getElementById("catLabel").textContent = label;
    });
    box.appendChild(chip);
  });
}
buildChips();

document.getElementById("catBtn").addEventListener("click", function () {
  document.getElementById("start").classList.remove("hidden");
});

document.addEventListener("keydown", function (event) {
  if (!document.getElementById("start").classList.contains("hidden")) {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); begin(); }
    return;
  }
  if (event.key === " " || event.key === "r" || event.key === "R") { event.preventDefault(); next(); return; }
  if (event.key === "Enter") { event.preventDefault(); next(); return; }
  if (event.key >= "1" && event.key <= "4" && !state.answered) {
    var option = state.question.options[parseInt(event.key, 10) - 1];
    if (option) answer(option.id);
  }
});

function begin() {
  document.body.classList.remove("at-start");
  var overlay = document.getElementById("start");
  overlay.classList.add("hidden");
  if (!state.question) { newQuestion(); playClip(); }
  else { newQuestion(); playClip(); }
}

document.getElementById("begin").addEventListener("click", begin);
updateStats();
Ach.init();

/* aperture opening on load */
window.addEventListener("load", function () {
  var veil = document.getElementById("veil");
  setTimeout(function () { veil.classList.add("open"); }, 220);
  setTimeout(function () { veil.style.display = "none"; }, 1900);
});
</script>
</body>
</html>
"""

page = (
    PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    .replace("__CHIPS__", json.dumps(chips, ensure_ascii=False))
    .replace("__TOTAL__", str(TOTAL))
    .replace("__FONT__", font_b64)
    .replace("__ACH__", ACH_JS)
)
with open(OUT, "w", encoding="utf-8") as handle:
    handle.write(page)
print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.1f} KB), guns={TOTAL}, font={'yes' if font_b64 else 'no'}")
