"""ICU 科室名称清单（问题单附件 2）：按 flucase 规则集 v0.3 的同一条科室规则，从读取源里数出
每个科室名称对应多少住院，并标出按现行规则算不算 ICU。

为什么需要单独的脚本：std_v3 导出里没有科室名称（encounters 没有 ward 列，alignment_report.json 的
icu 段只有按中心的例数），所以这份清单只能从读取源（GD 原始导出的入院记录、GAM 住院病历的"科室"列）
重新数。判 ICU 的规则直接用 flucase 的 `pipeline/extract/lexicon.py`，与两院线上跑的一致
（ICU_DEPT = ICU|CCU|重症医学|重症监护|监护(室|病房|中心|单元)；NOT_ICU_DEPT = 呼吸与危重症医学科|危重症医学科）。

只输出名称与例数，不输出就诊编号、患者编号、日期和病历文字。

用法（在本机仓库根目录）：
    flucase/backend/.venv/Scripts/python.exe scripts/crf_wide/icu_dept_list.py
    flucase/backend/.venv/Scripts/python.exe scripts/crf_wide/icu_dept_list.py --out tmp/icu_dept_list.md
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[2]
FLUCASE_BACKEND = REPO / "flucase" / "backend"
EXPORT_DIR = REPO / "data" / "export"

GD_DIR = REPO / "data" / "GD" / "GD(1)"
GAM_IP_FILE = REPO / "data" / "raw_20261001b" / "呼吸住院数据(2).xlsx"

ICU_DEPT = r"ICU|CCU|重症医学|重症监护|监护(?:室|病房|中心|单元)"
NOT_ICU_DEPT = r"呼吸与危重症医学科|危重症医学科"


def _load_flucase_lexicon():
    """优先用 flucase 自己的规则；拿不到就用本文件里的同一条正则。"""
    p = FLUCASE_BACKEND / "flucase" / "pipeline" / "extract" / "lexicon.py"
    try:
        spec = importlib.util.spec_from_file_location("flucase_lexicon", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["flucase_lexicon"] = m
        spec.loader.exec_module(m)
        return m.ICU_DEPT, m.NOT_ICU_DEPT, m.is_icu_dept
    except Exception:
        def is_icu_dept(name, rx=ICU_DEPT, not_rx=NOT_ICU_DEPT):
            s = name or ""
            if not re.search(rx, s, re.I):
                return False
            return bool(re.search(rx, re.sub(not_rx, "", s) if not_rx else s, re.I))
        return ICU_DEPT, NOT_ICU_DEPT, is_icu_dept


def _manifest_input_files():
    """从导出的 manifest 里拿输入文件清单（含 sha256），用来核对本地文件是不是同一批。"""
    out = {}
    for p in EXPORT_DIR.rglob("manifest.json"):
        try:
            man = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for name, sha in (man.get("input") or {}).get("files_sha256", {}).items():
            out[name] = sha
    return out


def _sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_key(p: pathlib.Path):
    """把本地文件对应到导出 manifest 里的输入文件名（GD 在 GD.zip/ 下，GAM 在顶层）。"""
    rel = p.relative_to(REPO).as_posix()
    if rel.startswith("data/GD/"):
        return "GD.zip/" + rel[len("data/GD/"):]
    return p.name


def _verify_manifest(used):
    """核对读取的文件与导出 manifest 里的输入文件是同一批（sha256 一致）。"""
    man = _manifest_input_files()
    if not man:
        return None
    out = []
    for rel in used:
        p = REPO / rel
        key = _manifest_key(p)
        want = man.get(key)
        if want is None:
            out.append((rel, "manifest 里没有这个文件"))
            continue
        out.append((rel, "一致" if _sha256(p) == want else "**与 manifest 不一致**"))
    return out


def _read_sheets(p: pathlib.Path):
    """用 pandas 读一个工作簿：{表名: (表头, DataFrame)}。openpyxl 的 read_only 维度不可靠，这里用 pandas。"""
    import pandas as pd

    xl = pd.ExcelFile(p)
    for name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=name, dtype=str)
        if df.empty:
            continue
        yield name, list(df.columns), df


def _pick(head, *cands):
    for i, c in enumerate(head):
        for cand in cands:
            if c == cand:
                return i
    for i, c in enumerate(head):
        for cand in cands:
            if cand in c:
                return i
    return None


def gd_departments():
    """GD：入院记录的入院科室 / 出院科室，按 ENCT_UUID 归住院。"""
    per_enc = defaultdict(set)
    files = sorted(GD_DIR.rglob("入院记录查询_*.xlsx"))
    if not files:
        return {}, []
    used = []
    for f in files:
        used.append(f.relative_to(REPO).as_posix())
        for _sheet, head, df in _read_sheets(f):
            i_uuid = _pick(head, "ENCT_UUID")
            i_in = _pick(head, "入院科室")
            i_out = _pick(head, "出院科室")
            if i_uuid is None or (i_in is None and i_out is None):
                continue
            key_col = df.iloc[:, i_uuid].fillna("").astype(str).str.strip()
            for i in (i_in, i_out):
                if i is None:
                    continue
                vals = df.iloc[:, i].fillna("").astype(str).str.strip()
                for k, v in zip(key_col, vals):
                    if k and v:
                        per_enc[k].add(v)
    return per_enc, used


def gam_departments():
    """GAM：住院病历每份文书一个"科室"列，按关联字段归住院。"""
    per_enc = defaultdict(set)
    if not GAM_IP_FILE.is_file():
        return {}, []
    for _sheet, head, df in _read_sheets(GAM_IP_FILE):
        i_key = _pick(head, "关联字段", "住院号")
        i_dept = _pick(head, "科室")
        if i_key is None or i_dept is None:
            continue
        keys = df.iloc[:, i_key].fillna("").astype(str).str.strip()
        vals = df.iloc[:, i_dept].fillna("").astype(str).str.strip()
        for k, v in zip(keys, vals):
            if k and v:
                per_enc[k].add(v)
    return per_enc, [GAM_IP_FILE.relative_to(REPO).as_posix()]


def counts(per_enc):
    """{科室名: 住院数}（同一次住院算一次）。"""
    c = defaultdict(int)
    for names in per_enc.values():
        for n in names:
            c[n] += 1
    return c


def verdict(name, is_icu_dept):
    if is_icu_dept(name):
        return "算 ICU"
    if re.search(ICU_DEPT, name, re.I):
        return "命中关键词但被规则排除"
    return "不算 ICU"


def main(argv=None):
    ap = argparse.ArgumentParser(description="ICU 科室名称清单（问题单附件 2）")
    ap.add_argument("--out", help="把 markdown 写到文件；不给就打到屏幕上")
    args = ap.parse_args(argv)

    _, _, is_icu_dept = _load_flucase_lexicon()

    gd_enc, gd_files = gd_departments()
    gam_enc, gam_files = gam_departments()
    gd_c = counts(gd_enc)
    gam_c = counts(gam_enc)

    names = sorted(set(gd_c) | set(gam_c), key=lambda n: (-(gd_c.get(n, 0) + gam_c.get(n, 0)), n))

    lines = []
    lines.append("| 科室名称 | 按现行规则算不算 ICU | GD 住院数 | GAM 住院数 |")
    lines.append("|---|---|---|---|")
    for n in names:
        lines.append(f"| {n} | {verdict(n, is_icu_dept)} | {gd_c.get(n, 0)} | {gam_c.get(n, 0)} |")
    lines.append("")

    gd_icu_names = {n for n in gd_c if is_icu_dept(n)}
    gam_icu_names = {n for n in gam_c if is_icu_dept(n)}
    gd_icu_enc = sum(1 for k, v in gd_enc.items() if any(is_icu_dept(x) for x in v))
    gam_icu_enc = sum(1 for k, v in gam_enc.items() if any(is_icu_dept(x) for x in v))
    lines.append(f"- GD 住院数（按 ENCT_UUID）：{len(gd_enc)}；其中科室名命中 ICU 规则的：{gd_icu_enc}")
    lines.append(f"- GAM 住院数（按关联字段）：{len(gam_enc)}；其中科室名命中 ICU 规则的：{gam_icu_enc}")
    lines.append(f"- 出现过 ICU 类名称的住院（GD / GAM）：{gd_icu_enc} / {gam_icu_enc}")
    lines.append(f"- 不同的科室名称：{len(names)}（GD {len(gd_c)}、GAM {len(gam_c)}）")
    lines.append(f"- 读取的文件：{'；'.join(gd_files + gam_files)}")
    verified = _verify_manifest(gd_files + gam_files)
    if verified:
        for rel, state in verified:
            lines.append(f"- 与导出的 manifest 比对：{rel} —— {state}")

    text = "\n".join(lines)
    if args.out:
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"写到 {out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
