"""虚构的 GAM 原始导出（住院、门诊用 flucase 的虚构样例生成器；急诊、护理记录按常见写法虚构），用来自测 gam_raw_probe.py 的遮蔽。

护理记录的真实列名还不知道（等扫描报告），这里一张宽表（每个体征一列）、一张长表（项目 + 值）两种都放；姓名、号码、正文全部虚构，
并故意在正文里写姓名和电话，检查报告里不出现。

用法（flucase 的 venv）：flucase/backend/.venv/Scripts/python.exe scripts/flucase_raw_scan/make_fake_gam.py <输出目录>
"""
from __future__ import annotations

import random
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook, load_workbook

from flucase.synth.raw_export import generate

out = Path(sys.argv[1] if len(sys.argv) > 1 else "fake_gam")
shutil.rmtree(out, ignore_errors=True)
out.mkdir(parents=True)
paths = generate(out / "_tmp")["files"]
shutil.move(str(paths["GAM_IP"]), out / "虚构_GAM_住院.xlsx")
shutil.move(str(paths["GAM_OP"]), out / "虚构_GAM_门诊.xlsx")
shutil.copy(out / "虚构_GAM_门诊.xlsx", out / "虚构_GAM_急诊.xlsx")
shutil.rmtree(out / "_tmp")

# 住院的关联字段、病人ID（护理记录挂到这些住院上）
wb = load_workbook(out / "虚构_GAM_住院.xlsx", read_only=True)
ws = wb["住院病历"]
rows = list(ws.iter_rows(values_only=True))
head = list(rows[0])
keys = sorted({(r[head.index("关联字段")], r[head.index("病人ID")]) for r in rows[1:] if r[0]})
wb.close()

rng = random.Random(27)
wide = Workbook()
a = wide.active
a.title = "护理记录"
a.append(["关联字段", "病人ID", "姓名", "科室", "记录时间", "体温", "脉搏", "呼吸", "血压", "血氧饱和度", "吸氧方式", "氧流量(L/min)",
          "意识", "护理级别", "病情观察及措施", "护士签名"])
long = Workbook()
b = long.active
b.title = "体征记录"
b.append(["住院号", "患者ID", "项目名称", "测量值", "单位", "测量时间", "录入人"])
for k, (key, pid) in enumerate(keys):
    t = datetime(2024, 1, 3, 8) + timedelta(days=k * 2)
    for i in range(12):
        tt = t + timedelta(hours=4 * i)
        o2 = rng.choice(["未吸氧", "鼻导管", "鼻导管", "面罩", "高流量"])
        a.append([key, pid, f"示例{k}号", rng.choice(["呼吸病房(8区)", "ICU重症监护病房", "急诊留观"]), tt.strftime("%Y-%m-%d %H:%M"),
                  round(rng.uniform(36.2, 39.4), 1), rng.randint(70, 120), rng.randint(16, 32), f"{rng.randint(100, 160)}/{rng.randint(60, 95)}",
                  rng.randint(86, 99), o2, None if o2 == "未吸氧" else rng.choice([2, 3, 5, 40]), rng.choice(["清醒", "清醒", "嗜睡"]),
                  rng.choice(["一级护理", "特级护理", "二级护理"]),
                  f"患者示例{k}号，家属电话13800001111，昨日至今晨无发热，予{o2}吸氧，SpO2 9{rng.randint(0, 9)}%。", "示例护士"])
        for item, unit, lo, hi in (("体温", "℃", 36.0, 39.5), ("脉搏", "次/分", 60, 130), ("呼吸", "次/分", 14, 34), ("血氧饱和度", "%", 85, 100)):
            b.append([key, pid, item, round(rng.uniform(lo, hi), 1), unit, tt, "示例护士"])
wide.save(out / "虚构_GAM_护理记录.xlsx")
long.save(out / "虚构_GAM_护理体征长表.xlsx")
print(f"写到 {out}：{len(keys)} 次住院的护理记录")
