# 脚本

生成 PPT、绘制图表、裁取论文图及共用绘图样式的 Python 脚本。

| 子目录或文件 | 内容 |
|---|---|
| [build_data_alignment_presentation.py](build_data_alignment_presentation.py) |  |
| [build_figures_20261107.py](build_figures_20261107.py) |  |
| [build_hospital_optimized.py](build_hospital_optimized.py) |  |
| [build_progress_reading_report_20261026.py](build_progress_reading_report_20261026.py) |  |
| [build_progress_reading_report_20261026_v2.py](build_progress_reading_report_20261026_v2.py) |  |
| [build_weekly_summary_20261023.py](build_weekly_summary_20261023.py) |  |
| [build_weekly_summary_20261107.py](build_weekly_summary_20261107.py) |  |
| [build_weekly_summary_20261107_v2.py](build_weekly_summary_20261107_v2.py) |  |
| [extract_paper_figures_20261026.py](extract_paper_figures_20261026.py) |  |
| [journal_style.py](journal_style.py) |  |

在仓库根目录运行，例如：

```bash
python PPT/脚本/build_data_alignment_presentation.py
python PPT/脚本/build_figures_20261107.py
python PPT/脚本/build_weekly_summary_20261107_v2.py
```

脚本按自身位置定位模板和素材，成品写入对应的成品子目录。历史 v1 `build_progress_reading_report_20261026.py` 的输出路径指向周报与进展目录；该 v1 成品在本次整理开始前已不在工作区。
