#!/usr/bin/env python3
"""Polish pass for kayle1v9.com, applied by make_site.py after uxpass.py:
1. matchup guide opens with a loading-screen banner (Kayle splash vs opponent splash, big win rate, verdict)
2. sparklines + direction arrows on the win / pick / ban stats in Builds (from the day-over-day history file)
3. spotlight scrolling: the section in view is bright, the rest dims a little
4. one card language: same radius, gold hover border and shadow on every card
5. no empty state: the matchup of the day is shown until the visitor picks another opponent
6. micro-feedback: toast on copy, gold flash on server switch, rank emblem spin
Usage: polish.py <in.html> <out.html> [history.json] [--preview]"""
import sys, re, json

h = ""

def apply(html, history=None, preview=False):
    global h
    h = html

    def R(a, b, count=1, must=True):
        global h
        if a not in h:
            if must: raise RuntimeError("polish anchor missing: " + a[:90])
            return False
        h = h.replace(a, b, count); return True

    # ---------- 1. banner in the matchup guide ----------
    R('''      var card = el("div", "mucard" + (animate ? " fresh" : ""));
      var hd = el("div", "muhead");''',
      '''      var card = el("div", "mucard" + (animate ? " fresh" : ""));
      (function(){ // loading-screen banner: Kayle vs the opponent
        var vd0 = verdict(d.w), bn = el("div", "mubn " + vd0[1]), L0 = el("div", "mubl"), R0 = el("div", "mubr"), M0 = el("div", "mubm");
        var kay = new Image(); kay.alt = ""; kay.decoding = "async"; kay.src = "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Kayle_0.jpg"; kay.onerror = function(){ kay.onerror = null; kay.src = window.KHERO || "a/572b4b283d60.jpg"; }; L0.appendChild(kay);
        var opp = new Image(); opp.alt = ""; opp.decoding = "async"; opp.src = "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/" + ddKey(d.nm) + "_0.jpg";
        opp.onerror = function(){ R0.classList.add("noart"); opp.remove(); var ic = chIcon(d.c, 120); ic.className = "mubic"; R0.appendChild(ic); };
        R0.appendChild(opp);
        var nm1 = el("span", "mubnm", "Kayle"), nm2 = el("span", "mubnm r", d.nm); L0.appendChild(nm1); R0.appendChild(nm2);
        var big = wrTint(el("b", "", "0.00%"), d.w); M0.appendChild(el("span", "mubvs", "VS")); M0.appendChild(big); M0.appendChild(el("span", "muvd " + vd0[1], vd0[0])); M0.appendChild(el("small", "", d.n.toLocaleString("en-US") + " games · Emerald+"));
        bn.appendChild(L0); bn.appendChild(M0); bn.appendChild(R0); card.appendChild(bn);
        if(animate) setTimeout(function(){ countTo(big, d.w, 200); }, 60); else big.textContent = d.w.toFixed(2) + "%";
      })();
      var hd = el("div", "muhead mubn-after");''')
    R('''    function chIcon(cid, size){''',
      '''    var DDK = {"Cho'Gath":"Chogath", "Dr. Mundo":"DrMundo", "Wukong":"MonkeyKing", "Kai'Sa":"Kaisa", "Kha'Zix":"Khazix", "Vel'Koz":"Velkoz", "Rek'Sai":"RekSai", "Kog'Maw":"KogMaw", "LeBlanc":"Leblanc", "Nunu & Willump":"Nunu", "Renata Glasc":"Renata", "Bel'Veth":"Belveth", "K'Sante":"KSante", "Tahm Kench":"TahmKench", "Twisted Fate":"TwistedFate", "Xin Zhao":"XinZhao", "Jarvan IV":"JarvanIV", "Lee Sin":"LeeSin", "Master Yi":"MasterYi", "Miss Fortune":"MissFortune", "Aurelion Sol":"AurelionSol", "Fiddlesticks":"Fiddlesticks"};
    function ddKey(nm){ return DDK[nm] || nm.replace(/[^A-Za-z]/g, ""); }
    function chIcon(cid, size){''')

    R('var sp = el("span", "bstat", x[0]); var sb = el("b", "", x[2] ? d.rates[x[2]] + "%" : x[1]);', 'var sp = el("span", "bstat", x[0]); if(x[2]) sp.dataset.stat = x[2]; var sb = el("b", "", x[2] ? d.rates[x[2]] + "%" : x[1]);')

    # ---------- 5. no empty state: the matchup of the day is shown right away ----------
    R('''      card.appendChild(im); card.appendChild(tx); card.appendChild(go); host.insertBefore(card, bar);
    })();''',
      '''      card.appendChild(im); card.appendChild(tx); card.appendChild(go); host.insertBefore(card, bar);
      window.KMOTD = k;
    })();
    setTimeout(function(){ if(!curSlug && window.KMOTD && L[window.KMOTD]){ choose(window.KMOTD); var g = host.querySelector(".mucard"); if(g) g.classList.add("motdpre"); } }, 0);''')

    # ---------- 6. gold flash on server switch, emblem spin ----------
    R('''      panel.classList.add("sw");
      setTimeout(function(){ render(t.dataset.r); panel.classList.remove("sw"); }, 220);''',
      '''      panel.classList.add("sw");
      setTimeout(function(){ render(t.dataset.r); panel.classList.remove("sw"); panel.classList.remove("flash"); void panel.offsetWidth; panel.classList.add("flash"); }, 220);''')

    R('  var it = L[i], done = false;', '  var it = L[i], done = false; window.KHERO = "hero/" + it[0] + ".webp";')

    CSS = r'''
<style id="polish">
/* --- 1. matchup banner --- */
.mubn{position:relative;flex:0 0 100%;width:calc(100% + 36px);box-sizing:border-box;display:grid;grid-template-columns:1fr auto 1fr;align-items:stretch;min-height:190px;margin:-18px -18px 16px;border-radius:14px 14px 0 0;overflow:hidden;background:#0B1226;isolation:isolate}
.mubl,.mubr{position:relative;overflow:hidden;min-height:190px}
.mubl img,.mubr img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 20%;transform:scale(1.04);transition:transform 1.4s cubic-bezier(.22,1,.36,1)}
.mubr img{object-position:50% 18%}
.mucard:hover .mubl img,.mucard:hover .mubr img{transform:scale(1.09)}
.mubl::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(11,18,38,.1),rgba(11,18,38,.96) 100%),linear-gradient(0deg,rgba(11,18,38,.8),transparent 60%)}
.mubr::after{content:"";position:absolute;inset:0;background:linear-gradient(270deg,rgba(11,18,38,.1),rgba(11,18,38,.96) 100%),linear-gradient(0deg,rgba(11,18,38,.8),transparent 60%)}
.mubr.noart{display:grid;place-items:center;background:radial-gradient(circle at 50% 40%,rgba(214,69,69,.25),transparent 60%)}
.mubr.noart .mubic{position:relative;z-index:1;width:96px;height:96px;border-radius:50%;border:3px solid var(--gold);box-shadow:0 0 30px rgba(240,185,75,.35)}
@media (max-width:720px){.mubr.noart .mubic{width:72px;height:72px}}
.mubnm{position:absolute;left:18px;bottom:14px;z-index:1;font-size:1.3rem;font-weight:800;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.8)}
.mubnm.r{left:auto;right:18px}
.mubm{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:16px 26px;min-width:200px;background:linear-gradient(180deg,rgba(11,18,38,.3),rgba(11,18,38,.85))}
.mubvs{font-size:.78rem;font-weight:800;letter-spacing:.3em;color:var(--gold);text-transform:uppercase}
.mubm b{font-size:2.6rem;line-height:1;font-weight:800;font-variant-numeric:tabular-nums;color:var(--text);text-shadow:0 0 24px rgba(240,185,75,.35)}
.mubm small{color:var(--muted);font-size:.78rem}
.mubn::before{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background:linear-gradient(180deg,transparent 70%,rgba(20,32,63,1))}
.mubn.fav::before{box-shadow:inset 0 -3px 0 #1f9d55}.mubn.even::before{box-shadow:inset 0 -3px 0 var(--gold)}.mubn.tough::before{box-shadow:inset 0 -3px 0 #d64545}
.muhead.mubn-after .muwr{display:none}
.muhead.mubn-after>img{display:none}
.muhead.mubn-after{display:none}
@media (max-width:720px){.mubn{grid-template-columns:1fr 1fr;grid-template-rows:150px auto;min-height:0;margin:-14px -14px 14px;width:calc(100% + 28px)}.mubl,.mubr{min-height:150px}.mubm{grid-column:1/-1;grid-row:2;flex-direction:row;flex-wrap:wrap;gap:8px 14px;padding:12px 14px;background:rgba(11,18,38,.9)}.mubm b{font-size:1.9rem}.mubvs{display:none}.mubnm{font-size:1.05rem;left:12px;bottom:10px}.mubnm.r{right:12px}}
/* --- 2. sparklines --- */
.spk{display:inline-flex;align-items:center;gap:6px;margin-left:10px;vertical-align:middle}
.spk svg{width:64px;height:20px;overflow:visible}
.spk svg path{fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.spk svg .area{fill:currentColor;opacity:.12;stroke:none}
.spk .arr{font-size:.74rem;font-weight:800}
.spk.up{color:#4ADE80}.spk.down{color:#FF7A7A}.spk.flat{color:var(--muted)}
.spk svg circle{fill:currentColor}
/* --- 3. spotlight --- */
.js section:not([hidden]),.js .today,.js .qstart{transition:opacity .6s ease,filter .6s ease}
.js body.spot section:not([hidden]):not(.lit){opacity:.72}
.js body.spot section.lit{opacity:1;filter:none}
@media (prefers-reduced-motion:reduce){.js section{transition:none}}
/* --- 4. one card language --- */
.bsbcard,.mucard,.gcard,.scard,.mcard,.video,.gear,.tier.tc,.pcard,.stile,.rvc{border-radius:18px}
.bsbcard,.mucard,.gcard,.scard,.gear,.pcard,.stile{border:1px solid var(--line)}
.bsbcard:hover,.mucard:hover,.gcard:hover,.scard:hover,.gear:hover,.pcard:hover,.video:hover,.mcard:hover{border-color:rgba(240,185,75,.6);box-shadow:0 22px 44px -20px rgba(0,0,0,.85),0 0 0 1px rgba(240,185,75,.25),0 0 30px -12px rgba(240,185,75,.4)}
.mcard{animation:none!important}
.mcard:hover{transform:translateY(-4px)}
.gear{transition:transform .35s cubic-bezier(.22,1,.36,1),box-shadow .35s,border-color .3s}
.gear:hover{transform:translateY(-3px)}
/* --- 6. micro feedback --- */
.ktoast{position:fixed;left:50%;bottom:calc(max(18px,env(safe-area-inset-bottom,0px)) + 18px);z-index:2147483000;transform:translate(-50%,16px);opacity:0;padding:11px 18px;border-radius:999px;border:1px solid rgba(240,185,75,.55);background:rgba(11,18,38,.96);color:var(--text);font:600 .9rem Poppins,system-ui,sans-serif;box-shadow:0 14px 40px -10px rgba(0,0,0,.9);pointer-events:none;transition:opacity .25s,transform .35s cubic-bezier(.22,1,.36,1);display:flex;align-items:center;gap:10px}
.ktoast.on{opacity:1;transform:translate(-50%,0)}
.ktoast i{display:grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--gold);color:#0F1A33;font-style:normal;font-size:.75rem;font-weight:900}
@keyframes kflash{0%{box-shadow:0 0 0 0 rgba(240,185,75,0)}25%{box-shadow:0 0 0 3px rgba(240,185,75,.55),0 0 40px rgba(240,185,75,.35)}100%{box-shadow:0 0 0 0 rgba(240,185,75,0)}}
.bpanel.flash{animation:kflash 1.1s ease-out;border-radius:18px}
@keyframes kspin{0%{transform:rotateY(0)}100%{transform:rotateY(360deg)}}
.btiers .bcchip.spin .rk img,.tdg button.spin .qsrk img{animation:kspin .7s cubic-bezier(.22,1,.36,1)}
.tdg button.spin{transform:scale(1.06)}
@media (prefers-reduced-motion:reduce){.bpanel.flash{animation:none}.btiers .bcchip.spin .rk img,.tdg button.spin .qsrk img{animation:none}.ktoast{transition:none}}
</style>
<script>
(function(){
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  // --- 6. toast ---
  var toast = document.createElement("div"); toast.className = "ktoast"; toast.setAttribute("role", "status"); toast.innerHTML = "<i>✓</i><span></span>"; document.body.appendChild(toast); var tT = 0;
  window.KTOAST = function(msg){ toast.lastChild.textContent = msg; toast.classList.add("on"); clearTimeout(tT); tT = setTimeout(function(){ toast.classList.remove("on"); }, 1800); };
  document.addEventListener("click", function(e){
    var b = e.target.closest("button"); if(!b) return;
    var t = (b.textContent || "").trim();
    if(/^Copy/i.test(t) || b.id === "copy" || b.id === "copySum" || b.classList.contains("cqsec") && /copy/i.test(t)) setTimeout(function(){ var t2 = (b.textContent || "").trim(); if(/copied/i.test(t2)) KTOAST(/rune/i.test(t) ? "Runes copied" : /code/i.test(t) || b.id === "copy" ? "Code copied" : "Copied to clipboard"); }, 120);
    if(b.closest(".btiers") || b.closest("#tdtier")){ b.classList.remove("spin"); void b.offsetWidth; b.classList.add("spin"); setTimeout(function(){ b.classList.remove("spin"); }, 800); }
    if(b.closest("#tdserver") && !b.disabled){ var bp = document.getElementById("bpanel"); if(bp){ setTimeout(function(){ bp.classList.remove("flash"); void bp.offsetWidth; bp.classList.add("flash"); }, 260); } }
  }, true);
  // --- 3. spotlight ---
  var secs = [].slice.call(document.querySelectorAll("section")), q = false;
  function spot(){
    q = false;
    var mid = innerHeight * .45, best = null, bd = 1e9;
    secs.forEach(function(s){ if(s.hidden) return; var r = s.getBoundingClientRect(); if(r.height === 0) return; var d = r.top <= mid && r.bottom >= mid ? 0 : Math.min(Math.abs(r.top - mid), Math.abs(r.bottom - mid)); if(d < bd){ bd = d; best = s; } });
    var on = scrollY > innerHeight * .5;
    document.body.classList.toggle("spot", on);
    secs.forEach(function(s){ var lit = s === best || (best && s.classList.contains("subsec") && s.previousElementSibling === best) || (best && best.classList.contains("subsec") && best.previousElementSibling === s); s.classList.toggle("lit", !!lit); });
  }
  if(!reduce){ addEventListener("scroll", function(){ if(!q){ q = true; requestAnimationFrame(spot); } }, {passive:true}); addEventListener("resize", spot); spot(); }
  // --- 2. sparklines on the win / pick / ban stats ---
  var HIST = window.KHIST; if(!HIST) return;
  function spark(vals){
    var n = vals.length; if(n < 3) return null;
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), rg = (hi - lo) || 1, W = 64, H = 18;
    var pts = vals.map(function(v, i){ return [(i / (n - 1) * W).toFixed(1), (H - (v - lo) / rg * (H - 3) - 1.5).toFixed(1)]; });
    var d = "M" + pts.map(function(p){ return p[0] + " " + p[1]; }).join(" L");
    var area = d + " L" + W + " " + H + " L0 " + H + " Z";
    var last = pts[n - 1], delta = vals[n - 1] - vals[0], base = Math.max(0.05, Math.abs(vals[0])), rel = delta / base, cls = Math.abs(rel) < 0.02 ? "flat" : (delta > 0 ? "up" : "down"), dp = base < 5 ? 2 : 1;
    var s = document.createElement("span"); s.className = "spk " + cls; s.title = n + " days: " + vals[0].toFixed(2) + "% → " + vals[n - 1].toFixed(2) + "%";
    s.innerHTML = '<svg viewBox="0 0 ' + W + ' ' + H + '" aria-hidden="true"><path class="area" d="' + area + '"/><path d="' + d + '" stroke="currentColor"/><circle cx="' + last[0] + '" cy="' + last[1] + '" r="2"/></svg><span class="arr">' + (cls === "flat" ? "→" : cls === "up" ? "↗ +" + delta.toFixed(1) : "↘ −" + Math.abs(delta).toFixed(1)) + "</span>";
    return s;
  }
  function decorate(){
    var KB = window.KB; if(!KB) return; var S = KB.get(), H1 = HIST[S.lane] && HIST[S.lane][S.r] && HIST[S.lane][S.r][S.tier]; if(!H1) return;
    var panel = document.getElementById("bpanel"); if(!panel) return;
    [].forEach.call(panel.querySelectorAll(".bstat[data-stat]"), function(x){ var k = x.dataset.stat; if(!H1[k] || x.querySelector(".spk")) return; var sp = spark(H1[k]); if(sp) x.appendChild(sp); });
  }
  document.addEventListener("k1v9:builds", function(){ setTimeout(decorate, 50); }); setTimeout(decorate, 400);
})();
</script>
'''
    if history:
        CSS = '<script>window.KHIST = ' + json.dumps(history, separators=(",", ":")) + ';</script>\n' + CSS
    if preview:
        CSS += '<div style="position:fixed;left:14px;bottom:14px;z-index:2147482000;padding:6px 12px;border-radius:99px;background:linear-gradient(90deg,#0AC8B9,#0397AB);color:#012;font:600 .76rem Poppins,system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.4)">Preview · polish · not live</div>\n'
    i = h.rindex("</body>")
    h = h[:i] + CSS + h[i:]
    return h


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    hist = json.load(open(args[2])) if len(args) > 2 else None
    out_h = apply(open(args[0], encoding="utf-8").read(), hist, "--preview" in sys.argv)
    open(args[1], "w", encoding="utf-8").write(out_h)
    print("ok", len(out_h))
