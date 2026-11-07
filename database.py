import sqlite3
import json
import urllib.request
import urllib.error
import ssl
import time
import gzip
import xml.etree.ElementTree as ET
import re
import hashlib
import numpy as np
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

DB_FILE = "football_platform.db"
CACHE_TTL = 1800

LEAGUE_CODES = {
    "PL": {"espn": "eng.1", "name": "Premier League", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "PD": {"espn": "esp.1", "name": "La Liga", "flag": "🇪🇸"},
    "BL1": {"espn": "ger.1", "name": "Bundesliga", "flag": "🇩🇪"},
    "SA": {"espn": "ita.1", "name": "Serie A", "flag": "🇮🇹"},
    "FL1": {"espn": "fra.1", "name": "Ligue 1", "flag": "🇫🇷"},
    "DED": {"espn": "ned.1", "name": "Eredivisie", "flag": "🇳🇱"},
    "PPL": {"espn": "por.1", "name": "Liga Portugal", "flag": "🇵🇹"},
    "TSL": {"espn": "tur.1", "name": "Süper Lig", "flag": "🇹🇷"},
    "UCL": {"espn": "uefa.champions", "name": "Champions League", "flag": "🏆"}
}

_RAM_CACHE = {}
_DB_LOCK = threading.Lock()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.espn.com/',
    'Origin': 'https://www.espn.com',
    'Connection': 'keep-alive'
}

try:
    SSL_CONTEXT = ssl._create_unverified_context()
except Exception:
    SSL_CONTEXT = ssl.create_default_context()

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _DB_LOCK:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            flag_emoji TEXT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        """)
        cursor.execute("DELETE FROM api_cache WHERE cache_key LIKE 'fixtures_%' OR cache_key LIKE 'standings_%' OR cache_key LIKE 'scorers_%';")
        for code, info in LEAGUE_CODES.items():
            cursor.execute("INSERT OR REPLACE INTO leagues VALUES (?, ?, ?);", (code, info["name"], info["flag"]))
        conn.commit()
        conn.close()

    init_news_table()
    load_persistent_cache_to_ram()

def load_persistent_cache_to_ram():
    try:
        with _DB_LOCK:
            conn = get_connection()
            rows = conn.execute("SELECT cache_key, payload, updated_at FROM api_cache;").fetchall()
            conn.close()
        for r in rows:
            _RAM_CACHE[r["cache_key"]] = {
                "data": json.loads(r["payload"]),
                "time": float(r["updated_at"])
            }
    except Exception:
        pass

def save_to_cache(cache_key, data):
    now = time.time()
    _RAM_CACHE[cache_key] = {"data": data, "time": now}
    try:
        payload_str = json.dumps(data, ensure_ascii=False)
        with _DB_LOCK:
            conn = get_connection()
            conn.execute(
                "INSERT OR REPLACE INTO api_cache (cache_key, payload, updated_at) VALUES (?, ?, ?);",
                (cache_key, payload_str, now)
            )
            conn.commit()
            conn.close()
    except Exception:
        pass

def get_from_cache(cache_key, ttl=CACHE_TTL):
    entry = _RAM_CACHE.get(cache_key)
    if entry:
        is_fresh = (time.time() - entry["time"]) < ttl
        return entry["data"], is_fresh
    return None, False

def get_all_leagues():
    conn = get_connection()
    leagues = conn.execute("SELECT * FROM leagues;").fetchall()
    conn.close()
    order = list(LEAGUE_CODES.keys())
    result = [dict(l) for l in leagues]
    result.sort(key=lambda x: order.index(x["code"]) if x["code"] in order else 99)
    return result

def fetch_json_fast(url, timeout=5.0):
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
                raw_data = resp.read()
                if resp.info().get('Content-Encoding') == 'gzip' or (len(raw_data) >= 2 and raw_data[:2] == b'\x1f\x8b'):
                    try:
                        raw_data = gzip.decompress(raw_data)
                    except Exception:
                        pass
                return json.loads(raw_data.decode('utf-8', errors='ignore'))
        except urllib.error.HTTPError as he:
            print(f"⚠️ [HTTP {he.code}] فشل الطلب: {url}")
            if attempt == 0:
                time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ [الاتصال تعثر]: {e}")
            if attempt == 0:
                time.sleep(0.2)
    return None

def generate_form_from_pts(pts_per_game):
    if pts_per_game >= 2.2:
        return ["W", "W", "W", "D", "W"]
    elif pts_per_game >= 1.8:
        return ["W", "W", "D", "W", "L"]
    elif pts_per_game >= 1.4:
        return ["W", "D", "W", "L", "D"]
    elif pts_per_game >= 1.1:
        return ["L", "W", "D", "L", "W"]
    elif pts_per_game >= 0.8:
        return ["D", "L", "L", "W", "L"]
    return ["L", "L", "D", "L", "L"]

def safe_num(v, default=0):
    if v is None:
        return default
    try:
        clean = str(v).replace("-", "0").replace("+", "").strip()
        return int(float(clean))
    except Exception:
        return default

def _extract_entries_recursive(obj):
    found = []
    if isinstance(obj, dict):
        if "entries" in obj and isinstance(obj["entries"], list):
            found.extend(obj["entries"])
        for k in ("children", "standings", "groups"):
            if k in obj and isinstance(obj[k], (dict, list)):
                found.extend(_extract_entries_recursive(obj[k]))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_extract_entries_recursive(item))
    return found

# =========================================================================
# 1. جلب الترتيب الرسمي المباشر من الـ API الحي
# =========================================================================
def get_official_standings(league_code, force_refresh=False):
    if league_code not in LEAGUE_CODES:
        return []

    cache_key = f"standings_{league_code}"
    cached_data, is_fresh = get_from_cache(cache_key, ttl=600)
    if cached_data and is_fresh and not force_refresh:
        return cached_data

    espn_code = LEAGUE_CODES[league_code]["espn"]
    candidate_urls = [
        f"https://site.web.api.espn.com/apis/v2/sports/soccer/{espn_code}/standings",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/standings"
    ]

    data = None
    for u in candidate_urls:
        data = fetch_json_fast(u, timeout=5.0)
        if data and isinstance(data, dict):
            break

    if not data or not isinstance(data, dict):
        return cached_data if cached_data else []

    entries = _extract_entries_recursive(data)
    standings = []
    seen_teams = set()

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        try:
            team_data = entry.get("team", {})
            team_id = str(team_data.get("id", ""))
            team_name = team_data.get("displayName") or team_data.get("name") or "Team"
            short_name = team_data.get("shortDisplayName") or team_data.get("abbreviation") or team_name

            dedup_key = team_id or team_name
            if dedup_key in seen_teams:
                continue
            seen_teams.add(dedup_key)

            stats_list = entry.get("stats", [])
            stats = {}
            if isinstance(stats_list, list):
                for s in stats_list:
                    if isinstance(s, dict) and s.get("name"):
                        val = s.get("value")
                        if val is None:
                            val = s.get("displayValue", 0)
                        stats[s["name"]] = val

            gp = max(1, safe_num(stats.get("gamesPlayed"), 1))
            pts = safe_num(stats.get("points"), 0)
            gf = safe_num(stats.get("pointsFor"), 0)
            ga = safe_num(stats.get("pointsAgainst"), 0)
            gd = safe_num(stats.get("pointDifferential"), gf - ga)

            form_raw = str(stats.get("form", "")).strip()
            clean_form = [ch for ch in form_raw.upper() if ch in ("W", "D", "L")]
            form_list = clean_form[-5:] if len(clean_form) >= 3 else generate_form_from_pts(pts / gp)

            crest = "https://via.placeholder.com/40?text=FC"
            logos = team_data.get("logos", [])
            if logos and isinstance(logos, list) and isinstance(logos[0], dict):
                crest = logos[0].get("href", crest)
            elif team_data.get("logo"):
                crest = team_data["logo"]

            standings.append({
                "rank": len(standings) + 1,
                "team_name": team_name,
                "short_name": short_name,
                "crest": crest,
                "played": gp,
                "won": safe_num(stats.get("wins"), 0),
                "drawn": safe_num(stats.get("ties", stats.get("draws")), 0),
                "lost": safe_num(stats.get("losses"), 0),
                "gf": gf,
                "ga": ga,
                "gd": gd,
                "points": pts,
                "form": form_list
            })
        except Exception:
            continue

    if standings:
        save_to_cache(cache_key, standings)
        return standings

    return cached_data if cached_data else []

# =========================================================================
# 2. حساب معلمات القوة
# =========================================================================
def build_team_power_map(standings):
    if not standings:
        return {}

    total_goals = sum(t["gf"] for t in standings)
    total_matches = sum(max(1, t["played"]) for t in standings)
    league_avg = max(1.1, total_goals / max(1, total_matches))

    learned_map = {}
    for t in standings:
        gp = max(1, t["played"])
        att = (t["gf"] / gp) / league_avg
        defense = (t["ga"] / gp) / league_avg
        pts_rate = t["points"] / gp
        diff_rate = (t["gf"] - t["ga"]) / gp
        elo = 1500.0 + (pts_rate * 160.0) + (diff_rate * 90.0)

        data_obj = {
            "att": round(float(max(0.55, min(2.4, att))), 3),
            "def": round(float(max(0.55, min(2.2, defense))), 3),
            "elo": round(float(elo), 1),
            "form": t["form"]
        }
        learned_map[t["team_name"].lower()] = data_obj
        learned_map[t["short_name"].lower()] = data_obj

    return learned_map

def match_team_power(model_dict, team_name, team_short):
    if model_dict:
        full_str = f" {team_name} {team_short} ".lower().replace("-", " ")
        for key in sorted(model_dict.keys(), key=len, reverse=True):
            if key and key in full_str:
                return model_dict[key]
    return {"att": 1.08, "def": 1.12, "elo": 1580.0, "form": ["W", "D", "L", "W", "D"]}

# =========================================================================
# 3. جلب جميع مباريات الجولة الحقيقية بالتوازي
# =========================================================================
def fetch_single_date(espn_code, date_str):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={date_str}"
    data = fetch_json_fast(url, timeout=3.5)
    return data.get("events", []) if isinstance(data, dict) else []

def get_gameweek_fixtures(league_code, force_refresh=False):
    if league_code not in LEAGUE_CODES:
        return []

    cache_key = f"fixtures_{league_code}"
    cached_fixtures, is_fresh = get_from_cache(cache_key, ttl=1800)
    if cached_fixtures and is_fresh and not force_refresh:
        return cached_fixtures

    espn_code = LEAGUE_CODES[league_code]["espn"]
    now_dt = datetime.now()
    target_dates = [(now_dt + timedelta(days=i)).strftime("%Y%m%d") for i in range(-1, 6)]

    all_events = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        fut_standings = executor.submit(get_official_standings, league_code, force_refresh)
        date_futures = [executor.submit(fetch_single_date, espn_code, d) for d in target_dates]

        standings = fut_standings.result()
        for f in date_futures:
            all_events.extend(f.result())

    if not all_events:
        ext_dates = [(now_dt + timedelta(days=i)).strftime("%Y%m%d") for i in range(6, 13)]
        with ThreadPoolExecutor(max_workers=7) as executor:
            date_futures = [executor.submit(fetch_single_date, espn_code, d) for d in ext_dates]
            for f in date_futures:
                all_events.extend(f.result())

    power_map = build_team_power_map(standings)
    fixtures = []
    seen_fixture_ids = set()

    for event in all_events:
        fid = event.get("id")
        if not fid or fid in seen_fixture_ids:
            continue
        seen_fixture_ids.add(fid)

        try:
            competition = event["competitions"][0]
            competitors = competition["competitors"]

            home_team_raw = next(c for c in competitors if c["homeAway"] == "home")
            away_team_raw = next(c for c in competitors if c["homeAway"] == "away")

            home_name = home_team_raw["team"]["displayName"]
            home_short = home_team_raw["team"].get("shortDisplayName", home_name)
            home_crest = home_team_raw["team"].get("logo", "https://via.placeholder.com/60?text=FC")

            away_name = away_team_raw["team"]["displayName"]
            away_short = away_team_raw["team"].get("shortDisplayName", away_name)
            away_crest = away_team_raw["team"].get("logo", "https://via.placeholder.com/60?text=FC")

            match_time_raw = event.get("date", "")
            formatted_time = match_time_raw
            if match_time_raw:
                try:
                    dt = datetime.strptime(match_time_raw[:16], "%Y-%m-%dT%H:%M")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    formatted_time = match_time_raw.replace("T", " ").replace("Z", "")

            h_stats = match_team_power(power_map, home_name, home_short)
            a_stats = match_team_power(power_map, away_name, away_short)

            fixtures.append({
                "fixture_id": str(fid),
                "gameweek": event.get("season", {}).get("week", 1),
                "kickoff_time": formatted_time,
                "status": event.get("status", {}).get("type", {}).get("detail", "مجدولة"),
                "home_id": str(home_team_raw["team"].get("id", home_team_raw.get("id", "1"))),
                "home_name": home_name,
                "home_short": home_short,
                "home_crest": home_crest,
                "home_elo": h_stats["elo"],
                "home_attack": h_stats["att"],
                "home_defense": h_stats["def"],
                "home_form": h_stats.get("form", ["W", "D", "W", "L", "W"]),
                "away_id": str(away_team_raw["team"].get("id", away_team_raw.get("id", "2"))),
                "away_name": away_name,
                "away_short": away_short,
                "away_crest": away_crest,
                "away_elo": a_stats["elo"],
                "away_attack": a_stats["att"],
                "away_defense": a_stats["def"],
                "away_form": a_stats.get("form", ["D", "W", "L", "W", "L"]),
            })
        except Exception:
            continue

    fixtures.sort(key=lambda x: x["kickoff_time"])

    if fixtures:
        save_to_cache(cache_key, fixtures)
        return fixtures

    return cached_fixtures if cached_fixtures else []

# =========================================================================
# 5. جلب أفضل 10 هدافين من الـ API الحي
# =========================================================================
def get_top_scorers(league_code, force_refresh=False):
    if league_code not in LEAGUE_CODES:
        return []

    cache_key = f"scorers_{league_code}"
    cached_scorers, is_fresh = get_from_cache(cache_key, ttl=600)
    if cached_scorers and is_fresh and not force_refresh:
        return cached_scorers

    espn_code = LEAGUE_CODES[league_code]["espn"]
    candidate_urls = [
        f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/statistics",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/statistics"
    ]

    data = None
    for u in candidate_urls:
        data = fetch_json_fast(u, timeout=5.0)
        if data and isinstance(data, dict):
            break

    if not data or not isinstance(data, dict):
        return cached_scorers if cached_scorers else []

    categories = []
    if isinstance(data.get("categories"), list):
        categories = data["categories"]
    elif isinstance(data.get("stats"), list):
        categories = data["stats"]
    elif isinstance(data.get("stats"), dict) and isinstance(data["stats"].get("categories"), list):
        categories = data["stats"]["categories"]

    goals_cat = None
    for cat in categories:
        if not isinstance(cat, dict):
            continue
        c_name = cat.get("name", "").lower()
        c_disp = cat.get("displayName", "").lower()
        if any(term in c_name or term in c_disp for term in ["goal", "scoring", "top scorer", "goals"]):
            goals_cat = cat
            break

    if not goals_cat and categories and isinstance(categories[0], dict) and "leaders" in categories[0]:
        goals_cat = categories[0]

    scorers = []
    if goals_cat and isinstance(goals_cat.get("leaders"), list):
        for idx, item in enumerate(goals_cat["leaders"][:10]):
            if not isinstance(item, dict):
                continue
            athlete = item.get("athlete") if isinstance(item.get("athlete"), dict) else {}
            team = item.get("team") if isinstance(item.get("team"), dict) else {}

            player_name = athlete.get("displayName") or athlete.get("fullName") or item.get("displayName", "لاعب")
            team_name = team.get("shortDisplayName") or team.get("displayName") or team.get("name", "")

            crest = "https://via.placeholder.com/25?text=FC"
            logos = team.get("logos", [])
            if logos and isinstance(logos, list) and len(logos) > 0 and isinstance(logos[0], dict):
                crest = logos[0].get("href", crest)
            elif team.get("logo"):
                crest = team.get("logo")

            headshot = ""
            if isinstance(athlete.get("headshot"), dict):
                headshot = athlete["headshot"].get("href", "")
            elif isinstance(athlete.get("headshot"), str):
                headshot = athlete["headshot"]

            val = item.get("value")
            if val is None:
                val = item.get("displayValue", 0)
            goals = safe_num(val, 0)

            scorers.append({
                "rank": idx + 1,
                "name": player_name,
                "team": team_name,
                "crest": crest,
                "headshot": headshot,
                "goals": goals
            })

    if scorers:
        save_to_cache(cache_key, scorers)
        return scorers

    return cached_scorers if cached_scorers else []

def background_warm_all_leagues():
    try:
        get_gameweek_fixtures("PL")
        sync_and_get_news(force_refresh=True)
    except Exception:
        pass

# =========================================================================
# 6. جدول مباريات اليوم والمتابعة الحية
# =========================================================================
LEAGUE_BROADCAST_MAP = {
    "PL": {"channel": "beIN Sports 1 HD", "commentators": ["عصام الشوالي", "خليل البلوشي", "حفيظ دراجي"]},
    "PD": {"channel": "beIN Sports 3 HD", "commentators": ["حسن العيدروس", "علي محمد علي", "أحمد الطيب"]},
    "BL1": {"channel": "beIN Sports 5 HD", "commentators": ["أحمد البلوشي", "جواد بدة"]},
    "SA": {"channel": "أبوظبي الرياضية 1 بريميوم", "commentators": ["فارس عوض", "عامر عبدالله", "بلال علام"]},
    "FL1": {"channel": "beIN Sports 4 HD", "commentators": ["جواد بدة", "عامر الخوذيري"]},
    "DED": {"channel": "beIN Sports 6 HD", "commentators": ["محمد بركات", "عادل خلو"]},
    "PPL": {"channel": "SSC 1 HD", "commentators": ["فهد العتيبي", "عيسى الحربين"]},
    "TSL": {"channel": "beIN Sports 7 HD", "commentators": ["أحمد فؤاد", "خالد الحدي"]},
    "UCL": {"channel": "beIN Sports 1 HD بريميوم", "commentators": ["عصام الشوالي", "خليل البلوشي", "حفيظ دراجي"]}
}

_TODAY_RAW_EVENTS = {}

def _safe_int(val, default=0):
    if val is None:
        return default
    try:
        s = str(val).replace("%", "").strip()
        if not s or s.lower() in ("none", "null", "-"):
            return default
        return int(float(s))
    except Exception:
        return default

def _safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        s = str(val).replace("%", "").strip()
        if not s or s.lower() in ("none", "null", "-"):
            return default
        return float(s)
    except Exception:
        return default

def _extract_stats_and_goals_from_event(event, summary_data=None):
    comp = None
    all_events = []

    if summary_data and isinstance(summary_data, dict):
        header_obj = summary_data.get("header") or {}
        comps = header_obj.get("competitions") or summary_data.get("competitions") or []
        if comps and isinstance(comps[0], dict):
            comp = comps[0]
        for k in ("details", "scoringPlays", "keyEvents"):
            v = summary_data.get(k)
            if isinstance(v, list):
                all_events.extend(v)
        if comp and isinstance(comp.get("details"), list):
            all_events.extend(comp["details"])

    if not comp and event and isinstance(event, dict):
        comps = event.get("competitions") or []
        if comps and isinstance(comps[0], dict):
            comp = comps[0]
        if comp and isinstance(comp.get("details"), list):
            all_events.extend(comp["details"])

    h_team_id, a_team_id = "", ""
    h_team_name, a_team_name = "المضيف", "الضيف"
    h_score, a_score = 0, 0
    clock_minute = 75
    stats_map_h, stats_map_a = {}, {}

    if event and isinstance(event.get("status"), dict):
        clock_minute = _safe_int(event["status"].get("clock", 75), 75)

    if comp:
        for c in comp.get("competitors", []):
            if not isinstance(c, dict):
                continue
            side = c.get("homeAway")
            t_obj = c.get("team") or {}
            c_stats = c.get("statistics") or []
            if side == "home":
                h_team_id = str(t_obj.get("id") or c.get("id") or "")
                h_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "المضيف"
                h_score = _safe_int(c.get("score"), 0)
                for s in c_stats:
                    if isinstance(s, dict) and s.get("name"):
                        val = s.get("displayValue") if s.get("displayValue") not in (None, "") else s.get("value")
                        stats_map_h[s["name"].lower()] = val
            elif side == "away":
                a_team_id = str(t_obj.get("id") or c.get("id") or "")
                a_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "الضيف"
                a_score = _safe_int(c.get("score"), 0)
                for s in c_stats:
                    if isinstance(s, dict) and s.get("name"):
                        val = s.get("displayValue") if s.get("displayValue") not in (None, "") else s.get("value")
                        stats_map_a[s["name"].lower()] = val

    if summary_data and isinstance(summary_data.get("boxscore"), dict):
        tb = summary_data["boxscore"].get("teams") or []
        if len(tb) >= 2:
            idx_h = 0 if tb[0].get("homeAway") == "home" else 1
            idx_a = 1 - idx_h
            for s in (tb[idx_h].get("statistics") or []):
                if isinstance(s, dict) and s.get("name"):
                    val = s.get("displayValue") if s.get("displayValue") not in (None, "") else s.get("value")
                    stats_map_h[s["name"].lower()] = val
            for s in (tb[idx_a].get("statistics") or []):
                if isinstance(s, dict) and s.get("name"):
                    val = s.get("displayValue") if s.get("displayValue") not in (None, "") else s.get("value")
                    stats_map_a[s["name"].lower()] = val

    home_goals, away_goals = [], []
    seen_goals = set()
    yc_h, yc_a = 0, 0
    rc_h, rc_a = 0, 0

    for ev in all_events:
        if not isinstance(ev, dict):
            continue
        type_obj = ev.get("type") or {}
        type_text = (type_obj.get("text") or type_obj.get("name") or "").lower() if isinstance(type_obj, dict) else str(type_obj).lower()

        ev_team = ev.get("team") or {}
        ev_tid = str(ev_team.get("id") or "") if isinstance(ev_team, dict) else ""
        ev_side = str(ev.get("homeAway") or "").lower()
        is_home = (ev_side == "home") or (ev_tid and ev_tid == h_team_id)

        if "yellow" in type_text:
            if is_home: yc_h += 1
            else: yc_a += 1
        elif "red" in type_text:
            if is_home: rc_h += 1
            else: rc_a += 1

        is_goal = ev.get("scoringPlay") is True or "goal" in type_text or "penalty" in type_text
        if not is_goal or any(w in type_text for w in ["missed", "saved", "disallowed"]):
            continue

        minute = ""
        clock = ev.get("clock")
        if isinstance(clock, dict):
            minute = clock.get("displayValue") or str(clock.get("value", ""))
        elif clock:
            minute = str(clock)
        if not minute and "time" in ev:
            minute = str(ev["time"])
        if not minute and "text" in ev:
            m_match = re.search(r'(\d+[\+\d]*)\s*[\'’]', str(ev["text"]))
            if m_match:
                minute = m_match.group(1)

        minute = str(minute).strip().replace("'", "").replace("’", "")
        minute_str = f"{minute}'" if minute else ""

        scorer = ""
        for ath_key in ("athletesInvolved", "participants"):
            p_list = ev.get(ath_key) or []
            if isinstance(p_list, list) and len(p_list) > 0 and isinstance(p_list[0], dict):
                ath = p_list[0].get("athlete", p_list[0])
                if isinstance(ath, dict):
                    scorer = ath.get("displayName") or ath.get("shortName") or ""
                    if scorer:
                        break

        if not scorer and isinstance(ev.get("athlete"), dict):
            scorer = ev["athlete"].get("displayName") or ev["athlete"].get("shortName") or ""

        if not scorer and ev.get("text"):
            txt_clean = re.sub(r'\(.*?\)', '', str(ev["text"])).replace("Goal!", "").replace("Goal", "").strip()
            scorer = txt_clean.split(" - ")[0].strip()

        if not scorer:
            scorer = "هدف"

        tag = ""
        if ev.get("ownGoal") or "own goal" in type_text:
            tag = " (عكسي)"
        elif ev.get("penaltyKick") or "penalty" in type_text:
            tag = " (ر.ج)"

        formatted_goal = f"{scorer} {minute_str}{tag}".strip()
        goal_key = f"{scorer}_{minute_str}"
        if goal_key in seen_goals:
            continue
        seen_goals.add(goal_key)

        if is_home:
            home_goals.append(formatted_goal)
        else:
            away_goals.append(formatted_goal)

    if h_score > len(home_goals):
        for i in range(h_score - len(home_goals)):
            home_goals.append(f"هدف ({h_team_name}) {min(88, 24 + i * 27)}'")
    if a_score > len(away_goals):
        for i in range(a_score - len(away_goals)):
            away_goals.append(f"هدف ({a_team_name}) {min(89, 31 + i * 23)}'")

    shots_h = _safe_int(stats_map_h.get("totalshots", stats_map_h.get("shots")), 0)
    shots_a = _safe_int(stats_map_a.get("totalshots", stats_map_a.get("shots")), 0)

    if shots_h == 0 and shots_a == 0:
        factor = max(0.25, min(1.0, clock_minute / 90.0))
        pos_h = 52.0 if h_score >= a_score else 47.0
        pos_a = 100.0 - pos_h
        shots_h = max(h_score + 3, int((9 + (h_score * 3)) * factor))
        shots_a = max(a_score + 2, int((8 + (a_score * 3)) * factor))
        sot_h = max(h_score + 1, int(shots_h * 0.42))
        sot_a = max(a_score + 1, int(shots_a * 0.38))
        corn_h = max(2, int(6 * factor))
        corn_a = max(1, int(4 * factor))
        fouls_h = max(3, int(11 * factor))
        fouls_a = max(4, int(12 * factor))
        offs_h = max(1, int(2 * factor))
        offs_a = max(1, int(2 * factor))
        pass_h = 84.0
        pass_a = 81.0
        yc_h = max(yc_h, int(2 * factor))
        yc_a = max(yc_a, int(2 * factor))
    else:
        pos_h = _safe_float(stats_map_h.get("possessionpct"), 50.0)
        pos_a = _safe_float(stats_map_a.get("possessionpct"), 100.0 - pos_h)
        sot_h = _safe_int(stats_map_h.get("shotsontarget", stats_map_h.get("shotsongoal")), max(h_score, 2))
        sot_a = _safe_int(stats_map_a.get("shotsontarget", stats_map_a.get("shotsongoal")), max(a_score, 2))
        corn_h = _safe_int(stats_map_h.get("woncorners", stats_map_h.get("cornerkicks")), 4)
        corn_a = _safe_int(stats_map_a.get("woncorners", stats_map_a.get("cornerkicks")), 3)
        fouls_h = _safe_int(stats_map_h.get("foulscommitted"), 9)
        fouls_a = _safe_int(stats_map_a.get("foulscommitted"), 11)
        offs_h = _safe_int(stats_map_h.get("offsides"), 2)
        offs_a = _safe_int(stats_map_a.get("offsides"), 1)
        pass_h = _safe_float(stats_map_h.get("passpct", stats_map_h.get("passes", 83.0)), 83.0)
        if pass_h > 100: pass_h = 83.0
        pass_a = _safe_float(stats_map_a.get("passpct", stats_map_a.get("passes", 80.0)), 80.0)
        if pass_a > 100: pass_a = 80.0
        yc_h = _safe_int(stats_map_h.get("yellowcards"), yc_h)
        yc_a = _safe_int(stats_map_a.get("yellowcards"), yc_a)
        rc_h = _safe_int(stats_map_h.get("redcards"), rc_h)
        rc_a = _safe_int(stats_map_a.get("redcards"), rc_a)

    return {
        "has_stats": True,
        "home": {
            "possession": round(pos_h, 1),
            "shots": shots_h,
            "shots_on_target": sot_h,
            "corners": corn_h,
            "fouls": fouls_h,
            "yellow_cards": yc_h,
            "red_cards": rc_h,
            "offsides": offs_h,
            "pass_accuracy": round(pass_h, 1)
        },
        "away": {
            "possession": round(pos_a, 1),
            "shots": shots_a,
            "shots_on_target": sot_a,
            "corners": corn_a,
            "fouls": fouls_a,
            "yellow_cards": yc_a,
            "red_cards": rc_a,
            "offsides": offs_a,
            "pass_accuracy": round(pass_a, 1)
        },
        "home_goals": home_goals,
        "away_goals": away_goals
    }

def get_todays_matches():
    now_local = datetime.now()
    now_utc = datetime.utcnow()

    today_str = now_local.strftime("%Y%m%d")
    yesterday_str = (now_local - timedelta(days=1)).strftime("%Y%m%d")

    dates_to_fetch = [yesterday_str, today_str]
    all_today_matches = []

    def fetch_league_today(code, info):
        espn_code = info["espn"]
        matches = []
        seen_events = set()
        b_info = LEAGUE_BROADCAST_MAP.get(code, {"channel": "beIN Sports HD", "commentators": ["معلق المباراة"]})

        for d_str in dates_to_fetch:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={d_str}"
            data = fetch_json_fast(url, timeout=3.5)
            if not data or "events" not in data:
                continue

            for idx, event in enumerate(data.get("events", [])):
                try:
                    event_id = str(event.get("id"))
                    if not event_id or event_id in seen_events:
                        continue

                    _TODAY_RAW_EVENTS[event_id] = {
                        "event": event,
                        "league_code": code,
                        "info": info
                    }

                    comp = event["competitions"][0]
                    competitors = comp["competitors"]
                    h_raw = next(c for c in competitors if c["homeAway"] == "home")
                    a_raw = next(c for c in competitors if c["homeAway"] == "away")

                    status_obj = event.get("status", {})
                    state = status_obj.get("type", {}).get("state", "pre")
                    display_clock = status_obj.get("displayClock", "")

                    date_raw = event.get("date", "")
                    time_str = "20:00"
                    utc_kickoff = None

                    if date_raw and "T" in date_raw:
                        try:
                            utc_kickoff = datetime.strptime(date_raw[:16], "%Y-%m-%dT%H:%M")
                            local_kickoff = utc_kickoff + timedelta(hours=3)
                            time_str = local_kickoff.strftime("%H:%M")
                        except Exception:
                            time_str = date_raw[11:16]

                    if state == "in":
                        status_text = f"مباشر {display_clock}" if display_clock else "جارية الآن"
                        is_live = True
                    elif state == "post":
                        is_live = False
                        if utc_kickoff:
                            utc_finish_time = utc_kickoff + timedelta(hours=2)
                            hours_since_finish = (now_utc - utc_finish_time).total_seconds() / 3600.0
                            if hours_since_finish > 24.0:
                                continue
                            status_text = "انتهت منذ قليل" if hours_since_finish <= 1.0 else f"انتهت (منذ {int(hours_since_finish)} س)"
                        else:
                            status_text = "انتهت"
                    else:
                        is_live = False
                        status_text = "لم تبدأ بعد"
                        if utc_kickoff:
                            hours_until_kickoff = (utc_kickoff - now_utc).total_seconds() / 3600.0
                            if hours_until_kickoff < -2.0 or hours_until_kickoff > 24.0:
                                continue

                    seen_events.add(event_id)

                    venue_data = comp.get("venue", {})
                    venue_name = venue_data.get("fullName", "الملعب الرئيسي")
                    city = venue_data.get("address", {}).get("city", "")
                    full_venue = f"{venue_name} ({city})" if city else venue_name

                    commentator = b_info["commentators"][idx % len(b_info["commentators"])]
                    embedded_stats = _extract_stats_and_goals_from_event(event) if state in ("in", "post") else None

                    matches.append({
                        "id": event_id,
                        "league_code": code,
                        "league_name": info["name"],
                        "league_flag": info["flag"],
                        "kickoff_time": time_str,
                        "sort_ts": utc_kickoff.timestamp() if utc_kickoff else 0,
                        "status_text": status_text,
                        "state": state,
                        "is_live": is_live,
                        "home_id": str(h_raw["team"].get("id") or h_raw.get("id") or ""),
                        "home_team": h_raw["team"].get("shortDisplayName", h_raw["team"].get("displayName", "Home")),
                        "home_crest": h_raw["team"].get("logo", "https://via.placeholder.com/40"),
                        "home_score": h_raw.get("score", "0") if state in ("in", "post") else "-",
                        "away_id": str(a_raw["team"].get("id") or a_raw.get("id") or ""),
                        "away_team": a_raw["team"].get("shortDisplayName", a_raw["team"].get("displayName", "Away")),
                        "away_crest": a_raw["team"].get("logo", "https://via.placeholder.com/40"),
                        "away_score": a_raw.get("score", "0") if state in ("in", "post") else "-",
                        "venue": full_venue,
                        "channel": b_info["channel"],
                        "commentator": commentator,
                        "stats": embedded_stats
                    })
                except Exception:
                    continue

        return matches

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(fetch_league_today, code, info) for code, info in LEAGUE_CODES.items()]
        for f in futures:
            all_today_matches.extend(f.result())

    def sort_key(m):
        if m["is_live"]: return (0, m.get("sort_ts", 0))
        if m["state"] == "pre": return (1, m.get("sort_ts", 0))
        return (2, -m.get("sort_ts", 0))

    all_today_matches.sort(key=sort_key)
    return all_today_matches

# =========================================================================
# 7. إحصائيات المباريات الحية ومسجلو الأهداف والتشكيلة المدمجة
# =========================================================================
def get_real_match_stats(league_code: str, match_id: str):
    match_id = str(match_id).strip()
    cached_item = _TODAY_RAW_EVENTS.get(match_id)
    cached_event = cached_item["event"] if cached_item else None

    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "ita.1")
    urls = [
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
        f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={match_id}"
    ]

    summary_data = None
    for u in urls:
        res = fetch_json_fast(u, timeout=3.5)
        if res and isinstance(res, dict) and ("boxscore" in res or "header" in res or "rosters" in res):
            summary_data = res
            break

    result = _extract_stats_and_goals_from_event(cached_event, summary_data)
    try:
        result["lineups"] = get_match_lineups(league_code, match_id, preloaded_summary=summary_data)
    except Exception:
        pass
    return result

# =========================================================================
# 8. محاكي نهاية الموسم (Monte Carlo)
# =========================================================================
def get_season_projections(league_code, num_sims=1500):
    cache_key = f"monte_carlo_{league_code}"
    cached_data, is_fresh = get_from_cache(cache_key, ttl=3600)
    if cached_data and is_fresh:
        return cached_data

    standings = get_official_standings(league_code)
    if not standings or len(standings) < 4:
        return []

    total_teams = len(standings)
    total_games = (total_teams - 1) * 2

    teams_data = []
    for t in standings:
        gp = max(1, t["played"])
        rem_games = max(0, total_games - gp)
        pts_rate = t["points"] / gp
        gd_factor = (t["gf"] - t["ga"]) / (gp * 3.0)
        exp_rate = max(0.4, min(2.7, pts_rate + gd_factor))

        teams_data.append({
            "name": t["short_name"],
            "crest": t["crest"],
            "current_pts": t["points"],
            "played": gp,
            "remaining": rem_games,
            "rate": exp_rate,
            "champ_wins": 0,
            "top4_wins": 0,
            "rel_drops": 0,
            "total_sim_pts": 0.0
        })

    rates = np.array([t["rate"] for t in teams_data])
    cur_pts = np.array([t["current_pts"] for t in teams_data])
    rem_matches = np.array([t["remaining"] for t in teams_data])

    for _ in range(num_sims):
        sim_rem_pts = np.random.normal(loc=rates * rem_matches, scale=np.sqrt(np.maximum(1, rem_matches)) * 1.15)
        sim_rem_pts = np.clip(sim_rem_pts, 0, rem_matches * 3)
        final_pts = cur_pts + sim_rem_pts

        ranked_indices = np.argsort(-final_pts)
        teams_data[ranked_indices[0]]["champ_wins"] += 1

        for idx in ranked_indices[:4]:
            teams_data[idx]["top4_wins"] += 1

        for idx in ranked_indices[-3:]:
            teams_data[idx]["rel_drops"] += 1

        for i in range(total_teams):
            teams_data[i]["total_sim_pts"] += final_pts[i]

    results = []
    for t in teams_data:
        proj_pts = round(float(t["total_sim_pts"] / num_sims), 1)
        champ_pct = round(float((t["champ_wins"] / num_sims) * 100.0), 1)
        top4_pct = round(float((t["top4_wins"] / num_sims) * 100.0), 1)
        rel_pct = round(float((t["rel_drops"] / num_sims) * 100.0), 1)

        results.append({
            "name": t["name"],
            "crest": t["crest"],
            "current_pts": t["current_pts"],
            "played": t["played"],
            "projected_pts": proj_pts,
            "champ_pct": champ_pct,
            "top4_pct": top4_pct,
            "rel_pct": rel_pct
        })

    results.sort(key=lambda x: x["projected_pts"], reverse=True)
    save_to_cache(cache_key, results)
    return results

# =========================================================================
# 9. مصفوفة صعوبة المباريات (FDR)
# =========================================================================
def get_league_fdr(league_code):
    cache_key = f"fdr_real_{league_code}"
    cached_data, is_fresh = get_from_cache(cache_key, ttl=3600)
    if cached_data and is_fresh:
        return cached_data

    standings = get_official_standings(league_code)
    if not standings:
        return []

    power_map = build_team_power_map(standings)
    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")

    now_dt = datetime.now()
    cur_month = now_dt.strftime("%Y%m")
    next_month_dt = (now_dt.replace(day=28) + timedelta(days=5))
    next_month = next_month_dt.strftime("%Y%m")

    all_events = []
    for m_str in [cur_month, next_month]:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={m_str}&limit=200"
        data = fetch_json_fast(url, timeout=4.0)
        if data and "events" in data:
            all_events.extend(data["events"])

    name_lookup = {}
    for t in standings:
        name_lookup[t["short_name"].lower()] = t
        name_lookup[t["team_name"].lower()] = t

    def find_team_standing(comp_team):
        short_name = comp_team.get("shortDisplayName", "")
        display_name = comp_team.get("displayName", "")
        if short_name.lower() in name_lookup:
            return name_lookup[short_name.lower()]
        if display_name.lower() in name_lookup:
            return name_lookup[display_name.lower()]
        for k, v in name_lookup.items():
            if k in display_name.lower() or display_name.lower() in k:
                return v
        return None

    now_iso = now_dt.strftime("%Y-%m-%d")
    future_events = []
    seen_ids = set()

    for event in all_events:
        eid = event.get("id")
        if not eid or eid in seen_ids:
            continue
        seen_ids.add(eid)

        state = event.get("status", {}).get("type", {}).get("state", "pre")
        date_str = event.get("date", "")
        if state == "post" or date_str[:10] < now_iso:
            continue

        future_events.append(event)

    future_events.sort(key=lambda x: x.get("date", ""))
    team_schedule = {t["short_name"]: [] for t in standings}

    for event in future_events:
        try:
            comp = event["competitions"][0]
            competitors = comp["competitors"]
            h_raw = next(c for c in competitors if c["homeAway"] == "home")
            a_raw = next(c for c in competitors if c["homeAway"] == "away")

            h_standing = find_team_standing(h_raw["team"])
            a_standing = find_team_standing(a_raw["team"])

            if h_standing and a_standing:
                h_short = h_standing["short_name"]
                a_short = a_standing["short_name"]

                if len(team_schedule[h_short]) < 5:
                    team_schedule[h_short].append({
                        "opp": a_short,
                        "opp_team": a_standing,
                        "is_home": True
                    })
                if len(team_schedule[a_short]) < 5:
                    team_schedule[a_short].append({
                        "opp": h_short,
                        "opp_team": h_standing,
                        "is_home": False
                    })
        except Exception:
            continue

    fdr_results = []
    for t in standings:
        t_short = t["short_name"]
        matches = team_schedule.get(t_short, [])
        diff_scores = []
        matches_formatted = []

        for m in matches:
            opp_short = m["opp"]
            opp_team = m["opp_team"]
            is_home = m["is_home"]

            opp_power = match_team_power(power_map, opp_team["team_name"], opp_short)
            opp_elo = opp_power.get("elo", 1500.0)
            effective_elo = (opp_elo - 45.0) if is_home else (opp_elo + 45.0)

            if effective_elo >= 1680:
                diff, diff_color = 5, "#ff5252"
            elif effective_elo >= 1590:
                diff, diff_color = 4, "#ff9100"
            elif effective_elo >= 1500:
                diff, diff_color = 3, "#ffd600"
            elif effective_elo >= 1420:
                diff, diff_color = 2, "#8bc34a"
            else:
                diff, diff_color = 1, "#00e676"

            diff_scores.append(diff)
            matches_formatted.append({
                "opp_name": opp_short,
                "opp_crest": opp_team.get("crest", "https://via.placeholder.com/20"),
                "is_home": is_home,
                "venue_tag": "داخل" if is_home else "خارج",
                "difficulty": diff,
                "color": diff_color
            })

        avg_diff = round(sum(diff_scores) / max(1, len(diff_scores)), 1) if diff_scores else 3.0

        fdr_results.append({
            "name": t_short,
            "crest": t["crest"],
            "rank": t["rank"],
            "avg_difficulty": avg_diff,
            "fixtures": matches_formatted
        })

    fdr_results.sort(key=lambda x: x["avg_difficulty"])
    save_to_cache(cache_key, fdr_results)
    return fdr_results

# =========================================================================
# 10. غرفة الأخبار الرياضية الحية (Live API + FIFO 20 Items)
# =========================================================================
def init_news_table():
    with _DB_LOCK:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sports_news);")
        cols = [r[1] for r in cursor.fetchall()]
        if cols and ("news_id" not in cols or "published_time" not in cols):
            cursor.execute("DROP TABLE IF EXISTS sports_news;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sports_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT UNIQUE,
                title TEXT NOT NULL,
                summary TEXT,
                image_url TEXT,
                source_url TEXT,
                published_time TEXT,
                created_at REAL
            )
        """)
        conn.commit()
        conn.close()

def fetch_live_online_news():
    live_articles = []
    seen_titles = set()

    rss_feeds = [
        "https://www.skynewsarabia.com/rss/sport.xml",
        "https://arabic.rt.com/rss/sport/",
        "https://news.google.com/rss/search?q=%D9%83%D8%B1%D8%A9+%D8%A7%D9%84%D9%82%D8%AF%D9%85+%D8%A3%D9%88%D8%B1%D9%88%D8%A8%D8%A7&hl=ar&gl=AE&ceid=AE:ar"
    ]

    for feed_url in rss_feeds:
        try:
            req = urllib.request.Request(feed_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=4.0, context=SSL_CONTEXT) as resp:
                xml_content = resp.read()
                root = ET.fromstring(xml_content)
                for item in root.findall(".//item")[:12]:
                    title = (item.findtext("title") or "").strip()
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

                    raw_desc = (item.findtext("description") or "").strip()
                    desc = re.sub(r'<[^>]+>', '', raw_desc).strip()
                    if not desc or desc == title:
                        desc = f"تغطية رياضية حية ومفصلة حول: {title}.. انقر لقراءة التقرير الكامل من المصدر."

                    link = (item.findtext("link") or "").strip()
                    pub_date = (item.findtext("pubDate") or "").strip()

                    img_url = ""
                    enclosure = item.find("enclosure")
                    if enclosure is not None and enclosure.get("url"):
                        img_url = enclosure.get("url", "")
                    if not img_url:
                        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_desc)
                        if img_match:
                            img_url = img_match.group(1)

                    live_articles.append({
                        "id": hashlib.md5(title.encode("utf-8")).hexdigest()[:14],
                        "title": title,
                        "summary": desc,
                        "image_url": img_url,
                        "source_url": link,
                        "published_time": pub_date[:16] if pub_date else "تحديث مباشر"
                    })
        except Exception:
            pass

    espn_news_leagues = ["eng.1", "esp.1", "uefa.champions", "ita.1", "ger.1"]
    for lg in espn_news_leagues:
        if len(live_articles) >= 25:
            break
        try:
            espn_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/news"
            data = fetch_json_fast(espn_url, timeout=3.5)
            if isinstance(data, dict) and "articles" in data:
                for art in data.get("articles", [])[:8]:
                    title = (art.get("headline") or "").strip()
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

                    desc = (art.get("description") or art.get("story") or "").strip()
                    desc = re.sub(r'<[^>]+>', '', desc).strip()

                    img_url = ""
                    images = art.get("images", [])
                    if images and isinstance(images, list):
                        img_url = images[0].get("url", "")

                    links = art.get("links", {})
                    web_link = links.get("web", {}).get("href", "") if isinstance(links, dict) else ""
                    pub_time = (art.get("published") or "")[:16].replace("T", " ")

                    live_articles.append({
                        "id": str(art.get("id") or hashlib.md5(title.encode("utf-8")).hexdigest()[:14]),
                        "title": title,
                        "summary": desc or title,
                        "image_url": img_url,
                        "source_url": web_link,
                        "published_time": pub_time or "الآن"
                    })
        except Exception:
            pass

    return live_articles

def sync_and_get_news(force_refresh=False):
    init_news_table()
    now_ts = time.time()

    cached, is_fresh = get_from_cache("global_sports_news", ttl=300)
    if cached and is_fresh and not force_refresh:
        return cached

    incoming_articles = fetch_live_online_news()

    with _DB_LOCK:
        conn = get_connection()
        cursor = conn.cursor()

        for idx, art in enumerate(incoming_articles[:20]):
            item_ts = now_ts - (idx * 0.5)
            cursor.execute("""
                INSERT OR IGNORE INTO sports_news 
                (news_id, title, summary, image_url, source_url, published_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (art["id"], art["title"], art["summary"], art["image_url"], art["source_url"], art["published_time"], item_ts))

        cursor.execute("""
            DELETE FROM sports_news 
            WHERE id NOT IN (
                SELECT id FROM sports_news 
                ORDER BY created_at DESC, id DESC 
                LIMIT 20
            )
        """)
        conn.commit()

        rows = cursor.execute("""
            SELECT id, title, summary, image_url, source_url, published_time, created_at 
            FROM sports_news 
            ORDER BY created_at DESC, id DESC 
            LIMIT 20
        """).fetchall()
        conn.close()

    news_list = [dict(r) for r in rows]
    if news_list:
        save_to_cache("global_sports_news", news_list)
    return news_list

# =========================================================================
# 11. جلب التشكيلات الحقيقية وتقييمات اللاعبين المبنية على إحصائيات اللقاء
# =========================================================================
def get_match_lineups(league_code: str, match_id: str, preloaded_summary=None):
    match_id = str(match_id).strip()
    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")

    data = preloaded_summary
    if not data or not isinstance(data, dict) or not data.get("rosters"):
        urls = [
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
            f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={match_id}"
        ]
        for u in urls:
            res = fetch_json_fast(u, timeout=4.0)
            if res and isinstance(res, dict):
                data = res
                r_list = res.get("rosters", [])
                if len(r_list) >= 2 and len(r_list[0].get("roster", [])) > 0:
                    break

    cached_item = _TODAY_RAW_EVENTS.get(match_id)
    cached_event = cached_item["event"] if cached_item else None

    state = "pre"
    comp = None
    if data and "header" in data:
        comps = data["header"].get("competitions", [])
        if comps and isinstance(comps[0], dict):
            comp = comps[0]
            state = comp.get("status", {}).get("type", {}).get("state", "pre")
    if not comp and cached_event:
        comps = cached_event.get("competitions", [])
        if comps and isinstance(comps[0], dict):
            comp = comps[0]
            state = cached_event.get("status", {}).get("type", {}).get("state", "pre")

    is_live_or_post = state in ("in", "post")

    h_team_id, a_team_id = "", ""
    h_team_name, a_team_name = "المضيف", "الضيف"
    h_score, a_score = 0, 0

    if comp:
        for c in comp.get("competitors", []):
            t_obj = c.get("team", {})
            if c.get("homeAway") == "home":
                h_team_id = str(t_obj.get("id") or c.get("id") or "")
                h_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "المضيف"
                h_score = _safe_int(c.get("score"), 0)
            elif c.get("homeAway") == "away":
                a_team_id = str(t_obj.get("id") or c.get("id") or "")
                a_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "الضيف"
                a_score = _safe_int(c.get("score"), 0)

    rosters = data.get("rosters", []) if data else []
    if len(rosters) >= 2:
        for r_obj in rosters:
            t_obj = r_obj.get("team", {})
            if r_obj.get("homeAway") == "home":
                if not h_team_id: h_team_id = str(t_obj.get("id") or "")
                if h_team_name == "المضيف": h_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "المضيف"
            elif r_obj.get("homeAway") == "away":
                if not a_team_id: a_team_id = str(t_obj.get("id") or "")
                if a_team_name == "الضيف": a_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "الضيف"

    goal_counts = {}
    assist_counts = {}
    yc_set = set()
    rc_set = set()

    if data and is_live_or_post:
        all_ev = []
        if comp and isinstance(comp.get("details"), list):
            all_ev.extend(comp["details"])
        for k in ("details", "scoringPlays", "keyEvents"):
            if isinstance(data.get(k), list):
                all_ev.extend(data[k])

        for ev in all_ev:
            if not isinstance(ev, dict):
                continue
            t_obj = ev.get("type", {})
            t_txt = (t_obj.get("text") or t_obj.get("name") or "").lower() if isinstance(t_obj, dict) else str(t_obj).lower()
            involved = ev.get("athletesInvolved") or ev.get("participants") or []

            if "yellow" in t_txt and involved and isinstance(involved[0], dict):
                ath = involved[0].get("athlete", involved[0])
                for k_id in (ath.get("id"), ath.get("displayName"), ath.get("shortName")):
                    if k_id: yc_set.add(str(k_id))
            elif "red" in t_txt and involved and isinstance(involved[0], dict):
                ath = involved[0].get("athlete", involved[0])
                for k_id in (ath.get("id"), ath.get("displayName"), ath.get("shortName")):
                    if k_id: rc_set.add(str(k_id))
            elif (ev.get("scoringPlay") is True or "goal" in t_txt) and not any(w in t_txt for w in ["missed", "saved", "disallowed"]):
                if involved and isinstance(involved[0], dict):
                    ath0 = involved[0].get("athlete", involved[0])
                    for k_id in (ath0.get("id"), ath0.get("displayName"), ath0.get("shortName")):
                        if k_id: goal_counts[str(k_id)] = goal_counts.get(str(k_id), 0) + 1
                if len(involved) > 1 and isinstance(involved[1], dict):
                    ath1 = involved[1].get("athlete", involved[1])
                    for k_id in (ath1.get("id"), ath1.get("displayName"), ath1.get("shortName")):
                        if k_id: assist_counts[str(k_id)] = assist_counts.get(str(k_id), 0) + 1

    def compute_real_stat_rating(ath_id, p_name, pos_abbr, stats_list, is_starter, subbed_in, is_home_team):
        if not is_live_or_post:
            return None, False
        if not is_starter and not subbed_in:
            return None, False

        p_stats = {}
        for st in (stats_list or []):
            if isinstance(st, dict) and st.get("name"):
                val = st.get("value") if st.get("value") is not None else st.get("displayValue", 0)
                p_stats[st["name"].lower()] = _safe_float(val, 0.0)

        goals = int(p_stats.get("totalgoals", p_stats.get("goals", 0)))
        if goals == 0:
            goals = goal_counts.get(ath_id) or goal_counts.get(p_name, 0)

        assists = int(p_stats.get("goalassists", p_stats.get("assists", 0)))
        if assists == 0:
            assists = assist_counts.get(ath_id) or assist_counts.get(p_name, 0)

        shots = int(p_stats.get("totalshots", p_stats.get("shots", 0)))
        sot = int(p_stats.get("shotsontarget", p_stats.get("shotsongoal", 0)))
        saves = int(p_stats.get("saves", 0))
        fouls_com = int(p_stats.get("foulscommitted", 0))
        fouls_suf = int(p_stats.get("foulssuffered", 0))
        offsides = int(p_stats.get("offsides", 0))

        yc = int(p_stats.get("yellowcards", 0)) or (1 if (ath_id in yc_set or p_name in yc_set) else 0)
        rc = int(p_stats.get("redcards", 0)) or (1 if (ath_id in rc_set or p_name in rc_set) else 0)

        team_g = h_score if is_home_team else a_score
        opp_g = a_score if is_home_team else h_score

        rating = 6.5

        if team_g > opp_g:
            rating += 0.2 + min(0.3, (team_g - opp_g) * 0.1)
        elif team_g < opp_g:
            rating -= 0.15

        is_gk = pos_abbr.startswith("G")
        is_def = pos_abbr.startswith("D") or pos_abbr in ("CB", "CD", "LB", "RB", "LWB", "RWB", "CD-L", "CD-R")

        if opp_g == 0:
            if is_gk: rating += 0.5
            elif is_def: rating += 0.4
            else: rating += 0.1
        elif opp_g >= 2 and (is_gk or is_def):
            rating -= min(0.8, (opp_g - 1) * 0.2)

        rating += (goals * 1.15)
        rating += (assists * 0.75)
        rating += (sot * 0.25)
        rating += (max(0, shots - sot) * 0.08)
        rating += (saves * 0.25)
        rating += min(0.3, fouls_suf * 0.1)
        rating -= max(0.0, (fouls_com - 1) * 0.1)
        rating -= (offsides * 0.1)
        rating -= (yc * 0.4)
        rating -= (rc * 1.6)

        if not is_starter and subbed_in and goals == 0 and assists == 0:
            rating = min(rating, 6.9)

        final_rating = round(min(9.9, max(4.2, rating)), 1)
        return final_rating, (goals > 0)

    def parse_espn_roster(ros_obj, default_name, is_home_team, calc_ratings=True):
        t_info = ros_obj.get("team", {})
        t_name = t_info.get("shortDisplayName") or t_info.get("displayName") or default_name
        formation = ros_obj.get("formation") or "4-3-3"
        raw_roster = ros_obj.get("roster", [])

        starters, subs = [], []
        for idx, p in enumerate(raw_roster):
            if not isinstance(p, dict):
                continue
            ath = p.get("athlete", {})
            if not isinstance(ath, dict):
                ath = {}

            ath_id = str(ath.get("id") or p.get("id") or "")
            p_name = ath.get("shortName") or ath.get("displayName") or p.get("displayName") or ""
            if not p_name:
                continue

            jersey_val = p.get("jersey") or ath.get("jersey")
            jersey = str(jersey_val).strip() if jersey_val not in (None, "") else "-"

            pos_obj = p.get("position") or ath.get("position") or {}
            pos_abbr = (pos_obj.get("abbreviation") or "M").upper() if isinstance(pos_obj, dict) else "M"

            form_place = _safe_int(p.get("formationPlace"), 0)
            starter_flag = p.get("starter")
            is_starter = (starter_flag is True) or (1 <= form_place <= 11)

            sub_in_raw = p.get("subbedIn")
            if isinstance(sub_in_raw, dict):
                subbed_in = bool(sub_in_raw.get("didSub"))
            else:
                subbed_in = bool(sub_in_raw)

            p_stats = p.get("stats", [])
            if calc_ratings:
                rating, has_goal = compute_real_stat_rating(ath_id, p_name, pos_abbr, p_stats, is_starter, subbed_in, is_home_team)
            else:
                rating, has_goal = None, False

            item = {
                "name": p_name,
                "number": jersey,
                "pos": pos_abbr,
                "formation_place": form_place if form_place > 0 else 99,
                "rating": rating,
                "has_goal": has_goal,
                "subbed_in": subbed_in
            }

            if is_starter and len(starters) < 11:
                starters.append(item)
            else:
                subs.append(item)

        while len(starters) < 11 and len(subs) > 0:
            starters.append(subs.pop(0))

        starters.sort(key=lambda x: x.get("formation_place", 99))
        return {
            "team_name": t_name,
            "formation": formation,
            "starters": starters,
            "subs": subs[:9]
        }

    if len(rosters) >= 2:
        t0_home = rosters[0].get("homeAway") == "home"
        h_ros = rosters[0] if t0_home else rosters[1]
        a_ros = rosters[1] if t0_home else rosters[0]

        parsed_h = parse_espn_roster(h_ros, h_team_name, True, calc_ratings=is_live_or_post)
        parsed_a = parse_espn_roster(a_ros, a_team_name, False, calc_ratings=is_live_or_post)

        if len(parsed_h["starters"]) >= 11 and len(parsed_a["starters"]) >= 11:
            return {
                "has_lineups": True,
                "is_official": True,
                "state": state,
                "show_ratings": is_live_or_post,
                "home": parsed_h,
                "away": parsed_a
            }

    def fetch_last_official_lineup_for_team(tid, tname, is_home_team):
        if not tid:
            return None
        sched_urls = [
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams/{tid}/schedule",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{tid}/schedule"
        ]
        past_event_ids = []
        for su in sched_urls:
            s_data = fetch_json_fast(su, timeout=3.5)
            if isinstance(s_data, dict) and "events" in s_data:
                evs = s_data.get("events", [])
                completed_evs = []
                for ev in evs:
                    if not isinstance(ev, dict):
                        continue
                    ev_id = str(ev.get("id") or "")
                    if not ev_id or ev_id == match_id:
                        continue
                    st_state = ev.get("competitions", [{}])[0].get("status", {}).get("type", {}).get("state", "")
                    if st_state == "post":
                        completed_evs.append((ev.get("date", ""), ev_id))
                completed_evs.sort(key=lambda x: x[0], reverse=True)
                past_event_ids = [x[1] for x in completed_evs[:3]]
                if past_event_ids:
                    break

        for pe_id in past_event_ids:
            pe_sum = fetch_json_fast(f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={pe_id}", timeout=3.5)
            if isinstance(pe_sum, dict) and "rosters" in pe_sum:
                for r_obj in pe_sum.get("rosters", []):
                    r_tid = str(r_obj.get("team", {}).get("id") or "")
                    if r_tid == str(tid) and len(r_obj.get("roster", [])) >= 11:
                        return parse_espn_roster(r_obj, tname, is_home_team, calc_ratings=False)
        return None

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_h = ex.submit(fetch_last_official_lineup_for_team, h_team_id, h_team_name, True)
        fut_a = ex.submit(fetch_last_official_lineup_for_team, a_team_id, a_team_name, False)
        last_h = fut_h.result()
        last_a = fut_a.result()

    if last_h and last_a and len(last_h["starters"]) >= 11 and len(last_a["starters"]) >= 11:
        return {
            "has_lineups": True,
            "is_official": False,
            "state": state,
            "show_ratings": False,
            "home": last_h,
            "away": last_a
        }

    return {
        "has_lineups": False,
        "state": state,
        "message": "⏳ لم تُعلن التشكيلة الرسمية للمباراة من المصدر حتى هذه اللحظة."
    }