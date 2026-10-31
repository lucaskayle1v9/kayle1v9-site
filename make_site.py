#!/usr/bin/env python3
"""Turn the published artifact HTML into a standalone index.html for kayle1v9.com.
usage: make_site.py <artifact-html> <out-dir>"""
import re, sys, os
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
i = s.find('<!DOCTYPE html>')
if i > 0 and s[:i].lower().startswith('<!doctype html><html><head>'):
    s = s[i:]
s = re.sub(r'\s*</body></html>\s*$', '\n', s) if s.count('</html>') > 1 else s
site = 'https://kayle1v9.com/'
extra = ('<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">\n'
         '<meta property="og:image" content="%sog-image.png">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
         '<meta property="og:image:alt" content="Kayle 1v9: Kayle coaching, live builds and minigames">\n<meta name="twitter:image" content="%sog-image.png">\n'
         '<meta property="og:site_name" content="Kayle 1v9">\n<link rel="icon" href="favicon.png" type="image/png">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">\n') % (site, site, site, site)
s = s.replace('<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:card" content="summary_large_image">\n' + extra, 1)
assert 'og-image.png' in s, 'meta anchor not found'

# --- Booked coaching slots -----------------------------------------------------------------------
# bookings.json (next to this script) lists booked sessions in Berlin time: [["YYYY-MM-DD", "HH:MM", minutes], ...].
# They are written into the booking form on every build, so the nightly sync from the artifact keeps them
# even when the artifact itself does not have them. The form greys out each booking and the hour before it.
import json
_bk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookings.json')
_bk = json.load(open(_bk_path)) if os.path.exists(_bk_path) else []
_bk_js = json.dumps(_bk, separators=(', ', ': '))
_av_plain = 'var AV = {tz:"Europe/Berlin", from:11, last:23, step:30, days:14, lead:12};'
if _av_plain in s:
    s = s.replace(_av_plain, 'var AV = {tz:"Europe/Berlin", from:11, last:23, step:30, days:14, lead:12,\n  booked:%s};  // booked sessions in Berlin time: [day, start, minutes]; their slots show greyed out as "booked"' % _bk_js, 1)
else:
    s, _n = re.subn(r'(var AV = \{[^\n]*lead:12,\n  booked:)\[.*?\](\};)', lambda m: m.group(1) + _bk_js + m.group(2), s, count=1)
    assert _n == 1, 'booking config not found'
if 'function isBooked(t)' not in s:
    _k = '  function key(ms){ var d = new Date(ms);'
    assert s.count(_k) == 1, 'booking anchor key() not found'
    s = s.replace(_k, (
        '  function isBooked(t){\n'
        '    return (AV.booked || []).some(function(b){\n'
        '      var d = b[0].split("-"), hm = b[1].split(":"), s = wall(+d[0], +d[1] - 1, +d[2], +hm[0], +hm[1]);\n'
        '      return t >= s - 60 * 60000 && t < s + (b[2] || 60) * 60000;  // also the hour before, so no new session runs into a booked one\n'
        '    });\n'
        '  }\n') + _k, 1)
    _f = '        g.forEach(function(t){ opt(ssel, String(t), timeLbl(t)); });'
    assert s.count(_f) == 1, 'booking anchor fillSlots not found'
    s = s.replace(_f, (
        '        g.forEach(function(t){\n'
        '          if(isBooked(t)){ var o = document.createElement("option"); o.value = ""; o.disabled = true; o.className = "booked"; o.textContent = timeLbl(t) + " \\u00b7 booked"; ssel.appendChild(o); }\n'
        '          else opt(ssel, String(t), timeLbl(t));\n'
        '        });'), 1)
os.makedirs(out, exist_ok=True)

# --- Move big inline images (jpeg/webp/png data URIs) into files under a/ -------------------------
# The artifact keeps every image inline (one file). For the real site the big ones become separate,
# cacheable files with content-hash names, so the HTML is much smaller and parses faster.
# Audio (read with atob() by the page) and small icons stay inline.
import hashlib, base64
MIN_CHARS = 4000
adir = os.path.join(out, 'a')
os.makedirs(adir, exist_ok=True)
for old_f in os.listdir(adir):
    os.remove(os.path.join(adir, old_f))
files = {}  # name -> position of first use (so we can tell hero images from the rest)
def _extract(m):
    kind, b64 = m.group(1), m.group(2)
    if len(m.group(0)) < MIN_CHARS:
        return m.group(0)
    raw = base64.b64decode(b64)
    name = hashlib.sha1(raw).hexdigest()[:12] + ('.jpg' if kind == 'jpeg' else '.' + kind)
    path = os.path.join(adir, name)
    if not os.path.exists(path):
        open(path, 'wb').write(raw)
    files.setdefault(name, m.start())
    return 'a/' + name
s = re.sub(r'data:image/(jpeg|webp|png);base64,([A-Za-z0-9+/=]+)', _extract, s)
# Preload the images the first screen needs (hero background in the CSS and images inside <header class="hero">)
hero_end = s.find('</header>')
hero_start = s.find('<header class="hero"')
first = []
for m in re.finditer(r'<style[^>]*>(.*?)</style>', s, re.S):
    # the largest image referenced from CSS is the hero background
    refs = re.findall(r'url\((?:&quot;|["\']?)(a/[0-9a-f]{12}\.[a-z]+)', m.group(1))
    sizes = [(os.path.getsize(os.path.join(adir, r[2:])), r) for r in refs]
    if sizes:
        first.append(max(sizes)[1]); break
if hero_start >= 0 and hero_end > hero_start:
    for r in re.findall(r'src="(a/[0-9a-f]{12}\.[a-z]+)"', s[hero_start:hero_end]):
        if r not in first: first.append(r)
pre = ''.join('<link rel="preload" as="image" href="%s"%s>\n' % (r, ' fetchpriority="high"' if i == 0 else '') for i, r in enumerate(first[:4]))
s = s.replace('</head>', pre + '</head>', 1)
# After the page has loaded and the browser is idle, fetch the remaining images quietly so reels and panels never wait for them
rest = [('a/' + n) for n in files if ('a/' + n) not in first]
loader = ('<script>(function(){var u=%s;function go(){var i=0;(function n(){if(i>=u.length)return;var im=new Image();im.decoding="async";im.onload=im.onerror=function(){setTimeout(n,60)};im.src=u[i++]})()}'
          'function idle(){(window.requestIdleCallback||function(f){setTimeout(f,400)})(go,{timeout:4000})}'
          'if(document.readyState==="complete")setTimeout(idle,1200);else addEventListener("load",function(){setTimeout(idle,1200)})})();</script>\n') % __import__('json').dumps(rest)
i = s.rfind('</body>')
s = s[:i] + loader + s[i:] if i >= 0 else s + loader
print('images moved to a/:', len(files), 'preloaded:', first[:4])

open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)
print('index.html', len(s))
