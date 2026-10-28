"""核对脚本共用：把研究者给的路径（文件夹、压缩包，或几个这样的路径）整理成 flucase 成套读取器要的 [(文件, 显示名)]。

压缩包用 flucase 自己的解包（`flucase.repo.archive`：防路径穿越，`__MACOSX`、`~$*`、以点开头的文件跳过，和导入页一致），
解到压缩包旁边的临时文件夹（真实数据不离开 BaseModel 的 data/），用完删掉。文件夹里的压缩包也解开。
"""
from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def bundle_files(paths: list[Path], exts: tuple[str, ...] = (".xlsx", ".xlsm")):
    from flucase.repo.archive import JUNK, expand, is_archive
    tmp: list[Path] = []
    out: list[tuple[Path, str]] = []

    def unpack(arc: Path, prefix: str) -> None:
        d = Path(tempfile.mkdtemp(prefix="_核对解包_", dir=arc.parent))
        tmp.append(d)
        for rel, p in expand(arc, d / "x"):
            if p.suffix.lower() in exts:
                out.append((p, f"{prefix}{arc.name}/{rel}"))

    missing = [str(p) for p in paths if not Path(p).exists()]
    if missing:
        raise SystemExit("✗ 这些路径不存在（检查拼写；路径里有空格要加引号）：\n  " + "\n  ".join(missing))
    try:
        for root in paths:
            root = Path(root)
            if root.is_file():
                if is_archive(root.name):
                    unpack(root, "")
                elif root.suffix.lower() in exts:
                    out.append((root, root.name))
                continue
            for p in sorted(root.rglob("*")):
                rel = p.relative_to(root).as_posix()
                if not p.is_file() or JUNK.search(rel):
                    continue
                if is_archive(p.name):
                    unpack(p, f"{root.name}/")
                elif p.suffix.lower() in exts:
                    out.append((p, f"{root.name}/{rel}"))
        yield out
    finally:
        for d in tmp:
            shutil.rmtree(d, ignore_errors=True)
