from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
INK='#24312d'; MUT='#56655e'; TEAL='#176b5b'; LINE='#b7c3bc'; LIGHT='#e9f2ee'; GREY='#f1f3f1'

def t(x,y,text,size=19,fill=INK,weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(text)}</text>'
def lines(x,y,texts,size=19,fill=INK,weight=400,gap=29,anchor='start'):
    return ''.join(t(x,y+i*gap,txt,size,fill,weight,anchor) for i,txt in enumerate(texts))
def line(x1,y1,x2,y2,color=LINE,width=2,dash=False,arrow=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="7 6"' if dash else '')+(' marker-end="url(#arr)"' if arrow else '')+'/>'
def path(d,color=LINE,width=2,dash=False,arrow=False):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="7 6"' if dash else '')+(' marker-end="url(#arr)"' if arrow else '')+'/>'
def rect(x,y,w,h,fill='white',stroke=LINE,dash=False):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="1.5"'+(' stroke-dasharray="7 6"' if dash else '')+'/>'
def circle(x,y,r=6,fill=TEAL,stroke='none'):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def svg(name,title,desc,height,body):
    s=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {height}" role="img" aria-labelledby="{name}-title {name}-desc">
<title id="{name}-title">{escape(title)}</title><desc id="{name}-desc">{escape(desc)}</desc>
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{TEAL}"/></marker></defs>
<rect width="1000" height="{height}" fill="white"/>
<g font-family="-apple-system,BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif">{body}</g></svg>'''
    s=s.replace('id="arr"',f'id="{name}-arr"').replace('url(#arr)',f'url(#{name}-arr)')
    (OUT/f'{name}.svg').write_text(s,encoding='utf-8')

# Teaching contract: distinguish observed reliance from causal harm and method gain.
b=t(34,45,'证据链：已有发现能推进到哪一步',27,weight=600)
b+=t(34,78,'实线边界＝已有实验支持；虚线边界＝下阶段待检验。箭头表示研究顺序。',18,MUT)
xs=[34,278,522,766]
head=['过程信息有预测力','保值序列的时间敏感性','真实跨院的风险代价','M2 超过强随机增强']
body=[['Process-only 超过患病率基线','加入过程信息可有增量','合作总结 · Stage 1'],['值、顺序、数量、端点固定','部分模型预测仍会改变','合作总结 · Stage 2A-v2'],['同库多医院、共同支持','区分病例构成与标签差异','本周建立可比较协议'],['同骨干、标签与训练预算','主要比较 M2 − M1b','本周完成最小试点']]
for i,x in enumerate(xs):
    b+=rect(x,124,202,210,LIGHT if i<2 else 'white',TEAL if i<2 else MUT,i>=2)
    b+=t(x+14,157,str(i+1).zfill(2),18,TEAL,600)
    # Long heading on two lines.
    hh=['保值序列的','时间敏感性'] if i==1 else [head[i]]
    b+=lines(x+14,190,hh,20,INK,600,gap=27)
    by=254 if i==1 else 239
    bb=body[i]
    # narrow labels explicitly split to keep 202-px columns legible
    if i==0: bb=['过程信息与结局相关','加入数值后仍可有增量','合作总结 · Stage 1']
    if i==1: bb=['值序列及数量不变','部分模型预测改变','Stage 2A-v2']
    if i==2: bb=['同库多医院、共同支持','拆查病例与标签差异','建立可比较协议']
    if i==3: bb=['同模型与信息预算','主要比较 M2 − M1b','最小后训练试点']
    b+=lines(x+14,by,bb,17,MUT,gap=25)
    if i<3:b+=line(x+208,223,x+237,223,TEAL,2,dash=i>=1,arrow=True)
b+=line(34,373,968,373,LINE)
b+=t(34,411,'关键边界：预测会变 ≠ 变化有害；保留值序列 ≠ 保留完整生理时间信息。',20,TEAL,600)
b+=t(34,447,'医院身份可被识别，也不等于该信息必然损害结局预测。',18,MUT)
svg('evidence_chain','从记录过程信息到后训练收益的证据链','已有过程信息和时间扰动证据不能直接推出有害的医院策略偏差。真实跨院风险代价与结构化增强超过随机增强仍待检验。',480,b)

# Teaching contract: visualize what moves and what disappears under each operator.
b=t(34,45,'两种干预回答不同问题',27,weight=600)
b+=t(34,77,'虚构数值与时间轴，仅说明操作；不代表实验结果或预期提升。',18,MUT)
b+=t(34,122,'A  保留值序列，移动中间时间',22,TEAL,600)
start=250; end=910; scale=(end-start)/8
for yy,label,ts in [(180,'原始时间',[0,2,5,8]),(270,'时间重排',[0,1,6,8])]:
    b+=t(36,yy+6,label,19)
    b+=line(start,yy,end,yy,LINE)
    for time,val in zip(ts,[80,92,85,90]):
        xx=start+time*scale
        b+=circle(xx,yy,6,TEAL)+t(xx,yy-18,str(val),19,INK,500,'middle')+t(xx,yy+31,f'{time} h',17,MUT,400,'middle')
b+=line(start+2*scale,226,start+1*scale,226,TEAL,1.6,True,True)
b+=line(start+5*scale,226,start+6*scale,226,TEAL,1.6,True,True)
b+=t(36,333,'固定：值、顺序、数量、首末位置。可能改变：变化速度、持续时间、跨通道相位。',18,MUT)
b+=line(34,359,966,359,LINE)
b+=t(34,406,'B  原有时间不动，只删观测',22,TEAL,600)
base=[0,1,2,3,4,5,6,7,8]
for yy,label,keep in [(461,'源记录',base),(529,'稀疏化视图',[0,2,5,8])]:
    b+=t(36,yy+6,label,19)
    b+=line(start,yy,end,yy,LINE)
    for time in base:
        xx=start+time*scale
        if time in keep: b+=circle(xx,yy,6,TEAL)
        else:
            b+=circle(xx,yy,5,'white',LINE)
            b+=line(xx-5,yy-5,xx+5,yy+5,MUT,1.5)
b+=t(36,579,'固定：所有保留值及其原时间戳。改变：可见信息量与记录过程表征。',18,MUT)
b+=lines(36,626,['M1a：总删减量匹配的随机删减','M1b：进一步匹配通道 × 时段预算的随机删减','M2：在相同预算与共同支持内，依赖可见历史选择删减'],19,gap=32)
b+=t(36,744,'比较 M2 与 M1b，才能判断历史依赖结构是否带来额外收益。',20,TEAL,600)
svg('timing_vs_thinning','时间重排与只删观测的操作区别','时间重排固定数值序列但改变间隔。稀疏化保留原时间但丢失部分信息。三种增强需要匹配预算后比较。',780,b)

# Teaching contract: locate hospital and patient boundaries and label-free target adaptation.
b=t(34,45,'数据边界：每个目标医院都有独立 support / query',27,weight=600)
b+=t(34,79,'拟议新协议；医院数与患者归属周一锁定。目标院适配只使用 support 输入。',18,MUT)
b+=t(34,130,'源库 · MIMIC-IV',21,TEAL,600)
b+=rect(34,153,400,92,LIGHT,TEAL)+lines(51,185,['train：源带标签数据与源模型','val：源侧选择与保持评估'],19,gap=30)
b+=line(446,198,510,198,TEAL,2,arrow=True)
b+=rect(527,153,438,92,'white',TEAL)+lines(544,185,['M0 / M1a / M1b / M2 共享源标签','骨干、输入、更新步数与预算保持可比'],19,gap=30)
b+=t(34,294,'eICU · 36 家原 tune 医院：本周按医院划为三组',21,TEAL,600)
cols=[(34,268,['策略库医院','支持范围与策略候选','不提供目标适配标签']),(348,268,['开发医院','每院独立 support / query','query 标签选全局超参']),(662,303,['本轮留出医院','每院独立 support / query','query 标签锁定至最终评价'])]
for x,w,txt in cols:
    b+=rect(x,318,w,126,'white',TEAL)
    b+=lines(x+17,353,txt,18,gap=31)
b+=t(34,481,'患者层：每个开发 / 留出医院 h 内，support 与 query 按患者互斥。',19,TEAL,600)
b+=t(34,515,'处理跨院重复患者时保持医院留出边界；归侧或排除规则先登记。',18,MUT)
b+=line(34,540,966,540,LINE)
b+=t(34,581,'逐目标院的适配与评价流程',21,TEAL,600)
# Two-level flow: independent support supplies q_h; source labels alone train f_h.
b+=rect(34,609,188,82,LIGHT,TEAL)+lines(50,642,['目标院 support X','仅输入，无标签'],18,gap=27)
b+=line(234,650,277,650,TEAL,2,arrow=True)
b+=rect(290,609,150,82,'white',TEAL)+lines(307,642,['拟合 q_h','医院记录策略'],18,gap=27)
b+=line(452,650,495,650,TEAL,2,arrow=True)
b+=rect(508,609,244,82,'white',TEAL)+lines(525,631,['源带标签数据增强','树：重拟合','神经：同 checkpoint 适配'],17,gap=25)
b+=line(764,650,807,650,TEAL,2,arrow=True)
b+=rect(820,609,145,82,LIGHT,TEAL)+lines(837,642,['得到 f_h','该院预测器'],18,gap=27)
b+=t(508,724,'训练标签仅来自 MIMIC',18,TEAL,600)
b+=path('M 892 703 L 892 769 L 765 769',TEAL,2,False,True)
b+=rect(34,731,332,78,'white',TEAL)+lines(51,763,['该院 query X：仅供推理','不进入 q_h 拟合或模型适配'],18,gap=27)
b+=line(378,769,421,769,TEAL,2,arrow=True)
b+=rect(434,731,318,78,'white',TEAL)+lines(451,763,['配对预测与评价','开发选参 / 留出仅最终评价'],18,gap=27)
b+=line(34,843,966,843,LINE)
b+=rect(34,869,931,123,GREY,MUT)
b+=t(51,903,'159 家历史 eval 医院：本周不重复评价',21,INK,600)
b+=lines(51,935,['历史结果已被查阅；AL4 使用过其无标签输入。不能重新命名为全新盲测集。','后续确认性证据：另行登记未触达数据 / 新外部库，并审查既往使用历史。'],18,MUT,gap=30)
svg('split_boundary','逐目标医院的support与query协议','36家原tune医院划为策略库、开发和本轮留出。每个开发与留出医院按患者划分support与query。support输入估计q_h，以源带标签数据增强，树模型重拟合、神经模型从共同checkpoint适配出f_h，再对该院query推理。开发query标签仅选全局超参，留出query标签锁定到最终评价。159家历史eval本周不重评。',1028,b)

# Teaching contract: make task dependencies and daily deliverables visible.
b=t(34,45,'11 月 2—8 日：七天的依赖与交付',27,weight=600)
b+=t(34,79,'这是计划顺序，不是已完成进度。上一环节未验收，下一环节保持缩小范围。',18,MUT)
b+=t(261,128,'当天主任务',18,MUT,600)+t(637,128,'当日验收物',18,MUT,600)
rows=[('11/02 · 一','冻结问题与信息边界','协议、版本、切分审计'),('11/03 · 二','理论模拟与策略初稿','oracle / 可见历史分开'),('11/04 · 三','策略拟合与顺序稀疏化','支持审计与输入不变量'),('11/05 · 四','建立公平 M0 / M1 对照','共同预算与可复现基线'),('11/06 · 五','M2；条件允许才神经冒烟','M2 − M1b 配对预测'),('11/07 · 六','统计分析与合作发现复核','不确定性、校准与分层图'),('11/08 · 日','复现与科研决策','结果包、未决项、后续预算')]
for i,(day,task,deliver) in enumerate(rows):
    yy=181+i*74
    b+=t(34,yy+5,day,19,TEAL,600)
    b+=circle(220,yy,7,TEAL)
    if i<6:b+=line(220,yy+11,220,yy+61,TEAL,2,arrow=True)
    b+=t(261,yy+5,task,20,INK,500)
    b+=t(637,yy+5,deliver,18,MUT)
    if i<6:b+=line(261,yy+34,963,yy+34,LINE,1)
b+=line(34,678,966,678,LINE)
b+=t(34,714,'并行分工：合作同学复核 timing 机制证据；主线检验结构化增强是否超过随机增强。',18,MUT)
svg('week_gantt','下周七日依赖计划','周一协议、周二模拟、周三稀疏化验收、周四基线、周五M2、周六统计、周日复现决策。每一步有具体验收物。',748,b)

# Teaching contract: distinguish implementation failure, estimand reach, and statistical outcomes.
b=t(34,45,'周日决策：依据证据类型分流',27,weight=600)
b+=t(34,79,'以 M2 对预算匹配 M1b 的原始概率评分差为主；负向损失越低越好。',18,MUT)
b+=rect(34,119,326,69,LIGHT,TEAL)+t(51,162,'输入、切分、预算验收通过？',20,INK,600)
b+=line(372,154,447,154,TEAL,2,arrow=True)+t(391,137,'否',18,MUT)
b+=lines(466,148,['修实现与协议；结果暂不作科学判断。'],19)
b+=line(196,200,196,234,TEAL,2,arrow=True)+t(211,224,'是',18,MUT)
b+=rect(34,246,326,69,LIGHT,TEAL)+t(51,289,'目标策略在共同支持范围内？',20,INK,600)
b+=line(372,280,447,280,TEAL,2,arrow=True)+t(391,263,'不足',18,MUT)
b+=lines(466,274,['缩小可实现策略范围，报告覆盖比例；','不向源记录更密的区域外推。'],19,gap=28)
b+=line(196,327,196,361,TEAL,2,arrow=True)+t(211,351,'足够',18,MUT)
b+=t(34,400,'在相同评价患者上比较 M2 − M1b',22,TEAL,600)
b+=line(34,420,966,420,LINE)
results=[('区间宽','未判定','给出精度不足的来源和后续样本 / 计算需求。'),('接近且区间窄','随机增强已足够','收窄方法主张；不靠堆模型掩盖零增量。'),('稳定改善','进入下一阶段','增加模型与医院验证，并落实最接近的基线。'),('评分变差','检查机制与实现','核对过删、信息损失、病例构成与策略误估。')]
for i,(signal,decision,detail) in enumerate(results):
    yy=462+i*82
    b+=t(34,yy,signal,20,INK,600)+t(268,yy,decision,20,TEAL,600)
    b+=t(268,yy+29,detail,18,MUT)
    if i<3:b+=line(34,yy+51,966,yy+51,LINE,1)
b+=line(34,778,966,778,LINE)
b+=t(34,816,'PEF 是描述性比率；不用 PEF ≥ 0.3 或单一显著性阈值决定本周是否继续。',19,TEAL,600)
svg('decision_gate','周日科研决策树','先验收实现和共同支持，再区分未判定、随机增强足够、稳定增益和有害。PEF不作为硬门槛。',852,b)
print('\n'.join(str(p) for p in OUT.glob('*.svg')))
