"""Language switch for kayle1v9.com: English (source) plus DE, ES, PT, FR, TR, KO, ZH (simplified), JA.

The page stays written in English. At runtime every visible text node and the attributes
placeholder / aria-label / title are looked up in a dictionary and swapped, also for text the
page creates later (MutationObserver). Numbers, dates and game names (champions, items, runes,
summoner spells) are cut out as placeholders before the lookup, so "Kayle vs Darius: 51.1%"
and "Kayle vs Garen: 57.5%" share one entry ("Kayle vs {p0}: {n0}") and game names stay English.

Usage in make_site.py:  s = i18n.apply(s, i18n.load(repo_dir))
Dictionaries: i18n/<code>.json ({template: translation}). They are not inlined: the page fetches only
the dictionary of the language it shows (i18n/<code>.json?v=<hash>), English needs none.
Collect mode for building the dictionaries: open the page with ?i18n=collect, every template the
page shows is gathered in window.__I18N_SEEN.
"""
import json
import os
import re

LANGS = [("en", "English"), ("de", "Deutsch"), ("es", "Español"), ("pt", "Português"), ("fr", "Français"),
         ("tr", "Türkçe"), ("ko", "한국어"), ("zh", "简体中文"), ("ja", "日本語")]


def load(repo):
    out = {}
    for code, _ in LANGS[1:]:
        p = os.path.join(repo, "i18n", code + ".json")
        if os.path.exists(p):
            out[code] = json.load(open(p, encoding="utf-8"))
    return out


def game_names(html):
    """Champion, item, rune and summoner spell names that stay English."""
    names = set()
    for var in ("ITN", "RN"):
        m = re.search(r"var %s = \{(.*?)\};" % var, html, re.S)
        if m:
            names.update(re.findall(r'\d+\s*:\s*"((?:[^"\\]|\\.)+)"', m.group(1)))
    m = re.search(r"var SPN = \{(.*?)\};", html, re.S)
    if m:
        names.update(re.findall(r'"\d+"\s*:\s*"([^"]+)"', m.group(1)))
    m = re.search(r"var ICON_T = \{", html)
    if m:
        names.update(re.findall(r'"([^"]{3,40})": "[A-Za-z0-9+/=]{40}', html[m.end() - 1:m.end() + 3000000].split("};")[0]))
    names.update(re.findall(r'"nm":"([^"]+)"', html))
    names = {n.replace("\\'", "'").replace('\\"', '"') for n in names}
    names = {n for n in names if 2 <= len(n) <= 40 and re.search(r"[A-Za-z]", n) and n != "Kayle"}
    return sorted(names, key=lambda n: (-len(n), n))


HEAD = r"""<script>
(function(){
  var L = __CODES__, l = null;
  try{ var q = new URLSearchParams(location.search).get("lang"); if(L.indexOf(q) >= 0) l = q; }catch(e){}
  if(!l){ try{ var s = localStorage.getItem("k1v9lang"); if(L.indexOf(s) >= 0) l = s; }catch(e){} }
  if(!l){ var n = (navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"]); for(var i = 0; i < n.length && !l; i++){ var c = String(n[i]).slice(0, 2).toLowerCase(); if(L.indexOf(c) >= 0) l = c; } }
  l = l || "en";
  window.K_LANG = l;
  document.documentElement.lang = l;
  if(l !== "en"){
    document.documentElement.classList.add("i18n-wait"); setTimeout(function(){ document.documentElement.classList.remove("i18n-wait"); }, 2500);
    try{ window.K_DICTP = fetch("i18n/" + l + ".json?v=__VER__").then(function(r){ if(!r.ok) throw 0; return r.json(); }); window.K_DICTP.catch(function(){}); }catch(e){}
  }
})();
</script>
<style>html.i18n-wait body{opacity:0}</style>
"""

CSS = r"""
#mainnav li.lgli{display:flex;align-items:center}
.lgw{position:relative;z-index:31;display:inline-flex;align-items:center}
.lgb{display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 11px;border-radius:999px;border:1px solid rgba(240,185,75,.55);background:rgba(11,18,38,.72);color:var(--text,#fff);font:inherit;font-weight:700;font-size:.86rem;letter-spacing:.04em;cursor:pointer;transition:border-color .2s,background .2s,transform .3s cubic-bezier(.34,1.56,.64,1)}
.lgb:hover{border-color:var(--gold,#F0B94B);transform:translateY(-1px)}
.lgb svg{width:16px;height:16px;flex:none}
.lgb .lgc{min-width:1.6em;text-align:left}
.lgm{position:absolute;top:calc(100% + 8px);right:0;z-index:30;min-width:170px;margin:0;padding:6px;list-style:none;border-radius:14px;border:1px solid rgba(240,185,75,.45);background:rgba(11,18,38,.97);box-shadow:0 18px 40px rgba(0,0,0,.55);opacity:0;transform:translateY(-6px) scale(.98);transform-origin:top right;pointer-events:none;transition:opacity .2s ease,transform .25s cubic-bezier(.22,1,.36,1)}
.lgw.open .lgm{opacity:1;transform:none;pointer-events:auto}
.lgm button{display:flex;align-items:center;gap:10px;width:100%;padding:9px 12px;border:0;border-radius:10px;background:transparent;color:var(--text,#fff);font:inherit;font-size:.95rem;text-align:left;cursor:pointer}
.lgm button b{display:inline-block;min-width:2em;font-size:.78rem;letter-spacing:.06em;color:var(--gold,#F0B94B)}
.lgm button:hover,.lgm button:focus-visible{background:rgba(240,185,75,.12)}
.lgm button.on{background:rgba(240,185,75,.2)}
html:lang(ko) body{word-break:keep-all;overflow-wrap:anywhere}
html:lang(ja) body,html:lang(zh) body{line-break:strict;overflow-wrap:anywhere}
html:lang(ko) h1,html:lang(ko) h2,html:lang(ko) h3,html:lang(ja) h1,html:lang(ja) h2,html:lang(ja) h3,html:lang(zh) h1,html:lang(zh) h2,html:lang(zh) h3{letter-spacing:0}
@media (max-width:720px){
  nav ul#mainnav li.lgli{display:block;padding:8px 6px 6px;margin-top:4px;border-top:1px solid rgba(240,185,75,.18)}
  nav ul#mainnav li.lgli .lgw{display:block}
  nav ul#mainnav li.lgli .lgb{display:none}
  nav ul#mainnav li.lgli .lgm{position:static;display:grid;grid-template-columns:repeat(3,1fr);gap:6px;min-width:0;padding:0;border:0;background:none;box-shadow:none;opacity:1;transform:none;pointer-events:auto}
  nav ul#mainnav li.lgli .lgm button{flex-direction:column;justify-content:center;gap:2px;padding:9px 4px;border:1px solid rgba(240,185,75,.35);border-radius:12px;font-size:.78rem;text-align:center}
  nav ul#mainnav li.lgli .lgm button b{min-width:0;font-size:.9rem}
  nav ul#mainnav li.lgli .lgm button.on{background:var(--gold,#F0B94B);color:#0F1A33;border-color:var(--gold,#F0B94B)}
  nav ul#mainnav li.lgli .lgm button.on b{color:#0F1A33}
}
"""

RUNTIME = r"""
(function(){
  var DICT = {}, NAMES = __NAMES__, LABELS = __LABELS__, VER = "__VER__";
  var lang = window.K_LANG || "en", collect = /[?&]i18n=collect/.test(location.search);
  var SEEN = window.__I18N_SEEN = collect ? {} : null;
  var MON = {de:{Jan:"Jan.",Feb:"Feb.",Mar:"März",Apr:"Apr.",May:"Mai",Jun:"Juni",Jul:"Juli",Aug:"Aug.",Sep:"Sep.",Oct:"Okt.",Nov:"Nov.",Dec:"Dez."},
             es:{Jan:"ene",Feb:"feb",Mar:"mar",Apr:"abr",May:"may",Jun:"jun",Jul:"jul",Aug:"ago",Sep:"sept",Oct:"oct",Nov:"nov",Dec:"dic"},
             pt:{Jan:"jan",Feb:"fev",Mar:"mar",Apr:"abr",May:"mai",Jun:"jun",Jul:"jul",Aug:"ago",Sep:"set",Oct:"out",Nov:"nov",Dec:"dez"},
             fr:{Jan:"janv.",Feb:"févr.",Mar:"mars",Apr:"avr.",May:"mai",Jun:"juin",Jul:"juil.",Aug:"août",Sep:"sept.",Oct:"oct.",Nov:"nov.",Dec:"déc."},
             tr:{Jan:"Oca",Feb:"Şub",Mar:"Mar",Apr:"Nis",May:"May",Jun:"Haz",Jul:"Tem",Aug:"Ağu",Sep:"Eyl",Oct:"Eki",Nov:"Kas",Dec:"Ara"}};
  var MNUM = {Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};
  function date(x){
    var q = x.split(" "), m = MNUM[q[1]];
    if(lang === "ko") return q[2] + "년 " + m + "월 " + q[0] + "일";
    if(lang === "zh" || lang === "ja") return q[2] + "年" + m + "月" + q[0] + "日";
    if(lang === "de") return q[0] + ". " + (MON.de[q[1]] || q[1]) + " " + q[2];
    return MON[lang] ? q[0] + " " + (MON[lang][q[1]] || q[1]) + " " + q[2] : x;
  }
  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  var TOK = new RegExp("(\\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \\d{4})|(" + (NAMES.length ? NAMES.map(esc).join("|") : "\\u0000") + ")(?![A-Za-z'])|([+\\u2212-]?\\d+(?:[.,:]\\d+)*%?)", "g");
  function tmpl(s){
    var v = [], c = {d:0, p:0, n:0};
    var k = s.replace(TOK, function(m, d, p, n){ var t = d ? "d" : p ? "p" : "n"; v.push([t, m]); return "{" + t + (c[t]++) + "}"; });
    return {k: k, v: v};
  }
  function fill(tr, v){
    var i = 0, by = {d:[], p:[], n:[]};
    v.forEach(function(x){ by[x[0]].push(x[1]); });
    return tr.replace(/\{([dpn])(\d+)\}/g, function(m, t, n){
      var x = by[t][+n]; if(x == null) return m;
      if(t === "d" && lang !== "en") x = date(x);
      return x;
    });
  }
  function tr(s){
    if(!s) return s;
    var a = s.match(/^\s*/)[0], z = s.match(/\s*$/)[0], core = s.slice(a.length, s.length - z.length);
    if(!core || !/[A-Za-z]/.test(core)) return s;
    var t = tmpl(core);
    if(SEEN && /[A-Za-z]{2}/.test(t.k.replace(/\{[dpn]\d+\}/g, ""))) SEEN[t.k] = (SEEN[t.k] || 0) + 1;
    var D = DICT[lang]; if(!D) return s;
    var x = D[t.k]; if(x == null) return s;
    return a + fill(x, t.v) + z;
  }
  window.K_T = tr;
  var ORIG = new WeakMap(), SET = new WeakMap(), AORIG = new WeakMap();
  // English source text of an element (what the page logic expects), whatever language is shown
  window.K_EN = function(el){
    if(!el) return "";
    if(el.nodeType === 3) return SET.has(el) && SET.get(el) === el.nodeValue ? ORIG.get(el) : el.nodeValue;
    var w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), n, out = "";
    while((n = w.nextNode())) out += SET.has(n) && SET.get(n) === n.nodeValue ? ORIG.get(n) : n.nodeValue;
    return out;
  };
  var SKIP = {SCRIPT:1, STYLE:1, NOSCRIPT:1, TEXTAREA:1, CODE:1, KBD:0};
  var skipRoots = [];
  function skipped(el){
    for(var e = el; e && e !== document.body; e = e.parentNode){
      if(e.nodeType === 1){ if(SKIP[e.tagName]) return true; if(e.hasAttribute("data-noi18n") || e.isContentEditable) return true; }
    }
    for(var i = 0; i < skipRoots.length; i++) if(skipRoots[i].contains(el)) return true;
    return false;
  }
  function doText(n){
    if(!n.parentNode || skipped(n.parentNode)) return;
    var cur = n.nodeValue, o = SET.has(n) && SET.get(n) === cur ? ORIG.get(n) : cur;
    var t = lang === "en" && !SEEN ? o : tr(o);
    ORIG.set(n, o); SET.set(n, t);
    if(t !== cur) n.nodeValue = t;
  }
  var ATTRS = ["placeholder", "aria-label", "title"];
  function doAttrs(el){
    if(el.nodeType !== 1 || skipped(el)) return;
    var m = AORIG.get(el); if(!m){ m = {}; AORIG.set(el, m); }
    ATTRS.forEach(function(a){
      if(!el.hasAttribute(a)) return;
      var cur = el.getAttribute(a), rec = m[a];
      var o = rec && cur === rec[1] ? rec[0] : cur;
      var t = lang === "en" && !SEEN ? o : tr(o);
      m[a] = [o, t];
      if(t !== cur) el.setAttribute(a, t);
    });
  }
  function walk(root){
    if(root.nodeType === 3){ doText(root); return; }
    if(root.nodeType !== 1 || SKIP[root.tagName]) return;
    doAttrs(root);
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null), n;
    while((n = w.nextNode())){ if(n.nodeType === 3) doText(n); else doAttrs(n); }
  }
  var busy = false;
  var mo = new MutationObserver(function(list){
    if(busy) return; busy = true;
    try{
      list.forEach(function(r){
        if(r.type === "characterData") doText(r.target);
        else if(r.type === "attributes") doAttrs(r.target);
        else r.addedNodes.forEach(function(n){ walk(n); });
      });
    }finally{ busy = false; }
  });
  var titleO = document.title;
  function legal(){
    var want = lang === "de" ? "de" : "en";
    document.querySelectorAll(".lsw button[data-l]").forEach(function(b){ if(b.dataset.l === want && !b.classList.contains("on")) b.click(); });
  }
  function run(){
    skipRoots = [].slice.call(document.querySelectorAll(".lsw")).map(function(x){ return x.closest("details") || x.parentNode; });
    walk(document.body);
    document.title = lang === "en" ? titleO : tr(titleO);
    document.documentElement.lang = lang;
    document.documentElement.classList.remove("i18n-wait");
    paint();
  }
  // ---- switcher
  var CODES = LABELS.map(function(x){ return x[0]; });
  function paint(){
    document.querySelectorAll(".lgb .lgc").forEach(function(c){ c.textContent = lang.toUpperCase(); });
    document.querySelectorAll(".lgm button").forEach(function(b){ var on = b.dataset.lang === lang; b.classList.toggle("on", on); b.setAttribute("aria-checked", on ? "true" : "false"); });
  }
  // dictionaries come as separate files, fetched once per language
  function need(l, cb){
    if(l === "en" || DICT[l]) return cb();
    var p = (l === window.K_LANG && window.K_DICTP) || fetch("i18n/" + l + ".json?v=" + VER).then(function(r){ if(!r.ok) throw 0; return r.json(); });
    p.then(function(d){ DICT[l] = d; cb(); }, function(){ cb(); });
  }
  function setLang(l){
    if(CODES.indexOf(l) < 0 || l === lang) return;
    need(l, function(){ apply(l); });
  }
  function apply(l){
    if(l === lang) return;
    lang = window.K_LANG = l;
    try{ localStorage.setItem("k1v9lang", l); }catch(e){}
    try{ var u = new URL(location.href); if(u.searchParams.has("lang")){ u.searchParams.set("lang", l); history.replaceState(null, "", u); } }catch(e){}
    busy = true; try{ run(); legal(); }finally{ busy = false; }
    try{ if(window.umami) umami.track("language", {lang: l}); }catch(e){}
    document.dispatchEvent(new CustomEvent("k1v9:lang", {detail: l}));
  }
  window.K_SETLANG = setLang;
  function build(){
    var nav = document.getElementById("mainnav"); if(!nav || document.getElementById("lgw")) return;
    var w = document.createElement("div"); w.className = "lgw"; w.id = "lgw"; w.setAttribute("data-noi18n", "");
    w.innerHTML = '<button type="button" class="lgb" aria-haspopup="true" aria-expanded="false" aria-label="Language"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.9 5.8 3.9 9s-1.3 6.2-3.9 9c-2.6-2.8-3.9-5.8-3.9-9S9.4 5.8 12 3z"/></svg><span class="lgc">EN</span></button><ul class="lgm" role="menu"></ul>';
    var ul = w.querySelector(".lgm"), btn = w.querySelector(".lgb");
    LABELS.forEach(function(x){
      var li = document.createElement("li"), b = document.createElement("button");
      b.type = "button"; b.dataset.lang = x[0]; b.setAttribute("role", "menuitemradio");
      b.innerHTML = "<b>" + x[0].toUpperCase() + "</b>"; b.appendChild(document.createTextNode(x[1]));
      b.addEventListener("click", function(){ setLang(x[0]); close(); btn.focus(); });
      li.appendChild(b); ul.appendChild(li);
    });
    function close(){ w.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }
    btn.addEventListener("click", function(e){ e.stopPropagation(); var o = !w.classList.contains("open"); w.classList.toggle("open", o); btn.setAttribute("aria-expanded", o ? "true" : "false"); if(o){ var c = ul.querySelector("button.on") || ul.querySelector("button"); if(c) c.focus(); } });
    document.addEventListener("click", function(e){ if(!w.contains(e.target)) close(); });
    document.addEventListener("keydown", function(e){ if(e.key === "Escape" && w.classList.contains("open")){ close(); btn.focus(); } });
    var li = document.createElement("li"); li.className = "lgli"; li.appendChild(w); nav.appendChild(li);
  }
  function start(){
    build(); paint();
    need(lang, function(){
      busy = true; try{ run(); if(lang !== "en") legal(); }finally{ busy = false; }
      mo.observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:ATTRS});
    });
  }
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
"""


# Page logic that reads visible text and sends it on (Google Form, analytics): keep it English.
EN_READS = [
    ('tier = t.querySelector("h3").textContent, price = pe.firstChild.textContent.trim() + " " + pe.querySelector("small").textContent.trim();',
     'tier = (window.K_EN ? K_EN(t.querySelector("h3")) : t.querySelector("h3").textContent), price = (window.K_EN ? K_EN(pe.firstChild) : pe.firstChild.textContent).trim() + " " + (window.K_EN ? K_EN(pe.querySelector("small")) : pe.querySelector("small").textContent).trim();'),
    ('var h = t && t.querySelector("h3,h4,b"); return h ? h.textContent.trim().slice(0, 40) : "";',
     'var h = t && t.querySelector("h3,h4,b"); return h ? (window.K_EN ? K_EN(h) : h.textContent).trim().slice(0, 40) : "";'),
]


def apply(html, dicts=None, preview=False):
    dicts = dicts or {}
    for a, b in EN_READS:
        if html.count(a) == 1:
            html = html.replace(a, b)
        else:
            print('i18n: page hook not found, skipped:', a[:60])
    names = game_names(html)
    import hashlib
    ver = hashlib.sha1(json.dumps(dicts, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]
    head = HEAD.replace("__CODES__", json.dumps([c for c, _ in LANGS])).replace("__VER__", ver)
    assert "<head>" in html
    html = html.replace("<head>", "<head>\n" + head, 1)
    js = (RUNTIME.replace("__VER__", ver)
                 .replace("__NAMES__", json.dumps(names, ensure_ascii=False))
                 .replace("__LABELS__", json.dumps(LANGS, ensure_ascii=False)))
    block = "<style>" + CSS + "</style>\n<script>" + js + "</script>\n"
    i = html.rfind("</body>")
    assert i > 0
    return html[:i] + block + html[i:]
