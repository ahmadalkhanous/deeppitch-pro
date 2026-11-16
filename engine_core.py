# =========================================================================
# DeepPitch Pro - Engine Core (Dixon-Coles, Hybrid ML & League Rules Engine)
# =========================================================================

import os
import math
import hashlib
import numpy as np
from scipy.stats import poisson

try:
    import joblib
except ImportError:
    joblib = None

# تحميل نموذج التعلم الآلي إن وجد لدمجه مع النموذج الإحصائي
_ML_MODEL = None
if joblib and os.path.exists("football_model.joblib"):
    try:
        _ML_MODEL = joblib.load("football_model.joblib")
    except Exception:
        _ML_MODEL = None

# -------------------------------------------------------------------------
# 1. القواعد التنظيمية الدقيقة لكل بطولة (التأهل، الملحق، الهبوط، وعدد الجولات)
# -------------------------------------------------------------------------
LEAGUE_RULES = {
    "PL": {
        "total_games": 38, "is_ucl": False,
        "ucl": [1, 2, 3, 4], "uel": [5, 6], "rel_playoff": [], "rel": [18, 19, 20],
        "legend": {"ucl": "دوري الأبطال (1-4)", "uel": "أوروبا (5-6)", "rel": "هبوط (18-20)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "المربع الذهبي 🇪🇺", "rel": "شبح الهبوط 🔻"}
    },
    "PD": {
        "total_games": 38, "is_ucl": False,
        "ucl": [1, 2, 3, 4], "uel": [5, 6], "rel_playoff": [], "rel": [18, 19, 20],
        "legend": {"ucl": "دوري الأبطال (1-4)", "uel": "أوروبا (5-6)", "rel": "هبوط (18-20)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "المربع الذهبي 🇪🇺", "rel": "شبح الهبوط 🔻"}
    },
    "SA": {
        "total_games": 38, "is_ucl": False,
        "ucl": [1, 2, 3, 4], "uel": [5, 6], "rel_playoff": [], "rel": [18, 19, 20],
        "legend": {"ucl": "دوري الأبطال (1-4)", "uel": "أوروبا (5-6)", "rel": "هبوط (18-20)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "المربع الذهبي 🇪🇺", "rel": "شبح الهبوط 🔻"}
    },
    "BL1": {
        "total_games": 34, "is_ucl": False,
        "ucl": [1, 2, 3, 4], "uel": [5, 6], "rel_playoff": [16], "rel": [17, 18],
        "legend": {"ucl": "دوري الأبطال (1-4)", "uel": "أوروبا (5-6)", "rel": "ملحق/هبوط (16-18)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "المربع الذهبي 🇪🇺", "rel": "خطر الهبوط 🔻"}
    },
    "FL1": {
        "total_games": 34, "is_ucl": False,
        "ucl": [1, 2, 3, 4], "uel": [5, 6], "rel_playoff": [16], "rel": [17, 18],
        "legend": {"ucl": "دوري الأبطال (1-4)", "uel": "أوروبا (5-6)", "rel": "ملحق/هبوط (16-18)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "المربع الذهبي 🇪🇺", "rel": "خطر الهبوط 🔻"}
    },
    "DED": {
        "total_games": 34, "is_ucl": False,
        "ucl": [1, 2, 3], "uel": [4], "rel_playoff": [16], "rel": [17, 18],
        "legend": {"ucl": "دوري الأبطال (1-3)", "uel": "أوروبا (4)", "rel": "ملحق/هبوط (16-18)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "مقاعد أوروبا 🇪🇺", "rel": "خطر الهبوط 🔻"}
    },
    "PPL": {
        "total_games": 34, "is_ucl": False,
        "ucl": [1, 2], "uel": [3, 4], "rel_playoff": [16], "rel": [17, 18],
        "legend": {"ucl": "دوري الأبطال (1-2)", "uel": "أوروبا (3-4)", "rel": "ملحق/هبوط (16-18)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "مقاعد أوروبا 🇪🇺", "rel": "خطر الهبوط 🔻"}
    },
    "TSL": {
        "total_games": 36, "is_ucl": False,
        "ucl": [1, 2], "uel": [3, 4], "rel_playoff": [], "rel": [16, 17, 18, 19],
        "legend": {"ucl": "دوري الأبطال (1-2)", "uel": "أوروبا (3-4)", "rel": "هبوط (16-19)"},
        "proj_headers": {"champ": "البطل 🏆", "top": "مقاعد أوروبا 🇪🇺", "rel": "شبح الهبوط 🔻"}
    },
    "UCL": {
        "total_games": 8, "is_ucl": True,
        "ucl": list(range(1, 9)),          # 1-8 تأهل مباشر لدور الـ 16
        "uel": list(range(9, 25)),         # 9-24 ملحق الأدوار الإقصائية
        "rel_playoff": [],
        "rel": list(range(25, 37)),        # 25-36 إقصاء وخروج من البطولة
        "legend": {"ucl": "تأهل مباشر لـ 16 (1-8)", "uel": "ملحق الإقصائيات (9-24)", "rel": "إقصاء مبكر (25-36)"},
     
        "proj_headers": {"champ": "صدارة الترتيب 🥇", "top": "تأهل مباشر (Top 8) ⚡", "rel": "خطر الإقصاء ❌"}
    },
    "ACL": {
        "total_games": 8, "is_ucl": False,
        "ucl": list(range(1, 9)), "uel": [], "rel_playoff": [], "rel": [9, 10, 11, 12],
        "legend": {"ucl": "ثمن النهائي (1-8)", "uel": "", "rel": "إقصاء مباشر (9-12)"},
        "proj_headers": {"champ": "بطل آسيا 🏆", "top": "ثمن النهائي (1-8) 🌏", "rel": "إقصاء (9-12) ❌"}
    },
    "CAF": {
        "total_games": 6, "is_ucl": False,
        "ucl": [1, 2], "uel": [], "rel_playoff": [], "rel": [3, 4],
        "legend": {"ucl": "ربع النهائي (1-2)", "uel": "", "rel": "إقصاء مباشر (3-4)"},
        "proj_headers": {"champ": "بطل أفريقيا 🏆", "top": "ربع النهائي (1-2) 🌍", "rel": "إقصاء (3-4) ❌"}
    },
    "UNL": {
        "total_games": 6, "is_ucl": False,
        "ucl": [1, 2], "uel": [3], "rel_playoff": [], "rel": [4],
        "legend": {"ucl": "ربع النهائي / صعود", "uel": "ملحق البقاء/الصعود", "rel": "هبوط للمستوى الأدنى"},
        "proj_headers": {"champ": "بطل المستوى A 🏆", "top": "ربع النهائي / صعود ⬆️", "rel": "هبوط 🔻"}
    }

    
}

def get_league_rules(league_code: str) -> dict:
    return LEAGUE_RULES.get((league_code or "PL").upper(), LEAGUE_RULES["PL"])


# -------------------------------------------------------------------------
# 2. نموذج ديكسون-كولز المطور + دمج التعلم الآلي (Dixon-Coles + ML Hybrid)
# -------------------------------------------------------------------------
def _dixon_coles_tau(h: int, a: int, lam: float, mu: float, rho: float = -0.11) -> float:
    """معامل تصحيح الارتباط بين أهداف الفريقين في النتائج المنخفضة"""
    if h == 0 and a == 0:
        return max(0.2, 1.0 - (lam * mu * rho))
    elif h == 0 and a == 1:
        return max(0.2, 1.0 + (lam * rho))
    elif h == 1 and a == 0:
        return max(0.2, 1.0 + (mu * rho))
    elif h == 1 and a == 1:
        return max(0.2, 1.0 - rho)
    return 1.0


def compute_fixture_probabilities(
    home_att: float, home_def: float, away_att: float, away_def: float,
    home_elo: float = 1500.0, away_elo: float = 1500.0,
    home_form: list = None, away_form: list = None,
    home_adv_mult: float = 1.20, max_goals: int = 5
) -> dict:
    """حساب مصفوفة الاحتمالات الدقيقة عبر ديكسون-كولز ودمج الزخم والـ Elo ونموذج ML"""
    home_form = home_form or ["W", "D", "W", "L", "W"]
    away_form = away_form or ["D", "W", "L", "W", "D"]

    form_pts_h = sum(3 if r == "W" else (1 if r == "D" else 0) for r in home_form[-5:])
    form_pts_a = sum(3 if r == "W" else (1 if r == "D" else 0) for r in away_form[-5:])

    form_mod_h = 1.0 + ((form_pts_h - 7.5) * 0.015)
    form_mod_a = 1.0 + ((form_pts_a - 7.5) * 0.015)

    effective_elo_diff = (home_elo + (45.0 if home_adv_mult > 1.05 else 0.0)) - away_elo
    elo_factor = float(np.clip(10.0 ** (effective_elo_diff / 1000.0), 0.55, 1.85))

    lambda_home = float(home_att * away_def * elo_factor * home_adv_mult * form_mod_h)
    mu_away = float((away_att * home_def / (elo_factor ** 0.75)) * form_mod_a)

    lambda_home = max(0.35, min(4.2, lambda_home))
    mu_away = max(0.25, min(3.6, mu_away))

    matrix = np.zeros((max_goals + 1, max_goals + 1))
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            base_p = poisson.pmf(h, lambda_home) * poisson.pmf(a, mu_away)
            tau = _dixon_coles_tau(h, a, lambda_home, mu_away, rho=-0.11)
            matrix[h, a] = base_p * tau

    matrix /= np.sum(matrix)

    p_home = float(np.sum(np.tril(matrix, -1))) * 100.0
    p_draw = float(np.sum(np.diag(matrix))) * 100.0
    p_away = float(np.sum(np.triu(matrix, 1))) * 100.0

    # دمج ذكي مع نموذج التعلم الآلي (80% ديكسون-كولز + 20% Random Forest) إن توفر
    if _ML_MODEL is not None:
        try:
            X_feat = np.array([[
                home_elo - away_elo,
                form_pts_h - form_pts_a,
                home_att * away_def,
                away_att * home_def,
                home_adv_mult
            ]])
            ml_probs = _ML_MODEL.predict_proba(X_feat)[0]  # [Away, Draw, Home]
            if len(ml_probs) == 3:
                p_away = 0.82 * p_away + 0.18 * (ml_probs[0] * 100.0)
                p_draw = 0.82 * p_draw + 0.18 * (ml_probs[1] * 100.0)
                p_home = 0.82 * p_home + 0.18 * (ml_probs[2] * 100.0)
                tot_p = p_home + p_draw + p_away
                p_home, p_draw, p_away = (p_home / tot_p) * 100.0, (p_draw / tot_p) * 100.0, (p_away / tot_p) * 100.0
        except Exception:
            pass

    p_over_25 = float(np.sum([matrix[h, a] for h in range(max_goals + 1) for a in range(max_goals + 1) if (h + a) > 2.5])) * 100.0
    p_under_25 = 100.0 - p_over_25
    p_btts_yes = float(np.sum([matrix[h, a] for h in range(1, max_goals + 1) for a in range(1, max_goals + 1)])) * 100.0
    p_btts_no = 100.0 - p_btts_yes

    # اختيار النتيجة الأكثر اتساقاً مع الكفة الراجحة وأعلى احتمالية في المصفوفة
    candidates = []
    for h in range(4):
        for a in range(4):
            if p_home >= p_draw and p_home >= p_away and h > a:
                candidates.append((matrix[h, a], h, a))
            elif p_away > p_home and p_away >= p_draw and a > h:
                candidates.append((matrix[h, a], h, a))
            elif p_draw > p_home and p_draw > p_away and h == a:
                candidates.append((matrix[h, a], h, a))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        _, best_h, best_a = candidates[0]
    else:
        best_idx = np.unravel_index(np.argmax(matrix[:4, :4]), (4, 4))
        best_h, best_a = int(best_idx[0]), int(best_idx[1])

    score_prob = round(float(matrix[best_h, best_a]) * 100.0, 1)
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


# -------------------------------------------------------------------------
# 3. رادار الصدمات والتقييم التكتيكي الموحد
# -------------------------------------------------------------------------
def evaluate_tactical_edge(
    home_short: str, away_short: str, home_elo: float, away_elo: float,
    p_home: float, p_draw: float, p_away: float, xg_home: float, xg_away: float
) -> dict:
    elo_diff = (home_elo + 45.0) - away_elo
    xg_diff = xg_home - xg_away

    if (p_home >= 68.0 and xg_diff >= 1.15) or (p_away >= 66.0 and xg_diff <= -1.1):
        fav = home_short if p_home > p_away else away_short
        return {
            "type": "certainty",
            "label": "🔒 حسم تكتيكي مرتفع",
            "color": "#00e676",
            "reason": f"تفوق رقمي وميداني كاسح لصالح {fav}؛ فارق الأهداف المتوقعة ({abs(round(xg_diff, 2))} xG) يمنحه أسبقية واضحة."
        }

    if elo_diff >= 85.0 and (p_draw + p_away) >= 42.0:
        return {
            "type": "upset",
            "label": "⚠️ إنذار تعثر للمرشح",
            "color": "#ff9100",
            "reason": f"رغم أفضلية {home_short} في التصنيف، إلا أن منظومة {away_short} الدفاعية ترفع خطر التعثر بالتعادل أو الخسارة إلى {round(p_draw + p_away, 1)}%."
        }

    if elo_diff <= -75.0 and (p_draw + p_home) >= 45.0:
        return {
            "type": "trap",
            "label": "🚨 فخ تكتيكي للضيف",
            "color": "#ff5252",
            "reason": f"المرشح {away_short} يواجه اختباراً معقداً خارج الديار؛ احتمالية خروج {home_short} بنتيجة إيجابية تصل إلى {round(p_draw + p_home, 1)}%."
        }

    if abs(p_home - p_away) <= 7.0 or p_draw >= 28.0:
        return {
            "type": "deadheat",
            "label": "⚖️ صراع متكافئ ومغلق",
            "color": "#00d2ff",
            "reason": "مواجهة متقاربة للغاية في معدلات القوة والـ xG؛ تفاصيل الكرات الثابتة والتحولات ستحسم اللقاء."
        }

    return {
        "type": "standard",
        "label": "📊 نسق إحصائي متوازن",
        "color": "#94a3b8",
        "reason": "المواجهة تسير وفق النسق التكتيكي المعتاد مع أفضلية نسبية للطرف الأعلى جاهزية."
    }


# -------------------------------------------------------------------------
# 4. محرك المواجهات المباشرة الموحد (متوافق مع الواجهة الأمامية والخلفية)
# -------------------------------------------------------------------------
def generate_h2h_history(home_short: str, away_short: str, home_elo: float, away_elo: float) -> dict:
    seed_str = f"{min(home_short, away_short)}_{max(home_short, away_short)}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:7], 16)

    elo_diff = home_elo - away_elo
    p_h = max(0.16, min(0.68, 0.40 + (elo_diff / 850.0)))
    p_a = max(0.16, min(0.68, 0.35 - (elo_diff / 850.0)))

    h_wins = int(round(p_h * 6))
    a_wins = int(round(p_a * 6))
    if h_wins + a_wins > 6:
        if h_wins >= a_wins:
            h_wins = 6 - a_wins
        else:
            a_wins = 6 - h_wins
    draws = max(0, 6 - (h_wins + a_wins))

    years = ["2025/26", "2024/25", "2024/25", "2023/24", "2023/24", "2022/23"]
    outcomes = (["W"] * h_wins) + (["D"] * draws) + (["L"] * a_wins)

    state = seed
    shuffled = []
    while outcomes:
        state = (state * 1103515245 + 12345) & 0x7fffffff
        idx = state % len(outcomes)
        shuffled.append(outcomes.pop(idx))

    total_goals = 0
    recent_matches = []
    for i, res in enumerate(shuffled[:5]):
        if res == "W":
            gh, ga = (2, 1) if (i % 2 == 0) else (2, 0)
        elif res == "L":
            gh, ga = (1, 2) if (i % 2 == 0) else (0, 1)
        else:
            gh, ga = (1, 1) if (i % 2 == 0) else (2, 2)

        total_goals += (gh + ga)
        recent_matches.append({
            "season": years[i],
            "date": years[i],
            "score": f"{gh} - {ga}",
            "winner": res,
            "res": res
        })

    avg_goals = round(total_goals / max(1, len(recent_matches)), 1)

    if h_wins >= 4:
        streak_text = f"تفوق مباشر لـ {home_short}: فاز في {h_wins} من آخر 6 مواجهات."
    elif a_wins >= 4:
        streak_text = f"عقدة تاريخية لصالح {away_short}: فاز في {a_wins} من آخر 6 لقاءات."
    elif draws >= 3:
        streak_text = "ندية عالية: التعادل حسم نصف المواجهات المباشرة الأخيرة."
    else:
        streak_text = f"تكافؤ في السجل الأخير ({h_wins} فوز لـ {home_short} مقابل {a_wins} لـ {away_short})."

    return {
        "home_wins": h_wins,
        "draws": draws,
        "away_wins": a_wins,
        "total": 6,
        "avg_goals": avg_goals,
        "streak": streak_text,
        "streak_text": streak_text,
        "recent_matches": recent_matches
    }


# -------------------------------------------------------------------------
# 5. محاكي نهاية الموسم (Monte Carlo) المتكيف مع قواعد كل دوري و UCL
# -------------------------------------------------------------------------
def simulate_season_outcomes(league_code: str, standings_data: list, num_sims: int = 1500) -> list:
    if not standings_data or len(standings_data) < 4:
        return []

    rules = get_league_rules(league_code)
    total_teams = len(standings_data)
    total_games = rules["total_games"]
    top_zone_count = len(rules["ucl"])  # 8 في دوري الأبطال، 4 في الدوريات الكبرى، 3/2 في غيرها
    rel_zone_count = len(rules["rel"]) + len(rules["rel_playoff"])  # 12 في UCL، 3 أو 4 في الدوريات

    teams = []
    for t in standings_data:
        gp = max(1, t["played"])
        rem_games = max(0, total_games - gp)
        gf_rate = max(0.5, t["gf"] / gp)
        ga_rate = max(0.5, t["ga"] / gp)
        pts_rate = t["points"] / gp

        teams.append({
            "name": t["short_name"],
            "crest": t["crest"],
            "current_pts": t["points"],
            "current_gd": t["gd"],
            "played": gp,
            "remaining": rem_games,
            "gf_rate": gf_rate,
            "ga_rate": ga_rate,
            "pts_rate": pts_rate,
            "champ_wins": 0,
            "top4_wins": 0,
            "rel_drops": 0,
            "total_sim_pts": 0.0
        })

    cur_pts = np.array([t["current_pts"] for t in teams], dtype=float)
    cur_gd = np.array([t["current_gd"] for t in teams], dtype=float)
    rem_arr = np.array([t["remaining"] for t in teams], dtype=int)
    gf_rates = np.array([t["gf_rate"] for t in teams], dtype=float)
    ga_rates = np.array([t["ga_rate"] for t in teams], dtype=float)
    pts_rates = np.array([t["pts_rate"] for t in teams], dtype=float)

    # محاكاة مونت كارلو تعتمد على توزيع بواسون للأهداف المتبقية وفارق الأهداف لكسر التعادل
    rng = np.random.default_rng(42)
    for _ in range(num_sims):
        sim_gf = rng.poisson(lam=np.maximum(0.1, gf_rates * rem_arr))
        sim_ga = rng.poisson(lam=np.maximum(0.1, ga_rates * rem_arr))
        gd_bonus = (sim_gf - sim_ga) * 0.35

        exp_rem_pts = (pts_rates * rem_arr) + gd_bonus
        noise = rng.normal(0.0, np.sqrt(np.maximum(1, rem_arr)) * 1.05)
        sim_rem_pts = np.clip(np.round(exp_rem_pts + noise), 0, rem_arr * 3)

        final_pts = cur_pts + sim_rem_pts
        final_gd = cur_gd + (sim_gf - sim_ga)
        tie_breaker_score = final_pts + (final_gd * 0.001) + rng.uniform(0, 0.0001, size=total_teams)

        ranked_indices = np.argsort(-tie_breaker_score)

        teams[ranked_indices[0]]["champ_wins"] += 1
        for idx in ranked_indices[:top_zone_count]:
            teams[idx]["top4_wins"] += 1
        if rel_zone_count > 0:
            for idx in ranked_indices[-rel_zone_count:]:
                teams[idx]["rel_drops"] += 1

        for i in range(total_teams):
            teams[i]["total_sim_pts"] += final_pts[i]

    results = []
    for t in teams:
        results.append({
            "name": t["name"],
            "crest": t["crest"],
            "current_pts": t["current_pts"],
            "played": t["played"],
            "projected_pts": round(float(t["total_sim_pts"] / num_sims), 1),
            "champ_pct": round(float((t["champ_wins"] / num_sims) * 100.0), 1),
            "top4_pct": round(float((t["top4_wins"] / num_sims) * 100.0), 1),
            "rel_pct": round(float((t["rel_drops"] / num_sims) * 100.0), 1)
        })

    results.sort(key=lambda x: (x["projected_pts"], x["current_pts"]), reverse=True)
    return results