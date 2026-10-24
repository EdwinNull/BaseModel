"""build_crf_workbook.py 的测试。只用虚构数据：测试里现场生成 std_v3 形状的导出（编号、名称全是虚构的）。

运行（仓库根目录）：flucase/backend/.venv/Scripts/python.exe -m pytest scripts/crf_wide -q -p no:cacheprovider
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_crf_workbook as B  # noqa: E402

T0 = datetime(2025, 12, 1, 8, 0)
GROUPS = (("GD", "inpatient", 12), ("GAM", "inpatient", 12), ("GAM", "ed", 11))
RULESET = "guideline2025_v0.3"
SHEETS = ["01_就诊与人口学", "02_流感检测", "03_基础病", "04_症状", "05_生命体征", "06_检验", "07_影像", "08_治疗", "09_并发症与诊断",
          "10_结局与去向", "11_分级时间线", "12_候选结局", "13_记录质量", "14_其他数据项"]


def _t(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _module(var: str) -> str:
    for pre, m in (("VS", "vital"), ("LAB", "lab"), ("EXT_", "lab"), ("SYM", "symptom"), ("COM", "comorbidity"), ("TRT", "treatment"),
                   ("CLP", "complication"), ("IMG", "imaging"), ("FLU", "flu"), ("OUT", "crf_outcome")):
        if var.startswith(pre):
            return m
    return "other"


def make_export(root: Path, version: str = "std_v3_20261101", generated: str = "2026-11-01T10:00:00+08:00", groups=GROUPS,
                lab_shift: float = 0.0, extra_col: bool = True) -> Path:
    """一份虚构的 std_v3 导出（解开后的目录）。"""
    d = root / version
    d.mkdir(parents=True)
    enc, ev, st, oc = [], [], [], []
    for site, setting, n in groups:
        for i in range(n):
            tag = "E" if setting == "ed" else "T"
            eid, pid, t0 = f"{site}:{tag}{i:05d}", f"{site}:P{tag}{i:05d}", T0 + timedelta(days=i)
            age = 58.0 + 2 * i
            row = {c: None for c in B.NEED["encounters"]}
            row.update(site=site, patient_id=pid, encounter_id=eid, source=f"REPO_{site}", setting=setting, age=age, sex="MF"[i % 2],
                       bmi=22.0 + i % 5, t0=_t(t0), t0_precision="minute", t0_rule="入院记录的入院时间" if setting == "inpatient" else "门诊就诊时间",
                       onset_date=(t0 - timedelta(days=2)).strftime("%Y-%m-%d"), onset_source="主诉解析", onset_to_t0_days=2.0,
                       fever_status="yes", fever_basis="测得体温 ≥37.3℃", flu_confirmed="yes", obese="no",
                       high_risk="年龄 ≥65 岁" if age >= 65 else None, vaccine="unrecorded",
                       discharge_time=_t(t0 + timedelta(days=5)) if setting == "inpatient" else None, discharge_precision="minute",
                       discharge_status="出院" if setting == "inpatient" else "普通门诊", died=False,
                       followup="complete" if setting == "inpatient" else "unknown", index_admitted=False, ruleset_version=RULESET,
                       icu="unrecorded", icu_periop=False, flu_season="2025-26", season_index="index", run_id=1)
            row.update({c: "yes" if c == "COM001" and i % 3 == 0 else "unrecorded" for c in B.COMORBID})
            if extra_col:
                row["source_kind"] = "示例来源"
            enc.append(row)

            def add(var, h, value=None, text=None, state="pos", unit=None, marks=None, o2=None, end_h=None, label=None, prec="minute"):
                ev.append({"event_id": f"{eid}-{len(ev):06d}", "site": site, "encounter_id": eid, "source": f"REPO_{site}", "var": var,
                           "label": label or B.NAMES.get(var, var), "module": _module(var), "state": state, "value": value, "value_text": text,
                           "unit": unit, "time": None if h is None else _t(t0 + timedelta(hours=h)), "time_precision": prec if h is not None else "unknown",
                           "t_rel_h": None if h is None else float(h), "method": "structured", "reviewed": False, "changed_by_review": False,
                           "rule_id": "MAP-TEST", "time_kind": "measured", "end": None if end_h is None else _t(t0 + timedelta(hours=end_h)),
                           "end_precision": None if end_h is None else "minute", "o2_status": o2, "marks": marks})
            for h, v in ((-30, 37.0), (2, 38.5), (10, 39.2), (50, 37.1)):
                add("VS001", h, v, unit="℃")
            if site == "GD" and i == 0:
                add("VS001", 3, 99.0, unit="℃", marks="implausible")
            add("VS006", 1, 95.0, unit="%", o2="空气")
            add("LAB006", 5, 10.0 + i + lab_shift, unit="mg/L")
            add("SYM001", 0, prec="note")
            add("SYM007", 0, state="neg", prec="note")
            add("TRT001", 4, text="示例抗病毒药", end_h=100)
            if i % 2 == 0:
                add("CLP001", 6)
            add("NEWX001", 7, 3.5, unit="分", label="NEWX001")                     # 本脚本不认识的编码
            add("LABX:示例检验项目", 8, 1.2, unit="g/L", label="示例检验项目")       # 未映射检验
            add("DX:J11.101", None, label="流行性感冒")
            add("FLU_TEST", 1, text="甲型流感病毒核酸：阳性")
            if setting == "inpatient" and i % 2 == 0:
                for layer in ("auto", "effective"):
                    common = {"encounter_id": eid, "layer": layer, "level": "severe", "start": _t(t0 + timedelta(hours=30)), "ruleset_version": RULESET}
                    st.append({**common, "row_type": "band", "end": _t(t0 + timedelta(hours=80))})
                    st.append({**common, "row_type": "criterion", "criterion": "RR30 呼吸≥30", "kind": "physiologic", "basis": "guideline", "precision": "minute"})
            for name in (("D0", "O1", "O2") if setting == "inpatient" else ("O3", "O3_7d")):
                val = ("event" if i % 2 == 0 else "no_event") if setting == "inpatient" else "unknown"
                for layer in ("auto", "effective"):
                    oc.append({"site": site, "encounter_id": eid, "source": f"REPO_{site}", "setting": setting, "outcome": name, "variant": "primary",
                               "layer": layer, "value": val, "event_time": None, "reason": None, "ruleset_version": RULESET, "candidate": True})
    st_cols = ["encounter_id", "layer", "row_type", "level", "start", "end", "criterion", "kind", "basis", "evidence_id", "precision", "ruleset_version"]
    tables = {"encounters": pd.DataFrame(enc), "events": pd.DataFrame(ev), "severity_timeline": pd.DataFrame(st, columns=st_cols),
              "outcomes": pd.DataFrame(oc), "review": pd.DataFrame(columns=["ext_id", "encounter_id", "item_type", "field", "decision"])}
    for name, df in tables.items():
        df.to_parquet(d / f"{name}.parquet", index=False)
    pd.DataFrame([{"code": "NEWX001", "label": "新数据项示例", "origin": "测试"}]).to_csv(d / "codes.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"layer": "分析层", "table": "encounters", "column": "source_kind", "type": "string", "description": "来源类型（示例）",
                   "values": "", "missing": ""}]).to_csv(d / "data_dictionary.csv", index=False, encoding="utf-8-sig")
    manifest = {"format": "std_v3", "version": version, "generated_at": generated, "snapshot": {"id": 1, "frozen_at": generated},
                "options": {"sites": sorted({g[0] for g in groups})}, "ruleset_versions": [RULESET],
                "row_counts": {f"{k}.parquet": len(v) for k, v in tables.items()}}
    (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return d


def _run(tmp_path: Path, *args: str, out: str = "out") -> tuple[int, Path]:
    o = tmp_path / out
    return B.main(["--input", str(tmp_path / "export"), "--out-dir", str(o), *args]), o


def _book(path: Path) -> dict[str, pd.DataFrame]:
    return {k: v.set_index("encounter_id") if "encounter_id" in v.columns else v for k, v in pd.read_excel(path, sheet_name=None, header=1).items()}


def _header(path: Path, sheet: str) -> list:
    return pd.read_excel(path, sheet_name=sheet, header=None, nrows=1).iloc[0].tolist()


def _a1(path: Path) -> pd.DataFrame:
    """分析 sheet：第 1 行标题，可能有一行说明，然后是表头。"""
    raw = pd.read_excel(path, sheet_name="A1_导出与结构检查", header=None)
    h = raw.index[raw[0] == "项"][0]
    return raw.iloc[h + 1:].set_axis(["项", "值"], axis=1)


def test_wide_values_and_new_items(tmp_path):
    make_export(tmp_path / "export")
    code, out = _run(tmp_path)
    assert code == 0
    (xlsx,) = out.glob("CRF宽表_*.xlsx")
    wb = _book(xlsx)
    for s in SHEETS:
        assert len(wb[s]) == 35 and wb[s].index.is_unique, s
    vs = wb["05_生命体征"]
    assert vs.loc["GD:T00000", "VS001_base"] == 38.5               # t0 前 30 小时那条在基线窗外
    assert vs.loc["GD:T00000", "VS001_all_max"] == 39.2            # 越界的 99 不进极值
    assert vs.loc["GD:T00000", "VS001_n"] == 4
    assert vs.loc["GD:T00000", "VS006_win_min_air"] == 95
    assert wb["08_治疗"].loc["GD:T00001", "TRT001_start_h"] == 4
    assert wb["11_分级时间线"].loc["GD:T00000", "severe_first_h"] == 30
    assert wb["11_分级时间线"].loc["GD:T00001", "sev_max"] == "未见中型及以上证据"
    assert wb["12_候选结局"].loc["GD:T00000", "D0_primary"] == "event"
    assert wb["01_就诊与人口学"].loc["GD:T00000", "pop_main"] == "no"       # 58 岁
    assert wb["01_就诊与人口学"].loc["GD:T00001", "pop_main"] == "yes"      # 60 岁
    # 新的数据项、新的列：不改脚本也能带出来，名称取自导出自带的 codes.csv、data_dictionary.csv
    assert wb["14_其他数据项"].loc["GAM:E00003", "NEWX001_value"] == 3.5
    assert any("新数据项示例" in str(h) for h in _header(xlsx, "14_其他数据项"))
    assert wb["01_就诊与人口学"].loc["GD:T00004", "source_kind"] == "示例来源"
    assert any("来源类型（示例）" in str(h) for h in _header(xlsx, "01_就诊与人口学"))
    assert not any(str(c).startswith("LABX:") for c in wb["06_检验"].columns) and wb["06_检验"]["labx_n"].eq(1).all()
    rec = json.loads(next(out.glob("生成记录_*.json")).read_text(encoding="utf-8"))
    assert rec["rows"]["encounters"] == 35 and rec["report_check"] == "通过" and rec["inputs"][0]["version"] == "std_v3_20261101"


def test_options(tmp_path):
    make_export(tmp_path / "export")
    code, out = _run(tmp_path, "--keep-implausible", "--include-unmapped", "--age-main", "65", "--window", "-48", "24", "--sites", "GD")
    assert code == 0
    (xlsx,) = out.glob("CRF宽表_*_GD.xlsx")
    wb = _book(xlsx)
    assert set(wb["01_就诊与人口学"]["site"]) == {"GD"} and len(wb["01_就诊与人口学"]) == 12
    assert wb["05_生命体征"].loc["GD:T00000", "VS001_all_max"] == 99      # 保留越界值
    assert wb["05_生命体征"].loc["GD:T00000", "VS001_base"] == 37.0       # 窗口放宽到 t0 前 48 小时
    assert wb["06_检验"].loc["GD:T00002", "LABX:示例检验项目_base"] == 1.2
    assert wb["01_就诊与人口学"].loc["GD:T00002", "pop_main"] == "no"      # 62 岁，主分析年龄改成 65
    assert any("研究者另定的年龄" in str(h) for h in _header(xlsx, "01_就诊与人口学"))


def test_report_is_aggregate_only(tmp_path):
    make_export(tmp_path / "export")
    code, out = _run(tmp_path)
    text = next(out.glob("分析报告_*.md")).read_text(encoding="utf-8")
    assert "GD:T" not in text and "T00000" not in text and "<10" in text
    assert "## A5 中心间差异（住院）" in text and "NEWX001" in text and "示例检验项目" in text
    d = B.combine(B.find_bundles(tmp_path / "export"))
    B.prepare(d)
    assert B.leak_check(text, d) == []
    assert B.leak_check(text + "\n| x | GD:T00003 |", d) and B.leak_check(text + "\n| x | PT00003 |", d)
    assert B.leak_check(text + "\n| x | 2025-12-03 |", d)
    code, out = _run(tmp_path, "--no-names", out="out_no_names")
    text = next(out.glob("分析报告_*.md")).read_text(encoding="utf-8")
    assert "示例检验项目" not in text and "J11.101" not in text


def test_versions_of_same_cases_each_or_merge_or_latest(tmp_path):
    exp = tmp_path / "export"
    make_export(exp, "std_v3_20261101", "2026-11-01T10:00:00+08:00")
    make_export(exp, "std_v3_20261115", "2026-11-15T10:00:00+08:00", lab_shift=100)   # 同一批病例的新版本
    code, out = _run(tmp_path)                                         # auto：有重叠，各出一份
    assert code == 0 and sorted(p.name for p in out.glob("*.xlsx")) == ["CRF宽表_std_v3_20261101.xlsx", "CRF宽表_std_v3_20261115.xlsx"]
    code, out = _run(tmp_path, "--mode", "latest", out="latest")
    assert [p.name for p in out.glob("*.xlsx")] == ["CRF宽表_std_v3_20261115.xlsx"]
    code, out = _run(tmp_path, "--mode", "merge", out="merge")
    (xlsx,) = out.glob("*.xlsx")
    wb = _book(xlsx)
    assert len(wb["06_检验"]) == 35 and wb["06_检验"].loc["GD:T00002", "LAB006_base"] == 112   # 同一就诊用较新的那份
    a1 = _a1(xlsx)
    assert a1.loc[a1["项"].str.contains("不止一份导出", na=False), "值"].astype(int).iloc[0] == 35


def test_disjoint_exports_merge_automatically(tmp_path):
    exp = tmp_path / "export"
    make_export(exp, "std_v3_gd", groups=(("GD", "inpatient", 12),))
    make_export(exp, "std_v3_gam", "2026-11-02T10:00:00+08:00", groups=(("GAM", "inpatient", 12), ("GAM", "ed", 11)))
    code, out = _run(tmp_path)
    (xlsx,) = out.glob("*.xlsx")
    wb = _book(xlsx)
    assert len(wb["01_就诊与人口学"]) == 35 and set(wb["01_就诊与人口学"]["site"]) == {"GD", "GAM"}


def test_zip_and_folder_counted_once_and_skip_existing(tmp_path, capsys):
    exp = tmp_path / "export"
    d = make_export(exp)
    shutil.make_archive(str(exp / d.name), "zip", root_dir=exp, base_dir=d.name)
    code, out = _run(tmp_path)
    assert code == 0 and len(list(out.glob("*.xlsx"))) == 1
    capsys.readouterr()
    code, out = _run(tmp_path, "--skip-existing")
    assert code == 0 and "跳过" in capsys.readouterr().out


def test_std_v2_shape(tmp_path):
    d = make_export(tmp_path / "export", extra_col=False)
    ev = pd.read_parquet(d / "events.parquet").rename(columns={"event_id": "obs_id"})
    ev.drop(columns=["site", "rule_id", "time_kind", "end", "end_precision", "o2_status", "marks"]).to_parquet(d / "observations.parquet", index=False)
    (d / "events.parquet").unlink()
    enc = pd.read_parquet(d / "encounters.parquet").drop(columns=["site", "icu", "icu_start", "icu_periop", "death_time", "flu_season", "season_index"])
    enc.to_parquet(d / "encounters.parquet", index=False)
    code, out = _run(tmp_path)
    assert code == 0
    (xlsx,) = out.glob("*.xlsx")
    assert len(_book(xlsx)["05_生命体征"]) == 35
    assert _a1(xlsx)["项"].str.contains("缺少的列：events", na=False).any()
