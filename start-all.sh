#!/bin/bash
# 缠论分析平台 - 前后端一键启动
# 用法: bash /data/chanlun/start-all.sh

# 启动后端
bash /data/chanlun/backend/start.sh &
BACKEND_PID=$!

# 启动前端
cd /data/chanlun/frontend
pnpm dev &
FRONTEND_PID=$!

echo "后端 PID: $BACKEND_PID (http://localhost:8503)"
echo "前端 PID: $FRONTEND_PID (http://localhost:8501)"
echo ""
echo "按 Ctrl+C 停止所有服务"
wait
