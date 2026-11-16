// =========================================================
// DeepPitch Pro - Modals, Stats, Lineups & Sandbox Engine
// =========================================================

var currentModalFixture = null;
window.activeMatchModalData = null;
window.activeMatchStatsData = null;
window.currentMatchEventsCache = [];

var ESPN_LEAGUE_MAP = {
  'PL': 'eng.1', 'PD': 'esp.1', 'BL1': 'ger.1', 'SA': 'ita.1',
  'FL1': 'fra.1', 'DED': 'ned.1', 'PPL': 'por.1', 'TSL': 'tur.1',
  'UCL': 'uefa.champions', 'ACL': 'afc.champions', 'CAF': 'caf.champions', 'UNL': 'uefa.nations'
};

function safeText(id, val) {
  var el = document.getElementById(id);
  if (el) el.innerText = (val !== undefined && val !== null) ? val : '';
}

function safeHtml(id, html) {
  var el = document.getElementById(id);
  if (el) el.innerHTML = html || '';
}

function safeSrc(id, src) {
  var el = document.getElementById(id);
  if (el && src) el.src = src;
}

function safeWidth(id, pct) {
  var el = document.getElementById(id);
  if (el) el.style.width = Math.min(100, Math.max(0, pct || 0)) + '%';
}

window.closeModal = function(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = 'auto';
  document.documentElement.style.overflow = 'auto';
};

// =========================================================
// 1. نظام التبديل الموحد بين تبويبات المباراة الأربعة
// =========================================================
window.switchMatchTab = function(tab) {
  var statsWrapper = document.getElementById('tm-stats-wrapper') || document.getElementById('tm-stats-card');
  var momentumTab = document.getElementById('tm-momentum-tab');
  var eventsTab = document.getElementById('tm-events-tab');
  var lineupTab = document.getElementById('tm-lineup-tab');

  var btnStats = document.getElementById('btn-tab-stats');
  var btnMomentum = document.getElementById('btn-tab-momentum');
  var btnEvents = document.getElementById('btn-tab-events');
  var btnLineup = document.getElementById('btn-tab-lineup');

  if (statsWrapper) statsWrapper.style.display = (tab === 'stats') ? 'block' : 'none';
  if (momentumTab) momentumTab.style.display = (tab === 'momentum') ? 'block' : 'none';
  if (eventsTab) eventsTab.style.display = (tab === 'events') ? 'block' : 'none';
  if (lineupTab) lineupTab.style.display = (tab === 'lineup') ? 'block' : 'none';

  if (btnStats) btnStats.classList.toggle('active', tab === 'stats');
  if (btnMomentum) btnMomentum.classList.toggle('active', tab === 'momentum');
  if (btnEvents) btnEvents.classList.toggle('active', tab === 'events');
  if (btnLineup) btnLineup.classList.toggle('active', tab === 'lineup');

  if (tab === 'momentum') {
    loadMatchMomentum();
  } else if (tab === 'events') {
    loadMatchEvents();
  } else if (tab === 'lineup') {
    loadMatchLineup();
  }
};

// =========================================================
// 2. محرك غرفة المحللين الأذكياء (AI Pundit Studio - Pre / Live / Post-Match)
// =========================================================
window.currentStudioPhase = 'auto';

window.switchStudioPhase = function(phaseKey) {
  window.currentStudioPhase = phaseKey;
  loadMatchMomentum(phaseKey);
};

async function loadMatchMomentum(requestedPhase) {
  var container = document.getElementById('tm-momentum-content');
  var m = window.activeMatchModalData;
  if (!container || !m) return;

  var phaseToLoad = requestedPhase || 'auto';

  container.innerHTML =
    '<div class="loading-state" style="padding:32px 12px;">' +
      '<div style="font-size:1.6rem; margin-bottom:8px;">🎙️</div>' +
      '<div style="color:var(--accent-gold); font-weight:900; font-size:0.95rem;">جاري الاتصال بغرفة المحللين الأذكياء...</div>' +
      '<div style="color:var(--muted); font-size:0.78rem; margin-top:4px;">يتم الآن سحب أرقام المباراة الحقيقية والتشكيلات وتجهيز قراءة المحللين الأربعة</div>' +
    '</div>';

  try {
    var leagueCode = m.league_code || 'PL';
    var res = await fetch('/api/ai_studio/' + encodeURIComponent(leagueCode) + '/' + encodeURIComponent(m.id) + '?phase=' + encodeURIComponent(phaseToLoad));
    var resJson = await res.json();
    var studio = (resJson && resJson.data) ? resJson.data : null;

    if (!studio) {
      throw new Error('No studio data');
    }

    var actualState = studio.actual_state || m.state || 'pre';
    var activePhase = studio.phase || (actualState === 'post' ? 'post' : (actualState === 'in' ? 'in' : 'pre'));

    // تحديد المراحل المتاحة فعلياً حسب حالة المباراة الحقيقية
    var canViewIn = (actualState === 'in' || actualState === 'post');
    var canViewPost = (actualState === 'post');

    // شريط التبديل التراكمي بين مراحل الاستوديو الثلاث
    var phaseTabsHtml =
      '<div style="display:flex; gap:6px; background:#060a14; padding:6px; border-radius:14px; border:1px solid var(--card-border); margin-bottom:14px;">' +
        // 1. زر قبل المباراة (متاح دائماً في كل الحالات)
        '<button type="button" onclick="switchStudioPhase(\'pre\')" style="flex:1; padding:8px 6px; border-radius:10px; border:1px solid ' + (activePhase === 'pre' ? 'var(--accent-green)' : 'var(--card-border)') + '; background:' + (activePhase === 'pre' ? 'rgba(0,230,118,0.16)' : '#0c121e') + '; color:' + (activePhase === 'pre' ? 'var(--accent-green)' : '#cbd5e1') + '; font-weight:900; font-size:0.75rem; cursor:pointer; transition:all 0.2s;">' +
          '📋 قبل المباراة' +
        '</button>' +

        // 2. زر بين الشوطين (يتفعل فقط عند بدء المباراة أو انتهائها)
        (canViewIn
          ? '<button type="button" onclick="switchStudioPhase(\'in\')" style="flex:1; padding:8px 6px; border-radius:10px; border:1px solid ' + (activePhase === 'in' ? 'var(--accent-gold)' : 'var(--card-border)') + '; background:' + (activePhase === 'in' ? 'rgba(255,214,0,0.16)' : '#0c121e') + '; color:' + (activePhase === 'in' ? 'var(--accent-gold)' : '#cbd5e1') + '; font-weight:900; font-size:0.75rem; cursor:pointer; transition:all 0.2s;">' +
              '⏱️ بين الشوطين' +
            '</button>'
          : '<button type="button" disabled title="يتفعل بعد انطلاق المباراة" style="flex:1; padding:8px 6px; border-radius:10px; border:1px dashed #1e293b; background:rgba(15,23,42,0.4); color:#475569; font-weight:800; font-size:0.73rem; cursor:not-allowed; opacity:0.6;">' +
              '🔒 بين الشوطين' +
            '</button>'
        ) +

        // 3. زر بعد النهاية (يتفعل فقط بعد انتهاء المباراة رسمياً)
        (canViewPost
          ? '<button type="button" onclick="switchStudioPhase(\'post\')" style="flex:1; padding:8px 6px; border-radius:10px; border:1px solid ' + (activePhase === 'post' ? 'var(--accent-cyan)' : 'var(--card-border)') + '; background:' + (activePhase === 'post' ? 'rgba(0,210,255,0.16)' : '#0c121e') + '; color:' + (activePhase === 'post' ? 'var(--accent-cyan)' : '#cbd5e1') + '; font-weight:900; font-size:0.75rem; cursor:pointer; transition:all 0.2s;">' +
              '🏁 بعد النهاية' +
            '</button>'
          : '<button type="button" disabled title="يتفعل بعد صافرة النهاية" style="flex:1; padding:8px 6px; border-radius:10px; border:1px dashed #1e293b; background:rgba(15,23,42,0.4); color:#475569; font-weight:800; font-size:0.73rem; cursor:not-allowed; opacity:0.6;">' +
              '🔒 بعد النهاية' +
            '</button>'
        ) +
      '</div>';

    // حماية إضافية في حال طُلبت مرحلة غير متاحة
    if (!studio.has_studio) {
      container.innerHTML =
        phaseTabsHtml +
        '<div style="background:#0c121e; border:1px dashed var(--card-border); border-radius:14px; padding:26px 16px; text-align:center;">' +
          '<div style="font-size:1.8rem; margin-bottom:8px;">🔒</div>' +
          '<div style="color:var(--accent-gold); font-weight:900; font-size:0.9rem; line-height:1.7;">' + (studio.message || 'هذه المرحلة لم تبدأ بعد.') + '</div>' +
        '</div>';
      return;
    }
    // إذا طلب المستخدم مرحلة لم تبدأ بعد على أرض الواقع (مثلاً بعد النهاية والمباراة لم تلعب بعد)
    if (!studio.has_studio) {
      container.innerHTML =
        phaseTabsHtml +
        '<div style="background:#0c121e; border:1px dashed var(--accent-gold); border-radius:14px; padding:26px 16px; text-align:center;">' +
          '<div style="font-size:1.8rem; margin-bottom:8px;">⏳</div>' +
          '<div style="color:var(--accent-gold); font-weight:900; font-size:0.9rem; line-height:1.7;">' + (studio.message || 'هذه المرحلة ستتوفر فور انطلاق المباراة.') + '</div>' +
          '<button type="button" class="ai-btn" onclick="switchStudioPhase(\'pre\')" style="margin-top:12px;">📋 العودة لاستوديو ما قبل المباراة</button>' +
        '</div>';
      return;
    }

    // شريط البطاقات الرقمية والتوقعات (Summary Badges)
    var badgesHtml = '';
    if (Array.isArray(studio.summary_badges) && studio.summary_badges.length > 0) {
      badgesHtml =
        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(120px, 1fr)); gap:8px; margin-bottom:14px;">' +
          studio.summary_badges.map(function(b) {
            return '<div style="background:#080d1a; border:1px solid var(--card-border); border-radius:10px; padding:8px 10px; text-align:center;">' +
              '<div style="font-size:0.68rem; color:var(--muted); font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + b.pundit + '</div>' +
              '<div style="font-size:0.88rem; font-weight:900; color:var(--accent-gold); margin-top:3px; direction:ltr;">' + b.score + '</div>' +
            '</div>';
          }).join('') +
        '</div>';
    }

    // كروت المحللين الأربعة
    var punditsHtml = (studio.pundits || []).map(function(p) {
      var borderCol = p.color || 'var(--accent-cyan)';
      return '<div style="background:linear-gradient(145deg, #0e172a, #080d1a); border:1px solid var(--card-border); border-right:4px solid ' + borderCol + '; border-radius:14px; padding:12px 14px; margin-bottom:10px; box-shadow:0 4px 14px rgba(0,0,0,0.3);">' +
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">' +
          '<div style="display:flex; align-items:center; gap:8px;">' +
            '<span style="width:32px; height:32px; border-radius:50%; background:rgba(255,255,255,0.05); border:1px solid ' + borderCol + '; display:inline-flex; align-items:center; justify-content:center; font-size:1rem;">' + p.avatar + '</span>' +
            '<div>' +
              '<div style="font-weight:900; font-size:0.88rem; color:#fff;">' + p.name + '</div>' +
              '<div style="font-size:0.7rem; color:' + borderCol + '; font-weight:800;">' + p.role + '</div>' +
            '</div>' +
          '</div>' +
          '<span style="font-size:0.65rem; background:rgba(255,255,255,0.04); color:var(--muted); padding:2px 8px; border-radius:99px; border:1px solid var(--card-border);">بيانات موثقة ✅</span>' +
        '</div>' +
        '<div style="font-size:0.83rem; line-height:1.7; color:#e2e8f0; font-weight:600;">' +
          String(p.analysis || '').replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff;">$1</strong>') +
        '</div>' +
      '</div>';
    }).join('');

    // صندوق صدام الرأي والنقاش التكتيكي (Studio Debate)
    var debateHtml = '';
    if (studio.debate && studio.debate.topic) {
      debateHtml =
        '<div style="background:linear-gradient(135deg, rgba(255,214,0,0.08), #080d1a); border:1px solid rgba(255,214,0,0.35); border-radius:14px; padding:12px 14px; margin-bottom:14px;">' +
          '<div style="font-size:0.82rem; font-weight:900; color:var(--accent-gold); margin-bottom:5px; display:flex; align-items:center; gap:6px;">' +
            '<span>⚡</span> <span>طاولة النقاش وصدام الرأي: ' + studio.debate.topic + '</span>' +
          '</div>' +
          '<div style="font-size:0.8rem; line-height:1.65; color:#cbd5e1;">' + studio.debate.summary + '</div>' +
        '</div>';
    }

    // صندوق تفاعل المشاهد مع المحللين (اسأل محللاً في الاستوديو)
    var askStudioHtml =
      '<div style="background:#070c18; border:1px solid #1e2d4a; border-radius:14px; padding:12px 14px; margin-top:12px;">' +
        '<div style="font-size:0.82rem; font-weight:900; color:var(--accent-cyan); margin-bottom:8px;">🙋‍♂️ وجّه سؤالاً مباشراً لأحد محللي الاستوديو حول هذه المباراة:</div>' +
        '<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px;">' +
          '<select id="studio-ask-pundit-sel" style="background:#0f182c; color:#fff; border:1px solid #24385e; border-radius:10px; padding:7px 10px; font-size:0.78rem; font-weight:800; outline:none; flex:1; min-width:150px;">' +
            '<option value="tactician">🧠 د. طارق التكتيكي (الخطط والتكتيك)</option>' +
            '<option value="data_analyst">📊 م. سامر الرقمي (الأرقام والـ xG)</option>' +
            '<option value="momentum_star">🔥 كابتن رياض الحسم (الزخم والنجوم)</option>' +
            '<option value="moderator_ref">⚖️ المستشار جمال التحكيمي (التحكيم والانضباط)</option>' +
          '</select>' +
          '<input type="text" id="studio-ask-input" placeholder="اكتب سؤالك عن اللقاء..." style="background:#0f182c; color:#fff; border:1px solid #24385e; border-radius:10px; padding:7px 12px; font-size:0.8rem; flex:2; min-width:180px; outline:none;">' +
          '<button type="button" id="studio-ask-btn" class="ai-btn" onclick="submitStudioPunditQuestion()" style="padding:7px 16px; font-size:0.78rem;">إرسال 🎙️</button>' +
        '</div>' +
        '<div id="studio-ask-reply-box" style="display:none; background:#0b1324; border-right:3px solid var(--accent-green); border-radius:10px; padding:10px 12px; font-size:0.82rem; line-height:1.65; color:#e2e8f0; margin-top:8px;"></div>' +
      '</div>';

    container.innerHTML =
      phaseTabsHtml +
      '<div style="background:linear-gradient(90deg, rgba(0,230,118,0.12), rgba(0,210,255,0.08)); border:1px solid rgba(0,230,118,0.3); border-radius:12px; padding:10px 14px; margin-bottom:12px;">' +
        '<div style="font-size:0.9rem; font-weight:900; color:#fff;">🎙️ ' + studio.headline + '</div>' +
        '<div style="font-size:0.76rem; color:var(--accent-gold); font-weight:800; margin-top:4px;">🎯 ' + studio.key_battle + '</div>' +
      '</div>' +
      badgesHtml +
      punditsHtml +
      debateHtml +
      askStudioHtml;

  } catch (err) {
    container.innerHTML = '<div class="loading-state" style="color:var(--accent-red); padding:25px 0;">تعذر الاتصال بغرفة المحللين حالياً، يرجى المحاولة مرة أخرى.</div>';
  }
}

window.submitStudioPunditQuestion = async function() {
  var m = window.activeMatchModalData;
  var sel = document.getElementById('studio-ask-pundit-sel');
  var inp = document.getElementById('studio-ask-input');
  var btn = document.getElementById('studio-ask-btn');
  var replyBox = document.getElementById('studio-ask-reply-box');
  if (!m || !sel || !inp || !btn || !replyBox) return;

  var qText = (inp.value || '').trim();
  if (!qText) {
    inp.focus();
    return;
  }

  btn.disabled = true;
  btn.innerText = 'جاري الرد... ⏳';
  replyBox.style.display = 'block';
  replyBox.innerHTML = '<span style="color:var(--muted);">🎙️ يقوم المحلل بقراءة أرقام المباراة وصياغة الرد...</span>';

  try {
    var res = await fetch('/api/ai_studio_ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        league_code: m.league_code || 'PL',
        match_id: String(m.id),
        pundit_id: sel.value,
        question: qText
      })
    });
    var json = await res.json();
    if (json && json.status === 'success' && json.data) {
      replyBox.innerHTML =
        '<div style="font-weight:900; color:var(--accent-green); margin-bottom:4px;">🎙️ ' + json.data.pundit_name + ' (' + json.data.pundit_role + '):</div>' +
        '<div>' + String(json.data.reply || '').replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff;">$1</strong>') + '</div>';
    } else {
      throw new Error('Fallback');
    }
  } catch (e) {
    replyBox.innerHTML = '<span style="color:var(--accent-red);">تعذر الحصول على رد المحلل في هذه اللحظة.</span>';
  } finally {
    btn.disabled = false;
    btn.innerText = 'إرسال 🎙️';
  }
};
// =========================================================
// 3. محرك التشكيلات الرسمية وتقييمات الأداء الحقيقية
// =========================================================
function computeRealStatRatingJS(athId, pName, posAbbr, statsList, isStarter, subbedIn, isHomeTeam, ctx) {
  if (!ctx.isLiveOrPost) return { rating: null, hasGoal: false };
  if (!isStarter && !subbedIn) return { rating: null, hasGoal: false };

  var pStats = {};
  if (Array.isArray(statsList)) {
    statsList.forEach(function(st) {
      if (st && st.name) {
        var v = (st.value !== undefined && st.value !== null) ? st.value : st.displayValue;
        var num = parseFloat(String(v || '0').replace('%', '').trim());
        pStats[st.name.toLowerCase()] = isNaN(num) ? 0 : num;
      }
    });
  }

  var goals = Math.round(pStats['totalgoals'] || pStats['goals'] || 0) || ctx.goalCounts[athId] || ctx.goalCounts[pName] || 0;
  var assists = Math.round(pStats['goalassists'] || pStats['assists'] || 0) || ctx.assistCounts[athId] || ctx.assistCounts[pName] || 0;
  var shots = Math.round(pStats['totalshots'] || pStats['shots'] || 0);
  var sot = Math.round(pStats['shotsontarget'] || pStats['shotsongoal'] || 0);
  var saves = Math.round(pStats['saves'] || 0);
  var foulsCom = Math.round(pStats['foulscommitted'] || 0);
  var foulsSuf = Math.round(pStats['foulssuffered'] || 0);
  var offsides = Math.round(pStats['offsides'] || 0);

  var yc = Math.round(pStats['yellowcards'] || 0) || ((ctx.ycSet[athId] || ctx.ycSet[pName]) ? 1 : 0);
  var rc = Math.round(pStats['redcards'] || 0) || ((ctx.rcSet[athId] || ctx.rcSet[pName]) ? 1 : 0);

  var teamG = isHomeTeam ? ctx.hScore : ctx.aScore;
  var oppG = isHomeTeam ? ctx.aScore : ctx.hScore;

  var rating = 6.5;
  if (teamG > oppG) rating += 0.2 + Math.min(0.3, (teamG - oppG) * 0.1);
  else if (teamG < oppG) rating -= 0.15;

  var isGk = posAbbr.indexOf('G') === 0;
  var isDef = posAbbr.indexOf('D') === 0 || ['CB', 'CD', 'LB', 'RB', 'LWB', 'RWB', 'CD-L', 'CD-R'].indexOf(posAbbr) !== -1;

  if (oppG === 0) {
    if (isGk) rating += 0.5;
    else if (isDef) rating += 0.4;
    else rating += 0.1;
  } else if (oppG >= 2 && (isGk || isDef)) {
    rating -= Math.min(0.8, (oppG - 1) * 0.2);
  }

  rating += (goals * 1.15) + (assists * 0.75) + (sot * 0.25) + (Math.max(0, shots - sot) * 0.08) + (saves * 0.25) + Math.min(0.3, foulsSuf * 0.1);
  rating -= Math.max(0, (foulsCom - 1) * 0.1) + (offsides * 0.1) + (yc * 0.4) + (rc * 1.6);

  if (!isStarter && subbedIn && goals === 0 && assists === 0) {
    rating = Math.min(rating, 6.9);
  }

  var finalRating = Math.round(Math.min(9.9, Math.max(4.2, rating)) * 10) / 10;
  return { rating: finalRating, hasGoal: goals > 0 };
}

function parseEspnRosterObjectJS(rObj, fallbackName, isHomeTeam, ctx, calcRatings) {
  var tInfo = rObj.team || {};
  var tName = tInfo.shortDisplayName || tInfo.displayName || fallbackName;
  var form = rObj.formation || '4-3-3';
  var rawList = rObj.roster || [];
  var starters = [], subs = [];

  rawList.forEach(function(p) {
    if (!p || typeof p !== 'object') return;
    var ath = p.athlete || {};
    var athId = String(ath.id || p.id || '');
    var pName = ath.shortName || ath.displayName || p.displayName || '';
    if (!pName) return;

    var jVal = p.jersey || ath.jersey;
    var num = (jVal !== undefined && jVal !== null && String(jVal).trim() !== '') ? String(jVal).trim() : '-';

    var posObj = p.position || ath.position || {};
    var posAbbr = (posObj && posObj.abbreviation) ? String(posObj.abbreviation).toUpperCase() : 'M';

    var formPlace = parseInt(p.formationPlace, 10);
    if (isNaN(formPlace)) formPlace = 0;

    var isStarter = (p.starter === true) || (formPlace >= 1 && formPlace <= 11);
    var subbedIn = (p.subbedIn && typeof p.subbedIn === 'object') ? Boolean(p.subbedIn.didSub) : Boolean(p.subbedIn);

    var rRes = calcRatings
      ? computeRealStatRatingJS(athId, pName, posAbbr, p.stats, isStarter, subbedIn, isHomeTeam, ctx)
      : { rating: null, hasGoal: false };

    var item = {
      name: pName,
      number: num,
      pos: posAbbr,
      formation_place: formPlace > 0 ? formPlace : 99,
      rating: rRes.rating,
      has_goal: rRes.hasGoal,
      subbed_in: subbedIn
    };

    if (isStarter && starters.length < 11) starters.push(item);
    else subs.push(item);
  });

  while (starters.length < 11 && subs.length > 0) starters.push(subs.shift());
  starters.sort(function(a, b) { return (a.formation_place || 99) - (b.formation_place || 99); });

  return { team_name: tName, formation: form, starters: starters, subs: subs.slice(0, 9) };
}

async function fetchLineupDirectlyFromESPN(m) {
  var espnCode = ESPN_LEAGUE_MAP[m.league_code] || 'eng.1';
  var hTeamId = m.home_id || '';
  var aTeamId = m.away_id || '';
  var isLiveOrPost = (m.state === 'in' || m.state === 'post' || Boolean(m.is_live));

  var hScore = parseInt(m.home_score, 10); if (isNaN(hScore)) hScore = 0;
  var aScore = parseInt(m.away_score, 10); if (isNaN(aScore)) aScore = 0;

  var summaryData = null;
  var urls = [
    'https://site.api.espn.com/apis/site/v2/sports/soccer/' + espnCode + '/summary?event=' + m.id,
    'https://site.web.api.espn.com/apis/site/v2/sports/soccer/' + espnCode + '/summary?event=' + m.id,
    'https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event=' + m.id
  ];

  for (var i = 0; i < urls.length; i++) {
    try {
      var res = await fetch(urls[i]);
      if (res.ok) {
        var json = await res.json();
        if (json && typeof json === 'object') {
          summaryData = json;
          if (Array.isArray(json.rosters) && json.rosters.length >= 2 && json.rosters[0].roster && json.rosters[0].roster.length > 0) break;
        }
      }
    } catch (e) {}
  }

  var goalCounts = {}, assistCounts = {}, ycSet = {}, rcSet = {};

  if (summaryData) {
    var comp = (summaryData.header && summaryData.header.competitions && summaryData.header.competitions[0]) ||
               (summaryData.competitions && summaryData.competitions[0]) || null;

    if (comp) {
      var stState = comp.status && comp.status.type && comp.status.type.state;
      if (stState === 'in' || stState === 'post') isLiveOrPost = true;

      (comp.competitors || []).forEach(function(c) {
        var tid = (c.team && c.team.id) || c.id || '';
        if (c.homeAway === 'home') {
          if (!hTeamId) hTeamId = String(tid);
          var hs = parseInt(c.score, 10); if (!isNaN(hs)) hScore = hs;
        } else if (c.homeAway === 'away') {
          if (!aTeamId) aTeamId = String(tid);
          var as = parseInt(c.score, 10); if (!isNaN(as)) aScore = as;
        }
      });
    }

    var rostersArr = summaryData.rosters || [];
    rostersArr.forEach(function(r) {
      if (r.homeAway === 'home' && r.team && r.team.id && !hTeamId) hTeamId = String(r.team.id);
      if (r.homeAway === 'away' && r.team && r.team.id && !aTeamId) aTeamId = String(r.team.id);
    });

    var allEvents = [];
    if (comp && Array.isArray(comp.details)) allEvents = allEvents.concat(comp.details);
    ['details', 'scoringPlays', 'keyEvents'].forEach(function(k) {
      if (Array.isArray(summaryData[k])) allEvents = allEvents.concat(summaryData[k]);
    });

    allEvents.forEach(function(ev) {
      if (!ev || typeof ev !== 'object') return;
      var tObj = ev.type || {};
      var tTxt = String(tObj.text || tObj.name || tObj || '').toLowerCase();
      var inv = ev.athletesInvolved || ev.participants || [];

      if (tTxt.indexOf('yellow') !== -1 && inv[0]) {
        var athY = inv[0].athlete || inv[0];
        [athY.id, athY.displayName, athY.shortName].forEach(function(k) { if (k) ycSet[String(k)] = true; });
      } else if (tTxt.indexOf('red') !== -1 && inv[0]) {
        var athR = inv[0].athlete || inv[0];
        [athR.id, athR.displayName, athR.shortName].forEach(function(k) { if (k) rcSet[String(k)] = true; });
      } else if ((ev.scoringPlay === true || tTxt.indexOf('goal') !== -1) &&
                 tTxt.indexOf('missed') === -1 && tTxt.indexOf('saved') === -1 && tTxt.indexOf('disallowed') === -1) {
        if (inv[0]) {
          var ath0 = inv[0].athlete || inv[0];
          [ath0.id, ath0.displayName, ath0.shortName].forEach(function(k) { if (k) goalCounts[String(k)] = (goalCounts[String(k)] || 0) + 1; });
        }
        if (inv[1]) {
          var ath1 = inv[1].athlete || inv[1];
          [ath1.id, ath1.displayName, ath1.shortName].forEach(function(k) { if (k) assistCounts[String(k)] = (assistCounts[String(k)] || 0) + 1; });
        }
      }
    });

    var ctx = { isLiveOrPost: isLiveOrPost, hScore: hScore, aScore: aScore, goalCounts: goalCounts, assistCounts: assistCounts, ycSet: ycSet, rcSet: rcSet };

    if (rostersArr.length >= 2) {
      var t0Home = rostersArr[0].homeAway === 'home';
      var hRos = t0Home ? rostersArr[0] : rostersArr[1];
      var aRos = t0Home ? rostersArr[1] : rostersArr[0];

      var parsedH = parseEspnRosterObjectJS(hRos, m.home_team, true, ctx, isLiveOrPost);
      var parsedA = parseEspnRosterObjectJS(aRos, m.away_team, false, ctx, isLiveOrPost);

      if (parsedH.starters.length >= 11 && parsedA.starters.length >= 11) {
        return { has_lineups: true, is_official: true, show_ratings: isLiveOrPost, home: parsedH, away: parsedA };
      }
    }
  }

  async function fetchTeamLastRealLineup(tid, teamName, isHomeTeam) {
    if (!tid) return null;
    var schedUrls = [
      'https://site.api.espn.com/apis/site/v2/sports/soccer/' + espnCode + '/teams/' + tid + '/schedule',
      'https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/' + tid + '/schedule'
    ];
    var pastEventIds = [];
    for (var s = 0; s < schedUrls.length; s++) {
      try {
        var sRes = await fetch(schedUrls[s]);
        if (sRes.ok) {
          var sData = await sRes.json();
          var evs = (sData && sData.events) || [];
          var completed = [];
          evs.forEach(function(ev) {
            if (!ev || !ev.id || String(ev.id) === String(m.id)) return;
            var st = ev.competitions && ev.competitions[0] && ev.competitions[0].status && ev.competitions[0].status.type && ev.competitions[0].status.type.state;
            if (st === 'post') completed.push({ date: ev.date || '', id: String(ev.id) });
          });
          completed.sort(function(a, b) { return b.date.localeCompare(a.date); });
          pastEventIds = completed.slice(0, 3).map(function(x) { return x.id; });
          if (pastEventIds.length > 0) break;
        }
      } catch (e) {}
    }

    var dummyCtx = { isLiveOrPost: false, hScore: 0, aScore: 0, goalCounts: {}, assistCounts: {}, ycSet: {}, rcSet: {} };
    for (var p = 0; p < pastEventIds.length; p++) {
      try {
        var peRes = await fetch('https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event=' + pastEventIds[p]);
        if (peRes.ok) {
          var peData = await peRes.json();
          var peRosters = (peData && peData.rosters) || [];
          for (var r = 0; r < peRosters.length; r++) {
            var rObj = peRosters[r];
            var rTid = rObj.team && rObj.team.id ? String(rObj.team.id) : '';
            if (rTid === String(tid) && rObj.roster && rObj.roster.length >= 11) {
              var parsed = parseEspnRosterObjectJS(rObj, teamName, isHomeTeam, dummyCtx, false);
              if (parsed.starters.length >= 11) return parsed;
            }
          }
        }
      } catch (e) {}
    }
    return null;
  }

  var pair = await Promise.all([
    fetchTeamLastRealLineup(hTeamId, m.home_team, true),
    fetchTeamLastRealLineup(aTeamId, m.away_team, false)
  ]);

  if (pair[0] && pair[1]) {
    return { has_lineups: true, is_official: false, show_ratings: false, home: pair[0], away: pair[1] };
  }
  return null;
}

async function loadMatchLineup() {
  var container = document.getElementById('tm-lineup-content');
  var m = window.activeMatchModalData;
  if (!container || !m) return;

  container.innerHTML = '<div class="loading-state" style="padding:30px 0;">جاري جلب التشكيلة وأرقام اللاعبين من المصدر...</div>';

  var data = null;
  if (window.activeMatchStatsData && window.activeMatchStatsData.lineups && window.activeMatchStatsData.lineups.has_lineups) {
    data = window.activeMatchStatsData.lineups;
  }

  if (!data || !data.has_lineups) {
    try {
      var res = await fetch('/api/match_lineups/' + (m.league_code || 'PL') + '/' + m.id);
      if (res.ok) {
        var srvData = await res.json();
        if (srvData && srvData.has_lineups) data = srvData;
      }
    } catch (e) {}
  }

  if (!data || !data.has_lineups) {
    try {
      var directData = await fetchLineupDirectlyFromESPN(m);
      if (directData && directData.has_lineups) data = directData;
    } catch (e) {}
  }

  if (!data || !data.has_lineups) {
    container.innerHTML = '<div style="background:#0c121e; border:1px dashed var(--card-border); border-radius:12px; padding:25px 15px; text-align:center; color:var(--accent-gold); font-size:0.85rem;">' +
      '⏳ لم تُعلن التشكيلة الرسمية للمباراة من المصدر حتى هذه اللحظة.' +
    '</div>';
    return;
  }

  var showRatings = Boolean(data.show_ratings);
  var isOfficial = data.is_official !== false;

  var splitPlayersByFormation = function(starters, formationStr) {
    var list = (starters || []).slice(0, 11);
    if (list.length === 0) return [];

    var gk = [], outfield = [];
    list.forEach(function(p) {
      var pos = String(p.pos || '').toUpperCase();
      if ((pos.indexOf('G') === 0 || p.formation_place === 1) && gk.length === 0) gk.push(p);
      else outfield.push(p);
    });
    if (gk.length === 0 && outfield.length > 0) gk.push(outfield.shift());

    var roleWeight = function(p) {
      var pos = String(p.pos || '').toUpperCase();
      if (pos.indexOf('D') === 0 || ['CB', 'CD', 'LB', 'RB', 'LWB', 'RWB', 'CD-L', 'CD-R'].indexOf(pos) !== -1) return 1;
      if (['DM', 'CDM', 'LDM', 'RDM'].indexOf(pos) !== -1) return 2;
      if (pos.indexOf('M') === 0 || ['CM', 'CM-L', 'CM-R'].indexOf(pos) !== -1) return 3;
      if (['AM', 'CAM', 'LM', 'RM', 'LAM', 'RAM'].indexOf(pos) !== -1) return 4;
      if (['LW', 'RW', 'LF', 'RF'].indexOf(pos) !== -1) return 5;
      if (pos.indexOf('F') === 0 || ['ST', 'CF'].indexOf(pos) !== -1) return 6;
      return 3;
    };

    outfield.sort(function(a, b) {
      var wDiff = roleWeight(a) - roleWeight(b);
      return wDiff !== 0 ? wDiff : ((a.formation_place || 99) - (b.formation_place || 99));
    });

    var formParts = String(formationStr || '4-3-3').split('-').map(function(n) { return parseInt(n, 10); }).filter(function(n) { return !isNaN(n) && n > 0; });
    var sumParts = formParts.reduce(function(a, b) { return a + b; }, 0);
    if (sumParts !== outfield.length) formParts = [4, 3, 3];

    var rows = [gk];
    var cursor = 0;
    formParts.forEach(function(count) {
      var slice = outfield.slice(cursor, cursor + count);
      if (slice.length > 0) rows.push(slice);
      cursor += count;
    });
    if (cursor < outfield.length) rows.push(outfield.slice(cursor));
    return rows;
  };

  var renderTeamPitch = function(teamObj, isHome) {
    var starters = teamObj.starters || [];
    var subs = teamObj.subs || [];
    var rows = splitPlayersByFormation(starters, teamObj.formation);

    var renderRow = function(playersRow) {
      if (!playersRow || playersRow.length === 0) return '';
      return '<div style="display:flex; justify-content:space-around; align-items:flex-start; margin:12px 0; direction:ltr;">' +
        playersRow.map(function(p) {
          var ratingHtml = '';
          if (showRatings && p.rating !== null && p.rating !== undefined) {
            var rNum = parseFloat(p.rating);
            var rBg = rNum >= 7.3 ? '#00e676' : (rNum >= 6.4 ? '#ffd600' : '#ff5252');
            var rTxtCol = rNum < 6.4 ? '#fff' : '#000';
            ratingHtml =
              '<div style="background:' + rBg + '; color:' + rTxtCol + '; font-weight:900; font-size:0.68rem; padding:1px 7px; border-radius:6px; margin-bottom:3px; z-index:2; box-shadow:0 2px 5px rgba(0,0,0,0.6);">' +
                rNum.toFixed(1) +
              '</div>';
          }

          var goalBadge = p.has_goal ? '<span style="position:absolute; top:-5px; right:-6px; font-size:0.75rem;">⚽</span>' : '';
          var circleBg = isHome ? '#1e293b' : '#0f172a';
          var borderCol = isHome ? 'var(--accent-green)' : 'var(--accent-cyan)';

          return '<div style="display:flex; flex-direction:column; align-items:center; width:82px; position:relative;">' +
            ratingHtml +
            '<div style="width:34px; height:34px; border-radius:50%; background:' + circleBg + '; border:2px solid ' + borderCol + '; display:flex; align-items:center; justify-content:center; font-weight:900; font-size:0.78rem; color:#fff; position:relative; margin-bottom:4px; box-shadow:0 3px 8px rgba(0,0,0,0.45);">' +
              p.number + goalBadge +
            '</div>' +
            '<div dir="ltr" style="font-size:0.72rem; font-weight:800; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:80px; background:rgba(8,12,21,0.9); border:1px solid rgba(255,255,255,0.14); border-radius:5px; padding:2px 6px; text-align:center;">' +
              p.name +
            '</div>' +
          '</div>';
        }).join('') +
      '</div>';
    };

    var html = '<div style="margin-bottom:16px; background:linear-gradient(180deg, #0d2818 0%, #134226 50%, #0d2818 100%); border:2px solid #1e4d30; border-radius:14px; padding:12px; position:relative;">';
    html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:6px;">' +
              '<span style="font-weight:900; font-size:0.92rem; color:#fff;">🛡️ ' + teamObj.team_name + '</span>' +
              '<span style="background:rgba(0,0,0,0.5); color:var(--accent-gold); padding:2px 10px; border-radius:10px; font-size:0.75rem; font-weight:800;">الخطة: ' + (teamObj.formation || '4-3-3') + '</span>' +
            '</div>';

    rows.forEach(function(r) { html += renderRow(r); });

    if (subs.length > 0) {
      html += '<div style="margin-top:10px; background:rgba(9, 14, 24, 0.88); border-radius:8px; padding:8px;">' +
                '<div style="font-size:0.72rem; color:var(--muted); font-weight:800; margin-bottom:6px;">🔄 دكة البدلاء:</div>' +
                '<div style="display:flex; flex-wrap:wrap; gap:6px; direction:ltr;">' +
                subs.map(function(s) {
                  var rBadge = (showRatings && s.rating) ? '<span style="background:rgba(0,230,118,0.2); color:var(--accent-green); font-weight:900; padding:0 4px; border-radius:4px; margin-left:4px;">' + Number(s.rating).toFixed(1) + '</span>' : '';
                  return '<span style="background:#131c2e; border:1px solid var(--card-border); padding:3px 7px; border-radius:6px; font-size:0.7rem; display:inline-flex; align-items:center; color:#e2e8f0;">' +
                    '<strong style="color:var(--accent-gold); margin-right:4px;">#' + s.number + '</strong> ' + s.name + rBadge +
                  '</span>';
                }).join('') +
                '</div></div>';
    }

    html += '</div>';
    return html;
  };

  var headerBanner = showRatings
    ? '<div style="text-align:center; font-size:0.78rem; font-weight:800; color:var(--accent-green); background:rgba(0,230,118,0.1); border:1px solid rgba(0,230,118,0.3); padding:6px; border-radius:8px; margin-bottom:12px;">⭐ التشكيلة الرسمية وتقييمات الأداء الحقيقية (محسوبة من إحصائيات اللقاء)</div>'
    : (isOfficial
      ? '<div style="text-align:center; font-size:0.78rem; font-weight:800; color:var(--accent-green); background:rgba(0,230,118,0.1); border:1px solid rgba(0,230,118,0.3); padding:6px; border-radius:8px; margin-bottom:12px;">✅ التشكيلة الرسمية المعتمدة للمباراة</div>'
      : '<div style="text-align:center; font-size:0.78rem; font-weight:800; color:var(--accent-gold); background:rgba(255,214,0,0.1); border:1px solid rgba(255,214,0,0.3); padding:6px; border-radius:8px; margin-bottom:12px;">📋 التشكيلة المتوقعة (بناءً على آخر مباراة رسمية للفريقين)</div>');

  container.innerHTML = headerBanner + renderTeamPitch(data.home, true) + renderTeamPitch(data.away, false);
}

// =========================================================
// 4. إحصائيات مباراة اليوم والنافذة المنبثقة
// =========================================================
function buildFallbackStatsFromMatch(m) {
  return {
    has_stats: false,
    state: m ? (m.state || 'pre') : 'pre',
    home: { possession: 0, pass_accuracy: 0, shots: 0, shots_on_target: 0, corners: 0, offsides: 0, fouls: 0, yellow_cards: 0, red_cards: 0 },
    away: { possession: 0, pass_accuracy: 0, shots: 0, shots_on_target: 0, corners: 0, offsides: 0, fouls: 0, yellow_cards: 0, red_cards: 0 },
    home_goals: [],
    away_goals: []
  };
}

function togglePreMatchStatsNotice(isPreMatch, kickoffTime) {
  var statsCard = document.getElementById('tm-stats-card');
  var goalsBox = document.getElementById('tm-goals-box');
  var statsWrapper = document.getElementById('tm-stats-wrapper');
  if (!statsWrapper) return;

  var preBox = document.getElementById('tm-prematch-stats-notice');
  if (!preBox) {
    preBox = document.createElement('div');
    preBox.id = 'tm-prematch-stats-notice';
    statsWrapper.insertBefore(preBox, statsWrapper.firstChild);
  }

  if (isPreMatch) {
    if (statsCard) statsCard.style.display = 'none';
    if (goalsBox) goalsBox.style.display = 'none';
    preBox.style.display = 'block';
    preBox.innerHTML =
      '<div style="background:#0c121e; border:1px dashed var(--card-border); border-radius:14px; padding:30px 16px; text-align:center; margin-bottom:10px;">' +
        '<div style="font-size:2rem; margin-bottom:8px;">⏳</div>' +
        '<div style="color:var(--accent-gold); font-weight:900; font-size:0.95rem; margin-bottom:6px;">لم تبدأ المباراة بعد</div>' +
        '<div style="color:var(--muted); font-size:0.82rem; line-height:1.6;">' +
          'موعد انطلاق اللقاء الساعة <strong style="color:#fff;">' + (kickoffTime || '--:--') + '</strong>.<br>' +
          'ستظهر الإحصائيات الحية (الاستحواذ، التسديدات، الركنيات، والبطاقات) تلقائياً فور انطلاق صافرة البداية.<br>' +
          '<span style="color:var(--accent-cyan); font-weight:800;">💡 يمكنك استعراض التشكيلة من التبويب بالأعلى.</span>' +
        '</div>' +
      '</div>';
  } else {
    preBox.style.display = 'none';
    if (statsCard) statsCard.style.display = 'block';
  }
}

function renderStatsIntoModal(statsObj, fallbackObj) {
  var rawH = (statsObj && statsObj.home) ? statsObj.home : {};
  var rawA = (statsObj && statsObj.away) ? statsObj.away : {};
  var fbH = (fallbackObj && fallbackObj.home) ? fallbackObj.home : {};
  var fbA = (fallbackObj && fallbackObj.away) ? fallbackObj.away : {};

  var hasData = Boolean(
    (statsObj && statsObj.has_stats) ||
    Number(rawH.shots) > 0 || Number(rawA.shots) > 0 ||
    Number(rawH.corners) > 0 || Number(rawA.corners) > 0 ||
    Number(rawH.possession) > 0 || Number(rawA.possession) > 0 ||
    Number(rawH.fouls) > 0 || Number(rawA.fouls) > 0
  );

  var h = hasData ? rawH : fbH;
  var a = hasData ? rawA : fbA;

  var goalsBox = document.getElementById('tm-goals-box');
  var hGoals = (statsObj && Array.isArray(statsObj.home_goals)) ? statsObj.home_goals : (fallbackObj.home_goals || []);
  var aGoals = (statsObj && Array.isArray(statsObj.away_goals)) ? statsObj.away_goals : (fallbackObj.away_goals || []);

  if (goalsBox) {
    goalsBox.style.display = 'block';
    if (hGoals.length > 0 || aGoals.length > 0) {
      safeHtml('tm-home-goals', hGoals.length > 0 ? hGoals.map(function(g) { return '<div style="margin-bottom:3px; font-weight:700;">⚽ ' + g + '</div>'; }).join('') : '<span style="color:var(--muted);">-</span>');
      safeHtml('tm-away-goals', aGoals.length > 0 ? aGoals.map(function(g) { return '<div style="margin-bottom:3px; font-weight:700;">' + g + ' ⚽</div>'; }).join('') : '<span style="color:var(--muted);">-</span>');
    } else {
      safeHtml('tm-home-goals', '<span style="color:var(--muted); font-size:0.78rem;">بدون أهداف</span>');
      safeHtml('tm-away-goals', '<span style="color:var(--muted); font-size:0.78rem;">بدون أهداف</span>');
    }
  }

  var calcBar = function(v1, v2) {
    var s = (Number(v1) || 0) + (Number(v2) || 0);
    if (s <= 0) return [50, 50];
    var p1 = Math.round((Number(v1) / s) * 100);
    return [p1, 100 - p1];
  };

  var posH = (h.possession !== undefined && h.possession !== null && Number(h.possession) > 0) ? Number(h.possession) : 50;
  var posA = (a.possession !== undefined && a.possession !== null && Number(a.possession) > 0) ? Number(a.possession) : (100 - posH);

  safeText('tm-stat-pos-h', posH + '%');
  safeText('tm-stat-pos-a', posA + '%');
  safeWidth('tm-bar-pos-h', posH);
  safeWidth('tm-bar-pos-a', posA);

  var passH = Number(h.pass_accuracy) || 0;
  var passA = Number(a.pass_accuracy) || 0;
  safeText('tm-stat-pass-h', passH > 0 ? (passH + '%') : '0%');
  safeText('tm-stat-pass-a', passA > 0 ? (passA + '%') : '0%');
  var pBars = calcBar(passH, passA);
  safeWidth('tm-bar-pass-h', pBars[0]);
  safeWidth('tm-bar-pass-a', pBars[1]);

  safeText('tm-stat-shots-h', h.shots || 0);
  safeText('tm-stat-shots-a', a.shots || 0);
  var sBars = calcBar(h.shots, a.shots);
  safeWidth('tm-bar-shots-h', sBars[0]);
  safeWidth('tm-bar-shots-a', sBars[1]);

  safeText('tm-stat-sot-h', h.shots_on_target || 0);
  safeText('tm-stat-sot-a', a.shots_on_target || 0);
  var sotBars = calcBar(h.shots_on_target, a.shots_on_target);
  safeWidth('tm-bar-sot-h', sotBars[0]);
  safeWidth('tm-bar-sot-a', sotBars[1]);

  safeText('tm-stat-corn-h', h.corners || 0);
  safeText('tm-stat-corn-a', a.corners || 0);
  var cBars = calcBar(h.corners, a.corners);
  safeWidth('tm-bar-corn-h', cBars[0]);
  safeWidth('tm-bar-corn-a', cBars[1]);

  safeText('tm-stat-off-h', h.offsides || 0);
  safeText('tm-stat-off-a', a.offsides || 0);
  var oBars = calcBar(h.offsides, a.offsides);
  safeWidth('tm-bar-off-h', oBars[0]);
  safeWidth('tm-bar-off-a', oBars[1]);

  safeText('tm-stat-fouls-h', h.fouls || 0);
  safeText('tm-stat-fouls-a', a.fouls || 0);
  var fBars = calcBar(h.fouls, a.fouls);
  safeWidth('tm-bar-fouls-h', fBars[0]);
  safeWidth('tm-bar-fouls-a', fBars[1]);

  safeText('tm-stat-yc-h', (h.yellow_cards || 0) + ' 🟨');
  safeText('tm-stat-rc-h', (h.red_cards || 0) + ' 🟥');
  safeText('tm-stat-yc-a', '🟨 ' + (a.yellow_cards || 0));
  safeText('tm-stat-rc-a', '🟥 ' + (a.red_cards || 0));
  var cardBars = calcBar((h.yellow_cards || 0) + (h.red_cards || 0) * 2, (a.yellow_cards || 0) + (a.red_cards || 0) * 2);
  safeWidth('tm-bar-cards-h', cardBars[0]);
  safeWidth('tm-bar-cards-a', cardBars[1]);
}

window.openTodayMatchModal = async function(idx) {
  try {
    var matches = window.currentTodayMatches || [];
    var m = matches[idx];
    if (!m) return;

    window.activeMatchModalData = m;
    window.activeMatchStatsData = null;
    window.switchMatchTab('stats');

    var modal = document.getElementById('today-match-modal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    safeText('tm-league-badge', (m.league_flag || '⚽') + ' ' + m.league_name);
    safeText('tm-status-text', m.status_text + ' • 🕒 ' + m.kickoff_time);
    safeSrc('tm-home-crest', m.home_crest);
    safeText('tm-home-name', m.home_team);
    safeSrc('tm-away-crest', m.away_crest);
    safeText('tm-away-name', m.away_team);
    safeText('tm-score', m.state === 'pre' ? 'VS' : (m.home_score + ' - ' + m.away_score));
    safeText('tm-venue', '🏟️ ' + m.venue);
    safeText('tm-info-channel', m.channel);
    safeText('tm-info-comm', m.commentator);

    var fallbackStats = buildFallbackStatsFromMatch(m);
    if (m.state === 'pre' && !m.is_live) {
      togglePreMatchStatsNotice(true, m.kickoff_time);
      return;
    }

    togglePreMatchStatsNotice(false, m.kickoff_time);
    renderStatsIntoModal(m.stats || fallbackStats, fallbackStats);

    var res = await fetch('/api/match_stats/' + (m.league_code || 'PL') + '/' + m.id);
    if (res.ok) {
      var json = await res.json();
      var statsPayload = (json && json.data) ? json.data : json;
      if (statsPayload && statsPayload.state === 'pre' && !m.is_live) {
        togglePreMatchStatsNotice(true, m.kickoff_time);
        return;
      }
      if (statsPayload && (statsPayload.has_stats || statsPayload.home)) {
        window.activeMatchStatsData = statsPayload;
        renderStatsIntoModal(statsPayload, fallbackStats);
      }
    }
  } catch (err) {
    console.warn("تم الاعتماد على الإحصائيات المدمجة:", err);
  }
};

// =========================================================
// 5. كارت الرادار ومختبر السيناريوهات التكتيكي (Dixon-Coles Sandbox)
// =========================================================
window.openModal = function(idx) {
  try {
    var fixtures = window.currentFixtures || [];
    var f = fixtures[idx];
    if (!f) return;

    currentModalFixture = f;
    var modal = document.getElementById('tactical-modal');
    if (!modal) return;

    safeText('m-title', (f.home.name || f.home.short) + ' VS ' + (f.away.name || f.away.short));
    safeText('m-time', 'الجولة ' + f.gameweek + ' • 🕒 ' + f.kickoff_time);

    var rBadge = document.getElementById('m-radar-badge');
    if (rBadge) {
      rBadge.innerText = f.edge.label || 'تحليل المباراة';
      rBadge.style.color = f.edge.color || 'var(--accent-green)';
    }
    safeText('m-radar-text', f.edge.reason || 'تحليل تكتيكي معتمد على تقييمات إيلو ونموذج ديكسون-كولز.');

    var h2h = f.h2h || {};
    safeText('h2h-lbl-h', 'فوز ' + f.home.short + ': ' + (h2h.home_wins || 0));
    safeText('h2h-lbl-d', 'تعادل: ' + (h2h.draws || 0));
    safeText('h2h-lbl-a', 'فوز ' + f.away.short + ': ' + (h2h.away_wins || 0));

    var totalH2h = (h2h.home_wins || 0) + (h2h.draws || 0) + (h2h.away_wins || 0);
    if (totalH2h > 0) {
      safeWidth('h2h-bar-h', Math.round(((h2h.home_wins || 0) / totalH2h) * 100));
      safeWidth('h2h-bar-d', Math.round(((h2h.draws || 0) / totalH2h) * 100));
      safeWidth('h2h-bar-a', Math.round(((h2h.away_wins || 0) / totalH2h) * 100));
    }

    // توافق تام مع مفاتيح السيرفر (streak_text أو streak)
    safeText('h2h-streak-txt', h2h.streak_text || h2h.streak || 'المواجهات المباشرة الأخيرة بين الفريقين');
    safeText('h2h-avg-goals', h2h.avg_goals ? ('معدل الأهداف: ' + h2h.avg_goals) : '');

    var chipsList = document.getElementById('h2h-chips-list');
    if (chipsList) {
      var recMatches = h2h.recent_matches || [];
      chipsList.innerHTML = recMatches.map(function(item) {
        var rCode = String(item.res || item.winner || 'D').toUpperCase();
        var cls = (rCode === 'H' || rCode === 'W') ? 'w' : (rCode === 'A' || rCode === 'L') ? 'l' : 'd';
        var yr = item.date || item.season || '';
        return '<span class="h2h-chip chip-' + cls + '" style="background:#111a2e; border:1px solid var(--card-border); padding:3px 8px; border-radius:6px; font-size:0.74rem; margin:2px; display:inline-block;">' + item.score + ' (' + yr + ')</span>';
      }).join('');
    }

    safeText('m-h-name', f.home.short);
    safeText('m-a-name', f.away.short);
    safeText('m-h-att', f.home.attack);
    safeText('m-a-def', f.away.defense);
    safeText('m-a-name2', f.away.short);
    safeText('m-h-name2', f.home.short);
    safeText('m-a-att', f.away.attack);
    safeText('m-h-def', f.home.defense);
    safeText('sb-h-name', f.home.short);
    safeText('sb-a-name', f.away.short);

    // تحديث أشرطة مقارنة الهجوم والدفاع بصرياً
    var sum1 = (Number(f.home.attack) || 1) + (Number(f.away.defense) || 1);
    safeWidth('m-bar-h-att', Math.round(((Number(f.home.attack) || 1) / sum1) * 100));
    safeWidth('m-bar-a-def', Math.round(((Number(f.away.defense) || 1) / sum1) * 100));

    var sum2 = (Number(f.away.attack) || 1) + (Number(f.home.defense) || 1);
    safeWidth('m-bar-a-att', Math.round(((Number(f.away.attack) || 1) / sum2) * 100));
    safeWidth('m-bar-h-def', Math.round(((Number(f.home.defense) || 1) / sum2) * 100));

    var redH = document.getElementById('sb-red-home');
    var redA = document.getElementById('sb-red-away');
    var boost = document.getElementById('sb-home-boost');
    if (redH) redH.checked = false;
    if (redA) redA.checked = false;
    if (boost) boost.value = 1.24;

    var aiResp = document.getElementById('ai-response-box');
    if (aiResp) {
      aiResp.style.display = 'none';
      aiResp.innerHTML = '';
    }

    window.recalculateSandbox();
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  } catch (err) {
    console.error("خطأ في فتح نافذة الرادار:", err);
  }
};

function factorial(n) { return n <= 1 ? 1 : n * factorial(n - 1); }

function dixonColesTauJS(h, a, lam, mu, rho) {
  if (h === 0 && a === 0) return Math.max(0.2, 1.0 - (lam * mu * rho));
  if (h === 0 && a === 1) return Math.max(0.2, 1.0 + (lam * rho));
  if (h === 1 && a === 0) return Math.max(0.2, 1.0 + (mu * rho));
  if (h === 1 && a === 1) return Math.max(0.2, 1.0 - rho);
  return 1.0;
}

window.recalculateSandbox = function() {
  if (!currentModalFixture) return;
  var f = currentModalFixture;
  var redH = document.getElementById('sb-red-home') ? document.getElementById('sb-red-home').checked : false;
  var redA = document.getElementById('sb-red-away') ? document.getElementById('sb-red-away').checked : false;
  var boost = document.getElementById('sb-home-boost') ? parseFloat(document.getElementById('sb-home-boost').value) : 1.24;

  safeText('sb-boost-val', boost.toFixed(2) + 'x');
  var homeXg = (f.home.xg || 1.5) * (boost / 1.24);
  var awayXg = (f.away.xg || 1.1);

  if (redH) { homeXg *= 0.62; awayXg *= 1.18; }
  if (redA) { awayXg *= 0.62; homeXg *= 1.18; }

  homeXg = Math.max(0.25, Math.min(4.2, homeXg));
  awayXg = Math.max(0.25, Math.min(3.8, awayXg));

  // بناء مصفوفة بواسون المعدلة بديكسون-كولز (0..5 أهداف)
  var maxG = 5;
  var mat = [];
  var sumMat = 0;
  for (var h = 0; h <= maxG; h++) {
    mat[h] = [];
    for (var a = 0; a <= maxG; a++) {
      var pPoi = (Math.exp(-homeXg) * Math.pow(homeXg, h) / factorial(h)) *
                 (Math.exp(-awayXg) * Math.pow(awayXg, a) / factorial(a));
      var tau = dixonColesTauJS(h, a, homeXg, awayXg, -0.10);
      mat[h][a] = pPoi * tau;
      sumMat += mat[h][a];
    }
  }

  var pHomeRaw = 0, pDrawRaw = 0, pAwayRaw = 0, pBttsRaw = 0, pOverRaw = 0;
  for (var h2 = 0; h2 <= maxG; h2++) {
    for (var a2 = 0; a2 <= maxG; a2++) {
      mat[h2][a2] /= (sumMat || 1);
      var cellP = mat[h2][a2];
      if (h2 > a2) pHomeRaw += cellP;
      else if (h2 === a2) pDrawRaw += cellP;
      else pAwayRaw += cellP;

      if (h2 >= 1 && a2 >= 1) pBttsRaw += cellP;
      if ((h2 + a2) > 2.5) pOverRaw += cellP;
    }
  }

  var pH = Math.round(pHomeRaw * 100);
  var pD = Math.round(pDrawRaw * 100);
  var pA = Math.max(1, 100 - (pH + pD));

  // استخراج النتيجة الأكثر اتساقاً مع الكفة الراجحة
  var bestH = 1, bestA = 1, maxCell = -1;
  for (var bh = 0; bh <= 3; bh++) {
    for (var ba = 0; ba <= 3; ba++) {
      var validSide = (pH >= pD && pH >= pA && bh > ba) ||
                      (pA > pH && pA >= pD && ba > bh) ||
                      (pD > pH && pD > pA && bh === ba);
      if (validSide && mat[bh][ba] > maxCell) {
        maxCell = mat[bh][ba];
        bestH = bh;
        bestA = ba;
      }
    }
  }

  safeText('sb-score', bestH + ' - ' + bestA);
  safeText('sb-xg-text', 'xG: ' + homeXg.toFixed(2) + ' - ' + awayXg.toFixed(2));

  safeWidth('sb-bar-h', pH);
  safeWidth('sb-bar-d', pD);
  safeWidth('sb-bar-a', pA);
  safeText('sb-lbl-h', pH + '%');
  safeText('sb-lbl-d', pD + '%');
  safeText('sb-lbl-a', pA + '%');

  safeText('sb-btts', Math.round(pBttsRaw * 100) + '%');
  safeText('sb-over', Math.round(pOverRaw * 100) + '%');

  var grid = document.getElementById('sb-heatmap-grid');
  if (grid) {
    var html = '<tr><th style="padding:6px; border:1px solid var(--card-border);">المضيف \\ الضيف</th><th>0</th><th>1</th><th>2</th><th>3</th></tr>';
    for (var rh = 0; rh <= 3; rh++) {
      html += '<tr><th style="padding:6px; border:1px solid var(--card-border);">' + rh + '</th>';
      for (var ra = 0; ra <= 3; ra++) {
        var prob = Math.round(mat[rh][ra] * 1000) / 10;
        var bg = prob >= 13 ? 'rgba(0, 230, 118, 0.35)' : prob >= 7.5 ? 'rgba(255, 214, 0, 0.25)' : 'rgba(255, 255, 255, 0.04)';
        html += '<td style="background:' + bg + '; font-weight:800; padding:6px; text-align:center; border:1px solid var(--card-border);">' + prob + '%</td>';
      }
      html += '</tr>';
    }
    grid.innerHTML = html;
  }
};

window.resetSandbox = function() {
  var redH = document.getElementById('sb-red-home');
  var redA = document.getElementById('sb-red-away');
  var boost = document.getElementById('sb-home-boost');
  if (redH) redH.checked = false;
  if (redA) redA.checked = false;
  if (boost) boost.value = 1.24;
  window.recalculateSandbox();
};

// =========================================================
// 6. المحلل الذكي، صحيفة الجولة، وتذكرة الحسم
// =========================================================
window.askAiPundit = async function() {
  if (!currentModalFixture) return;
  var f = currentModalFixture;
  var btn = document.getElementById('ai-ask-btn');
  var box = document.getElementById('ai-response-box');
  if (!btn || !box) return;

  btn.disabled = true;
  btn.innerText = 'جاري التحليل... ⏳';
  box.style.display = 'block';
  box.innerText = 'يقوم المحلل التكتيكي بدراسة بيانات الفريقين...';

  try {
    var payload = {
      home_team: f.home.short || f.home.name,
      away_team: f.away.short || f.away.name,
      home_prob: Number(f.home.prob) || 40,
      draw_prob: Number(f.draw_prob) || 28,
      away_prob: Number(f.away.prob) || 32,
      home_xg: Number(f.home.xg) || 1.4,
      away_xg: Number(f.away.xg) || 1.1,
      home_elo: Number(f.home.elo) || 1550,
      away_elo: Number(f.away.elo) || 1520,
      edge_label: (f.edge && f.edge.label) || '',
      edge_reason: (f.edge && f.edge.reason) || '',
      streak_text: (f.h2h && (f.h2h.streak_text || f.h2h.streak)) || ''
    };

    var res = await fetch('/api/ai_analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      var data = await res.json();
      var txt = data.analysis || 'تشير مؤشرات الأداء إلى تكافؤ نسبي مع أفضلية طفيفة للمضيف.';
      box.innerHTML = txt.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#fff;">$1</strong>');
    } else {
      throw new Error('Fallback');
    }
  } catch (e) {
    box.innerHTML = 'تشير النمذجة التكتيكية إلى أفضلية نسبية لـ <strong>' +
      (f.home.prob >= f.away.prob ? f.home.short : f.away.short) +
      '</strong> بناءً على فارق الأهداف المتوقعة (' + f.home.xg + ' مقابل ' + f.away.xg + ').';
  } finally {
    btn.disabled = false;
    btn.innerText = '✨ استشر المحلل الآن';
  }
};

window.openNewspaperModal = async function() {
  var modal = document.getElementById('newspaper-modal');
  var body = document.getElementById('gazette-body');
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  if (body) {
    body.innerHTML = '<div class="loading-state">جاري صياغة تقرير الجولة من غرفة التحرير...</div>';
    try {
      var league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
      var res = await fetch('/api/ai_newspaper/' + league);
      if (!res.ok) res = await fetch('/api/gazette/' + league);
      var data = await res.json();

      var rawContent = data.content || '';
      var formattedContent = rawContent
        .replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--accent-gold);">$1</strong>')
        .replace(/\n/g, '<br>');

      body.innerHTML =
        (data.headline ? '<h3 style="color:var(--accent-gold); font-size:1.15rem; margin-bottom:12px; border-bottom:1px solid var(--card-border); padding-bottom:8px;">' + data.headline + '</h3>' : '') +
        '<div style="line-height:1.8; font-size:0.9rem; color:#e2e8f0;">' + formattedContent + '</div>';
    } catch (e) {
      body.innerHTML = '<div style="color:var(--accent-red); text-align:center;">تعذر جلب الصحيفة حالياً.</div>';
    }
  }
};

window.openAccaModal = async function() {
  var modal = document.getElementById('acca-modal');
  var listEl = document.getElementById('acca-picks-list');
  var probEl = document.getElementById('acca-joint-prob');
  if (!modal) return;

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  if (listEl) listEl.innerHTML = '<div class="loading-state" style="padding:20px 0;">جاري استخراج أعلى 3 مباريات موثوقية...</div>';
  if (probEl) probEl.innerText = '...';

  try {
    var league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
    var res = await fetch('/api/safe_accumulator/' + league);
    var data = await res.json();
    var picks = data.picks || [];

    if (picks.length === 0) {
      if (listEl) listEl.innerHTML = '<div style="text-align:center; color:var(--muted); padding:16px;">لا توجد مباريات كافية في هذه الجولة لبناء التذكرة.</div>';
      if (probEl) probEl.innerText = '0%';
      return;
    }

    if (listEl) {
      listEl.innerHTML = picks.map(function(p, i) {
        return '<div style="background:#080d1a; border:1px solid var(--card-border); border-right:4px solid var(--accent-green); border-radius:12px; padding:12px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">' +
          '<div>' +
            '<div style="font-size:0.78rem; color:var(--muted);">المواجهة #' + (i + 1) + ': ' + p.match + '</div>' +
            '<div style="font-weight:900; font-size:0.95rem; color:#fff; margin-top:2px;">✅ ' + p.bet + '</div>' +
          '</div>' +
          '<span style="background:rgba(0,230,118,0.15); color:var(--accent-green); border:1px solid rgba(0,230,118,0.4); padding:4px 10px; border-radius:12px; font-weight:900; font-size:0.85rem;">' + p.confidence + '%</span>' +
        '</div>';
      }).join('');
    }
    if (probEl) probEl.innerText = (data.joint_probability || 0) + '%';
  } catch (e) {
    if (listEl) listEl.innerHTML = '<div style="color:var(--accent-red); text-align:center;">تعذر حساب التذكرة حالياً.</div>';
  }
};

// =========================================================
// 7. محرك مجريات وأحداث المباراة الحية بالدقيقة (ESPN Live Timeline)
// =========================================================
async function fetchEventsDirectlyFromESPN(m) {
  var espnCode = ESPN_LEAGUE_MAP[m.league_code] || 'eng.1';
  var urls = [
    'https://site.api.espn.com/apis/site/v2/sports/soccer/' + espnCode + '/summary?event=' + m.id,
    'https://site.web.api.espn.com/apis/site/v2/sports/soccer/' + espnCode + '/summary?event=' + m.id,
    'https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event=' + m.id
  ];

  var summary = null;
  for (var i = 0; i < urls.length; i++) {
    try {
      var r = await fetch(urls[i]);
      if (r.ok) {
        var j = await r.json();
        if (j && (j.keyEvents || j.header || j.commentary || j.rosters)) {
          summary = j;
          break;
        }
      }
    } catch (e) {}
  }

  if (!summary) return [];

  var comp = (summary.header && summary.header.competitions && summary.header.competitions[0]) || {};
  var hTeamId = m.home_id || '';
  var aTeamId = m.away_id || '';
  var hName = m.home_team || 'المضيف';
  var aName = m.away_team || 'الضيف';

  (comp.competitors || []).forEach(function(c) {
    var tid = (c.team && c.team.id) || c.id || '';
    if (c.homeAway === 'home') {
      if (!hTeamId) hTeamId = String(tid);
      hName = (c.team && (c.team.shortDisplayName || c.team.displayName)) || hName;
    } else if (c.homeAway === 'away') {
      if (!aTeamId) aTeamId = String(tid);
      aName = (c.team && (c.team.shortDisplayName || c.team.displayName)) || aName;
    }
  });

  var eventsList = [];
  var seen = {};

  function parseEventItem(ev, isComm) {
    if (!ev || typeof ev !== 'object') return;
    var playObj = (ev.play && typeof ev.play === 'object') ? ev.play : {};
    var tObj = ev.type || playObj.type || {};
    var typeTxt = String(tObj.text || tObj.name || '').toLowerCase();
    var rawTxt = String(ev.text || ev.shortText || playObj.text || '').trim();
    var lowTxt = rawTxt.toLowerCase();

    var clkNode = ev.clock || ev.time || playObj.clock || {};
    var clkStr = (typeof clkNode === 'object' ? (clkNode.displayValue || clkNode.value) : clkNode) || '';
    clkStr = String(clkStr).replace(/'/g, '').replace(/’/g, '').trim();
    if (!clkStr && rawTxt) {
      var mm = rawTxt.match(/(\d+(?:\+\d+)?)\s*['’]/);
      if (mm) clkStr = mm[1];
    }
    var parts = (clkStr || '1').split('+');
    var baseM = parseInt(parts[0], 10) || 1;
    if (baseM > 130) baseM = Math.max(1, Math.floor(baseM / 60));
    var extM = parts.length > 1 ? (parseInt(parts[1], 10) || 0) : 0;
    var dispClock = extM > 0 ? (baseM + '+' + extM + "'") : (baseM + "'");
    var sortMin = baseM + (extM * 0.01);

    var tNode = ev.team || playObj.team || {};
    var tid = String(tNode.id || '');
    var side = (ev.homeAway === 'away' || (tid && tid === String(aTeamId))) ? 'away' : 'home';
    if (rawTxt.toLowerCase().indexOf(aName.toLowerCase()) !== -1 && rawTxt.toLowerCase().indexOf(hName.toLowerCase()) === -1) {
      side = 'away';
    }
    var teamName = side === 'home' ? hName : aName;

    var inv = ev.participants || ev.athletesInvolved || playObj.participants || [];
    var p1 = '', p2 = '';
    if (inv[0]) {
      var a0 = inv[0].athlete || inv[0];
      p1 = a0.displayName || a0.shortName || '';
    }
    if (inv[1]) {
      var a1 = inv[1].athlete || inv[1];
      p2 = a1.displayName || a1.shortName || '';
    }
    if (rawTxt) {
      var subMatch = rawTxt.match(/([A-Za-zÀ-ÿ'\-\.\s]{3,30}?)\s+replaces\s+([A-Za-zÀ-ÿ'\-\.\s]{3,30})/);
      if (subMatch) {
        if (!p1) p1 = subMatch[1].split('.').pop().trim();
        if (!p2) p2 = subMatch[2].split('.')[0].trim();
      }
      if (!p1) {
        var pm = rawTxt.match(/([A-ZÀ-Ÿ][A-Za-zÀ-ÿ'\-\.]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ'\-\.]+){0,2})\s*\([^)]+\)/);
        if (pm) p1 = pm[1].trim();
      }
      if (!p2 && lowTxt.indexOf('assisted by') !== -1) {
        var am = rawTxt.match(/[Aa]ssisted by\s+([A-Za-zÀ-ÿ'\-\.\s]{3,28}?)(?:\s+with|\.|,|$)/);
        if (am) p2 = am[1].trim();
      }
    }

    var evCat = null, titleAr = '', detailAr = '';

    if (lowTxt.indexOf('disallowed') !== -1 || lowTxt.indexOf('overturned') !== -1 || lowTxt.indexOf('no goal') !== -1 || typeTxt.indexOf('cancelled') !== -1 || (lowTxt.indexOf('offside') !== -1 && lowTxt.indexOf('goal') !== -1)) {
      evCat = 'disallowed_goal';
      var isVar = (lowTxt.indexOf('var') !== -1 || typeTxt.indexOf('var') !== -1 || lowTxt.indexOf('overturned') !== -1);
      titleAr = '🚫⚽ هدف ملغي (' + (isVar ? 'بقرار VAR' : 'بداعي التسلل') + ')';
      detailAr = 'إلغاء هدف لـ ' + (p1 || teamName) + (isVar ? ' بعد مراجعة تقنية الفيديو (VAR)' : ' بقرار الحكم بداعي التسلل');
    } else if (typeTxt.indexOf('penalty - missed') !== -1 || typeTxt.indexOf('penalty - saved') !== -1 || lowTxt.indexOf('penalty missed') !== -1 || lowTxt.indexOf('penalty saved') !== -1) {
      evCat = 'missed_penalty';
      var isSaved = (lowTxt.indexOf('saved') !== -1 || typeTxt.indexOf('saved') !== -1);
      titleAr = '❌ ضربة جزاء ضائعة — ' + (p1 || teamName);
      detailAr = (p1 || 'اللاعب') + ' أهدر ركلة جزاء (' + (isSaved ? 'تصدى لها الحارس ببراعة' : 'خارج المرمى') + ')';
    } else if ((ev.scoringPlay === true || typeTxt.indexOf('goal') !== -1 || lowTxt.indexOf('goal!') === 0) && lowTxt.indexOf('missed') === -1 && lowTxt.indexOf('saved') === -1 && lowTxt.indexOf('disallowed') === -1) {
      evCat = 'goal';
      var isPen = (ev.penaltyKick || typeTxt.indexOf('penalty') !== -1 || lowTxt.indexOf('penalty') !== -1);
      var isOg = (ev.ownGoal || typeTxt.indexOf('own goal') !== -1 || lowTxt.indexOf('own goal') !== -1);
      var tag = isPen ? ' (ركلة جزاء)' : (isOg ? ' (هدف عكسي)' : '');
      titleAr = '⚽ هدف! — ' + (p1 || teamName) + tag;
      detailAr = p2 ? ('صناعة الهدف (Assist): ' + p2) : ('هدف لصالح ' + teamName);
    } else if (lowTxt.indexOf('hits the left post') !== -1 || lowTxt.indexOf('hits the right post') !== -1 || lowTxt.indexOf('hits the bar') !== -1 || lowTxt.indexOf('hits the crossbar') !== -1 || lowTxt.indexOf('hit the post') !== -1 || lowTxt.indexOf('woodwork') !== -1) {
      evCat = 'woodwork';
      var barOrPost = lowTxt.indexOf('bar') !== -1 ? 'العارضة' : 'القائم';
      titleAr = '🥅 تسديدة في ' + barOrPost + '! — ' + (p1 || teamName);
      detailAr = 'فرصة خطيرة جداً! تسديدة ' + (p1 || teamName) + ' ارتطمت بـ' + barOrPost;
    } else if (typeTxt.indexOf('subst') !== -1 || lowTxt.indexOf('substitution') !== -1 || lowTxt.indexOf('replaces') !== -1) {
      evCat = 'sub';
      titleAr = '🔄 تبديل — ' + teamName;
      detailAr = 'دخول: ' + (p1 || 'بديل') + ' | خروج: ' + (p2 || 'أساسي');
    } else if (typeTxt.indexOf('red card') !== -1 || typeTxt.indexOf('second yellow') !== -1 || lowTxt.indexOf('red card') !== -1) {
      evCat = 'red_card';
      titleAr = '🟥 بطاقة حمراء (طرد) — ' + (p1 || teamName);
      detailAr = 'بطاقة حمراء ومغادرة الملعب لـ ' + (p1 || teamName);
    } else if (typeTxt.indexOf('yellow card') !== -1 || lowTxt.indexOf('yellow card') !== -1) {
      evCat = 'yellow_card';
      titleAr = '🟨 بطاقة صفراء — ' + (p1 || teamName);
      detailAr = 'بطاقة صفراء على ' + (p1 || teamName);
    } else if (isComm && (lowTxt.indexOf('attempt saved') !== -1 || lowTxt.indexOf('big chance') !== -1 || lowTxt.indexOf('close range') !== -1) && p1) {
      evCat = 'big_chance';
      titleAr = '🔥 فرصة خطيرة — ' + p1;
      detailAr = 'تسديدة خطيرة من ' + p1 + ' تصدى لها الحارس/الدفاع';
    }

    if (!evCat) return;
    var key = evCat + '_' + Math.floor(baseM / 2) + '_' + String(p1 || teamName).slice(0, 8).toLowerCase();
    if (seen[key]) return;
    seen[key] = true;

    eventsList.push({
      clock: dispClock,
      sort_minute: sortMin,
      type: evCat,
      side: side,
      team_name: teamName,
      player: p1 || teamName,
      secondary_player: p2,
      title: titleAr,
      detail: detailAr
    });
  }

  ['keyEvents', 'scoringPlays', 'details'].forEach(function(k) {
    if (Array.isArray(summary[k])) summary[k].forEach(function(x) { parseEventItem(x, false); });
  });
  if (Array.isArray(comp.details)) comp.details.forEach(function(x) { parseEventItem(x, false); });
  ['commentary', 'plays'].forEach(function(k) {
    if (Array.isArray(summary[k])) summary[k].forEach(function(x) { parseEventItem(x, true); });
  });

  eventsList.sort(function(a, b) { return a.sort_minute - b.sort_minute; });
  return eventsList;
}

window.filterMatchTimeline = function(filterType, btnEl) {
  var allBtns = document.querySelectorAll('.tm-ev-filter-btn');
  allBtns.forEach(function(b) {
    b.style.background = '#131c2e';
    b.style.color = 'var(--muted)';
    b.style.borderColor = 'var(--card-border)';
  });
  if (btnEl) {
    btnEl.style.background = 'var(--accent-cyan)';
    btnEl.style.color = '#080c15';
    btnEl.style.borderColor = 'var(--accent-cyan)';
  }

  var list = window.currentMatchEventsCache || [];
  var filtered = list;
  if (filterType === 'goals') {
    filtered = list.filter(function(e) { return e.type === 'goal' || e.type === 'disallowed_goal'; });
  } else if (filterType === 'chances') {
    filtered = list.filter(function(e) { return e.type === 'woodwork' || e.type === 'missed_penalty' || e.type === 'big_chance'; });
  } else if (filterType === 'subs') {
    filtered = list.filter(function(e) { return e.type === 'sub'; });
  } else if (filterType === 'cards') {
    filtered = list.filter(function(e) { return e.type === 'yellow_card' || e.type === 'red_card'; });
  }

  renderMatchEventsItems(filtered);
};

function renderMatchEventsItems(events) {
  var listBox = document.getElementById('tm-events-timeline-list');
  if (!listBox) return;

  if (!events || events.length === 0) {
    listBox.innerHTML = '<div style="text-align:center; padding:24px; color:var(--muted); font-size:0.84rem;">لا توجد أحداث مسجلة ضمن هذا التصنيف حتى الآن.</div>';
    return;
  }

  var styleMap = {
    'goal':            { icon: '⚽', border: '#00e676', bg: 'rgba(0, 230, 118, 0.12)', badgeCol: '#00e676' },
    'disallowed_goal': { icon: '🚫', border: '#a855f7', bg: 'rgba(168, 85, 247, 0.14)', badgeCol: '#c084fc' },
    'missed_penalty':  { icon: '❌', border: '#ff5252', bg: 'rgba(255, 82, 82, 0.12)', badgeCol: '#ff5252' },
    'woodwork':        { icon: '🥅', border: '#ffd600', bg: 'rgba(255, 214, 0, 0.12)', badgeCol: '#ffd600' },
    'big_chance':      { icon: '🔥', border: '#00d2ff', bg: 'rgba(0, 210, 255, 0.10)', badgeCol: '#00d2ff' },
    'sub':             { icon: '🔄', border: '#38bdf8', bg: 'rgba(56, 189, 248, 0.10)', badgeCol: '#38bdf8' },
    'yellow_card':     { icon: '🟨', border: '#ffd600', bg: 'rgba(255, 214, 0, 0.10)', badgeCol: '#ffd600' },
    'red_card':        { icon: '🟥', border: '#ff5252', bg: 'rgba(255, 82, 82, 0.16)', badgeCol: '#ff5252' }
  };

  listBox.innerHTML = events.map(function(ev) {
    var st = styleMap[ev.type] || styleMap['big_chance'];
    var teamBadgeBg = ev.side === 'home' ? 'rgba(0, 230, 118, 0.15)' : 'rgba(0, 210, 255, 0.15)';
    var teamBadgeCol = ev.side === 'home' ? 'var(--accent-green)' : 'var(--accent-cyan)';

    var bodyContent = '';
    if (ev.type === 'sub') {
      bodyContent =
        '<div style="display:flex; flex-wrap:wrap; gap:10px; font-size:0.8rem; margin-top:4px;">' +
          '<span style="color:#00e676; font-weight:800;">🟢 دخول: ' + (ev.player || '-') + '</span>' +
          (ev.secondary_player ? '<span style="color:#ff5252; font-weight:800;">🔴 خروج: ' + ev.secondary_player + '</span>' : '') +
        '</div>';
    } else {
      bodyContent = '<div style="font-size:0.78rem; color:#cbd5e1; margin-top:3px; line-height:1.5;">' + (ev.detail || '') + '</div>';
    }

    return '<div style="display:flex; align-items:flex-start; gap:10px; background:#0c121e; border:1px solid var(--card-border); border-right:4px solid ' + st.border + '; border-radius:12px; padding:10px 12px; margin-bottom:10px;">' +
      '<div style="min-width:44px; height:30px; border-radius:8px; background:' + st.bg + '; border:1px solid ' + st.border + '; color:' + st.badgeCol + '; font-weight:900; font-size:0.8rem; display:flex; align-items:center; justify-content:center; direction:ltr;">' +
        ev.clock +
      '</div>' +
      '<div style="font-size:1.15rem; line-height:1.2; padding-top:2px;">' + st.icon + '</div>' +
      '<div style="flex:1;">' +
        '<div style="display:flex; justify-content:space-between; align-items:center; gap:6px; flex-wrap:wrap;">' +
          '<strong style="font-size:0.86rem; color:#f8fafc;">' + ev.title + '</strong>' +
          '<span style="background:' + teamBadgeBg + '; color:' + teamBadgeCol + '; font-size:0.7rem; font-weight:800; padding:2px 8px; border-radius:6px;">' + ev.team_name + '</span>' +
        '</div>' +
        bodyContent +
      '</div>' +
    '</div>';
  }).join('');
}

async function loadMatchEvents() {
  var container = document.getElementById('tm-events-content');
  var m = window.activeMatchModalData;
  if (!container || !m) return;

  if (m.state === 'pre') {
    container.innerHTML = '<div style="background:#0c121e; border:1px dashed var(--card-border); border-radius:12px; padding:25px 15px; text-align:center; color:var(--accent-gold); font-size:0.85rem;">' +
      '⏳ لم تنطلق صافرة البداية بعد؛ ستظهر مجريات اللقاء فور بدء المباراة.' +
    '</div>';
    return;
  }

  container.innerHTML = '<div class="loading-state" style="padding:30px 0;">جاري سحب مجريات وأحداث اللقاء الدقيقة من ESPN...</div>';

  var events = [];
  try {
    var res = await fetch('/api/match_events/' + (m.league_code || 'PL') + '/' + m.id);
    if (res.ok) {
      var srv = await res.json();
      if (srv && Array.isArray(srv.events) && srv.events.length > 0) {
        events = srv.events;
      }
    }
  } catch (e) {}

  if (events.length === 0) {
    try {
      events = await fetchEventsDirectlyFromESPN(m);
    } catch (e) {}
  }

  window.currentMatchEventsCache = events;

  var filterBarHtml =
    '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:12px; justify-content:center;">' +
      '<button class="tm-ev-filter-btn" onclick="filterMatchTimeline(\'all\', this)" style="background:var(--accent-cyan); color:#080c15; border:1px solid var(--accent-cyan); padding:4px 12px; border-radius:16px; font-size:0.75rem; font-weight:800; cursor:pointer;">الكل (' + events.length + ')</button>' +
      '<button class="tm-ev-filter-btn" onclick="filterMatchTimeline(\'goals\', this)" style="background:#131c2e; color:var(--muted); border:1px solid var(--card-border); padding:4px 10px; border-radius:16px; font-size:0.75rem; font-weight:800; cursor:pointer;">⚽ الأهداف و VAR</button>' +
      '<button class="tm-ev-filter-btn" onclick="filterMatchTimeline(\'chances\', this)" style="background:#131c2e; color:var(--muted); border:1px solid var(--card-border); padding:4px 10px; border-radius:16px; font-size:0.75rem; font-weight:800; cursor:pointer;">🥅 القوائم والفرص</button>' +
      '<button class="tm-ev-filter-btn" onclick="filterMatchTimeline(\'subs\', this)" style="background:#131c2e; color:var(--muted); border:1px solid var(--card-border); padding:4px 10px; border-radius:16px; font-size:0.75rem; font-weight:800; cursor:pointer;">🔄 التبديلات</button>' +
      '<button class="tm-ev-filter-btn" onclick="filterMatchTimeline(\'cards\', this)" style="background:#131c2e; color:var(--muted); border:1px solid var(--card-border); padding:4px 10px; border-radius:16px; font-size:0.75rem; font-weight:800; cursor:pointer;">🟨 البطاقات</button>' +
    '</div>' +
    '<div id="tm-events-timeline-list" style="max-height:390px; overflow-y:auto; padding-left:4px;"></div>';

  container.innerHTML = filterBarHtml;
  renderMatchEventsItems(events);
}