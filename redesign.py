#!/usr/bin/env python3
"""Redesign pass for kayle1v9.com (coaching art cards, mobile hero, spacing, section backdrops, motion, fixes).
Applied by make_site.py on every build; the artifact itself keeps the old layout.
Usage as a script: redesign.py <in.html> <out.html> [--preview]"""
import sys, re
h = ""

def apply(html, preview=False):
    global h
    h = html

    def R(a, b, count=1, must=True):
        global h
        if a not in h:
            if must: raise RuntimeError("redesign anchor missing: " + a[:90])
            return
        h = h.replace(a, b, count)

    # ---------- 1. coaching tiers as art cards ----------
    ART = {"review": ("6", "img/lv6.webp", "Power spike · Level 6", 1, ""),
           "session": ("11", "img/lv11.webp", "Power spike · Level 11", 2, '<span class="tbadge">Most booked</span>'),
           "program": ("16", "img/lv16.webp", "Power spike · Level 16", 3, "")}
    for k, (lv, art, kick, pips, badge) in ART.items():
        pat = re.compile(r'    <div class="tier">\n      <div><h3>(Level ' + lv + r' [^<]*)</h3>')
        m = pat.search(h)
        if not m: raise RuntimeError("redesign: tier " + lv + " not found")
        pipsh = "".join('<i class="%s"></i>' % ("on" if i < pips else "") for i in range(3))
        new = ('    <div class="tier tc" data-lv="%s">\n'
               '      <div class="tart"><img src="%s" alt="" width="960" height="720" decoding="async">%s'
               '<span class="tkick"><span class="tpips">%s</span>%s</span></div>\n'
               '      <div class="tbody"><div><h3>%s</h3>') % (lv, art, badge, pipsh, kick, m.group(1))
        h = h[:m.start()] + new + h[m.end():]
    # close .tbody right after each tier's .rq block: the .rq block ends with "</div></div></div>\n    </div>" (tier close)
    h = h.replace('Pay with StreamElements</a></div></div></div>\n    </div>\n',
                  'Pay with StreamElements</a></div></div></div>\n      </div>\n    </div>\n', 3)
    # wrap the three tiers
    R('    <div class="cq" id="cq"></div>\n    <div class="tier tc"', '    <div class="cq" id="cq"></div>\n    <div class="tiers">\n    <div class="tier tc"')
    R('    <p class="tz">Your time zone is', '    </div>\n    <p class="tz">Your time zone is')
    # level 11 art focus: the Transcended splash sits right of centre

    # ---------- 2. mobile hero: burger menu, one Play button, short promo ----------
    R('      <ul>\n        <li><a href="#coaching">Coaching</a></li>',
      '      <button type="button" class="burger" id="burger" aria-label="Menu" aria-expanded="false" aria-controls="mainnav"><i></i><i></i><i></i></button>\n'
      '      <ul id="mainnav">\n        <li><a href="#coaching">Coaching</a></li>')
    R('    <div class="lvrow">',
      '    <button type="button" class="playbtn" id="playbtn" aria-expanded="false" aria-controls="lvrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="7" width="19" height="11" rx="5.5"/><path d="M8 10.5v4M6 12.5h4"/><circle cx="15.5" cy="11.5" r=".9" fill="currentColor"/><circle cx="18" cy="13.7" r=".9" fill="currentColor"/></svg><span>Play</span><small>level up, skins, minigames</small></button>\n'
      '    <div class="lvrow" id="lvrow">')
    # promo pill: keep the long text, add a short one for phones
    m = re.search(r'(<a class="wdpill" href="#wdrop"><b>New</b><span>)(.*?)(</span><i aria-hidden="true">)', h, re.S)
    if not m: raise RuntimeError("redesign: wdpill not found")
    short = 'Free stickers over &euro;40' if 'sticker' in m.group(2).lower() else ('Free shipping over &euro;100' if 'shipping' in m.group(2).lower() else 'Winter drop is live')
    h = h[:m.start()] + m.group(1).replace('<span>', '<span class="lg">') + m.group(2) + '</span><span class="sh">' + short + '</span>' + m.group(3)[len('</span>'):] + h[m.end():]

    # ---------- 1b. request panel lives in a shared drawer under the cards ----------
    R('  function close(t){ var b = t.querySelector(".tbtn"); b.setAttribute("aria-expanded", "false"); t.querySelector(".rq").classList.remove("open"); }',
      '  function close(t){ var b = t.querySelector(".tbtn"); b.setAttribute("aria-expanded", "false"); (t._rq || t.querySelector(".rq")).classList.remove("open"); t.classList.remove("rqon"); }')
    R('    var ok = t.querySelector(".rqok"); f.hidden = true; ok.hidden = false;', '    var ok = (t._rq || t).querySelector(".rqok"); f.hidden = true; ok.hidden = false;')
    R('    requestAnimationFrame(function(){ t.querySelector(".rq").classList.add("open"); });', '    requestAnimationFrame(function(){ (t._rq || t.querySelector(".rq")).classList.add("open"); });')
    R('    var t = b.closest(".tier"), rq = t.querySelector(".rq"), f = t.querySelector("form");\n    if(window.KPICK) KPICK.init(f);',
      '    var t = b.closest(".tier"), rq = t.querySelector(".rq"), f = t.querySelector("form"); t._rq = rq; rq._tier = t;\n    if(window.KPICK) KPICK.init(f);')
    R('      b.setAttribute("aria-expanded", "true"); rq.classList.add("open");',
      '      b.setAttribute("aria-expanded", "true"); if(window.RQDRAWER) RQDRAWER(t, rq); rq.classList.add("open"); t.classList.add("rqon");')
    R('  function tierName(el){ var t = el.closest(".tier");', '  function tierName(el){ var rqx = el.closest(".rq"); var t = (rqx && rqx._tier) || el.closest(".tier");')
    R('document.addEventListener("submit", function(e){ if(e.target.closest(".tier")) track', 'document.addEventListener("submit", function(e){ if(e.target.closest(".tier,.rq")) track')

    # ---------- 3b. data-heavy cards start collapsed ----------
    R('var DD = {chart:true, runes:true, sb:true, boots:true, items:true, sp:true};', 'var DD = {chart:true, runes:true, sb:false, boots:false, items:true, sp:false};')

    # ---------- fixes ----------
    # a) count-up never sits on 0.00% for a second
    R('nums.forEach(function(n){ n.textContent = "0.00%"; });',
      'nums.forEach(function(n){ n.textContent = (parseFloat(n.dataset.v) * .5).toFixed(2) + "%"; });')
    R('delay = parseFloat(li.style.getPropertyValue("--i")) * 110 + parseFloat(li.style.getPropertyValue("--c")) * 220 + 300;',
      'delay = parseFloat(li.style.getPropertyValue("--i")) * 60 + parseFloat(li.style.getPropertyValue("--c")) * 120 + 60;')
    R('var q = Math.min(1, Math.max(0, (now - t0 - delay) / 1100)), e = 1 - Math.pow(1 - q, 3);\n          n.textContent = (parseFloat(n.dataset.v) * e).toFixed(2) + "%";',
      'var q = Math.min(1, Math.max(0, (now - t0 - delay) / 900)), e = 1 - Math.pow(1 - q, 3);\n          n.textContent = (parseFloat(n.dataset.v) * (.5 + .5 * e)).toFixed(2) + "%";')
    # b) one hero callout at a time: "My socials!" waits until the level pill was tried, or 12 s
    R('var bt = document.getElementById("brandtip"); if(bt) setTimeout(function(){ bt.classList.add("show"); }, still0 ? 0 : 2300);',
      'var bt = document.getElementById("brandtip"), lvEl = document.getElementById("level"), btShown = false;\n'
      '    function btShow(){ if(btShown || !bt) return; btShown = true; setTimeout(function(){ bt.classList.add("show"); }, 700); }\n'
      '    if(lvEl){ ["pointerenter", "focus", "click"].forEach(function(ev){ lvEl.addEventListener(ev, btShow, {once:true}); }); }\n'
      '    setTimeout(btShow, still0 ? 0 : 12000);')

    # ---------- styles + behaviour ----------
    CSS = r'''
    <style id="rd">
    /* --- 3. tighter rhythm --- */
    .hero{padding-bottom:110px}
    .hero::after{height:300px;background:linear-gradient(to bottom,rgba(11,18,38,0) 0%,rgba(11,18,38,.45) 45%,rgba(11,18,38,.85) 75%,var(--bg) 100%)}
    section{padding:56px 22px}
    .lead{margin-bottom:26px}
    @media (max-width:720px){.hero{padding-bottom:64px}.hero::after{height:200px}section{padding:44px 18px}nav{margin-bottom:22px}}

    /* --- 1. coaching cards --- */
    .tiers{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:6px}
    .tier.tc{display:flex;flex-direction:column;align-items:stretch;gap:0;padding:0;border:1px solid var(--line);border-radius:20px;overflow:hidden;background:linear-gradient(180deg,#16244A,#0F1A33);box-shadow:var(--drop);transition:transform .45s cubic-bezier(.22,1,.36,1),box-shadow .45s,border-color .3s}
    .tier.tc:last-of-type{border-bottom:1px solid var(--line)}
    .tier.tc:hover,.tier.tc.rqon{border-color:rgba(240,185,75,.7);box-shadow:0 24px 50px -22px rgba(0,0,0,.8),0 0 0 1px rgba(240,185,75,.35),0 0 40px -10px rgba(240,185,75,.35)}
    .tart{position:relative;width:100%;height:0;padding-top:75%;overflow:hidden;background:#16244A;margin-bottom:-1px}
    .tart img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 50%;display:block}
    .tart::before{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(180deg,rgba(240,185,75,.22),rgba(240,185,75,0) 70%);opacity:0;transition:opacity .5s ease;pointer-events:none}
    .tier.tc:hover .tart::before,.tier.tc.rqon .tart::before{opacity:1}
    .tart::after{content:"";position:absolute;inset:0 0 -2px;background:linear-gradient(180deg,rgba(11,18,38,0) 40%,rgba(15,26,51,.92) 100%)}
    .tkick{position:absolute;left:18px;bottom:14px;z-index:1;display:flex;align-items:center;gap:10px;font-size:.7rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);text-shadow:0 2px 6px rgba(0,0,0,.6)}
    .tpips{display:inline-flex;gap:4px}
    .tpips i{width:9px;height:9px;transform:rotate(45deg);border:1px solid var(--gold);background:transparent}
    .tpips i.on{background:var(--gold);box-shadow:0 0 8px rgba(240,185,75,.7)}
    .tbadge{position:absolute;top:14px;left:14px;z-index:1;padding:5px 11px;border-radius:99px;background:var(--gold);color:#0F1A33;font-size:.72rem;font-weight:800;letter-spacing:.04em;box-shadow:0 6px 18px rgba(0,0,0,.45)}
    .tier.tc[data-lv="11"]{border-color:rgba(240,185,75,.55)}
    .tbody{display:flex;flex-direction:column;gap:12px;padding:18px 20px 20px;flex:1}
    .tier.tc h3{font-size:1.35rem;font-weight:700;margin:0}
    .tier.tc .tbody>div:first-child p{margin:6px 0 0;font-size:.93rem;line-height:1.5;color:var(--muted);max-width:none}
    .tier.tc .price{display:flex;align-items:baseline;gap:8px;text-align:left;font-size:2rem;margin-top:auto}
    .tier.tc .price small{display:inline;font-size:.85rem}
    .tier.tc .btn.tbtn{grid-column:auto;justify-self:auto;width:100%;text-align:center;padding:13px 18px;border-radius:12px}
    .tier.tc .rq{grid-column:auto}
    /* the request form opens in a drawer under the row, the cards keep their place */
    .rqhost{grid-column:1/-1;position:relative;display:grid;grid-template-rows:0fr;margin-top:-18px;transition:grid-template-rows .6s cubic-bezier(.22,1,.36,1),margin .45s cubic-bezier(.22,1,.36,1)}
    .rqhost.open{grid-template-rows:1fr;margin-top:0}
    .rqhost>div{min-height:0;overflow:hidden}
    .rqhost .rq{display:block}
    .rqhost .rqi{padding:14px 2px 6px}
    .rqhost .rqf,.rqhost .rqok{margin-top:0;opacity:0;transform:translateY(8px);transition:opacity .35s ease,transform .45s cubic-bezier(.22,1,.36,1)}
    .rqhost.open .rqf,.rqhost.open .rqok{opacity:1;transform:none;transition-delay:.18s}
    .rqhost::before{content:"";position:absolute;left:var(--px,50%);top:6px;width:18px;height:18px;transform:translateX(-50%) rotate(45deg);border-left:2px solid var(--gold);border-top:2px solid var(--gold);background:var(--panel);opacity:0;transition:opacity .3s .25s,left .45s cubic-bezier(.22,1,.36,1);z-index:1}
    .rqhost.open::before{opacity:1}
    .tier.tc .tbody>.rq{display:none}
    @media (max-width:860px){.tiers{grid-template-columns:1fr 1fr}.tier.tc[data-lv="16"]{grid-column:1/-1}.tier.tc[data-lv="16"] .tart{padding-top:43.75%}.tier.tc[data-lv="16"] .tart img{object-position:50% 30%}.tier.tc[data-lv="16"] .tart img{object-position:50% 18%}}
    @media (max-width:620px){.tiers{grid-template-columns:1fr;gap:14px}.tier.tc .tart,.tier.tc[data-lv="16"] .tart{padding-top:50%}.tier.tc .tart img,.tier.tc[data-lv="16"] .tart img{object-position:50% 30%}}

    /* --- 2. mobile hero --- */
    .burger{display:none}
    .playbtn{display:none}
    .wdpill .sh{display:none}
    @media (max-width:720px){
      .hero .wrap{display:flex;flex-direction:column}
      .hero .wrap>nav{order:0}.hero .wrap>#top{order:1;margin-top:6px}.hero .wrap>h1+p{order:2;margin:14px 0 20px;font-size:1.08rem}.hero .wrap>.btns{order:3}
      .hero .wrap>.wdpill{order:4;margin:22px 0 0;align-self:flex-start;max-width:100%}
      .hero .wrap>.playbtn{order:5;margin-top:12px}.hero .wrap>.lvrow{order:6;margin-top:14px}
      .wdpill .lg{display:none}.wdpill .sh{display:inline}
      .wdpill{font-size:.86rem;padding:6px 14px 6px 6px}
      nav{flex-wrap:nowrap;gap:12px;margin-bottom:22px}
      nav ul#mainnav li.srli{padding:4px 6px 10px}
  nav ul#mainnav li.srli .srch{display:block;flex:none;width:100%;max-width:none;margin:0;order:0}
  nav ul#mainnav li.srli .srch input{width:100%}
  nav ul#mainnav li.srli .srk{display:none}
      .burger{display:grid;gap:5px;width:44px;height:44px;place-content:center;margin-left:auto;border:1px solid rgba(240,185,75,.55);border-radius:12px;background:rgba(11,18,38,.72);cursor:pointer;z-index:12}
      .burger i{display:block;width:20px;height:2px;border-radius:2px;background:var(--gold);transition:transform .3s,opacity .3s}
      .burger[aria-expanded="true"] i:nth-child(1){transform:translateY(7px) rotate(45deg)}.burger[aria-expanded="true"] i:nth-child(2){opacity:0}.burger[aria-expanded="true"] i:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
      nav ul#mainnav{position:absolute;top:calc(100% + 10px);left:0;right:0;z-index:11;flex-direction:column;gap:0;padding:8px;border-radius:16px;border:1px solid rgba(240,185,75,.4);background:rgba(11,18,38,.96);box-shadow:0 24px 50px -16px rgba(0,0,0,.9);opacity:0;transform:translateY(-8px);pointer-events:none;transition:opacity .25s,transform .3s cubic-bezier(.22,1,.36,1)}
      nav ul#mainnav.open{opacity:1;transform:none;pointer-events:auto}
      nav ul#mainnav li a{display:block;padding:13px 16px;border-radius:10px;font-size:1.05rem;font-weight:600;opacity:1}
      nav ul#mainnav li a:active{background:rgba(240,185,75,.15)}
      .playbtn{display:inline-flex;align-items:center;gap:10px;align-self:flex-start;padding:9px 16px 9px 12px;border-radius:99px;border:2px solid var(--gold);background:rgba(11,18,38,.62);color:var(--gold);font:inherit;font-weight:700;cursor:pointer}
      .playbtn svg{width:22px;height:22px}
      .playbtn small{font-weight:500;font-size:.78rem;color:var(--text);opacity:.85}
      .playbtn[aria-expanded="true"] small{display:none}
      .lvrow{display:none}
      .lvrow.show{display:flex}
      .lvwrap .lvtip{display:none}
    }

    /* --- 5. section moods --- */
    #coaching,#patch,#builds,#finder,#matchups,#videos,#merch{position:relative;isolation:isolate}
    #coaching::before,#patch::before,#matchups::before,#finder::before,#videos::before{content:"";position:absolute;inset:0;z-index:-1;pointer-events:none}
    #coaching::before{inset:auto;top:20px;right:-8%;width:min(820px,95vw);aspect-ratio:4/3;background:url(img/lv6.webp) center/cover no-repeat;opacity:.13;filter:grayscale(.35) saturate(1.1) brightness(.9);-webkit-mask-image:radial-gradient(closest-side,#000 25%,rgba(0,0,0,.6) 50%,transparent 74%);mask-image:radial-gradient(closest-side,#000 25%,rgba(0,0,0,.6) 50%,transparent 74%)}
    #patch::before{background:repeating-linear-gradient(180deg,transparent 0 34px,rgba(240,185,75,.055) 34px 35px),linear-gradient(90deg,rgba(255,122,122,.0),rgba(240,185,75,.06) 1px,transparent 1px) 72px 0/100% 100% no-repeat;-webkit-mask-image:linear-gradient(180deg,transparent,#000 12%,#000 88%,transparent);mask-image:linear-gradient(180deg,transparent,#000 12%,#000 88%,transparent);opacity:.9}
    #matchups::before{background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 800'><g fill='none' stroke='%23F0B94B' stroke-width='3' opacity='.55'><path d='M80 740 L1120 60'/><path d='M80 740 Q200 380 600 380 T1120 60' stroke-dasharray='10 14' opacity='.6'/><path d='M80 740 L80 60 L1120 60 L1120 740 Z' opacity='.4'/><circle cx='80' cy='740' r='54'/><circle cx='1120' cy='60' r='54'/><circle cx='600' cy='400' r='34' stroke-dasharray='6 8'/></g></svg>") center/min(1100px,100%) auto no-repeat;opacity:.11}
    #finder::before{background:radial-gradient(circle at 20% 30%,rgba(240,185,75,.14),transparent 40%),radial-gradient(circle at 80% 70%,rgba(74,222,128,.08),transparent 40%)}
    #videos::before{background:repeating-linear-gradient(90deg,rgba(255,255,255,.035) 0 2px,transparent 2px 46px);-webkit-mask-image:linear-gradient(180deg,#000,transparent 70%);mask-image:linear-gradient(180deg,#000,transparent 70%)}
    @media (max-width:720px){#coaching::before{width:120vw;right:-40%;top:0;opacity:.1}}

    /* --- 6. motion polish --- */
    .bsbcard,.mucard,.video,.gcard,.scard,.mcard{transition:transform .4s cubic-bezier(.22,1,.36,1),box-shadow .4s,border-color .3s}
    .bsbcard:hover,.mucard:hover,.gcard:hover,.scard:hover{transform:translateY(-4px);box-shadow:0 22px 44px -20px rgba(0,0,0,.85),0 0 0 1px rgba(240,185,75,.22)}
    .video:hover{transform:translateY(-5px) scale(1.01)}
    @media (prefers-reduced-motion:reduce){.tier.tc,.bsbcard,.mucard,.video,.gcard,.scard,.mcard,.tart img{transition:none!important}.tier.tc:hover,.bsbcard:hover,.mucard:hover,.video:hover,.gcard:hover,.scard:hover{transform:none}}
    @media (hover:none){.tier.tc:hover,.bsbcard:hover,.mucard:hover,.video:hover,.gcard:hover,.scard:hover{transform:none}}
    </style>
    <script>
    (function(){
      var bg = document.getElementById("burger"), ul = document.getElementById("mainnav");
      if(bg && ul){
        function set(o){ ul.classList.toggle("open", o); bg.setAttribute("aria-expanded", o ? "true" : "false"); }
        bg.addEventListener("click", function(){ set(!ul.classList.contains("open")); });
        ul.addEventListener("click", function(e){ if(e.target.closest("a")) set(false); });
        document.addEventListener("pointerdown", function(e){ if(ul.classList.contains("open") && !ul.contains(e.target) && !bg.contains(e.target)) set(false); });
        document.addEventListener("keydown", function(e){ if(e.key === "Escape") set(false); });
      }
      // phone: the search box moves into the menu
  var srf = document.getElementById("srch"), srHome = srf && srf.parentNode, srNext = srf && srf.nextSibling, mq = window.matchMedia("(max-width:720px)");
  function placeSearch(){ if(!srf || !ul) return; if(mq.matches){ var li = ul.querySelector("li.srli"); if(!li){ li = document.createElement("li"); li.className = "srli"; ul.insertBefore(li, ul.firstChild); } if(srf.parentNode !== li) li.appendChild(srf); } else if(srf.parentNode !== srHome){ srHome.insertBefore(srf, srNext); var li2 = ul.querySelector("li.srli"); if(li2) li2.remove(); } }
  placeSearch(); if(mq.addEventListener) mq.addEventListener("change", placeSearch); else mq.addListener(placeSearch);
  var pb = document.getElementById("playbtn"), lr = document.getElementById("lvrow");
      if(pb && lr){ pb.addEventListener("click", function(){ var o = !lr.classList.contains("show"); lr.classList.toggle("show", o); pb.setAttribute("aria-expanded", o ? "true" : "false"); if(o){ var lv = document.getElementById("level"); if(lv) lv.classList.remove("idle"); } }); }
      // request drawer: one shared panel under the three cards
      var tiersEl = document.querySelector(".tiers");
      if(tiersEl){
        var host = document.createElement("div"); host.className = "rqhost"; var hostIn = document.createElement("div"); host.appendChild(hostIn); tiersEl.appendChild(host);
        function place(t){ var tr = t.getBoundingClientRect(), hr = host.getBoundingClientRect(); host.style.setProperty("--px", Math.round(tr.left - hr.left + tr.width / 2) + "px"); }
        window.RQDRAWER = function(t, rq){
          var cur = hostIn.firstElementChild;
          if(cur && cur !== rq){ cur.classList.remove("open"); if(cur._tier){ cur._tier.classList.remove("rqon"); cur._tier.querySelector(".tbody").appendChild(cur); } }
          if(cur !== rq) hostIn.appendChild(rq);
          place(t); host.classList.add("open");
        };
        new MutationObserver(function(){ var rq = hostIn.firstElementChild; var open = rq && rq.classList.contains("open"); host.classList.toggle("open", !!open); if(open && rq._tier) place(rq._tier); }).observe(hostIn, {attributes:true, subtree:true, attributeFilter:["class"], childList:true});
        window.addEventListener("resize", function(){ var rq = hostIn.firstElementChild; if(rq && rq._tier) place(rq._tier); });
      }
      // the open drawer scrolls into view once it has grown
      document.querySelectorAll(".tier.tc .tbtn").forEach(function(b){ b.addEventListener("click", function(){ setTimeout(function(){ if(b.getAttribute("aria-expanded") === "true"){ var h = document.querySelector(".rqhost"); if(h){ var r = h.getBoundingClientRect(); if(r.bottom > innerHeight - 40 || r.top < 0) h.scrollIntoView({behavior:"smooth", block:"nearest"}); } } }, 500); }); });
    })();
    </script>
    '''
    if preview:
        CSS += '<div style="position:fixed;left:14px;bottom:14px;z-index:2147482000;padding:6px 12px;border-radius:99px;background:linear-gradient(90deg,#0AC8B9,#0397AB);color:#012;font:600 .76rem Poppins,system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.4)">Preview · redesign · not live</div>\n'
    i = h.rindex("</body>")
    h = h[:i] + CSS + h[i:]
    return h


if __name__ == "__main__":
    out_h = apply(open(sys.argv[1], encoding="utf-8").read(), "--preview" in sys.argv)
    open(sys.argv[2], "w", encoding="utf-8").write(out_h)
    print("ok", len(out_h))
