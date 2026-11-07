// ========================================================
// DeepPitch Pro - AI Scout & Fantasy Chatbot Engine
// ========================================================

function toggleScoutWidget() {
  const drawer = document.getElementById('scout-chat-drawer');
  if (!drawer) return;
  const isShown = drawer.style.display === 'flex';
  drawer.style.display = isShown ? 'none' : 'flex';

  if (!isShown) {
    const input = document.getElementById('scout-input-field');
    if (input) setTimeout(() => input.focus(), 100);
  }
}

function askScoutFast(questionText) {
  const input = document.getElementById('scout-input-field');
  if (input) {
    input.value = questionText;
    executeScoutQuery(questionText);
  }
}

function handleScoutSubmit(event) {
  event.preventDefault();
  const input = document.getElementById('scout-input-field');
  const text = input.value.trim();
  if (!text) return;
  executeScoutQuery(text);
  input.value = '';
}

async function executeScoutQuery(userText) {
  const body = document.getElementById('scout-messages-body');
  const sendBtn = document.getElementById('scout-send-btn');

  // إضافة رسالة المستخدم
  const userMsgEl = document.createElement('div');
  userMsgEl.className = 'scout-msg msg-user';
  userMsgEl.innerText = userText;
  body.appendChild(userMsgEl);

  // مؤشر جاري الكتابة
  const loadingEl = document.createElement('div');
  loadingEl.className = 'scout-msg msg-bot';
  loadingEl.innerText = '🔍 جاري تحليل الجداول والإحصائيات...';
  body.appendChild(loadingEl);
  body.scrollTop = body.scrollHeight;

  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch('/api/ai_scout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        league_code: (typeof activeLeague !== 'undefined' && activeLeague) ? activeLeague : 'PL'
      })
    });

    const data = await res.json();
    if (data && data.reply) {
      loadingEl.innerHTML = data.reply.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    } else {
      loadingEl.innerText = data.detail || 'تعذر استخراج توصية السكاوت حالياً.';
    }
  } catch (err) {
    console.error("Scout Error:", err);
    loadingEl.innerText = 'تعذر الاتصال بالسكاوت الذكي، يرجى التأكد من تشغيل السيرفر.';
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    body.scrollTop = body.scrollHeight;
  }
}