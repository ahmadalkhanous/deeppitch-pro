// =========================================================
// DeepPitch Pro - Views, Navigation & League Rules Engine
// =========================================================

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

function getLeagueRulesConfig(leagueCode) {
  const code = (leagueCode || 'PL').toUpperCase();
  return LEAGUE_RULES_ENGINE[code] || LEAGUE_RULES_ENGINE['PL'];
}

// =========================================================
// 1. إدارة التنقل بين الشاشات الرئيسية
// =========================================================
function activateSection(section) {
  window.activeSection = section;
  if (typeof activeSection !== 'undefined') activeSection = section;

  const hubGrid = document.getElementById('hub-grid-container');
  if (hubGrid) hubGrid.style.display = 'none';

  const welcome = document.getElementById('welcome-placeholder');
  if (welcome) welcome.style.display = 'none';

  const backBar = document.getElementById('mobile-back-bar');
  const viewTitle = document.getElementById('mobile-view-title');
  if (backBar) {
    backBar.style.display = 'flex';
    const sectionTitles = {
      'fixtures': '📅 مباريات الجولة والرادار',
      'today': '🔴 مباريات اليوم المباشرة',
      'standings': '🏆 جدول الترتيب والهدافين',
      'projections': '🔮 محاكي نهاية الموسم',
      'fdr': '🗓️ صعوبة المباريات (FDR)',
      'news': '📰 غرفة الأخبار الرياضية',
      'history': '🏛️ موسوعة وأرشيف الدوريات',
      'radar': '🕸️ استوديو المقارنة الرادارية ومحاكي القمم',
      'transfers': '💼 بورصة الانتقالات وتجديد العقود',
      'quiz': '🎮 ساحة التحدي الكروي التفاعلي'
    };
    if (viewTitle) viewTitle.innerText = sectionTitles[section] || 'عرض النتائج';
  }

  const mainMenu = document.getElementById('main-menu-section');
  const needsLeague = ['fixtures', 'standings', 'projections', 'fdr', 'history'].includes(section);
  if (mainMenu) mainMenu.style.display = needsLeague ? 'block' : 'none';

  const allViews = ['fixtures', 'today', 'standings', 'projections', 'fdr', 'news', 'history', 'radar', 'transfers','quiz'];
  allViews.forEach(v => {
    const el = document.getElementById(`${v}-view`);
    if (el) el.style.display = (v === section) ? 'block' : 'none';
  });

  if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) {
    clearTimeout(todayPollingTimeout);
    todayPollingTimeout = null;
  }

  window.scrollTo(0, 0);

  const league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  if (section === 'today') loadTodayMatches();
  else if (section === 'news') loadNewsFeed();
  else if (section === 'fixtures') loadGameweek(league);
  else if (section === 'standings') loadOfficialStandingsAndScorers(league);
  else if (section === 'projections') loadProjections(league);
  else if (section === 'fdr') loadFDR(league);
  else if (section === 'history') loadLeagueHistory(league);
  else if (section === 'radar') initRadarClashStudio();
  else if (section === 'transfers') loadMercatoHub();
  else if (section === 'quiz') loadQuizArena();
}

function goBackToMainMenu() {
  const allViews = ['fixtures', 'today', 'standings', 'projections', 'fdr', 'news', 'history', 'radar', 'transfers','quiz'];
  allViews.forEach(v => {
    const el = document.getElementById(`${v}-view`);
    if (el) el.style.display = 'none';
  });

  const mainMenu = document.getElementById('main-menu-section');
  if (mainMenu) mainMenu.style.display = 'none';

  const backBar = document.getElementById('mobile-back-bar');
  if (backBar) backBar.style.display = 'none';

  const hubGrid = document.getElementById('hub-grid-container');
  if (hubGrid) hubGrid.style.display = 'grid';

  const welcome = document.getElementById('welcome-placeholder');
  if (welcome) welcome.style.display = 'block';

  document.querySelectorAll('.hub-card').forEach(c => c.classList.remove('active'));

  if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) {
    clearTimeout(todayPollingTimeout);
    todayPollingTimeout = null;
  }

  window.scrollTo(0, 0);
}

function refreshCurrentView() {
  const league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  const sec = window.activeSection || (typeof activeSection !== 'undefined' ? activeSection : 'fixtures');

  if (sec === 'fixtures') loadGameweek(league);
  else if (sec === 'standings') loadOfficialStandingsAndScorers(league);
  else if (sec === 'projections') loadProjections(league);
  else if (sec === 'fdr') loadFDR(league);
  else if (sec === 'today') loadTodayMatches();
  else if (sec === 'news') loadNewsFeed(true);
  else if (sec === 'history') loadLeagueHistory(league);
  else if (sec === 'radar') initRadarClashStudio();
  else if (sec === 'transfers') loadMercatoHub(true);
  else if (sec === 'quiz') loadQuizArena(true);
}
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

  container.innerHTML = fixtures.map((f, idx) => `
    <div class="fixture-card" onclick="openModal(${idx})">
      <div class="fixture-header">
        <span>الجولة ${f.gameweek} • 🕒 ${f.kickoff_time}</span>
        <span class="radar-pill" style="background: ${f.edge.color}20; color: ${f.edge.color}; border: 1px solid ${f.edge.color};">
          ${f.edge.label}
        </span>
      </div>

      <div class="teams-matchup">
        <div class="team-col">
          <div class="crest-wrapper"><img src="${f.home.crest}" alt="${f.home.short}" onerror="this.src='https://via.placeholder.com/60?text=FC'"></div>
          <div class="team-title">${f.home.short}</div>
          <div class="team-elo">Elo ${f.home.elo}</div>
          <div class="form-badges">
            ${(f.home.form || []).map(res => `<span class="badge-f form-${res.toLowerCase()}">${res}</span>`).join('')}
          </div>
        </div>

        <div class="vs-center" style="text-align:center;">
          <div class="score-badge">${f.predicted_score}</div>
          <div style="font-size:0.72rem; color:var(--muted); margin-top:4px; font-weight:700;">ثقة (${f.score_confidence}%)</div>
        </div>

        <div class="team-col">
          <div class="crest-wrapper"><img src="${f.away.crest}" alt="${f.away.short}" onerror="this.src='https://via.placeholder.com/60?text=FC'"></div>
          <div class="team-title">${f.away.short}</div>
          <div class="team-elo">Elo ${f.away.elo}</div>
          <div class="form-badges">
            ${(f.away.form || []).map(res => `<span class="badge-f form-${res.toLowerCase()}">${res}</span>`).join('')}
          </div>
        </div>
      </div>

      <div class="prob-bar">
        <div class="prob-home" style="width: ${f.home.prob}%"></div>
        <div class="prob-draw" style="width: ${f.draw_prob}%"></div>
        <div class="prob-away" style="width: ${f.away.prob}%"></div>
      </div>

      <div class="prob-labels">
        <span>${f.home.short}: <strong>${f.home.prob}%</strong></span>
        <span>تعادل: <strong>${f.draw_prob}%</strong></span>
        <span>${f.away.short}: <strong>${f.away.prob}%</strong></span>
      </div>

      <div class="market-tags">
        <div class="tag-item">Over 2.5: <strong>${f.markets.over_25}%</strong></div>
        <div class="tag-item">BTTS: <strong>${f.markets.btts_yes}%</strong></div>
        <div class="tag-item">xG: <strong>${f.home.xg} - ${f.away.xg}</strong></div>
      </div>

      <div style="text-align:center; font-size:0.75rem; color:var(--accent-cyan); margin-top:10px;">
        🧪 انقر لعرض تقرير الرادار وسجل المواجهات المباشرة ومختبر السيناريوهات
      </div>
    </div>
  `).join('');
}

async function loadGameweek(leagueCode) {
  const container = document.getElementById('fixtures-container');
  if (!container) return;

  if (typeof BROWSER_CACHE !== 'undefined' && BROWSER_CACHE.fixtures && BROWSER_CACHE.fixtures[leagueCode] && BROWSER_CACHE.fixtures[leagueCode].length > 0) {
    window.currentFixtures = BROWSER_CACHE.fixtures[leagueCode];
    renderFixturesList(window.currentFixtures);
    return;
  }

  container.innerHTML = '<div class="loading-state">جاري فحص مؤشرات الصدمة ورادار التعثر...</div>';

  try {
    const res = await fetch(`/api/gameweek/${leagueCode}`);
    const data = await res.json();
    window.currentFixtures = data.fixtures || [];
    if (typeof BROWSER_CACHE !== 'undefined' && window.currentFixtures.length > 0) {
      BROWSER_CACHE.fixtures[leagueCode] = window.currentFixtures;
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
// 3. مباريات اليوم المباشرة
// =========================================================
async function loadTodayMatches() {
  const container = document.getElementById('today-matches-container');
  const dateTxt = document.getElementById('today-date-txt');
  const now = new Date();
  if (dateTxt) dateTxt.innerText = now.toLocaleDateString('ar-EG', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  if (!container) return;

  try {
    const res = await fetch('/api/todays_matches');
    const data = await res.json();
    const matches = data.matches || [];
    window.currentTodayMatches = matches;

    if (matches.length === 0) {
      container.innerHTML = '<div class="loading-state" style="grid-column: 1/-1;">لا توجد مباريات مجدولة لليوم في البطولات المدعومة.</div>';
      scheduleNextPoll(300000, "لا توجد مباريات - فحص دوري كل 5 دقائق");
      return;
    }

    container.innerHTML = matches.map((m, idx) => `
      <div class="today-card ${m.is_live ? 'live-match' : ''}" onclick="openTodayMatchModal(${idx})" style="cursor: pointer; transition: transform 0.2s;">
        <div class="today-header">
          <span>${m.league_flag || '⚽'} ${m.league_name}</span>
          ${m.is_live 
            ? `<span class="live-badge"><span class="live-dot-pulse"></span> ${m.status_text}</span>` 
            : `<span style="color:var(--muted);">${m.status_text} • 🕒 ${m.kickoff_time}</span>`}
        </div>

        <div class="today-body">
          <div class="today-team">
            <img src="${m.home_crest}" width="44" height="44" onerror="this.src='https://via.placeholder.com/44?text=FC'">
            <div style="font-weight:800; font-size:0.92rem;">${m.home_team}</div>
          </div>

          <div class="today-score-box">
            ${m.state === 'pre' 
              ? `<div style="font-size:1.05rem; color:var(--accent-gold);">${m.kickoff_time}</div>` 
              : `<span style="color:${m.is_live ? '#ff5252' : 'var(--text)'}; font-size:1.25rem; font-weight:900;">${m.home_score} - ${m.away_score}</span>`}
          </div>

          <div class="today-team">
            <img src="${m.away_crest}" width="44" height="44" onerror="this.src='https://via.placeholder.com/44?text=FC'">
            <div style="font-weight:800; font-size:0.92rem;">${m.away_team}</div>
          </div>
        </div>

        <div class="today-meta">
          <div>🏟️ <strong>الملعب:</strong> ${m.venue}</div>
          <div>📺 <strong>القناة:</strong> ${m.channel}</div>
          <div style="grid-column: 1/-1;">🎙️ <strong>المعلق:</strong> ${m.commentator}</div>
        </div>

       <div style="text-align:center; font-size:0.75rem; color:var(--accent-gold); font-weight:800; margin-top:10px; border-top:1px dashed #1e293b; padding-top:8px;">
          🎙️ انقر لدخول استوديو المحللين الأربعة والإحصائيات والتشكيلة
        </div>
      </div>
    `).join('');

    const hasLiveMatch = matches.some(m => m.is_live);
    scheduleNextPoll(hasLiveMatch ? 35000 : 300000, hasLiveMatch ? "مباراة جارية - تحديث مباشر كل 35 ثانية" : "المباريات مجدولة أو منتهية - تحديث هادئ كل 5 دقائق");
  } catch (e) {
    scheduleNextPoll(60000, "تعذر التحديث - إعادة المحاولة بعد دقيقة");
  }
}

function scheduleNextPoll(delayMs, statusMessage) {
  const statusTxt = document.getElementById('polling-status-txt');
  if (statusTxt) statusTxt.innerText = statusMessage;
  if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) clearTimeout(todayPollingTimeout);
  if (window.activeSection === 'today') {
    todayPollingTimeout = setTimeout(loadTodayMatches, delayMs);
  }
}

// =========================================================
// 4. جدول الترتيب الرسمي والهدافين (مربوط بنظام كل بطولة و UCL)
// =========================================================
// =========================================================
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

  let tabs = [{ key: 'ALL', label: 'الكل 📋' }];
  if (code === 'UNL') {
    tabs.push(
      { key: 'LVL_A', label: 'المستوى A 🏆' },
      { key: 'LVL_B', label: 'المستوى B ⬆️' },
      { key: 'LVL_C', label: 'المستوى C ⬆️' },
      { key: 'LVL_D', label: 'المستوى D ⬆️' }
    );
  } else {
    const seenGroups = [];
    items.forEach(t => {
      if (t.group_name && !seenGroups.includes(t.group_name)) seenGroups.push(t.group_name);
    });
    seenGroups.forEach(g => tabs.push({ key: g, label: g }));
  }

  return `
    <div class="dp-h-scroll-bar" style="display:flex; gap:8px; flex-wrap:nowrap; overflow-x:auto; margin-bottom:14px; padding:8px 10px; background:#070b15; border:1px solid var(--card-border); border-radius:14px;">
      ${tabs.map(tb => {
        const isAct = window._activeGroupFilter === tb.key;
        return `
          <button onclick="${onClickFnName}('${tb.key}')" style="flex:0 0 auto; white-space:nowrap; background:${isAct ? 'rgba(0,230,118,0.18)' : '#0f172a'}; color:${isAct ? 'var(--accent-green)' : '#cbd5e1'}; border:1px solid ${isAct ? 'var(--accent-green)' : '#1e293b'}; padding:5px 14px; border-radius:20px; font-size:0.78rem; font-weight:800; cursor:pointer; transition:all 0.2s;">
            ${tb.label}
          </button>
        `;
      }).join('')}
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
    tbody.innerHTML = '<tr><td colspan="11" class="loading-state">لا تتوفر بيانات ترتيب حالياً لهذا الاختيار.</td></tr>';
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
          <td colspan="10" style="background:linear-gradient(90deg, rgba(0,230,118,0.14) 0%, rgba(0,210,255,0.08) 50%, rgba(13,20,36,0.95) 100%); border-top:2px solid var(--accent-green); border-bottom:1px solid var(--card-border); padding:10px 14px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <span style="font-weight:900; font-size:0.92rem; color:var(--accent-green); display:flex; align-items:center; gap:6px;">
                <span>📌</span> <span>${t.group_name}</span>
              </span>
              ${ruleSub ? `<span style="font-size:0.74rem; color:#cbd5e1; font-weight:700; background:rgba(5,8,17,0.65); padding:3px 10px; border-radius:12px; border:1px solid #1e293b;">${ruleSub}</span>` : ''}
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
    let statusBadge = "";
    if (zoneClass) {
      const dotCol = zoneClass === "rank-ucl" ? "var(--accent-cyan)" : (zoneClass === "rank-uel" ? "var(--accent-gold)" : "var(--accent-red)");
      const dotShadow = zoneClass === "rank-ucl" ? "rgba(0,210,255,0.55)" : (zoneClass === "rank-uel" ? "rgba(255,214,0,0.55)" : "rgba(255,82,82,0.55)");
      statusBadge = `<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${dotCol}; box-shadow:0 0 8px ${dotShadow}; margin-right:6px; flex-shrink:0;"></span>`;
    }

    rowsHtml.push(`
      <tr>
        <td class="${zoneClass}"><strong>${t.rank}</strong></td>
        <td class="team-col-cell">
          <div style="display:flex; align-items:center; gap:6px;">
            <img src="${t.crest}" width="20" height="20" onerror="this.src='https://via.placeholder.com/20?text=FC'">
            <strong class="team-title-sm">${t.short_name || t.team_name}</strong>
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
        <td class="col-hide-mobile-sm">
          <div style="display:flex; gap:3px;">
            ${(t.form || []).map(f => `<span class="badge-f form-${f.toLowerCase()}">${f}</span>`).join('')}
          </div>
        </td>
      </tr>
    `);
  });

  tbody.innerHTML = rowsHtml.join('');
}

async function loadOfficialStandingsAndScorers(leagueCode) {
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
    tbody.innerHTML = '<tr><td colspan="11" class="loading-state">جاري سحب الترتيب الرسمي المباشر من الـ API...</td></tr>';
  }
  if (scorersList) {
    scorersList.innerHTML = '<div class="loading-state">جاري سحب قائمة الهدافين...</div>';
  }

  try {
    const [sRes, scRes] = await Promise.all([
      fetch(`/api/official_standings/${leagueCode}`),
      fetch(`/api/top_scorers/${leagueCode}`)
    ]);

    const sData = await sRes.json();
    const scData = await scRes.json();

    const standings = sData.standings || (Array.isArray(sData) ? sData : []);
    const scorers = scData.scorers || (Array.isArray(scData) ? scData : []);

    window._cachedStandingsData = standings;
    renderStandingsTableRows(standings, leagueCode);

    if (scorersList) {
      if (scorers.length === 0) {
        scorersList.innerHTML = '<div class="loading-state">لا توجد إحصائيات هدافين مسجلة حالياً.</div>';
      } else {
        scorersList.innerHTML = scorers.map(s => {
          let rankBadgeClass = s.rank === 1 ? 'rank-1' : s.rank === 2 ? 'rank-2' : s.rank === 3 ? 'rank-3' : '';
          let avatarHtml = s.headshot
            ? `<img src="${s.headshot}" width="34" height="34" style="border-radius:50%; object-fit:cover; background:#1a233a; border:1px solid var(--card-border);" onerror="this.style.display='none'">`
            : '';

          return `
            <div class="scorer-row">
              <div style="display:flex; align-items:center; gap:10px;">
                <div class="scorer-rank ${rankBadgeClass}">${s.rank}</div>
                ${avatarHtml}
                <div>
                  <div style="font-weight:800; font-size:0.9rem;">${s.name}</div>
                  <div style="font-size:0.75rem; color:var(--muted); display:flex; align-items:center; gap:5px;">
                    <img src="${s.crest}" width="14" height="14" onerror="this.style.display='none'">
                    <span>${s.team}</span>
                  </div>
                </div>
              </div>
              <div style="font-size:1.2rem; font-weight:900; color:var(--accent-gold);">
                ${s.goals} <span style="font-size:0.75rem; color:var(--muted); font-weight:400;">أهداف</span>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (e) {
    if (tbody) tbody.innerHTML = '<tr><td colspan="11" class="loading-state" style="color:var(--accent-red);">تعذر جلب بيانات الترتيب.</td></tr>';
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
          <td colspan="8" style="background:linear-gradient(90deg, rgba(0,230,118,0.14) 0%, rgba(0,210,255,0.08) 50%, rgba(13,20,36,0.95) 100%); border-top:2px solid var(--accent-green); border-bottom:1px solid var(--card-border); padding:10px 14px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <span style="font-weight:900; font-size:0.92rem; color:var(--accent-green);">📌 ${row.group_name}</span>
              ${ruleSub ? `<span style="font-size:0.74rem; color:#cbd5e1; font-weight:700; background:rgba(5,8,17,0.65); padding:3px 10px; border-radius:12px; border:1px solid #1e293b;">${ruleSub}</span>` : ''}
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
            <img src="${row.crest}" width="20" height="20" onerror="this.src='https://via.placeholder.com/20'">
            <strong>${row.name}</strong>
          </div>
        </td>
        <td>${row.played}</td>
        <td class="col-hide-mobile">${row.current_pts}</td>
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

async function loadProjections(leagueCode) {
  const tbody = document.getElementById('projections-tbody');
  if (!tbody) return;

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
    const res = await fetch(`/api/season_projections/${leagueCode}`);
    const data = await res.json();
    let dataList = data.projections || [];

    window._cachedProjData = dataList;
    renderProjectionsTableRows(dataList, leagueCode);
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--accent-red);">فشل جلب بيانات المحاكاة، يرجى المحاولة لاحقاً.</td></tr>';
  }
}


// =========================================================
// 6. مصفوفة صعوبة المباريات (FDR)
// =========================================================
async function loadFDR(leagueCode) {
  const tbody = document.getElementById('fdr-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:35px; color:var(--muted);">جاري بناء مصفوفة صعوبة المباريات الخمس القادمة...</td></tr>';

  try {
    const res = await fetch(`/api/fdr/${leagueCode}`);
    const data = await res.json();
    const dataList = data.fdr || [];

    if (dataList.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:25px; color:var(--muted);">لا تتوفر مواعيد مجدولة حالياً.</td></tr>';
      return;
    }

    tbody.innerHTML = dataList.map(row => `
      <tr>
        <td style="font-weight:800; color:var(--muted);">#${row.rank}</td>
        <td>
          <div style="display:flex; align-items:center; gap:6px;">
            <img src="${row.crest}" width="20" height="20" onerror="this.src='https://via.placeholder.com/20'">
            <strong>${row.name}</strong>
          </div>
        </td>
        <td>
          <span style="font-weight:900; font-size:0.95rem; color:${row.avg_difficulty <= 2.5 ? 'var(--accent-green)' : row.avg_difficulty >= 3.6 ? 'var(--accent-red)' : 'var(--accent-gold)'};">
            ${row.avg_difficulty}
          </span>
        </td>
        ${(row.fixtures || []).map(f => `
          <td style="text-align:center;">
            <div class="fdr-cell" style="background:${f.color};">
              <span class="fdr-diff-badge">${f.difficulty}</span>
              <span style="white-space:nowrap;">${f.opp_name}</span>
              <span class="fdr-tag-h">${f.venue_tag}</span>
            </div>
          </td>
        `).join('')}
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--accent-red);">فشل جلب مصفوفة الصعوبة، يرجى المحاولة لاحقاً.</td></tr>';
  }
}

// =========================================================
// 7. غرفة الأخبار الرياضية الحية (FIFO 20)
// =========================================================
let currentNewsItems = [];

async function loadNewsFeed(forceRefresh = false) {
  const container = document.getElementById('news-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-state" style="grid-column: 1/-1;">جاري جلب أحدث الأخبار الرياضية...</div>';

  try {
    const res = await fetch(`/api/news?refresh=${forceRefresh}`);
    const data = await res.json();
    const list = data.news || [];
    currentNewsItems = list;

    if (list.length === 0) {
      container.innerHTML = '<div class="loading-state" style="grid-column: 1/-1;">لا توجد أخبار متاحة حالياً.</div>';
      return;
    }

    container.innerHTML = list.map((item, idx) => `
      <div class="news-item-card" onclick="openNewsArticle(${idx})">
        ${item.image_url ? `<img src="${item.image_url}" class="news-card-thumb" onerror="this.style.display='none'">` : ''}
        <div class="news-card-content">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.72rem; color:var(--muted);">🕒 ${item.published_time || 'حديثاً'}</span>
            <span class="hub-badge" style="color:var(--accent-gold); border-color:var(--accent-gold); font-size:0.65rem;">#${idx + 1}</span>
          </div>
          <h3 class="news-card-title">${item.title}</h3>
          <p class="news-card-desc">${item.summary || 'انقر لقراءة التقرير والتفاصيل الكاملة...'}</p>
          <div style="font-size:0.75rem; color:var(--accent-cyan); font-weight:800; margin-top:8px;">
            قراءة الخبر كاملاً 📖 ↗
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = '<div class="loading-state" style="grid-column: 1/-1; color:var(--accent-red);">تعذر تحميل الأخبار، يرجى المحاولة لاحقاً.</div>';
  }
}

function openNewsArticle(idx) {
  const item = currentNewsItems[idx];
  if (!item) return;

  let modal = document.getElementById('news-reader-modal');
  // إنشاء النافذة ديناميكياً إذا لم تكن موجودة في ملف HTML
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'news-reader-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-content" style="max-width: 600px;">
        <button class="close-btn" onclick="closeModal('news-reader-modal')">&times;</button>
        <div id="news-modal-date" style="font-size:0.78rem; color:var(--accent-gold); margin-bottom:8px; font-weight:700;"></div>
        <h3 id="news-modal-title" style="font-size:1.15rem; font-weight:900; line-height:1.5; margin-bottom:14px; color:#fff;"></h3>
        <img id="news-modal-img" src="" style="width:100%; max-height:260px; object-fit:cover; border-radius:14px; margin-bottom:14px; display:none; border:1px solid var(--card-border);">
        <p id="news-modal-body" style="font-size:0.92rem; line-height:1.8; color:#cbd5e1; margin-bottom:18px;"></p>
        <div style="text-align:center;">
          <a id="news-modal-link" href="#" target="_blank" rel="noopener noreferrer" class="ai-btn" style="text-decoration:none; display:inline-block;">
            🌐 قراءة الخبر من المصدر الأصلي ↗
          </a>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  const img = document.getElementById('news-modal-img');
  const title = document.getElementById('news-modal-title');
  const body = document.getElementById('news-modal-body');
  const dateEl = document.getElementById('news-modal-date');
  const link = document.getElementById('news-modal-link');

  if (title) title.innerText = item.title;
  if (body) body.innerText = item.summary || item.title;
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
}

document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
    document.body.style.overflow = '';
  }
});

// =========================================================
// 8. محرك عرض الأرشيف التاريخي وموسوعة الدوريات الشاملة
// =========================================================
window._currentHistorySeasons = [];

function filterHistorySeasons(query) {
  const tbody = document.getElementById('history-seasons-tbody');
  const countBadge = document.getElementById('history-filtered-count');
  if (!tbody) return;

  const q = (query || '').trim().toLowerCase();
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

  tbody.innerHTML = filtered.map(s => `
    <tr>
      <td style="color:var(--muted); font-size:0.75rem;">#${list.length - list.indexOf(s)}</td>
      <td style="font-weight:900; color:var(--accent-cyan); white-space:nowrap;">${s.season}</td>
      <td style="font-weight:900; color:var(--accent-gold); max-width:145px; overflow:hidden; text-overflow:ellipsis;">🏆 ${s.champion}</td>
      <td style="font-size:0.8rem; color:#e2e8f0; max-width:130px; overflow:hidden; text-overflow:ellipsis;">${s.runner_up || '-'}</td>
      <td style="font-size:0.75rem; color:#94a3b8; max-width:180px; overflow:hidden; text-overflow:ellipsis;" title="${(s.top4 || []).join(' • ')}">${(s.top4 || []).slice(0, 3).join(' • ')}</td>
      <td style="font-size:0.78rem; color:#00e676; font-weight:700; max-width:160px; overflow:hidden; text-overflow:ellipsis;">${s.top_scorer || '-'}</td>
    </tr>
  `).join('');
}

async function loadLeagueHistory(leagueCode) {
  const container = document.getElementById('history-container');
  if (!container) return;

  container.innerHTML = '<div class="loading-state">⏳ جاري سحب السجل التاريخي الكامل لجميع النسخ منذ التأسيس عبر الـ API...</div>';

  try {
    const res = await fetch(`/api/league_history/${leagueCode}`);
    const resData = await res.json();

    if (!resData || resData.status !== 'success' || !resData.data) {
      const msg = (resData && resData.message) ? resData.message : 'لا تتوفر سجلات تاريخية حالياً.';
      container.innerHTML = `<div class="loading-state" style="color:var(--accent-red);">${msg}</div>`;
      return;
    }

    const d = resData.data;
    const rec = d.records || {};
    const titles = d.titles_table || [];
    const seasons = d.seasons || [];
    window._currentHistorySeasons = seasons;

    container.innerHTML = `
      <div style="max-width:1280px; margin:0 auto; background:var(--card); border:1px solid var(--card-border); border-radius:16px; padding:20px; margin-bottom:24px; box-shadow:0 8px 24px rgba(0,0,0,0.3);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--card-border); padding-bottom:14px; margin-bottom:18px; flex-wrap:wrap; gap:10px;">
          <div>
            <h2 style="font-size:1.35rem; color:var(--text); margin:0;">${d.flag} ${d.league_name}</h2>
            <div style="font-size:0.82rem; color:var(--muted); margin-top:4px;">
              تاريخ التأسيس: <strong style="color:#fff;">${d.founded}</strong> •
              إجمالي النسخ المؤرشفة: <strong style="color:var(--accent-green);">${d.total_editions || seasons.length} نسخة تاريخية</strong> •
              الأكثر تتويجاً: <strong style="color:var(--accent-gold);">${d.most_successful}</strong>
            </div>
          </div>
          <span class="hub-badge" style="color:var(--accent-gold); border-color:var(--accent-gold); font-size:0.8rem;">الموسوعة الرسمية الكاملة 🏛️</span>
        </div>

        <h4 style="font-size:0.98rem; color:var(--accent-cyan); margin-bottom:12px;">🌟 الأرقام القياسية وأساطير البطولة عبر التاريخ</h4>
        <div class="dp-h-scroll-bar" style="margin-bottom:22px; gap:12px;">
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #00e676; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">⚽ الهداف التاريخي للبطولة</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.top_scorer || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #00d2ff; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🎯 الأكثر صناعة للأهداف تاريخياً</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.most_assists || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #ffd600; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🛡️ عميد المشاركات (الأكثر لعباً)</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.most_apps || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #38bdf8; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🧤 الأكثر حفاظاً على نظافة الشباك</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.most_clean_sheets || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #facc15; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🟨 الأكثر تلقياً للبطاقات الصفراء</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.most_yellows || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #ff5252; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🟥 الأكثر تلقياً للبطاقات الحمراء</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.most_reds || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #a855f7; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🔥 هداف موسم واحد (رقم قياسي)</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.single_season_scorer || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #ec4899; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🚀 أقوى هجوم لفريق في موسم واحد</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.team_goals_season || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #10b981; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🧱 أطول سلسلة لاهزيمة تاريخياً</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.unbeaten_streak || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #f97316; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">💥 أكبر فوز في تاريخ المسابقة</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.biggest_win || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid #06b6d4; border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">🧠 المدرب الأكثر تتويجاً باللقب</div>
            <div style="font-weight:900; font-size:0.9rem; color:#fff; margin-top:4px;">${rec.top_manager || '-'}</div>
          </div>
          <div style="background:#0c121e; border:1px solid var(--card-border); border-right:4px solid var(--accent-gold); border-radius:10px; padding:10px 14px;">
            <div style="font-size:0.74rem; color:var(--muted);">⚡ أعلى رصيد نقطي في موسم واحد</div>
            <div style="font-weight:900; font-size:0.9rem; color:var(--accent-gold); margin-top:4px;">${rec.record_pts_season || '-'}</div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); gap:18px;" class="standings-layout">
          <div class="data-card" style="margin:0;">
            <h4 style="font-size:0.95rem; color:var(--accent-gold); margin-bottom:12px;">🏆 السجل الذهبي للأندية المتوجة (${titles.length} نادٍ)</h4>
            <div class="table-container" style="max-height:540px; overflow-y:auto;">
              <table class="styled-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>النادي</th>
                    <th style="text-align:center;">الألقاب 🥇</th>
                    <th style="text-align:center;">الوصيف 🥈</th>
                    <th style="text-align:center;">آخر لقب</th>
                  </tr>
                </thead>
                <tbody>
                  ${titles.map((t, idx) => `
                    <tr>
                      <td style="color:var(--muted); font-weight:700;">${idx + 1}</td>
                      <td style="font-weight:800; color:#fff;">${t.club}</td>
                      <td style="text-align:center; font-weight:900; color:var(--accent-gold); font-size:1.08rem;">${t.titles}</td>
                      <td style="text-align:center; color:var(--muted);">${t.runner_up}</td>
                      <td style="text-align:center; font-size:0.78rem; color:var(--accent-cyan);">${t.last_title || '-'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>

          <div class="data-card" style="margin:0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
              <h4 style="font-size:0.95rem; color:var(--accent-green); margin:0;">
                📜 سجل جميع النسخ منذ التأسيس (<span id="history-filtered-count">${seasons.length} نسخة</span>)
              </h4>
              <input
                type="text"
                placeholder="🔍 ابحث بالسنة، البطل، أو الهداف..."
                oninput="filterHistorySeasons(this.value)"
                style="background:#090e18; color:#fff; border:1px solid var(--card-border); border-radius:8px; padding:6px 12px; font-family:'Cairo', sans-serif; font-size:0.8rem; width:240px;"
              >
            </div>
            <div class="table-container" style="max-height:540px; overflow-y:auto;">
              <table class="styled-table">
                <thead>
                  <tr>
                    <th>نسخة</th>
                    <th>الموسم</th>
                    <th>البطل 🥇</th>
                    <th>الوصيف 🥈</th>
                    <th>أوائل الترتيب / المربع الذهبي 🇪🇺</th>
                    <th>هداف النسخة ⚽</th>
                  </tr>
                </thead>
                <tbody id="history-seasons-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    `;

    filterHistorySeasons('');
  } catch (err) {
    container.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">تعذر تحميل السجلات التاريخية حالياً.</div>';
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
    { key: 'attack', label: 'الهجوم ⚔️' },
    { key: 'finishing', label: 'الحسم 🎯' },
    { key: 'form', label: 'الفورمة 🔥' },
    { key: 'dominance', label: 'الهيمنة 👑' },
    { key: 'defense', label: 'الدفاع 🛡️' },
    { key: 'elo', label: 'القوة Elo ⚡' }
  ];

  const cx = 210, cy = 175, maxR = 115;
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
    const lblP = getPoint(i, 1.27);
    const valA = teamA.radar[ax.key] || 50;
    const valB = teamB.radar[ax.key] || 50;
    return `
      <line x1="${cx}" y1="${cy}" x2="${endP.x}" y2="${endP.y}" stroke="#1e2d4a" stroke-width="1" />
      <text x="${lblP.x}" y="${lblP.y}" fill="#e2e8f0" font-size="11.5" font-weight="800" text-anchor="middle" dominant-baseline="middle">
        ${ax.label}
      </text>
      <text x="${lblP.x}" y="${parseFloat(lblP.y) + 14}" fill="#8292b0" font-size="10" font-weight="700" text-anchor="middle">
        (${valA} - ${valB})
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
    <svg viewBox="0 0 420 355" class="radar-svg-chart">
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
          <img src="${a.crest}" alt="${a.short}" onerror="this.src='https://via.placeholder.com/64?text=FC'">
          <div class="radar-club-name" style="color:var(--accent-green);">${a.short}</div>
          <div class="radar-club-sub">${a.league_flag} ${a.league_name} • المركز #${a.rank}</div>
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
          <img src="${b.crest}" alt="${b.short}" onerror="this.src='https://via.placeholder.com/64?text=FC'">
          <div class="radar-club-name" style="color:var(--accent-cyan);">${b.short}</div>
          <div class="radar-club-sub">${b.league_flag} ${b.league_name} • المركز #${b.rank}</div>
          <div class="radar-overall-pill" style="border-color:var(--accent-cyan); color:var(--accent-cyan);">Overall: ${b.overall}</div>
        </div>
      </div>

      <div style="background:#0c121e; padding:12px 16px; border-radius:12px; border:1px solid var(--card-border); margin-bottom:18px;">
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
          <h4 style="font-size:0.95rem; color:var(--text); margin-bottom:6px;">🕸️ البصمة التكتيكية السداسية (Opta Spider Radar)</h4>
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

          <div style="background:#090e18; border-right:4px solid var(--accent-gold); padding:12px; border-radius:10px; margin-top:12px; font-size:0.83rem; line-height:1.6; color:#e2e8f0;">
            <div style="font-weight:900; color:var(--accent-gold); margin-bottom:4px;">🧠 الخلاصة التكتيكية للمواجهة:</div>
            <div>${sim.tactical_summary.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff;">$1</strong>')}</div>
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
  const badgeText = data.is_projected ? 'محاكاة تكتيكية 90د 🔮' : 'زخم مباشر Sofascore 📈';

  return `
    <div class="momentum-studio-box">
      <div class="momentum-box-header">
        <div style="display:flex; align-items:center; gap:6px;">
          <span style="font-size:1.05rem;">📈</span>
          <strong style="font-size:0.88rem; color:#fff;">منحنى الزخم الهجومي وخريطة التسديدات</strong>
          <span class="hub-badge" style="color:var(--accent-gold); border-color:var(--accent-gold); font-size:0.65rem;">${badgeText}</span>
        </div>
        <div class="momentum-sub-tabs">
          <button id="${prefix}-btn-wave" class="mom-tab-btn active" onclick="switchMomentumSubTab('${prefix}', 'wave')">🌊 موجة الزخم</button>
          <button id="${prefix}-btn-shot" class="mom-tab-btn" onclick="switchMomentumSubTab('${prefix}', 'shot')">🎯 خريطة التسديدات</button>
        </div>
      </div>

      <div class="momentum-kpis-grid">
        <div class="mom-kpi-item" style="border-right:3px solid var(--accent-green);">
          <div class="mom-kpi-lbl">هيمنة ${data.home_team}</div>
          <div class="mom-kpi-val" style="color:var(--accent-green);">${data.home_dominance}% <span style="font-size:0.7rem; color:var(--muted);">(${data.peak_home_window})</span></div>
        </div>
        <div class="mom-kpi-item" style="border-right:3px solid var(--accent-gold);">
          <div class="mom-kpi-lbl">مؤشر الخطورة الهجومية</div>
          <div class="mom-kpi-val" style="color:var(--accent-gold);">${data.threat_home} <span style="color:var(--muted); font-size:0.72rem;">ضد</span> ${data.threat_away}</div>
        </div>
        <div class="mom-kpi-item" style="border-right:3px solid var(--accent-cyan);">
          <div class="mom-kpi-lbl">هيمنة ${data.away_team}</div>
          <div class="mom-kpi-val" style="color:var(--accent-cyan);">${data.away_dominance}% <span style="font-size:0.7rem; color:var(--muted);">(${data.peak_away_window})</span></div>
        </div>
      </div>

      <div id="${prefix}-wave-pane">
        ${waveSvg}
      </div>

      <div id="${prefix}-shot-pane" style="display:none;">
        ${shotSvg}
      </div>
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

async function loadMercatoHub(forceRefresh = false) {
  const container = document.getElementById('transfers-hub-container');
  if (!container) return;

  if (!forceRefresh && window._mercatoState.transfersList.length > 0) {
    renderMercatoWorkspace();
    return;
  }

  container.innerHTML = '<div class="loading-state">✈️ جاري تحميل بورصة الانتقالات العالمية وسجلات تجديد العقود...</div>';

  try {
    const res = await fetch(`/api/mercato?refresh=${forceRefresh}`);
    const data = await res.json();
    if (data && data.status === 'success') {
      window._mercatoState.transfersList = data.transfers || [];
      window._mercatoState.contractsList = data.contracts || [];
      window._mercatoState.tickerNews = data.ticker || [];
      renderMercatoWorkspace();
    } else {
      container.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">تعذر تحميل بيانات بورصة الانتقالات حالياً.</div>';
    }
  } catch (e) {
    container.innerHTML = '<div class="loading-state" style="color:var(--accent-red);">حدث خطأ في الاتصال بالسيرفر، يرجى المحاولة لاحقاً.</div>';
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
    <span class="ticker-item">${item}</span>
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
            value="${st.searchQuery}"
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

    if (isTransfersPage) {
      // ==================== تصميم بطاقة الانتقال العصرية الواضحة ====================
      const notePrefix = item.status === 'failed'
        ? '🚫 سبب فشل الصفقة:'
        : (item.status === 'done' ? '✅ تفاصيل الصفقة:' : '⏳ آخر التطورات:');

      return `
        <div class="transfer-card ${sMeta.cls}" onclick="openMercatoDetailModal('transfers', '${item.id}')">
          <!-- 1. رأس البطاقة: اللاعب/المدرب + حالة الصفقة -->
          <div class="t-card-top">
            <div class="t-person-box">
              <div class="t-avatar-wrap">
                <img src="${item.avatar}" alt="${item.name}" onerror="this.src='https://ui-avatars.com/api/?name=P&background=1e293b&color=fff&rounded=true'">
              </div>
              <div style="min-width:0;">
                <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <span class="t-person-name">${item.name}</span>
                  ${roleBadge}
                </div>
                <div class="t-person-sub">${item.position} • ${item.age} سنة • ${item.nationality}</div>
              </div>
            </div>
            <span class="t-status-pill ${sMeta.pillCls}">${item.status_label}</span>
          </div>

          <!-- 2. جسر الانتقال البصري الواضح (من النادي السابق ⬅️ إلى النادي الجديد) -->
          <div class="transfer-bridge-box">
            <div class="t-club-node">
              <div class="t-club-role-hint">النادي السابق</div>
              <img src="${item.from_crest}" alt="${item.from_club}" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=1e293b&color=fff&rounded=true'">
              <div class="t-club-name">${item.from_club}</div>
            </div>

            <div class="t-arrow-tunnel">
              <span class="t-deal-type-lbl">${item.deal_type}</span>
              <div class="t-animated-arrow ${item.status === 'failed' ? 'arrow-failed' : ''}">
                <span class="arrow-line"></span>
                <span class="arrow-head">${sMeta.arrowIcon}</span>
              </div>
              <span class="t-fee-lbl">${item.fee}</span>
            </div>

            <div class="t-club-node">
              <div class="t-club-role-hint" style="color:var(--accent-cyan);">النادي الجديد</div>
              <img src="${item.to_crest}" alt="${item.to_club}" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=1e293b&color=fff&rounded=true'">
              <div class="t-club-name" style="color:#fff;">${item.to_club}</div>
            </div>
          </div>

          <!-- 3. كبسولات الشروط الأساسية (مدة العقد + الراتب) -->
          <div class="t-terms-grid">
            <div class="t-term-item">
              <span class="t-term-lbl">📅 مدة العقد</span>
              <span class="t-term-val">${item.contract_length}</span>
            </div>
            <div class="t-term-item">
              <span class="t-term-lbl">💰 الراتب</span>
              <span class="t-term-val" style="color:var(--accent-green);">${item.salary}</span>
            </div>
          </div>

          <!-- 4. صندوق السبب أو الملخص المباشر -->
          <div class="t-reason-banner ${sMeta.reasonCls}">
            <strong>${notePrefix}</strong> ${item.status_reason}
          </div>

          <!-- 5. شريط البطولة والمصدر السفلي -->
          <div class="t-card-footer">
            <span class="t-league-chip">${item.league_tag || '🌍 ميركاتو عالمي'}</span>
            <span class="t-more-hint">التفاصيل والشروط ⬅️</span>
          </div>
        </div>
      `;
    } else {
      // ==================== تصميم بطاقة تجديد العقد الواضحة ====================
      const notePrefix = item.status === 'failed'
        ? '🚫 سبب تعثر التجديد:'
        : (item.status === 'done' ? '✍️ بنود التجديد:' : '⏳ موقف التجديد:');

      return `
        <div class="transfer-card ${sMeta.cls}" onclick="openMercatoDetailModal('contracts', '${item.id}')">
          <!-- 1. رأس البطاقة -->
          <div class="t-card-top">
            <div class="t-person-box">
              <div class="t-avatar-wrap">
                <img src="${item.avatar}" alt="${item.name}" onerror="this.src='https://ui-avatars.com/api/?name=P&background=1e293b&color=fff&rounded=true'">
              </div>
              <div style="min-width:0;">
                <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                  <span class="t-person-name">${item.name}</span>
                  ${roleBadge}
                </div>
                <div class="t-person-sub">${item.position} • ${item.age} سنة • ${item.nationality}</div>
              </div>
            </div>
            <span class="t-status-pill ${sMeta.pillCls}">${item.status_label}</span>
          </div>

          <!-- 2. بطاقة النادي ومسار تمديد العقد (واضحة ومميزة عن الانتقالات) -->
          <div class="renewal-showcase-box">
            <div class="renewal-club-side">
              <img src="${item.from_crest}" alt="${item.from_club}" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=1e293b&color=fff&rounded=true'">
              <div>
                <div style="font-size:0.7rem; color:var(--muted); font-weight:700;">النادي الحالي</div>
                <div style="font-size:0.92rem; font-weight:900; color:#fff;">${item.from_club}</div>
              </div>
            </div>

            <div class="renewal-timeline-side">
              <div class="renewal-dates-row">
                <span class="old-date-tag">${item.old_expiry}</span>
                <span style="color:var(--accent-cyan); font-weight:900;">⬅️</span>
                <span class="new-date-tag ${item.status === 'failed' ? 'date-failed' : ''}">${item.new_expiry}</span>
              </div>
              <div style="font-size:0.73rem; color:var(--accent-gold); font-weight:800; margin-top:4px;">
                ${item.contract_length}
              </div>
            </div>
          </div>

          <!-- 3. الشروط المالية للتجديد -->
          <div class="t-terms-grid">
            <div class="t-term-item">
              <span class="t-term-lbl">💵 الراتب</span>
              <span class="t-term-val" style="color:var(--accent-green);">${item.salary}</span>
            </div>
            <div class="t-term-item">
              <span class="t-term-lbl">🔒 الشرط الجزائي</span>
              <span class="t-term-val" style="color:var(--accent-gold);">${item.release_clause}</span>
            </div>
          </div>

          <!-- 4. ملخص المفاوضات أو سبب الرفض -->
          <div class="t-reason-banner ${sMeta.reasonCls}">
            <strong>${notePrefix}</strong> ${item.status_reason}
          </div>

          <!-- 5. شريط البطولة والتعديل المالي -->
          <div class="t-card-footer">
            <span class="t-league-chip">${item.league_tag || '🌍 عقود عالمية'}</span>
            <span style="font-size:0.74rem; font-weight:800; color:${(item.salary_change || '').includes('⬇️') ? 'var(--accent-red)' : 'var(--accent-green)'};">
              ${item.salary_change}
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

  const votes = window._mercatoState.votesMap[item.id] || { up: item.likes || 142, down: item.dislikes || 19 };
  const totalV = Math.max(1, votes.up + votes.down);
  const upPct = Math.round((votes.up / totalV) * 100);

  body.innerHTML = `
    <div style="display:flex; align-items:center; gap:14px; border-bottom:1px solid var(--card-border); padding-bottom:14px; margin-bottom:16px;">
      <img src="${item.avatar}" width="64" height="64" style="border-radius:50%; object-fit:cover; border:2px solid var(--accent-cyan); background:#080d1a;" onerror="this.src='https://ui-avatars.com/api/?name=P&background=1e293b&color=fff&rounded=true'">
      <div style="flex:1;">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">
          <h3 style="font-size:1.2rem; font-weight:900; color:#fff;">${item.name}</h3>
          <span class="hub-badge" style="color:var(--accent-gold); border-color:var(--accent-gold);">${item.status_label}</span>
        </div>
        <div style="font-size:0.82rem; color:var(--muted); margin-top:4px;">
          ${item.role === 'coach' ? '👔 مدير فني' : '⚽ لاعب'} • ${item.position} • ${item.age} سنة • ${item.nationality}
        </div>
      </div>
    </div>

    ${pageType === 'transfers' ? `
      <div class="transfer-bridge-box" style="margin-bottom:16px; padding:14px;">
        <div class="t-club-node">
          <div class="t-club-role-hint">من نادي</div>
          <img src="${item.from_crest}" width="44" height="44">
          <div class="t-club-name" style="font-size:0.9rem;">${item.from_club}</div>
        </div>
        <div class="t-arrow-tunnel">
          <span class="t-deal-type-lbl" style="font-size:0.78rem;">${item.deal_type}</span>
          <div style="font-size:1.3rem; margin:4px 0;">⬅️</div>
          <span class="t-fee-lbl" style="font-size:0.82rem; color:var(--accent-gold);">${item.fee}</span>
        </div>
        <div class="t-club-node">
          <div class="t-club-role-hint" style="color:var(--accent-cyan);">إلى نادي</div>
          <img src="${item.to_crest}" width="44" height="44">
          <div class="t-club-name" style="font-size:0.9rem; color:#fff;">${item.to_club}</div>
        </div>
      </div>
    ` : `
      <div class="renewal-showcase-box" style="margin-bottom:16px; padding:14px;">
        <div class="renewal-club-side">
          <img src="${item.from_crest}" width="42" height="42">
          <div>
            <div style="font-size:0.75rem; color:var(--muted);">نادي التجديد</div>
            <div style="font-size:1rem; font-weight:900; color:#fff;">${item.from_club}</div>
          </div>
        </div>
        <div class="renewal-timeline-side">
          <div class="renewal-dates-row">
            <span class="old-date-tag">${item.old_expiry}</span>
            <span>⬅️</span>
            <span class="new-date-tag">${item.new_expiry}</span>
          </div>
          <div style="font-size:0.78rem; color:var(--accent-gold); font-weight:800; margin-top:4px;">${item.contract_length}</div>
        </div>
      </div>
    `}

    <div style="background:#080d1a; border:1px solid var(--card-border); border-radius:14px; padding:14px; margin-bottom:14px;">
      <div style="font-weight:900; color:var(--accent-cyan); margin-bottom:10px; font-size:0.9rem;">📋 البنود المالية والتعاقدية الكاملة:</div>
      <div class="t-terms-grid" style="margin-bottom:10px;">
        <div class="t-term-item">
          <span class="t-term-lbl">${pageType === 'transfers' ? '💵 قيمة الصفقة' : '📈 تعديل الراتب'}</span>
          <span class="t-term-val" style="color:var(--accent-green);">${pageType === 'transfers' ? item.fee : item.salary_change}</span>
        </div>
        <div class="t-term-item">
          <span class="t-term-lbl">💰 الراتب السنوي</span>
          <span class="t-term-val">${item.salary}</span>
        </div>
        <div class="t-term-item">
          <span class="t-term-lbl">📅 مدة العقد</span>
          <span class="t-term-val">${item.contract_length}</span>
        </div>
        <div class="t-term-item">
          <span class="t-term-lbl">🔒 الشرط الجزائي</span>
          <span class="t-term-val" style="color:var(--accent-gold);">${item.release_clause || 'غير معلن'}</span>
        </div>
      </div>
      <div style="background:#060a14; border:1px solid #18253f; border-radius:10px; padding:10px; font-size:0.82rem; color:#cbd5e1; line-height:1.6;">
        <strong style="color:#fff;">📌 الشروط والامتيازات:</strong> ${item.conditions}
      </div>
    </div>

    <div style="background:#090e1a; border-right:4px solid ${item.status === 'failed' ? 'var(--accent-red)' : 'var(--accent-gold)'}; padding:12px 14px; border-radius:10px; margin-bottom:16px; font-size:0.85rem; line-height:1.65; color:#e2e8f0;">
      <div style="font-weight:900; color:${item.status === 'failed' ? 'var(--accent-red)' : 'var(--accent-gold)'}; margin-bottom:4px;">
        ${item.status === 'failed' ? '🚫 سبب فشل وتعثر المفاوضات:' : '🕵️‍♂️ كواليس الصفقة والتفاصيل:'}
      </div>
      <div>${item.status_reason}</div>
      <div style="font-size:0.74rem; color:var(--muted); margin-top:6px;">📡 المصدر: <strong style="color:#fff;">${item.source}</strong> (موثوقية ${item.reliability}%)</div>
    </div>

    <div style="background:#070b15; border:1px solid #162238; border-radius:14px; padding:12px 14px;">
      <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:800; margin-bottom:8px;">
        <span>📊 تصويت زوار المنصة على الصفقة:</span>
        <span id="mercato-vote-pct" style="color:var(--accent-green);">${upPct}% يؤيدون الخطوة</span>
      </div>
      <div class="vote-btn-group">
        <button class="mercato-vote-btn" onclick="voteMercatoItem('${item.id}', 'up', '${pageType}')">🔥 صفقة رابحة (${votes.up})</button>
        <button class="mercato-vote-btn" onclick="voteMercatoItem('${item.id}', 'down', '${pageType}')">👎 غير موفقة (${votes.down})</button>
      </div>
    </div>
  `;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function voteMercatoItem(itemId, dir, pageType) {
  const list = pageType === 'transfers' ? window._mercatoState.transfersList : window._mercatoState.contractsList;
  const item = list.find(x => String(x.id) === String(itemId));
  if (!item) return;

  if (!window._mercatoState.votesMap[itemId]) {
    window._mercatoState.votesMap[itemId] = { up: item.likes || 142, down: item.dislikes || 19 };
  }
  if (dir === 'up') window._mercatoState.votesMap[itemId].up += 1;
  else window._mercatoState.votesMap[itemId].down += 1;

  openMercatoDetailModal(pageType, itemId);
}

// =========================================================
// 12. استوديو المسابقات الكروي المتكامل (DeepPitch Quiz Arena v6.0 - Instant Answer + Compact Horizontal Scroll)
// =========================================================
window._quizState = {
  phase: 'lobby',          // 'lobby' | 'playing' | 'summary'
  pool: [],
  totalPoolCount: 3800,
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
  timerSec: 20,
  timerMax: 20,
  questionStartTs: 0,
  timerInterval: null,
  blitzFound: [],
  profile: JSON.parse(localStorage.getItem('deeppitch_quiz_profile') || '{"highScore":0,"totalPoints":0,"correctCount":0,"answeredCount":0}')
};

const QUIZ_CATEGORIES_META = {
  'ALL':              { icon: '🌟', name: 'شامل (الـ 12 فئة)', sub: 'توليفة عالمية متنوعة' },
  'club_career':      { icon: '✈️', name: 'مسيرة لاعب بالشعارات', sub: 'شعارات الأندية بالترتيب' },
  'nations_cups':     { icon: '🌍', name: 'كأس العالم والمنتخبات', sub: 'المونديال والبطولات القارية' },
  'awards_scorers':   { icon: '🌕', name: 'البالون دور والهدافون', sub: 'الجوائز والأهداف الحاسمة' },
  'jersey_numbers':   { icon: '👕', name: 'أرقام القمصان', sub: 'أرقام نجوم الأندية الحية' },
  'derbies_stadiums': { icon: '🔥', name: 'قمم وديربيات العالم', sub: 'المواجهات الكبرى والملاعب' },
  'coaches_tactics':  { icon: '👔', name: 'عباقرة الدكة والمدربون', sub: 'مسيرة المدربين بالشعارات' },
  'finals_remontada': { icon: '⚡', name: 'النهائيات والريمونتادا', sub: 'نتائج النهائيات الدقيقة' },
  'visual':           { icon: '🔍', name: 'الشعار المغبش', sub: 'شعارات الأندية الرسمية' },
  'stats':            { icon: '📊', name: 'مقارنات الأرقام', sub: 'أعلى أم أقل داخل البطولة' },
  'who_am_i':         { icon: '🕵️‍♂️', name: 'من أنا؟ (3 أدلة)', sub: 'اكتشف الهوية بأقل تلميحات' },
  'tactics':          { icon: '📋', name: 'الترتيب التكتيكي', sub: 'رتب الأندية المتقاربة تنازلياً' },
  'blitz':            { icon: '⏱️', name: 'تحدي الـ 30 ثانية', sub: 'اكتب أكبر عدد من الأندية' }
};

// حقن تنسيقات السكرول العرضي وتلوين الإجابات مباشرة لضمان عملها على الموبايل والكمبيوتر دون تأثر بكاش المتصفح
function injectQuizHorizontalScrollStyles() {
  if (document.getElementById('deeppitch-quiz-v6-css')) return;
  const stEl = document.createElement('style');
  stEl.id = 'deeppitch-quiz-v6-css';
  stEl.innerHTML = `
    .quiz-h-strip {
      display: flex !important;
      flex-direction: row !important;
      flex-wrap: nowrap !important;
      align-items: center !important;
      gap: 8px !important;
      width: 100% !important;
      overflow-x: auto !important;
      overflow-y: hidden !important;
      padding: 4px 2px 8px 2px !important;
      margin-bottom: 8px !important;
      -webkit-overflow-scrolling: touch !important;
      scroll-snap-type: x mandatory !important;
      scrollbar-width: thin !important;
      scrollbar-color: rgba(0, 230, 118, 0.4) transparent !important;
    }
    .quiz-h-strip::-webkit-scrollbar { height: 4px !important; }
    .quiz-h-strip::-webkit-scrollbar-thumb { background: rgba(0, 230, 118, 0.45) !important; border-radius: 10px !important; }

    .q-chip-item {
      flex: 0 0 auto !important;
      scroll-snap-align: start !important;
      background: #080e1c !important;
      border: 1.5px solid #1d2d4d !important;
      color: #cbd5e1 !important;
      padding: 7px 14px !important;
      border-radius: 99px !important;
      font-size: 0.78rem !important;
      font-weight: 800 !important;
      cursor: pointer !important;
      white-space: nowrap !important;
      display: inline-flex !important;
      align-items: center !important;
      gap: 6px !important;
      transition: all 0.2s ease !important;
    }
    .q-chip-item.active {
      background: rgba(0, 230, 118, 0.16) !important;
      border-color: #00e676 !important;
      color: #00e676 !important;
      box-shadow: 0 0 12px rgba(0, 230, 118, 0.2) !important;
    }
    .q-chip-item.active-cyan {
      background: rgba(0, 210, 255, 0.16) !important;
      border-color: #00d2ff !important;
      color: #00d2ff !important;
      box-shadow: 0 0 12px rgba(0, 210, 255, 0.2) !important;
    }
    .q-chip-item.active-gold {
      background: rgba(255, 214, 0, 0.16) !important;
      border-color: #ffd600 !important;
      color: #ffd600 !important;
      box-shadow: 0 0 12px rgba(255, 214, 0, 0.2) !important;
    }

    .q-cat-card-compact {
      flex: 0 0 165px !important;
      scroll-snap-align: start !important;
      background: #080e1c !important;
      border: 1.5px solid #1d2d4d !important;
      border-radius: 14px !important;
      padding: 9px 11px !important;
      cursor: pointer !important;
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
      transition: all 0.2s ease !important;
    }
    .q-cat-card-compact.active {
      background: linear-gradient(145deg, rgba(0, 210, 255, 0.18), #0b162c) !important;
      border-color: #00d2ff !important;
      box-shadow: 0 4px 14px rgba(0, 210, 255, 0.2) !important;
    }

    .quiz-options-grid {
      display: grid !important;
      grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
      gap: 10px !important;
      margin-bottom: 12px !important;
    }
    .quiz-option-btn {
      background: linear-gradient(145deg, #0d172b, #080e1c) !important;
      border: 1.5px solid #223558 !important;
      color: #fff !important;
      padding: 12px 10px !important;
      border-radius: 14px !important;
      font-size: 0.85rem !important;
      font-weight: 800 !important;
      cursor: pointer !important;
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
      text-align: right !important;
      min-height: 50px !important;
      width: 100% !important;
      transition: all 0.18s ease !important;
    }
    .quiz-option-btn.opt-correct {
      background: rgba(0, 230, 118, 0.25) !important;
      border-color: #00e676 !important;
      color: #00e676 !important;
      box-shadow: 0 0 16px rgba(0, 230, 118, 0.35) !important;
    }
    .quiz-option-btn.opt-wrong {
      background: rgba(255, 82, 82, 0.25) !important;
      border-color: #ff5252 !important;
      color: #ff5252 !important;
      box-shadow: 0 0 16px rgba(255, 82, 82, 0.35) !important;
    }
  `;
  document.head.appendChild(stEl);
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
  const url = `/api/quiz_bank?league=${encodeURIComponent(st.filterLeague)}&difficulty=${encodeURIComponent(st.filterDiff)}&region=${encodeURIComponent(st.filterRegion)}&category=${encodeURIComponent(st.filterCategory)}&qtype=${encodeURIComponent(st.filterCategory)}&seed=${encodeURIComponent(seedParam)}&use_ai=${st.useAiGenerator}&count=200&_t=${Date.now()}`;
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

  if (!forceReload && Array.isArray(st.pool) && st.pool.length > 20) {
    renderQuizArenaWorkspace();
    return;
  }

  container.innerHTML = '<div class="loading-state">🌐 جاري سحب وبناء الأسئلة الحية من الـ APIs الخارجية...</div>';

  try {
    const data = await fetchQuizBankFromBackend();
    if (data && data.status === 'success' && Array.isArray(data.questions)) {
      st.pool = data.questions;
      st.totalPoolCount = data.total_pool_size || data.questions.length;
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
  window._quizState[key] = val;
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

function renderCleanQuizLobby(container) {
  const st = window._quizState;

  const modes = [
    { key: 'solo', icon: '🎯', title: 'طور فردي قياسي' },
    { key: 'ai_bot', icon: '🤖', title: 'تحدي البوت (vs AI)' },
    { key: 'survival', icon: '❤️', title: 'طور النجاة (3 قلوب)' },
    { key: 'friend_code', icon: '🔗', title: 'تحدي صديق بكود' }
  ];

  const regions = [
    { key: 'ALL', label: '🌍 كل القارات' },
    { key: 'europe', label: '🇪🇺 أوروبا' },
    { key: 'americas', label: '🌎 الأمريكيتين' },
    { key: 'africa', label: '🌍 أفريقيا' },
    { key: 'asia', label: '🌏 آسيا' }
  ];

  const leagues = [
    { key: 'ALL', label: '🏆 كل البطولات' },
    { key: 'UCL', label: '🏆 أبطال أوروبا' },
    { key: 'PL', label: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 البريميرليغ' },
    { key: 'PD', label: '🇪🇸 الليغا' },
    { key: 'SA', label: '🇮🇹 الكالتشيو' },
    { key: 'BL1', label: '🇩🇪 البوندسليغا' },
    { key: 'FL1', label: '🇫🇷 الدوري الفرنسي' },
    { key: 'ACL', label: '🌏 نخبة آسيا' },
    { key: 'CAF', label: '🌍 أبطال أفريقيا' },
    { key: 'UNL', label: '🏳️ المنتخبات' }
  ];

  container.innerHTML = `
    <div id="quiz-license-banner-wrap">${renderLicenseBannerHtml()}</div>

    <div class="quiz-lobby-card" style="padding:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid var(--card-border);">
        <div>
          <h3 style="font-size:1rem; font-weight:900; color:#fff; margin:0;">🏟️ إعدادات المسابقة الكروية</h3>
          <div style="font-size:0.7rem; color:var(--muted);">اسحب الأشرطة أفقياً للتخصيص (${st.totalPoolCount}+ سؤال متجدد)</div>
        </div>
        <label style="display:inline-flex; align-items:center; gap:5px; background:#070c18; border:1px solid var(--accent-cyan); padding:4px 10px; border-radius:99px; cursor:pointer; font-size:0.72rem; font-weight:800; color:var(--accent-cyan);">
          <input type="checkbox" ${st.useAiGenerator ? 'checked' : ''} onchange="window.setQuizLobbyParam('useAiGenerator', this.checked)" style="accent-color:var(--accent-green);">
          <span>🤖 أسئلة Gemini AI</span>
        </label>
      </div>

      <!-- 1. شريط أفقي مدمج لأطوار اللعب -->
      <div style="font-size:0.76rem; font-weight:900; color:var(--accent-cyan); margin-bottom:4px;">1️⃣ طور المنافسة (اسحب أفقياً ⬅️):</div>
      <div class="quiz-h-strip">
        ${modes.map(m => `
          <button type="button" class="q-chip-item ${st.gameMode === m.key ? 'active' : ''}" onclick="window.setQuizLobbyParam('gameMode', '${m.key}')">
            <span>${m.icon}</span>
            <span>${m.title}</span>
          </button>
        `).join('')}
      </div>

      ${st.gameMode === 'ai_bot' ? `
        <div class="quiz-h-strip">
          ${[
            { k: 'rookie', l: '🟢 بوت مبتدئ (60%)' },
            { k: 'tactician', l: '🟡 محلل تكتيكي (78%)' },
            { k: 'legend', l: '🔴 بوت أسطوري (92%)' }
          ].map(b => `
            <button type="button" class="q-chip-item ${st.botDifficulty === b.k ? 'active-cyan' : ''}" onclick="window.setQuizLobbyParam('botDifficulty', '${b.k}')">${b.l}</button>
          `).join('')}
        </div>
      ` : ''}

      ${st.gameMode === 'friend_code' ? `
        <div style="display:flex; gap:8px; align-items:center; background:#070c18; border:1px solid var(--accent-gold); padding:6px 12px; border-radius:12px; margin-bottom:8px;">
          <span style="font-size:0.74rem; font-weight:800; color:var(--accent-gold);">🔗 كود التحدي:</span>
          <input type="text" value="${st.challengeSeed}" oninput="window._quizState.challengeSeed = this.value.trim().toUpperCase()" placeholder="DP-4821" class="lobby-select-input" style="padding:4px 8px; font-size:0.78rem; max-width:130px; text-align:center;">
        </div>
      ` : ''}

      <!-- 2. شريط أفقي للفئات الـ 12 -->
      <div style="font-size:0.76rem; font-weight:900; color:var(--accent-cyan); margin-bottom:4px;">2️⃣ فئة الأسئلة (12 فئة — اسحب أفقياً ⬅️):</div>
      <div class="quiz-h-strip">
        ${Object.entries(QUIZ_CATEGORIES_META).map(([k, v]) => `
          <div class="q-cat-card-compact ${st.filterCategory === k ? 'active' : ''}" onclick="window.setQuizLobbyParam('filterCategory', '${k}')">
            <span style="font-size:1.2rem;">${v.icon}</span>
            <div style="min-width:0;">
              <div style="font-weight:900; font-size:0.76rem; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${v.name}</div>
              <div style="font-size:0.63rem; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${v.sub}</div>
            </div>
          </div>
        `).join('')}
      </div>

      <!-- 3. شريط أفقي مدمج للنطاق القاري والبطولة (سطر أفقي رفيع قابل للسحب) -->
      <div style="font-size:0.76rem; font-weight:900; color:var(--accent-cyan); margin-bottom:4px;">3️⃣ النطاق القاري والبطولة (اسحب أفقياً ⬅️):</div>
      <div class="quiz-h-strip">
        ${regions.map(r => `
          <button type="button" class="q-chip-item ${st.filterRegion === r.key ? 'active-gold' : ''}" onclick="window.setQuizLobbyParam('filterRegion', '${r.key}')">${r.label}</button>
        `).join('')}
        <span style="color:#334155; font-weight:900; padding:0 2px;">|</span>
        ${leagues.map(lg => `
          <button type="button" class="q-chip-item ${st.filterLeague === lg.key ? 'active-cyan' : ''}" onclick="window.setQuizLobbyParam('filterLeague', '${lg.key}')">${lg.label}</button>
        `).join('')}
      </div>

      <!-- 4. شريط أفقي للصعوبة وعدد الأسئلة -->
      <div class="quiz-h-strip" style="margin-bottom:10px;">
        ${[
          { k: 'ALL', l: '🎚️ كل المستويات' },
          { k: 'easy', l: '🟢 سهل' },
          { k: 'medium', l: '🟡 متوسط' },
          { k: 'hard', l: '🔴 صعب' }
        ].map(d => `
          <button type="button" class="q-chip-item ${st.filterDiff === d.k ? 'active' : ''}" onclick="window.setQuizLobbyParam('filterDiff', '${d.k}')">${d.l}</button>
        `).join('')}
        <span style="color:#334155; font-weight:900; padding:0 2px;">|</span>
        ${[10, 20, 35].map(n => `
          <button type="button" class="q-chip-item ${st.sessionLength === n ? 'active-gold' : ''}" onclick="window.setQuizLobbyParam('sessionLength', ${n})">🔢 ${n} سؤال</button>
        `).join('')}
      </div>

      <div style="text-align:center; padding-top:4px;">
        <button type="button" class="quiz-start-hero-btn" onclick="window.startQuizChallengeNow()">
          <span>🚀 ابدأ التحدي الآن (${(QUIZ_CATEGORIES_META[st.filterCategory] || QUIZ_CATEGORIES_META['ALL']).name})</span>
        </button>
      </div>
    </div>
  `;
}

window.startQuizChallengeNow = async function() {
  const st = window._quizState;
  const startBtn = document.querySelector('.quiz-start-hero-btn');
  if (startBtn) {
    startBtn.disabled = true;
    startBtn.innerHTML = '<span>⏳ جاري سحب دفعة أسئلة حية من السيرفر...</span>';
  }

  try {
    const data = await fetchQuizBankFromBackend();
    if (data && data.status === 'success' && Array.isArray(data.questions) && data.questions.length > 0) {
      st.pool = data.questions;
      st.totalPoolCount = data.total_pool_size || data.questions.length;
      if (data.seed_code) st.challengeSeed = data.seed_code;
    }
  } catch (e) {
    console.error('Failed to fetch from /api/quiz_bank:', e);
  }

  const seenIds = getSeenQuizIds();
  let unseenPool = (st.pool || []).filter(q => !seenIds.includes(q.id));

  if (unseenPool.length < (st.sessionLength || 10)) {
    const currentPoolIds = new Set((st.pool || []).map(q => q.id));
    const remainingSeen = seenIds.filter(id => !currentPoolIds.has(id));
    localStorage.setItem('deeppitch_seen_qids', JSON.stringify(remainingSeen));
    unseenPool = [...(st.pool || [])];
  }

  const seedToUse = st.gameMode === 'friend_code' ? st.challengeSeed : '';
  const ordered = shuffleQuizArray(unseenPool, seedToUse).map(q => {
    const copy = { ...q };
    if (Array.isArray(copy.options) && copy.options.length > 2) {
      copy.options = shuffleQuizArray(copy.options, seedToUse ? `${seedToUse}_${copy.id}` : '');
    }
    return copy;
  });

  const maxLen = st.gameMode === 'survival' ? Math.min(40, ordered.length) : Math.min(st.sessionLength || 10, ordered.length);
  st.activeQueue = ordered.slice(0, Math.max(1, maxLen));

  if (st.activeQueue.length === 0) {
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

function simulateBotTurnForQuestion(q, basePts) {
  const st = window._quizState;
  if (st.gameMode !== 'ai_bot') return;
  const accMap = { 'rookie': 0.60, 'tactician': 0.78, 'legend': 0.92 };
  const hit = Math.random() <= (accMap[st.botDifficulty] || 0.78);
  if (hit) {
    st.botScore += basePts;
    st.botCorrect += 1;
    st.botLastAction = `✅ البوت أصاب (+${basePts})`;
  } else {
    st.botLastAction = `❌ البوت أخطأ`;
  }
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
  markQuizQuestionSeen(q.id);

  st.answeredCurrent = false;
  st.blurLevel = 14;
  st.clueStage = 1;
  st.rankSelection = [];
  st.blitzFound = [];
  st.questionStartTs = Date.now();

  const catInfo = QUIZ_CATEGORIES_META[q.category] || QUIZ_CATEGORIES_META['ALL'];
  const totalSec = q.type === 'blitz_30s' ? 30 : 20;

  let visualStageHtml = '';
  let customOptionsHtml = '';

  if (q.type === 'career_path' && Array.isArray(q.career_stops)) {
    visualStageHtml = `
      <div class="quiz-career-scroll">
        ${q.career_stops.map((stItem, i) => `
          <div class="career-club-card">
            <span class="career-step-badge">محطة #${i + 1}</span>
            <img src="${stItem.crest}" alt="${stItem.club}" onerror="this.src='https://ui-avatars.com/api/?name=FC&background=1e293b&color=00e676&bold=true&rounded=true'">
            <div class="career-club-title">${stItem.club}</div>
          </div>
          ${i < q.career_stops.length - 1 ? `<span class="career-step-arrow">⬅️</span>` : ''}
        `).join('')}
      </div>
    `;
  } else if (q.type === 'logo_blur') {
    visualStageHtml = `
      <div class="quiz-visual-center">
        <img id="quiz-mystery-crest" src="${q.image_url}" style="filter: blur(${st.blurLevel}px); transition: filter 0.35s ease; width:88px; height:88px; object-fit:contain;">
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
          <div style="font-size:0.75rem; color:var(--muted);">النادي / المنتخب:</div>
          <div style="font-size:0.95rem; font-weight:900; color:#fff;">${q.jersey_club}</div>
        </div>
      </div>
    `;
  } else if (q.type === 'higher_lower') {
    visualStageHtml = `
      <div class="quiz-visual-center" style="justify-content:space-around;">
        <div style="text-align:center;">
          ${q.item_a.crest ? `<img src="${q.item_a.crest}" width="42" height="42" style="object-fit:contain;">` : ''}
          <div style="font-weight:900; font-size:0.86rem; color:#fff;">${q.item_a.name}</div>
          <div style="font-size:1.3rem; font-weight:900; color:var(--accent-green);">${q.item_a.stat_val}</div>
        </div>
        <div class="vs-circle-badge" style="width:36px; height:36px; font-size:0.8rem;">VS</div>
        <div style="text-align:center;">
          ${q.item_b.crest ? `<img src="${q.item_b.crest}" width="42" height="42" style="object-fit:contain;">` : ''}
          <div style="font-weight:900; font-size:0.86rem; color:#fff;">${q.item_b.name}</div>
          <div id="hl-mystery-val" style="font-size:1.3rem; font-weight:900; color:var(--accent-gold);">❓</div>
        </div>
      </div>
    `;
  } else if (q.type === 'three_clues') {
    const clues = q.clues || [];
    visualStageHtml = `
      <div style="margin-bottom:10px;">
        <div id="clues-stack-list" style="display:flex; flex-direction:column; gap:6px; margin-bottom:8px;">
          <div class="clue-item-card">🔎 ${clues[0] || ''}</div>
        </div>
        ${clues.length > 1 ? `
          <div style="text-align:center;">
            <button type="button" id="reveal-next-clue-btn" class="dock-lifeline-btn" onclick="window.revealNextProgressiveClue()" style="border-color:var(--accent-gold); color:var(--accent-gold);">
              🔓 كشف الدليل التالي
            </button>
          </div>
        ` : ''}
      </div>
    `;
  } else if (q.type === 'rank_order') {
    customOptionsHtml = `
      <div style="text-align:center; margin-bottom:8px;">
        <button type="button" class="dock-lifeline-btn" onclick="window.resetRankOrderSelection()">🔄 إعادة ترتيب</button>
      </div>
      <div class="quiz-options-grid" id="rank-order-grid">
        ${(q.rank_items || []).map((item, idx) => `
          <button type="button" class="quiz-option-btn rank-item-btn" id="rank-btn-${idx}" onclick="window.onRankItemClick(${idx})">
            <span class="opt-letter" id="rank-badge-${idx}">?</span>
            <div class="opt-text" style="display:flex; justify-content:space-between; align-items:center;">
              <span>${item.label}</span>
              <span class="rank-secret-val" style="display:none; color:var(--accent-gold); font-size:0.75rem;">${item.val}</span>
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
        <input type="text" id="blitz-live-input" class="quiz-blitz-input" style="padding:9px 12px; font-size:0.86rem; margin-bottom:8px;" placeholder="✍️ اكتب اسم النادي هنا..." oninput="window.onBlitzInputType(this.value)" autocomplete="off">
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
            <span class="opt-text">${String(opt)}</span>
          </button>
        `).join('')}
      </div>
    `);

  stage.innerHTML = `
    <div class="quiz-stage-card quiz-slide-anim">
      <div class="quiz-neon-timer-track">
        <div id="quiz-neon-timer-bar" class="quiz-neon-timer-fill" style="width:100%;"></div>
      </div>

      <!-- الشريط العلوي المدمج (HUD) -->
      <div class="quiz-hud-bar">
        <div style="display:flex; align-items:center; gap:6px;">
          <button type="button" class="hud-chip" onclick="window.returnToQuizLobby()" style="cursor:pointer;">⚙️ القائمة</button>
          <span class="hud-chip">${st.currentIndex + 1} / ${st.activeQueue.length}</span>
          ${st.gameMode === 'survival' ? `<span class="hud-chip">${'❤️'.repeat(st.lives)}</span>` : ''}
          ${st.gameMode === 'ai_bot' ? `<span class="hud-chip" style="border-color:var(--accent-cyan); color:var(--accent-cyan);">🤖 البوت: ${st.botScore}</span>` : ''}
        </div>

        <div style="display:flex; align-items:center; gap:6px;">
          <span class="hud-chip" style="border-color:var(--accent-gold); color:var(--accent-gold);">⭐ <strong id="quiz-live-score">${st.score}</strong></span>
          <span class="hud-chip" id="quiz-timer-badge" style="border-color:var(--accent-cyan); color:var(--accent-cyan);">⏱️ <strong id="quiz-timer-sec">${totalSec}</strong>ث</span>
        </div>
      </div>

      <!-- صندوق نص السؤال -->
      <div class="quiz-question-box">
        <span class="quiz-cat-tag">${catInfo.icon} ${catInfo.name}</span>
        <h3 class="quiz-question-title">${q.question}</h3>
      </div>

      <!-- المسرح البصري -->
      ${visualStageHtml}

      <!-- شبكة الخيارات 2×2 -->
      ${optionsGridHtml}

      <!-- شريط المساعدات السفلي المدمج -->
      ${!['blitz_30s', 'rank_order'].includes(q.type) ? `
        <div class="quiz-lifelines-dock">
          ${q.options && q.options.length > 2 ? `
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

// دالة التحقق الفوري من الإجابة عند النقر على أي خيار
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

  const basePts = q.type === 'three_clues'
    ? Math.max(1, 4 - (st.clueStage || 1))
    : (q.difficulty === 'hard' ? 3 : (q.difficulty === 'medium' ? 2 : 1));

  finalizeQuestionScoreAndFeedback(isCorrect, q, basePts, chosen);
};

window.revealNextProgressiveClue = function() {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q || !q.clues) return;
  if (st.clueStage < q.clues.length) {
    st.clueStage += 1;
    const listEl = document.getElementById('clues-stack-list');
    if (listEl) {
      const div = document.createElement('div');
      div.className = 'clue-item-card';
      div.innerText = `🔎 ${q.clues[st.clueStage - 1]}`;
      listEl.appendChild(div);
    }
    if (st.clueStage >= q.clues.length) {
      const btn = document.getElementById('reveal-next-clue-btn');
      if (btn) btn.style.display = 'none';
    }
  }
};

window.onRankItemClick = function(idx) {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q || q.type !== 'rank_order' || !Array.isArray(q.rank_items)) return;
  if (st.rankSelection.some(x => x.idx === idx)) return;

  const label = q.rank_items[idx] ? q.rank_items[idx].label : '';
  st.rankSelection.push({ idx, label });
  const btn = document.getElementById(`rank-btn-${idx}`);
  const badge = document.getElementById(`rank-badge-${idx}`);
  if (btn) btn.classList.add('rank-selected-btn');
  if (badge) {
    badge.innerText = `#${st.rankSelection.length}`;
    badge.style.background = 'var(--accent-gold)';
    badge.style.color = '#000';
  }

  if (st.rankSelection.length === q.rank_items.length) {
    st.answeredCurrent = true;
    stopQuizTimer();
    const userOrder = st.rankSelection.map(x => x.label);
    const isCorrect = JSON.stringify(userOrder) === JSON.stringify(q.correct_order);
    document.querySelectorAll('.rank-item-btn').forEach(b => {
      b.disabled = true;
      b.classList.add(isCorrect ? 'opt-correct' : 'opt-wrong');
    });
    document.querySelectorAll('.rank-secret-val').forEach(el => { el.style.display = 'inline-block'; });
    finalizeQuestionScoreAndFeedback(isCorrect, q, 2, userOrder.join(' ⬅️ '));
  }
};

window.resetRankOrderSelection = function() {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  st.rankSelection = [];
  document.querySelectorAll('.rank-item-btn').forEach((btn, i) => {
    btn.classList.remove('rank-selected-btn');
    const bdg = document.getElementById(`rank-badge-${i}`);
    if (bdg) {
      bdg.innerText = '?';
      bdg.style.background = '#050811';
      bdg.style.color = 'var(--accent-cyan)';
    }
  });
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

window.onBlitzInputType = function(rawVal) {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q || q.type !== 'blitz_30s') return;

  const clean = (rawVal || '').trim().toLowerCase();
  if (clean.length < 3) return;

  const matched = (q.accepted_answers || []).find(item => item.toLowerCase() === clean);
  if (matched && !st.blitzFound.includes(matched.toLowerCase())) {
    const oldLvl = computePlayerLevel500(st.profile.totalPoints).level;
    st.blitzFound.push(matched.toLowerCase());
    st.score += 1;
    st.roundCorrect += 1;
    st.roundAnswered += 1;
    st.profile.totalPoints += 1;
    st.profile.correctCount += 1;
    st.profile.answeredCount += 1;
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
  const fb = document.getElementById('quiz-feedback-banner');
  if (fb) {
    fb.style.display = 'block';
    fb.className = 'quiz-feedback-box fb-correct';
    fb.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:0.84rem;">✅ اكتشفت <strong>${st.blitzFound.length}</strong> أندية صحيحة!</span>
        <button type="button" class="ai-btn" onclick="window.nextQuizQuestion()">التالي ⬅️</button>
      </div>
    `;
  }
};

window.useQuizLifeline = function(type) {
  const st = window._quizState;
  if (st.answeredCurrent || st.lifelines[type] <= 0) return;
  const q = st.activeQueue[st.currentIndex];
  if (!q) return;

  st.lifelines[type] -= 1;

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
    if (btn) btn.innerText = `✂️ 50:50 (${st.lifelines.fifty})`;
  } else if (type === 'hint') {
    if (q.type === 'three_clues') window.revealNextProgressiveClue();
    else if (q.type === 'logo_blur') {
      st.blurLevel = Math.max(3, st.blurLevel - 7);
      const img = document.getElementById('quiz-mystery-crest');
      if (img) img.style.filter = `blur(${st.blurLevel}px)`;
    }
    const fb = document.getElementById('quiz-feedback-banner');
    if (fb && q.type !== 'three_clues') {
      fb.style.display = 'block';
      fb.className = 'quiz-feedback-box';
      fb.innerHTML = `<div style="color:var(--accent-gold); font-weight:800; font-size:0.8rem;">💡 تلميح: ${q.hint || ''}</div>`;
    }
    const btn = document.getElementById('lf-btn-hint');
    if (btn) btn.innerText = `💡 تلميح (${st.lifelines.hint})`;
  } else if (type === 'freeze') {
    st.timerSec += 10;
    st.timerMax = Math.max(st.timerMax, st.timerSec);
    const el = document.getElementById('quiz-timer-sec');
    if (el) el.innerText = st.timerSec;
    const btn = document.getElementById('lf-btn-freeze');
    if (btn) btn.innerText = `❄️ +10ث (${st.lifelines.freeze})`;
  }
};

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
  const fb = document.getElementById('quiz-feedback-banner');
  if (fb) {
    fb.style.display = 'block';
    fb.className = `quiz-feedback-box ${isCorrect ? 'fb-correct' : 'fb-wrong'}`;
    fb.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <div style="min-width:0;">
          <div style="font-weight:900; font-size:0.86rem; color:${isCorrect ? 'var(--accent-green)' : 'var(--accent-red)'};">
            ${isCorrect ? `✅ إجابة صحيحة! (+${deltaPts} نقطة)` : `❌ إجابة خاطئة! الصحيح: ${q.answer}`}
          </div>
          <div style="font-size:0.76rem; color:#cbd5e1; margin-top:2px;">${q.explanation || ''}</div>
        </div>
        <button type="button" class="ai-btn" onclick="window.nextQuizQuestion()" style="white-space:nowrap; padding:7px 14px;">
          ${isLastQ ? '🏁 النتيجة' : 'التالي ⬅️'}
        </button>
      </div>
    `;
  }
}

function handleQuizTimeout() {
  const st = window._quizState;
  if (st.answeredCurrent) return;
  st.answeredCurrent = true;
  st.streak = 0;
  st.roundAnswered += 1;
  if (st.gameMode === 'survival') st.lives -= 1;

  const q = st.activeQueue[st.currentIndex];
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

  simulateBotTurnForQuestion(q, 2);
  playQuizSound('wrong');

  const fb = document.getElementById('quiz-feedback-banner');
  if (fb) {
    fb.style.display = 'block';
    fb.className = 'quiz-feedback-box fb-wrong';
    fb.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="color:var(--accent-red); font-weight:900; font-size:0.84rem;">⌛ انتهى الوقت! الصحيح: ${q ? q.answer : ''}</span>
        <button type="button" class="ai-btn" onclick="window.nextQuizQuestion()" style="padding:7px 14px;">التالي ⬅️</button>
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
    alert(`تم نسخ كود التحدي (${codeStr})!`);
  } catch (e) {}
};

function renderQuizPostMatchSummary() {
  const stage = document.getElementById('quiz-stage-box');
  if (!stage) return;

  const st = window._quizState;
  const totalAns = Math.max(1, st.roundAnswered);
  const accPct = Math.round((st.roundCorrect / totalAns) * 100);
  const lvlObj = computePlayerLevel500(st.profile.totalPoints);

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

  stage.innerHTML = `
    <div class="quiz-stage-card quiz-slide-anim" style="text-align:center;">
      <span class="quiz-cat-tag">🏁 نهاية الجولة — المستوى ${lvlObj.level} / 500</span>

      ${botBannerHtml}

      <div class="post-match-kpis-grid">
        <div class="pm-kpi-card">
          <div class="pm-kpi-val" style="color:var(--accent-green);">+${st.score}</div>
          <div class="pm-kpi-lbl">النقاط ⭐</div>
        </div>
        <div class="pm-kpi-card" style="border-top-color:var(--accent-cyan);">
          <div class="pm-kpi-val" style="color:var(--accent-cyan);">${accPct}%</div>
          <div class="pm-kpi-lbl">الدقة (${st.roundCorrect}/${st.roundAnswered})</div>
        </div>
        <div class="pm-kpi-card" style="border-top-color:var(--accent-gold);">
          <div class="pm-kpi-val" style="color:var(--accent-gold);">Lv.${lvlObj.level}</div>
          <div class="pm-kpi-lbl">المستوى 🎖️</div>
        </div>
      </div>

      <div style="background:#060a14; border:1px dashed var(--accent-gold); border-radius:12px; padding:10px 14px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:0.78rem; color:var(--accent-gold); font-weight:900;">🔗 كود تحدي الصديق: ${st.challengeSeed}</span>
        <button type="button" class="dock-lifeline-btn" onclick="window.copyChallengeCodeToClipboard('${st.challengeSeed}')" style="border-color:var(--accent-gold); color:var(--accent-gold);">📋 نسخ</button>
      </div>

      <div style="display:flex; justify-content:center; gap:10px;">
        <button type="button" class="ai-btn" onclick="window.startQuizChallengeNow()">🔄 جولة جديدة</button>
        <button type="button" class="dock-lifeline-btn" onclick="window.returnToQuizLobby()">⚙️ الإعدادات</button>
      </div>
    </div>
  `;
}


// =========================================================
// 13. محرك توافق الجوال والسكرول العرضي الشامل (Mobile UX & Horizontal Scroll Engine)
// =========================================================
(function initDeepPitchMobileUX() {
  function injectMobileMasterStyles() {
    if (document.getElementById('dp-mobile-master-css')) return;
    const style = document.createElement('style');
    style.id = 'dp-mobile-master-css';
    style.innerHTML = `
      /* إصلاح تناسق شريط العودة للرئيسية ومنع التصاقه بعنوان الصفحة */
      .mobile-back-bar {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 12px !important;
        padding: 10px 14px !important;
      }
      .back-btn {
        flex-shrink: 0 !important;
        white-space: nowrap !important;
        padding: 6px 13px !important;
        font-size: 0.78rem !important;
      }
      .back-bar-title {
        flex: 1 !important;
        min-width: 0 !important;
        text-align: left !important;
        font-size: 0.84rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
      }

      /* إصلاح خروج أسماء الأندية من الكونتاينر وتفعيل السكرول في الميركاتو */
      .mercato-chips-group {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        padding-bottom: 6px !important;
        gap: 8px !important;
      }
      .mercato-region-chip, .mercato-filter-chip {
        flex: 0 0 auto !important;
        white-space: nowrap !important;
      }
      .transfer-bridge-box {
        grid-template-columns: minmax(0, 1fr) minmax(80px, 1.05fr) minmax(0, 1fr) !important;
        overflow: hidden !important;
      }
      .t-club-node, .t-arrow-tunnel, .renewal-club-side {
        min-width: 0 !important;
        max-width: 100% !important;
        overflow: hidden !important;
      }
      .t-club-name, .t-fee-lbl, .t-deal-type-lbl {
        max-width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: block !important;
      }

      /* شريط السكرول العرضي القياسي لجميع الفلاتر والأزرار */
      /* شريط السكرول العرضي القياسي لجميع الفلاتر والأزرار */
      .dp-h-scroll-bar {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 10px !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        -webkit-overflow-scrolling: touch !important;
        padding-bottom: 6px !important;
        scrollbar-width: thin !important;
        scrollbar-color: rgba(0, 230, 118, 0.4) transparent !important;
      }
      @media (min-width: 769px) {
        #smart-tools-bar {
          justify-content: center !important;
        }
      }
      .dp-h-scroll-bar::-webkit-scrollbar { height: 4px !important; }
      .dp-h-scroll-bar::-webkit-scrollbar-thumb {
        background: rgba(0, 230, 118, 0.4) !important;
        border-radius: 99px !important;
      }
      .dp-h-scroll-bar > * {
        flex: 0 0 auto !important;
        white-space: nowrap !important;
        scroll-snap-align: start !important;
      }

      /* شريط الدوريات في جميع الأقسام */
      #leagues-bar,
      #standings-leagues-bar,
      #sim-leagues-bar,
      #fdr-leagues-bar,
      #history-leagues-bar,
      #radar-leagues-bar,
      .leagues-bar,
      .league-tabs {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        padding: 8px 10px !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
      }
      #leagues-bar::-webkit-scrollbar,
      .leagues-bar::-webkit-scrollbar { display: none !important; }
      #leagues-bar > *,
      .leagues-bar > * {
        flex: 0 0 auto !important;
        white-space: nowrap !important;
      }

      /* تحسينات شاشات الجوال الشخصية */
      @media (max-width: 768px) {
        .container {
          padding: 10px 8px !important;
        }

        /* الصفحة الرئيسية: عرض البوابات الـ 10 في عمودين متجاورين بدلاً من عمود طويل */
        .nav-grid,
        .portal-grid,
        #main-menu-grid {
          display: grid !important;
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          gap: 10px !important;
        }
        .nav-card,
        .portal-card {
          padding: 12px 10px !important;
          border-radius: 16px !important;
        }
        .nav-card h3,
        .portal-card h3 {
          font-size: 0.88rem !important;
        }
        .nav-card p,
        .portal-card p {
          font-size: 0.68rem !important;
          line-height: 1.35 !important;
        }

        /* هيدر الأقسام الفرعية (عنوان القسم + زر العودة للرئيسية في سطر واحد) */
        .view-header,
        .section-header-bar {
          display: flex !important;
          flex-direction: row !important;
          justify-content: space-between !important;
          align-items: center !important;
          flex-wrap: nowrap !important;
          padding: 10px 12px !important;
          gap: 8px !important;
        }
        .view-header h2 {
          font-size: 0.95rem !important;
          white-space: nowrap !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
          margin: 0 !important;
        }

        /* بطاقتا التبديل في الميركاتو (انتقالات اللاعبين / تجديد العقود) في سكرول أفقي مضغوط */
        .dp-mercato-tabs-row {
          display: flex !important;
          flex-direction: row !important;
          flex-wrap: nowrap !important;
          overflow-x: auto !important;
          gap: 8px !important;
          padding-bottom: 6px !important;
        }
        .dp-mercato-tabs-row > div {
          flex: 0 0 82% !important;
          padding: 10px 12px !important;
        }
        .dp-mercato-tabs-row p,
        .dp-mercato-tabs-row small {
          font-size: 0.66rem !important;
          white-space: nowrap !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
        }

        /* تصغير زر مستشار الفانتازي العائم على الجوال حتى لا يغطي المحتوى */
        #fantasy-fab,
        .fantasy-fab,
        .floating-ai-btn,
        button[onclick*="Fantasy"],
        button[onclick*="fantasy"] {
          padding: 8px 13px !important;
          font-size: 0.76rem !important;
          bottom: 12px !important;
          left: 12px !important;
          border-radius: 99px !important;
          box-shadow: 0 4px 14px rgba(0, 210, 255, 0.35) !important;
        }
      }
    `;
    document.head.appendChild(style);
  }

  function applyHorizontalScrollUpgrades() {
    // 1. صفحة مباريات الجولة: شريط (تذكرة الحسم + صحيفة الجولة + تحديث البيانات)
    const allButtons = Array.from(document.querySelectorAll('button'));
    const ticketBtn = allButtons.find(b => b.textContent && (b.textContent.includes('تذكرة الحسم') || b.textContent.includes('صحيفة الجولة')));
    if (ticketBtn && ticketBtn.parentElement) {
      const actionRow = ticketBtn.parentElement;
      if (!actionRow.classList.contains('dp-h-scroll-bar')) {
        actionRow.classList.add('dp-h-scroll-bar');
      }
    }

    // 2. صفحة الميركاتو والعقود: تبويبات الانتقالات/العقود + فلاتر القارات + فلاتر نوع الصفقة
    const worldBtn = allButtons.find(b => b.textContent && b.textContent.includes('كل أندية العالم'));
    if (worldBtn) {
      const regionRow = worldBtn.parentElement;
      if (regionRow) {
        // إذا كان حقل البحث داخل نفس السطر مع أزرار القارات، نفصله في الأعلى ليأخذ عرضاً كاملاً أنيقاً
        const searchInput = regionRow.parentElement ? regionRow.parentElement.querySelector('input[type="text"], input[placeholder*="ابحث"]') : null;
        if (searchInput && searchInput.parentElement === regionRow) {
          const parentCard = regionRow.parentElement;
          const searchWrap = document.createElement('div');
          searchWrap.style.cssText = 'width:100%; margin-bottom:8px;';
          searchInput.style.cssText += ';width:100% !important; max-width:100% !important; box-sizing:border-box !important;';
          searchWrap.appendChild(searchInput);
          parentCard.insertBefore(searchWrap, regionRow);
        } else if (searchInput && searchInput.parentElement && searchInput.parentElement.parentElement === regionRow.parentElement) {
          // إذا كان البحث وأزرار القارات في صف واحد متجاور (flex-between) نحولهما لعمود فوق بعض
          const combinedRow = regionRow.parentElement;
          combinedRow.style.flexDirection = 'column';
          combinedRow.style.alignItems = 'stretch';
          combinedRow.style.gap = '8px';
          searchInput.style.width = '100%';
        }
        regionRow.classList.add('dp-h-scroll-bar');
      }
    }

    // شريط نوع وحالة الصفقة (تمت رسمياً، مفاوضات جارية، صفقات فشلت، إشاعات، مدربون)
    const doneDealBtn = allButtons.find(b => b.textContent && b.textContent.includes('تمت رسمياً') && b.textContent.length < 25);
    if (doneDealBtn && doneDealBtn.parentElement) {
      doneDealBtn.parentElement.classList.add('dp-h-scroll-bar');
    }

    // بطاقتا التبديل العلويتان في الميركاتو (1. انتقالات اللاعبين / 2. تجديد عقود اللاعبين)
    const allDivs = Array.from(document.querySelectorAll('#mercato-view div, #mercato-container div'));
    const tab1Div = allDivs.find(d => d.textContent && d.textContent.includes('1. انتقالات اللاعبين') && d.children.length <= 4);
    if (tab1Div && tab1Div.parentElement) {
      tab1Div.parentElement.classList.add('dp-mercato-tabs-row');
    }
  }

  // تشغيل فوري ومراقبة أي تحديث ديناميكي في الصفحة
  injectMobileMasterStyles();
  applyHorizontalScrollUpgrades();

  const observer = new MutationObserver(() => {
    applyHorizontalScrollUpgrades();
  });

  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  } else {
    window.addEventListener('DOMContentLoaded', () => {
      applyHorizontalScrollUpgrades();
      observer.observe(document.body, { childList: true, subtree: true });
    });
  }
})();

// =========================================================
// 14. محرك تطبيق الجوال (PWA + شريط التنقل السفلي + تثبيت أعمدة الجداول + الأندية المفضلة الحية)
// =========================================================
(function initDeepPitchMobileSuite() {
  const FAV_STORAGE_KEY = 'deeppitch_favorite_clubs_v1';
  let deferredInstallPrompt = null;
  let lastKnownScores = {};

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

  window.toggleFavoriteClub = function(clubName, event) {
    if (event) {
      event.stopPropagation();
      event.preventDefault();
    }
    const clean = (clubName || '').trim();
    if (!clean || clean.length < 2) return;

    let favs = getFavoriteClubs();
    const existsIdx = favs.findIndex(c => c.toLowerCase() === clean.toLowerCase());
    if (existsIdx >= 0) {
      favs.splice(existsIdx, 1);
      showMobileToast(`تمت إزالة (${clean}) من المفضلة`);
    } else {
      favs.push(clean);
      showMobileToast(`⭐ تمت إضافة (${clean}) إلى أنديتك المفضلة!`);
    }
    saveFavoriteClubs(favs);
    refreshFavoriteStarsAndSorting();
  };

  function showMobileToast(msg) {
    const old = document.getElementById('dp-mobile-toast');
    if (old) old.remove();
    const toast = document.createElement('div');
    toast.id = 'dp-mobile-toast';
    toast.style.cssText = `
      position: fixed; top: 16px; left: 50%; transform: translateX(-50%);
      background: rgba(13, 22, 40, 0.96); border: 1.5px solid #ffd600;
      color: #fff; padding: 9px 18px; border-radius: 99px; font-size: 0.82rem;
      font-weight: 800; z-index: 99999; box-shadow: 0 8px 24px rgba(0,0,0,0.6);
      white-space: nowrap; direction: rtl;
    `;
    toast.innerText = msg;
    document.body.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 2500);
  }

  // 1. حقن تنسيقات شريط التنقل السفلي + تثبيت أعمدة الجداول + النجوم
  function injectMobileSuiteCSS() {
    if (document.getElementById('dp-mobile-suite-css')) return;
    const css = document.createElement('style');
    css.id = 'dp-mobile-suite-css';
    css.innerHTML = `
      /* زر النجمة للأندية المفضلة */
      .dp-fav-star-btn {
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        font-size: 1rem !important;
        line-height: 1 !important;
        padding: 2px 4px !important;
        color: #64748b !important;
        transition: transform 0.18s ease, color 0.18s ease !important;
        vertical-align: middle !important;
      }
      .dp-fav-star-btn.is-fav {
        color: #ffd600 !important;
        text-shadow: 0 0 10px rgba(255, 214, 0, 0.5) !important;
        transform: scale(1.15) !important;
      }

      /* تمييز بطاقة مباراة الفريق المفضل */
      .dp-fav-match-card {
        border: 1.5px solid rgba(255, 214, 0, 0.65) !important;
        box-shadow: 0 0 18px rgba(255, 214, 0, 0.14) !important;
        position: relative !important;
      }

      /* تثبيت العمود الأول (الفريق) عند التمرير الأفقي في الجداول على الجوال */
      /* تثبيت عمود اسم النادي (العمود الثاني) وتفعيل السكرول العرضي في جميع الجداول */
      .standings-layout, .data-card {
        min-width: 0 !important;
        max-width: 100% !important;
      }
      .table-container {
        width: 100% !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
      }
      @media (max-width: 860px) {
        .styled-table {
          min-width: 560px !important;
          border-collapse: separate !important;
          border-spacing: 0 !important;
        }
        .styled-table th:nth-child(2),
        .styled-table td:nth-child(2):not([colspan]) {
          position: sticky !important;
          right: 0 !important;
          z-index: 5 !important;
          background: #0d1526 !important;
          box-shadow: -5px 0 12px rgba(0, 0, 0, 0.65) !important;
          border-left: 1px solid #1d2d4d !important;
        }
        .styled-table th:nth-child(2) {
          z-index: 7 !important;
          background: #090e1c !important;
        }
      }

      /* شريط التنقل السفلي الثابت للهاتف (Bottom Navigation Bar) */
      #dp-bottom-nav {
        display: none;
      }
      @media (max-width: 768px) {
        body {
          padding-bottom: 72px !important;
        }
        #dp-bottom-nav {
          display: flex !important;
          position: fixed !important;
          bottom: 0 !important;
          left: 0 !important;
          right: 0 !important;
          height: 62px !important;
          background: rgba(7, 11, 21, 0.96) !important;
          backdrop-filter: blur(14px) !important;
          -webkit-backdrop-filter: blur(14px) !important;
          border-top: 1px solid rgba(0, 230, 118, 0.25) !important;
          z-index: 9990 !important;
          justify-content: space-around !important;
          align-items: center !important;
          padding: 4px 4px env(safe-area-inset-bottom, 4px) 4px !important;
          box-shadow: 0 -6px 24px rgba(0, 0, 0, 0.65) !important;
        }
        .dp-bnav-btn {
          flex: 1 1 0 !important;
          background: transparent !important;
          border: none !important;
          color: #94a3b8 !important;
          display: flex !important;
          flex-direction: column !important;
          align-items: center !important;
          justify-content: center !important;
          gap: 2px !important;
          font-size: 0.67rem !important;
          font-weight: 800 !important;
          cursor: pointer !important;
          padding: 4px 2px !important;
          border-radius: 10px !important;
          transition: all 0.2s ease !important;
        }
        .dp-bnav-btn .bnav-ico {
          font-size: 1.15rem !important;
          line-height: 1.1 !important;
        }
        .dp-bnav-btn.active {
          color: #00e676 !important;
          background: rgba(0, 230, 118, 0.1) !important;
        }

        /* رفع زر مستشار الفانتازي العائم فوق الشريط السفلي */
        #fantasy-fab,
        .fantasy-fab,
        .floating-ai-btn,
        button[onclick*="Fantasy"],
        button[onclick*="fantasy"] {
          bottom: 72px !important;
          left: 12px !important;
          padding: 7px 12px !important;
          font-size: 0.74rem !important;
        }
      }
    `;
    document.head.appendChild(css);
  }

  // 2. بناء شريط التنقل السفلي للجوال وربطه بالبوابات الرئيسية
  function buildMobileBottomNav() {
    if (document.getElementById('dp-bottom-nav')) return;
    const nav = document.createElement('nav');
    nav.id = 'dp-bottom-nav';
    nav.setAttribute('dir', 'rtl');

    const tabs = [
      { id: 'home', icon: '🏠', label: 'الرئيسية', keywords: [] },
      { id: 'today', icon: '🔴', label: 'مباشر', keywords: ['مباريات اليوم'] },
      { id: 'standings', icon: '🏆', label: 'الترتيب', keywords: ['جدول الترتيب'] },
      { id: 'mercato', icon: '🔄', label: 'الميركاتو', keywords: ['الانتقالات', 'الميركاتو'] },
      { id: 'quiz', icon: '🎮', label: 'المسابقات', keywords: ['التحدي الكروي', 'المسابقات'] }
    ];

    nav.innerHTML = tabs.map((t, idx) => `
      <button type="button" class="dp-bnav-btn ${idx === 0 ? 'active' : ''}" data-bnav="${t.id}">
        <span class="bnav-ico">${t.icon}</span>
        <span>${t.label}</span>
      </button>
    `).join('');

    document.body.appendChild(nav);

    nav.querySelectorAll('.dp-bnav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        nav.querySelectorAll('.dp-bnav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-bnav');

        if (targetId === 'home') {
          const backBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('العودة للرئيسية'));
          if (backBtn && backBtn.offsetParent !== null) backBtn.click();
          window.scrollTo({ top: 0, behavior: 'smooth' });
          return;
        }

        const tabObj = tabs.find(x => x.id === targetId);
        if (!tabObj) return;

        // البحث عن بطاقة البوابة المطابقة وتشغيلها
        const portalCards = Array.from(document.querySelectorAll('.nav-card, .portal-card, [onclick]'));
        const matchedCard = portalCards.find(el => {
          const txt = el.textContent || '';
          return tabObj.keywords.some(kw => txt.includes(kw)) && !el.closest('#dp-bottom-nav');
        });
        if (matchedCard) {
          matchedCard.click();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
      });
    });
  }

  // 3. تسجيل Service Worker وتفعيل زر تثبيت التطبيق (PWA)
  function registerPWAEngine() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredInstallPrompt = e;

      if (document.getElementById('dp-pwa-install-pill')) return;
      const headerEl = document.querySelector('header, .hero-header, .container');
      if (!headerEl) return;

      const installBtn = document.createElement('button');
      installBtn.id = 'dp-pwa-install-pill';
      installBtn.type = 'button';
      installBtn.innerHTML = '📲 تثبيت التطبيق على جوالك';
      installBtn.style.cssText = `
        display: inline-flex; align-items: center; gap: 6px; margin: 8px auto 0 auto;
        background: linear-gradient(90deg, #00e676, #00d2ff); color: #050912;
        border: none; padding: 7px 16px; border-radius: 99px; font-size: 0.78rem;
        font-weight: 900; cursor: pointer; box-shadow: 0 4px 15px rgba(0, 230, 118, 0.35);
      `;
      installBtn.onclick = async () => {
        if (!deferredInstallPrompt) return;
        deferredInstallPrompt.prompt();
        const choice = await deferredInstallPrompt.userChoice;
        if (choice && choice.outcome === 'accepted') {
          installBtn.remove();
        }
        deferredInstallPrompt = null;
      };
      headerEl.insertAdjacentElement('afterbegin', installBtn);
    });
  }

  // 4. إضافة نجوم المفضلة بجانب الأندية وترتيب المباريات المفضلة في الأعلى
  let onlyFavoritesFilter = false;

  function refreshFavoriteStarsAndSorting() {
    const favs = getFavoriteClubs();

    // أ) إضافة النجمة في صفوف جدول الترتيب
    document.querySelectorAll('table tbody tr').forEach(tr => {
      const cells = tr.querySelectorAll('td');
      if (cells.length < 2) return;
      const teamCell = cells[0].querySelector('img') ? cells[0] : (cells[1].querySelector('img') ? cells[1] : cells[0]);
      if (!teamCell) return;

      const rawName = teamCell.textContent.replace(/[☆⭐0-9]/g, '').trim();
      if (!rawName || rawName.length < 2) return;

      let starBtn = teamCell.querySelector('.dp-fav-star-btn');
      if (!starBtn) {
        starBtn = document.createElement('button');
        starBtn.type = 'button';
        starBtn.className = 'dp-fav-star-btn';
        starBtn.title = 'إضافة إلى أنديتي المفضلة';
        starBtn.onclick = (ev) => window.toggleFavoriteClub(rawName, ev);
        teamCell.prepend(starBtn);
      }
      const active = isClubFavorite(rawName);
      starBtn.innerText = active ? '⭐' : '☆';
      starBtn.classList.toggle('is-fav', active);
    });

    // ب) إضافة النجوم في بطاقات المباريات (مباريات اليوم ومباريات الجولة)
    const matchCards = Array.from(document.querySelectorAll('.match-card, .fixture-card, [data-match-id]'));
    if (matchCards.length > 0) {
      const listParent = matchCards[0].parentElement;
      if (listParent && !document.getElementById('dp-fav-filter-bar') && favs.length > 0) {
        const bar = document.createElement('div');
        bar.id = 'dp-fav-filter-bar';
        bar.style.cssText = 'display:flex; justify-content:space-between; align-items:center; background:#0b1324; border:1px solid rgba(255,214,0,0.35); padding:7px 12px; border-radius:12px; margin-bottom:10px; font-size:0.78rem;';
        bar.innerHTML = `
          <span style="color:#ffd600; font-weight:800;">⭐ أنديتك المفضلة (${favs.length}) مثبتة في الأعلى</span>
          <button type="button" id="dp-toggle-only-favs" style="background:#13203b; border:1px solid #ffd600; color:#ffd600; padding:4px 10px; border-radius:99px; font-size:0.72rem; font-weight:800; cursor:pointer;">
            عرض المفضلة فقط
          </button>
        `;
        listParent.parentElement.insertBefore(bar, listParent);
        document.getElementById('dp-toggle-only-favs').onclick = function() {
          onlyFavoritesFilter = !onlyFavoritesFilter;
          this.innerText = onlyFavoritesFilter ? 'عرض جميع المباريات' : 'عرض المفضلة فقط';
          refreshFavoriteStarsAndSorting();
        };
      }

      matchCards.forEach(card => {
        const teamEls = card.querySelectorAll('.team-name, h4, strong');
        let cardHasFav = false;
        teamEls.forEach(el => {
          const tName = el.textContent.replace(/[☆⭐]/g, '').trim();
          if (!tName || tName.length < 2 || tName.length > 28 || /\d/.test(tName)) return;
          if (isClubFavorite(tName)) cardHasFav = true;

          let sBtn = el.querySelector('.dp-fav-star-btn');
          if (!sBtn && (el.classList.contains('team-name') || el.tagName === 'H4')) {
            sBtn = document.createElement('button');
            sBtn.type = 'button';
            sBtn.className = 'dp-fav-star-btn';
            sBtn.onclick = (ev) => window.toggleFavoriteClub(tName, ev);
            el.appendChild(sBtn);
          }
          if (sBtn) {
            const act = isClubFavorite(tName);
            sBtn.innerText = act ? '⭐' : '☆';
            sBtn.classList.toggle('is-fav', act);
          }
        });

        card.classList.toggle('dp-fav-match-card', cardHasFav);
        if (onlyFavoritesFilter) {
          card.style.display = cardHasFav ? '' : 'none';
        } else {
          card.style.display = '';
        }

        // تنبيه صوتي خفيف عند تغير نتيجة مباراة لفريق مفضل أثناء التصفح
        const mId = card.getAttribute('data-match-id') || card.id;
        const scoreTxt = (card.querySelector('.score-box, .match-score') || {}).textContent || '';
        if (cardHasFav && mId && scoreTxt.includes('-')) {
          if (lastKnownScores[mId] && lastKnownScores[mId] !== scoreTxt) {
            showMobileToast(`⚽ جووول! تحديث في مباراة فريقك المفضل (${scoreTxt.trim()})`);
            if (typeof playQuizSound === 'function') playQuizSound('correct');
          }
          lastKnownScores[mId] = scoreTxt;
        }
      });

      // رفع بطاقات الأندية المفضلة إلى أعلى القائمة تلقائياً
      if (listParent && favs.length > 0) {
        const favCards = matchCards.filter(c => c.classList.contains('dp-fav-match-card'));
        favCards.reverse().forEach(fc => {
          if (listParent.firstChild !== fc) {
            listParent.insertBefore(fc, listParent.firstChild);
          }
        });
      }
    }
  }

  injectMobileSuiteCSS();
  registerPWAEngine();

  let debounceTimer = null;
  const scheduleEnhance = () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      buildMobileBottomNav();
      refreshFavoriteStarsAndSorting();
    }, 220);
  };

  if (document.body) {
    scheduleEnhance();
    new MutationObserver(scheduleEnhance).observe(document.body, { childList: true, subtree: true });
  } else {
    window.addEventListener('DOMContentLoaded', () => {
      scheduleEnhance();
      new MutationObserver(scheduleEnhance).observe(document.body, { childList: true, subtree: true });
    });
  
  }
})();