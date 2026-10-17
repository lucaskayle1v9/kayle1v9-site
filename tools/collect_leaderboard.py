#!/usr/bin/env python3
"""Builds leaderboard.json (top Kayle players) from the official Riot API.

Needs the environment variable RIOT_API_KEY. Runs nightly through
.github/workflows/leaderboard.yml. Settings below can be changed freely.
"""
import collections, datetime, json, os, sys, time, urllib.error, urllib.parse, urllib.request

REGIONS = {  # label: (platform host, regional host, op.gg slug)
    "EUW": ("euw1", "europe", "euw"),
    "KR": ("kr", "asia", "kr"),
    "NA": ("na1", "americas", "na"),
}
MAX_PLAYERS = int(os.environ.get("LB_MAX_PLAYERS", "1500"))  # best players per region that get looked at
MIN_POINTS = int(os.environ.get("LB_MIN_POINTS", "10000"))  # Kayle mastery points needed to be checked closely
RECENT_DAYS = int(os.environ.get("LB_RECENT_DAYS", "21"))   # Kayle must have been played within this many days
MATCHES = int(os.environ.get("LB_MATCHES", "30"))           # recent ranked games checked per player
MIN_GAMES = int(os.environ.get("LB_MIN_GAMES", "2"))        # Kayle games needed to appear
PINNED = [  # always on the board, whatever their rank and recent games ("Name#TAG")
    "Kayle 1v9#STRM", "SenseyMaster123#EUW2", "예비군11#KR2", "Saneryus#TTV",
    "KAYLEKING#wish", "RaiderGO#R1GO", "죽기 아니면 살기#0305",
]
ME = "Kayle 1v9#STRM"  # gets a small "Creator" badge
SHARDS = {  # active shard from Riot -> (platform host, regional host, op.gg slug, label)
    "euw": ("euw1", "europe", "euw", "EUW"), "eune": ("eun1", "europe", "eune", "EUNE"),
    "na": ("na1", "americas", "na", "NA"), "kr": ("kr", "asia", "kr", "KR"),
    "tr": ("tr1", "europe", "tr", "TR"), "ru": ("ru", "europe", "ru", "RU"),
    "jp": ("jp1", "asia", "jp", "JP"), "br": ("br1", "americas", "br", "BR"),
    "lan": ("la1", "americas", "lan", "LAN"), "las": ("la2", "americas", "las", "LAS"),
    "oce": ("oc1", "sea", "oce", "OCE"),
}
TIER_ORDER = {"CHALLENGER": 9, "GRANDMASTER": 8, "MASTER": 7, "DIAMOND": 6, "EMERALD": 5, "PLATINUM": 4,
              "GOLD": 3, "SILVER": 2, "BRONZE": 1, "IRON": 0}
DIV_ORDER = {"I": 3, "II": 2, "III": 1, "IV": 0}
APEX = ("CHALLENGER", "GRANDMASTER", "MASTER")
UA = "Mozilla/5.0 (compatible; kayle1v9-leaderboard/1.0; +https://kayle1v9.com)"
LIST_SIZE = 25                                              # players kept in the file
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def diagnose(host):
    """Prints how Riot answers a few different endpoints, to find out why a key is refused."""
    print("--- diagnosis ---", flush=True)
    for h, path in ((host, "/lol/status/v4/platform-data"), (host, "/lol/platform/v3/champion-rotations"),
                    (host, "/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"),
                    ("europe", "/riot/account/v1/accounts/by-riot-id/Riot/EUW")):
        req = urllib.request.Request("https://%s.api.riotgames.com%s" % (h, path),
                                     headers={"X-Riot-Token": os.environ["RIOT_API_KEY"].strip(), "User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(h, path, "->", r.status, flush=True)
        except urllib.error.HTTPError as e:
            print(h, path, "->", e.code, e.read()[:160].decode("utf8", "replace"), flush=True)
        except Exception as e:
            print(h, path, "-> error", repr(e)[:120], flush=True)
    print("-----------------", flush=True)


def get(host, path, params=None, tries=6, soft403=False):
    url = "https://%s.api.riotgames.com%s" % (host, path)
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for n in range(tries):
        req = urllib.request.Request(url, headers={"X-Riot-Token": os.environ["RIOT_API_KEY"].strip(), "User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "5")) + 1)
            elif e.code in (404, 400):
                return None
            elif e.code in (401, 403):
                if soft403:
                    raise PermissionError(path)
                diagnose(host)
                sys.exit("Riot API refused the key (HTTP %d) on %s. Is RIOT_API_KEY valid and not expired?" % (e.code, path))
            else:
                time.sleep(3 * (n + 1))
        except Exception:
            time.sleep(3 * (n + 1))
    return None


def final_items():
    """Completed items only (no components, boots or consumables), with names, from Data Dragon."""
    with urllib.request.urlopen("https://ddragon.leagueoflegends.com/api/versions.json", timeout=30) as r:
        ver = json.load(r)[0]
    with urllib.request.urlopen("https://ddragon.leagueoflegends.com/cdn/%s/data/en_US/item.json" % ver, timeout=30) as r:
        d = json.load(r)["data"]
    return {int(k): v["name"] for k, v in d.items()
            if v.get("gold", {}).get("total", 0) >= 2200 and not v.get("into") and v.get("maps", {}).get("11")}


def kayle_stats(reg, puuid, items_ok, cache):
    ids = get(reg, "/lol/match/v5/matches/by-puuid/%s/ids" % puuid, {"queue": 420, "type": "ranked", "count": MATCHES}) or []
    games = wins = 0
    its = collections.Counter()
    for mid in ids:
        if mid not in cache:
            m = get(reg, "/lol/match/v5/matches/%s" % mid)
            cache[mid] = (m or {}).get("info", {}).get("participants", [])
        for p in cache[mid]:
            if p.get("puuid") == puuid and p.get("championName") == "Kayle":
                games += 1
                wins += 1 if p.get("win") else 0
                for i in range(6):
                    if p.get("item%d" % i) in items_ok:
                        its[p["item%d" % i]] += 1
    return len(ids), games, wins, its


def score(tier, div, lp):
    if not tier:
        return -1
    return TIER_ORDER.get(tier, 0) * 100000 + (0 if tier in APEX else DIV_ORDER.get(div, 0) * 1000) + (lp or 0)


def pinned_player(riot_id, items_ok, cache):
    name, tag = [x.strip() for x in riot_id.rsplit("#", 1)]
    acc = get("europe", "/riot/account/v1/accounts/by-riot-id/%s/%s" % (urllib.parse.quote(name), urllib.parse.quote(tag)))
    if not acc or not acc.get("puuid"):
        print("pinned: %s not found" % riot_id, flush=True)
        return None
    puuid = acc["puuid"]
    sh = get("europe", "/riot/account/v1/active-shards/by-game/lol/by-puuid/%s" % puuid) or {}
    shard = SHARDS.get(sh.get("activeShard", ""))
    if not shard:
        print("pinned: %s has unknown region %r" % (riot_id, sh.get("activeShard")), flush=True)
        return None
    plat, reg, slug, label = shard
    tier = div = None
    lp = None
    for e in get(plat, "/lol/league/v4/entries/by-puuid/%s" % puuid) or []:
        if e.get("queueType") == "RANKED_SOLO_5x5":
            tier, div, lp = e.get("tier"), e.get("rank"), e.get("leaguePoints")
    n_ids, games, wins, its = kayle_stats(reg, puuid, items_ok, cache)
    shown = "%s#%s" % (acc.get("gameName", name), acc.get("tagLine", tag))
    print("  pinned %s %s %s: %d games checked, %d on Kayle" % (label, shown, tier, n_ids, games), flush=True)
    t = "Unranked" if not tier else tier.capitalize() + ("" if tier in APEX else " " + (div or ""))
    return {"n": shown, "r": label, "t": t, "lp": lp, "g": games, "w": round(100.0 * wins / games, 1) if games else None,
            "u": "https://www.op.gg/summoners/%s/%s-%s" % (slug, urllib.parse.quote(acc.get("gameName", name)), urllib.parse.quote(acc.get("tagLine", tag))),
            "it": [i for i, _ in its.most_common(3)], "_its": its, "_puuid": puuid, "_s": score(tier, div, lp), "_apex": tier in APEX,
            "me": riot_id == ME}


def main():
    k = os.environ.get("RIOT_API_KEY", "").strip()
    print("key check: length %d, starts with RGAPI-: %s" % (len(k), k.startswith("RGAPI-")), flush=True)
    if not k:
        sys.exit("RIOT_API_KEY is empty. Add it as a repository secret named RIOT_API_KEY.")
    items_ok = final_items()
    print("item list: %d completed items" % len(items_ok), flush=True)
    today = datetime.date.today().isoformat()
    cand = []
    for label, (plat, reg, slug) in REGIONS.items():
        pool = []
        for lg in ("challengerleagues", "grandmasterleagues", "masterleagues"):
            d = get(plat, "/lol/league/v4/%s/by-queue/RANKED_SOLO_5x5" % lg)
            print(plat, lg, "->", "no answer" if not d else "%d entries, first keys: %s" % (len(d.get("entries", [])), sorted((d.get("entries") or [{}])[0].keys())), flush=True)
            if not d:
                continue
            for e in d.get("entries", []):
                if e.get("puuid"):
                    pool.append((e["leaguePoints"], d.get("tier", "").capitalize(), e["puuid"]))
        pool.sort(reverse=True)
        for lp, tier, puuid in pool[:MAX_PLAYERS]:
            cand.append((label, reg, slug, lp, tier, puuid))
    print("looking at %d players" % len(cand), flush=True)
    # Cheap pre-filter: one mastery request per player tells who really plays Kayle (champion id 10).
    now_ms = time.time() * 1000
    keep, denied = [], False
    for c in cand:
        label, reg, slug, lp, tier, puuid = c
        plat = REGIONS[label][0]
        try:
            m = get(plat, "/lol/champion-mastery/v4/champion-masteries/by-puuid/%s/by-champion/10" % puuid, soft403=True)
        except PermissionError:
            denied = True
            break
        if m and m.get("championPoints", 0) >= MIN_POINTS and now_ms - m.get("lastPlayTime", 0) <= RECENT_DAYS * 86400000:
            keep.append(c)
    if denied:
        print("mastery endpoint not allowed for this key, falling back to checking the %d best players per region" % 60, flush=True)
        per = collections.Counter()
        keep = []
        for c in cand:
            if per[c[0]] < 60:
                per[c[0]] += 1
                keep.append(c)
    cand = keep
    print("%d Kayle players to check closely" % len(cand), flush=True)

    match_cache, found = {}, []
    for label, reg, slug, lp, tier, puuid in cand:
        n_ids, games, wins, its = kayle_stats(reg, puuid, items_ok, match_cache)
        print("  %s %s LP %d: %d ranked games checked, %d on Kayle" % (label, tier, lp, n_ids, games), flush=True)
        if games >= MIN_GAMES:
            acc = get(reg, "/riot/account/v1/accounts/by-puuid/%s" % puuid)
            if not acc or not acc.get("gameName"):
                continue
            name = "%s#%s" % (acc["gameName"], acc["tagLine"])
            url = "https://www.op.gg/summoners/%s/%s-%s" % (slug, urllib.parse.quote(acc["gameName"]), urllib.parse.quote(acc["tagLine"]))
            found.append({"n": name, "r": label, "t": tier, "lp": lp, "g": games, "w": round(100.0 * wins / games, 1),
                          "u": url, "it": [i for i, _ in its.most_common(3)], "_its": its, "_puuid": puuid,
                          "_s": score(tier.upper(), None, lp), "_apex": True, "me": name == ME})

    pins = []
    for rid in PINNED:
        pl = pinned_player(rid, items_ok, match_cache)
        if pl:
            pins.append(pl)
    pin_ids = {p["_puuid"] for p in pins}
    auto = sorted([p for p in found if p["_puuid"] not in pin_ids], key=lambda p: -p["_s"])[:max(0, LIST_SIZE - len(pins))]
    found = sorted(pins + auto, key=lambda p: -p["_s"])
    if not found:
        sys.exit("no qualifying players found, leaving the old file untouched")

    total = collections.Counter()
    for p in found:
        for i, c in p["_its"].items():
            total[i] += c
    games_total = sum(p["g"] for p in found) or 1
    top_items = [{"id": i, "n": items_ok[i], "p": round(100.0 * c / games_total)} for i, c in total.most_common(6)]
    for p in found:
        for k in ("_its", "_puuid", "_s"):
            p.pop(k, None)

    hp = os.path.join(ROOT, "data", "lb_history.json")
    hist = json.load(open(hp)) if os.path.exists(hp) else {"lp": {}}
    for p in found:
        if p.get("_apex") and p["lp"] is not None:
            hist["lp"].setdefault(p["n"], {})[today] = p["lp"]
    os.makedirs(os.path.dirname(hp), exist_ok=True)
    dates = sorted({d for v in hist["lp"].values() for d in v})[-30:]
    hist["lp"] = {n: {d: v for d, v in s.items() if d in dates} for n, s in hist["lp"].items()}
    json.dump(hist, open(hp, "w"))
    series = [{"n": p["n"], "lp": [hist["lp"].get(p["n"], {}).get(d) for d in dates]} for p in found if p.get("_apex")][:5]
    for p in found:
        p.pop("_apex", None)

    out = {"updated": today, "players": found, "items": top_items, "history": {"dates": dates, "series": series}}
    json.dump(out, open(os.path.join(ROOT, "leaderboard.json"), "w"), ensure_ascii=False, indent=1)
    print("wrote leaderboard.json with %d players" % len(found))


if __name__ == "__main__":
    main()
