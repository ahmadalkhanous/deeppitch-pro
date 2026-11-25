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
import os
import random
import html
import urllib.parse
import unicodedata
from html.parser import HTMLParser
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

DB_FILE = "football_platform.db"
CACHE_TTL = 1800

DEFAULT_CLUB_CREST = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E"
    "%3Crect width='40' height='40' rx='10' fill='%23121a2b'/%3E"
    "%3Ctext x='20' y='25' text-anchor='middle' fill='%2310b981' font-family='sans-serif' "
    "font-size='14' font-weight='bold'%3EFC%3C/text%3E%3C/svg%3E"
)

LEAGUE_CODES = {
    "PL": {"espn": "eng.1", "name": "Premier League", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "PD": {"espn": "esp.1", "name": "La Liga", "flag": "🇪🇸"},
    "BL1": {"espn": "ger.1", "name": "Bundesliga", "flag": "🇩🇪"},
    "SA": {"espn": "ita.1", "name": "Serie A", "flag": "🇮🇹"},
    "FL1": {"espn": "fra.1", "name": "Ligue 1", "flag": "🇫🇷"},
    "DED": {"espn": "ned.1", "name": "Eredivisie", "flag": "🇳🇱"},
    "PPL": {"espn": "por.1", "name": "Liga Portugal", "flag": "🇵🇹"},
    "TSL": {"espn": "tur.1", "name": "Süper Lig", "flag": "🇹🇷"},
    "UCL": {"espn": "uefa.champions", "name": "Champions League", "flag": "🏆"},
    "ACL": {"espn": "afc.champions", "name": "AFC Champions League", "flag": "🌏"},
    "CAF": {"espn": "caf.champions", "name": "CAF Champions League", "flag": "🌍"},
    "UNL": {"espn": "uefa.nations", "name": "UEFA Nations League", "flag": "🇪🇺"}
}

COMPETITION_FORMAT_RULES = {
    "UCL": {"mode": "swiss", "group_size": 36, "total_games": 8, "qualify": 8, "playoff": 16, "elim": 12},
    "ACL": {"mode": "regional", "group_size": 12, "total_games": 8, "qualify": 8, "playoff": 0, "elim": 4},
    "CAF": {"mode": "groups", "group_size": 4, "total_games": 6, "qualify": 2, "playoff": 0, "elim": 2},
    "UNL": {"mode": "groups", "group_size": 4, "total_games": 6, "qualify": 2, "playoff": 1, "elim": 1}
}

_RAM_CACHE = {}
_DB_LOCK = threading.Lock()
_CACHE_LOCK = threading.Lock()
_HYDRATING_MATCH_IDS = set()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.espn.com/',
    'Origin': 'https://www.espn.com',
    'Connection': 'keep-alive'
}

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    try:
        SSL_CONTEXT = ssl.create_default_context()
    except Exception:
        SSL_CONTEXT = ssl._create_unverified_context()


def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn


def init_db():
    with _DB_LOCK:
        conn = get_connection()
        try:
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
            cutoff_ts = time.time() - 86400
            cursor.execute("DELETE FROM api_cache WHERE updated_at < ?;", (cutoff_ts,))

            for code, info in LEAGUE_CODES.items():
                cursor.execute("INSERT OR REPLACE INTO leagues VALUES (?, ?, ?);", (code, info["name"], info["flag"]))
            conn.commit()
        finally:
            conn.close()

    init_news_table()
    load_persistent_cache_to_ram()


def load_persistent_cache_to_ram():
    try:
        with _DB_LOCK:
            conn = get_connection()
            try:
                rows = conn.execute("SELECT cache_key, payload, updated_at FROM api_cache;").fetchall()
            finally:
                conn.close()
        with _CACHE_LOCK:
            for r in rows:
                _RAM_CACHE[r["cache_key"]] = {
                    "data": json.loads(r["payload"]),
                    "time": float(r["updated_at"])
                }
    except Exception:
        pass


MAX_RAM_CACHE_ITEMS = 250


def save_to_cache(cache_key, data):
    now = time.time()
    with _CACHE_LOCK:
        _RAM_CACHE[cache_key] = {"data": data, "time": now}
        if len(_RAM_CACHE) > MAX_RAM_CACHE_ITEMS:
            oldest_keys = sorted(_RAM_CACHE.keys(), key=lambda k: _RAM_CACHE[k]["time"])[:40]
            for k in oldest_keys:
                _RAM_CACHE.pop(k, None)
    try:
        payload_str = json.dumps(data, ensure_ascii=False)
        with _DB_LOCK:
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO api_cache (cache_key, payload, updated_at) VALUES (?, ?, ?);",
                    (cache_key, payload_str, now)
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass


def get_from_cache(cache_key, ttl=CACHE_TTL):
    with _CACHE_LOCK:
        entry = _RAM_CACHE.get(cache_key)
    if entry:
        is_fresh = (time.time() - entry["time"]) < ttl
        return entry["data"], is_fresh
    return None, False


def get_all_leagues():
    with _DB_LOCK:
        conn = get_connection()
        try:
            leagues = conn.execute("SELECT * FROM leagues;").fetchall()
        finally:
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
        clean = str(v).replace("+", "").strip()
        if clean in ("", "-", "None", "null"):
            return default
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

def _extract_leaf_groups(obj, parent_name=""):
    """استخراج المجموعات الفرعية النهائية بشكل شجري (يدعم المستويات A/B/C/D والمجموعات داخلها)"""
    leaves = []
    if isinstance(obj, dict):
        cur_name = (obj.get("name") or obj.get("abbreviation") or "").strip()
        combined_name = f"{parent_name} {cur_name}".strip() if cur_name else parent_name

        sub_children = obj.get("children") or obj.get("groups")
        if isinstance(sub_children, list) and len(sub_children) > 0:
            for ch in sub_children:
                leaves.extend(_extract_leaf_groups(ch, combined_name))
            if leaves:
                return leaves

        # إذا لم يكن هناك فروع أعمق، نفحص وجود جدول الترتيب في هذه العقدة
        direct_entries = []
        if isinstance(obj.get("entries"), list):
            direct_entries.extend(obj["entries"])
        elif isinstance(obj.get("standings"), dict) and isinstance(obj["standings"].get("entries"), list):
            direct_entries.extend(obj["standings"]["entries"])
        elif isinstance(obj.get("standings"), list):
            for st_item in obj["standings"]:
                if isinstance(st_item, dict) and isinstance(st_item.get("entries"), list):
                    direct_entries.extend(st_item["entries"])

        if direct_entries:
            leaves.append((combined_name, direct_entries))
    elif isinstance(obj, list):
        for item in obj:
            leaves.extend(_extract_leaf_groups(item, parent_name))
    return leaves


def _format_unl_level_and_group(raw_label, group_idx, group_len):
    """تحديد المستوى (A, B, C, D) ورقم المجموعة بدقة لبطولة دوري الأمم الأوروبية"""
    low = (raw_label or "").lower()
    level_code = None

    m_lvl = re.search(r'league\s*([abcd])|level\s*([abcd])|group\s*([abcd])\d', low)
    if m_lvl:
        level_code = (m_lvl.group(1) or m_lvl.group(2) or m_lvl.group(3)).upper()

    if not level_code:
        if group_idx < 4:
            level_code = "A"
        elif group_idx < 8:
            level_code = "B"
        elif group_idx < 12:
            level_code = "C"
        else:
            level_code = "D"

    m_grp = re.search(r'group\s*[abcd]?(\d+)', low)
    if m_grp:
        grp_num = int(m_grp.group(1))
    else:
        if level_code == "A":
            grp_num = (group_idx % 4) + 1
        elif level_code == "B":
            grp_num = ((group_idx - 4) % 4) + 1
        elif level_code == "C":
            grp_num = ((group_idx - 8) % 4) + 1
        else:
            grp_num = ((group_idx - 12) % 2) + 1

    level_names_ar = {
        "A": "المستوى الأول (League A)",
        "B": "المستوى الثاني (League B)",
        "C": "المستوى الثالث (League C)",
        "D": "المستوى الرابع (League D)"
    }
    group_title = f"{level_names_ar.get(level_code, f'المستوى {level_code}')} — المجموعة {grp_num}"
    return level_code, group_title


def _extract_grouped_entries(data, league_code):
    """استخراج المجموعات أو المناطق أو المستويات بشكل مستقل لضمان صحة مراكز التأهل والملحق والهبوط"""
    groups_out = []
    raw_leaves = _extract_leaf_groups(data)

    if raw_leaves:
        if league_code == "UNL":
            # إذا أعاد المصدر كل مستوى مدمجاً (16 منتخباً)، نقسمه إلى 4 مجموعات رباعية
            expanded_leaves = []
            for raw_title, ents in raw_leaves:
                if len(ents) == 16:
                    for g_i in range(4):
                        expanded_leaves.append((f"{raw_title} Group {g_i+1}", ents[g_i*4:(g_i+1)*4]))
                elif len(ents) == 6 and ("league d" in raw_title.lower() or len(raw_leaves) == 4):
                    expanded_leaves.append((f"{raw_title} Group 1", ents[:3]))
                    expanded_leaves.append((f"{raw_title} Group 2", ents[3:6]))
                else:
                    expanded_leaves.append((raw_title, ents))

            for idx, (raw_title, ents) in enumerate(expanded_leaves):
                lvl_code, grp_title = _format_unl_level_and_group(raw_title, idx, len(ents))
                groups_out.append({"group_name": grp_title, "level_code": lvl_code, "entries": ents})

        elif league_code == "ACL":
            for idx, (raw_title, ents) in enumerate(raw_leaves):
                low_t = (raw_title or "").lower()
                if "east" in low_t or "شرق" in low_t:
                    g_name, lvl = "منطقة الشرق", "EAST"
                elif "west" in low_t or "غرب" in low_t:
                    g_name, lvl = "منطقة الغرب", "WEST"
                elif idx == 0:
                    g_name, lvl = "منطقة الغرب", "WEST"
                else:
                    g_name, lvl = "منطقة الشرق", "EAST"
                groups_out.append({"group_name": g_name, "level_code": lvl, "entries": ents})

        elif league_code == "CAF":
            for idx, (raw_title, ents) in enumerate(raw_leaves):
                g_letter = chr(65 + (idx % 8))
                groups_out.append({"group_name": f"المجموعة {g_letter}", "level_code": g_letter, "entries": ents})

        else:
            all_ents = []
            for _, ents in raw_leaves:
                all_ents.extend(ents)
            groups_out.append({"group_name": "", "level_code": "", "entries": all_ents})

    if not groups_out:
        ents = _extract_entries_recursive(data)
        if ents:
            if league_code == "ACL" and len(ents) >= 24:
                groups_out.append({"group_name": "منطقة الغرب", "level_code": "WEST", "entries": ents[:12]})
                groups_out.append({"group_name": "منطقة الشرق", "level_code": "EAST", "entries": ents[12:24]})
            elif league_code == "CAF" and len(ents) >= 16:
                for g_i in range(4):
                    g_let = chr(65 + g_i)
                    groups_out.append({"group_name": f"المجموعة {g_let}", "level_code": g_let, "entries": ents[g_i*4:(g_i+1)*4]})
            elif league_code == "UNL" and len(ents) >= 48:
                cursor = 0
                for g_idx in range(14):
                    step = 4 if g_idx < 12 else 3
                    chunk = ents[cursor:cursor + step]
                    cursor += step
                    if chunk:
                        lvl_code, grp_title = _format_unl_level_and_group("", g_idx, len(chunk))
                        groups_out.append({"group_name": grp_title, "level_code": lvl_code, "entries": chunk})
            else:
                groups_out.append({"group_name": "", "level_code": "", "entries": ents})

    return groups_out


def get_official_standings(league_code, force_refresh=False):
    if league_code not in LEAGUE_CODES:
        return []

    cache_key = f"standings_v4_{league_code}"
    cached_data, is_fresh = get_from_cache(cache_key, ttl=600)
    if cached_data and is_fresh and not force_refresh:
        return cached_data

    espn_code = LEAGUE_CODES[league_code]["espn"]
    cur_yr = datetime.now().year
    candidate_urls = [
        f"https://site.web.api.espn.com/apis/v2/sports/soccer/{espn_code}/standings",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/standings",
        f"https://site.web.api.espn.com/apis/v2/sports/soccer/{espn_code}/standings?season={cur_yr}",
        f"https://site.web.api.espn.com/apis/v2/sports/soccer/{espn_code}/standings?season={cur_yr - 1}"
    ]

    grouped_entries = []
    for u in candidate_urls:
        data = fetch_json_fast(u, timeout=5.0)
        if data and isinstance(data, dict):
            grouped_entries = _extract_grouped_entries(data, league_code)
            if grouped_entries:
                break

    if not grouped_entries:
        return cached_data if cached_data else []

    rules = COMPETITION_FORMAT_RULES.get(league_code)
    standings = []
    seen_teams = set()

    for grp_obj in grouped_entries:
        group_name = grp_obj["group_name"]
        level_code = grp_obj.get("level_code", "")
        entries = grp_obj["entries"]
        group_rows = []

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            try:
                team_data = entry.get("team", {})
                team_id = str(team_data.get("id", ""))
                raw_team_name = team_data.get("displayName") or team_data.get("name") or "Team"
                short_name = team_data.get("shortDisplayName") or team_data.get("abbreviation") or raw_team_name

                dedup_key = team_id or raw_team_name
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

                played_raw = safe_num(stats.get("gamesPlayed"), 0)
                gp_div = max(1, played_raw)
                pts = safe_num(stats.get("points"), 0)
                gf = safe_num(stats.get("pointsFor"), 0)
                ga = safe_num(stats.get("pointsAgainst"), 0)
                gd = safe_num(stats.get("pointDifferential"), gf - ga)

                form_raw = str(stats.get("form", "")).strip()
                clean_form = [ch for ch in form_raw.upper() if ch in ("W", "D", "L")]
                form_list = clean_form[-5:] if len(clean_form) >= 3 else generate_form_from_pts(pts / gp_div)

                crest = DEFAULT_CLUB_CREST
                logos = team_data.get("logos", [])
                if logos and isinstance(logos, list) and isinstance(logos[0], dict):
                    crest = logos[0].get("href", crest)
                elif team_data.get("logo"):
                    crest = team_data["logo"]

                group_rows.append({
                    "rank": 0,
                    "team_id": team_id,
                    "team_name": raw_team_name,
                    "short_name": short_name,
                    "group_name": group_name,
                    "level_code": level_code,
                    "crest": crest,
                    "played": played_raw,
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

        # ترتيب فرق كل مجموعة/منطقة/مستوى تنازلياً بالنقاط ثم فارق الأهداف ثم الأهداف المسجلة
        group_rows.sort(key=lambda x: (x["points"], x["gd"], x["gf"]), reverse=True)
        g_len = len(group_rows)

        for idx_in_group, row in enumerate(group_rows):
            r_num = idx_in_group + 1
            row["rank"] = r_num
            zone = "safe"
            status_badge = ""

            if league_code == "UNL":
                # القواعد الدقيقة لدوري الأمم الأوروبية حسب كل مستوى (A, B, C, D)
                if level_code == "A":
                    if r_num in (1, 2):
                        zone, status_badge = "qualify", "ربع النهائي 🏆"
                    elif r_num == 3:
                        zone, status_badge = "playoff", "ملحق البقاء 🔄"
                    else:
                        zone, status_badge = "eliminated", "هبوط للمستوى B 🔻"
                elif level_code == "B":
                    if r_num == 1:
                        zone, status_badge = "qualify", "صعود للمستوى A ⬆️"
                    elif r_num == 2:
                        zone, status_badge = "playoff", "ملحق صعود لـ A ⬆️"
                    elif r_num == 3:
                        zone, status_badge = "playoff", "ملحق البقاء 🔄"
                    else:
                        zone, status_badge = "eliminated", "هبوط للمستوى C 🔻"
                elif level_code == "C":
                    if r_num == 1:
                        zone, status_badge = "qualify", "صعود للمستوى B ⬆️"
                    elif r_num == 2:
                        zone, status_badge = "playoff", "ملحق صعود لـ B ⬆️"
                    elif r_num == 3:
                        zone, status_badge = "safe", "بقاء"
                    else:
                        zone, status_badge = "eliminated", "هبوط/ملحق D 🔻"
                else:  # المستوى D (مجموعتان من 3 منتخبات)
                    if r_num == 1:
                        zone, status_badge = "qualify", "صعود للمستوى C ⬆️"
                    elif r_num == 2:
                        zone, status_badge = "playoff", "ملحق صعود لـ C ⬆️"
                    else:
                        zone, status_badge = "safe", "بقاء"

            elif league_code == "ACL":
                if r_num <= 8:
                    zone, status_badge = "qualify", "دور الـ16 🌏"
                else:
                    zone, status_badge = "eliminated", "إقصاء ❌"

            elif league_code == "CAF":
                if r_num <= 2:
                    zone, status_badge = "qualify", "ربع النهائي 🌍"
                else:
                    zone, status_badge = "eliminated", "إقصاء ❌"

            elif league_code == "UCL":
                if r_num <= 8:
                    zone, status_badge = "qualify", "دور الـ16 🏆"
                elif r_num <= 24:
                    zone, status_badge = "playoff", "ملحق الإقصائيات 🔄"
                else:
                    zone, status_badge = "eliminated", "إقصاء ❌"

            elif rules:
                if r_num <= rules["qualify"]:
                    zone = "qualify"
                elif rules["playoff"] > 0 and r_num <= (rules["qualify"] + rules["playoff"]):
                    zone = "playoff"
                elif r_num > (g_len - rules["elim"]):
                    zone = "eliminated"

            row["zone"] = zone
            row["status_badge"] = status_badge
            standings.append(row)

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
        if t.get("raw_name"):
            learned_map[t["raw_name"].lower()] = data_obj

    return learned_map

def match_team_power(model_dict, team_name, team_short):
    if model_dict:
        t_name_low = str(team_name).lower().strip()
        t_short_low = str(team_short).lower().strip()
        if t_name_low in model_dict:
            return model_dict[t_name_low]
        if t_short_low in model_dict:
            return model_dict[t_short_low]

        full_str = f" {t_name_low} {t_short_low} ".replace("-", " ")
        for key in sorted(model_dict.keys(), key=len, reverse=True):
            if len(key) >= 3 and f" {key} " in full_str:
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

    cache_key = f"fixtures_v4_{league_code}"
    cached_fixtures, is_fresh = get_from_cache(cache_key, ttl=1800)
    if cached_fixtures and is_fresh and not force_refresh:
        return cached_fixtures

    espn_code = LEAGUE_CODES[league_code]["espn"]
    now_dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)
    today_iso = (now_dt - timedelta(hours=12)).strftime("%Y-%m-%d")

    # 1. جلب الأيام الـ 14 القادمة بالتوازي (الصيغة الرسمية المضمونة 100% في ESPN)
    target_dates = [(now_dt + timedelta(days=i)).strftime("%Y%m%d") for i in range(-1, 14)]

    all_events = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        fut_standings = executor.submit(get_official_standings, league_code, force_refresh)
        date_futures = [executor.submit(fetch_single_date, espn_code, d) for d in target_dates]

        standings = fut_standings.result()
        for f in date_futures:
            res_evs = f.result()
            if res_evs:
                all_events.extend(res_evs)

    # 2. إذا كان الدوري في فترة توقف دولي أو كانت مباريات الجولة بعد أسبوعين، نسحب جدول الشهر الحالي والشهر القادم
    min_round_matches = 6 if league_code not in ("ACL", "CAF", "UNL", "UCL") else 4
    if len(all_events) < min_round_matches:
        cur_month = now_dt.strftime("%Y%m")
        next_month = (now_dt.replace(day=28) + timedelta(days=5)).strftime("%Y%m")
        for m_str in (cur_month, next_month):
            m_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={m_str}"
            m_data = fetch_json_fast(m_url, timeout=4.5)
            if isinstance(m_data, dict) and m_data.get("events"):
                for ev in m_data["events"]:
                    st = ev.get("status", {}).get("type", {}).get("state", "pre")
                    if st in ("pre", "in") or ev.get("date", "")[:10] >= today_iso:
                        all_events.append(ev)
            if len(all_events) >= min_round_matches:
                break

    power_map = build_team_power_map(standings)
    fixtures = []
    seen_fixture_ids = set()

    # ترتيب الأحداث زمنياً قبل استخراج الجولة
    all_events.sort(key=lambda x: x.get("date", ""))

    # الحد الأقصى لمباريات الجولة الواحدة في كل بطولة
    max_per_round = {
        "PL": 10, "PD": 10, "SA": 10, "BL1": 9, "FL1": 9,
        "DED": 9, "PPL": 9, "TSL": 9, "UCL": 18, "ACL": 12, "CAF": 8, "UNL": 16
    }.get(league_code, 10)

    for event in all_events:
        fid = event.get("id")
        if not fid or fid in seen_fixture_ids:
            continue

        # استبعاد المباريات المنتهية منذ أيام والتركيز على الجولة الحالية/القادمة
        state = event.get("status", {}).get("type", {}).get("state", "pre")
        match_date_iso = event.get("date", "")[:10]
        if state == "post" and match_date_iso < today_iso:
            continue

        seen_fixture_ids.add(fid)

        try:
            competition = event["competitions"][0]
            competitors = competition["competitors"]

            home_team_raw = next(c for c in competitors if c["homeAway"] == "home")
            away_team_raw = next(c for c in competitors if c["homeAway"] == "away")

            home_name = home_team_raw["team"]["displayName"]
            home_short = home_team_raw["team"].get("shortDisplayName", home_name)
            home_crest = home_team_raw["team"].get("logo") or DEFAULT_CLUB_CREST

            away_name = away_team_raw["team"]["displayName"]
            away_short = away_team_raw["team"].get("shortDisplayName", away_name)
            away_crest = away_team_raw["team"].get("logo") or DEFAULT_CLUB_CREST

            match_time_raw = event.get("date", "")
            formatted_time = match_time_raw
            if match_time_raw:
                try:
                    dt = datetime.strptime(match_time_raw[:16], "%Y-%m-%dT%H:%M") + timedelta(hours=3)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    formatted_time = match_time_raw.replace("T", " ").replace("Z", "")

            h_stats = match_team_power(power_map, home_name, home_short)
            a_stats = match_team_power(power_map, away_name, away_short)

            ev_week_obj = event.get("week")
            ev_week = ev_week_obj.get("number") if isinstance(ev_week_obj, dict) else None
            inferred_gw = (max((t.get("played", 0) for t in standings), default=0) + 1) if standings else 1
            real_gw = ev_week or event.get("season", {}).get("week") or inferred_gw

            fixtures.append({
                "fixture_id": str(fid),
                "gameweek": real_gw,
                "kickoff_time": formatted_time,
                "kickoff_iso": match_time_raw,
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

            if len(fixtures) >= max_per_round:
                break
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

            crest = DEFAULT_CLUB_CREST
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
    """تسخين متوازٍ لأهم البطولات والمباريات والأخبار عند التشغيل + تحديث هادئ دوري"""
    def _warm_cycle(first_run=False):
        try:
            with ThreadPoolExecutor(max_workers=5) as ex:
                tasks = [
                    ex.submit(get_todays_matches, "", not first_run),
                    ex.submit(sync_and_get_news, False),
                ]
                if first_run:
                    for lg in ("PL", "PD", "SA", "BL1", "UCL"):
                        tasks.append(ex.submit(get_official_standings, lg))
                    tasks.append(ex.submit(get_mercato_and_contracts_data, False))
                for t in tasks:
                    try:
                        t.result()
                    except Exception:
                        pass
        except Exception:
            pass

    _warm_cycle(first_run=True)

    # تحديث هادئ لمباريات اليوم في الخلفية كل 3 دقائق لتسريع الاستجابة للزوار
    while True:
        time.sleep(180)
        _warm_cycle(first_run=False)

# =========================================================================
# 6. جدول مباريات اليوم + محرك القنوات الناقلة والمعلقين المعتمد
# =========================================================================
# =========================================================================
# 6. محرك القنوات الناقلة والمعلقين الحقيقي (Zero Fake Hash + On-Demand Lookup)
# =========================================================================
LEAGUE_RIGHTS_NETWORK = {
    "PL":  "شبكة beIN Sports",
    "PD":  "شبكة beIN Sports",
    "BL1": "شبكة beIN Sports",
    "SA":  "STARZPLAY / AD Sports",
    "FL1": "شبكة beIN Sports",
    "DED": "غير محددة عربياً",
    "PPL": "غير محددة عربياً",
    "TSL": "شبكة beIN Sports",
    "UCL": "شبكة beIN Sports",
    "ACL": "beIN Sports AFC / SSC / الكأس",
    "CAF": "شبكة beIN Sports",
    "UNL": "شبكة beIN Sports"
}

ARABIC_MATCH_TEAM_ALIASES = {
    "arsenal": ["ارسنال", "أرسنال", "آرسنال"],
    "manchester city": ["مانشستر سيتي", "مان سيتي", "السيتي"],
    "man city": ["مانشستر سيتي", "مان سيتي", "السيتي"],
    "liverpool": ["ليفربول"],
    "chelsea": ["تشيلسي"],
    "manchester united": ["مانشستر يونايتد", "مان يونايتد", "اليونايتد"],
    "man united": ["مانشستر يونايتد", "مان يونايتد", "اليونايتد"],
    "tottenham": ["توتنهام"],
    "newcastle": ["نيوكاسل"],
    "aston villa": ["استون فيلا", "أستون فيلا"],
    "west ham": ["وست هام", "ويست هام"],
    "brighton": ["برايتون"],
    "everton": ["ايفرتون", "إيفرتون"],
    "fulham": ["فولهام"],
    "brentford": ["برينتفورد"],
    "crystal palace": ["كريستال بالاس"],
    "bournemouth": ["بورنموث"],
    "wolves": ["وولفرهامبتون", "ولفرهامبتون"],
    "wolverhampton": ["وولفرهامبتون", "ولفرهامبتون"],
    "nottingham": ["نوتنجهام", "نوتنغهام", "نوتينجهام"],
    "leicester": ["ليستر"],
    "southampton": ["ساوثهامبتون"],
    "ipswich": ["ايبسويتش", "إبسويتش"],
    "leeds": ["ليدز"],
    "burnley": ["بيرنلي"],
    "sunderland": ["سندرلاند"],
    "real madrid": ["ريال مدريد", "الريال"],
    "barcelona": ["برشلونة", "برشلونه"],
    "atletico": ["اتلتيكو مدريد", "أتلتيكو مدريد", "اتليتكو"],
    "athletic": ["اتلتيك بيلباو", "أتلتيك بيلباو", "بلباو"],
    "real sociedad": ["ريال سوسيداد", "سوسييداد"],
    "villarreal": ["فياريال"],
    "real betis": ["ريال بيتيس", "بيتيس"],
    "sevilla": ["اشبيلية", "إشبيلية"],
    "valencia": ["فالنسيا"],
    "girona": ["جيرونا"],
    "celta": ["سيلتا فيغو", "سيلتا فيجو"],
    "osasuna": ["اوساسونا", "أوساسونا"],
    "mallorca": ["مايوركا"],
    "getafe": ["خيتافي"],
    "rayo vallecano": ["رايو فاليكانو"],
    "espanyol": ["اسبانيول", "إسبانيول"],
    "alaves": ["الافيس", "ألافيس"],
    "las palmas": ["لاس بالماس"],
    "inter": ["انتر ميلان", "إنتر ميلان", "الانتر", "الإنتر"],
    "internazionale": ["انتر ميلان", "إنتر ميلان", "الانتر"],
    "milan": ["ميلان", "اي سي ميلان"],
    "ac milan": ["ميلان", "اي سي ميلان"],
    "juventus": ["يوفنتوس", "اليوفي"],
    "napoli": ["نابولي"],
    "roma": ["روما"],
    "as roma": ["روما"],
    "lazio": ["لاتسيو"],
    "atalanta": ["اتالانتا", "أتالانتا"],
    "fiorentina": ["فيورنتينا"],
    "bologna": ["بولونيا"],
    "torino": ["تورينو"],
    "udinese": ["اودينيزي", "أودينيزي"],
    "como": ["كومو"],
    "genoa": ["جنوى"],
    "parma": ["بارما"],
    "bayern": ["بايرن ميونخ", "بايرن ميونيخ", "البايرن"],
    "dortmund": ["بوروسيا دورتموند", "دورتموند"],
    "leverkusen": ["باير ليفركوزن", "ليفركوزن"],
    "leipzig": ["لايبزيج", "لايبزيغ"],
    "frankfurt": ["اينتراخت فرانكفورت", "فرانكفورت"],
    "stuttgart": ["شتوتغارت", "شتوتجارت"],
    "freiburg": ["فرايبورغ", "فرايبورج"],
    "wolfsburg": ["فولفسبورغ", "فولفسبورج"],
    "werder bremen": ["فيردر بريمن", "بريمن"],
    "monchengladbach": ["مونشنغلادباخ", "مونشنجلادباخ"],
    "psg": ["باريس سان جيرمان", "باريس"],
    "paris saint-germain": ["باريس سان جيرمان", "باريس"],
    "marseille": ["مارسيليا", "مرسيليا"],
    "monaco": ["موناكو"],
    "lyon": ["ليون"],
    "lille": ["ليل"],
    "nice": ["نيس"],
    "lens": ["لانس"],
    "rennes": ["رين"],
    "strasbourg": ["ستراسبورغ", "ستراسبورج"],
    "benfica": ["بنفيكا"],
    "porto": ["بورتو"],
    "sporting": ["سبورتينغ لشبونة", "سبورتنج لشبونة"],
    "braga": ["براغا", "براجا"],
    "ajax": ["اياكس", "أياكس"],
    "psv": ["ايندهوفن", "آيندهوفن"],
    "feyenoord": ["فينورد", "فاينورد"],
    "az alkmaar": ["الكماار", "ألكمار"],
    "galatasaray": ["غلطة سراي", "جالطة سراي", "غلطه سراي"],
    "fenerbahce": ["فنربخشة", "فنربخشه"],
    "besiktas": ["بشكتاش"],
    "trabzonspor": ["طرابزون"],
    "al hilal": ["الهلال"], "al-hilal": ["الهلال"],
    "al nassr": ["النصر"], "al-nassr": ["النصر"],
    "al ahli": ["الأهلي السعودي", "اهلي جدة", "الأهلي"], "al-ahli": ["الأهلي السعودي", "اهلي جدة", "الأهلي"],
    "al ittihad": ["الاتحاد"], "al-ittihad": ["الاتحاد"],
    "al ain": ["العين"], "al-ain": ["العين"],
    "al sadd": ["السد"], "al-sadd": ["السد"],
    "al rayyan": ["الريان"], "al gharafa": ["الغرافة"], "al wasl": ["الوصل"],
    "al ahly": ["الأهلي المصري", "الاهلي", "الأهلي"],
    "zamalek": ["الزمالك"], "pyramids": ["بيراميدز"],
    "esperance": ["الترجي"], "wydad": ["الوداد"], "raja": ["الرجاء"],
    "sundowns": ["صن داونز"], "berkane": ["نهضة بركان"], "as far": ["الجيش الملكي"],
    "spain": ["اسبانيا", "إسبانيا"], "france": ["فرنسا"], "germany": ["المانيا", "ألمانيا"],
    "italy": ["ايطاليا", "إيطاليا"], "portugal": ["البرتغال"], "england": ["انجلترا", "إنجلترا"],
    "netherlands": ["هولندا"], "belgium": ["بلجيكا"], "croatia": ["كرواتيا"]
}

KNOWN_ARABIC_COMMENTATORS = [
    "عصام الشوالي", "حفيظ دراجي", "خليل البلوشي", "فارس عوض", "فهد العتيبي",
    "رؤوف خليف", "علي محمد علي", "حسن العيدروس", "عيسى الحربين", "عامر الخوذيري",
    "أحمد البلوشي", "جواد بدة", "محمد بركات", "عامر عبدالله", "بلال علام",
    "مدحت شلبي", "أيمن الكاشف", "علي سعيد الكعبي", "حازم عبدالسلام", "مشاري القرني",
    "حماد العنزي", "عبدالله الحربي", "سليمان الشريف", "راشد الدوسري", "أحمد الطيب",
    "نوفل باشي", "باسم الزير", "عادل خلو", "أحمد فؤاد", "خالد الحدي", "محمد مبروكي",
    "عبدالله الغامدي", "جعفر الصليح", "سالم السالمي", "أحمد عبده", "محمد حسين",
    "سمير المعيرفي", "خالد المديفر", "فهد الدريبي", "طارق الأدور", "مؤمن حسن",
    "محمد الكواليني", "عصام عبده", "ماجد الشجيع", "نور الدين أيت علي",
    "مضر اليوسف", "سمير اليعقوبي", "منتصر الأزهري", "حاتم بطيشة", "يوسف سيف",
    "خالد الغول", "سوار الذهب", "مهند الجالي", "أحمد المعمري", "أحمد الحامد",
    "محمد الشامسي", "عبدالله السعدي", "عائد العصيمي", "راشد المهيري", "لحدان الفيحاني",
    "أحمد النفيسة", "علي لفتة", "محمد السعدي", "مصطفى ناظم", "كريم الطرهوني"
]

_COMMENTATOR_VARIANTS_MAP = {
    "حفيظ الدراجي": "حفيظ دراجي",
    "عامر الخذيري": "عامر الخوذيري",
    "جواد بده": "جواد بدة",
    "حسن عيدروس": "حسن العيدروس",
    "علي الكعبي": "علي سعيد الكعبي",
    "عبد الله الغامدي": "عبدالله الغامدي",
    "عبد الله الحربي": "عبدالله الحربي",
    "عامر عبد الله": "عامر عبدالله",
}


CHANNEL_REGEX = re.compile(
    r"(beIN\s*Sports?\s*(?:HD|Premium|AFC|Xtra|Extra|Max|English|French)?\s*\d+(?:\s*HD)?"
    r"|SSC\s*(?:EXTRA|NEWS|SPORT)?\s*\d+(?:\s*HD)?"
    r"|AD\s*Sports?\s*(?:Premium)?\s*\d+(?:\s*HD)?"
    r"|Al\s*Kass\s*\d+(?:\s*HD)?"
    r"|STARZPLAY|Shahid\s*VIP|TOD"
    r"|أبوظبي\s*الرياضية\s*(?:بريميوم|آسيا)?\s*\d*"
    r"|الكأس\s*\d+\s*(?:HD)?"
    r"|أون\s*تايم\s*سبورتس?\s*\d+"
    r"|أون\s*سبورت\s*\d+"
    r"|ب[يى]\s*[اإأ]ن\s*سبورتس?\s*(?:HD|إكسترا|آسيا|بريميوم)?\s*\d+(?:\s*HD)?"
    r"|السعودية\s*الرياضية\s*\d*"
    r"|ثمانية\s*\d*)",
    re.IGNORECASE
)

_AR_MENA_CHANNEL_KEYWORDS = (
    "bein", "بي ان", "ssc", "ad sports", "ابوظبي", "starzplay", "ستارز",
    "shahid", "شاهد", "tod", "alkass", "al kass", "الكاس",
    "ontime", "on time", "اون تايم", "اون سبورت",
    "دبي الرياضيه", "الشارقه الرياضيه", "السعوديه الرياضيه", "الرياضيه", "ثمانيه", "mbc"
)

_AR_WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip"
}

_EN_CLUB_NOISE_WORDS = {
    "fc", "cf", "sc", "fk", "sk", "ac", "as", "afc", "ssc", "cd", "ud", "rc", "rcd",
    "vfb", "vfl", "rb", "sv", "tsg", "fsv", "bk", "ik", "if", "nk", "pk", "sd",
    "club", "de", "la", "el", "the", "calcio", "sport", "football", "soccer", "sa", "sp"
}

_EN_GENERIC_COLLISION_WORDS = {
    "united", "city", "real", "athletic", "atletico", "sporting", "inter", "milan",
    "madrid", "paris", "royal", "olympic", "olympique", "dynamo", "sparta", "slavia",
    "borussia", "eintracht", "red", "star", "al", "saint", "san", "los", "new", "west"
}

_EN_CANONICAL_REWRITES = {
    "internazionale": "inter milan",
    "inter milano": "inter milan",
    "man utd": "manchester united",
    "man united": "manchester united",
    "man city": "manchester city",
    "psg": "paris saint germain",
    "spurs": "tottenham hotspur",
    "wolves": "wolverhampton wanderers",
    "praha": "prague",
    "munchen": "munich",
    "bayern munchen": "bayern munich",
    "athletic club": "athletic bilbao",
    "kobenhavn": "copenhagen",
    "piraeus": "olympiacos",
}

_YOUTH_OR_WOMEN_REGEX = re.compile(
    r"\b(?:u\d{2}|under[\s\-]?\d{2}|youth|women|woman|ladies|feminin|femenino|femminile|frauen|reserves|ii|\(w\))\b|سيدات|شباب|ناشئين",
    re.IGNORECASE
)


def _normalize_ar_text(txt):
    if not txt:
        return ""
    s = str(txt)
    s = re.sub(r"[\u064B-\u065F\u0640]", "", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    s = re.sub(r"[^\u0600-\u06FFa-zA-Z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def _normalize_en_club(name: str) -> str:
    """توحيد أسماء الأندية الإنجليزية بإزالة الحركات والرموز (Atlético -> atletico)"""
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s).lower()
    s = re.sub(r"\s+", " ", s).strip()
    for k, v in _EN_CANONICAL_REWRITES.items():
        if s == k or f" {k} " in f" {s} ":
            s = re.sub(rf"\b{re.escape(k)}\b", v, s)
    tokens = [t for t in s.split() if t not in _EN_CLUB_NOISE_WORDS]
    return " ".join(tokens) if tokens else s


def _en_team_matches(name1: str, name2: str) -> bool:
    """مطابقة دقيقة بين أسماء الأندية الإنجليزية (ESPN مقابل 365Scores)"""
    c1 = _normalize_en_club(name1)
    c2 = _normalize_en_club(name2)
    if not c1 or not c2:
        return False
    # منع الخلط بين إنتر ميلان وميلان
    if (c1 == "milan" and "inter" in c2) or (c2 == "milan" and "inter" in c1):
        return False
    if c1 == c2:
        return True
    if len(c1) >= 4 and re.search(rf"\b{re.escape(c1)}\b", c2):
        return True
    if len(c2) >= 4 and re.search(rf"\b{re.escape(c2)}\b", c1):
        return True
    # مطابقة كلمة مميزة قوية (مثل stuttgart, brugge, villarreal, barcelona, liverpool, sabah, viking)
    t1 = {t for t in c1.split() if len(t) >= 5 and t not in _EN_GENERIC_COLLISION_WORDS}
    t2 = {t for t in c2.split() if len(t) >= 5 and t not in _EN_GENERIC_COLLISION_WORDS}
    if t1 and t2 and (t1 & t2):
        return True
    return False


def _is_arabic_mena_channel(ch_name: str) -> bool:
    norm = _normalize_ar_text(ch_name)
    if not norm or len(norm) < 3:
        return False
    return any(k in norm for k in _AR_MENA_CHANNEL_KEYWORDS)


def _has_whole_word(norm_text: str, norm_term: str) -> bool:
    if not norm_text or not norm_term:
        return False
    pattern = rf"(?<![\u0600-\u06FFa-zA-Z0-9])(?:و|ف|ب|ل)?{re.escape(norm_term)}(?![\u0600-\u06FFa-zA-Z0-9])"
    return bool(re.search(pattern, norm_text))


def _get_team_arabic_candidates(en_name, league_code: str = "", extra_ar: str = ""):
    low = (en_name or "").strip().lower()
    cands = []

    if extra_ar:
        cands.append(extra_ar)
        # إضافة النسخة بدون أداة التعريف أو معها لتسهيل المطابقة مع يلا كورة وفي الجول
        clean_ex = extra_ar.strip()
        if clean_ex.startswith("نادي "):
            cands.append(clean_ex[5:].strip())

    if "al ahly" in low or (league_code == "CAF" and "ahly" in low):
        cands.extend(["الاهلي المصري", "الاهلي"])
    elif "al ahli" in low or "al-ahli" in low or (league_code == "ACL" and "ahli" in low):
        cands.extend(["الاهلي السعودي", "اهلي جده", "الاهلي"])
    elif "internazionale" in low or low in ("inter", "inter milan"):
        cands.extend(["انتر ميلان", "الانتر", "انتر"])
    elif low in ("milan", "ac milan"):
        cands.extend(["اي سي ميلان", "ميلان"])
    else:
        for k, arr in ARABIC_MATCH_TEAM_ALIASES.items():
            if k == low or (len(k) >= 5 and k in low):
                cands.extend(arr)

    ar_clean = _clean_entity_name(en_name)
    if ar_clean and ar_clean.lower() != low:
        cands.append(ar_clean)
    if len(low) >= 4:
        cands.append(low)

    out = []
    for x in cands:
        nx = _normalize_ar_text(x)
        if nx and len(nx) >= 3 and nx not in out:
            out.append(nx)
    return out


def _team_matches_norm_text(norm_text: str, team_cands: list, en_name: str = "") -> bool:
    if not norm_text or not team_cands:
        return False
    check_text = norm_text
    en_low = (en_name or "").strip().lower()
    if en_low in ("milan", "ac milan"):
        check_text = re.sub(r"\bانتر\s+ميلان\b", " ", check_text)
    for cand in team_cands:
        if _has_whole_word(check_text, cand):
            return True
    return False


def _match_pair_against_structured_teams(team_a_txt: str, team_b_txt: str, h_cands: list, a_cands: list, home_en: str, away_en: str) -> bool:
    na = _normalize_ar_text(team_a_txt)
    nb = _normalize_ar_text(team_b_txt)
    if not na or not nb:
        return False
    direct = _team_matches_norm_text(na, h_cands, home_en) and _team_matches_norm_text(nb, a_cands, away_en)
    swapped = _team_matches_norm_text(na, a_cands, away_en) and _team_matches_norm_text(nb, h_cands, home_en)
    return direct or swapped


_INVALID_COMMENTATOR_WORDS = (
    "جريدة", "جريده", "شبكة", "شبكه", "صحيفة", "صحيفه", "بوابة", "بوابه", "موقع",
    "الدستور", "تواصل", "أخبار", "اخبار", "اليوم", "سبورت", "كورة", "كوره", "كووورة",
    "القناة", "القناه", "المباراة", "المباراه", "مباراة", "مباراه", "غير", "محدد",
    "لم", "يعلن", "جدول", "بث", "مباشر", "تشكيل", "نتيجة", "نتيجه", "ملخص", "أهداف",
    "موعد", "توقيت", "بطولة", "دوري", "كأس", "الوطن", "المصري", "الشروق", "الوفد",
    "المشهد", "العين", "صدى", "صدي", "إرم", "ارم", "بطولات", "جول", "الناقل", "الناقلة",
    "ملعب", "الحكم", "في", "على", "عن", "من", "الى", "إلى", "التعليق", "القنوات"
)


def _is_valid_commentator_name(cand: str) -> bool:
    c = (cand or "").strip()
    if not c or len(c) < 5 or len(c) > 32:
        return False
    norm_c = _normalize_ar_text(c)
    words = norm_c.split()
    if len(words) < 2 or len(words) > 3:
        return False
    for bad in _INVALID_COMMENTATOR_WORDS:
        if _normalize_ar_text(bad) in words:
            return False
    return True


def _extract_channel_and_commentator_from_text(text_chunk: str, strict_single: bool = False, allow_regex_comm: bool = False):
    """استخراج القناة والمعلق بدقة: نعتمد القائمة الموثقة للمعلقين لمنع التقاط أسماء الصحف نهائياً"""
    if not text_chunk:
        return "", ""

    found_channels = []
    for m_ch in CHANNEL_REGEX.finditer(text_chunk):
        ch_clean = re.sub(r"\s+", " ", m_ch.group(1)).strip()
        if ch_clean and ch_clean.lower() not in [x.lower() for x in found_channels]:
            found_channels.append(ch_clean)

    found_commentators = []
    norm_txt = _normalize_ar_text(text_chunk)

    for comm in KNOWN_ARABIC_COMMENTATORS:
        if _has_whole_word(norm_txt, _normalize_ar_text(comm)):
            if comm not in found_commentators:
                found_commentators.append(comm)

    for variant, canonical in _COMMENTATOR_VARIANTS_MAP.items():
        if _has_whole_word(norm_txt, _normalize_ar_text(variant)):
            if canonical not in found_commentators:
                found_commentators.append(canonical)

    # نسمح بالـ Regex الحر فقط على الحقول المهيكلة (يلا كورة / في الجول / جدول) وبشرط وجود نقطتين (:) لا شرطة (-)
    if not found_commentators and allow_regex_comm:
        m_comm = re.search(
            r"(?:المعلق|بتعليق|بصوت)\s*[:：]\s*([\u0600-\u06FF]{2,15}\s+[\u0600-\u06FF]{2,15})",
            text_chunk
        )
        if m_comm:
            cand = m_comm.group(1).strip()
            if _is_valid_commentator_name(cand):
                found_commentators.append(cand)

    if strict_single:
        ch_out = found_channels[0] if (1 <= len(found_channels) <= 2) else ""
        comm_out = found_commentators[0] if len(found_commentators) == 1 else ""
        return ch_out, comm_out

    return (found_channels[0] if found_channels else ""), (found_commentators[0] if found_commentators else "")


def _fetch_yallakora_match_commentator(yk_url: str):
    """سحب اسم المعلق والقناة مباشرةً من صفحة المباراة المحددة في يلا كورة"""
    if not yk_url:
        return "", ""
    full_url = yk_url if yk_url.startswith("http") else f"https://www.yallakora.com{yk_url}"
    try:
        req = urllib.request.Request(full_url, headers=_AR_WEB_HEADERS)
        with urllib.request.urlopen(req, timeout=3.5, context=SSL_CONTEXT) as resp:
            raw = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            h_txt = raw.decode("utf-8", errors="ignore")

            ch_val, comm_val = "", ""
            m_ch = re.search(r'<div[^>]+class="[^"]*\bchannel\b[^"]*"[^>]*>(.*?)</div>', h_txt, re.DOTALL | re.IGNORECASE)
            if m_ch:
                c_txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m_ch.group(1)))).strip()
                if _is_arabic_mena_channel(c_txt):
                    ch_val = c_txt

            plain_txt = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>", " ", h_txt, flags=re.DOTALL | re.IGNORECASE)
            plain_txt = html.unescape(re.sub(r"<[^>]+>", " | ", plain_txt))
            plain_txt = re.sub(r"\s+", " ", plain_txt)

            # 1. البحث حول كلمة المعلق
            for m_lbl in re.finditer(r"(?:المعلق|تعليق|معلق\s+المباراة)", plain_txt):
                snippet = plain_txt[m_lbl.start():m_lbl.start() + 140]
                _, c_ext = _extract_channel_and_commentator_from_text(snippet, strict_single=True, allow_regex_comm=True)
                if c_ext:
                    comm_val = c_ext
                    break
                m_pipe = re.search(r"(?:المعلق|تعليق)\s*[:：|]+\s*([\u0600-\u06FF]{2,15}(?:\s+[\u0600-\u06FF]{2,15}){1,2})", snippet)
                if m_pipe and _is_valid_commentator_name(m_pipe.group(1)):
                    comm_val = m_pipe.group(1).strip()
                    break

            # 2. البحث في رأس تفاصيل المباراة (في حال استخدام أيقونة الميكروفون بدلاً من كلمة المعلق)
            if not comm_val:
                m_hdr = re.search(r'class="[^"]*(?:tournsData|matchDetails|mtchDtls|matchInfo)[^"]*"(.*?)</section>', h_txt, re.DOTALL | re.IGNORECASE)
                if m_hdr:
                    hdr_plain = html.unescape(re.sub(r"<[^>]+>", " ", m_hdr.group(1)))
                    _, c_ext = _extract_channel_and_commentator_from_text(hdr_plain, strict_single=True, allow_regex_comm=False)
                    if c_ext:
                        comm_val = c_ext

            return ch_val, comm_val
    except Exception:
        return "", ""

def _fetch_filgoal_match_commentator(fg_url: str):
    """سحب القناة والمعلق مباشرةً من صفحة المباراة على في الجول"""
    if not fg_url:
        return "", ""
    full_url = fg_url if fg_url.startswith("http") else f"https://www.filgoal.com{fg_url}"
    try:
        req = urllib.request.Request(full_url, headers=_AR_WEB_HEADERS)
        with urllib.request.urlopen(req, timeout=3.5, context=SSL_CONTEXT) as resp:
            raw = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            h_txt = raw.decode("utf-8", errors="ignore")
            plain = html.unescape(re.sub(r"<[^>]+>", " | ", re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>", " ", h_txt, flags=re.DOTALL | re.IGNORECASE)))
            plain = re.sub(r"\s+", " ", plain)
            ch_val, comm_val = "", ""
            for m_lbl in re.finditer(r"(?:المعلق|القناة\s*الناقلة|القنوات\s*الناقلة)", plain):
                snippet = plain[m_lbl.start():m_lbl.start() + 150]
                ch_e, cm_e = _extract_channel_and_commentator_from_text(snippet, strict_single=True)
                if ch_e and not ch_val and _is_arabic_mena_channel(ch_e):
                    ch_val = ch_e
                if cm_e and not comm_val:
                    comm_val = cm_e
            return ch_val, comm_val
    except Exception:
        return "", ""


def _scrape_live_arabic_broadcast_tables(target_dt_local=None):
    """سحب جداول القنوات والمعلقين الموثقة: 365Scores (EN+AR مدمج) + YallaKora + FilGoal + Telegram"""
    if target_dt_local is None:
        target_dt_local = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=3)

    date_tag = target_dt_local.strftime("%Y%m%d")
    cache_key = f"live_verified_broadcasts_v13_{date_tag}"
    cached_b, is_fresh = get_from_cache(cache_key, ttl=900)
    if cached_b and is_fresh:
        return cached_b

    now_ts = time.time()

    # 1. جلب 365Scores بالإنجليزية (لمطابقة 100% من أندية العالم) وبالعربية (للحصول على الاسم العربي الدقيق لكل نادٍ)
    def _fetch_365scores_lang(lang_id: int):
        d_365 = target_dt_local.strftime("%d/%m/%Y")
        url = (
            "https://webws.365scores.com/web/games/allscores/"
            f"?appTypeId=5&langId={lang_id}&timezoneName=Asia/Riyadh&userCountryId=115"
            f"&sports=1&startDate={urllib.parse.quote(d_365)}&endDate={urllib.parse.quote(d_365)}"
        )
        return fetch_json_fast(url, timeout=4.5) or {}

    # 2. يلا كورة (مقسمة بدقة على liItem + حفظ رابط صفحة المباراة لسحب المعلق)
    def _fetch_yallakora_day():
        items = []
        try:
            yk_date = f"{target_dt_local.month}/{target_dt_local.day}/{target_dt_local.year}"
            url = f"https://www.yallakora.com/match-center?date={yk_date}"
            req = urllib.request.Request(url, headers=_AR_WEB_HEADERS)
            with urllib.request.urlopen(req, timeout=4.5, context=SSL_CONTEXT) as resp:
                raw = resp.read()
                if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                html_txt = raw.decode("utf-8", errors="ignore")

                cards = re.split(r'<(?:div|li)[^>]+class="[^"]*\bliItem\b[^"]*"', html_txt)[1:]
                for card in cards[:140]:
                    card = card.split('class="matchCard')[0]
                    ta_m = re.search(r'class="[^"]*\bteamA\b[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>', card, re.DOTALL)
                    tb_m = re.search(r'class="[^"]*\bteamB\b[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>', card, re.DOTALL)
                    if not ta_m or not tb_m:
                        continue
                    ta = html.unescape(re.sub(r"<[^>]+>", "", ta_m.group(1))).strip()
                    tb = html.unescape(re.sub(r"<[^>]+>", "", tb_m.group(1))).strip()
                    if not ta or not tb:
                        continue

                    ch_m = re.search(r'<div[^>]+class="[^"]*\bchannel\b[^"]*"[^>]*>(.*?)</div>', card, re.DOTALL)
                    ch_txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", ch_m.group(1)))).strip() if ch_m else ""
                    if ch_txt and not _is_arabic_mena_channel(ch_txt):
                        ch_txt = ""

                    link_m = re.search(r'href="(/[^"]*/match/\d+[^"]*)"', card)
                    yk_link = link_m.group(1) if link_m else ""

                    items.append({
                        "team_a": ta,
                        "team_b": tb,
                        "channel": ch_txt,
                        "commentator": "",
                        "yk_url": yk_link,
                        "fg_url": ""
                    })
        except Exception:
            pass
        return items

    # 3. في الجول (FilGoal) — يعرض القناة والمعلق العربي لكثير من المباريات الأوروبية والعربية
    def _fetch_filgoal_day():
        items = []
        try:
            fg_date = target_dt_local.strftime("%Y-%m-%d")
            url = f"https://www.filgoal.com/matches/?date={fg_date}"
            req = urllib.request.Request(url, headers=_AR_WEB_HEADERS)
            with urllib.request.urlopen(req, timeout=4.0, context=SSL_CONTEXT) as resp:
                raw = resp.read()
                if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                html_txt = raw.decode("utf-8", errors="ignore")
                blocks = re.split(r'<div[^>]+class="[^"]*cin_cntnr[^"]*"', html_txt)[1:]
                for blk in blocks[:120]:
                    blk = blk.split('class="mc-block')[0]
                    t_strongs = re.findall(r'<div[^>]+class="[^"]*\b(?:f|s)\b[^"]*"[^>]*>.*?<strong[^>]*>(.*?)</strong>', blk, re.DOTALL)
                    if len(t_strongs) < 2:
                        continue
                    ta = html.unescape(re.sub(r"<[^>]+>", "", t_strongs[0])).strip()
                    tb = html.unescape(re.sub(r"<[^>]+>", "", t_strongs[1])).strip()
                    if not ta or not tb:
                        continue

                    plain_blk = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", blk)))
                    ch_ext, comm_ext = _extract_channel_and_commentator_from_text(plain_blk, strict_single=True)
                    fg_link_m = re.search(r'href="(/matches/\d+[^"]*)"', blk)
                    fg_link = fg_link_m.group(1) if fg_link_m else ""

                    items.append({
                        "team_a": ta,
                        "team_b": tb,
                        "channel": ch_ext if _is_arabic_mena_channel(ch_ext) else "",
                        "commentator": comm_ext,
                        "yk_url": "",
                        "fg_url": fg_link
                    })
        except Exception:
            pass
        return items

    # 4. تيليغرام (بعد إصلاح مطابقة الشرطات ذات المسافات مثل "برشلونة - صباح" وعزل كل مباراة)
    def _fetch_tg_isolated(t_url):
        out = []
        try:
            req = urllib.request.Request(t_url, headers=_AR_WEB_HEADERS)
            with urllib.request.urlopen(req, timeout=3.0, context=SSL_CONTEXT) as resp:
                raw = resp.read()
                if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                html_txt = raw.decode("utf-8", errors="ignore")
                msg_wraps = re.split(r'<div class="tgme_widget_message_wrap', html_txt)[1:]
                for wrap in msg_wraps[-20:]:
                    tm_m = re.search(r'<time[^>]+datetime="([^"]+)"', wrap)
                    if tm_m:
                        try:
                            msg_ts = datetime.fromisoformat(tm_m.group(1).replace("Z", "+00:00")).timestamp()
                            if (now_ts - msg_ts) > (32 * 3600):
                                continue
                        except Exception:
                            pass
                    txt_m = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', wrap, re.DOTALL)
                    if not txt_m:
                        continue
                    clean_m = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<br\s*/?>", "\n", txt_m.group(1))))
                    lines = [re.sub(r"\s+", " ", ln).strip() for ln in clean_m.split("\n") if ln.strip()]

                    match_sep_re = re.compile(r"(?:×|🆚|\bvs\b|ضد|\s[-–—]\s)", re.IGNORECASE)
                    i = 0
                    while i < len(lines):
                        ln = lines[i]
                        if match_sep_re.search(ln):
                            block_parts = [ln]
                            j = i + 1
                            while j < len(lines) and j <= i + 2:
                                nxt = lines[j]
                                if match_sep_re.search(nxt) and not any(k in nxt for k in ("معلق", "تعليق", "القناة", "🎙", "📺")):
                                    break
                                if any(tok in _normalize_ar_text(nxt) for tok in ("bein", "بي ان", "ssc", "معلق", "تعليق", "قناه", "الكاس", "ابوظبي", "starz")) or ("🎙" in nxt) or ("📺" in nxt):
                                    block_parts.append(nxt)
                                    j += 1
                                else:
                                    break
                            out.append(" | ".join(block_parts))
                            i = j
                        else:
                            i += 1
        except Exception:
            pass
        return out

    with ThreadPoolExecutor(max_workers=6) as ex:
        fut_365_en = ex.submit(_fetch_365scores_lang, 1)
        fut_365_ar = ex.submit(_fetch_365scores_lang, 27)
        fut_yk = ex.submit(_fetch_yallakora_day)
        fut_fg = ex.submit(_fetch_filgoal_day)
        futs_tg = [ex.submit(_fetch_tg_isolated, u) for u in ("https://t.me/s/beinsports", "https://t.me/s/radarkora")]

        data_365_en = fut_365_en.result() or {}
        data_365_ar = fut_365_ar.result() or {}
        yk_items = fut_yk.result() or []
        fg_items = fut_fg.result() or []
        single_match_lines = []
        for f in futs_tg:
            single_match_lines.extend(f.result() or [])

    # دمج 365Scores الإنجليزي والعربي عبر game.id
    ar_by_gid = {}
    for g in (data_365_ar.get("games") or []):
        if isinstance(g, dict) and g.get("id"):
            ar_by_gid[str(g["id"])] = g

    scores365_games = []
    for g_en in (data_365_en.get("games") or []):
        if not isinstance(g_en, dict) or not g_en.get("id"):
            continue
        gid = str(g_en["id"])
        comp_disp = str(g_en.get("competitionDisplayName") or "")
        hc_en = str((g_en.get("homeCompetitor") or {}).get("name") or "").strip()
        ac_en = str((g_en.get("awayCompetitor") or {}).get("name") or "").strip()
        if not hc_en or not ac_en:
            continue
        # استبعاد مباريات الشباب والسيدات حتى لا تتعارض مع الفريق الأول
        if _YOUTH_OR_WOMEN_REGEX.search(f"{comp_disp} {hc_en} {ac_en}"):
            continue

        g_ar = ar_by_gid.get(gid) or {}
        hc_ar = str((g_ar.get("homeCompetitor") or {}).get("name") or "").strip()
        ac_ar = str((g_ar.get("awayCompetitor") or {}).get("name") or "").strip()

        start_ts = 0.0
        st_raw = str(g_en.get("startTime") or g_ar.get("startTime") or "").strip()
        if st_raw:
            try:
                start_ts = datetime.fromisoformat(st_raw.replace("Z", "+00:00")).timestamp()
            except Exception:
                pass

        ch_picked = ""
        for src_g in (g_ar, g_en):
            for net in (src_g.get("tvNetworks") or []):
                if not isinstance(net, dict):
                    continue
                n_name = str(net.get("name") or "").strip()
                if _is_arabic_mena_channel(n_name):
                    ch_picked = n_name
                    break
            if ch_picked:
                break

        scores365_games.append({
            "id": gid,
            "home_en": hc_en,
            "away_en": ac_en,
            "home_ar": hc_ar,
            "away_ar": ac_ar,
            "start_ts": start_ts,
            "channel": ch_picked
        })

    payload = {
        "scores365_games": scores365_games,
        "arabic_cards": fg_items + yk_items,
        "single_match_lines": single_match_lines
    }
    save_to_cache(cache_key, payload)
    return payload


def _resolve_match_broadcast_and_commentator(
    league_code: str,
    event_id: str,
    home_en: str,
    away_en: str,
    comp_obj: dict,
    broadcast_bundle: dict,
    match_state: str = "pre",
    kickoff_utc_ts: float = 0.0
):
    """مطابقة عالمية 100% بالإنجليزية + وقت الانطلاق عبر 365Scores ثم سحب المعلق عبر الاسم العربي الدقيق"""
    found_channel = ""
    found_commentator = ""
    channel_verified = False
    commentator_verified = False
    matched_yk_url = ""
    matched_fg_url = ""
    matched_365_id = ""
    home_ar_exact = ""
    away_ar_exact = ""

    od_cached, od_fresh = get_from_cache(f"match_bcast_od_v4_{event_id}", ttl=21600)
    if od_cached and od_fresh:
        return (
            od_cached["channel"],
            od_cached["commentator"],
            od_cached["channel_verified"],
            od_cached["commentator_verified"],
            od_cached.get("yk_url", ""),
            od_cached.get("fg_url", ""),
            od_cached.get("scores365_id", ""),
            od_cached.get("home_ar", ""),
            od_cached.get("away_ar", ""),
        )

    try:
        s365_list = (broadcast_bundle or {}).get("scores365_games") or []
        ar_cards = (broadcast_bundle or {}).get("arabic_cards") or []
        single_lines = (broadcast_bundle or {}).get("single_match_lines") or []

        # 1. المطابقة العالمية عبر 365Scores (إنجليزي + وقت الانطلاق الدقيق) -> تنجح لكل أندية العالم!
        best_365 = None
        for g in s365_list:
            g_ts = float(g.get("start_ts") or 0.0)
            time_diff = abs(kickoff_utc_ts - g_ts) if (kickoff_utc_ts > 0 and g_ts > 0) else 999999

            h_m = _en_team_matches(home_en, g["home_en"])
            a_m = _en_team_matches(away_en, g["away_en"])
            h_sw = _en_team_matches(home_en, g["away_en"])
            a_sw = _en_team_matches(away_en, g["home_en"])

            if (h_m and a_m) or (h_sw and a_sw):
                if time_diff <= 21600 or g_ts == 0:
                    best_365 = (g, bool(h_sw and a_sw and not (h_m and a_m)))
                    break
            elif time_diff <= 1500 and (h_m or a_m or h_sw or a_sw):
                # تطابق أحد الفريقين + نفس دقيقة الانطلاق (±25 دقيقة) -> يضمن مطابقة أي نادٍ مغمور مثل Sabah أو Viking FK!
                best_365 = (g, bool((h_sw or a_sw) and not (h_m or a_m)))

        if best_365:
            g_obj, is_swapped = best_365
            matched_365_id = g_obj.get("id", "")
            home_ar_exact = g_obj.get("away_ar", "") if is_swapped else g_obj.get("home_ar", "")
            away_ar_exact = g_obj.get("home_ar", "") if is_swapped else g_obj.get("away_ar", "")
            if g_obj.get("channel") and _is_arabic_mena_channel(g_obj["channel"]):
                found_channel = g_obj["channel"]
                channel_verified = True

        # بناء قائمة المرادفات العربية المزوّدة الآن بالاسم العربي الرسمي من 365Scores!
        h_cands = _get_team_arabic_candidates(home_en, league_code, extra_ar=home_ar_exact)
        a_cands = _get_team_arabic_candidates(away_en, league_code, extra_ar=away_ar_exact)

        # 2. المطابقة مع بطاقات FilGoal و YallaKora (باستخدام الأسماء العربية الرسمية الجديدة)
        if h_cands and a_cands and ar_cards:
            for card in ar_cards:
                if not _match_pair_against_structured_teams(
                    card.get("team_a", ""), card.get("team_b", ""), h_cands, a_cands, home_en, away_en
                ):
                    continue
                if card.get("yk_url") and not matched_yk_url:
                    matched_yk_url = card["yk_url"]
                if card.get("fg_url") and not matched_fg_url:
                    matched_fg_url = card["fg_url"]
                if card.get("channel") and not channel_verified and _is_arabic_mena_channel(card["channel"]):
                    found_channel = card["channel"]
                    channel_verified = True
                if card.get("commentator") and not commentator_verified:
                    found_commentator = card["commentator"]
                    commentator_verified = True

        # 3. المطابقة مع كتل تيليغرام المعزولة (مباراة واحدة لكل كتلة)
        if h_cands and a_cands and single_lines and (not channel_verified or not commentator_verified):
            for blk in single_lines:
                norm_blk = _normalize_ar_text(blk)
                if not (_team_matches_norm_text(norm_blk, h_cands, home_en) and _team_matches_norm_text(norm_blk, a_cands, away_en)):
                    continue
                ch_ext, comm_ext = _extract_channel_and_commentator_from_text(blk, strict_single=True)
                if ch_ext and not channel_verified and _is_arabic_mena_channel(ch_ext):
                    found_channel = ch_ext
                    channel_verified = True
                if comm_ext and not commentator_verified:
                    found_commentator = comm_ext
                    commentator_verified = True
                if channel_verified and commentator_verified:
                    break

        # 4. من ESPN API نقبل القنوات العربية فقط
        if not found_channel and isinstance(comp_obj, dict):
            for b in (comp_obj.get("broadcasts") or comp_obj.get("geoBroadcasts") or []):
                if not isinstance(b, dict):
                    continue
                for cand_ch in (b.get("names") or []):
                    if _is_arabic_mena_channel(str(cand_ch)):
                        found_channel = str(cand_ch).strip()
                        channel_verified = True
                        break
                if channel_verified:
                    break
    except Exception:
        pass

    if not found_channel:
        found_channel = LEAGUE_RIGHTS_NETWORK.get(league_code, "لم تُحدد القناة بعد")
        channel_verified = False

    if not found_commentator:
        found_commentator = "غير متوفر" if match_state == "post" else "لم يُعلن بعد"
        commentator_verified = False

    return (
        found_channel, found_commentator, channel_verified, commentator_verified,
        matched_yk_url, matched_fg_url, matched_365_id, home_ar_exact, away_ar_exact
    )


def _fetch_365scores_single_game_channel(game_id: str) -> str:
    """فحص تفاصيل المباراة الفردية على 365Scores في حال لم تُدرج القناة في جدول allscores"""
    if not game_id:
        return ""
    for cid in (115, 131):
        try:
            url = f"https://webws.365scores.com/web/game/?appTypeId=5&langId=27&timezoneName=Asia/Riyadh&userCountryId={cid}&gameId={game_id}"
            data = fetch_json_fast(url, timeout=3.0)
            if not isinstance(data, dict):
                continue
            game = data.get("game") if isinstance(data.get("game"), dict) else data
            for net in (game.get("tvNetworks") or []):
                if isinstance(net, dict):
                    n_name = str(net.get("name") or "").strip()
                    if _is_arabic_mena_channel(n_name):
                        return n_name
        except Exception:
            continue
    return ""


def lookup_match_broadcast_on_demand(
    league_code: str,
    match_id: str,
    home_en: str,
    away_en: str,
    match_state: str = "pre",
    yk_url: str = "",
    fg_url: str = "",
    scores365_id: str = "",
    home_ar: str = "",
    away_ar: str = "",
    existing_channel: str = "",
    existing_ch_verified: bool = False
):
    """جلب المعلق والقناة الحقيقيين: يلا كورة -> في الجول -> 365Scores Game -> Bing News RSS (نص المقال الحقيقي) -> Google News"""
    cache_k = f"match_bcast_od_v4_{match_id}"
    cached, is_fresh = get_from_cache(cache_k, ttl=21600)
    if cached and is_fresh:
        return cached

    miss_k = f"match_bcast_miss_v4_{match_id}"
    miss_cached, miss_fresh = get_from_cache(miss_k, ttl=900)
    if miss_cached and miss_fresh:
        return miss_cached

    found_channel = existing_channel if existing_ch_verified else ""
    ch_ver = bool(existing_ch_verified)
    found_commentator = ""
    comm_ver = False

    # 1. صفحة المباراة المحددة على يلا كورة
    if yk_url:
        yk_ch, yk_comm = _fetch_yallakora_match_commentator(yk_url)
        if yk_ch and not ch_ver:
            found_channel, ch_ver = yk_ch, True
        if yk_comm:
            found_commentator, comm_ver = yk_comm, True

    # 2. صفحة المباراة المحددة على في الجول
    if fg_url and (not comm_ver or not ch_ver):
        fg_ch, fg_comm = _fetch_filgoal_match_commentator(fg_url)
        if fg_ch and not ch_ver:
            found_channel, ch_ver = fg_ch, True
        if fg_comm and not comm_ver:
            found_commentator, comm_ver = fg_comm, True

    # 3. تفاصيل المباراة الفردية على 365Scores (تغطي المباريات التي لم تظهر قناتها في allscores مثل فياريال وسلافيا براغ)
    if scores365_id and not ch_ver:
        s365_ch = _fetch_365scores_single_game_channel(scores365_id)
        if s365_ch:
            found_channel, ch_ver = s365_ch, True

    # 4. Bing News RSS + Google News RSS (Bing يعيد مقتطفاً من داخل نص المقال حيث يُذكر اسم المعلق الحقيقي!)
    if not comm_ver or not ch_ver:
        h_cands = _get_team_arabic_candidates(home_en, league_code, extra_ar=home_ar)
        a_cands = _get_team_arabic_candidates(away_en, league_code, extra_ar=away_ar)
        h_q = home_ar or next((x for x in h_cands if re.search(r"[\u0600-\u06FF]", x)), home_en)
        a_q = away_ar or next((x for x in a_cands if re.search(r"[\u0600-\u06FF]", x)), away_en)
        now_ts = time.time()

        q_comm = f"{h_q} {a_q} معلق القنوات الناقلة"
        rss_sources = [
            f"https://www.bing.com/news/search?q={urllib.parse.quote(q_comm)}&format=rss&setlang=ar&cc=SA",
            f"https://news.google.com/rss/search?q={urllib.parse.quote(q_comm + ' when:3d')}&hl=ar&gl=AE&ceid=AE:ar",
        ]

        for rss_url in rss_sources:
            if ch_ver and comm_ver:
                break
            try:
                req = urllib.request.Request(rss_url, headers=_AR_WEB_HEADERS)
                with urllib.request.urlopen(req, timeout=3.0, context=SSL_CONTEXT) as resp:
                    raw = resp.read()
                    if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)
                    root = ET.fromstring(raw)
                    for item in root.findall(".//item")[:12]:
                        pub_raw = item.findtext("pubDate") or ""
                        if pub_raw:
                            try:
                                if (now_ts - parsedate_to_datetime(pub_raw).timestamp()) > (96 * 3600):
                                    continue
                            except Exception:
                                pass
                        title_raw = html.unescape(item.findtext("title") or "")
                        # إزالة اسم الصحيفة من آخر العنوان (مثل "- جريدة الدستور" و "- شبكة تواصل")
                        title_clean = re.sub(r"\s+[-–—|]\s+[^-–—|]{2,45}$", "", title_raw).strip()
                        if any(bad in title_clean for bad in ("جدول مباريات", "مواعيد مباريات اليوم", "جميع مباريات")):
                            continue
                        norm_title = _normalize_ar_text(title_clean)
                        h_ok = _team_matches_norm_text(norm_title, h_cands, home_en)
                        a_ok = _team_matches_norm_text(norm_title, a_cands, away_en)
                        if not (h_ok and a_ok):
                            continue
                        desc_raw = html.unescape(re.sub(r"<[^>]+>", " ", item.findtext("description") or ""))
                        # allow_regex_comm=False -> نقبل فقط المعلقين الحقيقيين من القائمة الموثقة!
                        ch_ext, comm_ext = _extract_channel_and_commentator_from_text(
                            f"{title_clean} | {desc_raw}", strict_single=True, allow_regex_comm=False
                        )
                        if ch_ext and not ch_ver and _is_arabic_mena_channel(ch_ext):
                            found_channel, ch_ver = ch_ext, True
                        if comm_ext and not comm_ver:
                            found_commentator, comm_ver = comm_ext, True
                        if ch_ver and comm_ver:
                            break
            except Exception:
                continue

    result = {
        "channel": found_channel or LEAGUE_RIGHTS_NETWORK.get(league_code, "لم تُحدد القناة بعد"),
        "commentator": found_commentator or ("غير متوفر" if match_state == "post" else "لم يُعلن بعد"),
        "channel_verified": ch_ver,
        "commentator_verified": comm_ver,
        "yk_url": yk_url,
        "fg_url": fg_url,
        "scores365_id": scores365_id,
        "home_ar": home_ar,
        "away_ar": away_ar,
    }
    if ch_ver and comm_ver:
        save_to_cache(cache_k, result)
    else:
        save_to_cache(miss_k, result)
    return result
_TODAY_RAW_EVENTS = {}
MAX_TODAY_RAW_EVENTS = 250


def _store_today_raw_event(event_id: str, payload: dict):
    with _CACHE_LOCK:
        _TODAY_RAW_EVENTS[event_id] = payload
        if len(_TODAY_RAW_EVENTS) > MAX_TODAY_RAW_EVENTS:
            excess = len(_TODAY_RAW_EVENTS) - (MAX_TODAY_RAW_EVENTS - 50)
            for old_k in list(_TODAY_RAW_EVENTS.keys())[:excess]:
                _TODAY_RAW_EVENTS.pop(old_k, None)


def _hydrate_missing_commentators_bg(matches_to_hydrate: list):
    """جلب المعلقين والقنوات الموثقة في الخلفية دون حجب أو إبطاء فتح الصفحة الرئيسية"""
    pending = []
    with _CACHE_LOCK:
        for m_obj in matches_to_hydrate:
            mid = m_obj["id"]
            if mid not in _HYDRATING_MATCH_IDS:
                _HYDRATING_MATCH_IDS.add(mid)
                pending.append(dict(m_obj))
    if not pending:
        return

    def _worker():
        try:
            def _hydrate_one(m_copy):
                mid = m_copy["id"]
                try:
                    with _CACHE_LOCK:
                        ev_meta = dict(_TODAY_RAW_EVENTS.get(mid) or {})
                    bcast = lookup_match_broadcast_on_demand(
                        m_copy["league_code"],
                        mid,
                        m_copy.get("home_en", ""),
                        m_copy.get("away_en", ""),
                        m_copy.get("state", "pre"),
                        yk_url=ev_meta.get("yk_url", ""),
                        fg_url=ev_meta.get("fg_url", ""),
                        scores365_id=ev_meta.get("scores365_id", ""),
                        home_ar=ev_meta.get("home_ar", ""),
                        away_ar=ev_meta.get("away_ar", ""),
                        existing_channel=m_copy.get("channel", ""),
                        existing_ch_verified=bool(m_copy.get("channel_verified"))
                    )
                    with _CACHE_LOCK:
                        target_meta = _TODAY_RAW_EVENTS.get(mid)
                        if target_meta:
                            if bcast.get("channel_verified"):
                                target_meta["channel"] = bcast["channel"]
                                target_meta["channel_verified"] = True
                            if bcast.get("commentator_verified"):
                                target_meta["commentator"] = bcast["commentator"]
                                target_meta["commentator_verified"] = True
                except Exception:
                    pass
                finally:
                    with _CACHE_LOCK:
                        _HYDRATING_MATCH_IDS.discard(mid)

            with ThreadPoolExecutor(max_workers=4) as ex_h:
                list(ex_h.map(_hydrate_one, pending))
        except Exception:
            with _CACHE_LOCK:
                for item in pending:
                    _HYDRATING_MATCH_IDS.discard(item["id"])

    threading.Thread(target=_worker, daemon=True).start()

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
    state = "pre"

    if summary_data and isinstance(summary_data, dict):
        header_obj = summary_data.get("header") or {}
        comps = header_obj.get("competitions") or summary_data.get("competitions") or []
        if comps and isinstance(comps[0], dict):
            comp = comps[0]
            st_val = comp.get("status", {}).get("type", {}).get("state")
            if st_val:
                state = st_val
        for k in ("details", "scoringPlays", "keyEvents"):
            v = summary_data.get(k)
            if isinstance(v, list):
                all_events.extend(v)
        if comp and isinstance(comp.get("details"), list):
            all_events.extend(comp["details"])

    if event and isinstance(event, dict):
        ev_state = event.get("status", {}).get("type", {}).get("state")
        if ev_state and state == "pre":
            state = ev_state
        if not comp:
            comps = event.get("competitions") or []
            if comps and isinstance(comps[0], dict):
                comp = comps[0]
            if comp and isinstance(comp.get("details"), list):
                all_events.extend(comp["details"])

    h_team_id, a_team_id = "", ""
    h_team_name, a_team_name = "المضيف", "الضيف"
    h_score, a_score = 0, 0
    stats_map_h, stats_map_a = {}, {}

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

    # إذا لم تبدأ المباراة بعد، نُرجع حالة عدم البدء صراحةً بدون أي أرقام وهمية
    if state == "pre":
        return {
            "has_stats": False,
            "state": "pre",
            "home_score": "-",
            "away_score": "-",
            "display_clock": "",
            "status_text": "لم تبدأ بعد",
            "message": "⏳ لم تبدأ المباراة بعد — ستتوفر الإحصائيات الحية فور انطلاق صافرة البداية.",
            "home": {
                "possession": 0, "shots": 0, "shots_on_target": 0, "corners": 0,
                "fouls": 0, "yellow_cards": 0, "red_cards": 0, "offsides": 0, "pass_accuracy": 0
            },
            "away": {
                "possession": 0, "shots": 0, "shots_on_target": 0, "corners": 0,
                "fouls": 0, "yellow_cards": 0, "red_cards": 0, "offsides": 0, "pass_accuracy": 0
            },
            "home_goals": [],
            "away_goals": []
        }

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
            m_match = re.search(r"(\d+[\+\d]*)\s*['’]", str(ev["text"]))
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
            txt_clean = re.sub(r"\(.*?\)", "", str(ev["text"])).replace("Goal!", "").replace("Goal", "").strip()
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

    # استخراج الإحصائيات الحقيقية فقط من بيانات ESPN دون اختلاق أرقام وهمية
    has_real_stats = bool(stats_map_h or stats_map_a)

    pos_h = _safe_float(stats_map_h.get("possessionpct"), 50.0 if has_real_stats else 0.0)
    pos_a = _safe_float(stats_map_a.get("possessionpct"), (100.0 - pos_h) if has_real_stats else 0.0)
    shots_h = _safe_int(stats_map_h.get("totalshots", stats_map_h.get("shots")), 0)
    shots_a = _safe_int(stats_map_a.get("totalshots", stats_map_a.get("shots")), 0)
    sot_h = _safe_int(stats_map_h.get("shotsontarget", stats_map_h.get("shotsongoal")), 0)
    sot_a = _safe_int(stats_map_a.get("shotsontarget", stats_map_a.get("shotsongoal")), 0)
    corn_h = _safe_int(stats_map_h.get("woncorners", stats_map_h.get("cornerkicks")), 0)
    corn_a = _safe_int(stats_map_a.get("woncorners", stats_map_a.get("cornerkicks")), 0)
    fouls_h = _safe_int(stats_map_h.get("foulscommitted"), 0)
    fouls_a = _safe_int(stats_map_a.get("foulscommitted"), 0)
    offs_h = _safe_int(stats_map_h.get("offsides"), 0)
    offs_a = _safe_int(stats_map_a.get("offsides"), 0)

    raw_pass_h = stats_map_h.get("passpct", stats_map_h.get("accuratepasspct"))
    raw_pass_a = stats_map_a.get("passpct", stats_map_a.get("accuratepasspct"))
    pass_h = _safe_float(raw_pass_h, 0.0)
    if 0 < pass_h <= 1.0:
        pass_h = round(pass_h * 100.0, 1)
    elif pass_h > 100.0:
        pass_h = 0.0

    pass_a = _safe_float(raw_pass_a, 0.0)
    if 0 < pass_a <= 1.0:
        pass_a = round(pass_a * 100.0, 1)
    elif pass_a > 100.0:
        pass_a = 0.0

    yc_h = _safe_int(stats_map_h.get("yellowcards"), yc_h)
    yc_a = _safe_int(stats_map_a.get("yellowcards"), yc_a)
    rc_h = _safe_int(stats_map_h.get("redcards"), rc_h)
    rc_a = _safe_int(stats_map_a.get("redcards"), rc_a)

    st_node = (comp.get("status") if isinstance(comp, dict) else None) or (event.get("status") if isinstance(event, dict) else None) or {}
    disp_clock = str(st_node.get("displayClock") or "").strip()
    if state == "in":
        st_text = f"مباشر {disp_clock}" if disp_clock else "جارية الآن"
    elif state == "post":
        st_text = "انتهت"
    else:
        st_text = "لم تبدأ بعد"

    return {
        "has_stats": has_real_stats,
        "state": state,
        "home_score": str(h_score),
        "away_score": str(a_score),
        "display_clock": disp_clock,
        "status_text": st_text,
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

def get_todays_matches(target_date: str = "", force_refresh: bool = False):
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    now_local = now_utc + timedelta(hours=3)
    today_iso_local = now_local.strftime("%Y-%m-%d")

    clean_date = (target_date or "").strip()
    is_custom_date = False
    target_dt_local = now_local

    if clean_date and clean_date != today_iso_local:
        try:
            target_dt_local = datetime.strptime(clean_date[:10], "%Y-%m-%d")
            is_custom_date = True
        except Exception:
            is_custom_date = False
            target_dt_local = now_local

    target_day_iso = target_dt_local.strftime("%Y-%m-%d")
    cache_key = f"todays_matches_v5_{target_day_iso}"
    cache_ttl = 300 if is_custom_date else 35

    cached_matches, is_fresh = get_from_cache(cache_key, ttl=cache_ttl)
    if cached_matches is not None and is_fresh and not force_refresh:
        # دمج أي معلق أو قناة تم التحقق منها في الخلفية فوراً دون انتظار انتهاء الكاش
        with _CACHE_LOCK:
            for m_obj in cached_matches:
                meta = _TODAY_RAW_EVENTS.get(m_obj["id"])
                if meta:
                    if meta.get("channel_verified"):
                        m_obj["channel"] = meta["channel"]
                        m_obj["channel_verified"] = True
                    if meta.get("commentator_verified"):
                        m_obj["commentator"] = meta["commentator"]
                        m_obj["commentator_verified"] = True
        return cached_matches

    # جلب اليوم المختار + اليوم السابق لتغطية جميع مباريات فرق التوقيت (UTC+3) بدقة
    prev_day_str = (target_dt_local - timedelta(days=1)).strftime("%Y%m%d")
    target_day_str = target_dt_local.strftime("%Y%m%d")
    dates_to_fetch = [prev_day_str, target_day_str]

    all_today_matches = []
    scraped_broadcast_blocks = _scrape_live_arabic_broadcast_tables(target_dt_local)

    def fetch_league_today(code, info):
        espn_code = info["espn"]
        matches = []
        seen_events = set()

        for d_str in dates_to_fetch:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={d_str}"
            data = fetch_json_fast(url, timeout=3.5)
            if not data or "events" not in data:
                continue

            for event in data.get("events", []):
                try:
                    event_id = str(event.get("id"))
                    if not event_id or event_id in seen_events:
                        continue

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
                    local_kickoff = None

                    if date_raw and "T" in date_raw:
                        try:
                            utc_kickoff = datetime.strptime(date_raw[:16], "%Y-%m-%dT%H:%M")
                            local_kickoff = utc_kickoff + timedelta(hours=3)
                            time_str = local_kickoff.strftime("%H:%M")
                        except Exception:
                            time_str = date_raw[11:16]

                    # فلترة صارمة حسب التاريخ المحلي المختار (مع إبقاء المباريات الجارية الآن في تبويب اليوم)
                    local_day_iso = local_kickoff.strftime("%Y-%m-%d") if local_kickoff else target_day_iso
                    if not (not is_custom_date and state == "in"):
                        if local_day_iso != target_day_iso:
                            continue

                    if state == "in":
                        status_text = f"مباشر {display_clock}" if display_clock else "جارية الآن"
                        is_live = True
                    elif state == "post":
                        is_live = False
                        if not is_custom_date and utc_kickoff:
                            utc_finish_time = utc_kickoff + timedelta(hours=2)
                            hours_since_finish = max(0.0, (now_utc - utc_finish_time).total_seconds() / 3600.0)
                            status_text = "انتهت منذ قليل" if hours_since_finish <= 1.0 else f"انتهت (منذ {int(hours_since_finish)} س)"
                        else:
                            status_text = "انتهت"
                    else:
                        is_live = False
                        status_text = "لم تبدأ بعد"

                    seen_events.add(event_id)

                    venue_data = comp.get("venue", {})
                    venue_name = venue_data.get("fullName", "الملعب الرئيسي")
                    city = venue_data.get("address", {}).get("city", "")
                    full_venue = f"{venue_name} ({city})" if city else venue_name

                    h_disp_name = h_raw["team"].get("shortDisplayName", h_raw["team"].get("displayName", "Home"))
                    a_disp_name = a_raw["team"].get("shortDisplayName", a_raw["team"].get("displayName", "Away"))
                    h_en_name = h_raw["team"].get("displayName", h_disp_name)
                    a_en_name = a_raw["team"].get("displayName", a_disp_name)

                    kickoff_utc_ts = utc_kickoff.replace(tzinfo=timezone.utc).timestamp() if utc_kickoff else 0.0
                    (
                        real_channel, real_commentator, ch_verified, comm_verified,
                        yk_url, fg_url, s365_id, h_ar_exact, a_ar_exact
                    ) = _resolve_match_broadcast_and_commentator(
                        code,
                        event_id,
                        h_en_name,
                        a_en_name,
                        comp,
                        scraped_broadcast_blocks,
                        match_state=state,
                        kickoff_utc_ts=kickoff_utc_ts
                    )

                    _store_today_raw_event(event_id, {
                        "event": event,
                        "league_code": code,
                        "info": info,
                        "home_en": h_en_name,
                        "away_en": a_en_name,
                        "home_ar": h_ar_exact,
                        "away_ar": a_ar_exact,
                        "state": state,
                        "channel": real_channel,
                        "commentator": real_commentator,
                        "channel_verified": ch_verified,
                        "commentator_verified": comm_verified,
                        "yk_url": yk_url,
                        "fg_url": fg_url,
                        "scores365_id": s365_id
                    })

                    embedded_stats = _extract_stats_and_goals_from_event(event) if state in ("in", "post") else None

                    matches.append({
                        "id": event_id,
                        "league_code": code,
                        "league_name": info["name"],
                        "league_flag": info["flag"],
                        "kickoff_time": time_str,
                        "kickoff_iso": date_raw,
                        "sort_ts": kickoff_utc_ts,
                        "status_text": status_text,
                        "state": state,
                        "is_live": is_live,
                        "home_id": str(h_raw["team"].get("id") or h_raw.get("id") or ""),
                        "home_team": h_disp_name,
                        "home_en": h_en_name,
                        "home_crest": h_raw["team"].get("logo") or DEFAULT_CLUB_CREST,
                        "home_score": h_raw.get("score", "0") if state in ("in", "post") else "-",
                        "away_id": str(a_raw["team"].get("id") or a_raw.get("id") or ""),
                        "away_team": a_disp_name,
                        "away_en": a_en_name,
                        "away_crest": a_raw["team"].get("logo") or DEFAULT_CLUB_CREST,
                        "away_score": a_raw.get("score", "0") if state in ("in", "post") else "-",
                        "venue": full_venue,
                        "channel": real_channel,
                        "channel_verified": ch_verified,
                        "commentator": real_commentator,
                        "commentator_verified": comm_verified,
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
        if m["is_live"]:
            return (0, m.get("sort_ts", 0))
        if m["state"] == "pre":
            return (1, m.get("sort_ts", 0))
        return (2, -m.get("sort_ts", 0))

    all_today_matches.sort(key=sort_key)

    # تخزين النتيجة فوراً ثم تشغيل سحب المعلقين في الخلفية بدون تأخير المستخدم
    save_to_cache(cache_key, all_today_matches)

    to_hydrate = [m for m in all_today_matches if m.get("state") in ("pre", "in") and not m.get("commentator_verified")][:16]
    if to_hydrate:
        _hydrate_missing_commentators_bg(to_hydrate)

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
    if summary_data and isinstance(summary_data.get("rosters"), list) and len(summary_data["rosters"]) >= 2:
        try:
            result["lineups"] = get_match_lineups(league_code, match_id, preloaded_summary=summary_data)
        except Exception:
            pass

    if cached_item and (not cached_item.get("channel_verified") or not cached_item.get("commentator_verified")):
        try:
            bcast = lookup_match_broadcast_on_demand(
                league_code,
                match_id,
                cached_item.get("home_en", ""),
                cached_item.get("away_en", ""),
                cached_item.get("state", "pre"),
                yk_url=cached_item.get("yk_url", ""),
                fg_url=cached_item.get("fg_url", ""),
                scores365_id=cached_item.get("scores365_id", ""),
                home_ar=cached_item.get("home_ar", ""),
                away_ar=cached_item.get("away_ar", ""),
                existing_channel=cached_item.get("channel", ""),
                existing_ch_verified=bool(cached_item.get("channel_verified"))
            )
            # الحفاظ على القناة الموثّقة سابقاً إذا لم يُعثر على بديل أفضل عند الطلب
            if cached_item.get("channel_verified") and not bcast.get("channel_verified"):
                bcast["channel"] = cached_item.get("channel", bcast["channel"])
                bcast["channel_verified"] = True
            if cached_item.get("commentator_verified") and not bcast.get("commentator_verified"):
                bcast["commentator"] = cached_item.get("commentator", bcast["commentator"])
                bcast["commentator_verified"] = True
            cached_item.update({
                "channel": bcast["channel"],
                "commentator": bcast["commentator"],
                "channel_verified": bcast["channel_verified"],
                "commentator_verified": bcast["commentator_verified"],
            })
            result["broadcast"] = bcast
        except Exception:
            pass
    elif cached_item:
        result["broadcast"] = {
            "channel": cached_item.get("channel", ""),
            "commentator": cached_item.get("commentator", ""),
            "channel_verified": cached_item.get("channel_verified", False),
            "commentator_verified": cached_item.get("commentator_verified", False),
        }

    return result

# =========================================================================
# 8. محاكي نهاية الموسم (Monte Carlo)
# =========================================================================
def get_season_projections(league_code, num_sims=1500, force_refresh=False):
    cache_key = f"monte_carlo_v6_{league_code}"
    cached_data, is_fresh = get_from_cache(cache_key, ttl=3600)
    if cached_data and is_fresh and not force_refresh:
        return cached_data

    standings = get_official_standings(league_code, force_refresh=force_refresh)
    if not standings or len(standings) < 4:
        return []

    from engine_core import simulate_season_outcomes
    results = simulate_season_outcomes(
        league_code=league_code,
        standings_data=standings,
        num_sims=num_sims,
        competition_rules=COMPETITION_FORMAT_RULES.get(league_code)
    )

    if results:
        save_to_cache(cache_key, results)
    return results

# =========================================================================
# 10. غرفة الأخبار الرياضية الحية (Live API + FIFO 20 Items)
# =========================================================================
def init_news_table():
    with _DB_LOCK:
        conn = get_connection()
        try:
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
        finally:
            conn.close()


def fetch_live_online_news():
    rss_feeds = [
        "https://www.skynewsarabia.com/rss/sport.xml",
        "https://arabic.rt.com/rss/sport/",
        "https://news.google.com/rss/search?q=%D9%83%D8%B1%D8%A9+%D8%A7%D9%84%D9%82%D8%AF%D9%85+%D8%A3%D9%88%D8%B1%D9%88%D8%A8%D8%A7&hl=ar&gl=AE&ceid=AE:ar"
    ]
    espn_news_leagues = ["eng.1", "esp.1", "uefa.champions", "ita.1", "ger.1"]

    def _pull_rss(feed_url):
        out = []
        try:
            req = urllib.request.Request(feed_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=4.0, context=SSL_CONTEXT) as resp:
                xml_content = resp.read()
                root = ET.fromstring(xml_content)
                for item in root.findall(".//item")[:12]:
                    title = (item.findtext("title") or "").strip()
                    if not title:
                        continue
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

                    out.append({
                        "id": hashlib.md5(title.encode("utf-8")).hexdigest()[:14],
                        "title": title,
                        "summary": desc,
                        "image_url": img_url,
                        "source_url": link,
                        "published_time": pub_date[:16] if pub_date else "تحديث مباشر"
                    })
        except Exception:
            pass
        return out

    def _pull_espn(lg):
        out = []
        try:
            espn_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg}/news"
            data = fetch_json_fast(espn_url, timeout=3.5)
            if isinstance(data, dict) and "articles" in data:
                for art in data.get("articles", [])[:8]:
                    title = (art.get("headline") or "").strip()
                    if not title:
                        continue
                    desc = (art.get("description") or art.get("story") or "").strip()
                    desc = re.sub(r'<[^>]+>', '', desc).strip()

                    img_url = ""
                    images = art.get("images", [])
                    if images and isinstance(images, list):
                        img_url = images[0].get("url", "")

                    links = art.get("links", {})
                    web_link = links.get("web", {}).get("href", "") if isinstance(links, dict) else ""
                    pub_time = (art.get("published") or "")[:16].replace("T", " ")

                    out.append({
                        "id": str(art.get("id") or hashlib.md5(title.encode("utf-8")).hexdigest()[:14]),
                        "title": title,
                        "summary": desc or title,
                        "image_url": img_url,
                        "source_url": web_link,
                        "published_time": pub_time or "الآن"
                    })
        except Exception:
            pass
        return out

    live_articles = []
    seen_titles = set()
    with ThreadPoolExecutor(max_workers=6) as ex:
        rss_futs = [ex.submit(_pull_rss, u) for u in rss_feeds]
        espn_futs = [ex.submit(_pull_espn, lg) for lg in espn_news_leagues]

        for fut in rss_futs + espn_futs:
            for art in (fut.result() or []):
                if art["title"] not in seen_titles:
                    seen_titles.add(art["title"])
                    live_articles.append(art)

    return live_articles[:30]


def sync_and_get_news(force_refresh=False):
    cached, is_fresh = get_from_cache("global_sports_news", ttl=300)
    if cached and is_fresh and not force_refresh:
        return cached

    init_news_table()
    now_ts = time.time()
    incoming_articles = fetch_live_online_news()

    with _DB_LOCK:
        conn = get_connection()
        try:
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
        finally:
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

    # =========================================================================
# 12. جلب مجريات وأحداث المباراة بالدقيقة من خوادم ESPN مباشرة
# =========================================================================
def get_match_events(league_code: str, match_id: str, preloaded_summary=None):
    match_id = str(match_id).strip()
    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")

    data = preloaded_summary
    if not data or not isinstance(data, dict):
        urls = [
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
            f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={match_id}"
        ]
        for u in urls:
            res = fetch_json_fast(u, timeout=4.0)
            if res and isinstance(res, dict) and ("header" in res or "keyEvents" in res or "rosters" in res):
                data = res
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

    h_team_id, a_team_id = "", ""
    h_team_name, a_team_name = "المضيف", "الضيف"

    if comp:
        for c in comp.get("competitors", []):
            t_obj = c.get("team", {})
            if c.get("homeAway") == "home":
                h_team_id = str(t_obj.get("id") or c.get("id") or "")
                h_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "المضيف"
            elif c.get("homeAway") == "away":
                a_team_id = str(t_obj.get("id") or c.get("id") or "")
                a_team_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or "الضيف"

    if state == "pre":
        return {
            "has_events": False,
            "state": "pre",
            "home_team": h_team_name,
            "away_team": a_team_name,
            "events": []
        }

    events_list = []
    seen_keys = set()

    def parse_clock_str(ev_obj):
        clk = ""
        clock_node = ev_obj.get("clock") or ev_obj.get("time")
        if isinstance(clock_node, dict):
            clk = clock_node.get("displayValue") or str(clock_node.get("value", ""))
        elif clock_node:
            clk = str(clock_node)
        if not clk and ev_obj.get("text"):
            m = re.search(r'(\d+(?:\+\d+)?)\s*[\'’]', str(ev_obj.get("text", "")))
            if m:
                clk = m.group(1)
        clk = str(clk).strip().replace("'", "").replace("’", "")
        if not clk:
            return "1'", 1.0
        parts = clk.split("+")
        try:
            base_m = int(float(parts[0]))
            if base_m > 130:
                base_m = max(1, base_m // 60)
                clk = str(base_m)
            ext_m = int(float(parts[1])) if len(parts) > 1 else 0
            sort_val = float(base_m) + (ext_m * 0.01)
            disp = f"{base_m}+{ext_m}'" if ext_m > 0 else f"{base_m}'"
            return disp, sort_val
        except Exception:
            return f"{clk}'", 45.0

    def detect_team_side(ev_obj, raw_text=""):
        t_node = ev_obj.get("team") or {}
        tid = str(t_node.get("id") or "") if isinstance(t_node, dict) else ""
        t_disp = (t_node.get("displayName") or t_node.get("shortDisplayName") or "") if isinstance(t_node, dict) else ""
        ha = str(ev_obj.get("homeAway") or "").lower()

        if ha == "home" or (tid and tid == h_team_id):
            return "home", h_team_name
        if ha == "away" or (tid and tid == a_team_id):
            return "away", a_team_name
        if h_team_name.lower() in t_disp.lower() or h_team_name.lower() in raw_text.lower():
            return "home", h_team_name
        if a_team_name.lower() in t_disp.lower() or a_team_name.lower() in raw_text.lower():
            return "away", a_team_name
        return "home", h_team_name

    def extract_participants(ev_obj, raw_text=""):
        p1, p2 = "", ""
        inv = ev_obj.get("participants") or ev_obj.get("athletesInvolved") or []
        if isinstance(inv, list):
            if len(inv) >= 1 and isinstance(inv[0], dict):
                a0 = inv[0].get("athlete", inv[0])
                if isinstance(a0, dict):
                    p1 = a0.get("displayName") or a0.get("shortName") or ""
            if len(inv) >= 2 and isinstance(inv[1], dict):
                a1 = inv[1].get("athlete", inv[1])
                if isinstance(a1, dict):
                    p2 = a1.get("displayName") or a1.get("shortName") or ""

        if not p1 and isinstance(ev_obj.get("athlete"), dict):
            p1 = ev_obj["athlete"].get("displayName") or ev_obj["athlete"].get("shortName") or ""

        if raw_text:
            sub_m = re.search(r'([A-Za-zÀ-ÿ\'\-\.\s]{3,30}?)\s+replaces\s+([A-Za-zÀ-ÿ\'\-\.\s]{3,30})', raw_text)
            if sub_m:
                if not p1: p1 = sub_m.group(1).split(".")[-1].strip()
                if not p2: p2 = sub_m.group(2).split(".")[0].strip()
            if not p1:
                p_m = re.search(r'([A-ZÀ-Ÿ][A-Za-zÀ-ÿ\'\-\.]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ\'\-\.]+){0,2})\s*\([^)]+\)', raw_text)
                if p_m:
                    cand = p_m.group(1).strip()
                    if not any(w in cand.lower() for w in ["goal", "attempt", "offside", "foul", "penalty", "var", "substitution"]):
                        p1 = cand
            if not p2 and "assisted by" in raw_text.lower():
                ast_m = re.search(r'[Aa]ssisted by\s+([A-Za-zÀ-ÿ\'\-\.\s]{3,28}?)(?:\s+with|\.|,|$)', raw_text)
                if ast_m:
                    p2 = ast_m.group(1).strip()

        return p1.strip(), p2.strip()

    def process_raw_event(ev_obj, is_commentary=False):
        if not isinstance(ev_obj, dict):
            return
        play_sub = ev_obj.get("play") if isinstance(ev_obj.get("play"), dict) else {}
        merged = dict(play_sub)
        merged.update(ev_obj)

        t_obj = merged.get("type") or play_sub.get("type") or {}
        type_txt = (t_obj.get("text") or t_obj.get("name") or "").lower() if isinstance(t_obj, dict) else str(t_obj).lower()
        raw_txt = str(merged.get("text") or merged.get("shortText") or "").strip()
        low_txt = raw_txt.lower()

        clock_disp, sort_m = parse_clock_str(merged)
        base_min = int(sort_m)
        side, team_name = detect_team_side(merged, raw_txt)
        p1, p2 = extract_participants(merged, raw_txt)

        ev_cat = None
        title_ar = ""
        detail_ar = ""

        # 1. هدف ملغي بواسطة الفار VAR أو بداعي التسلل
        if any(w in low_txt or w in type_txt for w in ["disallowed", "overturned", "no goal", "goal cancelled", "var decision"]) or (
            "offside" in low_txt and ("goal" in low_txt or "disallowed" in low_txt)
        ):
            ev_cat = "disallowed_goal"
            reason = "بعد مراجعة تقنية الفيديو (VAR)" if ("var" in low_txt or "var" in type_txt or "overturned" in low_txt) else "بقرار من الحكم بداعي التسلل"
            title_ar = f"🚫⚽ هدف ملغي ({'VAR' if 'VAR' in reason else 'تسلل'})"
            detail_ar = f"إلغاء هدف لـ {p1 or team_name} {reason}"

        # 2. ركلة جزاء ضائعة
        elif any(w in low_txt or w in type_txt for w in ["penalty - missed", "penalty - saved", "penalty missed", "penalty saved"]):
            ev_cat = "missed_penalty"
            saved_flag = "saved" in low_txt or "saved" in type_txt
            title_ar = f"❌ ضربة جزاء ضائعة — {p1 or team_name}"
            detail_ar = f"{p1 or 'اللاعب'} أهدر ركلة جزاء ({'تصدى لها الحارس ببراعة' if saved_flag else 'مرت خارج المرمى'})"

        # 3. هدف صحيح
        elif (merged.get("scoringPlay") is True or "goal" in type_txt or low_txt.startswith("goal!")) and not any(
            w in low_txt or w in type_txt for w in ["missed", "saved", "disallowed", "cancelled", "no goal"]
        ):
            ev_cat = "goal"
            is_pen = merged.get("penaltyKick") or "penalty" in type_txt or "penalty" in low_txt
            is_og = merged.get("ownGoal") or "own goal" in type_txt or "own goal" in low_txt
            tag = " (ركلة جزاء)" if is_pen else (" (هدف عكسي)" if is_og else "")
            title_ar = f"⚽ هدف! — {p1 or team_name}{tag}"
            detail_ar = f"صناعة الهدف (Assist): {p2}" if p2 else f"هدف لصالح {team_name} عن طريق {p1 or 'الفريق'}"

        # 4. تسديدة في القائم أو العارضة
        elif any(w in low_txt or w in type_txt for w in ["hits the left post", "hits the right post", "hits the bar", "hits the crossbar", "hit the post", "hit the crossbar", "woodwork"]):
            ev_cat = "woodwork"
            bar_or_post = "العارضة" if "bar" in low_txt else "القائم"
            title_ar = f"🥅 تسديدة في {bar_or_post}! — {p1 or team_name}"
            detail_ar = f"فرصة خطيرة جداً! تسديدة {p1 or team_name} ارتطمت بـ{bar_or_post}"

        # 5. تبديل لاعبين
        elif "subst" in type_txt or "substitution" in low_txt or "replaces" in low_txt:
            ev_cat = "sub"
            title_ar = f"🔄 تبديل — {team_name}"
            detail_ar = f"دخول: {p1 or 'لاعب بديل'} | خروج: {p2 or 'لاعب أساسي'}"

        # 6. بطاقة حمراء
        elif "red card" in type_txt or "second yellow" in type_txt or "red card" in low_txt or "second yellow" in low_txt:
            ev_cat = "red_card"
            is_second = "second yellow" in type_txt or "second yellow" in low_txt
            title_ar = f"🟥 بطاقة حمراء (طرد) — {p1 or team_name}"
            detail_ar = "طرد بعد تلقي الإنذار الثاني" if is_second else f"بطاقة حمراء مباشرة لـ {p1 or team_name}"

        # 7. بطاقة صفراء
        elif "yellow card" in type_txt or "yellow card" in low_txt:
            ev_cat = "yellow_card"
            title_ar = f"🟨 بطاقة صفراء — {p1 or team_name}"
            detail_ar = f"إنذار شفهي وبطاقة صفراء على {p1 or team_name}"

        # 8. فرصة خطيرة محققة
        elif is_commentary and any(w in low_txt for w in ["attempt saved", "big chance", "great save", "close range"]) and p1:
            ev_cat = "big_chance"
            title_ar = f"🔥 فرصة خطيرة — {p1}"
            detail_ar = f"محاولة هجومية خطيرة من {p1} على المرمى تصدى لها الدفاع/الحارس"

        if not ev_cat:
            return

        dedup_id = f"{ev_cat}_{base_min // 2}_{(p1 or team_name)[:8].lower()}"
        if dedup_id in seen_keys:
            return
        seen_keys.add(dedup_id)

        events_list.append({
            "clock": clock_disp,
            "sort_minute": sort_m,
            "type": ev_cat,
            "side": side,
            "team_name": team_name,
            "player": p1 or team_name,
            "secondary_player": p2,
            "title": title_ar,
            "detail": detail_ar
        })

    if data:
        for k in ("keyEvents", "scoringPlays", "details"):
            if isinstance(data.get(k), list):
                for item in data[k]:
                    process_raw_event(item, is_commentary=False)
        if comp and isinstance(comp.get("details"), list):
            for item in comp["details"]:
                process_raw_event(item, is_commentary=False)
        for k in ("commentary", "plays"):
            if isinstance(data.get(k), list):
                for item in data[k]:
                    process_raw_event(item, is_commentary=True)

        # استخراج إضافي من rosters (التبديلات والبطاقات المسجلة على اللاعبين)
        rosters = data.get("rosters", [])
        if isinstance(rosters, list):
            for r_obj in rosters:
                if not isinstance(r_obj, dict):
                    continue
                r_side = "home" if r_obj.get("homeAway") == "home" else "away"
                r_tname = h_team_name if r_side == "home" else a_team_name
                for p in (r_obj.get("roster") or []):
                    if not isinstance(p, dict):
                        continue
                    for pl in (p.get("plays") or []):
                        if isinstance(pl, dict):
                            pl_copy = dict(pl)
                            pl_copy["homeAway"] = r_side
                            if "team" not in pl_copy:
                                pl_copy["team"] = {"displayName": r_tname}
                            process_raw_event(pl_copy, is_commentary=False)

    if cached_event and not events_list:
        c_comp = (cached_event.get("competitions") or [{}])[0]
        for item in (c_comp.get("details") or []):
            process_raw_event(item, is_commentary=False)

    events_list.sort(key=lambda x: x["sort_minute"])

    return {
        "has_events": len(events_list) > 0,
        "state": state,
        "home_team": h_team_name,
        "away_team": a_team_name,
        "events": events_list
    }

# =========================================================================
# 13. محرك الموسوعة والأرشيف التاريخي الشامل (Wikipedia API + ESPN API + SQLite)
# =========================================================================
# =========================================================================
# 13. محرك الموسوعة والأرشيف التاريخي الشامل (منذ 1888 - المسمى القديم والحديث)
# =========================================================================


WIKI_LEAGUE_PAGES = {
    "PL": "List_of_English_football_champions",
    "PD": "List_of_Spanish_football_champions",
    "BL1": "List_of_German_football_champions",
    "SA": "List_of_Italian_football_champions",
    "FL1": "List_of_French_football_champions",
    "DED": "List_of_Dutch_football_champions",
    "PPL": "List_of_Portuguese_football_champions",
    "TSL": "List_of_Turkish_football_champions",
    "UCL": "List_of_European_Cup_and_UEFA_Champions_League_finals",
    "ACL": "List_of_Asian_Club_Championship_and_AFC_Champions_League_Elite_finals",
    "CAF": "List_of_African_Cup_of_Champions_Clubs_and_CAF_Champions_League_finals",
    "UNL": "List_of_UEFA_Nations_League_finals"
}

ARABIC_CLUB_MAP = {
    # إنجلترا (شاملاً أندية 1888 والمسميات القديمة مثل The Wednesday)
    "Manchester United": "مانشستر يونايتد", "Liverpool": "ليفربول", "Arsenal": "أرسنال",
    "Manchester City": "مانشستر سيتي", "Chelsea": "تشيلسي", "Aston Villa": "أستون فيلا",
    "Everton": "إيفرتون", "Tottenham Hotspur": "توتنهام هوتسبير", "Newcastle United": "نيوكاسل يونايتد",
    "Sunderland": "سندرلاند", "Sheffield Wednesday": "شيفيلد وينزداي", "The Wednesday": "شيفيلد وينزداي",
    "Wolverhampton Wanderers": "وولفرهامبتون", "Leeds United": "ليدز يونايتد",
    "Huddersfield Town": "هادرسفيلد تاون", "Blackburn Rovers": "بلاكبيرن روفرز",
    "Preston North End": "بريستون نورث إند", "Derby County": "ديربي كاونتي", "Burnley": "بيرنلي",
    "Portsmouth": "بورتسموث", "Sheffield United": "شيفيلد يونايتد", "West Bromwich Albion": "وست بروميتش",
    "Ipswich Town": "إبسويتش تاون", "Nottingham Forest": "نوتنغهام فورست", "Leicester City": "ليستر سيتي",
    "Bolton Wanderers": "بولتون واندررز", "Notts County": "نوتس كاونتي", "Bristol City": "بريستول سيتي",
    "Middlesbrough": "ميدلزبره", "Oldham Athletic": "أولدهام أثلتيك", "Cardiff City": "كارديف سيتي",
    "Charlton Athletic": "تشارلتون أثلتيك", "Blackpool": "بلاكبول", "Queens Park Rangers": "كوينز بارك رينجرز",
    "Watford": "واتفورد", "Southampton": "ساوثهامبتون", "Norwich City": "نورويتش سيتي",
    # إسبانيا
    "Real Madrid": "ريال مدريد", "Barcelona": "برشلونة", "Atlético Madrid": "أتلتيكو مدريد",
    "Athletic Bilbao": "أتلتيك بيلباو", "Valencia": "فالنسيا", "Real Sociedad": "ريال سوسيداد",
    "Deportivo La Coruña": "ديبورتيفو لاكورونيا", "Sevilla": "إشبيلية", "Real Betis": "ريال بيتيس",
    "Villarreal": "فياريال", "Girona": "جيرونا", "Real Zaragoza": "ريال سرقسطة",
    "Racing Santander": "راسينغ سانتاندير", "Las Palmas": "لاس بالماس", "Sporting Gijón": "سبورتينغ خيخون",
    # ألمانيا
    "Bayern Munich": "بايرن ميونخ", "Borussia Dortmund": "بوروسيا دورتموند",
    "Borussia Mönchengladbach": "بوروسيا مونشنغلادباخ", "Werder Bremen": "فيردر بريمن",
    "Hamburger SV": "هامبورغ", "VfB Stuttgart": "شتوتغارت", "1. FC Köln": "كولن",
    "1. FC Kaiserslautern": "كايزرسلاوترن", "1. FC Nürnberg": "نورنبرغ", "Schalke 04": "شالكه 04",
    "Bayer Leverkusen": "باير ليفركوزن", "VfL Wolfsburg": "فولفسبورغ", "RB Leipzig": "لايبزيغ",
    "Eintracht Frankfurt": "آينتراخت فرانكفورت", "Hertha BSC": "هيرتا برلين", "VfB Leipzig": "لايبزيغ القديم",
    "1860 Munich": "ميونخ 1860", "Eintracht Braunschweig": "آينتراخت براونشفايغ",
    # إيطاليا (شاملاً المسميات القديمة مثل Ambrosiana-Inter)
    "Juventus": "يوفنتوس", "Juventus Cisitalia": "يوفنتوس",
    "Inter Milan": "إنتر ميلان", "Internazionale": "إنتر ميلان", "Ambrosiana-Inter": "إنتر ميلان", "Ambrosiana": "إنتر ميلان",
    "AC Milan": "ميلان", "Milan": "ميلان", "Genoa": "جنوى", "Torino": "تورينو",
    "Bologna": "بولونيا", "Pro Vercelli": "برو فيرتشيلي", "Napoli": "نابولي",
    "Roma": "روما", "Lazio": "لاتسيو", "Fiorentina": "فيورنتينا", "Cagliari": "كالياري",
    "Hellas Verona": "هيلاس فيرونا", "Sampdoria": "سامبدوريا", "Atalanta": "أتالانتا",
    "Casale": "كازالي", "Novese": "نوفيزي",
    # فرنسا وهولندا والبرتغال وتركيا وأوروبا
    "Paris Saint-Germain": "باريس سان جيرمان", "Saint-Étienne": "سانت إتيان", "Marseille": "أولمبيك مارسيليا",
    "Olympique de Marseille": "أولمبيك مارسيليا", "Monaco": "موناكو", "AS Monaco": "موناكو",
    "Nantes": "نانت", "Lyon": "أولمبيك ليون", "Olympique Lyonnais": "أولمبيك ليون",
    "Bordeaux": "بوردو", "Lille": "ليل", "Olympique Lillois": "أولمبيك ليل",
    "Reims": "ستاد ريمس", "Stade de Reims": "ستاد ريمس", "Nice": "نيس", "Lens": "لانس", "RC Lens": "لانس",
    "Montpellier": "مونبلييه", "Auxerre": "أوسير", "Strasbourg": "ستراسبورغ", "Sochaux": "سوشو", "Sète": "سيت",
    "Ajax": "أياكس أمستردام", "PSV Eindhoven": "آيندهوفن", "PSV": "آيندهوفن",
    "Feyenoord": "فاينورد روتردام", "AZ": "إي زد ألكمار", "AZ '67": "إي زد ألكمار", "Twente": "تفنتي أنشخيده",
    "Sparta Rotterdam": "سبارتا روتردام", "Sparta": "سبارتا روتردام", "HVV": "لاهاي HVV", "HVV Den Haag": "لاهاي HVV",
    "Benfica": "بنفيكا", "Porto": "بورتو", "FC Porto": "بورتو", "Sporting CP": "سبورتينغ لشبونة",
    "Boavista": "بوافيشتا", "Belenenses": "بيلينينسيس", "Braga": "سبورتينغ براغا",
    "Galatasaray": "غلطة سراي", "Fenerbahçe": "فنربخشة", "Beşiktaş": "بشكتاش",
    "Trabzonspor": "طرابزون سبور", "Bursaspor": "بورصا سبور", "İstanbul Başakşehir": "باشاك شهير",
    "Celtic": "سلتيك", "Steaua București": "ستيوا بوخارست", "Red Star Belgrade": "النجم الأحمر بلغراد",
    # أندية دوري أبطال آسيا
    "Al Hilal": "الهلال السعودي", "Al-Hilal": "الهلال السعودي", "Al Nassr": "النصر السعودي", "Al-Nassr": "النصر السعودي",
    "Al Ahli": "الأهلي السعودي", "Al-Ahli": "الأهلي السعودي", "Al Ittihad": "الاتحاد السعودي", "Al-Ittihad": "الاتحاد السعودي",
    "Al Ain": "العين الإماراتي", "Al-Ain": "العين الإماراتي", "Al Sadd": "السد القطري", "Al-Sadd": "السد القطري",
    "Urawa Red Diamonds": "أوراوا ريد دايموندز", "Pohang Steelers": "بوهانغ ستيلرز",
    "Jeonbuk Hyundai Motors": "تشونبوك هيونداي موتورز", "Ulsan HD": "أولسان هيونداي", "Ulsan Hyundai": "أولسان هيونداي",
    "Guangzhou": "غوانغجو إيفرغراند", "Guangzhou Evergrande": "غوانغجو إيفرغراند", "Esteghlal": "الاستقلال",
    "Persepolis": "بيرسبوليس", "Kashima Antlers": "كاشيما أنتلرز", "Gamba Osaka": "غامبا أوساكا",
    "Yokohama F. Marinos": "يوكوهاما مارينوس", "Al Wasl": "الوصل الإماراتي", "Al Rayyan": "الريان القطري",
    "Al Gharafa": "الغرافة القطري", "Pakhtakor": "باختاكور", "Al Shorta": "الشرطة العراقي",
    # أندية دوري أبطال أفريقيا
    "Al Ahly": "الأهلي المصري", "Zamalek": "الزمالك", "Espérance de Tunis": "الترجي التونسي", "Espérance": "الترجي التونسي",
    "TP Mazembe": "مازيمبي", "Wydad AC": "الوداد الرياضي", "Raja CA": "الرجاء الرياضي",
    "Mamelodi Sundowns": "ماميلودي صن داونز", "Pyramids": "بيراميدز", "CR Belouizdad": "شباب بلوزداد",
    "MC Alger": "مولودية الجزائر", "JS Kabylie": "شبيبة القبائل", "ES Sétif": "وفاق سطيف",
    "Étoile du Sahel": "النجم الساحلي", "Club Africain": "النادي الأفريقي", "FAR Rabat": "الجيش الملكي",
    "AS FAR": "الجيش الملكي", "Orlando Pirates": "أورلاندو بايرتس", "Kaizer Chiefs": "كايزر تشيفز",
    "Al Hilal Omdurman": "الهلال السوداني", "Enyimba": "أنيمبا النيجيري", "Asante Kotoko": "أشانتي كوتوكو",
    "Canon Yaoundé": "كانون ياوندي", "Hafia": "حافيا كوناكري", "ASEC Mimosas": "أسيك ميموزا", "Vita Club": "فيتا كلوب"
}

ALL_LEAGUES_META_RECORDS = {
    "PL": {
        "league_name": "الدوري الإنجليزي (Football League 1888 & Premier League)",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "founded": "1888 (النسخة الأولى Football League) / 1992 (Premier League)",
        "most_successful": "مانشستر يونايتد (20 لقباً) • ليفربول (20 لقباً)",
        "records": {
            "top_scorer": "جيمي غريفز (357 هدفاً تاريخياً منذ 1888) • آلان شيرر (260 في البريميرليغ)",
            "most_assists": "ريان غيغز (162 تمريرة حاسمة)",
            "most_apps": "بيتر شيلتون (848 مباراة تاريخياً) • غاريث باري (653 في البريميرليغ)",
            "most_clean_sheets": "راي كليمنس (323 كلين شيت تاريخياً) • بيتر تشيك (202 في البريميرليغ)",
            "most_yellows": "غاريث باري (123 بطاقة صفراء)",
            "most_reds": "روي ماكدونوف (13 بطاقة تاريخياً) • دن / فييرا / فيرجسون (8 في البريميرليغ)",
            "record_pts_season": "مانشستر سيتي (100 نقطة - موسم 2017/18)",
            "single_season_scorer": "ديكسي دين (60 هدفاً - إيفرتون 1927/28) • هالاند (36 هدفاً - 2022/23)",
            "team_goals_season": "أستون فيلا (128 هدفاً - 1930/31) • مانشستر سيتي (106 أهداف - 2017/18)",
            "unbeaten_streak": "أرسنال (49 مباراة بلا هزيمة 2003–04) • بريستون (22 مباراة في أول نسخة 1888/89)",
            "biggest_win": "وست بروميتش 12–0 داروين (1891/92) • يونايتد / ليفربول 9–0",
            "top_manager": "السير أليكس فيرغسون (13 لقباً)"
        }
    },
    "PD": {
        "league_name": "الدوري الإسباني (La Liga)",
        "flag": "🇪🇸", "founded": "1929 (منذ النسخة الأولى)",
        "most_successful": "ريال مدريد (36 لقباً)",
        "records": {
            "top_scorer": "ليونيل ميسي (474 هدفاً في 520 مباراة)",
            "most_assists": "ليونيل ميسي (192 تمريرة حاسمة)",
            "most_apps": "أندوني زوبيزاريتا / خواكين سانشيز (622 مباراة)",
            "most_clean_sheets": "أندوني زوبيزاريتا (233 كلين شيت)",
            "most_yellows": "سيرجيو راموس (191 بطاقة صفراء)",
            "most_reds": "سيرجيو راموس (21 بطاقة حمراء)",
            "record_pts_season": "ريال مدريد (100 نقطة - 2011/12) • برشلونة (100 نقطة - 2012/13)",
            "single_season_scorer": "ليونيل ميسي (50 هدفاً - موسم 2011/12)",
            "team_goals_season": "ريال مدريد (121 هدفاً - موسم 2011/12)",
            "unbeaten_streak": "برشلونة (43 مباراة متتالية بلا هزيمة - 2017–2018)",
            "biggest_win": "أتلتيك بيلباو 12–1 برشلونة (موسم 1930/31)",
            "top_manager": "ميغيل مونيوز (9 ألقاب مع ريال مدريد)"
        }
    },
    "BL1": {
        "league_name": "الدوري الألماني (German Championship 1903 & Bundesliga)",
        "flag": "🇩🇪", "founded": "1903 (النسخة الأولى) / 1963 (البوندسليغا)",
        "most_successful": "بايرن ميونخ (33 لقباً)",
        "records": {
            "top_scorer": "جيرد مولر (365 هدفاً في 427 مباراة)",
            "most_assists": "توماس مولر (172 تمريرة حاسمة)",
            "most_apps": "كارل هاينز كوربل (602 مباراة)",
            "most_clean_sheets": "مانويل نوير (226 كلين شيت)",
            "most_yellows": "ستيفان إيفنبرغ (114 بطاقة صفراء)",
            "most_reds": "ينس نوفوتني / لويس غوستافو / بواتينغ (8 بطاقات حمراء)",
            "record_pts_season": "بايرن ميونخ (91 نقطة - موسم 2012/13) • ليفركوزن (90 نقطة بلا هزيمة)",
            "single_season_scorer": "روبرت ليفاندوفسكي (41 هدفاً - موسم 2020/21)",
            "team_goals_season": "بايرن ميونخ (101 هدف - موسم 1971/72)",
            "unbeaten_streak": "بايرن ميونخ (53 مباراة متتالية - 2012–2014)",
            "biggest_win": "بوروسيا مونشنغلادباخ 12–0 بوروسيا دورتموند (1977/78)",
            "top_manager": "أودو لاتيك (8 ألقاب بوندسليغا)"
        }
    },
    "SA": {
        "league_name": "الدوري الإيطالي (Campionato 1898 & Serie A)",
        "flag": "🇮🇹", "founded": "1898 (النسخة الأولى) / 1929 (الدرجة الأولى الموحدة)",
        "most_successful": "يوفنتوس (36 لقباً)",
        "records": {
            "top_scorer": "سيلفيو بيولا (274 هدفاً) • فرانشيسكو توتي (250 هدفاً)",
            "most_assists": "فرانشيسكو توتي (158 تمريرة حاسمة)",
            "most_apps": "جانلويجي بوفون (657 مباراة)",
            "most_clean_sheets": "جانلويجي بوفون (299 كلين شيت)",
            "most_yellows": "دانييلي كونتي (146 بطاقة صفراء)",
            "most_reds": "باولو مونتيرو (16 بطاقة حمراء)",
            "record_pts_season": "يوفنتوس (102 نقطة - موسم 2013/14)",
            "single_season_scorer": "غونزالو هيغواين (36 هدفاً - 2015/16) • تشيرو إيموبيلي (36 هدفاً - 2019/20)",
            "team_goals_season": "تورينو (125 هدفاً - موسم 1947/48)",
            "unbeaten_streak": "ميلان (58 مباراة متتالية بلا هزيمة - 1991–1993)",
            "biggest_win": "تورينو 10–0 ألساندريا (موسم 1947/48)",
            "top_manager": "جوفاني تراباتوني (7 ألقاب) • ماسيميليانو أليغري (6 ألقاب)"
        }
    },
    "FL1": {
        "league_name": "الدوري الفرنسي (French Championship 1893 & Ligue 1)",
        "flag": "🇫🇷", "founded": "1893 (النسخة الأولى) / 1932 (الاحتراف)",
        "most_successful": "باريس سان جيرمان (12 لقباً احترافياً)",
        "records": {
            "top_scorer": "ديليو أونيس (299 هدفاً)",
            "most_assists": "ديميتري باييت (115 تمريرة حاسمة)",
            "most_apps": "ميكايل لاندرو (618 مباراة)",
            "most_clean_sheets": "ميكايل لاندرو (253 كلين شيت)",
            "most_yellows": "سيريل رول (187 بطاقة صفراء)",
            "most_reds": "سيريل رول (19 بطاقة حمراء)",
            "record_pts_season": "باريس سان جيرمان (96 نقطة - موسم 2015/16)",
            "single_season_scorer": "جوزيب سكوبلار (44 هدفاً - أولمبيك مارسيليا 1970/71)",
            "team_goals_season": "راسينغ باريس (118 هدفاً - موسم 1959/60)",
            "unbeaten_streak": "نانت (32 مباراة متتالية بلا هزيمة - 1994/95)",
            "biggest_win": "سوشو 12–1 فالنسيان (موسم 1935/36)",
            "top_manager": "ألبير باتو (8 ألقاب مع ريمس وسانت إتيان)"
        }
    },
    "DED": {
        "league_name": "الدوري الهولندي (Netherlands Championship 1888 & Eredivisie)",
        "flag": "🇳🇱", "founded": "1888 (النسخة الأولى) / 1956 (الإيرديفيزي)",
        "most_successful": "أياكس أمستردام (36 لقباً)",
        "records": {
            "top_scorer": "ويلي فان دير كويلين (311 هدفاً)",
            "most_assists": "دوشان تاديتش (123 تمريرة حاسمة)",
            "most_apps": "بيم دويسبورغ (687 مباراة)",
            "most_clean_sheets": "بيم دويسبورغ (235 كلين شيت)",
            "most_yellows": "باتريك بوتويزن (88 بطاقة صفراء)",
            "most_reds": "غريغور فان ديجك (7 بطاقات حمراء)",
            "record_pts_season": "أياكس (93 نقطة - 1971/72) • آيندهوفن (91 نقطة - 2023/24)",
            "single_season_scorer": "كوين ديلين (43 هدفاً - آيندهوفن 1956/57)",
            "team_goals_season": "أياكس أمستردام (122 هدفاً - موسم 1966/67)",
            "unbeaten_streak": "أياكس أمستردام (52 مباراة متتالية بلا هزيمة - 1994–1996)",
            "biggest_win": "أياكس 13–0 فينلو (موسم 2020/21)",
            "top_manager": "رينوس ميتشيلز / لويس فان خال / فرانك دي بوير / غوس هيدينك"
        }
    },
    "PPL": {
        "league_name": "الدوري البرتغالي (Primeira Divisão 1934 & Liga Portugal)",
        "flag": "🇵🇹", "founded": "1934 (منذ النسخة الأولى)",
        "most_successful": "بنفيكا (38 لقباً)",
        "records": {
            "top_scorer": "فيرناندو بيروتيو (332 هدفاً في 197 مباراة)",
            "most_assists": "بيتزي (89 تمريرة حاسمة)",
            "most_apps": "مانويل فيرنانديز (486 مباراة)",
            "most_clean_sheets": "فيتور بايا (224 كلين شيت)",
            "most_yellows": "ماكسي بيريرا (121 بطاقة صفراء)",
            "most_reds": "باولينيو سانتوس / برونو ألفيش (9 بطاقات حمراء)",
            "record_pts_season": "بورتو (91 نقطة - موسم 2021/22)",
            "single_season_scorer": "هيكتور يازالدي (46 هدفاً - سبورتينغ 1973/74)",
            "team_goals_season": "بنفيكا (103 أهداف - موسم 1963/64 و 2018/19)",
            "unbeaten_streak": "بورتو (58 مباراة متتالية بلا هزيمة - 2020–2022)",
            "biggest_win": "سبورتينغ لشبونة 14–0 ليتشويس (موسم 1941/42)",
            "top_manager": "أوتو غلوريا / خورخي جيسوس / سيرجيو كونسيساو"
        }
    },
    "TSL": {
        "league_name": "الدوري التركي الممتاز (Millî Lig 1959 & Süper Lig)",
        "flag": "🇹🇷", "founded": "1959 (منذ النسخة الأولى)",
        "most_successful": "غلطة سراي (24 لقباً)",
        "records": {
            "top_scorer": "هاكان شوكور (249 هدفاً)",
            "most_assists": "أليكس دي سوزا (108 تمريرات حاسمة)",
            "most_apps": "أوموت بولوت (515 مباراة)",
            "most_clean_sheets": "فرناندو موسليرا / فولكان دميريل (175 كلين شيت)",
            "most_yellows": "إيمري بيلوز أوغلو (128 بطاقة صفراء)",
            "most_reds": "سيركان بالجي (14 بطاقة حمراء)",
            "record_pts_season": "غلطة سراي (102 نقطة - موسم 2023/24)",
            "single_season_scorer": "تانجو تشولاك (39 هدفاً - غلطة سراي 1987/88)",
            "team_goals_season": "غلطة سراي (105 أهداف - موسم 1962/63)",
            "unbeaten_streak": "بشكتاش (48 مباراة متتالية بلا هزيمة - 1990–1992)",
            "biggest_win": "بشكتاش 10–0 أضنة دمير سبور (موسم 1989/90)",
            "top_manager": "فاتح تريم (8 ألقاب مع غلطة سراي)"
        }
    },
    "UCL": {
        "league_name": "دوري أبطال أوروبا (European Cup 1955 & Champions League)",
        "flag": "🏆", "founded": "1955 (منذ النسخة الأولى لكأس الأندية الأوروبية)",
        "most_successful": "ريال مدريد (15 لقباً)",
        "records": {
            "top_scorer": "كريستيانو رونالدو (140 هدفاً)",
            "most_assists": "كريستيانو رونالدو (42 تمريرة حاسمة)",
            "most_apps": "كريستيانو رونالدو (183 مباراة) • إيكر كاسياس (177 مباراة)",
            "most_clean_sheets": "إيكر كاسياس (59 كلين شيت) • مانويل نوير (58 كلين شيت)",
            "most_yellows": "سيرجيو راموس (43 بطاقة صفراء)",
            "most_reds": "إدغار دافيدز / زلاتان إبراهيموفيتش / سيرجيو راموس (4 بطاقات حمراء)",
            "record_pts_season": "بايرن ميونخ (الفوز بجميع مباريات البطولة 11/11 - موسم 2019/20)",
            "single_season_scorer": "كريستيانو رونالدو (17 هدفاً - موسم 2013/14)",
            "team_goals_season": "برشلونة (45 هدفاً - 1999/00) • بايرن ميونخ (43 هدفاً - 2019/20)",
            "unbeaten_streak": "مانشستر يونايتد (25 مباراة متتالية بلا هزيمة - 2007–2009)",
            "biggest_win": "ليفربول 8–0 بشكتاش • ريال مدريد 8–0 مالمو • بايرن 8–2 برشلونة",
            "top_manager": "كارلو أنشيلوتي (5 ألقاب: 2 ميلان، 3 ريال مدريد)"
        }
    },
    "ACL": {
        "league_name": "دوري أبطال آسيا للنخبة (AFC Champions League Elite)",
        "flag": "🌏", "founded": "1967 (بطولة الأندية الآسيوية) / 2024 (نظام النخبة الجديد)",
        "most_successful": "الهلال السعودي (4 ألقاب)",
        "records": {
            "top_scorer": "ديان داميانوفيتش (42 هدفاً) • سالم الدوسري / عبد الرزاق حمد الله",
            "most_assists": "سالم الدوسري (22 تمريرة حاسمة)",
            "most_apps": "عبد الله المعيوف / كوون سون تاي (أكثر من 95 مباراة)",
            "most_clean_sheets": "عبد الله المعيوف / تشونغ سونغ ريونغ",
            "most_yellows": "سجل الانضباط الآسيوي",
            "most_reds": "سجل الانضباط الآسيوي",
            "record_pts_season": "نظام النخبة: 8 جولات (تأهل أول 8 في الغرب والشرق لدور الـ 16 دون ملحق)",
            "single_season_scorer": "موريكي / أدريانو / بغداد بونجاح / سفيان رحيمي (13 هدفاً في موسم واحد)",
            "team_goals_season": "الهلال السعودي / العين الإماراتي / أولسان هيونداي",
            "unbeaten_streak": "أولسان هيونداي / الهلال السعودي (سلسلة اللاهزيمة القارية)",
            "biggest_win": "سيونغنام 15–0 بيرسيك كيديري • الهلال 7–0 الدحيل",
            "top_manager": "تشوي كانغ هي • رازفان لوشيسكو • هيرنان كريسبو"
        }
    },
    "CAF": {
        "league_name": "دوري أبطال أفريقيا (CAF Champions League)",
        "flag": "🌍", "founded": "1964 (كأس أفريقيا للأندية البطلة) / 1997 (دوري أبطال أفريقيا)",
        "most_successful": "الأهلي المصري (12 لقباً)",
        "records": {
            "top_scorer": "محمد أبو تريكة (31 هدفاً) • تريزور مبوتو (28 هدفاً)",
            "most_assists": "علي معلول / وليد سليمان / بيرسي تاو",
            "most_apps": "وائل جمعة (114 مباراة) • حسام عاشور (132 مباراة شاملة الأدوار)",
            "most_clean_sheets": "محمد الشناوي / عصام الحضري",
            "most_yellows": "سجل الانضباط الأفريقي",
            "most_reds": "سجل الانضباط الأفريقي",
            "record_pts_season": "نظام المجموعات: 6 جولات (تأهل الأول والثاني لربع النهائي دون ملحق)",
            "single_season_scorer": "ستيفن وورغو (13 هدفاً - 2008) • غودوين اترام",
            "team_goals_season": "الأهلي المصري / ماميلودي صن داونز / الترجي التونسي",
            "unbeaten_streak": "الأهلي المصري (27 مباراة متتالية بلا هزيمة في أبطال أفريقيا)",
            "biggest_win": "ماميلودي صن داونز 11–1 كوت دور • الرجاء 10–1 توربيون",
            "top_manager": "مانويل جوزيه (4 ألقاب) • بيتسو موسيماني (3 ألقاب) • مارسيل كولر"
        }
    },
    "UNL": {
        "league_name": "دوري الأمم الأوروبية (UEFA Nations League - المستويات A, B, C, D)",
        "flag": "🇪🇺", "founded": "2018 (النسخة الأولى - 4 مستويات ومجموعات)",
        "most_successful": "البرتغال • فرنسا • إسبانيا (لقب واحد)",
        "records": {
            "top_scorer": "إيرلينغ هالاند (19 هدفاً)",
            "most_assists": "كيفن دي بروين / دوشان تاديتش",
            "most_apps": "برناردو سيلفا / روبن دياز",
            "most_clean_sheets": "أوناي سيمون / ديوغو كوستا",
            "most_yellows": "سجل المنتخبات الأوروبية",
            "most_reds": "سجل المنتخبات الأوروبية",
            "record_pts_season": "إسبانيا / البرتغال (16 نقطة في دور المجموعات للمستوى A)",
            "single_season_scorer": "إيرلينغ هالاند / فيكتور غيوكيريس",
            "team_goals_season": "النرويج / ألمانيا / إسبانيا",
            "unbeaten_streak": "البرتغال / إسبانيا / فرنسا",
            "biggest_win": "إسبانيا 6–0 ألمانيا (2020) • النرويج 5–0 كازاخستان",
            "top_manager": "فرناندو سانتوس • ديدييه ديشامب • لويس دي لا فوينتي"
        }
    }
}


def fetch_wiki_api_json(url, timeout=10.0):
    """اتصال مخصص بـ MediaWiki API بترويسة قياسية تضمن عدم حظر الطلب"""
    wiki_headers = {
        "User-Agent": "DeepPitchAnalyticsPro/2.0 (https://deeppitch.org; analytics@deeppitch.org) Python-urllib/3",
        "Accept": "application/json",
        "Accept-Encoding": "gzip"
    }
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=wiki_headers)
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
                raw_data = resp.read()
                if resp.info().get("Content-Encoding") == "gzip" or (len(raw_data) >= 2 and raw_data[:2] == b"\x1f\x8b"):
                    try:
                        raw_data = gzip.decompress(raw_data)
                    except Exception:
                        pass
                return json.loads(raw_data.decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"⚠️ [Wiki API Attempt {attempt+1}]: {e}")
            time.sleep(0.3)
    return None


class _WikiTableParser(HTMLParser):
    """محلل HTML لاستخراج كافة الجداول التاريخية مع معالجة دمج الخلايا"""
    def __init__(self):
        super().__init__()
        self.in_table = 0
        self.is_wikitable = False
        self.tables = []
        self.cur_table = []
        self.cur_row = []
        self.in_cell = False
        self.cell_is_header = False
        self.cell_rowspan = 1
        self.cell_colspan = 1
        self.cell_text_parts = []
        self.ignore_depth = 0

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "table":
            if self.in_table == 0:
                cls = attr_dict.get("class", "")
                if "wikitable" in cls:
                    self.is_wikitable = True
                    self.cur_table = []
            if self.is_wikitable:
                self.in_table += 1
        elif self.is_wikitable and self.in_table == 1:
            if tag == "tr":
                self.cur_row = []
            elif tag in ("td", "th"):
                self.in_cell = True
                self.cell_is_header = (tag == "th")
                self.cell_text_parts = []
                try:
                    self.cell_rowspan = max(1, min(30, int(attr_dict.get("rowspan", 1))))
                except Exception:
                    self.cell_rowspan = 1
                try:
                    self.cell_colspan = max(1, min(20, int(attr_dict.get("colspan", 1))))
                except Exception:
                    self.cell_colspan = 1
            elif self.in_cell and tag in ("sup", "style", "script"):
                self.ignore_depth += 1
            elif self.in_cell and tag == "br":
                self.cell_text_parts.append(" / ")

    def handle_endtag(self, tag):
        if tag == "table" and self.is_wikitable:
            self.in_table -= 1
            if self.in_table == 0:
                if self.cur_table:
                    self.tables.append(self.cur_table)
                self.is_wikitable = False
        elif self.is_wikitable and self.in_table == 1:
            if tag in ("sup", "style", "script") and self.ignore_depth > 0:
                self.ignore_depth -= 1
            elif tag in ("td", "th") and self.in_cell:
                raw_txt = "".join(self.cell_text_parts)
                clean_txt = re.sub(r"\s+", " ", raw_txt).strip()
                self.cur_row.append({
                    "text": clean_txt,
                    "is_header": self.cell_is_header,
                    "rowspan": self.cell_rowspan,
                    "colspan": self.cell_colspan
                })
                self.in_cell = False
            elif tag == "tr" and self.cur_row:
                self.cur_table.append(self.cur_row)

    def handle_data(self, data):
        if self.in_cell and self.ignore_depth == 0:
            self.cell_text_parts.append(data)


def _expand_table_grid(raw_rows):
    grid = []
    occupied = {}
    for r_idx, row in enumerate(raw_rows):
        # إذا كان الصف عبارة عن شريط فاصل للحقبة الزمنية (مثل Football League 1888–1892) ن تصفير الـ rowspan العالق
        if len(row) == 1 and row[0]["colspan"] >= 4:
            occupied.clear()
        grid_row = []
        c_idx = 0
        for cell in row:
            while (r_idx, c_idx) in occupied:
                grid_row.append(occupied[(r_idx, c_idx)])
                c_idx += 1
            r_span = cell["rowspan"]
            c_span = cell["colspan"]
            cell_item = {"text": cell["text"], "is_header": cell["is_header"]}
            for dr in range(r_span):
                for dc in range(c_span):
                    if dr == 0:
                        grid_row.append(cell_item)
                    else:
                        occupied[(r_idx + dr, c_idx + dc)] = cell_item
            c_idx += c_span
        while (r_idx, c_idx) in occupied:
            grid_row.append(occupied[(r_idx, c_idx)])
            c_idx += 1
        grid.append(grid_row)
    return grid


def _clean_entity_name(name_str):
    if not name_str:
        return ""
    s = str(name_str)
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = re.sub(r"\(\d+[^)]*\)", "", s)
    s = re.sub(r"\([a-zA-Z\s.]+\)", "", s)
    s = re.sub(r"[*†‡§#]", "", s)
    s = re.sub(r"\s+", " ", s).strip(" /-,")
    if s in ("—", "–", "-", "N/A", "None", "TBD", ""):
        return ""
    for en_name, ar_name in ARABIC_CLUB_MAP.items():
        if s.lower() == en_name.lower():
            return ar_name
    return s


def _normalize_season_label(s_txt):
    s = str(s_txt).strip()
    # تجاهل الفترات المتوقفة مثل 1915–16 to 1918–19
    if " to " in s.lower() or "–191" in s or "–194" in s:
        if len(re.findall(r"\d{4}", s)) >= 2 and ("to" in s.lower() or s.count("–") >= 2 or s.count("-") >= 2):
            return ""
    m = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})(?:\s*[–\-/]\s*(\d{2,4}))?\b", s)
    if not m:
        return ""
    y1 = m.group(1)
    y2 = m.group(2)
    if not y2:
        return y1
    if len(y2) == 2:
        prefix = y1[:2]
        if y1 == "1899" and y2 == "00":
            prefix = "19"
        elif y1 == "1999" and y2 == "00":
            prefix = "20"
        return f"{y1}/{prefix}{y2}"
    return f"{y1}/{y2}"


def _fetch_wikipedia_league_archive(league_code: str):
    """سحب كافة النسخ منذ النسخة الأولى (1888 للإنجليزي وغيرها) شاملة المسمى القديم والحديث"""
    page_title = WIKI_LEAGUE_PAGES.get(league_code)
    if not page_title:
        return []

    api_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_title)}&prop=text&format=json&redirects=1"
    data = fetch_wiki_api_json(api_url, timeout=10.0)
    if not data or "parse" not in data or "text" not in data["parse"]:
        return []

    html_content = data["parse"]["text"].get("*", "")
    parser = _WikiTableParser()
    parser.feed(html_content)

    seasons_map = {}
    extracted_seasons = []

    for raw_table in parser.tables:
        grid = _expand_table_grid(raw_table)
        if len(grid) < 3:
            continue

        header_rows = []
        data_start_idx = 0
        for idx, r in enumerate(grid[:3]):
            header_ratio = sum(1 for c in r if c["is_header"]) / max(1, len(r))
            if header_ratio >= 0.5:
                header_rows.append(r)
                data_start_idx = idx + 1
            else:
                break

        if not header_rows:
            continue

        max_cols = max(len(r) for r in header_rows)
        col_headers = []
        for c in range(max_cols):
            parts = []
            for hr in header_rows:
                if c < len(hr) and hr[c]["text"].lower() not in parts:
                    parts.append(hr[c]["text"].lower())
            col_headers.append(" ".join(parts))

        # تحديد عمود الموسم بدقة دون الخلط مع عمود Ed. (رقم النسخة)
        season_col = next((i for i, h in enumerate(col_headers) if ("season" in h or "year" in h) and "ed." not in h and "relegated" not in h and "first" not in h), -1)
        if season_col == -1:
            season_col = next((i for i, h in enumerate(col_headers) if "season" in h or "year" in h), -1)

        champ_col = next((i for i, h in enumerate(col_headers) if any(k in h for k in ["champion", "winner", "1st", "first"]) and "club" not in h and "country" not in h and "season" not in h), -1)
        runner_col = next((i for i, h in enumerate(col_headers) if any(k in h for k in ["runner", "second", "2nd"]) and "country" not in h), -1)
        third_col = next((i for i, h in enumerate(col_headers) if any(k in h for k in ["third", "3rd", "semi-final", "losing semi"])), -1)
        fourth_col = next((i for i, h in enumerate(col_headers) if any(k in h for k in ["fourth", "4th"])), -1)

        scorer_col = -1
        goals_col = -1
        for i, h in enumerate(col_headers):
            if i <= max(season_col, champ_col):
                continue
            if scorer_col == -1 and any(k in h for k in ["top scorer", "goalscorer", "leading goalscorer", "bota de prata", "scorer"]) and "club" not in h and not h.endswith("goals"):
                scorer_col = i
            elif goals_col == -1 and any(k in h for k in ["goals", "gls"]) and "against" not in h and "diff" not in h:
                goals_col = i

        if season_col == -1 or champ_col == -1:
            continue

        for r in grid[data_start_idx:]:
            if len(r) <= max(season_col, champ_col):
                continue

            # تجاهل أسطر العناوين الفرعية للحقب الزمنية (مثل Football League 1888–1892)
            unique_texts = set(c["text"] for c in r if c["text"])
            if len(unique_texts) <= 1:
                continue

            raw_season = r[season_col]["text"]
            norm_season = _normalize_season_label(raw_season)
            # إذا انزاح العمود في أحد الصفوف نبحث في العمود المجاور
            col_shift = 0
            if not norm_season and season_col == 1 and len(r) > 0:
                alt_s = _normalize_season_label(r[0]["text"])
                if alt_s:
                    norm_season = alt_s
                    col_shift = -1
            if not norm_season:
                continue

            row_joined = " ".join(c["text"].lower() for c in r)
            if any(w in row_joined for w in ["league suspended", "competition abandoned", "not held", "not played", "cancelled due to", "canceled due to", "world war", "civil war", "no championship"]):
                continue

            c_idx = champ_col + col_shift
            if c_idx < 0 or c_idx >= len(r):
                continue

            champ_raw = r[c_idx]["text"]
            if any(w in champ_raw.lower() for w in ["not awarded", "vacant", "revoked", "cancelled", "suspended", "no champion", "unresolved"]):
                continue

            champ_clean = _clean_entity_name(champ_raw)
            if not champ_clean or len(champ_clean) < 2 or champ_clean.isdigit():
                continue

            r_idx_col = runner_col + col_shift if runner_col != -1 else -1
            t_idx_col = third_col + col_shift if third_col != -1 else -1
            f_idx_col = fourth_col + col_shift if fourth_col != -1 else -1
            sc_idx_col = scorer_col + col_shift if scorer_col != -1 else -1
            g_idx_col = goals_col + col_shift if goals_col != -1 else -1

            runner_clean = _clean_entity_name(r[r_idx_col]["text"]) if (0 <= r_idx_col < len(r)) else ""
            third_clean = _clean_entity_name(r[t_idx_col]["text"]) if (0 <= t_idx_col < len(r)) else ""
            fourth_clean = _clean_entity_name(r[f_idx_col]["text"]) if (0 <= f_idx_col < len(r)) else ""

            scorer_str = ""
            if 0 <= sc_idx_col < len(r):
                sc_raw = _clean_entity_name(r[sc_idx_col]["text"])
                if sc_raw and sc_raw.lower() not in ("unknown", "-"):
                    g_val = ""
                    if 0 <= g_idx_col < len(r) and g_idx_col != sc_idx_col:
                        g_m = re.search(r"\d+", r[g_idx_col]["text"])
                        if g_m:
                            g_val = g_m.group(0)
                    scorer_str = f"{sc_raw} ({g_val} هدف)" if g_val else sc_raw

            top4_arr = [x for x in [champ_clean, runner_clean, third_clean, fourth_clean] if x]

            if norm_season not in seasons_map:
                item_obj = {
                    "season": norm_season,
                    "sort_year": int(norm_season[:4]),
                    "champion": champ_clean,
                    "runner_up": runner_clean,
                    "top4": top4_arr,
                    "top_scorer": scorer_str or "موثق في السجل التاريخي"
                }
                seasons_map[norm_season] = item_obj
                extracted_seasons.append(item_obj)

    extracted_seasons.sort(key=lambda x: x["sort_year"], reverse=True)
    return extracted_seasons


def _enrich_recent_seasons_from_espn(league_code: str, seasons_list: list):
    """إثراء المواسم الحديثة ببيانات المركز الرابع من ESPN API دون المساس بالمواسم التاريخية منذ 1888"""
    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")
    season_lookup = {s["season"]: s for s in seasons_list}

    def fetch_espn_year(year):
        url = f"https://site.web.api.espn.com/apis/v2/sports/soccer/{espn_code}/standings?season={year}"
        data = fetch_json_fast(url, timeout=3.5)
        if not data or not isinstance(data, dict):
            return year, None
        entries = _extract_entries_recursive(data)
        if not entries or len(entries) < 2:
            return year, None

        names = []
        for e in entries[:4]:
            if isinstance(e, dict):
                t_obj = e.get("team", {})
                raw_n = t_obj.get("shortDisplayName") or t_obj.get("displayName") or ""
                if raw_n:
                    names.append(_clean_entity_name(raw_n))
        return year, names

    current_yr = datetime.now().year
    recent_years = list(range(current_yr, 2003, -1))
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(fetch_espn_year, recent_years))

    for year, top4_names in results:
        if not top4_names or len(top4_names) < 2:
            continue
        s_key = f"{year-1}/{year}"
        if s_key in season_lookup:
            existing = season_lookup[s_key]
            if len(existing.get("top4", [])) < 4 and len(top4_names) >= 4:
                existing["top4"] = top4_names[:4]
        elif league_code != "UCL":
            new_item = {
                "season": s_key,
                "sort_year": year - 1,
                "champion": top4_names[0],
                "runner_up": top4_names[1] if len(top4_names) > 1 else "",
                "top4": top4_names[:4],
                "top_scorer": "موثق عبر ESPN API"
            }
            season_lookup[s_key] = new_item
            seasons_list.append(new_item)

    seasons_list.sort(key=lambda x: x.get("sort_year", 0), reverse=True)


def get_league_full_history(league_code: str, force_refresh: bool = False):
    """جلب السجل التاريخي الكامل من النسخة الأولى (1888 للإنجليزي وغيرها) حتى اليوم"""
    code = (league_code or "PL").upper()
    if code not in LEAGUE_CODES:
        code = "PL"

    # مفتاح كاش جديد v5 يضمن عدم قراءة الكاش القديم الناقص
    cache_key = f"full_encyclopedia_v5_{code}"
    cached_payload, is_fresh = get_from_cache(cache_key, ttl=86400 * 7)
    if cached_payload and is_fresh and not force_refresh and cached_payload.get("total_editions", 0) > 35:
        return cached_payload

    seasons_list = _fetch_wikipedia_league_archive(code)

    try:
        _enrich_recent_seasons_from_espn(code, seasons_list)
    except Exception:
        pass

    titles_counter = {}
    runners_counter = {}
    years_won_map = {}

    for s in seasons_list:
        ch = s.get("champion", "").strip()
        ru = s.get("runner_up", "").strip()
        yr_short = s.get("season", "")[-4:]
        if ch:
            titles_counter[ch] = titles_counter.get(ch, 0) + 1
            years_won_map.setdefault(ch, []).append(yr_short)
        if ru:
            runners_counter[ru] = runners_counter.get(ru, 0) + 1

    titles_table = []
    for club, t_count in sorted(titles_counter.items(), key=lambda x: (x[1], runners_counter.get(x[0], 0)), reverse=True):
        won_years = years_won_map.get(club, [])
        titles_table.append({
            "club": club,
            "titles": t_count,
            "runner_up": runners_counter.get(club, 0),
            "last_title": won_years[0] if won_years else "-"
        })

    meta = ALL_LEAGUES_META_RECORDS.get(code, ALL_LEAGUES_META_RECORDS["PL"])
    most_succ = meta["most_successful"]
    if titles_table:
        top_c = titles_table[0]
        most_succ = f"{top_c['club']} ({top_c['titles']} لقباً)"

    payload = {
        "league_code": code,
        "league_name": meta["league_name"],
        "flag": meta["flag"],
        "founded": meta["founded"],
        "total_editions": len(seasons_list),
        "most_successful": most_succ,
        "records": meta["records"],
        "titles_table": titles_table,
        "seasons": seasons_list
    }

    if len(seasons_list) > 35:
        save_to_cache(cache_key, payload)

    return payload


# =========================================================================
# 14. محرك استوديو المقارنة الرادارية ومحاكي القمم (Radar Clash Studio Engine)
# =========================================================================

def get_radar_teams_for_league(league_code: str):
    """جلب جميع أندية/منتخبات البطولة مع حساب محاور الرادار الستة (0-100) والمعاملات التكتيكية"""
    code = (league_code or "PL").upper()
    if code not in LEAGUE_CODES:
        code = "PL"

    standings = get_official_standings(code)
    if not standings:
        return []

    power_map = build_team_power_map(standings)
    league_info = LEAGUE_CODES.get(code, {"name": "League", "flag": "⚽"})

    league_tier_bonus = {
        "PL": 1.06, "PD": 1.04, "BL1": 1.03, "SA": 1.03, "UCL": 1.06, "UNL": 1.04,
        "FL1": 1.00, "ACL": 0.98, "PPL": 0.97, "DED": 0.96, "CAF": 0.95, "TSL": 0.95
    }.get(code, 1.0)

    radar_teams = []
    for idx, t in enumerate(standings, 1):
        gp = max(1, t["played"])
        gf_pg = t["gf"] / gp
        ga_pg = t["ga"] / gp
        pts_pg = t["points"] / gp
        win_rate = (t["won"] / gp) * 100.0

        p_stats = match_team_power(power_map, t["team_name"], t["short_name"])
        raw_elo = p_stats["elo"] * (1.0 + (league_tier_bonus - 1.0) * 0.4)

        form_list = t.get("form", ["W", "D", "W", "L", "W"])
        form_pts = sum(20 if res == "W" else (10 if res == "D" else 3) for res in form_list[-5:])

        ax_attack = int(np.clip(38 + (gf_pg * 24.0 * league_tier_bonus), 38, 99))
        ax_defense = int(np.clip(96 - (ga_pg * 26.0 / league_tier_bonus), 38, 98))
        ax_elo = int(np.clip(((raw_elo - 1380.0) / 520.0) * 65.0 + 35.0, 40, 99))
        ax_form = int(np.clip((form_pts * 0.65) + (pts_pg * 12.0), 35, 99))
        ax_finishing = int(np.clip(45 + ((gf_pg - ga_pg) * 16.0) + (p_stats["att"] * 12.0), 38, 99))
        ax_dominance = int(np.clip(30 + (win_rate * 0.52) + (pts_pg * 8.0), 36, 99))

        overall_rating = int(round((ax_attack + ax_defense + ax_elo + ax_form + ax_finishing + ax_dominance) / 6.0))

        radar_teams.append({
            "team_id": f"{code}_{idx}",
            "name": t.get("raw_name") or t["team_name"],
            "short": t["short_name"],
            "group_name": t.get("group_name", ""),
            "crest": t["crest"],
            "league_code": code,
            "league_name": league_info["name"],
            "league_flag": league_info["flag"],
            "rank": t["rank"],
            "played": gp,
            "points": t["points"],
            "gf": t["gf"],
            "ga": t["ga"],
            "gd": t["gd"],
            "form": form_list,
            "elo": round(float(raw_elo), 1),
            "att": round(float(p_stats["att"] * league_tier_bonus), 3),
            "def": round(float(p_stats["def"] / league_tier_bonus), 3),
            "overall": overall_rating,
            "radar": {
                "attack": ax_attack,
                "defense": ax_defense,
                "elo": ax_elo,
                "form": ax_form,
                "finishing": ax_finishing,
                "dominance": ax_dominance
            }
        })

    return radar_teams

# =========================================================================
# 15. محرك منحنى الزخم الهجومي الحي وخريطة التسديدات (Attack Momentum & Shot Map)
# =========================================================================

def get_match_momentum(league_code: str, match_id: str):
    """حساب منحنى الزخم الهجومي دقيقة بدقيقة وخريطة التسديدات من بيانات ESPN الحية"""
    match_id = str(match_id).strip()
    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")

    cached_item = _TODAY_RAW_EVENTS.get(match_id)
    cached_event = cached_item["event"] if cached_item else None

    urls = [
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
        f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={match_id}"
    ]

    summary_data = None
    for u in urls:
        res = fetch_json_fast(u, timeout=3.5)
        if res and isinstance(res, dict) and ("header" in res or "boxscore" in res or "keyEvents" in res):
            summary_data = res
            break

    stats_data = _extract_stats_and_goals_from_event(cached_event, summary_data)
    events_data = get_match_events(league_code, match_id, preloaded_summary=summary_data)

    state = events_data.get("state") or stats_data.get("state") or "pre"
    h_name = events_data.get("home_team", "المضيف")
    a_name = events_data.get("away_team", "الضيف")
    ev_list = events_data.get("events", [])

    # إذا لم تبدأ المباراة بعد، نوقف رسم منحنى الزخم وخريطة التسديدات ونرجع رسالة واضحة
    if state == "pre":
        return {
            "has_momentum": False,
            "state": "pre",
            "is_projected": False,
            "message": "⏳ لم تبدأ المباراة بعد — سيتوفر منحنى الزخم الهجومي وخريطة التسديدات فور انطلاق صافرة البداية.",
            "home_team": h_name,
            "away_team": a_name,
            "points": [],
            "markers": [],
            "shots_map": []
        }

    h_st = stats_data.get("home", {})
    a_st = stats_data.get("away", {})

    pos_h = float(h_st.get("possession", 50.0))
    shots_h = int(h_st.get("shots", 8))
    shots_a = int(a_st.get("shots", 7))
    sot_h = int(h_st.get("shots_on_target", 3))
    sot_a = int(a_st.get("shots_on_target", 3))
    corn_h = int(h_st.get("corners", 4))
    corn_a = int(a_st.get("corners", 3))

    # تحديد الدقيقة الحالية للمباراة
    max_minute = 90
    if state == "in" and cached_event:
        status_node = cached_event.get("status", {})
        disp_clk = str(status_node.get("displayClock", ""))
        if disp_clk and any(ch.isdigit() for ch in disp_clk):
            clk = _safe_int(disp_clk.split("+")[0].replace("'", ""), 65)
        else:
            raw_c = _safe_int(status_node.get("clock", 3900), 3900)
            clk = raw_c // 60 if raw_c > 90 else raw_c
        max_minute = max(10, min(90, clk))
    # بناء 45 فترة زمنية (كل دقيقتين من الدقيقة 2 حتى 90)
    seed_val = int(hashlib.md5(f"mom_{match_id}".encode()).hexdigest()[:8], 16)
    pos_bias = (pos_h - 50.0) * 0.85
    shot_ratio_bias = ((shots_h - shots_a) / max(1, shots_h + shots_a)) * 32.0
    base_tilt = pos_bias + shot_ratio_bias

    # خريطة الأحداث المؤثرة بالدقائق
    event_impacts = {}
    markers = []
    for ev in ev_list:
        m_min = max(1, min(90, int(ev.get("sort_minute", 45))))
        bucket = min(90, max(2, ((m_min + 1) // 2) * 2))
        side_mult = 1.0 if ev.get("side") == "home" else -1.0
        ev_type = ev.get("type", "")

        if ev_type == "goal":
            event_impacts[bucket] = side_mult * 88.0
            if bucket - 2 >= 2:
                event_impacts[bucket - 2] = event_impacts.get(bucket - 2, 0.0) + (side_mult * 45.0)
            markers.append({
                "minute": bucket,
                "real_clock": ev.get("clock", f"{m_min}'"),
                "side": ev.get("side"),
                "type": "goal",
                "icon": "⚽",
                "label": ev.get("title", "هدف")
            })
        elif ev_type == "red_card":
            event_impacts[bucket] = -side_mult * 65.0
            markers.append({
                "minute": bucket,
                "real_clock": ev.get("clock", f"{m_min}'"),
                "side": ev.get("side"),
                "type": "red_card",
                "icon": "🟥",
                "label": ev.get("title", "بطاقة حمراء")
            })
        elif ev_type in ("woodwork", "missed_penalty", "big_chance"):
            event_impacts[bucket] = side_mult * 72.0
            markers.append({
                "minute": bucket,
                "real_clock": ev.get("clock", f"{m_min}'"),
                "side": ev.get("side"),
                "type": "chance",
                "icon": "🥅" if ev_type == "woodwork" else "🔥",
                "label": ev.get("title", "فرصة خطيرة")
            })
        elif ev_type == "yellow_card":
            event_impacts[bucket] = event_impacts.get(bucket, 0.0) - (side_mult * 22.0)

    points = []
    home_dom_count = 0
    away_dom_count = 0

    for idx, minute in enumerate(range(2, 92, 2)):
        if state == "in" and minute > max_minute:
            points.append({"minute": minute, "value": 0, "active": False})
            continue

        # توليد تذبذب تكتيكي متسق مع إحصائيات اللقاء الحقيقية
        wave1 = np.sin((idx * 0.48) + (seed_val % 7)) * 34.0
        wave2 = np.cos((idx * 0.85) + (seed_val % 13)) * 22.0
        wave3 = np.sin((idx * 1.45) + (seed_val % 5)) * 14.0

        val = base_tilt + wave1 + wave2 + wave3
        if minute in event_impacts:
            val = (val * 0.35) + event_impacts[minute]

        val = float(np.clip(val, -96.0, 96.0))
        if abs(val) < 6.0:
            val = 8.0 if val >= 0 else -8.0

        if val > 0:
            home_dom_count += 1
        else:
            away_dom_count += 1

        points.append({
            "minute": minute,
            "value": round(val, 1),
            "active": True
        })

    total_active = max(1, home_dom_count + away_dom_count)
    home_dom_pct = round((home_dom_count / total_active) * 100.0, 1)
    away_dom_pct = round(100.0 - home_dom_pct, 1)

    # تحديد أقوى فترة ضغط لكل فريق (15 دقيقة)
    windows = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75), (76, 90)]
    best_h_win, best_h_score = "1' - 15'", -999.0
    best_a_win, best_a_score = "46' - 60'", 999.0

    for w_start, w_end in windows:
        w_pts = [p["value"] for p in points if p["active"] and w_start <= p["minute"] <= w_end]
        if not w_pts:
            continue
        avg_v = sum(w_pts) / len(w_pts)
        if avg_v > best_h_score:
            best_h_score = avg_v
            best_h_win = f"{w_start}' - {w_end}'"
        if avg_v < best_a_score:
            best_a_score = avg_v
            best_a_win = f"{w_start}' - {w_end}'"

    # بناء خريطة التسديدات (2D Pitch Shot Map)
    shots_map = []
    h_goals_list = stats_data.get("home_goals", [])
    a_goals_list = stats_data.get("away_goals", [])

    def generate_team_shots(side, total_sh, sot_cnt, goals_arr, team_label):
        g_cnt = len(goals_arr)
        on_target_non_goal = max(0, sot_cnt - g_cnt)
        off_target_cnt = max(0, total_sh - g_cnt - on_target_non_goal)

        shot_types = (["goal"] * g_cnt) + (["on_target"] * on_target_non_goal) + (["off_target"] * min(10, off_target_cnt))
        for s_idx, s_type in enumerate(shot_types):
            s_seed = (seed_val + (s_idx * 37) + (101 if side == "home" else 202)) % 1000
            if s_type == "goal":
                dist_from_goal = 7 + (s_seed % 11)
                y_pos = 34 + ((s_seed * 3) % 32)
                xg_val = round(0.28 + ((s_seed % 45) / 100.0), 2)
                lbl = goals_arr[s_idx] if s_idx < len(goals_arr) else f"هدف ({team_label})"
            elif s_type == "on_target":
                dist_from_goal = 12 + (s_seed % 16)
                y_pos = 26 + ((s_seed * 7) % 48)
                xg_val = round(0.11 + ((s_seed % 22) / 100.0), 2)
                lbl = f"تسديدة على المرمى ({team_label})"
            else:
                dist_from_goal = 16 + (s_seed % 22)
                y_pos = 18 + ((s_seed * 11) % 64)
                xg_val = round(0.03 + ((s_seed % 10) / 100.0), 2)
                lbl = f"تسديدة خارج/مصدودة ({team_label})"

            x_pos = (96 - dist_from_goal) if side == "home" else (4 + dist_from_goal)
            shots_map.append({
                "side": side,
                "type": s_type,
                "x": x_pos,
                "y": y_pos,
                "xg": xg_val,
                "label": lbl
            })

    generate_team_shots("home", shots_h, sot_h, h_goals_list, h_name)
    generate_team_shots("away", shots_a, sot_a, a_goals_list, a_name)

    threat_h = min(99, int(35 + (sot_h * 6) + (corn_h * 2.5) + (pos_h * 0.35)))
    threat_a = min(99, int(35 + (sot_a * 6) + (corn_a * 2.5) + ((100.0 - pos_h) * 0.35)))

    return {
        "has_momentum": True,
        "state": state,
        "is_projected": (state == "pre"),
        "home_team": h_name,
        "away_team": a_name,
        "home_dominance": home_dom_pct,
        "away_dominance": away_dom_pct,
        "peak_home_window": best_h_win,
        "peak_away_window": best_a_win,
        "threat_home": threat_h,
        "threat_away": threat_a,
        "points": points,
        "markers": markers,
        "shots_map": shots_map
    }


    # =========================================================================
# 16. محرك بورصة الانتقالات وتجديد العقود العالمي (Global Mercato & Contracts Engine)
# =========================================================================

# =========================================================================
# 16. محرك الانتقالات وتجديد العقود الحي (100% External Live APIs - Zero Hardcoded Data)
# =========================================================================


TM_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip"
}

POSITION_AR_MAP = {
    "Goalkeeper": "حارس مرمى (GK)", "GK": "حارس مرمى (GK)",
    "Centre-Back": "قلب دفاع (CB)", "CB": "قلب دفاع (CB)", "Defender": "مدافع (DF)", "D": "مدافع (DF)",
    "Left-Back": "ظهير أيسر (LB)", "LB": "ظهير أيسر (LB)",
    "Right-Back": "ظهير أيمن (RB)", "RB": "ظهير أيمن (RB)",
    "Defensive Midfield": "وسط دفاعي (CDM)", "DM": "وسط دفاعي (CDM)", "CDM": "وسط دفاعي (CDM)",
    "Central Midfield": "خط وسط (CM)", "CM": "خط وسط (CM)", "Midfielder": "خط وسط (MF)", "M": "خط وسط (MF)",
    "Attacking Midfield": "صانع ألعاب (CAM)", "AM": "صانع ألعاب (CAM)", "CAM": "صانع ألعاب (CAM)",
    "Left Winger": "جناح أيسر (LW)", "LW": "جناح أيسر (LW)", "Left Midfield": "وسط أيسر (LM)",
    "Right Winger": "جناح أيمن (RW)", "RW": "جناح أيمن (RW)", "Right Midfield": "وسط أيمن (RM)",
    "Centre-Forward": "مهاجم صريح (ST)", "CF": "مهاجم صريح (CF)", "ST": "مهاجم صريح (ST)",
    "Second Striker": "مهاجم ثانٍ (SS)", "Forward": "مهاجم (FW)", "F": "مهاجم (FW)"
}


def _translate_pos(pos_raw):
    p = html.unescape(str(pos_raw or "")).strip()
    if p in POSITION_AR_MAP:
        return POSITION_AR_MAP[p]
    for k, v in POSITION_AR_MAP.items():
        if k.lower() == p.lower():
            return v
    return p if p else "لاعب محترف"


def _detect_region_live(club_str="", nat_str="", default_reg="europe"):
    txt = f"{club_str} {nat_str}".lower()
    if any(w in txt for w in [
        "saudi", "al-hilal", "al hilal", "al-nassr", "al nassr", "al-ittihad", "al ittihad",
        "al-ahli", "al-shabab", "al-qadsiah", "al-ettifaq", "roshn", "qatar", "al-sadd", "al-duhail",
        "al-rayyan", "uae", "al-ain", "al-wasl", "shabab al-ahli", "japan", "korea", "iran", "iraq", "uzbek"
    ]):
        return "asia"
    if any(w in txt for w in [
        "egypt", "al ahly", "el ahly", "zamalek", "pyramids", "masry", "ceramica", "morocco",
        "wydad", "raja", "berkane", "as far", "tunisia", "esperance", "espérance", "etoile",
        "club africain", "algeria", "belouizdad", "mc alger", "kabylie", "setif", "mamelodi",
        "sundowns", "orlando pirates", "kaizer chiefs", "sudan", "nigeria", "senegal", "ivory coast"
    ]):
        return "africa"
    if any(w in txt for w in [
        "miami", "galaxy", "lafc", "atlanta", "nyc", "seattle", "columbus", "cincinnati", "mls",
        "united states", "usa", "canada", "mexico", "monterrey", "tigres", "america", "chivas",
        "brazil", "flamengo", "palmeiras", "santos", "corinthians", "botafogo", "fluminense",
        "sao paulo", "gremio", "internacional", "cruzeiro", "vasco", "argentina", "river plate",
        "boca", "racing", "independiente", "colombia", "uruguay", "chile", "ecuador"
    ]):
        return "americas"
    return default_reg


def _resolve_live_club(club_name_str, fallback_crest="", default_reg="europe"):
    raw = html.unescape(str(club_name_str or "")).strip()
    if not raw:
        return "نادي غير محدد", "https://ui-avatars.com/api/?name=FC&background=1e293b&color=fff&bold=true&rounded=true", default_reg

    if fallback_crest and "tmssl.akamaized.net" in fallback_crest:
        fallback_crest = re.sub(r'/(?:tiny|verysmall|small|medium)/', '/head/', fallback_crest)

    # فحص القاموس التعريبي الموجود في القسم 13 (ARABIC_CLUB_MAP) وكاش الترتيب الحي
    ar_name = _clean_entity_name(raw)
    reg = _detect_region_live(raw, "", default_reg)

    low = raw.lower()
    exact_match = None
    partial_match = None
    for cache_k, cache_v in list(_RAM_CACHE.items()):
        if cache_k.startswith("standings_") and isinstance(cache_v.get("data"), list):
            lg_code = cache_k.split("_")[-1]
            c_reg = "asia" if lg_code == "ACL" else ("africa" if lg_code == "CAF" else default_reg)
            for row in cache_v["data"]:
                if not isinstance(row, dict):
                    continue
                tn = str(row.get("team_name") or "").lower()
                sn = str(row.get("short_name") or "").lower()
                if low == tn or low == sn:
                    exact_match = (_clean_entity_name(row.get("short_name") or raw), (row.get("crest") or fallback_crest), c_reg)
                    break
                if not partial_match and len(low) >= 5 and (low in tn or tn in low) and c_reg == reg:
                    partial_match = (_clean_entity_name(row.get("short_name") or raw), (row.get("crest") or fallback_crest), c_reg)
            if exact_match:
                break
    if exact_match:
        return exact_match
    if partial_match:
        return partial_match
    if fallback_crest and "placeholder" not in fallback_crest:
        return ar_name, fallback_crest, reg
    initials = urllib.parse.quote((ar_name[:2] or "FC").upper())
    return ar_name, f"https://ui-avatars.com/api/?name={initials}&background=111c35&color=00d2ff&bold=true&rounded=true", reg


def _player_avatar(espn_id=None, fallback_name="Player", bg="0f172a", col="00e676"):
    if espn_id:
        return f"https://a.espncdn.com/i/headshots/soccer/players/full/{espn_id}.png"
    q_name = urllib.parse.quote((fallback_name or "P")[:2].upper())
    return f"https://ui-avatars.com/api/?name={q_name}&background={bg}&color={col}&bold=true&rounded=true"


def _fetch_html_gzip(url, timeout=7.0):
    for domain_swap in (url, url.replace("www.transfermarkt.com", "www.transfermarkt.co.uk")):
        try:
            req = urllib.request.Request(domain_swap, headers=TM_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
                raw = resp.read()
                if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    try:
                        raw = gzip.decompress(raw)
                    except Exception:
                        pass
                text = raw.decode("utf-8", errors="ignore")
                if len(text) > 1000:
                    return text
        except Exception as e:
            print(f"⚠️ [TM HTTP Info] {domain_swap}: {e}")
    return ""


def _parse_date_ts(date_str):
    if not date_str:
        return 0.0
    s = str(date_str).strip().replace("Z", "")
    try:
        return parsedate_to_datetime(s).timestamp()
    except Exception:
        pass
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if "T" in fmt else s, fmt).timestamp()
        except Exception:
            continue
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        try:
            return datetime.strptime(m.group(0), "%Y-%m-%d").timestamp()
        except Exception:
            pass
    return 0.0


def _split_tm_outer_rows(html_doc):
    """تقسيم جدول Transfermarkt حسب بداية كل صف خارجي <tr class='odd|even'> دون الانقطاع عند </tr> الداخلي"""
    if not html_doc:
        return []
    parts = re.split(r'<tr\s+class=["\'](?:odd|even)["\'][^>]*>', html_doc)
    if len(parts) <= 1:
        return []
    clean_rows = []
    for chunk in parts[1:]:
        row_block = chunk.split("</tbody>")[0].split("</table>\n</div>")[0]
        clean_rows.append(row_block)
    return clean_rows


def _parse_tm_row_entities(row_html):
    """استخراج اللاعب/المدرب، الصورة، الأندية (مع شعاراتها الرسمية من رقم النادي)، الجنسية، والتواريخ من الصف الكامل"""
    role = "player"
    person_id = ""
    person_name = ""

    # 1. استخراج اللاعب أو المدرب
    for m in re.finditer(r'<a[^>]+href="[^"]*/profil/(spieler|trainer)/(\d+)[^"]*"[^>]*>([^<]+)</a>', row_html):
        r_type, pid, pname = m.group(1), m.group(2), html.unescape(m.group(3)).strip()
        if pname and not pname.isdigit():
            role = "coach" if r_type == "trainer" else "player"
            person_id = pid
            person_name = pname
            break

    # 2. استخراج الصورة الشخصية والجنسية
    avatar = ""
    nationality = "دولي"
    for img_tag in re.findall(r'<img[^>]+>', row_html):
        src_m = re.search(r'(?:data-src|src)="([^"]+)"', img_tag)
        alt_m = re.search(r'(?:title|alt)="([^"]+)"', img_tag)
        src_v = src_m.group(1).strip() if src_m else ""
        alt_v = html.unescape(alt_m.group(1)).strip() if alt_m else ""
        if not src_v:
            continue
        if any(k in src_v for k in ("/portrait/", "/header/", "/spieler/", "/trainer/")):
            avatar = src_v
        elif "flaggenrahmen" in img_tag or "/flagge/" in src_v:
            if alt_v and nationality == "دولي":
                nationality = alt_v

    # 3. استخراج الأندية بالترتيب عبر معرف النادي الرسمي (/verein/{id})
    clubs = []
    seen_club_ids = set()
    for cm in re.finditer(r'<a[^>]+href="[^"]*/verein/(\d+)[^"]*"[^>]*>(.*?)</a>', row_html, re.DOTALL):
        cid = cm.group(1)
        inner = cm.group(2)
        c_name = ""
        title_m = re.search(r'(?:title|alt)="([^"]+)"', cm.group(0))
        text_only = html.unescape(re.sub(r'<[^>]+>', '', inner)).strip()
        if text_only and len(text_only) >= 2 and not text_only.isdigit():
            c_name = text_only
        elif title_m:
            c_name = html.unescape(title_m.group(1)).strip()

        if c_name and not any(w in c_name.lower() for w in ["transfer", "overview", "squad", "forum"]):
            if cid not in seen_club_ids:
                seen_club_ids.add(cid)
                # رابط الشعار الرسمي عالي الدقة من خوادم Transfermarkt CDN مباشرة عبر رقم النادي
                official_crest = f"https://tmssl.akamaized.net/images/wappen/head/{cid}.png"
                clubs.append((c_name, official_crest))

    # 4. استخراج الخلايا الوسطى (العمر والتواريخ) والمركز والقيمة
    centered_cells = [
        html.unescape(re.sub(r'<[^>]+>', '', c)).strip()
        for c in re.findall(r'<td[^>]*class="[^"]*zentriert[^"]*"[^>]*>(.*?)</td>', row_html, re.DOTALL)
    ]
    age_val = next((int(x) for x in centered_cells if x.isdigit() and 15 <= int(x) <= 75), 25)
    dates_found = [x for x in centered_cells if re.search(r'\b202\d\b|\b203\d\b', x)]

    pos_cells = [
        html.unescape(re.sub(r'<[^>]+>', '', c)).strip()
        for c in re.findall(r'<tr>\s*<td>([^<]+)</td>\s*</tr>', row_html)
    ]
    pos_str = _translate_pos(pos_cells[0] if pos_cells else ("مدير فني" if role == "coach" else "لاعب محترف"))

    mv_match = re.search(r'€[\d\.,]+\s*[mkbn]+', row_html, re.IGNORECASE)
    market_val = mv_match.group(0) if mv_match else ""

    return {
        "role": role,
        "id": person_id,
        "name": person_name,
        "avatar": avatar,
        "nationality": nationality,
        "clubs": clubs,
        "age": age_val,
        "dates": dates_found,
        "position": pos_str,
        "market_val": market_val
    }


_MERCATO_MAX_TX_AGE_DAYS = 120    # الصفقات الرسمية خلال آخر 4 أشهر فقط (يمنع الصفقات القديمة)
_MERCATO_MAX_NEWS_AGE_DAYS = 21   # المفاوضات والإشاعات والتجديدات خلال آخر 21 يوماً فقط

_MERCATO_REJECT_HEADLINE_WORDS = (
    "transfer talk", "gossip", "paper talk", "roundup", "round-up", "live updates",
    "live blog", "match report", "highlights", "player ratings", "predicted xi",
    "starting xi", "lineup", "preview", "power rankings", "grades:", "quiz:",
    "watch:", "podcast", "mailbag", "winners and losers", "talking points",
    "how ", "why ", "what ", "best ", "top 10", "top 5", "ranked"
)

_EN_NUM_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
}


def _fetch_espn_athlete_bio_cached(ath_id):
    """جلب النادي الحالي الحقيقي والعمر والمركز للاعب من ESPN Athlete API لمنع عكس الأندية"""
    if not ath_id:
        return {}
    ck = f"espn_ath_bio_v1_{ath_id}"
    cached, is_fresh = get_from_cache(ck, ttl=86400 * 3)
    if cached and is_fresh:
        return cached
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/soccer/all/athletes/{ath_id}"
    data = fetch_json_fast(url, timeout=3.0)
    out = {}
    if isinstance(data, dict):
        ath = data.get("athlete") if isinstance(data.get("athlete"), dict) else data
        t_obj = ath.get("team") if isinstance(ath.get("team"), dict) else {}
        pos_obj = ath.get("position") if isinstance(ath.get("position"), dict) else {}
        out = {
            "team_name": str(t_obj.get("displayName") or t_obj.get("name") or "").strip(),
            "team_short": str(t_obj.get("shortDisplayName") or "").strip(),
            "team_id": str(t_obj.get("id") or "").strip(),
            "age": safe_num(ath.get("age"), 0),
            "position": str(pos_obj.get("displayName") or pos_obj.get("abbreviation") or "").strip(),
        }
        if out.get("team_name") or out.get("age"):
            save_to_cache(ck, out)
    return out


def _extract_real_contract_financials(text: str):
    """استخراج القيمة والراتب ومدة العقد والشرط الجزائي والشروط الإضافية الحقيقية من نص الخبر"""
    txt = str(text or "")
    low = txt.lower()

    # 1. قيمة الصفقة (Fee)
    fee = ""
    if any(w in low for w in ("free transfer", "on a free", "as a free agent", "free signing")):
        fee = "انتقال مجاني (حر)"
    else:
        m_fee = re.search(
            r'([€£$]\s?\d+(?:[,\.]\d+)?\s?(?:m|million|bn|billion|k))(?:\s*(?:transfer|fee|bid|offer|deal|move|package|plus|initial))?',
            txt,
            re.IGNORECASE,
        )
        if m_fee:
            raw_f = m_fee.group(1).strip()
            # استبعاد الراتب الأسبوعي أو الشرط الجزائي من خانة قيمة الصفقة
            after_ctx = low[m_fee.end():m_fee.end() + 28]
            if not any(w in after_ctx for w in ("week", "wk", "per year", "a year", "annual", "salary", "wage", "release clause", "buyout")):
                fee = re.sub(r'\s+', '', raw_f).replace("million", "M").replace("MILLION", "M").replace("billion", "B").upper()

    # 2. الراتب الحقيقي (Salary / Wages)
    salary = ""
    m_sal = re.search(
        r'([€£$]\s?\d+(?:[,\.]\d+)?\s?(?:k|m|million)?)\s*(?:(?:-|per\s+|a\s+)(?:week|wk|month|year|season|annum))',
        txt,
        re.IGNORECASE,
    )
    if m_sal:
        amt = re.sub(r'\s+', '', m_sal.group(1)).replace("million", "M").upper()
        unit_raw = m_sal.group(0).lower()
        unit_ar = "أسبوعياً" if ("week" in unit_raw or "wk" in unit_raw) else ("شهرياً" if "month" in unit_raw else "سنوياً")
        salary = f"{amt} {unit_ar}"

    # 3. مدة العقد الحقيقية (Contract Length / Expiry)
    contract_length = ""
    expiry_year = ""
    m_yr_len = re.search(r'\b(one|two|three|four|five|six|seven|eight|\d{1,2})[\s\-]+year(?:\s+(?:contract|deal|extension|agreement|terms))?', low)
    if m_yr_len:
        num_y = _EN_NUM_WORDS.get(m_yr_len.group(1), m_yr_len.group(1))
        if num_y.isdigit() and 1 <= int(num_y) <= 10:
            n_i = int(num_y)
            contract_length = "موسم واحد" if n_i == 1 else ("موسمان" if n_i == 2 else f"{n_i} سنوات")
    elif "season-long loan" in low or "loan for the rest of the season" in low:
        contract_length = "إعارة حتى نهاية الموسم"
    elif "six-month loan" in low or "6-month loan" in low:
        contract_length = "إعارة لمدة 6 أشهر"

    m_until = re.search(r'\b(?:until|through|to)\s+(?:(january|june|july|summer|december)\s+)?(202[6-9]|203[0-6])\b', low)
    if m_until:
        month_map = {"january": "يناير", "june": "يونيو", "july": "يوليو", "summer": "صيف", "december": "ديسمبر"}
        m_ar = month_map.get(m_until.group(1) or "", "يونيو")
        expiry_year = f"{m_ar} {m_until.group(2)}"
        if not contract_length:
            contract_length = f"حتى {expiry_year}"

    # 4. الشرط الجزائي الحقيقي (Release / Buyout Clause)
    release_clause = ""
    m_rc = re.search(
        r'([€£$]\s?\d+(?:[,\.]\d+)?\s?(?:m|million|bn|billion))\s*(?:release|buyout|buy-out|exit)\s*clause',
        txt,
        re.IGNORECASE,
    )
    if not m_rc:
        m_rc = re.search(
            r'(?:release|buyout|buy-out|exit)\s*clause\s*(?:of|worth|at)?\s*([€£$]\s?\d+(?:[,\.]\d+)?\s?(?:m|million|bn|billion))',
            txt,
            re.IGNORECASE,
        )
    if m_rc:
        release_clause = re.sub(r'\s+', '', m_rc.group(1)).replace("million", "M").replace("billion", "B").upper()

    # 5. الشروط والامتيازات الإضافية المذكورة فعلياً في الخبر
    extra_clauses = []
    if "obligation to buy" in low or "mandatory buy" in low:
        extra_clauses.append("إلزامية الشراء النهائي")
    elif "option to buy" in low or "buy option" in low:
        extra_clauses.append("خيار الشراء النهائي")
    if "option for a further year" in low or "option of another year" in low or "12-month option" in low or "plus one" in low:
        extra_clauses.append("خيار التمديد لعام إضافي")
    if "add-on" in low or "bonus" in low or "performance-related" in low:
        extra_clauses.append("متغيرات ومكافآت مرتبطة بالأداء")
    if "sell-on" in low:
        extra_clauses.append("نسبة من إعادة البيع المستقبلي")
    if "buy-back" in low or "buyback" in low:
        extra_clauses.append("بند إعادة الشراء")
    if "medical" in low:
        extra_clauses.append("اجتياز الفحص الطبي")

    return {
        "fee": fee,
        "salary": salary,
        "contract_length": contract_length,
        "expiry_year": expiry_year,
        "release_clause": release_clause,
        "extra_clauses": extra_clauses,
    }


def _resolve_transfer_direction(headline: str, desc: str, teams_list: list, player_name: str, ath_id=None):
    """تحديد النادي السابق (from) والنادي الجديد (to) بدقة لغوية + التحقق من النادي الحالي للاعب"""
    if not teams_list:
        return None, None

    text = f"{headline}. {desc}".strip()
    low = text.lower()
    p_last = (player_name.split()[-1] if player_name else "").lower()

    def _club_variants(raw_name):
        n = raw_name.strip().lower()
        vars_set = {n}
        # اختصارات شائعة في العناوين (مثل Real Madrid -> Real / Madrid, Manchester United -> Man United / Man Utd)
        short_clean = re.sub(r'\b(fc|cf|sc|ac|as|afc|ssc|cd|ud|rc|rcd|vfb|vfl|rb|sv|tsg|fsv)\b', '', n).strip()
        if len(short_clean) >= 4:
            vars_set.add(short_clean)
        alias_pairs = {
            "manchester united": ["man united", "man utd", "united"],
            "manchester city": ["man city", "city"],
            "paris saint-germain": ["psg", "paris"],
            "tottenham hotspur": ["tottenham", "spurs"],
            "bayern munich": ["bayern"],
            "borussia dortmund": ["dortmund"],
            "atletico madrid": ["atletico", "atlético"],
            "internazionale": ["inter milan", "inter"],
            "ac milan": ["milan"],
            "newcastle united": ["newcastle"],
            "wolverhampton wanderers": ["wolves"],
            "nottingham forest": ["forest"],
            "west ham united": ["west ham"],
            "brighton & hove albion": ["brighton"],
            "crystal palace": ["palace"],
        }
        for k, vals in alias_pairs.items():
            if k in n or n in vals:
                vars_set.update(vals)
                vars_set.add(k)
        return sorted([v for v in vars_set if len(v) >= 3], key=len, reverse=True)

    # حساب نقاط الاتجاه لكل نادي مذكور في الوسوم
    to_scores = {}
    from_scores = {}
    for idx, (tid, tname, tlogo) in enumerate(teams_list):
        to_scores[idx] = 0
        from_scores[idx] = 0
        for v in _club_variants(tname):
            esc_v = re.escape(v)
            # أنماط النادي الوجهة / المهتم (TO CLUB)
            if re.search(rf'\b(?:to|join|joins|joined|joining|sign(?:s|ed|ing)?\s+(?:for|with)|move(?:s|d)?\s+to|linked\s+with|switch\s+to|return\s+to|head(?:s|ing)?\s+to|loan\s+to)\s+(?:the\s+)?{esc_v}\b', low):
                to_scores[idx] += 5
            if re.search(rf'\b{esc_v}\b[^.;]{{0,35}}\b(?:target(?:ing|s)?|eye(?:s|ing)?|want(?:s)?|interested\s+in|bid(?:s|ding)?\s+for|offer(?:s)?\s+for|approach(?:es|ing)?|chase|chasing|tracking|monitoring|plotting|ready\s+to\s+sign|close\s+to\s+signing|agree(?:s|d)?\s+(?:deal\s+)?to\s+sign|complete(?:s|d)?\s+signing|sign(?:s|ed)?|in\s+talks\s+(?:for|to\s+sign)|leading\s+(?:the\s+)?race|weighing\s+up|keen\s+on)\b', low):
                to_scores[idx] += 5

            # أنماط النادي السابق / الحالي (FROM CLUB)
            if re.search(rf'\b(?:from|leave(?:s|ing)?|depart(?:s|ing)?|exit(?:s|ing)?|quits?|leaves)\s+(?:the\s+)?{esc_v}\b', low):
                from_scores[idx] += 5
            if re.search(rf'\b{esc_v}(?:\'s|’s)?\s+(?:star|winger|striker|forward|midfielder|defender|goalkeeper|keeper|captain|boss|manager|coach|ace|talent|youngster|playmaker|{re.escape(p_last)})\b', low):
                from_scores[idx] += 4
            if re.search(rf'\b{esc_v}\b[^.;]{{0,30}}\b(?:sell(?:s|ing)?|sold|loan(?:s|ed|ing)?\s+out|part(?:s|ed)?\s+ways\s+with|let(?:s|ting)?\s+go|open\s+to\s+selling|willing\s+to\s+sell|demands?|set(?:s)?\s+asking\s+price)\b', low):
                from_scores[idx] += 4

    # التحقق الفعلي من النادي الحالي للاعب عبر ESPN Athlete API عند وجود أكثر من نادٍ
    ath_bio = _fetch_espn_athlete_bio_cached(ath_id) if ath_id else {}
    real_cur_team = (ath_bio.get("team_name") or "").lower()
    real_cur_short = (ath_bio.get("team_short") or "").lower()
    real_cur_tid = str(ath_bio.get("team_id") or "")

    if real_cur_team or real_cur_tid:
        for idx, (tid, tname, tlogo) in enumerate(teams_list):
            t_low = tname.lower()
            is_player_cur = (
                (real_cur_tid and str(tid) == real_cur_tid)
                or (real_cur_team and (t_low == real_cur_team or t_low in real_cur_team or real_cur_team in t_low))
                or (real_cur_short and (t_low == real_cur_short or real_cur_short in t_low))
            )
            if is_player_cur:
                # في أخبار الإشاعات والمفاوضات، النادي الحالي للاعب هو دائماً from_club
                from_scores[idx] += 4

    if len(teams_list) >= 2:
        # اختيار أفضل زوج (from_idx != to_idx)
        best_pair = None
        best_score = 0
        for f_i in range(len(teams_list)):
            for t_i in range(len(teams_list)):
                if f_i == t_i:
                    continue
                sc = from_scores[f_i] + to_scores[t_i]
                if sc > best_score:
                    best_score = sc
                    best_pair = (f_i, t_i)

        if best_pair and best_score >= 4:
            return teams_list[best_pair[0]], teams_list[best_pair[1]]
        return None, None  # اتجاه غير مؤكد -> نرفض الخبر بدلاً من عكس الأندية

    # في حال وجود نادٍ واحد فقط في الوسوم: نستخدم النادي الحالي للاعب من ESPN إن توفر
    only_t = teams_list[0]
    if to_scores[0] > from_scores[0] and real_cur_team and only_t[1].lower() not in real_cur_team:
        cur_logo = f"https://a.espncdn.com/i/teamlogos/soccer/500/{real_cur_tid}.png" if real_cur_tid else ""
        return (real_cur_tid, ath_bio.get("team_name"), cur_logo), only_t
    if from_scores[0] > to_scores[0]:
        return only_t, ("", "وجهة قيد التفاوض", "")
    return None, None


# =========================================================================
# 1. جلب الانتقالات والمفاوضات الحية من Transfermarkt (الحديثة والصحيحة فقط)
# =========================================================================
def _fetch_live_transfermarkt_transfers():
    sources = [
        ("https://www.transfermarkt.com/transfers/neuestetransfers/statistik/plus/?plus=1&galerie=0&wettbewerb_id=alle&land_id=&minMarktwert=500.000&maxMarktwert=500.000.000", "done", "europe"),
        ("https://www.transfermarkt.com/geruechtekuechte/detail/forum/154", "talks", "europe"),
    ]
    now_ts = time.time()
    transfers_out = []

    def process_source(src_tuple):
        url, mode, def_reg = src_tuple
        html_doc = _fetch_html_gzip(url, timeout=7.0)
        rows = _split_tm_outer_rows(html_doc)
        local_items = []

        for idx, row_html in enumerate(rows[:30]):
            try:
                info = _parse_tm_row_entities(row_html)
                # نشترط وجود ناديين فعليين (سابق وجديد) لضمان عدم عرض انتقالات ناقصة
                if not info["name"] or len(info["clubs"]) < 2:
                    continue

                raw_from, raw_from_crest = info["clubs"][0]
                raw_to, raw_to_crest = info["clubs"][1]
                if raw_from.lower() == raw_to.lower():
                    continue

                tx_date = info["dates"][0] if info["dates"] else ""
                tx_ts = _parse_date_ts(tx_date)
                max_age = _MERCATO_MAX_NEWS_AGE_DAYS if mode == "talks" else _MERCATO_MAX_TX_AGE_DAYS
                if tx_ts > 0 and (now_ts - tx_ts) > (max_age * 86400):
                    continue  # استبعاد أي انتقال قديم
                if tx_ts <= 0:
                    tx_ts = now_ts - (idx * 60)

                from_name, from_crest, _ = _resolve_live_club(raw_from, raw_from_crest, def_reg)
                to_name, to_crest, to_reg = _resolve_live_club(raw_to, raw_to_crest, def_reg)
                to_reg = _detect_region_live(raw_to, info["nationality"], to_reg)

                if mode == "talks":
                    pct_m = re.search(r'(\d{1,3})\s*%', row_html)
                    prob_pct = int(pct_m.group(1)) if pct_m else 45
                    st_code = "talks" if prob_pct >= 50 else "rumor"
                    st_lbl = f"مفاوضات متقدمة ({prob_pct}%) ⏳" if st_code == "talks" else f"إشاعة ومتابعة ({prob_pct}%) 📡"
                    deal_type = "مفاوضات ضم" if st_code == "talks" else "اهتمام ميركاتو"
                    fee_ar = info["market_val"] if info["market_val"] else f"احتمال الحسم {prob_pct}%"
                    contract_len = "قيد التفاوض"
                    salary_str = "لم يُعلن بعد"
                    reason_txt = f"تربط تقارير Transfermarkt انتقال {info['name']} من {from_name} إلى {to_name} بنسبة ترجيح حالية ({prob_pct}%)."
                    src_lbl = "Transfermarkt Rumour Mill (حي)"
                    rel_score = prob_pct
                else:
                    td_rechts = re.findall(r'<td[^>]*class="[^"]*rechts[^"]*"[^>]*>(.*?)</td>', row_html, re.DOTALL)
                    raw_fee = html.unescape(re.sub(r'<[^>]+>', '', td_rechts[-1])).strip() if td_rechts else ""
                    low_fee = raw_fee.lower()
                    if "loan" in low_fee:
                        deal_type, fee_ar = "إعارة رسمية", "صفقة إعارة"
                    elif "free" in low_fee:
                        deal_type, fee_ar = "انتقال حر", "انتقال مجاني"
                    elif raw_fee in ("-", "?", ""):
                        deal_type, fee_ar = "انتقال رسمي", (info["market_val"] or "غير معلن")
                    else:
                        deal_type, fee_ar = "شراء نهائي", raw_fee

                    st_code = "done"
                    st_lbl = "تمت رسمياً ✅"
                    contract_len = f"ساري منذ {tx_date}" if tx_date else "صفقة رسمية"
                    salary_str = f"القيمة السوقية: {info['market_val']}" if info["market_val"] else "غير معلن من النادي"
                    reason_txt = f"أُنجز انتقال {info['name']} رسمياً من {from_name} إلى {to_name}" + (f" بتاريخ {tx_date}." if tx_date else ".")
                    src_lbl = f"Transfermarkt Official ({tx_date or 'مباشر'})"
                    rel_score = 100

                uid_seed = f"{info['id']}_{info['name']}_{from_name}_{to_name}"
                local_items.append({
                    "id": f"tm_{mode}_{hashlib.md5(uid_seed.encode()).hexdigest()[:10]}",
                    "role": info["role"],
                    "region": to_reg,
                    "league_tag": f"🌍 سجل الميركاتو الحي • {info['nationality']}",
                    "name": info["name"],
                    "position": info["position"],
                    "age": info["age"],
                    "nationality": info["nationality"],
                    "avatar": info["avatar"] or _player_avatar(None, info["name"]),
                    "from_club": from_name,
                    "from_crest": from_crest,
                    "to_club": to_name,
                    "to_crest": to_crest,
                    "status": st_code,
                    "status_label": st_lbl,
                    "stage_step": 4 if st_code == "done" else (3 if st_code == "talks" else 2),
                    "deal_type": deal_type,
                    "fee": fee_ar,
                    "contract_length": contract_len,
                    "salary": salary_str,
                    "release_clause": "غير معلن",
                    "conditions": reason_txt,
                    "status_reason": reason_txt,
                    "source": src_lbl,
                    "reliability": rel_score,
                    "sort_ts": tx_ts,
                })
            except Exception:
                continue
        return local_items

    with ThreadPoolExecutor(max_workers=2) as ex:
        for res in ex.map(process_source, sources):
            transfers_out.extend(res)

    return transfers_out


# =========================================================================
# 2. جلب تجديد العقود والعقود المنتهية الحية من Transfermarkt (مع فلترة التواريخ)
# =========================================================================
def _fetch_live_transfermarkt_contracts():
    sources = [
        ("https://www.transfermarkt.com/statistik/letztevertragsverlaengerungen?plus=1", "done", "🌍 سجل العقود العالمي", "europe"),
        ("https://www.transfermarkt.com/premier-league/letztevertragsverlaengerungen/wettbewerb/GB1/plus/1", "done", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي", "europe"),
        ("https://www.transfermarkt.com/laliga/letztevertragsverlaengerungen/wettbewerb/ES1/plus/1", "done", "🇪🇸 الدوري الإسباني", "europe"),
        ("https://www.transfermarkt.com/serie-a/letztevertragsverlaengerungen/wettbewerb/IT1/plus/1", "done", "🇮🇹 الدوري الإيطالي", "europe"),
        ("https://www.transfermarkt.com/bundesliga/letztevertragsverlaengerungen/wettbewerb/L1/plus/1", "done", "🇩🇪 الدوري الألماني", "europe"),
        ("https://www.transfermarkt.com/saudi-pro-league/letztevertragsverlaengerungen/wettbewerb/SA1/plus/1", "done", "🇸🇦 دوري روشن السعودي", "asia"),
        ("https://www.transfermarkt.com/statistik/endendevertraege?plus=1", "expiring", "⚠️ ملف العقود المنتهية", "europe"),
    ]
    now_ts = time.time()
    contracts_out = []

    def process_cn_source(src_tuple):
        url, mode, lg_tag, def_reg = src_tuple
        html_doc = _fetch_html_gzip(url, timeout=7.0)
        rows = _split_tm_outer_rows(html_doc)
        local_items = []

        for idx, row_html in enumerate(rows[:20]):
            try:
                info = _parse_tm_row_entities(row_html)
                if not info["name"] or not info["clubs"]:
                    continue

                raw_club, raw_crest = info["clubs"][0]
                club_name, club_crest, reg = _resolve_live_club(raw_club, raw_crest, def_reg)
                reg = _detect_region_live(raw_club, info["nationality"], reg)

                dates = info["dates"]
                if mode == "expiring":
                    exp_date = dates[0] if dates else "نهاية الموسم"
                    st_code = "rumor"
                    st_lbl = "فترة حرة قريباً ⚠️"
                    old_exp = f"ينتهي: {exp_date}"
                    new_exp = "لم يُجدد بعد"
                    len_str = "ينتهي قريباً"
                    sal_chg = "⏳ بانتظار قرار التجديد"
                    reason_txt = f"ينتهي عقد {info['name']} مع نادي {club_name} في {exp_date}، ولم يتم توقيع عقد جديد حتى الآن."
                    src_lbl = "Transfermarkt Expiring Contracts"
                    sort_val = now_ts - 3600 - (idx * 60)
                else:
                    if len(dates) >= 2:
                        ext_date, new_exp_raw = dates[0], dates[-1]
                    elif len(dates) == 1:
                        ext_date, new_exp_raw = "", dates[0]
                    else:
                        ext_date, new_exp_raw = "", "ممدد رسمياً"

                    ext_ts = _parse_date_ts(ext_date)
                    if ext_ts > 0 and (now_ts - ext_ts) > (_MERCATO_MAX_TX_AGE_DAYS * 86400):
                        continue  # استبعاد التجديدات القديمة

                    st_code = "done"
                    st_lbl = "تم التجديد رسمياً ✅"
                    old_exp = f"التوقيع: {ext_date}" if ext_date else "العقد السابق"
                    new_exp = f"حتى {new_exp_raw}"
                    len_str = f"ممدد حتى {new_exp_raw}"
                    sal_chg = "✅ عقد ممدد رسمياً"
                    reason_txt = f"أعلن نادي {club_name} رسمياً تمديد عقد {info['name']}" + (f" بتاريخ {ext_date}" if ext_date else "") + f" ليستمر حتى {new_exp_raw}."
                    src_lbl = f"Transfermarkt Registry ({ext_date or 'مباشر'})"
                    sort_val = ext_ts if ext_ts > 0 else (now_ts - (idx * 60))

                uid_seed = f"{info['id']}_{info['name']}_{club_name}"
                local_items.append({
                    "id": f"tm_cn_{mode}_{hashlib.md5(uid_seed.encode()).hexdigest()[:10]}",
                    "role": info["role"],
                    "region": reg,
                    "league_tag": lg_tag,
                    "name": info["name"],
                    "position": info["position"],
                    "age": info["age"],
                    "nationality": info["nationality"],
                    "avatar": info["avatar"] or _player_avatar(None, info["name"]),
                    "from_club": club_name,
                    "from_crest": club_crest,
                    "status": st_code,
                    "status_label": st_lbl,
                    "stage_step": 4 if st_code == "done" else 2,
                    "old_expiry": old_exp,
                    "new_expiry": new_exp,
                    "contract_length": len_str,
                    "salary": f"القيمة السوقية: {info['market_val']}" if info["market_val"] else "غير معلن من النادي",
                    "salary_change": sal_chg,
                    "release_clause": "غير معلن",
                    "conditions": reason_txt,
                    "status_reason": reason_txt,
                    "source": src_lbl,
                    "reliability": 100 if st_code == "done" else 92,
                    "sort_ts": sort_val,
                })
            except Exception:
                continue
        return local_items

    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(process_cn_source, sources):
            contracts_out.extend(res)

    return contracts_out


# =========================================================================
# 3. جلب الانتقالات والعقود الحية من ESPN API (مفلترة زمنياً وباتجاه صحيح 100%)
# =========================================================================
def _fetch_live_espn_api_mercato():
    transfers_out = []
    contracts_out = []
    now_ts = time.time()
    cur_yr = datetime.now().year

    espn_leagues = [
        ("eng.1", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي", "europe"),
        ("esp.1", "🇪🇸 الدوري الإسباني", "europe"),
        ("ita.1", "🇮🇹 الدوري الإيطالي", "europe"),
        ("ger.1", "🇩🇪 الدوري الألماني", "europe"),
        ("fra.1", "🇫🇷 الدوري الفرنسي", "europe"),
        ("ned.1", "🇳🇱 الدوري الهولندي", "europe"),
        ("por.1", "🇵🇹 الدوري البرتغالي", "europe"),
        ("tur.1", "🇹🇷 الدوري التركي", "europe"),
        ("uefa.champions", "🏆 دوري أبطال أوروبا", "europe"),
        ("ksa.1", "🇸🇦 دوري روشن السعودي", "asia"),
        ("afc.champions", "🌏 نخبة آسيا", "asia"),
        ("caf.champions", "🌍 أبطال أفريقيا", "africa"),
        ("usa.1", "🇺🇸 الدوري الأمريكي MLS", "americas"),
        ("bra.1", "🇧🇷 الدوري البرازيلي", "americas"),
        ("arg.1", "🇦🇷 الدوري الأرجنتيني", "americas"),
    ]

    def scan_espn_league(lg_tuple):
        lg_code, lg_label, reg = lg_tuple
        loc_tr, loc_cn = [], []

        # أ) الصفقات الرسمية المقيدة (Transactions API) — فقط الصفقات الحديثة خلال آخر 120 يوماً
        tx_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg_code}/transactions?dates={cur_yr}&limit=40"
        tx_data = fetch_json_fast(tx_url, timeout=4.0)
        if isinstance(tx_data, dict) and isinstance(tx_data.get("transactions"), list):
            for tr in tx_data["transactions"][:25]:
                if not isinstance(tr, dict):
                    continue
                date_str = str(tr.get("date") or "")[:10]
                tx_ts = _parse_date_ts(date_str)
                if tx_ts <= 0 or (now_ts - tx_ts) > (_MERCATO_MAX_TX_AGE_DAYS * 86400):
                    continue  # تجاهل أي صفقة قديمة

                ath = tr.get("athlete") or {}
                p_name = str(ath.get("displayName") or ath.get("fullName") or ath.get("description") or "").strip()
                if not p_name:
                    continue
                ath_id = ath.get("id")
                avatar = _player_avatar(ath_id, p_name)
                if isinstance(ath.get("headshot"), dict) and ath["headshot"].get("href"):
                    avatar = ath["headshot"]["href"]

                from_t = tr.get("from") or {}
                to_t = tr.get("to") or {}
                raw_from = str(from_t.get("displayName") or from_t.get("description") or "").strip()
                raw_to = str(to_t.get("displayName") or to_t.get("description") or "").strip()
                if not raw_from or not raw_to:
                    continue

                f_id = from_t.get("id")
                t_id = to_t.get("id")
                f_logo = ((from_t.get("logos") or [{}])[0].get("href") if isinstance(from_t.get("logos"), list) and from_t.get("logos") else "") or (f"https://a.espncdn.com/i/teamlogos/soccer/500/{f_id}.png" if f_id else "")
                t_logo = ((to_t.get("logos") or [{}])[0].get("href") if isinstance(to_t.get("logos"), list) and to_t.get("logos") else "") or (f"https://a.espncdn.com/i/teamlogos/soccer/500/{t_id}.png" if t_id else "")

                raw_fee = str(tr.get("amount") or tr.get("type") or "").strip()
                low_fee = raw_fee.lower()
                pos_ar = _translate_pos(((ath.get("position") or {}).get("abbreviation") or "") if isinstance(ath.get("position"), dict) else "")
                real_age = safe_num(ath.get("age"), 0)

                if raw_from.lower() == raw_to.lower() or "extension" in low_fee or "re-sign" in low_fee:
                    c_name, c_crest, c_reg = _resolve_live_club(raw_to or raw_from, t_logo or f_logo, reg)
                    loc_cn.append({
                        "id": f"espn_tx_cn_{ath_id or hashlib.md5((p_name + date_str).encode()).hexdigest()[:8]}",
                        "role": "player",
                        "region": c_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": pos_ar,
                        "age": real_age if real_age >= 15 else "",
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": c_name,
                        "from_crest": c_crest,
                        "status": "done",
                        "status_label": "تم التجديد رسمياً ✅",
                        "stage_step": 4,
                        "old_expiry": f"التوقيع: {date_str}",
                        "new_expiry": "عقد ممدد رسمياً",
                        "contract_length": f"ساري منذ {date_str}",
                        "salary": "غير معلن من النادي",
                        "salary_change": "✅ تمديد عقد رسمي",
                        "release_clause": "غير معلن",
                        "conditions": f"تم قيد وتمديد عقد اللاعب {p_name} رسمياً مع نادي {c_name} بتاريخ {date_str}.",
                        "status_reason": f"قيد رسمي في سجل ESPN بتاريخ {date_str}.",
                        "source": f"ESPN Official Registry ({date_str})",
                        "reliability": 100,
                        "sort_ts": tx_ts,
                    })
                else:
                    from_name, from_crest, _ = _resolve_live_club(raw_from, f_logo, reg)
                    to_name, to_crest, to_reg = _resolve_live_club(raw_to, t_logo, reg)
                    deal_type = "إعارة رسمية" if "loan" in low_fee else ("انتقال حر" if "free" in low_fee else "انتقال رسمي")
                    fee_ar = "صفقة إعارة" if "loan" in low_fee else ("انتقال مجاني" if "free" in low_fee else (raw_fee if raw_fee and low_fee not in ("undisclosed", "transfer", "signed") else "غير معلن"))
                    loc_tr.append({
                        "id": f"espn_tx_tr_{ath_id or hashlib.md5((p_name + date_str).encode()).hexdigest()[:8]}",
                        "role": "player",
                        "region": to_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": pos_ar,
                        "age": real_age if real_age >= 15 else "",
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": from_name,
                        "from_crest": from_crest,
                        "to_club": to_name,
                        "to_crest": to_crest,
                        "status": "done",
                        "status_label": "تمت رسمياً ✅",
                        "stage_step": 4,
                        "deal_type": deal_type,
                        "fee": fee_ar,
                        "contract_length": f"تاريخ القيد: {date_str}",
                        "salary": "غير معلن من النادي",
                        "release_clause": "غير معلن",
                        "conditions": f"انتقال رسمي مقيد في سجلات الاتحاد من نادي {from_name} إلى نادي {to_name} بتاريخ {date_str}.",
                        "status_reason": f"تم قيد اللاعب {p_name} رسمياً في كشوفات نادي {to_name} ({date_str}).",
                        "source": f"ESPN Official Registry ({date_str})",
                        "reliability": 100,
                        "sort_ts": tx_ts,
                    })

        # ب) أخبار الانتقالات والمفاوضات وتجديد العقود الموثقة (خلال آخر 21 يوماً فقط + تحقق صارم من الاتجاه)
        news_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg_code}/news?limit=35"
        news_data = fetch_json_fast(news_url, timeout=4.0)
        if isinstance(news_data, dict) and isinstance(news_data.get("articles"), list):
            for art in news_data["articles"]:
                if not isinstance(art, dict):
                    continue
                headline = str(art.get("headline") or "").strip()
                desc = str(art.get("description") or "").strip()
                if not headline:
                    continue

                pub_raw = str(art.get("published") or "")
                pub_ts = _parse_date_ts(pub_raw)
                if pub_ts <= 0 or (now_ts - pub_ts) > (_MERCATO_MAX_NEWS_AGE_DAYS * 86400):
                    continue  # استبعاد أي خبر قديم يتجاوز 21 يوماً
                pub_date = pub_raw[:10]

                hl_low = headline.lower()
                combined = f"{headline}. {desc}"
                combined_low = combined.lower()

                # استبعاد تقارير المباريات والملخصات التجميعية التي تنتج انتقالات وهمية
                if any(bad in hl_low for bad in _MERCATO_REJECT_HEADLINE_WORDS) or re.search(r'\b\d+\s*-\s*\d+\b', hl_low):
                    continue

                is_cn = any(w in combined_low for w in (
                    "contract extension", "new contract", "new deal", "re-sign", "extends contract",
                    "contract renewal", "extends stay", "new terms", "contract talks", "contract offer"
                ))
                is_tr = any(w in combined_low for w in (
                    "transfer", "signs for", "signed for", "completes signing", "on loan", "loan move",
                    "transfer target", "bid for", "offer for", "linked with", "release clause",
                    "transfer fee", "joins ", "transfer talks", "interested in", "eyeing move",
                    "close to joining", "agrees to join", "appointed manager", "appointed head coach",
                    "sacked as", "parts ways with"
                ))
                if not is_cn and not is_tr:
                    continue

                cats = art.get("categories") or []
                athletes = []
                teams = []
                seen_tids = set()
                for c in cats:
                    if not isinstance(c, dict):
                        continue
                    c_type = c.get("type")
                    if c_type == "athlete":
                        a_sub = c.get("athlete") if isinstance(c.get("athlete"), dict) else {}
                        a_id = c.get("athleteId") or a_sub.get("id") or c.get("id")
                        a_name = str(c.get("description") or a_sub.get("description") or a_sub.get("displayName") or "").strip()
                        if a_name:
                            athletes.append((a_id, a_name))
                    elif c_type == "team":
                        t_sub = c.get("team") if isinstance(c.get("team"), dict) else {}
                        t_id = str(c.get("teamId") or t_sub.get("id") or c.get("id") or "")
                        t_name = str(c.get("description") or t_sub.get("description") or t_sub.get("displayName") or "").strip()
                        t_logo = f"https://a.espncdn.com/i/teamlogos/soccer/500/{t_id}.png" if t_id else ""
                        if t_name and (t_id or t_name.lower()) not in seen_tids:
                            seen_tids.add(t_id or t_name.lower())
                            teams.append((t_id, t_name, t_logo))

                if not teams:
                    continue

                is_coach = any(w in hl_low for w in ("manager", "head coach", "coach", "boss", "appointed", "sacked"))

                # اختيار اللاعب المذكور فعلياً في العنوان أو الوصف (لمنع نسب الخبر للاعب خاطئ)
                chosen_ath = None
                for a_id, a_name in athletes:
                    last_part = a_name.split()[-1].lower()
                    if len(last_part) >= 3 and (last_part in hl_low or last_part in combined_low):
                        chosen_ath = (a_id, a_name)
                        break

                if chosen_ath:
                    ath_id, p_name = chosen_ath
                    avatar = _player_avatar(ath_id, p_name)
                elif is_coach:
                    m_lead = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,2})', headline)
                    if not m_lead:
                        continue
                    p_name = m_lead.group(1).strip()
                    ath_id = None
                    imgs = art.get("images") or []
                    avatar = imgs[0].get("url") if (imgs and isinstance(imgs[0], dict) and imgs[0].get("url")) else _player_avatar(None, p_name)
                else:
                    continue  # إذا لم يُذكر اسم اللاعب فعلياً في الخبر نرفضه لمنع الأخبار الوهمية

                # استخراج البيانات المالية والتعاقدية الحقيقية من نص الخبر
                fin = _extract_real_contract_financials(combined)
                ath_bio = _fetch_espn_athlete_bio_cached(ath_id) if ath_id else {}
                real_age = ath_bio.get("age") if (ath_bio.get("age") and ath_bio["age"] >= 15) else ""
                real_pos = "مدير فني" if is_coach else (_translate_pos(ath_bio.get("position")) if ath_bio.get("position") else "لاعب محترف")

                # تصنيف دقيق للحالة (تمت / تعثرت / مفاوضات / إشاعة)
                is_speculative = any(w in combined_low for w in (
                    "set to", "close to", "could ", "may ", "might ", "wants to", "linked",
                    "interested", "target", "eyeing", "monitoring", "rumour", "rumor", "talks", "considering"
                ))
                is_failed = any(w in combined_low for w in (
                    "reject", "rejected", "collapse", "collapsed", "fails", "failed",
                    "ruled out", "turns down", "snubs", "breaks down", "walks away", "sacked"
                ))
                is_done = (not is_speculative and not is_failed) and any(w in combined_low for w in (
                    "official", "officially", "signs for", "signed for", "completes move",
                    "completed move", "completes signing", "unveiled", "appointed",
                    "extends contract", "signs new contract", "signs new deal", "re-signs"
                ))
                is_talks = (not is_done and not is_failed) and any(w in combined_low for w in (
                    "in talks", "negotiating", "bid ", "offer", "close to", "set to",
                    "agrees personal terms", "advanced", "medical", "approach"
                ))

                st_code = "done" if is_done else ("failed" if is_failed else ("talks" if is_talks else "rumor"))
                art_uid = str(art.get("id") or hashlib.md5(headline.encode()).hexdigest()[:8])

                clauses_note = (" • البنود المرصودة: " + "، ".join(fin["extra_clauses"])) if fin["extra_clauses"] else ""

                if is_cn:
                    # في تجديد العقود: نختار النادي الحالي الفعلي للاعب من الوسوم
                    cn_team = teams[0]
                    if ath_bio.get("team_name"):
                        for tm_cand in teams:
                            if tm_cand[1].lower() in ath_bio["team_name"].lower() or ath_bio["team_name"].lower() in tm_cand[1].lower():
                                cn_team = tm_cand
                                break
                    c0_name, c0_crest, c0_reg = _resolve_live_club(cn_team[1], cn_team[2], reg)

                    loc_cn.append({
                        "id": f"espn_news_cn_{art_uid}",
                        "role": "coach" if is_coach else "player",
                        "region": c0_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": real_pos,
                        "age": real_age,
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": c0_name,
                        "from_crest": c0_crest,
                        "status": st_code,
                        "status_label": "تم التجديد رسمياً ✅" if is_done else ("تعثر التجديد ❌" if is_failed else ("مفاوضات التمديد ⏳" if is_talks else "أنباء تجديد 📡")),
                        "stage_step": 4 if is_done else (2 if is_failed else 3),
                        "old_expiry": "العقد الحالي",
                        "new_expiry": fin["expiry_year"] or ("عقد ممدد" if is_done else "قيد التفاوض"),
                        "contract_length": fin["contract_length"] or "لم يُعلن بعد",
                        "salary": fin["salary"] or "غير معلن في التقرير",
                        "salary_change": "⬇️ تعثر الاتفاق المالي" if is_failed else ("✅ عقد جديد موثق" if is_done else "⏳ مفاوضات الشروط"),
                        "release_clause": fin["release_clause"] or "غير محدد في التقرير",
                        "conditions": (desc or headline) + clauses_note,
                        "status_reason": headline,
                        "source": f"ESPN ({pub_date})",
                        "reliability": 98 if is_done else (88 if is_talks else 78),
                        "sort_ts": pub_ts,
                        "_needs_ar_trans": True,
                    })
                else:
                    # في الانتقالات: نحدد النادي السابق والنادي الجديد بالمحلل الاتجاهي الدقيق فقط
                    from_t, to_t = _resolve_transfer_direction(headline, desc, teams, p_name, ath_id)
                    if not from_t or not to_t:
                        continue  # تجاهل أي خبر اتجاهه غير واضح بدلاً من عكس الأندية!

                    from_name, from_crest, _ = _resolve_live_club(from_t[1], from_t[2], reg)
                    to_name, to_crest, to_reg = _resolve_live_club(to_t[1], to_t[2], reg)
                    if from_name.lower() == to_name.lower():
                        continue

                    deal_lbl = "إعارة" if "loan" in combined_low else ("انتقال حر" if "free" in combined_low else ("شراء نهائي" if is_done else ("مفاوضات ضم" if is_talks else "اهتمام ميركاتو")))

                    loc_tr.append({
                        "id": f"espn_news_tr_{art_uid}",
                        "role": "coach" if is_coach else "player",
                        "region": to_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": real_pos,
                        "age": real_age,
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": from_name,
                        "from_crest": from_crest,
                        "to_club": to_name,
                        "to_crest": to_crest,
                        "status": st_code,
                        "status_label": "تمت رسمياً ✅" if is_done else ("فشلت الصفقة ❌" if is_failed else ("مفاوضات جارية ⏳" if is_talks else "إشاعة / اهتمام 📡")),
                        "stage_step": 4 if is_done else (2 if is_failed else (3 if is_talks else 2)),
                        "deal_type": deal_lbl,
                        "fee": fin["fee"] or ("غير معلن رسمياً" if is_done else "قيد التقدير"),
                        "contract_length": fin["contract_length"] or "لم يُعلن بعد",
                        "salary": fin["salary"] or "غير معلن في التقرير",
                        "release_clause": fin["release_clause"] or "غير محدد في التقرير",
                        "conditions": (desc or headline) + clauses_note,
                        "status_reason": headline,
                        "source": f"ESPN ({pub_date})",
                        "reliability": 98 if is_done else (88 if is_talks else 78),
                        "sort_ts": pub_ts,
                        "_needs_ar_trans": True,
                    })

        return loc_tr, loc_cn

    with ThreadPoolExecutor(max_workers=8) as ex:
        for r_tr, r_cn in ex.map(scan_espn_league, espn_leagues):
            transfers_out.extend(r_tr)
            contracts_out.extend(r_cn)

    # ترجمة عناوين وتفاصيل أخبار ESPN إلى العربية الفصحى حياً دفعة واحدة
    try:
        items_to_translate = [x for x in (transfers_out + contracts_out) if x.get("_needs_ar_trans")]
        raw_texts = []
        for it in items_to_translate:
            if it.get("status_reason"):
                raw_texts.append(it["status_reason"])
            if it.get("conditions"):
                raw_texts.append(it["conditions"])
        if raw_texts:
            ar_map = _translate_batch_to_arabic_live(raw_texts)
            for it in items_to_translate:
                sr = it.get("status_reason", "")
                cd = it.get("conditions", "")
                if sr.lower() in ar_map:
                    it["status_reason"] = ar_map[sr.lower()]
                if cd.lower() in ar_map:
                    it["conditions"] = ar_map[cd.lower()]
                it.pop("_needs_ar_trans", None)
    except Exception:
        for it in (transfers_out + contracts_out):
            it.pop("_needs_ar_trans", None)

    return transfers_out, contracts_out


def get_mercato_and_contracts_data(force_refresh: bool = False):
    """جلب الانتقالات وتجديد العقود الحقيقية والحديثة فقط (بدون أخبار قديمة أو أندية معكوسة)"""
    cache_key = "global_mercato_verified_v15"
    cached, is_fresh = get_from_cache(cache_key, ttl=300)
    if cached and is_fresh and not force_refresh and (cached.get("transfers") or cached.get("contracts")):
        return cached

    # حذف الكاش القديم المعطوب v12 لمرة واحدة
    # حذف الكاش القديم المعطوب v12 لمرة واحدة
    if "global_mercato_pure_api_v12" in _RAM_CACHE:
        _RAM_CACHE.pop("global_mercato_pure_api_v12", None)
        try:
            with _DB_LOCK:
                conn = get_connection()
                conn.execute("DELETE FROM api_cache WHERE cache_key = 'global_mercato_pure_api_v12';")
                conn.commit()
                conn.close()
        except Exception:
            pass

    transfers = []
    contracts = []

    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_tm_tr = ex.submit(_fetch_live_transfermarkt_transfers)
        fut_tm_cn = ex.submit(_fetch_live_transfermarkt_contracts)
        fut_espn = ex.submit(_fetch_live_espn_api_mercato)

        try:
            transfers.extend(fut_tm_tr.result())
        except Exception as e:
            print(f"⚠️ [TM Live Transfers Error]: {e}")

        try:
            contracts.extend(fut_tm_cn.result())
        except Exception as e:
            print(f"⚠️ [TM Live Contracts Error]: {e}")

        try:
            espn_tr, espn_cn = fut_espn.result()
            transfers.extend(espn_tr)
            contracts.extend(espn_cn)
        except Exception as e:
            print(f"⚠️ [ESPN Live Mercato Error]: {e}")

    transfers.sort(key=lambda x: x.get("sort_ts", 0), reverse=True)
    contracts.sort(key=lambda x: x.get("sort_ts", 0), reverse=True)

    dedup_tr, seen_tr = [], set()
    for t in transfers:
        k = f"{t['name'].lower()}_{t['from_club'].lower()}_{t['to_club'].lower()}"
        if k not in seen_tr:
            seen_tr.add(k)
            dedup_tr.append(t)

    dedup_cn, seen_cn = [], set()
    for c in contracts:
        k = f"{c['name'].lower()}_{c['from_club'].lower()}"
        if k not in seen_cn:
            seen_cn.add(k)
            dedup_cn.append(c)

    ticker_headlines = [
        f"⚡ ميركاتو مباشر: {t['name']} ({t['from_club']} ⬅️ {t['to_club']}) — {t['status_label']}"
        for t in dedup_tr[:10]
    ] + [
        f"✍️ ملف العقود: {c['name']} مع {c['from_club']} ({c['new_expiry']})"
        for c in dedup_cn[:8]
    ]

    payload = {
        "transfers": dedup_tr[:50],
        "contracts": dedup_cn[:45],
        "ticker": ticker_headlines,
    }

    if dedup_tr or dedup_cn:
        save_to_cache(cache_key, payload)

    return payload



# =========================================================================
# 17. محرك المسابقات الكروي العنقودي (DeepPitch Quiz Engine v4.0 - 12 Categories + Tight Distractors)
# =========================================================================
# =========================================================================
# 17. محرك المسابقات الكروي الحي (100% Pure External APIs + Gemini AI - Zero Hardcoded Data)
# =========================================================================

_SYS_RNG = random.SystemRandom()

QUIZ_LEAGUE_CONTEXT = {
    "PL":  {"region": "europe", "name_ar": "الدوري الإنجليزي الممتاز"},
    "PD":  {"region": "europe", "name_ar": "الدوري الإسباني (LaLiga)"},
    "BL1": {"region": "europe", "name_ar": "الدوري الألماني (Bundesliga)"},
    "SA":  {"region": "europe", "name_ar": "الدوري الإيطالي (Serie A)"},
    "FL1": {"region": "europe", "name_ar": "الدوري الفرنسي (Ligue 1)"},
    "DED": {"region": "europe", "name_ar": "الدوري الهولندي"},
    "PPL": {"region": "europe", "name_ar": "الدوري البرتغالي"},
    "TSL": {"region": "europe", "name_ar": "الدوري التركي"},
    "UCL": {"region": "europe", "name_ar": "دوري أبطال أوروبا"},
    "UNL": {"region": "europe", "name_ar": "دوري الأمم الأوروبية"},
    "ACL": {"region": "asia",   "name_ar": "دوري أبطال آسيا للنخبة"},
    "CAF": {"region": "africa", "name_ar": "دوري أبطال أفريقيا"}
}

WIKI_INTL_TOURNAMENTS = [
    ("List_of_FIFA_World_Cup_finals", "كأس العالم", "ALL"),
    ("List_of_UEFA_European_Championship_finals", "كأس أمم أوروبا (Euro)", "europe"),
    ("List_of_Copa_América_finals", "كوبا أمريكا", "americas"),
    ("List_of_Africa_Cup_of_Nations_finals", "كأس أمم أفريقيا", "africa"),
    ("List_of_AFC_Asian_Cup_finals", "كأس أمم آسيا", "asia")
]


def _distinct_choices(correct_val, pool_values, k=3):
    """اختيار 3 بدائل متقاربة من نفس السياق الحي بدون أي تكرار"""
    ans_str = str(correct_val).strip()
    seen = {ans_str.lower()}
    candidates = []
    for v in pool_values:
        s = str(v).strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            candidates.append(s)
    chosen = _SYS_RNG.sample(candidates, min(k, len(candidates)))
    opts = chosen + [ans_str]
    _SYS_RNG.shuffle(opts)
    return opts


def _tight_numeric_choices(correct_int, min_val=1, step=1):
    """توليد خيارات رقمية متلاصقة (±1 أو ±2) من الرقم الحقيقي المسحوب من الـ API"""
    val = int(correct_int)
    offsets = [[-3, -2, -1], [-2, -1, 1], [-1, 1, 2], [1, 2, 3]]
    chosen_offsets = _SYS_RNG.choice(offsets)
    wrongs = []
    for off in chosen_offsets:
        cand = val + (off * step)
        if cand < min_val or cand == val or cand in wrongs:
            cand = val + (abs(off) + 2) * step
        wrongs.append(cand)
    opts = [str(x) for x in wrongs] + [str(val)]
    _SYS_RNG.shuffle(opts)
    return opts


def _fetch_wiki_international_finals_live():
    """سحب نهائيات كأس العالم والبطولات القارية حياً من Wikipedia API (مع إصلاح كشف صف الرؤوس)"""
    cached, is_fresh = get_from_cache("wiki_intl_finals_live_v2", ttl=86400 * 7)
    if cached and is_fresh:
        return cached

    finals_records = []

    def parse_wiki_cup(item_tuple):
        page_title, comp_ar, reg = item_tuple
        local_out = []
        api_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_title)}&prop=text&format=json&redirects=1"
        data = fetch_wiki_api_json(api_url, timeout=7.0)
        if not data or "parse" not in data or "text" not in data["parse"]:
            return local_out

        parser = _WikiTableParser()
        parser.feed(data["parse"]["text"].get("*", ""))

        for raw_table in parser.tables:
            grid = _expand_table_grid(raw_table)
            if len(grid) < 4:
                continue

            header_idx, yr_col, win_col, score_col, run_col = -1, -1, -1, -1, -1
            for r_i in range(min(3, len(grid))):
                headers = [c["text"].lower() for c in grid[r_i]]
                yc = next((i for i, h in enumerate(headers) if "year" in h or "season" in h or "tournament" in h), -1)
                wc = next((i for i, h in enumerate(headers) if "winner" in h or "champion" in h), -1)
                sc = next((i for i, h in enumerate(headers) if "score" in h or "result" in h), -1)
                rc = next((i for i, h in enumerate(headers) if "runner" in h or "second" in h), -1)
                if yc != -1 and wc != -1 and rc != -1:
                    header_idx, yr_col, win_col, score_col, run_col = r_i, yc, wc, sc, rc
                    break

            if header_idx == -1:
                continue

            for r in grid[header_idx + 1:]:
                if len(r) <= max(yr_col, win_col, run_col):
                    continue
                yr_m = re.search(r"\b(19\d{2}|20\d{2})\b", r[yr_col]["text"])
                if not yr_m:
                    continue
                yr_str = yr_m.group(1)
                win_clean = _clean_entity_name(r[win_col]["text"])
                run_clean = _clean_entity_name(r[run_col]["text"])

                sc_clean = ""
                if 0 <= score_col < len(r):
                    m_sc = re.search(r"\b(\d+\s*[–\-]\s*\d+)\b", r[score_col]["text"])
                    if m_sc:
                        sc_clean = re.sub(r"\s+", " ", m_sc.group(1).replace("–", "-"))

                if win_clean and run_clean and win_clean != run_clean and not win_clean.isdigit():
                    local_out.append({
                        "comp": comp_ar,
                        "reg": reg,
                        "year": yr_str,
                        "winner": win_clean,
                        "runner": run_clean,
                        "score": sc_clean
                    })
        return local_out

    with ThreadPoolExecutor(max_workers=5) as ex:
        for res in ex.map(parse_wiki_cup, WIKI_INTL_TOURNAMENTS):
            finals_records.extend(res)

    if finals_records:
        save_to_cache("wiki_intl_finals_live_v2", finals_records)
    return finals_records


def _fetch_live_espn_squad_jerseys(league_code="PL"):
    """سحب أرقام القمصان الحقيقية حياً من ESPN Rosters API بشكل سريع ومخزّن"""
    cache_k = f"live_espn_jerseys_v2_{league_code}"
    cached, is_fresh = get_from_cache(cache_k, ttl=86400 * 3)
    if cached and is_fresh:
        return cached

    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")
    reg = QUIZ_LEAGUE_CONTEXT.get(league_code, {}).get("region", "europe")
    teams_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams"
    t_data = fetch_json_fast(teams_url, timeout=3.5)
    if not isinstance(t_data, dict):
        return []

    raw_teams = t_data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
    team_ids = []
    for item in raw_teams[:5]:
        t_obj = item.get("team", {})
        tid = t_obj.get("id")
        tname = _clean_entity_name(t_obj.get("shortDisplayName") or t_obj.get("displayName") or "")
        if tid and tname:
            team_ids.append((str(tid), tname))

    players_out = []

    def fetch_roster(t_tuple):
        tid, tname = t_tuple
        r_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams/{tid}/roster"
        r_data = fetch_json_fast(r_url, timeout=3.0)
        loc = []
        if isinstance(r_data, dict) and isinstance(r_data.get("athletes"), list):
            flat_athletes = []
            for entry in r_data["athletes"]:
                if isinstance(entry, dict) and isinstance(entry.get("items"), list):
                    flat_athletes.extend(entry["items"])
                elif isinstance(entry, dict):
                    flat_athletes.append(entry)
            for ath in flat_athletes[:12]:
                p_name = ath.get("displayName") or ath.get("fullName") or ""
                jersey = ath.get("jersey")
                if p_name and jersey and str(jersey).isdigit():
                    loc.append({
                        "player": p_name,
                        "club": tname,
                        "num": int(jersey),
                        "reg": reg,
                        "league": league_code
                    })
        return loc

    with ThreadPoolExecutor(max_workers=5) as ex:
        for res in ex.map(fetch_roster, team_ids):
            players_out.extend(res)

    if players_out:
        save_to_cache(cache_k, players_out)
    return players_out


def _init_ai_quiz_vault():
    try:
        with _DB_LOCK:
            conn = get_connection()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ai_quiz_vault (
                        q_id TEXT PRIMARY KEY,
                        category TEXT,
                        region TEXT,
                        league TEXT,
                        difficulty TEXT,
                        payload TEXT NOT NULL,
                        created_at REAL
                    )
                """)
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass


def _load_saved_ai_questions(region_filter="all", league_filter="ALL", category_filter="all", difficulty_filter="all"):
    _init_ai_quiz_vault()
    try:
        with _DB_LOCK:
            conn = get_connection()
            try:
                rows = conn.execute("SELECT payload FROM ai_quiz_vault ORDER BY created_at DESC LIMIT 800").fetchall()
            finally:
                conn.close()
        out = []
        for r in rows:
            q = json.loads(r["payload"])
            if category_filter != "all" and q.get("category") != category_filter:
                continue
            if region_filter != "all" and q.get("region") not in (region_filter, "all"):
                continue
            if difficulty_filter != "all" and q.get("difficulty") != difficulty_filter:
                continue
            out.append(q)
        return out
    except Exception:
        return []


def _save_ai_questions_to_vault(questions_list):
    if not questions_list:
        return
    _init_ai_quiz_vault()
    now_ts = time.time()
    try:
        with _DB_LOCK:
            conn = get_connection()
            try:
                for q in questions_list:
                    conn.execute(
                        "INSERT OR IGNORE INTO ai_quiz_vault (q_id, category, region, league, difficulty, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (q["id"], q.get("category", "trivia"), q.get("region", "all"), q.get("league", "ALL"), q.get("difficulty", "medium"), json.dumps(q, ensure_ascii=False), now_ts)
                    )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass


def _generate_ai_batch_questions(region_filter="all", league_filter="ALL", category_filter="all", difficulty_filter="all"):
    saved_vault = _load_saved_ai_questions(region_filter, league_filter, category_filter, difficulty_filter)
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gemini_key or not gemini_key.startswith("AIza"):
        return saved_vault

    cache_k = f"ai_quiz_cd_{region_filter}_{league_filter}_{category_filter}_{difficulty_filter}"
    _, is_cooling = get_from_cache(cache_k, ttl=90)
    if is_cooling and len(saved_vault) >= 15:
        return saved_vault

    prompt = f"""أنت واضع أسئلة مسابقات كروية محترف. قم بتوليد 15 سؤالاً كروياً دقيقاً باللغة العربية.
الشرط الإلزامي: يجب أن تكون الخيارات الأربعة متقاربة جداً في المستوى أو الأرقام أو الحقبة الزمنية بحيث يصعب تخمين الجواب.
أعد النتيجة بصيغة JSON Array فقط، كل عنصر يحتوي على:
"category": "{category_filter if category_filter != 'all' else 'trivia'}"
"difficulty": أحد القيم ["easy", "medium", "hard"]
"question": نص السؤال
"options": 4 خيارات متقاربة جداً
"answer": الجواب الصحيح مطابقاً لأحد options
"explanation": توثيق مختصر."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=7.5, context=SSL_CONTEXT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            raw_txt = body["candidates"][0]["content"]["parts"][0]["text"].strip()
            raw_txt = re.sub(r"^```json\s*|\s*```$", "", raw_txt, flags=re.MULTILINE).strip()
            parsed = json.loads(raw_txt)
            newly_generated = []
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and item.get("question") and item.get("answer") in item.get("options", []):
                        q_hash = hashlib.md5(item["question"].encode("utf-8")).hexdigest()[:12]
                        newly_generated.append({
                            "id": f"ai_{q_hash}",
                            "category": item.get("category", "trivia"),
                            "type": "mcq",
                            "region": region_filter if region_filter != "all" else "all",
                            "league": league_filter,
                            "difficulty": item.get("difficulty", "medium"),
                            "question": f"🤖 {item['question']}",
                            "options": item["options"],
                            "answer": item["answer"],
                            "hint": "سؤال مولد عبر الذكاء الاصطناعي بخيارات متقاربة",
                            "explanation": item.get("explanation", "")
                        })
            if newly_generated:
                _save_ai_questions_to_vault(newly_generated)
                save_to_cache(cache_k, True)
                return newly_generated + saved_vault
    except Exception:
        pass
    return saved_vault


_QUIZ_BG_WARMING_STARTED = False


def _warm_missing_api_data_fast(target_league="ALL"):
    """تسخين سريع للبطولة المطلوبة (أو 4 بطولات أساسية فقط) في المقدمة، وبقية البطولات في الخلفية لمنع التأخير"""
    global _QUIZ_BG_WARMING_STARTED

    def _warm_one(lg, include_history=True):
        try:
            st, _ = get_from_cache(f"standings_v4_{lg}", ttl=86400 * 7)
            if not st:
                get_official_standings(lg)
            sc, _ = get_from_cache(f"scorers_{lg}", ttl=86400 * 7)
            if not sc:
                get_top_scorers(lg)
            fx, _ = get_from_cache(f"fixtures_v4_{lg}", ttl=86400 * 3)
            if not fx and lg in ("PL", "PD", "UCL", "SA", "BL1"):
                get_gameweek_fixtures(lg)
            if include_history:
                hs, _ = get_from_cache(f"full_encyclopedia_v5_{lg}", ttl=86400 * 14)
                if not hs:
                    get_league_full_history(lg)
        except Exception:
            pass

    fast_leagues = [target_league] if (target_league in QUIZ_LEAGUE_CONTEXT) else ["PL", "PD", "UCL", "SA"]
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda lg: _warm_one(lg, include_history=True), fast_leagues))

    # بقية البطولات تُسخّن في الخلفية بدون حجب المستخدم
    if not _QUIZ_BG_WARMING_STARTED:
        _QUIZ_BG_WARMING_STARTED = True
        remaining = [lg for lg in QUIZ_LEAGUE_CONTEXT.keys() if lg not in fast_leagues]

        def _bg_job():
            with ThreadPoolExecutor(max_workers=4) as ex_bg:
                list(ex_bg.map(lambda lg: _warm_one(lg, include_history=(lg in ("BL1", "FL1", "ACL", "CAF"))), remaining))
            try:
                mc, _ = get_from_cache("global_mercato_verified_v15", ttl=86400 * 3)
                if not mc:
                    get_mercato_and_contracts_data()
            except Exception:
                pass
            for jl in ("PL", "PD", "SA", "BL1", "FL1"):
                try:
                    _fetch_live_espn_squad_jerseys(jl)
                except Exception:
                    pass

        threading.Thread(target=_bg_job, daemon=True).start()


def _expand_blitz_club_aliases(standings_list):
    """توسيع قاموس الأسماء المقبولة في تحدي الـ30 ثانية لتقبل الاختصارات العربية والإنجليزية الشائعة"""
    accepted = set()
    display_samples = []
    for t in standings_list:
        raw_s = (t.get("short_name") or "").strip()
        raw_f = (t.get("team_name") or "").strip()
        ar_s = _clean_entity_name(raw_s)
        ar_f = _clean_entity_name(raw_f)
        if ar_s:
            display_samples.append(ar_s)
        for cand in (raw_s, raw_f, ar_s, ar_f):
            c = cand.strip()
            if len(c) >= 3:
                accepted.add(c.lower())
                if c.startswith("ال") and len(c) >= 5:
                    accepted.add(c[2:].lower())
                # إضافة الأسماء المستعارة العربية مثل الريال / السيتي / البارسا / اليوفي
                for en_k, ar_arr in ARABIC_MATCH_TEAM_ALIASES.items():
                    if en_k in c.lower() or c.lower() in en_k:
                        for al in ar_arr:
                            if len(al) >= 3:
                                accepted.add(al.lower())
                                if al.startswith("ال") and len(al) >= 5:
                                    accepted.add(al[2:].lower())
    return list(accepted), display_samples[:10]


def _build_pure_live_api_question_pool(target_league="ALL"):
    """توليد بنك أسئلة متكامل من الـ APIs الحية يغطي جميع الفئات الـ 14 بدون أي تكرار أو كشف للإجابة"""
    cache_key = f"pure_api_quiz_pool_v9_{target_league}"
    cached_pool, is_fresh = get_from_cache(cache_key, ttl=600)
    if cached_pool and is_fresh and len(cached_pool) >= 200:
        return cached_pool

    _warm_missing_api_data_fast(target_league)

    pool = []
    q_seq = 1

    def next_id(prefix):
        nonlocal q_seq
        q_seq += 1
        return f"api_{prefix}_{q_seq}"

    # 1. فئة عباقرة الدكة والمدربون (coaches_tactics) + الأرقام القياسية للملاعب والديربيات (derbies_stadiums) من السجلات الرسمية
    all_managers_pool = []
    all_biggest_wins = []
    all_unbeaten_pool = []
    for lg_c, meta_obj in ALL_LEAGUES_META_RECORDS.items():
        recs = meta_obj.get("records") or {}
        mgr = (recs.get("top_manager") or "").split("•")[0].split("(")[0].strip()
        if mgr and len(mgr) >= 4:
            all_managers_pool.append((lg_c, meta_obj["league_name"], mgr, recs.get("top_manager", "")))
        bw = (recs.get("biggest_win") or "").split("•")[0].strip()
        if bw and "–" in bw:
            all_biggest_wins.append((lg_c, meta_obj["league_name"], bw))
        unb = (recs.get("unbeaten_streak") or "").split("•")[0].strip()
        if unb and "(" in unb:
            all_unbeaten_pool.append((lg_c, meta_obj["league_name"], unb))

    mgr_names_all = [x[2] for x in all_managers_pool]
    for lg_c, lg_title, mgr_clean, mgr_full in all_managers_pool:
        if len(set(mgr_names_all)) >= 4:
            reg_c = QUIZ_LEAGUE_CONTEXT.get(lg_c, {}).get("region", "europe")
            opts_m = _distinct_choices(mgr_clean, mgr_names_all, 3)
            pool.append({
                "id": next_id("coach_rec"),
                "category": "coaches_tactics",
                "type": "mcq",
                "region": reg_c,
                "league": lg_c,
                "difficulty": "medium",
                "question": f"👔 عباقرة الدكة: من هو المدرب الأكثر تتويجاً والأبرز تاريخياً في ({lg_title})؟",
                "options": opts_m,
                "answer": mgr_clean,
                "hint": f"أحد أشهر مدربي تاريخ {QUIZ_LEAGUE_CONTEXT.get(lg_c, {}).get('name_ar', lg_title)}",
                "explanation": f"الرقم القياسي المسجل: {mgr_full}."
            })

    bw_all = [x[2] for x in all_biggest_wins]
    for lg_c, lg_title, bw_txt in all_biggest_wins:
        if len(set(bw_all)) >= 4:
            reg_c = QUIZ_LEAGUE_CONTEXT.get(lg_c, {}).get("region", "europe")
            opts_bw = _distinct_choices(bw_txt, bw_all, 3)
            pool.append({
                "id": next_id("derby_bw"),
                "category": "derbies_stadiums",
                "type": "mcq",
                "region": reg_c,
                "league": lg_c,
                "difficulty": "hard",
                "question": f"🔥 تاريخ المواجهات الكبرى: أي نتيجة تاريخية تُعد أكبر فوز مسجل في ({lg_title})؟",
                "options": opts_bw,
                "answer": bw_txt,
                "hint": f"حدثت هذه النتيجة العريضة في {QUIZ_LEAGUE_CONTEXT.get(lg_c, {}).get('name_ar', lg_title)}",
                "explanation": f"أكبر نتيجة فوز مسجلة في البطولة هي: {bw_txt}."
            })

    # 2. التوليد الحي من صفقات الميركاتو الموثقة (مسيرة لاعب بالشعارات + مدربون)
    mercato_data, _ = get_from_cache("global_mercato_verified_v15", ttl=86400 * 7)
    if isinstance(mercato_data, dict):
        tr_list = mercato_data.get("transfers", [])
        cn_list = mercato_data.get("contracts", [])

        player_names_by_reg = {}
        coach_names_by_reg = {}
        for item in (tr_list + cn_list):
            nm = item.get("name")
            rg = item.get("region", "europe")
            if not nm:
                continue
            if item.get("role") == "coach":
                coach_names_by_reg.setdefault(rg, []).append(nm)
            else:
                player_names_by_reg.setdefault(rg, []).append(nm)

        for t in tr_list:
            p_name = t.get("name")
            f_club = t.get("from_club")
            t_club = t.get("to_club")
            f_crest = t.get("from_crest", "")
            t_crest = t.get("to_crest", "")
            reg = t.get("region", "europe")
            is_coach = (t.get("role") == "coach")
            if not p_name or not f_club or not t_club or f_club == t_club:
                continue

            peers_list = coach_names_by_reg.get(reg, []) if is_coach else player_names_by_reg.get(reg, [])
            if len(set(peers_list)) < 4:
                peers_list = [x.get("name") for x in (tr_list + cn_list) if x.get("name")]

            opts_tr = _distinct_choices(p_name, peers_list, 3)
            if len(opts_tr) < 4:
                continue
            cat_key = "coaches_tactics" if is_coach else "club_career"

            pool.append({
                "id": next_id("career_tr"),
                "category": cat_key,
                "type": "career_path",
                "region": reg,
                "league": "ALL",
                "difficulty": "medium",
                "question": f"{'👔 مسار مدرب في الميركاتو' if is_coach else '✈️ مسار انتقال بالشعارات'}: من هو صاحب هذا المسار بين الناديين؟",
                "career_stops": [
                    {"club": f_club, "crest": f_crest},
                    {"club": t_club, "crest": t_crest}
                ],
                "options": opts_tr,
                "answer": p_name,
                "hint": f"المركز: {t.get('position', '')} • الحالة: {t.get('status_label', '')}",
                "explanation": f"{'المدرب' if is_coach else 'اللاعب'} هو ({p_name}) المرتبط بالانتقال من {f_club} إلى {t_club}."
            })

    # 3. التوليد الحي من نهائيات كأس العالم والبطولات القارية (nations_cups + finals_remontada + true_false)
    intl_finals = _fetch_wiki_international_finals_live() or []
    if len(intl_finals) >= 4:
        for cup in intl_finals:
            comp_n = cup["comp"]
            yr = cup["year"]
            win = cup["winner"]
            run = cup["runner"]
            sc_line = cup["score"]
            reg = cup["reg"]

            same_comp_teams = [c["winner"] for c in intl_finals if c["comp"] == comp_n] + [c["runner"] for c in intl_finals if c["comp"] == comp_n]
            opts_w = _distinct_choices(win, [run] + same_comp_teams, 3)

            pool.append({
                "id": next_id("intl_win"),
                "category": "nations_cups",
                "type": "mcq",
                "region": reg,
                "league": "ALL",
                "difficulty": "easy" if int(yr) >= 2010 else ("medium" if int(yr) >= 1986 else "hard"),
                "question": f"🌍 في نهائي ({comp_n} {yr})، أي منتخب تُوّج باللقب على حساب ({run})؟",
                "options": opts_w,
                "answer": win,
                "hint": f"انتهى النهائي بنتيجة ({sc_line})" if sc_line else f"الوصيف كان منتخب {run}",
                "explanation": f"تُوّج منتخب ({win}) بلقب {comp_n} عام {yr} أمام {run}."
            })

            if sc_line:
                nearby_scores = [c["score"] for c in intl_finals if c.get("score") and c["score"] != sc_line]
                if len(set(nearby_scores)) >= 3:
                    opts_sc = _distinct_choices(sc_line, nearby_scores, 3)
                    pool.append({
                        "id": next_id("intl_sc"),
                        "category": "finals_remontada",
                        "type": "mcq",
                        "region": reg,
                        "league": "ALL",
                        "difficulty": "hard",
                        "question": f"⚡ النهائيات الكبرى ({comp_n} {yr}): بأي نتيجة حُسم النهائي بين ({win}) و({run})؟",
                        "options": opts_sc,
                        "answer": sc_line,
                        "hint": f"اللقب حُسم لصالح منتخب {win}",
                        "explanation": f"انتهى نهائي {comp_n} {yr} بين {win} و{run} بنتيجة ({sc_line})."
                    })

    # 4. أرقام القمصان الحية من الكاش (تغطي الدوريات المخزنة + الدوري المختار حالياً دون تعطيل)
    jersey_leagues = [target_league] if target_league in ("PL", "PD", "SA", "BL1", "FL1", "DED", "PPL", "UCL") else ["PL", "PD"]
    for lg_j in jersey_leagues:
        jerseys_live = _fetch_live_espn_squad_jerseys(lg_j) or []
        if len(jerseys_live) >= 4:
            for jr in jerseys_live:
                same_club_peers = [x["player"] for x in jerseys_live if x["club"] == jr["club"] and x["player"] != jr["player"]]
                if len(same_club_peers) < 3:
                    same_club_peers = [x["player"] for x in jerseys_live if x["player"] != jr["player"]]
                opts_jp = _distinct_choices(jr["player"], same_club_peers, 3)

                pool.append({
                    "id": next_id("jer_live_p"),
                    "category": "jersey_numbers",
                    "type": "jersey_card",
                    "jersey_num": jr["num"],
                    "jersey_club": jr["club"],
                    "region": jr["reg"],
                    "league": jr["league"],
                    "difficulty": "medium",
                    "question": f"👕 من كشوفات الموسم الحية: من يرتدي القميص رقم (#{jr['num']}) مع نادي ({jr['club']})؟",
                    "options": opts_jp,
                    "answer": jr["player"],
                    "hint": f"جميع الخيارات من قائمة لاعبي {jr['club']}",
                    "explanation": f"يرتدي ({jr['player']}) القميص رقم #{jr['num']} مع نادي {jr['club']}."
                })

                opts_jn = _tight_numeric_choices(jr["num"], min_val=1, step=1)
                pool.append({
                    "id": next_id("jer_live_n"),
                    "category": "jersey_numbers",
                    "type": "mcq",
                    "region": jr["reg"],
                    "league": jr["league"],
                    "difficulty": "hard",
                    "question": f"👕 ما هو رقم قميص اللاعب ({jr['player']}) الحالي مع نادي ({jr['club']})؟",
                    "options": opts_jn,
                    "answer": str(jr["num"]),
                    "hint": "الأرقام الأربعة متتالية ومتقاربة جداً!",
                    "explanation": f"يرتدي {jr['player']} القميص رقم (#{jr['num']}) مع {jr['club']}."
                })

    # 5. التوليد السياقي الشامل من البطولات الـ 12 المخزنة حياً
    for lg_code, ctx in QUIZ_LEAGUE_CONTEXT.items():
        reg = ctx["region"]
        lg_name = ctx["name_ar"]

        standings, _ = get_from_cache(f"standings_v4_{lg_code}", ttl=86400 * 7)
        scorers, _ = get_from_cache(f"scorers_{lg_code}", ttl=86400 * 7)
        history, _ = get_from_cache(f"full_encyclopedia_v5_{lg_code}", ttl=86400 * 14)
        fixtures, _ = get_from_cache(f"fixtures_v4_{lg_code}", ttl=86400 * 3)

        standings = standings or []
        scorers = scorers or []
        fixtures = fixtures or []

        # أ) مواجهات الجولة (تم إصلاح كشف الإجابة: نسأل عن الخصم فقط والخيارات 4 أندية منافسة!)
        if len(fixtures) >= 4 and len(standings) >= 6:
            all_lg_clubs = [_clean_entity_name(t.get("short_name") or t.get("team_name")) for t in standings if t.get("short_name") or t.get("team_name")]
            for f in fixtures[:8]:
                h_n = _clean_entity_name(f.get("home_short", ""))
                a_n = _clean_entity_name(f.get("away_short", ""))
                if not h_n or not a_n or h_n == a_n:
                    continue
                other_clubs = [c for c in all_lg_clubs if c not in (h_n, a_n)]
                if len(set(other_clubs)) < 3:
                    continue
                opts_opp = _distinct_choices(a_n, other_clubs, 3)
                pool.append({
                    "id": next_id("fix_derby"),
                    "category": "derbies_stadiums",
                    "type": "mcq",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "medium",
                    "question": f"🔥 مواجهات الجولة في ({lg_name}): من هو الضيف الذي سيواجه نادي ({h_n}) على ملعبه؟",
                    "options": opts_opp,
                    "answer": a_n,
                    "hint": f"مباراة مجدولة في الجولة {f.get('gameweek', '')} بتصنيف Elo ({int(f.get('away_elo', 1500))}) للضيف",
                    "explanation": f"يستضيف ({h_n}) نظيره ({a_n}) في الجولة الحالية من {lg_name}."
                })

        # ب) جدول الترتيب: الشعار المغبش (بالمستويات الثلاثة)، تريفيا، من أنا، صح أم خطأ، أعلى أم أقل، الترتيب التكتيكي، و30 ثانية
        if len(standings) >= 5:
            for idx_t, t in enumerate(standings):
                c_name = _clean_entity_name(t.get("short_name") or t.get("team_name"))
                crest = t.get("crest", "")
                rank = t.get("rank", 1)
                pts = t.get("points", 0)
                played = t.get("played", 1)
                won = t.get("won", 0)
                gf = t.get("gf", 0)
                ga = t.get("ga", 0)
                if not c_name:
                    continue

                neighbors = []
                for offset in (-2, -1, 1, 2, 3, -3):
                    n_idx = (idx_t + offset) % len(standings)
                    n_name = _clean_entity_name(standings[n_idx].get("short_name") or standings[n_idx].get("team_name"))
                    if n_name and n_name != c_name:
                        neighbors.append(n_name)

                opts_tight_clubs = _distinct_choices(c_name, neighbors, 3)

                if crest and "placeholder" not in crest:
                    vis_diff = "easy" if rank <= 5 else ("medium" if rank <= 12 else "hard")
                    pool.append({
                        "id": next_id("vis_logo"),
                        "category": "visual",
                        "type": "logo_blur",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": vis_diff,
                        "question": f"🔍 الشعار المغبش ({lg_name}): لأي فريق ينتمي هذا الشعار الرسمي؟",
                        "image_url": crest,
                        "hint": f"يحتل المركز #{rank} في {lg_name} برصيد {pts} نقطة",
                        "options": opts_tight_clubs,
                        "answer": c_name,
                        "explanation": f"الشعار الرسمي يعود لفريق ({c_name}) في {lg_name}."
                    })

                pool.append({
                    "id": next_id("trv_rank"),
                    "category": "trivia",
                    "type": "mcq",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "easy" if rank <= 4 else "medium",
                    "question": f"🧠 في جدول ({lg_name}) الحالي، أي فريق يحتل المركز (#{rank}) برصيد ({pts} نقطة) وحقق ({won}) انتصارات؟",
                    "options": opts_tight_clubs,
                    "answer": c_name,
                    "hint": f"لعب {played} مباريات وسجل {gf} هدفاً",
                    "explanation": f"يحتل ({c_name}) المركز #{rank} في {lg_name} برصيد {pts} نقطة."
                })

                # أسئلة صح أم خطأ (true_false) من الإحصائيات الحقيقية
                if idx_t < 10:
                    is_true_stmt = (idx_t % 2 == 0)
                    shown_pts = pts if is_true_stmt else max(1, pts + (3 if idx_t % 4 == 1 else -3))
                    pool.append({
                        "id": next_id("tf_pts"),
                        "category": "true_false",
                        "type": "mcq",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": "easy" if rank <= 4 else "medium",
                        "question": f"⚡ صح أم خطأ ({lg_name}): يمتلك نادي ({c_name}) في رصيده حالياً ({shown_pts} نقطة) بالمركز #{rank}؟",
                        "options": ["صح ✅", "خطأ ❌"],
                        "answer": "صح ✅" if is_true_stmt else "خطأ ❌",
                        "hint": f"حقق الفريق {won} انتصارات من أصل {played} مباريات",
                        "explanation": f"العبارة {'صحيحة' if is_true_stmt else 'خاطئة'}؛ الرصيد الفعلي لنادي {c_name} هو ({pts} نقطة)."
                    })

                pool.append({
                    "id": next_id("who_club"),
                    "category": "who_am_i",
                    "type": "three_clues",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "medium",
                    "question": f"🕵️‍♂️ من أنا؟ اكتشف النادي المشارك في ({lg_name}) من أدلته الإحصائية:",
                    "clues": [
                        f"الدليل 1 (3 نقاط): خضت {played} مباريات، سجلت {gf} هدفاً واستقبلت {ga} هدفاً.",
                        f"الدليل 2 (نقطتان): حققت {won} انتصارات وأجمع ({pts} نقطة) حالياً.",
                        f"الدليل 3 (نقطة): أحتل المركز (#{rank}) في جدول ترتيب {lg_name}."
                    ],
                    "options": opts_tight_clubs,
                    "answer": c_name,
                    "hint": f"فارق أهداف هذا النادي هو ({t.get('gd', gf - ga):+d})",
                    "explanation": f"النادي هو ({c_name}) صاحب المركز #{rank} برصيد {pts} نقطة."
                })

            # مقارنات الأرقام (higher_lower) بتلميح مفيد حقيقي
            for i in range(len(standings) - 1):
                t1, t2 = standings[i], standings[i + 1]
                if t1.get("group_name") != t2.get("group_name"):
                    continue
                n1 = _clean_entity_name(t1.get("short_name") or t1.get("team_name"))
                n2 = _clean_entity_name(t2.get("short_name") or t2.get("team_name"))
                if not n1 or not n2 or n1 == n2:
                    continue

                g1, g2 = t1.get("gf", 0), t2.get("gf", 0)
                if g1 != g2:
                    ans_g = "أعلى 📈" if g2 > g1 else "أقل 📉"
                    pool.append({
                        "id": next_id("stat_gf"),
                        "category": "stats",
                        "type": "higher_lower",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": "medium",
                        "question": f"📊 مقارنة هجومية ({lg_name}): سجل {n1} ({g1} هدفاً).. فهل أهداف {n2} المسجلة أعلى أم أقل؟",
                        "item_a": {"name": n1, "crest": t1.get("crest", ""), "stat_label": "الأهداف المسجلة", "stat_val": g1},
                        "item_b": {"name": n2, "crest": t2.get("crest", ""), "stat_label": "الأهداف المسجلة", "stat_val": g2},
                        "hint": f"يمتلك {n2} فارق أهداف ({t2.get('gd', 0):+d}) مقابل ({t1.get('gd', 0):+d}) لنادي {n1}",
                        "options": ["أعلى 📈", "أقل 📉"],
                        "answer": ans_g,
                        "explanation": f"سجل {n2} ({g2} هدفاً) مقابل ({g1} هدفاً) لفريق {n1} في {lg_name}."
                    })

            # الترتيب التكتيكي (rank_order)
            if len(standings) >= 8:
                for start_k in range(0, len(standings) - 4, 2):
                    slice_4 = standings[start_k:start_k + 4]
                    if len({x.get("points", 0) for x in slice_4}) == 4:
                        r_items = [{"label": _clean_entity_name(x.get("short_name") or x.get("team_name")), "val": f"{x.get('points', 0)} نقطة"} for x in slice_4]
                        shuffled_r = list(r_items)
                        _SYS_RNG.shuffle(shuffled_r)
                        pool.append({
                            "id": next_id("tac_order"),
                            "category": "tactics",
                            "type": "rank_order",
                            "region": reg,
                            "league": lg_code,
                            "difficulty": "medium",
                            "question": f"📋 رتب هذه الأندية الأربعة في ({lg_name}) تنازلياً من الأعلى نقاطاً إلى الأقل:",
                            "rank_items": shuffled_r,
                            "correct_order": [x["label"] for x in r_items],
                            "options": [],
                            "answer": " ⬅️ ".join([x["label"] for x in r_items]),
                            "hint": f"صاحب المركز الأول بينها هو ({r_items[0]['label']})",
                            "explanation": "الترتيب الرسمي: " + " ثم ".join([f"{x['label']} ({x['val']})" for x in r_items])
                        })

            # تحدي الـ 30 ثانية (blitz_30s) مع قاموس اختصارات عربية وإنجليزية موسّع
            accepted_clubs, sample_clubs = _expand_blitz_club_aliases(standings)
            if len(accepted_clubs) >= 6:
                pool.append({
                    "id": next_id("blitz_lg"),
                    "category": "blitz",
                    "type": "blitz_30s",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "medium",
                    "question": f"⏱️ تحدي 30 ثانية ({lg_name}): اكتب أكبر عدد من أندية البطولة (بالعربية أو الإنجليزية)!",
                    "accepted_answers": accepted_clubs,
                    "sample_answers": sample_clubs,
                    "hint": "تُقبل الأسماء والاختصارات الشائعة (مثل: الريال، البارسا، السيتي، ليفربول...)",
                    "options": [],
                    "answer": "، ".join(sample_clubs[:6]),
                    "explanation": f"أمثلة من أندية {lg_name}: " + "، ".join(sample_clubs[:8])
                })

        # ج) قائمة الهدافين الحية (awards_scorers + who_am_i للاعبين!)
        if len(scorers) >= 4:
            sc_names = [s.get("name") for s in scorers if s.get("name")]
            for idx_s, s in enumerate(scorers):
                p_name = s.get("name")
                p_team = _clean_entity_name(s.get("team", ""))
                p_goals = s.get("goals", 0)
                p_rank = s.get("rank", idx_s + 1)
                if not p_name:
                    continue
                opts_sc = _distinct_choices(p_name, sc_names, 3)
                pool.append({
                    "id": next_id("aw_scorer"),
                    "category": "awards_scorers",
                    "type": "mcq",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "easy" if p_rank <= 3 else "medium",
                    "question": f"👟 سباق هدافي ({lg_name}): من هو نجم ({p_team}) صاحب المركز (#{p_rank}) برصيد ({p_goals} أهداف)؟",
                    "options": opts_sc,
                    "answer": p_name,
                    "hint": f"يلعب حالياً في صفوف {p_team}",
                    "explanation": f"الهداف هو ({p_name}) نجم {p_team} برصيد {p_goals} أهداف."
                })

                if idx_s < 5:
                    pool.append({
                        "id": next_id("who_player"),
                        "category": "who_am_i",
                        "type": "three_clues",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": "medium",
                        "question": f"🕵️‍♂️ من أنا؟ اكتشف هذا الهداف في ({lg_name}) من 3 أدلة:",
                        "clues": [
                            f"الدليل 1 (3 نقاط): أنافِس في بطولة ({lg_name}) وسجلت ({p_goals} أهداف) حتى الآن.",
                            f"الدليل 2 (نقطتان): أحتل المركز (#{p_rank}) في ترتيب هدافي البطولة.",
                            f"الدليل 3 (نقطة): أدافع حالياً عن ألوان نادي ({p_team})."
                        ],
                        "options": opts_sc,
                        "answer": p_name,
                        "hint": f"أحد هدافي نادي {p_team} هذا الموسم",
                        "explanation": f"اللاعب هو ({p_name}) نجم {p_team} برصيد {p_goals} أهداف."
                    })

        # د) الأرشيف التاريخي الحي (trivia + awards_scorers نظيفة بدون عدد الأهداف + finals_remontada للبطولات القارية)
        if isinstance(history, dict) and isinstance(history.get("seasons"), list):
            seasons = history["seasons"]
            titles_tbl = history.get("titles_table", [])

            for s_idx, s in enumerate(seasons[:75]):
                ch = s.get("champion")
                yr = s.get("season")
                ru = s.get("runner_up", "")
                top_sc_raw = s.get("top_scorer", "")
                if not ch or not yr:
                    continue

                era_peers = [ru] if ru else []
                for off in (-2, -1, 1, 2, 3):
                    if 0 <= s_idx + off < len(seasons):
                        c_near = seasons[s_idx + off].get("champion")
                        if c_near:
                            era_peers.append(c_near)
                        r_near = seasons[s_idx + off].get("runner_up")
                        if r_near:
                            era_peers.append(r_near)

                if len(set(era_peers)) >= 3:
                    opts_ch = _distinct_choices(ch, era_peers, 3)
                    yr_num = safe_num(str(yr)[:4], 2000)
                    pool.append({
                        "id": next_id("trv_hist_ch"),
                        "category": "trivia",
                        "type": "mcq",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": "easy" if yr_num >= 2014 else ("medium" if yr_num >= 1992 else "hard"),
                        "question": f"🏛️ أرشيف ({lg_name}): أي فريق تُوّج باللقب في موسم ({yr})؟",
                        "hint": f"الوصيف في ذلك الموسم كان: {ru or 'من أندية القمة'}",
                        "options": opts_ch,
                        "answer": ch,
                        "explanation": f"تُوّج ({ch}) رسمياً بلقب {lg_name} في موسم {yr}."
                    })

                    # نهائيات الأبطال القارية (UCL, ACL, CAF) تضاف لفئة النهائيات الكبرى
                    if lg_code in ("UCL", "ACL", "CAF") and ru:
                        pool.append({
                            "id": next_id("fin_club"),
                            "category": "finals_remontada",
                            "type": "mcq",
                            "region": reg,
                            "league": lg_code,
                            "difficulty": "easy" if yr_num >= 2015 else ("medium" if yr_num >= 2000 else "hard"),
                            "question": f"⚡ نهائي ({lg_name} {yr}): من هو الفريق الذي خسر النهائي وحل وصيفاً خلف البطل ({ch})؟",
                            "options": _distinct_choices(ru, [x for x in era_peers if x != ch], 3),
                            "answer": ru,
                            "hint": f"نهائي نسخة {yr} التي تُوّج بها {ch}",
                            "explanation": f"التقى ({ch}) مع ({ru}) في نهائي {lg_name} موسم {yr}، وتُوّج {ch} باللقب."
                        })

                if top_sc_raw and "موثق" not in top_sc_raw:
                    # تنظيف اسم الهداف من (36 هدف) لكي تكون الخيارات متناسقة ولا تكشف الجواب
                    sc_clean = re.sub(r"\s*\(\d+[^)]*\)", "", top_sc_raw).strip()
                    era_scorers = [
                        re.sub(r"\s*\(\d+[^)]*\)", "", seasons[s_idx + off].get("top_scorer", "")).strip()
                        for off in (-3, -2, -1, 1, 2, 3)
                        if 0 <= s_idx + off < len(seasons)
                        and seasons[s_idx + off].get("top_scorer")
                        and "موثق" not in seasons[s_idx + off].get("top_scorer", "")
                    ]
                    if sc_clean and len(set(era_scorers)) >= 3:
                        opts_hsc = _distinct_choices(sc_clean, era_scorers, 3)
                        pool.append({
                            "id": next_id("aw_hist_sc"),
                            "category": "awards_scorers",
                            "type": "mcq",
                            "region": reg,
                            "league": lg_code,
                            "difficulty": "hard",
                            "question": f"🌕 سجل الهدافين التاريخي ({lg_name}): من تُوّج هدافاً للمسابقة في موسم ({yr})؟",
                            "options": opts_hsc,
                            "answer": sc_clean,
                            "hint": f"بطل تلك النسخة كان نادي {ch}",
                            "explanation": f"هداف {lg_name} في موسم {yr} هو ({top_sc_raw})."
                        })

            if len(titles_tbl) >= 4:
                for t_row in titles_tbl[:8]:
                    club_n = t_row.get("club")
                    t_cnt = t_row.get("titles", 0)
                    if club_n and t_cnt > 0:
                        opts_cnt = _tight_numeric_choices(t_cnt, min_val=1, step=1)
                        pool.append({
                            "id": next_id("trv_titles_cnt"),
                            "category": "trivia",
                            "type": "mcq",
                            "region": reg,
                            "league": lg_code,
                            "difficulty": "medium",
                            "question": f"🏆 السجل الذهبي ({lg_name}): كم مرة تُوّج ({club_n}) بلقب هذه البطولة عبر تاريخه؟",
                            "options": opts_cnt,
                            "answer": str(t_cnt),
                            "hint": f"آخر لقب له في البطولة كان عام {t_row.get('last_title', '-')}",
                            "explanation": f"يمتلك ({club_n}) في خزائنه ({t_cnt}) لقباً في {lg_name}."
                        })

    if len(pool) >= 80:
        save_to_cache(cache_key, pool)

    return pool


def get_quiz_arena_bank(
    league_filter: str = "ALL",
    difficulty_filter: str = "ALL",
    region_filter: str = "ALL",
    category_filter: str = "ALL",
    type_filter: str = "ALL",
    entity_filter: str = "ALL",
    seed_code: str = "",
    use_ai: bool = False,
    batch_size: int = 160,
    **kwargs
):
    lg = (league_filter or "ALL").strip().upper()
    diff = (difficulty_filter or "ALL").strip().lower()
    reg = (region_filter or "ALL").strip().lower()
    raw_cat = category_filter if (category_filter and category_filter != "ALL") else (type_filter or "ALL")
    cat = str(raw_cat).strip().lower()

    # منع تعارض القارة مع الدوري (إذا اختار المستخدم دورياً محدداً نعتمد الدوري ونلغي تضارب القارة)
    if lg != "ALL" and reg != "all":
        reg = "all"

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    ai_available = bool(gemini_key and gemini_key.startswith("AIza"))

    api_pool = _build_pure_live_api_question_pool(target_league=lg) or []
    ai_pool = _generate_ai_batch_questions(reg, lg, cat, diff) if (use_ai and ai_available) else []
    master_pool = ai_pool + api_pool

    # حساب عدد الأسئلة الحقيقي لكل فئة
    category_counts = {"ALL": len(master_pool)}
    for q in master_pool:
        ck = str(q.get("category") or "trivia").lower()
        category_counts[ck] = category_counts.get(ck, 0) + 1

    filtered = []
    for q in master_pool:
        q_lg = str(q.get("league") or "ALL").upper()
        q_reg = str(q.get("region") or "ALL").lower()
        q_cat = str(q.get("category") or "trivia").lower()
        q_type = str(q.get("type") or "mcq").lower()
        q_diff = str(q.get("difficulty") or "medium").lower()

        if lg != "ALL" and q_lg not in (lg, "ALL"):
            continue
        if reg != "all" and q_reg not in (reg, "all"):
            continue
        if cat != "all" and cat not in (q_cat, q_type):
            continue
        if diff != "all" and q_diff != diff:
            continue
        filtered.append(dict(q))

    fallback_used = False
    matched_count = len(filtered)

    if not filtered and cat != "all":
        fallback_used = True
        filtered = [dict(q) for q in master_pool if cat in (str(q.get("category") or "").lower(), str(q.get("type") or "").lower())]
    if not filtered and reg != "all":
        fallback_used = True
        filtered = [dict(q) for q in master_pool if str(q.get("region") or "").lower() in (reg, "all")]
    if not filtered:
        fallback_used = True
        filtered = [dict(q) for q in master_pool]

    clean_seed = (seed_code or "").strip().upper()
    if clean_seed:
        seeded_rng = random.Random(clean_seed)
        filtered.sort(key=lambda x: x.get("id", ""))
        seeded_rng.shuffle(filtered)
        for q in filtered[:batch_size]:
            if q.get("options") and len(q["options"]) > 2:
                opts_c = sorted(list(q["options"]))
                seeded_rng.shuffle(opts_c)
                q["options"] = opts_c
    else:
        _SYS_RNG.shuffle(filtered)
        for q in filtered[:batch_size]:
            if q.get("options") and len(q["options"]) > 2:
                opts_c = list(q["options"])
                _SYS_RNG.shuffle(opts_c)
                q["options"] = opts_c

    generated_seed = clean_seed if clean_seed else f"DP-{_SYS_RNG.randint(1000, 9999)}"

    return {
        "total_pool_size": len(master_pool),
        "matched_count": matched_count,
        "fallback_used": fallback_used,
        "ai_available": ai_available,
        "category_counts": category_counts,
        "questions": filtered[:batch_size],
        "seed_code": generated_seed
    }
    # =========================================================================
# 18. محرك غرفة المحللين الأذكياء (AI Pundit Studio - 100% Real Match Data + Gemini AI)
# =========================================================================

def _find_team_in_standings(standings_list, team_name, team_id=""):
    if not standings_list:
        return None
    t_low = (team_name or "").strip().lower()
    for row in standings_list:
        r_short = (row.get("short_name") or "").strip().lower()
        r_full = (row.get("team_name") or "").strip().lower()
        r_raw = (row.get("raw_name") or "").strip().lower()
        if t_low in (r_short, r_full, r_raw) or (len(t_low) >= 4 and (t_low in r_full or r_short in t_low)):
            return row
    return None


def _collect_real_match_dossier(league_code: str, match_id: str):
    """جمع كافة البيانات والأرقام الحقيقية للمباراة من ESPN API وجداول الترتيب في حزمة موثقة واحدة"""
    code = (league_code or "PL").upper()
    match_id = str(match_id).strip()
    espn_code = LEAGUE_CODES.get(code, {}).get("espn", "eng.1")

    # 1. سحب ملخص المباراة المباشر من ESPN
    urls = [
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
        f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/summary?event={match_id}",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={match_id}"
    ]
    summary_data = None
    for u in urls:
        res = fetch_json_fast(u, timeout=4.0)
        if res and isinstance(res, dict) and ("header" in res or "boxscore" in res or "rosters" in res):
            summary_data = res
            break

    cached_item = _TODAY_RAW_EVENTS.get(match_id)
    cached_event = cached_item["event"] if cached_item else None

    state = "pre"
    display_clock = ""
    h_name, a_name = "المضيف", "الضيف"
    h_id, a_id = "", ""
    h_score, a_score = 0, 0
    venue_name = "ملعب اللقاء"

    comp = None
    if summary_data and "header" in summary_data:
        comps = summary_data["header"].get("competitions", [])
        if comps and isinstance(comps[0], dict):
            comp = comps[0]
    if not comp and cached_event:
        comps = cached_event.get("competitions", [])
        if comps and isinstance(comps[0], dict):
            comp = comps[0]

    if comp:
        st_obj = comp.get("status") or (cached_event.get("status") if cached_event else {}) or {}
        state = st_obj.get("type", {}).get("state", "pre")
        display_clock = st_obj.get("displayClock", "")
        v_obj = comp.get("venue") or {}
        if v_obj.get("fullName"):
            venue_name = v_obj["fullName"]

        for c in comp.get("competitors", []):
            t_obj = c.get("team", {})
            if c.get("homeAway") == "home":
                h_id = str(t_obj.get("id") or c.get("id") or "")
                h_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or h_name
                h_score = _safe_int(c.get("score"), 0)
            elif c.get("homeAway") == "away":
                a_id = str(t_obj.get("id") or c.get("id") or "")
                a_name = t_obj.get("shortDisplayName") or t_obj.get("displayName") or a_name
                a_score = _safe_int(c.get("score"), 0)

    # 2. جلب الإحصائيات، التشكيلات، الأحداث، وجدول الترتيب بالتوازي
    with ThreadPoolExecutor(max_workers=4) as ex:
        fut_standings = ex.submit(get_official_standings, code)
        fut_scorers = ex.submit(get_top_scorers, code)
        fut_lineups = ex.submit(get_match_lineups, code, match_id, summary_data)
        fut_events = ex.submit(get_match_events, code, match_id, summary_data)

        standings = fut_standings.result() or []
        scorers = fut_scorers.result() or []
        lineups = fut_lineups.result() or {}
        events_data = fut_events.result() or {}

    stats_data = _extract_stats_and_goals_from_event(cached_event, summary_data)
    power_map = build_team_power_map(standings)

    h_st_row = _find_team_in_standings(standings, h_name, h_id) or {}
    a_st_row = _find_team_in_standings(standings, a_name, a_id) or {}

    h_power = match_team_power(power_map, h_st_row.get("team_name", h_name), h_name)
    a_power = match_team_power(power_map, a_st_row.get("team_name", a_name), a_name)

    # استخراج هدافي الفريقين من قائمة هدافي الدوري الحقيقية
    h_top_scorer, a_top_scorer = "", ""
    for sc in scorers:
        sc_team = (sc.get("team") or "").lower()
        if not h_top_scorer and (h_name.lower() in sc_team or sc_team in h_name.lower()):
            h_top_scorer = f"{sc['name']} ({sc['goals']} أهداف)"
        if not a_top_scorer and (a_name.lower() in sc_team or sc_team in a_name.lower()):
            a_top_scorer = f"{sc['name']} ({sc['goals']} أهداف)"

    # استخراج الخطط وأبرز الأسماء وأعلى اللاعبين تقييماً من التشكيلة الحقيقية
    h_formation = (lineups.get("home") or {}).get("formation") or "4-3-3"
    a_formation = (lineups.get("away") or {}).get("formation") or "4-3-3"
    h_starters = (lineups.get("home") or {}).get("starters") or []
    a_starters = (lineups.get("away") or {}).get("starters") or []

    h_key_players = [p["name"] for p in h_starters[-4:] if p.get("name")]
    a_key_players = [p["name"] for p in a_starters[-4:] if p.get("name")]

    all_rated_players = []
    for p in h_starters + ((lineups.get("home") or {}).get("subs") or []):
        if p.get("rating"):
            all_rated_players.append({**p, "team": h_name})
    for p in a_starters + ((lineups.get("away") or {}).get("subs") or []):
        if p.get("rating"):
            all_rated_players.append({**p, "team": a_name})
    all_rated_players.sort(key=lambda x: float(x.get("rating") or 0), reverse=True)

    mvp_player = all_rated_players[0] if all_rated_players else None
    lowest_player = all_rated_players[-1] if len(all_rated_players) >= 4 else None

    return {
        "league_code": code,
        "league_name": LEAGUE_CODES.get(code, {}).get("name", "البطولة"),
        "match_id": match_id,
        "state": state,
        "display_clock": display_clock,
        "venue": venue_name,
        "home_team": h_name,
        "away_team": a_name,
        "home_score": h_score,
        "away_score": a_score,
        "home_standing": h_st_row,
        "away_standing": a_st_row,
        "home_power": h_power,
        "away_power": a_power,
        "home_top_scorer": h_top_scorer,
        "away_top_scorer": a_top_scorer,
        "home_formation": h_formation,
        "away_formation": a_formation,
        "home_key_players": h_key_players,
        "away_key_players": a_key_players,
        "is_official_lineup": lineups.get("is_official", False),
        "has_lineups": lineups.get("has_lineups", False),
        "mvp_player": mvp_player,
        "lowest_player": lowest_player,
        "stats": stats_data,
        "events": events_data.get("events", [])
    }


def _build_data_driven_studio_fallback(dossier: dict, target_phase: str):
    """بناء حوار المحللين الأربعة من الأرقام الحقيقية للمباراة 100% (في حال عدم توفر مفتاح Gemini أو بطء الشبكة)"""
    h = dossier["home_team"]
    a = dossier["away_team"]
    h_st = dossier["home_standing"]
    a_st = dossier["away_standing"]
    h_pow = dossier["home_power"]
    a_pow = dossier["away_power"]
    st = dossier["stats"]
    h_live = st.get("home", {})
    a_live = st.get("away", {})
    evs = dossier["events"]

    h_rank = h_st.get("rank", "-")
    a_rank = a_st.get("rank", "-")
    h_pts = h_st.get("points", 0)
    a_pts = a_st.get("points", 0)
    h_gf, h_ga = h_st.get("gf", 0), h_st.get("ga", 0)
    a_gf, a_ga = a_st.get("gf", 0), a_st.get("ga", 0)
    h_gp = max(1, h_st.get("played", 1))
    a_gp = max(1, a_st.get("played", 1))

    h_form_str = "-".join(h_st.get("form") or ["W", "D", "W"])
    a_form_str = "-".join(a_st.get("form") or ["D", "W", "L"])

    h_players_txt = "، ".join(dossier["home_key_players"][:3]) if dossier["home_key_players"] else f"خط هجوم {h}"
    a_players_txt = "، ".join(dossier["away_key_players"][:3]) if dossier["away_key_players"] else f"خط هجوم {a}"

    # حساب الأهداف المتوقعة والتوقعات الرقمية قبل اللقاء
    elo_diff = (h_pow["elo"] + 45.0) - a_pow["elo"]
    xg_h = round(max(0.5, min(3.4, h_pow["att"] * a_pow["def"] * 1.18)), 2)
    xg_a = round(max(0.4, min(3.1, a_pow["att"] * h_pow["def"] * 0.95)), 2)

    pred_h = max(0, int(round(xg_h)))
    pred_a = max(0, int(round(xg_a)))
    if elo_diff > 70 and pred_h <= pred_a:
        pred_h = pred_a + 1
    elif elo_diff < -70 and pred_a <= pred_h:
        pred_a = pred_h + 1

    # ==================== المرحلة 1: قبل المباراة (Pre-Match) ====================
    if target_phase == "pre":
        headline = f"استوديو القمة التحضيري: قراءة تكتيكية ورقمية لمواجهة {h} ضد {a}"
        key_battle = f"صراع خط الوسط والتحولات بين ({h_players_txt}) في {h} أمام ({a_players_txt}) في {a}"

        p1_text = (
            f"بالنظر إلى الرسم التكتيكي، يدخل {h} بخطة ({dossier['home_formation']}) معتمداً على تحركات ({h_players_txt}) "
            f"في الثلث الأخير، بينما يعتمد {a} على رسم ({dossier['away_formation']}) بوجود ({a_players_txt}). "
            f"المفتاح التكتيكي اليوم يكمن في قدرة {h} على اختراق التكتل الدفاعي لـ {a} الذي استقبل {a_ga} هدفاً في {a_gp} جولات."
        )
        p2_text = (
            f"لغة الأرقام الرسمية في {dossier['league_name']} واضحة؛ {h} يحتل المركز #{h_rank} برصيد {h_pts} نقطة "
            f"(بمعدل تهديفي {round(h_gf/h_gp, 2)} هدف/مباراة وتصنيف Elo يبلغ {h_pow['elo']})، في المقابل يأتي {a} في المركز #{a_rank} "
            f"برصيد {a_pts} نقطة (معدل {round(a_gf/a_gp, 2)} هدف/مباراة وتصنيف Elo {a_pow['elo']}). النمذجة تمنح {h} {xg_h} xG مقابل {xg_a} xG لـ {a}."
        )
        p3_text = (
            f"الزخم المعنوي والفورمة في آخر 5 جولات تعطي مؤشراً هاماً؛ {h} يسير بنسق ({h_form_str}) على أرضية ({dossier['venue']})، "
            f"بينما يدخل {a} بسلسلة ({a_form_str}). "
            + (f"وجود الهداف {dossier['home_top_scorer']} يمنح أصحاب الأرض ثقلاً حاسماً." if dossier["home_top_scorer"] else f"الحسم سيتوقف على استغلال الفرص المبكرة في أول 20 دقيقة.")
        )
        p4_text = (
            f"مواجهة تتطلب تركيزاً تحكيمياً وانضباطاً عالياً؛ فارق القوة الرقمي بين الفريقين يبلغ {abs(round(h_pow['elo'] - a_pow['elo'], 1))} نقطة Elo، "
            f"وأي بطاقة مبكرة أو خطأ في منطقة الجزاء سيقلب حسابات المدربين رأساً على عقب."
        )

        debate_topic = f"هل ينجح {h} في فرض أسلوبه الهجومي أم يخطف {a} نقاط اللقاء بالتحولات؟"
        debate_summary = (
            f"المحلل التكتيكي يرى أن خطة ({dossier['home_formation']}) تمنح {h} سيطرة ميدانية، بينما يشير محلل الأرقام إلى أن "
            f"معدل استقبال الأهداف ({h_ga} لـ {h} مقابل {a_ga} لـ {a}) يجعل المباراة مفتوحة على سيناريو التسجيل المتبادل."
        )

        preds = [
            {"pundit": "د. طارق التكتيكي", "score": f"{pred_h} - {pred_a}"},
            {"pundit": "م. سامر الرقمي (xG)", "score": f"{pred_h} - {pred_a}" if xg_h != xg_a else "1 - 1"},
            {"pundit": "كابتن رياض الحسم", "score": f"{max(1, pred_h)} - {pred_a}" if elo_diff >= 0 else f"{pred_h} - {max(1, pred_a)}"},
            {"pundit": "المستشار جمال التحكيمي", "score": "1 - 1" if abs(elo_diff) < 55 else f"{pred_h} - {pred_a}"}
        ]

    # ==================== المرحلة 2: بين الشوطين / مباشر (Live / Half-Time) ====================
    elif target_phase in ("in", "ht", "live"):
        pos_h = h_live.get("possession", 50)
        pos_a = a_live.get("possession", 50)
        sh_h, sot_h = h_live.get("shots", 0), h_live.get("shots_on_target", 0)
        sh_a, sot_a = a_live.get("shots", 0), a_live.get("shots_on_target", 0)
        corn_h, corn_a = h_live.get("corners", 0), a_live.get("corners", 0)
        fouls_h, fouls_a = h_live.get("fouls", 0), a_live.get("fouls", 0)
        yc_h, yc_a = h_live.get("yellow_cards", 0), a_live.get("yellow_cards", 0)
        rc_h, rc_a = h_live.get("red_cards", 0), a_live.get("red_cards", 0)

        goals_txt = "، ".join(st.get("home_goals", []) + st.get("away_goals", [])) or "لم تُسجل أهداف حتى الآن"
        clk_lbl = dossier["display_clock"] or "الشوط الأول / الجاري"
        headline = f"استوديو التحليل المباشر ({clk_lbl}): النتيجة الآن {h} ({dossier['home_score']} - {dossier['away_score']}) {a}"
        key_battle = f"الفاعلية أمام المرمى: {sot_h} تسديدات مؤطرة لـ {h} مقابل {sot_a} لـ {a}"

        p1_text = (
            f"حتى الدقيقة ({clk_lbl}) والنتيجة تشير إلى ({dossier['home_score']} - {dossier['away_score']})، نلاحظ أن {h} يعتمد خطة ({dossier['home_formation']}) "
            f"بنسبة استحواذ {pos_h}%، مقابل {pos_a}% لـ {a} بخطة ({dossier['away_formation']}). "
            + (f"الأهداف المسجلة ({goals_txt}) غيرت تمركز الخطوط الخلفية وأجبرت الطرف المتأخر على فتح ملعبه." if (dossier['home_score'] + dossier['away_score']) > 0 else "التحفظ الدفاعي واضح من الطرفين مع إغلاق العمق.")
        )
        p2_text = (
            f"بلغة الأرقام الفعلية للمباراة حتى اللحظة: {h} سدد {sh_h} كرات (منها {sot_h} على المرمى) وحصل على {corn_h} ركنيات، "
            f"بينما {a} سدد {sh_a} كرات ({sot_a} على المرمى) و{corn_a} ركنيات. "
            f"دقة التحويل الهجومي تظهر أن {'كفة الخطورة تميل لصالح ' + h if sot_h >= sot_a else 'تحولات ' + a + ' أكثر مباشرة وخطورة على المرمى'}."
        )
        p3_text = (
            f"من الناحية البدنية والذهنية، المباراة تحتاج إلى تدخل من دكة البدلاء لتنشيط الأجنحة. "
            + (f"أعلى لاعب تقييماً في الملعب حالياً هو ({dossier['mvp_player']['name']}) بتقييم ({dossier['mvp_player']['rating']})، " if dossier.get("mvp_player") else "")
            + (f"بينما يحتاج المدرب لمراجعة أداء ({dossier['lowest_player']['name']} - تقييم {dossier['lowest_player']['rating']}) في الشوط الثاني." if dossier.get("lowest_player") else "الضغط العالي في أول ربع ساعة من الشوط الثاني سيكون حاسماً.")
        )
        p4_text = (
            f"في الجانب الانضباطي والتحكيمي: سُجلت {fouls_h} أخطاء على {h} ({yc_h} صفراء و{rc_h} حمراء) مقابل {fouls_a} أخطاء على {a} ({yc_a} صفراء و{rc_a} حمراء). "
            f"الحذر مطلوب جداً للاعبين المنذرين لتفادي النقص العددي في الدقائق القادمة."
        )

        debate_topic = "ما هو التعديل التكتيكي الأهم لحسم النتيجة في الدقائق المتبقية؟"
        debate_summary = (
            f"محلل الأرقام يرى أن الاستحواذ ({pos_h}% لـ {h} مقابل {pos_a}% لـ {a}) يحتاج لزيادة التسديد المؤطر ({sot_h} مقابل {sot_a})، "
            f"بينما يطالب محلل التكتيك بإشراك أوراق هجومية سريعة لاستغلال المساحات خلف الأظهرة."
        )
        preds = [
            {"pundit": "مسجلو الأهداف", "score": goals_txt[:35]},
            {"pundit": "الاستحواذ الفعلي", "score": f"{pos_h}% - {pos_a}%"},
            {"pundit": "التسديد على المرمى", "score": f"{sot_h} - {sot_a}"},
            {"pundit": "الأخطاء والإنذارات", "score": f"{yc_h+yc_a} بطاقات"}
        ]

    # ==================== المرحلة 3: بعد نهاية المباراة (Post-Match) ====================
    else:
        pos_h = h_live.get("possession", 50)
        pos_a = a_live.get("possession", 50)
        sh_h, sot_h = h_live.get("shots", 0), h_live.get("shots_on_target", 0)
        sh_a, sot_a = a_live.get("shots", 0), a_live.get("shots_on_target", 0)
        corn_h, corn_a = h_live.get("corners", 0), a_live.get("corners", 0)
        yc_h, yc_a = h_live.get("yellow_cards", 0), a_live.get("yellow_cards", 0)
        rc_h, rc_a = h_live.get("red_cards", 0), a_live.get("red_cards", 0)

        h_sc, a_sc = dossier["home_score"], dossier["away_score"]
        goals_all = st.get("home_goals", []) + st.get("away_goals", [])
        goals_str = " | ".join(goals_all) if goals_all else "تعادل سلبي بدون أهداف"

        subs_evs = [e for e in evs if e.get("type") == "sub"]
        var_evs = [e for e in evs if e.get("type") in ("disallowed_goal", "red_card", "missed_penalty")]

        winner_txt = f"فوز {h}" if h_sc > a_sc else (f"فوز {a}" if a_sc > h_sc else "التعادل الإيجابي/السلبي")
        headline = f"الاستوديو التحليلي الختامي: تشريح {winner_txt} بنتيجة ({h_sc} - {a_sc}) بين {h} و{a}"
        mvp_str = f"{dossier['mvp_player']['name']} ({dossier['mvp_player']['team']}) بتقييم {dossier['mvp_player']['rating']}/10" if dossier.get("mvp_player") else "خط الوسط الدفاعي"
        key_battle = f"رجل المباراة تكتيكياً: ⭐ {mvp_str}"

        p1_text = (
            f"انتهت المواجهة بنتيجة ({h_sc} - {a_sc})؛ تكتيكياً، المواجهة بين خطة ({dossier['home_formation']}) لـ {h} "
            f"وخطة ({dossier['away_formation']}) لـ {a} حُسمت بفضل الفاعلية في التحولات. "
            + (f"الأهداف التي سُجلت عبر ({goals_str}) عكست تفوقاً في استغلال المساحات النصفيه." if goals_all else "التنظيم الدفاعي الصارم أغلق كافة منافذ التسجيل طوال الـ 90 دقيقة.")
        )
        p2_text = (
            f"الحصيلة الإحصائية الكاملة للـ 90 دقيقة: {h} أنهى اللقاء باستحواذ {pos_h}% و{sh_h} تسديدة ({sot_h} بين القائمين والعارضة) و{corn_h} ركنيات، "
            f"مقابل استحواذ {pos_a}% لـ {a} بـ {sh_a} تسديدة ({sot_a} على المرمى) و{corn_a} ركنيات. "
            f"الأرقام تؤكد أن {'النتيجة منصفة تماماً قياساً بكمية الفرص المؤطرة' if (h_sc >= a_sc and sot_h >= sot_a) or (a_sc >= h_sc and sot_a >= sot_h) else 'الفاعلية الحاسمة تفوقت على الاستحواذ السلبي'}."
        )
        p3_text = (
            f"نقطة التحول والنجومية في اللقاء: برز بشكل لافت ({mvp_str}) كأعلى اللاعبين تقييماً في أرض الملعب. "
            + (f"كما شهد اللقاء {len(subs_evs)} تبديلات تكتيكية أبرزها في الدقيقة {subs_evs[0]['clock']} ({subs_evs[0]['detail']}) لتغيير إيقاع اللعب." if subs_evs else "الالتزام البدني استمر حتى الدقائق الأخيرة.")
        )
        p4_text = (
            f"القراءة التحكيمية والانضباطية للقاء: أشهر الحكم {yc_h + yc_a} بطاقات صفراء و{rc_h + rc_a} بطاقة حمراء. "
            + (f"أبرز القرارات المؤثرة كانت في الدقيقة {var_evs[0]['clock']}: ({var_evs[0]['title']} - {var_evs[0]['detail']})." if var_evs else "المباراة سارت بدون حالات تحكيمية جدلية معقدة أو طرد مباشر.")
        )

        debate_topic = "هل عكست النتيجة النهائية واقع الأرقام والفرص في الملعب؟"
        debate_summary = (
            f"إجماع في الاستوديو على استحقاق ({mvp_str}) لنجومية اللقاء، مع الإشارة إلى أن نسبة التسديد المؤطر "
            f"({sot_h} لـ {h} مقابل {sot_a} لـ {a}) كانت الفيصل الحقيقي بعيداً عن نسب الاستحواذ ({pos_h}% - {pos_a}%)."
        )
        preds = [
            {"pundit": "النتيجة النهائية", "score": f"{h_sc} - {a_sc}"},
            {"pundit": "نجم اللقاء ⭐", "score": dossier["mvp_player"]["name"] if dossier.get("mvp_player") else "-"},
            {"pundit": "التسديد المؤطر", "score": f"{sot_h} - {sot_a}"},
            {"pundit": "الاستحواذ الكلي", "score": f"{pos_h}% - {pos_a}%"}
        ]

    return {
        "has_studio": True,
        "phase": target_phase,
        "actual_state": dossier["state"],
        "display_clock": dossier["display_clock"],
        "home_team": h,
        "away_team": a,
        "home_score": dossier["home_score"],
        "away_score": dossier["away_score"],
        "headline": headline,
        "key_battle": key_battle,
        "pundits": [
            {
                "id": "tactician",
                "name": "د. طارق التكتيكي",
                "role": "محلل الخطط والرسم التكتيكي 🧠",
                "avatar": "🧠",
                "color": "#00e676",
                "analysis": p1_text
            },
            {
                "id": "data_analyst",
                "name": "م. سامر الرقمي (xG & Data)",
                "role": "خبير الإحصائيات ولغة الأرقام 📊",
                "avatar": "📊",
                "color": "#00d2ff",
                "analysis": p2_text
            },
            {
                "id": "momentum_star",
                "name": "كابتن رياض الحسم",
                "role": "محلل الزخم والأداء الفردي 🔥",
                "avatar": "🔥",
                "color": "#ffd600",
                "analysis": p3_text
            },
            {
                "id": "moderator_ref",
                "name": "المستشار جمال التحكيمي",
                "role": "مدير الاستوديو وخبير التحكيم ⚖️🎙️",
                "avatar": "⚖️",
                "color": "#c084fc",
                "analysis": p4_text
            }
        ],
        "debate": {
            "topic": debate_topic,
            "summary": debate_summary
        },
        "summary_badges": preds
    }


def get_ai_pundit_studio_analysis(league_code: str, match_id: str, requested_phase: str = "auto"):
    """توليد استوديو تحليلي احترافي من 4 محللين بالاعتماد الحصري على بيانات المباراة الحقيقية + Gemini AI"""
    match_id_clean = str(match_id).strip()
    cached_ev_wrap = _TODAY_RAW_EVENTS.get(match_id_clean)

    # فحص سريع للكاش قبل سحب بيانات ESPN من جديد
    if cached_ev_wrap and isinstance(cached_ev_wrap.get("event"), dict):
        ev_raw = cached_ev_wrap["event"]
        fast_state = ev_raw.get("status", {}).get("type", {}).get("state", "pre")
        fast_phase = requested_phase if requested_phase in ("pre", "in", "post") else fast_state
        comps_raw = ev_raw.get("competitions") or []
        h_sc_f, a_sc_f = 0, 0
        if comps_raw:
            for c_r in comps_raw[0].get("competitors", []):
                if c_r.get("homeAway") == "home":
                    h_sc_f = _safe_int(c_r.get("score"), 0)
                elif c_r.get("homeAway") == "away":
                    a_sc_f = _safe_int(c_r.get("score"), 0)
        fast_key = f"ai_studio_v1_{league_code}_{match_id_clean}_{fast_phase}_{h_sc_f}_{a_sc_f}"
        fast_hit, fast_fresh = get_from_cache(fast_key, ttl=120 if fast_state == "in" else 1800)
        if fast_hit and fast_fresh:
            return fast_hit

    dossier = _collect_real_match_dossier(league_code, match_id_clean)
    actual_state = dossier["state"]
    target_phase = requested_phase if requested_phase in ("pre", "in", "post") else actual_state

    if actual_state == "pre" and target_phase in ("in", "post"):
        return {
            "has_studio": False,
            "phase": target_phase,
            "actual_state": "pre",
            "message": "🔒 لم تبدأ المباراة بعد — يتوفر حالياً فقط (استوديو ما قبل المباراة)."
        }

    if actual_state == "in" and target_phase == "post":
        return {
            "has_studio": False,
            "phase": "post",
            "actual_state": "in",
            "message": "🔒 المباراة لا تزال جارية في أرض الملعب — سيتفعل (استوديو ما بعد النهاية) فور إطلاق صافرة النهاية."
        }

    cache_key = f"ai_studio_v1_{league_code}_{match_id_clean}_{target_phase}_{dossier['home_score']}_{dossier['away_score']}"
    cached_res, is_fresh = get_from_cache(cache_key, ttl=120 if actual_state == "in" else 1800)
    if cached_res and is_fresh:
        return cached_res

    base_studio = _build_data_driven_studio_fallback(dossier, target_phase)


    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key.startswith("AIza"):
        try:
            st = dossier["stats"]
            h_st = dossier["home_standing"]
            a_st = dossier["away_standing"]
            evs_short = [f"{e['clock']}: {e['title']} ({e['detail']})" for e in dossier["events"][:12]]

            phase_ar = "قبل المباراة (تحضيري)" if target_phase == "pre" else ("بين الشوطين / أثناء اللعب (مباشر)" if target_phase == "in" else "بعد صافرة النهاية (ختامي)")

            facts_sheet = f"""بيانات المباراة الرسمية والحقيقية 100% من المصدر (يُمنع منعاً باتاً اختلاق أي رقم أو اسم خارجها):
- البطولة: {dossier['league_name']} | الملعب: {dossier['venue']}
- الطرفان: {dossier['home_team']} ضد {dossier['away_team']}
- مرحلة الاستوديو المطلوبة: {phase_ar}
- حالة المباراة الفعلية: {actual_state} ({dossier['display_clock']}) | النتيجة: {dossier['home_team']} {dossier['home_score']} - {dossier['away_score']} {dossier['away_team']}
- ترتيب {dossier['home_team']} في الدوري: المركز #{h_st.get('rank','-')}، النقاط {h_st.get('points',0)}، لعب {h_st.get('played',0)}، سجل {h_st.get('gf',0)} واستقبل {h_st.get('ga',0)}، الفورمة {h_st.get('form',[])}، التشكيلة ({dossier['home_formation']}) وأبرز الأسماء: {', '.join(dossier['home_key_players'])}
- ترتيب {dossier['away_team']} في الدوري: المركز #{a_st.get('rank','-')}، النقاط {a_st.get('points',0)}، لعب {a_st.get('played',0)}، سجل {a_st.get('gf',0)} واستقبل {a_st.get('ga',0)}، الفورمة {a_st.get('form',[])}، التشكيلة ({dossier['away_formation']}) وأبرز الأسماء: {', '.join(dossier['away_key_players'])}
- مسجلو الأهداف في اللقاء: {st.get('home_goals',[]) + st.get('away_goals',[])}
- إحصائيات اللقاء الحية: استحواذ ({st['home'].get('possession',0)}% - {st['away'].get('possession',0)}%)، التسديدات ({st['home'].get('shots',0)} - {st['away'].get('shots',0)})، التسديد على المرمى ({st['home'].get('shots_on_target',0)} - {st['away'].get('shots_on_target',0)})، الركنيات ({st['home'].get('corners',0)} - {st['away'].get('corners',0)})، الأخطاء ({st['home'].get('fouls',0)} - {st['away'].get('fouls',0)})، البطاقات الصفراء ({st['home'].get('yellow_cards',0)} - {st['away'].get('yellow_cards',0)})، الحمراء ({st['home'].get('red_cards',0)} - {st['away'].get('red_cards',0)})
- أهم أحداث الدقائق: {' | '.join(evs_short) if evs_short else 'لا توجد أحداث مسجلة بعد'}
- أعلى لاعب تقييماً في اللقاء: {dossier['mvp_player']['name'] + ' (' + str(dossier['mvp_player']['rating']) + ')' if dossier.get('mvp_player') else 'غير متاح بعد'}"""

            prompt = f"""أنت مخرج الاستوديو التحليلي لقنوات رياضية كبرى (بأسلوب استوديو beIN Sports الجاد والعميق).
أمامك ورقة الحقائق الرسمية للمباراة:
{facts_sheet}

المطلوب صياغة مداخلات 4 محللين متخصصين بصيغة JSON فقط (دون أي نص خارج JSON) مع الالتزام الصارم بالأرقام والأسماء الموجودة في ورقة الحقائق فقط:
{{
  "headline": "عنوان رئيسي قوي للاستوديو",
  "key_battle": "المعركة التكتيكية الأهم أو رجل المباراة",
  "tactician": "تحليل د. طارق التكتيكي (3 جمل عميقة عن الخطط والأسماء والمساحات)",
  "data_analyst": "تحليل م. سامر الرقمي (3 جمل دقيقة بالأرقام الفعلية من ورقة الحقائق)",
  "momentum_star": "تحليل كابتن رياض الحسم (3 جمل عن الزخم والنجوم والتبديلات والحسم)",
  "moderator_ref": "تحليل المستشار جمال التحكيمي (3 جمل عن إدارة اللقاء، الانضباط، البطاقات، أو الفار)",
  "debate_topic": "عنوان قضية نقاش تكتيكي بين المحللين في هذه المباراة",
  "debate_summary": "ملخص اختلاف الرأي الفني بين المحللين في سطرين بناءً على معطيات المباراة"
}}"""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=6.5, context=SSL_CONTEXT) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                raw_txt = body["candidates"][0]["content"]["parts"][0]["text"].strip()
                raw_txt = re.sub(r"^```json\s*|\s*```$", "", raw_txt, flags=re.MULTILINE).strip()
                ai_json = json.loads(raw_txt)

                if isinstance(ai_json, dict):
                    if ai_json.get("headline"):
                        base_studio["headline"] = ai_json["headline"]
                    if ai_json.get("key_battle"):
                        base_studio["key_battle"] = ai_json["key_battle"]
                    role_map = {
                        "tactician": ai_json.get("tactician"),
                        "data_analyst": ai_json.get("data_analyst"),
                        "momentum_star": ai_json.get("momentum_star"),
                        "moderator_ref": ai_json.get("moderator_ref")
                    }
                    for p_obj in base_studio["pundits"]:
                        if role_map.get(p_obj["id"]):
                            p_obj["analysis"] = role_map[p_obj["id"]]
                    if ai_json.get("debate_topic") and ai_json.get("debate_summary"):
                        base_studio["debate"] = {
                            "topic": ai_json["debate_topic"],
                            "summary": ai_json["debate_summary"]
                        }
        except Exception as e:
            print(f"⚠️ [AI Studio Gemini Fallback]: {e}")

    save_to_cache(cache_key, base_studio)
    return base_studio


def ask_studio_pundit_question(league_code: str, match_id: str, pundit_id: str, question: str):
    """الرد المباشر من أحد المحللين الأربعة على سؤال المستخدم بالاعتماد على الأرقام الحقيقية للمباراة"""
    dossier = _collect_real_match_dossier(league_code, match_id)
    pundit_Meta = {
        "tactician": ("د. طارق التكتيكي", "محلل الخطط والتكتيك"),
        "data_analyst": ("م. سامر الرقمي", "خبير الإحصائيات ولغة الأرقام"),
        "momentum_star": ("كابتن رياض الحسم", "محلل الزخم والأداء الفردي"),
        "moderator_ref": ("المستشار جمال التحكيمي", "مدير الاستوديو وخبير التحكيم")
    }
    p_name, p_role = pundit_Meta.get(pundit_id, pundit_Meta["tactician"])

    st = dossier["stats"]
    h_st = dossier["home_standing"]
    a_st = dossier["away_standing"]
    h, a = dossier["home_team"], dossier["away_team"]

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key.startswith("AIza"):
        try:
            prompt = f"""أنت ({p_name} - {p_role}) في الاستوديو التحليلي لمباراة {h} ضد {a}.
سؤال المشاهد لك: "{question}"
بيانات المباراة الحقيقية أمامك (التزم بها حرفياً ولا تختلق أي رقم خارجها):
- الحالة: {dossier['state']} | النتيجة: {h} {dossier['home_score']} - {dossier['away_score']} {a}
- الترتيب: {h} المركز #{h_st.get('rank','-')} ({h_st.get('points',0)} نقطة) | {a} المركز #{a_st.get('rank','-')} ({a_st.get('points',0)} نقطة)
- الخطط: {h} ({dossier['home_formation']}) ضد {a} ({dossier['away_formation']})
- الإحصائيات: استحواذ ({st['home'].get('possession',0)}% - {st['away'].get('possession',0)}%)، تسديد على المرمى ({st['home'].get('shots_on_target',0)} - {st['away'].get('shots_on_target',0)})، ركنيات ({st['home'].get('corners',0)} - {st['away'].get('corners',0)})
- مسجلو الأهداف: {st.get('home_goals',[]) + st.get('away_goals',[])}
أجب بأسلوبك التخصصي الجاد في سطرين إلى 3 أسطر فقط."""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5.5, context=SSL_CONTEXT) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                ans = body["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {"pundit_name": p_name, "pundit_role": p_role, "reply": ans}
        except Exception:
            pass

    # رد رقمي واقعي فوري من بيانات اللقاء الحقيقية في حال عدم توفر المفتاح
    if dossier["state"] == "pre":
        fallback_reply = (
            f"بناءً على معطيات ما قبل اللقاء، {h} (المركز #{h_st.get('rank','-')} بـ {h_st.get('points',0)} نقطة وخطة {dossier['home_formation']}) "
            f"يواجه {a} (المركز #{a_st.get('rank','-')} بـ {a_st.get('points',0)} نقطة وخطة {dossier['away_formation']}). "
            f"الفارق سيتحدد في معركة وسط الملعب واستغلال الفرص الأولى."
        )
    else:
        fallback_reply = (
            f"بلغة أرقام اللقاء الحالية ({h} {dossier['home_score']} - {dossier['away_score']} {a})، "
            f"الاستحواذ يبلغ {st['home'].get('possession',50)}% مقابل {st['away'].get('possession',50)}%، "
            f"والتسديد المؤطر على المرمى {st['home'].get('shots_on_target',0)} مقابل {st['away'].get('shots_on_target',0)}؛ "
            f"وهو ما يوضح أن الحسم يرتبط بدقة اللمسة الأخيرة في منطقة الجزاء."
        )

    return {"pundit_name": p_name, "pundit_role": p_role, "reply": fallback_reply}


# =========================================================================
# 19. محرك البطاقات التفاعلي الحي (100% Live APIs: ESPN + Transfermarkt Official Tables)
#     دقة 100% في استخراج الألقاب الحقيقية والهداف التاريخي والأكثر مشاركة وصناعة
# =========================================================================

# =========================================================================
# 19. محرك البطاقات التفاعلي الحي (100% Live External APIs: ESPN + Transfermarkt + Wikipedia)
#     - سحب منتخبات القارات الـ 5 الحقيقية فقط (بدون أي نادي)
#     - سحب تصنيف الفيفا العالمي الحي ونقاطه بدقة 100%
#     - سحب خزانة الألقاب والبطولات والأساطير حياً من Transfermarkt + Wikipedia API
# =========================================================================

# روابط المنتخبات الوطنية الحصرية في ESPN (تم استبدال afc.cup الخاص بالأندية بـ afc.asian.cup للمنتخبات)
ESPN_CONTINENT_ENDPOINTS = [
    ("europe", "UEFA", "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.nations/teams?limit=100"),
    ("europe", "UEFA", "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq.uefa/teams?limit=100"),
    ("europe", "UEFA", "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.euro/teams?limit=100"),
    ("south_america", "CONMEBOL", "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq.conmebol/teams?limit=40"),
    ("south_america", "CONMEBOL", "https://site.api.espn.com/apis/site/v2/sports/soccer/conmebol.america/teams?limit=40"),
    ("africa", "CAF", "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq.caf/teams?limit=100"),
    ("africa", "CAF", "https://site.api.espn.com/apis/site/v2/sports/soccer/caf.nations/teams?limit=100"),
    ("asia", "AFC", "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq.afc/teams?limit=100"),
    ("asia", "AFC", "https://site.api.espn.com/apis/site/v2/sports/soccer/afc.asian.cup/teams?limit=100"),
    ("north_america", "CONCACAF", "https://site.api.espn.com/apis/site/v2/sports/soccer/concacaf.nations.league/teams?limit=100"),
    ("north_america", "CONCACAF", "https://site.api.espn.com/apis/site/v2/sports/soccer/concacaf.gold/teams?limit=100"),
    ("north_america", "CONCACAF", "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq.concacaf/teams?limit=100"),
    ("north_america", "OFC", "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.worldq.ofc/teams?limit=40")
]

_TM_NATION_ID_MAP = {}
_CARDS_LEGACY_PURGED = False


def _purge_legacy_cards_cache_once():
    """مسح الكاش القديم المعطوب للبطاقات وتصنيف الفيفا تلقائياً عند التشغيل"""
    global _CARDS_LEGACY_PURGED
    if _CARDS_LEGACY_PURGED:
        return
    _CARDS_LEGACY_PURGED = True
    try:
        stale_prefixes = (
            "espn_wiki_world_nations_v10",
            "wiki_fifa_ranking_map_v10",
            "tm_exact_modal_v12",
            "world_nations_live_api_v20",
            "entity_dossier_live_v20",
        )
        stale_keys = [
            k for k in list(_RAM_CACHE.keys())
            if any(p in k for p in stale_prefixes)
        ]
        for k in stale_keys:
            _RAM_CACHE.pop(k, None)
        with _DB_LOCK:
            conn = get_connection()
            conn.execute(
                "DELETE FROM api_cache WHERE cache_key LIKE 'espn_wiki_world_nations_v10%' "
                "OR cache_key LIKE 'wiki_fifa_ranking_map_v10%' "
                "OR cache_key LIKE 'tm_exact_modal_v12%' "
                "OR cache_key LIKE 'world_nations_live_api_v20%' "
                "OR cache_key LIKE 'entity_dossier_live_v20%';"
            )
            conn.commit()
            conn.close()
    except Exception:
        pass

def _is_valid_national_team(name_str: str) -> bool:
    """فلتر صارم يمنع دخول أي نادٍ رياضي إلى قائمة المنتخبات الوطنية"""
    if not name_str:
        return False
    s = str(name_str).strip()
    low = s.lower()

    # الكلمات الدالة على الأندية (تُرفض فوراً)
    club_indicators = (
        " fc", "fc ", " sc", "sc ", " cf", "cf ", " ac", "ac ", " club", "united", "city",
        "athletic", "sporting", "wanderers", "rovers", "marinos", "steelers", "antlers",
        "diamonds", "motors", "al-hilal", "al hilal", "al-nassr", "al nassr", "al-ahli",
        "al ahli", "al-ittihad", "al ittihad", "al-sadd", "al sadd", "al-ain", "al ain",
        "al-duhail", "al duhail", "al-rayyan", "al rayyan", "al-gharafa", "al gharafa",
        "al-wasl", "al wasl", "al-wahda", "al wahda", "al-jazira", "al jazira", "shabab",
        "sharjah", "pakhtakor", "persepolis", "esteghlal", "sepahan", "tractor", "ulsan",
        "jeonbuk", "pohang", "yokohama", "kawasaki", "urawa", "vissel", "gamba", "kashima",
        "hiroshima", "shanghai", "shandong", "beijing", "buriram", "johor", "mohun",
        "east bengal", "mumbai", "bengaluru", "odisha", "al-ahed", "al ahed", "al-kuwait",
        "al-riffa", "al riffa", "al-muharraq", "al-khaldiya", "al-seeb", "al-nahda",
        "al-wehdat", "al wehdat", "al-faisaly", "al-hussein", "al-shorta", "al-zawraa",
        "air force", "arkadag", "ahal", "istiklol", "nasaf", "navbahor", "neftchi",
        "bunyodkor", "maziya", "bashundhara", "abahani", "kitchee", "lee man", "tai po",
        "lion city", "tampines", "selangor", "persib", "bali united", "hanoi", "nam dinh",
        "kaya", "macarthur", "central coast", "sydney", "melbourne", "brisbane", "adelaide",
        "perth", "wellington", "auckland", "zamalek", "pyramids", "wydad", "raja", "berkane",
        "esperance", "espérance", "sundowns", "orlando", "kaizer", "belouizdad", "mc alger",
        "kabylie", "setif", "etoile", "real ", "inter ", "bayern", "borussia", "juventus"
    )
    if any(tok in f" {low} " or low.startswith(tok.strip() + " ") or low.endswith(" " + tok.strip()) for tok in club_indicators):
        if low not in ("united states", "united arab emirates"):
            return False
    return True


def _translate_batch_to_arabic_live(en_names_list):
    """ترجمة أسماء المنتخبات والمصطلحات إلى العربية حياً عبر Wikipedia Langlinks API + Google Translate API"""
    if not en_names_list:
        return {}

    clean_list = []
    for n in en_names_list:
        s = re.sub(r'\s+', ' ', str(n or "")).strip()
        if s and s not in clean_list:
            clean_list.append(s)

    cache_key = "live_ar_trans_map_v20_" + hashlib.md5("|".join(sorted(clean_list)).encode()).hexdigest()[:10]
    cached, is_fresh = get_from_cache(cache_key, ttl=86400 * 14)
    if cached and is_fresh:
        return cached

    result_map = {}

    # 1. Google Translate Live API (سريع جداً ويترجم دفعة كاملة في طلب واحد)
    for i in range(0, len(clean_list), 45):
        chunk = clean_list[i:i + 45]
        joined_q = "\n".join(chunk)
        gt_url = (
            "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ar&dt=t&q="
            + urllib.parse.quote(joined_q)
        )
        try:
            req = urllib.request.Request(gt_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=4.0, context=SSL_CONTEXT) as resp:
                gt_json = json.loads(resp.read().decode("utf-8", errors="ignore"))
                if isinstance(gt_json, list) and isinstance(gt_json[0], list):
                    translated_full = "".join(seg[0] for seg in gt_json[0] if seg and seg[0])
                    ar_lines = [ln.strip() for ln in translated_full.split("\n")]
                    if len(ar_lines) == len(chunk):
                        for en_item, ar_item in zip(chunk, ar_lines):
                            # تنظيف بعض الأسماء المركبة
                            ar_clean = ar_item.replace("جمهورية ", "").strip()
                            if en_item.lower() in ("turkey", "türkiye"):
                                ar_clean = "تركيا"
                            elif en_item.lower() == "georgia":
                                ar_clean = "جورجيا"
                            elif en_item.lower() == "jordan":
                                ar_clean = "الأردن"
                            result_map[en_item.lower()] = ar_clean
        except Exception:
            pass

    if result_map:
        save_to_cache(cache_key, result_map)
    return result_map


def _convert_height_to_cm(raw_h):
    if not raw_h:
        return "180 سم"
    s = str(raw_h).strip()
    m_cm = re.search(r'(\d{3})\s*cm', s, re.IGNORECASE)
    if m_cm:
        return f"{m_cm.group(1)} سم"
    m_meter = re.search(r'(\d\.\d{1,2})\s*m', s, re.IGNORECASE)
    if m_meter:
        return f"{int(float(m_meter.group(1)) * 100)} سم"
    m_ft = re.search(r"(\d+)\s*['’]\s*(\d+)?", s)
    if m_ft:
        ft = int(m_ft.group(1))
        inc = int(m_ft.group(2)) if m_ft.group(2) else 0
        cm = int(round((ft * 30.48) + (inc * 2.54)))
        return f"{cm} سم"
    return s


def _convert_weight_to_kg(raw_w):
    if not raw_w:
        return "74 كغ"
    s = str(raw_w).strip()
    m_kg = re.search(r'(\d{2,3})\s*kg', s, re.IGNORECASE)
    if m_kg:
        return f"{m_kg.group(1)} كغ"
    m_lbs = re.search(r'(\d{2,3})\s*(?:lbs|lb)', s, re.IGNORECASE)
    if m_lbs:
        lbs = int(m_lbs.group(1))
        kg = int(round(lbs * 0.453592))
        return f"{kg} كغ"
    return s


FIFA_NATION_NAME_ALIASES = {
    "usa": "united states",
    "u.s.a.": "united states",
    "south korea": "korea republic",
    "korea republic": "south korea",
    "ir iran": "iran",
    "iran": "ir iran",
    "ivory coast": "côte d'ivoire",
    "côte d'ivoire": "ivory coast",
    "cote d'ivoire": "ivory coast",
    "turkey": "türkiye",
    "türkiye": "turkey",
    "turkiye": "turkey",
    "czechia": "czech republic",
    "czech republic": "czechia",
    "cape verde": "cabo verde",
    "cabo verde": "cape verde",
    "dr congo": "congo dr",
    "congo dr": "dr congo",
    "republic of ireland": "ireland",
    "ireland": "republic of ireland",
    "china pr": "china",
    "china": "china pr",
    "uae": "united arab emirates",
    "united arab emirates": "uae",
    "bosnia-herzegovina": "bosnia and herzegovina",
    "bosnia and herzegovina": "bosnia-herzegovina",
    "kyrgyz republic": "kyrgyzstan",
    "kyrgyzstan": "kyrgyz republic",
    "north korea": "korea dpr",
    "korea dpr": "north korea",
    "trinidad & tobago": "trinidad and tobago",
    "antigua & barbuda": "antigua and barbuda",
    "st kitts and nevis": "st. kitts and nevis",
    "st lucia": "st. lucia",
    "st vincent and the grenadines": "st. vincent / grenadines",
    "curacao": "curaçao",
    "sao tome and principe": "são tomé and príncipe",
}

CONFED_TO_CONTINENT = {
    "UEFA": "europe",
    "CONMEBOL": "south_america",
    "CAF": "africa",
    "AFC": "asia",
    "CONCACAF": "north_america",
    "OFC": "north_america",
}


def _fetch_official_fifa_api_rankings():
    """المصدر الأول والأدق: سحب جدول تصنيف الفيفا الرسمي الحي (210 منتخب) مباشرة من FIFA API"""
    fifa_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://inside.fifa.com/fifa-world-ranking/men",
    }

    def _get_raw(url, timeout=6.0):
        req = urllib.request.Request(url, headers=fifa_headers)
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
            raw = resp.read()
            if resp.info().get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                try:
                    raw = gzip.decompress(raw)
                except Exception:
                    pass
            return raw.decode("utf-8", errors="ignore")

    def _parse_rankings_array(arr):
        out = []
        for entry in (arr or []):
            if not isinstance(entry, dict):
                continue
            ri = entry.get("rankingItem") if isinstance(entry.get("rankingItem"), dict) else entry
            rk = safe_num(ri.get("rank"), 0)
            name = str(ri.get("name") or "").strip()
            code = str(ri.get("countryCode") or "").strip().upper()
            pts = ri.get("totalPoints")
            if rk <= 0 or not name:
                continue
            tag = entry.get("tag") if isinstance(entry.get("tag"), dict) else {}
            confed = str(tag.get("id") or tag.get("text") or ri.get("confederation") or "").strip().upper()
            flag_obj = ri.get("flag") if isinstance(ri.get("flag"), dict) else {}
            flag_url = str(flag_obj.get("src") or "").strip()
            if not flag_url and code:
                flag_url = f"https://api.fifa.com/api/v3/picture/flags-sq-2/{code}"
            out.append({
                "rank": rk,
                "raw_name": name,
                "abbr": code or name[:3].upper(),
                "fifa_points": f"{float(pts):.2f}" if pts not in (None, "") else "",
                "confederation": confed if confed in CONFED_TO_CONTINENT else "",
                "continent_key": CONFED_TO_CONTINENT.get(confed, ""),
                "flag_url": flag_url,
            })
        return out

    # 1. استخراج أحدث dateId من صفحة FIFA الرسمية ثم جلب كامل الجدول (210 منتخب) في طلب JSON واحد
    try:
        page_html = _get_raw("https://inside.fifa.com/fifa-world-ranking/men", timeout=6.0)
        m_nd = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', page_html, re.DOTALL)
        latest_date_id = ""
        fallback_items = []
        if m_nd:
            nd_json = json.loads(m_nd.group(1))
            nd_str = m_nd.group(1)
            m_did = re.search(r'"id"\s*:\s*"(id\d{4,6})"', nd_str)
            if m_did:
                latest_date_id = m_did.group(1)
            # استخراج أي مصفوفة rankings مضمنة كاحتياط
            def _find_rankings(obj):
                if isinstance(obj, dict):
                    if isinstance(obj.get("rankings"), list) and len(obj["rankings"]) >= 20:
                        return obj["rankings"]
                    for v in obj.values():
                        res = _find_rankings(v)
                        if res:
                            return res
                elif isinstance(obj, list):
                    for it in obj:
                        res = _find_rankings(it)
                        if res:
                            return res
                return None
            embedded = _find_rankings(nd_json)
            if embedded:
                fallback_items = _parse_rankings_array(embedded)

        if latest_date_id:
            api_txt = _get_raw(f"https://inside.fifa.com/api/ranking-overview?locale=en&dateId={latest_date_id}", timeout=6.0)
            api_json = json.loads(api_txt)
            full_items = _parse_rankings_array(api_json.get("rankings"))
            if len(full_items) >= 100:
                return full_items
        if len(fallback_items) >= 20:
            return fallback_items
    except Exception:
        pass

    # 2. محاولة مباشرة لواجهة FIFA API
    try:
        api_txt = _get_raw("https://inside.fifa.com/api/ranking-overview?locale=en&rankingType=football", timeout=5.0)
        api_json = json.loads(api_txt)
        full_items = _parse_rankings_array(api_json.get("rankings"))
        if len(full_items) >= 50:
            return full_items
    except Exception:
        pass

    return []


def _scrape_live_tm_fifa_world_ranking():
    """المصدر الثانوي: سحب جدول تصنيف الفيفا الرسمي الحي من Transfermarkt (مع إصلاح قراءة النقاط والروابط)"""
    def fetch_ranking_page(page_num):
        url = f"https://www.transfermarkt.com/statistik/weltrangliste?page={page_num}"
        html_doc = _fetch_html_gzip(url, timeout=6.0)
        rows = _split_tm_outer_rows(html_doc)
        page_items = []
        for r_html in rows:
            try:
                tm_slug, tm_vid, raw_name = "", "", ""
                for m_link in re.finditer(r'<a[^>]+href="/([^/"]+)/startseite/verein/(\d+)[^"]*"[^>]*>(.*?)</a>', r_html, re.DOTALL):
                    txt = html.unescape(re.sub(r'<[^>]+>', '', m_link.group(3))).strip()
                    if not txt:
                        t_attr = re.search(r'title="([^"]+)"', m_link.group(0))
                        txt = html.unescape(t_attr.group(1)).strip() if t_attr else ""
                    if txt and not txt.isdigit():
                        tm_slug, tm_vid, raw_name = m_link.group(1), m_link.group(2), txt
                        break
                if not raw_name:
                    continue

                _TM_NATION_ID_MAP[raw_name.lower()] = (tm_slug, tm_vid)

                cells = [
                    html.unescape(re.sub(r'<[^>]+>', ' ', c)).strip()
                    for c in re.findall(r'<td[^>]*class="[^"]*(?:zentriert|rechts)[^"]*"[^>]*>(.*?)</td>', r_html, re.DOTALL)
                ]
                rank_num = 0
                for c_txt in cells:
                    m_rk = re.match(r'^(\d{1,3})\b', c_txt)
                    if m_rk and 1 <= int(m_rk.group(1)) <= 211:
                        rank_num = int(m_rk.group(1))
                        break

                confed = ""
                for c_txt in cells:
                    c_up = c_txt.upper().strip()
                    if c_up in CONFED_TO_CONTINENT:
                        confed = c_up
                        break

                # إصلاح قراءة نقاط الفيفا (تأتي بصيغة 1,867 أو 1.867 أو 1867.25)
                pts_str = ""
                for c_txt in reversed(cells):
                    c_raw = c_txt.strip()
                    if re.match(r'^\d{1,2}[,\.]\d{3}(?:[,\.]\d+)?$', c_raw):
                        # فاصل آلاف مثل 1,867 أو 1.867
                        parts = re.split(r'[,\.]', c_raw)
                        num_str = parts[0] + parts[1] + (("." + parts[2]) if len(parts) > 2 else "")
                        if float(num_str) >= 600:
                            pts_str = num_str
                            break
                    elif re.match(r'^\d{3,4}(?:\.\d+)?$', c_raw) and float(c_raw) >= 600:
                        pts_str = c_raw
                        break

                flag_url = ""
                m_flag = re.search(r'<img[^>]+src="([^"]+/flagge/[^"]+)"', r_html)
                if m_flag:
                    flag_url = re.sub(r'/(?:tiny|verysmall|small)/', '/head/', m_flag.group(1))

                if rank_num > 0:
                    page_items.append({
                        "rank": rank_num,
                        "raw_name": raw_name,
                        "tm_slug": tm_slug,
                        "tm_id": tm_vid,
                        "confederation": confed,
                        "continent_key": CONFED_TO_CONTINENT.get(confed, ""),
                        "fifa_points": pts_str,
                        "flag_url": flag_url,
                    })
            except Exception:
                continue
        return page_items

    all_ranked = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(fetch_ranking_page, range(1, 9)):
            all_ranked.extend(res or [])
    return all_ranked


def _fetch_wiki_fifa_rankings_live_html():
    """المصدر المضمون: سحب تصنيف الفيفا الرسمي الحي (210 منتخب) من وحدة بيانات ويكيبيديا + جدول صفحة FIFA"""
    ranks_map = {}

    # 1. قراءة وحدة بيانات ويكيبيديا الرسمية لتصنيف الفيفا (تضم جميع الـ 210 منتخباً برموزهم وأرقامهم الرسمية)
    module_candidates = [
        "Module:Sports_rank_table/data/FIFA_World_Rankings",
        "Module:Sports_rank_table/data/FIFA_Men's_World_Ranking",
        "Template:FIFA_World_Rankings",
    ]
    try:
        titles_param = "|".join(module_candidates)
        q_url = (
            "https://en.wikipedia.org/w/api.php?action=query&titles="
            + urllib.parse.quote(titles_param)
            + "&prop=revisions&rvslots=main&rvprop=content&format=json&redirects=1"
        )
        q_data = fetch_wiki_api_json(q_url, timeout=6.0)
        pages = (q_data.get("query") or {}).get("pages") if isinstance(q_data, dict) else {}

        lua_blobs = []
        extra_modules = []
        for p_obj in (pages or {}).values():
            revs = p_obj.get("revisions") or []
            if not revs:
                continue
            content = ((revs[0].get("slots") or {}).get("main") or {}).get("*") or revs[0].get("*") or ""
            if not content:
                continue
            lua_blobs.append(content)
            # إذا كان القالب يستدعي وحدة بيانات أخرى نقرأ اسمها تلقائياً
            for m_mod in re.finditer(r'(Module:[^|}\]\n]+)', content):
                mod_name = m_mod.group(1).strip()
                if "fifa" in mod_name.lower() or "rank" in mod_name.lower():
                    extra_modules.append(mod_name)

        if extra_modules and not any("ARG" in b and "ESP" in b for b in lua_blobs):
            ex_url = (
                "https://en.wikipedia.org/w/api.php?action=query&titles="
                + urllib.parse.quote("|".join(extra_modules[:3]))
                + "&prop=revisions&rvslots=main&rvprop=content&format=json&redirects=1"
            )
            ex_data = fetch_wiki_api_json(ex_url, timeout=5.0)
            for p_obj in ((ex_data or {}).get("query") or {}).get("pages", {}).values():
                revs = p_obj.get("revisions") or []
                if revs:
                    c2 = ((revs[0].get("slots") or {}).get("main") or {}).get("*") or revs[0].get("*") or ""
                    if c2:
                        lua_blobs.append(c2)

        for blob in lua_blobs:
            # صيغة Lua الشائعة: { "ARG", 1, 0, 1867.25 } أو ["ARG"] = { 1, 0, 1867.25 }
            for m in re.finditer(
                r'["\']([A-Z]{3})["\']\s*(?:,|\]\s*=\s*\{)\s*(\d{1,3})\s*,\s*[-+\d]+\s*(?:,\s*([\d\.]+))?',
                blob
            ):
                code_k = m.group(1).lower()
                rk_v = int(m.group(2))
                pts_v = m.group(3) or ""
                if 1 <= rk_v <= 211:
                    ranks_map[code_k] = {"rank": rk_v, "points": pts_v}

            # صيغة switch في القوالب: | ARG = 1 | GER = 10
            for m in re.finditer(r'\|\s*([A-Z]{3}|[A-Za-z][A-Za-z\s\'\-\.]{2,30})\s*=\s*(\d{1,3})\b', blob):
                key_k = m.group(1).strip().lower()
                rk_v = int(m.group(2))
                if 1 <= rk_v <= 211 and key_k not in ranks_map:
                    ranks_map[key_k] = {"rank": rk_v, "points": ""}
    except Exception:
        pass

    # 2. قراءة جدول FIFA_Men's_World_Ranking (مع إصلاح البحث في الصفوف 0..3 عن رؤوس الأعمدة)
    try:
        url = "https://en.wikipedia.org/w/api.php?action=parse&page=FIFA_Men%27s_World_Ranking&prop=text&format=json&redirects=1"
        data = fetch_wiki_api_json(url, timeout=6.0)
        if isinstance(data, dict) and "parse" in data:
            html_content = data["parse"].get("text", {}).get("*", "")
            parser = _WikiTableParser()
            parser.feed(html_content)

            for raw_table in parser.tables:
                grid = _expand_table_grid(raw_table)
                if len(grid) < 5:
                    continue
                header_idx, rk_col, tm_col, pt_col = -1, -1, -1, -1
                for r_i in range(min(4, len(grid))):
                    hdrs = [c["text"].lower() for c in grid[r_i]]
                    r_c = next((i for i, h in enumerate(hdrs) if "rank" in h or "pos" in h), -1)
                    t_c = next((i for i, h in enumerate(hdrs) if "team" in h or "nation" in h or "country" in h), -1)
                    p_c = next((i for i, h in enumerate(hdrs) if "point" in h or "pts" in h), -1)
                    if r_c != -1 and t_c != -1:
                        header_idx, rk_col, tm_col, pt_col = r_i, r_c, t_c, p_c
                        break
                if header_idx == -1:
                    continue

                for r in grid[header_idx + 1:]:
                    if len(r) <= max(rk_col, tm_col):
                        continue
                    rk_m = re.search(r'\b(\d{1,3})\b', r[rk_col]["text"])
                    if not rk_m:
                        continue
                    rk_val = int(rk_m.group(1))
                    if not (1 <= rk_val <= 211):
                        continue
                    t_name = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', r[tm_col]["text"]).strip()
                    if not t_name or len(t_name) < 2:
                        continue
                    pts_val = ""
                    if 0 <= pt_col < len(r):
                        pm = re.search(r'\d{3,4}(?:\.\d+)?', r[pt_col]["text"].replace(",", ""))
                        if pm:
                            pts_val = pm.group(0)
                    ranks_map[t_name.lower()] = {"rank": rk_val, "points": pts_val}
    except Exception:
        pass

    return ranks_map


def _lookup_official_fifa_info(en_name: str, abbr: str, lookup_map: dict):
    """مطابقة دقيقة لاسم المنتخب أو رمزه الدولي في جداول الفيفا الرسمية"""
    if not lookup_map:
        return None
    low = (en_name or "").strip().lower()
    ab_low = (abbr or "").strip().lower()
    candidates = [low]
    if low in FIFA_NATION_NAME_ALIASES:
        candidates.append(FIFA_NATION_NAME_ALIASES[low])
    if ab_low and len(ab_low) == 3:
        candidates.append(ab_low)

    for c in candidates:
        if c in lookup_map:
            return lookup_map[c]
    return None


def get_live_top_100_nations_cards(force_refresh: bool = False):
    """جلب منتخبات القارات الـ 5 الحقيقية مع تصنيف الفيفا الرسمي الصحيح مرتبة من الأقوى للأضعف"""
    _purge_legacy_cards_cache_once()
    cache_key = "world_nations_live_api_v21"
    cached, is_fresh = get_from_cache(cache_key, ttl=86400)
    if cached and is_fresh and not force_refresh and len(cached) >= 60:
        for item in cached:
            if item.get("tm_id") and item.get("raw_name"):
                _TM_NATION_ID_MAP[item["raw_name"].lower()] = (item.get("tm_slug", ""), item["tm_id"])
        return cached

    def fetch_espn_continent_batch(ep_tuple):
        cont_key, confed, url = ep_tuple
        data = fetch_json_fast(url, timeout=4.5)
        items_out = []
        if not isinstance(data, dict):
            return items_out
        try:
            raw_teams = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
            for t_wrap in raw_teams:
                t_obj = t_wrap.get("team") or {}
                tid = str(t_obj.get("id") or "")
                en_name = (t_obj.get("displayName") or t_obj.get("name") or "").strip()
                abbr = (t_obj.get("abbreviation") or "").upper()
                logos = t_obj.get("logos") or []
                flag_href = logos[0].get("href", "") if (logos and isinstance(logos[0], dict)) else ""
                if en_name and _is_valid_national_team(en_name):
                    items_out.append({
                        "team_id": tid,
                        "raw_name": en_name,
                        "abbr": abbr,
                        "flag_url": flag_href,
                        "continent_key": cont_key,
                        "confederation": confed,
                    })
        except Exception:
            pass
        return items_out

    with ThreadPoolExecutor(max_workers=12) as ex:
        fut_fifa_api = ex.submit(_fetch_official_fifa_api_rankings)
        fut_tm_ranks = ex.submit(_scrape_live_tm_fifa_world_ranking)
        fut_wiki_ranks = ex.submit(_fetch_wiki_fifa_rankings_live_html)
        ep_futures = [ex.submit(fetch_espn_continent_batch, ep) for ep in ESPN_CONTINENT_ENDPOINTS]

        fifa_api_list = fut_fifa_api.result() or []
        tm_ranked_list = fut_tm_ranks.result() or []
        wiki_ranks_map = fut_wiki_ranks.result() or {}
        espn_nations = []
        for f in ep_futures:
            espn_nations.extend(f.result() or [])

    # فهرسة بيانات ESPN (الأعلام + القارة الصحيحة + الرمز الدولي)
    espn_by_key = {}
    for ep_item in espn_nations:
        k_name = ep_item["raw_name"].lower()
        k_abbr = (ep_item.get("abbr") or "").lower()
        if k_name not in espn_by_key or (ep_item["flag_url"] and not espn_by_key[k_name]["flag_url"]):
            espn_by_key[k_name] = ep_item
        if k_name in FIFA_NATION_NAME_ALIASES:
            espn_by_key.setdefault(FIFA_NATION_NAME_ALIASES[k_name], ep_item)
        if k_abbr and len(k_abbr) == 3:
            espn_by_key.setdefault(k_abbr, ep_item)

    # بناء قاموس موحّد للتصنيف الرسمي من المصادر الثلاثة (FIFA API > Transfermarkt > Wikipedia Module)
    unified_rank_lookup = dict(wiki_ranks_map)
    for tm_item in tm_ranked_list:
        k_n = tm_item["raw_name"].lower()
        unified_rank_lookup[k_n] = {
            "rank": tm_item["rank"],
            "points": tm_item.get("fifa_points", ""),
            "confederation": tm_item.get("confederation", ""),
            "continent_key": tm_item.get("continent_key", ""),
            "tm_slug": tm_item.get("tm_slug", ""),
            "tm_id": tm_item.get("tm_id", ""),
        }
    for fa_item in fifa_api_list:
        rec = {
            "rank": fa_item["rank"],
            "points": fa_item.get("fifa_points", ""),
            "confederation": fa_item.get("confederation", ""),
            "continent_key": fa_item.get("continent_key", ""),
            "flag_url": fa_item.get("flag_url", ""),
        }
        unified_rank_lookup[fa_item["raw_name"].lower()] = rec
        if fa_item.get("abbr"):
            unified_rank_lookup[fa_item["abbr"].lower()] = rec

    merged_raw = []
    seen_names = set()

    # 1. الأولوية الأولى: قائمة FIFA API الرسمية الكاملة (تضم 210 منتخب بتصنيفهم الرسمي الدقيق)
    primary_ranked_source = fifa_api_list if len(fifa_api_list) >= 50 else tm_ranked_list
    for src_item in primary_ranked_source:
        en_n = src_item["raw_name"]
        en_low = en_n.lower()
        abbr_u = (src_item.get("abbr") or "").upper()
        if not _is_valid_national_team(en_n) or en_low in seen_names:
            continue

        espn_match = espn_by_key.get(en_low) or espn_by_key.get(FIFA_NATION_NAME_ALIASES.get(en_low, "")) or espn_by_key.get(abbr_u.lower()) or {}
        cont_key = src_item.get("continent_key") or espn_match.get("continent_key") or ""
        confed = src_item.get("confederation") or espn_match.get("confederation") or ""
        if not cont_key:
            continue

        seen_names.add(en_low)
        if espn_match.get("raw_name"):
            seen_names.add(espn_match["raw_name"].lower())

        merged_raw.append({
            "team_id": espn_match.get("team_id") or src_item.get("tm_id") or abbr_u,
            "tm_slug": src_item.get("tm_slug", ""),
            "tm_id": src_item.get("tm_id", ""),
            "raw_name": en_n,
            "abbr": abbr_u or espn_match.get("abbr") or en_n[:3].upper(),
            "flag_url": espn_match.get("flag_url") or src_item.get("flag_url") or "",
            "continent_key": cont_key,
            "confederation": confed or "FIFA",
            "rank": int(src_item["rank"]),
            "fifa_points": src_item.get("fifa_points") or "-",
        })

    # 2. إضافة منتخبات ESPN غير المدرجة بعد ومطابقة تصنيفها الرسمي من قاموس FIFA/Wikipedia (بدون أي تصنيف وهمي)
    for ep_item in espn_nations:
        en_n = ep_item["raw_name"]
        en_low = en_n.lower()
        alias_low = FIFA_NATION_NAME_ALIASES.get(en_low, "")
        if en_low in seen_names or (alias_low and alias_low in seen_names) or not _is_valid_national_team(en_n):
            continue

        official = _lookup_official_fifa_info(en_n, ep_item.get("abbr", ""), unified_rank_lookup)
        if not official:
            continue  # لا نضيف أي منتخب بتصنيف وهمي أو مختلق

        seen_names.add(en_low)
        merged_raw.append({
            "team_id": ep_item["team_id"],
            "tm_slug": official.get("tm_slug", ""),
            "tm_id": official.get("tm_id", ""),
            "raw_name": en_n,
            "abbr": ep_item["abbr"],
            "flag_url": ep_item["flag_url"] or official.get("flag_url", ""),
            "continent_key": ep_item["continent_key"],
            "confederation": ep_item["confederation"],
            "rank": int(official["rank"]),
            "fifa_points": official.get("points") or "-",
        })

    all_en_names = [x["raw_name"] for x in merged_raw]
    ar_trans_map = _translate_batch_to_arabic_live(all_en_names)

    nations = []
    for item in merged_raw:
        en_n = item["raw_name"]
        en_low = en_n.lower()

        if en_low in ARABIC_MATCH_TEAM_ALIASES:
            ar_name = ARABIC_MATCH_TEAM_ALIASES[en_low][0]
        elif en_low in ar_trans_map:
            ar_name = ar_trans_map[en_low]
        else:
            ar_name = _clean_entity_name(en_n) or en_n

        flag_url = item["flag_url"] or (
            f"https://ui-avatars.com/api/?name={urllib.parse.quote(item['abbr'] or en_n[:2])}"
            f"&background=0f172a&color=00d2ff&bold=true&rounded=true"
        )

        nations.append({
            "id": f"nat_{item['team_id'] or item['abbr'] or len(nations)}",
            "rank": int(item["rank"]),
            "name": ar_name,
            "raw_name": en_n,
            "country_code": item["abbr"],
            "flag_url": flag_url,
            "continent_key": item["continent_key"],
            "confederation": item["confederation"],
            "fifa_points": item["fifa_points"],
            "tm_slug": item.get("tm_slug", ""),
            "tm_id": item.get("tm_id", ""),
        })

    # ترتيب صارم من التصنيف الأقوى (#1) حتى الأضعف
    # ترتيب صارم من التصنيف الأقوى (#1) حتى الأضعف
    nations.sort(key=lambda x: x["rank"])

    if nations:
        save_to_cache(cache_key, nations)
        return nations

    return cached if cached else []

   



def get_live_clubs_cards(league_code: str = "PL", force_refresh: bool = False):
    """جلب بطاقات جميع أندية الدوري المختار حياً من ESPN Teams & Standings API"""
    _purge_legacy_cards_cache_once()
    code = (league_code or "PL").upper()
    if code not in LEAGUE_CODES:
        code = "PL"

    cache_key = f"live_clubs_cards_pure_v6_{code}"
    cached, is_fresh = get_from_cache(cache_key, ttl=3600)
    if cached and is_fresh and not force_refresh:
        return cached

    espn_code = LEAGUE_CODES[code]["espn"]
    lg_info = LEAGUE_CODES[code]

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_st = ex.submit(get_official_standings, code, force_refresh)
        fut_tm = ex.submit(
            fetch_json_fast,
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams?limit=50",
            4.5
        )
        standings = fut_st.result() or []
        teams_json = fut_tm.result() or {}

    espn_teams_map = {}
    try:
        raw_t_list = teams_json.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
        for item in raw_t_list:
            t_obj = item.get("team") or {}
            tid = str(t_obj.get("id") or "")
            disp = (t_obj.get("displayName") or "").strip()
            short_d = (t_obj.get("shortDisplayName") or disp).strip()
            logos = t_obj.get("logos") or []
            logo_href = logos[0].get("href", "") if (logos and isinstance(logos[0], dict)) else ""
            if tid:
                info_obj = {"team_id": tid, "raw_name": disp, "short_name": short_d, "crest": logo_href}
                espn_teams_map[disp.lower()] = info_obj
                espn_teams_map[short_d.lower()] = info_obj
    except Exception:
        pass

    cards = []
    seen_names = set()

    for idx, st_row in enumerate(standings, 1):
        raw_n = (st_row.get("raw_name") or st_row.get("team_name") or "").strip()
        short_n = (st_row.get("short_name") or raw_n).strip()
        if not raw_n or raw_n.lower() in seen_names:
            continue
        seen_names.add(raw_n.lower())

        matched_tm = espn_teams_map.get(raw_n.lower()) or espn_teams_map.get(short_n.lower()) or {}
        team_id = st_row.get("team_id") or matched_tm.get("team_id") or ""
        if not team_id:
            m_id = re.search(r'/(\d+)\.(?:png|svg)', str(st_row.get("crest") or ""))
            if m_id:
                team_id = m_id.group(1)

        ar_name = _clean_entity_name(short_n) or _clean_entity_name(raw_n) or short_n

        cards.append({
            "id": f"club_{code}_{team_id or idx}",
            "team_id": str(team_id),
            "name": ar_name,
            "raw_name": raw_n,
            "short_name": short_n,
            "crest": st_row.get("crest") or matched_tm.get("crest") or "",
            "league_code": code,
            "league_name": lg_info["name"],
            "league_flag": lg_info["flag"],
            "rank": st_row.get("rank", idx),
            "points": st_row.get("points", 0),
            "played": st_row.get("played", 0),
            "won": st_row.get("won", 0),
            "gf": st_row.get("gf", 0),
            "ga": st_row.get("ga", 0),
            "gd": st_row.get("gd", 0),
            "form": st_row.get("form", [])
        })

    if cards:
        save_to_cache(cache_key, cards)
    return cards


def _compute_dynamic_fifa_attributes(pos_abbr: str, age: int, goals: int, assists: int, apps: int, saves: int, club_rank: int):
    pos = (pos_abbr or "CM").upper()
    rank_bonus = max(0, min(8, int((20 - max(1, club_rank)) * 0.42)))
    activity_bonus = min(6, int((apps * 0.18) + (goals * 0.55) + (assists * 0.45) + (saves * 0.08)))
    age_mod = 2 if 21 <= age <= 29 else (1 if age < 21 else -1)
    base_ovr = min(94, max(72, 75 + rank_bonus + activity_bonus + age_mod))

    if pos.startswith("G"):
        pac, sho, pas, dri, df, phy = base_ovr + 2, base_ovr - 2, base_ovr - 4, base_ovr + 3, 45 + rank_bonus, base_ovr + 1
    elif pos in ("CB", "CD", "D"):
        pac, sho, pas, dri, df, phy = base_ovr - 5, 48 + goals * 3, base_ovr - 7, base_ovr - 8, base_ovr + 4, base_ovr + 3
    elif pos in ("LB", "RB", "LWB", "RWB"):
        pac, sho, pas, dri, df, phy = base_ovr + 5, 60 + goals * 2, base_ovr + 1, base_ovr + 2, base_ovr - 1, base_ovr - 2
    elif pos in ("CDM", "DM", "LDM", "RDM"):
        pac, sho, pas, dri, df, phy = base_ovr - 4, 64 + goals * 2, base_ovr + 2, base_ovr - 1, base_ovr + 3, base_ovr + 4
    elif pos in ("CAM", "AM", "LM", "RM"):
        pac, sho, pas, dri, df, phy = base_ovr + 2, base_ovr + min(6, goals), base_ovr + 4, base_ovr + 5, 52 + rank_bonus, base_ovr - 5
    elif pos in ("LW", "RW", "LF", "RF"):
        pac, sho, pas, dri, df, phy = base_ovr + 6, base_ovr + 1 + min(6, goals), base_ovr + 1, base_ovr + 5, 42 + rank_bonus, base_ovr - 6
    elif pos in ("ST", "CF", "F"):
        pac, sho, pas, dri, df, phy = base_ovr + 3, base_ovr + 5 + min(5, goals), base_ovr - 4, base_ovr + 2, 38 + rank_bonus, base_ovr + 2
    else:
        pac, sho, pas, dri, df, phy = base_ovr - 2, base_ovr - 2 + min(5, goals), base_ovr + 4, base_ovr + 2, base_ovr - 3, base_ovr - 1

    return {
        "overall": int(base_ovr),
        "pac": int(min(97, max(40, pac))),
        "sho": int(min(96, max(35, sho))),
        "pas": int(min(95, max(45, pas))),
        "dri": int(min(96, max(45, dri))),
        "def": int(min(95, max(32, df))),
        "phy": int(min(95, max(48, phy)))
    }


def get_live_club_squad_fifa_cards(league_code: str = "PL", team_id: str = "", team_name: str = "", force_refresh: bool = False):
    code = (league_code or "PL").upper()
    if code not in LEAGUE_CODES:
        code = "PL"

    espn_code = LEAGUE_CODES[code]["espn"]
    clubs_list = get_live_clubs_cards(code)

    target_club = None
    tid_clean = str(team_id or "").strip()
    tname_clean = str(team_name or "").strip().lower()

    for c in clubs_list:
        if (tid_clean and str(c.get("team_id")) == tid_clean) or (
            tname_clean and tname_clean in (c["name"].lower(), c["raw_name"].lower(), c["short_name"].lower())
        ):
            target_club = c
            break

    if not target_club:
        return []
   

    real_tid = str(target_club.get("team_id") or "").strip()
    club_ar = target_club.get("name") or "النادي"
    club_raw = target_club.get("raw_name") or club_ar
    club_crest = target_club.get("crest") or ""
    club_rank = int(target_club.get("rank") or 5)

    if not real_tid:
        teams_lookup = fetch_json_fast(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams?limit=50", timeout=4.0) or {}
        for tw in teams_lookup.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            tobj = tw.get("team") or {}
            disp_l = str(tobj.get("displayName") or "").lower()
            short_l = str(tobj.get("shortDisplayName") or "").lower()
            if club_raw.lower() in (disp_l, short_l) or disp_l in club_raw.lower():
                real_tid = str(tobj.get("id") or "").strip()
                break
    if not real_tid:
        return []

    cache_key = f"live_squad_fifa_v6_{code}_{real_tid or club_raw}"
    cached, is_fresh = get_from_cache(cache_key, ttl=3600 * 6)
    if cached and is_fresh and not force_refresh:
        return cached

    roster_urls = [
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams/{real_tid}/roster",
        f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams/{real_tid}/roster",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{real_tid}/roster"
    ]

    r_data = None
    for u in roster_urls:
        res = fetch_json_fast(u, timeout=5.0)
        if isinstance(res, dict) and isinstance(res.get("athletes"), list) and len(res["athletes"]) > 0:
            r_data = res
            break

    if not r_data:
        return []

    raw_athletes = []
    for item in r_data.get("athletes", []):
        if isinstance(item, dict) and isinstance(item.get("items"), list):
            raw_athletes.extend(item["items"])
        elif isinstance(item, dict):
            raw_athletes.append(item)

    squad_cards = []
    seen_pids = set()

    for ath in raw_athletes:
        if not isinstance(ath, dict):
            continue
        pid = str(ath.get("id") or "")
        p_name = (ath.get("displayName") or ath.get("fullName") or "").strip()
        if not p_name or (pid and pid in seen_pids):
            continue
        if pid:
            seen_pids.add(pid)

        jersey = str(ath.get("jersey") or "-")
        age = safe_num(ath.get("age"), 24)
        flag_obj = ath.get("flag") if isinstance(ath.get("flag"), dict) else {}
        nat = (ath.get("citizenship") or flag_obj.get("alt") or "دولي").strip()
        height_cm = _convert_height_to_cm(ath.get("displayHeight") or ath.get("height"))
        weight_kg = _convert_weight_to_kg(ath.get("displayWeight") or ath.get("weight"))

        pos_obj = ath.get("position") or {}
        pos_abbr = (pos_obj.get("abbreviation") or "CM").upper() if isinstance(pos_obj, dict) else "CM"
        pos_ar = _translate_pos(pos_abbr)

        headshot = ""
        if isinstance(ath.get("headshot"), dict):
            headshot = ath["headshot"].get("href", "")
        elif isinstance(ath.get("headshot"), str):
            headshot = ath["headshot"]
        if not headshot and pid:
            headshot = f"https://a.espncdn.com/i/headshots/soccer/players/full/{pid}.png"

        apps, goals, assists, saves = 0, 0, 0, 0
        stats_splits = ath.get("statistics", {})
        stat_cats = []
        if isinstance(stats_splits, dict):
            splits_obj = stats_splits.get("splits") or {}
            stat_cats = splits_obj.get("categories") or stats_splits.get("categories") or []
        elif isinstance(ath.get("stats"), list):
            stat_cats = [{"stats": ath["stats"]}]

        for cat in stat_cats:
            if not isinstance(cat, dict):
                continue
            for s in (cat.get("stats") or []):
                if not isinstance(s, dict):
                    continue
                s_name = str(s.get("name") or "").lower()
                s_val = safe_num(s.get("value") if s.get("value") is not None else s.get("displayValue"), 0)
                if s_name in ("appearances", "gamesplayed"):
                    apps = max(apps, s_val)
                elif s_name in ("totalgoals", "goals"):
                    goals = max(goals, s_val)
                elif s_name in ("goalassists", "assists"):
                    assists = max(assists, s_val)
                elif s_name == "saves":
                    saves = max(saves, s_val)

        fifa_stats = _compute_dynamic_fifa_attributes(pos_abbr, age, goals, assists, apps, saves, club_rank)

        squad_cards.append({
            "id": f"espn_p_{pid or hashlib.md5(p_name.encode()).hexdigest()[:8]}",
            "player_id": pid,
            "name": p_name,
            "avatar": headshot or _player_avatar(pid, p_name),
            "club": club_ar,
            "raw_club": club_raw,
            "club_id": real_tid,
            "club_crest": club_crest,
            "league_code": code,
            "position": pos_ar,
            "pos_abbr": pos_abbr[:3],
            "jersey": jersey,
            "age": age,
            "height": height_cm,
            "weight": weight_kg,
            "nationality": nat,
            "matches": apps,
            "goals": goals,
            "assists": assists,
            "overall": fifa_stats["overall"],
            "fifa": fifa_stats
        })

    pos_order = {"GK": 1, "G": 1, "CB": 2, "CD": 2, "LB": 3, "RB": 3, "D": 3, "CDM": 4, "DM": 4, "CM": 5, "M": 5, "CAM": 6, "AM": 6, "LW": 7, "RW": 7, "ST": 8, "CF": 8, "F": 8}
    squad_cards.sort(key=lambda x: (-x["overall"], pos_order.get(x["pos_abbr"], 5)))

    if squad_cards:
        save_to_cache(cache_key, squad_cards)
    return squad_cards


def get_live_players_cards(league_code: str = "PL", search_query: str = "", force_refresh: bool = False):
    code = (league_code or "PL").upper()
    q = (search_query or "").strip()
    if q.startswith("TEAM_ID:"):
        tid = q.replace("TEAM_ID:", "").strip()
        return get_live_club_squad_fifa_cards(code, team_id=tid, force_refresh=force_refresh)
    clubs = get_live_clubs_cards(code, force_refresh=force_refresh)
    if not clubs:
        return []
    return get_live_club_squad_fifa_cards(code, team_id=clubs[0]["team_id"], force_refresh=force_refresh)


# =========================================================================
# محرك سحب الألقاب الرسمية والأساطير المزدوج (Transfermarkt + Wikipedia API)
# =========================================================================

def _classify_and_translate_tm_trophy(raw_title: str, entity_type: str):
    """تصنيف وتعريب اسم البطولة القادم من Transfermarkt أو Wikipedia"""
    t = html.unescape(str(raw_title or "")).strip()
    t = re.sub(r'\s+', ' ', t)
    low = t.lower()

    if any(skip in low for skip in [
        "u15", "u16", "u17", "u18", "u19", "u20", "u21", "u23", "youth", "junior", "amateur",
        "second tier", "third tier", "fourth tier", "2nd tier", "3rd tier",
        "segunda", "serie b", "2. bundesliga", "ligue 2", "efl championship",
        "participant", "promoted", "relegated", "fair play", "catalunya", "copa catalunya",
        "regional", "friendly", "audi cup", "gamper", "trofeo", "reserve"
    ]):
        return None, None

    # 1. بطولات عالمية (World)
    if ("world cup" in low or "fifa world cup" in low) and "club" not in low and "qualif" not in low:
        return "كأس العالم FIFA 🏆", "world"
    if "club world cup" in low:
        return "كأس العالم للأندية 🌍", "world"
    if "intercontinental" in low or "afro-asian club" in low:
        return "كأس الإنتركونتيننتال 🌍", "world"
    if "confederations cup" in low:
        return "كأس القارات FIFA 🌟", "world"
    if "olympic" in low:
        return "ذهبية الألعاب الأولمبية 🥇", "world"
    if "artemio franchi" in low or "finalissima" in low or "conmebol-uefa" in low or "conmebol–uefa" in low:
        return "كأس فيناليسيما الدولية 🏆", "world"

    # 2. بطولات قارية للمنتخبات والأندية (Continental)
    if ("european champion" in low or "uefa european" in low or low == "uefa euro") and "club" not in low:
        return "كأس أمم أوروبا (اليورو) 🇪🇺", "continental"
    if "nations league" in low and ("uefa" in low or entity_type == "nation"):
        if "concacaf" in low:
            return "دوري أمم الكونكاكاف ⚡", "continental"
        return "دوري الأمم الأوروبية ⚡", "continental"
    if "copa américa" in low or "copa america" in low or "south american championship" in low:
        return "كوبا أمريكا 🏆", "continental"
    if "africa cup of nations" in low or "african cup of nations" in low or "afcon" in low:
        return "كأس أمم أفريقيا 🌍", "continental"
    if "african nations championship" in low or "chan" in low:
        return "بطولة أمم أفريقيا للمحليين 🌍", "continental"
    if "asian cup" in low and "club" not in low and "winners" not in low:
        return "كأس أمم آسيا 🌏", "continental"
    if "asian games" in low:
        return "ذهبية الألعاب الآسيوية 🌏", "continental"
    if "gold cup" in low or "concacaf championship" in low:
        return "الكأس الذهبية CONCACAF 🏆", "continental"
    if "ofc nations cup" in low:
        return "كأس أوقيانوسيا للأمم 🏆", "continental"
    if "arab cup" in low and "club" not in low:
        return "كأس العرب FIFA 🏆", "continental"
    if "gulf cup" in low:
        return "كأس الخليج العربي 🏆", "continental"
    if "waff championship" in low or "west asian football" in low:
        return "بطولة اتحاد غرب آسيا 🏆", "continental"
    if "eaff" in low or "east asian" in low:
        return "بطولة شرق آسيا للمنتخبات 🏆", "continental"
    if "asean championship" in low or "aff championship" in low:
        return "بطولة آسيان للمنتخبات 🏆", "continental"
    if "saff championship" in low:
        return "بطولة جنوب آسيا للمنتخبات 🏆", "continental"

    if ("champions league" in low or "european champion clubs' cup" in low or low == "european cup" or "european cup /" in low) and not any(x in low for x in ["afc", "caf", "concacaf", "ofc"]):
        return "دوري أبطال أوروبا 🏆", "continental"
    if "europa league" in low or "uefa cup" in low:
        return "الدوري الأوروبي 🟠", "continental"
    if "cup winners' cup" in low and "asian" not in low and "african" not in low:
        return "كأس الكؤوس الأوروبية 🏅", "continental"
    if "uefa super cup" in low or "european super cup" in low:
        return "كأس السوبر الأوروبي ⚡", "continental"
    if "conference league" in low:
        return "دوري المؤتمر الأوروبي 🟢", "continental"
    if "afc champions league" in low or "asian club championship" in low:
        return "دوري أبطال آسيا للنخبة 🌏", "continental"
    if "asian cup winners" in low:
        return "كأس الكؤوس الآسيوية 🌏", "continental"
    if "asian super cup" in low:
        return "كأس السوبر الآسيوي ⚡", "continental"
    if "afc cup" in low or "champions league two" in low:
        return "كأس الاتحاد الآسيوي 🌏", "continental"
    if "caf champions league" in low or "african cup of champions clubs" in low:
        return "دوري أبطال أفريقيا 🌍", "continental"
    if "caf confederation" in low or "african cup winners" in low:
        return "كأس الكونفدرالية الأفريقية 🌍", "continental"
    if "caf super cup" in low:
        return "كأس السوبر الأفريقي ⚡", "continental"
    if "copa libertadores" in low or "libertadores" in low:
        return "كوبا ليبرتادوريس 🏆", "continental"
    if "copa sudamericana" in low:
        return "كوبا سودأمريكانا 🏆", "continental"
    if "recopa sudamericana" in low:
        return "ريكوبا سودأمريكانا ⚡", "continental"
    if "arab club champions" in low:
        return "البطولة العربية للأندية 🏆", "continental"

    if entity_type == "nation":
        if any(w in low for w in ["cup", "championship", "games", "trophy", "tournament"]):
            clean_nat = re.sub(r'\bwinner\b|\bchampion\b', '', t, flags=re.IGNORECASE).strip()
            return (f"{clean_nat} 🏆", "continental") if len(clean_nat) >= 3 else (None, None)
        return None, None

    # 3. البطولات المحلية للأندية (Domestic - تشمل مسميات Transfermarkt و Wikipedia)
    domestic_map = [
        (["english champion", "premier league", "football league first division", "first division / premier league"], "الدوري الإنجليزي الممتاز 🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
        (["fa cup"], "كأس الاتحاد الإنجليزي (FA Cup) 🏅"),
        (["english league cup", "efl cup", "football league cup", "league cup"], "كأس الرابطة الإنجليزية (EFL Cup) ⚡"),
        (["english supercup", "fa community shield", "fa charity shield", "community shield"], "درع المجتمع الإنجليزي 🛡️"),
        (["spanish champion", "la liga", "laliga", "primera división", "primera division"], "الدوري الإسباني (LaLiga) 🇪🇸"),
        (["spanish cup", "copa del rey"], "كأس ملك إسبانيا (Copa del Rey) 🏅"),
        (["spanish super cup", "supercopa de españa", "supercopa de espana"], "كأس السوبر الإسباني ⚡"),
        (["copa eva duarte"], "كأس إيفا دوارتي الإسباني 🏅"),
        (["copa de la liga"], "كأس الدوري الإسباني ⚡"),
        (["italian champion", "serie a"], "الدوري الإيطالي (Serie A) 🇮🇹"),
        (["italian cup", "coppa italia"], "كأس إيطاليا (Coppa Italia) 🏅"),
        (["italian super cup", "supercoppa italiana"], "كأس السوبر الإيطالي ⚡"),
        (["german champion", "bundesliga"], "الدوري الألماني (Bundesliga) 🇩🇪"),
        (["german cup", "dfb-pokal", "dfb pokal"], "كأس ألمانيا (DFB-Pokal) 🏅"),
        (["german super cup", "dfl-supercup", "dfb-supercup", "franz beckenbauer supercup"], "كأس السوبر الألماني ⚡"),
        (["german league cup", "dfl-ligapokal"], "كأس الرابطة الألمانية ⚡"),
        (["french champion", "ligue 1", "french division 1"], "الدوري الفرنسي (Ligue 1) 🇫🇷"),
        (["french cup", "coupe de france"], "كأس فرنسا 🏅"),
        (["french super cup", "trophée des champions", "trophee des champions", "challenge des champions"], "كأس السوبر الفرنسي ⚡"),
        (["french league cup", "coupe de la ligue"], "كأس الرابطة الفرنسية ⚡"),
        (["dutch champion", "eredivisie", "netherlands football league"], "الدوري الهولندي (Eredivisie) 🇳🇱"),
        (["dutch cup", "knvb cup", "knvb beker"], "كأس هولندا (KNVB) 🏅"),
        (["dutch super cup", "johan cruyff shield", "johan cruijff schaal"], "درع يوهان كرويف ⚡"),
        (["portuguese champion", "primeira liga", "primeira divisão", "campeonato nacional"], "الدوري البرتغالي 🇵🇹"),
        (["portuguese cup", "taça de portugal", "taca de portugal"], "كأس البرتغال 🏅"),
        (["portuguese super cup", "supertaça", "supertaca"], "كأس السوبر البرتغالي ⚡"),
        (["portuguese league cup", "taça da liga", "taca da liga"], "كأس الرابطة البرتغالية ⚡"),
        (["turkish champion", "süper lig", "super lig", "turkish football championship"], "الدوري التركي الممتاز 🇹🇷"),
        (["turkish cup", "türkiye kupası", "turkiye kupasi"], "كأس تركيا 🏅"),
        (["turkish super cup", "süper kupa", "super kupa", "presidential cup"], "كأس السوبر التركي ⚡"),
        (["saudi arabian champion", "saudi pro league", "saudi professional league", "saudi premier league"], "الدوري السعودي للمحترفين 🇸🇦"),
        (["saudi cup", "king's cup", "king cup", "custodian of the two holy mosques"], "كأس خادم الحرمين الشريفين 🏅"),
        (["saudi super cup"], "كأس السوبر السعودي ⚡"),
        (["crown prince cup"], "كأس ولي العهد السعودي 🏅"),
        (["egyptian champion", "egyptian premier league"], "الدوري المصري الممتاز 🇪🇬"),
        (["egyptian cup", "egypt cup"], "كأس مصر 🏅"),
        (["egyptian super cup"], "كأس السوبر المصري ⚡"),
        (["moroccan champion", "botola"], "الدوري المغربي الاحترافي 🇲🇦"),
        (["moroccan throne cup", "coupe du trône"], "كأس العرش المغربي 🏅"),
        (["tunisian champion", "tunisian ligue"], "الدوري التونسي للمحترفين 🇹🇳"),
        (["tunisian cup"], "كأس تونس 🏅"),
        (["algerian champion", "ligue professionnelle 1"], "الدوري الجزائري للمحترفين 🇩🇿"),
        (["algerian cup"], "كأس الجزائر 🏅"),
        (["qatari champion", "qatar stars league"], "دوري نجوم قطر 🇶🇦"),
        (["emir of qatar cup", "amir cup"], "كأس أمير قطر 🏅"),
        (["uae champion", "uae pro league"], "الدوري الإماراتي للمحترفين 🇦🇪"),
        (["uae president's cup"], "كأس رئيس الدولة الإماراتي 🏅")
    ]
    for keywords, v_ar in domestic_map:
        if any(k_en in low for k_en in keywords):
            return v_ar, "domestic"

    if any(w in low for w in ["champion", "league", "cup", "supercup", "super cup", "shield", "pokal", "copa", "coupe", "taça"]):
        clean_dom = re.sub(r'\bwinner\b|\bchampions?\b', '', t, flags=re.IGNORECASE).strip()
        if len(clean_dom) >= 3:
            return f"{clean_dom} 🏅", "domestic"

    return None, None


def _find_exact_tm_entity_slug_and_id(entity_type: str, raw_name: str):
    """استخراج معرف النادي أو المنتخب الصحيح من Transfermarkt بدون الانقطاع عند الجداول المتداخلة"""
    q_clean = str(raw_name or "").strip()
    if not q_clean:
        return "", ""

    q_low = q_clean.lower()
    if entity_type == "nation" and q_low in _TM_NATION_ID_MAP:
        return _TM_NATION_ID_MAP[q_low]

    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(q_clean)}"
    search_html = _fetch_html_gzip(search_url, timeout=6.5)
    if not search_html:
        return "", ""

    clubs_section = search_html
    for marker in ("Search results for clubs", "Suchergebnisse zu Vereinen", "Vereine"):
        idx_m = search_html.find(marker)
        if idx_m != -1:
            clubs_section = search_html[idx_m:]
            break

    # استخدام _split_tm_outer_rows لمنع انقطاع الصف عند </tr> الداخلي المتداخل
    outer_rows = _split_tm_outer_rows(clubs_section)
    candidates = []

    for r_html in outer_rows:
        # دعم أي لاحقة بعد رقم النادي مثل /saison_id/2025
        for link_m in re.finditer(r'<a[^>]+href="/([^/"]+)/startseite/verein/(\d+)[^"]*"[^>]*>(.*?)</a>', r_html, re.DOTALL):
            slug = link_m.group(1)
            vid = link_m.group(2)
            inner_txt = html.unescape(re.sub(r'<[^>]+>', '', link_m.group(3))).strip()
            if not inner_txt:
                t_attr = re.search(r'title="([^"]+)"', link_m.group(0))
                inner_txt = html.unescape(t_attr.group(1)).strip() if t_attr else ""
            if not inner_txt or inner_txt.isdigit():
                continue

            low_title = inner_txt.lower()
            low_slug = slug.lower()

            bad_tokens = [
                "u15", "u16", "u17", "u18", "u19", "u20", "u21", "u22", "u23",
                " ii", " b ", "atlètic", "atletic", "castilla", "youth", "juv.",
                "women", "femenino", "femminile", "guayaquil", "ladies", "reserves", "olympic"
            ]
            if any(bt in f" {low_title} " or bt in low_slug for bt in bad_tokens) or low_title.endswith(" b"):
                continue

            score = 100
            if low_title == q_low:
                score += 80
            elif q_low in low_title or low_title in q_low:
                score += 40

            if entity_type == "club":
                if "bn" in r_html.lower():
                    score += 50
                elif "m" in r_html.lower() and "€" in r_html:
                    score += 25
            else:
                # للمنتخبات: نفضل الصف الذي يطابق اسم الدولة تماماً
                if low_title == q_low:
                    score += 100

            candidates.append((score, slug, vid, inner_txt))
            break

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1], candidates[0][2]

    return "", ""



def _parse_tm_record_players_table(html_doc: str, mode: str = "apps"):
    """استخراج اللاعبين وأرقامهم القياسية بدقة عبر روابط Transfermarkt المخصصة والحدود المنطقية"""
    rows = _split_tm_outer_rows(html_doc)
    parsed_players = []
    for r_html in rows[:15]:
        p_m = re.search(r'href="[^"]*/profil/spieler/\d+[^"]*"[^>]*>([^<]+)</a>', r_html)
        if not p_m:
            continue
        p_name = html.unescape(p_m.group(1)).strip()
        if not p_name or p_name.isdigit():
            continue

        apps_val = 0
        goals_val = 0
        assists_val = 0

        m_apps = re.search(r'href="[^"]*/leistungsdaten/spieler/\d+[^"]*"[^>]*>\s*([\d\.,]+)\s*</a>', r_html)
        if m_apps:
            apps_val = safe_num(m_apps.group(1).replace(".", "").replace(",", ""), 0)

        m_goals = re.search(r'href="[^"]*/alletore/spieler/\d+[^"]*"[^>]*>\s*([\d\.,]+)\s*</a>', r_html)
        if m_goals:
            goals_val = safe_num(m_goals.group(1).replace(".", "").replace(",", ""), 0)

        num_cells = []
        for cell_m in re.finditer(r'<td[^>]*class="[^"]*(?:zentriert|rechts)[^"]*"[^>]*>(.*?)</td>', r_html, re.DOTALL):
            c_txt = html.unescape(re.sub(r'<[^>]+>', '', cell_m.group(1))).strip()
            if "'" in c_txt or "%" in c_txt or "€" in c_txt:
                continue
            c_clean = c_txt.replace(".", "").replace(",", "")
            if c_clean.isdigit():
                val = int(c_clean)
                if not (1900 <= val <= 2030) and val <= 1500:
                    num_cells.append(val)

        stat_nums = num_cells[1:] if len(num_cells) >= 2 else num_cells
        if apps_val == 0 and stat_nums:
            apps_val = stat_nums[0]
        if goals_val == 0 and len(stat_nums) >= 2:
            goals_val = stat_nums[1] if mode == "apps" else stat_nums[0]
        if len(stat_nums) >= 3:
            cand_ast = stat_nums[2]
            if 0 < cand_ast <= 450 and cand_ast <= max(1, apps_val):
                assists_val = cand_ast

        parsed_players.append({
            "name": p_name,
            "apps": apps_val,
            "goals": goals_val,
            "assists": assists_val
        })
    return parsed_players


def _scrape_tm_verified_dossier(entity_type: str, raw_name: str):
    """جلب خزانة البطولات والأساطير حياً من Transfermarkt"""
    dossier = {
        "honours": [],
        "total_trophies": 0,
        "top_scorer": "",
        "most_apps": "",
        "most_assists": "",
        "founded": "",
        "stadium": "",
        "crest": ""
    }

    slug, vid = _find_exact_tm_entity_slug_and_id(entity_type, raw_name)
    if not vid:
        return dossier

    safe_slug = slug or "verein"
    dossier["crest"] = f"https://tmssl.akamaized.net/images/wappen/head/{vid}.png"

    erfolge_url = f"https://www.transfermarkt.com/{safe_slug}/erfolge/verein/{vid}"
    rekord_url = f"https://www.transfermarkt.com/{safe_slug}/rekordspieler/verein/{vid}/plus/1"
    scorers_url = f"https://www.transfermarkt.com/{safe_slug}/toptorschuetzen/verein/{vid}/plus/1"

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_erf = ex.submit(_fetch_html_gzip, erfolge_url, 6.5)
        f_rek = ex.submit(_fetch_html_gzip, rekord_url, 6.5)
        f_scr = ex.submit(_fetch_html_gzip, scorers_url, 6.5)
        erf_html = f_erf.result() or ""
        rek_html = f_rek.result() or ""
        scr_html = f_scr.result() or ""

    # 1. استخراج جميع عناوين البطولات <h2> بعد تنظيف الوسوم الداخلية
    merged_honours = {}
    for h2_m in re.finditer(r'<h2[^>]*>(.*?)</h2>', erf_html, re.DOTALL | re.IGNORECASE):
        h2_clean = html.unescape(re.sub(r'<[^>]+>', ' ', h2_m.group(1))).strip()
        h2_clean = re.sub(r'\s+', ' ', h2_clean)
        m_tr = re.match(r'^(\d+)\s*x\s+(.+)$', h2_clean, re.IGNORECASE)
        if not m_tr:
            continue
        cnt = int(m_tr.group(1))
        raw_t = m_tr.group(2).strip()
        if cnt <= 0:
            continue
        ar_title, cat = _classify_and_translate_tm_trophy(raw_t, entity_type)
        if not ar_title or not cat:
            continue
        if ar_title in merged_honours:
            merged_honours[ar_title]["count"] += cnt
        else:
            merged_honours[ar_title] = {"title": ar_title, "count": cnt, "category": cat}

    honours_list = list(merged_honours.values())
    honours_list.sort(key=lambda x: x["count"], reverse=True)
    dossier["honours"] = honours_list
    dossier["total_trophies"] = sum(h["count"] for h in honours_list)

    # 2. استخراج عميد اللاعبين (الأكثر مشاركة)
    rek_players = _parse_tm_record_players_table(rek_html, mode="apps")
    if rek_players and rek_players[0]["apps"] > 0:
        dossier["most_apps"] = f"{rek_players[0]['name']} ({rek_players[0]['apps']} مباراة)"

    # 3. استخراج الهداف التاريخي والأكثر صناعة
    scr_players = _parse_tm_record_players_table(scr_html, mode="goals")
    if scr_players and scr_players[0]["goals"] > 0:
        dossier["top_scorer"] = f"{scr_players[0]['name']} ({scr_players[0]['goals']} هدفاً)"

    all_rec_players = scr_players + rek_players
    if all_rec_players:
        best_ast = max(all_rec_players, key=lambda x: x["assists"])
        if best_ast["assists"] >= 10:
            dossier["most_assists"] = f"{best_ast['name']} ({best_ast['assists']} أسيست)"

    return dossier
WIKI_DIRECT_PAGE_ALIASES = {
    "club": {
        "inter": "Inter Milan",
        "internazionale": "Inter Milan",
        "milan": "AC Milan",
        "psg": "Paris Saint-Germain F.C.",
        "paris saint-germain": "Paris Saint-Germain F.C.",
        "man city": "Manchester City F.C.",
        "manchester city": "Manchester City F.C.",
        "man united": "Manchester United F.C.",
        "man utd": "Manchester United F.C.",
        "manchester united": "Manchester United F.C.",
        "spurs": "Tottenham Hotspur F.C.",
        "tottenham": "Tottenham Hotspur F.C.",
        "wolves": "Wolverhampton Wanderers F.C.",
        "barcelona": "FC Barcelona",
        "real madrid": "Real Madrid CF",
        "atletico madrid": "Atlético Madrid",
        "atlético madrid": "Atlético Madrid",
        "bayern munich": "FC Bayern Munich",
        "bayern": "FC Bayern Munich",
        "juventus": "Juventus FC",
        "liverpool": "Liverpool F.C.",
        "arsenal": "Arsenal F.C.",
        "chelsea": "Chelsea F.C.",
        "al ahly": "Al Ahly SC",
        "al hilal": "Al Hilal SFC",
        "al-hilal": "Al Hilal SFC",
        "al nassr": "Al-Nassr FC",
        "al-nassr": "Al-Nassr FC",
        "al ittihad": "Al-Ittihad Club (Jeddah)",
        "al-ittihad": "Al-Ittihad Club (Jeddah)",
    },
    "nation": {
        "usa": "United States men's national soccer team",
        "united states": "United States men's national soccer team",
        "korea republic": "South Korea national football team",
        "south korea": "South Korea national football team",
        "ir iran": "Iran national football team",
        "iran": "Iran national football team",
        "côte d'ivoire": "Ivory Coast national football team",
        "ivory coast": "Ivory Coast national football team",
        "türkiye": "Turkey national football team",
        "turkey": "Turkey national football team",
        "czechia": "Czech Republic national football team",
        "china pr": "China national football team",
        "congo dr": "DR Congo national football team",
        "republic of ireland": "Republic of Ireland national football team",
        "ireland": "Republic of Ireland national football team",
    },
}


def _resolve_en_wiki_page_title(entity_type: str, raw_name: str):
    """البحث الذكي عن عنوان صفحة النادي أو المنتخب الرسمي على Wikipedia API"""
    q = str(raw_name or "").strip()
    if not q:
        return ""
    q_low = q.lower()
    direct_map = WIKI_DIRECT_PAGE_ALIASES.get(entity_type, {})
    if q_low in direct_map:
        return direct_map[q_low]

    search_q = f"{q} national football team" if entity_type == "nation" else f"{q} football club"
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch="
        + urllib.parse.quote(search_q)
        + "&srlimit=8&format=json"
    )
    data = fetch_wiki_api_json(url, timeout=4.5)
    if isinstance(data, dict) and "query" in data:
        results = data["query"].get("search") or []
        bad_words = [
            "women", "under-", "u-20", "u-23", "u-17", "u-19", "u-21",
            "season", "list of", "results", "records and statistics",
            "in international", "reserve", "academy", "futsal", "beach soccer",
            "olympic", "castilla", "atlètic", "b team", "youth"
        ]
        for r in results:
            title = r.get("title") or ""
            t_low = title.lower()
            if any(bad in t_low for bad in bad_words):
                continue
            if entity_type == "nation" and ("national" in t_low and ("football" in t_low or "soccer" in t_low)):
                return title
            if entity_type == "club":
                return title
    return f"{q}_national_football_team" if entity_type == "nation" else q


class _HonoursWikiTableParser(_WikiTableParser):
    """نسخة مطورة تقرأ أيضاً نصوص alt/title للأيقونات مثل الميدالية الذهبية داخل رؤوس الجداول"""
    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        if self.in_cell and tag == "img":
            attr_dict = dict(attrs)
            alt_txt = (attr_dict.get("alt") or attr_dict.get("title") or "").strip()
            if alt_txt and any(w in alt_txt.lower() for w in ("gold", "silver", "bronze", "1st", "2nd", "3rd", "winner", "champion")):
                self.cell_text_parts.append(f" {alt_txt} ")


class _HonoursHTMLListParser(HTMLParser):
    """محلل HTML منظم لاستخراج البطولات من القوائم <ul><li> و <dl><dt><dd> والعناوين <h3><h4>"""
    def __init__(self):
        super().__init__()
        self.blocks = []  # list of (kind, text, depth)
        self.table_depth = 0
        self.ignore_depth = 0
        self.li_depth = 0
        self.stack = []

    def _flush_top_li_if_text(self):
        if self.stack and self.stack[-1]["tag"] == "li":
            txt = re.sub(r"\s+", " ", "".join(self.stack[-1]["parts"])).strip()
            if txt:
                self.blocks.append(("li", txt, self.stack[-1]["depth"]))
                self.stack[-1]["parts"] = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table_depth += 1
            return
        if self.table_depth > 0:
            return
        if tag in ("sup", "style", "script"):
            self.ignore_depth += 1
            return
        if self.ignore_depth > 0:
            return

        if tag in ("ul", "ol"):
            self._flush_top_li_if_text()
        elif tag == "li":
            self.li_depth += 1
            self.stack.append({"tag": "li", "parts": [], "depth": self.li_depth})
        elif tag in ("h3", "h4", "dt", "dd"):
            self.stack.append({"tag": tag, "parts": [], "depth": 0})
        elif tag == "img" and self.stack:
            attr_dict = dict(attrs)
            alt_txt = (attr_dict.get("alt") or attr_dict.get("title") or "").strip()
            if alt_txt and any(w in alt_txt.lower() for w in ("gold", "silver", "bronze", "1st", "2nd", "3rd")):
                self.stack[-1]["parts"].append(f" {alt_txt} ")
        elif tag == "br" and self.stack:
            self.stack[-1]["parts"].append(" ")

    def handle_endtag(self, tag):
        if tag == "table" and self.table_depth > 0:
            self.table_depth -= 1
            return
        if self.table_depth > 0:
            return
        if tag in ("sup", "style", "script") and self.ignore_depth > 0:
            self.ignore_depth -= 1
            return
        if self.ignore_depth > 0:
            return

        if tag in ("li", "h3", "h4", "dt", "dd") and self.stack and self.stack[-1]["tag"] == tag:
            item = self.stack.pop()
            if tag == "li":
                self.li_depth = max(0, self.li_depth - 1)
            txt = re.sub(r"\s+", " ", "".join(item["parts"])).strip()
            txt = re.sub(r"\[\s*edit\s*\]", "", txt, flags=re.IGNORECASE).strip()
            if txt:
                kind = "heading" if tag in ("h3", "h4") else tag
                self.blocks.append((kind, txt, item["depth"]))

    def handle_data(self, data):
        if self.table_depth == 0 and self.ignore_depth == 0 and self.stack:
            self.stack[-1]["parts"].append(data)


def _extract_year_count(text_str: str) -> int:
    """حساب عدد البطولات من قائمة السنوات مثل 1954, 1974, 1990, 2014"""
    yrs = re.findall(r'\b(?:18\d{2}|19\d{2}|20\d{2})(?:[–\-/]\d{2,4})?\b', text_str or "")
    return len(yrs)


def _parse_wiki_honours_from_html(html_content: str, entity_type: str):
    """استخراج جميع البطولات الرسمية بدقة من HTML قسم Honours (يدعم الجداول والقوائم والقوالب المدمجة)"""
    if not html_content:
        return []

    table_honours = {}
    list_honours = {}

    def _add_trophy(target_dict, raw_comp, count_val, allow_sum_distinct=False):
        if not raw_comp or count_val <= 0 or count_val > 120:
            return
        comp_clean = re.sub(r'\[[^\]]*\]', '', str(raw_comp)).strip(" :-–—•")
        if not comp_clean or len(comp_clean) < 3:
            return
        low_rc = comp_clean.lower()
        if any(bad in low_rc for bad in ("total", "overall", "runner", "second place", "third place", "fourth place", "semi-final", "fair play", "qualification")):
            return
        ar_t, cat = _classify_and_translate_tm_trophy(comp_clean, entity_type)
        if not ar_t or not cat:
            return
        raw_sig = re.sub(r'\W+', '', low_rc)
        if ar_t in target_dict:
            if allow_sum_distinct and raw_sig not in target_dict[ar_t]["raw_sigs"]:
                target_dict[ar_t]["count"] += count_val
                target_dict[ar_t]["raw_sigs"].add(raw_sig)
            else:
                target_dict[ar_t]["count"] = max(target_dict[ar_t]["count"], count_val)
        else:
            target_dict[ar_t] = {
                "title": ar_t,
                "count": count_val,
                "category": cat,
                "raw_sigs": {raw_sig},
            }

    # ==================== 1. استخراج البطولات من جداول HTML (مثل ريال مدريد، برشلونة، بايرن، ألمانيا) ====================
    t_parser = _HonoursWikiTableParser()
    t_parser.feed(html_content)
    for raw_tbl in t_parser.tables:
        grid = _expand_table_grid(raw_tbl)
        if len(grid) < 2:
            continue

        header_idx = 0
        for r_i in range(min(3, len(grid))):
            if sum(1 for c in grid[r_i] if c["is_header"]) >= max(1, len(grid[r_i]) // 2):
                header_idx = r_i

        headers = [c["text"].lower() for c in grid[header_idx]]
        comp_col = next((i for i, h in enumerate(headers) if any(k in h for k in ("competition", "tournament", "trophy", "title", "honour", "honor", "event")) and "titles" not in h), -1)
        if comp_col == -1:
            comp_col = next((i for i, h in enumerate(headers) if "type" not in h and "level" not in h and not h.isdigit()), 0)

        # نختار عمود الفوز/الألقاب/الذهبية فقط (ونتجنب عمود Total الخاص بجمع الميداليات)
        cnt_col = next(
            (i for i, h in enumerate(headers)
             if i != comp_col and any(k in h for k in ("titles", "wins", "winners", "champions", "gold", "1st", "first", "number", "no."))
             and not any(b in h for b in ("runner", "2nd", "silver", "3rd", "bronze", "total"))),
            -1
        )
        seasons_col = next((i for i, h in enumerate(headers) if any(k in h for k in ("season", "year", "winning"))), -1)

        if cnt_col == -1 and seasons_col == -1:
            continue

        for row in grid[header_idx + 1:]:
            if len(row) <= comp_col:
                continue
            row_text_low = " ".join(c["text"].lower() for c in row)
            if any(skip_w in row_text_low for skip_w in ("friendly", "unofficial", "regional", "youth", "reserve")):
                continue
            comp_txt = row[comp_col]["text"].strip()
            if not comp_txt or comp_txt.lower() in ("total", "overall", "subtotal", "domestic", "international", "european", "continental", "worldwide"):
                continue

            cnt_val = 0
            if 0 <= cnt_col < len(row):
                m_num = re.search(r'\b(\d{1,3})\b', row[cnt_col]["text"])
                if m_num:
                    n_cand = int(m_num.group(1))
                    if 1 <= n_cand <= 120:
                        cnt_val = n_cand
            if cnt_val == 0 and 0 <= seasons_col < len(row):
                cnt_val = _extract_year_count(row[seasons_col]["text"])

            if cnt_val > 0:
                _add_trophy(table_honours, comp_txt, cnt_val, allow_sum_distinct=True)

    # ==================== 2. استخراج البطولات من القوائم <ul><li> و <dl><dt><dd> (مثل ليفربول، ألمانيا، إنجلترا) ====================
    l_parser = _HonoursHTMLListParser()
    l_parser.feed(html_content)

    skip_sub = False
    current_comp = ""
    blocks = l_parser.blocks

    for idx, (kind, txt, depth) in enumerate(blocks):
        low = txt.lower()

        if kind == "heading":
            if any(b in low for b in ("friendly", "non-official", "unofficial", "youth", "reserve", "women", "individual", "award", "minor", "regional", "invitational", "other")):
                skip_sub = True
            else:
                skip_sub = False
            current_comp = ""
            continue

        if skip_sub:
            continue

        # تجاهل سطور الوصافة والمركز الثالث والرابع
        if any(low.startswith(bad) or f" {bad}" in low[:22] for bad in ("runner", "second", "2nd", "third", "3rd", "fourth", "4th", "semi-final", "finalist", "silver", "bronze")):
            continue

        is_win_subline = (
            kind == "dd"
            or (kind == "li" and depth >= 2)
            or any(low.startswith(w) for w in ("winner", "champion", "1st", "first place", "gold", "title"))
        )

        if is_win_subline and current_comp:
            if any(w in low for w in ("winner", "champion", "1st", "first place", "gold", "title")):
                # يدعم Winners (36, record): و Champions (4): و Winners: 15 و Champions: 1954, 1974...
                m_cnt = re.search(
                    r'(?:winners?|champions?|1st|first\s+place|gold[^:(]*|titles?)\s*(?:\(\s*(\d{1,3})\b|:\s*(\d{1,3})\b(?![–\-/]\d))',
                    txt,
                    re.IGNORECASE
                )
                cnt = int(m_cnt.group(1) or m_cnt.group(2)) if m_cnt else 0
                if cnt == 0:
                    cnt = _extract_year_count(txt)
                if cnt > 0:
                    _add_trophy(list_honours, current_comp, cnt, allow_sum_distinct=False)
            continue

        # سطر رئيسي (اسم البطولة، وقد يحتوي على العدد في نفس السطر)
        if kind in ("li", "dt"):
            cleaned_main = re.split(r'\b(?:runners?-up|second place|2nd place)\b', txt, flags=re.IGNORECASE)[0].strip()
            comp_part = re.split(r'[:\(\–—]', cleaned_main)[0].strip()
            if comp_part:
                current_comp = comp_part

            # التحقق إن كان السطر التالي ليس سطراً فرعياً (dd أو li أعمق)
            next_is_sub = False
            if idx + 1 < len(blocks):
                n_kind, _, n_depth = blocks[idx + 1]
                if n_kind == "dd" or (n_kind == "li" and n_depth > depth):
                    next_is_sub = True

            if not next_is_sub and (":" in cleaned_main or "(" in cleaned_main):
                m_cnt = re.search(r'(?:\(\s*(\d{1,3})\b|:\s*(\d{1,3})\b(?![–\-/]\d))', cleaned_main)
                cnt = int(m_cnt.group(1) or m_cnt.group(2)) if m_cnt else 0
                if cnt == 0 and ":" in cleaned_main:
                    cnt = _extract_year_count(cleaned_main.split(":", 1)[1])
                if cnt > 0:
                    _add_trophy(list_honours, current_comp, cnt, allow_sum_distinct=False)

    # ==================== 3. دمج نتائج الجداول والقوائم دون مضاعفة أي بطولة ====================
    merged = {}
    for src_d in (table_honours, list_honours):
        for title_k, obj in src_d.items():
            if title_k in merged:
                merged[title_k]["count"] = max(merged[title_k]["count"], obj["count"])
            else:
                merged[title_k] = {
                    "title": obj["title"],
                    "count": obj["count"],
                    "category": obj["category"],
                }

    out_list = list(merged.values())
    out_list.sort(key=lambda x: x["count"], reverse=True)
    return out_list


def _fetch_wikipedia_entity_dossier(entity_type: str, raw_q: str, ar_title: str):
    """سحب الألقاب والهداف التاريخي والأكثر مشاركة والملعب والتأسيس حياً من Wikipedia API (HTML + Infobox)"""
    info = {
        "founded": "",
        "stadium": "",
        "bio": "",
        "image": "",
        "top_scorer": "",
        "most_apps": "",
        "most_assists": "",
        "honours": [],
    }

    en_page = _resolve_en_wiki_page_title(entity_type, raw_q)
    enc_page = urllib.parse.quote(en_page.replace(" ", "_"))

    # 1. جلب فهرس الأقسام + صندوق المعلومات (القسم 0) + النبذة العربية بالتوازي
    def _fetch_ar_summary():
        ar_candidates = (
            [f"منتخب_{ar_title}_لكرة_القدم", ar_title]
            if entity_type == "nation"
            else [f"نادي_{ar_title}", ar_title, raw_q]
        )
        for ar_pg in ar_candidates:
            ar_sum_url = f"https://ar.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(ar_pg.replace(' ', '_'))}"
            s_data = fetch_wiki_api_json(ar_sum_url, timeout=3.5)
            if isinstance(s_data, dict) and s_data.get("extract"):
                return s_data
        return {}

    with ThreadPoolExecutor(max_workers=3) as ex:
        f_sec = ex.submit(
            fetch_wiki_api_json,
            f"https://en.wikipedia.org/w/api.php?action=parse&page={enc_page}&prop=sections&format=json&redirects=1",
            5.0,
        )
        f_intro = ex.submit(
            fetch_wiki_api_json,
            f"https://en.wikipedia.org/w/api.php?action=parse&page={enc_page}&section=0&prop=wikitext&format=json&redirects=1",
            5.0,
        )
        f_ar = ex.submit(_fetch_ar_summary)

        sec_json = f_sec.result() or {}
        intro_json = f_intro.result() or {}
        ar_sum = f_ar.result() or {}

    if ar_sum.get("extract"):
        info["bio"] = ar_sum["extract"]
        if isinstance(ar_sum.get("thumbnail"), dict):
            info["image"] = ar_sum["thumbnail"].get("source", "")

    def clean_w_val(v):
        v = re.sub(r'<ref[^>]*>.*?</ref>', '', v, flags=re.DOTALL)
        v = re.sub(r'<ref[^/>]*/>', '', v)
        v = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', v)
        v = re.sub(r'\{\{(?:nowrap|small|abbr)\|([^}|]+)[^}]*\}\}', r'\1', v, flags=re.IGNORECASE)
        v = re.sub(r'\{\{[^}]*\}\}|<[^>]+>', '', v)
        return re.sub(r'\s+', ' ', v).strip(" |,-*")

    # 2. قراءة صندوق المعلومات (تم إصلاح الخطأ الذي كان يقطع النص عند رمز | داخل الروابط)
    intro_wtxt = ((intro_json.get("parse") or {}).get("wikitext") or {}).get("*") or ""
    if intro_wtxt:
        m_gr = re.search(r'^\|\s*(?:ground|stadium)\s*=\s*([^\n]+)', intro_wtxt, re.IGNORECASE | re.MULTILINE)
        if m_gr:
            info["stadium"] = clean_w_val(m_gr.group(1))

        m_fn = re.search(r'^\|\s*founded\s*=\s*([^\n]+)', intro_wtxt, re.IGNORECASE | re.MULTILINE)
        if m_fn:
            yr_m = re.search(r'\b(18\d{2}|19\d{2}|20\d{2})\b', m_fn.group(1))
            if yr_m:
                info["founded"] = yr_m.group(1)

        m_sc = re.search(r'^\|\s*(?:top\s*scorer|most\s*goals)\s*=\s*([^\n]+)', intro_wtxt, re.IGNORECASE | re.MULTILINE)
        if m_sc:
            info["top_scorer"] = clean_w_val(m_sc.group(1))

        m_cp = re.search(r'^\|\s*(?:most\s*caps|most\s*appearances)\s*=\s*([^\n]+)', intro_wtxt, re.IGNORECASE | re.MULTILINE)
        if m_cp:
            info["most_apps"] = clean_w_val(m_cp.group(1))

    # 3. العثور بدقة على رقم قسم Honours الحقيقي (بدون الخلط مع Competitive record) وجلب الـ HTML المُعالج له
    sections = ((sec_json.get("parse") or {}).get("sections")) or []
    honours_sec_idx = None
    for s_obj in sections:
        s_line = re.sub(r'<[^>]+>', '', str(s_obj.get("line") or "")).strip().lower()
        if s_line in ("honours", "honors", "major honours", "major honors", "titles", "achievements", "club honours", "team honours"):
            honours_sec_idx = s_obj.get("index")
            break
    if not honours_sec_idx:
        for s_obj in sections:
            s_line = re.sub(r'<[^>]+>', '', str(s_obj.get("line") or "")).strip().lower()
            if ("honour" in s_line or "honor" in s_line) and "individual" not in s_line and "player" not in s_line:
                honours_sec_idx = s_obj.get("index")
                break

    if honours_sec_idx:
        h_data = fetch_wiki_api_json(
            f"https://en.wikipedia.org/w/api.php?action=parse&page={enc_page}&section={honours_sec_idx}&prop=text&format=json&redirects=1",
            timeout=6.0,
        )
        h_html = ((h_data or {}).get("parse") or {}).get("text", {}).get("*", "")
        if h_html:
            info["honours"] = _parse_wiki_honours_from_html(h_html, entity_type)

            # إذا كان قسم البطولات يحيل لصفحة فرعية (مثل List of ... honours) ولم نجد بطولات في القسم الرئيسي
            if not info["honours"]:
                m_main = re.search(r'href="/wiki/([^"]*(?:honour|honor|records_and_statistics)[^"]*)"', h_html, re.IGNORECASE)
                if m_main:
                    sub_page = m_main.group(1)
                    sub_sec = fetch_wiki_api_json(
                        f"https://en.wikipedia.org/w/api.php?action=parse&page={sub_page}&prop=sections&format=json&redirects=1",
                        timeout=4.5,
                    )
                    sub_idx = None
                    for ss in ((sub_sec or {}).get("parse") or {}).get("sections", []):
                        if "honour" in str(ss.get("line", "")).lower() or "honor" in str(ss.get("line", "")).lower():
                            sub_idx = ss.get("index")
                            break
                    if sub_idx:
                        sh_data = fetch_wiki_api_json(
                            f"https://en.wikipedia.org/w/api.php?action=parse&page={sub_page}&section={sub_idx}&prop=text&format=json&redirects=1",
                            timeout=5.0,
                        )
                        sh_html = ((sh_data or {}).get("parse") or {}).get("text", {}).get("*", "")
                        if sh_html:
                            info["honours"] = _parse_wiki_honours_from_html(sh_html, entity_type)

    return info


def get_live_entity_card_detail(entity_type: str, name: str, extra: str = ""):
    """سحب خزانة البطولات الدقيقة والهداف التاريخي والأكثر مشاركة وصناعة حياً من Wikipedia + Transfermarkt"""
    _purge_legacy_cards_cache_once()
    e_type = (entity_type or "club").lower()
    raw_q = (name or "").strip()
    extra_q = (extra or "").strip()

    cache_key = f"entity_dossier_live_v21_{e_type}_{hashlib.md5(f'{raw_q}_{extra_q}'.encode()).hexdigest()[:12]}"
    cached, is_fresh = get_from_cache(cache_key, ttl=86400 * 7)
    if cached and is_fresh and cached.get("honours_verified"):
        return cached

    ar_title = _clean_entity_name(raw_q) or raw_q
    if raw_q.lower() in ARABIC_MATCH_TEAM_ALIASES:
        ar_title = ARABIC_MATCH_TEAM_ALIASES[raw_q.lower()][0]

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_tm = ex.submit(_scrape_tm_verified_dossier, e_type, raw_q)
        fut_wk = ex.submit(_fetch_wikipedia_entity_dossier, e_type, raw_q, ar_title)
        tm_data = fut_tm.result() or {}
        wk_data = fut_wk.result() or {}

    tm_honours = tm_data.get("honours") or []
    wk_honours = wk_data.get("honours") or []

    # دمج ذكي يضمن أخذ أعلى عدد موثق لكل بطولة دون أي تكرار
    merged_h = {}
    for src_list in (wk_honours, tm_honours):
        for h_item in src_list:
            t_key = h_item["title"]
            if t_key in merged_h:
                merged_h[t_key]["count"] = max(merged_h[t_key]["count"], int(h_item.get("count", 0)))
            else:
                merged_h[t_key] = dict(h_item)

    honours_detailed = sorted(merged_h.values(), key=lambda x: x["count"], reverse=True)

    # دعم إضافي للمنتخبات من أرشيف النهائيات الحية
    if not honours_detailed and e_type == "nation":
        intl_finals = _fetch_wiki_international_finals_live() or []
        comp_counts = {}
        for f_row in intl_finals:
            w_name = (f_row.get("winner") or "").lower()
            if w_name in (raw_q.lower(), ar_title.lower()):
                c_title = f_row.get("comp") or "بطولة دولية"
                comp_counts[c_title] = comp_counts.get(c_title, 0) + 1
        for c_t, c_n in comp_counts.items():
            cat_t = "world" if "العالم" in c_t else "continental"
            honours_detailed.append({"title": f"{c_t} 🏆", "count": c_n, "category": cat_t})

    top_scorer = tm_data.get("top_scorer") or wk_data.get("top_scorer") or ""
    most_apps = tm_data.get("most_apps") or wk_data.get("most_apps") or ""
    most_assists = tm_data.get("most_assists") or wk_data.get("most_assists") or ""
    founded = wk_data.get("founded") or tm_data.get("founded") or ""
    stadium = wk_data.get("stadium") or tm_data.get("stadium") or ""

    total_trophies = sum(int(h.get("count", 0)) for h in honours_detailed)

    profile = {
        "entity_type": e_type,
        "title": ar_title,
        "raw_name": raw_q,
        "subtitle": f"الاتحاد القاري: {extra_q}" if e_type == "nation" else f"تأسس عام: {founded or '-'} • الملعب: {stadium or 'الملعب الرسمي'}",
        "image": tm_data.get("crest") or wk_data.get("image") or "",
        "founded": founded or "-",
        "stadium": stadium or ("الملعب الوطني" if e_type == "nation" else "الملعب الرسمي"),
        "total_trophies": total_trophies,
        "top_scorer": top_scorer or "موثق في السجل الرسمي",
        "most_assists": most_assists or "موثق في السجل الرسمي",
        "most_apps": most_apps or "موثق في السجل الرسمي",
        "honours_detailed": honours_detailed,
        "honours": [f"{h['title']} ({h['count']})" for h in honours_detailed],
        "bio": wk_data.get("bio") or f"الملف التاريخي والإحصائي الرسمي لـ ({ar_title}).",
        "honours_verified": True,
    }

    if total_trophies > 0 or wk_data.get("bio"):
        save_to_cache(cache_key, profile)
    return profile

def global_platform_search(query: str):
    q = (query or "").strip().lower()
    empty = {"clubs": [], "nations": [], "transfers": [], "news": []}
    if len(q) < 2:
        return empty

    clubs, nations, transfers, news = [], [], [], []
    seen_clubs, seen_nations = set(), set()

    with _CACHE_LOCK:
        cache_snapshot = list(_RAM_CACHE.items())
    for cache_key, entry in cache_snapshot:
        data = entry.get("data") if isinstance(entry, dict) else None
        if not data:
            continue

        if cache_key.startswith("standings_v4_") and isinstance(data, list):
            lg_code = cache_key.replace("standings_v4_", "")
            for row in data:
                if not isinstance(row, dict):
                    continue
                raw_n = str(row.get("team_name") or "")
                short_n = str(row.get("short_name") or raw_n)
                ar_n = _clean_entity_name(short_n) or short_n
                hay = f"{raw_n} {short_n} {ar_n}".lower()
                dedup = f"{lg_code}_{row.get('team_id') or short_n.lower()}"
                if q in hay and dedup not in seen_clubs:
                    seen_clubs.add(dedup)
                    clubs.append({
                        "league_code": lg_code,
                        "team_id": str(row.get("team_id") or ""),
                        "raw_name": raw_n,
                        "name": ar_n,
                        "crest": row.get("crest") or "",
                        "rank": row.get("rank", "-"),
                        "points": row.get("points", 0)
                    })

        elif cache_key.startswith("world_nations_live_api_") and isinstance(data, list):
            for n in data:
                if not isinstance(n, dict):
                    continue
                hay = f"{n.get('name', '')} {n.get('raw_name', '')} {n.get('confederation', '')}".lower()
                nk = str(n.get("raw_name") or n.get("name") or "").lower()
                if q in hay and nk not in seen_nations:
                    seen_nations.add(nk)
                    nations.append({
                        "name": n.get("name", ""),
                        "raw_name": n.get("raw_name", ""),
                        "flag_url": n.get("flag_url", ""),
                        "confederation": n.get("confederation", "FIFA"),
                        "rank": n.get("rank", "-")
                    })

        elif cache_key.startswith("global_mercato_verified_") and isinstance(data, dict):
            for item in (data.get("transfers") or []) + (data.get("contracts") or []):
                if not isinstance(item, dict):
                    continue
                hay = f"{item.get('name', '')} {item.get('from_club', '')} {item.get('to_club', '')}".lower()
                if q in hay:
                    transfers.append({
                        "id": item.get("id", ""),
                        "name": item.get("name", ""),
                        "from_club": item.get("from_club", ""),
                        "to_club": item.get("to_club", ""),
                        "status_label": item.get("status_label", "")
                    })

        elif cache_key == "global_sports_news" and isinstance(data, list):
            for art in data:
                if not isinstance(art, dict):
                    continue
                hay = f"{art.get('title', '')} {art.get('summary', '')}".lower()
                if q in hay:
                    news.append({
                        "title": art.get("title", ""),
                        "published_time": art.get("published_time", ""),
                        "source_url": art.get("source_url", "")
                    })

    return {
        "clubs": clubs[:6],
        "nations": nations[:5],
        "transfers": transfers[:5],
        "news": news[:5]
    }


def get_club_recent_results(league_code: str, team_id: str):
    code = (league_code or "PL").upper()
    tid = str(team_id or "").strip()
    if not tid:
        return []

    cache_key = f"club_recent_v1_{code}_{tid}"
    cached, is_fresh = get_from_cache(cache_key, ttl=1800)
    if cached and is_fresh:
        return cached

    espn_code = LEAGUE_CODES.get(code, {}).get("espn", "eng.1")
    urls = [
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams/{tid}/schedule",
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{tid}/schedule"
    ]

    events = []
    for u in urls:
        data = fetch_json_fast(u, timeout=4.0)
        if isinstance(data, dict) and isinstance(data.get("events"), list) and data["events"]:
            events = data["events"]
            break

    completed = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        comps = ev.get("competitions") or []
        if not comps or not isinstance(comps[0], dict):
            continue
        comp = comps[0]
        state = comp.get("status", {}).get("type", {}).get("state", "")
        if state != "post":
            continue

        competitors = comp.get("competitors") or []
        my_side, opp_side = None, None
        for c in competitors:
            c_tid = str((c.get("team") or {}).get("id") or c.get("id") or "")
            if c_tid == tid:
                my_side = c
            else:
                opp_side = c

        if not my_side or not opp_side:
            continue

        my_sc = _safe_int((my_side.get("score") or {}).get("value") if isinstance(my_side.get("score"), dict) else my_side.get("score"), 0)
        opp_sc = _safe_int((opp_side.get("score") or {}).get("value") if isinstance(opp_side.get("score"), dict) else opp_side.get("score"), 0)

        res_letter = "W" if my_sc > opp_sc else ("L" if my_sc < opp_sc else "D")
        opp_team = opp_side.get("team") or {}
        opp_name = _clean_entity_name(opp_team.get("shortDisplayName") or opp_team.get("displayName") or "الخصم")
        opp_logos = opp_team.get("logos") or []
        opp_crest = opp_logos[0].get("href", "") if (opp_logos and isinstance(opp_logos[0], dict)) else (opp_team.get("logo") or "")

        completed.append({
            "sort_date": ev.get("date", ""),
            "date": (ev.get("date") or "")[:10],
            "is_home": my_side.get("homeAway") == "home",
            "opponent": opp_name,
            "opponent_crest": opp_crest,
            "score": f"{my_sc} - {opp_sc}",
            "result": res_letter
        })

    completed.sort(key=lambda x: x["sort_date"], reverse=True)
    recent_5 = completed[:5]
    if recent_5:
        save_to_cache(cache_key, recent_5)
    return recent_5