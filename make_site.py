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
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)
print('index.html', len(s))
