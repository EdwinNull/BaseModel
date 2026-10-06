"""下载综合实验规划（20261004）§3.2 所需的模型权重到本机 models/，供之后上传到服务器。

为什么在本机下载：服务器访问 Hugging Face 时会被重定向到 xet 存储，连接超时；
本机经 hf-mirror.com 镜像可以正常下载。

用法（在仓库根目录运行）：
    python scripts/download_models_v2.py            # 下载默认的 TSFM 清单
    python scripts/download_models_v2.py --group llm  # 只下载 LLM（体积大，放在后面）

每个仓库下载完成后：
1. 通过镜像 API 取每个大文件（LFS）的官方 sha256；
2. 在本地重新计算 sha256 并比对；
3. 把结果写入 models/<目录>/SHA256SUMS.txt，上传到服务器后可以用 `sha256sum -c` 再核对一次。
"""
import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

# 必须在导入 huggingface_hub 之前设置镜像地址
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")      # 不走 xet 协议，避免镜像侧重定向失败

from huggingface_hub import HfApi, snapshot_download  # noqa: E402

# (仓库名, 本地目录名, 分组)。分组 tsfm 先下载，llm 体积大放在后面。
MODELS = [
    ("amazon/chronos-t5-small", "chronos-t5-small", "tsfm"),
    ("amazon/chronos-t5-base", "chronos-t5-base", "tsfm"),
    ("amazon/chronos-bolt-small", "chronos-bolt-small", "tsfm"),
    ("amazon/chronos-bolt-base", "chronos-bolt-base", "tsfm"),
    ("amazon/chronos-2", "chronos-2", "tsfm"),
    ("google/timesfm-2.5-200m-pytorch", "timesfm-2.5-200m-pytorch", "tsfm"),
    ("google/timesfm-3.0-pytorch", "timesfm-3.0-pytorch", "tsfm"),
    ("Salesforce/moirai-moe-1.0-R-small", "moirai-moe-1.0-R-small", "tsfm"),
    ("Salesforce/moirai-2.0-R-small", "moirai-2.0-R-small", "tsfm"),
    ("NX-AI/TiRex", "TiRex", "tsfm"),
    ("Datadog/Toto-2.0-22m", "Toto-2.0-22m", "tsfm"),
    ("Datadog/Toto-2.0-313m", "Toto-2.0-313m", "tsfm"),
    ("time-series-foundation-models/Lag-Llama", "Lag-Llama", "tsfm"),
    ("paris-noah/Mantis-8M", "Mantis-8M", "tsfm"),
    ("Prior-Labs/TabPFN-v2-reg", "TabPFN-v2-reg", "tsfm"),
    ("Qwen/Qwen3-1.7B", "Qwen3-1.7B", "llm"),
    ("Qwen/Qwen3-4B", "Qwen3-4B", "llm"),
]

# 同一权重常有多种格式，只保留 safetensors / ckpt 与配置文件，跳过重复的 .bin、ONNX 等
IGNORE = ["*.onnx", "*.h5", "*.msgpack", "*.tflite", "*.ot", "onnx/*", "*.gguf"]


def sha256_of(path: Path) -> str:
    """分块计算文件的 sha256，避免一次把大文件读进内存。"""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download_one(api: HfApi, repo: str, local: Path) -> str:
    """下载一个仓库并核对 LFS 文件的 sha256；返回一行状态说明。"""
    t0 = time.time()
    snapshot_download(repo_id=repo, local_dir=local, ignore_patterns=IGNORE, max_workers=4)
    # 官方 sha256：只有 LFS 管理的大文件才有；小文件（json 等）只记录本地值
    info = api.model_info(repo, files_metadata=True)
    official = {s.rfilename: s.lfs.sha256 for s in info.siblings if getattr(s, "lfs", None)}
    lines, bad = [], []
    for f in sorted(p for p in local.rglob("*") if p.is_file() and ".cache" not in p.parts):
        rel = f.relative_to(local).as_posix()
        if rel == "SHA256SUMS.txt":
            continue
        digest = sha256_of(f)
        lines.append(f"{digest}  {rel}")
        if rel in official and official[rel] != digest:
            bad.append(rel)
    (local / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    size_mb = sum(f.stat().st_size for f in local.rglob("*") if f.is_file()) / 1e6
    status = "sha256 不一致: " + ", ".join(bad) if bad else f"{len(official)} 个 LFS 文件 sha256 一致"
    return f"{repo}: {size_mb:.0f} MB, {time.time() - t0:.0f} s, {status}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="tsfm", choices=["tsfm", "llm", "all"])
    args = ap.parse_args()
    api = HfApi()
    root = Path("models")
    root.mkdir(exist_ok=True)
    for repo, name, group in MODELS:
        if args.group != "all" and group != args.group:
            continue
        try:
            print(download_one(api, repo, root / name), flush=True)
        except Exception as e:  # 单个仓库失败（如需要登录同意许可）不影响其他仓库
            print(f"{repo}: 失败 {type(e).__name__}: {str(e)[:200]}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
