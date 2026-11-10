# -*- coding: utf-8 -*-
"""
从本地论文 PDF 裁出汇报 v2 用的原图（PPT/素材/论文原图_20261026/*.png）。

PDF 在 paper/数据集构建调研_20261025/（第三方 PDF，不入库）。裁出的图同样是第三方材料：
MIMIC-IV（Sci Data，CC BY 4.0）、CLIF（medRxiv 预印本，CC BY 4.0）、ACES（ICLR 2025）、
Lauritsen 2021（npj Digit Med，CC BY 4.0）、ISARIC 4C Deterioration（Lancet Respir Med，CC BY 4.0）。
幻灯片上每张图都注明了出处与页码；按仓库约定只放本地，是否入库由研究者定。

做法：整页按 300 dpi 渲染 → 按框裁切（框坐标以 110 dpi 页面像素记）→ 去掉四周白边。
渲染优先用 PyMuPDF（pip install pymupdf），没有就用 poppler 的 pdftoppm。

运行（BaseModel 根目录）：python PPT/脚本/extract_paper_figures_20261026.py
依赖：Pillow；PyMuPDF 或 pdftoppm
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "paper" / "数据集构建调研_20261025"
OUT_DIR = Path(__file__).resolve().parents[1] / "素材" / "论文原图_20261026"
DPI = 300
S = DPI / 110  # 框坐标按 110 dpi 记录

# (输出文件, PDF 相对路径, 页码（从 1 起）, 裁切框 (x0, y0, x1, y1)，110 dpi 像素)
FIGS = [
    ("MIMIC-IV_Fig1.png", "01_数据库范本/01_MIMIC-IV_2023.pdf", 2, (140, 62, 856, 395)),
    ("CLIF_Fig1.png", "02_多中心协调与公共数据模型/08_CLIF_2025.pdf", 13, (82, 198, 870, 892)),
    ("CLIF_Fig2A.png", "02_多中心协调与公共数据模型/08_CLIF_2025.pdf", 14, (58, 143, 736, 452)),
    ("ACES_Fig4.png", "03_队列_时间零点_标签/18_ACES_2025.pdf", 7, (168, 294, 772, 826)),
    ("ISARIC4C_Fig2.png", "03_队列_时间零点_标签/16_ISARIC_4C_Deterioration_2021.pdf", 8, (52, 193, 870, 428)),
]
# Lauritsen 2021 图 2：上半部（a–d 四种取样方式）+ 图例，上下拼接
LAURITSEN = ("Lauritsen_Fig2_ad.png", "03_队列_时间零点_标签/12_Lauritsen_framing_2021.pdf", 5,
             [(86, 86, 874, 590), (86, 800, 874, 822)])


def render(pdf, page, tmp):
    """整页渲染成 PIL 图像。"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf))
        pix = doc[page - 1].get_pixmap(dpi=DPI)
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    except ImportError:
        exe = shutil.which("pdftoppm")
        if not exe:
            raise SystemExit("需要 PyMuPDF（pip install pymupdf）或 poppler 的 pdftoppm")
        stem = Path(tmp) / f"p{page}"
        subprocess.run([exe, "-r", str(DPI), "-png", "-singlefile", "-f", str(page), "-l", str(page),
                        str(pdf), str(stem)], check=True)
        return Image.open(f"{stem}.png").convert("RGB")


def trim(im, pad=12, thresh=245):
    """去掉四周白边，留 pad 像素。"""
    mask = im.convert("L").point(lambda v: 255 if v < thresh else 0)
    bbox = mask.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


def cut(page_img, box):
    return page_img.crop(tuple(int(round(v * S)) for v in box))


def main():
    OUT_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(OUT_DIR)) as tmp:
        for name, rel, page, box in FIGS:
            img = trim(cut(render(PDF_DIR / rel, page, tmp), box))
            if name.startswith("ISARIC"):
                # 去掉 Lancet 的图框细线：向内收 16 像素再去白边
                img = trim(img.crop((16, 16, img.width - 16, img.height - 16)))
            img.save(OUT_DIR / name, optimize=True)
            print(name, img.size)
        name, rel, page, boxes = LAURITSEN
        page_img = render(PDF_DIR / rel, page, tmp)
        top, leg = (cut(page_img, b) for b in boxes)
        canvas = Image.new("RGB", (max(top.width, leg.width), top.height + leg.height + 10), "white")
        canvas.paste(top, (0, 0))
        canvas.paste(leg, (0, top.height + 10))
        img = trim(canvas)
        img.save(OUT_DIR / name, optimize=True)
        print(name, img.size)


if __name__ == "__main__":
    main()
