#!/bin/bash
# 缠论分析平台 - 后端启动脚本

# 检测 MySQL 是否运行
if ! mysql -S /tmp/mysql.sock -u root -p'Chanlun2026!' -e "SELECT 1" > /dev/null 2>&1; then
    echo "[MySQL] 未运行，正在启动..."
    mkdir -p /run/mysql /var/log/mysql
    chown -R mysql:mysql /run/mysql /var/log/mysql /data/mysql
    nohup /usr/sbin/mysqld --defaults-file=/data/mysql/chanlun.cnf --user=mysql > /tmp/mysqld.log 2>&1 &
    sleep 5
    echo "[MySQL] 启动完成"
else
    echo "[MySQL] 已运行"
fi

cd /root/.openclaw/workspace/projects/chanlun/backend

# 安装依赖（如缺失）
pip install -r requirements.txt -q

# 启动 FastAPI
echo "[Backend] 启动中 (http://0.0.0.0:8503)..."
uvicorn app.main:app --host 0.0.0.0 --port 8503 --reload
