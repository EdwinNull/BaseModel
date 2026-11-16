// AI 助手：右下角按钮或 ⌘J（Windows 上 Ctrl+J）打开的悬浮面板。
// 问题连同当前文档（路径、PDF 当前页、选中的文字）发给 /api/assistant/chat，服务端让模型自己检索和阅读文档，
// 过程（搜索、阅读、联网）和回答以事件流返回。回答里的 doc: 链接换成文档库内的跳转。依赖 app.js 的全局函数。

Object.assign(I, {
  spark: '<path d="M12 3.5l1.9 5 5 1.9-5 1.9-1.9 5-1.9-5-5-1.9 5-1.9z"/><path d="M18.5 15.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  send: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  stop: '<rect x="7" y="7" width="10" height="10" rx="1.5"/>',
  pen: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7"/>',
  alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5M12 16h.01"/>',
  back: '<path d="M15 6l-6 6 6 6"/>',
  sel: '<path d="M5 7h14M5 12h9M5 17h11"/>',
});

const PRESETS = [
  ['openai', 'OpenAI', 'https://api.openai.com/v1'],
  ['deepseek', 'DeepSeek', 'https://api.deepseek.com'],
  ['qwen', '通义千问（阿里云百炼）', 'https://dashscope.aliyuncs.com/compatible-mode/v1'],
  ['kimi', 'Kimi（月之暗面）', 'https://api.moonshot.cn/v1'],
  ['glm', '智谱 GLM', 'https://open.bigmodel.cn/api/paas/v4'],
  ['siliconflow', '硅基流动', 'https://api.siliconflow.cn/v1'],
  ['openrouter', 'OpenRouter', 'https://openrouter.ai/api/v1'],
  ['ollama', 'Ollama（本机）', 'http://127.0.0.1:11434/v1'],
  ['custom', '自定义', ''],
];
const SUGGESTIONS = ['用几句话总结当前文档的要点', '这一页在讲什么？结论的依据是什么？', '文档库里还有哪些相关的方案和结果？'];
const HISTORY_SEND = 20;

const AI = {
  open: false,
  cfg: null,
  msgs: [],      // {role, content, ctxLabel} 或 {role:'assistant', content, parts, status, live, error, stopped}
  ctrl: null,
  view: 'chat',
  attach: true,
  sel: null,     // {path, text}：最近一次在文档里选中的文字
  renderQueued: false,
};

const isLocalUrl = u => /^https?:\/\/(127\.0\.0\.1|localhost)(:|\/|$)/.test(u);
const globRe = pat => new RegExp('^' + pat.split('*').map(s => escRe(s).replace(/\\\?/g, '.')).join('.*') + '$');
function aiBlocked(path) {
  return path.split('/')[0] === 'data' || AI.cfg.exclude.some(p => globRe(p).test(path));
}
const activeProvider = () => AI.cfg.providers.find(p => p.id === AI.cfg.provider);

// ------------------------------------------------------------ 面板骨架

function buildAssistant() {
  document.body.insertAdjacentHTML('beforeend', `
    <button id="ai-fab" title="AI 助手（${IS_MAC ? '⌘J' : 'Ctrl+J'}）">${ico('spark')}</button>
    <section id="ai-panel" hidden aria-label="AI 助手">
      <div class="ai-grip" title="拖动调整大小"></div>
      <header class="ai-head">
        <span class="ai-title">${ico('spark')}<b>AI 助手</b></span>
        <button class="ai-model" data-ai="settings" title="切换模型或修改设置"></button>
        <span class="sp"></span>
        <button class="icon-btn" data-ai="new" title="新对话">${ico('pen')}</button>
        <button class="icon-btn" data-ai="settings" title="设置">${ico('gear')}</button>
        <button class="icon-btn" data-ai="close" title="收起（Esc）">${ico('x')}</button>
      </header>
      <div class="ai-body" id="ai-body"></div>
      <footer class="ai-foot">
        <div class="ai-ctx" id="ai-ctx"></div>
        <div class="ai-compose">
          <textarea id="ai-input" rows="1" placeholder="问当前文档，或让它去查资料（Enter 发送，Shift+Enter 换行）"></textarea>
          <button class="ai-send" id="ai-send" title="发送">${ico('send')}</button>
        </div>
      </footer>
    </section>`);
  const size = store.get('aiSize', null);
  if (size) setPanelSize(size.w, size.h);

  $('#ai-fab').addEventListener('click', () => togglePanel(true));
  $('#ai-panel').addEventListener('click', e => {
    const a = e.target.closest('a[href^="#/"]');
    if (a) { S.pushNav = true; return; }
    const b = e.target.closest('[data-ai]');
    if (b) aiAction(b.dataset.ai, b).catch(err => toast(err.message, true));
  });
  $('#ai-panel').addEventListener('submit', e => {
    e.preventDefault();
    saveProvider(e.target, false).catch(err => toast(err.message, true));
  });
  $('#ai-panel').addEventListener('change', e => {
    if (e.target.id === 'ai-web') setWeb(e.target.value).catch(err => toast(err.message, true));
    if (e.target.name === 'preset') applyPreset(e.target.form, e.target.value);
  });

  const input = $('#ai-input');
  input.addEventListener('input', autosize);
  input.addEventListener('keydown', e => {
    // 输入法选词时的回车不发送
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && e.keyCode !== 229) {
      e.preventDefault();
      send();
    }
  });
  $('#ai-send').addEventListener('click', () => (AI.ctrl ? AI.ctrl.abort() : send()));

  $('.ai-grip').addEventListener('mousedown', e => {
    e.preventDefault();
    const panel = $('#ai-panel');
    const r = panel.getBoundingClientRect();
    const x0 = e.clientX, y0 = e.clientY;
    document.body.classList.add('resizing');
    let w = r.width, h = r.height;
    const move = ev => {
      w = Math.min(innerWidth - 32, Math.max(340, r.width + x0 - ev.clientX));
      h = Math.min(innerHeight - 32, Math.max(360, r.height + y0 - ev.clientY));
      setPanelSize(w, h);
    };
    const up = () => {
      document.body.classList.remove('resizing');
      removeEventListener('mousemove', move);
      removeEventListener('mouseup', up);
      store.set('aiSize', { w, h });
    };
    addEventListener('mousemove', move);
    addEventListener('mouseup', up);
  });

  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'j') {
      e.preventDefault();
      togglePanel(!AI.open);
    } else if (e.key === 'Escape' && AI.open && $('#ai-panel').contains(document.activeElement) && !$('.modal')) {
      togglePanel(false);
    }
  });
  document.addEventListener('selectionchange', () => grabSelection(window));
  // PDF.js 在框架里，选中的文字要在它自己的文档上监听
  document.addEventListener('webviewerloaded', e => {
    const w = e.detail.source;
    w.document.addEventListener('selectionchange', () => grabSelection(w));
  });
  window.addEventListener('hashchange', () => {
    if (AI.sel && AI.sel.path !== parseHash().path) AI.sel = null;
    if (AI.open) updateCtx();
  });
}

function setPanelSize(w, h) {
  const p = $('#ai-panel');
  p.style.width = w + 'px';
  p.style.height = h + 'px';
}

async function togglePanel(open) {
  AI.open = open;
  $('#ai-panel').hidden = !open;
  $('#ai-fab').hidden = open;
  if (!open) return;
  if (!AI.cfg) {
    $('#ai-body').innerHTML = loadingBox('读取助手设置…');
    await loadCfg();
  }
  if (AI.view === 'settings') renderSettings();
  else renderChat();
  updateCtx();
  $('#ai-input').focus();
}

async function loadCfg() {
  AI.cfg = await api('/api/assistant/settings');
  updateHead();
}

function updateHead() {
  const p = activeProvider();
  $('.ai-model').textContent = p ? `${p.name} · ${p.model || '未选模型'}` : '未配置模型';
}

function autosize() {
  const t = $('#ai-input');
  t.style.height = 'auto';
  t.style.height = Math.min(t.scrollHeight, 160) + 'px';
}

async function aiAction(act, el) {
  if (act === 'close') return togglePanel(false);
  if (act === 'new') {
    if (AI.ctrl) AI.ctrl.abort();
    AI.msgs = [];
    AI.view = 'chat';
    renderChat();
    return $('#ai-input').focus();
  }
  if (act === 'settings') {
    AI.view = 'settings';
    await loadCfg();
    return renderSettings();
  }
  if (act === 'back') {
    AI.view = 'chat';
    return renderChat();
  }
  if (act === 'sug') {
    $('#ai-input').value = el.textContent;
    return send();
  }
  if (act === 'attach') {
    AI.attach = !AI.attach;
    return updateCtx();
  }
  if (act === 'drop-sel') {
    AI.sel = null;
    return updateCtx();
  }
  if (act === 'copy') {
    await navigator.clipboard.writeText(AI.msgs[+el.dataset.i].content);
    return toast('已复制回答');
  }
  if (act === 'use') return useProvider(el.dataset.id);
  if (act === 'add') return showForm(null);
  if (act === 'edit') return showForm(AI.cfg.providers.find(p => p.id === el.dataset.id));
  if (act === 'cancel') { $('#ai-form').innerHTML = ''; return; }
  if (act === 'del') return deleteProvider(el.closest('form').dataset.id);
  if (act === 'models') return fetchModels(el.closest('form'));
  if (act === 'tavily-save') return saveKey('tavily', $('#ai-tavily-key').value);
}

// ------------------------------------------------------------ 当前文档与选中文字

// 点进输入框时页面上的选区会移进面板，这种变化不算；选区清空时，只清掉同一个窗口（页面或 PDF 框架）里的记录
function grabSelection(win) {
  const sel = win.getSelection();
  if (win === window && sel.anchorNode && $('#ai-panel').contains(sel.anchorNode)) return;
  const text = sel.toString().trim();
  const path = parseHash().path;
  if (text && path) AI.sel = { path, text: text.slice(0, 4000), win };
  else if (AI.sel && AI.sel.win === win) AI.sel = null;
  if (AI.open) updateCtx();
}

function currentDoc() {
  const path = S.route.path;
  const n = path && S.nodes.get(path);
  return n && !n.d ? n : null;
}

function currentContext() {
  const n = currentDoc();
  if (!n || aiBlocked(n.p)) return n ? { path: n.p, page: null, selection: null } : null;
  let page = null;
  const f = $('iframe.pdfjs');
  if (f && f.contentWindow.PDFViewerApplication && f.contentWindow.PDFViewerApplication.pdfDocument) page = f.contentWindow.PDFViewerApplication.page;
  const sel = AI.sel && AI.sel.path === n.p ? AI.sel.text : null;
  return { path: n.p, page, selection: sel };
}

function updateCtx() {
  const el = $('#ai-ctx');
  const n = currentDoc();
  if (!n || !AI.cfg) { el.innerHTML = ''; return; }
  if (aiBlocked(n.p)) {
    el.innerHTML = `<span class="ai-chip warn" title="${esc(n.p)}">${ico('alert')}<span>当前文档不向 AI 开放</span></span>`;
    return;
  }
  const sel = AI.sel && AI.sel.path === n.p && AI.attach
    ? `<button class="ai-chip on" data-ai="drop-sel" title="点击不带选中的文字">${ico('sel')}<span>选中 ${AI.sel.text.length} 字</span>${ico('x', 'xs')}</button>` : '';
  el.innerHTML = `<button class="ai-chip${AI.attach ? ' on' : ''}" data-ai="attach" title="${AI.attach ? '提问时附带当前文档，点击取消' : '点击附带当前文档'}：${esc(n.p)}">${badge(n.n)}<span>${esc(n.n)}</span></button>${sel}`;
}

function ctxLabel(ctx) {
  const name = ctx.path.split('/').pop();
  return name + (ctx.page ? ` · 第 ${ctx.page} 页` : '') + (ctx.selection ? ` · 选中 ${ctx.selection.length} 字` : '');
}

// ------------------------------------------------------------ 对话

async function send() {
  const input = $('#ai-input');
  const text = input.value.trim();
  if (!text || AI.ctrl) return;
  if (AI.view !== 'chat') { AI.view = 'chat'; }
  const ctx = AI.attach ? currentContext() : null;
  const user = { role: 'user', content: text, ctxLabel: ctx ? ctxLabel(ctx) : '' };
  const bot = { role: 'assistant', content: '', parts: [], status: '', live: true, error: '', stopped: false };
  AI.msgs.push(user, bot);
  input.value = '';
  autosize();
  renderChat();
  const history = AI.msgs.filter(m => m.role === 'user' || (m !== bot && m.content)).slice(-HISTORY_SEND)
    .map(m => ({ role: m.role, content: m.content }));
  AI.ctrl = new AbortController();
  setSending(true);
  try {
    const r = await fetch('/api/assistant/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Doc-Browser': '1' },
      body: JSON.stringify({ messages: history, context: ctx }),
      signal: AI.ctrl.signal,
    });
    if (!r.ok) throw new Error((await r.json()).error);
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let k;
      while ((k = buf.indexOf('\n\n')) >= 0) {
        const ev = buf.slice(0, k);
        buf = buf.slice(k + 2);
        if (ev.startsWith('data: ')) onEvent(bot, JSON.parse(ev.slice(6)));
      }
    }
    if (bot.live) bot.error = '连接中断，没有收到完整的回答';
  } catch (e) {
    if (e.name === 'AbortError') bot.stopped = true;
    else bot.error = e.message;
  } finally {
    bot.live = false;
    AI.ctrl = null;
    setSending(false);
    renderBotNow(bot);
  }
}

function onEvent(bot, ev) {
  const last = bot.parts[bot.parts.length - 1];
  if (ev.t === 'text') {
    if (last && last.type === 'text') last.text += ev.d;
    else bot.parts.push({ type: 'text', text: ev.d });
    bot.status = '';
  } else if (ev.t === 'status') {
    bot.status = ev.text;
  } else if (ev.t === 'round') {
    bot.status = '';
  } else if (ev.t === 'tool') {
    const item = { id: ev.id, label: ev.label, state: 'run', summary: '' };
    if (last && last.type === 'tools') last.items.push(item);
    else bot.parts.push({ type: 'tools', items: [item] });
    bot.status = '';
  } else if (ev.t === 'tool_end') {
    for (const p of bot.parts) {
      if (p.type !== 'tools') continue;
      const it = p.items.find(x => x.id === ev.id && x.state === 'run');
      if (it) { it.state = ev.ok ? 'ok' : 'err'; it.summary = ev.summary; }
    }
  } else if (ev.t === 'done') {
    bot.content = ev.content;
    bot.live = false;
  } else if (ev.t === 'error') {
    bot.error = ev.message;
    bot.live = false;
  }
  scheduleRender(bot);
}

function setSending(on) {
  const b = $('#ai-send');
  b.innerHTML = ico(on ? 'stop' : 'send');
  b.title = on ? '停止' : '发送';
  b.classList.toggle('stop', on);
}

function scheduleRender(bot) {
  if (AI.renderQueued) return;
  AI.renderQueued = true;
  requestAnimationFrame(() => {
    AI.renderQueued = false;
    renderBotNow(bot);
  });
}

function renderBotNow(bot) {
  if (AI.view !== 'chat' || !AI.open) return;
  const i = AI.msgs.indexOf(bot);
  const el = $(`#ai-body [data-i="${i}"]`);
  if (!el) return;
  const body = $('#ai-body');
  const stick = body.scrollHeight - body.scrollTop - body.clientHeight < 80;
  el.innerHTML = botHtml(bot, i);
  if (stick) body.scrollTop = body.scrollHeight;
}

function renderChat() {
  const body = $('#ai-body');
  if (!AI.msgs.length) {
    body.innerHTML = emptyHtml();
    return;
  }
  body.innerHTML = AI.msgs.map((m, i) => (m.role === 'user'
    ? `<div class="ai-msg user"><div class="ai-bubble">${esc(m.content)}</div>${m.ctxLabel ? `<div class="ai-about">${esc(m.ctxLabel)}</div>` : ''}</div>`
    : `<div class="ai-msg bot" data-i="${i}">${botHtml(m, i)}</div>`)).join('');
  body.scrollTop = body.scrollHeight;
}

function emptyHtml() {
  const p = activeProvider();
  let setup = '';
  if (!p) setup = '还没有配置模型服务商。';
  else if (!p.model) setup = `${esc(p.name)} 还没选模型。`;
  else if (!AI.cfg.keys[p.id] && !isLocalUrl(p.base_url)) setup = `${esc(p.name)} 还没填 API key。`;
  return `<div class="ai-empty">
    <div class="ai-hello">${ico('spark')}</div>
    <p>问当前打开的文档，或者让我在文档库里找资料${AI.cfg.web_search !== 'off' ? '、上网查' : ''}。回答会标出处，点一下就跳到原文那一页。</p>
    ${setup ? `<div class="notice">${setup}<button class="btn" data-ai="settings">去设置</button></div>` : ''}
    <div class="ai-sugs">${SUGGESTIONS.map(s => `<button data-ai="sug">${esc(s)}</button>`).join('')}</div>
  </div>`;
}

function botHtml(m, i) {
  const out = [];
  for (const part of m.parts) {
    if (part.type === 'tools') out.push(stepsHtml(part.items, m.live));
    else out.push(`<div class="ai-md md">${answerHtml(part.text, m)}</div>`);
  }
  const lastIsText = m.parts.length && m.parts[m.parts.length - 1].type === 'text';
  if (m.live && (m.status || !lastIsText)) {
    out.push(`<div class="ai-live"><span class="spinner"></span><span>${esc(m.status || (m.parts.length ? '整理中…' : '正在思考…'))}</span></div>`);
  }
  if (m.error) {
    const fix = /设置|key|模型|服务商|401|403|404/.test(m.error) ? '<button class="btn" data-ai="settings">打开设置</button>' : '';
    out.push(`<div class="ai-err">${ico('alert')}<span>${esc(m.error)}</span>${fix}</div>`);
  }
  if (m.stopped) out.push('<div class="ai-note">已停止</div>');
  if (!m.live && m.content) out.push(`<div class="ai-actions"><button class="btn small" data-ai="copy" data-i="${i}">${ico('copy')}<span>复制</span></button></div>`);
  return out.join('');
}

function stepsHtml(items, live) {
  const rows = items.map(it => `<div class="ai-step ${it.state}">${it.state === 'run' ? '<span class="spinner"></span>' : ico(it.state === 'ok' ? 'check' : 'alert')}<span class="lbl">${esc(it.label)}</span>${it.summary ? `<small>${esc(it.summary)}</small>` : ''}</div>`).join('');
  if (live) return `<div class="ai-steps">${rows}</div>`;
  const bad = items.filter(it => it.state === 'err').length;
  return `<details class="ai-steps"><summary>查阅了 ${items.length} 步${bad ? `（${bad} 步出错）` : ''}</summary>${rows}</details>`;
}

let AMD = null;
function answerMd() {
  if (AMD) return AMD;
  AMD = window.markdownit({
    html: false,
    linkify: true,
    highlight: (code, lang) => (lang && hljs.getLanguage(lang) ? hljs.highlight(code, { language: lang, ignoreIllegals: true }).value : ''),
  }).use(mathPlugin);
  AMD.renderer.rules.table_open = () => '<div class="table-wrap"><table>\n';
  AMD.renderer.rules.table_close = () => '</table></div>\n';
  AMD.renderer.rules.link_open = (tokens, i, opts, env, self) => {
    const t = tokens[i];
    const href = t.attrGet('href') || '';
    if (href.startsWith('doc:')) {
      const hashAt = href.indexOf('#');
      const raw = href.slice(4, hashAt < 0 ? undefined : hashAt);
      const path = raw.split('/').map(safeDecode).join('/');
      const frag = new URLSearchParams(hashAt < 0 ? '' : href.slice(hashAt + 1));
      const params = {};
      if (frag.get('page')) params.page = frag.get('page');
      if (frag.get('hl')) params.hl = frag.get('hl');
      t.attrSet('href', hashFor(path, params));
      t.attrSet('class', 'doc-link');
      t.attrSet('title', path + (params.page ? `，第 ${params.page} 页` : frag.get('line') ? `，第 ${frag.get('line')} 行` : ''));
    } else if (/^https?:/i.test(href)) {
      t.attrSet('target', '_blank');
      t.attrSet('rel', 'noopener noreferrer');
    }
    return self.renderToken(tokens, i, opts);
  };
  return AMD;
}

function answerHtml(text, m) {
  if (MATH_RE.test(text) && !window.katex) {
    // 公式渲染器还没加载：这一帧先显示原文，加载完再重画
    loadKatex().then(() => scheduleRender(m));
    return `<p style="white-space:pre-wrap">${esc(text)}</p>`;
  }
  return DOMPurify.sanitize(answerMd().render(text), { ADD_ATTR: ['target'] });
}

// ------------------------------------------------------------ 设置

function renderSettings() {
  const c = AI.cfg;
  const webOpts = [['off', '关闭'], ['tavily', 'Tavily（任何模型都能用，需要 Tavily 的 key）'],
    ...c.providers.map(p => [`responses:${p.id}`, `用「${p.name}」的内置网页搜索（Responses 接口）`])];
  $('#ai-body').innerHTML = `<div class="ai-set">
    <div class="ai-set-h"><button class="icon-btn" data-ai="back" title="返回对话">${ico('back')}</button><b>助手设置</b></div>
    <section>
      <h4>模型服务商</h4>
      <p class="ai-hint">使用 OpenAI 兼容接口（Chat Completions），需要模型支持工具调用。点选一行切换当前使用的服务商。</p>
      <div class="ai-provs">${c.providers.map(provRow).join('') || '<div class="ai-hint">还没有服务商</div>'}</div>
      <div id="ai-form"></div>
      <button class="btn" data-ai="add">${ico('plus')}<span>添加服务商</span></button>
    </section>
    <section>
      <h4>联网搜索</h4>
      <select id="ai-web">${webOpts.map(([v, l]) => `<option value="${esc(v)}"${v === c.web_search ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select>
      ${c.web_search === 'tavily' ? `<div class="ai-row"><input id="ai-tavily-key" type="password" autocomplete="off" placeholder="${c.keys.tavily ? `已保存 ${esc(c.keys.tavily)}，留空表示清除` : '粘贴 Tavily API key（tvly-…）'}"><button class="btn" data-ai="tavily-save">保存</button></div>` : ''}
      <p class="ai-hint">内置网页搜索由服务商在服务端完成，OpenAI 官方接口支持；其他兼容服务商多数没有这个接口，选 Tavily 更通用。打开网页只限对话、文档或搜索结果里出现过的网址。</p>
    </section>
    <section>
      <h4>不向 AI 开放</h4>
      <ul class="ai-ex"><li><code>data/</code>（仓库的真实数据目录，固定屏蔽）</li>${c.exclude.map(x => `<li><code>${esc(x)}</code></li>`).join('')}</ul>
      <p class="ai-hint">按仓库相对路径匹配，<code>*</code> 代表任意字符。在 config.json 的 <code>assistant.exclude</code> 里增删，改完重启文档库。被屏蔽的文件搜不到、读不了，打开它时选中的文字也不会发出。</p>
    </section>
    <p class="ai-hint">API key 只保存在本机：<code>${esc(c.keys_path)}</code></p>
  </div>`;
}

function provRow(p) {
  const c = AI.cfg;
  const keyText = c.keys[p.id] ? `key ${c.keys[p.id]}` : isLocalUrl(p.base_url) ? '本机，无需 key' : '未填 key';
  let host = p.base_url;
  try { host = new URL(p.base_url).host; } catch { /* 地址已由服务端校验，这里只为显示 */ }
  return `<div class="ai-prov${p.id === c.provider ? ' on' : ''}">
    <button class="ai-prov-main" data-ai="use" data-id="${esc(p.id)}"><span class="radio"></span>
      <span class="txt"><b>${esc(p.name)}</b><small>${esc(p.model || '未选模型')} · ${esc(host)}</small></span></button>
    <span class="ai-key${c.keys[p.id] ? ' ok' : ''}">${esc(keyText)}</span>
    <button class="icon-btn small" data-ai="edit" data-id="${esc(p.id)}" title="编辑">${ico('pen')}</button>
  </div>`;
}

function showForm(p) {
  const c = AI.cfg;
  const key = p && c.keys[p.id];
  $('#ai-form').innerHTML = `<form class="ai-form" data-id="${p ? esc(p.id) : ''}" autocomplete="off">
    ${p ? '' : `<label>类型<select name="preset">${PRESETS.map(([id, name]) => `<option value="${id}">${esc(name)}</option>`).join('')}</select></label>`}
    <label>名称<input name="name" required value="${esc(p ? p.name : PRESETS[0][1])}"></label>
    <label>接口地址（base URL）<input name="base_url" required value="${esc(p ? p.base_url : PRESETS[0][2])}" placeholder="https://…/v1"></label>
    <label>模型<span class="ai-row"><input name="model" list="ai-models" value="${esc(p ? p.model : '')}" placeholder="填写或点“获取列表”选择"><button type="button" class="btn" data-ai="models">获取列表</button></span></label>
    <datalist id="ai-models"></datalist>
    <label>API key<input name="key" type="password" placeholder="${key ? `已保存 ${esc(key)}，留空表示不修改` : '粘贴 API key；本机 Ollama 可不填'}"></label>
    <div class="ai-row">${p ? '<button type="button" class="btn danger" data-ai="del">删除</button>' : ''}<span class="sp"></span>
      <button type="button" class="btn" data-ai="cancel">取消</button><button type="submit" class="btn primary">保存</button></div>
  </form>`;
  $('#ai-form input[name="name"]').focus();
}

function applyPreset(form, id) {
  const [, name, url] = PRESETS.find(x => x[0] === id);
  form.name.value = id === 'custom' ? '' : name;
  form.base_url.value = url;
}

function newProviderId(preset) {
  const ids = new Set(AI.cfg.providers.map(p => p.id));
  let id = preset, n = 2;
  while (ids.has(id)) id = `${preset}-${n++}`;
  return id;
}

async function saveProvider(form, keepOpen) {
  const f = new FormData(form);
  const id = form.dataset.id || newProviderId(f.get('preset'));
  const prov = { id, name: f.get('name').trim(), base_url: f.get('base_url').trim(), model: f.get('model').trim() };
  const list = AI.cfg.providers.slice();
  const at = list.findIndex(p => p.id === id);
  if (at >= 0) list[at] = prov;
  else list.push(prov);
  AI.cfg = await post('/api/assistant/settings', {
    provider: AI.cfg.providers.some(p => p.id === AI.cfg.provider) ? AI.cfg.provider : id,
    providers: list,
    web_search: AI.cfg.web_search,
  });
  if (f.get('key').trim()) AI.cfg = await post('/api/assistant/key', { name: id, key: f.get('key') });
  form.dataset.id = id;
  updateHead();
  if (keepOpen) {
    form.key.value = '';
    return;
  }
  renderSettings();
  toast(`已保存 ${prov.name}`);
}

async function fetchModels(form) {
  if (!form.reportValidity()) return;
  await saveProvider(form, true);
  const btn = form.querySelector('[data-ai="models"]');
  btn.disabled = true;
  btn.textContent = '获取中…';
  try {
    const { models } = await post('/api/assistant/models', { provider: form.dataset.id });
    $('#ai-models').innerHTML = models.map(m => `<option value="${esc(m)}">`).join('');
    toast(`共 ${models.length} 个模型，在“模型”框里输入或点选`);
    form.model.focus();
  } finally {
    btn.disabled = false;
    btn.textContent = '获取列表';
  }
}

async function useProvider(id) {
  AI.cfg = await post('/api/assistant/settings', { provider: id, providers: AI.cfg.providers, web_search: AI.cfg.web_search });
  updateHead();
  renderSettings();
}

async function deleteProvider(id) {
  const p = AI.cfg.providers.find(x => x.id === id);
  if (!confirm(`删除服务商「${p.name}」？它保存的 API key 也会一并删除。`)) return;
  if (AI.cfg.keys[id]) AI.cfg = await post('/api/assistant/key', { name: id, key: '' });
  const list = AI.cfg.providers.filter(x => x.id !== id);
  AI.cfg = await post('/api/assistant/settings', {
    provider: AI.cfg.provider === id ? (list[0] ? list[0].id : '') : AI.cfg.provider,
    providers: list,
    web_search: AI.cfg.web_search === `responses:${id}` ? 'off' : AI.cfg.web_search,
  });
  updateHead();
  renderSettings();
}

async function setWeb(value) {
  AI.cfg = await post('/api/assistant/settings', { provider: AI.cfg.provider, providers: AI.cfg.providers, web_search: value });
  renderSettings();
}

async function saveKey(name, key) {
  AI.cfg = await post('/api/assistant/key', { name, key });
  renderSettings();
  toast(key.trim() ? '已保存 key' : '已清除 key');
}

buildAssistant();
