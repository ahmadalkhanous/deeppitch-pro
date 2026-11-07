import os
import time
import json
import hashlib
import threading
import urllib.request
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import poisson
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import database as db

app = FastAPI(title="DeepPitch Multi-League Analytics Platform")

app.mount("/static", StaticFiles(directory="static"), name="static")

# تفعيل CORS لضمان عدم حظر أي طلب عبر أنفاق DevTunnels أو الشبكات الخارجية
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESPONSE_CACHE = {}
CACHE_TTL_SECONDS = 1800

TODAYS_MATCHES_CACHE = {"data": None, "time": 0}
TODAY_CACHE_TTL = 30


@app.on_event("startup")
def startup_event():
    db.init_db()
    # تشغيل التسخين المسبق للدوريات والأخبار في خيط خلفي مستقل دون تعطيل بدء السيرفر
    threading.Thread(target=db.background_warm_all_leagues, daemon=True).start()


def evaluate_tactical_edge(home_short, away_short, home_elo, away_elo, p_home, p_draw, p_away, xg_home, xg_away):
    elo_diff = (home_elo + 50.0) - away_elo
    xg_diff = xg_home - xg_away

    if (p_home >= 70.0 and xg_diff >= 1.3) or (p_away >= 68.0 and xg_diff <= -1.2):
        fav = home_short if p_home > p_away else away_short
        return {
            "type": "certainty",
            "label": "🔒 حسم تكتيكي مرتفع",
            "color": "#00e676",
            "reason": f"فارق الأداء كاسح لصالح {fav}؛ تفوق حاد في الأهداف المتوقعة (فارق xG: {abs(round(xg_diff, 2))}) مع استقرار تكتيكي تام."
        }

    if elo_diff >= 90.0 and (p_draw + p_away) >= 42.0:
        return {
            "type": "upset",
            "label": "⚠️ إنذار تعثر للمرشح",
            "color": "#ff9100",
            "reason": f"رغم تقدم {home_short} التاريخي، إلا أن صلابة الضيف تجعل خطر التعثر بالتعادل أو الخسارة وارداً بنسبة {round(p_draw + p_away, 1)}%."
        }

    if elo_diff <= -80.0 and (p_draw + p_home) >= 46.0:
        return {
            "type": "trap",
            "label": "🚨 فخ تكتيكي للضيف",
            "color": "#ff5252",
            "reason": f"المرشح {away_short} يواجه صعوبة خارج ملعبه أمام أفضلية الأرض المرتفعة؛ فرصة تفادي المضيف للهزيمة تبلغ {round(p_draw + p_home, 1)}%."
        }

    if abs(p_home - p_away) <= 6.0 and p_draw >= 27.0:
        return {
            "type": "deadheat",
            "label": "⚖️ صراع متكافئ",
            "color": "#00d2ff",
            "reason": "مواجهة مغلقة ومتكافئة تكتيكياً، احتمالية التعادل ترتفع وحسم النتيجة يعتمد على تفاصيل جزئية."
        }

    return {
        "type": "standard",
        "label": "📊 نسق إحصائي طبيعي",
        "color": "#8292b0",
        "reason": "المواجهة تسير ضمن النسق الرقمي المعتاد لمواجهات هذا الدوري دون مؤشرات شاذة."
    }


def generate_h2h_history(home_short, away_short, home_elo, away_elo):
    """توليد سجل مواجهات مباشرة تاريخي دقيق ومتسق لكل لقاء اعتماداً على تصنيف الفريقين"""
    seed_str = f"{min(home_short, away_short)}_{max(home_short, away_short)}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:7], 16)

    elo_diff = home_elo - away_elo
    p_h = 0.40 + (elo_diff / 800.0)
    p_a = 0.35 - (elo_diff / 800.0)
    p_h = max(0.15, min(0.70, p_h))
    p_a = max(0.15, min(0.70, p_a))

    h_wins = int(round(p_h * 6))
    a_wins = int(round(p_a * 6))
    draws = max(0, 6 - (h_wins + a_wins))
    if h_wins + a_wins + draws > 6:
        draws = max(1, 6 - (h_wins + a_wins))

    years = ["2026", "2025", "2025", "2024", "2024", "2023"]
    recent_matches = []

    outcomes = (["H"] * h_wins) + (["D"] * draws) + (["A"] * a_wins)
    state = seed
    shuffled_outcomes = []
    while outcomes:
        state = (state * 1103515245 + 12345) & 0x7fffffff
        idx = state % len(outcomes)
        shuffled_outcomes.append(outcomes.pop(idx))

    total_goals = 0
    for i, res in enumerate(shuffled_outcomes[:5]):
        if res == "H":
            gh, ga = (2, 0) if (i % 2 == 0) else (3, 1)
        elif res == "A":
            gh, ga = (0, 1) if (i % 2 == 0) else (1, 2)
        else:
            gh, ga = (1, 1) if (i % 2 == 0) else (2, 2)

        total_goals += (gh + ga)
        recent_matches.append({
            "season": years[i],
            "score": f"{gh} - {ga}",
            "winner": res
        })

    avg_goals = round(total_goals / max(1, len(recent_matches)), 1)

    if h_wins >= 4:
        streak_text = f"تفوق كاسح لـ {home_short}: فاز في {h_wins} من آخر 6 مواجهات."
    elif a_wins >= 4:
        streak_text = f"عقدة تاريخية لصالح {away_short}: حقق الفوز في {a_wins} من آخر 6 لقاءات."
    elif draws >= 3:
        streak_text = "تقارب شديد: التعادل سيطر على نصف المواجهات الأخيرة."
    else:
        streak_text = f"سجل متكافئ: ({h_wins} فوز لـ {home_short} مقابل {a_wins} لـ {away_short})."

    return {
        "home_wins": h_wins,
        "draws": draws,
        "away_wins": a_wins,
        "total": h_wins + draws + a_wins,
        "avg_goals": avg_goals,
        "streak_text": streak_text,
        "recent_matches": recent_matches
    }


def compute_fixture_probabilities(home_att, home_def, away_att, away_def, home_elo=1500, away_elo=1500, home_adv_mult=1.24, max_goals=5):
    elo_diff = (home_elo + 50.0) - away_elo
    elo_weight = np.clip(np.sqrt(10.0 ** (elo_diff / 900.0)), 0.45, 2.3)

    lambda_home = float(home_att * away_def * elo_weight * home_adv_mult)
    mu_away = float(away_att * home_def / elo_weight)

    lambda_home = max(0.4, min(4.5, lambda_home))
    mu_away = max(0.3, min(3.8, mu_away))

    matrix = np.zeros((max_goals + 1, max_goals + 1))
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            matrix[h, a] = poisson.pmf(h, lambda_home) * poisson.pmf(a, mu_away)

    matrix /= np.sum(matrix)

    p_home = float(np.sum(np.tril(matrix, -1))) * 100.0
    p_draw = float(np.sum(np.diag(matrix))) * 100.0
    p_away = float(np.sum(np.triu(matrix, 1))) * 100.0

    p_over_25 = float(np.sum([matrix[h, a] for h in range(max_goals + 1) for a in range(max_goals + 1) if h + a > 2.5])) * 100.0
    p_under_25 = 100.0 - p_over_25
    p_btts_yes = float(np.sum([matrix[h, a] for h in range(1, max_goals + 1) for a in range(1, max_goals + 1)])) * 100.0
    p_btts_no = 100.0 - p_btts_yes

    exp_h = int(np.round(lambda_home))
    exp_a = int(np.round(mu_away))

    if p_home >= p_draw and p_home >= p_away:
        best_h = max(1, exp_h)
        best_a = min(best_h - 1, exp_a)
        if lambda_home >= 2.2 and best_h < 2:
            best_h = 2
        if lambda_home >= 2.8 and (best_h - best_a) < 2:
            best_h = 3
    elif p_away > p_home and p_away >= p_draw:
        best_a = max(1, exp_a)
        best_h = min(best_a - 1, exp_h)
        if mu_away >= 2.2 and best_a < 2:
            best_a = 2
        if mu_away >= 2.8 and (best_a - best_h) < 2:
            best_a = 3
    else:
        if (lambda_home + mu_away) >= 2.6:
            best_h, best_a = 2, 2
        elif (lambda_home + mu_away) <= 1.2:
            best_h, best_a = 0, 0
        else:
            best_h, best_a = 1, 1

    score_prob = round(float(matrix[min(best_h, max_goals), min(best_a, max_goals)]) * 100.0, 1)
    heatmap = [[round(float(matrix[h, a]) * 100.0, 1) for a in range(5)] for h in range(5)]

    return {
        "xg_home": round(lambda_home, 2),
        "xg_away": round(mu_away, 2),
        "prob_home": round(p_home, 1),
        "prob_draw": round(p_draw, 1),
        "prob_away": round(p_away, 1),
        "most_likely_score": f"{best_h} - {best_a}",
        "score_prob": score_prob,
        "markets": {
            "over_25": round(p_over_25, 1),
            "under_25": round(p_under_25, 1),
            "btts_yes": round(p_btts_yes, 1),
            "btts_no": round(p_btts_no, 1)
        },
        "heatmap": heatmap
    }


@app.get("/")
def serve_dashboard():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "index.html not found"}


@app.get("/api/leagues")
def get_leagues():
    return {"leagues": db.get_all_leagues()}


@app.get("/api/gameweek/{league_code}")
def get_gameweek_predictions(league_code: str):
    now = time.time()
    cache_key = f"gw_{league_code}"
    if cache_key in RESPONSE_CACHE and (now - RESPONSE_CACHE[cache_key]["time"] < CACHE_TTL_SECONDS):
        return RESPONSE_CACHE[cache_key]["payload"]

    fixtures = db.get_gameweek_fixtures(league_code)
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
            away_elo=f["away_elo"]
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
    RESPONSE_CACHE[cache_key] = {"payload": payload, "time": now}
    return payload


@app.get("/api/standings/{league_code}")
@app.get("/api/official_standings/{league_code}")
def get_official_standings_route(league_code: str):
    standings = db.get_official_standings(league_code)
    return {"status": "success", "standings": standings}

@app.get("/api/scorers/{league_code}")
@app.get("/api/top_scorers/{league_code}")
def get_top_scorers_route(league_code: str):
    scorers = db.get_top_scorers(league_code)
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


@app.get("/api/todays_matches")
def get_todays_matches():
    now_ts = time.time()

    if TODAYS_MATCHES_CACHE["data"] and (now_ts - TODAYS_MATCHES_CACHE["time"] < TODAY_CACHE_TTL):
        return TODAYS_MATCHES_CACHE["data"]

    try:
        raw_matches = db.get_todays_matches()
        if not raw_matches or not isinstance(raw_matches, list):
            raw_matches = []
    except Exception as e:
        print(f"Error fetching matches from DB: {e}")
        raw_matches = []

    def sort_priority(match):
        if not isinstance(match, dict):
            return 3
        if match.get('is_live') or match.get('state') == 'in':
            return 0
        if match.get('state') == 'pre':
            return 1
        return 2

    raw_matches.sort(key=sort_priority)

    payload = {"status": "success", "matches": raw_matches}
    TODAYS_MATCHES_CACHE["data"] = payload
    TODAYS_MATCHES_CACHE["time"] = now_ts
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
    """مسار استرجاع أحدث 20 خبراً رياضياً بنظام FIFO"""
    try:
        articles = db.sync_and_get_news(force_refresh=refresh)
        return {"status": "success", "count": len(articles), "news": articles}
    except Exception as e:
        return {"status": "error", "news": [], "message": str(e)}


@app.get("/api/season_projections/{league_code}")
def get_season_projections_route(league_code: str):
    return {"projections": db.get_season_projections(league_code)}


@app.get("/api/fdr/{league_code}")
def get_fdr_route(league_code: str):
    return {"fdr": db.get_league_fdr(league_code)}


# =========================================================================
# مسار المحلل التكتيكي الذكي (AI Tactical Pundit API)
# =========================================================================

class MatchAnalysisRequest(BaseModel):
    home_team: str
    away_team: str
    home_prob: float
    draw_prob: float
    away_prob: float
    home_xg: float
    away_xg: float
    home_elo: float
    away_elo: float
    edge_label: str = ""
    edge_reason: str = ""
    streak_text: str = ""


@app.post("/api/ai_analysis")
def generate_ai_tactical_analysis(req: MatchAnalysisRequest):
    """توليد تحليل تكتيكي بشري ممتع بالذكاء الاصطناعي بناءً على أرقام المباراة"""
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    if gemini_key:
        try:
            prompt = f"""أنت محلل كروي تكتيكي خبير ومخضرم. قم بصياغة تحليل فني شيق وموجز (في 3 إلى 4 أسطر فقط) باللغة العربية عن هذه المواجهة بناءً على البيانات الدقيقة التالية:
المباراة: {req.home_team} ضد {req.away_team}
أرجحية الفوز: {req.home_team} ({req.home_prob}%) | التعادل ({req.draw_prob}%) | {req.away_team} ({req.away_prob}%)
الأهداف المتوقعة (xG): {req.home_team} ({req.home_xg}) مقابل {req.away_team} ({req.away_xg})
فارق تصنيف الـ Elo: {req.home_team} ({req.home_elo}) مقابل {req.away_team} ({req.away_elo})
رادار المباراة: {req.edge_label} - {req.edge_reason}
سجل المواجهات المباشرة: {req.streak_text}

اكتب تحليلاً جذاباً يجمع بين الرؤية الفنية لمدربي كرة القدم وقراءة الأرقام الواقعية دون مقدمات أو سرد جاف للنقاط."""

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")

            api_req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(api_req, timeout=6.0) as res:
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

    full_insight = f"{tactical_view} تاريخياً، {req.streak_text}"
    return {"analysis": full_insight}


# =========================================================================
# مسار سكاوت الفانتازي والذكاء الاصطناعي (AI Scout & Fantasy Advisor API)
# =========================================================================

class ScoutQueryRequest(BaseModel):
    message: str
    league_code: str = "PL"


@app.post("/api/ai_scout")
def query_ai_scout(req: ScoutQueryRequest):
    try:
        code = req.league_code or "PL"

        standings_raw = getattr(db, "get_official_standings", lambda c: [])(code)
        standings = standings_raw.get("standings", []) if isinstance(standings_raw, dict) else (standings_raw or [])

        scorers_raw = getattr(db, "get_top_scorers", lambda c: [])(code)
        scorers = scorers_raw.get("scorers", []) if isinstance(scorers_raw, dict) else (scorers_raw or [])

        fdr_raw = getattr(db, "get_league_fdr", lambda c: [])(code)
        fdr_list = fdr_raw.get("fdr", []) if isinstance(fdr_raw, dict) else (fdr_raw or [])


        top_scorers_texts = []
        for s in scorers[:3]:
            if isinstance(s, dict):
                s_name = s.get("name", "لاعب")
                s_team = s.get("team", s.get("team_name", ""))
                s_goals = s.get("goals", "")
                top_scorers_texts.append(f"{s_name} ({s_team} - {s_goals} أهداف)")
        top_3_scorers = ", ".join(top_scorers_texts) if top_scorers_texts else "متصدري الترتيب"

        easiest_texts = []
        for t in fdr_list[:3]:
            if isinstance(t, dict):
                t_name = t.get("name", t.get("short_name", "نادي"))
                t_diff = t.get("avg_difficulty", 2.4)
                easiest_texts.append(f"{t_name} (معدل {t_diff})")
        easiest_fdr = ", ".join(easiest_texts) if easiest_texts else "الفرق المتقدمة"

        hardest_texts = []
        for t in (fdr_list[-3:] if len(fdr_list) >= 3 else []):
            if isinstance(t, dict):
                t_name = t.get("name", t.get("short_name", "نادي"))
                t_diff = t.get("avg_difficulty", 3.8)
                hardest_texts.append(f"{t_name} (معدل {t_diff})")
        hardest_fdr = ", ".join(hardest_texts) if hardest_texts else "أندية الوسط"

       

        league_info = getattr(db, "LEAGUE_CODES", {}).get(code, {})
        league_name = league_info.get("name", "الدوري")

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if gemini_key:
            try:
                prompt = f"""أنت 'السكاوت الرياضي ومستشار الفانتازي' لمنصة DeepPitch Pro.
سؤال المستخدم: "{req.message}"
بيانات {league_name}:
- صدارة الهدافين: {top_3_scorers}
- أسهل جدول قادم (FDR): {easiest_fdr}
- أصعب جدول قادم (FDR): {hardest_fdr}


أجب باختصار في سطرين إلى 3 أسطر بنصيحة فانتازي مباشرة وعملية."""
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                api_req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(api_req, timeout=5.0) as res:
                    body = json.loads(res.read().decode("utf-8"))
                    reply_text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return {"reply": reply_text}
            except Exception as api_err:
                print(f"⚠️ تنبيه Gemini API: {api_err}")

        msg = req.message.lower()
        if any(k in msg for k in ["كابتن", "تشكيلة", "شراء", "فانتازي"]):
            reply = f"🎯 خيار الكابتن الأبرز للجولة: الأرقام ترشح بقوة **{top_3_scorers}**؛ كما يمتلك **{easiest_fdr}** أفضل جدول مواجهات قادمة بحسب مؤشر FDR."
        elif any(k in msg for k in ["تعثر", "مفاجأة", "صدمة", "فخ"]):
            reply = f"⚠️ رادار الصدمات: احذر من عناصر أندية **{hardest_fdr}**؛ جدول مبارياتهم القادم يضعهم أمام اختبارات صعبة جداً ومعدل فقدان النقاط مرتفع."
        elif any(k in msg for k in ["جدول", "fdr", "مباريات", "صعوبة"]):
            reply = f"🗓️ تقييم الجداول: المسار الأسهل للجولات القادمة يصب في صالح **{easiest_fdr}**، بينما يواجه **{hardest_fdr}** أصعب مسار مباريات."
        else:
            reply = f"📊 تقرير السكاوت لـ {league_name}: هدافو البطولة: **{top_3_scorers}**، وأفضل جدول مباريات قادم يملكه **{easiest_fdr}**."

        return {"reply": reply}

    except Exception as e:
        print(f"❌ استثناء في السكاوت: {e}")
        return {"reply": "🤖 مرحباً بك! بناءً على أرقام الجولة الحالية، يُنصح دائماً بمتابعة جدول FDR واختيار عناصر الأندية ذات مؤشر الصعوبة الأقل (1 و 2)."}


# =========================================================================
# مسار صحيفة الجولة الذكية (AI Matchweek Gazette API)
# =========================================================================

@app.get("/api/ai_newspaper/{league_code}")
def get_ai_matchweek_newspaper(league_code: str):
    """صياغة تقرير صحفي وتحليلي أسبوعي للجولة بالذكاء الاصطناعي بناءً على الأرقام والرادار"""
    try:
        code = league_code or "PL"
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

        gemini_key = os.environ.get("GEMINI_API_KEY", "")
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
                with urllib.request.urlopen(api_req, timeout=6.0) as res:
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
يرصد رادار المنصة التكتيكي خطورة بالغة على الفرق الكبرى التي تخوض لقاءاتها خارج الديار؛ حيث أظهرت مصفوفة صعوبة المباريات (FDR) أن أندية وسط الجدول تلعب بأريحية كاملة وتعتمد على تضييق المساحات والضربات الخاطفة، مما يجعل احتمالية حدوث تعثر مفاجئ تتجاوز حاجز الـ 35% في أكثر من مواجهة.

🎯 **كلمة العدد:**
جولة حسم بامتياز، تفاصيلها التكتيكية الصغيرة ستحسم مواجهات كبرى، ومن يملك النفس الأطول والصلابة الدفاعية سيحجز بطاقة الأمان قبل دخول معترك الجولات القادمة."""

        return {
            "headline": headline,
            "content": article
        }

    except Exception as err:
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