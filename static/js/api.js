// ==========================================
// DeepPitch Pro - API & Global State Manager
// ==========================================

let activeLeague = "PL";
let activeSection = null;
let currentFixtures = [];
let activeFixtureForModal = null;
let currentRequestToken = 0;
let todayPollingTimeout = null;

// كاش المتصفح المركزي لمنع تكرار طلبات الشبكة
const BROWSER_CACHE = {
  fixtures: {},
  standings: {},
  scorers: {},
  xpts: {},
  projections: {},
  fdr: {}
};

// دالة جلب مرنة تدعم إعادة المحاولة التلقائية عند بطء الاتصال
async function fetchWithRetry(url, retries = 3, delayMs = 350) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise(r => setTimeout(r, delayMs * (i + 1)));
    }
  }
}

// تحميل قائمة الدوريات المدعومة وبناء الأزرار
async function loadLeagues() {
  try {
    const data = await fetchWithRetry('/api/leagues');
    const bar = document.getElementById('league-bar');
    if (!bar) return;

    bar.innerHTML = (data.leagues || []).map(l => `
      <button class="league-btn ${l.code === activeLeague ? 'active' : ''}" data-league="${l.code}" onclick="selectLeague('${l.code}')">
        <span>${l.flag_emoji}</span>
        <span>${l.name}</span>
      </button>
    `).join('');
  } catch (e) {
    console.error("خطأ في تحميل الدوريات:", e);
  }
}

// تبديل الدوري الفعّال
async function selectLeague(code) {
  activeLeague = code;
  document.querySelectorAll('.league-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-league') === code);
  });
  await refreshCurrentView();
}

// تهيئة التطبيق عند اكتمال تحميل الصفحة
window.addEventListener('DOMContentLoaded', async () => {
  await loadLeagues();
});