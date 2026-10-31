#!/usr/bin/env python3
"""Collect the day-over-day win / pick / ban rates from the repo history into data/rates_history.json
(lane -> region -> tier -> {win:[..], pick:[..], ban:[..], days:[..]}), oldest first, last 21 days.
Reads TD / TDM blocks of index.html at each commit whose CHECKED date differs. Usage: rates_history.py <repo> <out.json>"""
import re, sys, json, subprocess
repo, out = sys.argv[1], sys.argv[2]
def grab(src, name):
    m = re.search(r'var %s = \{' % name, src)
    if not m: return None
    i = m.end() - 1; d = 0
    for j in range(i, len(src)):
        if src[j] == "{": d += 1
        elif src[j] == "}":
            d -= 1
            if d == 0: return src[i:j + 1]
def js(t):
    t = re.sub(r'//[^\n]*', '', t); t = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', t); t = re.sub(r',\s*([}\]])', r'\1', t)
    return json.loads(t)
log = subprocess.run(["git", "-C", repo, "log", "--format=%H", "-n", "400", "--", "index.html"], capture_output=True, text=True).stdout.split()
seen = {}; order = []
for c in log:
    src = subprocess.run(["git", "-C", repo, "show", c + ":index.html"], capture_output=True, text=True, errors="replace").stdout
    m = re.search(r'CHECKED = "([^"]+)"', src)
    if not m: continue
    day = m.group(1)
    if day in seen: continue
    rec = {}
    for lane, name in (("top", "TD"), ("mid", "TDM")):
        if name == "TD" and not re.search(r"var TD = \{", src): continue
        raw = grab(src, name)
        if not raw: continue
        try: rec[lane] = js(raw)
        except Exception: pass
    if rec: seen[day] = rec; order.append(day)
    if len(order) >= 21: break
order.reverse()
hist = {}
for day in order:
    rec = seen[day]
    for lane, regs in rec.items():
        for reg, tiers in regs.items():
            for tier, a in tiers.items():
                if not isinstance(a, list) or len(a) < 3: continue
                H = hist.setdefault(lane, {}).setdefault(reg, {}).setdefault(tier, {"win": [], "pick": [], "ban": [], "days": []})
                H["win"].append(a[0]); H["pick"].append(a[1]); H["ban"].append(a[2]); H["days"].append(day)
json.dump(hist, open(out, "w"), separators=(",", ":"))
print("days", order)
