"""虚构的"病历系统原始导出"：按人分目录 + 全院汇总表，姓名、号码全部虚构，用来检验扫描脚本的遮蔽。"""
import datetime as dt, random, csv
from pathlib import Path
from openpyxl import Workbook
import docx
random.seed(1)
root = Path("fake_raw/GD导出")
names = ["张三", "李四", "王五", "赵六", "欧阳娜娜", "陈小明"]
ids = ["0012345678", "0012345679", "0012345680", "0012345681", "0012345682", "0012345683"]
# 1 全院汇总：检验结果.xlsx（长表）
wb = Workbook(); ws = wb.active; ws.title = "检验结果"
ws.append(["住院号", "病人姓名", "检验项目", "子项名称", "结果", "单位", "参考范围", "报告时间", "检验医师"])
for n, i in zip(names, ids):
    for k in range(30):
        ws.append([i, n, "血常规", random.choice(["白细胞计数", "血红蛋白", "血小板计数"]), f"{random.uniform(3,10):.2f}", "10^9/L", "3.5-9.5",
                   dt.datetime(2024, 1, 3) + dt.timedelta(hours=k * 7), "刘医生"])
ws2 = wb.create_sheet("张三")          # 故意：以病人姓名命名的工作表
ws2.append(["2024-01-03", "张三", "0012345678"])
wb.save(root.parent / "检验结果.xlsx") if root.parent.exists() else None
root.mkdir(parents=True, exist_ok=True)
wb.save(root / "检验结果.xlsx")
# 2 医嘱：假 xls（其实是 HTML 表）
rows = "".join(f"<tr><td>{i}</td><td>{n}</td><td>奥司他韦胶囊</td><td>75mg</td><td>2024-01-0{k+1} 08:00</td></tr>" for n, i in zip(names, ids) for k in range(3))
(root / "医嘱明细.xls").write_text(f"<html><body><table><tr><th>住院号</th><th>姓名</th><th>医嘱名称</th><th>剂量</th><th>开始时间</th></tr>{rows}</table></body></html>", encoding="gb18030")
# 3 病案首页：GB18030 的 CSV
with open(root / "病案首页.csv", "w", encoding="gb18030", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["病案号", "住院号", "姓名", "性别", "年龄", "入院时间", "出院时间", "身份证号", "联系电话"])
    for n, i in zip(names, ids):
        w.writerow([i[2:], i, n, "男", "78岁", "2024-01-02 10:11", "2024-01-15", "440101194501011234", "13800001111"])
# 4 按人分目录的病历文书（docx），文件名带姓名和号码
for n, i in zip(names, ids):
    d = root / "病历文书" / f"{n}_{i}"
    d.mkdir(parents=True, exist_ok=True)
    for typ in ["入院记录", "首次病程记录", "出院记录"]:
        doc = docx.Document()
        doc.add_paragraph(f"2024-01-02 10:30 {typ}")
        doc.add_paragraph(f"姓名：{n}  住院号：{i}")
        doc.add_paragraph("主诉：发热、咳嗽3天。现病史：患者3天前受凉后出现发热，最高体温39.2℃。既往史：否认高血压。")
        doc.save(d / f"{n}_{typ}.docx")
print("ok")
