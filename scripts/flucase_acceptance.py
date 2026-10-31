#!/usr/bin/env python3
"""在 BaseModel 根目录跑 flucase 的 std_v3 导出验收与比对（只出聚合量的质量成绩单，可以交回）。

`python -m flucase.export.acceptance` 在 BaseModel 根目录会被同名的 `flucase/` 仓库目录挡住（Python 先把当前目录里的 flucase/
当成包，报 cannot import name '__version__'）；按路径运行这个脚本就不会。用法与参数同 flucase.export.acceptance：

  flucase/backend/.venv/Scripts/python.exe scripts/flucase_acceptance.py data/export/<新>.zip --against data/export/<旧>.zip
"""
import sys

from flucase.export.acceptance import main

if __name__ == "__main__":
    sys.exit(main())
