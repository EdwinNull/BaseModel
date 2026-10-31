#!/bin/bash
# 上传模型权重到服务器，传完在服务器上按 SHA256SUMS.local 核对（scripts/download_models.py 下载时写的）。
#   bash scripts/upload_models.sh                               # 默认：MOMENT-1-large、chronos-t5-large → W/（原来的位置）
#   bash scripts/upload_models.sh OpenJev-Flash-9B Qwen3.5-9B   # J 线 → W/models/（plans/零样本决策读出J线_参照MedJev_实验计划_20261029.md J0）
# 本机有 rsync 就用 rsync（能断点续传），没有就用 scp。

# ====== 配置区域 ======
SERVER_USER="ud202482579"             # 服务器用户名
SERVER_HOST="202.114.0.141"           # 服务器地址
SERVER_PATH="/home/ud202482579/wangyiming"  # 服务器工作区 W
# ====================

LOCAL_MODELS_DIR="./models"
if [ $# -eq 0 ]; then
    NAMES=(MOMENT-1-large chronos-t5-large); DEST="$SERVER_PATH"
else
    NAMES=("$@"); DEST="$SERVER_PATH/models"
fi
REMOTE="$SERVER_USER@$SERVER_HOST"

for n in "${NAMES[@]}"; do
    if [ ! -d "$LOCAL_MODELS_DIR/$n" ]; then
        echo "❌ 本机没有 $LOCAL_MODELS_DIR/$n（先跑 python scripts/download_models.py $n）"
        exit 1
    fi
done
ssh "$REMOTE" "mkdir -p '$DEST'" || exit 1

for n in "${NAMES[@]}"; do
    echo "== 上传 $n → $DEST/$n"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --partial --exclude .huggingface "$LOCAL_MODELS_DIR/$n/" "$REMOTE:$DEST/$n/" || { echo "❌ $n 上传失败"; exit 1; }
    else
        ssh "$REMOTE" "mkdir -p '$DEST/$n'" || exit 1
        (cd "$LOCAL_MODELS_DIR/$n" && find . -type f -not -path './.huggingface/*' -printf '%P\n') | while read -r f; do
            ssh -n "$REMOTE" "mkdir -p \"\$(dirname '$DEST/$n/$f')\"" && scp -q "$LOCAL_MODELS_DIR/$n/$f" "$REMOTE:$DEST/$n/$f" || { echo "❌ $f 上传失败"; exit 1; }
        done || exit 1
    fi
    if [ -f "$LOCAL_MODELS_DIR/$n/SHA256SUMS.local" ]; then
        ssh "$REMOTE" "cd '$DEST/$n' && sha256sum -c --quiet SHA256SUMS.local" && echo "✓ $n 服务器上 sha256 核对通过" || { echo "❌ $n 服务器上 sha256 对不上"; exit 1; }
    else
        echo "✓ $n 已上传（没有 SHA256SUMS.local，未核对）"
    fi
done
echo "✓ 全部上传完成"
