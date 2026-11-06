#!/usr/bin/env python3
"""UX pass for kayle1v9.com, applied by make_site.py after redesign.py:
1. remembered player profile (lane / server / rank) that drives Builds and Matchups
2. quick start under the hero: profile pills + opponent search with the five most played
3. section order: Coaching, Builds, Matchups, Patch, Videos, About, Merch, Minigames(+Trophies), My setup(Settings+Gear), Support
4. Matchups: visible opponent search with suggestions and the five most played opponents; the Build-Finder is folded in
6. day-over-day deltas next to item / spell / boots win rates (from the previous build, when given)
7. gear tiles with category icons and known specs, live patch line, (jump chips already open their card, Subscribe already opens the dialog)
Usage as a script: uxpass.py <in.html> <out.html> [prev.html] [--preview]"""
import sys, re, json

h = ""

def apply(html, prev_html=None, preview=False):
    global h
    h = html

    def R(a, b, count=1, must=True):
        global h
        if a not in h:
            if must: raise RuntimeError("uxpass anchor missing: " + a[:90])
            return False
        h = h.replace(a, b, count); return True

    # ---------- hooks into the builds closure ----------
    R('  setLane(START_LANE, true);\n',
      '  setLane(START_LANE, true);\n'
      '  window.KB = {get:function(){ return {lane:LANE, r:curR, tier:TIER, IB:IBLIVE, SB:SBLIVE, RL:RLIVE, SP:SPLIVE, servers:SERVERS, patch:PATCH, where:(RMETA[curR] || {}).where || curR}; },\n'
      '    ITI:ITI, ITN:ITN, RN:RN, SPI:SPI, SPN:SPN, runeIcon:runeIcon, sbIcon:sbIcon, switchLane:switchLane, tabs:tabs, tierBtns:tierBtns, LANES:LANES, FLAGS:FLAGS, flagUri:flagUri, RANKI:RANKI};\n'
      '  document.dispatchEvent(new CustomEvent("k1v9:builds"));\n')
    R('    B[r].forEach(function(id){ var c = card(id); if(c) panel.appendChild(c); });\n  }',
      '    B[r].forEach(function(id){ var c = card(id); if(c) panel.appendChild(c); });\n    document.dispatchEvent(new CustomEvent("k1v9:builds"));\n  }')

    # ---------- 6. deltas in the sorted lists ----------
    R('      var nm = el("span", "sbnum"), b = el("b", "", "0%"); b.dataset.v = r[1]; wrTint(b, r[1]); nm.appendChild(b);',
      '      var nm = el("span", "sbnum"), b = el("b", "", "0%"); b.dataset.v = r[1]; wrTint(b, r[1]); nm.appendChild(b);\n'
      '      (function(){ var P = window.KPREV && KPREV[LANE] && KPREV[LANE][curR], pv = P && P[title + "|" + r[0]]; if(pv == null) return; var d = r[1] - pv; if(Math.abs(d) < 0.05) return;\n'
      '        var dl = el("small", "sbd " + (d > 0 ? "up" : "down"), (d > 0 ? "+" : "\\u2212") + Math.abs(d).toFixed(1)); dl.title = (d > 0 ? "Up " : "Down ") + Math.abs(d).toFixed(2) + " points since yesterday (" + pv.toFixed(2) + "%)"; nm.appendChild(dl); })();')

    # ---------- 4. matchups: quick search + top five, right above the picker ----------
    R('    host.appendChild(bar); host.appendChild(guideBox);\n',
      '''    host.appendChild(bar); host.appendChild(guideBox);
    (function(){ // quick search: type a name or tap one of the most played opponents
      var q = el("div", "muquick"), lab = el("label", "muql", "Who are you against?"), wrap = el("div", "muqw"), inp2 = el("input", "musearch muq"), sug = el("ul", "musug");
      inp2.type = "search"; inp2.placeholder = "Type a champion, e.g. Darius"; inp2.autocomplete = "off"; inp2.id = "muq"; lab.htmlFor = "muq"; inp2.setAttribute("aria-label", "Search an opponent");
      sug.setAttribute("role", "listbox"); sug.hidden = true;
      wrap.appendChild(inp2); wrap.appendChild(sug); q.appendChild(lab); q.appendChild(wrap);
      var chips = el("div", "muqc"), top = slugs.slice().sort(function(a, b){ return L[b].n - L[a].n; }).slice(0, 5);
      chips.appendChild(el("span", "btl", "Most played"));
      top.forEach(function(k){ var d = L[k], c = el("button", "muqchip"); c.type = "button"; c.appendChild(chIcon(d.c, 28)); c.appendChild(el("span", "", d.nm)); c.appendChild(wrTint(el("small", "", d.w.toFixed(1) + "%"), d.w)); c.title = "Kayle vs " + d.nm + ": " + d.w.toFixed(1) + "% in " + d.n.toLocaleString("en-US") + " games"; c.addEventListener("click", function(){ pick(k); }); chips.appendChild(c); });
      q.appendChild(chips);
      function pick(k){ sug.hidden = true; inp2.value = ""; choose(k); setTimeout(function(){ var g = host.querySelector(".mugb"); if(g) g.scrollIntoView({behavior:"smooth", block:"start"}); }, 80); }
      function fill(){
        var s = inp2.value.trim().toLowerCase(); sug.innerHTML = "";
        if(!s){ sug.hidden = true; return; }
        var a = slugs.filter(function(k){ return L[k].nm.toLowerCase().indexOf(s) === 0; }).concat(slugs.filter(function(k){ var n = L[k].nm.toLowerCase(); return n.indexOf(s) > 0; })).slice(0, 6);
        if(!a.length){ var li0 = el("li", "muqe", "No opponent called \\u201c" + inp2.value.trim() + "\\u201d"); sug.appendChild(li0); sug.hidden = false; return; }
        a.forEach(function(k){ var d = L[k], li = el("li"), b = el("button", "muqrow"); b.type = "button"; b.setAttribute("role", "option"); b.appendChild(chIcon(d.c, 30)); b.appendChild(el("span", "", d.nm)); b.appendChild(wrTint(el("small", "", d.w.toFixed(1) + "%"), d.w)); b.addEventListener("click", function(){ pick(k); }); li.appendChild(b); sug.appendChild(li); });
        sug.hidden = false;
      }
      inp2.addEventListener("input", fill); inp2.addEventListener("focus", fill);
      inp2.addEventListener("keydown", function(e){ if(e.key === "Enter"){ var f = sug.querySelector(".muqrow"); if(f) f.click(); e.preventDefault(); } if(e.key === "Escape"){ sug.hidden = true; } });
      muOn("click", function(e){ if(!wrap.contains(e.target)) sug.hidden = true; });
      [].slice.call(document.querySelectorAll(".muquick")).forEach(function(o){ if(o.parentNode) o.parentNode.removeChild(o); }); // one picker only: re-rendering (lane switch) must not stack a second one
      var isr = document.getElementById("isr"); if(isr && isr.parentNode === host.parentNode) host.parentNode.insertBefore(q, isr); else host.insertBefore(q, bar);
      window.KMUQ = {choose:choose, L:L, slugs:slugs}; window.KCHI = CHI; document.dispatchEvent(new CustomEvent("k1v9:mu"));
    })();
''')

    # ---------- 3. section order and merges ----------
    def cut(sid):
        global h
        m = re.search(r'\n<section id="%s"[^>]*>.*?\n</section>\n' % sid, h, re.S)
        if not m: raise RuntimeError("section " + sid)
        s = m.group(0); h = h[:m.start()] + "\n" + h[m.end():]; return s.strip("\n") + "\n"
    order = ["coaching", "reviews", "builds", "matchups", "finder", "leaderboard", "patch", "videos", "about", "merch", "games", "trophies", "settings", "gear", "support"]
    blocks = {sid: cut(sid) for sid in order}
    # finder folds into matchups: keep the markup (scripts reference it) but hide it
    blocks["finder"] = blocks["finder"].replace('<section id="finder">', '<section id="finder" hidden>', 1)
    # trophies becomes part of the minigames block, gear part of "My setup"
    blocks["trophies"] = blocks["trophies"].replace('<section id="trophies">', '<section id="trophies" class="subsec">', 1)
    blocks["gear"] = blocks["gear"].replace('<section id="gear">', '<section id="gear" class="subsec">', 1)
    blocks["settings"] = blocks["settings"].replace('<span>My settings</span>', '<span>My setup</span>', 1)
    # the marker that cut() left behind: all sections sat between the hero and the footer
    i = h.index('</header>\n') + len('</header>\n')
    j = h.index('<footer>')
    middle = h[i:j]
    if middle.strip(): raise RuntimeError("unexpected content between sections: " + middle.strip()[:80])
    h = h[:i] + "\n" + "\n".join(blocks[s] for s in order) + "\n" + h[j:]
    # nav: no Finder link
    R('        <li><a href="#finder">Finder</a></li>\n', '')
    R('        <li><a href="#coaching">Coaching</a></li>\n        <li><a href="#patch">Patch</a></li>\n        <li><a href="#builds">Builds</a></li>\n        <li><a href="#matchups">Matchups</a></li>\n',
      '        <li><a href="#coaching">Coaching</a></li>\n        <li><a href="#builds">Builds</a></li>\n        <li><a href="#matchups">Matchups</a></li>\n        <li><a href="#patch">Patch</a></li>\n')
    # rail names
    R('coaching:"Coaching", patch:"Patch", builds:"Builds", finder:"Finder", matchups:"Matchups", leaderboard:"Leaderboard", games:"Minigames", trophies:"Trophies", videos:"Videos", about:"About", merch:"Merch", settings:"Settings", gear:"Gear", support:"Support"',
      'coaching:"Coaching", builds:"Builds", matchups:"Matchups", leaderboard:"Leaderboard", patch:"Patch", videos:"Videos", about:"About", merch:"Merch", games:"Minigames", settings:"My setup", support:"Support"')

    # ---------- 7. gear tiles: category icon + known specs ----------
    GEAR_ICON = {
        "Microphone": '<path d="M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z"/><path d="M19 11a7 7 0 0 1-14 0M12 18v3M8 21h8"/>',
        "Mouse": '<rect x="6" y="3" width="12" height="18" rx="6"/><path d="M12 3v6"/>',
        "Mousepad": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 12h10"/>',
        "Keyboard": '<rect x="2" y="7" width="20" height="10" rx="2"/><path d="M6 11h.01M10 11h.01M14 11h.01M18 11h.01M8 14h8"/>',
        "Headphones": '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>',
        "Monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
        "Camera": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7l1.5-3h5L16 7"/><circle cx="12" cy="13.5" r="3.5"/>',
        "Lens": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
        "Chair": '<path d="M7 4h10v8H7zM7 12v8M17 12v8M5 12h14"/>',
        "Stream Deck": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 9h2M11 9h2M15 9h2M7 13h2M11 13h2M15 13h2"/>',
    }
    GEAR_SPEC = {"Microphone": "Shure SM7B", "Mouse": "Razer Viper V4 Pro \u00b7 2600 DPI", "Mousepad": "Razer Gigantus V2 XXL", "Keyboard": "Razer Huntsman V3 Pro TKL", "Headphones": "beyerdynamic DT 770 Pro", "Monitor": "ASUS TUF VG27AQML1A \u00b7 1440p 260 Hz", "Camera": "Panasonic Lumix G70", "Lens": "Sigma 16mm f/1.4", "Chair": "AutoFull M6 Ultra 2.0", "Stream Deck": "Elgato Stream Deck MK.2"}
    def gear_tile(m):
        name = m.group(2)
        ic = GEAR_ICON.get(name, '<circle cx="12" cy="12" r="8"/>')
        return ('%s<i class="gic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg></i><b>%s</b><span>%s</span><em>View on Amazon ↗</em></a>'
                % (m.group(1), ic, name, GEAR_SPEC.get(name, "")))
    h, n = re.subn(r'(<a class="gear" href="[^"]+" target="_blank" rel="sponsored noopener">)([A-Za-z ]+)<span>View on Amazon</span></a>', gear_tile, h)
    if n < 5: raise RuntimeError("gear tiles not found")

    # ---------- 7. patch: live line under the next-patch card ----------
    R('<div class="pp" data-p="next" role="tabpanel">\n',
      '<div class="pp" data-p="next" role="tabpanel">\n      <p class="plive" id="plive" hidden></p>\n')

    # ---------- 2. quick start under the hero ----------
    R('</header>\n',
      """</header>
<section id="start" class="qstart" aria-label="Quick start">
  <div class="wrap">
    <div class="qscard" id="qscard">
      <div class="qsglow" aria-hidden="true"></div>
      <div class="qstop">
        <div class="qstitle"><span class="dtag">Quick start</span><div class="qsh" id="qsh" role="heading" aria-level="2">Who are you against?</div><p id="qsnote"></p></div>
        <div class="tdpick" role="group" aria-label="Your profile">
          <div class="tdg" id="tdlane"><span class="btl">Lane</span><button type="button" data-v="top"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3.5" stroke-width="1.6" opacity=".38"/><path d="M4.5 19.5L19.5 4.5" stroke-width="1.6" opacity=".38"/><path d="M6.5 18V6.5H18" stroke-width="3.2"/></svg>Top</button><button type="button" data-v="mid"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3.5" stroke-width="1.6" opacity=".38"/><path d="M4.5 19.5L19.5 4.5" stroke-width="1.6" opacity=".38"/><path d="M8 16L16 8" stroke-width="3.4"/></svg>Mid</button></div>
          <div class="tdg" id="tdserver"><span class="btl">Server</span><button type="button" data-v="eu"><i class="qsf" data-f="eu"></i>EU</button><button type="button" data-v="na"><i class="qsf" data-f="na"></i>NA</button><button type="button" data-v="china"><i class="qsf" data-f="china"></i>China</button><button type="button" data-v="korea"><i class="qsf" data-f="korea"></i>Korea</button></div>
          <div class="tdg" id="tdtier"><span class="btl">Rank</span><button type="button" data-v="emerald">Emerald+</button><button type="button" data-v="diamond">Diamond+</button><button type="button" data-v="master">Master+</button><button type="button" data-v="all">All</button></div>
        </div>
      </div>
      <div class="qsrow">
        <div class="muqw qsw"><svg class="qsi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg><input type="search" class="musearch muq" id="qsq" placeholder="Type a champion, e.g. Darius" autocomplete="off" aria-label="Search an opponent"><kbd class="qsk" aria-hidden="true">Enter</kbd><ul class="musug" id="qssug" role="listbox" hidden></ul></div>
        <div class="qsvs" aria-hidden="true"><img class="qskayle" src="a/9497fbaee003.jpg" alt=""><span>vs</span></div>
      </div>
      <div class="muqc qschips" id="qschips"><span class="btl">Most played</span></div>
    </div>
  </div>
</section>
""")

    CSS = r'''
<style id="ux">
/* --- Quick start --- */
.qstart{position:relative;z-index:3;padding-top:0;margin-top:-40px}
.qscard{position:relative;isolation:isolate;overflow:hidden;padding:26px 26px 22px;border-radius:24px;border:1px solid rgba(240,185,75,.5);background:linear-gradient(135deg,rgba(240,185,75,.12),rgba(20,32,63,.94) 45%,rgba(11,18,38,.98));box-shadow:0 30px 70px -30px rgba(0,0,0,.9),inset 0 1px 0 rgba(255,255,255,.08)}
.qscard::before{content:"";position:absolute;inset:0;z-index:-2;background:var(--qsflag,none) right -60px top -10px/330px auto no-repeat;opacity:.07;filter:saturate(1.3);-webkit-mask-image:radial-gradient(45% 70% at 92% 25%,#000,transparent 75%);mask-image:radial-gradient(45% 70% at 92% 25%,#000,transparent 75%);transition:opacity .5s}
.qsglow{position:absolute;z-index:-1;right:-120px;top:-160px;width:420px;height:420px;border-radius:50%;background:radial-gradient(circle,rgba(240,185,75,.22),transparent 65%);pointer-events:none}
.qstop{display:flex;flex-wrap:wrap;align-items:flex-start;justify-content:space-between;gap:14px 28px;margin-bottom:18px}
.qstitle .dtag{display:block;margin:0 0 4px}
.qstitle .qsh{font-size:clamp(1.6rem,3.6vw,2.3rem);font-weight:800;margin:0 0 6px;line-height:1.05;color:#fff}
.qstitle p{margin:0;color:var(--muted);font-size:.86rem}
.qstitle p b{color:var(--text)}
.tdpick{display:flex;flex-wrap:wrap;gap:8px 12px}
.tdg{display:inline-flex;align-items:center;gap:3px;padding:4px;border-radius:999px;border:1px solid rgba(255,255,255,.1);background:rgba(11,18,38,.75);box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
.tdg .btl{margin:0 8px 0 10px;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.tdg button{display:inline-flex;align-items:center;gap:7px;font:inherit;font-size:.86rem;font-weight:600;padding:7px 13px;border:0;border-radius:999px;background:transparent;color:var(--text);cursor:pointer;transition:background .2s,color .2s,transform .25s cubic-bezier(.34,1.56,.64,1)}
.tdg button svg{width:17px;height:17px}
.tdg button:hover{background:rgba(240,185,75,.14)}
.tdg button.on{background:var(--gold);color:#0F1A33;box-shadow:0 4px 14px -4px rgba(240,185,75,.8)}
.tdg button.on svg{opacity:1}
.tdg button[disabled]{opacity:.35;cursor:not-allowed}
.qsrk{display:inline-flex;align-items:center;height:20px;margin:-3px 0;flex:none}
.qsrk img{display:block;width:22px;height:22px;filter:drop-shadow(0 1px 1px rgba(0,0,0,.4))}
.qsrk.multi img{width:18px;height:18px}
.qsrk.multi img+img{margin-left:-7px}
.qsf{display:inline-block;width:21px;height:14px;border-radius:3px;background:var(--fl) center/cover no-repeat;box-shadow:0 0 0 1px rgba(0,0,0,.35);flex:none}
.tdg button.on .qsf{box-shadow:0 0 0 1px rgba(15,26,51,.5)}
.qsrow{display:flex;align-items:center;gap:18px}
.qsw{flex:1;max-width:none}
.qsi{position:absolute;left:16px;top:50%;width:20px;height:20px;transform:translateY(-50%);color:var(--gold);pointer-events:none}
.qsbox .muq,.qsw .muq{min-height:58px;font-size:1.08rem;padding-left:48px;padding-right:72px;border:2px solid rgba(240,185,75,.45);background:rgba(8,14,32,.8);box-shadow:inset 0 2px 8px rgba(0,0,0,.4)}
.qsw .muq:focus{border-color:var(--gold);box-shadow:inset 0 2px 8px rgba(0,0,0,.4),0 0 0 4px rgba(240,185,75,.22)}
.qsk{position:absolute;right:14px;top:50%;transform:translateY(-50%);font:600 .7rem Poppins,system-ui,sans-serif;color:var(--muted);padding:3px 7px;border-radius:6px;border:1px solid rgba(255,255,255,.18);pointer-events:none}
.qsvs{display:flex;align-items:center;gap:10px;flex:none;color:var(--gold);font-weight:800;font-size:1.1rem;letter-spacing:.06em;text-transform:uppercase}
.qskayle{width:52px;height:52px;border-radius:50%;border:2px solid var(--gold);box-shadow:0 0 0 4px rgba(240,185,75,.15),0 8px 20px -6px rgba(0,0,0,.8);object-fit:cover}
.qschips{margin-top:14px}
.qschips .btl{margin-right:4px}
.qschips .muqchip{background:rgba(11,18,38,.8);border-color:rgba(255,255,255,.12)}
.qschips .muqchip:hover{border-color:var(--gold);background:rgba(240,185,75,.1)}
.qschips .muqchip img{width:30px;height:30px;border:1.5px solid rgba(240,185,75,.6)}
.musug .muqrow img{border:1.5px solid rgba(240,185,75,.5)}
@media (max-width:860px){.qsvs span{display:none}}
@media (max-width:720px){.qstart{margin-top:-20px}.qscard{padding:18px 16px 16px;border-radius:20px}.qstop{gap:12px}.qsrow{gap:12px}.qsvs{display:none}.qsw .muq{min-height:54px;font-size:1rem;padding-right:16px}.qsk{display:none}.tdpick{flex-direction:column;align-items:stretch;gap:8px;max-width:100%}.tdg{flex-wrap:nowrap;overflow-x:auto;max-width:100%;scrollbar-width:none;-webkit-overflow-scrolling:touch}.tdg::-webkit-scrollbar{display:none}.tdg button{flex:none;padding:7px 11px;font-size:.82rem}.tdg .btl{flex:none}}

/* --- merged sections --- */
section.subsec{padding-top:0;margin-top:-30px}
section.subsec h2{font-size:clamp(1.4rem,3vw,1.9rem);margin-bottom:8px}
section.subsec .lead{margin-bottom:18px}
/* --- matchups quick search --- */
.muquick{margin:0 0 18px}
.muql{display:block;font-weight:700;margin:0 0 8px}
.muqw{position:relative;max-width:520px}
.muq{width:100%;min-height:50px;font-size:1.02rem}
.musug{position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:30;list-style:none;margin:0;padding:6px;border-radius:14px;border:1px solid rgba(240,185,75,.5);background:rgba(11,18,38,.98);box-shadow:0 24px 50px -16px rgba(0,0,0,.9)}
.musug[hidden]{display:none}
.muqrow{display:flex;align-items:center;gap:10px;width:100%;padding:8px 10px;border:0;border-radius:10px;background:transparent;color:var(--text);font:inherit;font-weight:600;text-align:left;cursor:pointer}
.muqrow:hover,.muqrow:focus-visible{background:rgba(240,185,75,.14);outline:none}
.muqrow img{width:30px;height:30px;border-radius:50%}
.muqrow small{margin-left:auto;font-weight:700}
.muqe{padding:10px 12px;color:var(--muted);font-size:.9rem}
.muqc{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:12px}
.muqc .btl{margin-right:4px}
.muqchip{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:4px 12px 4px 5px;border-radius:999px;border:1.5px solid var(--line);background:var(--panel);color:var(--text);font:inherit;font-size:.88rem;font-weight:600;cursor:pointer;transition:border-color .2s,transform .25s}
.muqchip:hover{border-color:var(--gold);transform:translateY(-2px)}
.muqchip img{width:28px;height:28px;border-radius:50%}
.muqchip small{font-weight:700}
/* --- deltas --- */
.sbd{display:inline-block;margin-left:6px;font-size:.72rem;font-weight:800;padding:1px 6px;border-radius:99px;vertical-align:middle}
.sbd.up{color:#4ADE80;background:rgba(74,222,128,.12)}
.sbd.down{color:#FF7A7A;background:rgba(255,122,122,.12)}
/* --- gear --- */
.gear{display:grid;grid-template-columns:auto 1fr;grid-template-rows:auto auto;gap:2px 14px;align-items:center}
.gear .gic{grid-row:1/3;display:grid;place-items:center;width:44px;height:44px;border-radius:12px;background:rgba(240,185,75,.12);color:var(--gold)}
.gear .gic svg{width:24px;height:24px}
.gear b{font-size:1rem}
.gear span{color:var(--muted);font-size:.84rem}
.gear em{grid-column:2;font-style:normal;font-size:.78rem;color:var(--gold);margin-top:4px}
/* --- patch live line --- */
.plive{margin:0 0 12px;padding:10px 14px;border-radius:12px;border:1px solid rgba(74,222,128,.35);background:rgba(74,222,128,.07);font-size:.92rem}
.plive b{color:#4ADE80}
.plive[hidden]{display:none}
</style>
<script>
(function(){
  var KB = window.KB; if(!KB) return;
  var gl = document.getElementById("tdlane"), gs = document.getElementById("tdserver"), gt = document.getElementById("tdtier");
  var KEY = "k1v9prof", el = function(t, c, x){ var n = document.createElement(t); if(c) n.className = c; if(x != null) n.textContent = x; return n; };
  var NAMES = {eu:"EUW", na:"NA", china:"China", korea:"Korea", top:"Top", mid:"Mid", emerald:"Emerald+", diamond:"Diamond+", master:"Master+", all:"All ranks"};
  function pressed(group, v, avail){ [].forEach.call(group.querySelectorAll("button"), function(b){ b.classList.toggle("on", b.dataset.v === v); b.disabled = !!(avail && avail.indexOf(b.dataset.v) < 0); b.hidden = !!(avail && b.dataset.v === "na" && avail.indexOf("na") < 0); }); }
  function mostPicked(rows){ return (rows || []).slice().sort(function(a, b){ return (b[2] || 0) - (a[2] || 0); })[0]; }
  function copyText(S){
    var r = S.RL[S.r].common, P = KB.RN; if(!r) return "";
    return "Kayle · " + NAMES[S.lane] + " · " + S.where + " · patch " + S.patch + "\nRunes: " + [r.key].concat(r.main).map(function(i){ return P[i] || i; }).join(", ") + " | " + r.sec.map(function(i){ return P[i] || i; }).join(", ") + " | shards: " + r.shards.map(function(i){ return P[i] || i; }).join(", ");
  }
  [].forEach.call(document.querySelectorAll(".qsf"), function(f){ if(KB.flagUri) f.style.setProperty("--fl", KB.flagUri(f.dataset.f)); });
  (function(){ var map = {emerald:["emerald"], diamond:["diamond"], master:["master"], all:["iron", "gold", "challenger"]}, RI = KB.RANKI || {};
    [].forEach.call(gt.querySelectorAll("button"), function(b){ var ks = map[b.dataset.v]; if(!ks) return; var f = el("span", "qsrk" + (ks.length > 1 ? " multi" : "")); f.setAttribute("aria-hidden", "true");
      ks.forEach(function(k){ if(!RI[k]) return; var im = new Image(); im.alt = ""; im.decoding = "async"; im.src = RI[k]; f.appendChild(im); }); if(f.childNodes.length) b.insertBefore(f, b.firstChild); }); })();
  var card = document.getElementById("qscard");
  var note = document.getElementById("qsnote"), chips = document.getElementById("qschips"), qsq = document.getElementById("qsq"), qssug = document.getElementById("qssug");
  function fillChips(){
    var M = window.KMUQ; if(!M) return; [].forEach.call(chips.querySelectorAll(".muqchip"), function(c){ c.remove(); });
    var L = M.L, top = M.slugs.slice().sort(function(a, b){ return L[b].n - L[a].n; }).slice(0, 5);
    top.forEach(function(k){ var d = L[k], c = el("button", "muqchip"); c.type = "button"; var im = new Image(); im.width = im.height = 28; im.alt = ""; im.src = (window.KCHI && KCHI[d.c]) || ""; c.appendChild(im); c.appendChild(el("span", "", d.nm)); var sm = el("small", "", d.w.toFixed(1) + "%"); sm.className = "wr"; sm.style.setProperty("--wh", d.w <= 44 ? 0 : d.w <= 50 ? Math.round((d.w - 44) / 6 * 34) : d.w <= 56 ? Math.round(34 + (d.w - 50) / 6 * 96) : 130); c.appendChild(sm); c.title = "Kayle vs " + d.nm + ": " + d.w.toFixed(1) + "% in " + d.n.toLocaleString("en-US") + " games"; c.addEventListener("click", function(){ go(k); }); chips.appendChild(c); });
  }
  function go(k){ var M = window.KMUQ; if(!M) return; qssug.hidden = true; qsq.value = ""; M.choose(k); setTimeout(function(){ var g = document.querySelector("#mu .mugb"); if(g) g.scrollIntoView({behavior:"smooth", block:"start"}); }, 80); }
  function fillSug(){
    var M = window.KMUQ; if(!M) return; var L = M.L, s = qsq.value.trim().toLowerCase(); qssug.innerHTML = "";
    if(!s){ qssug.hidden = true; return; }
    var a = M.slugs.filter(function(k){ return L[k].nm.toLowerCase().indexOf(s) === 0; }).concat(M.slugs.filter(function(k){ return L[k].nm.toLowerCase().indexOf(s) > 0; })).slice(0, 6);
    if(!a.length){ qssug.appendChild(el("li", "muqe", "No opponent called “" + qsq.value.trim() + "” in this lane")); qssug.hidden = false; return; }
    a.forEach(function(k){ var d = L[k], li = el("li"), b = el("button", "muqrow"); b.type = "button"; b.setAttribute("role", "option"); var im = new Image(); im.width = im.height = 30; im.alt = ""; im.src = (window.KCHI && KCHI[d.c]) || ""; b.appendChild(im); b.appendChild(el("span", "", d.nm)); b.appendChild(el("small", "", d.w.toFixed(1) + "%")); b.addEventListener("click", function(){ go(k); }); li.appendChild(b); qssug.appendChild(li); });
    qssug.hidden = false;
  }
  qsq.addEventListener("input", fillSug); qsq.addEventListener("focus", fillSug);
  qsq.addEventListener("keydown", function(e){ if(e.key === "Enter"){ var f = qssug.querySelector(".muqrow"); if(f) f.click(); e.preventDefault(); } if(e.key === "Escape") qssug.hidden = true; });
  document.addEventListener("click", function(e){ if(!qsq.parentNode.contains(e.target)) qssug.hidden = true; });
  function draw(){
    var S = KB.get();
    pressed(gl, S.lane); pressed(gs, S.r, S.servers); pressed(gt, S.tier);
    note.innerHTML = "Pick your opponent and get runes, spells and items for <b>" + NAMES[S.lane] + " \u00b7 " + S.where + " \u00b7 " + NAMES[S.tier] + "</b>, patch " + S.patch + ". Remembered on this device.";
    if(card && KB.flagUri) card.style.setProperty("--qsflag", KB.flagUri(S.r));
    fillChips();
    try{ localStorage.setItem(KEY, JSON.stringify({lane:S.lane, r:S.r, tier:S.tier})); }catch(e){}
  }
  function clickIn(list, attr, v){ for(var i = 0; i < list.length; i++){ if(list[i].dataset[attr] === v){ if(!list[i].classList.contains("on") && !list[i].hidden) list[i].click(); return; } } }
  gl.addEventListener("click", function(e){ var b = e.target.closest("button"); if(b) KB.switchLane(b.dataset.v); });
  gs.addEventListener("click", function(e){ var b = e.target.closest("button"); if(b && !b.disabled) clickIn(KB.tabs, "r", b.dataset.v); });
  gt.addEventListener("click", function(e){ var b = e.target.closest("button"); if(b) clickIn(KB.tierBtns, "t", b.dataset.v); });
  document.addEventListener("k1v9:builds", draw); document.addEventListener("k1v9:mu", fillChips);
  // restore the saved profile once (lane is restored by the page itself)
  try{ var p = JSON.parse(localStorage.getItem(KEY) || "null"); if(p){ var S0 = KB.get(); if(p.tier && p.tier !== S0.tier) clickIn(KB.tierBtns, "t", p.tier); if(p.r && p.r !== S0.r && S0.servers.indexOf(p.r) >= 0) clickIn(KB.tabs, "r", p.r); } }catch(e){}
  draw();
  // patch section: what the live numbers say right now
  (function(){ var pl = document.getElementById("plive"); if(!pl) return; var S = KB.get(), LT = KB.LANES.top, a = LT.TD && LT.TD.eu && LT.TD.eu.emerald; if(!a) return; var d = a[0] - a[3], s = (d >= 0 ? "+" : "−") + Math.abs(d).toFixed(1);
    pl.innerHTML = "Live right now: Kayle top lane on EU (Emerald+) sits at <b>" + a[0].toFixed(1) + "% win rate</b>, " + s + " points against the previous patch. Updated every night from the ladder."; pl.hidden = false; })();
})();
</script>
'''
    if preview:
        CSS += '<div style="position:fixed;left:14px;bottom:14px;z-index:2147482000;padding:6px 12px;border-radius:99px;background:linear-gradient(90deg,#0AC8B9,#0397AB);color:#012;font:600 .76rem Poppins,system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.4)">Preview · UX pass · not live</div>\n'

    # ---------- 6. previous build's rates for the day-over-day deltas ----------
    prev = extract_prev(prev_html) if prev_html else None
    if prev:
        CSS = '<script>window.KPREV = ' + json.dumps(prev, separators=(",", ":")) + ';</script>\n' + CSS
    i = h.rindex("</body>")
    h = h[:i] + CSS + h[i:]
    return h


def _grab(src, name):
    """Return the JS object literal text of `var NAME = {...};` (balanced braces)."""
    m = re.search(r'var %s = \{' % re.escape(name), src)
    if not m: return None
    i = m.end() - 1; depth = 0
    for j in range(i, len(src)):
        c = src[j]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return src[i:j + 1]
    return None

def _js_to_json(t):
    t = re.sub(r'//[^\n]*', '', t)
    t = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', t)
    t = re.sub(r',\s*([}\]])', r'\1', t)
    return json.loads(t)

def extract_prev(src):
    """Day-over-day reference: title|id -> win rate, per lane and region, from a previous build."""
    out = {}
    for lane, names in (("top", ("SBLIVE", "IBLIVE", "SPLIVE")), ("mid", ("SBLIVEM", "IBLIVEM", "SPLIVEM"))):
        d = {}
        for name in names:
            raw = _grab(src, name)
            if not raw: continue
            try: obj = _js_to_json(raw)
            except Exception: continue
            for reg, v in obj.items():
                d.setdefault(reg, {})
                for key, title in (("start", "Starting items"), ("boots", "Best boots"), ("rows", "Best pairs"), ("fifth", "Fifth item"), ("sixth", "Sixth item")):
                    for r in v.get(key, []) or []:
                        if isinstance(r, list) and len(r) > 1 and isinstance(r[1], (int, float)):
                            d[reg][title + "|" + str(r[0])] = r[1]
        if any(d.values()): out[lane] = d
    return out or None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    prev = open(args[2], encoding="utf-8").read() if len(args) > 2 else None
    out_h = apply(open(args[0], encoding="utf-8").read(), prev, "--preview" in sys.argv)
    open(args[1], "w", encoding="utf-8").write(out_h)
    print("ok", len(out_h))
