'use strict';
/* 研究文档浏览器前端：目录树、各类文件预览、搜索与目录管理。无构建步骤，第三方库都在 static/vendor。 */

// ------------------------------------------------------------ 小工具

const $ = (sel, el = document) => el.querySelector(sel);
const view = () => $('#view');
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const escRe = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const collator = new Intl.Collator('zh-Hans-CN', { numeric: true, sensitivity: 'base' });
const IS_MAC = /Mac|iPhone|iPad/.test(navigator.platform);
const ROOT_COLORS = ['#3b82f6', '#f97316', '#8b5cf6', '#10b981', '#ef4444', '#eab308', '#06b6d4', '#ec4899'];
const ROW_LIMIT = 3000;
const LINE_LIMIT = 6000;
const HL_LIMIT = 400_000;

const store = {
  get: (k, d) => { const v = localStorage.getItem('docb.' + k); return v === null ? d : JSON.parse(v); },
  set: (k, v) => localStorage.setItem('docb.' + k, JSON.stringify(v)),
};

const I = {
  home: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
  chev: '<path d="M9 6l6 6-6 6"/>',
  file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
  pages: '<path d="M8 3h7l4 4v11a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M15 3v4h4"/><path d="M3.5 7v12a2 2 0 0 0 2 2H14"/>',
  star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
  copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/>',
  reveal: '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5V12"/><path d="M3 7.5v10A2.5 2.5 0 0 0 5.5 20H11"/><circle cx="17" cy="16.5" r="3"/><path d="M21.5 21l-2.3-2.3"/>',
  open: '<path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
  app: '<rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M3 9h18"/><path d="M10 13.5l4 2.5-4 2.5z"/>',
  code: '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  history: '<path d="M3.5 12a8.5 8.5 0 1 0 2.5-6"/><path d="M3 4v4h4"/><path d="M12 8v4l3 2"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  up: '<path d="M6 15l6-6 6 6"/>',
  down: '<path d="M6 9l6 6 6-6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  auto: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/>',
};
const ico = (name, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true">${I[name]}</svg>`;
const FOLDER_PATH = '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5v8a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17.5z"/>';
const folderIco = color => `<svg class="i fold" style="--c:${color}" viewBox="0 0 24 24" aria-hidden="true">${FOLDER_PATH}</svg>`;

// 文件类别：决定颜色与分布条
const CATS = [
  ['md', 'Markdown', '#4f6bed', 'md markdown'],
  ['slide', '演示文稿', '#d9622b', 'pptx ppt pps ppsx odp key'],
  ['pdf', 'PDF', '#e5484d', 'pdf'],
  ['doc', 'Word', '#2f6fd6', 'docx doc odt rtf'],
  ['sheet', '表格', '#1f9d6b', 'xlsx xls ods csv tsv'],
  ['web', '网页', '#8b5cf6', 'html htm'],
  ['image', '图片', '#0ea5a5', 'png jpg jpeg gif webp bmp svg ico'],
  ['code', '代码与数据', '#64748b', 'py js mjs ts sh bat ps1 r sql json jsonl yaml yml toml xml ini cfg ipynb tex bib css'],
  ['text', '文本', '#94a3b8', 'txt log sha256 exit'],
];
const EXT_CAT = {};
for (const [k, , , exts] of CATS) for (const e of exts.split(' ')) EXT_CAT[e] = k;
const CAT = Object.fromEntries(CATS.map(([k, label, color]) => [k, { label, color }]));
CAT.other = { label: '其他', color: '#a1a1aa' };
const CAT_ORDER = [...CATS.map(c => c[0]), 'other'];

const extOf = name => { const i = name.lastIndexOf('.'); return i > 0 ? name.slice(i + 1).toLowerCase() : ''; };
const catOf = name => EXT_CAT[extOf(name)] || 'other';
const dirOf = p => p.slice(0, Math.max(0, p.lastIndexOf('/')));
const encPath = p => p.split('/').map(encodeURIComponent).join('/');
const rawUrl = p => '/raw/' + encPath(p);
const safeDecode = s => { try { return decodeURIComponent(s); } catch { return s; } }; // 文件名里本来就有 % 时保持原样

const LANG = {
  md: 'markdown', markdown: 'markdown', py: 'python', js: 'javascript', mjs: 'javascript', ts: 'typescript',
  sh: 'bash', bat: 'dos', ps1: 'powershell', r: 'r', sql: 'sql', json: 'json', jsonl: 'json', ipynb: 'json',
  yaml: 'yaml', yml: 'yaml', toml: 'ini', ini: 'ini', cfg: 'ini', xml: 'xml', svg: 'xml', tex: 'latex', css: 'css',
};

function viewerKind(name) {
  if (S.forceText) return 'code';
  const e = extOf(name);
  if (e === 'md' || e === 'markdown') return 'markdown';
  if (e === 'pdf') return 'pdf';
  if (e === 'docx') return S.docxPdf ? 'convert' : 'docx';
  if (['pptx', 'ppt', 'pps', 'ppsx', 'odp', 'doc', 'odt', 'rtf'].includes(e)) return 'convert';
  if (['xlsx', 'xls', 'ods'].includes(e)) return 'sheet';
  if (e === 'csv' || e === 'tsv') return 'csv';
  if (e === 'html' || e === 'htm') return 'html';
  if (catOf(name) === 'image') return 'image';
  if (['code', 'text'].includes(catOf(name))) return 'code';
  return 'other';
}
const FULL_KINDS = new Set(['pdf', 'convert', 'html']);

function relTime(ms) {
  if (!ms) return '';
  const d = (Date.now() - ms) / 1000;
  if (d < 60) return '刚刚';
  if (d < 3600) return Math.floor(d / 60) + ' 分钟前';
  if (d < 86400) return Math.floor(d / 3600) + ' 小时前';
  if (d < 86400 * 7) return Math.floor(d / 86400) + ' 天前';
  return fullTime(ms).slice(0, 10);
}
function fullTime(ms) {
  const t = new Date(ms), p = n => String(n).padStart(2, '0');
  return `${t.getFullYear()}-${p(t.getMonth() + 1)}-${p(t.getDate())} ${p(t.getHours())}:${p(t.getMinutes())}`;
}
function shortDate(ms) {
  const s = fullTime(ms).slice(0, 10);
  return s.startsWith(String(new Date().getFullYear())) ? s.slice(5) : s;
}
function fmtSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1024 * 1024) return (b / 1024).toFixed(b < 10240 ? 1 : 0) + ' KB';
  return (b / 1024 / 1024).toFixed(1) + ' MB';
}

function badge(name, big) {
  const e = extOf(name);
  return `<span class="badge${big ? ' big' : ''}" style="--c:${CAT[catOf(name)].color}">${esc((e || '文件').slice(0, 4).toUpperCase())}</span>`;
}
const fileIco = name => `<svg class="i fico" style="--c:${CAT[catOf(name)].color}" viewBox="0 0 24 24" aria-hidden="true">${I.file}</svg>`;
const nodeIco = n => (n.d ? folderIco(n.root.color) : badge(n.n));
const loadingBox = msg => `<div class="loading"><span class="spinner"></span><span>${msg}</span></div>`;
const errorBox = (title, msg) => `<div class="error-box"><b>${esc(title)}</b>${esc(msg)}</div>`;
const actBtn = (act, icon, label, withText) =>
  `<button class="btn" data-act="${act}" title="${esc(label)}">${ico(icon)}${withText ? `<span>${esc(label)}</span>` : ''}</button>`;

function hlText(text, terms) {
  if (!terms.length) return esc(text);
  const re = new RegExp('(' + terms.map(escRe).join('|') + ')', 'gi');
  return text.split(re).map((s, i) => (i % 2 ? `<mark>${esc(s)}</mark>` : esc(s))).join('');
}

let toastTimer = 0;
function toast(msg, isErr) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.toggle('err', !!isErr);
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), isErr ? 5000 : 2200);
}

const loaded = new Map();
function loadScript(src) {
  if (!loaded.has(src)) {
    loaded.set(src, new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = () => reject(new Error('脚本加载失败：' + src));
      document.head.appendChild(s);
    }));
  }
  return loaded.get(src);
}
function loadKatex() {
  if (!$('link[data-katex]')) document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" data-katex href="/static/vendor/katex/katex.min.css">');
  return loadScript('/static/vendor/katex/katex.min.js');
}

// ------------------------------------------------------------ 与服务端通信

async function api(url, opts) {
  const r = await fetch(url, opts);
  const isJson = (r.headers.get('content-type') || '').includes('json');
  const body = isJson ? await r.json() : await r.text();
  if (!r.ok) throw new Error(isJson ? body.error : `${r.status} ${body}`);
  return body;
}
const post = (url, data) => api(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'X-Doc-Browser': '1' },
  body: JSON.stringify(data),
});
async function fetchRaw(p) {
  const r = await fetch(rawUrl(p));
  if (!r.ok) throw new Error((await r.json()).error);
  return r;
}
async function fetchText(p) {
  const buf = await (await fetchRaw(p)).arrayBuffer();
  try {
    return { text: new TextDecoder('utf-8', { fatal: true }).decode(buf), enc: 'UTF-8' };
  } catch {
    // 医院导出的 CSV 常是 GBK；解码方式会在页面上注明
    return { text: new TextDecoder('gb18030').decode(buf), enc: 'GB18030' };
  }
}
const encNotice = enc => (enc === 'UTF-8' ? '' : `<div class="notice">文件不是 UTF-8 编码，按 ${enc} 解码显示</div>`);

// ------------------------------------------------------------ 状态

const S = {
  cfg: null,
  repo: '',
  roots: [],
  nodes: new Map(),
  files: [],
  treeText: '',
  loadedAt: 0,
  route: { path: null, params: new URLSearchParams() },
  tok: 0,
  expanded: new Set(store.get('expanded', [])),
  sort: store.get('sort', { key: 'name', dir: 1 }),
  scroll: new Map(),
  pushNav: false,
  mdSource: false,
  docxPdf: false,
  forceText: false,
  showAll: false,
  toc: null,
  hl: null,
  searchMode: store.get('searchMode', 'name'),
  lastQuery: '',
  desc: new Map(),
};

const pins = () => store.get('pins', []);
function addRecent(p) {
  const list = store.get('recent', []).filter(x => x.p !== p);
  list.unshift({ p, t: Date.now() });
  store.set('recent', list.slice(0, 40));
}

async function loadTree() {
  const r = await fetch('/api/tree');
  const text = await r.text();
  if (!r.ok) throw new Error(JSON.parse(text).error);
  S.loadedAt = Date.now();
  if (text === S.treeText) return false;
  S.treeText = text;
  const data = JSON.parse(text);
  S.repo = data.repo;
  S.nodes = new Map();
  S.files = [];
  S.roots = data.roots.map((root, i) => {
    root.color = ROOT_COLORS[i % ROOT_COLORS.length];
    indexNode(root, null, root);
    return root;
  });
  return true;
}

function indexNode(n, parent, root) {
  n.parent = parent;
  n.root = root;
  S.nodes.set(n.p, n);
  if (!n.d) {
    S.files.push(n);
    return;
  }
  n.c.sort((a, b) => (b.d | 0) - (a.d | 0) || collator.compare(a.n, b.n));
  let files = 0, dirs = 0, m = 0;
  const cats = {};
  for (const c of n.c) {
    indexNode(c, n, root);
    m = Math.max(m, c.m);
    if (c.d) {
      dirs += 1 + c.dirs;
      files += c.files;
      for (const k in c.cats) cats[k] = (cats[k] || 0) + c.cats[k];
    } else {
      files += 1;
      const k = catOf(c.n);
      cats[k] = (cats[k] || 0) + 1;
    }
  }
  Object.assign(n, { files, dirs, m, cats });
}

function catBar(cats, thin) {
  const segs = CAT_ORDER.filter(k => cats[k]).map(k =>
    `<span style="--c:${CAT[k].color};flex:${cats[k]}" title="${CAT[k].label} ${cats[k]}"></span>`);
  return `<div class="catbar${thin ? ' thin' : ''}">${segs.join('')}</div>`;
}
function legend(cats, max) {
  return `<div class="legend">${CAT_ORDER.filter(k => cats[k]).sort((a, b) => cats[b] - cats[a]).slice(0, max)
    .map(k => `<span><i style="--c:${CAT[k].color}"></i>${CAT[k].label} ${cats[k]}</span>`).join('')}</div>`;
}

// ------------------------------------------------------------ 路由

function hashFor(path, params) {
  const q = params ? new URLSearchParams(params).toString() : '';
  return '#/p/' + encPath(path) + (q ? '?' + q : '');
}
function parseHash() {
  const h = location.hash.slice(1);
  if (!h.startsWith('/p/') || h === '/p/') return { path: null, params: new URLSearchParams() };
  const rest = h.slice(3);
  const qi = rest.indexOf('?');
  const raw = qi < 0 ? rest : rest.slice(0, qi);
  return { path: raw.split('/').map(safeDecode).join('/'), params: new URLSearchParams(qi < 0 ? '' : rest.slice(qi + 1)) };
}
function go(path, params) {
  S.pushNav = true;
  const h = hashFor(path, params);
  if (location.hash === h) route();
  else location.hash = h;
}

async function route() {
  if (S.route) S.scroll.set(S.route.path ?? '/', view().scrollTop);
  const r = parseHash();
  if (r.path !== S.route.path) Object.assign(S, { mdSource: false, docxPdf: false, forceText: false, showAll: false });
  S.route = r;
  const tok = ++S.tok;
  S.toc = null;
  hideHlBar();
  document.body.classList.remove('side-open');
  $('#home-link').classList.toggle('cur', r.path === null);
  view().scrollTop = 0;
  try {
    if (r.path === null) {
      renderTree();
      renderHome();
    } else {
      let n = S.nodes.get(r.path);
      // 文件可能是刚新建的：重新扫描一次再判断
      if (!n && Date.now() - S.loadedAt > 1000 && await loadTree()) n = S.nodes.get(r.path);
      if (tok !== S.tok) return;
      if (!n) {
        renderTree();
        await renderMissing(r.path, tok);
        return;
      }
      expandTo(n);
      renderTree();
      if (n.d) await renderFolder(n, tok);
      else await renderFile(n, tok);
    }
  } catch (e) {
    if (tok === S.tok) view().innerHTML = `<div class="page">${errorBox('出错了', e.message)}</div>`;
    return;
  }
  if (tok !== S.tok) return;
  const a = r.params.get('a');
  if (a) scrollToId(a);
  else if (!S.pushNav && !r.params.get('hl')) view().scrollTop = S.scroll.get(r.path ?? '/') || 0;
  S.pushNav = false;
}

function setTitle(t) { document.title = `${t} · 文档库`; }
function setCrumbs(n) {
  const chain = [];
  for (let x = n; x; x = x.parent) chain.unshift(x);
  const label = x => esc(x === x.root ? x.p : x.n);
  $('#crumbs').innerHTML = `<a href="#/" title="首页">${ico('home')}</a>` + chain.map((x, i) =>
    `<span class="sep">${ico('chev')}</span>` + (i === chain.length - 1
      ? `<span class="last" title="${esc(x.p)}">${label(x)}</span>`
      : `<a href="${hashFor(x.p)}" title="${esc(x.p)}">${label(x)}</a>`)).join('');
}
function scrollToId(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ block: 'start' });
  else toast('页面里没有这个位置：#' + id, true);
}

// ------------------------------------------------------------ 目录树

function expandTo(n) {
  for (let x = n.d ? n : n.parent; x; x = x.parent) S.expanded.add(x.p);
  store.set('expanded', [...S.expanded]);
}
function toggleDir(p) {
  if (S.expanded.has(p)) S.expanded.delete(p);
  else S.expanded.add(p);
  store.set('expanded', [...S.expanded]);
  renderTree();
}
function renderTree() {
  const out = [];
  const cur = S.route.path;
  const walk = (n, depth) => {
    const on = cur === n.p ? ' cur' : '';
    if (n.d) {
      const open = S.expanded.has(n.p);
      out.push(`<div class="row dir${on}${depth ? '' : ' root'}" data-p="${esc(n.p)}" style="--d:${depth}" title="${esc(n.p)}">`
        + `<span class="tw${open ? ' open' : ''}">${ico('chev')}</span>${folderIco(n.root.color)}`
        + `<span class="nm">${esc(depth ? n.n : n.p)}</span><span class="ct">${n.files}</span></div>`);
      if (open) for (const c of n.c) walk(c, depth + 1);
    } else {
      out.push(`<div class="row file${on}" data-p="${esc(n.p)}" style="--d:${depth}" title="${esc(n.n)}">`
        + `<span class="tw"></span>${fileIco(n.n)}<span class="nm">${esc(n.n)}</span></div>`);
    }
  };
  for (const root of S.roots) walk(root, 0);
  const tree = $('#tree');
  tree.innerHTML = out.join('');
  const curRow = $('.row.cur', tree);
  if (curRow) {
    const a = curRow.getBoundingClientRect(), b = tree.getBoundingClientRect();
    if (a.top < b.top || a.bottom > b.bottom) tree.scrollTop += a.top - b.top - b.height / 2;
  }
}

// ------------------------------------------------------------ 首页

function renderHome() {
  setTitle('首页');
  $('#crumbs').innerHTML = `<a href="#/">${ico('home')}</a><span class="sep">${ico('chev')}</span><span class="last">首页</span>`;
  const latest = Math.max(0, ...S.roots.map(r => r.m));
  const recentModified = [...S.files].sort((a, b) => b.m - a.m).slice(0, 14).map(n => ({ n, t: n.m }));
  const viewed = store.get('recent', []).map(x => ({ n: S.nodes.get(x.p), t: x.t })).filter(x => x.n).slice(0, 8);
  const pinned = pins().map(p => S.nodes.get(p)).filter(Boolean).map(n => ({ n, t: n.m }));
  view().innerHTML = `<div class="page home">
    <header class="hero"><h1>研究文档库</h1>
      <p class="muted">${S.roots.length} 个目录 · ${S.files.length} 个文件${latest ? ` · 最近更新 ${relTime(latest)}` : ''}</p></header>
    <section class="root-grid">${S.roots.map(rootCard).join('')}</section>
    <div class="home-cols">
      <section class="panel"><h2>${ico('clock')}最近修改</h2>${fileRows(recentModified, '没有文件')}</section>
      <div class="panel-stack">
        <section class="panel"><h2>${ico('star')}收藏</h2>${fileRows(pinned, '在文件页点星标即可收藏')}</section>
        <section class="panel"><h2>${ico('history')}最近查看</h2>${fileRows(viewed, '还没有查看记录')}</section>
      </div>
    </div>
  </div>`;
  for (const root of S.roots) loadRootDesc(root);
}

function rootCard(r) {
  return `<a class="root-card" href="${hashFor(r.p)}" style="--c:${r.color}">
    <div class="rc-top">${folderIco(r.color)}<span class="rc-name">${esc(r.p)}</span><span class="rc-count">${r.files} 个文件</span></div>
    <p class="rc-desc" data-desc="${esc(r.p)}"></p>
    ${catBar(r.cats)}${legend(r.cats, 4)}
    <div class="rc-foot">${r.dirs} 个子目录${r.m ? ` · 更新于 ${relTime(r.m)}` : ''}</div>
  </a>`;
}

function fileRows(items, emptyText) {
  if (!items.length) return `<div class="empty">${emptyText}</div>`;
  return items.map(({ n, t }) => `<a class="fl-row" href="${hashFor(n.p)}">${nodeIco(n)}
    <div class="fl-main"><div class="fl-name" title="${esc(n.n)}">${esc(n.n)}</div><div class="fl-dir">${esc(dirOf(n.p))}</div></div>
    <span class="fl-time" title="${fullTime(t)}">${relTime(t)}</span></a>`).join('');
}

// 目录卡片上的一句话简介取自该目录 README 的第一段
async function loadRootDesc(root) {
  const readme = root.c.find(c => !c.d && /^readme\.md$/i.test(c.n));
  if (!readme) return;
  const key = readme.p + '@' + readme.m;
  if (!S.desc.has(key)) S.desc.set(key, fetchText(readme.p).then(({ text }) => firstParagraph(text)));
  const desc = await S.desc.get(key);
  const el = document.querySelector(`[data-desc="${CSS.escape(root.p)}"]`);
  if (el) el.textContent = desc;
}
function firstParagraph(md) {
  const out = [];
  for (const line of md.split(/\r?\n/)) {
    const t = line.trim();
    const skip = !t || /^(#|\||>|-{3,}|```|<|!\[)/.test(t);
    if (skip) {
      if (out.length) break;
      continue;
    }
    out.push(t);
  }
  return out.join(' ').replace(/!?\[([^\]]*)\]\([^)]*\)/g, '$1').replace(/[*_`]/g, '');
}

// ------------------------------------------------------------ 目录页

const OPEN_DIR_LABEL = IS_MAC ? '在 Finder 中打开' : '在资源管理器中打开';
const REVEAL_LABEL = IS_MAC ? '在 Finder 中显示' : '在资源管理器中显示';

function sortFiles(files) {
  const { key, dir } = S.sort;
  const cmp = key === 'name' ? (a, b) => collator.compare(a.n, b.n) : (a, b) => a[key] - b[key] || collator.compare(a.n, b.n);
  return [...files].sort((a, b) => cmp(a, b) * dir);
}

async function renderFolder(n, tok) {
  setTitle(n.n);
  setCrumbs(n);
  const dirs = n.c.filter(c => c.d);
  const files = sortFiles(n.c.filter(c => !c.d));
  const readme = n.c.find(c => !c.d && /^readme\.(md|markdown)$/i.test(c.n));
  const arrow = k => (S.sort.key === k ? `<span class="arrow">${S.sort.dir > 0 ? '↑' : '↓'}</span>` : '');
  view().innerHTML = `<div class="page folder">
    <header class="fhead">
      <div class="fh-ico" style="--c:${n.root.color}">${folderIco(n.root.color)}</div>
      <div class="fh-main"><h1>${esc(n === n.root ? n.p : n.n)}</h1>
        <div class="meta"><span>${dirs.length ? `${dirs.length} 个子目录 · ` : ''}共 ${n.files} 个文件</span>
          ${n.m ? `<span title="${fullTime(n.m)}">更新于 ${relTime(n.m)}</span>` : ''}<span class="path">${esc(n.p)}/</span></div>
        ${n.files ? `<div style="margin-top:10px;max-width:420px">${catBar(n.cats, true)}</div>` : ''}</div>
      <div class="actions">${actBtn('copy', 'copy', '复制路径')}${actBtn('open', 'reveal', OPEN_DIR_LABEL, true)}</div>
    </header>
    ${dirs.length ? `<div class="section-h">子目录</div><div class="dir-grid">${dirs.map(dirCard).join('')}</div>` : ''}
    ${files.length ? `<div class="section-h">文件</div>
      <table class="ftable"><thead><tr><th data-sort="name">名称${arrow('name')}</th>
        <th class="w-time num" data-sort="m">修改时间${arrow('m')}</th><th class="w-size num" data-sort="s">大小${arrow('s')}</th></tr></thead>
      <tbody>${files.map(f => `<tr data-go="${esc(f.p)}"><td><a class="c-name" href="${hashFor(f.p)}">${badge(f.n)}<span>${esc(f.n)}</span></a></td>
        <td class="num" title="${fullTime(f.m)}">${relTime(f.m)}</td><td class="num size">${fmtSize(f.s)}</td></tr>`).join('')}</tbody></table>` : ''}
    ${!dirs.length && !files.length ? '<div class="empty">空目录</div>' : ''}
    ${readme ? `<section class="readme"><div class="readme-h">${ico('file')}<span>${esc(readme.n)}</span><a href="${hashFor(readme.p)}">单独打开</a></div>
      <article class="md" id="readme-md">${loadingBox('读取中…')}</article></section>` : ''}
  </div>`;
  if (!readme) return;
  const { text } = await fetchText(readme.p);
  if (tok !== S.tok) return;
  await renderMarkdown($('#readme-md'), text, n.p, readme.p);
}

function dirCard(d) {
  return `<a class="dir-card" href="${hashFor(d.p)}" style="--c:${d.root.color}">
    <div class="dc-top">${folderIco(d.root.color)}<span class="dc-name" title="${esc(d.n)}">${esc(d.n)}</span></div>
    <div class="dc-meta">${d.dirs ? `${d.dirs} 个子目录 · ` : ''}${d.files} 个文件${d.m ? ` · ${shortDate(d.m)}` : ''}</div>
    ${catBar(d.cats, true)}</a>`;
}

// ------------------------------------------------------------ 文件页

async function renderFile(n, tok) {
  setTitle(n.n);
  setCrumbs(n);
  addRecent(n.p);
  const kind = viewerKind(n.n);
  view().innerHTML = `<div class="page file${FULL_KINDS.has(kind) ? ' full' : ''}">${fileHeader(n, kind)}<div class="fbody" id="fbody"></div></div>`;
  const ctx = { tok, alive: () => tok === S.tok, params: S.route.params };
  const body = $('#fbody');
  try {
    await VIEWERS[kind](body, n, ctx);
  } catch (e) {
    if (ctx.alive()) body.innerHTML = errorBox('无法预览', e.message);
  }
}

function fileHeader(n, kind) {
  const ext = extOf(n.n);
  const pinned = pins().includes(n.p);
  const extra = [];
  if (kind === 'markdown' || (S.forceText && ext === 'md')) {
    extra.push(`<button class="btn${S.mdSource ? ' on' : ''}" data-act="src">${ico('code')}<span>源码</span></button>`);
  }
  if (ext === 'docx') extra.push(`<button class="btn${S.docxPdf ? ' on' : ''}" data-act="docx-pdf" title="用 LibreOffice 转成 PDF，版式更准">${ico('pages')}<span>PDF 版式</span></button>`);
  if (['pdf', 'html', 'image'].includes(kind)) extra.push(actBtn('tab', 'open', '新标签页打开', true));
  return `<header class="fhead">
    <div class="fh-ico" style="--c:${CAT[catOf(n.n)].color}">${badge(n.n, true)}</div>
    <div class="fh-main"><h1>${esc(n.n)}</h1>
      <div class="meta"><span class="path">${esc(dirOf(n.p))}/</span><span>${fmtSize(n.s)}</span>
        <span>修改于 ${fullTime(n.m)}（${relTime(n.m)}）</span></div></div>
    <div class="actions">${extra.join('')}
      <button class="btn star${pinned ? ' on' : ''}" data-act="pin" title="${pinned ? '取消收藏' : '收藏'}">${ico('star')}</button>
      ${actBtn('copy', 'copy', '复制路径')}${actBtn('reveal', 'reveal', REVEAL_LABEL)}${actBtn('open', 'app', '用默认程序打开', true)}</div>
  </header>`;
}

function siblingNav(n) {
  const sibs = n.parent.c.filter(c => !c.d);
  const i = sibs.indexOf(n);
  const prev = sibs[i - 1], next = sibs[i + 1];
  if (!prev && !next) return '';
  return `<nav class="sib-nav">
    ${prev ? `<a class="sib prev" href="${hashFor(prev.p)}"><small>← 上一个</small><span>${esc(prev.n)}</span></a>` : ''}
    ${next ? `<a class="sib next" href="${hashFor(next.p)}"><small>下一个 →</small><span>${esc(next.n)}</span></a>` : ''}</nav>`;
}

const PDFJS_VIEWER = '/static/vendor/pdfjs/web/viewer.html';
const SLIDE_EXTS = new Set(['pptx', 'ppt', 'pps', 'ppsx', 'odp']);

// PDF.js 的阅读器通过网址 # 部分接收页码、缩放和要高亮的词
function pdfViewer(body, file, n, ctx) {
  const h = new URLSearchParams();
  const page = ctx.params.get('page');
  if (page) h.set('page', page);
  // LibreOffice 转出的 PDF 会要求打开大纲，幻灯片的大纲只有“Slide N”，换成缩略图；窄窗口里侧栏会盖住页面，不打开
  const wide = body.clientWidth >= 900;
  if (SLIDE_EXTS.has(extOf(n.n))) {
    h.set('zoom', 'page-fit');
    h.set('pagemode', wide ? 'thumbs' : 'none');
  } else if (!wide) {
    h.set('pagemode', 'none');
  }
  const hl = ctx.params.get('hl');
  if (hl) h.set('search', hl);
  const pin = page && hl ? ` data-pin-page="${+page}"` : '';
  body.innerHTML = `<iframe class="frame pdfjs" src="${PDFJS_VIEWER}?file=${encodeURIComponent(file)}#${h}" title="${esc(n.n)}"${pin} allowfullscreen></iframe>`;
}

// 同时给了页码和高亮词时以页码为准（搜索结果和 AI 引用都指向“第 N 页”）。PDF.js 会把第一处匹配
// 滚到视口最上沿：匹配在别的页时要拉回来；幻灯片按整页显示时，匹配在页面下部也会把视图推成大半个下一页。
// 所以除了“匹配就在这一页、而且页面比视口高”的情况，都回到这一页的整页视图，匹配照样高亮。
// 只管打开时这一次，之后用户自己搜索不受影响。
function pinPdfPage(app, page) {
  app.initializedPromise.then(() => {
    const onState = ev => {
      if (ev.state === 3) return; // FindState.PENDING
      app.eventBus.off('updatefindcontrolstate', onState);
      const fc = app.findController;
      if (fc.selected.pageIdx === page - 1 && app.pdfViewer.currentScaleValue !== 'page-fit') return;
      // 等 PDF.js 这一轮跳页做完再拉回；关掉 _scrollMatches，免得匹配页的文字层画好后又滚过去
      setTimeout(() => { fc._scrollMatches = false; app.page = page; });
    };
    app.eventBus.on('updatefindcontrolstate', onState);
  });
}

// PDF.js 在框架里启动前会向上层页面发这个事件，此时它还没读取设置
document.addEventListener('webviewerloaded', e => {
  const opts = e.detail.source.PDFViewerApplicationOptions;
  opts.set('disablePreferences', true);
  opts.set('externalLinkTarget', 2); // 文档里的外链开新标签页，不把文档库整页换掉
  opts.set('viewerCssTheme', { auto: 0, light: 1, dark: 2 }[store.get('theme', 'auto')]);
  const pin = +e.detail.source.frameElement.dataset.pinPage;
  if (pin) pinPdfPage(e.detail.source.PDFViewerApplication, pin);
});

const VIEWERS = {
  async markdown(body, n, ctx) {
    const { text, enc } = await fetchText(n.p);
    if (!ctx.alive()) return;
    if (S.mdSource) return showCode(body, n, text, 'markdown', enc, ctx);
    body.innerHTML = `${encNotice(enc)}<div class="md-layout"><article class="md" id="md"></article><nav class="toc" id="toc"></nav></div>${siblingNav(n)}`;
    const md = $('#md', body);
    await renderMarkdown(md, text, dirOf(n.p), n.p);
    if (!ctx.alive()) return;
    buildToc(md, $('#toc', body));
    highlightParam(md, ctx);
  },

  pdf(body, n, ctx) {
    pdfViewer(body, rawUrl(n.p), n, ctx);
  },

  async convert(body, n, ctx) {
    body.innerHTML = loadingBox(`正在用 LibreOffice 把 ${esc(extOf(n.n).toUpperCase())} 转成 PDF。每个文件第一次打开要十几秒，之后直接读缓存。`);
    const url = '/api/convert?path=' + encodeURIComponent(n.p);
    await api(url + '&check=1');
    if (!ctx.alive()) return;
    pdfViewer(body, url, n, ctx);
  },

  async docx(body, n, ctx) {
    body.innerHTML = loadingBox('正在渲染 Word 文档…');
    await loadScript('/static/vendor/jszip.min.js');
    await loadScript('/static/vendor/docx-preview.min.js');
    const buf = await (await fetchRaw(n.p)).arrayBuffer();
    if (!ctx.alive()) return;
    body.innerHTML = '<div class="notice">浏览器内渲染，版式可能和 Word 略有出入；点上方“PDF 版式”可看 LibreOffice 排版结果。</div><div class="docx-host"></div>';
    await window.docx.renderAsync(buf, $('.docx-host', body), null, {
      className: 'docx', inWrapper: true, breakPages: true, ignoreLastRenderedPageBreak: true, useBase64URL: true,
    });
    highlightParam($('.docx-host', body), ctx);
  },

  async sheet(body, n, ctx) {
    body.innerHTML = loadingBox('正在读取表格…');
    await loadScript('/static/vendor/xlsx.full.min.js');
    const buf = await (await fetchRaw(n.p)).arrayBuffer();
    if (!ctx.alive()) return;
    showWorkbook(body, window.XLSX.read(buf, { type: 'array' }), ctx);
  },

  async csv(body, n, ctx) {
    const { text, enc } = await fetchText(n.p);
    if (!ctx.alive()) return;
    showTable(body, parseDelimited(text, extOf(n.n) === 'tsv' ? '\t' : ','), enc, ctx);
  },

  html(body, n) {
    body.innerHTML = `<iframe class="frame" sandbox="allow-scripts allow-popups allow-forms allow-modals" src="${rawUrl(n.p)}" title="${esc(n.n)}"></iframe>`;
  },

  image(body, n) {
    body.innerHTML = `<div class="img-view"><img src="${rawUrl(n.p)}" alt="${esc(n.n)}" title="点击切换原始大小"></div>`;
  },

  async code(body, n, ctx) {
    if (n.s > 50 * 1024 * 1024) {
      body.innerHTML = `<div class="info-card">${badge(n.n, true)}<div>文件有 ${fmtSize(n.s)}，太大，不在浏览器里显示。</div></div>`;
      return;
    }
    const { text, enc } = await fetchText(n.p);
    if (!ctx.alive()) return;
    showCode(body, n, text, LANG[extOf(n.n)], enc, ctx);
  },

  other(body, n) {
    body.innerHTML = `<div class="info-card">${badge(n.n, true)}
      <div>这种文件（${extOf(n.n) ? '.' + esc(extOf(n.n)) : '无扩展名'}）没有内置预览。</div>
      <div class="actions">${actBtn('open', 'app', '用默认程序打开', true)}${actBtn('reveal', 'reveal', REVEAL_LABEL, true)}
        <button class="btn" data-act="as-text">${ico('code')}<span>按文本查看</span></button></div></div>`;
  },
};

function showCode(body, n, text, lang, enc, ctx) {
  const notes = [];
  if (enc !== 'UTF-8') notes.push(`文件不是 UTF-8 编码，按 ${enc} 解码显示`);
  let shown = text;
  if (extOf(n.n) === 'json' && text.length > 300 && text.trimEnd().split('\n').length <= 2) {
    try {
      shown = JSON.stringify(JSON.parse(text), null, 2);
      notes.push('原文件是单行 JSON，这里格式化后显示');
    } catch (e) {
      notes.push('JSON 解析失败，按原文显示：' + esc(e.message));
    }
  }
  let lines = shown.split('\n');
  if (lines.length > LINE_LIMIT && !S.showAll) {
    notes.push(`共 ${lines.length} 行，只显示前 ${LINE_LIMIT} 行 <button class="btn" data-act="show-all">显示全部</button>`);
    lines = lines.slice(0, LINE_LIMIT);
    shown = lines.join('\n');
  }
  let html;
  if (lang && hljs.getLanguage(lang) && shown.length <= HL_LIMIT) {
    html = hljs.highlight(shown, { language: lang, ignoreIllegals: true }).value;
  } else {
    html = esc(shown);
    if (lang && shown.length > HL_LIMIT) notes.push('内容较长，没有做语法高亮');
  }
  body.innerHTML = notes.map(x => `<div class="notice">${x}</div>`).join('')
    + `<div class="code-view"><pre class="gutter">${lines.map((_, i) => i + 1).join('\n')}</pre><pre class="code"><code class="hljs">${html}</code></pre></div>`;
  highlightParam($('.code', body), ctx);
}

// RFC 4180 风格的 CSV：支持引号内的逗号、换行和双引号转义
function parseDelimited(text, delim) {
  const rows = [];
  let row = [], cell = '', quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') { cell += '"'; i++; } else quoted = false;
      } else cell += ch;
    } else if (ch === '"' && cell === '') quoted = true;
    else if (ch === delim) { row.push(cell); cell = ''; }
    else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); rows.push(row); row = []; cell = '';
    } else cell += ch;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  return rows;
}

function showTable(body, rows, enc, ctx) {
  const head = rows[0] || [];
  const data = rows.slice(1);
  let ncol = 0;
  for (const r of rows) ncol = Math.max(ncol, r.length);
  const cols = [...Array(ncol).keys()];
  const NUM = /^[-+]?(\d[\d,]*)?(\.\d+)?([eE][-+]?\d+)?%?$/;
  const numeric = cols.map(c => {
    const vals = data.slice(0, 300).map(r => r[c]).filter(v => v !== undefined && v !== '');
    return vals.length > 0 && vals.every(v => NUM.test(v.trim()));
  });
  const shown = S.showAll ? data : data.slice(0, ROW_LIMIT);
  const cell = (v, c) => {
    const s = v ?? '';
    return `<td${numeric[c] ? ' class="r"' : ''}${s.length > 40 ? ` title="${esc(s)}"` : ''}>${esc(s)}</td>`;
  };
  const notes = [encNotice(enc), `<div class="notice">${data.length} 行 × ${ncol} 列（第一行作表头）${shown.length < data.length
    ? ` · 只显示前 ${ROW_LIMIT} 行 <button class="btn" data-act="show-all">显示全部</button>` : ''}</div>`];
  body.innerHTML = notes.join('') + `<div class="sheet-wrap"><table>
    <thead><tr><th class="rn">#</th>${cols.map(c => `<th>${esc(head[c] ?? '')}</th>`).join('')}</tr></thead>
    <tbody>${shown.map((r, i) => `<tr><td class="rn">${i + 1}</td>${cols.map(c => cell(r[c], c)).join('')}</tr>`).join('')}</tbody></table></div>`;
  highlightParam($('.sheet-wrap', body), ctx);
}

function showWorkbook(body, wb, ctx) {
  const XLSX = window.XLSX;
  const names = wb.SheetNames;
  body.innerHTML = `${names.length > 1 ? `<div class="sheet-tabs">${names.map((s, i) => `<button data-sheet="${i}">${esc(s)}</button>`).join('')}</div>` : ''}
    <div id="sheet-note"></div><div class="sheet-wrap xl" id="sheet"></div>`;
  const show = (i, all) => {
    body.querySelectorAll('[data-sheet]').forEach(b => b.classList.toggle('on', +b.dataset.sheet === i));
    const ws = wb.Sheets[names[i]];
    let note = '';
    let shown = ws;
    if (ws['!ref']) {
      const r = XLSX.utils.decode_range(ws['!ref']);
      const rows = r.e.r - r.s.r + 1;
      note = `${names.length > 1 ? `工作表“${esc(names[i])}”：` : ''}${rows} 行 × ${r.e.c - r.s.c + 1} 列`;
      if (rows > ROW_LIMIT && !all) {
        shown = { ...ws, '!ref': XLSX.utils.encode_range({ s: r.s, e: { r: r.s.r + ROW_LIMIT - 1, c: r.e.c } }) };
        note += ` · 只显示前 ${ROW_LIMIT} 行 <button class="btn" data-all="${i}">显示全部</button>`;
      }
    }
    $('#sheet-note', body).innerHTML = note ? `<div class="notice">${note}</div>` : '';
    $('#sheet', body).innerHTML = ws['!ref']
      ? DOMPurify.sanitize(XLSX.utils.sheet_to_html(shown, { header: '', footer: '' }))
      : '<div class="empty">空工作表</div>';
    highlightParam($('#sheet', body), ctx);
  };
  body.addEventListener('click', e => {
    const tab = e.target.closest('[data-sheet]');
    if (tab) show(+tab.dataset.sheet, false);
    const all = e.target.closest('[data-all]');
    if (all) show(+all.dataset.all, true);
  });
  show(0, false);
}

// ------------------------------------------------------------ Markdown

let MD = null;
function markdown() {
  if (MD) return MD;
  MD = window.markdownit({
    html: true,
    linkify: true,
    highlight: (code, lang) => (lang && hljs.getLanguage(lang) ? hljs.highlight(code, { language: lang, ignoreIllegals: true }).value : ''),
  })
    .use(window.markdownitTaskLists, { enabled: false })
    .use(window.markdownitFootnote)
    .use(mathPlugin)
    .use(headingIds);
  const fence = MD.renderer.rules.fence;
  MD.renderer.rules.fence = (tokens, i, opts, env, self) =>
    (tokens[i].info.trim() === 'mermaid' ? `<div class="mermaid">${esc(tokens[i].content)}</div>` : fence(tokens, i, opts, env, self));
  MD.renderer.rules.table_open = () => '<div class="table-wrap"><table>\n';
  MD.renderer.rules.table_close = () => '</table></div>\n';
  return MD;
}

// 与 GitHub 一致的标题锚点，文档里现有的 [](#1-xxx) 目录链接才能跳转
function slugify(text) {
  return text.trim().toLowerCase().replace(/[^\p{L}\p{M}\p{N}\p{Pc}\- ]/gu, '').replace(/ /g, '-');
}
function headingIds(md) {
  md.core.ruler.push('heading_ids', state => {
    const seen = new Map();
    const toks = state.tokens;
    for (let i = 0; i < toks.length; i++) {
      if (toks[i].type !== 'heading_open') continue;
      const text = toks[i + 1].children.filter(t => t.type === 'text' || t.type === 'code_inline').map(t => t.content).join('');
      let slug = slugify(text);
      const n = seen.get(slug);
      seen.set(slug, n === undefined ? 0 : n + 1);
      if (n !== undefined) slug += '-' + (n + 1);
      toks[i].attrSet('id', slug);
    }
  });
}

// 公式认 $$…$$ 和 \[…\]（独立成段）、$$…$$ 和 \(…\)（行内）。单个 $ 不当公式，文档里有不少 PowerShell 变量
const MATH_RE = /\$\$|\\\[|\\\(/;
function mathPlugin(md) {
  const tex = (src, display) => window.katex.renderToString(src, { displayMode: display, throwOnError: false });
  md.block.ruler.before('fence', 'math_block', (state, start, end, silent) => {
    const pos = state.bMarks[start] + state.tShift[start];
    if (state.sCount[start] - state.blkIndent >= 4) return false;
    const delim = [['$$', '$$'], ['\\[', '\\]']].find(([open]) => state.src.startsWith(open, pos));
    if (!delim) return false;
    const [open, close] = delim;
    const first = state.src.slice(pos + open.length, state.eMarks[start]).trim();
    let content;
    let last = start;
    if (first.endsWith(close)) content = first.slice(0, -close.length);
    // \[ 开头却没独占一行，多半是转义的方括号（如 \[1\] 引注），不当公式
    else if (open === '\\[' && first) return false;
    else {
      const lines = [first];
      let found = false;
      for (last = start + 1; last < end; last++) {
        const line = state.src.slice(state.bMarks[last] + state.tShift[last], state.eMarks[last]).trim();
        if (line.endsWith(close)) { lines.push(line.slice(0, -close.length)); found = true; break; }
        lines.push(line);
      }
      if (!found) return false;
      content = lines.join('\n');
    }
    if (silent) return true;
    const tok = state.push('math_block', 'div', 0);
    tok.block = true;
    tok.content = content;
    tok.map = [start, last + 1];
    state.line = last + 1;
    return true;
  }, { alt: ['paragraph', 'reference', 'blockquote', 'list'] });
  // 要排在 escape 规则前面，否则 \( 会先被当成转义的括号吃掉
  md.inline.ruler.before('escape', 'math_inline', (state, silent) => {
    const delim = [['$$', '$$'], ['\\(', '\\)']].find(([open]) => state.src.startsWith(open, state.pos));
    if (!delim) return false;
    const [open, close] = delim;
    const end = state.src.indexOf(close, state.pos + open.length);
    if (end < 0 || end === state.pos + open.length) return false;
    if (!silent) state.push('math_inline', 'span', 0).content = state.src.slice(state.pos + open.length, end);
    state.pos = end + close.length;
    return true;
  });
  md.renderer.rules.math_block = (t, i) => `<div class="math-block">${tex(t[i].content, true)}</div>\n`;
  md.renderer.rules.math_inline = (t, i) => tex(t[i].content, false);
}

async function renderMarkdown(el, text, baseDir, selfPath) {
  if (MATH_RE.test(text)) await loadKatex();
  el.innerHTML = DOMPurify.sanitize(markdown().render(text), { ADD_ATTR: ['target'] });
  rewriteLinks(el, baseDir, selfPath);
  if (el.querySelector('.mermaid')) {
    await loadScript('/static/vendor/mermaid.min.js');
    window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: isDark() ? 'dark' : 'default' });
    await window.mermaid.run({ nodes: [...el.querySelectorAll('.mermaid')], suppressErrors: true });
  }
}

function resolveRel(baseDir, href) {
  const parts = href.startsWith('/') ? [] : baseDir.split('/').filter(Boolean);
  for (const seg of href.split('/')) {
    if (seg === '..') parts.pop();
    else if (seg && seg !== '.') parts.push(safeDecode(seg));
  }
  return parts.join('/');
}

// 文档里的相对链接改成本页路由，图片改走 /raw/；指向浏览目录之外的链接标灰
function rewriteLinks(el, baseDir, selfPath) {
  const external = /^[a-z][a-z0-9+.-]*:|^\/\//i;
  for (const a of el.querySelectorAll('a[href]')) {
    const href = a.getAttribute('href');
    if (external.test(href)) {
      a.target = '_blank';
      a.rel = 'noopener';
      continue;
    }
    if (href.startsWith('#')) {
      const id = safeDecode(href.slice(1));
      a.dataset.to = id;
      a.href = hashFor(selfPath, { a: id });
      continue;
    }
    const at = href.indexOf('#');
    const frag = at < 0 ? '' : safeDecode(href.slice(at + 1));
    const target = resolveRel(baseDir, (at < 0 ? href : href.slice(0, at)).split('?')[0]);
    a.href = hashFor(target, frag ? { a: frag } : null);
    if (!S.nodes.has(target)) {
      a.classList.add('outside');
      a.title = '不在当前浏览目录里：' + target;
    }
  }
  for (const img of el.querySelectorAll('img[src]')) {
    const src = img.getAttribute('src');
    if (external.test(src)) continue;
    img.src = rawUrl(resolveRel(baseDir, src));
    img.loading = 'lazy';
  }
}

function buildToc(md, toc) {
  const heads = [...md.querySelectorAll('h1, h2, h3, h4')].filter(h => h.id);
  if (heads.length < 3) {
    toc.remove();
    md.parentElement.classList.add('no-toc');
    return;
  }
  const min = Math.min(...heads.map(h => +h.tagName[1]));
  const shown = heads.filter(h => +h.tagName[1] <= min + 2);
  toc.innerHTML = '<div class="toc-h">本页目录</div>' + shown.map(h =>
    `<a data-to="${esc(h.id)}" class="l${+h.tagName[1] - min}" title="${esc(h.textContent)}">${esc(h.textContent)}</a>`).join('');
  S.toc = { heads: shown, links: [...toc.querySelectorAll('a')] };
  tocSpy();
}
function tocSpy() {
  if (!S.toc || !S.toc.heads[0].isConnected) return;
  const top = view().getBoundingClientRect().top + 100;
  let idx = 0;
  S.toc.heads.forEach((h, i) => { if (h.getBoundingClientRect().top < top) idx = i; });
  S.toc.links.forEach((a, i) => a.classList.toggle('on', i === idx));
}

// ------------------------------------------------------------ 搜索词高亮（从全文搜索结果打开时）

function highlightParam(root, ctx) {
  const q = ctx.params.get('hl');
  if (!q || !root) return;
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  const re = new RegExp(terms.map(escRe).join('|'), 'gi');
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: t => (t.parentElement.closest('script, style, .katex, .mermaid, svg') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
  });
  const textNodes = [];
  while (walker.nextNode()) textNodes.push(walker.currentNode);
  const marks = [];
  for (const node of textNodes) {
    const s = node.nodeValue;
    re.lastIndex = 0;
    if (!re.test(s)) continue;
    re.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0, m;
    while ((m = re.exec(s))) {
      frag.append(s.slice(last, m.index));
      const mk = document.createElement('mark');
      mk.className = 'hl';
      mk.textContent = m[0];
      frag.append(mk);
      marks.push(mk);
      last = m.index + m[0].length;
    }
    frag.append(s.slice(last));
    node.replaceWith(frag);
  }
  if (!marks.length) return;
  S.hl = { marks, i: 0, q };
  const bar = document.createElement('div');
  bar.className = 'hlbar';
  bar.innerHTML = `<span>“${esc(q)}”</span><b id="hl-pos"></b>
    <button class="icon-btn small" data-hl="-1" title="上一处">${ico('up')}</button>
    <button class="icon-btn small" data-hl="1" title="下一处">${ico('down')}</button>
    <button class="icon-btn small" data-hl="0" title="关闭">${ico('x')}</button>`;
  bar.addEventListener('click', e => {
    const b = e.target.closest('[data-hl]');
    if (!b) return;
    const d = +b.dataset.hl;
    if (d === 0) hideHlBar();
    else focusMark(S.hl.i + d);
  });
  document.body.appendChild(bar);
  focusMark(0);
}
function focusMark(i) {
  const { marks } = S.hl;
  S.hl.i = (i + marks.length) % marks.length;
  marks.forEach((m, j) => m.classList.toggle('now', j === S.hl.i));
  marks[S.hl.i].scrollIntoView({ block: 'center' });
  $('#hl-pos').textContent = `${S.hl.i + 1} / ${marks.length}`;
}
function hideHlBar() {
  document.querySelector('.hlbar')?.remove();
  if (S.hl) S.hl.marks.forEach(m => m.classList.remove('now'));
  S.hl = null;
}

// ------------------------------------------------------------ 找不到的路径

async function renderMissing(path, tok) {
  setTitle('找不到');
  $('#crumbs').innerHTML = `<a href="#/">${ico('home')}</a><span class="sep">${ico('chev')}</span><span class="last">${esc(path)}</span>`;
  const st = await api('/api/stat?path=' + encodeURIComponent(path));
  if (tok !== S.tok) return;
  let msg, extra = '';
  if (!st.exists) msg = errorBox('文件不存在', `${path}\n链接可能已经失效，或者文件被移动、改名了。`);
  else if (st.excluded) msg = errorBox('这个位置被排除在外', `${path}\n它匹配 config.json 里的排除规则。`);
  else {
    msg = errorBox('不在浏览目录内', `${path}\n文件存在，但它所在的目录“${st.top}”还没有加入浏览范围。`);
    extra = `<button class="btn primary" data-act="add-root" data-root="${esc(st.top)}">${ico('plus')}<span>把 ${esc(st.top)} 加入浏览目录</span></button>`;
  }
  view().innerHTML = `<div class="page">${msg}<div class="actions" style="justify-content:flex-start;margin-top:14px">${extra}<a class="btn" href="#/">回到首页</a></div></div>`;
}

// ------------------------------------------------------------ 弹窗：搜索

function openModal(html, cls) {
  closeModal();
  const m = document.createElement('div');
  m.className = 'modal ' + cls;
  m.innerHTML = html;
  m.addEventListener('mousedown', e => { if (e.target === m) closeModal(); });
  m.addEventListener('click', e => { if (e.target.closest('[data-close]')) closeModal(); });
  $('#modal-root').appendChild(m);
  return m;
}
function closeModal() {
  const m = $('#modal-root .modal');
  if (!m) return false;
  m.remove();
  return true;
}

function nameSearch(q) {
  const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
  if (!terms.length) return store.get('recent', []).map(x => S.nodes.get(x.p)).filter(Boolean).slice(0, 20);
  const scored = [];
  for (const n of S.nodes.values()) {
    const p = n.p.toLowerCase();
    if (!terms.every(t => p.includes(t))) continue;
    const name = n.n.toLowerCase();
    let score = -n.p.length / 200;
    for (const t of terms) {
      if (name.includes(t)) score += 10;
      if (name.startsWith(t)) score += 4;
    }
    scored.push([score, n]);
  }
  scored.sort((a, b) => b[0] - a[0] || b[1].m - a[1].m);
  return scored.slice(0, 60).map(x => x[1]);
}

function openSearch() {
  if ($('.modal.search')) return;
  const m = openModal(`<div class="dialog">
    <div class="sb-top">${ico('search')}<input id="sq" autocomplete="off" spellcheck="false">
      <div class="seg"><button data-mode="name">文件名</button><button data-mode="content">全文</button></div></div>
    <div class="sb-status" id="sstatus"></div>
    <div class="sb-results" id="sres"></div>
    <div class="sb-foot"><span><kbd>↑</kbd><kbd>↓</kbd>选择</span><span><kbd>Enter</kbd>打开</span><span><kbd>Tab</kbd>切换文件名 / 全文</span><span><kbd>Esc</kbd>关闭</span></div>
  </div>`, 'search');
  const input = $('#sq', m), res = $('#sres', m), status = $('#sstatus', m);
  let items = [], sel = 0, timer = 0, ctrl = null, lastQ = null;
  const terms = () => input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);

  const draw = () => {
    if (!items.length) {
      const q = input.value.trim();
      res.innerHTML = `<div class="sb-empty">${S.searchMode === 'content' && !q
        ? '输入关键词开始全文搜索，多个词用空格分开（要求同时出现）。<br>覆盖 Markdown、文本与代码、网页、Word、PPT、Excel 和 PDF。'
        : q ? '没有匹配的文件' : '还没有查看记录'}</div>`;
      return;
    }
    const ts = terms();
    res.innerHTML = items.map((it, i) => {
      const n = it.n;
      const snips = it.r ? it.r.hits.map((h, j) => `<a class="snip" data-i="${i}" data-hit="${j}">`
        + `<span class="loc">${h.page ? `第 ${h.page} 页` : `第 ${h.line} 行`}</span>${hlText(h.text, ts)}</a>`).join('') : '';
      const more = it.r && it.r.count > it.r.hits.length ? `<div class="sr-path">共 ${it.r.count} 处</div>` : '';
      return `<div class="sr${i === sel ? ' sel' : ''}" data-i="${i}">${nodeIco(n)}
        <div class="sr-main"><div class="sr-name">${hlText(n.n, ts)}</div><div class="sr-path">${hlText(dirOf(n.p), ts)}</div>${snips}${more}</div>
        <span class="sr-time">${relTime(n.m)}</span></div>`;
    }).join('');
  };

  const contentSearch = async q => {
    if (q === lastQ) return;
    lastQ = q;
    if (ctrl) ctrl.abort();
    ctrl = new AbortController();
    status.innerHTML = '<span class="spinner" style="width:12px;height:12px;border-width:2px"></span>搜索中…';
    try {
      const r = await api('/api/search?q=' + encodeURIComponent(q), { signal: ctrl.signal });
      if (r.results.some(x => !S.nodes.has(x.path)) && await loadTree()) renderTree();
      items = r.results.filter(x => S.nodes.has(x.path)).map(x => ({ n: S.nodes.get(x.path), r: x }));
      sel = 0;
      status.innerHTML = `${r.total} 个文件匹配${r.total > r.results.length ? `（显示前 ${r.results.length} 个）` : ''}`
        + ` · 检索 ${r.searched} 个文件，用时 ${r.ms} ms`
        + (r.skipped.length ? ` · <details><summary>${r.skipped.length} 个文件没有全文索引</summary><ul>${r.skipped.map(s =>
          `<li>${esc(s.path)}：${esc(s.reason)}</li>`).join('')}</ul></details>` : '');
      draw();
    } catch (e) {
      if (e.name === 'AbortError') return; // 被更新的搜索取代
      lastQ = null;
      status.innerHTML = `<span class="tool-miss">搜索失败：${esc(e.message)}</span>`;
    }
  };

  const run = () => {
    const q = input.value.trim();
    S.lastQuery = input.value;
    if (S.searchMode === 'name') {
      clearTimeout(timer);
      items = nameSearch(q).map(n => ({ n }));
      sel = 0;
      status.textContent = q ? `${items.length >= 60 ? '前 60 个' : items.length + ' 个'}文件名匹配 · 按 Tab 改为搜全文` : '最近查看';
      draw();
      return;
    }
    if (!q) {
      items = [];
      lastQ = null;
      status.textContent = '';
      draw();
      return;
    }
    clearTimeout(timer);
    timer = setTimeout(() => contentSearch(q), 300);
  };

  const setMode = mode => {
    S.searchMode = mode;
    store.set('searchMode', mode);
    m.querySelectorAll('[data-mode]').forEach(b => b.classList.toggle('on', b.dataset.mode === mode));
    input.placeholder = mode === 'name' ? '按文件名或路径查找…' : '搜索文件里的文字…';
    lastQ = null;
    items = [];
    run();
    input.focus();
  };

  const openItem = (i, hitIdx) => {
    const it = items[i];
    if (!it) return;
    closeModal();
    const params = {};
    if (it.r && it.r.hits.length) {
      const h = it.r.hits[hitIdx ?? 0];
      if (h.page) params.page = h.page;
      if (viewerKind(it.n.n) !== 'html') params.hl = terms().join(' ');
    }
    go(it.n.p, params);
  };

  input.addEventListener('input', run);
  input.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!items.length) return;
      sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      res.querySelectorAll('.sr').forEach(x => x.classList.toggle('sel', +x.dataset.i === sel));
      res.querySelector('.sr.sel').scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const q = input.value.trim();
      if (S.searchMode === 'content' && q && q !== lastQ) {
        clearTimeout(timer);
        contentSearch(q);
      } else openItem(sel);
    } else if (e.key === 'Tab') {
      e.preventDefault();
      setMode(S.searchMode === 'name' ? 'content' : 'name');
    }
  });
  m.querySelectorAll('[data-mode]').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));
  res.addEventListener('click', e => {
    const s = e.target.closest('.snip');
    if (s) return openItem(+s.dataset.i, +s.dataset.hit);
    const r = e.target.closest('.sr');
    if (r) openItem(+r.dataset.i);
  });
  res.addEventListener('mousemove', e => {
    const r = e.target.closest('.sr');
    if (!r || +r.dataset.i === sel) return;
    sel = +r.dataset.i;
    res.querySelectorAll('.sr').forEach(x => x.classList.toggle('sel', x === r));
  });
  input.value = S.lastQuery;
  setMode(S.searchMode);
  input.select();
}

// ------------------------------------------------------------ 弹窗：管理目录

async function openManage() {
  const cfg = S.cfg = await api('/api/config');
  let roots = [...cfg.roots];
  const tool = (path, missing) => (path ? `<span class="tool-ok">✓ ${esc(path)}</span>` : `<span class="tool-miss">未找到，${missing}</span>`);
  const m = openModal(`<div class="dialog manage">
    <div class="dlg-h"><h2>管理浏览目录</h2><button class="icon-btn" data-close title="关闭">${ico('x')}</button></div>
    <div class="dlg-b">
      <div id="mr-list"></div>
      <div class="add-row"><input id="mr-input" placeholder="仓库内的目录，如 result 或 paper/精读笔记" spellcheck="false">
        <button class="btn" id="mr-add">${ico('plus')}<span>添加</span></button></div>
      <div class="chips" id="mr-chips"></div>
      <div class="form-err" id="mr-err"></div>
      <div class="dlg-note">目录写成相对于仓库 <code>${esc(cfg.repo_path)}</code> 的路径，保存后写入 <code>${esc(cfg.config_path)}</code>；也可以直接改这个文件，改完刷新页面。<br>
        LibreOffice：${tool(cfg.tools.soffice, 'PPT、旧版 Word / Excel 无法预览')}<br>
        pdftotext：${tool(cfg.tools.pdftotext, 'PDF 只能按文件名搜索')}</div>
    </div>
    <div class="dlg-f"><button class="btn" data-close>取消</button><button class="btn primary" id="mr-save">保存</button></div>
  </div>`, 'manage');
  const err = $('#mr-err', m);
  const draw = () => {
    $('#mr-list', m).innerHTML = roots.map((r, i) => {
      const n = S.nodes.get(r);
      return `<div class="mr-row"><span class="dot" style="--c:${ROOT_COLORS[i % ROOT_COLORS.length]}"></span>
        <span class="mr-path">${esc(r)}</span><span class="muted" style="font-size:12px">${n && n.root === n ? `${n.files} 个文件` : '保存后加入'}</span>
        <button class="icon-btn small" data-mv="${i},-1" title="上移">${ico('up')}</button>
        <button class="icon-btn small" data-mv="${i},1" title="下移">${ico('down')}</button>
        <button class="icon-btn small" data-rm="${i}" title="移除">${ico('x')}</button></div>`;
    }).join('') || '<div class="empty">至少保留一个目录</div>';
    $('#mr-chips', m).innerHTML = cfg.candidates.filter(c => !roots.includes(c))
      .map(c => `<button class="chip" data-cand="${esc(c)}">+ ${esc(c)}</button>`).join('');
  };
  const add = value => {
    const v = value.trim().replace(/\\/g, '/').replace(/\/+$/, '');
    if (!v) return;
    if (roots.includes(v)) { err.textContent = `${v} 已经在列表里`; return; }
    roots.push(v);
    err.textContent = '';
    $('#mr-input', m).value = '';
    draw();
  };
  m.addEventListener('click', async e => {
    const t = e.target;
    const mv = t.closest('[data-mv]');
    if (mv) {
      const [i, d] = mv.dataset.mv.split(',').map(Number);
      const j = i + d;
      if (j >= 0 && j < roots.length) [roots[i], roots[j]] = [roots[j], roots[i]];
      draw();
    }
    const rm = t.closest('[data-rm]');
    if (rm) { roots.splice(+rm.dataset.rm, 1); draw(); }
    const cand = t.closest('[data-cand]');
    if (cand) add(cand.dataset.cand);
    if (t.closest('#mr-add')) add($('#mr-input', m).value);
    if (t.closest('#mr-save')) {
      try {
        S.cfg = await post('/api/roots', { roots });
      } catch (ex) {
        err.textContent = ex.message;
        return;
      }
      closeModal();
      await loadTree();
      route();
      toast('浏览目录已更新');
    }
  });
  $('#mr-input', m).addEventListener('keydown', e => { if (e.key === 'Enter') add(e.target.value); });
  draw();
}

// ------------------------------------------------------------ 页面级交互

async function doAction(act, btn) {
  const p = S.route.path;
  if (act === 'copy') {
    await navigator.clipboard.writeText(p);
    toast('已复制路径：' + p);
  } else if (act === 'reveal' || act === 'open') {
    await post('/api/open', { path: p, reveal: act === 'reveal' });
  } else if (act === 'tab') {
    window.open(rawUrl(p), '_blank', 'noopener');
  } else if (act === 'pin') {
    const list = pins();
    const on = !list.includes(p);
    store.set('pins', on ? [p, ...list] : list.filter(x => x !== p));
    btn.classList.toggle('on', on);
    btn.title = on ? '取消收藏' : '收藏';
    toast(on ? '已收藏，首页可以找到' : '已取消收藏');
  } else if (act === 'src') {
    S.mdSource = !S.mdSource;
    S.forceText = false;
    route();
  } else if (act === 'docx-pdf') {
    S.docxPdf = !S.docxPdf;
    route();
  } else if (act === 'as-text') {
    S.forceText = true;
    route();
  } else if (act === 'show-all') {
    S.showAll = true;
    route();
  } else if (act === 'add-root') {
    S.cfg = await post('/api/roots', { roots: [...S.cfg.roots, btn.dataset.root] });
    await loadTree();
    toast(`已把 ${btn.dataset.root} 加入浏览目录`);
    route();
  }
}

function applyTheme() {
  const t = store.get('theme', 'auto');
  if (t === 'auto') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = t;
  for (const f of document.querySelectorAll('iframe.pdfjs')) {
    const st = f.contentDocument.documentElement.style;
    if (t === 'auto') st.removeProperty('color-scheme');
    else st.setProperty('color-scheme', t);
  }
  const btn = $('#theme-btn');
  btn.innerHTML = ico(t === 'auto' ? 'auto' : t === 'light' ? 'sun' : 'moon');
  btn.title = `外观：${{ auto: '跟随系统', light: '浅色', dark: '深色' }[t]}（点击切换）`;
}
function isDark() {
  const t = document.documentElement.dataset.theme;
  return t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
}
const isTyping = el => el.closest('input, textarea, [contenteditable="true"]');

function setupChrome() {
  $('#search-kbd').textContent = IS_MAC ? '⌘K' : 'Ctrl K';
  const sideW = store.get('sideW', 288);
  document.documentElement.style.setProperty('--side-w', sideW + 'px');

  $('#theme-btn').addEventListener('click', () => {
    const order = ['auto', 'light', 'dark'];
    store.set('theme', order[(order.indexOf(store.get('theme', 'auto')) + 1) % 3]);
    applyTheme();
  });
  $('#search-trigger').addEventListener('click', openSearch);
  $('#manage-btn').addEventListener('click', () => openManage().catch(e => toast(e.message, true)));
  $('#refresh-btn').addEventListener('click', async () => {
    await loadTree();
    route();
    toast('已重新扫描目录');
  });
  $('#menu-btn').addEventListener('click', () => document.body.classList.toggle('side-open'));
  $('#scrim').addEventListener('click', () => document.body.classList.remove('side-open'));

  $('#resizer').addEventListener('mousedown', e => {
    e.preventDefault();
    document.body.classList.add('resizing');
    let w = sideW;
    const move = ev => {
      w = Math.min(560, Math.max(200, ev.clientX));
      document.documentElement.style.setProperty('--side-w', w + 'px');
    };
    const up = () => {
      document.body.classList.remove('resizing');
      removeEventListener('mousemove', move);
      removeEventListener('mouseup', up);
      store.set('sideW', w);
    };
    addEventListener('mousemove', move);
    addEventListener('mouseup', up);
  });

  $('#tree').addEventListener('click', e => {
    const row = e.target.closest('.row');
    if (!row) return;
    const n = S.nodes.get(row.dataset.p);
    if (n.d && (e.target.closest('.tw') || (S.route.path === n.p && S.expanded.has(n.p)))) {
      toggleDir(n.p);
      return;
    }
    go(n.p);
  });

  view().addEventListener('click', e => {
    const a = e.target.closest('a');
    if (a) {
      if (a.dataset.to) {
        e.preventDefault();
        scrollToId(a.dataset.to);
      } else if ((a.getAttribute('href') || '').startsWith('#/') && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
        S.pushNav = true;
      }
      return;
    }
    const act = e.target.closest('[data-act]');
    if (act) {
      doAction(act.dataset.act, act).catch(err => toast(err.message, true));
      return;
    }
    const th = e.target.closest('th[data-sort]');
    if (th) {
      const k = th.dataset.sort;
      S.sort = { key: k, dir: S.sort.key === k ? -S.sort.dir : (k === 'name' ? 1 : -1) };
      store.set('sort', S.sort);
      route();
      return;
    }
    const tr = e.target.closest('tr[data-go]');
    if (tr) {
      go(tr.dataset.go);
      return;
    }
    const img = e.target.closest('.img-view img');
    if (img) img.parentElement.classList.toggle('actual');
  });

  let spyQueued = false;
  view().addEventListener('scroll', () => {
    if (spyQueued || !S.toc) return;
    spyQueued = true;
    requestAnimationFrame(() => { spyQueued = false; tocSpy(); });
  }, { passive: true });

  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openSearch();
    } else if (e.key === 'Escape') {
      if (!closeModal()) hideHlBar();
    } else if (e.key === '/' && !isTyping(e.target) && !$('.modal')) {
      e.preventDefault();
      openSearch();
    }
  });

  // 切回这个窗口时重新扫描：别处改了文件，这里马上能看到
  window.addEventListener('focus', async () => {
    if (Date.now() - S.loadedAt < 3000) return;
    const path = S.route.path;
    const before = path && S.nodes.get(path);
    const beforeM = before && before.m;
    if (!await loadTree()) return;
    if ($('.modal')) { renderTree(); return; }
    const now = path && S.nodes.get(path);
    if (path === null || !now || now.d || now.m !== beforeM) route();
    else renderTree();
  });
}

async function init() {
  applyTheme();
  setupChrome();
  S.cfg = await api('/api/config');
  $('#repo-name').textContent = S.cfg.repo;
  await loadTree();
  window.addEventListener('hashchange', route);
  route();
}

init().catch(e => {
  view().innerHTML = `<div class="page">${errorBox('启动失败', e.message)}</div>`;
});
