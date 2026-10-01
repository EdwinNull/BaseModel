#!/bin/bash
# 使用 SCP 上传模型权重到服务器（备用方案）
# 使用前请修改以下配置

# ====== 配置区域 ======
SERVER_USER="your_username"           # 服务器用户名
SERVER_HOST="your_server_ip"          # 服务器地址
SERVER_PATH="/path/to/models"         # 服务器目标路径
# ====================

LOCAL_MODELS_DIR="./models"

echo "========================================"
echo "准备上传模型到服务器 (SCP 方式)"
echo "========================================"
echo "本地路径: $LOCAL_MODELS_DIR"
echo "服务器: $SERVER_USER@$SERVER_HOST"
echo "目标路径: $SERVER_PATH"
echo ""

# 检查本地模型是否存在
if [ ! -d "$LOCAL_MODELS_DIR/MOMENT-1-large" ]; then
    echo "❌ 错误: MOMENT 模型不存在"
    exit 1
fi

if [ ! -d "$LOCAL_MODELS_DIR/chronos-t5-large" ]; then
    echo "❌ 错误: Chronos 模型不存在"
    exit 1
fi

echo "✓ 本地模型检查通过"
echo ""

# 使用 scp 上传
echo "[1/2] 上传 MOMENT 模型..."
scp -r "$LOCAL_MODELS_DIR/MOMENT-1-large" \
    "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"

if [ $? -eq 0 ]; then
    echo "✓ MOMENT 模型上传成功"
else
    echo "❌ MOMENT 模型上传失败"
    exit 1
fi

echo ""
echo "[2/2] 上传 Chronos 模型..."
scp -r "$LOCAL_MODELS_DIR/chronos-t5-large" \
    "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"

if [ $? -eq 0 ]; then
    echo "✓ Chronos 模型上传成功"
else
    echo "❌ Chronos 模型上传失败"
    exit 1
fi

echo ""
echo "========================================"
echo "✓ 所有模型上传完成！"
echo "========================================"
