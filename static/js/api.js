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
  projections: {}
};

const BROWSER_CACHE_TTL_MS = 5 * 60 * 1000;
const BROWSER_CACHE_TS = {};

function isBrowserCacheFresh(key) {
  return Boolean(BROWSER_CACHE_TS[key] && (Date.now() - BROWSER_CACHE_TS[key]) < BROWSER_CACHE_TTL_MS);
}

function touchBrowserCache(key) {
  BROWSER_CACHE_TS[key] = Date.now();
}
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
// ==========================================
// محرك شعارات البطولات الرسمية التلقائي (ESPN CDN + API + Cache)
// ==========================================
const DP_LEAGUE_LOGO_CACHE_KEY = 'deeppitch_league_logos_v1';
const DP_LEAGUE_LOGO_TTL_MS = 7 * 24 * 60 * 60 * 1000;

const DP_DEFAULT_LEAGUE_LOGOS = {
  'PL':  'https://a.espncdn.com/i/leaguelogos/soccer/500/23.png',
  'PD':  'https://a.espncdn.com/i/leaguelogos/soccer/500/15.png',
  'BL1': 'https://a.espncdn.com/i/leaguelogos/soccer/500/10.png',
  'SA':  'https://a.espncdn.com/i/leaguelogos/soccer/500/12.png',
  'FL1': 'https://a.espncdn.com/i/leaguelogos/soccer/500/9.png',
  'UCL': 'https://a.espncdn.com/i/leaguelogos/soccer/500/2.png',
  'DED': 'https://a.espncdn.com/i/leaguelogos/soccer/500/11.png',
  'PPL': 'https://a.espncdn.com/i/leaguelogos/soccer/500/14.png',
  'TSL': 'https://a.espncdn.com/i/leaguelogos/soccer/500/18.png'
};

const DP_DYNAMIC_ESPN_SLUGS = {
  'ACL': 'afc.champions',
  'CAF': 'caf.champions',
  'UNL': 'uefa.nations'
};

function loadSavedLeagueLogos() {
  try {
    const raw = JSON.parse(localStorage.getItem(DP_LEAGUE_LOGO_CACHE_KEY) || '{}');
    if (raw && raw.ts && (Date.now() - raw.ts) < DP_LEAGUE_LOGO_TTL_MS && raw.map) {
      return raw.map;
    }
  } catch (e) {}
  return {};
}

window.DP_LEAGUE_LOGOS_MAP = Object.assign({}, DP_DEFAULT_LEAGUE_LOGOS, loadSavedLeagueLogos());

function escapeLogoAttr(v) {
  return String(v || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

window.getLeagueLogoUrl = function(code, customUrl) {
  if (customUrl) return customUrl;
  const key = String(code || '').toUpperCase().trim();
  return window.DP_LEAGUE_LOGOS_MAP[key] || '';
};

window.renderLeagueLogoHtml = function(code, fallbackFlag, sizeClass, customUrl) {
  const key = String(code || '').toUpperCase().trim();
  const fb = escapeLogoAttr(fallbackFlag || '⚽');
  const sz = sizeClass || 'size-sm';
  const url = window.getLeagueLogoUrl(key, customUrl);

  if (!url) {
    return `<span class="dp-league-logo-wrap is-emoji ${sz}" data-league-logo="${escapeLogoAttr(key)}" data-fallback-flag="${fb}"><span class="dp-league-logo-fb">${fb}</span></span>`;
  }

  return `<span class="dp-league-logo-wrap ${sz}" data-league-logo="${escapeLogoAttr(key)}" data-fallback-flag="${fb}"><img src="${escapeLogoAttr(url)}" alt="" loading="lazy" onerror="this.style.display='none'; this.parentElement.classList.add('is-emoji'); if(this.nextElementSibling) this.nextElementSibling.style.display='inline';"><span class="dp-league-logo-fb" style="display:none;">${fb}</span></span>`;
};

async function hydrateDynamicLeagueLogos() {
  const saved = loadSavedLeagueLogos();
  let updated = false;

  const entries = Object.entries(DP_DYNAMIC_ESPN_SLUGS).filter(([code]) => !window.DP_LEAGUE_LOGOS_MAP[code]);
  if (entries.length === 0) return;

  await Promise.all(entries.map(async ([code, slug]) => {
    try {
      const res = await fetch(`https://site.api.espn.com/apis/site/v2/sports/soccer/${slug}/scoreboard`);
      if (!res.ok) return;
      const json = await res.json();
      const logos = json && json.leagues && json.leagues[0] && json.leagues[0].logos;
      if (Array.isArray(logos) && logos[0] && logos[0].href) {
        const href = logos[0].href;
        window.DP_LEAGUE_LOGOS_MAP[code] = href;
        saved[code] = href;
        updated = true;

        // تحديث جميع شعارات هذه البطولة الظاهرة حالياً في الصفحة تلقائياً
        document.querySelectorAll(`.dp-league-logo-wrap[data-league-logo="${code}"]`).forEach(el => {
          const fb = el.getAttribute('data-fallback-flag') || '⚽';
          el.classList.remove('is-emoji');
          el.innerHTML = `<img src="${escapeLogoAttr(href)}" alt="" loading="lazy" onerror="this.style.display='none'; this.parentElement.classList.add('is-emoji'); if(this.nextElementSibling) this.nextElementSibling.style.display='inline';"><span class="dp-league-logo-fb" style="display:none;">${escapeLogoAttr(fb)}</span>`;
        });
      }
    } catch (e) {}
  }));

  if (updated) {
    try {
      localStorage.setItem(DP_LEAGUE_LOGO_CACHE_KEY, JSON.stringify({ ts: Date.now(), map: saved }));
    } catch (e) {}
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
        ${window.renderLeagueLogoHtml(l.code, l.flag_emoji, 'size-sm', l.logo)}
        <span>${l.name}</span>
      </button>
    `).join('');

    hydrateDynamicLeagueLogos();
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
  await refreshCurrentView(false); // يستفيد من الكاش عند التنقل العادي، ويحدث من السيرفر عند ضغط زر التحديث
}

// ==========================================
// نظام تبديل الوضع الليلي والنهاري (Theme Engine)
// ==========================================
function syncAppThemeUI() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const sunIcon = document.getElementById('dp-theme-icon-sun');
  const moonIcon = document.getElementById('dp-theme-icon-moon');
  const toggleBtn = document.getElementById('dp-theme-toggle-btn');
  const themeMeta = document.querySelector('meta[name="theme-color"]');

  // في الوضع الليلي نعرض أيقونة الشمس للتبديل للنهاري، والعكس صحيح
  if (sunIcon) sunIcon.style.display = isLight ? 'none' : 'block';
  if (moonIcon) moonIcon.style.display = isLight ? 'block' : 'none';
  if (toggleBtn) {
    toggleBtn.title = isLight ? 'التبديل إلى الوضع الليلي' : 'التبديل إلى الوضع النهاري';
    toggleBtn.classList.toggle('is-active', isLight);
  }
  if (themeMeta) {
    themeMeta.setAttribute('content', isLight ? '#f1f5f9' : '#090d16');
  }
}

window.toggleAppTheme = function() {
  const isCurrentlyLight = document.documentElement.getAttribute('data-theme') === 'light';
  const nextTheme = isCurrentlyLight ? 'dark' : 'light';

  if (nextTheme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }

  try {
    localStorage.setItem('deeppitch_theme', nextTheme);
  } catch (e) {}

  syncAppThemeUI();

  if (typeof window.showAppToast === 'function') {
    window.showAppToast(nextTheme === 'light' ? 'تم تفعيل الوضع النهاري' : 'تم تفعيل الوضع الليلي');
  }
};

// تهيئة التطبيق عند اكتمال تحميل الصفحة
window.addEventListener('DOMContentLoaded', async () => {
  syncAppThemeUI();
  await loadLeagues();
});