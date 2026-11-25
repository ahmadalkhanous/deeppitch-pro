// =========================================================
// DeepPitch Pro - Views, Navigation & League Rules Engine
// =========================================================

function escapeHtml(str) {
  return String(str !== undefined && str !== null ? str : '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// محرك القواعد التنظيمية الدقيق لكل بطولة (المقاعد الأوروبية، الملحق، الهبوط، ونظام دوري الأبطال)
const LEAGUE_RULES_ENGINE = {
  'PL': {
    totalGames: 38,
    isUclFormat: false,
    uclRanks: [1, 2, 3, 4],
    uelRanks: [5, 6],
    relRanks: [18, 19, 20],
    legend: {
      ucl: 'دوري الأبطال (1-4)',
      uel: 'الدوري الأوروبي (5-6)',
      rel: 'هبوط مباشر (18-20)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 38 جولة):</strong> احتساب احتمالات التتويج باللقب، المربع الذهبي، وشبح الهبوط.',
      champ: 'البطل 🏆',
      top: 'المربع الذهبي 🇪🇺',
      rel: 'شبح الهبوط 🔻'
    }
  },
  'PD': {
    totalGames: 38,
    isUclFormat: false,
    uclRanks: [1, 2, 3, 4],
    uelRanks: [5, 6],
    relRanks: [18, 19, 20],
    legend: {
      ucl: 'دوري الأبطال (1-4)',
      uel: 'الدوري الأوروبي (5-6)',
      rel: 'هبوط مباشر (18-20)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 38 جولة):</strong> احتساب احتمالات التتويج باللقب، المربع الذهبي، وشبح الهبوط.',
      champ: 'البطل 🏆',
      top: 'المربع الذهبي 🇪🇺',
      rel: 'شبح الهبوط 🔻'
    }
  },
  'SA': {
    totalGames: 38,
    isUclFormat: false,
    uclRanks: [1, 2, 3, 4],
    uelRanks: [5, 6],
    relRanks: [18, 19, 20],
    legend: {
      ucl: 'دوري الأبطال (1-4)',
      uel: 'الدوري الأوروبي (5-6)',
      rel: 'هبوط مباشر (18-20)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 38 جولة):</strong> احتساب احتمالات التتويج باللقب، المربع الذهبي، وشبح الهبوط.',
      champ: 'البطل 🏆',
      top: 'المربع الذهبي 🇪🇺',
      rel: 'شبح الهبوط 🔻'
    }
  },
  'BL1': {
    totalGames: 34,
    isUclFormat: false,
    uclRanks: [1, 2, 3, 4],
    uelRanks: [5, 6],
    relRanks: [16, 17, 18],
    legend: {
      ucl: 'دوري الأبطال (1-4)',
      uel: 'أوروبا (5-6)',
      rel: 'ملحق هبوط (16) / هبوط (17-18)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 34 جولة):</strong> احتساب احتمالات اللقب، المربع الذهبي، والهبوط/الملحق.',
      champ: 'البطل 🏆',
      top: 'المربع الذهبي 🇪🇺',
      rel: 'هبوط / ملحق 🔻'
    }
  },
  'FL1': {
    totalGames: 34,
    isUclFormat: false,
    uclRanks: [1, 2, 3, 4],
    uelRanks: [5, 6],
    relRanks: [16, 17, 18],
    legend: {
      ucl: 'دوري الأبطال (1-4)',
      uel: 'أوروبا (5-6)',
      rel: 'ملحق هبوط (16) / هبوط (17-18)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 34 جولة):</strong> احتساب احتمالات اللقب، دوري الأبطال، والهبوط/الملحق.',
      champ: 'البطل 🏆',
      top: 'مقاعد الأبطال 🇪🇺',
      rel: 'هبوط / ملحق 🔻'
    }
  },
  'DED': {
    totalGames: 34,
    isUclFormat: false,
    uclRanks: [1, 2, 3],
    uelRanks: [4],
    relRanks: [16, 17, 18],
    legend: {
      ucl: 'دوري الأبطال (1-3)',
      uel: 'الدوري الأوروبي (4)',
      rel: 'ملحق هبوط (16) / هبوط (17-18)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 34 جولة):</strong> احتساب احتمالات اللقب، التأهل لدوري الأبطال (Top 3)، والهبوط.',
      champ: 'البطل 🏆',
      top: 'توب 3 أبطال 🇪🇺',
      rel: 'هبوط / ملحق 🔻'
    }
  },
  'PPL': {
    totalGames: 34,
    isUclFormat: false,
    uclRanks: [1, 2],
    uelRanks: [3, 4],
    relRanks: [16, 17, 18],
    legend: {
      ucl: 'دوري الأبطال (1-2)',
      uel: 'أوروبا (3-4)',
      rel: 'ملحق هبوط (16) / هبوط (17-18)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 34 جولة):</strong> احتساب احتمالات اللقب، مقاعد الأبطال، والهبوط.',
      champ: 'البطل 🏆',
      top: 'تأهل أوروبي 🇪🇺',
      rel: 'هبوط / ملحق 🔻'
    }
  },
  'TSL': {
    totalGames: 36,
    isUclFormat: false,
    uclRanks: [1, 2],
    uelRanks: [3, 4],
    relRanks: [16, 17, 18, 19],
    legend: {
      ucl: 'دوري الأبطال (1-2)',
      uel: 'أوروبا (3-4)',
      rel: 'هبوط مباشر (16-19)'
    },
    projHeaders: {
      note: '🔮 <strong>محاكاة مونت كارلو (1,500 دورة - 36 جولة):</strong> احتساب احتمالات اللقب، مقاعد أوروبا، وهبوط آخر 4 أندية.',
      champ: 'البطل 🏆',
      top: 'تأهل أوروبي 🇪🇺',
      rel: 'شبح الهبوط 🔻'
    }
  },
  
  'UCL': {
    totalGames: 8,
    isUclFormat: true,
    isGrouped: false,
    uclRanks: [1, 2, 3, 4, 5, 6, 7, 8],
    uelRanks: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
    relRanks: [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36],
    legend: {
      ucl: 'تأهل مباشر لدور الـ16 (1-8)',
      uel: 'ملحق الإقصائيات (9-24)',
      rel: 'إقصاء وخروج نهائي (25-36)'
    },
    projHeaders: {
      note: '🏆 <strong>نظام مرحلة الدوري لدوري أبطال أوروبا (8 جولات):</strong> المراكز (1–8) تأهل مباشر لثمن النهائي • المراكز (9–24) ملحق الإقصائيات • المراكز (25–36) إقصاء نهائي.',
      champ: 'بطل أوروبا 🏆',
      top: 'تأهل مباشر (Top 8) ⚡',
      rel: 'إقصاء وخروج ❌'
    }
  },
  'ACL': {
    totalGames: 8,
    isUclFormat: false,
    isGrouped: true,
    uclRanks: [1, 2, 3, 4, 5, 6, 7, 8],
    uelRanks: [],
    relRanks: [9, 10, 11, 12],
    legend: {
      ucl: 'تأهل مباشر لثمن النهائي (1-8 في الغرب والشرق)',
      uel: '',
      rel: 'إقصاء مباشر بدون ملحق (9-12)'
    },
    projHeaders: {
      note: '🌏 <strong>نظام دوري أبطال آسيا للنخبة (منطقتا الغرب والشرق - 8 جولات):</strong> يتأهل أصحاب المراكز (1–8) في كل منطقة مباشرة لدور الـ 16، بينما يودع أصحاب المراكز (9–12) البطولة مباشرة دون ملحق.',
      champ: 'بطل آسيا 🏆',
      top: 'ثمن النهائي (1-8) 🌏',
      rel: 'إقصاء (9-12) ❌'
    }
  },
  'CAF': {
    totalGames: 6,
    isUclFormat: false,
    isGrouped: true,
    uclRanks: [1, 2],
    uelRanks: [],
    relRanks: [3, 4],
    legend: {
      ucl: 'تأهل مباشر لربع النهائي (الأول والثاني)',
      uel: '',
      rel: 'إقصاء مباشر بدون ملحق (الثالث والرابع)'
    },
    projHeaders: {
      note: '🌍 <strong>نظام مجموعات دوري أبطال أفريقيا (4 مجموعات - 6 جولات):</strong> يتأهل الأول والثاني من كل مجموعة مباشرة إلى ربع النهائي، بينما يخرج الثالث والرابع نهائياً دون ملحق.',
      champ: 'بطل أفريقيا 🏆',
      top: 'ربع النهائي (1-2) 🌍',
      rel: 'إقصاء (3-4) ❌'
    }
  },
  'UNL': {
    totalGames: 6,
    isUclFormat: false,
    isGrouped: true,
    uclRanks: [1, 2],
    uelRanks: [3],
    relRanks: [4],
    legend: {
      ucl: 'ربع النهائي (مستوى A) / صعود مباشر (B, C, D)',
      uel: 'ملحق الصعود أو البقاء',
      rel: 'هبوط للمستوى الأدنى'
    },
    projHeaders: {
      note: '🇪🇺 <strong>نظام المستويات والمجموعات لدوري الأمم الأوروبية (Leagues A, B, C, D):</strong> أول وثاني مجموعات المستوى A يتأهلان لربع النهائي للمنافسة على اللقب • أوائل المستويات B و C و D يصعدون للمستوى الأعلى وأصحاب المركز الثاني يخوضون ملحق الصعود • أواخر المجموعات يهبطون للمستوى الأدنى.',
      champ: 'بطل المستوى A 🏆',
      top: 'ربع النهائي / صعود ⬆️',
      rel: 'هبوط للمستوى الأدنى 🔻'
    }
  }

};

window._viewReqToken = 0;

function formatLocalKickoff(isoStr, fallbackText, onlyTime = false) {
  if (!isoStr) return fallbackText || '';
  try {
    const dt = new Date(isoStr);
    if (isNaN(dt.getTime())) return fallbackText || '';
    if (onlyTime) {
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    }
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, '0');
    const d = String(dt.getDate()).padStart(2, '0');
    const t = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    return `${y}-${m}-${d} ${t}`;
  } catch (e) {
    return fallbackText || '';
  }
}

function getLeagueRulesConfig(leagueCode) {
  const code = (leagueCode || 'PL').toUpperCase();
  return LEAGUE_RULES_ENGINE[code] || LEAGUE_RULES_ENGINE['PL'];
}

// =========================================================
// 1. إدارة التنقل بين الشاشات الرئيسية
// =========================================================
// =========================================================
// 1. إدارة التنقل الموحّد (5 بوابات + Hash Router + البحث السريع + Skeleton)
// =========================================================
const DP_SECTION_TO_PILLAR = {
  'today': 'today',
  'fixtures': 'competitions',
  'standings': 'competitions',
  'projections': 'competitions',
  'history': 'competitions',
  'transfers': 'media',
  'news': 'media',
  'cards': 'explore',
  'radar': 'explore',
  'quiz': 'quiz'
};

const DP_PILLAR_LAST_SUB = {
  'today': 'today',
  'competitions': 'fixtures',
  'media': 'transfers',
  'explore': 'cards',
  'quiz': 'quiz'
};

function renderSkeletonCardsHtml(count = 4) {
  return Array.from({ length: count }).map(() => `
    <div class="dp-skel-card">
      <div style="display:flex; justify-content:space-between; gap:10px;">
        <div class="dp-skel" style="height:14px; width:42%;"></div>
        <div class="dp-skel" style="height:18px; width:24%; border-radius:99px;"></div>
      </div>
      <div style="display:flex; justify-content:space-around; align-items:center; padding:10px 0;">
        <div class="dp-skel" style="width:46px; height:46px; border-radius:14px;"></div>
        <div class="dp-skel" style="width:68px; height:34px; border-radius:10px;"></div>
        <div class="dp-skel" style="width:46px; height:46px; border-radius:14px;"></div>
      </div>
      <div class="dp-skel" style="height:8px; width:100%; border-radius:99px;"></div>
      <div class="dp-skel" style="height:30px; width:100%; border-radius:10px;"></div>
    </div>
  `).join('');
}

function navigateToPillar(pillarKey) {
  const targetSection = DP_PILLAR_LAST_SUB[pillarKey] || 'today';
  activateSection(targetSection);
}

function activateSection(section, fromHash = false) {
  const validViews = ['today', 'fixtures', 'standings', 'projections', 'history', 'transfers', 'news', 'cards', 'radar', 'quiz'];
  if (!validViews.includes(section)) section = 'today';

  const pillar = DP_SECTION_TO_PILLAR[section] || 'today';
  DP_PILLAR_LAST_SUB[pillar] = section;

  window.activeSection = section;
  if (typeof activeSection !== 'undefined') activeSection = section;

  // تحديث رابط المتصفح ليعمل زر الرجوع في الجوال والكمبيوتر بشكل طبيعي
  if (!fromHash && window.location.hash !== `#${section}`) {
    try { history.pushState({ section }, '', `#${section}`); } catch (e) { window.location.hash = section; }
  }

  // مزامنة الشريط العلوي للكمبيوتر والشريط السفلي للجوال
  document.querySelectorAll('#dp-desktop-nav .dp-nav-pill').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-pillar') === pillar);
  });
  if (typeof window.syncMobileBottomNav === 'function') window.syncMobileBottomNav(pillar);

  // إظهار/إخفاء التبويبات الفرعية لكل بوابة
  const compShell = document.getElementById('competitions-shell');
  const mediaSub = document.getElementById('media-subtabs');
  const exploreSub = document.getElementById('explore-subtabs');
  const smartBar = document.getElementById('smart-tools-bar');

  if (compShell) compShell.style.display = (pillar === 'competitions') ? 'block' : 'none';
  if (mediaSub) mediaSub.style.display = (pillar === 'media') ? 'flex' : 'none';
  if (exploreSub) exploreSub.style.display = (pillar === 'explore') ? 'flex' : 'none';
  if (smartBar) smartBar.style.display = (section === 'fixtures') ? 'flex' : 'none';

  document.querySelectorAll('.dp-subtab-btn[data-sub]').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-sub') === section);
  });

  validViews.forEach(v => {
    const el = document.getElementById(`${v}-view`);
    if (el) el.style.display = (v === section) ? 'block' : 'none';
  });

  if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) {
    clearTimeout(todayPollingTimeout);
    todayPollingTimeout = null;
  }
  if (section !== 'quiz' && typeof stopQuizTimer === 'function') {
    stopQuizTimer();
  }

  window.scrollTo({ top: 0, behavior: 'instant' });

  const league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  if (section === 'today') loadTodayMatches();
  else if (section === 'news') loadNewsFeed();
  else if (section === 'fixtures') loadGameweek(league);
  else if (section === 'standings') loadOfficialStandingsAndScorers(league);
  else if (section === 'projections') loadProjections(league);
  else if (section === 'cards') loadCardsHub();
  else if (section === 'history') loadLeagueHistory(league);
  else if (section === 'radar') initRadarClashStudio();
  else if (section === 'transfers') loadMercatoHub();
  else if (section === 'quiz') loadQuizArena();
}

function goBackToMainMenu() {
  navigateToPillar('today');
}

function refreshCurrentView(forceRefresh = true) {
  const league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  const sec = window.activeSection || 'today';
  if (sec === 'fixtures') loadGameweek(league, forceRefresh);
  else if (sec === 'standings') loadOfficialStandingsAndScorers(league, forceRefresh);
  else if (sec === 'projections') loadProjections(league, forceRefresh);
  else if (sec === 'cards') loadCardsHub(forceRefresh);
  else if (sec === 'today') loadTodayMatches();
  else if (sec === 'news') loadNewsFeed(forceRefresh);
  else if (sec === 'history') loadLeagueHistory(league, forceRefresh);
  else if (sec === 'radar') initRadarClashStudio();
  else if (sec === 'transfers') loadMercatoHub(true);
  else if (sec === 'quiz') loadQuizArena(true);
}

// =========================================================
// البحث العالمي السريع (Global Quick Search)
// =========================================================
// =========================================================
// إشعار Toast موحد بديل عن alert() التقليدي
// =========================================================
window.showAppToast = function(msg) {
  const old = document.getElementById('dp-mobile-toast');
  if (old) old.remove();
  const toast = document.createElement('div');
  toast.id = 'dp-mobile-toast';
  toast.style.cssText = `
    position: fixed; top: 72px; left: 50%; transform: translateX(-50%);
    background: var(--card, #121a2b); border: 1px solid var(--accent-green, #10b981);
    color: var(--text, #f8fafc); padding: 9px 18px; border-radius: 99px; font-size: 0.82rem;
    font-weight: 800; z-index: 3500; box-shadow: 0 8px 24px rgba(0,0,0,0.45);
    white-space: nowrap; max-width: 92vw; overflow: hidden; text-overflow: ellipsis; direction: rtl;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => { if (toast.parentNode) toast.remove(); }, 2600);
};

// =========================================================
// البحث العالمي السريع (Global Quick Search) وفتح ملف النادي
// =========================================================
window._globalSearchLoading = false;

async function preloadGlobalSearchSources() {
  if (window._globalSearchLoading) return;
  const tasks = [];
  const curLg = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';

  if (!window._cachedStandingsData || window._cachedStandingsData.length === 0) {
    tasks.push(
      fetch(`/api/official_standings/${curLg}?refresh=false`)
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          const list = d && (d.standings || (Array.isArray(d) ? d : []));
          if (list && list.length > 0) {
            window._cachedStandingsData = list;
            window._cachedStandingsLeague = curLg;
          }
        }).catch(() => {})
    );
  }

  if (typeof currentNewsItems !== 'undefined' && currentNewsItems.length === 0) {
    tasks.push(
      fetch('/api/news?refresh=false')
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d && Array.isArray(d.news)) currentNewsItems = d.news; })
        .catch(() => {})
    );
  }

  if (window._mercatoState && window._mercatoState.transfersList.length === 0) {
    tasks.push(
      fetch('/api/mercato?refresh=false')
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (d && d.status === 'success') {
            window._mercatoState.transfersList = d.transfers || [];
            window._mercatoState.contractsList = d.contracts || [];
            window._mercatoState.tickerNews = d.ticker || [];
          }
        }).catch(() => {})
    );
  }

  if (tasks.length === 0) return;
  window._globalSearchLoading = true;
  await Promise.all(tasks);
  window._globalSearchTimer = null;
window._globalSearchToken = 0;
window._lastQuickSearchResults = [];

window.openGlobalSearchModal = function() {
  const modal = document.getElementById('global-search-modal');
  const inp = document.getElementById('dp-global-search-input');
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  if (inp) { inp.value = ''; inp.focus(); }
  window.runGlobalQuickSearch('');
};

window.openDirectSearchClub = function(lg, tid, rawName, arName, crest, rank) {
  if (typeof window.closeModal === 'function') window.closeModal('global-search-modal');
  if (typeof openEntityHistoryModal === 'function') {
    openEntityHistoryModal(
      'club',
      encodeURIComponent(rawName || arName || ''),
      encodeURIComponent(arName || rawName || ''),
      encodeURIComponent(crest || ''),
      lg || window._cachedStandingsLeague || (typeof activeLeague !== 'undefined' ? activeLeague : 'PL'),
      rank || '-',
      tid || ''
    );
  }
};

async function openMercatoItemFromSearch(itemId) {
  if (typeof window.closeModal === 'function') window.closeModal('global-search-modal');
  const st = window._mercatoState;
  const findAndOpen = () => {
    if (st.transfersList.some(x => String(x.id) === String(itemId))) {
      openMercatoDetailModal('transfers', itemId);
      return true;
    }
    if (st.contractsList.some(x => String(x.id) === String(itemId))) {
      openMercatoDetailModal('contracts', itemId);
      return true;
    }
    return false;
  };
  if (findAndOpen()) return;
  try {
    const res = await fetch('/api/mercato?refresh=false');
    const data = await res.json();
    if (data && data.status === 'success') {
      st.transfersList = data.transfers || [];
      st.contractsList = data.contracts || [];
      st.tickerNews = data.ticker || [];
      if (findAndOpen()) return;
    }
  } catch (e) {}
  activateSection('transfers');
}

window.executeQuickSearchItem = function(idx) {
  const item = (window._lastQuickSearchResults || [])[idx];
  if (!item) return;
  if (typeof window.closeModal === 'function') window.closeModal('global-search-modal');

  if (item.kind === 'match') {
    openTodayMatchModal(item.matchIdx);
  } else if (item.kind === 'club') {
    openDirectSearchClub(item.leagueCode, item.teamId, item.rawName, item.name, item.crest, item.rank);
  } else if (item.kind === 'nation') {
    openEntityHistoryModal(
      'nation',
      encodeURIComponent(item.rawName || item.name),
      encodeURIComponent(item.name),
      encodeURIComponent(item.flagUrl || ''),
      item.confed || 'FIFA',
      item.rank || '-'
    );
  } else if (item.kind === 'mercato') {
    openMercatoItemFromSearch(item.itemId);
  } else if (item.kind === 'news') {
    openNewsArticleByObj(item.newsObj);
  }
};

function renderQuickSearchBox(results, isSearchingBackend = false) {
  const box = document.getElementById('dp-global-search-results');
  if (!box) return;
  window._lastQuickSearchResults = results;

  if (results.length === 0) {
    box.innerHTML = isSearchingBackend
      ? '<div style="text-align:center; padding:24px 10px; color:var(--accent-green); font-size:0.84rem; font-weight:700;">جاري البحث في جميع البطولات والمنتخبات والأخبار...</div>'
      : '<div style="text-align:center; padding:24px 10px; color:var(--muted); font-size:0.84rem;">لم يتم العثور على نتائج مطابقة حالياً.</div>';
    return;
  }

  box.innerHTML = results.slice(0, 18).map((r, idx) => `
    <div class="dp-search-item" onclick="executeQuickSearchItem(${idx})">
      <div style="min-width:0;">
        <div style="font-weight:800; font-size:0.86rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(r.title)}</div>
        <div style="font-size:0.74rem; color:var(--muted); margin-top:2px;">${escapeHtml(r.sub)}</div>
      </div>
      <span class="hub-badge">${escapeHtml(r.badge)}</span>
    </div>
  `).join('');
}

window.runGlobalQuickSearch = function(rawQuery) {
  const box = document.getElementById('dp-global-search-results');
  if (!box) return;
  const q = (rawQuery || '').trim();
  const qLow = q.toLowerCase();

  if (window._globalSearchTimer) clearTimeout(window._globalSearchTimer);

  if (qLow.length < 2) {
    window._lastQuickSearchResults = [];
    box.innerHTML = '<div style="text-align:center; padding:24px 10px; color:var(--muted); font-size:0.84rem;">اكتب حرفين على الأقل للبحث السريع في المباريات والأندية والمنتخبات والأخبار والانتقالات</div>';
    return;
  }

  // 1. نتائج فورية من مباريات اليوم المحمّلة
  const localMatches = [];
  (window.currentTodayMatches || []).forEach((m, idx) => {
    const hay = `${m.home_team} ${m.away_team} ${m.home_en || ''} ${m.away_en || ''} ${m.league_name}`.toLowerCase();
    if (hay.includes(qLow)) {
      localMatches.push({
        kind: 'match',
        badge: 'مباراة',
        title: `${m.home_team} ضد ${m.away_team}`,
        sub: `${m.league_name} • ${m.state === 'pre' ? formatLocalKickoff(m.kickoff_iso, m.kickoff_time, true) : `${m.home_score} - ${m.away_score}`}`,
        matchIdx: idx
      });
    }
  });

  renderQuickSearchBox(localMatches, true);

  // 2. استعلام السيرفر /api/search بعد 250ms للبحث الشامل في كل البطولات والمنتخبات والميركاتو والأخبار
  const token = ++window._globalSearchToken;
  window._globalSearchTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      if (token !== window._globalSearchToken) return;
      const json = await res.json();
      const srv = (json && json.results) ? json.results : {};
      const merged = [...localMatches];

      (srv.clubs || []).forEach(c => {
        merged.push({
          kind: 'club',
          badge: 'نادٍ',
          title: c.name || c.raw_name,
          sub: `${c.league_code || ''} • المركز #${c.rank} • ${c.points} نقطة`,
          leagueCode: c.league_code,
          teamId: c.team_id,
          rawName: c.raw_name,
          name: c.name,
          crest: c.crest,
          rank: c.rank
        });
      });

      (srv.nations || []).forEach(n => {
        merged.push({
          kind: 'nation',
          badge: 'منتخب',
          title: n.name || n.raw_name,
          sub: `${n.confederation || 'FIFA'} • تصنيف الفيفا #${n.rank}`,
          rawName: n.raw_name,
          name: n.name,
          flagUrl: n.flag_url,
          confed: n.confederation,
          rank: n.rank
        });
      });

      (srv.transfers || []).forEach(t => {
        merged.push({
          kind: 'mercato',
          badge: 'ميركاتو',
          title: t.name,
          sub: `${t.from_club}${t.to_club ? ` ⬅️ ${t.to_club}` : ''} (${t.status_label || ''})`,
          itemId: t.id
        });
      });

      (srv.news || []).forEach(n => {
        merged.push({
          kind: 'news',
          badge: 'خبر',
          title: n.title,
          sub: n.published_time || 'غرفة الأخبار',
          newsObj: n
        });
      });

      renderQuickSearchBox(merged, false);
    } catch (e) {
      if (token === window._globalSearchToken) {
        renderQuickSearchBox(localMatches, false);
      }
    }
  }, 250);
};
};

// تفعيل التوجيه بالرابط وزر الرجوع التلقائي بشكل متزامن مع النوافذ
window.addEventListener('hashchange', () => {
  document.querySelectorAll('.modal-overlay').forEach(m => {
    if (m.style.display === 'flex') m.style.display = 'none';
  });
  document.body.style.overflow = '';
  document.documentElement.style.overflow = '';
  const sec = (window.location.hash || '#today').replace('#', '');
  if (sec && sec !== window.activeSection) activateSection(sec, true);
});

window.addEventListener('DOMContentLoaded', () => {
  const initialSec = (window.location.hash || '#today').replace('#', '');
  setTimeout(() => activateSection(initialSec || 'today', true), 60);
});
// =========================================================
// 2. عرض كروت مباريات الجولة والرادار التكتيكي
// =========================================================
function renderFixturesList(fixtures) {
  const container = document.getElementById('fixtures-container');
  if (!container) return;

  if (!fixtures || fixtures.length === 0) {
    container.innerHTML = '<div class="loading-state">لا توجد مباريات مجدولة حالياً لهذا الدوري.</div>';
    return;
  }

  container.innerHTML = fixtures.map((f, idx) => {
    const safeColor = escapeHtml((f.edge && f.edge.color) || '#10b981');
    return `
      <div class="fixture-card" data-match-id="${escapeHtml(f.fixture_id)}" onclick="openModal(${idx})">
        <div class="fixture-header">
          <span>الجولة ${escapeHtml(f.gameweek)} • 🕒 ${escapeHtml(formatLocalKickoff(f.kickoff_iso, f.kickoff_time, false))}</span>
          <span class="radar-pill" style="background: ${safeColor}20; color: ${safeColor}; border: 1px solid ${safeColor};">
            ${escapeHtml(f.edge && f.edge.label)}
          </span>
        </div>

        <div class="teams-matchup">
          <div class="team-col">
            <div class="crest-wrapper"><img src="${escapeHtml(f.home.crest)}" alt="${escapeHtml(f.home.short)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;"></div>
            <div class="team-title">${escapeHtml(f.home.short)}</div>
            <div class="team-elo">Elo ${escapeHtml(f.home.elo)}</div>
            <div class="form-badges">
              ${(f.home.form || []).map(res => `<span class="badge-f form-${escapeHtml(res).toLowerCase()}">${escapeHtml(res)}</span>`).join('')}
            </div>
          </div>

          <div class="vs-center" style="text-align:center;">
            <div class="score-badge">${escapeHtml(f.predicted_score)}</div>
            <div style="font-size:0.72rem; color:var(--muted); margin-top:4px; font-weight:700;">ثقة (${escapeHtml(f.score_confidence)}%)</div>
          </div>

          <div class="team-col">
            <div class="crest-wrapper"><img src="${escapeHtml(f.away.crest)}" alt="${escapeHtml(f.away.short)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;"></div>
            <div class="team-title">${escapeHtml(f.away.short)}</div>
            <div class="team-elo">Elo ${escapeHtml(f.away.elo)}</div>
            <div class="form-badges">
              ${(f.away.form || []).map(res => `<span class="badge-f form-${escapeHtml(res).toLowerCase()}">${escapeHtml(res)}</span>`).join('')}
            </div>
          </div>
        </div>

        <div class="prob-bar">
          <div class="prob-home" style="width: ${Number(f.home.prob) || 0}%"></div>
          <div class="prob-draw" style="width: ${Number(f.draw_prob) || 0}%"></div>
          <div class="prob-away" style="width: ${Number(f.away.prob) || 0}%"></div>
        </div>

        <div class="prob-labels">
          <span>${escapeHtml(f.home.short)}: <strong>${escapeHtml(f.home.prob)}%</strong></span>
          <span>تعادل: <strong>${escapeHtml(f.draw_prob)}%</strong></span>
          <span>${escapeHtml(f.away.short)}: <strong>${escapeHtml(f.away.prob)}%</strong></span>
        </div>

        <div class="market-tags">
          <div class="tag-item">Over 2.5: <strong>${escapeHtml(f.markets.over_25)}%</strong></div>
          <div class="tag-item">BTTS: <strong>${escapeHtml(f.markets.btts_yes)}%</strong></div>
          <div class="tag-item">xG: <strong>${escapeHtml(f.home.xg)} - ${escapeHtml(f.away.xg)}</strong></div>
        </div>

        <div style="text-align:center; font-size:0.75rem; color:var(--accent-cyan); margin-top:10px;">
          🧪 انقر لعرض تقرير الرادار ومؤشر التكافؤ ومختبر السيناريوهات
        </div>
      </div>
    `;
  }).join('');
  if (typeof window.refreshFavoriteStarsAndSorting === 'function') window.refreshFavoriteStarsAndSorting();
}

async function loadGameweek(leagueCode, forceRefresh = false) {
  const container = document.getElementById('fixtures-container');
  if (!container) return;
  const reqToken = ++window._viewReqToken;
  const cacheKey = `gw_${leagueCode}`;

  if (
    !forceRefresh &&
    typeof BROWSER_CACHE !== 'undefined' &&
    BROWSER_CACHE.fixtures &&
    BROWSER_CACHE.fixtures[leagueCode] &&
    BROWSER_CACHE.fixtures[leagueCode].length > 0 &&
    typeof isBrowserCacheFresh === 'function' &&
    isBrowserCacheFresh(cacheKey)
  ) {
    window.currentFixtures = BROWSER_CACHE.fixtures[leagueCode];
    renderFixturesList(window.currentFixtures);
    return;
  }

  container.innerHTML = renderSkeletonCardsHtml(6);

  try {
    const res = await fetch(`/api/gameweek/${leagueCode}?refresh=${forceRefresh}`);
    const data = await res.json();
    if (reqToken !== window._viewReqToken) return;
    window.currentFixtures = data.fixtures || [];
    if (typeof BROWSER_CACHE !== 'undefined' && window.currentFixtures.length > 0) {
      BROWSER_CACHE.fixtures[leagueCode] = window.currentFixtures;
      if (typeof touchBrowserCache === 'function') touchBrowserCache(cacheKey);
    }
    renderFixturesList(window.currentFixtures);
  } catch (e) {
    container.innerHTML = `
      <div class="loading-state">
        <div>تأخر الاتصال بالسيرفر، يرجى المحاولة مرة أخرى.</div>
        <button class="retry-btn" onclick="refreshCurrentView()">إعادة المحاولة فوراً ↻</button>
      </div>
    `;
  }
}

// =========================================================
// 3. مركز المباريات المباشر (الشاشة الرئيسية المطورة - Phase 2)
// =========================================================
window._todayStatusFilter = 'ALL';
window._todayLeagueFilter = 'ALL';
window._todaySelectedDateKey = 'today'; // 'today' | 'YYYY-MM-DD'
window._collapsedLeagueGroups = {};

function computeIsoDateOffset(daysOffset) {
  const d = new Date();
  d.setDate(d.getDate() + daysOffset);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function renderWeekDateStrip() {
  const strip = document.getElementById('dp-date-strip');
  if (!strip) return;

  const todayIso = computeIsoDateOffset(0);
  const activeKey = window._todaySelectedDateKey === 'today'
    ? todayIso
    : (window._todaySelectedDateKey === 'yesterday'
      ? computeIsoDateOffset(-1)
      : (window._todaySelectedDateKey === 'tomorrow'
        ? computeIsoDateOffset(1)
        : window._todaySelectedDateKey));

  const offsets = [-3, -2, -1, 0, 1, 2, 3];
  const dayNames = ['أحد', 'إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت'];
  let matchedInStrip = false;

  strip.innerHTML = offsets.map(off => {
    const dt = new Date();
    dt.setDate(dt.getDate() + off);
    const iso = computeIsoDateOffset(off);
    const isActive = (iso === activeKey);
    if (isActive) matchedInStrip = true;

    let label = dayNames[dt.getDay()];
    if (off === -1) label = 'أمس';
    else if (off === 0) label = 'اليوم';
    else if (off === 1) label = 'غداً';

    const dayNum = dt.getDate();
    const keyParam = (off === 0) ? 'today' : iso;

    return `
      <button type="button" class="dp-week-day-btn ${isActive ? 'active' : ''} ${off === 0 ? 'is-today' : ''}" data-iso="${iso}" onclick="selectMatchCenterDate('${keyParam}')">
        <span class="dp-wd-name">${label}</span>
        <span class="dp-wd-num">${dayNum}</span>
      </button>
    `;
  }).join('');

  const calBtn = document.getElementById('dp-cal-trigger-btn');
  if (calBtn) calBtn.classList.toggle('is-active', !matchedInStrip);

  const activeBtn = strip.querySelector('.dp-week-day-btn.active');
  if (activeBtn && typeof activeBtn.scrollIntoView === 'function') {
    try { activeBtn.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' }); } catch (e) {}
  }
}

window.selectMatchCenterDate = function(dayKey) {
  if (!dayKey) return;
  const todayIso = computeIsoDateOffset(0);
  if (dayKey === todayIso) dayKey = 'today';
  else if (dayKey === 'yesterday') dayKey = computeIsoDateOffset(-1);
  else if (dayKey === 'tomorrow') dayKey = computeIsoDateOffset(1);

  window._todaySelectedDateKey = dayKey;
  window._todayStatusFilter = 'ALL';
  window._todayLeagueFilter = 'ALL';

  const calInput = document.getElementById('dp-custom-date-input');
  if (calInput) calInput.value = (dayKey === 'today') ? todayIso : dayKey;

  renderWeekDateStrip();
  loadTodayMatches(true);
};

window.setTodayStatusFilter = function(filterKey) {
  window._todayStatusFilter = filterKey;
  renderTodayMatchesGrouped(window.currentTodayMatches || []);
};

window.setTodayLeagueFilter = function(leagueCode) {
  window._todayLeagueFilter = leagueCode;
  renderTodayMatchesGrouped(window.currentTodayMatches || []);
};

window.toggleLeagueAccordion = function(groupKey) {
  window._collapsedLeagueGroups[groupKey] = !window._collapsedLeagueGroups[groupKey];
  const card = document.querySelector(`.dp-league-card[data-group-key="${CSS.escape(groupKey)}"]`);
  if (card) card.classList.toggle('is-collapsed', Boolean(window._collapsedLeagueGroups[groupKey]));
};

function renderMatchRowHtml(m, origIdx) {
  const isHomeFav = typeof window.isClubFavoritePublic === 'function' && window.isClubFavoritePublic(m.home_team);
  const isAwayFav = typeof window.isClubFavoritePublic === 'function' && window.isClubFavoritePublic(m.away_team);
  const pillCls = m.is_live ? 'is-live' : (m.state === 'pre' ? 'is-pre' : '');
  const scoreContent = m.state === 'pre'
    ? formatLocalKickoff(m.kickoff_iso, m.kickoff_time, true)
    : `${escapeHtml(m.home_score)} - ${escapeHtml(m.away_score)}`;

  const showBcastSub = m.channel_verified || m.commentator_verified;

  return `
    <div class="dp-match-row ${m.is_live ? 'is-live' : ''}" data-match-id="${escapeHtml(m.id)}" onclick="openTodayMatchModal(${origIdx})">
      <div class="dp-row-side home">
        <button type="button" class="dp-fav-star-btn dp-row-fav ${isHomeFav ? 'is-fav' : ''}" data-club="${escapeHtml(m.home_team)}" onclick="window.toggleFavoriteClub(this.dataset.club, event)" title="إضافة ${escapeHtml(m.home_team)} للمفضلة">${isHomeFav ? '★' : '☆'}</button>
        <span class="dp-row-team-name">${escapeHtml(m.home_team)}</span>
        <img src="${escapeHtml(m.home_crest)}" alt="" loading="lazy" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
      </div>

      <div class="dp-row-center">
        <div class="dp-row-score-pill ${pillCls}">${scoreContent}</div>
        <div class="dp-row-status ${m.is_live ? 'is-live' : ''}">${escapeHtml(m.status_text)}</div>
      </div>

      <div class="dp-row-side away">
        <img src="${escapeHtml(m.away_crest)}" alt="" loading="lazy" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
        <span class="dp-row-team-name">${escapeHtml(m.away_team)}</span>
        <button type="button" class="dp-fav-star-btn dp-row-fav ${isAwayFav ? 'is-fav' : ''}" data-club="${escapeHtml(m.away_team)}" onclick="window.toggleFavoriteClub(this.dataset.club, event)" title="إضافة ${escapeHtml(m.away_team)} للمفضلة">${isAwayFav ? '★' : '☆'}</button>
      </div>

      ${showBcastSub ? `
        <div class="dp-row-bcast-sub">
          ${m.channel_verified ? `<span>${escapeHtml(m.channel)}</span>` : ''}
          ${m.channel_verified && m.commentator_verified ? `<span>•</span>` : ''}
          ${m.commentator_verified ? `<span class="dp-bcast-comm">${escapeHtml(m.commentator)}</span>` : ''}
        </div>
      ` : ''}
    </div>
  `;
}

function renderTodayMatchesGrouped(matches) {
  const container = document.getElementById('today-matches-container');
  const filtersBox = document.getElementById('today-filters-bar');
  if (!container) return;

  if (!matches || matches.length === 0) {
    if (filtersBox) filtersBox.innerHTML = '';
    container.innerHTML = `
      <div class="dp-empty-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--muted)" stroke-width="1.6" width="38" height="38"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
        <div style="font-weight:800; color:var(--text); font-size:0.96rem;">لا توجد مباريات مجدولة في هذا التاريخ</div>
        <div style="font-size:0.8rem; color:var(--muted);">جرّب اختيار يوم آخر من التقويم بالأعلى أو استعرض توقعات الجولة القادمة.</div>
        <div style="display:flex; gap:8px; flex-wrap:wrap; justify-content:center; margin-top:6px;">
          <button type="button" class="retry-btn" onclick="selectMatchCenterDate('tomorrow')">مباريات غداً</button>
          <button type="button" class="ai-btn" onclick="navigateToPillar('competitions')">توقعات الجولة القادمة</button>
        </div>
      </div>
    `;
    loadHomeQuietHighlightsStrip();
    return;
  }

  const indexed = matches.map((m, idx) => ({ m, idx }));
  const liveCount = indexed.filter(x => x.m.is_live).length;
  const preCount = indexed.filter(x => x.m.state === 'pre').length;
  const postCount = indexed.filter(x => x.m.state === 'post').length;
  const favItems = indexed.filter(x =>
    typeof window.isClubFavoritePublic === 'function' &&
    (window.isClubFavoritePublic(x.m.home_team) || window.isClubFavoritePublic(x.m.away_team))
  );

  const leagueMap = new Map();
  indexed.forEach(x => {
    const code = x.m.league_code || 'OTHER';
    if (!leagueMap.has(code)) {
      leagueMap.set(code, { code, name: x.m.league_name, flag: x.m.league_flag || '', count: 0 });
    }
    leagueMap.get(code).count += 1;
  });
  const uniqueLeagues = Array.from(leagueMap.values());

  const curStatus = window._todayStatusFilter || 'ALL';
  const curLg = window._todayLeagueFilter || 'ALL';

  const statusPills = [
    { key: 'ALL', label: `الكل (${indexed.length})` },
    { key: 'LIVE', label: `مباشر (${liveCount})` },
    { key: 'PRE', label: `قادمة (${preCount})` },
    { key: 'POST', label: `انتهت (${postCount})` }
  ];
  if (favItems.length > 0) statusPills.splice(1, 0, { key: 'FAV', label: `★ المفضلة (${favItems.length})` });

  if (filtersBox) {
    filtersBox.innerHTML = `
      <div class="dp-mc-filter-bar">
        <div class="dp-filter-pills">
          ${statusPills.map(p => `
            <button type="button" class="dp-filter-pill ${curStatus === p.key ? 'active' : ''} ${p.key === 'LIVE' && liveCount > 0 ? 'has-live' : ''}" onclick="setTodayStatusFilter('${p.key}')">
              ${p.key === 'LIVE' && liveCount > 0 ? '<span class="live-dot-pulse"></span>' : ''}
              <span>${p.label}</span>
            </button>
          `).join('')}
        </div>
        ${uniqueLeagues.length > 1 ? `
          <select class="dp-league-select" aria-label="تصفية حسب البطولة" onchange="setTodayLeagueFilter(this.value)">
            <option value="ALL" ${curLg === 'ALL' ? 'selected' : ''}>كل البطولات (${uniqueLeagues.length})</option>
            ${uniqueLeagues.map(lg => `
              <option value="${escapeHtml(lg.code)}" ${curLg === lg.code ? 'selected' : ''}>${escapeHtml(lg.flag)} ${escapeHtml(lg.name)} (${lg.count})</option>
            `).join('')}
          </select>
        ` : ''}
      </div>
    `;
  }

  let filtered = indexed;
  if (curStatus === 'LIVE') filtered = filtered.filter(x => x.m.is_live);
  else if (curStatus === 'PRE') filtered = filtered.filter(x => x.m.state === 'pre');
  else if (curStatus === 'POST') filtered = filtered.filter(x => x.m.state === 'post');
  else if (curStatus === 'FAV') filtered = favItems;

  if (curLg !== 'ALL') {
    filtered = filtered.filter(x => x.m.league_code === curLg);
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="dp-empty-state">
        <div>لا توجد مباريات مطابقة لهذا الفلتر حالياً.</div>
        <button type="button" class="retry-btn" onclick="window._todayLeagueFilter='ALL'; setTodayStatusFilter('ALL');">إعادة ضبط الفلاتر</button>
      </div>
    `;
    return;
  }

  let groupsHtml = '';
  const shownFavIds = new Set();

  if (curStatus === 'ALL' && curLg === 'ALL' && favItems.length > 0) {
    favItems.forEach(x => shownFavIds.add(x.m.id));
    const favCollapsed = Boolean(window._collapsedLeagueGroups['FAV_GRP']);
    groupsHtml += `
      <div class="dp-league-card is-fav-group ${favCollapsed ? 'is-collapsed' : ''}" data-group-key="FAV_GRP">
        <div class="dp-league-card-hdr" onclick="toggleLeagueAccordion('FAV_GRP')">
          <div class="dp-league-hdr-right">
            <span style="color:var(--accent-gold-bright);">★</span>
            <span>مباريات أنديتك المفضلة</span>
          </div>
          <div class="dp-league-hdr-left">
            <span class="hub-badge">${favItems.length}</span>
            <svg class="dp-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>
        <div class="dp-league-rows">
          ${favItems.map(x => renderMatchRowHtml(x.m, x.idx)).join('')}
        </div>
      </div>
    `;
  }

  const byLeague = new Map();
  filtered.forEach(item => {
    if (curStatus === 'ALL' && curLg === 'ALL' && shownFavIds.has(item.m.id)) return;
    const key = item.m.league_name || 'بطولات أخرى';
    if (!byLeague.has(key)) {
      byLeague.set(key, {
        code: item.m.league_code || '',
        logo: item.m.league_logo || '',
        flag: item.m.league_flag || '',
        name: key,
        items: []
      });
    }
    byLeague.get(key).items.push(item);
  });

  byLeague.forEach((grp, gKey) => {
    const liveInGrp = grp.items.filter(x => x.m.is_live).length;
    const isCollapsed = Boolean(window._collapsedLeagueGroups[gKey]);
    groupsHtml += `
      <div class="dp-league-card ${isCollapsed ? 'is-collapsed' : ''}" data-group-key="${escapeHtml(gKey)}">
        <div class="dp-league-card-hdr" onclick="toggleLeagueAccordion(this.closest('.dp-league-card').dataset.groupKey)">
          <div class="dp-league-hdr-right">
            ${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(grp.code, grp.flag, 'size-sm', grp.logo) : `<span>${escapeHtml(grp.flag)}</span>`}
            <span>${escapeHtml(grp.name)}</span>
          </div>
          <div class="dp-league-hdr-left">
            ${liveInGrp > 0 ? `<span class="live-badge" style="padding:2px 8px; font-size:0.66rem;"><span class="live-dot-pulse"></span> ${liveInGrp} مباشر</span>` : ''}
            <span class="hub-badge">${grp.items.length}</span>
            <svg class="dp-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg>
          </div>
        </div>
        <div class="dp-league-rows">
          ${grp.items.map(x => renderMatchRowHtml(x.m, x.idx)).join('')}
        </div>
      </div>
    `;
  });

  container.innerHTML = groupsHtml;
  loadHomeQuietHighlightsStrip();
}

window._sidebarNewsItems = [];

async function loadHomeQuietHighlightsStrip(forceReload = false) {
  const strip = document.getElementById('today-highlights-strip');
  if (!strip || (!forceReload && strip.dataset.loaded === '1')) return;
  strip.dataset.loaded = '1';

  try {
    const res = await fetch('/api/news');
    const data = await res.json();
    const newsList = (data && data.news) ? data.news.slice(0, 5) : [];
    if (newsList.length === 0) return;
    window._sidebarNewsItems = newsList;

    strip.innerHTML = `
      <div class="dp-side-card">
        <div class="dp-side-card-hdr">
          <span>أحدث الأخبار الرياضية</span>
          <button type="button" class="dp-side-link-btn" onclick="activateSection('news')">عرض الكل ↗</button>
        </div>
        <div class="dp-side-news-list">
          ${newsList.map((n, idx) => `
            <div class="dp-side-news-item" onclick="openNewsArticleByObj(window._sidebarNewsItems[${idx}])">
              ${n.image_url
                ? `<img src="${escapeHtml(n.image_url)}" alt="" class="dp-side-news-thumb" loading="lazy" onerror="this.onerror=null; this.style.display='none';">`
                : `<div class="dp-side-news-thumb is-fallback"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/></svg></div>`
              }
              <div class="dp-side-news-body">
                <div class="dp-side-news-title">${escapeHtml(n.title)}</div>
                <div class="dp-side-news-time">${escapeHtml(n.published_time || 'تحديث مباشر')}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (e) {}
}

async function loadTodayMatches(showSkeleton = false) {
  const container = document.getElementById('today-matches-container');
  const dateTxt = document.getElementById('today-date-txt');
  if (!container) return;

  renderWeekDateStrip();

  const todayIso = computeIsoDateOffset(0);
  const dayKey = window._todaySelectedDateKey || 'today';
  let queryDate = '';
  let labelDateObj = new Date();

  if (dayKey !== 'today' && dayKey !== todayIso) {
    queryDate = dayKey;
    const parsed = new Date(dayKey + 'T12:00:00');
    if (!isNaN(parsed.getTime())) labelDateObj = parsed;
  }

  if (dateTxt) {
    dateTxt.innerText = labelDateObj.toLocaleDateString('ar-EG', { weekday: 'long', day: 'numeric', month: 'long' });
  }

  if (showSkeleton || !window.currentTodayMatches || window.currentTodayMatches.length === 0) {
    container.innerHTML = renderSkeletonCardsHtml(4);
  }

  try {
    const endpoint = queryDate ? `/api/todays_matches?date=${encodeURIComponent(queryDate)}` : '/api/todays_matches';
    const res = await fetch(endpoint);
    const data = await res.json();
    const matches = data.matches || [];
    window.currentTodayMatches = matches;

    if (!queryDate && typeof window.checkLiveScoreNotifications === 'function') {
      window.checkLiveScoreNotifications(matches);
    }

    renderTodayMatchesGrouped(matches);

    if (queryDate) {
      if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) clearTimeout(todayPollingTimeout);
      const statusTxt = document.getElementById('polling-status-txt');
      if (statusTxt) statusTxt.innerText = `جدول ${queryDate}`;
      return;
    }

    if (matches.length === 0) {
      scheduleNextPoll(300000, 'لا توجد مباريات اليوم');
      return;
    }

    const hasLiveMatch = matches.some(m => m.is_live);
    scheduleNextPoll(
      hasLiveMatch ? 35000 : 300000,
      hasLiveMatch ? 'مباشر • تحديث كل 35ث' : 'تحديث تلقائي كل 5د'
    );
  } catch (e) {
    scheduleNextPoll(60000, 'تعذر التحديث - إعادة المحاولة');
  }
}

function scheduleNextPoll(delayMs, statusMessage) {
  const statusTxt = document.getElementById('polling-status-txt');
  if (statusTxt) statusTxt.innerText = statusMessage;
  if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) clearTimeout(todayPollingTimeout);
  if (window.activeSection === 'today' && (window._todaySelectedDateKey || 'today') === 'today') {
    todayPollingTimeout = setTimeout(() => loadTodayMatches(false), delayMs);
  }
}
// 4. جدول الترتيب الرسمي والهدافين (مع الفواصل البصرية وفلترة المستويات/المجموعات)
// =========================================================
window._cachedStandingsData = [];
window._activeGroupFilter = 'ALL';

function getGroupRuleSubtitle(leagueCode, groupName, levelCode) {
  const code = (leagueCode || '').toUpperCase();
  if (code === 'UNL') {
    if (levelCode === 'A') return 'الأول والثاني: ربع النهائي 🏆 • الثالث: ملحق البقاء 🔄 • الرابع: هبوط للمستوى B 🔻';
    if (levelCode === 'B') return 'الأول: صعود لـ A ⬆️ • الثاني: ملحق صعود ⬆️ • الثالث: ملحق بقاء 🔄 • الرابع: هبوط لـ C 🔻';
    if (levelCode === 'C') return 'الأول: صعود لـ B ⬆️ • الثاني: ملحق صعود ⬆️ • الثالث: بقاء • الرابع: هبوط/ملحق D 🔻';
    return 'الأول: صعود للمستوى C ⬆️ • الثاني: ملحق صعود لـ C ⬆️ • الثالث: بقاء';
  }
  if (code === 'ACL') return 'المراكز 1–8: تأهل مباشر لثمن النهائي 🌏 • المراكز 9–12: إقصاء مباشر بدون ملحق ❌';
  if (code === 'CAF') return 'الأول والثاني: تأهل مباشر لربع النهائي 🌍 • الثالث والرابع: إقصاء مباشر ❌';
  return '';
}

function buildGroupFilterTabsHtml(items, leagueCode, onClickFnName) {
  const code = (leagueCode || '').toUpperCase();
  if (!['UNL', 'ACL', 'CAF'].includes(code)) return '';

  let tabs = [{ key: 'ALL', label: 'الكل' }];
  if (code === 'UNL') {
    tabs.push(
      { key: 'LVL_A', label: 'المستوى A' },
      { key: 'LVL_B', label: 'المستوى B' },
      { key: 'LVL_C', label: 'المستوى C' },
      { key: 'LVL_D', label: 'المستوى D' }
    );
  } else {
    const seenGroups = [];
    items.forEach(t => {
      if (t.group_name && !seenGroups.includes(t.group_name)) seenGroups.push(t.group_name);
    });
    seenGroups.forEach(g => tabs.push({ key: g, label: g }));
  }

  return `
    <div class="dp-h-scroll-bar" style="margin-bottom:12px;">
      ${tabs.map(tb => `
        <button type="button" class="q-chip-item ${window._activeGroupFilter === tb.key ? 'active' : ''}" onclick="${onClickFnName}('${escapeHtml(tb.key)}')">
          ${escapeHtml(tb.label)}
        </button>
      `).join('')}
    </div>
  `;
}

function filterStandingsByGroup(filterKey) {
  window._activeGroupFilter = filterKey;
  const leagueCode = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  renderStandingsTableRows(window._cachedStandingsData, leagueCode);
}

function renderStandingsTableRows(standings, leagueCode) {
  const tbody = document.getElementById('official-standings-tbody') || document.getElementById('standings-tbody');
  if (!tbody) return;

  const rules = getLeagueRulesConfig(leagueCode);
  const totalTeams = standings.length;

  // حقن شريط فلترة المستويات/المجموعات أعلى الجدول
  let filterWrap = document.getElementById('standings-group-filter-bar');
  if (!filterWrap && tbody.closest('.data-card')) {
    filterWrap = document.createElement('div');
    filterWrap.id = 'standings-group-filter-bar';
    const tblCont = tbody.closest('.table-container');
    tbody.closest('.data-card').insertBefore(filterWrap, tblCont);
  }
  if (filterWrap) {
    filterWrap.innerHTML = buildGroupFilterTabsHtml(standings, leagueCode, 'filterStandingsByGroup');
  }

  const filtered = standings.filter(t => {
    if (window._activeGroupFilter === 'ALL') return true;
    if (window._activeGroupFilter.startsWith('LVL_')) {
      return t.level_code === window._activeGroupFilter.replace('LVL_', '');
    }
    return t.group_name === window._activeGroupFilter;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" class="loading-state">لا تتوفر بيانات ترتيب حالياً لهذا الاختيار.</td></tr>';
    return;
  }

  let lastGroup = null;
  const rowsHtml = [];

  filtered.forEach(t => {
    // إدراج فاصل بصري أنيق عند بداية كل مجموعة أو منطقة أو مستوى
    if (t.group_name && t.group_name !== lastGroup) {
      lastGroup = t.group_name;
      const ruleSub = getGroupRuleSubtitle(leagueCode, t.group_name, t.level_code);
    rowsHtml.push(`
        <tr class="group-divider-row">
          <td colspan="10" class="dp-group-divider-cell">
            <div class="dp-group-divider-wrap">
              <span class="dp-group-divider-title">${escapeHtml(t.group_name)}</span>
              ${ruleSub ? `<span class="dp-group-divider-sub">${escapeHtml(ruleSub)}</span>` : ''}
            </div>
          </td>
        </tr>
      `);
    }

    let zoneClass = "";
    const codeUpper = (leagueCode || 'PL').toUpperCase();
    const isContinental = ['UCL', 'ACL', 'CAF', 'UNL'].includes(codeUpper);

    if (isContinental && t.zone && t.zone !== "safe") {
      if (t.zone === "qualify") zoneClass = "rank-ucl";
      else if (t.zone === "playoff") zoneClass = "rank-uel";
      else if (t.zone === "eliminated") zoneClass = "rank-rel";
    } else if (rules.isUclFormat) {
      if (t.rank <= 8) zoneClass = "rank-ucl";
      else if (t.rank <= 24) zoneClass = "rank-uel";
      else zoneClass = "rank-rel";
    } else if (!isContinental) {
      // الدوريات المحلية: تحديد الفئة اللونية فقط (أخضر/سماوي، أصفر، أحمر) بدون كتابة نص
      const isRelegationRank = rules.relRanks.includes(t.rank) || (totalTeams >= 16 && t.rank > totalTeams - rules.relRanks.length);
      if (rules.uclRanks.includes(t.rank)) {
        zoneClass = "rank-ucl";
      } else if (rules.uelRanks.includes(t.rank)) {
        zoneClass = "rank-uel";
      } else if (isRelegationRank) {
        zoneClass = "rank-rel";
      }
    }

    // شارة لونية صامتة (نقطة مضيئة أنيقة بدون أي كلام) بجانب اسم النادي
  // الحد اللوني بجانب رقم المركز يكفي بصرياً دون تكرار النقطة
    let statusBadge = "";

    rowsHtml.push(`
      <tr>
        <td class="${zoneClass}"><strong>${t.rank}</strong></td>
       <td class="team-col-cell">
          <div style="display:flex; align-items:center; gap:6px;">
            <span style="display:inline-flex; align-items:center; gap:6px; cursor:pointer;"
              data-lg="${escapeHtml(leagueCode)}"
              data-tid="${escapeHtml(t.team_id || '')}"
              data-raw="${escapeHtml(t.team_name || t.short_name)}"
              data-ar="${escapeHtml(t.short_name || t.team_name)}"
              data-crest="${escapeHtml(t.crest || '')}"
              data-rank="${escapeHtml(t.rank)}"
              onclick="openDirectSearchClub(this.dataset.lg, this.dataset.tid, this.dataset.raw, this.dataset.ar, this.dataset.crest, this.dataset.rank)"
              title="اضغط لعرض ملف النادي وألقابه وآخر 5 نتائج">
              <img src="${escapeHtml(t.crest)}" width="20" height="20" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
              <strong class="team-title-sm">${escapeHtml(t.short_name || t.team_name)}</strong>
            </span>
            ${statusBadge}
          </div>
        </td>
      <td>${t.played}</td>
        <td>${t.won}</td>
        <td>${t.drawn}</td>
        <td>${t.lost}</td>
        <td>${t.gf}:${t.ga}</td>
        <td style="color:${t.gd > 0 ? 'var(--accent-green)' : t.gd < 0 ? 'var(--accent-red)' : 'var(--muted)'}">
          ${t.gd > 0 ? '+' : ''}${t.gd}
        </td>
        <td style="font-weight:900; color:var(--accent-gold); font-size:1.05rem;">${t.points}</td>
        <td>
          <div style="display:flex; gap:3px;">
            ${(t.form || []).map(f => `<span class="badge-f form-${escapeHtml(f).toLowerCase()}">${escapeHtml(f)}</span>`).join('')}
          </div>
        </td>
      </tr>
    `);
  });

 tbody.innerHTML = rowsHtml.join('');
  if (typeof window.refreshFavoriteStarsAndSorting === 'function') window.refreshFavoriteStarsAndSorting();
}
window.switchStandingsMobileTab = function(tab) {
  const view = document.getElementById('standings-view');
  if (view) view.classList.toggle('is-mobile-scorers', tab === 'scorers');
  document.querySelectorAll('#standings-mobile-switch .dp-subtab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-smob') === tab);
  });
};  

async function loadOfficialStandingsAndScorers(leagueCode, forceRefresh = false) {
  const reqToken = ++window._viewReqToken;
  const tbody = document.getElementById('official-standings-tbody') || document.getElementById('standings-tbody');
  const scorersList = document.getElementById('top-scorers-list') || document.getElementById('scorers-tbody');
  const rules = getLeagueRulesConfig(leagueCode);
  window._activeGroupFilter = 'ALL';

  const legendBox = document.querySelector('#standings-view .legend-badges');
  if (legendBox) {
    legendBox.innerHTML = `
      <span><span style="color:var(--accent-cyan)">■</span> ${rules.legend.ucl}</span>
      ${rules.legend.uel ? `<span><span style="color:var(--accent-gold)">■</span> ${rules.legend.uel}</span>` : ''}
      <span><span style="color:var(--accent-red)">■</span> ${rules.legend.rel}</span>
    `;
  }

  if (tbody) {
    tbody.innerHTML = '<tr><td colspan="10" class="loading-state">جاري سحب الترتيب الرسمي المباشر من الـ API...</td></tr>';
  }
  if (scorersList) {
    scorersList.innerHTML = '<div class="loading-state">جاري سحب قائمة الهدافين...</div>';
  }

  try {
    const [sRes, scRes] = await Promise.all([
      fetch(`/api/official_standings/${leagueCode}?refresh=${forceRefresh}`),
      fetch(`/api/top_scorers/${leagueCode}?refresh=${forceRefresh}`)
    ]);

    const sData = await sRes.json();
    const scData = await scRes.json();
    if (reqToken !== window._viewReqToken) return;

    const standings = sData.standings || (Array.isArray(sData) ? sData : []);
    const scorers = scData.scorers || (Array.isArray(scData) ? scData : []);

    window._cachedStandingsData = standings;
    window._cachedStandingsLeague = leagueCode;
    renderStandingsTableRows(standings, leagueCode);

    if (scorersList) {
      if (scorers.length === 0) {
        scorersList.innerHTML = '<div class="loading-state">لا توجد إحصائيات هدافين مسجلة حالياً.</div>';
      } else {
        scorersList.innerHTML = scorers.map(s => {
          let rankBadgeClass = s.rank === 1 ? 'rank-1' : s.rank === 2 ? 'rank-2' : s.rank === 3 ? 'rank-3' : '';
          let avatarHtml = s.headshot
            ? `<img src="${escapeHtml(s.headshot)}" width="34" height="34" style="border-radius:50%; object-fit:cover; background:var(--surface-inset); border:1px solid var(--card-border);" onerror="this.onerror=null; this.style.display='none';">`
            : '';

          return `
            <div class="scorer-row">
              <div style="display:flex; align-items:center; gap:10px;">
                <div class="scorer-rank ${rankBadgeClass}">${escapeHtml(s.rank)}</div>
                ${avatarHtml}
                <div>
                  <div style="font-weight:800; font-size:0.9rem;">${escapeHtml(s.name)}</div>
                  <div style="font-size:0.75rem; color:var(--muted); display:flex; align-items:center; gap:5px;">
                    <img src="${escapeHtml(s.crest)}" width="14" height="14" onerror="this.onerror=null; this.style.display='none';">
                    <span>${escapeHtml(s.team)}</span>
                  </div>
                </div>
              </div>
              <div style="font-size:1.2rem; font-weight:900; color:var(--accent-gold);">
                ${escapeHtml(s.goals)} <span style="font-size:0.75rem; color:var(--muted); font-weight:400;">أهداف</span>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (e) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="10" class="loading-state" style="color:var(--accent-red);">تعذر جلب بيانات الترتيب.</td></tr>';
  }
}

// =========================================================
// 5. محاكي نهاية الموسم (Monte Carlo) مع الفواصل البصرية للمجموعات والمستويات
// =========================================================
window._cachedProjData = [];

function filterProjectionsByGroup(filterKey) {
  window._activeGroupFilter = filterKey;
  const leagueCode = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  renderProjectionsTableRows(window._cachedProjData, leagueCode);
}

function renderProjectionsTableRows(dataList, leagueCode) {
  const tbody = document.getElementById('projections-tbody');
  if (!tbody) return;
  const rules = getLeagueRulesConfig(leagueCode);

let filterWrap = document.getElementById('proj-group-filter-bar');
  const parentCard = tbody.closest('.data-card');
  const tblCont = tbody.closest('.table-container') || tbody.closest('table');
  if (!filterWrap && parentCard && tblCont && tblCont.parentElement === parentCard) {
    filterWrap = document.createElement('div');
    filterWrap.id = 'proj-group-filter-bar';
    parentCard.insertBefore(filterWrap, tblCont);
  }
  if (filterWrap) {
    filterWrap.innerHTML = buildGroupFilterTabsHtml(dataList, leagueCode, 'filterProjectionsByGroup');
  }

  const filtered = dataList.filter(t => {
    if (window._activeGroupFilter === 'ALL') return true;
    if (window._activeGroupFilter.startsWith('LVL_')) {
      return t.level_code === window._activeGroupFilter.replace('LVL_', '');
    }
    return t.group_name === window._activeGroupFilter;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:25px; color:var(--muted);">لا توجد بيانات متاحة لهذا الاختيار.</td></tr>';
    return;
  }

  let lastGroup = null;
  const rowsHtml = [];

  filtered.forEach((row, idx) => {
    if (row.group_name && row.group_name !== lastGroup) {
      lastGroup = row.group_name;
      const ruleSub = getGroupRuleSubtitle(leagueCode, row.group_name, row.level_code);
     rowsHtml.push(`
        <tr class="group-divider-row">
          <td colspan="8" class="dp-group-divider-cell">
            <div class="dp-group-divider-wrap">
              <span class="dp-group-divider-title">${escapeHtml(row.group_name)}</span>
              ${ruleSub ? `<span class="dp-group-divider-sub">${escapeHtml(ruleSub)}</span>` : ''}
            </div>
          </td>
        </tr>
      `);
    }

    const rankNum = row.group_rank || (idx + 1);
    let rankClass = "";
    if (row.zone === "qualify" || (!row.group_name && rules.uclRanks.includes(rankNum))) rankClass = "rank-ucl";
    else if (row.zone === "playoff" || (!row.group_name && rules.uelRanks.includes(rankNum))) rankClass = "rank-uel";
    else if (row.zone === "eliminated" || (!row.group_name && rules.relRanks.includes(rankNum))) rankClass = "rank-rel";

    rowsHtml.push(`
      <tr>
        <td class="${rankClass}" style="font-weight:900; color:var(--accent-gold);">#${rankNum}</td>
        <td>
          <div style="display:flex; align-items:center; gap:6px;">
            <img src="${escapeHtml(row.crest)}" width="20" height="20" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
            <strong>${escapeHtml(row.name)}</strong>
          </div>
        </td>
     <td>${row.played}</td>
        <td style="font-weight:800; color:var(--text);">${row.current_pts}</td>
        <td style="font-weight:900; font-size:1.02rem; color:var(--accent-green);">${row.projected_pts}</td>
        <td>
          ${row.champ_pct > 0.1 
            ? `<span class="prob-pill prob-champ">${row.champ_pct}%</span>` 
            : `<span style="color:var(--muted); font-size:0.8rem;">-</span>`}
        </td>
        <td>
          ${row.top4_pct > 0.5 
            ? `<span class="prob-pill prob-top4">${row.top4_pct}%</span>` 
            : `<span style="color:var(--muted); font-size:0.8rem;">-</span>`}
        </td>
        <td>
          ${row.rel_pct > 0.5 
            ? `<span class="prob-pill prob-rel">${row.rel_pct}%</span>` 
            : `<span style="color:var(--muted); font-size:0.8rem;">-</span>`}
        </td>
      </tr>
    `);
  });

  tbody.innerHTML = rowsHtml.join('');
}

async function loadProjections(leagueCode, forceRefresh = false) {
  const tbody = document.getElementById('projections-tbody');
  if (!tbody) return;
  const reqToken = ++window._viewReqToken;
  

  const rules = getLeagueRulesConfig(leagueCode);
  window._activeGroupFilter = 'ALL';

  const noteCard = document.querySelector('#projections-view .info-note-card');
  if (noteCard) noteCard.innerHTML = rules.projHeaders.note;

  const ths = document.querySelectorAll('#projections-view thead th');
  if (ths && ths.length >= 8) {
    ths[5].innerText = rules.projHeaders.champ;
    ths[6].innerText = rules.projHeaders.top;
    ths[7].innerText = rules.projHeaders.rel;
  }

  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:35px; color:var(--muted);">جاري تشغيل محاكي مونت كارلو ومحاكاة 1,500 موسم افتراضي...</td></tr>';

try {
    const res = await fetch(`/api/season_projections/${leagueCode}?refresh=${forceRefresh}`);
    const data = await res.json();
    if (reqToken !== window._viewReqToken) return;
    let dataList = data.projections || [];

    window._cachedProjData = dataList;
    renderProjectionsTableRows(dataList, leagueCode);
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--accent-red);">فشل جلب بيانات المحاكاة، يرجى المحاولة لاحقاً.</td></tr>';
  }
}



// =========================================================
// 6. محرك مركز البطاقات الشامل (100% Live API: Clubs, Top 100 Nations & Players)
// =========================================================
// =========================================================
// 6. محرك مركز البطاقات التفاعلي الشامل (100% Live API)
//    1) المنتخبات (5 قارات ⬅️ منتخبات القارة ⬅️ صندوق الألقاب والأساطير)
//    2) الأندية (الدوري ⬅️ أندية الدوري ⬅️ صندوق البطولات والأساطير)
//    3) اللاعبون بنظام FIFA Cards (الدوري ⬅️ الـ 20 نادياً ⬅️ لاعبو النادي ⬅️ بطاقة اللاعب)
// =========================================================

window._cardsHubState = {
  subPortal: 'nations',        // 'nations' | 'clubs' | 'players'
  selectedContinent: 'europe', // 'europe' | 'asia' | 'africa' | 'south_america' | 'north_america'
  clubLeague: 'PD',
  playerLeague: 'PD',
  selectedClubId: '',          // إذا كان فارغاً في قسم اللاعبين نعرض شبكة الـ 20 نادياً للاختيار
  selectedClubName: '',
  selectedClubCrest: '',
  searchQuery: '',
  nationsData: [],
  clubsData: [],
  playerClubsList: [],
  squadPlayersData: [],
  _reqToken: 0,
  _filteredNations: [],
  _filteredClubs: [],
  _filteredPlayerClubs: [],
  _filteredPlayers: []
};

const CARDS_CONTINENTS_META = [
  { key: 'europe',        icon: '🇪🇺', name: 'أوروبا (UEFA)',               sub: 'اليورو • دوري الأمم • تصنيف الفيفا', color: '#00d2ff' },
  { key: 'south_america', icon: '🌎', name: 'أمريكا الجنوبية (CONMEBOL)',  sub: 'كوبا أمريكا • أبطال المونديال',     color: '#ffd600' },
  { key: 'africa',        icon: '🌍', name: 'أفريقيا (CAF)',               sub: 'كأس أمم أفريقيا • عمالقة القارة',   color: '#00e676' },
  { key: 'asia',          icon: '🌏', name: 'آسيا (AFC)',                  sub: 'كأس أمم آسيا • المنتخبات العربية',   color: '#38bdf8' },
  { key: 'north_america', icon: '🌊', name: 'أمريكا الشمالية وأوقيانوسيا', sub: 'الكأس الذهبية CONCACAF & OFC',      color: '#c084fc' }
];

const CARDS_LEAGUES_BAR = [
  { code: 'PD',  flag: '🇪🇸', name: 'الدوري الإسباني',  label: '🇪🇸 الدوري الإسباني' },
  { code: 'PL',  flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', name: 'الدوري الإنجليزي', label: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 الدوري الإنجليزي' },
  { code: 'SA',  flag: '🇮🇹', name: 'الدوري الإيطالي',  label: '🇮🇹 الدوري الإيطالي' },
  { code: 'BL1', flag: '🇩🇪', name: 'الدوري الألماني',  label: '🇩🇪 الدوري الألماني' },
  { code: 'FL1', flag: '🇫🇷', name: 'الدوري الفرنسي',  label: '🇫🇷 الدوري الفرنسي' },
  { code: 'UCL', flag: '🏆', name: 'أبطال أوروبا',     label: '🏆 أبطال أوروبا' },
  { code: 'ACL', flag: '🌏', name: 'نخبة آسيا',        label: '🌏 نخبة آسيا' },
  { code: 'CAF', flag: '🌍', name: 'أبطال أفريقيا',    label: '🌍 أبطال أفريقيا' },
  { code: 'DED', flag: '🇳🇱', name: 'الدوري الهولندي',  label: '🇳🇱 الدوري الهولندي' },
  { code: 'PPL', flag: '🇵🇹', name: 'الدوري البرتغالي', label: '🇵🇹 الدوري البرتغالي' },
  { code: 'TSL', flag: '🇹🇷', name: 'الدوري التركي',    label: '🇹🇷 الدوري التركي' }
];

function injectCardsHubCustomStyles() {
  // جميع تنسيقات البطاقات موجودة بشكل رسمي في ملف style.css
}

async function loadCardsHub(forceRefresh = false) {
  injectCardsHubCustomStyles();
  const container = document.getElementById('cards-hub-container');
  if (!container) return;

  const st = window._cardsHubState;
  const reqToken = ++st._reqToken;
  renderCardsHubSkeleton();

  const grid = document.getElementById('cards-grid-box');
  if (grid) {
    grid.innerHTML = '<div class="loading-state" style="grid-column:1/-1;">🌐 جاري سحب البيانات الحية من الـ API...</div>';
  }

  try {
    if (st.subPortal === 'nations') {
      if (forceRefresh || st.nationsData.length === 0) {
        const res = await fetch(`/api/cards_hub?sub_type=nations&refresh=${forceRefresh}`);
        const data = await res.json();
        if (data && data.status === 'success') st.nationsData = data.items || [];
      }
    } else if (st.subPortal === 'clubs') {
      const res = await fetch(`/api/cards_hub?sub_type=clubs&league=${encodeURIComponent(st.clubLeague)}&refresh=${forceRefresh}`);
      const data = await res.json();
      if (data && data.status === 'success') st.clubsData = data.items || [];
    } else if (st.subPortal === 'players') {
      if (!st.selectedClubId) {
        // الخطوة 1 و 2: جلب أندية الدوري المختار ليختار المستخدم النادي (مثل برشلونة)
        const res = await fetch(`/api/cards_hub?sub_type=clubs&league=${encodeURIComponent(st.playerLeague)}&refresh=${forceRefresh}`);
        const data = await res.json();
        if (data && data.status === 'success') st.playerClubsList = data.items || [];
      } else {
        // الخطوة 3: جلب بطاقات جميع لاعبي النادي المختار
        const res = await fetch(`/api/cards_hub?sub_type=squad&league=${encodeURIComponent(st.playerLeague)}&team_id=${encodeURIComponent(st.selectedClubId)}&team_name=${encodeURIComponent(st.selectedClubName)}&refresh=${forceRefresh}`);
        const data = await res.json();
        if (data && data.status === 'success') st.squadPlayersData = data.items || [];
      }
    }
  } catch (e) {
    console.error('Cards Hub API Error:', e);
  }
  if (reqToken !== window._cardsHubState._reqToken) return;

  renderCardsGridItems();
}

function switchCardsSubPortal(portalKey) {
  const st = window._cardsHubState;
  st.subPortal = portalKey;
  st.searchQuery = '';
  if (portalKey === 'players') {
    st.selectedClubId = '';
    st.selectedClubName = '';
  }
  loadCardsHub(false);
}

function selectCardsContinent(contKey) {
  window._cardsHubState.selectedContinent = contKey;
  renderCardsHubSkeleton();
  renderCardsGridItems();
}

function selectCardsLeagueFilter(lgCode) {
  const st = window._cardsHubState;
  if (st.subPortal === 'players') {
    st.playerLeague = lgCode;
    st.selectedClubId = '';
    st.selectedClubName = '';
  } else {
    st.clubLeague = lgCode;
  }
  loadCardsHub(false);
}

function selectClubForPlayerSquad(teamId, teamName, teamCrest) {
  const st = window._cardsHubState;
  st.selectedClubId = String(teamId || '');
  st.selectedClubName = teamName || '';
  st.selectedClubCrest = teamCrest || '';
  st.searchQuery = '';
  loadCardsHub(false);
}

function backToPlayerClubsSelection() {
  const st = window._cardsHubState;
  st.selectedClubId = '';
  st.selectedClubName = '';
  st.searchQuery = '';
  loadCardsHub(false);
}

function jumpFromClubModalToSquad(leagueCode, teamId, teamName, teamCrest) {
  closeModal('cards-detail-modal');
  const st = window._cardsHubState;
  st.subPortal = 'players';
  st.playerLeague = leagueCode || st.clubLeague || 'PD';
  st.selectedClubId = String(teamId || '');
  st.selectedClubName = teamName || '';
  st.selectedClubCrest = teamCrest || '';
  st.searchQuery = '';
  loadCardsHub(false);
}

function onCardsSearchInput(val) {
  window._cardsHubState.searchQuery = (val || '').trim();
  renderCardsGridItems();
}

function renderCardsHubSkeleton() {
  const container = document.getElementById('cards-hub-container');
  if (!container) return;

  const st = window._cardsHubState;
  const sub = st.subPortal;

  let navigationBlockHtml = '';

  if (sub === 'nations') {
    navigationBlockHtml = `
      <div style="margin-bottom:8px; font-size:0.82rem; font-weight:900; color:var(--accent-cyan);">
        🌍 اختر القارة لاستعراض منتخباتها وتصنيفها في الفيفا:
      </div>
      <div class="continent-selector-grid">
        ${CARDS_CONTINENTS_META.map(c => `
          <div class="continent-card-btn ${st.selectedContinent === c.key ? 'active' : ''}" onclick="selectCardsContinent('${c.key}')">
            <span style="font-size:1.7rem;">${c.icon}</span>
            <div style="min-width:0;">
              <div style="font-weight:900; font-size:0.88rem; color:#fff;">${c.name}</div>
              <div style="font-size:0.7rem; color:var(--muted); margin-top:2px;">${c.sub}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } else if (sub === 'clubs') {
    navigationBlockHtml = `
      <div style="margin-bottom:8px; font-size:0.82rem; font-weight:900; color:var(--accent-gold);">
        🏟️ اختر الدوري لاستعراض أنديته وسجلات بطولاته التاريخية:
      </div>
     <div class="mercato-chips-group" style="margin-bottom:12px;">
        ${CARDS_LEAGUES_BAR.map(lg => `
          <button class="mercato-region-chip ${st.clubLeague === lg.code ? 'active' : ''}" onclick="selectCardsLeagueFilter('${lg.code}')">
            ${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(lg.code, lg.flag, 'size-xs') : lg.flag}
            <span>${lg.name}</span>
          </button>
        `).join('')}
      </div>
    `;
  } else if (sub === 'players') {
    const breadcrumbHtml = st.selectedClubId
      ? `
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; background:linear-gradient(90deg, rgba(0,230,118,0.14), rgba(0,210,255,0.08)); border:1px solid var(--accent-green); border-radius:14px; padding:10px 14px; margin-top:10px;">
          <div style="display:flex; align-items:center; gap:10px;">
            ${st.selectedClubCrest ? `<img src="${st.selectedClubCrest}" width="32" height="32" style="object-fit:contain;">` : ''}
            <div>
              <div style="font-weight:900; font-size:0.95rem; color:#fff;">بطاقات لاعبي نادي ${st.selectedClubName} (FIFA Cards)</div>
              <div style="font-size:0.74rem; color:var(--accent-gold); font-weight:700;">اضغط على أي لاعب لفتح بطاقته الكاملة وطاقاته وتفاصيله الجسدية</div>
            </div>
          </div>
          <button class="back-btn" onclick="backToPlayerClubsSelection()" style="padding:6px 14px; font-size:0.78rem;">
            ⬅️ العودة لقائمة أندية الدوري
          </button>
        </div>
      `
      : `
        <div style="font-size:0.8rem; color:var(--accent-gold); font-weight:800; margin-top:6px;">
          👈 الخطوة 2: اختر النادي من القائمة بالأسفل لعرض بطاقات جميع لاعبيه (مثل: برشلونة، ريال مدريد، ليفربول...)
        </div>
      `;

    navigationBlockHtml = `
      <div style="margin-bottom:8px; font-size:0.82rem; font-weight:900; color:var(--accent-green);">
        🎮 الخطوة 1: اختر الدوري للوصول إلى أنديته ولاعبيه:
      </div>
      <div class="mercato-chips-group">
        ${CARDS_LEAGUES_BAR.map(lg => `
          <button class="mercato-region-chip ${st.playerLeague === lg.code ? 'active' : ''}" onclick="selectCardsLeagueFilter('${lg.code}')">
            ${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(lg.code, lg.flag, 'size-xs') : lg.flag}
            <span>${lg.name}</span>
          </button>
        `).join('')}
      </div>
      ${breadcrumbHtml}
    `;
  }

  container.innerHTML = `
    <!-- البوابات الثلاث الرئيسية لصفحة البطاقات -->
    <div class="cards-main-tabs">
      <div class="cards-portal-tab ${sub === 'nations' ? 'active-nations' : ''}" onclick="switchCardsSubPortal('nations')">
        <div>
          <div class="mercato-tab-title"><span>🌍</span> <span>1. قسم المنتخبات العالمية</span></div>
          <div class="mercato-tab-sub">القارات الـ 5، تصنيف الفيفا، ألقاب المونديال والقارات، والهداف التاريخي</div>
        </div>
        <span class="mercato-count-pill" style="color:var(--accent-cyan); border-color:rgba(0,210,255,0.4); background:rgba(0,210,255,0.12);">5 قارات</span>
      </div>

      <div class="cards-portal-tab ${sub === 'clubs' ? 'active-clubs' : ''}" onclick="switchCardsSubPortal('clubs')">
        <div>
          <div class="mercato-tab-title"><span>🏟️</span> <span>2. قسم الأندية التاريخية</span></div>
          <div class="mercato-tab-sub">ألقاب الأندية المحلية والقارية والعالمية، الهداف التاريخي، وعميد اللاعبين</div>
        </div>
        <span class="mercato-count-pill" style="color:var(--accent-gold); border-color:rgba(255,214,0,0.4); background:rgba(255,214,0,0.12);">11 بطولة</span>
      </div>

      <div class="cards-portal-tab ${sub === 'players' ? 'active-players' : ''}" onclick="switchCardsSubPortal('players')">
        <div>
          <div class="mercato-tab-title"><span>🎮</span> <span>3. بطاقات اللاعبين (FIFA)</span></div>
          <div class="mercato-tab-sub">اختر الدوري ⬅️ النادي ⬅️ بطاقات جميع اللاعبين (السرعة، الهجوم، الدفاع، الطول، الوزن)</div>
        </div>
        <span class="mercato-count-pill">FUT Cards</span>
      </div>
    </div>

    <!-- شريط القارات / الدوريات + شريط البحث -->
    <div class="mercato-filters-bar">
      ${navigationBlockHtml}
      <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06);">
        <input
          type="text"
          class="mercato-search-input"
          style="flex:1; min-width:220px;"
          placeholder="${sub === 'nations' ? '🔍 ابحث باسم المنتخب...' : (sub === 'clubs' ? '🔍 ابحث باسم النادي...' : (st.selectedClubId ? '🔍 ابحث باسم اللاعب أو المركز داخل النادي...' : '🔍 ابحث باسم النادي...'))}"
          value="${escapeHtml(st.searchQuery)}"
          oninput="onCardsSearchInput(this.value)"
        >
        <button class="retry-btn" onclick="loadCardsHub(true)" style="padding:7px 14px; font-size:0.78rem;">تحديث حي من الـ API ↻</button>
      </div>
    </div>

    <div id="cards-grid-box" class="cards-grid-layout"></div>
  `;
}

function renderCardsGridItems() {
  const grid = document.getElementById('cards-grid-box');
  if (!grid) return;

  const st = window._cardsHubState;
  const q = (st.searchQuery || '').toLowerCase();

  // ==================== 1. قسم المنتخبات (مقسمة حسب القارات الـ 5) ====================
  if (st.subPortal === 'nations') {
    const list = (st.nationsData || [])
      .filter(n => {
        if (n.continent_key !== st.selectedContinent) return false;
        if (!q) return true;
        return `${n.name} ${n.raw_name} ${n.confederation}`.toLowerCase().includes(q);
      })
      .sort((a, b) => (Number(a.rank) || 999) - (Number(b.rank) || 999));

    if (list.length === 0) {
      grid.innerHTML = '<div class="loading-state" style="grid-column:1/-1;">لا توجد منتخبات مطابقة لبحثك في هذه القارة.</div>';
      return;
    }

    st._filteredNations = list;
    grid.innerHTML = list.map((n, idx) => `
      <div class="sleek-nation-card" onclick="openNationCardByIdx(${idx})">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
          <div style="display:flex; align-items:center; gap:12px; min-width:0;">
            <div class="entity-crest-box" style="width:58px; height:58px; border-radius:14px; overflow:hidden; padding:4px;">
              <img src="${escapeHtml(n.flag_url)}" alt="${escapeHtml(n.name)}" style="width:100%; height:100%; object-fit:cover; border-radius:10px;" onerror="this.src='https://ui-avatars.com/api/?name=NT&background=0f172a&color=00d2ff&rounded=true'">
            </div>
            <div style="min-width:0;">
              <div style="font-size:1.06rem; font-weight:800; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(n.name)}</div>
              <div style="font-size:0.75rem; color:var(--accent-cyan); font-weight:700; margin-top:2px;">الاتحاد: ${escapeHtml(n.confederation)}</div>
            </div>
          </div>

          <div style="text-align:center; background:var(--accent-green-soft); border:1px solid rgba(16,185,129,0.4); border-radius:12px; padding:5px 11px; flex-shrink:0;">
            <div style="font-size:0.64rem; color:var(--muted); font-weight:700;">تصنيف الفيفا</div>
            <div style="font-size:1.12rem; font-weight:900; color:var(--accent-green); direction:ltr;">#${escapeHtml(n.rank)}</div>
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--surface-inset); border:1px solid var(--card-border); border-radius:11px; padding:8px 12px; font-size:0.76rem;">
          <span style="color:var(--muted); font-weight:700;">نقاط الفيفا: <strong style="color:var(--text);">${escapeHtml(n.fifa_points)}</strong></span>
          <span style="color:var(--accent-gold-bright); font-weight:800;">الألقاب والسجل ↗</span>
        </div>
      </div>
    `).join('');
    return;
  }

  // ==================== 2. قسم الأندية (كروت نظيفة تفتح صندوق البطولات والأساطير) ====================
  if (st.subPortal === 'clubs') {
    const list = (st.clubsData || []).filter(c => {
      if (!q) return true;
      return `${c.name} ${c.raw_name} ${c.short_name}`.toLowerCase().includes(q);
    });

    if (list.length === 0) {
      grid.innerHTML = '<div class="loading-state" style="grid-column:1/-1;">لا توجد أندية مطابقة لبحثك.</div>';
      return;
    }

   st._filteredClubs = list;
    grid.innerHTML = list.map((c, idx) => `
      <div class="sleek-club-card" onclick="openClubCardByIdx(${idx})">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
          <div style="display:flex; align-items:center; gap:12px; min-width:0;">
            <div class="entity-crest-box" style="width:58px; height:58px;">
              <img src="${escapeHtml(c.crest)}" alt="${escapeHtml(c.name)}" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=1e293b&color=fff&rounded=true'">
            </div>
            <div style="min-width:0;">
              <div style="font-size:1.06rem; font-weight:800; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(c.name)}</div>
             <div class="dp-inline-league-tag" style="font-size:0.75rem; color:var(--accent-gold-bright); font-weight:700; margin-top:3px;">
                ${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(c.league_code, c.league_flag, 'size-xs') : (c.league_flag || '')}
                <span>${escapeHtml(c.league_name)}</span>
              </div>
            </div>
          </div>

          <div style="text-align:center; background:var(--accent-gold-soft); border:1px solid rgba(245,158,11,0.4); border-radius:12px; padding:5px 11px; flex-shrink:0;">
            <div style="font-size:0.64rem; color:var(--muted); font-weight:700;">المركز</div>
            <div style="font-size:1.12rem; font-weight:900; color:var(--accent-gold-bright); direction:ltr;">#${escapeHtml(c.rank)}</div>
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--surface-inset); border:1px solid var(--card-border); border-radius:11px; padding:8px 12px; font-size:0.76rem;">
          <span style="color:var(--muted); font-weight:700;">النقاط: <strong style="color:var(--accent-green);">${escapeHtml(c.points)}</strong> (${escapeHtml(c.played)} جولة)</span>
          <span style="color:var(--accent-cyan); font-weight:800;">خزانة الألقاب ↗</span>
        </div>
      </div>
    `).join('');
    return;
  }

  // ==================== 3. قسم اللاعبين (الخطوة أ: اختيار النادي | الخطوة ب: بطاقات FIFA للاعبي النادي) ====================
  if (!st.selectedClubId) {
    // عرض أندية الدوري الـ 20 ليختار المستخدم النادي (مثل برشلونة)
    const clubs = (st.playerClubsList || []).filter(c => {
      if (!q) return true;
      return `${c.name} ${c.raw_name} ${c.short_name}`.toLowerCase().includes(q);
    });

    if (clubs.length === 0) {
      grid.innerHTML = '<div class="loading-state" style="grid-column:1/-1;">لا توجد أندية متاحة حالياً.</div>';
      return;
    }

    st._filteredPlayerClubs = clubs;
    grid.innerHTML = clubs.map((c, idx) => `
      <div class="sleek-club-card" onclick="selectClubForSquadByIdx(${idx})">
        <div style="display:flex; align-items:center; gap:14px;">
          <div class="entity-crest-box" style="width:64px; height:64px;">
            <img src="${escapeHtml(c.crest)}" alt="${escapeHtml(c.name)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          </div>
          <div style="flex:1; min-width:0;">
            <div style="font-size:1.15rem; font-weight:900; color:var(--text);">${escapeHtml(c.name)}</div>
            <div style="font-size:0.76rem; color:var(--muted); font-weight:700; margin-top:3px;">
              ${escapeHtml(c.league_flag)} ${escapeHtml(c.league_name)} • المركز #${escapeHtml(c.rank)}
            </div>
          </div>
        </div>
        <div style="background:var(--accent-green-soft); border:1px solid rgba(16, 185, 129, 0.35); border-radius:12px; padding:8px 12px; text-align:center; font-size:0.8rem; font-weight:900; color:var(--accent-green);">
          🎮 استعراض بطاقات جميع لاعبي ${escapeHtml(c.name)} ⬅️
        </div>
      </div>
    `).join('');
    return;
  }

  const players = (st.squadPlayersData || []).filter(p => {
    if (!q) return true;
    return `${p.name} ${p.position} ${p.pos_abbr} ${p.nationality} ${p.jersey}`.toLowerCase().includes(q);
  });

  if (players.length === 0) {
    grid.innerHTML = '<div class="loading-state" style="grid-column:1/-1;">لا يوجد لاعبون مطابقون لبحثك في هذا النادي.</div>';
    return;
  }

  st._filteredPlayers = players;
  grid.innerHTML = players.map((p, idx) => {
    const f = p.fifa || { pac: 80, sho: 75, pas: 78, dri: 80, def: 65, phy: 76 };
    const ovr = p.overall || 82;
    const isSpecial = ovr >= 86;

    return `
      <div class="fifa-fut-card ${isSpecial ? 'tier-special' : ''}" onclick="openFifaPlayerModal(${idx})">
        <div class="fut-header-split">
          <div class="fut-rating-column">
            <div class="fut-ovr-big">${escapeHtml(ovr)}</div>
            <div class="fut-pos-tag">${escapeHtml(p.pos_abbr || 'CM')}</div>
            <div style="font-size:0.7rem; color:var(--accent-cyan); font-weight:900; margin-top:3px;">#${escapeHtml(p.jersey || '-')}</div>
          </div>

          <div class="fut-player-portrait">
            <img src="${escapeHtml(p.avatar)}" alt="${escapeHtml(p.name)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          </div>

          <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
            ${p.club_crest ? `<img src="${escapeHtml(p.club_crest)}" width="34" height="34" style="object-fit:contain;" onerror="this.onerror=null; this.style.display='none';">` : ''}
            <span style="font-size:0.68rem; background:rgba(255,255,255,0.08); padding:2px 8px; border-radius:8px; color:#e2e8f0; font-weight:800;">${escapeHtml(p.nationality)}</span>
          </div>
        </div>

        <div class="fut-name-banner">${escapeHtml(p.name)}</div>

        <div class="fut-attributes-grid">
          <div class="fut-attr-item"><span class="fut-attr-lbl">⚡ السرعة PAC</span><span class="fut-attr-val">${escapeHtml(f.pac)}</span></div>
          <div class="fut-attr-item"><span class="fut-attr-lbl">🪄 المراوغة DRI</span><span class="fut-attr-val">${escapeHtml(f.dri)}</span></div>
          <div class="fut-attr-item"><span class="fut-attr-lbl">🎯 الهجوم SHO</span><span class="fut-attr-val">${escapeHtml(f.sho)}</span></div>
          <div class="fut-attr-item"><span class="fut-attr-lbl">🛡️ الدفاع DEF</span><span class="fut-attr-val">${escapeHtml(f.def)}</span></div>
          <div class="fut-attr-item"><span class="fut-attr-lbl">📐 التمرير PAS</span><span class="fut-attr-val">${escapeHtml(f.pas)}</span></div>
          <div class="fut-attr-item"><span class="fut-attr-lbl">💪 البدني PHY</span><span class="fut-attr-val">${escapeHtml(f.phy)}</span></div>
        </div>

        <div class="fut-bio-strip">
          <span>📏 ${escapeHtml(p.height || '180 سم')}</span>
          <span>⚖️ ${escapeHtml(p.weight || '74 كغ')}</span>
          <span>🎂 ${escapeHtml(p.age)} سنة</span>
          <span style="color:var(--accent-green);">${escapeHtml(p.position)}</span>
        </div>
      </div>
    `;
  }).join('');
}
function openNationCardByIdx(idx) {
  const n = (window._cardsHubState._filteredNations || [])[idx];
  if (!n) return;
  openEntityHistoryModal('nation', encodeURIComponent(n.raw_name || n.name), encodeURIComponent(n.name), encodeURIComponent(n.flag_url || ''), n.confederation, n.rank);
}

function openClubCardByIdx(idx) {
  const c = (window._cardsHubState._filteredClubs || [])[idx];
  if (!c) return;
  openEntityHistoryModal('club', encodeURIComponent(c.raw_name || c.name), encodeURIComponent(c.name), encodeURIComponent(c.crest || ''), c.league_code, c.rank, c.team_id || '');
}

function selectClubForSquadByIdx(idx) {
  const c = (window._cardsHubState._filteredPlayerClubs || [])[idx];
  if (!c) return;
  selectClubForPlayerSquad(c.team_id, c.name, c.crest);
}

// =========================================================
// الصندوق المنبثق (Modal) لتفاصيل المنتخب أو النادي (الألقاب + الأساطير)
// =========================================================
async function openEntityHistoryModal(entityType, encodedRawName, encodedArName, encodedImg, extraInfo, rankNum, teamId = '') {
  const modal = document.getElementById('cards-detail-modal');
  const body = document.getElementById('cards-modal-body');
  if (!modal || !body) return;

  const arName = decodeURIComponent(encodedArName || '');
  const imgUrl = decodeURIComponent(encodedImg || '');

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  body.innerHTML = `
    <div class="loading-state" style="padding:40px 15px;">
      <div style="font-size:2rem; margin-bottom:10px;">🏆</div>
      <div style="color:var(--accent-gold); font-weight:900;">جاري سحب سجل البطولات التاريخي وأساطير (${arName}) حياً من الـ API...</div>
    </div>
  `;

  try {
    const res = await fetch(`/api/card_profile_detail?entity_type=${encodeURIComponent(entityType)}&name=${encodedRawName}&extra=${encodeURIComponent(extraInfo || '')}`);
    const data = await res.json();
    const pf = (data && data.profile) ? data.profile : {};

    const honoursList = Array.isArray(pf.honours_detailed) ? pf.honours_detailed : [];
    const worldHonours = honoursList.filter(h => h.category === 'world');
    const contHonours = honoursList.filter(h => h.category === 'continental');
    const domHonours = honoursList.filter(h => h.category !== 'world' && h.category !== 'continental');

    const renderHonoursGroup = (title, items, borderCol) => {
      if (!items || items.length === 0) return '';
      return `
        <div style="margin-bottom:12px;">
          <div style="font-size:0.78rem; font-weight:900; color:${borderCol}; margin-bottom:6px;">${title}</div>
          <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(175px, 1fr)); gap:8px;">
            ${items.map(h => `
              <div style="background:var(--surface-inset); border:1px solid var(--card-border); border-right:3.5px solid ${borderCol}; border-radius:12px; padding:8px 12px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.78rem; font-weight:800; color:var(--text);">${escapeHtml(h.title)}</span>
                <span style="font-size:1.05rem; font-weight:900; color:${borderCol}; background:var(--card); padding:2px 9px; border-radius:8px;">${escapeHtml(h.count)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    };

    const allHonoursHtml = honoursList.length > 0
      ? (
          renderHonoursGroup('🌍 الألقاب العالمية والدولية الكبرى:', worldHonours, 'var(--accent-gold-bright)') +
          renderHonoursGroup('🏆 الألقاب القارية الرسمية:', contHonours, 'var(--accent-cyan)') +
          renderHonoursGroup('🥇 البطولات المحلية (الدوري والكأس والسوبر):', domHonours, 'var(--accent-green)')
        )
      : `<div class="dp-modal-subpanel" style="border-style:dashed; text-align:center; color:var(--muted); margin-bottom:12px;">
          لم يتوج بألقاب كبرى في السجل الدولي أو أن البيانات قيد التحديث.
         </div>`;

    const squadJumpBtn = (entityType === 'club' && teamId)
      ? `<button class="ai-btn"
            data-league="${extraInfo}"
            data-team-id="${escapeHtml(teamId)}"
            data-team-name="${arName}"
            data-team-crest="${escapeHtml(imgUrl)}"
            onclick="jumpFromClubModalToSquad(this.dataset.league, this.dataset.teamId, this.dataset.teamName, this.dataset.teamCrest)"
            style="width:100%; margin-top:12px; padding:10px; font-size:0.86rem;">
          🎮 استعراض بطاقات جميع لاعبي ${escapeHtml(arName)} (FIFA Cards) ⬅️
         </button>`
      : '';

    body.innerHTML = `
      <!-- رأس الصندوق -->
      <div style="display:flex; justify-content:space-between; align-items:center; gap:14px; border-bottom:1px solid var(--card-border); padding-bottom:14px; margin-bottom:16px; flex-wrap:wrap; padding-left: 38px;">
        <div style="display:flex; align-items:center; gap:14px;">
          <img src="${escapeHtml(imgUrl || pf.image)}" width="68" height="68" style="object-fit:contain; border-radius:16px; background:var(--surface-inset); padding:6px; border:1.5px solid var(--accent-gold);" onerror="this.onerror=null; this.style.display='none';">
          <div>
            <h3 style="font-size:1.3rem; font-weight:900; color:var(--text); margin:0;">${escapeHtml(arName)}</h3>
            <div style="font-size:0.8rem; color:var(--accent-cyan); font-weight:800; margin-top:4px;">
              ${entityType === 'nation'
                ? `🌍 الاتحاد القاري: ${escapeHtml(extraInfo)} • تصنيف الفيفا العالمي: #${escapeHtml(rankNum)}`
                : `📅 التأسيس: ${escapeHtml(pf.founded || '-')} • 🏟️ الملعب: ${escapeHtml(pf.stadium || '-')}`}
            </div>
          </div>
        </div>
        <div style="background:var(--accent-gold-soft); border:1.5px solid var(--accent-gold); color:var(--accent-gold-bright); padding:6px 14px; border-radius:14px; text-align:center;">
          <div style="font-size:0.65rem; font-weight:800;">إجمالي البطولات</div>
          <div style="font-size:1.25rem; font-weight:900;">🏆 ${escapeHtml(pf.total_trophies || 0)}</div>
        </div>
      </div>

      <!-- خزانة الألقاب التفصيلية -->
      <h4 style="font-size:0.92rem; color:var(--accent-gold-bright); margin-bottom:10px;">🏛️ خزانة الألقاب والبطولات الرسمية:</h4>
      ${allHonoursHtml}

      <!-- السجلات التاريخية (الهداف التاريخي، الأكثر صناعة، الأكثر مشاركة) -->
      <h4 style="font-size:0.92rem; color:var(--accent-cyan); margin:14px 0 8px 0;">🌟 السجل التاريخي وأساطير ${entityType === 'nation' ? 'المنتخب' : 'النادي'}:</h4>
      <div class="entity-records-list" style="gap:10px; font-size:0.84rem; margin-bottom:14px;">
        <div class="entity-rec-row" style="border-bottom:1px dashed var(--card-border); padding-bottom:6px;">
          <span class="entity-rec-lbl">⚽ الهداف التاريخي:</span>
          <span class="entity-rec-val" style="color:var(--accent-gold-bright); font-size:0.88rem;">${escapeHtml(pf.top_scorer || '-')}</span>
        </div>
        <div class="entity-rec-row" style="border-bottom:1px dashed var(--card-border); padding-bottom:6px;">
          <span class="entity-rec-lbl">🎯 الأكثر صناعة للأهداف:</span>
          <span class="entity-rec-val" style="color:var(--accent-green); font-size:0.88rem;">${escapeHtml(pf.most_assists || '-')}</span>
        </div>
        <div class="entity-rec-row">
          <span class="entity-rec-lbl">🛡️ الأكثر لعباً ومشاركة:</span>
          <span class="entity-rec-val" style="color:var(--accent-cyan); font-size:0.88rem;">${escapeHtml(pf.most_apps || '-')}</span>
        </div>
      </div>

      ${entityType === 'club' && teamId ? '<div id="dp-club-recent-results-box" style="margin-bottom:14px;"></div>' : ''}

      <!-- نبذة موسوعية حية -->
      <div class="dp-modal-panel" style="border-right:4px solid var(--accent-green); font-size:0.82rem; line-height:1.7; color:var(--text-secondary);">
        <div style="font-weight:900; color:var(--accent-green); margin-bottom:4px;">📖 نبذة تاريخية موثقة:</div>
        <div>${escapeHtml(pf.bio || '')}</div>
      </div>

      ${squadJumpBtn}
    `;
    if (entityType === 'club' && teamId && extraInfo) {
      loadClubRecentMatchesIntoModal(extraInfo, teamId);
    }
  } catch (e) {
    body.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">تعذر جلب بيانات السجل التاريخي في هذه اللحظة.</div>';
  }
}

async function loadClubRecentMatchesIntoModal(leagueCode, teamId) {
  const box = document.getElementById('dp-club-recent-results-box');
  if (!box) return;
  box.innerHTML = '<div style="font-size:0.76rem; color:var(--muted); padding:6px 0;">جاري جلب آخر 5 نتائج رسمية للنادي...</div>';

  try {
    const res = await fetch(`/api/club_recent/${encodeURIComponent(leagueCode)}/${encodeURIComponent(teamId)}`);
    const data = await res.json();
    const list = (data && Array.isArray(data.matches)) ? data.matches : [];
    if (list.length === 0) {
      box.innerHTML = '';
      return;
    }

    box.innerHTML = `
      <h4 style="font-size:0.88rem; color:var(--accent-green); margin-bottom:8px;">آخر 5 مباريات رسمية (النتائج الحقيقية)</h4>
      <div style="display:flex; flex-direction:column; gap:6px;">
        ${list.map(m => {
          const badgeCls = m.result === 'W' ? 'form-w' : (m.result === 'L' ? 'form-l' : 'form-d');
          return `
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; background:var(--surface-inset); border:1px solid var(--card-border); border-radius:10px; padding:7px 11px; font-size:0.78rem;">
              <div style="display:flex; align-items:center; gap:8px; min-width:0;">
                <span class="badge-f ${badgeCls}">${escapeHtml(m.result)}</span>
                ${m.opponent_crest ? `<img src="${escapeHtml(m.opponent_crest)}" width="18" height="18" style="object-fit:contain;" onerror="this.style.display='none'">` : ''}
                <span style="font-weight:700; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                  ${m.is_home ? 'ضد' : 'خارج الأرض أمام'} ${escapeHtml(m.opponent)}
                </span>
              </div>
              <div style="display:flex; align-items:center; gap:8px; flex-shrink:0;">
                <strong style="color:var(--accent-gold-bright); direction:ltr;">${escapeHtml(m.score)}</strong>
                <span style="color:var(--muted); font-size:0.7rem;">${escapeHtml(m.date)}</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (e) {
    box.innerHTML = '';
  }
}

// =========================================================
// الصندوق المنبثق لبطاقة اللاعب التفصيلية (FIFA Player Modal)
// =========================================================
function openFifaPlayerModal(playerIdx) {


  const p = (window._cardsHubState._filteredPlayers || [])[playerIdx];
  if (!p) return;

  const modal = document.getElementById('cards-detail-modal');
  const body = document.getElementById('cards-modal-body');
  if (!modal || !body) return;

  const f = p.fifa || { pac: 80, sho: 75, pas: 78, dri: 80, def: 65, phy: 76 };

 const statBarRow = (label, val, col) => `
    <div style="margin-bottom:9px;">
      <div style="display:flex; justify-content:space-between; font-size:0.82rem; font-weight:800; margin-bottom:4px;">
        <span style="color:var(--text-secondary);">${label}</span>
        <span style="color:${col}; font-weight:900;">${escapeHtml(val)} / 99</span>
      </div>
      <div style="height:8px; background:var(--surface-inset); border-radius:99px; overflow:hidden; border:1px solid var(--card-border);">
        <div style="width:${Math.min(100, Number(val) || 0)}%; height:100%; background:${col}; border-radius:99px;"></div>
      </div>
    </div>
  `;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

// =========================================================
// 7. غرفة الأخبار الرياضية الحية (FIFO 20)
// =========================================================
let currentNewsItems = [];

window._newsReqToken = 0;

async function loadNewsFeed(forceRefresh = false) {
  const container = document.getElementById('news-container');
  if (!container) return;
  const reqToken = ++window._newsReqToken;

  container.innerHTML = renderSkeletonCardsHtml(6);

  try {
    const res = await fetch(`/api/news?refresh=${forceRefresh}`);
    const data = await res.json();
    if (reqToken !== window._newsReqToken) return;
    const list = data.news || [];
    currentNewsItems = list;

    if (forceRefresh) {
      loadHomeQuietHighlightsStrip(true);
    }

    if (list.length === 0) {
      container.innerHTML = '<div class="loading-state" style="grid-column: 1/-1;">لا توجد أخبار متاحة حالياً.</div>';
      return;
    }

    container.innerHTML = list.map((item, idx) => `
      <div class="news-item-card" onclick="openNewsArticle(${idx})">
        ${item.image_url ? `<img src="${escapeHtml(item.image_url)}" class="news-card-thumb" onerror="this.onerror=null; this.style.display='none';">` : ''}
        <div class="news-card-content">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.72rem; color:var(--muted);">🕒 ${escapeHtml(item.published_time || 'حديثاً')}</span>
            <span class="hub-badge" style="color:var(--accent-gold-bright); font-size:0.68rem;">${escapeHtml(item.source || 'أخبار عالمية')}</span>
          </div>
          <h3 class="news-card-title">${escapeHtml(item.title)}</h3>
          <p class="news-card-desc">${escapeHtml(item.summary || 'انقر لقراءة التقرير والتفاصيل الكاملة...')}</p>
          <div style="font-size:0.75rem; color:var(--accent-cyan); font-weight:800; margin-top:8px;">
            قراءة الخبر كاملاً 📖 ↗
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    if (reqToken === window._newsReqToken) {
      container.innerHTML = '<div class="loading-state" style="grid-column: 1/-1; color:var(--accent-red);">تعذر تحميل الأخبار، يرجى المحاولة لاحقاً.</div>';
    }
  }
}

window._activeNewsArticle = null;

window.shareCurrentNewsArticle = async function() {
  const item = window._activeNewsArticle;
  if (!item) return;
  const shareText = `📰 ${item.title}\n${item.source_url || window.location.href}\nعبر DeepPitch Analytics Pro`;
  if (navigator.share) {
    try {
      await navigator.share({ title: item.title, text: item.title, url: item.source_url || window.location.href });
      return;
    } catch (e) {}
  }
  try {
    await navigator.clipboard.writeText(shareText);
    if (typeof window.showAppToast === 'function') window.showAppToast('تم نسخ رابط الخبر بنجاح');
  } catch (e) {}
};

window.openNewsArticleByObj = function(item) {
  if (!item) return;
  window._activeNewsArticle = item;

  const modal = document.getElementById('news-reader-modal');
  if (!modal) return;

  const img = document.getElementById('news-modal-img');
  const title = document.getElementById('news-modal-title');
  const body = document.getElementById('news-modal-body');
  const dateEl = document.getElementById('news-modal-date');
  const link = document.getElementById('news-modal-link');

  if (title) title.innerText = item.title || '';
  if (body) body.innerText = item.summary || item.title || '';
  if (dateEl) dateEl.innerText = item.published_time ? `نُشر في: ${item.published_time}` : '';

  if (img) {
    if (item.image_url) {
      img.src = item.image_url;
      img.style.display = 'block';
    } else {
      img.style.display = 'none';
    }
  }

  if (link) {
    if (item.source_url) {
      link.href = item.source_url;
      link.style.display = 'inline-block';
    } else {
      link.style.display = 'none';
    }
  }

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
};

function openNewsArticle(idx) {
  const item = currentNewsItems[idx];
  if (item) window.openNewsArticleByObj(item);
}
document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-overlay')) {
    if (e.target.id && typeof window.closeModal === 'function') {
      window.closeModal(e.target.id);
    } else {
      e.target.style.display = 'none';
      document.body.style.overflow = '';
    }
  }
});
// =========================================================
// 8. محرك عرض الأرشيف التاريخي وموسوعة الدوريات الشاملة
// =========================================================
window._currentHistorySeasons = [];
window._historySeasonsLimit = 15;
window._historySearchQuery = '';

window.expandHistorySeasons = function() {
  window._historySeasonsLimit += 25;
  filterHistorySeasons(window._historySearchQuery);
};

function filterHistorySeasons(query) {
  const tbody = document.getElementById('history-seasons-tbody');
  const countBadge = document.getElementById('history-filtered-count');
  const moreWrap = document.getElementById('history-more-wrap');
  if (!tbody) return;

  window._historySearchQuery = query || '';
  const q = window._historySearchQuery.trim().toLowerCase();
  const list = window._currentHistorySeasons || [];
  const filtered = q
    ? list.filter(s =>
        (s.season || '').toLowerCase().includes(q) ||
        (s.champion || '').toLowerCase().includes(q) ||
        (s.runner_up || '').toLowerCase().includes(q) ||
        (s.top_scorer || '').toLowerCase().includes(q) ||
        ((s.top4 || []).join(' ').toLowerCase().includes(q))
      )
    : list;

  if (countBadge) countBadge.innerText = `${filtered.length} نسخة`;

  const visibleList = q ? filtered : filtered.slice(0, window._historySeasonsLimit);

  tbody.innerHTML = visibleList.map(s => `
    <tr>
      <td style="color:var(--muted); font-size:0.75rem;">#${list.length - list.indexOf(s)}</td>
      <td style="font-weight:900; color:var(--accent-cyan); white-space:nowrap;">${escapeHtml(s.season)}</td>
      <td style="font-weight:900; color:var(--accent-gold); max-width:145px; overflow:hidden; text-overflow:ellipsis;">🏆 ${escapeHtml(s.champion)}</td>
      <td style="font-size:0.8rem; color:var(--text-secondary); max-width:130px; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(s.runner_up || '-')}</td>
      <td style="font-size:0.75rem; color:var(--muted); max-width:180px; overflow:hidden; text-overflow:ellipsis;" title="${escapeHtml((s.top4 || []).join(' • '))}">${escapeHtml((s.top4 || []).slice(0, 3).join(' • '))}</td>
      <td style="font-size:0.78rem; color:var(--accent-green); font-weight:700; max-width:160px; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(s.top_scorer || '-')}</td>
    </tr>
  `).join('');

  if (moreWrap) {
    if (!q && filtered.length > visibleList.length) {
      moreWrap.innerHTML = `<button type="button" class="retry-btn" onclick="expandHistorySeasons()" style="width:100%; margin-top:10px; justify-content:center;">عرض المزيد من النسخ (${visibleList.length} من ${filtered.length}) ▼</button>`;
    } else {
      moreWrap.innerHTML = '';
    }
  }
}

async function loadLeagueHistory(leagueCode, forceRefresh = false) {
  const container = document.getElementById('history-container');
  if (!container) return;
  const reqToken = ++window._viewReqToken;

  container.innerHTML = renderSkeletonCardsHtml(4);

  try {
    const res = await fetch(`/api/league_history/${leagueCode}?refresh=${forceRefresh}`);
    const resData = await res.json();
    if (reqToken !== window._viewReqToken) return;

    if (!resData || resData.status !== 'success' || !resData.data) {
      const msg = (resData && resData.message) ? resData.message : 'لا تتوفر سجلات تاريخية حالياً.';
      container.innerHTML = `<div class="dp-empty-state">${escapeHtml(msg)}</div>`;
      return;
    }

    const d = resData.data;
    const rec = d.records || {};
    const titles = d.titles_table || [];
    const seasons = d.seasons || [];
    window._currentHistorySeasons = seasons;
    window._historySeasonsLimit = 15;
    window._historySearchQuery = '';

    const recordItems = [
      { lbl: 'الهداف التاريخي للبطولة', val: rec.top_scorer, cls: '' },
      { lbl: 'الأكثر صناعة للأهداف', val: rec.most_assists, cls: 'accent-cyan' },
      { lbl: 'الأكثر مشاركة (عميد اللاعبين)', val: rec.most_apps, cls: 'accent-gold' },
      { lbl: 'الأكثر حفاظاً على نظافة الشباك', val: rec.most_clean_sheets, cls: 'accent-cyan' },
      { lbl: 'هداف موسم واحد (رقم قياسي)', val: rec.single_season_scorer, cls: 'accent-gold' },
      { lbl: 'أعلى رصيد نقطي في موسم واحد', val: rec.record_pts_season, cls: 'accent-gold' },
      { lbl: 'أقوى هجوم لفريق في موسم', val: rec.team_goals_season, cls: '' },
      { lbl: 'أطول سلسلة لاهزيمة تاريخياً', val: rec.unbeaten_streak, cls: '' },
      { lbl: 'أكبر فوز في تاريخ المسابقة', val: rec.biggest_win, cls: 'accent-red' },
      { lbl: 'المدرب الأكثر تتويجاً', val: rec.top_manager, cls: 'accent-cyan' },
      { lbl: 'الأكثر تلقياً للبطاقات الصفراء', val: rec.most_yellows, cls: 'accent-gold' },
      { lbl: 'الأكثر تلقياً للبطاقات الحمراء', val: rec.most_reds, cls: 'accent-red' }
    ];

    container.innerHTML = `
      <div class="dp-history-shell">
        <div class="dp-history-hdr">
          <div>
            <h2 style="font-size:1.25rem; font-weight:800; color:var(--text); margin:0; display:flex; align-items:center; gap:10px;">
              ${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(leagueCode, d.flag, 'size-lg') : (d.flag || '')}
              <span>${escapeHtml(d.league_name)}</span>
            </h2>
            <div style="font-size:0.8rem; color:var(--muted); margin-top:4px;">
              التأسيس: <strong style="color:var(--text-secondary);">${escapeHtml(d.founded)}</strong> •
              النسخ المؤرشفة: <strong style="color:var(--accent-green);">${d.total_editions || seasons.length} نسخة</strong> •
              الأكثر تتويجاً: <strong style="color:var(--accent-gold-bright);">${escapeHtml(d.most_successful)}</strong>
            </div>
          </div>
          <span class="hub-badge">الموسوعة الرسمية</span>
        </div>

        <h4 style="font-size:0.92rem; color:var(--text); margin-bottom:10px; font-weight:800;">الأرقام القياسية عبر التاريخ</h4>
        <div class="history-records-scroll">
          ${recordItems.map(r => `
            <div class="dp-history-rec-card ${r.cls}">
              <div class="dp-history-rec-lbl">${r.lbl}</div>
              <div class="dp-history-rec-val">${escapeHtml(r.val || '-')}</div>
            </div>
          `).join('')}
        </div>

        <div class="history-tables-split">
          <div class="data-card" style="margin:0;">
           <h4 style="font-size:0.92rem; color:var(--accent-gold-bright); margin-bottom:12px;">السجل الذهبي للأندية المتوجة (${titles.length})</h4>
            <div class="table-container">
              <table class="styled-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>النادي</th>
                    <th style="text-align:center;">الألقاب</th>
                    <th style="text-align:center;">الوصيف</th>
                    <th style="text-align:center;">آخر لقب</th>
                  </tr>
                </thead>
                <tbody>
                  ${titles.map((t, idx) => `
                    <tr>
                      <td style="color:var(--muted);">${idx + 1}</td>
                      <td style="font-weight:800;">${escapeHtml(t.club)}</td>
                      <td style="text-align:center; font-weight:900; color:var(--accent-gold-bright);">${t.titles}</td>
                      <td style="text-align:center; color:var(--muted);">${t.runner_up}</td>
                      <td style="text-align:center; font-size:0.78rem; color:var(--accent-cyan);">${escapeHtml(t.last_title || '-')}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>

          <div class="data-card" style="margin:0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
              <h4 style="font-size:0.92rem; color:var(--accent-green); margin:0;">
                سجل جميع النسخ (<span id="history-filtered-count">${seasons.length} نسخة</span>)
              </h4>
              <input
                type="text"
                class="mercato-search-input"
                style="min-width:210px; padding:6px 12px; font-size:0.78rem;"
                placeholder="ابحث بالسنة، البطل، أو الهداف..."
                oninput="filterHistorySeasons(this.value)"
              >
            </div>
            <div class="table-container">
              <table class="styled-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>الموسم</th>
                    <th>البطل</th>
                    <th>الوصيف</th>
                    <th>أوائل الترتيب</th>
                    <th>هداف النسخة</th>
                  </tr>
                </thead>
                <tbody id="history-seasons-tbody"></tbody>
              </table>
            </div>
            <div id="history-more-wrap"></div>
          </div>
        </div>
      </div>
    `;

    filterHistorySeasons('');
  } catch (err) {
    container.innerHTML = '<div class="dp-empty-state" style="color:var(--accent-red);">تعذر تحميل السجلات التاريخية حالياً.</div>';
  }
}

// =========================================================
// 9. محرك استوديو المقارنة الرادارية ومحاكي القمم (Radar Clash Studio)
// =========================================================
window._radarTeamsCache = {};
window._radarState = {
  leagueA: 'PD',
  teamA: '',
  leagueB: 'PL',
  teamB: '',
  venue: 'neutral',
  initialized: false
};

const RADAR_LEAGUE_LIST = [
  { code: 'PL', name: 'Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  { code: 'PD', name: 'La Liga 🇪🇸' },
  { code: 'BL1', name: 'Bundesliga 🇩🇪' },
  { code: 'SA', name: 'Serie A 🇮🇹' },
  { code: 'FL1', name: 'Ligue 1 🇫🇷' },
  { code: 'UCL', name: 'Champions League 🏆' },
  { code: 'ACL', name: 'AFC Champions League 🌏' },
  { code: 'CAF', name: 'CAF Champions League 🌍' },
  { code: 'UNL', name: 'UEFA Nations League 🇪🇺' },
  { code: 'DED', name: 'Eredivisie 🇳🇱' },
  { code: 'PPL', name: 'Liga Portugal 🇵🇹' },
  { code: 'TSL', name: 'Süper Lig 🇹🇷' }
];

async function fetchRadarLeagueTeams(leagueCode) {
  if (window._radarTeamsCache[leagueCode] && window._radarTeamsCache[leagueCode].length > 0) {
    return window._radarTeamsCache[leagueCode];
  }
  try {
    const res = await fetch(`/api/radar_teams/${leagueCode}`);
    const data = await res.json();
    if (data && data.status === 'success' && Array.isArray(data.teams)) {
      window._radarTeamsCache[leagueCode] = data.teams;
      return data.teams;
    }
  } catch (e) {}
  return [];
}

async function initRadarClashStudio() {
  const container = document.getElementById('radar-studio-container');
  if (!container) return;

  const leagueOptionsA = RADAR_LEAGUE_LIST.map(l =>
    `<option value="${l.code}" ${l.code === window._radarState.leagueA ? 'selected' : ''}>${l.name}</option>`
  ).join('');

  const leagueOptionsB = RADAR_LEAGUE_LIST.map(l =>
    `<option value="${l.code}" ${l.code === window._radarState.leagueB ? 'selected' : ''}>${l.name}</option>`
  ).join('');

  container.innerHTML = `
    <div class="radar-studio-card">
      <div class="radar-presets-bar">
        <span style="font-size:0.78rem; color:var(--muted); font-weight:800;">🔥 قمم جاهزة بنقرة:</span>
        <button class="radar-preset-chip" onclick="applyRadarPreset('PD','Real Madrid','PL','Man City')">ريال مدريد ⚔️ مان سيتي</button>
        <button class="radar-preset-chip" onclick="applyRadarPreset('PD','Barcelona','BL1','Bayern Munich')">برشلونة ⚔️ بايرن ميونخ</button>
        <button class="radar-preset-chip" onclick="applyRadarPreset('PL','Liverpool','SA','Inter')">ليفربول ⚔️ إنتر ميلان</button>
        <button class="radar-preset-chip" onclick="applyRadarPreset('PL','Arsenal','FL1','PSG')">أرسنال ⚔️ باريس</button>
        <button class="radar-preset-chip" onclick="applyRadarPreset('PD','Real Madrid','PD','Barcelona')">الكلاسيكو 🇪🇸</button>
      </div>

      <div class="radar-selectors-grid">
        <div class="radar-team-picker picker-a">
          <div class="picker-badge" style="color:var(--accent-green);">🟢 الطرف الأول (Team A)</div>
          <div class="picker-row">
            <select id="radar-league-a" onchange="onRadarLeagueChange('A')">${leagueOptionsA}</select>
            <select id="radar-team-a" onchange="triggerRadarClash()"></select>
          </div>
        </div>

        <div class="radar-vs-controls">
          <div class="vs-circle-badge">VS</div>
          <div class="venue-pills">
            <button id="v-btn-neutral" class="venue-pill active" onclick="setRadarVenue('neutral')">🏟️ أرض محايدة</button>
            <button id="v-btn-home_a" class="venue-pill" onclick="setRadarVenue('home_a')">🏠 ملعب الأول</button>
            <button id="v-btn-home_b" class="venue-pill" onclick="setRadarVenue('home_b')">✈️ ملعب الثاني</button>
          </div>
        </div>

        <div class="radar-team-picker picker-b">
          <div class="picker-badge" style="color:var(--accent-cyan);">🔵 الطرف الثاني (Team B)</div>
          <div class="picker-row">
            <select id="radar-league-b" onchange="onRadarLeagueChange('B')">${leagueOptionsB}</select>
            <select id="radar-team-b" onchange="triggerRadarClash()"></select>
          </div>
        </div>
      </div>

      <div id="radar-clash-output">
        <div class="loading-state">جاري رسم المخطط الراداري السداسي وحساب احتمالات القمة...</div>
      </div>
    </div>
  `;

  await Promise.all([populateTeamDropdown('A'), populateTeamDropdown('B')]);
  await triggerRadarClash();
}

async function populateTeamDropdown(side) {
  const isA = side === 'A';
  const lgSelect = document.getElementById(isA ? 'radar-league-a' : 'radar-league-b');
  const tmSelect = document.getElementById(isA ? 'radar-team-a' : 'radar-team-b');
  if (!lgSelect || !tmSelect) return;

  const lgCode = lgSelect.value;
  if (isA) window._radarState.leagueA = lgCode;
  else window._radarState.leagueB = lgCode;

  tmSelect.innerHTML = '<option value="">جاري التحميل...</option>';
  const teams = await fetchRadarLeagueTeams(lgCode);

  if (!teams.length) {
    tmSelect.innerHTML = '<option value="">لا توجد فرق</option>';
    return;
  }

  let targetShort = isA ? window._radarState.teamA : window._radarState.teamB;
  if (!targetShort || !teams.some(t => t.short.toLowerCase().includes(targetShort.toLowerCase()) || t.name.toLowerCase().includes(targetShort.toLowerCase()))) {
    targetShort = teams[0].short;
  }

  tmSelect.innerHTML = teams.map(t => {
    const isSel = t.short.toLowerCase().includes(targetShort.toLowerCase()) || t.name.toLowerCase().includes(targetShort.toLowerCase());
    return `<option value="${t.short}" ${isSel ? 'selected' : ''}>#${t.rank} ${t.short} (Elo ${t.elo})</option>`;
  }).join('');

  if (isA) window._radarState.teamA = tmSelect.value;
  else window._radarState.teamB = tmSelect.value;
}

async function onRadarLeagueChange(side) {
  if (side === 'A') window._radarState.teamA = '';
  else window._radarState.teamB = '';
  await populateTeamDropdown(side);
  await triggerRadarClash();
}

function setRadarVenue(venueMode) {
  window._radarState.venue = venueMode;
  ['neutral', 'home_a', 'home_b'].forEach(v => {
    const btn = document.getElementById(`v-btn-${v}`);
    if (btn) btn.classList.toggle('active', v === venueMode);
  });
  triggerRadarClash();
}

async function applyRadarPreset(lgA, tmA, lgB, tmB) {
  window._radarState.leagueA = lgA;
  window._radarState.teamA = tmA;
  window._radarState.leagueB = lgB;
  window._radarState.teamB = tmB;

  const selLgA = document.getElementById('radar-league-a');
  const selLgB = document.getElementById('radar-league-b');
  if (selLgA) selLgA.value = lgA;
  if (selLgB) selLgB.value = lgB;

  await Promise.all([populateTeamDropdown('A'), populateTeamDropdown('B')]);
  await triggerRadarClash();
}

function buildRadarSvgChart(teamA, teamB) {
  const axes = [
    { key: 'attack', label: 'الهجوم' },
    { key: 'finishing', label: 'الحسم' },
    { key: 'form', label: 'الفورمة' },
    { key: 'dominance', label: 'الهيمنة' },
    { key: 'defense', label: 'الدفاع' },
    { key: 'elo', label: 'القوة Elo' }
  ];

  const cx = 220, cy = 170, maxR = 104;
  const levels = [0.25, 0.5, 0.75, 1.0];

  const getPoint = (idx, ratio) => {
    const angle = (Math.PI * 2 * idx) / axes.length - Math.PI / 2;
    const x = cx + maxR * ratio * Math.cos(angle);
    const y = cy + maxR * ratio * Math.sin(angle);
    return { x: x.toFixed(1), y: y.toFixed(1) };
  };

  const gridPolygons = levels.map(lvl => {
    const pts = axes.map((_, i) => {
      const p = getPoint(i, lvl);
      return `${p.x},${p.y}`;
    }).join(' ');
    return `<polygon points="${pts}" fill="none" stroke="#1e2d4a" stroke-width="1" stroke-dasharray="${lvl === 1 ? 'none' : '3,3'}" />`;
  }).join('');

  const axisLinesAndLabels = axes.map((ax, i) => {
    const endP = getPoint(i, 1.0);
    const lblP = getPoint(i, 1.28);
    const valA = teamA.radar[ax.key] || 50;
    const valB = teamB.radar[ax.key] || 50;
    return `
      <line x1="${cx}" y1="${cy}" x2="${endP.x}" y2="${endP.y}" stroke="#1e2d4a" stroke-width="1" />
      <text x="${lblP.x}" y="${lblP.y}" fill="#e2e8f0" font-size="13" font-weight="800" text-anchor="middle" dominant-baseline="middle">
        ${ax.label}
      </text>
      <text x="${lblP.x}" y="${parseFloat(lblP.y) + 15}" fill="#8292b0" font-size="10.5" font-weight="700" text-anchor="middle">
        ${valA} - ${valB}
      </text>
    `;
  }).join('');

  const ptsA = axes.map((ax, i) => {
    const ratio = Math.max(0.15, Math.min(1.0, (teamA.radar[ax.key] || 50) / 100));
    const p = getPoint(i, ratio);
    return `${p.x},${p.y}`;
  }).join(' ');

  const dotsA = axes.map((ax, i) => {
    const ratio = Math.max(0.15, Math.min(1.0, (teamA.radar[ax.key] || 50) / 100));
    const p = getPoint(i, ratio);
    return `<circle cx="${p.x}" cy="${p.y}" r="4.5" fill="#00e676" stroke="#080c15" stroke-width="1.5" />`;
  }).join('');

  const ptsB = axes.map((ax, i) => {
    const ratio = Math.max(0.15, Math.min(1.0, (teamB.radar[ax.key] || 50) / 100));
    const p = getPoint(i, ratio);
    return `${p.x},${p.y}`;
  }).join(' ');

  const dotsB = axes.map((ax, i) => {
    const ratio = Math.max(0.15, Math.min(1.0, (teamB.radar[ax.key] || 50) / 100));
    const p = getPoint(i, ratio);
    return `<circle cx="${p.x}" cy="${p.y}" r="4.5" fill="#00d2ff" stroke="#080c15" stroke-width="1.5" />`;
  }).join('');

  return `
    <svg viewBox="0 0 440 345" class="radar-svg-chart">
      <defs>
        <filter id="glowA" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#00e676" flood-opacity="0.45"/>
        </filter>
        <filter id="glowB" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#00d2ff" flood-opacity="0.45"/>
        </filter>
      </defs>
      ${gridPolygons}
      ${axisLinesAndLabels}
      <polygon points="${ptsA}" fill="rgba(0, 230, 118, 0.24)" stroke="#00e676" stroke-width="2.5" filter="url(#glowA)" />
      <polygon points="${ptsB}" fill="rgba(0, 210, 255, 0.24)" stroke="#00d2ff" stroke-width="2.5" filter="url(#glowB)" />
      ${dotsA}
      ${dotsB}
    </svg>
  `;
}

async function triggerRadarClash() {
  const output = document.getElementById('radar-clash-output');
  const selLgA = document.getElementById('radar-league-a');
  const selTmA = document.getElementById('radar-team-a');
  const selLgB = document.getElementById('radar-league-b');
  const selTmB = document.getElementById('radar-team-b');
  if (!output || !selLgA || !selTmA || !selLgB || !selTmB) return;

  window._radarState.leagueA = selLgA.value;
  window._radarState.teamA = selTmA.value;
  window._radarState.leagueB = selLgB.value;
  window._radarState.teamB = selTmB.value;

  output.innerHTML = '<div class="loading-state">⚙️ جاري تشغيل محاكاة القمة وبناء المخطط السداسي...</div>';

  try {
    const res = await fetch('/api/radar_clash', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        league_a: window._radarState.leagueA,
        team_a_short: window._radarState.teamA,
        league_b: window._radarState.leagueB,
        team_b_short: window._radarState.teamB,
        venue: window._radarState.venue
      })
    });

    const data = await res.json();
    if (!data || data.status !== 'success') {
      output.innerHTML = `<div class="loading-state" style="color:var(--accent-red);">${data.message || 'تعذر إجراء المقارنة'}</div>`;
      return;
    }

    const a = data.team_a;
    const b = data.team_b;
    const sim = data.simulation;
    const svgChart = buildRadarSvgChart(a, b);

    const compareMetrics = [
      { label: '⚔️ القوة الهجومية', valA: a.radar.attack, valB: b.radar.attack },
      { label: '🛡️ الصلابة الدفاعية', valA: a.radar.defense, valB: b.radar.defense },
      { label: '🎯 الحسم التهديفي', valA: a.radar.finishing, valB: b.radar.finishing },
      { label: '🔥 الفورمة والزخم', valA: a.radar.form, valB: b.radar.form },
      { label: '👑 الهيمنة والاستقرار', valA: a.radar.dominance, valB: b.radar.dominance },
      { label: '⚡ مؤشر القوة (Elo)', valA: a.radar.elo, valB: b.radar.elo }
    ];

    const barsHtml = compareMetrics.map(m => {
      const total = Math.max(1, m.valA + m.valB);
      const pctA = Math.round((m.valA / total) * 100);
      const pctB = 100 - pctA;
      return `
        <div style="margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:800; margin-bottom:4px;">
            <span style="color:${m.valA >= m.valB ? 'var(--accent-green)' : '#cbd5e1'};">${m.valA}</span>
            <span style="color:var(--muted);">${m.label}</span>
            <span style="color:${m.valB >= m.valA ? 'var(--accent-cyan)' : '#cbd5e1'};">${m.valB}</span>
          </div>
          <div style="display:flex; height:7px; border-radius:4px; overflow:hidden; background:#090e18;">
            <div style="width:${pctA}%; background:var(--accent-green);"></div>
            <div style="width:${pctB}%; background:var(--accent-cyan);"></div>
          </div>
        </div>
      `;
    }).join('');

    output.innerHTML = `
      <div class="radar-matchup-banner">
        <div class="radar-club-box">
          <img src="${escapeHtml(a.crest)}" alt="${escapeHtml(a.short)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          <div class="radar-club-name" style="color:var(--accent-green);">${a.short}</div>
          <div class="radar-club-sub dp-inline-league-tag" style="justify-content:center;">${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(window._radarState.leagueA, a.league_flag, 'size-xs') : a.league_flag} <span>${escapeHtml(a.league_name)} • #${a.rank}</span></div>
          <div class="radar-overall-pill" style="border-color:var(--accent-green); color:var(--accent-green);">Overall: ${a.overall}</div>
        </div>

        <div class="radar-sim-center">
          <div style="font-size:0.76rem; color:var(--muted); margin-bottom:4px;">النتيجة المتوقعة إحصائياً</div>
          <div class="radar-predicted-score">${sim.predicted_score}</div>
          <div style="font-size:0.78rem; color:var(--accent-gold); font-weight:800; margin-top:4px;">
            xG: ${sim.xg_a} - ${sim.xg_b} (ثقة ${sim.score_prob}%)
          </div>
          <div style="display:flex; gap:10px; justify-content:center; margin-top:8px; font-size:0.74rem; color:#cbd5e1;">
            <span>Over 2.5: <strong style="color:var(--accent-green);">${sim.markets.over_25}%</strong></span>
            <span>•</span>
            <span>BTTS: <strong style="color:var(--accent-cyan);">${sim.markets.btts_yes}%</strong></span>
          </div>
        </div>

        <div class="radar-club-box">
         <img src="${escapeHtml(b.crest)}" alt="${escapeHtml(b.short)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          <div class="radar-club-name" style="color:var(--accent-cyan);">${b.short}</div>
          <div class="radar-club-sub dp-inline-league-tag" style="justify-content:center;">${typeof renderLeagueLogoHtml === 'function' ? renderLeagueLogoHtml(window._radarState.leagueB, b.league_flag, 'size-xs') : b.league_flag} <span>${escapeHtml(b.league_name)} • #${b.rank}</span></div>
          <div class="radar-overall-pill" style="border-color:var(--accent-cyan); color:var(--accent-cyan);">Overall: ${b.overall}</div>
        </div>
      </div>

      <div style="background:var(--surface-inset); padding:12px 16px; border-radius:12px; border:1px solid var(--card-border); margin-bottom:18px;">
        <div class="prob-bar" style="height:12px;">
          <div class="prob-home" style="width:${sim.prob_a}%; background:var(--accent-green);"></div>
          <div class="prob-draw" style="width:${sim.prob_draw}%; background:var(--accent-gold);"></div>
          <div class="prob-away" style="width:${sim.prob_b}%; background:var(--accent-cyan);"></div>
        </div>
        <div class="prob-labels" style="margin-bottom:0; font-size:0.82rem;">
          <span style="color:var(--accent-green);">فوز ${a.short}: <strong>${sim.prob_a}%</strong></span>
          <span style="color:var(--accent-gold);">التعادل: <strong>${sim.prob_draw}%</strong></span>
          <span style="color:var(--accent-cyan);">فوز ${b.short}: <strong>${sim.prob_b}%</strong></span>
        </div>
      </div>

      <div class="radar-main-split">
        <div class="data-card" style="margin:0; text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:center;">
          <h4 style="font-size:0.95rem; color:var(--text); margin-bottom:6px;">🕸️البصمة التكتيكية السداسية (DeepPitch Radar)</h4>
          <div style="display:flex; gap:16px; font-size:0.8rem; font-weight:800; margin-bottom:4px;">
            <span style="color:var(--accent-green);">🟢 ${a.short}</span>
            <span style="color:var(--accent-cyan);">🔵 ${b.short}</span>
          </div>
          ${svgChart}
        </div>

        <div class="data-card" style="margin:0; display:flex; flex-direction:column; justify-content:space-between;">
          <div>
            <h4 style="font-size:0.95rem; color:var(--accent-gold); margin-bottom:14px;">📊 المقارنة المحورية المباشرة (0 - 100)</h4>
            ${barsHtml}
          </div>

          <div style="background:var(--surface-inset); border:1px solid var(--card-border); border-right:3.5px solid var(--accent-gold); padding:12px; border-radius:10px; margin-top:12px; font-size:0.83rem; line-height:1.6; color:var(--text-secondary);">
            <div style="font-weight:800; color:var(--accent-gold-bright); margin-bottom:4px;">الخلاصة التكتيكية للمواجهة</div>
            <div>${escapeHtml(sim.tactical_summary).replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--text);">$1</strong>')}</div>
          </div>
        </div>
      </div>
    `;
  } catch (err) {
    output.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">حدث خطأ أثناء الاتصال بمحرك المقارنة الرادارية.</div>';
  }
}

// =========================================================
// 10. محرك منحنى الزخم الهجومي الحي وخريطة التسديدات (Attack Momentum Wave & Shot Map)
// =========================================================
function buildMomentumWaveSvg(points, markers, homeName, awayName, isProjected = false) {
  const width = 600, height = 195, midY = 98;
  const startX = 28, endX = 582;
  const plotW = endX - startX;
  const maxBarH = 74;

  const barsSvg = (points || []).map(pt => {
    const x = startX + ((pt.minute / 90) * plotW) - 4;
    if (!pt.active) {
      return `<rect x="${x.toFixed(1)}" y="${midY - 2}" width="7" height="4" rx="2" fill="#1e293b" opacity="0.4" />`;
    }
    const val = pt.value || 0;
    const h = Math.max(4, (Math.abs(val) / 100) * maxBarH);
    const isHome = val >= 0;
    const y = isHome ? (midY - h) : midY;
    const fillUrl = isHome ? 'url(#momGradHome)' : 'url(#momGradAway)';
    const strokeCol = isHome ? '#00e676' : '#00d2ff';
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="7.5" height="${h.toFixed(1)}" rx="2.5" fill="${fillUrl}" stroke="${strokeCol}" stroke-width="0.6" />`;
  }).join('');

  const markersSvg = (markers || []).map(mk => {
    const x = startX + ((mk.minute / 90) * plotW);
    const isHome = mk.side === 'home';
    const pinY = isHome ? 18 : (height - 18);
    const badgeCol = mk.type === 'goal' ? '#ffd600' : (mk.type === 'red_card' ? '#ff5252' : '#00e676');
    return `
      <g class="mom-marker-group">
        <line x1="${x.toFixed(1)}" y1="${midY}" x2="${x.toFixed(1)}" y2="${pinY}" stroke="${badgeCol}" stroke-width="1.4" stroke-dasharray="2,2" />
        <circle cx="${x.toFixed(1)}" cy="${pinY}" r="10" fill="#090e18" stroke="${badgeCol}" stroke-width="1.8" />
        <text x="${x.toFixed(1)}" y="${pinY + 1}" font-size="10" text-anchor="middle" dominant-baseline="middle">${mk.icon}</text>
        <title>${mk.real_clock} - ${mk.label}</title>
      </g>
    `;
  }).join('');

  const timeTicks = [15, 30, 45, 60, 75, 90].map(t => {
    const tx = startX + ((t / 90) * plotW);
    const isHT = t === 45;
    return `
      <line x1="${tx.toFixed(1)}" y1="12" x2="${tx.toFixed(1)}" y2="${height - 12}" stroke="${isHT ? '#ffd600' : '#1e293b'}" stroke-width="${isHT ? '1.3' : '0.8'}" stroke-dasharray="${isHT ? '4,3' : '2,3'}" opacity="${isHT ? '0.75' : '0.5'}" />
      <rect x="${tx - 14}" y="${midY - 8}" width="28" height="16" rx="4" fill="#090e18" stroke="${isHT ? '#ffd600' : '#1e293b'}" stroke-width="0.8" />
      <text x="${tx.toFixed(1)}" y="${midY + 1}" fill="${isHT ? '#ffd600' : '#94a3b8'}" font-size="9.5" font-weight="800" text-anchor="middle" dominant-baseline="middle">${isHT ? 'HT' : t + "'"}</text>
    `;
  }).join('');

  return `
    <svg viewBox="0 0 ${width} ${height}" class="momentum-wave-svg">
      <defs>
        <linearGradient id="momGradHome" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#00e676" stop-opacity="0.95"/>
          <stop offset="100%" stop-color="#00e676" stop-opacity="0.20"/>
        </linearGradient>
        <linearGradient id="momGradAway" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#00d2ff" stop-opacity="0.20"/>
          <stop offset="100%" stop-color="#00d2ff" stop-opacity="0.95"/>
        </linearGradient>
      </defs>
      <rect x="${startX}" y="10" width="${plotW}" height="${midY - 10}" fill="rgba(0, 230, 118, 0.03)" rx="6" />
      <rect x="${startX}" y="${midY}" width="${plotW}" height="${midY - 10}" fill="rgba(0, 210, 255, 0.03)" rx="6" />
      <line x1="${startX}" y1="${midY}" x2="${endX}" y2="${midY}" stroke="#334155" stroke-width="1.5" />
      ${barsSvg}
      ${timeTicks}
      ${markersSvg}
      <text x="22" y="32" fill="#00e676" font-size="10" font-weight="900" text-anchor="middle" writing-mode="tb">${(homeName || '').slice(0, 8)}</text>
      <text x="22" y="${height - 32}" fill="#00d2ff" font-size="10" font-weight="900" text-anchor="middle" writing-mode="tb">${(awayName || '').slice(0, 8)}</text>
    </svg>
  `;
}

function buildShotMapPitchSvg(shots, homeName, awayName) {
  const width = 560, height = 250;

  const circlesSvg = (shots || []).map(s => {
    const cx = 20 + ((s.x / 100) * (width - 40));
    const cy = 15 + ((s.y / 100) * (height - 30));
    const r = Math.max(5.5, Math.min(13, 4.5 + (s.xg * 18)));
    const isHome = s.side === 'home';
    const baseCol = isHome ? '#00e676' : '#00d2ff';

    if (s.type === 'goal') {
      return `
        <g>
          <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${(r + 3).toFixed(1)}" fill="rgba(255, 214, 0, 0.28)" />
          <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="#ffd600" stroke="#000" stroke-width="1.5" />
          <text x="${cx.toFixed(1)}" y="${(cy + 1).toFixed(1)}" font-size="8.5" text-anchor="middle" dominant-baseline="middle">⚽</text>
          <title>${s.label} (xG: ${s.xg})</title>
        </g>
      `;
    } else if (s.type === 'on_target') {
      return `
        <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="${baseCol}" fill-opacity="0.85" stroke="#080c15" stroke-width="1.3">
          <title>${s.label} (xG: ${s.xg})</title>
        </circle>
      `;
    } else {
      return `
        <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${r.toFixed(1)}" fill="rgba(15, 23, 42, 0.7)" stroke="${baseCol}" stroke-width="1.8" stroke-dasharray="2,1">
          <title>${s.label} (xG: ${s.xg})</title>
        </circle>
      `;
    }
  }).join('');

  return `
    <svg viewBox="0 0 ${width} ${height}" class="shotmap-pitch-svg">
      <rect x="10" y="8" width="${width - 20}" height="${height - 16}" rx="10" fill="#0a1929" stroke="#1e3a5f" stroke-width="2" />
      <line x1="${width / 2}" y1="8" x2="${width / 2}" y2="${height - 8}" stroke="#1e3a5f" stroke-width="1.5" />
      <circle cx="${width / 2}" cy="${height / 2}" r="34" fill="none" stroke="#1e3a5f" stroke-width="1.5" />
      <circle cx="${width / 2}" cy="${height / 2}" r="3" fill="#1e3a5f" />
      <rect x="10" y="55" width="72" height="140" fill="none" stroke="#1e3a5f" stroke-width="1.5" />
      <rect x="10" y="90" width="26" height="70" fill="none" stroke="#1e3a5f" stroke-width="1.2" />
      <rect x="${width - 82}" y="55" width="72" height="140" fill="none" stroke="#1e3a5f" stroke-width="1.5" />
      <rect x="${width - 36}" y="90" width="26" height="70" fill="none" stroke="#1e3a5f" stroke-width="1.2" />
      <text x="115" y="24" fill="#00e676" font-size="10.5" font-weight="800">🟢 هجوم ${homeName} ➔</text>
      <text x="${width - 115}" y="24" fill="#00d2ff" font-size="10.5" font-weight="800" text-anchor="end">⬅ هجوم ${awayName} 🔵</text>
      ${circlesSvg}
    </svg>
    <div class="shotmap-legend">
      <span><strong style="color:#ffd600;">⚽ دائرة ذهبية:</strong> هدف محقق</span>
      <span><strong style="color:#00e676;">● دائرة مصمتة:</strong> تسديدة على المرمى</span>
      <span><strong style="color:#94a3b8;">◯ دائرة مفرغة:</strong> خارج المرمى / دفاع</span>
      <span><strong style="color:#00d2ff;">حجم الدائرة:</strong> خطورة الفرصة (xG)</span>
    </div>
  `;
}

function switchMomentumSubTab(prefix, mode) {
  const wavePane = document.getElementById(`${prefix}-wave-pane`);
  const shotPane = document.getElementById(`${prefix}-shot-pane`);
  const btnWave = document.getElementById(`${prefix}-btn-wave`);
  const btnShot = document.getElementById(`${prefix}-btn-shot`);

  if (wavePane) wavePane.style.display = (mode === 'wave') ? 'block' : 'none';
  if (shotPane) shotPane.style.display = (mode === 'shot') ? 'block' : 'none';
  if (btnWave) btnWave.classList.toggle('active', mode === 'wave');
  if (btnShot) btnShot.classList.toggle('active', mode === 'shot');
}

function renderMomentumWidgetHtml(prefix, data) {
  const waveSvg = buildMomentumWaveSvg(data.points, data.markers, data.home_team, data.away_team, data.is_projected);
  const shotSvg = buildShotMapPitchSvg(data.shots_map, data.home_team, data.away_team);
  const badgeText = 'تقدير خوارزمي مبني على إحصائيات اللقاء';

  return `
    <div class="momentum-studio-box">
      <div class="momentum-box-header">
        <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
          <span style="font-size:1.05rem;">📈</span>
          <strong style="font-size:0.88rem; color:var(--text);">منحنى الزخم الهجومي وخريطة التسديدات</strong>
          <span class="hub-badge" style="color:var(--accent-gold-bright); border-color:var(--accent-gold); font-size:0.65rem;">${badgeText}</span>
        </div>
        <div class="momentum-sub-tabs">
          <button id="${escapeHtml(prefix)}-btn-wave" class="mom-tab-btn active" onclick="switchMomentumSubTab('${escapeHtml(prefix)}', 'wave')">🌊 موجة الزخم</button>
          <button id="${escapeHtml(prefix)}-btn-shot" class="mom-tab-btn" onclick="switchMomentumSubTab('${escapeHtml(prefix)}', 'shot')">🎯 خريطة التسديدات</button>
        </div>
      </div>

      <div class="momentum-kpis-grid">
        <div class="mom-kpi-item" style="border-right:3px solid var(--accent-green);">
          <div class="mom-kpi-lbl">هيمنة ${escapeHtml(data.home_team)}</div>
          <div class="mom-kpi-val" style="color:var(--accent-green);">${escapeHtml(data.home_dominance)}% <span style="font-size:0.7rem; color:var(--muted);">(${escapeHtml(data.peak_home_window)})</span></div>
        </div>
        <div class="mom-kpi-item" style="border-right:3px solid var(--accent-gold);">
          <div class="mom-kpi-lbl">مؤشر الخطورة الهجومية</div>
          <div class="mom-kpi-val" style="color:var(--accent-gold-bright);">${escapeHtml(data.threat_home)} <span style="color:var(--muted); font-size:0.72rem;">ضد</span> ${escapeHtml(data.threat_away)}</div>
        </div>
        <div class="mom-kpi-item" style="border-right:3px solid var(--accent-cyan);">
          <div class="mom-kpi-lbl">هيمنة ${escapeHtml(data.away_team)}</div>
          <div class="mom-kpi-val" style="color:var(--accent-cyan);">${escapeHtml(data.away_dominance)}% <span style="font-size:0.7rem; color:var(--muted);">(${escapeHtml(data.peak_away_window)})</span></div>
        </div>
      </div>

      <div id="${escapeHtml(prefix)}-wave-pane">${waveSvg}</div>
      <div id="${escapeHtml(prefix)}-shot-pane" style="display:none;">${shotSvg}</div>
    </div>
  `;
}

// =========================================================
// 11. محرك بورصة الانتقالات وتجديد العقود العالمي (Global Mercato & Contracts Hub)
// =========================================================
window.openSafeAccumulator = function() {
  if (typeof window.openAccaModal === 'function') window.openAccaModal();
};
window.openAiNewspaper = function() {
  if (typeof window.openNewspaperModal === 'function') window.openNewspaperModal();
};

window._mercatoState = {
  subPage: 'transfers', // 'transfers' (1: الانتقالات) | 'contracts' (2: تجديد العقود)
  filterRegion: 'ALL',  // ALL | europe | asia | africa | americas
  filterStatus: 'ALL',  // ALL | done | talks | rumor | failed | coach
  searchQuery: '',
  transfersList: [],
  contractsList: [],
  tickerNews: [],
  votesMap: {}
};

window._mercatoReqToken = 0;

async function loadMercatoHub(forceRefresh = false) {
  const container = document.getElementById('transfers-hub-container');
  if (!container) return;

  if (!forceRefresh && window._mercatoState.transfersList.length > 0) {
    renderMercatoWorkspace();
    return;
  }

  const reqToken = ++window._mercatoReqToken;
  container.innerHTML = '<div class="loading-state">✈️ جاري تحميل بورصة الانتقالات العالمية وسجلات تجديد العقود...</div>';

  try {
    const res = await fetch(`/api/mercato?refresh=${forceRefresh}`);
    const data = await res.json();
    if (reqToken !== window._mercatoReqToken) return;
    if (data && data.status === 'success') {
      window._mercatoState.transfersList = data.transfers || [];
      window._mercatoState.contractsList = data.contracts || [];
      window._mercatoState.tickerNews = data.ticker || [];
      renderMercatoWorkspace();
    } else {
      container.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">تعذر تحميل بيانات بورصة الانتقالات حالياً.</div>';
    }
  } catch (e) {
    if (reqToken === window._mercatoReqToken) {
      container.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">حدث خطأ في الاتصال بالسيرفر، يرجى المحاولة لاحقاً.</div>';
    }
  }
}

function switchMercatoSubPage(pageKey) {
  window._mercatoState.subPage = pageKey;
  window._mercatoState.filterStatus = 'ALL';
  renderMercatoWorkspace();
}

function setMercatoRegionFilter(regionKey) {
  window._mercatoState.filterRegion = regionKey;
  renderMercatoCardsGrid();
  document.querySelectorAll('.mercato-region-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-region') === regionKey);
  });
}

function setMercatoStatusFilter(statusKey) {
  window._mercatoState.filterStatus = statusKey;
  renderMercatoCardsGrid();
  document.querySelectorAll('.mercato-filter-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-filter') === statusKey);
  });
}

function onMercatoSearchInput(val) {
  window._mercatoState.searchQuery = (val || '').trim().toLowerCase();
  renderMercatoCardsGrid();
}

function renderMercatoWorkspace() {
  const container = document.getElementById('transfers-hub-container');
  if (!container) return;

  const st = window._mercatoState;
  const isTransfersPage = st.subPage === 'transfers';

  const tickerHtml = (st.tickerNews || []).map(item => `
    <span class="ticker-item">${escapeHtml(item)}</span>
  `).join('<span style="color:var(--accent-gold); margin:0 8px;">•</span>');

  const regionChips = [
    { key: 'ALL', label: '🌍 كل أندية العالم' },
    { key: 'europe', label: '🇪🇺 أوروبا الكبرى' },
    { key: 'asia', label: '🇸🇦 آسيا وروشن' },
    { key: 'africa', label: '🌍 أفريقيا والعرب' },
    { key: 'americas', label: '🌎 الأمريكيتين' }
  ];

  const filterChips = isTransfersPage
    ? [
        { key: 'ALL', label: 'الكل' },
        { key: 'done', label: '✅ تمت رسمياً' },
        { key: 'talks', label: '⏳ مفاوضات جارية' },
        { key: 'failed', label: '❌ صفقات فشلت' },
        { key: 'rumor', label: '📡 إشاعات' },
        { key: 'coach', label: '👔 مدربون' }
      ]
    : [
        { key: 'ALL', label: 'الكل' },
        { key: 'done', label: '✅ تم التجديد' },
        { key: 'talks', label: '⏳ مفاوضات التمديد' },
        { key: 'rumor', label: '⚠️ فترة حرة قريباً' },
        { key: 'failed', label: '❌ تعثر / رحيل' },
        { key: 'coach', label: '👔 مدربون' }
      ];

  container.innerHTML = `
    <!-- شريط برقيات الميركاتو العاجلة -->
    <div class="mercato-ticker-bar">
      <span class="ticker-badge">⚡ شريط الميركاتو العالمي</span>
      <div class="ticker-track-wrap">${tickerHtml}</div>
      <button onclick="loadMercatoHub(true)" class="retry-btn" style="padding:4px 12px; font-size:0.75rem; flex-shrink:0;">تحديث ↻</button>
    </div>

    <!-- التبديل بين الصفحتين الداخليتين: (1) الانتقالات | (2) تجديد العقود -->
    <div class="mercato-main-tabs">
      <div class="mercato-tab-btn ${isTransfersPage ? 'active-tab-transfers' : ''}" onclick="switchMercatoSubPage('transfers')">
        <div>
          <div class="mercato-tab-title">
            <span>✈️</span>
            <span>1. انتقالات اللاعبين والمدربين</span>
          </div>
          <div class="mercato-tab-sub">الصفقات الرسمية، الإعارات، المفاوضات الجارية، وأسباب فشل الصفقات في جميع الدوريات</div>
        </div>
        <span class="mercato-count-pill">${st.transfersList.length} صفقة</span>
      </div>

      <div class="mercato-tab-btn ${!isTransfersPage ? 'active-tab-contracts' : ''}" onclick="switchMercatoSubPage('contracts')">
        <div>
          <div class="mercato-tab-title">
            <span>✍️</span>
            <span>2. تجديد عقود اللاعبين والمدربين</span>
          </div>
          <div class="mercato-tab-sub">العقود المجددة، مفاوضات التمديد، تعديل الرواتب، واللاعبون في الفترة الحرة</div>
        </div>
        <span class="mercato-count-pill" style="color:var(--accent-cyan); border-color:rgba(0,210,255,0.35); background:rgba(0,210,255,0.12);">${st.contractsList.length} عقد</span>
      </div>
    </div>

    <!-- شريط الفلاتر المبسط (القارات + حالة الصفقة + البحث) -->
    <div class="mercato-filters-bar">
      <div style="display:flex; flex-direction:column; gap:10px; width:100%;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
          <div class="mercato-chips-group">
            ${regionChips.map(r => `
              <button class="mercato-region-chip ${st.filterRegion === r.key ? 'active' : ''}" data-region="${r.key}" onclick="setMercatoRegionFilter('${r.key}')">
                ${r.label}
              </button>
            `).join('')}
          </div>
          <input
            type="text"
            class="mercato-search-input"
            placeholder="🔍 ابحث باسم اللاعب، المدرب، أو النادي..."
          value="${escapeHtml(st.searchQuery)}"
            oninput="onMercatoSearchInput(this.value)"
          >
        </div>

        <div class="mercato-chips-group" style="border-top:1px solid rgba(255,255,255,0.06); padding-top:8px;">
          ${filterChips.map(c => `
            <button class="mercato-filter-chip ${st.filterStatus === c.key ? 'active' : ''}" data-filter="${c.key}" onclick="setMercatoStatusFilter('${c.key}')">
              ${c.label}
            </button>
          `).join('')}
        </div>
      </div>
    </div>

    <!-- شبكة الكروت العصرية المبسطة -->
    <div id="mercato-cards-grid-box" class="mercato-cards-grid"></div>
  `;

  renderMercatoCardsGrid();
}

function renderMercatoCardsGrid() {
  const gridBox = document.getElementById('mercato-cards-grid-box');
  if (!gridBox) return;

  const st = window._mercatoState;
  const isTransfersPage = st.subPage === 'transfers';
  const rawList = isTransfersPage ? st.transfersList : st.contractsList;

  const filtered = rawList.filter(item => {
    if (st.filterRegion !== 'ALL' && item.region !== st.filterRegion) return false;
    if (st.filterStatus === 'coach' && item.role !== 'coach') return false;
    if (st.filterStatus !== 'ALL' && st.filterStatus !== 'coach' && item.status !== st.filterStatus) return false;
    if (st.searchQuery) {
      const hay = `${item.name} ${item.from_club} ${item.to_club || ''} ${item.position} ${item.nationality || ''} ${item.league_tag || ''}`.toLowerCase();
      if (!hay.includes(st.searchQuery)) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    gridBox.innerHTML = '<div class="loading-state" style="grid-column:1/-1;">لا توجد صفقات مطابقة لهذا البحث حالياً — جرب اختيار "كل أندية العالم".</div>';
    return;
  }

  gridBox.innerHTML = filtered.map(item => {
    const isCoach = item.role === 'coach';
    const roleBadge = isCoach
      ? `<span class="m-role-pill role-coach">👔 مدرب</span>`
      : `<span class="m-role-pill role-player">⚽ لاعب</span>`;

    const statusMap = {
      'done':   { cls: 'status-done',   pillCls: 'pill-done',   reasonCls: 'reason-done',   arrowIcon: '⬅️' },
      'talks':  { cls: 'status-talks',  pillCls: 'pill-talks',  reasonCls: 'reason-talks',  arrowIcon: '⬅️' },
      'rumor':  { cls: 'status-rumor',  pillCls: 'pill-rumor',  reasonCls: 'reason-rumor',  arrowIcon: '⬅️' },
      'failed': { cls: 'status-failed', pillCls: 'pill-failed', reasonCls: 'reason-failed', arrowIcon: '✖️' }
    };
    const sMeta = statusMap[item.status] || statusMap['talks'];
    const safeId = escapeHtml(item.id);
    const pageKey = isTransfersPage ? 'transfers' : 'contracts';

    if (isTransfersPage) {
      const notePrefix = item.status === 'failed'
        ? '🚫 سبب فشل الصفقة:'
        : (item.status === 'done' ? '✅ تفاصيل الصفقة:' : '⏳ آخر التطورات:');

      return `
        <div class="transfer-card ${sMeta.cls}" data-mid="${safeId}" onclick="openMercatoDetailModal('${pageKey}', this.dataset.mid)">
          <div class="t-card-top">
            <div class="t-person-box">
              <div class="t-avatar-wrap">
                <img src="${escapeHtml(item.avatar)}" alt="${escapeHtml(item.name)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
              </div>
              <div style="min-width:0;">
                <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <span class="t-person-name">${escapeHtml(item.name)}</span>
                  ${roleBadge}
                </div>
                <div class="t-person-sub">${escapeHtml(item.position)} • ${item.age ? `${escapeHtml(item.age)} سنة • ` : ''}${escapeHtml(item.nationality)}</div>
              </div>
            </div>
            <span class="t-status-pill ${sMeta.pillCls}">${escapeHtml(item.status_label)}</span>
          </div>

          <div class="transfer-bridge-box">
            <div class="t-club-node">
              <div class="t-club-role-hint">النادي السابق</div>
              <img src="${escapeHtml(item.from_crest)}" alt="${escapeHtml(item.from_club)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
              <div class="t-club-name">${escapeHtml(item.from_club)}</div>
            </div>

            <div class="t-arrow-tunnel">
              <span class="t-deal-type-lbl">${escapeHtml(item.deal_type)}</span>
              <div class="t-animated-arrow ${item.status === 'failed' ? 'arrow-failed' : ''}">
                <span class="arrow-line"></span>
                <span class="arrow-head">${sMeta.arrowIcon}</span>
              </div>
              <span class="t-fee-lbl">${escapeHtml(item.fee)}</span>
            </div>

            <div class="t-club-node">
              <div class="t-club-role-hint" style="color:var(--accent-cyan);">النادي الجديد</div>
              <img src="${escapeHtml(item.to_crest)}" alt="${escapeHtml(item.to_club)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
              <div class="t-club-name" style="color:var(--text);">${escapeHtml(item.to_club)}</div>
            </div>
          </div>

          <div class="t-terms-grid">
            <div class="t-term-item">
              <span class="t-term-lbl">📅 مدة العقد</span>
              <span class="t-term-val">${escapeHtml(item.contract_length)}</span>
            </div>
            <div class="t-term-item">
              <span class="t-term-lbl">💰 الراتب</span>
              <span class="t-term-val" style="color:var(--accent-green);">${escapeHtml(item.salary)}</span>
            </div>
          </div>

          <div class="t-reason-banner ${sMeta.reasonCls}">
            <strong>${notePrefix}</strong> ${escapeHtml(item.status_reason)}
          </div>

          <div class="t-card-footer">
            <span class="t-league-chip">${escapeHtml(item.league_tag || '🌍 ميركاتو عالمي')}</span>
            <span class="t-more-hint">التفاصيل والشروط ⬅️</span>
          </div>
        </div>
      `;
    } else {
      const notePrefix = item.status === 'failed'
        ? '🚫 سبب تعثر التجديد:'
        : (item.status === 'done' ? '✍️ بنود التجديد:' : '⏳ موقف التجديد:');

      return `
        <div class="transfer-card ${sMeta.cls}" data-mid="${safeId}" onclick="openMercatoDetailModal('${pageKey}', this.dataset.mid)">
          <div class="t-card-top">
            <div class="t-person-box">
              <div class="t-avatar-wrap">
                <img src="${escapeHtml(item.avatar)}" alt="${escapeHtml(item.name)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
              </div>
              <div style="min-width:0;">
                <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <span class="t-person-name">${escapeHtml(item.name)}</span>
                  ${roleBadge}
                </div>
                <div class="t-person-sub">${escapeHtml(item.position)} • ${item.age ? `${escapeHtml(item.age)} سنة • ` : ''}${escapeHtml(item.nationality)}</div>
              </div>
            </div>
            <span class="t-status-pill ${sMeta.pillCls}">${escapeHtml(item.status_label)}</span>
          </div>

          <div class="renewal-showcase-box">
            <div class="renewal-club-side">
              <img src="${escapeHtml(item.from_crest)}" alt="${escapeHtml(item.from_club)}" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
              <div>
                <div style="font-size:0.7rem; color:var(--muted); font-weight:700;">النادي الحالي</div>
                <div style="font-size:0.92rem; font-weight:900; color:var(--text);">${escapeHtml(item.from_club)}</div>
              </div>
            </div>

            <div class="renewal-timeline-side">
              <div class="renewal-dates-row">
                <span class="old-date-tag">${escapeHtml(item.old_expiry)}</span>
                <span style="color:var(--accent-cyan); font-weight:900;">⬅️</span>
                <span class="new-date-tag ${item.status === 'failed' ? 'date-failed' : ''}">${escapeHtml(item.new_expiry)}</span>
              </div>
              <div style="font-size:0.73rem; color:var(--accent-gold-bright); font-weight:800; margin-top:4px;">
                ${escapeHtml(item.contract_length)}
              </div>
            </div>
          </div>

          <div class="t-terms-grid">
            <div class="t-term-item">
              <span class="t-term-lbl">💵 الراتب</span>
              <span class="t-term-val" style="color:var(--accent-green);">${escapeHtml(item.salary)}</span>
            </div>
            <div class="t-term-item">
              <span class="t-term-lbl">🔒 الشرط الجزائي</span>
              <span class="t-term-val" style="color:var(--accent-gold-bright);">${escapeHtml(item.release_clause)}</span>
            </div>
          </div>

          <div class="t-reason-banner ${sMeta.reasonCls}">
            <strong>${notePrefix}</strong> ${escapeHtml(item.status_reason)}
          </div>

          <div class="t-card-footer">
            <span class="t-league-chip">${escapeHtml(item.league_tag || '🌍 عقود عالمية')}</span>
            <span style="font-size:0.74rem; font-weight:800; color:${(item.salary_change || '').includes('⬇️') ? 'var(--accent-red)' : 'var(--accent-green)'};">
              ${escapeHtml(item.salary_change)}
            </span>
          </div>
        </div>
      `;
    }
  }).join('');
}

function openMercatoDetailModal(pageType, itemId) {
  const modal = document.getElementById('mercato-detail-modal');
  const body = document.getElementById('mercato-modal-body');
  if (!modal || !body) return;

  const list = pageType === 'transfers' ? window._mercatoState.transfersList : window._mercatoState.contractsList;
  const item = list.find(x => String(x.id) === String(itemId));
  if (!item) return;

  const savedVotes = getSavedMercatoVotes();
  const votes = savedVotes[item.id] || window._mercatoState.votesMap[item.id] || { up: item.likes || 142, down: item.dislikes || 19, userVote: null };
  const totalV = Math.max(1, votes.up + votes.down);
  const upPct = Math.round((votes.up / totalV) * 100);
  const safeId = escapeHtml(item.id);
  const safePage = escapeHtml(pageType);

  body.innerHTML = `
    <div style="display:flex; align-items:center; gap:14px; border-bottom:1px solid var(--card-border); padding-bottom:14px; margin-bottom:16px; padding-left:42px;">
      <img src="${escapeHtml(item.avatar)}" width="64" height="64" style="border-radius:50%; object-fit:cover; border:2px solid var(--accent-cyan); background:var(--surface-inset);" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
      <div style="flex:1;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">
          <h3 style="font-size:1.2rem; font-weight:900; color:var(--text);">${escapeHtml(item.name)}</h3>
          <span class="hub-badge" style="color:var(--accent-gold-bright); border-color:var(--accent-gold);">${escapeHtml(item.status_label)}</span>
        </div>
        <div style="font-size:0.82rem; color:var(--muted); margin-top:4px;">
          ${item.role === 'coach' ? '👔 مدير فني' : '⚽ لاعب'} • ${escapeHtml(item.position)}${item.age ? ` • ${escapeHtml(item.age)} سنة` : ''} • ${escapeHtml(item.nationality)}
        </div>
      </div>
    </div>

    ${pageType === 'transfers' ? `
      <div class="transfer-bridge-box" style="margin-bottom:16px; padding:14px;">
        <div class="t-club-node">
          <div class="t-club-role-hint">من نادي</div>
          <img src="${escapeHtml(item.from_crest)}" width="44" height="44" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          <div class="t-club-name" style="font-size:0.9rem;">${escapeHtml(item.from_club)}</div>
        </div>
        <div class="t-arrow-tunnel">
          <span class="t-deal-type-lbl" style="font-size:0.78rem;">${escapeHtml(item.deal_type)}</span>
          <div style="font-size:1.3rem; margin:4px 0;">${item.status === 'failed' ? '✖️' : '⬅️'}</div>
          <span class="t-fee-lbl" style="font-size:0.82rem; color:var(--accent-gold-bright);">${escapeHtml(item.fee)}</span>
        </div>
        <div class="t-club-node">
          <div class="t-club-role-hint" style="color:var(--accent-cyan);">إلى نادي</div>
          <img src="${escapeHtml(item.to_crest)}" width="44" height="44" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          <div class="t-club-name" style="font-size:0.9rem; color:var(--text);">${escapeHtml(item.to_club)}</div>
        </div>
      </div>
    ` : `
      <div class="renewal-showcase-box" style="margin-bottom:16px; padding:14px;">
        <div class="renewal-club-side">
          <img src="${escapeHtml(item.from_crest)}" width="42" height="42" onerror="this.onerror=null; this.src=window.DEFAULT_CLUB_CREST;">
          <div>
            <div style="font-size:0.75rem; color:var(--muted);">نادي التجديد</div>
            <div style="font-size:1rem; font-weight:900; color:var(--text);">${escapeHtml(item.from_club)}</div>
          </div>
        </div>
        <div class="renewal-timeline-side">
          <div class="renewal-dates-row">
            <span class="old-date-tag">${escapeHtml(item.old_expiry)}</span>
            <span>⬅️</span>
            <span class="new-date-tag ${item.status === 'failed' ? 'date-failed' : ''}">${escapeHtml(item.new_expiry)}</span>
          </div>
          <div style="font-size:0.78rem; color:var(--accent-gold-bright); font-weight:800; margin-top:4px;">${escapeHtml(item.contract_length)}</div>
        </div>
      </div>
    `}

    <div class="dp-modal-panel" style="margin-bottom:14px;">
      <div style="font-weight:900; color:var(--accent-cyan); margin-bottom:10px; font-size:0.9rem;">📋 البنود المالية والتعاقدية الكاملة:</div>
      <div class="t-terms-grid" style="margin-bottom:10px;">
        <div class="t-term-item">
          <span class="t-term-lbl">${pageType === 'transfers' ? '💵 قيمة الصفقة' : '📈 تعديل الراتب'}</span>
          <span class="t-term-val" style="color:var(--accent-green);">${escapeHtml(pageType === 'transfers' ? item.fee : item.salary_change)}</span>
        </div>
        <div class="t-term-item">
          <span class="t-term-lbl">💰 الراتب السنوي</span>
          <span class="t-term-val">${escapeHtml(item.salary)}</span>
        </div>
        <div class="t-term-item">
          <span class="t-term-lbl">📅 مدة العقد</span>
          <span class="t-term-val">${escapeHtml(item.contract_length)}</span>
        </div>
        <div class="t-term-item">
          <span class="t-term-lbl">🔒 الشرط الجزائي</span>
          <span class="t-term-val" style="color:var(--accent-gold-bright);">${escapeHtml(item.release_clause || 'غير معلن')}</span>
        </div>
      </div>
      <div class="dp-modal-subpanel">
        <strong style="color:var(--text);">📌 الشروط والامتيازات:</strong> ${escapeHtml(item.conditions)}
      </div>
    </div>

    <div class="dp-modal-panel" style="border-right:4px solid ${item.status === 'failed' ? 'var(--accent-red)' : 'var(--accent-gold)'}; margin-bottom:16px; font-size:0.85rem; line-height:1.65; color:var(--text-secondary);">
      <div style="font-weight:900; color:${item.status === 'failed' ? 'var(--accent-red)' : 'var(--accent-gold-bright)'}; margin-bottom:4px;">
        ${item.status === 'failed' ? '🚫 سبب فشل وتعثر المفاوضات:' : '🕵️‍♂️ كواليس الصفقة والتفاصيل:'}
      </div>
      <div>${escapeHtml(item.status_reason)}</div>
      <div style="font-size:0.74rem; color:var(--muted); margin-top:6px;">📡 المصدر: <strong style="color:var(--text);">${escapeHtml(item.source)}</strong> (موثوقية ${escapeHtml(item.reliability)}%)</div>
    </div>

    <div class="dp-modal-panel">
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:800; margin-bottom:8px;">
        <span>📊 تصويت زوار المنصة على الصفقة:</span>
        <span id="mercato-vote-pct" style="color:var(--accent-green);">${upPct}% يؤيدون الخطوة</span>
      </div>
      <div class="vote-btn-group">
        <button id="mercato-vote-up-btn" type="button" class="mercato-vote-btn ${votes.userVote === 'up' ? 'is-voted-up' : ''}" data-mid="${safeId}" data-pt="${safePage}" onclick="voteMercatoItem(this.dataset.mid, 'up', this.dataset.pt)">🔥 صفقة رابحة (${votes.up})</button>
        <button id="mercato-vote-down-btn" type="button" class="mercato-vote-btn ${votes.userVote === 'down' ? 'is-voted-down' : ''}" data-mid="${safeId}" data-pt="${safePage}" onclick="voteMercatoItem(this.dataset.mid, 'down', this.dataset.pt)">👎 غير موفقة (${votes.down})</button>
      </div>
    </div>
  `;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function getSavedMercatoVotes() {
  try {
    return JSON.parse(localStorage.getItem('deeppitch_mercato_votes_v1') || '{}');
  } catch (e) {
    return {};
  }
}

function voteMercatoItem(itemId, dir, pageType) {
  const list = pageType === 'transfers' ? window._mercatoState.transfersList : window._mercatoState.contractsList;
  const item = list.find(x => String(x.id) === String(itemId));
  if (!item) return;

  const saved = getSavedMercatoVotes();
  const entry = saved[itemId] || { up: item.likes || 142, down: item.dislikes || 19, userVote: null };

  if (entry.userVote === dir) return; // منع التكرار لنفس الخيار
  if (entry.userVote === 'up') entry.up = Math.max(0, entry.up - 1);
  if (entry.userVote === 'down') entry.down = Math.max(0, entry.down - 1);

  if (dir === 'up') entry.up += 1;
  else entry.down += 1;
  entry.userVote = dir;

  saved[itemId] = entry;
  window._mercatoState.votesMap[itemId] = entry;
  try { localStorage.setItem('deeppitch_mercato_votes_v1', JSON.stringify(saved)); } catch (e) {}

const totalV = Math.max(1, entry.up + entry.down);
  const upPct = Math.round((entry.up / totalV) * 100);
  const pctEl = document.getElementById('mercato-vote-pct');
  const upBtn = document.getElementById('mercato-vote-up-btn');
  const downBtn = document.getElementById('mercato-vote-down-btn');

  if (pctEl) pctEl.textContent = `${upPct}% يؤيدون الخطوة`;
  if (upBtn) {
    upBtn.textContent = `🔥 صفقة رابحة (${entry.up})`;
    upBtn.classList.toggle('is-voted-up', entry.userVote === 'up');
  }
  if (downBtn) {
    downBtn.textContent = `👎 غير موفقة (${entry.down})`;
    downBtn.classList.toggle('is-voted-down', entry.userVote === 'down');
  }
}

// =========================================================
// 12. استوديو المسابقات الكروي المتكامل (DeepPitch Quiz Arena v6.0 - Instant Answer + Compact Horizontal Scroll)
// =========================================================
window._quizState = {
  phase: 'lobby',          // 'lobby' | 'playing' | 'summary'
  pool: [],
  totalPoolCount: 0,
  categoryCounts: {},
  aiAvailable: true,
  fallbackNotice: '',
  activeQueue: [],
  currentIndex: 0,
  score: 0,
  streak: 0,
  bestStreakInRound: 0,
  roundCorrect: 0,
  roundAnswered: 0,
  speedBonusCount: 0,
  lives: 3,
  gameMode: 'solo',        // 'solo' | 'ai_bot' | 'survival' | 'friend_code'
  botDifficulty: 'tactician',
  botScore: 0,
  botCorrect: 0,
  botLastAction: 'جاهز للمنافسة...',
  challengeSeed: '',
  useAiGenerator: false,
  filterCategory: 'ALL',
  filterRegion: 'ALL',
  filterLeague: 'ALL',
  filterDiff: 'ALL',
  sessionLength: 10,
  soundEnabled: true,
  blurLevel: 14,
  clueStage: 1,
  rankSelection: [],
  historyLog: [],
  answeredCurrent: false,
  lifelines: { fifty: 2, hint: 2, freeze: 2 },
  usedLifelinesThisQ: { fifty: false, hint: false, freeze: false },
  timerSec: 20,
  timerMax: 20,
  questionStartTs: 0,
  timerInterval: null,
  blitzFound: [],
  profile: JSON.parse(localStorage.getItem('deeppitch_quiz_profile') || '{"highScore":0,"totalPoints":0,"correctCount":0,"answeredCount":0}')
};

const QUIZ_CATEGORIES_META = {
  'ALL':              { icon: '🌟', name: 'شامل (كل الفئات)', sub: 'توليفة عالمية متنوعة' },
  'trivia':           { icon: '🧠', name: 'معلومات وتاريخ الدوريات', sub: 'أبطال المواسم والسجل الذهبي' },
  'true_false':       { icon: '⚡', name: 'صح أم خطأ', sub: 'تحدي سرعة الحقائق الحية' },
  'visual':           { icon: '🔍', name: 'الشعار المغبش', sub: 'شعارات الأندية الرسمية' },
  'nations_cups':     { icon: '🌍', name: 'كأس العالم والمنتخبات', sub: 'المونديال والبطولات القارية' },
  'awards_scorers':   { icon: '🌕', name: 'سباق الهدافين والتاريخ', sub: 'هدافو المواسم والحاليون' },
  'finals_remontada': { icon: '🏆', name: 'النهائيات الكبرى', sub: 'نتائج وأطراف النهائيات' },
  'who_am_i':         { icon: '🕵️‍♂️', name: 'من أنا؟ (3 أدلة)', sub: 'اكتشف النادي أو الهداف' },
  'stats':            { icon: '📊', name: 'أعلى أم أقل', sub: 'مقارنات الأرقام الحية' },
  'tactics':          { icon: '📋', name: 'الترتيب التكتيكي', sub: 'رتب الأندية تنازلياً بالنقاط' },
  'jersey_numbers':   { icon: '👕', name: 'أرقام القمصان', sub: 'أرقام نجوم الأندية الحية' },
  'club_career':      { icon: '✈️', name: 'مسار الميركاتو بالشعارات', sub: 'شعارات انتقالات اللاعبين' },
  'coaches_tactics':  { icon: '👔', name: 'عباقرة الدكة والمدربون', sub: 'المدربون التاريخيون والحاليون' },
  'derbies_stadiums': { icon: '🔥', name: 'مواجهات وأرقام قياسية', sub: 'قمم الجولة وأكبر النتائج' },
  'blitz':            { icon: '⏱️', name: 'تحدي الـ 30 ثانية', sub: 'اكتب أكبر عدد من الأندية' }
};

function injectQuizHorizontalScrollStyles() {
  // جميع تنسيقات ساحة التحدي موحّدة رسمياً في ملف style.css لدعم الوضعين الليلي والنهاري
}

function saveQuizProfile() {
  try {
    localStorage.setItem('deeppitch_quiz_profile', JSON.stringify(window._quizState.profile));
  } catch (e) {}
}

function getSeenQuizIds() {
  try {
    return JSON.parse(localStorage.getItem('deeppitch_seen_qids') || '[]');
  } catch (e) {
    return [];
  }
}

function markQuizQuestionSeen(qid) {
  if (!qid) return;
  try {
    const seen = getSeenQuizIds();
    if (!seen.includes(qid)) {
      seen.push(qid);
      if (seen.length > 1500) seen.shift();
      localStorage.setItem('deeppitch_seen_qids', JSON.stringify(seen));
    }
  } catch (e) {}
}

function createSeededRng(seedStr) {
  let h = 2166136261 >>> 0;
  const s = String(seedStr || Date.now());
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return function() {
    h += h << 13; h ^= h >>> 7;
    h += h << 3;  h ^= h >>> 17;
    h += h << 5;
    return (h >>> 0) / 4294967296;
  };
}

function shuffleQuizArray(arr, seedStr = '') {
  const copy = [...(arr || [])];
  const rng = seedStr ? createSeededRng(seedStr) : Math.random;
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function computePlayerLevel500(totalPoints) {
  let pts = Math.max(0, Math.floor(totalPoints || 0));
  let level = 1;
  let reqForNext = 4;
  while (level < 500) {
    reqForNext = 2 + (level * 2);
    if (pts >= reqForNext) {
      pts -= reqForNext;
      level += 1;
    } else {
      break;
    }
  }
  let rankTitle = '🥉 مبتدئ الملاعب';
  let rankColor = '#cbd5e1';
  if (level >= 500) { rankTitle = '👑 أسطورة الـ 500'; rankColor = '#ffd600'; }
  else if (level >= 350) { rankTitle = '🏆 أيقونة تاريخية'; rankColor = '#ffd600'; }
  else if (level >= 200) { rankTitle = '🔥 مايسترو التكتيك'; rankColor = '#ff9100'; }
  else if (level >= 100) { rankTitle = '💎 بروفيسور الكرة'; rankColor = '#a855f7'; }
  else if (level >= 50)  { rankTitle = '🥇 كشاف محترف'; rankColor = '#00e676'; }
  else if (level >= 20)  { rankTitle = '🥈 محلل معتمد'; rankColor = '#00d2ff'; }
  else if (level >= 5)   { rankTitle = '⚡ نجم صاعد بقوة'; rankColor = '#38bdf8'; }

  const pct = level >= 500 ? 100 : Math.min(100, Math.round((pts / Math.max(1, reqForNext)) * 100));
  return {
    level, maxLevel: 500, title: rankTitle, color: rankColor,
    curLevelPts: pts, reqForNext, remainingPts: Math.max(0, reqForNext - pts), progressPct: pct
  };
}

function playQuizSound(effectType) {
  if (!window._quizState.soundEnabled) return;
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    if (!window._quizAudioCtx) window._quizAudioCtx = new AudioCtx();
    const ctx = window._quizAudioCtx;
    if (ctx.state === 'suspended') ctx.resume();
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    if (effectType === 'levelup') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.09);
      osc.frequency.setValueAtTime(783.99, now + 0.18);
      osc.frequency.setValueAtTime(1046.50, now + 0.28);
      gain.gain.setValueAtTime(0.14, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
      osc.start(now);
      osc.stop(now + 0.6);
    } else if (effectType === 'correct') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.08);
      osc.frequency.setValueAtTime(783.99, now + 0.16);
      gain.gain.setValueAtTime(0.11, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
      osc.start(now);
      osc.stop(now + 0.3);
    } else if (effectType === 'wrong') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.linearRampToValueAtTime(130, now + 0.25);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
      osc.start(now);
      osc.stop(now + 0.28);
    }
  } catch (e) {}
}

function triggerLevelUpCelebration(oldLvl, newLvl) {
  playQuizSound('levelup');
  const existing = document.getElementById('quiz-levelup-toast');
  if (existing) existing.remove();
  const lvlInfo = computePlayerLevel500(window._quizState.profile.totalPoints);
  const toast = document.createElement('div');
  toast.id = 'quiz-levelup-toast';
  toast.className = 'levelup-celebration-toast';
  toast.innerHTML = `
    <div style="font-size:1.1rem; font-weight:900; color:#ffd600;">🎉 ترقية للمستوى ${newLvl} / 500!</div>
    <div style="font-size:0.8rem; color:#fff; margin-top:4px;">الرتبة: <span style="color:${lvlInfo.color};">${lvlInfo.title}</span></div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => { if (toast && toast.parentNode) toast.remove(); }, 2600);
}

function stopQuizTimer() {
  const st = window._quizState;
  if (st.timerInterval) {
    clearInterval(st.timerInterval);
    st.timerInterval = null;
  }
}

async function fetchQuizBankFromBackend() {
  const st = window._quizState;
  const seedParam = st.gameMode === 'friend_code' ? st.challengeSeed : '';
  const url = `/api/quiz_bank?league=${encodeURIComponent(st.filterLeague)}&difficulty=${encodeURIComponent(st.filterDiff)}&region=${encodeURIComponent(st.filterRegion)}&category=${encodeURIComponent(st.filterCategory)}&seed=${encodeURIComponent(seedParam)}&use_ai=${st.useAiGenerator}&count=200&_t=${Date.now()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

window.loadQuizArena = async function(forceReload = false) {
  injectQuizHorizontalScrollStyles();
  const container = document.getElementById('quiz-arena-container');
  if (!container) return;

  const st = window._quizState;
  stopQuizTimer();
  st.phase = 'lobby';
  st.fallbackNotice = '';

  if (!forceReload && Array.isArray(st.pool) && st.pool.length > 20) {
    renderQuizArenaWorkspace();
    return;
  }

  container.innerHTML = '<div class="loading-state">🌐 جاري سحب وتجهيز بنك الأسئلة الحي...</div>';

  try {
    const data = await fetchQuizBankFromBackend();
    if (data && data.status === 'success' && Array.isArray(data.questions)) {
      st.pool = data.questions;
      st.totalPoolCount = data.total_pool_size || data.questions.length;
      st.categoryCounts = data.category_counts || {};
      st.aiAvailable = data.ai_available !== false;
      if (!st.challengeSeed && data.seed_code) st.challengeSeed = data.seed_code;
    }
  } catch (e) {
    console.error('Live Quiz API Error:', e);
  }

  if (!st.challengeSeed) {
    st.challengeSeed = `DP-${Math.floor(1000 + Math.random() * 9000)}`;
  }

  renderQuizArenaWorkspace();
};

function renderLicenseBannerHtml() {
  const st = window._quizState;
  const prof = st.profile;
  const lvlObj = computePlayerLevel500(prof.totalPoints);
  const accuracy = prof.answeredCount > 0 ? Math.round((prof.correctCount / prof.answeredCount) * 100) : 100;

  return `
    <div id="quiz-top-license-banner" class="quiz-license-banner" style="padding:10px 14px; margin-bottom:12px;">
      <div class="license-left">
        <div class="level-shield-box" style="width:50px; height:54px;">
          <div class="level-shield-lbl">LEVEL</div>
          <div class="level-shield-num" style="font-size:1.1rem;">${lvlObj.level}</div>
          <div class="level-shield-max">/ 500</div>
        </div>
        <div style="flex:1; min-width:0;">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
            <span style="font-size:0.86rem; font-weight:900; color:${lvlObj.color}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${lvlObj.title}</span>
            <button class="quiz-sound-pill ${!st.soundEnabled ? 'muted' : ''}" onclick="window._quizState.soundEnabled=!window._quizState.soundEnabled; refreshLiveLicenseBannerUI();">
              ${st.soundEnabled ? '🔊 الصوت' : '🔇 صامت'}
            </button>
          </div>
          <div class="xp-bar-container" style="height:6px; margin-top:4px;">
            <div class="xp-bar-fill" style="width:${lvlObj.progressPct}%; background:linear-gradient(90deg, ${lvlObj.color}, #00e676);"></div>
          </div>
          <div style="display:flex; justify-content:space-between; font-size:0.66rem; color:#94a3b8; margin-top:3px;">
            <span>تقدم المستوى ${Math.min(500, lvlObj.level + 1)}: <strong style="color:#fff;">${lvlObj.curLevelPts}/${lvlObj.reqForNext}</strong></span>
            <span style="color:var(--accent-cyan); font-weight:800;">باقي ${lvlObj.remainingPts} نقطة ⚡</span>
          </div>
        </div>
      </div>

      <div class="license-stats-grid">
        <div class="lic-stat-box" style="padding:5px 10px; min-width:70px;">
          <div class="lic-val" style="font-size:0.95rem; color:var(--accent-green);">${prof.totalPoints}</div>
          <div class="lic-lbl">النقاط ⭐</div>
        </div>
        <div class="lic-stat-box" style="padding:5px 10px; min-width:70px;">
          <div class="lic-val" style="font-size:0.95rem; color:var(--accent-cyan);">${accuracy}%</div>
          <div class="lic-lbl">الدقة 🎯</div>
        </div>
      </div>
    </div>
  `;
}

window.refreshLiveLicenseBannerUI = function() {
  const wrap = document.getElementById('quiz-license-banner-wrap');
  if (wrap) wrap.innerHTML = renderLicenseBannerHtml();
};

window.setQuizLobbyParam = function(key, val) {
  const st = window._quizState;
  st[key] = val;
  if (key === 'filterLeague' && val !== 'ALL') {
    st.filterRegion = 'ALL';
  } else if (key === 'filterRegion' && val !== 'ALL') {
    st.filterLeague = 'ALL';
  }
  if (key === 'useAiGenerator' && val === true && st.aiAvailable === false) {
    st.fallbackNotice = '⚠️ تنبيه: مفتاح Gemini AI غير مضبوط على السيرفر حالياً، سيتم استخدام بنك الأسئلة الحية.';
  } else {
    st.fallbackNotice = '';
  }
  renderQuizArenaWorkspace();
};

function renderQuizArenaWorkspace() {
  injectQuizHorizontalScrollStyles();
  const container = document.getElementById('quiz-arena-container');
  if (!container) return;

  const st = window._quizState;
  stopQuizTimer();

  if (st.phase === 'lobby') {
    renderCleanQuizLobby(container);
  } else if (st.phase === 'playing') {
    container.innerHTML = `<div id="quiz-license-banner-wrap">${renderLicenseBannerHtml()}</div><div id="quiz-stage-box"></div>`;
    renderCurrentQuizQuestion();
  } else if (st.phase === 'summary') {
    container.innerHTML = `<div id="quiz-license-banner-wrap">${renderLicenseBannerHtml()}</div><div id="quiz-stage-box"></div>`;
    renderQuizPostMatchSummary();
  }
}

window._quizAdvancedOpen = false;

window.toggleQuizAdvancedFilters = function() {
  window._quizAdvancedOpen = !window._quizAdvancedOpen;
  renderQuizArenaWorkspace();
};

function renderCleanQuizLobby(container) {
  const st = window._quizState;
  const catCountNow = st.filterCategory === 'ALL'
    ? (st.totalPoolCount || st.pool.length)
    : ((st.categoryCounts && st.categoryCounts[st.filterCategory.toLowerCase()]) || 0);

  const modes = [
    { key: 'solo', icon: '🎯', title: 'طور فردي' },
    { key: 'ai_bot', icon: '🤖', title: 'تحدي البوت' },
    { key: 'survival', icon: '❤️', title: 'طور النجاة' },
    { key: 'friend_code', icon: '🔗', title: 'تحدي صديق' }
  ];

  const regions = [
    { key: 'ALL', label: '🌍 كل القارات' },
    { key: 'europe', label: '🇪🇺 أوروبا' },
    { key: 'americas', label: '🌎 الأمريكيتين' },
    { key: 'africa', label: '🌍 أفريقيا' },
    { key: 'asia', label: '🌏 آسيا' }
  ];

  const leagues = [
    { key: 'ALL', label: 'كل البطولات' },
    { key: 'UCL', label: 'أبطال أوروبا' },
    { key: 'PL', label: 'البريميرليغ' },
    { key: 'PD', label: 'الليغا' },
    { key: 'SA', label: 'الكالتشيو' },
    { key: 'BL1', label: 'البوندسليغا' },
    { key: 'FL1', label: 'الفرنسي' },
    { key: 'ACL', label: 'نخبة آسيا' },
    { key: 'CAF', label: 'أبطال أفريقيا' },
    { key: 'UNL', label: 'المنتخبات' }
  ];

  const advSummary = `${st.sessionLength} سؤال • ${st.filterDiff === 'ALL' ? 'كل المستويات' : st.filterDiff} • ${st.filterLeague !== 'ALL' ? st.filterLeague : (st.filterRegion !== 'ALL' ? st.filterRegion : 'عالمي')}`;

  container.innerHTML = `
    <div id="quiz-license-banner-wrap">${renderLicenseBannerHtml()}</div>

    <div class="quiz-lobby-card">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid var(--card-border);">
        <div>
          <h3 style="font-size:1.05rem; font-weight:800; margin:0;">ساحة التحدي الكروي</h3>
          <div style="font-size:0.74rem; color:var(--muted);">
            متاح حالياً: <strong style="color:var(--accent-green);">${catCountNow > 0 ? catCountNow + ' سؤال' : 'جاهز للتوليد'}</strong>
          </div>
        </div>
        <label style="display:inline-flex; align-items:center; gap:5px; background:var(--surface-inset); border:1px solid var(--card-border-strong); padding:4px 10px; border-radius:99px; cursor:pointer; font-size:0.72rem; font-weight:700; color:${st.aiAvailable ? 'var(--accent-cyan)' : 'var(--muted)'};">
          <input type="checkbox" ${st.useAiGenerator ? 'checked' : ''} onchange="window.setQuizLobbyParam('useAiGenerator', this.checked)" style="accent-color:var(--accent-green);">
          <span>توليد Gemini AI ${st.aiAvailable ? '' : '(غير مفعل)'}</span>
        </label>
      </div>

      ${st.fallbackNotice ? `
        <div style="background:var(--accent-gold-soft); border:1px solid rgba(245,158,11,0.35); color:var(--accent-gold-bright); padding:8px 12px; border-radius:10px; font-size:0.75rem; font-weight:700; margin-bottom:10px;">
          ${escapeHtml(st.fallbackNotice)}
        </div>
      ` : ''}

      <!-- الخطوة 1: طور المنافسة -->
      <div style="font-size:0.78rem; font-weight:800; color:var(--text-secondary); margin-bottom:6px;">1. اختر طور المنافسة</div>
      <div class="quiz-h-strip">
        ${modes.map(m => `
          <button type="button" class="q-chip-item ${st.gameMode === m.key ? 'active' : ''}" onclick="window.setQuizLobbyParam('gameMode', '${m.key}')">
            <span>${m.icon}</span><span>${m.title}</span>
          </button>
        `).join('')}
      </div>

      ${st.gameMode === 'ai_bot' ? `
        <div class="quiz-h-strip">
          ${[
            { k: 'rookie', l: 'بوت مبتدئ (60%)' },
            { k: 'tactician', l: 'محلل تكتيكي (78%)' },
            { k: 'legend', l: 'بوت أسطوري (92%)' }
          ].map(b => `
            <button type="button" class="q-chip-item ${st.botDifficulty === b.k ? 'active-cyan' : ''}" onclick="window.setQuizLobbyParam('botDifficulty', '${b.k}')">${b.l}</button>
          `).join('')}
        </div>
      ` : ''}

      ${st.gameMode === 'friend_code' ? `
        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; background:var(--surface-inset); border:1px solid rgba(245,158,11,0.4); padding:8px 12px; border-radius:12px; margin-bottom:10px;">
          <span style="font-size:0.76rem; font-weight:800; color:var(--accent-gold-bright);">كود التحدي:</span>
          <input type="text" value="${escapeHtml(st.challengeSeed)}" oninput="window._quizState.challengeSeed = this.value.trim().toUpperCase()" placeholder="DP-4821" class="lobby-select-input" style="padding:4px 8px; font-size:0.8rem; max-width:120px; text-align:center;">
          <span style="font-size:0.7rem; color:var(--muted);">شارك نفس الكود والفئة مع صديقك لأسئلة متطابقة 100%</span>
        </div>
      ` : ''}

      <!-- الخطوة 2: فئة الأسئلة -->
      <div style="font-size:0.78rem; font-weight:800; color:var(--text-secondary); margin-bottom:6px;">2. اختر فئة الأسئلة</div>
      <div class="quiz-h-strip">
        ${Object.entries(QUIZ_CATEGORIES_META).map(([k, v]) => {
          const cnt = k === 'ALL' ? (st.totalPoolCount || '') : ((st.categoryCounts && st.categoryCounts[k.toLowerCase()]) || '');
          return `
            <div class="q-cat-card-compact ${st.filterCategory === k ? 'active' : ''}" onclick="window.setQuizLobbyParam('filterCategory', '${k}')">
              <span style="font-size:1.2rem;">${v.icon}</span>
              <div style="min-width:0; flex:1;">
                <div style="font-weight:800; font-size:0.76rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${v.name}</div>
                <div style="font-size:0.64rem; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${cnt ? `${cnt} سؤال • ` : ''}${v.sub}</div>
              </div>
            </div>
          `;
        }).join('')}
      </div>

      <!-- زر البدء السريع مباشرة بدون تمرير طويل -->
      <div style="text-align:center; margin:14px 0 12px 0;">
        <button type="button" class="quiz-start-hero-btn" onclick="window.startQuizChallengeNow()">
          <span>ابدأ التحدي الآن (${(QUIZ_CATEGORIES_META[st.filterCategory] || QUIZ_CATEGORIES_META['ALL']).name})</span>
        </button>
      </div>

      <!-- خيارات متقدمة قابلة للطي (القارة + البطولة + الصعوبة + عدد الأسئلة) -->
      <div style="border-top:1px solid var(--card-border); padding-top:10px;">
        <button type="button" onclick="window.toggleQuizAdvancedFilters()" style="width:100%; background:var(--surface-inset); border:1px solid var(--card-border); color:var(--text-secondary); padding:8px 12px; border-radius:10px; font-size:0.78rem; font-weight:700; cursor:pointer; display:flex; justify-content:space-between; align-items:center;">
          <span>تخصيص النطاق والصعوبة (${advSummary})</span>
          <span style="color:var(--accent-green);">${window._quizAdvancedOpen ? 'إخفاء ▲' : 'تخصيص ▼'}</span>
        </button>

        ${window._quizAdvancedOpen ? `
          <div style="margin-top:10px;">
            <div style="font-size:0.74rem; color:var(--muted); font-weight:700; margin-bottom:5px;">القارة أو البطولة:</div>
            <div class="quiz-h-strip">
              ${regions.map(r => `<button type="button" class="q-chip-item ${st.filterRegion === r.key ? 'active-gold' : ''}" onclick="window.setQuizLobbyParam('filterRegion', '${r.key}')">${r.label}</button>`).join('')}
              ${leagues.map(lg => `<button type="button" class="q-chip-item ${st.filterLeague === lg.key ? 'active-cyan' : ''}" onclick="window.setQuizLobbyParam('filterLeague', '${lg.key}')">${lg.label}</button>`).join('')}
            </div>

            <div style="font-size:0.74rem; color:var(--muted); font-weight:700; margin-bottom:5px;">الصعوبة وعدد الأسئلة:</div>
            <div class="quiz-h-strip" style="margin-bottom:0;">
              ${[
                { k: 'ALL', l: 'كل المستويات' },
                { k: 'easy', l: 'سهل' },
                { k: 'medium', l: 'متوسط' },
                { k: 'hard', l: 'صعب' }
              ].map(d => `<button type="button" class="q-chip-item ${st.filterDiff === d.k ? 'active' : ''}" onclick="window.setQuizLobbyParam('filterDiff', '${d.k}')">${d.l}</button>`).join('')}
              ${[10, 20, 35].map(n => `<button type="button" class="q-chip-item ${st.sessionLength === n ? 'active-gold' : ''}" onclick="window.setQuizLobbyParam('sessionLength', ${n})">${n} سؤال</button>`).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

window.startQuizChallengeNow = async function() {
  const st = window._quizState;
  const startBtn = document.querySelector('.quiz-start-hero-btn');
  if (startBtn) {
    startBtn.disabled = true;
    startBtn.innerHTML = '<span>⏳ جاري تجهيز الأسئلة الحية من السيرفر...</span>';
  }

  let fetchFailed = false;
  try {
    const data = await fetchQuizBankFromBackend();
    if (data && data.status === 'success' && Array.isArray(data.questions) && data.questions.length > 0) {
      st.pool = data.questions;
      st.totalPoolCount = data.total_pool_size || data.questions.length;
      st.categoryCounts = data.category_counts || st.categoryCounts;
      st.aiAvailable = data.ai_available !== false;
      if (data.seed_code && st.gameMode !== 'friend_code') st.challengeSeed = data.seed_code;
      st.fallbackNotice = data.fallback_used
        ? 'ℹ️ لم يتوفر عدد كافٍ في الفلتر الدقيق المختار، فتم توسيع النطاق تلقائياً لتجهيز الجولة.'
        : '';
    } else {
      fetchFailed = true;
    }
  } catch (e) {
    console.error('Failed to fetch from /api/quiz_bank:', e);
    fetchFailed = true;
  }

  if (fetchFailed && (!st.pool || st.pool.length === 0)) {
    st.fallbackNotice = '❌ تعذر الاتصال بالسيرفر لجلب الأسئلة، يرجى المحاولة مرة أخرى.';
    renderQuizArenaWorkspace();
    return;
  }

  const isFriendMode = (st.gameMode === 'friend_code');
  const seedToUse = isFriendMode ? (st.challengeSeed || 'DP-2026') : '';

  let candidatePool = [];
  if (isFriendMode) {
    candidatePool = [...(st.pool || [])].sort((a, b) => String(a.id || '').localeCompare(String(b.id || '')));
  } else {
    const seenIds = getSeenQuizIds();
    candidatePool = (st.pool || []).filter(q => !seenIds.includes(q.id));
    if (candidatePool.length < (st.sessionLength || 10)) {
      const currentPoolIds = new Set((st.pool || []).map(q => q.id));
      const remainingSeen = seenIds.filter(id => !currentPoolIds.has(id));
      localStorage.setItem('deeppitch_seen_qids', JSON.stringify(remainingSeen));
      candidatePool = [...(st.pool || [])];
    }
  }

  const ordered = shuffleQuizArray(candidatePool, seedToUse).map(q => {
    const copy = { ...q };
    if (Array.isArray(copy.options) && copy.options.length > 2) {
      const baseOpts = isFriendMode ? [...copy.options].sort() : [...copy.options];
      copy.options = shuffleQuizArray(baseOpts, seedToUse ? `${seedToUse}_${copy.id}` : '');
    }
    return copy;
  });

  const maxLen = st.gameMode === 'survival' ? Math.min(40, ordered.length) : Math.min(st.sessionLength || 10, ordered.length);
  st.activeQueue = ordered.slice(0, Math.max(1, maxLen));

  if (st.activeQueue.length === 0) {
    st.fallbackNotice = '⚠️ لا توجد أسئلة متاحة لهذا الاختيار حالياً.';
    renderQuizArenaWorkspace();
    return;
  }

  st.phase = 'playing';
  st.currentIndex = 0;
  st.score = 0;
  st.botScore = 0;
  st.botCorrect = 0;
  st.botLastAction = 'ينتظر إجابتك...';
  st.streak = 0;
  st.bestStreakInRound = 0;
  st.roundCorrect = 0;
  st.roundAnswered = 0;
  st.speedBonusCount = 0;
  st.lives = 3;
  st.historyLog = [];
  st.answeredCurrent = false;
  st.blurLevel = 14;
  st.clueStage = 1;
  st.rankSelection = [];
  st.lifelines = { fifty: 2, hint: 2, freeze: 2 };
  playQuizSound('correct');
  renderQuizArenaWorkspace();
};

window.returnToQuizLobby = function() {
  stopQuizTimer();
  window._quizState.phase = 'lobby';
  renderQuizArenaWorkspace();
};

window.finishQuizSessionToSummary = function() {
  stopQuizTimer();
  window._quizState.phase = 'summary';
  renderQuizArenaWorkspace();
};

function getQuestionBasePoints(q, st) {
  if (!q) return 1;
  if (q.type === 'three_clues') return Math.max(1, 4 - (st.clueStage || 1));
  if (q.difficulty === 'hard') return 3;
  if (q.difficulty === 'medium') return 2;
  return 1;
}

function simulateBotTurnForQuestion(q, basePts) {
  const st = window._quizState;
  if (st.gameMode !== 'ai_bot') return;
  const accMap = { 'rookie': 0.60, 'tactician': 0.78, 'legend': 0.92 };
  const hit = Math.random() <= (accMap[st.botDifficulty] || 0.78);
  if (hit) {
    st.botScore += basePts;
    st.botCorrect += 1;
    st.botLastAction = `🤖 البوت أصاب (+${basePts})`;
  } else {
    st.botLastAction = `🤖 البوت أخطأ (0)`;
  }
  const botHud = document.getElementById('quiz-bot-hud-score');
  if (botHud) botHud.innerText = st.botScore;
}

function renderCurrentQuizQuestion() {
  const stage = document.getElementById('quiz-stage-box');
  if (!stage) return;

  const st = window._quizState;
  stopQuizTimer();

  if ((st.gameMode === 'survival' && st.lives <= 0) || st.currentIndex >= st.activeQueue.length) {
    window.finishQuizSessionToSummary();
    return;
  }

  const q = st.activeQueue[st.currentIndex];
  if (st.gameMode !== 'friend_code') {
    markQuizQuestionSeen(q.id);
  }

  st.answeredCurrent = false;
  st.usedLifelinesThisQ = { fifty: false, hint: false, freeze: false };
  st.blurLevel = 14;
  st.clueStage = 1;
  st.rankSelection = [];
  st.blitzFound = [];
  st.questionStartTs = Date.now();

  const catInfo = QUIZ_CATEGORIES_META[q.category] || QUIZ_CATEGORIES_META['trivia'];
  const totalSec = q.type === 'blitz_30s' ? 30 : 20;

  let visualStageHtml = '';
  let customOptionsHtml = '';

  if (q.type === 'career_path' && Array.isArray(q.career_stops)) {
    visualStageHtml = `
      <div class="quiz-career-scroll">
        ${q.career_stops.map((stItem, i) => `
          <div class="career-club-card">
            <span class="career-step-badge">محطة #${i + 1}</span>
            <img src="${stItem.crest}" alt="${escapeHtml(stItem.club)}" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=1e293b&color=00e676&bold=true&rounded=true'">
            <div class="career-club-title">${escapeHtml(stItem.club)}</div>
          </div>
          ${i < q.career_stops.length - 1 ? `<span class="career-step-arrow">⬅️</span>` : ''}
        `).join('')}
      </div>
    `;
  } else if (q.type === 'logo_blur') {
    visualStageHtml = `
      <div class="quiz-visual-center">
        <img id="quiz-mystery-crest" src="${q.image_url}" style="filter: blur(${st.blurLevel}px); transition: filter 0.35s ease; width:88px; height:88px; object-fit:contain;" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=0f172a&color=00d2ff&bold=true&rounded=true'">
      </div>
    `;
  } else if (q.type === 'jersey_card') {
    visualStageHtml = `
      <div class="quiz-visual-center">
        <div class="jersey-shirt-badge">
          <div style="font-size:0.62rem; color:#cbd5e1; font-weight:800;">قميص رقم</div>
          <div class="jersey-num-txt">#${q.jersey_num}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.75rem; color:var(--muted);">النادي:</div>
          <div style="font-size:0.95rem; font-weight:900; color:#fff;">${escapeHtml(q.jersey_club)}</div>
        </div>
      </div>
    `;
  } else if (q.type === 'higher_lower') {
    visualStageHtml = `
      <div class="quiz-visual-center" style="justify-content:space-around;">
        <div style="text-align:center;">
          ${q.item_a.crest ? `<img src="${q.item_a.crest}" width="42" height="42" style="object-fit:contain;" onerror="this.style.display='none'">` : ''}
          <div style="font-weight:900; font-size:0.86rem; color:#fff;">${escapeHtml(q.item_a.name)}</div>
          <div style="font-size:1.3rem; font-weight:900; color:var(--accent-green);">${q.item_a.stat_val}</div>
        </div>
        <div class="vs-circle-badge" style="width:36px; height:36px; font-size:0.8rem;">VS</div>
        <div style="text-align:center;">
          ${q.item_b.crest ? `<img src="${q.item_b.crest}" width="42" height="42" style="object-fit:contain;" onerror="this.style.display='none'">` : ''}
          <div style="font-weight:900; font-size:0.86rem; color:#fff;">${escapeHtml(q.item_b.name)}</div>
          <div id="hl-mystery-val" style="font-size:1.3rem; font-weight:900; color:var(--accent-gold);">❓</div>
        </div>
      </div>
    `;
  } else if (q.type === 'three_clues') {
    const clues = q.clues || [];
    visualStageHtml = `
      <div style="margin-bottom:10px;">
        <div id="clues-stack-list" style="display:flex; flex-direction:column; gap:6px; margin-bottom:8px;">
          <div class="clue-item-card">🔎 ${escapeHtml(clues[0] || '')}</div>
        </div>
        ${clues.length > 1 ? `
          <div style="text-align:center;">
            <button type="button" id="reveal-next-clue-btn" class="dock-lifeline-btn" onclick="window.revealNextProgressiveClue(false)" style="border-color:var(--accent-gold); color:var(--accent-gold);">
              🔓 كشف الدليل التالي (يقلل النقاط -1)
            </button>
          </div>
        ` : ''}
      </div>
    `;
  } else if (q.type === 'rank_order') {
    customOptionsHtml = `
      <div style="display:flex; justify-content:center; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap;">
        <span style="font-size:0.72rem; color:var(--muted);">انقر بالترتيب من #1 إلى #4 (يمكنك النقر مجدداً لإلغاء اختيار عنصر)</span>
        <button type="button" class="dock-lifeline-btn" onclick="window.resetRankOrderSelection()">🔄 إعادة الكل</button>
      </div>
      <div class="quiz-options-grid" id="rank-order-grid">
        ${(q.rank_items || []).map((item, idx) => `
          <button type="button" class="quiz-option-btn rank-item-btn" id="rank-btn-${idx}" onclick="window.onRankItemClick(${idx})">
            <span class="opt-letter" id="rank-badge-${idx}">?</span>
            <div class="opt-text" style="display:flex; justify-content:space-between; align-items:center; gap:6px;">
              <span>${escapeHtml(item.label)}</span>
              <span class="rank-secret-val" style="display:none; color:var(--accent-gold); font-size:0.74rem;">${escapeHtml(item.val)}</span>
            </div>
          </button>
        `).join('')}
      </div>
    `;
  } else if (q.type === 'blitz_30s') {
    visualStageHtml = `
      <div style="background:#050912; border:1px solid #1b2a47; border-radius:14px; padding:12px; margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="font-size:0.84rem; font-weight:900; color:var(--accent-green);">⚡ المكتشف: <strong id="blitz-counter-num">0</strong></span>
          <button type="button" class="dock-lifeline-btn" onclick="window.finishBlitzRound()">إنهاء والانتقال للتالي ⬅️</button>
        </div>
        <input type="text" id="blitz-live-input" class="quiz-blitz-input" style="padding:9px 12px; font-size:0.86rem; margin-bottom:8px; width:100%;" placeholder="✍️ اكتب اسم النادي بالعربية أو الإنجليزية (مثل: الريال، برشلونة، ليفربول...)" oninput="window.onBlitzInputType(this.value)" autocomplete="off">
        <div id="blitz-tags-cloud" class="blitz-tags-cloud"></div>
      </div>
    `;
  }

  const optionsGridHtml = customOptionsHtml || (q.type === 'blitz_30s'
    ? ''
    : `
      <div class="quiz-options-grid" id="quiz-options-box">
        ${(q.options || []).map((opt, idx) => `
          <button type="button" class="quiz-option-btn" id="quiz-opt-btn-${idx}" onclick="window.submitQuizAnswer(${idx})">
            <span class="opt-letter">${['أ', 'ب', 'ج', 'د'][idx] || '•'}</span>
            <span class="opt-text">${escapeHtml(String(opt))}</span>
          </button>
        `).join('')}
      </div>
    `);

  stage.innerHTML = `
    <div class="quiz-stage-card quiz-slide-anim">
      <div class="quiz-neon-timer-track">
        <div id="quiz-neon-timer-bar" class="quiz-neon-timer-fill" style="width:100%;"></div>
      </div>

      ${st.fallbackNotice && st.currentIndex === 0 ? `
        <div style="background:rgba(255,214,0,0.08); border:1px solid rgba(255,214,0,0.3); color:var(--accent-gold); padding:5px 10px; border-radius:8px; font-size:0.72rem; font-weight:700; margin-bottom:8px; text-align:center;">
          ${escapeHtml(st.fallbackNotice)}
        </div>
      ` : ''}

      <div class="quiz-hud-bar">
        <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
          <button type="button" class="hud-chip" onclick="window.returnToQuizLobby()" style="cursor:pointer;">⚙️ القائمة</button>
          <span class="hud-chip">${st.currentIndex + 1} / ${st.activeQueue.length}</span>
          ${st.streak >= 2 ? `<span class="hud-chip" style="border-color:#ff9100; color:#ff9100;">🔥 ×${st.streak}</span>` : ''}
          ${st.gameMode === 'survival' ? `<span class="hud-chip">${'❤️'.repeat(st.lives)}</span>` : ''}
          ${st.gameMode === 'ai_bot' ? `<span class="hud-chip" style="border-color:var(--accent-cyan); color:var(--accent-cyan);">🤖 البوت: <strong id="quiz-bot-hud-score">${st.botScore}</strong></span>` : ''}
        </div>

        <div style="display:flex; align-items:center; gap:6px;">
          <span class="hud-chip" style="border-color:var(--accent-gold); color:var(--accent-gold);">⭐ <strong id="quiz-live-score">${st.score}</strong></span>
          <span class="hud-chip" id="quiz-timer-badge" style="border-color:var(--accent-cyan); color:var(--accent-cyan);">⏱️ <strong id="quiz-timer-sec">${totalSec}</strong>ث</span>
        </div>
      </div>

      <div class="quiz-question-box">
        <span class="quiz-cat-tag">${catInfo.icon} ${catInfo.name}</span>
        <h3 class="quiz-question-title">${escapeHtml(q.question)}</h3>
      </div>

      ${visualStageHtml}
      ${optionsGridHtml}

      ${q.type !== 'blitz_30s' ? `
        <div class="quiz-lifelines-dock">
          ${q.type !== 'rank_order' && q.options && q.options.length > 2 ? `
            <button type="button" id="lf-btn-fifty" class="dock-lifeline-btn" onclick="window.useQuizLifeline('fifty')" ${st.lifelines.fifty <= 0 ? 'disabled' : ''}>✂️ 50:50 (${st.lifelines.fifty})</button>
          ` : ''}
          <button type="button" id="lf-btn-hint" class="dock-lifeline-btn" onclick="window.useQuizLifeline('hint')" ${st.lifelines.hint <= 0 ? 'disabled' : ''}>💡 تلميح (${st.lifelines.hint})</button>
          <button type="button" id="lf-btn-freeze" class="dock-lifeline-btn" onclick="window.useQuizLifeline('freeze')" ${st.lifelines.freeze <= 0 ? 'disabled' : ''}>❄️ +10ث (${st.lifelines.freeze})</button>
        </div>
      ` : ''}

      <div id="quiz-feedback-banner" style="display:none;"></div>
    </div>
  `;

  startQuizQuestionTimer(totalSec);
  if (q.type === 'blitz_30s') {
    const inp = document.getElementById('blitz-live-input');
    if (inp) inp.focus();
  }
}

window.submitQuizAnswer = function(optIdx) {
  const st = window._quizState;
  if (!st || st.answeredCurrent) return;
  st.answeredCurrent = true;
  stopQuizTimer();

  const q = st.activeQueue[st.currentIndex];
  if (!q || !Array.isArray(q.options)) return;

  const chosen = String(q.options[optIdx] !== undefined ? q.options[optIdx] : '').trim();
  const correctAns = String(q.answer !== undefined ? q.answer : '').trim();
  const isCorrect = (chosen === correctAns) || (chosen.toLowerCase() === correctAns.toLowerCase());

  const mysteryCrest = document.getElementById('quiz-mystery-crest');
  if (mysteryCrest) mysteryCrest.style.filter = 'blur(0px)';

  const hlVal = document.getElementById('hl-mystery-val');
  if (hlVal && q.item_b) hlVal.innerText = q.item_b.stat_val;

  q.options.forEach((optVal, idx) => {
    const btn = document.getElementById(`quiz-opt-btn-${idx}`);
    if (!btn) return;
    btn.disabled = true;
    const optStr = String(optVal).trim();
    if (optStr === correctAns || optStr.toLowerCase() === correctAns.toLowerCase()) {
      btn.classList.add('opt-correct');
    } else if (idx === optIdx && !isCorrect) {
      btn.classList.add('opt-wrong');
    } else {
      btn.style.opacity = '0.45';
    }
  });

  const basePts = getQuestionBasePoints(q, st);
  finalizeQuestionScoreAndFeedback(isCorrect, q, basePts, chosen);
};

window.revealNextProgressiveClue = function(isFreeFromLifeline = false) {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q || !q.clues) return;

  const listEl = document.getElementById('clues-stack-list');
  const shownCount = listEl ? listEl.children.length : 1;
  if (shownCount < q.clues.length) {
    if (!isFreeFromLifeline) {
      st.clueStage += 1;
    }
    if (listEl) {
      const div = document.createElement('div');
      div.className = 'clue-item-card';
      div.innerText = `🔎 ${q.clues[shownCount]}`;
      listEl.appendChild(div);
    }
    if (shownCount + 1 >= q.clues.length) {
      const btn = document.getElementById('reveal-next-clue-btn');
      if (btn) btn.style.display = 'none';
    }
  }
};

function redrawRankBadgesUI() {
  const st = window._quizState;
  document.querySelectorAll('.rank-item-btn').forEach((btn, i) => {
    const selPos = st.rankSelection.findIndex(x => x.idx === i);
    const bdg = document.getElementById(`rank-badge-${i}`);
    if (selPos >= 0) {
      btn.classList.add('rank-selected-btn');
      if (bdg) {
        bdg.innerText = `#${selPos + 1}`;
        bdg.style.background = 'var(--accent-gold)';
        bdg.style.color = '#000';
      }
    } else {
      btn.classList.remove('rank-selected-btn');
     if (bdg) {
        bdg.innerText = '?';
        bdg.style.background = 'var(--card)';
        bdg.style.color = 'var(--accent-cyan)';
      }
    }
  });
}

window.onRankItemClick = function(idx) {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q || q.type !== 'rank_order' || !Array.isArray(q.rank_items)) return;

  const existingPos = st.rankSelection.findIndex(x => x.idx === idx);
  if (existingPos >= 0) {
    st.rankSelection.splice(existingPos, 1);
    redrawRankBadgesUI();
    return;
  }

  const label = q.rank_items[idx] ? q.rank_items[idx].label : '';
  st.rankSelection.push({ idx, label });
  redrawRankBadgesUI();

  if (st.rankSelection.length === q.rank_items.length) {
    st.answeredCurrent = true;
    stopQuizTimer();
    const userOrder = st.rankSelection.map(x => x.label);
    const isCorrect = JSON.stringify(userOrder) === JSON.stringify(q.correct_order);

    st.rankSelection.forEach((selObj, posIdx) => {
      const btn = document.getElementById(`rank-btn-${selObj.idx}`);
      const bdg = document.getElementById(`rank-badge-${selObj.idx}`);
      const trueIdx = (q.correct_order || []).indexOf(selObj.label);
      const slotRight = (trueIdx === posIdx);
      if (btn) {
        btn.disabled = true;
        btn.classList.remove('rank-selected-btn');
        btn.classList.add(slotRight ? 'opt-correct' : 'opt-wrong');
      }
      if (bdg && trueIdx >= 0) {
        bdg.innerText = `#${trueIdx + 1}`;
      }
    });
    document.querySelectorAll('.rank-secret-val').forEach(el => { el.style.display = 'inline-block'; });
    finalizeQuestionScoreAndFeedback(isCorrect, q, 2, userOrder.join(' ⬅️ '));
  }
};

window.resetRankOrderSelection = function() {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  st.rankSelection = [];
  redrawRankBadgesUI();
};

function startQuizQuestionTimer(seconds) {
  const st = window._quizState;
  st.timerSec = seconds;
  st.timerMax = seconds;
  stopQuizTimer();

  st.timerInterval = setInterval(() => {
    if (st.answeredCurrent || st.phase !== 'playing') {
      stopQuizTimer();
      return;
    }
    st.timerSec -= 1;
    const el = document.getElementById('quiz-timer-sec');
    const neonBar = document.getElementById('quiz-neon-timer-bar');
    if (el) el.innerText = Math.max(0, st.timerSec);
    if (neonBar) {
      const pct = Math.max(0, Math.min(100, (st.timerSec / Math.max(1, st.timerMax)) * 100));
      neonBar.style.width = `${pct}%`;
    }
    if (st.timerSec <= 0) {
      stopQuizTimer();
      const curQ = st.activeQueue[st.currentIndex];
      if (curQ && curQ.type === 'blitz_30s') window.finishBlitzRound();
      else handleQuizTimeout();
    }
  }, 1000);
}

function normalizeArabicQuizText(str) {
  return String(str || '')
    .trim()
    .toLowerCase()
    .replace(/[\u064B-\u065F\u0640]/g, '')
    .replace(/[أإآ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/ى/g, 'ي');
}

window.onBlitzInputType = function(rawVal) {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q || q.type !== 'blitz_30s') return;

  const clean = normalizeArabicQuizText(rawVal);
  if (clean.length < 3) return;

  const matched = (q.accepted_answers || []).find(item => normalizeArabicQuizText(item) === clean);
  const normMatched = matched ? normalizeArabicQuizText(matched) : '';
  if (matched && !st.blitzFound.includes(normMatched)) {
    const oldLvl = computePlayerLevel500(st.profile.totalPoints).level;
    st.blitzFound.push(normMatched);
    st.score += 1;
    st.profile.totalPoints += 1;
    saveQuizProfile();

    const newLvl = computePlayerLevel500(st.profile.totalPoints).level;
    window.refreshLiveLicenseBannerUI();
    if (newLvl > oldLvl) triggerLevelUpCelebration(oldLvl, newLvl);
    else playQuizSound('correct');

    const inp = document.getElementById('blitz-live-input');
    if (inp) inp.value = '';
    const cntEl = document.getElementById('blitz-counter-num');
    if (cntEl) cntEl.innerText = st.blitzFound.length;
    const scEl = document.getElementById('quiz-live-score');
    if (scEl) scEl.innerText = st.score;

    const cloud = document.getElementById('blitz-tags-cloud');
    if (cloud) {
      const chip = document.createElement('span');
      chip.className = 'blitz-hit-chip';
      chip.innerText = `✅ ${rawVal.trim()}`;
      cloud.prepend(chip);
    }
  }
};

window.finishBlitzRound = function() {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  st.answeredCurrent = true;
  stopQuizTimer();

  const q = st.activeQueue[st.currentIndex];
  const foundCount = st.blitzFound.length;
  const passed = foundCount > 0;

  st.roundAnswered += 1;
  st.profile.answeredCount += 1;
  if (passed) {
    st.roundCorrect += 1;
    st.profile.correctCount += 1;
    st.streak += 1;
    if (st.streak > st.bestStreakInRound) st.bestStreakInRound = st.streak;
  } else {
    st.streak = 0;
    if (st.gameMode === 'survival') st.lives -= 1;
    playQuizSound('wrong');
  }

  st.historyLog.push({
    question: q.question,
    userAnswer: passed ? `اكتشف ${foundCount} أندية (+${foundCount} نقطة)` : '0 أندية',
    correctAnswer: q.answer || '',
    isCorrect: passed
  });

  saveQuizProfile();
  window.refreshLiveLicenseBannerUI();
  simulateBotTurnForQuestion(q, Math.max(2, Math.min(4, foundCount || 2)));

  const isLastQ = (st.currentIndex + 1 >= st.activeQueue.length) || (st.gameMode === 'survival' && st.lives <= 0);
  const fb = document.getElementById('quiz-feedback-banner');
  if (fb) {
    fb.style.display = 'block';
    fb.className = `quiz-feedback-box ${passed ? 'fb-correct' : 'fb-wrong'}`;
    fb.innerHTML = `
      <div class="dp-quiz-fb-layout">
        <div style="min-width:0;">
          <div style="font-size:0.84rem; font-weight:900; color:${passed ? 'var(--accent-green)' : 'var(--accent-red)'};">
            ${passed ? `✅ رائع! اكتشفت ${foundCount} أندية (+${foundCount} نقطة)` : '❌ لم تكتشف أي نادٍ في هذا التحدي!'}
          </div>
          <div style="font-size:0.74rem; color:#cbd5e1; margin-top:3px;">${escapeHtml(q.explanation || '')}</div>
          ${st.gameMode === 'ai_bot' ? `<div style="font-size:0.72rem; color:var(--accent-cyan); font-weight:800; margin-top:2px;">${st.botLastAction}</div>` : ''}
        </div>
        <button type="button" class="ai-btn" onclick="window.nextQuizQuestion()" style="white-space:nowrap;">${isLastQ ? '🏁 النتيجة' : 'التالي ⬅️'}</button>
      </div>
    `;
  }
};

window.useQuizLifeline = function(type) {
  const st = window._quizState;
  if (st.answeredCurrent || st.lifelines[type] <= 0 || st.usedLifelinesThisQ[type]) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q) return;

  st.lifelines[type] -= 1;
  st.usedLifelinesThisQ[type] = true;

  if (type === 'fifty' && q.options && q.options.length > 2) {
    const correctAns = String(q.answer).trim().toLowerCase();
    let hiddenCount = 0;
    q.options.forEach((optVal, idx) => {
      if (hiddenCount < 2 && String(optVal).trim().toLowerCase() !== correctAns) {
        const btn = document.getElementById(`quiz-opt-btn-${idx}`);
        if (btn) {
          btn.disabled = true;
          btn.style.opacity = '0.2';
          hiddenCount += 1;
        }
      }
    });
    const btn = document.getElementById('lf-btn-fifty');
    if (btn) { btn.innerText = `✂️ 50:50 (${st.lifelines.fifty})`; btn.disabled = true; }
  } else if (type === 'hint') {
    if (q.type === 'three_clues') {
      window.revealNextProgressiveClue(true);
    } else if (q.type === 'logo_blur') {
      st.blurLevel = Math.max(3, st.blurLevel - 7);
      const img = document.getElementById('quiz-mystery-crest');
      if (img) img.style.filter = `blur(${st.blurLevel}px)`;
    }
    const fb = document.getElementById('quiz-feedback-banner');
    if (fb && q.hint) {
      fb.style.display = 'block';
      fb.className = 'quiz-feedback-box';
      fb.innerHTML = `<div style="color:var(--accent-gold); font-weight:800; font-size:0.8rem;">💡 تلميح: ${escapeHtml(q.hint)}</div>`;
    }
    const btn = document.getElementById('lf-btn-hint');
    if (btn) { btn.innerText = `💡 تلميح (${st.lifelines.hint})`; btn.disabled = true; }
  } else if (type === 'freeze') {
    st.timerSec += 10;
    st.timerMax = Math.max(st.timerMax, st.timerSec);
    const el = document.getElementById('quiz-timer-sec');
    if (el) el.innerText = st.timerSec;
    const btn = document.getElementById('lf-btn-freeze');
    if (btn) { btn.innerText = `❄️ +10ث (${st.lifelines.freeze})`; btn.disabled = true; }
  }
};

function handleQuizTimeout() {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  st.answeredCurrent = true;
  st.streak = 0;
  st.roundAnswered += 1;
  st.profile.answeredCount += 1;
  if (st.gameMode === 'survival') st.lives -= 1;

  const q = st.activeQueue[st.currentIndex];

  const mysteryCrest = document.getElementById('quiz-mystery-crest');
  if (mysteryCrest) mysteryCrest.style.filter = 'blur(0px)';
  const hlVal = document.getElementById('hl-mystery-val');
  if (hlVal && q && q.item_b) hlVal.innerText = q.item_b.stat_val;

  if (q && Array.isArray(q.options)) {
    const correctAns = String(q.answer).trim().toLowerCase();
    q.options.forEach((optVal, idx) => {
      const btn = document.getElementById(`quiz-opt-btn-${idx}`);
      if (btn) {
        btn.disabled = true;
        if (String(optVal).trim().toLowerCase() === correctAns) {
          btn.classList.add('opt-correct');
        }
      }
    });
  }
  if (q && q.type === 'rank_order') {
    document.querySelectorAll('.rank-item-btn').forEach(b => { b.disabled = true; });
    document.querySelectorAll('.rank-secret-val').forEach(el => { el.style.display = 'inline-block'; });
  }

  st.historyLog.push({
    question: q ? q.question : '',
    userAnswer: 'انتهى الوقت ⌛',
    correctAnswer: q ? q.answer : '',
    isCorrect: false
  });

  saveQuizProfile();
  window.refreshLiveLicenseBannerUI();
  simulateBotTurnForQuestion(q, getQuestionBasePoints(q, st));
  playQuizSound('wrong');

  const isLastQ = (st.currentIndex + 1 >= st.activeQueue.length) || (st.gameMode === 'survival' && st.lives <= 0);
  const fb = document.getElementById('quiz-feedback-banner');
  if (fb) {
    fb.style.display = 'block';
    fb.className = 'quiz-feedback-box fb-wrong';
    fb.innerHTML = `
      <div class="dp-quiz-fb-layout">
        <div style="min-width:0;">
          <div style="color:var(--accent-red); font-weight:900; font-size:0.84rem;">⌛ انتهى الوقت! الصحيح: ${escapeHtml(q ? q.answer : '')}</div>
          ${st.gameMode === 'ai_bot' ? `<div style="font-size:0.72rem; color:var(--accent-cyan); font-weight:800; margin-top:2px;">${st.botLastAction}</div>` : ''}
        </div>
        <button type="button" class="ai-btn" onclick="window.nextQuizQuestion()" style="padding:7px 14px; white-space:nowrap;">${isLastQ ? '🏁 النتيجة' : 'التالي ⬅️'}</button>
      </div>
    `;
  }
}

function finalizeQuestionScoreAndFeedback(isCorrect, q, basePts, userChosenText = '') {
  const st = window._quizState;
  const elapsedSec = (Date.now() - (st.questionStartTs || Date.now())) / 1000;
  const speedBonus = isCorrect && elapsedSec <= 5.0 ? 1 : 0;
  const oldLvl = computePlayerLevel500(st.profile.totalPoints).level;

  st.roundAnswered += 1;
  st.profile.answeredCount += 1;

  let deltaPts = 0;
  if (isCorrect) {
    st.streak += 1;
    if (st.streak > st.bestStreakInRound) st.bestStreakInRound = st.streak;
    st.roundCorrect += 1;
    st.profile.correctCount += 1;
    deltaPts = basePts + speedBonus;
    if (speedBonus) st.speedBonusCount += 1;
    st.score += deltaPts;
    st.profile.totalPoints += deltaPts;
  } else {
    st.streak = 0;
    if (st.gameMode === 'survival') st.lives -= 1;
  }

  simulateBotTurnForQuestion(q, basePts);

  st.historyLog.push({
    question: q.question,
    userAnswer: userChosenText,
    correctAnswer: q.answer,
    isCorrect: isCorrect
  });

  saveQuizProfile();
  const newLvl = computePlayerLevel500(st.profile.totalPoints).level;
  window.refreshLiveLicenseBannerUI();

  if (isCorrect) {
    if (newLvl > oldLvl) triggerLevelUpCelebration(oldLvl, newLvl);
    else playQuizSound('correct');
  } else {
    playQuizSound('wrong');
  }

  const scEl = document.getElementById('quiz-live-score');
  if (scEl) scEl.innerText = st.score;

  const isLastQ = (st.currentIndex + 1 >= st.activeQueue.length) || (st.gameMode === 'survival' && st.lives <= 0);
  const speedTag = speedBonus ? ' <span style="color:var(--accent-gold);">(⚡ +1 سرعة)</span>' : '';
  const botTag = st.gameMode === 'ai_bot'
    ? `<div style="font-size:0.72rem; color:var(--accent-cyan); font-weight:800; margin-top:3px;">${st.botLastAction}</div>`
    : '';

  const fb = document.getElementById('quiz-feedback-banner');
  if (fb) {
    fb.style.display = 'block';
    fb.className = `quiz-feedback-box ${isCorrect ? 'fb-correct' : 'fb-wrong'}`;
    fb.innerHTML = `
     <div class="dp-quiz-fb-layout">
        <div style="min-width:0;">
          <div style="font-weight:900; font-size:0.86rem; color:${isCorrect ? 'var(--accent-green)' : 'var(--accent-red)'};">
            ${isCorrect ? `✅ إجابة صحيحة! (+${deltaPts} نقطة)${speedTag}` : `❌ إجابة خاطئة! الصحيح: ${escapeHtml(q.answer)}`}
          </div>
          <div style="font-size:0.76rem; color:#cbd5e1; margin-top:2px;">${escapeHtml(q.explanation || '')}</div>
          ${botTag}
        </div>
        <button type="button" class="ai-btn" onclick="window.nextQuizQuestion()" style="white-space:nowrap; padding:7px 14px;">
          ${isLastQ ? '🏁 النتيجة' : 'التالي ⬅️'}
        </button>
      </div>
    `;
  }
}

window.nextQuizQuestion = function() {
  const st = window._quizState;
  st.currentIndex += 1;
  if ((st.gameMode === 'survival' && st.lives <= 0) || st.currentIndex >= st.activeQueue.length) {
    window.finishQuizSessionToSummary();
  } else {
    renderQuizArenaWorkspace();
  }
};

window.copyChallengeCodeToClipboard = function(codeStr) {
  try {
    navigator.clipboard.writeText(codeStr);
    window.showAppToast(`تم نسخ كود التحدي (${codeStr}) بنجاح`);
  } catch (e) {}
};

function renderQuizPostMatchSummary() {
  const stage = document.getElementById('quiz-stage-box');
  if (!stage) return;

  const st = window._quizState;
  const totalAns = Math.max(1, st.roundAnswered);
  const accPct = Math.round((st.roundCorrect / totalAns) * 100);
  const lvlObj = computePlayerLevel500(st.profile.totalPoints);

  if (st.score > (st.profile.highScore || 0)) {
    st.profile.highScore = st.score;
    saveQuizProfile();
  }

  let botBannerHtml = '';
  if (st.gameMode === 'ai_bot') {
    const won = st.score > st.botScore;
    const draw = st.score === st.botScore;
    botBannerHtml = `
      <div style="background:#081224; border:1px solid ${won ? 'var(--accent-green)' : (draw ? 'var(--accent-gold)' : 'var(--accent-red)')}; border-radius:14px; padding:12px; margin-bottom:14px;">
        <div style="font-weight:900; color:${won ? 'var(--accent-green)' : (draw ? 'var(--accent-gold)' : 'var(--accent-red)')};">
          ${won ? '🏆 تفوقت على البوت الذكي!' : (draw ? '🤝 تعادل مثير مع البوت!' : '🤖 تفوق البوت الذكي في هذه الجولة!')}
        </div>
        <div style="font-size:0.82rem; color:#fff; margin-top:4px;">أنت: ${st.score} ⭐ — البوت: ${st.botScore} ⭐</div>
      </div>
    `;
  }

  const reviewHtml = (st.historyLog || []).length > 0
    ? `
      <div style="text-align:right; margin-top:12px;">
        <div style="font-size:0.84rem; font-weight:900; color:var(--accent-cyan); margin-bottom:6px;">📝 مراجعة إجاباتك في هذه الجولة (${st.historyLog.length} أسئلة):</div>
        <div class="quiz-review-list">
          ${st.historyLog.map((item, idx) => `
            <div class="quiz-review-item ${item.isCorrect ? '' : 'rev-wrong'}">
              <div style="font-weight:800; color:#fff; margin-bottom:3px;">${idx + 1}. ${escapeHtml(item.question)}</div>
              <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px; font-size:0.73rem;">
                <span style="color:${item.isCorrect ? 'var(--accent-green)' : 'var(--accent-red)'}; font-weight:800;">
                  ${item.isCorrect ? '✅' : '❌'} إجابتك: ${escapeHtml(item.userAnswer)}
                </span>
                ${!item.isCorrect ? `<span style="color:var(--accent-gold); font-weight:800;">الصحيح: ${escapeHtml(item.correctAnswer)}</span>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `
    : '';

  stage.innerHTML = `
    <div class="quiz-stage-card quiz-slide-anim" style="text-align:center;">
      <span class="quiz-cat-tag">🏁 نهاية الجولة — المستوى ${lvlObj.level} / 500</span>

      ${botBannerHtml}

      <div class="post-match-kpis-grid" style="grid-template-columns:repeat(auto-fit, minmax(95px, 1fr));">
        <div class="pm-kpi-card">
          <div class="pm-kpi-val" style="color:var(--accent-green);">+${st.score}</div>
          <div class="pm-kpi-lbl">النقاط ⭐</div>
        </div>
        <div class="pm-kpi-card" style="border-top-color:var(--accent-cyan);">
          <div class="pm-kpi-val" style="color:var(--accent-cyan);">${accPct}%</div>
          <div class="pm-kpi-lbl">الدقة (${st.roundCorrect}/${st.roundAnswered})</div>
        </div>
        <div class="pm-kpi-card" style="border-top-color:#ff9100;">
          <div class="pm-kpi-val" style="color:#ff9100;">🔥 ${st.bestStreakInRound}</div>
          <div class="pm-kpi-lbl">أطول سلسلة</div>
        </div>
        <div class="pm-kpi-card" style="border-top-color:var(--accent-gold);">
          <div class="pm-kpi-val" style="color:var(--accent-gold);">⚡ ${st.speedBonusCount}</div>
          <div class="pm-kpi-lbl">بونص السرعة</div>
        </div>
      </div>

      ${reviewHtml}

      <div style="background:#060a14; border:1px dashed var(--accent-gold); border-radius:12px; padding:10px 14px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:0.78rem; color:var(--accent-gold); font-weight:900;">🔗 كود تحدي الصديق: ${escapeHtml(st.challengeSeed)}</span>
        <button type="button" class="dock-lifeline-btn" onclick="window.copyChallengeCodeToClipboard('${escapeHtml(st.challengeSeed)}')" style="border-color:var(--accent-gold); color:var(--accent-gold);">📋 نسخ</button>
      </div>

      <div style="display:flex; justify-content:center; gap:10px;">
        <button type="button" class="ai-btn" onclick="window.startQuizChallengeNow()">🔄 جولة جديدة</button>
        <button type="button" class="dock-lifeline-btn" onclick="window.returnToQuizLobby()">⚙️ الإعدادات</button>
      </div>
    </div>
  `;
}


// =========================================================
// 13. محرك الجوال الموحّد (PWA + الشريط السفلي المتزامن + الأندية المفضلة الذكية بدون استهلاك البطارية)
// =========================================================
(function initDeepPitchMobileSuite() {
  const FAV_STORAGE_KEY = 'deeppitch_favorite_clubs_v1';
  let deferredInstallPrompt = null;
  let onlyFavoritesFilter = false;

  function getFavoriteClubs() {
    try {
      return JSON.parse(localStorage.getItem(FAV_STORAGE_KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function saveFavoriteClubs(list) {
    try {
      localStorage.setItem(FAV_STORAGE_KEY, JSON.stringify(list));
    } catch (e) {}
  }

  function isClubFavorite(clubName) {
    if (!clubName) return false;
    const clean = clubName.trim().toLowerCase();
    return getFavoriteClubs().some(c => c.toLowerCase() === clean);
  }

  function showMobileToast(msg) {
    const old = document.getElementById('dp-mobile-toast');
    if (old) old.remove();
    const toast = document.createElement('div');
    toast.id = 'dp-mobile-toast';
    toast.style.cssText = `
      position: fixed; top: 66px; left: 50%; transform: translateX(-50%);
      background: rgba(13, 22, 40, 0.96); border: 1.5px solid #ffd600;
      color: #fff; padding: 9px 18px; border-radius: 99px; font-size: 0.8rem;
      font-weight: 800; z-index: 3000; box-shadow: 0 8px 24px rgba(0,0,0,0.6);
      white-space: nowrap; max-width: 92vw; overflow: hidden; text-overflow: ellipsis; direction: rtl;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 2500);
  }

  window.toggleFavoriteClub = function(clubName, event) {
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }
    const clean = (clubName || '').trim();
    if (!clean || clean.length < 2) return;

    const favs = getFavoriteClubs();
    const existsIdx = favs.findIndex(c => c.toLowerCase() === clean.toLowerCase());
    if (existsIdx >= 0) {
      favs.splice(existsIdx, 1);
      showMobileToast(`تمت إزالة (${clean}) من المفضلة`);
    } else {
      favs.push(clean);
      showMobileToast(`⭐ تمت إضافة (${clean}) إلى أنديتك المفضلة!`);
    }
    saveFavoriteClubs(favs);
    window.refreshFavoriteStarsAndSorting();
  };

  window.syncMobileBottomNav = function(activeKey) {
    const nav = document.getElementById('dp-bottom-nav');
    if (!nav) return;
    nav.querySelectorAll('.dp-bnav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-bnav') === activeKey);
    });
  };

  function buildMobileBottomNav() {
    if (document.getElementById('dp-bottom-nav')) return;
    const nav = document.createElement('nav');
    nav.id = 'dp-bottom-nav';
    nav.setAttribute('dir', 'rtl');

    const tabs = [
      { id: 'today', label: 'المباريات', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>' },
      { id: 'competitions', label: 'البطولات', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>' },
      { id: 'media', label: 'الميركاتو', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/></svg>' },
      { id: 'explore', label: 'استكشاف', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>' },
      { id: 'quiz', label: 'التحدي', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="6" width="20" height="12" rx="4"/><line x1="6" y1="12" x2="10" y2="12"/><line x1="8" y1="10" x2="8" y2="14"/></svg>' }
    ];

    nav.innerHTML = tabs.map((t, idx) => `
      <button type="button" class="dp-bnav-btn ${idx === 0 ? 'active' : ''}" data-bnav="${t.id}">
        <span class="bnav-ico">${t.svg}</span>
        <span>${t.label}</span>
      </button>
    `).join('');

    document.body.appendChild(nav);

    nav.querySelectorAll('.dp-bnav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const pillarId = btn.getAttribute('data-bnav');
        navigateToPillar(pillarId);
      });
    });
  }
function registerPWAEngine() {
    if ('serviceWorker' in navigator && !window._dpSwRegistered) {
      window._dpSwRegistered = true;
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredInstallPrompt = e;

      const installBtn = document.getElementById('dp-pwa-install-pill');
      if (!installBtn) return;
      installBtn.style.display = 'inline-flex';
      installBtn.onclick = async () => {
        if (!deferredInstallPrompt) return;
        deferredInstallPrompt.prompt();
        const choice = await deferredInstallPrompt.userChoice;
        if (choice && choice.outcome === 'accepted') installBtn.style.display = 'none';
        deferredInstallPrompt = null;
      };
    });
  }


  window.isClubFavoritePublic = isClubFavorite;

  window.refreshFavoriteStarsAndSorting = function() {
    const favs = getFavoriteClubs();

  // 1. إعادة رسم مباريات اليوم مع الحفاظ على موضع التمرير بدون قفز
    if (window.activeSection === 'today' && Array.isArray(window.currentTodayMatches) && typeof renderTodayMatchesGrouped === 'function') {
      const prevScrollY = window.scrollY;
      renderTodayMatchesGrouped(window.currentTodayMatches);
      requestAnimationFrame(() => window.scrollTo({ top: prevScrollY, behavior: 'instant' }));
    }
    // 2. نجوم المفضلة في جدول الترتيب الرسمي
    document.querySelectorAll('#official-standings-tbody tr').forEach(tr => {
      const cells = tr.querySelectorAll('td');
      if (cells.length < 3) return;
      const teamWrap = cells[1].querySelector('div') || cells[1];
      const nameEl = cells[1].querySelector('.team-title-sm');
      if (!nameEl) return;

      const rawName = nameEl.textContent.trim();
      if (!rawName || rawName.length < 2) return;

      let starBtn = teamWrap.querySelector('.dp-fav-star-btn');
      if (!starBtn) {
        starBtn = document.createElement('button');
        starBtn.type = 'button';
        starBtn.className = 'dp-fav-star-btn';
        starBtn.title = 'إضافة إلى أنديتي المفضلة';
        starBtn.onclick = (ev) => window.toggleFavoriteClub(rawName, ev);
        teamWrap.prepend(starBtn);
      }
      const active = isClubFavorite(rawName);
      starBtn.textContent = active ? '⭐' : '☆';
      starBtn.classList.toggle('is-fav', active);
    });

    // 3. تمييز وتثبيت مباريات الأندية المفضلة في مباريات الجولة
    const listParent = document.getElementById('fixtures-container');
    if (listParent) {
      const cards = Array.from(listParent.querySelectorAll('.fixture-card'));
      const existingBar = document.getElementById('dp-fav-bar-fixtures');

      if (cards.length === 0 || favs.length === 0) {
        if (existingBar) existingBar.remove();
        onlyFavoritesFilter = false;
      } else {
        let bar = existingBar;
        if (!bar && listParent.parentElement) {
          bar = document.createElement('div');
          bar.id = 'dp-fav-bar-fixtures';
          bar.style.cssText = 'display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; background:var(--card); border:1px solid rgba(245,158,11,0.35); padding:8px 12px; border-radius:12px; margin-bottom:12px; font-size:0.78rem;';
          listParent.parentElement.insertBefore(bar, listParent);
        }
        if (bar) {
          bar.innerHTML = `
            <span style="color:var(--accent-gold-bright); font-weight:800;">⭐ أنديتك المفضلة (${favs.length}) مثبتة في الأعلى</span>
            <button type="button" class="retry-btn" style="padding:4px 12px; font-size:0.72rem;">
              ${onlyFavoritesFilter ? 'عرض جميع المباريات' : 'عرض المفضلة فقط'}
            </button>
          `;
          const toggleBtn = bar.querySelector('button');
          if (toggleBtn) {
            toggleBtn.onclick = () => {
              onlyFavoritesFilter = !onlyFavoritesFilter;
              window.refreshFavoriteStarsAndSorting();
            };
          }
        }
      }

      cards.forEach(card => {
        let cardHasFav = false;
        card.querySelectorAll('.team-title').forEach(el => {
          const tName = el.textContent.replace(/[☆⭐]/g, '').trim();
          if (!tName || tName.length < 2) return;
          if (isClubFavorite(tName)) cardHasFav = true;

          let sBtn = el.querySelector('.dp-fav-star-btn');
          if (!sBtn) {
            sBtn = document.createElement('button');
            sBtn.type = 'button';
            sBtn.className = 'dp-fav-star-btn';
            sBtn.onclick = (ev) => window.toggleFavoriteClub(tName, ev);
            el.appendChild(sBtn);
          }
          const act = isClubFavorite(tName);
          sBtn.textContent = act ? '⭐' : '☆';
          sBtn.classList.toggle('is-fav', act);
        });

        card.classList.toggle('dp-fav-match-card', cardHasFav);
        card.style.display = (onlyFavoritesFilter && favs.length > 0 && !cardHasFav) ? 'none' : '';
      });

      if (favs.length > 0) {
        const favCards = cards.filter(c => c.classList.contains('dp-fav-match-card'));
        favCards.reverse().forEach(fc => {
          if (listParent.firstChild !== fc) listParent.insertBefore(fc, listParent.firstChild);
        });
      }
    }
  };

  // إيماءة السحب للأسفل لإغلاق النوافذ السفلية على الجوال (Swipe-to-Dismiss Bottom Sheets)
  // إيماءة السحب للأسفل لإغلاق النوافذ السفلية على الجوال بدون تعارض مع التمرير الداخلي
  function initMobileBottomSheetGestures() {
    let startX = 0;
    let startY = 0;
    let deltaY = 0;
    let lockedOut = false;
    let activeSheet = null;

    function hasScrolledAncestor(target, stopAt) {
      let node = target;
      while (node && node !== stopAt) {
        if (node.scrollTop > 2) return true;
        node = node.parentElement;
      }
      return Boolean(stopAt && stopAt.scrollTop > 2);
    }

    document.addEventListener('touchstart', (e) => {
      if (window.innerWidth > 768 || !e.touches || e.touches.length !== 1) return;
      const sheet = e.target.closest('.modal-content');
      if (!sheet) return;

      // تجاهل اللمس على الحقول والأشرطة المنزلقة والجداول الأفقية وقوائم البحث
      if (e.target.closest('input, select, textarea, .table-container, .dp-subtabs, .dp-ev-filters, .dp-search-results, .quiz-review-list')) {
        return;
      }
      if (hasScrolledAncestor(e.target, sheet)) return;

      activeSheet = sheet;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      deltaY = 0;
      lockedOut = false;
      activeSheet.style.transition = 'none';
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
      if (!activeSheet || lockedOut || !e.touches || e.touches.length !== 1) return;
      const dx = Math.abs(e.touches[0].clientX - startX);
      const dy = e.touches[0].clientY - startY;

      // إذا كانت حركة الإصبع أفقية أو للأعلى، نلغي سحب النافذة فوراً
      if (dy < 0 || dx > Math.max(12, dy * 0.75)) {
        lockedOut = true;
        activeSheet.style.transform = '';
        return;
      }

      if (dy > 8) {
        deltaY = dy;
        activeSheet.style.transform = `translateY(${Math.min(dy, 260)}px)`;
      }
    }, { passive: true });

    document.addEventListener('touchend', () => {
      if (!activeSheet) return;
      const sheet = activeSheet;
      activeSheet = null;
      sheet.style.transition = 'transform 0.2s ease';

      if (!lockedOut && deltaY > 95) {
        const overlay = sheet.closest('.modal-overlay');
        sheet.style.transform = '';
        if (overlay) {
          if (overlay.id && typeof window.closeModal === 'function') {
            window.closeModal(overlay.id);
          } else {
            overlay.style.display = 'none';
            document.body.style.overflow = '';
          }
        }
      } else {
        sheet.style.transform = '';
      }
    });
  }

  // مراقب حالة الإنترنت (Offline / Online Graceful Feedback)
  function initNetworkStatusWatcher() {
    const showNetBanner = (isOnline) => {
      let el = document.getElementById('dp-network-banner');
      if (isOnline) {
        if (el) el.remove();
        showMobileToast('تمت استعادة الاتصال بالإنترنت — جاري التحديث...');
        refreshCurrentView(false);
        return;
      }
      if (!el) {
        el = document.createElement('div');
        el.id = 'dp-network-banner';
        el.style.cssText = 'position:fixed;bottom:74px;left:50%;transform:translateX(-50%);background:#7f1d1d;border:1px solid #ef4444;color:#fff;padding:8px 16px;border-radius:99px;font-size:0.78rem;font-weight:800;z-index:3500;box-shadow:0 8px 24px rgba(0,0,0,0.5);white-space:nowrap;';
        el.textContent = 'انقطع الاتصال بالإنترنت — يتم عرض البيانات المخزنة مؤقتاً';
        document.body.appendChild(el);
      }
    };
    window.addEventListener('offline', () => showNetBanner(false));
    window.addEventListener('online', () => showNetBanner(true));
  }

  registerPWAEngine();
  initMobileBottomSheetGestures();
  initNetworkStatusWatcher();

  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', buildMobileBottomNav);
  } else {
    buildMobileBottomNav();
  }
})();