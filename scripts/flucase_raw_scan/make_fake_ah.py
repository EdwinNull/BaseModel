"""虚构的“科室数据统计”式导出，用来自测 ah_raw_probe.py 的遮蔽（AH 的真实格式还不知道，按科室自己整理的统计表常见写法虚构）。

一个工作簿三张表：患者统计（宽表，中文表头，一次住院一行，症状 / 基础病 / 检验 / 治疗 / 结局各一列）、检验明细（长表）、病程记录（长文字）。
姓名、号码、正文全部虚构；故意在备注和正文里写姓名、电话，并让一个虚构医生的名字作为“记录类型”出现在 ≥10 次住院里，检查报告不出现这些。

用法（flucase 的 venv）：flucase/backend/.venv/bin/python scripts/flucase_raw_scan/make_fake_ah.py <输出目录>
"""
from __future__ import annotations

import random
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook

FAKE_NAMES = ["赵小明", "钱多多", "孙悟能", "李逍遥", "周芷若", "吴有才", "郑美丽", "王大锤", "冯宝宝", "陈一发"]
FAKE_DOCTOR = "王建国"
FAKE_PHONE = "13900001111"

out = Path(sys.argv[1] if len(sys.argv) > 1 else "fake_ah")
shutil.rmtree(out, ignore_errors=True)
out.mkdir(parents=True)
rnd = random.Random(20261111)

wb = Workbook()
ws = wb.active
ws.title = "流感患者统计"
head = ["序号", "住院号", "姓名", "性别", "年龄", "联系电话", "入院日期", "出院日期", "住院天数", "主治医生", "发热", "最高体温", "咳嗽", "咳痰",
        "咽痛", "肌痛", "乏力", "呼吸困难", "基础疾病", "COPD", "冠心病", "糖尿病", "甲流抗原", "乙流抗原", "流感核酸", "白细胞", "中性粒细胞绝对值",
        "淋巴细胞绝对值", "CRP", "PCT", "胸部CT", "吸氧方式", "无创通气", "有创通气", "转入ICU", "奥司他韦", "玛巴洛沙韦", "出院诊断", "转归", "备注"]
ws.append(head)
lab = []
notes = []
yn = lambda p: "是" if rnd.random() < p else "否"  # noqa: E731
for i in range(120):
    mrn = f"{8800000 + i * 7}"
    name = FAKE_NAMES[i % len(FAKE_NAMES)]
    adm = datetime(2023, 11, 1) + timedelta(days=rnd.randint(0, 150), hours=rnd.randint(0, 23))
    los = rnd.randint(3, 20)
    dx = "J11.100 流行性感冒, J18.900 肺炎" + (", I10.x00 高血压" if rnd.random() < .5 else "") + (", J96.000 呼吸衰竭" if rnd.random() < .2 else "")
    ws.append([i + 1, mrn, name, rnd.choice(["男", "女"]), rnd.randint(60, 95), FAKE_PHONE, adm.date(), (adm + timedelta(days=los)).date(), los,
               FAKE_DOCTOR, yn(.8), round(rnd.uniform(36.5, 40.2), 1), yn(.9), yn(.6), yn(.3), yn(.2), yn(.5), yn(.3),
               rnd.choice(["高血压、糖尿病", "慢阻肺", "无", f"冠心病（{name}自述）"]), yn(.2), yn(.2), yn(.3),
               rnd.choice(["阳性", "阴性", "未检"]), rnd.choice(["阴性", "未检"]), rnd.choice(["阳性", "阴性", ""]),
               round(rnd.uniform(2, 18), 2), round(rnd.uniform(1, 15), 2), round(rnd.uniform(.2, 3), 2), round(rnd.uniform(1, 150), 1),
               round(rnd.uniform(.02, 5), 2), rnd.choice(["双肺炎症", "未见异常", f"右下肺渗出，{name}复查"]),
               rnd.choice(["鼻导管", "面罩", "高流量", "未吸氧"]), yn(.1), yn(.05), yn(.08), yn(.7), yn(.2), dx,
               rnd.choice(["好转", "治愈", "死亡", "自动出院"]), f"家属{name}电话{FAKE_PHONE}"])
    for item, unit in (("白细胞计数", "10^9/L"), ("C反应蛋白", "mg/L"), ("降钙素原", "ng/mL"), ("甲型流感病毒抗原", "")):
        lab.append([mrn, item, f"{rnd.uniform(1, 20):.2f}" if unit else rnd.choice(["阳性", "阴性"]), unit, "", adm + timedelta(hours=rnd.randint(1, 48))])
    for k in range(2):
        notes.append([mrn, adm + timedelta(days=k), f"{FAKE_DOCTOR}查房记录" if k == 0 else "日常病程记录",
                      f"患者{name}，主诉：发热咳嗽3天。现病史：……予鼻导管吸氧2L/min。家属电话{FAKE_PHONE}。{FAKE_DOCTOR}医师查房后指示……" * 3])
ws2 = wb.create_sheet("检验明细")
ws2.append(["住院号", "检验项目", "结果", "单位", "参考范围", "报告时间"])
for r in lab:
    ws2.append(r)
ws3 = wb.create_sheet("病程记录")
ws3.append(["住院号", "记录时间", "记录类型", "内容"])
for r in notes:
    ws3.append(r)
p = out / "虚构_呼吸内二科数据统计.xlsx"
wb.save(p)
print(p)
