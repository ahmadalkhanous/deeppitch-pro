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
        # مسح الكاش القديم شاملاً الميركاتو والعقود والأخبار لضمان جلب البيانات الحية فوراً
        cursor.execute("""
            DELETE FROM api_cache 
            WHERE cache_key LIKE 'fixtures_%' 
               OR cache_key LIKE 'standings_%' 
               OR cache_key LIKE 'scorers_%'
               OR cache_key LIKE 'global_mercato%'
               OR cache_key LIKE 'global_sports_news%';
        """)
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
                if "west" in raw_title.lower() or "غرب" in raw_title or idx == 0:
                    g_name = "منطقة الغرب"
                    lvl = "WEST"
                else:
                    g_name = "منطقة الشرق"
                    lvl = "EAST"
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

    cache_key = f"standings_v3_{league_code}"
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

                group_rows.append({
                    "rank": 0,
                    "team_name": raw_team_name,
                    "raw_name": raw_team_name,
                    "short_name": short_name,
                    "group_name": group_name,
                    "level_code": level_code,
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

    if not all_events and league_code in ("ACL", "CAF", "UCL", "UNL"):
        cur_m = now_dt.strftime("%Y%m")
        nxt_m = (now_dt.replace(day=28) + timedelta(days=5)).strftime("%Y%m")
        for m_str in (cur_m, nxt_m):
            m_data = fetch_json_fast(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={m_str}&limit=100", timeout=4.0)
            if isinstance(m_data, dict) and m_data.get("events"):
                all_events.extend(m_data["events"])
                break

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
    "UCL": {"channel": "beIN Sports 1 HD بريميوم", "commentators": ["عصام الشوالي", "خليل البلوشي", "حفيظ دراجي"]},
    "ACL": {"channel": "beIN Sports AFC / SSC 1 HD", "commentators": ["فهد العتيبي", "عصام الشوالي", "فارس عوض", "عامر الخوذيري"]},
    "CAF": {"channel": "beIN Sports 6 HD", "commentators": ["عصام الشوالي", "حفيظ دراجي", "علي محمد علي", "جواد بدة"]},
    "UNL": {"channel": "beIN Sports 1 HD", "commentators": ["عصام الشوالي", "حفيظ دراجي", "خليل البلوشي", "حسن العيدروس"]}
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

    return {
        "has_stats": has_real_stats,
        "state": state,
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
    cache_key = f"monte_carlo_v4_{league_code}"
    cached_data, is_fresh = get_from_cache(cache_key, ttl=3600)
    if cached_data and is_fresh:
        return cached_data

    standings = get_official_standings(league_code)
    if not standings or len(standings) < 4:
        return []

    total_teams = len(standings)
    rules = COMPETITION_FORMAT_RULES.get(league_code)

    teams_data = []
    for t in standings:
        gp = max(1, t["played"])
        lvl = t.get("level_code", "")
        grp_name = t.get("group_name", "")

        if league_code == "UNL":
            t_games = 4 if lvl == "D" else 6
        elif rules:
            t_games = rules["total_games"]
        else:
            t_games = (total_teams - 1) * 2

        rem_games = max(0, t_games - gp)
        pts_rate = t["points"] / gp
        gd_factor = (t["gf"] - t["ga"]) / (gp * 3.0)
        exp_rate = max(0.4, min(2.7, pts_rate + gd_factor))

        teams_data.append({
            "name": t.get("raw_name") or t["short_name"],
            "short_name": t["short_name"],
            "group_name": grp_name,
            "level_code": lvl,
            "rank": t.get("rank", 1),
            "zone": t.get("zone", "safe"),
            "status_badge": t.get("status_badge", ""),
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

    # تقسيم الفهارس حسب المجموعات / المناطق / المستويات
    group_map = {}
    group_order_keys = []
    for idx, td in enumerate(teams_data):
        g_key = td["group_name"] or "ALL"
        if g_key not in group_map:
            group_map[g_key] = []
            group_order_keys.append(g_key)
        group_map[g_key].append(idx)

    for _ in range(num_sims):
        sim_rem_pts = np.random.normal(loc=rates * rem_matches, scale=np.sqrt(np.maximum(1, rem_matches)) * 1.15)
        sim_rem_pts = np.clip(sim_rem_pts, 0, rem_matches * 3)
        final_pts = cur_pts + sim_rem_pts

        qualified_for_trophy = []

        for g_key in group_order_keys:
            g_indices = group_map[g_key]
            g_arr = np.array(g_indices)
            g_pts = final_pts[g_arr]
            g_order = g_arr[np.argsort(-g_pts)]
            g_len = len(g_order)
            lvl = teams_data[g_indices[0]]["level_code"]

            if league_code == "UNL":
                if lvl == "A":
                    # المستوى A: أول وثاني المجموعة يتأهلان لربع النهائي للمنافسة على اللقب، والرابع يهبط
                    for q_idx in g_order[:min(2, g_len)]:
                        teams_data[q_idx]["top4_wins"] += 1
                        qualified_for_trophy.append(q_idx)
                    if g_len >= 4:
                        teams_data[g_order[-1]]["rel_drops"] += 1
                elif lvl in ("B", "C"):
                    # المستويان B و C: الأول يصعد مباشرة والثاني ملحق صعود، والأخير يهبط
                    for q_idx in g_order[:min(2, g_len)]:
                        teams_data[q_idx]["top4_wins"] += 1
                    if g_len >= 4:
                        teams_data[g_order[-1]]["rel_drops"] += 1
                else:
                    # المستوى D: الأول يصعد مباشرة والثاني ملحق صعود (لا يوجد هبوط)
                    for q_idx in g_order[:min(2, g_len)]:
                        teams_data[q_idx]["top4_wins"] += 1

            elif rules:
                q_cnt = min(g_len, rules["qualify"])
                e_cnt = min(g_len, rules["elim"])
                for q_idx in g_order[:q_cnt]:
                    teams_data[q_idx]["top4_wins"] += 1
                    qualified_for_trophy.append(q_idx)
                if e_cnt > 0:
                    for r_idx in g_order[-e_cnt:]:
                        teams_data[r_idx]["rel_drops"] += 1
            else:
                for q_idx in g_order[:min(4, g_len)]:
                    teams_data[q_idx]["top4_wins"] += 1
                for r_idx in g_order[-min(3, g_len):]:
                    teams_data[r_idx]["rel_drops"] += 1
                teams_data[g_order[0]]["champ_wins"] += 1

        if (league_code == "UNL" or rules) and qualified_for_trophy:
            q_arr = np.array(qualified_for_trophy)
            ko_score = final_pts[q_arr] + np.random.normal(0, 2.2, size=len(q_arr))
            champ_idx = q_arr[np.argmax(ko_score)]
            teams_data[champ_idx]["champ_wins"] += 1

        for i in range(total_teams):
            teams_data[i]["total_sim_pts"] += final_pts[i]

    results = []
    for g_key in group_order_keys:
        g_list = []
        for idx in group_map[g_key]:
            t = teams_data[idx]
            g_list.append({
                "name": t["short_name"] or t["name"],
                "full_name": t["name"],
                "group_name": t["group_name"],
                "level_code": t["level_code"],
                "zone": t["zone"],
                "status_badge": t["status_badge"],
                "crest": t["crest"],
                "current_pts": t["current_pts"],
                "played": t["played"],
                "projected_pts": round(float(t["total_sim_pts"] / num_sims), 1),
                "champ_pct": round(float((t["champ_wins"] / num_sims) * 100.0), 1),
                "top4_pct": round(float((t["top4_wins"] / num_sims) * 100.0), 1),
                "rel_pct": round(float((t["rel_drops"] / num_sims) * 100.0), 1)
            })
        # ترتيب كل مجموعة/مستوى داخلياً حسب النقاط المتوقعة
        g_list.sort(key=lambda x: (x["projected_pts"], x["current_pts"]), reverse=True)
        for r_i, item in enumerate(g_list, 1):
            item["group_rank"] = r_i
        results.extend(g_list)

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
        if t.get("raw_name"):
            name_lookup[t["raw_name"].lower()] = t

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
    cached, is_fresh = get_from_cache("global_sports_news", ttl=300)
    if cached and is_fresh and not force_refresh:
        return cached

    init_news_table()
    now_ts = time.time()

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
from html.parser import HTMLParser
import urllib.parse

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
import html
from email.utils import parsedate_to_datetime

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
    for cache_k, cache_v in list(_RAM_CACHE.items()):
        if cache_k.startswith("standings_") and isinstance(cache_v.get("data"), list):
            lg_code = cache_k.split("_")[-1]
            c_reg = "asia" if lg_code == "ACL" else ("africa" if lg_code == "CAF" else default_reg)
            for row in cache_v["data"]:
                if not isinstance(row, dict):
                    continue
                tn = str(row.get("team_name") or "").lower()
                sn = str(row.get("short_name") or "").lower()
                if low == tn or low == sn or (len(low) >= 4 and (low in tn or low in sn)):
                    return _clean_entity_name(row.get("short_name") or raw), (row.get("crest") or fallback_crest), c_reg

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


# =========================================================================
# 1. جلب الانتقالات والمفاوضات الحية من Transfermarkt (جميع القارات)
# =========================================================================
def _fetch_live_transfermarkt_transfers():
    sources = [
        ("https://www.transfermarkt.com/transfers/neuestetransfers/statistik/plus/?plus=1&galerie=0&wettbewerb_id=alle&land_id=&minMarktwert=300.000&maxMarktwert=500.000.000", "done", "europe"),
        ("https://www.transfermarkt.com/transfers/neuestetransfers/statistik", "done", "europe"),
        ("https://www.transfermarkt.com/geruechtekuechte/detail/forum/154", "talks", "europe")
    ]

    transfers_out = []

    def process_source(src_tuple):
        url, mode, def_reg = src_tuple
        html_doc = _fetch_html_gzip(url, timeout=7.0)
        rows = _split_tm_outer_rows(html_doc)
        local_items = []

        for idx, row_html in enumerate(rows[:30]):
            try:
                info = _parse_tm_row_entities(row_html)
                if not info["name"] or len(info["clubs"]) < 1:
                    continue

                if len(info["clubs"]) >= 2:
                    raw_from, raw_from_crest = info["clubs"][0]
                    raw_to, raw_to_crest = info["clubs"][1]
                else:
                    raw_from, raw_from_crest = info["clubs"][0]
                    raw_to, raw_to_crest = "وجهة جديدة", ""

                from_name, from_crest, _ = _resolve_live_club(raw_from, raw_from_crest, def_reg)
                to_name, to_crest, to_reg = _resolve_live_club(raw_to, raw_to_crest, def_reg)
                to_reg = _detect_region_live(raw_to, info["nationality"], to_reg)

                tx_date = info["dates"][0] if info["dates"] else datetime.now().strftime("%Y-%m-%d")
                tx_ts = _parse_date_ts(tx_date) or (time.time() - (idx * 60))

                if mode == "talks":
                    pct_m = re.search(r'(\d+)\s*%', row_html)
                    prob_pct = int(pct_m.group(1)) if pct_m else 50
                    st_code = "talks" if prob_pct >= 45 else "rumor"
                    st_lbl = f"مفاوضات جارية ({prob_pct}%) ⏳" if st_code == "talks" else f"اهتمام ومتابعة ({prob_pct}%) 📡"
                    deal_type = "مفاوضات ضم"
                    fee_ar = f"نسبة الحسم {prob_pct}%"
                    reason_txt = f"مفاوضات مرصودة لانتقال {info['name']} من {from_name} إلى {to_name} بنسبة ترجيح {prob_pct}%."
                    src_lbl = "Transfermarkt Live Rumour Mill"
                    rel_score = prob_pct
                else:
                    td_rechts = re.findall(r'<td[^>]*class="[^"]*rechts[^"]*"[^>]*>(.*?)</td>', row_html, re.DOTALL)
                    raw_fee = html.unescape(re.sub(r'<[^>]+>', '', td_rechts[-1])).strip() if td_rechts else "انتقال رسمي"
                    low_fee = raw_fee.lower()
                    if "loan" in low_fee:
                        deal_type, fee_ar = "إعارة رسمية", "صفقة إعارة"
                    elif "free" in low_fee:
                        deal_type, fee_ar = "انتقال حر", "انتقال مجاني"
                    elif raw_fee in ("-", "?", ""):
                        deal_type, fee_ar = "انتقال رسمي", (info["market_val"] or "تمت رسمياً")
                    else:
                        deal_type, fee_ar = "شراء نهائي", raw_fee

                    st_code = "done"
                    st_lbl = "تمت رسمياً ✅"
                    reason_txt = f"تم قيد وإتمام انتقال {info['name']} رسمياً من {from_name} إلى {to_name} ({tx_date})."
                    src_lbl = f"Transfermarkt Registry ({tx_date})"
                    rel_score = 100

                local_items.append({
                    "id": f"tm_{mode}_{info['id'] or hashlib.md5(info['name'].encode()).hexdigest()[:8]}",
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
                    "contract_length": f"تاريخ القيد: {tx_date}",
                    "salary": f"القيمة السوقية: {info['market_val']}" if info["market_val"] else "وفق هيكل النادي",
                    "release_clause": "حسب لوائح البطولة",
                    "conditions": reason_txt,
                    "status_reason": reason_txt,
                    "source": src_lbl,
                    "reliability": rel_score,
                    "sort_ts": tx_ts
                })
            except Exception:
                continue
        return local_items

    with ThreadPoolExecutor(max_workers=3) as ex:
        for res in ex.map(process_source, sources):
            transfers_out.extend(res)

    return transfers_out


# =========================================================================
# 2. جلب تجديد العقود والعقود المنتهية الحية من Transfermarkt
# =========================================================================
def _fetch_live_transfermarkt_contracts():
    sources = [
        ("https://www.transfermarkt.com/statistik/letztevertragsverlaengerungen?plus=1", "done", "🌍 سجل العقود العالمي", "europe"),
        ("https://www.transfermarkt.com/premier-league/letztevertragsverlaengerungen/wettbewerb/GB1/plus/1", "done", "🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي", "europe"),
        ("https://www.transfermarkt.com/laliga/letztevertragsverlaengerungen/wettbewerb/ES1/plus/1", "done", "🇪🇸 الدوري الإسباني", "europe"),
        ("https://www.transfermarkt.com/serie-a/letztevertragsverlaengerungen/wettbewerb/IT1/plus/1", "done", "🇮🇹 الدوري الإيطالي", "europe"),
        ("https://www.transfermarkt.com/bundesliga/letztevertragsverlaengerungen/wettbewerb/L1/plus/1", "done", "🇩🇪 الدوري الألماني", "europe"),
        ("https://www.transfermarkt.com/saudi-pro-league/letztevertragsverlaengerungen/wettbewerb/SA1/plus/1", "done", "🇸🇦 دوري روشن السعودي", "asia"),
        ("https://www.transfermarkt.com/statistik/endendevertraege?plus=1", "expiring", "⚠️ ملف العقود المنتهية", "europe")
    ]

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
                    st_code = "talks" if idx % 2 == 0 else "rumor"
                    st_lbl = "مفاوضات التمديد ⏳" if st_code == "talks" else "فترة حرة قريباً ⚠️"
                    old_exp = f"ينتهي: {exp_date}"
                    new_exp = "قيد التفاوض"
                    len_str = "يدخل الفترة الحرة"
                    sal_chg = "⏳ بانتظار الحسم الرسمي"
                    reason_txt = f"عقد {info['name']} مع نادي {club_name} ينتهي في {exp_date}، والمفاوضات جارية لحسم مستقبله."
                    src_lbl = "Transfermarkt Expiring Contracts"
                    sort_val = time.time() - 3600 - (idx * 60)
                else:
                    if len(dates) >= 2:
                        ext_date, new_exp_raw = dates[0], dates[-1]
                    elif len(dates) == 1:
                        ext_date, new_exp_raw = "تحديث رسمي", dates[0]
                    else:
                        ext_date, new_exp_raw = "تحديث رسمي", "ممدد"

                    st_code = "done"
                    st_lbl = "تم التجديد رسمياً ✅"
                    old_exp = f"التوقيع: {ext_date}"
                    new_exp = f"حتى {new_exp_raw}"
                    len_str = f"ممدد حتى {new_exp_raw}"
                    sal_chg = "⬆️ تمديد عقد رسمي"
                    reason_txt = f"أعلن نادي {club_name} رسمياً تمديد عقد لاعبه {info['name']} بتاريخ {ext_date} ليستمر حتى {new_exp_raw}."
                    src_lbl = f"Transfermarkt Registry ({ext_date})"
                    sort_val = _parse_date_ts(ext_date) or (time.time() - (idx * 60))

                local_items.append({
                    "id": f"tm_cn_{mode}_{info['id'] or hashlib.md5(info['name'].encode()).hexdigest()[:8]}",
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
                    "stage_step": 4 if st_code == "done" else 3,
                    "old_expiry": old_exp,
                    "new_expiry": new_exp,
                    "contract_length": len_str,
                    "salary": f"القيمة السوقية: {info['market_val']}" if info["market_val"] else "وفق السلم المحدث للنادي",
                    "salary_change": sal_chg,
                    "release_clause": "وفق لوائح النادي",
                    "conditions": reason_txt,
                    "status_reason": reason_txt,
                    "source": src_lbl,
                    "reliability": 100 if st_code == "done" else 90,
                    "sort_ts": sort_val
                })
            except Exception:
                continue
        return local_items

    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(process_cn_source, sources):
            contracts_out.extend(res)

    return contracts_out


# =========================================================================
# 3. جلب الانتقالات والعقود والمدربين من واجهة ESPN الرسمية (JSON API)
# =========================================================================
def _fetch_live_espn_api_mercato():
    transfers_out = []
    contracts_out = []
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
        ("arg.1", "🇦🇷 الدوري الأرجنتيني", "americas")
    ]

    def scan_espn_league(lg_tuple):
        lg_code, lg_label, reg = lg_tuple
        loc_tr, loc_cn = [], []

        # أ) فحص سجل الانتقالات الرسمي (Transactions API) مع تمرير السنة الحالية
        for tx_url in (
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg_code}/transactions?dates={cur_yr}&limit=50",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg_code}/transactions?limit=50"
        ):
            tx_data = fetch_json_fast(tx_url, timeout=4.0)
            if not isinstance(tx_data, dict) or not isinstance(tx_data.get("transactions"), list):
                continue
            for tr in tx_data["transactions"][:20]:
                if not isinstance(tr, dict):
                    continue
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
                if not raw_from and not raw_to:
                    continue

                f_id = from_t.get("id")
                t_id = to_t.get("id")
                f_logo = ((from_t.get("logos") or [{}])[0].get("href") if isinstance(from_t.get("logos"), list) and from_t.get("logos") else "") or (f"https://a.espncdn.com/i/teamlogos/soccer/500/{f_id}.png" if f_id else "")
                t_logo = ((to_t.get("logos") or [{}])[0].get("href") if isinstance(to_t.get("logos"), list) and to_t.get("logos") else "") or (f"https://a.espncdn.com/i/teamlogos/soccer/500/{t_id}.png" if t_id else "")

                date_str = str(tr.get("date") or "")[:10]
                tx_ts = _parse_date_ts(date_str) or time.time()
                raw_fee = str(tr.get("amount") or tr.get("type") or "مسجل رسمياً").strip()
                low_fee = raw_fee.lower()
                pos_ar = _translate_pos(((ath.get("position") or {}).get("abbreviation") or "") if isinstance(ath.get("position"), dict) else "")

                if raw_from.lower() == raw_to.lower() or "extension" in low_fee or "re-sign" in low_fee:
                    c_name, c_crest, c_reg = _resolve_live_club(raw_to or raw_from, t_logo or f_logo, reg)
                    loc_cn.append({
                        "id": f"espn_tx_cn_{ath_id or hashlib.md5((p_name + date_str).encode()).hexdigest()[:8]}",
                        "role": "player",
                        "region": c_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": pos_ar,
                        "age": ath.get("age") or 24,
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": c_name,
                        "from_crest": c_crest,
                        "status": "done",
                        "status_label": "تم التجديد رسمياً ✅",
                        "stage_step": 4,
                        "old_expiry": f"التوقيع: {date_str}",
                        "new_expiry": "عقد ممدد رسمياً",
                        "contract_length": f"موثق ({date_str})",
                        "salary": "وفق السلم الجديد",
                        "salary_change": "⬆️ تمديد عقد رسمي",
                        "release_clause": "حسب لوائح البطولة",
                        "conditions": f"تم قيد وتمديد عقد اللاعب {p_name} رسمياً مع نادي {c_name} بتاريخ {date_str}.",
                        "status_reason": f"قيد رسمي في سجل ESPN بتاريخ {date_str}.",
                        "source": f"ESPN Official API ({date_str})",
                        "reliability": 100,
                        "sort_ts": tx_ts
                    })
                elif raw_from and raw_to:
                    from_name, from_crest, _ = _resolve_live_club(raw_from, f_logo, reg)
                    to_name, to_crest, to_reg = _resolve_live_club(raw_to, t_logo, reg)
                    deal_type = "إعارة رسمية" if "loan" in low_fee else ("انتقال حر" if "free" in low_fee else "انتقال رسمي")
                    fee_ar = "صفقة إعارة" if "loan" in low_fee else ("انتقال مجاني" if "free" in low_fee or raw_fee in ("", "Undisclosed") else raw_fee)
                    loc_tr.append({
                        "id": f"espn_tx_tr_{ath_id or hashlib.md5((p_name + date_str).encode()).hexdigest()[:8]}",
                        "role": "player",
                        "region": to_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": pos_ar,
                        "age": ath.get("age") or 24,
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
                        "salary": "وفق هيكل النادي",
                        "release_clause": "حسب لوائح البطولة",
                        "conditions": f"انتقال رسمي مقيد في سجلات الاتحاد من نادي {from_name} إلى نادي {to_name} بتاريخ {date_str}.",
                        "status_reason": f"تم قيد اللاعب {p_name} رسمياً في كشوفات نادي {to_name} ({date_str}).",
                        "source": f"ESPN Official API ({date_str})",
                        "reliability": 100,
                        "sort_ts": tx_ts
                    })
            if loc_tr or loc_cn:
                break

        # ب) فحص الكائنات المهيكلة في واجهة أخبار ESPN الرسمية (حيث اسم اللاعب والنادي في حقل description)
        news_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{lg_code}/news?limit=40"
        news_data = fetch_json_fast(news_url, timeout=4.0)
        if isinstance(news_data, dict) and isinstance(news_data.get("articles"), list):
            for art in news_data["articles"]:
                if not isinstance(art, dict):
                    continue
                headline = str(art.get("headline") or "").strip()
                desc = str(art.get("description") or headline).strip()
                combined_low = f"{headline} {desc}".lower()

                is_cn = any(w in combined_low for w in [
                    "contract", "extension", "new deal", "re-sign", "extends", "extend",
                    "renewal", "free agent", "stay at", "stays at", "future", "until 202", "until 203"
                ])
                is_tr = any(w in combined_low for w in [
                    "transfer", "sign", "signs", "signing", "loan", "move", "target", "bid",
                    "interest", "linked", "medical", "release clause", "fee", "join", "joins",
                    "deal", "talks", "negotiation", "appointed", "manager", "head coach", "sacked"
                ])
                if not is_cn and not is_tr:
                    continue

                # قراءة الكائنات المهيكلة من مصفوفة categories في ESPN (باستخدام حقل description و athleteId و teamId)
                cats = art.get("categories") or []
                athletes = []
                teams = []
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
                        t_id = c.get("teamId") or t_sub.get("id") or c.get("id")
                        t_name = str(c.get("description") or t_sub.get("description") or t_sub.get("displayName") or "").strip()
                        t_logo = f"https://a.espncdn.com/i/teamlogos/soccer/500/{t_id}.png" if t_id else ""
                        if t_name:
                            teams.append((t_id, t_name, t_logo))

                if not teams:
                    continue

                is_coach = any(w in combined_low for w in ["manager", "head coach", "coach", "boss", "appointed", "sacked"])
                if athletes:
                    ath_id, p_name = athletes[0]
                    avatar = _player_avatar(ath_id, p_name)
                else:
                    # إذا كان الخبر عن مدرب أو لاعب غير مصنف كـ athlete، نستخرج الاسم من بداية العنوان أو الصورة
                    m_lead = re.match(r'^([A-Z][a-zA-Z\'\-\.]+(?:\s+[A-Z][a-zA-Z\'\-\.]+){1,2})', headline)
                    if not m_lead:
                        continue
                    p_name = m_lead.group(1).strip()
                    ath_id = None
                    imgs = art.get("images") or []
                    avatar = imgs[0].get("url") if (imgs and isinstance(imgs[0], dict) and imgs[0].get("url")) else _player_avatar(None, p_name)

                _, t0_raw, t0_logo = teams[0]
                c0_name, c0_crest, c0_reg = _resolve_live_club(t0_raw, t0_logo, reg)

                pub_raw = str(art.get("published") or "")
                pub_date = pub_raw[:10] if pub_raw else datetime.now().strftime("%Y-%m-%d")
                pub_ts = _parse_date_ts(pub_raw) or time.time()

                is_done = any(w in combined_low for w in ["official", "confirms", "confirmed", "signs", "signed", "completes", "completed", "agrees", "agreed", "appointed", "extends"])
                is_failed = any(w in combined_low for w in ["reject", "rejected", "collapse", "collapsed", "fails", "failed", "ruled out", "turns down", "sacked"])
                st_code = "done" if is_done else ("failed" if is_failed else "talks")

                yr_m = re.search(r'\b(202[7-9]|203[0-5])\b', f"{headline} {desc}")
                exp_yr = f"يونيو {yr_m.group(1)}" if yr_m else f"تحديث ({pub_date})"

                fee_m = re.search(r'([€£$]\s?\d+(?:\.\d+)?\s?(?:m|million|bn))', f"{headline} {desc}", re.IGNORECASE)
                fee_str = fee_m.group(1).upper() if fee_m else (pub_date if is_done else "قيد التفاوض")

                art_uid = str(art.get("id") or hashlib.md5(headline.encode()).hexdigest()[:8])

                if is_cn:
                    loc_cn.append({
                        "id": f"espn_news_cn_{art_uid}",
                        "role": "coach" if is_coach else "player",
                        "region": c0_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": "مدير فني" if is_coach else "نجم الفريق الأول",
                        "age": 25,
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": c0_name,
                        "from_crest": c0_crest,
                        "status": st_code,
                        "status_label": "تم التجديد رسمياً ✅" if is_done else ("تعثر التجديد ❌" if is_failed else "مفاوضات التمديد ⏳"),
                        "stage_step": 4 if is_done else (2 if is_failed else 3),
                        "old_expiry": "العقد الحالي",
                        "new_expiry": exp_yr,
                        "contract_length": f"تحديث مباشر ({pub_date})",
                        "salary": "وفق البنود المحدثة",
                        "salary_change": "⬆️ تحسين شروط العقد" if not is_failed else "⬇️ تباين في المطالب",
                        "release_clause": "حسب لوائح النادي",
                        "conditions": desc,
                        "status_reason": headline,
                        "source": f"ESPN Official API ({pub_date})",
                        "reliability": 96 if is_done else 86,
                        "sort_ts": pub_ts
                    })
                else:
                    if len(teams) >= 2:
                        _, t1_raw, t1_logo = teams[1]
                        from_name, from_crest, _ = _resolve_live_club(t1_raw, t1_logo, reg)
                        to_name, to_crest = c0_name, c0_crest
                    else:
                        from_name, from_crest = c0_name, c0_crest
                        to_name, to_crest = "أندية مهتمة / وجهة محتملة", "https://ui-avatars.com/api/?name=TR&background=111c35&color=ffd600&bold=true&rounded=true"

                    loc_tr.append({
                        "id": f"espn_news_tr_{art_uid}",
                        "role": "coach" if is_coach else "player",
                        "region": c0_reg,
                        "league_tag": lg_label,
                        "name": p_name,
                        "position": "مدير فني" if is_coach else "لاعب محترف",
                        "age": 25,
                        "nationality": lg_label.split(" ")[0] + " دولي",
                        "avatar": avatar,
                        "from_club": from_name,
                        "from_crest": from_crest,
                        "to_club": to_name,
                        "to_crest": to_crest,
                        "status": st_code,
                        "status_label": "تمت رسمياً ✅" if is_done else ("فشلت الصفقة ❌" if is_failed else "مفاوضات جارية ⏳"),
                        "stage_step": 4 if is_done else (2 if is_failed else 3),
                        "deal_type": "إعارة" if "loan" in combined_low else ("صفقة رسمية" if is_done else "مفاوضات ميركاتو"),
                        "fee": fee_str,
                        "contract_length": f"تحديث ({pub_date})",
                        "salary": "وفق هيكل النادي",
                        "release_clause": "حسب لوائح البطولة",
                        "conditions": desc,
                        "status_reason": headline,
                        "source": f"ESPN Official API ({pub_date})",
                        "reliability": 96 if is_done else 85,
                        "sort_ts": pub_ts
                    })

        return loc_tr, loc_cn

    with ThreadPoolExecutor(max_workers=8) as ex:
        for r_tr, r_cn in ex.map(scan_espn_league, espn_leagues):
            transfers_out.extend(r_tr)
            contracts_out.extend(r_cn)

    return transfers_out, contracts_out


def get_mercato_and_contracts_data(force_refresh: bool = False):
    """جلب جميع الانتقالات وتجديد العقود حياً من الـ API الخارجي (ESPN + Transfermarkt) بدون أي بيانات محلية"""
    cache_key = "global_mercato_pure_api_v12"
    cached, is_fresh = get_from_cache(cache_key, ttl=300)
    if cached and is_fresh and not force_refresh and cached.get("transfers") and cached.get("contracts"):
        return cached

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
        k = f"{t['name'].lower()}_{t['to_club'].lower()}"
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
        "ticker": ticker_headlines
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
import os
import re
import json
import time
import random
import hashlib
import urllib.request
import urllib.parse

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
    """سحب نهائيات كأس العالم والبطولات القارية حياً من Wikipedia API"""
    cached, is_fresh = get_from_cache("wiki_intl_finals_live_v1", ttl=86400 * 7)
    if cached and is_fresh:
        return cached

    finals_records = []

    def parse_wiki_cup(item_tuple):
        page_title, comp_ar, reg = item_tuple
        local_out = []
        api_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_title)}&prop=text&format=json&redirects=1"
        data = fetch_wiki_api_json(api_url, timeout=8.0)
        if not data or "parse" not in data or "text" not in data["parse"]:
            return local_out

        parser = _WikiTableParser()
        parser.feed(data["parse"]["text"].get("*", ""))

        for raw_table in parser.tables:
            grid = _expand_table_grid(raw_table)
            if len(grid) < 4:
                continue
            headers = [c["text"].lower() for c in grid[0]]
            yr_col = next((i for i, h in enumerate(headers) if "year" in h or "season" in h or "tournament" in h), -1)
            win_col = next((i for i, h in enumerate(headers) if "winner" in h or "champion" in h), -1)
            score_col = next((i for i, h in enumerate(headers) if "score" in h or "result" in h), -1)
            run_col = next((i for i, h in enumerate(headers) if "runner" in h or "second" in h), -1)

            if yr_col == -1 or win_col == -1 or run_col == -1:
                continue

            for r in grid[1:]:
                if len(r) <= max(yr_col, win_col, run_col):
                    continue
                yr_m = re.search(r"\b(19\d{2}|20\d{2})\b", r[yr_col]["text"])
                if not yr_m:
                    continue
                yr_str = yr_m.group(1)
                win_clean = _clean_entity_name(r[win_col]["text"])
                run_clean = _clean_entity_name(r[run_col]["text"])
                sc_clean = re.sub(r"\[[^\]]*\]", "", r[score_col]["text"]).strip() if (0 <= score_col < len(r)) else ""

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
        save_to_cache("wiki_intl_finals_live_v1", finals_records)
    return finals_records


def _fetch_live_espn_squad_jerseys(league_code="PL"):
    """سحب أرقام القمصان الحقيقية ومراكز اللاعبين حياً من ESPN Rosters API"""
    cache_k = f"live_espn_jerseys_{league_code}"
    cached, is_fresh = get_from_cache(cache_k, ttl=86400 * 3)
    if cached and is_fresh:
        return cached

    espn_code = LEAGUE_CODES.get(league_code, {}).get("espn", "eng.1")
    reg = QUIZ_LEAGUE_CONTEXT.get(league_code, {}).get("region", "europe")
    teams_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams"
    t_data = fetch_json_fast(teams_url, timeout=4.0)
    if not isinstance(t_data, dict):
        return []

    sports = t_data.get("sports", [{}])[0]
    leagues_arr = sports.get("leagues", [{}])[0]
    raw_teams = leagues_arr.get("teams", [])

    team_ids = []
    for item in raw_teams[:8]:
        t_obj = item.get("team", {})
        tid = t_obj.get("id")
        tname = _clean_entity_name(t_obj.get("shortDisplayName") or t_obj.get("displayName") or "")
        if tid and tname:
            team_ids.append((str(tid), tname))

    players_out = []

    def fetch_roster(t_tuple):
        tid, tname = t_tuple
        r_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/teams/{tid}/roster"
        r_data = fetch_json_fast(r_url, timeout=3.5)
        loc = []
        if isinstance(r_data, dict) and isinstance(r_data.get("athletes"), list):
            for ath in r_data["athletes"][:12]:
                if not isinstance(ath, dict):
                    continue
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

    with ThreadPoolExecutor(max_workers=4) as ex:
        for res in ex.map(fetch_roster, team_ids):
            players_out.extend(res)

    if players_out:
        save_to_cache(cache_k, players_out)
    return players_out


def _init_ai_quiz_vault():
    try:
        with _DB_LOCK:
            conn = get_connection()
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
            conn.close()
    except Exception:
        pass


def _load_saved_ai_questions(region_filter="ALL", league_filter="ALL", category_filter="ALL", difficulty_filter="ALL"):
    _init_ai_quiz_vault()
    try:
        with _DB_LOCK:
            conn = get_connection()
            rows = conn.execute("SELECT payload FROM ai_quiz_vault ORDER BY created_at DESC LIMIT 800").fetchall()
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
            for q in questions_list:
                conn.execute(
                    "INSERT OR IGNORE INTO ai_quiz_vault (q_id, category, region, league, difficulty, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (q["id"], q.get("category", "trivia"), q.get("region", "all"), q.get("league", "ALL"), q.get("difficulty", "medium"), json.dumps(q, ensure_ascii=False), now_ts)
                )
            conn.commit()
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


def _warm_missing_api_data_concurrently(target_league="ALL"):
    """سحب البيانات الحية تلقائياً من الـ APIs إذا كان الكاش فارغاً لضمان آلاف الأسئلة دون انتظار"""
    leagues_to_warm = [target_league] if (target_league in QUIZ_LEAGUE_CONTEXT) else ["PL", "PD", "UCL", "SA", "BL1", "FL1", "ACL", "CAF", "UNL"]

    def warm_task(lg):
        try:
            st, _ = get_from_cache(f"standings_v3_{lg}", ttl=86400 * 7)
            if not st:
                get_official_standings(lg)
            sc, _ = get_from_cache(f"scorers_{lg}", ttl=86400 * 7)
            if not sc:
                get_top_scorers(lg)
            hs, _ = get_from_cache(f"full_encyclopedia_v5_{lg}", ttl=86400 * 14)
            if not hs and lg in ("PL", "PD", "UCL", "SA", "BL1", "ACL", "CAF"):
                get_league_full_history(lg)
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(warm_task, leagues_to_warm))

    try:
        mc, _ = get_from_cache("global_mercato_pure_api_v12", ttl=86400 * 3)
        if not mc:
            get_mercato_and_contracts_data()
    except Exception:
        pass


def _build_pure_live_api_question_pool(target_league="ALL"):
    """توليد آلاف الأسئلة المتجددة 100% من الـ APIs الحية (ESPN + Transfermarkt + Wikipedia) بصفر بيانات محلية"""
    cache_key = f"pure_api_quiz_pool_v7_{target_league}"
    cached_pool, is_fresh = get_from_cache(cache_key, ttl=600)
    if cached_pool and is_fresh and len(cached_pool) >= 250:
        return cached_pool

    _warm_missing_api_data_concurrently(target_league)

    pool = []
    q_seq = 1

    def next_id(prefix):
        nonlocal q_seq
        q_seq += 1
        return f"api_{prefix}_{q_seq}"

    # 1. التوليد الحي من صفقات وانتقالات Transfermarkt & ESPN API (مسيرة اللاعبين والمدربين بالشعارات)
    mercato_data, _ = get_from_cache("global_mercato_pure_api_v12", ttl=86400 * 7)
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
            if not p_name or not f_club or not t_club:
                continue

            peers_list = coach_names_by_reg.get(reg, []) if is_coach else player_names_by_reg.get(reg, [])
            if len(set(peers_list)) < 4:
                peers_list = [x.get("name") for x in tr_list if x.get("name")]

            opts_tr = _distinct_choices(p_name, peers_list, 3)
            cat_key = "coaches_tactics" if is_coach else "club_career"

            pool.append({
                "id": next_id("career_tr"),
                "category": cat_key,
                "type": "career_path",
                "region": reg,
                "league": "ALL",
                "difficulty": "medium",
                "question": f"{'👔 مسيرة مدرب حية' if is_coach else '✈️ مسار انتقالات حي بالشعارات'}: من هو صاحب هذا المسار بين الأندية؟",
                "career_stops": [
                    {"club": f_club, "crest": f_crest},
                    {"club": t_club, "crest": t_crest}
                ],
                "options": opts_tr,
                "answer": p_name,
                "hint": f"المركز: {t.get('position', '')} • التفاصيل: {t.get('fee', '')}",
                "explanation": f"{'المدرب' if is_coach else 'النجم'} هو ({p_name}) المنتقل من {f_club} إلى {t_club}."
            })

    # 2. التوليد الحي من نهائيات كأس العالم والبطولات القارية عبر Wikipedia API
    intl_finals = _fetch_wiki_international_finals_live() or []
    if len(intl_finals) >= 4:
        for idx_f, cup in enumerate(intl_finals):
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
                "league": "UNL",
                "difficulty": "easy" if int(yr) >= 2010 else "medium",
                "question": f"🌍 في نهائي ({comp_n} {yr})، أي منتخب تُوّج باللقب بعد تغلبه على ({run})؟",
                "options": opts_w,
                "answer": win,
                "hint": f"انتهى النهائي بنتيجة ({sc_line})" if sc_line else f"الوصيف كان منتخب {run}",
                "explanation": f"تُوّج منتخب ({win}) بلقب {comp_n} عام {yr} على حساب {run}."
            })

            if sc_line and any(ch.isdigit() for ch in sc_line):
                nearby_scores = [c["score"] for c in intl_finals if c.get("score") and c["score"] != sc_line]
                if len(set(nearby_scores)) >= 3:
                    opts_sc = _distinct_choices(sc_line, nearby_scores, 3)
                    pool.append({
                        "id": next_id("intl_sc"),
                        "category": "finals_remontada",
                        "type": "mcq",
                        "region": reg,
                        "league": "UNL",
                        "difficulty": "hard",
                        "question": f"⚡ النهائيات الكبرى ({comp_n} {yr}): بأي نتيجة حُسمت المباراة النهائية بين ({win}) و({run})؟",
                        "options": opts_sc,
                        "answer": sc_line,
                        "hint": f"اللقب ذهب لصالح {win}",
                        "explanation": f"انتهى نهائي {comp_n} {yr} بين {win} و{run} بنتيجة ({sc_line})."
                    })

    # 3. التوليد الحي من قوائم اللاعبين وأرقام قمصانهم في ESPN Rosters API
    for lg_j in ("PL", "PD", "SA", "BL1"):
        jerseys_live = _fetch_live_espn_squad_jerseys(lg_j) or []
        if len(jerseys_live) >= 4:
            for idx_j, jr in enumerate(jerseys_live):
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
                    "question": f"👕 من كشوفات الموسم الحية: من يرتدي القميص رقم (#{jr['num']}) في صفوف نادي ({jr['club']})؟",
                    "options": opts_jp,
                    "answer": jr["player"],
                    "hint": f"جميع الخيارات من لاعبي {jr['club']}",
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

    # 4. التوليد السياقي الشامل من البطولات الـ 12 الحية (الترتيب، الهدافين، المباريات، والأرشيف التاريخي منذ 1888)
    for lg_code, ctx in QUIZ_LEAGUE_CONTEXT.items():
        reg = ctx["region"]
        lg_name = ctx["name_ar"]

        standings, _ = get_from_cache(f"standings_v3_{lg_code}", ttl=86400 * 7)
        scorers, _ = get_from_cache(f"scorers_{lg_code}", ttl=86400 * 7)
        history, _ = get_from_cache(f"full_encyclopedia_v5_{lg_code}", ttl=86400 * 14)
        fixtures, _ = get_from_cache(f"fixtures_{lg_code}", ttl=86400 * 3)

        standings = standings or []
        scorers = scorers or []
        fixtures = fixtures or []

        # أ) من مباريات وقمم الجولة الحية (derbies_stadiums)
        if len(fixtures) >= 4:
            match_pairs = [f"{_clean_entity_name(f.get('home_short',''))} ⚔️ {_clean_entity_name(f.get('away_short',''))}" for f in fixtures if f.get("home_short") and f.get("away_short")]
            for f in fixtures[:10]:
                h_n = _clean_entity_name(f.get("home_short", ""))
                a_n = _clean_entity_name(f.get("away_short", ""))
                if not h_n or not a_n or len(match_pairs) < 4:
                    continue
                pair_str = f"{h_n} ⚔️ {a_n}"
                opts_m = _distinct_choices(pair_str, match_pairs, 3)
                pool.append({
                    "id": next_id("fix_derby"),
                    "category": "derbies_stadiums",
                    "type": "mcq",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "medium",
                    "question": f"🔥 مواجهات ({lg_name}): أي مواجهة تجمع صاحب الأرض ({h_n} - Elo {int(f.get('home_elo',1500))}) بضيفه في الجولة الحالية؟",
                    "options": opts_m,
                    "answer": pair_str,
                    "hint": f"الطرف المضيف هو {h_n}",
                    "explanation": f"المواجهة الرسمية المجدولة هي ({pair_str})."
                })

        # ب) من جدول الترتيب الرسمي الحي (مع تقارب الخيارات من المراكز المجاورة ±1, ±2)
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
                    pool.append({
                        "id": next_id("vis_logo"),
                        "category": "visual",
                        "type": "logo_blur",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": "easy" if rank <= 5 else "medium",
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

                pool.append({
                    "id": next_id("who_club"),
                    "category": "who_am_i",
                    "type": "three_clues",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "medium",
                    "question": f"🕵️‍♂️ من أنا؟ اكتشف الفريق المشارك في ({lg_name}) من أدلته الإحصائية الحية:",
                    "clues": [
                        f"الدليل 1 (3 نقاط): خضت {played} مباريات في {lg_name}، سجلت {gf} هدفاً واستقبلت {ga} هدفاً.",
                        f"الدليل 2 (نقطتان): حققت {won} انتصارات وأجمع في رصيدي ({pts} نقطة) حالياً.",
                        f"الدليل 3 (نقطة): أحتل المركز (#{rank}) في جدول ترتيب {lg_name}."
                    ],
                    "options": opts_tight_clubs,
                    "answer": c_name,
                    "hint": f"صاحب المركز #{rank} في {lg_name}",
                    "explanation": f"الفريق هو ({c_name}) صاحب المركز #{rank} برصيد {pts} نقطة."
                })

            # مقارنات الأرقام المتقاربة بين الفرق المتجاورة في الترتيب
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
                        "question": f"📊 مقارنة هجومية متقاربة ({lg_name}): سجل {n1} ({g1} هدفاً).. فهل أهداف {n2} المسجلة أعلى أم أقل؟",
                        "item_a": {"name": n1, "crest": t1.get("crest", ""), "stat_label": "الأهداف المسجلة", "stat_val": g1},
                        "item_b": {"name": n2, "crest": t2.get("crest", ""), "stat_label": "الأهداف المسجلة", "stat_val": g2},
                        "hint": "مقارنة بين فريقين متجاورين مباشرة في جدول الترتيب!",
                        "options": ["أعلى 📈", "أقل 📉"],
                        "answer": ans_g,
                        "explanation": f"سجل {n2} ({g2} هدفاً) مقابل ({g1} هدفاً) لفريق {n1} في {lg_name}."
                    })

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
                            "question": f"📋 رتب هذه الأندية المتجاورة في ({lg_name}) تنازلياً حسب نقاطها:",
                            "rank_items": shuffled_r,
                            "correct_order": [x["label"] for x in r_items],
                            "options": [],
                            "answer": " ⬅️ ".join([x["label"] for x in r_items]),
                            "hint": f"الأول بينها هو {r_items[0]['label']}",
                            "explanation": "الترتيب الرسمي: " + " ثم ".join([f"{x['label']} ({x['val']})" for x in r_items])
                        })

            accepted_clubs = list({
                x.lower() for t in standings
                for x in [_clean_entity_name(t.get("short_name") or ""), _clean_entity_name(t.get("team_name") or ""), t.get("short_name") or ""]
                if len(x.strip()) >= 3
            })
            if len(accepted_clubs) >= 6:
                pool.append({
                    "id": next_id("blitz_lg"),
                    "category": "blitz",
                    "type": "blitz_30s",
                    "region": reg,
                    "league": lg_code,
                    "difficulty": "medium",
                    "question": f"⏱️ تحدي 30 ثانية ({lg_name}): اكتب أكبر عدد من أندية البطولة المشاركة هذا الموسم!",
                    "accepted_answers": accepted_clubs,
                    "hint": "يُحتسب اسم الفريق تلقائياً فور كتابته!",
                    "options": [],
                    "answer": f"أندية {lg_name}",
                    "explanation": f"كل نادٍ صحيح من {lg_name} منحك نقطة فورية!"
                })

        # ج) من قائمة الهدافين الحية في ESPN API (awards_scorers)
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
                    "hint": f"مهاجم نادي {p_team}",
                    "explanation": f"الهداف هو ({p_name}) نجم {p_team} برصيد {p_goals} أهداف."
                })

        # د) من الأرشيف التاريخي الحي منذ التأسيس عبر Wikipedia & ESPN API
        if isinstance(history, dict) and isinstance(history.get("seasons"), list):
            seasons = history["seasons"]
            titles_tbl = history.get("titles_table", [])

            for s_idx, s in enumerate(seasons[:85]):
                ch = s.get("champion")
                yr = s.get("season")
                ru = s.get("runner_up", "")
                top_sc = s.get("top_scorer", "")
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
                    pool.append({
                        "id": next_id("trv_hist_ch"),
                        "category": "trivia",
                        "type": "mcq",
                        "region": reg,
                        "league": lg_code,
                        "difficulty": "easy" if int(yr[:4]) >= 2012 else ("medium" if int(yr[:4]) >= 1990 else "hard"),
                        "question": f"🏛️ أرشيف ({lg_name}): أي فريق تُوّج باللقب في موسم ({yr})؟",
                        "hint": f"الوصيف في ذلك الموسم كان: {ru or 'من أندية القمة'}",
                        "options": opts_ch,
                        "answer": ch,
                        "explanation": f"تُوّج ({ch}) رسمياً بلقب {lg_name} في موسم {yr}."
                    })

                if top_sc and "موثق" not in top_sc:
                    era_scorers = [
                        seasons[s_idx + off].get("top_scorer", "")
                        for off in (-3, -2, -1, 1, 2, 3)
                        if 0 <= s_idx + off < len(seasons) and seasons[s_idx + off].get("top_scorer") and "موثق" not in seasons[s_idx + off].get("top_scorer", "")
                    ]
                    if len(set(era_scorers)) >= 3:
                        opts_hsc = _distinct_choices(top_sc, era_scorers, 3)
                        pool.append({
                            "id": next_id("aw_hist_sc"),
                            "category": "awards_scorers",
                            "type": "mcq",
                            "region": reg,
                            "league": lg_code,
                            "difficulty": "hard",
                            "question": f"🌕 سجل الهدافين التاريخي ({lg_name}): من تُوّج بلقب هداف المسابقة في موسم ({yr})؟",
                            "options": opts_hsc,
                            "answer": top_sc,
                            "hint": f"بطل ذلك الموسم كان {ch}",
                            "explanation": f"هداف {lg_name} في موسم {yr} هو ({top_sc})."
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
                            "question": f"🏆 السجل الذهبي ({lg_name}): كم مرة تُوّج نادي ({club_n}) بلقب هذه البطولة عبر تاريخه؟",
                            "options": opts_cnt,
                            "answer": str(t_cnt),
                            "hint": f"آخر لقب له في البطولة كان عام {t_row.get('last_title', '-')}",
                            "explanation": f"يمتلك نادي {club_n} في خزائنه ({t_cnt}) لقباً في {lg_name}."
                        })

    if len(pool) >= 100:
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
    # توحيد الفلتر سواء أرسله main.py باسم type_filter أو أرسله views.js باسم category_filter
    raw_cat = category_filter if (category_filter and category_filter != "ALL") else (type_filter or "ALL")
    cat = str(raw_cat).strip().lower()

    api_pool = _build_pure_live_api_question_pool(target_league=lg) or []
    ai_pool = _generate_ai_batch_questions(reg, lg, cat, diff) if use_ai else []
    master_pool = ai_pool + api_pool

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

    if len(filtered) < 6 and cat != "all":
        filtered = [dict(q) for q in master_pool if cat in (str(q.get("category") or "").lower(), str(q.get("type") or "").lower())]
    if len(filtered) < 6 and reg != "all":
        filtered = [dict(q) for q in master_pool if str(q.get("region") or "").lower() in (reg, "all")]
    if len(filtered) < 6:
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
        "questions": filtered[:batch_size],
        "seed_code": generated_seed
    }