"""
下载模型权重到本地 models/，下完按 Hugging Face 给的 sha256 逐个核对（服务器连不上 HuggingFace 的 xet 存储，权重在本机中转）。

    python scripts/download_models.py                               # 默认：MOMENT-1-large、chronos-t5-large（原来的两份）
    python scripts/download_models.py OpenJev-Flash-9B Qwen3.5-9B   # J 线（plans/零样本决策读出J线_参照MedJev_实验计划_20261029.md §2、J0）

核对结果写到 models/<名字>/SHA256SUMS.local（上传后在服务器上用它再核对一次，见 scripts/upload_models.sh）。
"""
import hashlib
import sys
import time
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

MODELS = {
    "MOMENT-1-large": "AutonLab/MOMENT-1-large",
    "chronos-t5-large": "amazon/chronos-t5-large",
    "OpenJev-Flash-9B": "openjev/OpenJev-Flash-9B",        # 权重 CC BY-NC 4.0（研究者 10-29 确认可用，Q14）
    "Qwen3.5-9B": "Qwen/Qwen3.5-9B",                        # Apache 2.0；J 线的基座对照
}
DEFAULT = ["MOMENT-1-large", "chronos-t5-large"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def fetch(name: str, models_dir: Path) -> bool:
    repo = MODELS[name]
    dest = models_dir / name
    print(f"\n== {name}（{repo}）→ {dest}", flush=True)
    for k in range(5):                     # 下完移动文件时偶尔被别的程序占着（如 Syncthing 在扫 models/）：等一会儿接着下
        try:
            snapshot_download(repo_id=repo, local_dir=dest)
            break
        except OSError as e:
            if k == 4:
                raise
            print(f"  第 {k + 1} 次没下完（{type(e).__name__}），30 秒后接着下", flush=True)
            time.sleep(30)
    info = HfApi().model_info(repo, files_metadata=True)
    bad, lines = [], []
    for s in info.siblings:
        p = dest / s.rfilename
        if not p.is_file():
            bad.append(f"缺 {s.rfilename}")
            continue
        got = sha256(p)
        lines.append((s.rfilename, got))
        want = s.lfs.sha256 if s.lfs else None
        if want and got != want:
            bad.append(f"sha256 不对：{s.rfilename}")
    (dest / "SHA256SUMS.local").write_text("".join(f"{h}  {f}\n" for f, h in sorted(lines)), encoding="utf-8", newline="\n")
    size = sum(p.stat().st_size for p in dest.rglob("*") if p.is_file()) / 1e9
    print(f"{'✗' if bad else '✓'} {name}：{len(info.siblings)} 个文件，{size:.1f} GB"
          + ("；" + "；".join(bad) if bad else "，大文件 sha256 与 Hugging Face 一致"), flush=True)
    return not bad


def main(argv: list[str]) -> int:
    names = argv or DEFAULT
    unknown = [n for n in names if n not in MODELS]
    if unknown:
        print(f"不认识：{'、'.join(unknown)}；可选：{'、'.join(MODELS)}")
        return 2
    models_dir = Path("./models")
    models_dir.mkdir(exist_ok=True)
    ok = [fetch(n, models_dir) for n in names]
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
