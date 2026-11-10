from pathlib import Path
import json,re,hashlib,html
import markdown
B=Path(__file__).resolve().parent
R=B/'report.md'
s=R.read_text()
# External sources retain actual lookup provenance; internal sources use a separate path ledger.
external=[]
for line in (B/'literature_sources.jsonl').read_text().splitlines():
 d=json.loads(line); i=int(d['id'][1:]); ext=dict(d)
 ext.update(source_id=f'S{i:03d}',source_type='primary_research' if i not in (1,2,5) else 'preprint',accessed_at='2026-10-31',quality_level='B' if i in (1,2,5) else 'A',access_level='full_text',supports=[f'C{i:02d}'],locators={f'C{i:02d}':d.get('read_level','see literature_audit.md')})
 if i==8:ext['access_level']='full_text_public_technical_report_and_published_metadata'
 external.append(ext)
(B/'sources.jsonl').write_text('\n'.join(json.dumps(d,ensure_ascii=False) for d in external)+'\n')
repo=B.parents[2]
paths={
'E01':['plans/观测过程建模/医学时序预测_生理状态与记录过程分解_可行性分析_20261031.md'],
'E02':['result/观测过程建模/MC_MED_观测过程问题发现阶段总结.docx',str((B/'evidence/MC_colleague.txt').relative_to(repo))],
'E03':[str((B/'evidence/B1v2.md').relative_to(repo))],
'E04':[str((B/'evidence/V2.md').relative_to(repo))],
'E05':[str((B/'evidence'/f).relative_to(repo)) for f in ['MC_test.md','MC_test_prereg.md','MC_deviations.md']],
'E06':[str((B/'evidence/MC_oct.md').relative_to(repo))],
'E07':[str((B/'server_method_audit.md').relative_to(repo))],
'E08':['docs/数据标准/数据集说明/数据集说明书_Healthsheet_v0.1_20261031.md'],
'E09':['docs/数据标准/质量验收/质量成绩单_std_v3_20261031_5.md'],
'E10':[str((B/'evidence'/f).relative_to(repo)) for f in ['A4.md','decisions.md']],
'E11':['research/观测过程与研究设计/measurement-process-plan-review-20261031/toy/ponly_leak_sim4.py'],
'E12':['CLAUDE.md']}
ledger=[]
for k,ps in paths.items():
 entries=[]
 for path in ps:
  p=repo/path
  assert p.is_file(),path
  entries.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 ledger.append({'evidence_id':k,'accessed_at':'2026-10-31','files':entries,'access':'local_full_document_or_readonly_audit','limitation':'原报告未独立重跑；具体限制见正文'})
(B/'evidence-index.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
md=markdown.Markdown(extensions=['extra','toc','sane_lists'],extension_configs={'toc':{'toc_depth':'2-2'}})
body=md.convert(s)
# Embed all figures; no external font or image dependencies.
def embed(m):
 alt,src=m.group(1),m.group(2)
 path=B/src
 svg=path.read_text()
 return '<figure class="figure"><div class="graphic-scroll" tabindex="0" aria-label="'+html.escape(alt)+'；窄屏可横向滚动">'+svg+'</div></figure>'
body=re.sub(r'<p><img alt="([^"]*)" src="([^"]*)"\s*/></p>',embed,body)
body=re.sub(r'<table>', '<div class="table-scroll" tabindex="0" aria-label="可横向滚动的数据表"><table>',body)
body=body.replace('</table>','</table></div>')
body=re.sub(r'<p>\[([SE]\d+)\]',r'<p class="reference" id="ref-\1">[\1]',body)
# Link inline evidence citations while preserving reference labels.
body=re.sub(r'(?<!>)\[([SE]\d+)\]',r'<a class="cite" href="#ref-\1">[\1]</a>',body)
style='''
:root{color-scheme:light;--bg:#f8faf8;--paper:#fff;--ink:#23312c;--muted:#58675f;--accent:#176b5b;--line:#d8e1db}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:28px}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-size:17px;line-height:1.85}header{max-width:1120px;margin:0 auto;padding:42px 56px 0}header .eyebrow{color:var(--accent);font-size:14px;letter-spacing:.12em;font-weight:600}header p{color:var(--muted);font-size:15px;margin:10px 0}main{max-width:1120px;margin:20px auto 64px;padding:32px 56px 56px;background:var(--paper);border-top:3px solid var(--accent)}h1{font-size:35px;line-height:1.42;letter-spacing:-.025em;margin:0 0 14px;font-weight:600}h2{font-size:27px;line-height:1.5;margin:64px 0 22px;padding-top:22px;border-top:1px solid var(--line);font-weight:600}h1+h2{border:0;margin:0 0 24px;padding:0;font-size:22px;color:var(--muted)}h3{font-size:21px;margin:34px 0 14px;line-height:1.5;font-weight:600}p{margin:15px 0}strong{font-weight:600}a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}a:focus-visible,summary:focus-visible,div[tabindex]:focus-visible{outline:3px solid #176b5b;outline-offset:4px}nav{margin:30px 0;padding:20px 24px;border-block:1px solid var(--line);font-size:15px}nav summary{cursor:pointer;font-weight:600}nav ul{columns:2;gap:36px;padding-left:22px}nav li{break-inside:avoid;line-height:1.65;margin:8px 0}.table-scroll{max-width:100%;overflow-x:auto;margin:22px 0}table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.7;min-width:740px}th{text-align:left;font-weight:600;color:var(--accent);background:#eef5f1;border-block:1px solid var(--line)}td,th{padding:12px 14px;vertical-align:top;border-bottom:1px solid var(--line)}td{min-width:105px}tr:nth-child(even) td{background:#fbfcfb}figure{margin:30px 0 12px}.graphic-scroll{overflow-x:auto;border:1px solid var(--line);background:#fff}.graphic-scroll svg{display:block;width:100%;min-width:820px;height:auto}figure+p:has(em){font-size:14px;color:var(--muted);line-height:1.75;margin-bottom:26px}code{font-size:.88em;background:#f0f4f1;padding:.12em .28em;border-radius:2px;overflow-wrap:anywhere}pre{padding:18px;background:#f0f4f1;overflow-x:auto;font-size:14px;line-height:1.75}pre code{padding:0;background:none}li{padding-left:3px;margin:9px 0}blockquote{border-left:3px solid var(--accent);margin:20px 0;padding:1px 22px;background:#f5f9f6}.reference{font-size:14px;line-height:1.8;padding-left:14px;border-left:2px solid var(--line);margin:18px 0}.cite{font-size:.83em;text-decoration:none;white-space:nowrap}footer{max-width:1000px;margin:0 auto 48px;padding:0 20px;font-size:14px;color:var(--muted)}@media(max-width:740px){body{font-size:16px;line-height:1.85}header{padding:25px 20px 0}main{margin:14px auto 30px;padding:26px 20px 36px}h1{font-size:28px}h2{font-size:23px;margin-top:44px}h3{font-size:20px}nav{padding:14px 15px}nav ul{columns:1}.table-scroll,.graphic-scroll{max-width:100%}table{font-size:14px}header p{font-size:14px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{body{background:#fff;font-size:11pt}header{padding:0}main{max-width:none;margin:0;padding:15px 0;border:0}nav{display:none}h2{break-before:page}h1+h2{break-before:auto}table{min-width:0;font-size:8.2pt}td,th{padding:6px}figure,.table-scroll{break-inside:avoid}.graphic-scroll svg{min-width:0}.graphic-scroll,.table-scroll{overflow:visible}a{color:inherit}footer{display:none}}
'''
# Insert TOC after overview before the first numbered main section.
toc_html=re.sub(r'<li><a href="[^"]*">2026 年 11 月 2—8 日详细研究计划</a></li>\s*', '', md.toc)
toc='<nav aria-label="文档目录"><details open><summary>阅读导航 · 14 个部分</summary>'+toc_html+'</details></nav>'
body=body.replace('<h2 id="1',toc+'<h2 id="1',1) if '<h2 id="1' in body else toc+body
# markdown's numeric heading ids may be prefixed; use stable insertion before first main numbered section.
if body.startswith(toc):
 body=body[len(toc):]
 match=re.search(r'<h2[^>]*>1\.',body)
 if match:body=body[:match.start()]+toc+body[match.start():]
 else:body=toc+body
out='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="基于服务器实验与MC-MED合作发现的观测策略后训练一周研究计划"><title>观测策略后训练｜11月2—8日研究计划</title><style>'+style+'</style></head><body><header><div class="eyebrow">RESEARCH PLAN · 2026 / 11 / 02—08</div><p>结合 v1.1、服务器实验审计与合作同学的新发现 · 5 张结构图 · 8 篇定向核验论文</p><p><a href="report.md">可编辑 Markdown</a>　·　<a href="literature_audit.md">文献审计附录</a>　·　<a href="server_method_audit.md">服务器方法审计</a></p><p>阅读提示：目录可折叠；窄屏下图表可横向滚动。</p></header><main>'+body+'</main><footer>编制与核验：2026-10-31。本文为研究计划；已完成结果、作者报告与待检验假设均分开标注。主文和图可离线阅读；外部全文链接需联网。</footer></body></html>'
(B/'下周研究计划_20261102-1108.html').write_text(out)
entry=repo/'plans/观测过程建模/观测策略后训练_下周详细计划_20261102-1108.md'
entry.write_text('''# 观测策略后训练：2026-11-02—11-08 详细计划\n\n本计划已结合 v1.1、服务器只读审计和合作同学的 MC-MED 观测过程总结。为避免两份正文漂移，主文集中维护于 research。\n\n- [完整图文阅读版](../../research/观测过程与研究设计/measurement-process-next-week-20261031/下周研究计划_20261102-1108.html)\n- [可编辑 Markdown 主文](../../research/观测过程与研究设计/measurement-process-next-week-20261031/report.md)\n- [服务器方法审计](../../research/观测过程与研究设计/measurement-process-next-week-20261031/server_method_audit.md)\n- [8篇论文阅读与实现约束](../../research/观测过程与研究设计/measurement-process-next-week-20261031/literature_audit.md)\n- [合作实验设计审查](../../research/观测过程与研究设计/measurement-process-next-week-20261031/colleague_design_review.md)\n\n本周最低主线：协议/支持/算子验收，预定目标医院上强表格骨干的 M0/M1b/M2，合作线补齐输入变化、校准和配对损失。神经后训练为条件扩展；当前文档不代表新实验已执行。\n''')
print(json.dumps({'html_bytes':len(out.encode()),'svg_count':out.count('<svg'),'sources':len(external),'local_sources':len(ledger),'entry':str(entry)},ensure_ascii=False))
