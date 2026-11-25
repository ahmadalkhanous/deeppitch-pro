import os
import time
import json
import threading
import urllib.request
from collections import defaultdict
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database as db
from engine_core import (
    compute_fixture_probabilities,
    evaluate_tactical_edge,
    generate_h2h_history
)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    db.init_db()
    threading.Thread(target=db.background_warm_all_leagues, daemon=True).start()
    yield


app = FastAPI(title="DeepPitch Multi-League Analytics Platform", lifespan=lifespan)


@app.get("/static/manifest.json")
def manifest_file():
    if os.path.exists("manifest.json"):
        return FileResponse("manifest.json", media_type="application/json")
    if os.path.exists("static/manifest.json"):
        return FileResponse("static/manifest.json", media_type="application/json")
    return Response(content="{}", media_type="application/json")


if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# يمكن تقييد النطاقات لاحقاً عبر متغير البيئة ALLOWED_ORIGINS="https://yourdomain.com"
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*").strip()
_allowed_origins = ["*"] if _raw_origins == "*" else [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_MAIN_LOCK = threading.Lock()
RESPONSE_CACHE = {}
CACHE_TTL_SECONDS = 1800

TODAYS_MATCHES_CACHE = {}
TODAY_CACHE_TTL = 35
LAST_FORCE_REFRESH_TS = {"news": 0.0, "mercato": 0.0, "cards": 0.0}
FORCE_REFRESH_COOLDOWN = 60  # السماح بالتحديث الإجباري مرة كل 60 ثانية كحد أقصى

_AI_RATE_LIMITS = defaultdict(list)


def check_ai_rate_limit(request: Request, max_requests: int = 12, window_sec: int = 60):
    """حماية مسارات الذكاء الاصطناعي من الاستنزاف (حد 12 طلباً في الدقيقة لكل IP)"""
    fwd = request.headers.get("x-forwarded-for", "")
    client_ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "unknown")
    now_ts = time.time()
    cutoff = now_ts - window_sec

    with _MAIN_LOCK:
        if len(_AI_RATE_LIMITS) > 1000:
            stale_ips = [ip for ip, ts_list in _AI_RATE_LIMITS.items() if not ts_list or ts_list[-1] < cutoff]
            for ip in stale_ips:
                _AI_RATE_LIMITS.pop(ip, None)

        recent = [ts for ts in _AI_RATE_LIMITS[client_ip] if ts > cutoff]
        if len(recent) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="تجاوزت الحد المسموح من طلبات الذكاء الاصطناعي، يرجى المحاولة بعد دقيقة."
            )
        recent.append(now_ts)
        _AI_RATE_LIMITS[client_ip] = recent


def can_force_refresh(scope_key: str, requested: bool) -> bool:
    if not requested:
        return False
    now_ts = time.time()
    with _MAIN_LOCK:
        last_ts = LAST_FORCE_REFRESH_TS.get(scope_key, 0.0)
        if (now_ts - last_ts) > FORCE_REFRESH_COOLDOWN:
            LAST_FORCE_REFRESH_TS[scope_key] = now_ts
            return True
    return False


@app.get("/")
def serve_dashboard():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "index.html not found"}


@app.get("/sw.js")
def serve_service_worker():
    if os.path.exists("sw.js"):
        return FileResponse("sw.js", media_type="application/javascript")
    return Response(
        content="self.addEventListener('install', () => self.skipWaiting());",
        media_type="application/javascript"
    )





@app.get("/api/leagues")
def get_leagues():
    return {"leagues": db.get_all_leagues()}


@app.get("/api/gameweek/{league_code}")
def get_gameweek_predictions(league_code: str, refresh: bool = False):
    now = time.time()
    cache_key = f"gw_{league_code}"
    allow_refresh = can_force_refresh(cache_key, refresh)
    if not allow_refresh:
        with _MAIN_LOCK:
            cached_gw = RESPONSE_CACHE.get(cache_key)
        if cached_gw and (now - cached_gw["time"] < CACHE_TTL_SECONDS):
            return cached_gw["payload"]

    fixtures = db.get_gameweek_fixtures(league_code, force_refresh=allow_refresh)
    if not fixtures:
        return {"league_code": league_code, "fixtures": []}

    results = []
    for f in fixtures:
        stats = compute_fixture_probabilities(
            home_att=f["home_attack"],
            home_def=f["home_defense"],
            away_att=f["away_attack"],
            away_def=f["away_defense"],
            home_elo=f["home_elo"],
            away_elo=f["away_elo"],
            home_form=f.get("home_form"),
            away_form=f.get("away_form")
        )

        edge_data = evaluate_tactical_edge(
            home_short=f["home_short"],
            away_short=f["away_short"],
            home_elo=f["home_elo"],
            away_elo=f["away_elo"],
            p_home=stats["prob_home"],
            p_draw=stats["prob_draw"],
            p_away=stats["prob_away"],
            xg_home=stats["xg_home"],
            xg_away=stats["xg_away"]
        )

        h2h_data = generate_h2h_history(
            f["home_short"], f["away_short"], f["home_elo"], f["away_elo"]
        )

        results.append({
            "fixture_id": f["fixture_id"],
            "gameweek": f["gameweek"],
            "kickoff_time": f["kickoff_time"],
            "kickoff_iso": f.get("kickoff_iso", ""),
            "status": f["status"],
            "h2h": h2h_data,
            "home": {
                "id": f["home_id"],
                "name": f["home_name"],
                "short": f["home_short"],
                "crest": f["home_crest"],
                "elo": round(f["home_elo"], 1),
                "attack": f["home_attack"],
                "defense": f["home_defense"],
                "form": f["home_form"],
                "xg": stats["xg_home"],
                "prob": stats["prob_home"]
            },
            "away": {
                "id": f["away_id"],
                "name": f["away_name"],
                "short": f["away_short"],
                "crest": f["away_crest"],
                "elo": round(f["away_elo"], 1),
                "attack": f["away_attack"],
                "defense": f["away_defense"],
                "form": f["away_form"],
                "xg": stats["xg_away"],
                "prob": stats["prob_away"]
            },
            "draw_prob": stats["prob_draw"],
            "predicted_score": stats["most_likely_score"],
            "score_confidence": stats["score_prob"],
            "markets": stats["markets"],
            "heatmap": stats["heatmap"],
            "edge": edge_data
        })

    payload = {"league_code": league_code, "fixtures": results}
    with _MAIN_LOCK:
        RESPONSE_CACHE[cache_key] = {"payload": payload, "time": now}
    return payload



@app.get("/api/standings/{league_code}")
@app.get("/api/official_standings/{league_code}")
def get_official_standings_route(league_code: str, refresh: bool = False):
    allow_refresh = can_force_refresh(f"standings_{league_code}", refresh)
    standings = db.get_official_standings(league_code, force_refresh=allow_refresh)
    return {"status": "success", "standings": standings}


@app.get("/api/scorers/{league_code}")
@app.get("/api/top_scorers/{league_code}")
def get_top_scorers_route(league_code: str, refresh: bool = False):
    allow_refresh = can_force_refresh(f"scorers_{league_code}", refresh)
    scorers = db.get_top_scorers(league_code, force_refresh=allow_refresh)
    return {"status": "success", "scorers": scorers} 


@app.get("/api/safe_accumulator/{league_code}")
def get_safe_accumulator(league_code: str):
    gw_data = get_gameweek_predictions(league_code)
    fixtures = gw_data.get("fixtures", [])
    if not fixtures:
        return {"picks": [], "joint_probability": 0}

    ranked_picks = []
    for f in fixtures:
        h_prob = f["home"]["prob"]
        a_prob = f["away"]["prob"]
        over_prob = f["markets"]["over_25"]

        if h_prob >= 58.0:
            ranked_picks.append({
                "match": f"{f['home']['short']} vs {f['away']['short']}",
                "bet": f"فوز {f['home']['short']} (أفضلية الأرض)",
                "confidence": h_prob
            })
        elif a_prob >= 56.0:
            ranked_picks.append({
                "match": f"{f['home']['short']} vs {f['away']['short']}",
                "bet": f"فوز {f['away']['short']}",
                "confidence": a_prob
            })
        elif over_prob >= 60.0:
            ranked_picks.append({
                "match": f"{f['home']['short']} vs {f['away']['short']}",
                "bet": "أكثر من 2.5 هدف",
                "confidence": over_prob
            })
        else:
            best_side = f["home"]["short"] if h_prob >= a_prob else f["away"]["short"]
            best_val = max(h_prob, a_prob)
            ranked_picks.append({
                "match": f"{f['home']['short']} vs {f['away']['short']}",
                "bet": f"ترجيح كفة {best_side}",
                "confidence": best_val
            })

    ranked_picks.sort(key=lambda x: x["confidence"], reverse=True)
    top_picks = ranked_picks[:3]

    joint_prob = 1.0
    for p in top_picks:
        joint_prob *= (p["confidence"] / 100.0)

    return {
        "picks": top_picks,
        "joint_probability": round(float(joint_prob * 100.0), 1)
    }


@app.get("/api/today_matches")
@app.get("/api/todays_matches")
def get_todays_matches(date: str = "", refresh: bool = False):
    now_ts = time.time()
    date_key = (date or "today").strip()[:10]
    ttl = TODAY_CACHE_TTL if date_key == "today" else 300
    allow_refresh = can_force_refresh(f"today_{date_key}", refresh)

    if not allow_refresh:
        with _MAIN_LOCK:
            cached_entry = TODAYS_MATCHES_CACHE.get(date_key)
        if cached_entry and (now_ts - cached_entry["time"] < ttl):
            return cached_entry["data"]

    try:
        raw_matches = db.get_todays_matches(
            target_date="" if date_key == "today" else date_key,
            force_refresh=allow_refresh
        )
        if not raw_matches or not isinstance(raw_matches, list):
            raw_matches = []
    except Exception as e:
        print(f"Error fetching matches from DB: {e}")
        raw_matches = []

    def sort_priority(match):
        if not isinstance(match, dict):
            return 3
        if match.get("is_live") or match.get("state") == "in":
            return 0
        if match.get("state") == "pre":
            return 1
        return 2

    raw_matches.sort(key=sort_priority)

    payload = {"status": "success", "date": date_key, "matches": raw_matches}
    with _MAIN_LOCK:
        TODAYS_MATCHES_CACHE[date_key] = {"data": payload, "time": now_ts}
        if len(TODAYS_MATCHES_CACHE) > 20:
            oldest = min(TODAYS_MATCHES_CACHE.keys(), key=lambda k: TODAYS_MATCHES_CACHE[k]["time"])
            TODAYS_MATCHES_CACHE.pop(oldest, None)
    return payload  



@app.get("/api/match_stats/{league_code}/{match_id}")
def get_match_stats_route(league_code: str, match_id: str):
    try:
        if hasattr(db, "get_real_match_stats"):
            stats = db.get_real_match_stats(league_code, match_id)
        elif hasattr(db, "get_match_statistics"):
            stats = db.get_match_statistics(league_code, match_id)
        else:
            stats = None

        if not stats:
            return {"status": "error", "has_stats": False, "message": "الإحصائيات غير متوفرة لهذا اللقاء"}
        return {"status": "success", "data": stats}
    except Exception as e:
        return {"status": "error", "has_stats": False, "message": str(e)}


@app.get("/api/news")
def get_sports_news_route(refresh: bool = False):
    try:
        now_ts = time.time()
        allow_refresh = False
        if refresh and (now_ts - LAST_FORCE_REFRESH_TS["news"] > FORCE_REFRESH_COOLDOWN):
            allow_refresh = True
            LAST_FORCE_REFRESH_TS["news"] = now_ts

        articles = db.sync_and_get_news(force_refresh=allow_refresh)
        return {"status": "success", "count": len(articles), "news": articles}
    except Exception as e:
        return {"status": "error", "news": [], "message": str(e)}


@app.get("/api/season_projections/{league_code}")
def get_season_projections_route(league_code: str, refresh: bool = False):
    allow_refresh = can_force_refresh(f"proj_{league_code}", refresh)
    return {"projections": db.get_season_projections(league_code, force_refresh=allow_refresh)}


# =========================================================================
# مسار المحلل التكتيكي الذكي (AI Tactical Pundit API)
# =========================================================================

class MatchAnalysisRequest(BaseModel):
    home_team: str = Field(..., min_length=1, max_length=80)
    away_team: str = Field(..., min_length=1, max_length=80)
    home_prob: float
    draw_prob: float
    away_prob: float
    home_xg: float
    away_xg: float
    home_elo: float
    away_elo: float
    edge_label: str = Field(default="", max_length=120)
    edge_reason: str = Field(default="", max_length=400)
    streak_text: str = Field(default="", max_length=300)


@app.post("/api/ai_analysis")
def generate_ai_tactical_analysis(req: MatchAnalysisRequest, request: Request):
    check_ai_rate_limit(request, max_requests=12, window_sec=60)
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if gemini_key:
        try:
            prompt = f"""أنت محلل كروي تكتيكي خبير ومخضرم. قم بصياغة تحليل فني شيق وموجز (في 3 إلى 4 أسطر فقط) باللغة العربية عن هذه المواجهة بناءً على البيانات الدقيقة التالية:
المباراة: {req.home_team} ضد {req.away_team}
أرجحية الفوز: {req.home_team} ({req.home_prob}%) | التعادل ({req.draw_prob}%) | {req.away_team} ({req.away_prob}%)
الأهداف المتوقعة (xG): {req.home_team} ({req.home_xg}) مقابل {req.away_team} ({req.away_xg})
فارق تصنيف الـ Elo: {req.home_team} ({req.home_elo}) مقابل {req.away_team} ({req.away_elo})
رادار المباراة: {req.edge_label} - {req.edge_reason}
مؤشر التكافؤ: {req.streak_text}

اكتب تحليلاً جذاباً يجمع بين الرؤية الفنية لمدربي كرة القدم وقراءة الأرقام الواقعية دون مقدمات أو سرد جاف للنقاط."""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")

            api_req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(api_req, timeout=6.0, context=db.SSL_CONTEXT) as res:
                body = json.loads(res.read().decode("utf-8"))
                text = body["candidates"][0]["content"]["parts"][0]["text"]
                return {"analysis": text.strip()}
        except Exception:
            pass

    fav = req.home_team if req.home_prob > req.away_prob else req.away_team
    und = req.away_team if req.home_prob > req.away_prob else req.home_team
    max_p = max(req.home_prob, req.away_prob)

    if "فخ" in req.edge_label or "التعثر" in req.edge_label:
        tactical_view = f"تحذر النماذج الرقمية من فخ محكم قد ينصبه {und}؛ فرغم أفضلية {fav} في تصنيف القوة، إلا أن الصلابة الدفاعية ومعدل الـ xG للضيف يرجح سيناريو إغلاق المساحات والاعتماد على التحولات السريعة المباغتة."
    elif max_p >= 65.0:
        tactical_view = f"يدخل {fav} اللقاء بأسبقية فنية كاسحة ومعدل هجومي مرتفع ({max(req.home_xg, req.away_xg)} xG). مفتاح اللقاء يكمن في سرعة تدوير الكرة واختراق التكتل الدفاعي المتوقع لـ {und} في الثلث الأخير."
    else:
        tactical_view = f"مواجهة تكتيكية متوازنة للغاية تحسمها تفاصيل دقيقة؛ تقارب نسب الاستحواذ والأهداف المتوقعة يجعل معركة خط الوسط والكرات الثابتة هي الفيصل لتحديد الطرف المنتصر."

    full_insight = f"{tactical_view} {req.streak_text}".strip()
    return {"analysis": full_insight}


# =========================================================================
# مسار سكاوت الفانتازي والذكاء الاصطناعي (AI Scout & Fantasy Advisor API)
# =========================================================================

class ScoutQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=300)
    league_code: str = Field(default="PL", max_length=10)


@app.post("/api/ai_scout")
def query_ai_scout(req: ScoutQueryRequest, request: Request):
    check_ai_rate_limit(request, max_requests=12, window_sec=60)
    try:
        code = (req.league_code or "PL").upper()

        standings_raw = getattr(db, "get_official_standings", lambda c: [])(code)
        standings = standings_raw.get("standings", []) if isinstance(standings_raw, dict) else (standings_raw or [])

        scorers_raw = getattr(db, "get_top_scorers", lambda c: [])(code)
        scorers = scorers_raw.get("scorers", []) if isinstance(scorers_raw, dict) else (scorers_raw or [])

        top_scorers_texts = []
        for s in scorers[:3]:
            if isinstance(s, dict):
                s_name = s.get("name", "لاعب")
                s_team = s.get("team", s.get("team_name", ""))
                s_goals = s.get("goals", "")
                top_scorers_texts.append(f"{s_name} ({s_team} - {s_goals} أهداف)")
        top_3_scorers = ", ".join(top_scorers_texts) if top_scorers_texts else "متصدري الترتيب"

        valid_st = [t for t in standings if isinstance(t, dict) and t.get("played", 0) > 0]
        by_attack = sorted(valid_st, key=lambda x: x.get("gf", 0) / max(1, x.get("played", 1)), reverse=True)
        by_weak_def = sorted(valid_st, key=lambda x: x.get("ga", 0) / max(1, x.get("played", 1)), reverse=True)

        strongest_attack = ", ".join([
            f"{t.get('short_name', 'نادي')} ({t.get('gf', 0)} هدفاً)"
            for t in by_attack[:3]
        ]) if by_attack else "الأندية المتصدرة"

        weakest_defense = ", ".join([
            f"{t.get('short_name', 'نادي')} (استقبل {t.get('ga', 0)} هدفاً)"
            for t in by_weak_def[:3]
        ]) if by_weak_def else "أندية المؤخرة"

        league_info = getattr(db, "LEAGUE_CODES", {}).get(code, {})
        league_name = league_info.get("name", "الدوري")

        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if gemini_key:
            try:
                prompt = f"""أنت 'السكاوت الرياضي ومستشار الفانتازي' لمنصة DeepPitch Pro.
سؤال المستخدم: "{req.message}"
بيانات {league_name} الحقيقية:
- صدارة الهدافين: {top_3_scorers}
- أقوى خطوط الهجوم (معدل التسجيل): {strongest_attack}
- أضعف خطوط الدفاع (أكثر استقبالاً للأهداف): {weakest_defense}

أجب باختصار في سطرين إلى 3 أسطر بنصيحة فانتازي مباشرة وعملية بناءً على هذه الأرقام فقط."""
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                api_req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(api_req, timeout=5.0, context=db.SSL_CONTEXT) as res:
                    body = json.loads(res.read().decode("utf-8"))
                    reply_text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return {"reply": reply_text}
            except Exception as api_err:
                print(f"⚠️ تنبيه Gemini API: {api_err}")

        msg = req.message.lower()
        if any(k in msg for k in ["كابتن", "تشكيلة", "شراء", "فانتازي"]):
            reply = f"🎯 خيار الكابتن الأبرز للجولة: الأرقام ترشح بقوة **{top_3_scorers}**؛ كما تتصدر أندية **{strongest_attack}** قائمة أقوى خطوط الهجوم في البطولة."
        elif any(k in msg for k in ["تعثر", "مفاجأة", "صدمة", "فخ", "دفاع"]):
            reply = f"⚠️ رادار الدفاع: استهدف مهاجمين يواجهون أندية **{weakest_defense}** كونها الأكثر استقبالاً للأهداف هذا الموسم، وتجنّب مدافعيها."
        elif any(k in msg for k in ["هجوم", "هداف", "أهداف"]):
            reply = f"🔥 مؤشر الهجوم: الأقوى تهديفياً حالياً هي **{strongest_attack}**، ويتصدر الهدافين **{top_3_scorers}**."
        else:
            reply = f"📊 تقرير السكاوت لـ {league_name}: صدارة الهدافين: **{top_3_scorers}**، أقوى هجوم: **{strongest_attack}**، وأضعف دفاع: **{weakest_defense}**."

        return {"reply": reply}

    except Exception as e:
        print(f"❌ استثناء في السكاوت: {e}")
        return {"reply": "🤖 مرحباً بك! بناءً على أرقام الجولة الحالية، يُنصح باختيار عناصر الأندية الأعلى تهديفاً ومراقبة رادار التعثر في صفحة مباريات الجولة."}


# =========================================================================
# مسار صحيفة الجولة الذكية (AI Matchweek Gazette API)
# =========================================================================

@app.get("/api/ai_newspaper/{league_code}")
def get_ai_matchweek_newspaper(league_code: str, request: Request):
    check_ai_rate_limit(request, max_requests=10, window_sec=60)
    try:
        code = (league_code or "PL").upper()
        info = getattr(db, "LEAGUE_CODES", {}).get(code, {})
        league_name = info.get("name", "الدوري")
        flag = info.get("flag", "⚽")

        fixtures_raw = getattr(db, "get_gameweek_fixtures", lambda c: [])(code)
        fixtures = fixtures_raw.get("fixtures", []) if isinstance(fixtures_raw, dict) else (fixtures_raw or [])

        standings_raw = getattr(db, "get_official_standings", lambda c: [])(code)
        standings = standings_raw.get("standings", []) if isinstance(standings_raw, dict) else (standings_raw or [])

        match_summaries = []
        for f in fixtures[:5]:
            h_name = f.get("home_short", f.get("home_full", "المضيف"))
            a_name = f.get("away_short", f.get("away_full", "الضيف"))
            match_summaries.append(f"{h_name} vs {a_name}")

        leader = standings[0].get("short_name", "المتصدر") if standings else "المتصدر"
        chaser = standings[1].get("short_name", "الوصيف") if len(standings) > 1 else "الملاحق"

        gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if gemini_key:
            try:
                matches_str = " | ".join(match_summaries[:4])
                prompt = f"""أنت رئيس التحرير والمحلل الرياضي الأول لصحيفة 'DeepPitch Gazette'.
اكتب تقريراً صحفياً كروياً ممتعاً ومثيراً (بأسلوب الصحافة الرياضية الراقية) لتغطية جولة {league_name} {flag}.

المعطيات:
- المتصدر الحالي: {leader}، ملاحقه المباشر: {chaser}
- أبرز مواجهات الجولة المجدولة: {matches_str}

المطلوب صياغة التقرير بالعناصر التالية وبصيغة نصية منسقة:
1. المانشيت الرئيسي (عنوان صحفي ناري ومثير)
2. قمة الجولة وصراع النقاط (فقرة تحليلية عن أهمية الجولة للقمة)
3. رادار الفخاخ والمفاجآت (تحذير من تعثر غير متوقع)
4. كلمة العدد (خاتمة تكتيكية مقتضبة في سطرين)

اكتب بلهجة صحفية حماسية وممتعة دون وضع وسوم برمجية أو جداول."""

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                api_req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(api_req, timeout=6.0, context=db.SSL_CONTEXT) as res:
                    body = json.loads(res.read().decode("utf-8"))
                    text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return {
                        "headline": f"ملحق الجولة: اشتعال صراع القمة في {league_name}",
                        "content": text
                    }
            except Exception as e:
                print(f"⚠️ Gazette Gemini fallback: {e}")

        headline = f"صدام الجولة في {league_name}: {leader} تحت وطأة الضغط و{chaser} يتربص بالصدارة!"
        article = f"""📰 **مانشيت الجولة:**
تتجه أنظار عشاق الساحرة المستديرة هذا الأسبوع نحو جولة محفوفة بالمخاطر والحسابات الرقمية الدقيقة في {league_name} {flag}.

⚔️ **قمة الجولة وصراع النقاط:**
يدخل {leader} هذه الجولة وهو يعلم تماماً أن أي نزيف للنقاط سيمنح غريمه المباشر {chaser} فرصة ذهبية لتقليص الفارق وخطف الأسبقية النفسية. تشير نماذج الأداء الهجومي للطرفين إلى أن الجولة الحالية قد تشهد تحولات جذرية في جدول الترتيب العام نظراً لتقارب فوارق الأهداف المتوقعة (xG).

⚠️ **رادار الفخاخ وتحذير الأرقام:**
يرصد رادار المنصة التكتيكي خطورة بالغة على الفرق الكبرى التي تخوض لقاءاتها خارج الديار؛ حيث تلعب أندية وسط الجدول بأريحية كاملة وتعتمد على تضييق المساحات والضربات الخاطفة، مما يرفع احتمالية حدوث تعثر مفاجئ في أكثر من مواجهة.

🎯 **كلمة العدد:**
جولة حسم بامتياز، تفاصيلها التكتيكية الصغيرة ستحسم مواجهات كبرى، ومن يملك النفس الأطول والصلابة الدفاعية سيحجز بطاقة الأمان قبل دخول معترك الجولات القادمة."""

        return {
            "headline": headline,
            "content": article
        }

    except Exception:
        return {
            "headline": "صحيفة DeepPitch الرياضية",
            "content": "جاري تجهيز مقالات وتحليلات الجولة من غرفة الأخبار الرياضية..."
        }

@app.get("/api/match_lineups/{league_code}/{match_id}")
def get_match_lineups_route(league_code: str, match_id: str):
    data = db.get_match_lineups(league_code, match_id)
    if not data:
        return {"has_lineups": False}
    return data


@app.get("/api/match_events/{league_code}/{match_id}")
def get_match_events_route(league_code: str, match_id: str):
    try:
        if hasattr(db, "get_match_events"):
            data = db.get_match_events(league_code, match_id)
            if data:
                return data
        return {"has_events": False, "events": []}
    except Exception as e:
        return {"has_events": False, "events": [], "message": str(e)}


# =========================================================================
# مسار أرشيف وتاريخ الدوريات (مربوط بقاعدة البيانات الرسمية و ESPN)
# =========================================================================
@app.get("/api/league_history/{league_code}")
def get_league_history_route(league_code: str, refresh: bool = False):
    try:
        allow_refresh = can_force_refresh(f"hist_{league_code.upper()}", refresh)
        data = db.get_league_full_history(league_code.upper(), force_refresh=allow_refresh)
        if data:
            return {"status": "success", "data": data}
        return {"status": "error", "message": "تعذر العثور على بيانات الدوري"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =========================================================================
# مسارات استوديو المقارنة الرادارية ومحاكي القمم (Radar Clash Studio API)
# =========================================================================

class RadarClashRequest(BaseModel):
    league_a: str = "PD"
    team_a_short: str = ""
    league_b: str = "PL"
    team_b_short: str = ""
    venue: str = "neutral"


@app.get("/api/radar_teams/{league_code}")
def get_radar_teams_route(league_code: str):
    try:
        teams = db.get_radar_teams_for_league(league_code.upper())
        return {"status": "success", "league_code": league_code.upper(), "teams": teams}
    except Exception as e:
        return {"status": "error", "teams": [], "message": str(e)}


@app.post("/api/radar_clash")
def simulate_radar_clash(req: RadarClashRequest):
    try:
        teams_a = db.get_radar_teams_for_league(req.league_a.upper())
        teams_b = db.get_radar_teams_for_league(req.league_b.upper())

        if not teams_a or not teams_b:
            return {"status": "error", "message": "تعذر جلب بيانات الأندية للمقارنة"}

        def find_club(t_list, query_name, default_idx=0):
            if query_name:
                q = query_name.strip().lower()
                for item in t_list:
                    if item["short"].lower() == q or item["name"].lower() == q:
                        return item
                for item in t_list:
                    if q in item["short"].lower() or q in item["name"].lower():
                        return item
            return t_list[min(default_idx, len(t_list) - 1)]

        club_a = find_club(teams_a, req.team_a_short, 0)
        club_b = find_club(teams_b, req.team_b_short, 1 if req.league_a.upper() == req.league_b.upper() else 0)

        if req.venue == "home_a":
            sim = compute_fixture_probabilities(
                home_att=club_a["att"], home_def=club_a["def"],
                away_att=club_b["att"], away_def=club_b["def"],
                home_elo=club_a["elo"], away_elo=club_b["elo"],
                home_form=club_a.get("form"), away_form=club_b.get("form"),
                home_adv_mult=1.22
            )
            prob_a, prob_draw, prob_b = sim["prob_home"], sim["prob_draw"], sim["prob_away"]
            xg_a, xg_b = sim["xg_home"], sim["xg_away"]
            pred_score = sim["most_likely_score"]
            heatmap = sim["heatmap"]
        elif req.venue == "home_b":
            sim = compute_fixture_probabilities(
                home_att=club_b["att"], home_def=club_b["def"],
                away_att=club_a["att"], away_def=club_a["def"],
                home_elo=club_b["elo"], away_elo=club_a["elo"],
                home_form=club_b.get("form"), away_form=club_a.get("form"),
                home_adv_mult=1.22
            )
            prob_a, prob_draw, prob_b = sim["prob_away"], sim["prob_draw"], sim["prob_home"]
            xg_a, xg_b = sim["xg_away"], sim["xg_home"]
            parts = sim["most_likely_score"].split(" - ")
            pred_score = f"{parts[1]} - {parts[0]}" if len(parts) == 2 else sim["most_likely_score"]
            heatmap = [[sim["heatmap"][a][h] for a in range(5)] for h in range(5)]
        else:
            sim = compute_fixture_probabilities(
                home_att=club_a["att"], home_def=club_a["def"],
                away_att=club_b["att"], away_def=club_b["def"],
                home_elo=club_a["elo"] - 50.0, away_elo=club_b["elo"],
                home_form=club_a.get("form"), away_form=club_b.get("form"),
                home_adv_mult=1.04
            )
            prob_a, prob_draw, prob_b = sim["prob_home"], sim["prob_draw"], sim["prob_away"]
            xg_a, xg_b = sim["xg_home"], sim["xg_away"]
            pred_score = sim["most_likely_score"]
            heatmap = sim["heatmap"]

        ra, rb = club_a["radar"], club_b["radar"]
        adv_a, adv_b = [], []
        axis_names = {
            "attack": "الفاعلية الهجومية",
            "defense": "الصلابة الدفاعية",
            "elo": "التصنيف التراكمي (Elo)",
            "form": "الفورمة والزخم الحالي",
            "finishing": "الحسم التهديفي",
            "dominance": "الهيمنة ونسبة الانتصار"
        }
        for k, label in axis_names.items():
            if ra[k] - rb[k] >= 4:
                adv_a.append(label)
            elif rb[k] - ra[k] >= 4:
                adv_b.append(label)

        verdict_parts = []
        if adv_a:
            verdict_parts.append(f"يتفوق **{club_a['short']}** رادارياً في ({'، '.join(adv_a[:3])})")
        if adv_b:
            verdict_parts.append(f"يمتلك **{club_b['short']}** الأفضلية في ({'، '.join(adv_b[:3])})")
        if not verdict_parts:
            verdict_parts.append("تطابق تكتيكي مذهل بين الفريقين في أغلب محاور اللعب الستة")

        winner_side = club_a["short"] if prob_a >= prob_b else club_b["short"]
        max_win_prob = max(prob_a, prob_b)
        tactical_summary = "، بينما ".join(verdict_parts) + f". ترجح النمذجة كفة **{winner_side}** بنسبة **{max_win_prob}%** مع أهداف متوقعة (**{xg_a} مقابل {xg_b}**)."

        return {
            "status": "success",
            "team_a": club_a,
            "team_b": club_b,
            "venue": req.venue,
            "simulation": {
                "prob_a": prob_a,
                "prob_draw": prob_draw,
                "prob_b": prob_b,
                "xg_a": xg_a,
                "xg_b": xg_b,
                "predicted_score": pred_score,
                "score_prob": sim["score_prob"],
                "markets": sim["markets"],
                "heatmap": heatmap,
                "tactical_summary": tactical_summary
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =========================================================================
# مسار منحنى الزخم الهجومي الحي وخريطة التسديدات (Attack Momentum API)
# =========================================================================
@app.get("/api/match_momentum/{league_code}/{match_id}")
def get_match_momentum_route(league_code: str, match_id: str):
    try:
        data = db.get_match_momentum(league_code.upper(), match_id)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# =========================================================================
# مسار بورصة الانتقالات وتجديد العقود (Mercato & Contract Renewals API)
# =========================================================================
@app.get("/api/mercato")
def get_mercato_and_contracts_route(refresh: bool = False):
    try:
        now_ts = time.time()
        allow_refresh = False
        if refresh and (now_ts - LAST_FORCE_REFRESH_TS["mercato"] > FORCE_REFRESH_COOLDOWN):
            allow_refresh = True
            LAST_FORCE_REFRESH_TS["mercato"] = now_ts

        data = db.get_mercato_and_contracts_data(force_refresh=allow_refresh)
        return {
            "status": "success",
            "transfers": data.get("transfers", []),
            "contracts": data.get("contracts", []),
            "ticker": data.get("ticker", [])
        }
    except Exception as e:
        return {"status": "error", "transfers": [], "contracts": [], "ticker": [], "message": str(e)}


# =========================================================================
# مسار ساحة التحدي الكروي الذكي
# =========================================================================
@app.get("/api/quiz_bank")
def get_quiz_arena_bank_route(
    league: str = "ALL",
    difficulty: str = "ALL",
    region: str = "ALL",
    category: str = "ALL",
    seed: str = "",
    use_ai: bool = False,
    count: int = 120
):
    try:
        data = db.get_quiz_arena_bank(
            league_filter=league,
            difficulty_filter=difficulty,
            region_filter=region,
            category_filter=category,
            seed_code=seed,
            use_ai=use_ai,
            batch_size=count
        )
        return {
            "status": "success",
            "total_pool_size": data.get("total_pool_size", 0),
            "matched_count": data.get("matched_count", 0),
            "fallback_used": data.get("fallback_used", False),
            "ai_available": data.get("ai_available", False),
            "category_counts": data.get("category_counts", {}),
            "questions": data.get("questions", []),
            "seed_code": data.get("seed_code", "")
        }
    except Exception as e:
        return {"status": "error", "questions": [], "message": str(e)}

# =========================================================================
# مسارات غرفة المحللين الأذكياء (AI Pundit Studio API)
# =========================================================================

class StudioAskRequest(BaseModel):
    league_code: str = "PL"
    match_id: str
    pundit_id: str = "tactician"
    question: str


@app.get("/api/ai_studio/{league_code}/{match_id}")
def get_ai_pundit_studio_route(league_code: str, match_id: str, phase: str = "auto"):
    try:
        data = db.get_ai_pundit_studio_analysis(
            league_code=league_code.upper(),
            match_id=match_id,
            requested_phase=phase.lower()
        )
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/ai_studio_ask")

class StudioAskRequest(BaseModel):
    league_code: str = Field(default="PL", max_length=10)
    match_id: str = Field(..., min_length=1, max_length=40)
    pundit_id: str = Field(default="tactician", max_length=30)
    question: str = Field(..., min_length=1, max_length=300)


@app.get("/api/ai_studio/{league_code}/{match_id}")
def get_ai_pundit_studio_route(league_code: str, match_id: str, phase: str = "auto"):
    try:
        data = db.get_ai_pundit_studio_analysis(
            league_code=league_code.upper(),
            match_id=match_id,
            requested_phase=phase.lower()
        )
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/ai_studio_ask")
def ask_studio_pundit_route(req: StudioAskRequest, request: Request):
    check_ai_rate_limit(request, max_requests=12, window_sec=60)
    try:
        res = db.ask_studio_pundit_question(
            league_code=req.league_code.upper(),
            match_id=req.match_id,
            pundit_id=req.pundit_id,
            question=req.question
        )
        return {"status": "success", "data": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}

 
@app.get("/api/card_profile_detail")
def get_card_profile_detail_route(
    entity_type: str = "club",
    name: str = "",
    extra: str = ""
):
    try:
        profile = db.get_live_entity_card_detail(
            entity_type=entity_type,
            name=name,
            extra=extra
        )
        return {"status": "success", "profile": profile}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/search")
def global_search_route(q: str = ""):
    try:
        res = db.global_platform_search(q)
        return {"status": "success", "query": q, "results": res}
    except Exception as e:
        return {"status": "error", "results": {"clubs": [], "nations": [], "transfers": [], "news": []}, "message": str(e)}


@app.get("/api/club_recent/{league_code}/{team_id}")
def club_recent_results_route(league_code: str, team_id: str):
    try:
        items = db.get_club_recent_results(league_code.upper(), team_id)
        return {"status": "success", "matches": items}
    except Exception as e:
        return {"status": "error", "matches": [], "message": str(e)}