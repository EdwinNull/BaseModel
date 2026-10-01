"""
下载 MOMENT 和 Chronos 模型权重到本地
"""
import os
from pathlib import Path
from huggingface_hub import snapshot_download

# 创建模型存储目录
models_dir = Path("./models")
models_dir.mkdir(exist_ok=True)

print("=" * 60)
print("开始下载模型权重...")
print("=" * 60)

# 下载 MOMENT 模型
print("\n[1/2] 下载 MOMENT 模型...")
print("-" * 60)
try:
    moment_path = snapshot_download(
        repo_id="AutonLab/MOMENT-1-large",
        local_dir=models_dir / "MOMENT-1-large",
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print(f"✓ MOMENT 模型下载完成: {moment_path}")
except Exception as e:
    print(f"✗ MOMENT 模型下载失败: {e}")

# 下载 Chronos 模型
print("\n[2/2] 下载 Chronos 模型...")
print("-" * 60)
try:
    chronos_path = snapshot_download(
        repo_id="amazon/chronos-t5-large",
        local_dir=models_dir / "chronos-t5-large",
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print(f"✓ Chronos 模型下载完成: {chronos_path}")
except Exception as e:
    print(f"✗ Chronos 模型下载失败: {e}")

print("\n" + "=" * 60)
print("下载完成！")
print("=" * 60)
print(f"\n模型存储位置: {models_dir.absolute()}")
print(f"MOMENT: {(models_dir / 'MOMENT-1-large').absolute()}")
print(f"Chronos: {(models_dir / 'chronos-t5-large').absolute()}")
