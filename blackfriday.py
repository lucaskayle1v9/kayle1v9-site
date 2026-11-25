#!/usr/bin/env python3
"""Black Friday coaching offer for kayle1v9.com (25 Nov - 1 Dec 2026).

Everything is driven by blackfriday.json next to this file:
  enabled     false = nothing is added to the page
  ends        the offer switches itself off at this moment (visitors see normal prices again, no rebuild needed)
  total/left  spots in the offer and how many are still free (edit "left" by hand after each booking; 0 = offer off)
  prices      normal price in EUR -> Black Friday price in EUR
  paypal/wise payment links by Black Friday price. A level only shows its reduced price when it has at least one link.

While the offer runs the page gets: a pill in the hero, a banner with countdown and free spots above the coaching
cards, and the reduced price (old price struck through) on each card. The booking form picks the payment link by
the price shown on the card, so the reduced price also selects the right link.

make_site.py calls apply() on every build, so the nightly sync from the artifact keeps the offer.
Standalone (patch the built page in place, also refreshes the i18n version):  python3 blackfriday.py index.html
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
START, END = '<!--BF:start-->', '<!--BF:end-->'

CSS = r"""
.bfpill{display:flex;width:max-content;max-width:100%;margin-bottom:10px}
.bfc{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:16px 28px;margin:0 0 18px;padding:18px 22px;border:1px solid rgba(240,185,75,.6);border-radius:18px;background:linear-gradient(135deg,rgba(240,185,75,.2),rgba(240,185,75,0) 62%),var(--panel);box-shadow:0 14px 34px rgba(3,7,18,.55),inset 0 1px 0 rgba(255,255,255,.1)}
.bfc .bfk{display:block;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.bfc h3{margin:4px 0 0;font-size:1.6rem;font-weight:800;line-height:1.15}
.bfc>div:first-child{flex:1 1 320px;min-width:0}
.bfc p{margin:6px 0 0;color:var(--muted);font-size:.93rem;line-height:1.45}
.bfc .bfs{display:flex;gap:12px}
.bfc .bfb{min-width:132px;padding:10px 14px;border:1px solid var(--line);border-radius:14px;background:rgba(11,18,38,.6);text-align:center}
.bfc .bfb span{display:block;font-size:.68rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.bfc .bfb b{display:block;margin-top:2px;font-size:1.25rem;font-weight:800;color:var(--gold);white-space:nowrap;font-variant-numeric:tabular-nums}
.tier.bfon .price{color:var(--gold)}
.tier.bfon .price s.bfold{font-size:.55em;font-weight:600;color:var(--muted);margin-left:.45em}
@media (max-width:620px){.bfc{padding:16px}.bfc .bfs{width:100%}.bfc .bfb{flex:1;min-width:0}.bfc h3{font-size:1.35rem}}
"""

JS = r"""
(function(){
  var BF = __CFG__;
  var end = Date.parse(BF.ends);
  if(!BF.enabled || !(BF.left > 0) || !(Date.now() < end)) return;
  function el(tag, cls, text){ var e = document.createElement(tag); if(cls) e.className = cls; if(text != null) e.textContent = text; return e; }
  function start(){
    var C = window.CONFIG, sec = document.getElementById("coaching");
    if(!C || !sec) return;
    C.paypalLinks = C.paypalLinks || {}; C.wiseLinks = C.wiseLinks || {};
    var on = 0;
    [].forEach.call(sec.querySelectorAll(".tier"), function(t){
      var pe = t.querySelector(".price"); if(!pe || !pe.firstChild) return;
      var old = Math.round(parseFloat((pe.firstChild.textContent || "").replace(/[^0-9.]/g, ""))), nw = BF.prices[old];
      if(!nw) return;
      var pp = BF.paypal[nw], ws = BF.wise[nw];
      if(!pp && !ws) return;                                  // no payment link yet: this level keeps its normal price
      if(pp) C.paypalLinks[nw] = pp;
      if(ws) C.wiseLinks[nw] = ws;
      pe.firstChild.textContent = "€" + nw;              // the booking form reads the price from this text node
      var s = el("s", "bfold", "€" + old); s.setAttribute("data-noi18n", "");
      pe.insertBefore(s, pe.firstChild.nextSibling);
      t.classList.add("bfon"); on++;
    });
    if(!on) return;

    var pill = document.querySelector(".hero .wdpill"), pct = BF.percent + "%";
    if(pill){
      var a = el("a", "wdpill bfpill"); a.href = "#coaching";
      a.appendChild(el("b", "", "Black Friday"));
      a.appendChild(el("span", "lg", pct + " off all coaching until Dec " + BF.until_day));
      a.appendChild(el("span", "sh", pct + " off coaching"));
      var i = el("i", "", "→"); i.setAttribute("aria-hidden", "true"); a.appendChild(i);
      pill.parentNode.insertBefore(a, pill);
    }

    var c = el("div", "bfc"), l = el("div"), r = el("div", "bfs");
    l.appendChild(el("span", "bfk", "Black Friday"));
    l.appendChild(el("h3", "", pct + " off all coaching"));
    l.appendChild(el("p", "", "Book and pay by Dec " + BF.until_day + ". Your session can take place any time until Jan " + BF.redeem_day + "."));
    var b1 = el("div", "bfb"); b1.appendChild(el("span", "", "Ends in")); var cd = el("b"); cd.setAttribute("data-noi18n", ""); b1.appendChild(cd);
    var b2 = el("div", "bfb"); b2.appendChild(el("span", "", "Spots left"));
    var dots = el("b"); dots.setAttribute("data-noi18n", ""); dots.textContent = BF.left + " / " + BF.total; b2.appendChild(dots);
    r.appendChild(b1); r.appendChild(b2); c.appendChild(l); c.appendChild(r);
    var anchor = document.getElementById("cq") || sec.querySelector(".tiers");
    anchor.parentNode.insertBefore(c, anchor);

    function tick(){
      var ms = end - Date.now();
      if(ms <= 0){ location.reload(); return; }
      var m = Math.floor(ms / 60000), d = Math.floor(m / 1440), h = Math.floor(m % 1440 / 60);
      cd.textContent = d > 0 ? d + "d " + h + "h " + (m % 60) + "m" : h + "h " + (m % 60) + "m";
    }
    tick(); setInterval(tick, 20000);
  }
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
"""

# Translations of the offer texts (numbers are placeholders, see i18n.py). "Black Friday" stays as it is.
I18N = {
    "{n0} off all coaching until Dec {n1}": {
        "de": "{n0} auf jedes Coaching bis {n1}. Dez.", "es": "{n0} de descuento en todo el coaching hasta el {n1} de dic",
        "pt": "{n0} de desconto em todo o coaching até {n1} de dez", "fr": "{n0} de réduction sur tout le coaching jusqu'au {n1} déc.",
        "tr": "{n1} Aralık'a kadar tüm koçluklarda {n0} indirim", "ko": "12월 {n1}일까지 모든 코칭 {n0} 할인",
        "zh": "12月{n1}日前所有教练课程优惠{n0}", "ja": "12月{n1}日まで全コーチング{n0}オフ", "ru": "Скидка {n0} на весь коучинг до {n1} дек."},
    "{n0} off coaching": {
        "de": "{n0} auf Coaching", "es": "{n0} de descuento en coaching", "pt": "{n0} de desconto no coaching",
        "fr": "{n0} de réduction sur le coaching", "tr": "Koçlukta {n0} indirim", "ko": "코칭 {n0} 할인",
        "zh": "教练课程优惠{n0}", "ja": "コーチング{n0}オフ", "ru": "Скидка {n0} на коучинг"},
    "{n0} off all coaching": {
        "de": "{n0} auf jedes Coaching", "es": "{n0} de descuento en todo el coaching", "pt": "{n0} de desconto em todo o coaching",
        "fr": "{n0} de réduction sur tout le coaching", "tr": "Tüm koçluklarda {n0} indirim", "ko": "모든 코칭 {n0} 할인",
        "zh": "所有教练课程优惠{n0}", "ja": "全コーチング{n0}オフ", "ru": "Скидка {n0} на весь коучинг"},
    "Book and pay by Dec {n0}. Your session can take place any time until Jan {n1}.": {
        "de": "Buch und bezahl bis zum {n0}. Dez. Deine Session kann jederzeit bis zum {n1}. Jan. stattfinden.",
        "es": "Reserva y paga antes del {n0} de dic. Tu sesión puede ser cualquier día hasta el {n1} de ene.",
        "pt": "Reserve e pague até {n0} de dez. Sua sessão pode acontecer a qualquer momento até {n1} de jan.",
        "fr": "Réserve et paie avant le {n0} déc. Ta session peut avoir lieu à tout moment jusqu'au {n1} janv.",
        "tr": "{n0} Aralık'a kadar rezervasyon yap ve öde. Seansın {n1} Ocak'a kadar istediğin zaman olabilir.",
        "ko": "12월 {n0}일까지 예약하고 결제하세요. 세션은 1월 {n1}일까지 언제든 진행할 수 있습니다.",
        "zh": "请在12月{n0}日前预约并付款。课程可在1月{n1}日前任意时间进行。",
        "ja": "12月{n0}日までに予約と支払いを。セッションは1月{n1}日までいつでも受けられます。",
        "ru": "Забронируй и оплати до {n0} дек. Сессию можно провести в любое время до {n1} янв."},
    "Ends in": {"de": "Endet in", "es": "Termina en", "pt": "Termina em", "fr": "Se termine dans", "tr": "Kalan süre",
                "ko": "남은 시간", "zh": "剩余时间", "ja": "終了まで", "ru": "До конца"},
    "Spots left": {"de": "Freie Plätze", "es": "Plazas libres", "pt": "Vagas livres", "fr": "Places restantes", "tr": "Kalan yer",
                   "ko": "남은 자리", "zh": "剩余名额", "ja": "残り枠", "ru": "Осталось мест"},
}


def config():
    p = os.path.join(HERE, 'blackfriday.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {"enabled": False}


def strip(html):
    return re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', '', html, flags=re.S)


def apply(html, cfg=None):
    cfg = config() if cfg is None else cfg
    html = strip(html)
    if not cfg.get('enabled'):
        return html
    block = START + '<style>' + CSS + '</style>\n<script>' + JS.replace('__CFG__', json.dumps(cfg, separators=(',', ':'))) + '</script>' + END + '\n'
    i = html.rfind('</body>')
    assert i > 0
    return html[:i] + block + html[i:]


def add_translations(repo=HERE):
    """Write the offer texts into i18n/<code>.json. Returns True when a file changed."""
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
    old = hashlib.sha1(json.dumps(i18n.load(HERE), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]
    add_translations()
    new = hashlib.sha1(json.dumps(i18n.load(HERE), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:10]
    if old != new:
        print('i18n version', old, '->', new, 'replaced', s.count(old))
        s = s.replace(old, new)
    s = apply(s)
    open(path, 'w', encoding='utf-8').write(s)
    print('black friday:', 'on' if config().get('enabled') else 'off', '| index.html', len(s))
