#!/usr/bin/env node
// Morning overview for Kayle 1v9: compares the newest live data on kayle1v9.com with the previous day.
// Usage: node kayle_morning.js <repo dir> <out dir>
// Reads index.html at HEAD and at the newest older commit whose data date (CHECKED) differs,
// writes summary.json, rates.json, builds.json, movers.json (arrays of row objects) into <out dir>.
"use strict";
const fs = require("fs"), path = require("path"), cp = require("child_process");
const [repo, out] = process.argv.slice(2);
if (!repo || !out) { console.error("usage: node kayle_morning.js <repo dir> <out dir>"); process.exit(2); }
fs.mkdirSync(out, { recursive: true });

function git(args) { return cp.execFileSync("git", ["-C", repo].concat(args), { maxBuffer: 1 << 30 }).toString(); }

// Pull "var NAME = <value>" out of the page and evaluate the value (object, array, string or number).
function grab(html, name) {
  const re = new RegExp("(?:var |,\\s*)" + name + " = ");
  const m = re.exec(html); if (!m) return undefined;
  let i = m.index + m[0].length, c = html[i];
  if (c === '"') { const j = html.indexOf('"', i + 1); return html.slice(i + 1, j); }
  if (c !== "{" && c !== "[") { const j = html.slice(i).search(/[,;\n]/); return Number(html.slice(i, i + j)); }
  let depth = 0, str = null, j = i;
  for (; j < html.length; j++) {
    const ch = html[j];
    if (str) { if (ch === "\\") { j++; continue; } if (ch === str) str = null; continue; }
    if (ch === '"' || ch === "'") { str = ch; continue; }
    if (ch === "{" || ch === "[") depth++;
    else if (ch === "}" || ch === "]") { depth--; if (depth === 0) break; }
  }
  try { return Function('"use strict";return (' + html.slice(i, j + 1) + ")")(); } catch (e) { return undefined; }
}
function load(html) {
  const d = {};
  ["TD", "TDM", "RLIVE", "RLIVEM", "IBLIVE", "IBLIVEM", "SPLIVE", "SPLIVEM", "MULIVE", "MULIVEM", "CHSTAT", "RN", "SPN", "ITN"].forEach(n => d[n] = grab(html, n));
  ["PATCH", "PREV", "CHECKED", "PATCHM", "PREVM", "CHECKEDM"].forEach(n => d[n] = grab(html, n));
  return d;
}

const commits = git(["log", "--format=%H", "-n", "80", "--", "index.html"]).trim().split("\n").filter(Boolean);
const cur = load(git(["show", "HEAD:index.html"]));
let prev = null, prevCommit = null;
for (const h of commits) {
  const d = load(git(["show", h + ":index.html"]));
  if (d.CHECKED && d.CHECKED !== cur.CHECKED) { prev = d; prevCommit = h; break; }
}
const P = prev || {};

const r2 = x => (x == null || isNaN(x)) ? null : Math.round(x * 100) / 100;
const diff = (a, b) => (a == null || b == null) ? null : r2(a - b);
const itn = id => (cur.ITN && cur.ITN[id]) || (P.ITN && P.ITN[id]) || ("Item " + id);
const rn = id => (cur.RN && cur.RN[id]) || ("Rune " + id);
const spn = ids => ids.split("_").map(i => (cur.SPN && cur.SPN[i]) || ("Spell " + i)).join(" + ");
const REG = { eu: "EU", china: "China", korea: "Korea" };
const LANES = [
  { k: "top", name: "Top", td: "TD", r: "RLIVE", ib: "IBLIVE", sp: "SPLIVE", mu: "MULIVE", patch: "PATCH" },
  { k: "mid", name: "Mid", td: "TDM", r: "RLIVEM", ib: "IBLIVEM", sp: "SPLIVEM", mu: "MULIVEM", patch: "PATCHM" }
];

// Win / pick / ban, Emerald+, day over day and against the previous patch.
const rates = [], builds = [], movers = [];
LANES.forEach(L => {
  const t = cur[L.td] || {}, tp = P[L.td] || {};
  Object.keys(t).forEach(reg => {
    const a = (t[reg] || {}).emerald, b = (tp[reg] || {}).emerald;
    if (!a) return;
    rates.push({
      id: L.k + "-" + reg, lane: L.name, region: REG[reg] || reg, patch: cur[L.patch],
      win: a[0], pick: a[1], ban: a[2],
      d_win: b ? diff(a[0], b[0]) : null, d_pick: b ? diff(a[1], b[1]) : null, d_ban: b ? diff(a[2], b[2]) : null,
      win_prev_patch: a[3], d_patch: diff(a[0], a[3])
    });
  });
  // Core build, keystone, spells per server, with what changed since yesterday.
  const ib = cur[L.ib] || {}, ibp = P[L.ib] || {}, rl = cur[L.r] || {}, rlp = P[L.r] || {}, sp = cur[L.sp] || {}, spp = P[L.sp] || {};
  Object.keys(ib).forEach(reg => {
    const c = ib[reg] && ib[reg].core; if (!c) return;
    const cp0 = ibp[reg] && ibp[reg].core;
    const key = rl[reg] && rl[reg].common && rl[reg].common.key, keyp = rlp[reg] && rlp[reg].common && rlp[reg].common.key;
    const s = sp[reg] && sp[reg].rows && sp[reg].rows.slice().sort((x, y) => (y[2] || 0) - (x[2] || 0))[0];
    const sP = spp[reg] && spp[reg].rows && spp[reg].rows.slice().sort((x, y) => (y[2] || 0) - (x[2] || 0))[0];
    const changes = [];
    if (cp0 && cp0.ids.join() !== c.ids.join()) changes.push("Core neu (vorher " + cp0.ids.map(itn).join(" › ") + ")");
    if (keyp && key && keyp !== key) changes.push("Keystone neu (vorher " + rn(keyp) + ")");
    if (sP && s && sP[0] !== s[0]) changes.push("Spells neu (vorher " + spn(sP[0]) + ")");
    builds.push({
      id: L.k + "-" + reg, lane: L.name, region: REG[reg] || reg,
      core: c.ids.map(itn).join(" › "), core_win: c.win, d_core_win: cp0 && cp0.ids.join() === c.ids.join() ? diff(c.win, cp0.win) : null,
      keystone: key ? rn(key) : "", spells: s ? spn(s[0]) : "",
      changes: changes.length ? changes.join("; ") : (prev ? "unverändert" : "kein Vortag")
    });
  });
  // Matchups: biggest day-over-day win rate moves, at least 150 games on both days.
  const mu = (cur[L.mu] || {}).list || {}, mup = (P[L.mu] || {}).list || {};
  const rows = [];
  Object.keys(mu).forEach(slug => {
    const a = mu[slug], b = mup[slug];
    if (!a || !b || a.n < 150 || b.n < 150) return;
    const d = diff(a.w, b.w); if (d == null || d === 0) return;
    rows.push({ id: L.k + "-" + slug, lane: L.name, opponent: a.nm, win: a.w, d_win: d, games: a.n });
  });
  rows.sort((x, y) => Math.abs(y.d_win) - Math.abs(x.d_win));
  movers.push.apply(movers, rows.slice(0, 6));
});

const ch = cur.CHSTAT || {}, chp = P.CHSTAT || {};
const summary = [{
  id: "today", data_date: cur.CHECKED || "", prev_date: P.CHECKED || "",
  patch: cur.PATCH || "", subs: ch.subs == null ? null : ch.subs, d_subs: diff(ch.subs, chp.subs),
  videos: ch.videos == null ? null : ch.videos, goal: ch.goal == null ? null : ch.goal,
  build_changes: builds.filter(b => b.changes !== "unverändert" && b.changes !== "kein Vortag").length,
  generated: new Date().toISOString()
}];

const write = (n, rows) => fs.writeFileSync(path.join(out, n), JSON.stringify(rows));
write("summary.json", summary); write("rates.json", rates); write("builds.json", builds); write("movers.json", movers);
console.log(JSON.stringify({ data_date: cur.CHECKED, prev_date: P.CHECKED || null, prev_commit: prevCommit, rates: rates.length, builds: builds.length, movers: movers.length }));
