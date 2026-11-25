#!/usr/bin/env python3
"""Featured "Build of the week" card at the top of the builds section of kayle1v9.com.

The card is written into the "Build of the day" box (#botd) on every build, so the nightly sync from the
artifact keeps it even though the artifact itself does not have it. Outside its date window the page shows
the normal automatic "Build of the day" again, nothing has to be switched off by hand.

Current card: 25 Nov - 2 Dec 2026 (Europe/Berlin), Rageblade Kayle mid from the video d1s4k1MENgo.
Source of the build: the EUW Master Kayle one-trick shown in the video (onetricks.gg, checked 25 Nov 2026):
Doran's Blade start, Berserker's Greaves, Guinsoo's Rageblade > Nashor's Tooth > Rabadon's Deathcap > Lich Bane,
Lethal Tempo / Triumph / Legend: Alacrity / Last Stand + Celerity / Gathering Storm, shards attack speed,
move speed, health, Flash + Exhaust, skills E-Q-W at levels 1-3, max order Q > E > W.

For a new card: change CARD below (and the texts in I18N), then run  python3 botw.py index.html
make_site.py calls add_translations() and apply() on every build.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
START, END = '/*BOTW:start*/', '/*BOTW:end*/'

CARD = {
    "from": "2026-11-25", "to": "2026-12-02",          # shown on these days (Berlin time), both included
    "video": "d1s4k1MENgo",
    "title": "Rageblade Kayle Mid",
    "sub": "Guinsoo's Rageblade first with Lethal Tempo and Exhaust · the build of an EUW Master one-trick with a 54% win rate over 900 games",
    "items": [3006, 3124, 3115, 3089, 3100],           # Berserker's Greaves, Guinsoo's Rageblade, Nashor's Tooth, Rabadon's Deathcap, Lich Bane
    "pri": ["Precision", 8008, [9111, 9104, 8299]],    # Lethal Tempo; Triumph, Legend: Alacrity, Last Stand
    "sec": ["Sorcery", [8234, 8236]],                  # Celerity, Gathering Storm
    "shards": [[5005, "Attack Speed"], [5010, "Move Speed"], [5011, "Health"]],
    "spells": [4, 3],                                  # Flash, Exhaust
    "start": [1055, 2003],                             # Doran's Blade, Health Potion
    "skills": ["Q", "E", "W"],
    "skillnote": "Start E, then Q, then W",
    "lane": "mid", "region": "eu", "button": "Open EU builds",   # the button switches the builds below to this lane and server
}

YT_SVG = ('<svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true" style="vertical-align:-2px;margin-right:5px">'
          '<path d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .6 12a31 31 0 0 0 .4 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .4-4.8 31 31 0 0 0-.4-4.8zM9.8 15.3V8.7l6 3.3z"/></svg>')


def _eu_flag():
    import math
    star = 'M0,-1L0.588,0.809L-0.951,-0.309L0.951,-0.309L-0.588,0.809Z'
    stars = ''.join('<path d="%s" transform="translate(%.2f,%.2f) scale(1.05)"/>' % (star, 15 + 6.3 * math.sin(math.radians(a)), 10 - 6.3 * math.cos(math.radians(a)))
                    for a in range(0, 360, 30))
    return '<svg class="cnflag" viewBox="0 0 30 20" aria-hidden="true"><rect width="30" height="20" fill="#003399"/><g fill="#FFCC00">%s</g></svg>' % stars


JS = r"""
      __START__
      // Build of the week __FROM__ to __TO__ (Europe/Berlin): __TITLE__. Written by botw.py on every build, see there.
      var rbDay = ""; try{ rbDay = new Date().toLocaleDateString("sv-SE", {timeZone: "Europe/Berlin"}); }catch(e){}
      var RB = __CFG__;
      if(box && rbDay >= RB.from && rbDay <= RB.to && RB.items.concat(RB.start).every(function(id){ return ITI[id]; })){
        var rInner = el("div", ""), rTag = el("span", "dtag", "Build of the week · Featured"), rT = el("div", "bt");
        var rB = el("b", "", RB.title); rB.appendChild(el("span", "bnew", "NEW")); rT.appendChild(rB);
        rT.appendChild(el("span", "", RB.sub));
        var rYt = el("a", "bsrc byt"); rYt.target = "_blank"; rYt.rel = "noopener"; rYt.href = "https://www.youtube.com/watch?v=" + RB.video;
        rYt.innerHTML = '__YT__I tested it: watch the video'; rT.appendChild(rYt);
        var rIc = el("div", "bi");
        RB.items.forEach(function(id, i){ if(i) rIc.appendChild(el("span", "barr", "›")); rIc.appendChild(sbIcon(id, false)); });
        // runes, shards, summoner spells, start and skill order of the build
        var rX = el("div", "bxtra");
        var rChip = function(img, name, cls){ var c = el("span", "bxchip" + (cls ? " " + cls : "")); if(img) c.appendChild(img); c.appendChild(el("span", "", name)); return c; };
        var rGrp = function(title, cls){ var g = el("div", "bxgrp" + (cls ? " " + cls : "")); g.appendChild(el("span", "bxh", title)); var r = el("div", "bxrow"); g.appendChild(r); rX.appendChild(g); return r; };
        var rItem = function(id){ var im = sbIcon(id, true); im.width = im.height = 28; im.className = ""; im.style.borderRadius = "7px"; return im; };
        var rSpell = function(id){ var im = new Image(); im.width = im.height = 28; im.alt = SPN[id] || ""; im.decoding = "async"; im.src = SPI[id] || GIF; return rChip(im, SPN[id] || ""); };
        var rP = rGrp(RB.pri[0], "pri");
        rP.appendChild(rChip(runeIcon(RB.pri[1], 40), RN[RB.pri[1]] || "", "key"));
        RB.pri[2].forEach(function(id){ rP.appendChild(rChip(runeIcon(id, 28), RN[id] || "")); });
        var rS = rGrp(RB.sec[0], "sec");
        RB.sec[1].forEach(function(id){ rS.appendChild(rChip(runeIcon(id, 28), RN[id] || "")); });
        var rH = rGrp("Shards", "sha");
        RB.shards.forEach(function(s){ var im = runeIcon(s[0], 22); im.alt = im.title = s[1]; rH.appendChild(rChip(im, s[1])); });
        var rSp = rGrp("Summoner spells", "spl");
        RB.spells.forEach(function(id){ rSp.appendChild(rSpell(id)); });
        var rSt = rGrp("Starting items", "spl");
        RB.start.forEach(function(id){ rSt.appendChild(rChip(rItem(id), ITN[id] || "")); });
        var rK = rGrp("Skill order", "sko");
        RB.skills.forEach(function(k, i){ if(i) rK.appendChild(el("span", "barr", "›")); rK.appendChild(el("span", "bxkey", k)); });
        var rR = el("span", "bxult"); rR.appendChild(el("span", "bxkey r", "R")); rR.appendChild(el("span", "", "at 6 · 11 · 16")); rK.appendChild(rR);
        if(RB.skillnote) rK.appendChild(el("span", "bxnote", RB.skillnote));
        var rGo = el("button", "bgo bcnf"); rGo.type = "button";
        rGo.innerHTML = '__FLAG__<span></span>'; rGo.lastChild.textContent = RB.button;
        rGo.addEventListener("click", function(){
          var lb = document.querySelector('#builds .lnb[data-l="' + RB.lane + '"]'); if(lb && !lb.classList.contains("on")) lb.click();
          var tb = document.querySelector('.btab[data-r="' + RB.region + '"]'); if(tb) tb.click();
          var pn = document.getElementById("bpanel"); if(pn) pn.scrollIntoView({behavior: "smooth", block: "start"});
        });
        rInner.appendChild(rTag); rInner.appendChild(rT); box.innerHTML = ""; box.appendChild(rInner); box.appendChild(rIc); box.appendChild(rGo); box.appendChild(rX); box.hidden = false;
        box.classList.add("hot");
        [[6,12,0],[38,8,.9],[71,18,1.7],[90,70,.4],[55,85,1.3],[18,78,2.1]].forEach(function(s){ var sp = el("span", "spk"); sp.style.left = s[0] + "%"; sp.style.top = s[1] + "%"; sp.style.animationDelay = s[2] + "s"; box.appendChild(sp); });
        Array.prototype.forEach.call(rIc.querySelectorAll("img"), function(im, i){ im.style.animationDelay = (i * 0.12) + "s, " + (0.6 + i * 0.25) + "s"; });
        return;
      }
      __END__
"""

# Where the block goes: inside the "Build of the day" function, before the older featured cards. If the first
# anchor is gone from the artifact one day, the start of the automatic pick is used instead.
ANCHORS = ['      // Build of the week 10-17 Nov 2026: Korean Aery Kayle',
           '      var pick = function(min){ return slugs.filter(function(k){ var c = L[k].iw']

# Translations of the card texts. Numbers and game names (items, runes, spells) are placeholders, see i18n.py.
I18N = {
    "Rageblade Kayle Mid": {
        "de": "Rageblade-Kayle Mid", "es": "Kayle Rageblade mid", "pt": "Kayle Rageblade mid", "fr": "Kayle Rageblade mid",
        "tr": "Rageblade Kayle Mid", "ko": "Rageblade 미드 케일", "zh": "Rageblade 中单凯尔", "ja": "Rageblade ミッドケイル", "ru": "Rageblade Кейл на миде"},
    "{p0} first with {p1} and {p2} · the build of an EUW Master one-trick with a {n0} win rate over {n1} games": {
        "de": "{p0} zuerst, mit {p1} und {p2} · der Build eines EUW-Master-Onetricks mit {n0} Winrate über {n1} Spiele",
        "es": "{p0} primero, con {p1} y {p2} · la build de un one-trick Master de EUW con {n0} de winrate en {n1} partidas",
        "pt": "{p0} primeiro, com {p1} e {p2} · a build de um one-trick Master do EUW com {n0} de winrate em {n1} partidas",
        "fr": "{p0} en premier, avec {p1} et {p2} · le build d'un one-trick Master EUW avec {n0} de winrate sur {n1} parties",
        "tr": "Önce {p0}, {p1} ve {p2} ile · {n1} maçta {n0} winrate'li bir EUW Master one-trick'in buildi",
        "ko": "{p0} 선템에 {p1}, {p2} · {n1}판 승률 {n0}의 EUW 마스터 원챔 빌드",
        "zh": "先出 {p0}，搭配 {p1} 和 {p2} · 欧服大师专精玩家的出装，{n1} 场胜率 {n0}",
        "ja": "{p0}を最初に、{p1}と{p2} · {n1}試合で勝率{n0}のEUWマスターOTPのビルド",
        "ru": "Сначала {p0}, с {p1} и {p2} · сборка мастера-уантрика с EUW с винрейтом {n0} за {n1} игр"},
    "Start E, then Q, then W": {
        "de": "Erst E, dann Q, dann W", "es": "Empieza con E, luego Q, luego W", "pt": "Comece com E, depois Q, depois W",
        "fr": "Commence par E, puis Q, puis W", "tr": "Önce E, sonra Q, sonra W", "ko": "E 먼저, 다음 Q, 그다음 W",
        "zh": "先 E，再 Q，然后 W", "ja": "E→Q→Wの順に取る", "ru": "Сначала E, потом Q, потом W"},
    "Open EU builds": {
        "de": "EU-Builds öffnen", "es": "Abrir builds de EU", "pt": "Abrir builds da EU", "fr": "Ouvrir les builds EU",
        "tr": "EU buildlerini aç", "ko": "유럽 빌드 열기", "zh": "打开欧服出装", "ja": "EUビルドを開く", "ru": "Открыть сборки EU"},
}


def strip(html):
    return re.sub(r'\n?[ \t]*' + re.escape(START) + r'.*?' + re.escape(END) + r'[ \t]*\n?', '\n', html, flags=re.S) if START in html else html


def apply(html, card=None):
    card = CARD if card is None else card
    html = strip(html)
    if not card:
        return html
    block = (JS.replace('__CFG__', json.dumps(card, ensure_ascii=False, separators=(',', ':')))
               .replace('__FROM__', card['from']).replace('__TO__', card['to']).replace('__TITLE__', card['title'])
               .replace('__YT__', YT_SVG).replace('__FLAG__', _eu_flag())
               .replace('__START__', START).replace('__END__', END)).strip('\n') + '\n'
    for a in ANCHORS:
        if html.count(a) == 1:
            return html.replace(a, block + a, 1)
    print('botw: no anchor found, card skipped')
    return html


def add_translations(repo=HERE):
    """Write the card texts into i18n/<code>.json. Returns True when a file changed."""
    changed = False
    for code in sorted({c for v in I18N.values() for c in v}):
        p = os.path.join(repo, 'i18n', code + '.json')
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        new = {k: v[code] for k, v in I18N.items() if code in v and d.get(k) != v[code]}
        if new:
            d.update(new)
            open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=0) + '\n')
            changed = True
    return changed


if __name__ == '__main__':
    import hashlib
    sys.path.insert(0, HERE)
    import i18n
    path = sys.argv[1]
    s = open(path, encoding='utf-8').read()
    add_translations()
    # the page fetches i18n/<code>.json?v=<hash of all dictionaries>: bring the hash in the page in step with the files
    new = hashlib.sha1(json.dumps(i18n.load(HERE), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]
    for old in sorted(set(re.findall(r'\.json\?v=([0-9a-f]{10})', s))):
        if old != new:
            print('i18n version', old, '->', new, 'replaced', s.count(old))
            s = s.replace(old, new)
    s = apply(s)
    open(path, 'w', encoding='utf-8').write(s)
    print('botw:', 'card written' if START in s else 'no card', '| index.html', len(s))
