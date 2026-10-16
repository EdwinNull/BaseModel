// 把 spec/*.json 渲染成 .docx。用法：node render.js <spec.json> <out.docx> [pdf]
// 第三个参数为 pdf 时换成本机有的中文字体（给 LibreOffice 转 PDF 用），否则用 Windows 常见的微软雅黑。
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, HeadingLevel, LevelFormat, Footer, Header, PageNumber, PageBreak, TableLayoutType, VerticalAlign,
} = require('docx');

const [, , specPath, outPath, mode] = process.argv;
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const PDF = mode === 'pdf';
const CJK = PDF ? 'Hiragino Sans GB' : 'Microsoft YaHei';
const LATIN = 'Arial';
const MONO = PDF ? 'Menlo' : 'Consolas';
const FONT = { ascii: LATIN, hAnsi: LATIN, eastAsia: CJK, cs: LATIN };

// A4，页边距 2 cm；版心 9638 DXA ≈ 642 px
const PAGE_W = 11906, MARGIN = 1134, TEXT_W = PAGE_W - 2 * MARGIN;
const IMG_W = 640;
const C = { accent: '2A78D6', ink2: '52514E', muted: '898781', grid: 'D9D8D1', head: 'F0EFEC', info: 'EAF2FC', warn: 'FFF3D6', warnBar: 'E0A100', infoBar: '2A78D6', code: 'F0EFEC' };

// ---- 行内：**粗体**、`代码`
function runs(text, base = {}) {
  const out = [];
  for (const part of String(text).split(/(\*\*[^*]+\*\*|`[^`]+`)/)) {
    if (!part) continue;
    if (part.startsWith('**') && part.endsWith('**')) out.push(new TextRun({ ...base, text: part.slice(2, -2), bold: true }));
    else if (part.startsWith('`') && part.endsWith('`'))
      out.push(new TextRun({ ...base, text: part.slice(1, -1), font: { ascii: MONO, hAnsi: MONO, eastAsia: CJK }, shading: { type: ShadingType.CLEAR, fill: C.code, color: 'auto' } }));
    else out.push(new TextRun({ ...base, text: part }));
  }
  return out;
}

let listInstance = 0;
function listParas(items, ordered, opts = {}) {
  const inst = ++listInstance;
  return items.map((t) => new Paragraph({
    children: runs(t, opts.run),
    numbering: { reference: ordered ? 'num' : 'bul', level: 0, instance: ordered ? inst : 0 },
    spacing: { after: 30, line: 276 },
  }));
}

const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const LINE = { style: BorderStyle.SINGLE, size: 4, color: C.grid };

function dxa(widths) {
  const sum = widths.reduce((a, b) => a + b, 0);
  const ws = widths.map((w) => Math.floor((w / sum) * TEXT_W));
  ws[ws.length - 1] += TEXT_W - ws.reduce((a, b) => a + b, 0);
  return ws;
}

function cell(children, width, opts = {}) {
  return new TableCell({
    children, width: { size: width, type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: 'auto' } : undefined,
    borders: opts.borders, verticalAlign: opts.valign,
  });
}

function table(t) {
  const ws = dxa(t.widths);
  const borders = { top: LINE, bottom: LINE, left: LINE, right: LINE };
  const rows = [new TableRow({
    tableHeader: true,
    children: t.head.map((h, i) => cell([new Paragraph({ children: runs(h, { bold: true, color: C.ink2, size: 19 }) })], ws[i], { fill: C.head, borders })),
  })];
  for (const r of t.rows) {
    rows.push(new TableRow({
      cantSplit: true,
      children: r.map((x, i) => cell(
        String(x).split('\n').map((line) => new Paragraph({ children: runs(line, { size: 19 }), spacing: { line: 280 } })),
        ws[i], { borders })),
    }));
  }
  return [new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: ws, layout: TableLayoutType.FIXED, rows }), gap(80)];
}

function box(b) {
  const bar = b.kind === 'warn' ? C.warnBar : C.infoBar;
  const fill = b.kind === 'warn' ? C.warn : C.info;
  const kids = [];
  if (b.title) kids.push(new Paragraph({ children: runs(b.title, { bold: true, size: 20 }), spacing: { after: 60 } }));
  if (b.items.length === 1 && !b.title?.startsWith('#')) kids.push(new Paragraph({ children: runs(b.items[0], { size: 20 }), spacing: { line: 300 } }));
  else kids.push(...listParas(b.items, false, { run: { size: 20 } }));
  return [new Table({
    width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], layout: TableLayoutType.FIXED,
    rows: [new TableRow({ cantSplit: true, children: [cell(kids, TEXT_W, {
      fill, borders: { top: NONE, bottom: NONE, right: NONE, left: { style: BorderStyle.SINGLE, size: 24, color: bar } },
    })] })],
  }), gap(100)];
}

function gap(after = 120) {
  return new Paragraph({ children: [], spacing: { after, line: 120 } });
}

function figure(f) {
  const w = Math.min(IMG_W, Math.round(f.w * IMG_W / 1440)) || IMG_W;
  const h = Math.round(f.h * w / f.w);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 80, after: 40 },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(f.path), transformation: { width: w, height: h },
        altText: { title: f.caption, description: f.caption, name: f.caption } })],
    }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: runs(f.caption, { size: 18, color: C.muted }), spacing: { after: 160 } }),
  ];
}

function codeBlock(text) {
  const lines = text.split('\n');
  return [new Table({
    width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: [TEXT_W], layout: TableLayoutType.FIXED,
    rows: [new TableRow({ children: [cell(lines.map((l) => new Paragraph({
      children: [new TextRun({ text: l || ' ', font: { ascii: MONO, hAnsi: MONO, eastAsia: CJK }, size: 17 })], spacing: { line: 260 },
    })), TEXT_W, { fill: C.code, borders: { top: NONE, bottom: NONE, left: NONE, right: NONE } })] })],
  }), gap(100)];
}

function step(s) {
  const out = [new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: runs(`步骤 ${s.no}　${s.title}`) })];
  if (s.do.length || s.see.length) {
    const ws = dxa([1, 1.25]);
    const borders = { top: LINE, bottom: LINE, left: LINE, right: LINE };
    out.push(new Table({
      width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: ws, layout: TableLayoutType.FIXED,
      rows: [
        new TableRow({ tableHeader: true, children: [
          cell([new Paragraph({ children: runs('操作', { bold: true, color: C.ink2, size: 19 }) })], ws[0], { fill: C.head, borders }),
          cell([new Paragraph({ children: runs('应该看到', { bold: true, color: C.ink2, size: 19 }) })], ws[1], { fill: C.head, borders }),
        ] }),
        new TableRow({ cantSplit: true, children: [
          cell(s.do.length ? listParas(s.do, true, { run: { size: 20 } }) : [new Paragraph('—')], ws[0], { borders }),
          cell(s.see.length ? listParas(s.see, false, { run: { size: 20 } }) : [new Paragraph('—')], ws[1], { borders }),
        ] }),
      ],
    }), gap(100));
  }
  if (s.tip) out.push(...box({ kind: 'info', title: null, items: [s.tip] }));
  if (s.code) out.push(...codeBlock(s.code));
  for (const f of s.figs) out.push(...figure(f));
  if (s.note) out.push(...box({ kind: 'warn', title: '已知问题（本次测试发现，修复前会遇到）', items: s.note }));
  return out;
}

function blocks(list) {
  const out = [];
  for (const b of list) {
    if (b.p !== undefined) out.push(new Paragraph({ children: runs(b.p), spacing: { after: 120, line: 320 } }));
    else if (b.small !== undefined) out.push(new Paragraph({ children: runs(b.small, { size: 18, color: C.muted }), spacing: { after: 120 } }));
    else if (b.h3 !== undefined) out.push(new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, children: runs(b.h3) }));
    else if (b.list) out.push(...listParas(b.list, b.ordered), gap(60));
    else if (b.box) out.push(...box(b.box));
    else if (b.table) out.push(...table(b.table));
    else if (b.code !== undefined) out.push(...codeBlock(b.code));
    else if (b.step) out.push(...step(b.step));
    else if (b.fig) out.push(...figure(b.fig));
    else if (b.pagebreak) out.push(new Paragraph({ children: [new PageBreak()] }));
  }
  return out;
}

// ---- 封面
const cover = [
  new Paragraph({ children: runs(spec.eyebrow, { size: 20, color: C.muted }), spacing: { before: 1800, after: 200 } }),
  new Paragraph({ children: runs(spec.title, { size: 52, bold: true }), spacing: { after: 240 } }),
  new Paragraph({ children: runs(spec.lede, { size: 24, color: C.ink2 }), spacing: { after: 360, line: 360 } }),
  ...table({ head: ['项目', '内容'], rows: spec.facts, widths: [1, 3.2] }),
  new Paragraph({ children: runs('内容', { bold: true, size: 22 }), spacing: { before: 360, after: 80 } }),
  ...spec.sections.map((s) => new Paragraph({ children: runs(s.h, { size: 21, color: C.ink2 }), spacing: { after: 40 }, indent: { left: 240 } })),
  new Paragraph({ children: runs(spec.foot, { size: 17, color: C.muted }), spacing: { before: 480, line: 280 } }),
];

const body = [];
spec.sections.forEach((s) => {
  body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: runs(s.h) }));
  body.push(...blocks(s.blocks));
});

const doc = new Document({
  creator: 'flucase 测试', title: spec.title, description: spec.lede,
  styles: {
    default: { document: { run: { font: FONT, size: 21 }, paragraph: { spacing: { line: 300 } } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: '0B0B0B' }, paragraph: { spacing: { before: 120, after: 240 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 25, bold: true, color: C.accent }, paragraph: { spacing: { before: 360, after: 140 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT, size: 22, bold: true, color: '0B0B0B' }, paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 300, hanging: 220 } } } }] },
      { reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 340, hanging: 300 } } } }] },
    ],
  },
  sections: [
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
      children: cover },
    { properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: runs(spec.title + ' · 2026-10-16', { size: 16, color: C.muted }) })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ children: ['第 ', PageNumber.CURRENT, ' 页 / 共 ', PageNumber.TOTAL_PAGES, ' 页'], size: 16, color: C.muted }),
      ] })] }) },
      children: body },
  ],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outPath, buf); console.log('wrote', outPath, buf.length); });
