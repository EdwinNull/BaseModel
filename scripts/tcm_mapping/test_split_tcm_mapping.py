"""split_tcm_mapping.py 的测试（虚构写法与次数）。运行：python -m pytest scripts/tcm_mapping -q -p no:cacheprovider"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from split_tcm_mapping import atoms, split  # noqa: E402


def test_atoms_dedupe_and_order():
    assert atoms("甲证¤甲证¤乙证") == ["甲证", "乙证"]
    assert atoms(" 甲证 ") == ["甲证"]


def test_split_status():
    rows = [
        ("甲证", "否", 10, 1, None),                 # 单写没填，重复写法填了 → 已填
        ("甲证¤甲证", "否", 3, 0, "热毒袭肺"),
        ("乙证", "否", 5, 0, "毒热壅盛"),            # 两种纯写法填得不一样 → 冲突
        ("乙证¤乙证", "否", 1, 0, "热毒袭肺"),
        ("丙证¤丁证", "否", 2, 2, "风热犯卫"),       # 只在多证候写法里填过
        ("戊证", "否", 0, 4, None),                  # 待补
    ]
    single, multi = split(rows)
    by = {r["证候"]: r for r in single}
    assert by["甲证"]["状态"] == "已填" and by["甲证"]["对应证型"] == "热毒袭肺" and by["甲证"]["GD 就诊"] == 13
    assert by["乙证"]["状态"] == "冲突" and by["乙证"]["对应证型"] == "毒热壅盛 / 热毒袭肺"
    assert by["丙证"]["状态"] == by["丁证"]["状态"] == "只在多证候写法里填过"
    assert by["戊证"]["状态"] == "待补"
    assert [m["写法"] for m in multi] == ["丙证¤丁证"]
    assert single[-1]["状态"] == "已填"                # 待处理的排在前面
