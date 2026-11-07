# =========================================================================
# DeepPitch Pro - Machine Learning Training Pipeline (Scikit-Learn)
# =========================================================================

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

print("⚙️ جاري تجهيز البيانات التدريبية واستخراج الميزات (Feature Engineering)...")

# توليد مجموعة بيانات تاريخية معيارية لـ 3,500 مواجهة كروية محاكية لمسار الدوريات الكبرى
np.random.seed(42)
n_samples = 3500

# الميزات المستخرجة (Features):
# 1. فارق تصنيف الـ Elo بين الفريقين (Home Elo - Away Elo)
# 2. فارق نقاط الفورم لآخر 5 مباريات (Home Form - Away Form)
# 3. قوة هجوم المضيف مقابل دفاع الضيف
# 4. قوة هجوم الضيف مقابل دفاع المضيف
# 5. أفضلية اللعب على الأرض (Home Advantage constant)

elo_diff = np.random.normal(loc=0, scale=180, size=n_samples)
home_form = np.random.randint(2, 15, size=n_samples)
away_form = np.random.randint(2, 15, size=n_samples)
form_diff = home_form - away_form

home_att = np.random.uniform(0.6, 2.3, size=n_samples)
away_def = np.random.uniform(0.6, 2.3, size=n_samples)
h_att_matchup = home_att * away_def

away_att = np.random.uniform(0.6, 2.1, size=n_samples)
home_def = np.random.uniform(0.6, 2.1, size=n_samples)
a_att_matchup = away_att * home_def

home_adv = np.full(n_samples, 1.25)

X = np.column_stack([elo_diff, form_diff, h_att_matchup, a_att_matchup, home_adv])

# تحديد النتائج الواقعية وفق قوانين كرة القدم (0: خسارة المضيف، 1: تعادل، 2: فوز المضيف)
y = []
for i in range(n_samples):
    # حساب أرجحية كل نتيجة
    latent_score = (elo_diff[i] / 400.0) + (form_diff[i] * 0.08) + (h_att_matchup[i] - a_att_matchup[i]) * 0.5 + 0.35
    
    # إضافة ضوضاء عشوائية تحاكي طبيعة كرة القدم
    noise = np.random.normal(0, 0.45)
    final_val = latent_score + noise

    if final_val > 0.45:
        y.append(2)  # فوز المضيف (Home Win)
    elif final_val < -0.30:
        y.append(0)  # فوز الضيف (Away Win)
    else:
        y.append(1)  # تعادل (Draw)

y = np.array(y)

# تقسيم البيانات إلى تدريب (80%) واختبار (20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

print("🧠 جاري تدريب نموذج الغابات العشوائية (Random Forest Classifier)...")
model = RandomForestClassifier(
    n_estimators=180,
    max_depth=8,
    min_samples_split=6,
    random_state=42
)
model.fit(X_train, y_train)

# اختبار دقة النموذج
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"✅ تم التدريب بنجاح! دقة النموذج الرياضي على بيانات الاختبار: {acc * 100:.2f}%")

# حفظ النموذج المدرب
joblib.dump(model, "football_model.joblib")
print("💾 تم حفظ النموذج كملف جاهز للاستخدام: 'football_model.joblib'")