#!/usr/bin/env python3
"""Daily live-data refresh for Kayle's site, using plain HTTP (curl) only.

Usage: python3 kayle_update.py <in.html> <out.html> <report.json>

Reads the page, fetches YouTube, LoLalytics, OP.GG and the China (mlol.qt.qq.com)
data, rewrites only the marked live-data blocks and writes a JSON report.
A value that cannot be fetched or fails a check keeps its old value.
"""
import concurrent.futures as cf
import datetime
import html as htmlmod
import json
import re
import subprocess
import sys
import time
from html.parser import HTMLParser

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/130.0 Safari/537.36')
REPORT = {'notes': {}, 'kept_old': {}, 'errors': []}


def note(part, msg):
    REPORT['notes'].setdefault(part, []).append(msg)


def kept(part, msg):
    REPORT['kept_old'].setdefault(part, []).append(msg)


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            r = subprocess.run(
                ['curl', '-sSL', '--compressed', '-m', '45', '-A', UA,
                 '-H', 'Accept-Language: de-DE,de;q=0.9,en;q=0.8',
                 '-b', 'CONSENT=YES+1; SOCS=CAI', '-w', '\n%{http_code}', url],
                capture_output=True, timeout=60)
            body = r.stdout.decode('utf-8', 'replace')
            body, _, code = body.rpartition('\n')
            if r.returncode == 0 and code == '200':
                return body
            last = 'curl rc=%s http=%s' % (r.returncode, code)
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(2 + 3 * i)
    raise RuntimeError('%s: %s' % (url, last))


def today():
    try:
        from zoneinfo import ZoneInfo
        d = datetime.datetime.now(ZoneInfo('Europe/Berlin'))
    except Exception:  # noqa: BLE001
        d = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    return '%d %s %d' % (d.day, d.strftime('%b'), d.year)


TODAY = today()


def r2(x):
    return None if x is None else round(float(x), 2)


# ---------------------------------------------------------------- JS blocks

def js(v):
    """Serialize like the page does: unquoted identifier keys, compact lists."""
    if isinstance(v, dict):
        return '{' + ', '.join(
            (k if re.fullmatch(r'[A-Za-z_]\w*', k) else json.dumps(k)) + ':' + js(x)
            for k, x in v.items()) + '}'
    if isinstance(v, list):
        return '[' + ', '.join(js(x) for x in v) + ']'
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return repr(v)
    return json.dumps(v)


def js_to_py(src):
    src = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', src)
    return json.loads(src)


def block_span(h, name):
    m = re.search(r'// === %s START[^\n]*\n' % re.escape(name), h)
    e = h.find('// === %s END' % name, m.end() if m else 0)
    if not m or e < 0:
        raise RuntimeError('block %s not found' % name)
    return m.end(), e


def find_var(h, name, var):
    s, e = block_span(h, name)
    b = h[s:e]
    m = re.search(r'var %s\s*=\s*' % var, b)
    i = m.end()
    depth, j, ins = 0, i, False
    while True:
        c = b[j]
        if ins:
            if c == '\\':
                j += 1
            elif c == '"':
                ins = False
        elif c == '"':
            ins = True
        elif c in '{[':
            depth += 1
        elif c in '}]':
            depth -= 1
            if depth == 0:
                break
        j += 1
    return s + i, s + j + 1, b[i:j + 1]


def get_var(h, name, var):
    return js_to_py(find_var(h, name, var)[2])


def set_var(h, name, var, value, pretty=None):
    a, b, _ = find_var(h, name, var)
    text = pretty(value) if pretty else js(value)
    return h[:a] + text + h[b:]


def pretty_servers(v):
    """Multi-line layout per server, like the page: one line per inner key."""
    out = ['{']
    keys = list(v.keys())
    for n, srv in enumerate(keys):
        d = v[srv]
        head = [k for k in d if k in ('patch', 'chk')]
        rest = [k for k in d if k not in head]
        line = '    %s:{%s' % (srv, ', '.join('%s:%s' % (k, js(d[k])) for k in head))
        if rest:
            parts = ['      %s:%s' % (k, js(d[k])) for k in rest]
            if len(rest) == 1 and len(js(d[rest[0]])) < 160:
                line += ', %s:%s}' % (rest[0], js(d[rest[0]]))
            else:
                line += ',\n' + ',\n'.join(parts) + '}'
        else:
            line += '}'
        out.append(line + (',' if n < len(keys) - 1 else ''))
    out.append('  }')
    return '\n'.join(out)


def pretty_td(v):
    out = ['{']
    keys = list(v.keys())
    for n, srv in enumerate(keys):
        tiers = v[srv]
        out.append('    %s:{%s}%s' % (srv, ', '.join(
            '%s:[%s]' % (t, ', '.join(js(x) for x in arr)) for t, arr in tiers.items()),
            ',' if n < len(keys) - 1 else ''))
    out.append('  }')
    return '\n'.join(out)


# ---------------------------------------------------------------- parsers

def qwik(h):
    m = re.search(r'<script type="qwik/json">([\s\S]*?)</script>', h)
    if not m:
        raise RuntimeError('no qwik json')
    return json.loads(m.group(1))['objs']


class Q:
    def __init__(self, objs):
        self.o = objs

    def __call__(self, i):
        return self.o[int(i, 36)]

    def ref(self, v):
        return (isinstance(v, str) and re.fullmatch(r'[0-9a-z]{1,4}', v)
                and int(v, 36) < len(self.o))

    def dec(self, v, d=0):
        if d > 9:
            return None
        if self.ref(v):
            return self.dec(self(v), d + 1)
        if isinstance(v, list):
            return [self.dec(e, d + 1) for e in v]
        if isinstance(v, dict):
            return {k: self.dec(x, d + 1) for k, x in v.items()}
        return v

    def find(self, *keys):
        return [o for o in self.o if isinstance(o, dict) and all(k in o for k in keys)]


def lola_build(lane, region, tier='emerald_plus', patch=None):
    url = 'https://lolalytics.com/lol/kayle/build/?lane=%s&region=%s&tier=%s' % (lane, region, tier)
    if patch:
        url += '&patch=' + patch
    q = Q(qwik(fetch(url)))
    rate = q.find('wr', 'pr', 'rankTotal')[0]
    res = {k: q.dec(rate.get(k)) for k in ('patch', 'lane', 'wr', 'pr', 'br', 'n')}
    m = q.find('boots', 'startSet')
    res['m'] = m[0] if m else None
    res['q'] = q
    return res


def lola_runes(b):
    q, m = b['q'], b['m']
    s = q(m['summary'])
    out = {}
    for k in ('pick', 'win'):
        r = q(q(s[k])['runes'])
        st, pg = q(r['set']), q(r['page'])
        out[k] = {'pri': [q(x) for x in q(st['pri'])], 'sec': [q(x) for x in q(st['sec'])],
                  'mod': [q(x) for x in q(st['mod'])], 'pt': q(pg['pri']), 'st': q(pg['sec'])}
    return out


def lola_spells(b):
    q = b['q']
    rows = []
    for a in q.o:
        if isinstance(a, list) and len(a) == 4 and all(isinstance(e, str) for e in a):
            try:
                v = [q(e) for e in a]
            except Exception:  # noqa: BLE001
                continue
            if (isinstance(v[0], str) and re.fullmatch(r'\d{1,2}_\d{1,2}', v[0])
                    and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v[1:])):
                rows.append(v)
    return rows


def china(endpoint, version, itier=26):
    url = ('https://mlol.qt.qq.com/go/battle_info/odp_proxy/lol_101strategy_%s'
           '?itier=%s&version_id=%s&lane=TOP&championid=10' % (endpoint, itier, version))
    d = json.loads(fetch(url))
    fv = (d.get('data') or {}).get('_fieldValues') or {}
    if not fv:
        return None
    v = list(fv.values())[0]
    v = json.loads(v) if isinstance(v, str) else v
    return v or None


def split_hash(s):
    return [x for x in (s or '').split('#') if x]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.intb, self.row, self.cell = [], 0, None, None

    def handle_starttag(self, t, a):
        a = dict(a)
        if t == 'table':
            self.tables.append([])
        elif t == 'tbody':
            self.intb += 1
        elif t == 'tr' and self.intb and self.tables:
            self.row = {'alts': [], 'tds': []}
        elif t == 'td' and self.row is not None:
            self.cell = []
        elif t == 'img' and self.row is not None and a.get('alt'):
            self.row['alts'].append(a['alt'])

    def handle_endtag(self, t):
        if t == 'tbody':
            self.intb -= 1
        elif t == 'tr' and self.row is not None:
            self.tables[-1].append(self.row)
            self.row = None
        elif t == 'td' and self.cell is not None:
            self.row['tds'].append(' '.join(self.cell).strip())
            self.cell = None

    def handle_data(self, d):
        if self.cell is not None and d.strip():
            self.cell.append(d.strip())


def page_text(h):
    t = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', h)
    t = htmlmod.unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.sub(r'\s+', ' ', t)


def opgg_title_patch(h):
    m = re.search(r'<title>[^<]*?Patch (\d+\.\d+)', h)
    return m.group(1) if m else None


def num(s):
    return float(s.replace(',', '').replace('%', ''))


# ---------------------------------------------------------------- id lists

BOOTS_NAMES = {"Berserker's Greaves": 3006, "Gluttonous Greaves": 3008, "Boots of Swiftness": 3009,
               "Sorcerer's Shoes": 3020, "Plated Steelcaps": 3047, "Mercury's Treads": 3111,
               "Ionian Boots of Lucidity": 3158}
ITEM_NAMES_TOP = {"Nashor's Tooth": 3115, "Dusk and Dawn": 2510, "Rabadon's Deathcap": 3089,
                  "Shadowflame": 4645, "Void Staff": 3135, "Rylai's Crystal Scepter": 3116,
                  "Zhonya's Hourglass": 3157, "Infinity Edge": 3031}
ITEM_NAMES_MID = dict(ITEM_NAMES_TOP, **{"Lich Bane": 3100, "Banshee's Veil": 3102,
                                         "Mejai's Soulstealer": 3041})
START_IDS = {1001, 1054, 1055, 1056, 1083, 1086, 1120, 2003, 2031}
BOOT_IDS = {3006, 3008, 3009, 3020, 3047, 3111, 3158}
SPELL_IDS = {1, 3, 4, 6, 7, 11, 12, 14, 21}
RUNE_MID = {8005, 8008, 8021, 9101, 9111, 9104, 8014, 8017, 8299, 8009, 8234, 8236, 8275, 8242,
            8473, 8444, 8453, 8429, 8446, 8451, 5001, 5005, 5008, 5010, 5011, 5013, 8237}
# The page knows the same rune icons for both lanes (8009 etc. are used top and mid).
RUNE_TOP = RUNE_MID
# Secondary runes in the order the rune page shows them (row by row), as LoLalytics' DOM did.
SORC = [8224, 8226, 8275, 8210, 8234, 8233, 8237, 8232, 8236]
RESO = [8446, 8463, 8401, 8429, 8444, 8473, 8451, 8453, 8242]
MU_ITEMS = {1054, 1055, 1056, 1083, 1086, 1120, 2003, 2031, 2510, 3006, 3008, 3009, 3020, 3047,
            3072, 3087, 3089, 3091, 3100, 3102, 3111, 3115, 3116, 3124, 3135, 3139, 3146, 3153,
            3157, 3158, 3165, 3302, 4645, 6672, 6676, 3031}
MU_ITEMS_MID = MU_ITEMS | {3041}
MU_RUNES = {5001, 5005, 5008, 5010, 5011, 5013, 8000, 8005, 8008, 8009, 8014, 8017, 8021, 8200,
            8234, 8236, 8237, 8242, 8275, 8299, 8400, 8429, 8444, 8446, 8451, 8453, 8473, 9101, 9104,
            9111}
BOOTS_ALL = {1001, 3005, 3006, 3008, 3009, 3010, 3020, 3047, 3111, 3117, 3158, 9999}
TREE = {0: 8000, 1: 8100, 2: 8200, 3: 8400, 4: 8300}


def prev_patch(p, old_patch, old_prev):
    a, b = p.split('.')
    if int(b) > 1:
        return '%s.%d' % (a, int(b) - 1)
    if p == old_patch:
        return old_prev
    raise RuntimeError('season change: previous patch of %s unknown' % p)


def sec_tree(sec):
    if all(x in SORC for x in sec):
        return 8200
    if all(x in RESO for x in sec):
        return 8400
    return None


def best4(rows, key_ok, min_ok, n=4):
    rows = [r for r in rows if min_ok(r) and key_ok(r)]
    rows.sort(key=lambda r: -r[1])
    return rows[:n]


# ---------------------------------------------------------------- PART 1

def part1(h):
    P = 'abos'
    old = get_var(h, 'CHANNEL STATS', 'CHSTAT')
    try:
        t = fetch('https://www.youtube.com/@kayle_1v9/videos')
        m = re.search(r'"(\d[\d.,]*)\s*(Tsd\.|Mio\.)?\s*Abonnenten"', t) or \
            re.search(r'(\d[\d.,]*)\s*(Tsd\.|Mio\.)?\s*Abonnenten', t)
        mv = re.search(r'(\d[\d.]*)\s*Videos', t)
        if not m or not mv:
            raise RuntimeError('Abonnenten/Videos nicht gefunden')
        n, unit = m.group(1), m.group(2)
        if unit:
            subs = int(round(float(n.replace('.', '').replace(',', '.')) *
                             (1000 if unit == 'Tsd.' else 1000000)))
        else:
            subs = int(n.replace('.', '').replace(',', ''))
        videos = int(mv.group(1).replace('.', ''))
        if not (0.9 * old['subs'] <= subs <= 1.15 * old['subs']):
            raise RuntimeError('unplausibler Sprung %s -> %s' % (old['subs'], subs))
        new = dict(old, subs=subs, videos=videos, checked=TODAY)
        if subs >= new['goal']:
            for g in (100000, 250000, 500000, 1000000, 2500000, 5000000):
                if g > subs:
                    new['goal'] = g
                    break
        note(P, 'subs %d (vorher %d, %+d), videos %d' % (subs, old['subs'], subs - old['subs'], videos))
        return set_var(h, 'CHANNEL STATS', 'CHSTAT', new)
    except Exception as e:  # noqa: BLE001
        kept(P, 'Abozahl unverändert: %s' % e)
        return h


# ---------------------------------------------------------------- rates

def rates_part(h, lane, P):
    top = lane == 'top'
    blk, var = ('LIVE DATA', 'TD') if top else ('LIVE DATA MID', 'TDM')
    pv = ('PATCH', 'PREV', 'CHECKED') if top else ('PATCHM', 'PREVM', 'CHECKEDM')
    s, e = block_span(h, blk)
    b = h[s:e]
    m = re.search(r'var %s = "([\d.]+)", %s = "([\d.]+)", %s = "([^"]*)";' % pv, b)
    old_patch, old_prev = m.group(1), m.group(2)
    td = get_var(h, blk, var)
    first = lola_build(lane, 'euw')
    patch = first['patch']
    prev = prev_patch(patch, old_patch, old_prev)
    tiers = [('emerald_plus', 'emerald'), ('diamond_plus', 'diamond'), ('master_plus', 'master'), ('all', 'all')]
    lo, hi = (40, 65) if top else (35, 65)
    plo = 0.1 if top else 0.05
    changed = False
    for region, srv in [('euw', 'eu'), ('kr', 'korea')]:
        for tier, key in tiers:
            arr = list(td[srv][key])
            ok = True
            for i, p in enumerate([patch, prev]):
                try:
                    if top and srv == 'korea':
                        ph = fetch('https://op.gg/lol/champions/kayle/build/top?region=kr&tier=%s&patch=%s' % (tier, p))
                        if opgg_title_patch(ph) != p:
                            raise RuntimeError('OP.GG zeigt nicht Patch %s' % p)
                        mm = re.search(r'Win rate ([\d.]+)% Pick rate ([\d.]+)% Ban rate ([\d.]+)%', page_text(ph))
                        w, pk, bn = [float(x) for x in mm.groups()]
                    else:
                        r = lola_build(lane, region, tier, p)
                        if r['patch'] != p or r['lane'] != lane:
                            raise RuntimeError('falscher Patch/Lane %s/%s' % (r['patch'], r['lane']))
                        w, pk, bn = r['wr'], r['pr'], r['br']
                    if not (lo <= w <= hi and plo <= pk <= 10 and 0 <= bn <= 15):
                        raise RuntimeError('Sanity %s/%s/%s' % (w, pk, bn))
                    arr[3 * i:3 * i + 3] = [r2(w), r2(pk), r2(bn)]
                except Exception as ex:  # noqa: BLE001
                    ok = False
                    kept(P, 'Raten %s %s %s: %s' % (srv, key, p, ex))
            if patch != old_patch and not ok:
                continue
            if arr != td[srv][key]:
                changed = True
            td[srv][key] = arr
    if top:
        for p_i, p in enumerate([patch, prev]):
            try:
                v = china('segment', p, itier=255)
                if not v:
                    raise RuntimeError('keine Daten')
                ent = {x.split('_')[0]: x.split('_')[1:] for x in split_hash(v.get('datadetails'))}
                for tid, key in [('26', 'emerald'), ('27', 'diamond'), ('28', 'master'), ('255', 'all')]:
                    w, pk, bn = [float(x) for x in ent[tid][:3]]
                    if not (40 <= w <= 65 and 0.1 <= pk <= 10 and 0 <= bn <= 15):
                        raise RuntimeError('Sanity %s' % key)
                    td['china'][key][3 * p_i:3 * p_i + 3] = [w, pk, bn]
            except Exception as ex:  # noqa: BLE001
                kept(P, 'Raten china %s: %s' % (p, ex))
    for srv in td:
        note(P, 'Raten %s emerald: %s' % (srv, td[srv]['emerald']))
    h = set_var(h, blk, var, td, pretty_td)
    s, e = block_span(h, blk)
    b = h[s:e]
    b = re.sub(r'var %s = "[\d.]+", %s = "[\d.]+", %s = "[^"]*";' % pv,
               'var %s = "%s", %s = "%s", %s = "%s";' % (pv[0], patch, pv[1], prev, pv[2], TODAY), b, count=1)
    if patch != old_patch:
        note(P, 'neuer Patch %s (vorher %s)' % (patch, old_patch))
    return h[:s] + b + h[e:], patch, first


# ---------------------------------------------------------------- runes

def runes_part(h, lane, patch, P, builds):
    top = lane == 'top'
    blk, var = ('RUNES LIVE', 'RLIVE') if top else ('RUNES LIVE MID', 'RLIVEM')
    known = RUNE_TOP if top else RUNE_MID
    R = get_var(h, blk, var)
    for srv in R:
        refreshed = False
        if srv == 'china':
            try:
                v = None
                for p in (patch, prev_patch(patch, patch, patch)):
                    v = china('runeinfo', p)
                    if v and v.get('rune_top_details'):
                        break
                ents = []
                for x in split_hash(v.get('rune_top_details') if v else ''):
                    f = x.split('_')
                    if len(f) < 7 or f[2] not in ('ws', 'jj'):
                        continue
                    ids = [int(i) for i in f[3].split(',')]
                    if len(ids) != 9:
                        continue
                    ents.append({'ids': ids, 'tree': 8200 if f[2] == 'ws' else 8400,
                                 'pick': float(f[4]), 'win': float(f[5]), 'games': int(f[6])})
                if not ents:
                    raise RuntimeError('keine Runendaten')
                cands = {'common': max(ents, key=lambda e: e['pick'])}
                big = [e for e in ents if e['games'] >= 300]
                if big:
                    cands['best'] = max(big, key=lambda e: e['win'])
                for k, en in cands.items():
                    ids = en['ids']
                    if any(i not in known for i in ids) or ids[0] not in (8005, 8008):
                        kept(P, 'Runen china %s: unbekannte id %s' % (k, [i for i in ids if i not in known]))
                        continue
                    pg = {'key': ids[0], 'main': ids[1:4], 'tree': en['tree'], 'sec': ids[4:6],
                          'shards': ids[6:9], 'win': en['win'], 'games': en['games'], 'pick': en['pick']}
                    if pg != R[srv][k]:
                        note(P, 'Runen china %s geändert' % k)
                    R[srv][k] = pg
                    refreshed = True
            except Exception as ex:  # noqa: BLE001
                kept(P, 'Runen china: %s' % ex)
        else:
            try:
                b = builds[srv]
                if b['patch'] != patch:
                    raise RuntimeError('Seite zeigt Patch %s' % b['patch'])
                rr = lola_runes(b)
                for k, src in (('common', 'pick'), ('best', 'win')):
                    x = rr[src]
                    tree = sec_tree(x['sec'])
                    if tree:
                        order = SORC if tree == 8200 else RESO
                        x['sec'] = sorted(x['sec'], key=order.index)
                    ids = x['pri'] + x['sec'] + x['mod']
                    if len(ids) != 9 or x['pt'] != 0 or tree is None:
                        kept(P, 'Runen %s %s: Seite unvollständig/anderer Baum' % (srv, k))
                        continue
                    unk = [i for i in ids if i not in known]
                    if unk:
                        kept(P, 'Runen %s %s: unbekannte id %s' % (srv, k, unk))
                        continue
                    pg = {'key': ids[0], 'main': ids[1:4], 'tree': tree, 'sec': ids[4:6], 'shards': ids[6:9]}
                    if {kk: R[srv][k].get(kk) for kk in pg} != pg:
                        note(P, 'Runen %s %s geändert' % (srv, k))
                    R[srv][k] = pg
                    refreshed = True
            except Exception as ex:  # noqa: BLE001
                kept(P, 'Runen %s: %s' % (srv, ex))
        if refreshed:
            R[srv]['patch'], R[srv]['chk'] = patch, TODAY
    return set_var(h, blk, var, R, pretty_servers)


# ---------------------------------------------------------------- starters

def starters_part(h, lane, patch, P, builds):
    top = lane == 'top'
    blk, var = ('STARTERS LIVE', 'SBLIVE') if top else ('STARTERS LIVE MID', 'SBLIVEM')
    ming = 100 if top else 50
    S = get_var(h, blk, var)

    def start_ok(r):
        ids = [int(x) for x in str(r[0]).split('_') if x]
        bad = [i for i in ids if i not in START_IDS]
        if bad:
            note(P, 'Start %s %s übersprungen (unbekannte id %s)' % (srv, r[0], bad))
        return ids and not bad

    def boot_ok(r):
        if r[0] in (1001, 9999):
            return False
        if r[0] not in BOOT_IDS:
            note(P, 'Stiefel %s übersprungen (unbekannte id)' % r[0])
            return False
        return True

    for srv in S:
        refreshed = False
        try:
            if srv == 'china':
                v = china('build', patch)
                if not v:
                    raise RuntimeError('keine Daten')
                st, bt = [], []
                for x in split_hash(v.get('starting_details')):
                    ids, _, pk, w = x.split('_')
                    st.append([ids.replace(',', '_'), float(w), float(pk), None])
                for x in split_hash(v.get('shoes_details')):
                    ids, _, pk, w = x.split('_')
                    bt.append([int(ids), float(w), float(pk), None])
                mok = lambda r: r[2] >= 1  # noqa: E731
            else:
                b = builds[srv]
                if b['patch'] != patch:
                    raise RuntimeError('Seite zeigt Patch %s' % b['patch'])
                q, m = b['q'], b['m']
                bt = [list(r[:4]) for r in q.dec(m['boots'])]
                st = [list(r[:4]) for r in q.dec(m['startSet'])]
                mok = lambda r: (r[3] or 0) >= ming  # noqa: E731
            ns = best4(st, start_ok, mok)
            nb = best4(bt, boot_ok, mok)
            if ns:
                if [r[0] for r in ns] != [r[0] for r in S[srv]['start']]:
                    note(P, 'Startitems %s neue Reihenfolge: %s' % (srv, [r[0] for r in ns]))
                S[srv]['start'] = [[r[0], r2(r[1]), r2(r[2]), r[3]] for r in ns]
                refreshed = True
            if nb:
                if [r[0] for r in nb] != [r[0] for r in S[srv]['boots']]:
                    note(P, 'Stiefel %s neue Reihenfolge: %s' % (srv, [r[0] for r in nb]))
                S[srv]['boots'] = [[r[0], r2(r[1]), r2(r[2]), r[3]] for r in nb]
                refreshed = True
        except Exception as ex:  # noqa: BLE001
            kept(P, 'Startitems/Stiefel %s: %s' % (srv, ex))
        if refreshed:
            S[srv]['patch'], S[srv]['chk'] = patch, TODAY
    return set_var(h, blk, var, S, pretty_servers)


# ---------------------------------------------------------------- items

def opgg_items(lane, region, patch, names):
    path = 'top' if lane == 'top' else 'mid'
    url = 'https://op.gg/lol/champions/kayle/build/%s?region=%s&tier=emerald_plus' % (path, region)
    ph = fetch(url)
    tp = opgg_title_patch(ph)
    if tp != patch:
        raise RuntimeError('OP.GG zeigt Patch %s statt %s' % (tp, patch))
    p = Tables()
    p.feed(ph)
    tabs = p.tables
    bi = next(i for i, t in enumerate(tabs) if t and len(t[0]['alts']) == 1 and t[0]['alts'][0] in BOOTS_NAMES)
    core_t, f_t, x_t = tabs[bi + 1], tabs[bi + 2], tabs[bi + 3]

    def stats(row):
        txt = ' '.join(row['tds'])
        pcts = re.findall(r'([\d.]+)%', txt)
        g = re.search(r'([\d,]+) Games', txt)
        return [num(x) for x in pcts], (int(g.group(1).replace(',', '')) if g else None)

    if len(core_t[0]['alts']) != 3:
        raise RuntimeError('Core-Tabelle nicht erkannt')
    pc, g = stats(core_t[0])
    core = {'names': core_t[0]['alts'], 'pick': pc[0], 'win': pc[1], 'games': g}

    def opts(t):
        out = []
        for r in t:
            if len(r['alts']) != 1:
                continue
            pc, g = stats(r)
            out.append((r['alts'][0], pc[0], g))
        return out
    return core, opts(f_t), opts(x_t)


def items_part(h, lane, patch, P):
    top = lane == 'top'
    blk, var = ('ITEMS LIVE', 'IBLIVE') if top else ('ITEMS LIVE MID', 'IBLIVEM')
    names = ITEM_NAMES_TOP if top else ITEM_NAMES_MID
    known = set(names.values())
    I = get_var(h, blk, var)
    for srv in I:
        refreshed = False
        try:
            if srv == 'china':
                v = china('build', patch)
                if not v:
                    raise RuntimeError('keine Daten')
                c = [x for x in split_hash(v.get('core_details')) if x.split('_')[1] == '1'][0].split('_')
                core = {'ids': [int(i) for i in c[0].split(',')], 'win': float(c[3]), 'pick': float(c[2]), 'games': None}

                def chopts(field):
                    out = []
                    for x in split_hash(v.get(field)):
                        f = x.split('_')
                        out.append((int(f[0]), float(f[3]), float(f[2]), None, float(f[2])))
                    return out
                fifth, sixth = chopts('fifth_details'), chopts('sixth_details')
            else:
                region = 'euw' if srv == 'eu' else 'kr'
                c, f, x = opgg_items(lane, region, patch, names)
                if any(n not in names for n in c['names']):
                    core = {'unknown': [n for n in c['names'] if n not in names]}
                else:
                    core = {'ids': [names[n] for n in c['names']], 'win': c['win'], 'pick': c['pick'], 'games': c['games']}

                def conv(lst):
                    out = []
                    for nm, w, g in lst:
                        out.append((names.get(nm, nm), w, None, g, g or 0))
                    return out
                fifth, sixth = conv(f), conv(x)
            if 'unknown' in core or any(i not in known for i in core['ids']):
                kept(P, 'Core %s: unbekanntes Item %s' % (srv, core.get('unknown') or [i for i in core['ids'] if i not in known]))
                core_ids = I[srv]['core']['ids']
            else:
                if core['ids'] != I[srv]['core']['ids']:
                    note(P, 'Core %s geändert: %s' % (srv, core['ids']))
                I[srv]['core'] = core
                core_ids = core['ids']
                refreshed = True
            for key, lst in (('fifth', fifth), ('sixth', sixth)):
                lst = [r for r in lst if r[0] not in core_ids]
                lst.sort(key=lambda r: -r[4])
                rows = []
                for r in lst:
                    if r[0] not in known:
                        note(P, '%s %s: unbekanntes Item %s übersprungen' % (key, srv, r[0]))
                        continue
                    rows.append([r[0], r2(r[1]), r2(r[2]), r[3]])
                    if len(rows) == 3:
                        break
                if len(rows) == 3:
                    if [r[0] for r in rows] != [r[0] for r in I[srv][key]]:
                        note(P, '%s %s neu: %s' % (key, srv, [r[0] for r in rows]))
                    I[srv][key] = rows
                    refreshed = True
                else:
                    kept(P, '%s %s: weniger als 3 bekannte Optionen' % (key, srv))
        except Exception as ex:  # noqa: BLE001
            kept(P, 'Items %s: %s' % (srv, ex))
        if refreshed:
            I[srv]['patch'], I[srv]['chk'] = patch, TODAY
    return set_var(h, blk, var, I, pretty_servers)


# ---------------------------------------------------------------- spells

def spells_part(h, lane, patch, P, builds):
    top = lane == 'top'
    blk, var = ('SPELLS LIVE', 'SPLIVE') if top else ('SPELLS LIVE MID', 'SPLIVEM')
    ming = 100 if top else 50
    S = get_var(h, blk, var)

    def ok(r):
        ids = [int(x) for x in r[0].split('_')]
        if any(i not in SPELL_IDS for i in ids):
            note(P, 'Spells %s übersprungen (unbekannte id)' % r[0])
            return False
        return True

    for srv in S:
        try:
            if srv == 'china':
                v = china('skill', patch)
                if not v:
                    raise RuntimeError('keine Daten')
                rows = []
                for x in split_hash(v.get('data_details')):
                    a, b, w, pk = x.split('_')
                    ids = sorted([int(a), int(b)])
                    rows.append(['%d_%d' % tuple(ids), float(w), float(pk), None])
                mok = lambda r: r[2] >= 1  # noqa: E731
            else:
                b = builds[srv]
                if b['patch'] != patch:
                    raise RuntimeError('Seite zeigt Patch %s' % b['patch'])
                rows = []
                for r in lola_spells(b):
                    ids = sorted(int(i) for i in r[0].split('_'))
                    rows.append(['%d_%d' % tuple(ids), r[1], r[2], r[3]])
                mok = lambda r: (r[3] or 0) >= ming  # noqa: E731
            nr = best4(rows, ok, mok)
            if not nr:
                raise RuntimeError('keine Zeilen')
            if [r[0] for r in nr] != [r[0] for r in S[srv]['rows']]:
                note(P, 'Spells %s neue Reihenfolge: %s' % (srv, [r[0] for r in nr]))
            S[srv]['rows'] = [[r[0], r2(r[1]), r2(r[2]), r[3]] for r in nr]
            S[srv]['patch'], S[srv]['chk'] = patch, TODAY
        except Exception as ex:  # noqa: BLE001
            kept(P, 'Spells %s: %s' % (srv, ex))
    return set_var(h, blk, var, S, pretty_servers)


# ---------------------------------------------------------------- matchups

def mu_parse(html):
    q = Q(qwik(html))
    o = q.find('summary', 'startItem', 'boots')
    if not o:
        return None
    o = o[0]
    s, hd = q(o['summary']), q(o['header'])

    def page(k):
        r = q(q(s[k])['runes'])
        st, pg = q(r['set']), q(r['page'])
        return {'wr': q(r['wr']), 'n': q(r['n']), 'pri': [q(x) for x in q(st['pri'])],
                'sec': [q(x) for x in q(st['sec'])], 'mod': [q(x) for x in q(st['mod'])],
                'pt': q(pg['pri']), 'st': q(pg['sec'])}

    def sums(k):
        z = q(q(s[k])['sums'])
        return {'ids': [q(x) for x in q(z['ids'])], 'n': q(z['n']), 'wr': q(z['wr'])}

    def items(k):
        it = q(q(s[k])['items'])
        out = {}
        for n in ('item1', 'item2', 'item3'):
            x = q(it[n])
            out[n] = [{'id': q(x['id']), 'n': q(x['n']), 'wr': q(x['wr'])}]
        for n in ('item4', 'item5', 'item6'):
            lst = []
            for r in q(it[n]):
                x = q(r)
                if isinstance(x, dict):
                    lst.append({'id': q(x['id']), 'n': q(x['n']), 'wr': q(x['wr'])})
            out[n] = lst
        st = q(it['start'])
        sset = q(st['set']) if st and st.get('set') is not None else None
        out['start'] = {'set': [q(x) for x in sset] if sset else None,
                        'n': q(st['n']) if st else None, 'wr': q(st['wr']) if st else None}
        return out

    def boots():
        res = []
        for b in q(o['boots']):
            a = q(b)
            res.append([q(x) for x in a][:4] if isinstance(a, list) else a)
        return res
    d = {'hd': {'wr': q(hd['wr']), 'n': q(hd['n']), 'patch': q(hd['patch'])},
         'pickR': page('pick'), 'winR': page('win'), 'pickS': sums('pick'), 'winS': sums('win'),
         'pickI': items('pick')}
    try:
        d['winI'] = items('win')
    except Exception:  # noqa: BLE001
        d['winI'] = None
    d['bootsAll'] = boots()
    d['boots'] = d['bootsAll'][:4]
    return d


def mu_fetch(lane):
    base = 'https://lolalytics.com'
    q = Q(qwik(fetch(base + '/lol/kayle/counters/?lane=%s&vslane=%s&tier=emerald_plus' % (lane, lane))))
    meta = q.find('champPath')[0]
    cp, ch = q(meta['champPath']), q(meta['champions'])
    lst = []
    for o in q.o:
        if isinstance(o, dict) and 'vsWr' in o and 'cid' in o and 'n' in o:
            cid = q(o['cid'])
            slug = q(cp[str(cid)])
            lst.append({'cid': cid, 'n': q(o['n']), 'slug': slug, 'name': q(ch[slug])})
    out, errs = {}, []

    def one(x):
        try:
            d = mu_parse(fetch(base + '/lol/kayle/vs/%s/build/?lane=%s&vslane=%s&tier=emerald_plus' % (x['slug'], lane, lane)))
            if not d:
                return x, None, 'noobj'
            return x, d, None
        except Exception as e:  # noqa: BLE001
            return x, None, str(e)[:80]
    with cf.ThreadPoolExecutor(5) as ex:
        for x, d, err in ex.map(one, lst):
            if err:
                errs.append('%s:%s' % (x['slug'], err))
            else:
                d.update(cid=x['cid'], slug=x['slug'], name=x['name'], games=x['n'])
                out[x['slug']] = d
    return out, errs, len(lst)


def mu_convert(d, known_items):
    def page(p):
        return {'k': p['pri'][0], 'm': p['pri'][1:4], 't': TREE.get(p['st']), 's': p['sec'], 'h': p['mod'],
                'w': r2(p['wr']), 'n': p['n']}

    def core_of(I):
        seq = [I['item1'][0], I['item2'][0], I['item3'][0]] + I['item4'][:1]
        core = [x for x in seq if x['id'] not in BOOTS_ALL][:3]
        if len(core) < 3:
            nb = [x for x in I['item5'] if x['id'] not in BOOTS_ALL]
            if nb:
                core.append(nb[0])
        if len(core) < 3:
            return None
        return [{'i': x['id'], 'w': r2(x['wr']), 'n': x['n']} for x in core]

    def opts(lst, core_ids, by_win):
        r = [x for x in lst if x['id'] not in BOOTS_ALL and x['id'] not in core_ids and (x['n'] or 0) >= 10]
        r.sort(key=(lambda x: -x['wr']) if by_win else (lambda x: -x['n']))
        return [{'i': x['id'], 'w': r2(x['wr']), 'n': x['n']} for x in r[:3]]

    e = {'c': d['cid'], 'nm': d['name'], 'n': d['games'], 'w': r2(d['hd']['wr']),
         'r': {'p': page(d['pickR']), 'b': page(d['winR'])},
         'sp': {'p': {'i': d['pickS']['ids'], 'w': r2(d['pickS']['wr']), 'n': d['pickS']['n']},
                'b': {'i': d['winS']['ids'], 'w': r2(d['winS']['wr']), 'n': d['winS']['n']}}}
    st = d['pickI']['start']
    e['st'] = {'s': st['set'], 'w': r2(st['wr']), 'n': st['n']}
    bt = [[b[0], r2(b[1]), r2(b[2]), b[3]] for b in d['boots']
          if isinstance(b, list) and b[0] not in (1001, 9999) and (b[3] or 0) >= 10][:3]
    if not bt:
        return None, 'keine Stiefel'
    e['bt'] = bt
    c = core_of(d['pickI'])
    if not c:
        return None, 'kein Core'
    ids = [x['i'] for x in c]
    e['it'] = {'c': c, 'f': opts(d['pickI']['item5'], ids, False), 'x': opts(d['pickI']['item6'], ids, False)}
    win = None
    if d.get('winI'):
        try:
            wc = core_of(d['winI'])
            if wc:
                wids = [x['i'] for x in wc]
                win = {'iw': {'c': wc, 'f': opts(d['winI']['item5'], wids, True), 'x': opts(d['winI']['item6'], wids, True)}}
                rows = [[b[0], r2(b[1]), r2(b[2]), b[3]] for b in d['bootsAll']
                        if isinstance(b, list) and b[0] not in (1001, 9999)]
                bw = [r for r in rows if (r[3] or 0) >= 25] or [r for r in rows if (r[3] or 0) >= 10]
                bw.sort(key=lambda r: -r[1])
                win['bw'] = bw[:3]
                ws = d['winI']['start']
                if ws['set'] is not None and (ws['n'] or 0) >= 10:
                    win['sw'] = {'s': ws['set'], 'w': r2(ws['wr']), 'n': ws['n']}
        except Exception:  # noqa: BLE001
            win = None
    return (e, win), None


def mu_ids(e):
    runes, items, spells = [], [], []
    for p in e['r'].values():
        runes += [p['k']] + p['m'] + [p['t']] + p['s'] + p['h']
    for p in e['sp'].values():
        spells += p['i']
    items += e['st']['s'] or []
    items += [b[0] for b in e['bt']]
    for k in ('c', 'f', 'x'):
        items += [x['i'] for x in e['it'][k]]
    return runes, items, spells


def win_ids(w):
    items = []
    for k in ('c', 'f', 'x'):
        items += [x['i'] for x in w['iw'][k]]
    items += [b[0] for b in w.get('bw', [])]
    if 'sw' in w:
        items += w['sw']['s']
    return items


def matchups_part(h, lane, P, chi_keys=None):
    top = lane == 'top'
    blk, var = ('MATCHUPS LIVE', 'MULIVE') if top else ('MATCHUPS LIVE MID', 'MULIVEM')
    known_items = MU_ITEMS if top else MU_ITEMS_MID
    a, b, raw = find_var(h, blk, var)
    old = json.loads(raw)
    champs = {v['c'] for v in old['list'].values()} if top else chi_keys
    try:
        data, errs, total = mu_fetch(lane)
    except Exception as ex:  # noqa: BLE001
        kept(P, 'Matchups komplett alt: %s' % ex)
        return h
    new = dict(old['list'])
    refreshed, moves, patches = 0, [], set()
    for slug, d in data.items():
        try:
            res, err = mu_convert(d, known_items)
        except Exception as ex:  # noqa: BLE001
            res, err = None, 'Parse: %s' % ex
        if not res:
            kept(P, 'Matchup %s alt: %s' % (slug, err))
            continue
        e, win = res
        if e['c'] not in champs:
            kept(P, 'Matchup %s übersprungen: kein Champion-Icon (%s)' % (slug, e['nm']))
            continue
        if not (25 <= (e['w'] or 0) <= 80):
            kept(P, 'Matchup %s alt: Winrate %s unplausibel' % (slug, e['w']))
            continue
        runes, items, spells = mu_ids(e)
        unk = [i for i in runes if i not in MU_RUNES] + [i for i in items if i not in known_items] + \
              [i for i in spells if i not in SPELL_IDS]
        if unk:
            kept(P, 'Matchup %s alt: unbekannte ids %s' % (slug, sorted(set(unk))))
            continue
        o = old['list'].get(slug, {})
        if win:
            wu = [i for i in win_ids(win) if i not in known_items]
            if wu:
                kept(P, 'Matchup %s: Best-Winrate-Teil alt (unbekannte ids %s)' % (slug, sorted(set(wu))))
                win = None
        if win:
            e.update(win)
        else:
            for k in ('iw', 'bw', 'sw'):
                if k in o:
                    e[k] = o[k]
        if o.get('w') is not None and e['w'] is not None:
            if round(e['w'] - o['w'], 2):
                moves.append((round(e['w'] - o['w'], 2), e['nm']))
        new[slug] = e
        refreshed += 1
        patches.add(d['hd']['patch'])
    need = 40 if top else 20
    if refreshed < need:
        kept(P, 'Matchups komplett alt: nur %d aktualisiert (mindestens %d nötig), Fehler: %s' % (refreshed, need, errs[:10]))
        return h
    moves.sort(key=lambda m: -abs(m[0]))
    note(P, 'Matchups: %d von %d aktualisiert, %d in der Liste, Fehler/zu wenig Daten: %s' % (refreshed, total, len(new), errs))
    note(P, 'größte Matchup-Bewegungen: %s' % (', '.join('%s %+.2f' % (n, d) for d, n in moves[:5]) or 'keine'))
    out = {'patch': sorted(patches)[-1], 'chk': TODAY,
           'list': dict(sorted(new.items(), key=lambda kv: kv[1]['nm']))}
    return h[:a] + json.dumps(out, separators=(',', ':'), ensure_ascii=False) + h[b:]


# ---------------------------------------------------------------- main

def lane_parts(h, lane, P):
    try:
        h, patch, first = rates_part(h, lane, P)
    except Exception as ex:  # noqa: BLE001
        kept(P, 'Raten/Patch nicht lesbar, ganze Lane alt: %s' % ex)
        return h
    builds = {'eu': first}
    try:
        builds['korea'] = lola_build(lane, 'kr', 'emerald_plus', patch)
    except Exception as ex:  # noqa: BLE001
        builds['korea'] = {'patch': None}
        kept(P, 'LoLalytics Korea: %s' % ex)
    try:
        builds['eu'] = lola_build(lane, 'euw', 'emerald_plus', patch)
    except Exception:  # noqa: BLE001
        pass
    for fn in (runes_part, starters_part):
        try:
            h = fn(h, lane, patch, P, builds)
        except Exception as ex:  # noqa: BLE001
            kept(P, '%s: %s' % (fn.__name__, ex))
    try:
        h = items_part(h, lane, patch, P)
    except Exception as ex:  # noqa: BLE001
        kept(P, 'items: %s' % ex)
    try:
        h = spells_part(h, lane, patch, P, builds)
    except Exception as ex:  # noqa: BLE001
        kept(P, 'spells: %s' % ex)
    chi = None
    if lane != 'top':
        a, b, raw = find_var(h, 'MATCHUPS LIVE', 'MULIVE')  # noqa: F841
        m = re.search(r'var CHI = \{', h)
        chi = {int(k) for k in re.findall(r'"(\d+)":\s*"data:', h[m.end() - 1:m.end() - 1 + 3000000].split('};')[0])}
    try:
        h = matchups_part(h, lane, P, chi)
    except Exception as ex:  # noqa: BLE001
        kept(P, 'matchups: %s' % ex)
    return h


def main():
    src, dst, rep = sys.argv[1:4]
    h0 = open(src, encoding='utf-8').read()
    h = part1(h0)
    h = lane_parts(h, 'top', 'top')
    h = lane_parts(h, 'middle', 'mid')
    REPORT['date'] = TODAY
    REPORT['changed'] = h != h0
    open(dst, 'w', encoding='utf-8').write(h)
    json.dump(REPORT, open(rep, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(REPORT, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
