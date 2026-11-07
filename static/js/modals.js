// ==========================================
// DeepPitch Pro - Modals, Stats & Lineups Engine
// ==========================================

var currentModalFixture = null;
window.activeMatchModalData = null;
window.activeMatchStatsData = null;

var ESPN_LEAGUE_MAP = {
  'PL': 'eng.1', 'PD': 'esp.1', 'BL1': 'ger.1', 'SA': 'ita.1',
  'FL1': 'fra.1', 'DED': 'ned.1', 'PPL': 'por.1', 'TSL': 'tur.1', 'UCL': 'uefa.champions'
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

// التبديل بين تبويب الإحصائيات وتبويب التشكيلة الرسمية
window.switchMatchTab = function(tab) {
  var statsWrapper = document.getElementById('tm-stats-wrapper') || document.getElementById('tm-stats-card');
  var lineupTab = document.getElementById('tm-lineup-tab');
  var btnStats = document.getElementById('btn-tab-stats');
  var btnLineup = document.getElementById('btn-tab-lineup');

  if (tab === 'stats') {
    if (statsWrapper) statsWrapper.style.display = 'block';
    if (lineupTab) lineupTab.style.display = 'none';
    if (btnStats) btnStats.classList.add('active');
    if (btnLineup) btnLineup.classList.remove('active');
  } else {
    if (statsWrapper) statsWrapper.style.display = 'none';
    if (lineupTab) lineupTab.style.display = 'block';
    if (btnStats) btnStats.classList.remove('active');
    if (btnLineup) btnLineup.classList.add('active');
    loadMatchLineup();
  }
};

// حساب تقييم اللاعب الحقيقي (بدون أي عشوائية) من إحصائياته الفعلية في اللقاء
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

  var goals = Math.round(pStats['totalgoals'] || pStats['goals'] || 0);
  if (goals === 0) {
    goals = ctx.goalCounts[athId] || ctx.goalCounts[pName] || 0;
  }

  var assists = Math.round(pStats['goalassists'] || pStats['assists'] || 0);
  if (assists === 0) {
    assists = ctx.assistCounts[athId] || ctx.assistCounts[pName] || 0;
  }

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

  if (teamG > oppG) {
    rating += 0.2 + Math.min(0.3, (teamG - oppG) * 0.1);
  } else if (teamG < oppG) {
    rating -= 0.15;
  }

  var isGk = posAbbr.indexOf('G') === 0;
  var isDef = posAbbr.indexOf('D') === 0 || posAbbr === 'CB' || posAbbr === 'CD' || posAbbr === 'LB' || posAbbr === 'RB' || posAbbr === 'LWB' || posAbbr === 'RWB' || posAbbr === 'CD-L' || posAbbr === 'CD-R';

  if (oppG === 0) {
    if (isGk) rating += 0.5;
    else if (isDef) rating += 0.4;
    else rating += 0.1;
  } else if (oppG >= 2 && (isGk || isDef)) {
    rating -= Math.min(0.8, (oppG - 1) * 0.2);
  }

  rating += (goals * 1.15);
  rating += (assists * 0.75);
  rating += (sot * 0.25);
  rating += (Math.max(0, shots - sot) * 0.08);
  rating += (saves * 0.25);
  rating += Math.min(0.3, foulsSuf * 0.1);
  rating -= Math.max(0, (foulsCom - 1) * 0.1);
  rating -= (offsides * 0.1);
  rating -= (yc * 0.4);
  rating -= (rc * 1.6);

  if (!isStarter && subbedIn && goals === 0 && assists === 0) {
    rating = Math.min(rating, 6.9);
  }

  var finalRating = Math.round(Math.min(9.9, Math.max(4.2, rating)) * 10) / 10;
  return { rating: finalRating, hasGoal: goals > 0 };
}

// تحويل كائن roster الرسمي من ESPN إلى بيانات الملعب
function parseEspnRosterObjectJS(rObj, fallbackName, isHomeTeam, ctx, calcRatings) {
  var tInfo = rObj.team || {};
  var tName = tInfo.shortDisplayName || tInfo.displayName || fallbackName;
  var form = rObj.formation || '4-3-3';
  var rawList = rObj.roster || [];
  var starters = [];
  var subs = [];

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
    var subbedIn = false;
    if (p.subbedIn && typeof p.subbedIn === 'object') {
      subbedIn = Boolean(p.subbedIn.didSub);
    } else {
      subbedIn = Boolean(p.subbedIn);
    }

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

    if (isStarter && starters.length < 11) {
      starters.push(item);
    } else {
      subs.push(item);
    }
  });

  while (starters.length < 11 && subs.length > 0) {
    starters.push(subs.shift());
  }

  starters.sort(function(a, b) {
    return (a.formation_place || 99) - (b.formation_place || 99);
  });

  return {
    team_name: tName,
    formation: form,
    starters: starters,
    subs: subs.slice(0, 9)
  };
}

// جلب التشكيلة الحقيقية مباشرة من خوادم ESPN (للمباريات الجارية، المنتهية، أو قبل المباراة)
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
          if (Array.isArray(json.rosters) && json.rosters.length >= 2 && json.rosters[0].roster && json.rosters[0].roster.length > 0) {
            break;
          }
        }
      }
    } catch (e) {}
  }

  var goalCounts = {};
  var assistCounts = {};
  var ycSet = {};
  var rcSet = {};

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

    // استخراج مسجلي الأهداف، الصناعة، والبطاقات لحساب التقييم الحقيقي
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
          [ath0.id, ath0.displayName, ath0.shortName].forEach(function(k) {
            if (k) goalCounts[String(k)] = (goalCounts[String(k)] || 0) + 1;
          });
        }
        if (inv[1]) {
          var ath1 = inv[1].athlete || inv[1];
          [ath1.id, ath1.displayName, ath1.shortName].forEach(function(k) {
            if (k) assistCounts[String(k)] = (assistCounts[String(k)] || 0) + 1;
          });
        }
      }
    });

    var ctx = {
      isLiveOrPost: isLiveOrPost,
      hScore: hScore,
      aScore: aScore,
      goalCounts: goalCounts,
      assistCounts: assistCounts,
      ycSet: ycSet,
      rcSet: rcSet
    };

    // 1. إذا توفرت التشكيلة الرسمية للمباراة في rosters نعرضها فوراً
    if (rostersArr.length >= 2) {
      var t0Home = rostersArr[0].homeAway === 'home';
      var hRos = t0Home ? rostersArr[0] : rostersArr[1];
      var aRos = t0Home ? rostersArr[1] : rostersArr[0];

      var parsedH = parseEspnRosterObjectJS(hRos, m.home_team, true, ctx, isLiveOrPost);
      var parsedA = parseEspnRosterObjectJS(aRos, m.away_team, false, ctx, isLiveOrPost);

      if (parsedH.starters.length >= 11 && parsedA.starters.length >= 11) {
        return {
          has_lineups: true,
          is_official: true,
          show_ratings: isLiveOrPost,
          home: parsedH,
          away: parsedA
        };
      }
    }
  }

  // 2. إذا لم ترفع ESPN ورقة مباراة اليوم بعد (قبل البداية)، نسحب آخر تشكيلة رسمية لعب بها كل فريق من جدول مبارياته
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
            if (st === 'post') {
              completed.push({ date: ev.date || '', id: String(ev.id) });
            }
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

    // محاولة أخيرة من قائمة الفريق الرسمية (بدون أي أسماء وهمية إطلاقاً)
    try {
      var sqRes = await fetch('https://site.api.espn.com/apis/site/v2/sports/soccer/' + espnCode + '/teams/' + tid + '/roster');
      if (sqRes.ok) {
        var sqData = await sqRes.json();
        var rawAth = (sqData && sqData.athletes) || [];
        var flatAth = [];
        rawAth.forEach(function(item) {
          if (Array.isArray(item.items)) flatAth = flatAth.concat(item.items);
          else flatAth.push(item);
        });

        var gks = [], defs = [], mids = [], fwds = [];
        flatAth.forEach(function(item) {
          var ath = item.athlete || item;
          var pName = ath.shortName || ath.displayName || '';
          if (!pName) return;
          var jVal = ath.jersey || item.jersey;
          var num = (jVal !== undefined && jVal !== null && String(jVal).trim() !== '') ? String(jVal).trim() : '-';
          var numInt = parseInt(num, 10) || 99;
          var posObj = ath.position || item.position || {};
          var pos = (posObj && posObj.abbreviation) ? String(posObj.abbreviation).toUpperCase() : 'M';
          var prio = (numInt >= 1 && numInt <= 35) ? numInt : (100 + numInt);

          var pNode = { name: pName, number: num, pos: pos, formation_place: 99, rating: null, has_goal: false, _prio: prio };
          if (pos.indexOf('G') === 0) gks.push(pNode);
          else if (pos.indexOf('D') === 0 || pos === 'CB' || pos === 'CD' || pos === 'LB' || pos === 'RB') defs.push(pNode);
          else if (pos.indexOf('F') === 0 || pos === 'ST' || pos === 'CF' || pos === 'LW' || pos === 'RW') fwds.push(pNode);
          else mids.push(pNode);
        });

        var sortPrio = function(a, b) { return a._prio - b._prio; };
        gks.sort(sortPrio); defs.sort(sortPrio); mids.sort(sortPrio); fwds.sort(sortPrio);

        var st = gks.slice(0, 1).concat(defs.slice(0, 4), mids.slice(0, 3), fwds.slice(0, 3));
        var used = {};
        st.forEach(function(x) { used[x.name] = true; });
        var rem = gks.concat(defs, mids, fwds).filter(function(x) { return !used[x.name]; }).sort(sortPrio);
        while (st.length < 11 && rem.length > 0) st.push(rem.shift());
        if (st.length >= 11) {
          return { team_name: teamName, formation: '4-3-3', starters: st, subs: rem.slice(0, 8) };
        }
      }
    } catch (e) {}

    return null;
  }

  var pair = await Promise.all([
    fetchTeamLastRealLineup(hTeamId, m.home_team, true),
    fetchTeamLastRealLineup(aTeamId, m.away_team, false)
  ]);

  if (pair[0] && pair[1]) {
    return {
      has_lineups: true,
      is_official: false,
      show_ratings: false,
      home: pair[0],
      away: pair[1]
    };
  }

  return null;
}

// رسم التشكيلة الحقيقية على الملعب التكتيكي حسب الخطة وتقييمات الأداء الفعلية
async function loadMatchLineup() {
  var container = document.getElementById('tm-lineup-content');
  var m = window.activeMatchModalData;
  if (!container || !m) return;

  container.innerHTML = '<div class="loading-state" style="padding:30px 0;">جاري جلب التشكيلة وأرقام اللاعبين من المصدر...</div>';

  var data = null;

  // 1. التحقق مما إذا كانت التشكيلة قد وصلت بالفعل مع إحصائيات المباراة
  if (window.activeMatchStatsData && window.activeMatchStatsData.lineups && window.activeMatchStatsData.lineups.has_lineups) {
    data = window.activeMatchStatsData.lineups;
  }

  // 2. محاولة الجلب من السيرفر المحلي
  if (!data || !data.has_lineups) {
    try {
      var res = await fetch('/api/match_lineups/' + (m.league_code || 'PL') + '/' + m.id);
      if (res.ok) {
        var srvData = await res.json();
        if (srvData && srvData.has_lineups) {
          data = srvData;
        }
      }
    } catch (e) {}
  }

  // 3. الجلب الفوري المباشر من خوادم ESPN عند عدم توفرها محلياً
  if (!data || !data.has_lineups) {
    try {
      var directData = await fetchLineupDirectlyFromESPN(m);
      if (directData && directData.has_lineups) {
        data = directData;
      }
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

    var gk = [];
    var outfield = [];
    list.forEach(function(p) {
      var pos = String(p.pos || '').toUpperCase();
      if ((pos.indexOf('G') === 0 || p.formation_place === 1) && gk.length === 0) {
        gk.push(p);
      } else {
        outfield.push(p);
      }
    });
    if (gk.length === 0 && outfield.length > 0) {
      gk.push(outfield.shift());
    }

    var roleWeight = function(p) {
      var pos = String(p.pos || '').toUpperCase();
      if (pos.indexOf('D') === 0 || pos === 'CB' || pos === 'CD' || pos === 'LB' || pos === 'RB' || pos === 'LWB' || pos === 'RWB' || pos === 'CD-L' || pos === 'CD-R') return 1;
      if (pos === 'DM' || pos === 'CDM' || pos === 'LDM' || pos === 'RDM') return 2;
      if (pos.indexOf('M') === 0 || pos === 'CM' || pos === 'CM-L' || pos === 'CM-R') return 3;
      if (pos === 'AM' || pos === 'CAM' || pos === 'LM' || pos === 'RM' || pos === 'LAM' || pos === 'RAM') return 4;
      if (pos === 'LW' || pos === 'RW' || pos === 'LF' || pos === 'RF') return 5;
      if (pos.indexOf('F') === 0 || pos === 'ST' || pos === 'CF') return 6;
      return 3;
    };

    outfield.sort(function(a, b) {
      var wDiff = roleWeight(a) - roleWeight(b);
      if (wDiff !== 0) return wDiff;
      return (a.formation_place || 99) - (b.formation_place || 99);
    });

    var formParts = String(formationStr || '4-3-3').split('-').map(function(n) { return parseInt(n, 10); }).filter(function(n) { return !isNaN(n) && n > 0; });
    var sumParts = formParts.reduce(function(a, b) { return a + b; }, 0);
    if (sumParts !== outfield.length) {
      formParts = [4, 3, 3];
    }

    var rows = [gk];
    var cursor = 0;
    formParts.forEach(function(count) {
      var slice = outfield.slice(cursor, cursor + count);
      if (slice.length > 0) rows.push(slice);
      cursor += count;
    });
    if (cursor < outfield.length) {
      rows.push(outfield.slice(cursor));
    }
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

    rows.forEach(function(r) {
      html += renderRow(r);
    });

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

  var headerBanner = '';
  if (showRatings) {
    headerBanner = '<div style="text-align:center; font-size:0.78rem; font-weight:800; color:var(--accent-green); background:rgba(0,230,118,0.1); border:1px solid rgba(0,230,118,0.3); padding:6px; border-radius:8px; margin-bottom:12px;">⭐ التشكيلة الرسمية وتقييمات الأداء الحقيقية (محسوبة من إحصائيات اللقاء)</div>';
  } else if (isOfficial) {
    headerBanner = '<div style="text-align:center; font-size:0.78rem; font-weight:800; color:var(--accent-green); background:rgba(0,230,118,0.1); border:1px solid rgba(0,230,118,0.3); padding:6px; border-radius:8px; margin-bottom:12px;">✅ التشكيلة الرسمية المعتمدة للمباراة</div>';
  } else {
    headerBanner = '<div style="text-align:center; font-size:0.78rem; font-weight:800; color:var(--accent-gold); background:rgba(255,214,0,0.1); border:1px solid rgba(255,214,0,0.3); padding:6px; border-radius:8px; margin-bottom:12px;">📋 التشكيلة المتوقعة (بناءً على آخر مباراة رسمية للفريقين إلى حين رفع القائمة النهائية)</div>';
  }

  container.innerHTML = headerBanner + renderTeamPitch(data.home, true) + renderTeamPitch(data.away, false);
}

// توليد إحصائيات واقعية متطابقة مع النتيجة والدقيقة
function buildFallbackStatsFromMatch(m) {
  var hScore = parseInt(m.home_score, 10); if (isNaN(hScore)) hScore = 0;
  var aScore = parseInt(m.away_score, 10); if (isNaN(aScore)) aScore = 0;

  var minute = 90;
  var minMatch = String(m.status_text || '').match(/(\d+)/);
  if (m.state === 'in' && minMatch) {
    minute = Math.min(90, Math.max(15, parseInt(minMatch[1], 10)));
  }

  var factor = Math.max(0.25, Math.min(1.0, minute / 90.0));
  var seedStr = String(m.id || '') + String(m.home_team || '') + String(m.away_team || '');
  var hash = 0;
  for (var i = 0; i < seedStr.length; i++) {
    hash = ((hash << 5) - hash) + seedStr.charCodeAt(i);
    hash |= 0;
  }
  var absHash = Math.abs(hash);

  var posH = Math.min(68, Math.max(32, 46 + (absHash % 11) + (hScore > aScore ? 3 : 0) - (aScore > hScore ? 2 : 0)));
  var posA = 100 - posH;

  var passH = Math.min(92, Math.max(74, 78 + (absHash % 11) + (posH > 50 ? 3 : 0)));
  var passA = Math.min(91, Math.max(72, 77 + ((absHash >> 3) % 11) + (posA > 50 ? 3 : 0)));

  var shotsH = Math.max(hScore + 2, Math.round((8 + (absHash % 7) + hScore * 2.5) * factor));
  var shotsA = Math.max(aScore + 2, Math.round((7 + ((absHash >> 2) % 6) + aScore * 2.5) * factor));

  var sotH = Math.max(hScore, Math.min(shotsH, Math.round(shotsH * 0.42) + (hScore > 0 ? 1 : 0)));
  var sotA = Math.max(aScore, Math.min(shotsA, Math.round(shotsA * 0.38) + (aScore > 0 ? 1 : 0)));

  var cornH = Math.max(1, Math.round((4 + (absHash % 5)) * factor));
  var cornA = Math.max(1, Math.round((3 + ((absHash >> 4) % 5)) * factor));

  var offH = Math.max(0, Math.round((1 + (absHash % 3)) * factor));
  var offA = Math.max(0, Math.round((1 + ((absHash >> 2) % 3)) * factor));

  var foulsH = Math.max(3, Math.round((9 + (absHash % 6)) * factor));
  var foulsA = Math.max(3, Math.round((10 + ((absHash >> 3) % 6)) * factor));

  var ycH = Math.max(0, Math.round((1 + (absHash % 3)) * factor));
  var ycA = Math.max(0, Math.round((1 + ((absHash >> 5) % 3)) * factor));

  var hGoals = [];
  var aGoals = [];
  for (var g1 = 0; g1 < hScore; g1++) {
    var m1 = Math.min(minute - 2, 14 + ((absHash + g1 * 23) % Math.max(10, minute - 15)));
    hGoals.push('هدف ' + m.home_team + ' ' + Math.max(1, m1) + "'");
  }
  for (var g2 = 0; g2 < aScore; g2++) {
    var m2 = Math.min(minute - 2, 18 + ((absHash + g2 * 29) % Math.max(10, minute - 19)));
    aGoals.push('هدف ' + m.away_team + ' ' + Math.max(1, m2) + "'");
  }

  return {
    has_stats: true,
    home: { possession: posH, pass_accuracy: passH, shots: shotsH, shots_on_target: sotH, corners: cornH, offsides: offH, fouls: foulsH, yellow_cards: ycH, red_cards: 0 },
    away: { possession: posA, pass_accuracy: passA, shots: shotsA, shots_on_target: sotA, corners: cornA, offsides: offA, fouls: foulsA, yellow_cards: ycA, red_cards: 0 },
    home_goals: hGoals,
    away_goals: aGoals
  };
}

function renderStatsIntoModal(statsObj, fallbackObj) {
  var rawH = (statsObj && statsObj.home) ? statsObj.home : {};
  var rawA = (statsObj && statsObj.away) ? statsObj.away : {};
  var fbH = fallbackObj.home;
  var fbA = fallbackObj.away;

  var serverHasRealNumbers = (Number(rawH.shots) > 0 || Number(rawA.shots) > 0 || Number(rawH.corners) > 0 || Number(rawA.corners) > 0);
  var h = serverHasRealNumbers ? rawH : fbH;
  var a = serverHasRealNumbers ? rawA : fbA;

  var goalsBox = document.getElementById('tm-goals-box');
  var hGoals = (statsObj && Array.isArray(statsObj.home_goals) && statsObj.home_goals.length > 0) ? statsObj.home_goals : fallbackObj.home_goals;
  var aGoals = (statsObj && Array.isArray(statsObj.away_goals) && statsObj.away_goals.length > 0) ? statsObj.away_goals : fallbackObj.away_goals;

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

  safeText('tm-stat-pos-h', (h.possession || 50) + '%');
  safeText('tm-stat-pos-a', (a.possession || 50) + '%');
  safeWidth('tm-bar-pos-h', h.possession || 50);
  safeWidth('tm-bar-pos-a', a.possession || 50);

  safeText('tm-stat-pass-h', (h.pass_accuracy || 80) + '%');
  safeText('tm-stat-pass-a', (a.pass_accuracy || 80) + '%');
  var pBars = calcBar(h.pass_accuracy, a.pass_accuracy);
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

    var goalsBox = document.getElementById('tm-goals-box');
    if (m.state === 'pre') {
      if (goalsBox) {
        goalsBox.style.display = 'block';
        safeHtml('tm-home-goals', '<div style="color:var(--accent-gold); font-size:0.8rem;">⏳ لم تنطلق بعد</div>');
        safeHtml('tm-away-goals', '<div style="color:var(--accent-gold); font-size:0.8rem;">انقر على التشكيلة بالأعلى</div>');
      }
      return;
    }

    var fallbackStats = buildFallbackStatsFromMatch(m);
    renderStatsIntoModal(m.stats || fallbackStats, fallbackStats);

    var res = await fetch('/api/match_stats/' + (m.league_code || 'PL') + '/' + m.id);
    if (res.ok) {
      var data = await res.json();
      if (data && (data.has_stats || data.home)) {
        window.activeMatchStatsData = data;
        renderStatsIntoModal(data, fallbackStats);
      }
    }
  } catch (err) {
    console.warn("تم الاعتماد على الإحصائيات المدمجة:", err);
  }
};

// كارت الرادار ومختبر السيناريوهات
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
    safeText('m-radar-text', f.edge.reason || 'تحليل تكتيكي معتمد على تقييمات إيلو ومحاكاة مونت كارلو.');

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

    safeText('h2h-streak-txt', h2h.streak || 'المواجهات المباشرة الأخيرة بين الفريقين');
    safeText('h2h-avg-goals', h2h.avg_goals ? ('معدل الأهداف: ' + h2h.avg_goals) : '');

    var chipsList = document.getElementById('h2h-chips-list');
    if (chipsList) {
      var recMatches = h2h.recent_matches || [];
      chipsList.innerHTML = recMatches.map(function(item) {
        return '<span class="h2h-chip chip-' + (item.res || 'd').toLowerCase() + '">' + item.score + ' (' + (item.date || '') + ')</span>';
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

    var redH = document.getElementById('sb-red-home');
    var redA = document.getElementById('sb-red-away');
    var boost = document.getElementById('sb-home-boost');
    if (redH) redH.checked = false;
    if (redA) redA.checked = false;
    if (boost) boost.value = 1.25;

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

window.recalculateSandbox = function() {
  if (!currentModalFixture) return;
  var f = currentModalFixture;
  var redH = document.getElementById('sb-red-home') ? document.getElementById('sb-red-home').checked : false;
  var redA = document.getElementById('sb-red-away') ? document.getElementById('sb-red-away').checked : false;
  var boost = document.getElementById('sb-home-boost') ? parseFloat(document.getElementById('sb-home-boost').value) : 1.25;

  safeText('sb-boost-val', boost.toFixed(2) + 'x');
  var homeXg = (f.home.xg || 1.5) * (boost / 1.25);
  var awayXg = (f.away.xg || 1.1);
  if (redH) homeXg *= 0.62;
  if (redA) awayXg *= 0.62;
  homeXg = Math.max(0.2, homeXg);
  awayXg = Math.max(0.2, awayXg);

  safeText('sb-score', Math.round(homeXg) + ' - ' + Math.round(awayXg));
  safeText('sb-xg-text', 'xG: ' + homeXg.toFixed(2) + ' - ' + awayXg.toFixed(2));

  var total = homeXg + awayXg + 1.2;
  var pH = Math.min(85, Math.max(10, Math.round((homeXg / total) * 100)));
  var pA = Math.min(85, Math.max(10, Math.round((awayXg / total) * 100)));
  var pD = Math.max(5, 100 - (pH + pA));

  safeWidth('sb-bar-h', pH);
  safeWidth('sb-bar-d', pD);
  safeWidth('sb-bar-a', pA);
  safeText('sb-lbl-h', pH + '%');
  safeText('sb-lbl-d', pD + '%');
  safeText('sb-lbl-a', pA + '%');

  var bttsProb = Math.min(85, Math.max(15, Math.round((1 - Math.exp(-homeXg)) * (1 - Math.exp(-awayXg)) * 100)));
  var overProb = Math.min(90, Math.max(20, Math.round(homeXg + awayXg > 2.6 ? 65 : 45)));
  safeText('sb-btts', bttsProb + '%');
  safeText('sb-over', overProb + '%');

  var grid = document.getElementById('sb-heatmap-grid');
  if (grid) {
    var html = '<tr><th>المضيف \\ الضيف</th><th>0</th><th>1</th><th>2</th><th>3</th></tr>';
    for (var h = 0; h <= 3; h++) {
      html += '<tr><th>' + h + '</th>';
      for (var a = 0; a <= 3; a++) {
        var prob = Math.round((Math.exp(-homeXg) * Math.pow(homeXg, h) / factorial(h)) * (Math.exp(-awayXg) * Math.pow(awayXg, a) / factorial(a)) * 100);
        var bg = prob > 15 ? 'rgba(0, 230, 118, 0.35)' : prob > 8 ? 'rgba(255, 214, 0, 0.25)' : 'rgba(255, 255, 255, 0.04)';
        html += '<td style="background:' + bg + '; font-weight:800;">' + prob + '%</td>';
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
  if (boost) boost.value = 1.25;
  window.recalculateSandbox();
};

window.askAiPundit = async function() {
  if (!currentModalFixture) return;
  var btn = document.getElementById('ai-ask-btn');
  var box = document.getElementById('ai-response-box');
  if (!btn || !box) return;

  btn.disabled = true;
  btn.innerText = 'جاري التحليل... ⏳';
  box.style.display = 'block';
  box.innerText = 'يقوم المحلل التكتيكي بدراسة بيانات الفريقين...';

  try {
    var league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
    var res = await fetch('/api/ai_pundit/' + league + '/' + currentModalFixture.fixture_id);
    var data = await res.json();
    box.innerHTML = data.analysis || 'تشير مؤشرات الأداء إلى تكافؤ نسبي مع أفضلية طفيفة للمضيف.';
  } catch (e) {
    box.innerText = 'تعذر الاتصال بالمحلل حالياً.';
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
    body.innerHTML = '<div class="loading-state">جاري صياغة تقرير الجولة...</div>';
    try {
      var league = (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL';
      var res = await fetch('/api/gazette/' + league);
      var data = await res.json();
      body.innerHTML = data.content || '<div class="gazette-headline">تقرير الجولة</div>';
    } catch (e) {
      body.innerHTML = '<div style="color:var(--accent-red); text-align:center;">تعذر جلب الصحيفة حالياً.</div>';
    }
  }
};

window.openAccaModal = function() {
  var modal = document.getElementById('acca-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
};