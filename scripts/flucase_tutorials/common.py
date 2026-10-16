# flucase 测试教程的内容描述：每份教程写成一份 JSON，由 render.js 渲染成 .docx。截图全部来自虚构数据。
# 行内标记：**粗体**、`代码`。
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]          # BaseModel
WORK = ROOT / "tmp" / "flucase_tutorial"            # 截图与中间产物（tmp/ 已 gitignore，只留本机）
SHOTS = WORK / "shots"
IMG = WORK / "img"
SPEC = WORK / "spec"
DATE = "20261016"
# 截图对应的 flucase 版本（10-16 测试问题修复合并到 main 之后）
VERSION = "main c5575d6"
IMG.mkdir(parents=True, exist_ok=True)
SPEC.mkdir(parents=True, exist_ok=True)


def img(name: str, crop: tuple[int, int, int, int] | None = None) -> dict:
    """截图统一成 1440 宽（少数几张截于 1690 宽的窗口），可裁剪；存 PNG，返回路径与像素尺寸。"""
    out = IMG / (name + ("" if not crop else "_" + "_".join(map(str, crop))) + ".png")
    if True:   # 每次重新生成（覆盖旧文件）
        im = Image.open(SHOTS / f"{name}.png").convert("RGB")
        if im.width != 1440:
            im = im.resize((1440, round(im.height * 1440 / im.width)), Image.LANCZOS)
        if crop:
            im = im.crop(crop)
        else:
            im = trim_bottom(im)
        im.save(out, optimize=True)
    w, h = Image.open(out).size
    return {"path": str(out), "w": w, "h": h}


def trim_bottom(im: Image.Image, margin: int = 24) -> Image.Image:
    """裁掉主内容区（侧栏右边）底部大块的空白背景，至少留 360 像素高。"""
    import numpy as np
    a = np.asarray(im).astype(int)
    h = a.shape[0]
    main = a[:, 230:1420, :]
    bg = main[h - 3, -5, :]
    diff = np.abs(main - bg).max(axis=2).max(axis=1)
    rows = np.nonzero(diff > 8)[0]
    last = int(rows.max()) if len(rows) else h - 1
    cut = min(h, max(last + margin, 360))
    return im.crop((0, 0, im.width, cut)) if cut < h - 40 else im


def fig(name: str, caption: str, crop=None) -> dict:
    return {"fig": {**img(name, crop), "caption": caption}}


def p(text: str) -> dict:
    return {"p": text}


def small(text: str) -> dict:
    return {"small": text}


def bullets(items: list[str], ordered: bool = False) -> dict:
    return {"list": items, "ordered": ordered}


def box(kind: str, title: str | None, items: list[str] | str) -> dict:
    """kind: info / warn"""
    return {"box": {"kind": kind, "title": title, "items": items if isinstance(items, list) else [items]}}


def table(head: list[str], rows: list[list[str]], widths: list[int] | None = None) -> dict:
    """widths：各列占比（加起来随意，渲染时按版心宽度折算）"""
    return {"table": {"head": head, "rows": rows, "widths": widths or [1] * len(head)}}


def code(text: str) -> dict:
    return {"code": text}


def h3(text: str) -> dict:
    return {"h3": text}


def step(no: str, title: str, do=None, see=None, figs=None, note=None, tip=None, code=None) -> dict:
    """一步：操作 / 应该看到 两栏，提示框，截图，“已知问题”框。figs: [(截图名, 说明[, 裁剪])]"""
    return {"step": {"no": no, "title": title, "do": do or [], "see": see or [], "tip": tip, "code": code,
                     "figs": [fig(*f)["fig"] for f in (figs or [])],
                     "note": note if (note is None or isinstance(note, list)) else [note]}}


def write(spec: dict) -> Path:
    out = SPEC / (Path(spec["file"]).stem + ".json")
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


FOOT = (f"截图来自 2026-10-16 测试问题修复后的本机正式模式测试（flucase {VERSION}，FLUCASE_ENV=prod），病例、姓名、编号全部虚构，本文不含任何真实病例。"
        "真实数据测试时只回报计数、问题代码、页面现象和原表列名，不发病例内容，也不发带病例信息的截图。")
