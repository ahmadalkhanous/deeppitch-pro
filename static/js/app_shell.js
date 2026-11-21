// =========================================================
// DeepPitch Pro - App Shell, Hash Router & Global Search Engine
// =========================================================

(function initDeepPitchAppShell() {
  const PILLARS = {
    matches: {
      id: 'matches',
      label: 'المباريات',
      defaultSection: 'today',
      tabs: [
        { section: 'today', label: 'مباريات اليوم والمباشر', badge: 'LIVE' },
        { section: 'fixtures', label: 'مباريات الجولة والتوقعات' }
      ]
    },
    leagues: {
      id: 'leagues',
      label: 'البطولات',
      defaultSection: 'standings',
      tabs: [
        { section: 'standings', label: 'الترتيب والهدافون' },
        { section: 'fixtures', label: 'مباريات الجولة' },
        { section: 'projections', label: 'محاكي نهاية الموسم' },
        { section: 'history', label: 'الموسوعة والأرشيف' }
      ]
    },
    media: {
      id: 'media',
      label: 'الميركاتو والأخبار',
      defaultSection: 'transfers',
      tabs: [
        { section: 'transfers', label: 'سوق الانتقالات والعقود' },
        { section: 'news', label: 'غرفة الأخبار الحية' }
      ]
    },
    explore: {
      id: 'explore',
      label: 'الاستكشاف والمختبر',
      defaultSection: 'cards',
      tabs: [
        { section: 'cards', label: 'بطاقات FIFA والأندية والمنتخبات' },
        { section: 'radar', label: 'استوديو المقارنة الرادارية' }
      ]
    },
    quiz: {
      id: 'quiz',
      label: 'ساحة التحدي',
      defaultSection: 'quiz',
      tabs: []
    }
  };

  const SECTION_TO_PILLAR = {
    today: 'matches',
    fixtures: 'leagues',
    standings: 'leagues',
    projections: 'leagues',
    history: 'leagues',
    transfers: 'media',
    news: 'media',
    cards: 'explore',
    radar: 'explore',
    quiz: 'quiz'
  };

  const VALID_SECTIONS = Object.keys(SECTION_TO_PILLAR);
  let activePillar = 'matches';
  let deferredInstallEvent = null;

  const _origActivateSection = typeof window.activateSection === 'function' ? window.activateSection : null;

  function safeTextStr(v) {
    return String(v !== undefined && v !== null ? v : '');
  }

  function escapeStr(s) {
    return safeTextStr(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function getOpenModal() {
    const modals = document.querySelectorAll('.modal-overlay');
    for (let i = modals.length - 1; i >= 0; i--) {
      if (window.getComputedStyle(modals[i]).display !== 'none') {
        return modals[i];
      }
    }
    return null;
  }

  function closeAllOverlays() {
    document.querySelectorAll('.modal-overlay').forEach(m => {
      m.style.display = 'none';
    });
    const notifPop = document.getElementById('dp-notify-popover');
    if (notifPop) notifPop.classList.remove('open');
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
  }

  function renderSubNavigation(pillarKey, currentSection) {
    const bar = document.getElementById('dp-subnav-bar');
    const inner = document.getElementById('dp-subnav-tabs');
    if (!bar || !inner) return;

    const pillar = PILLARS[pillarKey];
    if (!pillar || !pillar.tabs || pillar.tabs.length === 0) {
      bar.style.display = 'none';
      inner.innerHTML = '';
      return;
    }

    bar.style.display = 'block';
    inner.innerHTML = pillar.tabs.map(tab => {
      const isActive = tab.section === currentSection;
      const liveBadge = tab.badge === 'LIVE' ? '<span class="dp-subtab-live-dot"></span>' : '';
      return `
        <button type="button"
          class="dp-subtab-btn ${isActive ? 'active' : ''}"
          onclick="window.activateSection('${tab.section}', { pillar: '${pillarKey}' })">
          ${liveBadge}
          <span>${tab.label}</span>
        </button>
      `;
    }).join('');
  }

  function syncNavUI(pillarKey) {
    activePillar = pillarKey;

    document.querySelectorAll('.dp-nav-link').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-pillar') === pillarKey);
    });

    document.querySelectorAll('#dp-bottom-nav .dp-bnav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-pillar') === pillarKey);
    });
  }

  function syncContextualLeagueTools(section) {
    const accaBtn = document.getElementById('tool-btn-acca');
    const paperBtn = document.getElementById('tool-btn-newspaper');
    const showMatchweekTools = section === 'fixtures';
    if (accaBtn) accaBtn.style.display = showMatchweekTools ? 'inline-flex' : 'none';
    if (paperBtn) paperBtn.style.display = showMatchweekTools ? 'inline-flex' : 'none';
  }

  // التفاف نظيف حول activateSection لربط التوجيه والتبويبات والشريطين العلوي والسفلي
  window.activateSection = function(section, opts = {}) {
    const cleanSection = VALID_SECTIONS.includes(section) ? section : 'today';
    const targetPillar = opts.pillar || (cleanSection === 'fixtures' && activePillar === 'matches' ? 'matches' : SECTION_TO_PILLAR[cleanSection]) || 'matches';

    closeAllOverlays();

    if (!opts.fromHash && window.location.hash !== '#' + cleanSection) {
      try {
        history.pushState({ section: cleanSection, pillar: targetPillar }, '', '#' + cleanSection);
      } catch (e) {
        window.location.hash = cleanSection;
      }
    }

    syncNavUI(targetPillar);
    renderSubNavigation(targetPillar, cleanSection);
    syncContextualLeagueTools(cleanSection);

    if (_origActivateSection) {
      _origActivateSection(cleanSection);
    }

    // التأكد من بقاء شريط التنقل السفلي متزامناً مع المحور الحالي
    syncNavUI(targetPillar);
  };

  window.switchPillar = function(pillarKey) {
    const pillar = PILLARS[pillarKey] || PILLARS.matches;
    window.activateSection(pillar.defaultSection, { pillar: pillar.id });
  };

  window.goBackToMainMenu = function() {
    window.activateSection('today', { pillar: 'matches' });
  };

  window.syncMobileBottomNav = function(key) {
    const mapped = PILLARS[key] ? key : (SECTION_TO_PILLAR[key] || 'matches');
    syncNavUI(mapped);
  };

  // =========================================================
  // قائمة الإشعارات المدمجة في الجرس العلوي
  // =========================================================
  window.toggleNotifyPopover = function(ev) {
    if (ev) ev.stopPropagation();
    const pop = document.getElementById('dp-notify-popover');
    if (pop) pop.classList.toggle('open');
  };

  // =========================================================
  // محرك البحث العالمي الفوري (Global Quick Search)
  // =========================================================
  window.openGlobalSearch = function() {
    const modal = document.getElementById('global-search-modal');
    const inp = document.getElementById('global-search-input');
    if (!modal) return;
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    renderGlobalSearchResults(inp ? inp.value : '');
    if (inp) setTimeout(() => inp.focus(), 60);
  };

  window.onGlobalSearchType = function(val) {
    renderGlobalSearchResults(val);
  };

  function renderGlobalSearchResults(rawQuery) {
    const box = document.getElementById('global-search-results');
    if (!box) return;
    const q = safeTextStr(rawQuery).trim().toLowerCase();

    const quickNavs = [
      { label: 'مباريات اليوم والمباشر', sub: 'النتائج الحية والتشكيلات واستوديو المحللين', section: 'today', pillar: 'matches', tag: 'مباشر' },
      { label: 'مباريات الجولة والتوقعات', sub: 'نموذج ديكسون-كولز ورادار التعثر', section: 'fixtures', pillar: 'matches', tag: 'توقعات' },
      { label: 'جدول الترتيب والهدافون', sub: '12 بطولة رسمية محدثة حياً', section: 'standings', pillar: 'leagues', tag: 'الترتيب' },
      { label: 'محاكي نهاية الموسم (Monte Carlo)', sub: '1,500 محاكاة لنسب التتويج والهبوط', section: 'projections', pillar: 'leagues', tag: 'محاكاة' },
      { label: 'سوق الانتقالات وتجديد العقود', sub: 'الصفقات الرسمية والمفاوضات الجارية', section: 'transfers', pillar: 'media', tag: 'ميركاتو' },
      { label: 'بطاقات FIFA والأندية والمنتخبات', sub: 'تصنيف الفيفا وخزانة الألقاب وطاقات اللاعبين', section: 'cards', pillar: 'explore', tag: 'بطاقات' },
      { label: 'استوديو المقارنة الرادارية (Opta)', sub: 'مقارنة سداسية ومحاكي القمم', section: 'radar', pillar: 'explore', tag: 'رادار' },
      { label: 'ساحة التحدي الكروي', sub: '14 فئة أسئلة كروية حية', section: 'quiz', pillar: 'quiz', tag: 'مسابقات' }
    ];

    if (!q) {
      box.innerHTML = `
        <div class="gsearch-group-title">وصول سريع للأقسام</div>
        <div class="gsearch-list">
          ${quickNavs.map(item => `
            <button type="button" class="gsearch-item" onclick="closeModal('global-search-modal'); window.activateSection('${item.section}', { pillar: '${item.pillar}' });">
              <div class="gsearch-item-main">
                <div class="gsearch-item-title">${escapeStr(item.label)}</div>
                <div class="gsearch-item-sub">${escapeStr(item.sub)}</div>
              </div>
              <span class="gsearch-tag">${escapeStr(item.tag)}</span>
            </button>
          `).join('')}
        </div>
      `;
      return;
    }

    const htmlBlocks = [];

    // 1. البحث في مباريات اليوم
    const todayMatches = (window.currentTodayMatches || []).filter(m =>
      `${m.home_team} ${m.away_team} ${m.league_name}`.toLowerCase().includes(q)
    ).slice(0, 6);

    if (todayMatches.length > 0) {
      htmlBlocks.push(`
        <div class="gsearch-group-title">مباريات اليوم (${todayMatches.length})</div>
        <div class="gsearch-list">
          ${todayMatches.map(m => {
            const realIdx = (window.currentTodayMatches || []).indexOf(m);
            return `
              <button type="button" class="gsearch-item" onclick="closeModal('global-search-modal'); window.activateSection('today'); setTimeout(() => openTodayMatchModal(${realIdx}), 120);">
                <div class="gsearch-item-main">
                  <div class="gsearch-item-title">${escapeStr(m.home_team)} ضد ${escapeStr(m.away_team)}</div>
                  <div class="gsearch-item-sub">${escapeStr(m.league_name)} • ${escapeStr(m.status_text)}</div>
                </div>
                <span class="gsearch-tag">${m.state === 'pre' ? escapeStr(m.kickoff_time) : `${m.home_score} - ${m.away_score}`}</span>
              </button>
            `;
          }).join('')}
        </div>
      `);
    }

    // 2. البحث في أندية الترتيب المخزنة
    const standingsHit = (window._cachedStandingsData || []).filter(t =>
      `${t.short_name} ${t.team_name}`.toLowerCase().includes(q)
    ).slice(0, 5);

    if (standingsHit.length > 0) {
      htmlBlocks.push(`
        <div class="gsearch-group-title">أندية الجدول الحالي</div>
        <div class="gsearch-list">
          ${standingsHit.map(t => `
            <button type="button" class="gsearch-item" onclick="closeModal('global-search-modal'); window.activateSection('standings', { pillar: 'leagues' });">
              <div class="gsearch-item-main">
                <div class="gsearch-item-title">${escapeStr(t.short_name || t.team_name)}</div>
                <div class="gsearch-item-sub">المركز #${t.rank} • ${t.points} نقطة (${t.played} لعب)</div>
              </div>
              <span class="gsearch-tag">الترتيب</span>
            </button>
          `).join('')}
        </div>
      `);
    }

    // 3. البحث في الميركاتو والعقود
    const mState = window._mercatoState || {};
    const mercatoAll = [...(mState.transfersList || []), ...(mState.contractsList || [])];
    const mercatoHit = mercatoAll.filter(it =>
      `${it.name} ${it.from_club} ${it.to_club || ''}`.toLowerCase().includes(q)
    ).slice(0, 5);

    if (mercatoHit.length > 0) {
      htmlBlocks.push(`
        <div class="gsearch-group-title">سوق الانتقالات والعقود</div>
        <div class="gsearch-list">
          ${mercatoHit.map(it => {
            const kind = it.to_club ? 'transfers' : 'contracts';
            return `
              <button type="button" class="gsearch-item" onclick="closeModal('global-search-modal'); window.activateSection('transfers', { pillar: 'media' }); setTimeout(() => openMercatoDetailModal('${kind}', '${escapeStr(it.id)}'), 180);">
                <div class="gsearch-item-main">
                  <div class="gsearch-item-title">${escapeStr(it.name)}</div>
                  <div class="gsearch-item-sub">${escapeStr(it.from_club)}${it.to_club ? ' ← ' + escapeStr(it.to_club) : ''} • ${escapeStr(it.status_label)}</div>
                </div>
                <span class="gsearch-tag">ميركاتو</span>
              </button>
            `;
          }).join('')}
        </div>
      `);
    }

    // 4. البحث في الأقسام
    const secHits = quickNavs.filter(s => `${s.label} ${s.sub} ${s.tag}`.toLowerCase().includes(q));
    if (secHits.length > 0) {
      htmlBlocks.push(`
        <div class="gsearch-group-title">الأقسام</div>
        <div class="gsearch-list">
          ${secHits.map(item => `
            <button type="button" class="gsearch-item" onclick="closeModal('global-search-modal'); window.activateSection('${item.section}', { pillar: '${item.pillar}' });">
              <div class="gsearch-item-main">
                <div class="gsearch-item-title">${escapeStr(item.label)}</div>
                <div class="gsearch-item-sub">${escapeStr(item.sub)}</div>
              </div>
              <span class="gsearch-tag">${escapeStr(item.tag)}</span>
            </button>
          `).join('')}
        </div>
      `);
    }

    if (htmlBlocks.length === 0) {
      box.innerHTML = `
        <div class="gsearch-empty">
          لم نجد نتائج مباشرة لـ "<strong>${escapeStr(rawQuery)}</strong>".<br>
          <span>جرّب البحث باسم فريق من مباريات اليوم أو انتقل لقسم البطاقات والميركاتو للبحث الموسع.</span>
        </div>
      `;
    } else {
      box.innerHTML = htmlBlocks.join('');
    }
  }

  // =========================================================
  // معالجة زر الرجوع (Browser / Mobile Back) + اختصارات لوحة المفاتيح + PWA + Offline
  // =========================================================
  window.addEventListener('popstate', () => {
    const openModal = getOpenModal();
    if (openModal) {
      openModal.style.display = 'none';
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
      return;
    }
    const hashSec = (window.location.hash || '#today').replace('#', '').trim();
    if (VALID_SECTIONS.includes(hashSec)) {
      window.activateSection(hashSec, { fromHash: true });
    } else {
      window.activateSection('today', { fromHash: true });
    }
  });

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      window.openGlobalSearch();
      return;
    }
    if (e.key === 'Escape') {
      closeAllOverlays();
    }
  });

  document.addEventListener('click', (e) => {
    const pop = document.getElementById('dp-notify-popover');
    const bellBtn = document.getElementById('dp-bell-trigger');
    if (pop && pop.classList.contains('open')) {
      if (!pop.contains(e.target) && (!bellBtn || !bellBtn.contains(e.target))) {
        pop.classList.remove('open');
      }
    }
  });

  // إدارة زر التثبيت PWA داخل الشريط العلوي بهدوء
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallEvent = e;
    const btn = document.getElementById('dp-pwa-install-pill');
    if (btn) {
      btn.style.display = 'inline-flex';
      btn.onclick = async () => {
        if (!deferredInstallEvent) return;
        deferredInstallEvent.prompt();
        const choice = await deferredInstallEvent.userChoice;
        if (choice && choice.outcome === 'accepted') btn.style.display = 'none';
        deferredInstallEvent = null;
      };
    }
  });

  // مراقبة حالة الاتصال بالإنترنت
  function updateOnlineBanner() {
    const banner = document.getElementById('dp-offline-banner');
    if (!banner) return;
    banner.style.display = navigator.onLine ? 'none' : 'flex';
  }
  window.addEventListener('online', updateOnlineBanner);
  window.addEventListener('offline', updateOnlineBanner);

  // الإقلاع التلقائي المباشر إلى القسم المطلوب أو مباريات اليوم الحية (بدون شاشة المتاهة)
  function bootAppShell() {
    updateOnlineBanner();
    const initialHash = (window.location.hash || '#today').replace('#', '').trim();
    const startSection = VALID_SECTIONS.includes(initialHash) ? initialHash : 'today';
    window.activateSection(startSection, { fromHash: true });
  }

  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', () => setTimeout(bootAppShell, 30));
  } else {
    setTimeout(bootAppShell, 30);
  }
})();