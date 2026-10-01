"""
Python 版本上传脚本 - 支持多种方式上传模型到服务器
"""
import os
import subprocess
from pathlib import Path

# ====== 配置区域 ======
SERVER_CONFIG = {
    "user": "your_username",          # 服务器用户名
    "host": "your_server_ip",         # 服务器地址
    "path": "/path/to/models",        # 服务器目标路径
    "method": "rsync"                 # 上传方式: rsync 或 scp
}
# ====================

LOCAL_MODELS_DIR = Path("./models")
MODELS = ["MOMENT-1-large", "chronos-t5-large"]

def check_local_models():
    """检查本地模型是否存在"""
    print("检查本地模型...")
    for model in MODELS:
        model_path = LOCAL_MODELS_DIR / model
        if not model_path.exists():
            print(f"❌ 错误: {model} 不存在于 {model_path}")
            return False
        print(f"✓ 找到 {model}")
    return True

def upload_with_rsync(local_path, remote_path):
    """使用 rsync 上传（推荐，支持断点续传）"""
    cmd = [
        "rsync", "-avz", "--progress",
        str(local_path) + "/",
        f"{SERVER_CONFIG['user']}@{SERVER_CONFIG['host']}:{remote_path}/"
    ]
    return subprocess.run(cmd)

def upload_with_scp(local_path, remote_path):
    """使用 scp 上传"""
    cmd = [
        "scp", "-r",
        str(local_path),
        f"{SERVER_CONFIG['user']}@{SERVER_CONFIG['host']}:{SERVER_CONFIG['path']}/"
    ]
    return subprocess.run(cmd)

def main():
    print("=" * 60)
    print("准备上传模型到服务器")
    print("=" * 60)
    print(f"本地路径: {LOCAL_MODELS_DIR.absolute()}")
    print(f"服务器: {SERVER_CONFIG['user']}@{SERVER_CONFIG['host']}")
    print(f"目标路径: {SERVER_CONFIG['path']}")
    print(f"上传方式: {SERVER_CONFIG['method']}")
    print()

    # 检查本地模型
    if not check_local_models():
        return

    print()
    print("=" * 60)
    print("开始上传...")
    print("=" * 60)

    # 选择上传方法
    upload_func = upload_with_rsync if SERVER_CONFIG['method'] == 'rsync' else upload_with_scp

    # 上传每个模型
    for i, model in enumerate(MODELS, 1):
        print(f"\n[{i}/{len(MODELS)}] 上传 {model}...")
        print("-" * 60)

        local_path = LOCAL_MODELS_DIR / model
        remote_path = f"{SERVER_CONFIG['path']}/{model}"

        result = upload_func(local_path, remote_path)

        if result.returncode == 0:
            print(f"✓ {model} 上传成功")
        else:
            print(f"❌ {model} 上传失败")
            return

    print()
    print("=" * 60)
    print("✓ 所有模型上传完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
