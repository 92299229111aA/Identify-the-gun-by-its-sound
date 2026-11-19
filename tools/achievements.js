/* ---------- achievements ---------- */
var Ach = (function () {
  var KEY = "tarkovQuizAchV1";
  var BADGES = [
    { id: "first", name: "首次接触", en: "First Contact", desc: "答对第一题", p: function (s) { return [Math.min(s.correct, 1), 1]; } },
    { id: "recruit", name: "新兵", en: "Recruit", desc: "累计答对 25 题", p: function (s) { return [s.correct, 25]; } },
    { id: "veteran", name: "老兵", en: "Veteran", desc: "累计答对 100 题", p: function (s) { return [s.correct, 100]; } },
    { id: "five", name: "五连", en: "Five Straight", desc: "最高连击达到 5", p: function (s) { return [s.best, 5]; } },
    { id: "ten", name: "十连", en: "Ten Straight", desc: "最高连击达到 10", p: function (s) { return [s.best, 10]; } },
    { id: "twenty", name: "二十连", en: "Twenty", desc: "最高连击达到 20", p: function (s) { return [s.best, 20]; } },
    { id: "rifleman", name: "步兵", en: "Rifleman", desc: "步枪族累计答对 20 题", p: function (s) { return [s.families.rifle || 0, 20]; } },
    { id: "cqb", name: "近战", en: "CQB", desc: "冲锋枪族累计答对 10 题", p: function (s) { return [s.families.smg || 0, 10]; } },
    { id: "sidearm", name: "副武器", en: "Sidearm", desc: "手枪族累计答对 8 题", p: function (s) { return [s.families.pistol || 0, 8]; } },
    { id: "oneshot", name: "一击必中", en: "One Shot", desc: "霰弹与狙击族合计答对 10 题", p: function (s) { return [(s.families.shotgun || 0) + (s.families.sniper || 0), 10]; } },
    { id: "silent", name: "静默行动", en: "Silent", desc: "消音题累计答对 10 次", p: function (s) { return [s.variants.suppressed || 0, 10]; } },
    { id: "fullauto", name: "全自动", en: "Full Auto", desc: "连发题累计答对 10 次", p: function (s) { return [s.variants.auto || 0, 10]; } },
    { id: "flashbang", name: "闪光弹", en: "Flashbang", desc: "听出 KS-23 闪光喷", p: function (s) { return [s.guns.ks23 ? 1 : 0, 1]; } },
    { id: "papasha", name: "波波沙", en: "Papasha", desc: "听出 PPSh-41", p: function (s) { return [s.guns.ppsh ? 1 : 0, 1]; } },
    { id: "collector", name: "图鉴", en: "Collector", desc: "57 把枪各答对一次", p: function (s) { return [Object.keys(s.guns).length, 57]; } }
  ];

  function fresh() {
    return {
      correct: 0,
      best: 0,
      families: { rifle: 0, smg: 0, pistol: 0, shotgun: 0, sniper: 0 },
      variants: { standard: 0, suppressed: 0, auto: 0 },
      guns: {},
      unlocked: {}
    };
  }

  var prog = fresh();
  try {
    var raw = localStorage.getItem(KEY);
    if (raw) {
      var saved = JSON.parse(raw);
      prog = Object.assign(fresh(), saved);
      prog.families = Object.assign(fresh().families, saved.families || {});
      prog.variants = Object.assign(fresh().variants, saved.variants || {});
      prog.guns = saved.guns || {};
      prog.unlocked = saved.unlocked || {};
    }
  } catch (e) {}
  prog.best = Math.max(prog.best, state.best || 0);

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(prog)); } catch (e) {}
  }

  function toast(badge) {
    var box = document.getElementById("toasts");
    if (!box) return;
    var el = document.createElement("div");
    el.className = "toast";
    el.innerHTML = '<div class="k">Unlocked</div><div class="n">' + badge.name + '</div><div class="e">' + badge.en + "</div>";
    box.appendChild(el);
    requestAnimationFrame(function () { el.classList.add("on"); });
    setTimeout(function () {
      el.classList.remove("on");
      setTimeout(function () { el.remove(); }, 400);
    }, 3200);
  }

  function count() {
    var n = Object.keys(prog.unlocked).length;
    var el = document.getElementById("badgeCount");
    if (el) el.textContent = n;
    var sub = document.getElementById("achSub");
    if (sub) sub.textContent = n + " / " + BADGES.length + " unlocked";
  }

  function render() {
    var rows = document.getElementById("achRows");
    if (!rows) return;
    rows.innerHTML = "";
    BADGES.forEach(function (b) {
      var pair = b.p(prog);
      var cur = Math.min(pair[0], pair[1]);
      var done = !!prog.unlocked[b.id];
      var row = document.createElement("div");
      row.className = "row-a" + (done ? " done" : "");
      row.innerHTML = '<span class="mark">' + (done ? "\u2713" : "\u25cb") + "</span>" +
        '<div><div class="nm">' + b.name + "<em>" + b.en + "</em></div>" +
        '<div class="ds">' + b.desc + "</div></div>" +
        '<span class="pg">' + (done ? "done" : cur + "/" + pair[1]) + "</span>";
      rows.appendChild(row);
    });
    count();
  }

  function check() {
    var newly = [];
    BADGES.forEach(function (b) {
      if (prog.unlocked[b.id]) return;
      var pair = b.p(prog);
      if (pair[0] >= pair[1]) {
        prog.unlocked[b.id] = Date.now();
        newly.push(b);
      }
    });
    if (newly.length) {
      save();
      count();
      newly.forEach(function (b, i) {
        setTimeout(function () {
          toast(b);
          if (window.FX && FX.pulse) FX.pulse(0.55);
        }, i * 420);
      });
    }
    return newly;
  }

  function record(question, ok) {
    if (!ok) return;
    prog.correct++;
    prog.best = Math.max(prog.best, state.best || 0);
    var fam = question.gun.category;
    prog.families[fam] = (prog.families[fam] || 0) + 1;
    prog.variants[question.group.key] = (prog.variants[question.group.key] || 0) + 1;
    prog.guns[question.gun.id] = 1;
    save();
    check();
  }

  function reset() {
    prog = fresh();
    save();
    state.best = 0;
    state.streak = 0;
    try { localStorage.setItem("tarkovQuizBest", "0"); } catch (e) {}
    updateStats();
    render();
    count();
  }

  return { record: record, render: render, reset: reset, init: count, check: check, state: function () { return prog; }, badges: BADGES };
})();

document.getElementById("badgeBtn").addEventListener("click", function () {
  Ach.render();
  document.getElementById("achPanel").classList.remove("hidden");
});
document.getElementById("achPanel").addEventListener("click", function (e) {
  if (e.target.id === "achPanel") document.getElementById("achPanel").classList.add("hidden");
});
document.getElementById("achReset").addEventListener("click", function () {
  if (window.confirm("重置成就与最佳连击？")) Ach.reset();
});
