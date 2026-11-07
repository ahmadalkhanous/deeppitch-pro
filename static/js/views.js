// ==========================================
// DeepPitch Pro - Views & Render Engines
// ==========================================

// التبديل الموحد بين الأقسام الرئيسية
// ==========================================
// DeepPitch Pro - Views & Render Engines
// ==========================================

// التبديل بين الشاشات: إخفاء الكروت وعرض المحتوى مباشرة في الأعلى
// ==========================================
// DeepPitch Pro - Views & Navigation System
// ==========================================

// 1. التبديل بين الشاشات: إخفاء الكروت وعرض محتوى القسم المطلوب فوراً في الأعلى
function activateSection(section) {
  window.activeSection = section;

  // إخفاء شبكة الكروت الرئيسية ورسالة الترحيب
  const hubGrid = document.getElementById('hub-grid-container');
  if (hubGrid) hubGrid.style.display = 'none';

  const welcome = document.getElementById('welcome-placeholder');
  if (welcome) welcome.style.display = 'none';

  // إظهار شريط الرجوع وتعيين عنوان القسم
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
      'news': '📰 غرفة الأخبار الرياضية'
    };
    if (viewTitle) viewTitle.innerText = sectionTitles[section] || 'عرض النتائج';
  }

  // إظهار شريط الدوريات في الأقسام التي تعتمد على دوري محدد
  const mainMenu = document.getElementById('main-menu-section');
  const needsLeague = ['fixtures', 'standings', 'projections', 'fdr'].includes(section);
  if (mainMenu) mainMenu.style.display = needsLeague ? 'block' : 'none';

  // إظهار القسم المختار وإخفاء باقي الأقسام
  const allViews = ['fixtures', 'today', 'standings', 'projections', 'fdr', 'news'];
  allViews.forEach(v => {
    const el = document.getElementById(`${v}-view`);
    if (el) el.style.display = (v === section) ? 'block' : 'none';
  });

  // إيقاف التحديث التلقائي لمباريات اليوم عند الانتقال لقسم آخر
  if (typeof todayPollingTimeout !== 'undefined' && todayPollingTimeout) {
    clearTimeout(todayPollingTimeout);
    todayPollingTimeout = null;
  }

  // التمرير لأعلى الشاشة مباشرة
  window.scrollTo(0, 0);

  // استدعاء جلب البيانات المباشرة بحسب القسم المختار فوراً
  const league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  if (section === 'today') {
    loadTodayMatches();
  } else if (section === 'news') {
    loadNewsFeed();
  } else if (section === 'fixtures') {
    loadGameweek(league);
  } else if (section === 'standings') {
    loadOfficialStandingsAndScorers(league);
  } else if (section === 'projections') {
    loadProjections(league);
  } else if (section === 'fdr') {
    loadFDR(league);
  }
}

// 2. العودة للشاشة الرئيسية وإعادة إظهار الكروت
function goBackToMainMenu() {
  const allViews = ['fixtures', 'today', 'standings', 'projections', 'fdr', 'news'];
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

// 3. إعادة تحميل القسم الحالي عند تبديل الدوري من الشريط
function refreshCurrentView() {
  const league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
  const sec = (typeof activeSection !== 'undefined' && activeSection) ? activeSection : (window.activeSection || 'fixtures');

  if (sec === 'fixtures') {
    loadGameweek(league);
  } else if (sec === 'standings') {
    loadOfficialStandingsAndScorers(league);
  } else if (sec === 'projections') {
    loadProjections(league);
  } else if (sec === 'fdr') {
    loadFDR(league);
  } else if (sec === 'today') {
    loadTodayMatches();
  } else if (sec === 'news') {
    loadNewsFeed();
  }
}

// 1. عرض كروت مباريات الجولة والرادار التكتيكي
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

        <div class="vs-center">
          <div class="score-badge">${f.predicted_score}</div>
          <div class="score-label">ثقة (${f.score_confidence}%)</div>
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

// 2. مباريات اليوم المباشرة
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
    window.currentTodayMatches = matches; // <--- تخزين عالمي مباشر

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
            <img src="${m.home_crest}" onerror="this.src='https://via.placeholder.com/44?text=FC'">
            <div style="font-weight:800; font-size:0.92rem;">${m.home_team}</div>
          </div>

          <div class="today-score-box">
            ${m.state === 'pre' 
              ? `<div style="font-size:1.05rem; color:var(--accent-gold);">${m.kickoff_time}</div>` 
              : `<span style="color:${m.is_live ? '#ff5252' : 'var(--text)'}; font-size:1.25rem; font-weight:900;">${m.home_score} - ${m.away_score}</span>`}
          </div>

          <div class="today-team">
            <img src="${m.away_crest}" onerror="this.src='https://via.placeholder.com/44?text=FC'">
            <div style="font-weight:800; font-size:0.92rem;">${m.away_team}</div>
          </div>
        </div>

        <div class="today-meta">
          <div>🏟️ <strong>الملعب:</strong> ${m.venue}</div>
          <div>📺 <strong>القناة:</strong> ${m.channel}</div>
          <div style="grid-column: 1/-1;">🎙️ <strong>المعلق:</strong> ${m.commentator}</div>
        </div>

        <div style="text-align:center; font-size:0.75rem; color:var(--accent-cyan); margin-top:10px; border-top:1px dashed #1e293b; padding-top:8px;">
          📊 انقر لمشاهدة إحصائيات المباراة وتفاصيل اللقاء
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
  if (typeof activeSection !== 'undefined' && activeSection === 'today') {
    todayPollingTimeout = setTimeout(loadTodayMatches, delayMs);
  }
}

// 3. جدول الترتيب الرسمي وقائمة الهدافين الحية من الـ API مباشرة
async function loadOfficialStandingsAndScorers(leagueCode) {
  const tbody = document.getElementById('official-standings-tbody') || document.getElementById('standings-tbody');
  const scorersList = document.getElementById('top-scorers-list') || document.getElementById('scorers-tbody');

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

    // رندر جدول الترتيب مع كلاسات التجاوب للجوال
    if (tbody) {
      const totalTeams = standings.length;
      if (totalTeams === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="loading-state">لا تتوفر بيانات ترتيب حالياً لهذا الدوري.</td></tr>';
      } else {
        tbody.innerHTML = standings.map(t => {
          let zoneClass = "";
          if (t.rank <= 4) zoneClass = "rank-ucl";
          else if (t.rank === 5 || t.rank === 6) zoneClass = "rank-uel";
          else if (totalTeams >= 12 && t.rank > (totalTeams - 3)) zoneClass = "rank-rel";

          return `
            <tr>
              <td class="${zoneClass}"><strong>${t.rank}</strong></td>
              <td class="team-col-cell">
                <div style="display:flex; align-items:center; gap:6px;">
                  <img src="${t.crest}" width="20" height="20" onerror="this.src='https://via.placeholder.com/20?text=FC'">
                  <strong class="team-title-sm">${t.short_name || t.team_name}</strong>
                </div>
              </td>
              <td>${t.played}</td>
              <td class="col-hide-mobile">${t.won}</td>
              <td class="col-hide-mobile">${t.drawn}</td>
              <td class="col-hide-mobile">${t.lost}</td>
              <td class="col-hide-mobile">${t.gf}:${t.ga}</td>
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
          `;
        }).join('');
      }
    }

    // رندر قائمة الهدافين
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

// 4. محاكي نهاية الموسم (Monte Carlo)
async function loadProjections(leagueCode) {
  const tbody = document.getElementById('projections-tbody');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:35px; color:var(--muted);">جاري تشغيل محاكي مونت كارلو ومحاكاة 1,500 موسم افتراضي...</td></tr>';

  try {
    const res = await fetch(`/api/season_projections/${leagueCode}`);
    const data = await res.json();
    const dataList = data.projections || [];

    if (dataList.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:25px; color:var(--muted);">لا توجد بيانات متاحة لهذا الدوري.</td></tr>';
      return;
    }

    tbody.innerHTML = dataList.map((row, idx) => `
      <tr>
        <td style="font-weight:900; color:var(--accent-gold);">#${idx + 1}</td>
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
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--accent-red);">فشل جلب بيانات المحاكاة، يرجى المحاولة لاحقاً.</td></tr>';
  }
}

// 5. مصفوفة صعوبة المباريات (FDR)
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
        ${row.fixtures.map(f => `
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

// 6. غرفة الأخبار الرياضية الحية (FIFO 20)
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

  const modal = document.getElementById('news-reader-modal');
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

  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

// إغلاق النوافذ المنبثقة بالنقر خارج المحتوى على شاشات اللمس
document.addEventListener('click', (e) => {
  if (e.target.classList && e.target.classList.contains('modal-overlay')) {
    e.target.style.display = 'none';
    document.body.style.overflow = '';
  }
});