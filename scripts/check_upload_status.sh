#!/bin/bash
# 检查服务器上的模型上传状态

SERVER_USER="ud202482579"
SERVER_HOST="202.114.0.141"
SERVER_PATH="/home/ud202482579/wangyiming"

echo "========================================"
echo "检查服务器上的模型状态"
echo "========================================"
echo ""

echo "服务器: $SERVER_USER@$SERVER_HOST"
echo "路径: $SERVER_PATH"
echo ""

echo "检查目录结构..."
ssh $SERVER_USER@$SERVER_HOST "ls -lh $SERVER_PATH/"
echo ""

echo "检查 MOMENT 模型..."
ssh $SERVER_USER@$SERVER_HOST "du -sh $SERVER_PATH/MOMENT-1-large 2>/dev/null || echo '未找到或上传中'"
echo ""

echo "检查 Chronos 模型..."
ssh $SERVER_USER@$SERVER_HOST "du -sh $SERVER_PATH/chronos-t5-large 2>/dev/null || echo '未找到或上传中'"
echo ""

echo "========================================"
