#!/bin/bash

# 部署脚本 deploy.sh
# 功能：杀死旧服务 -> 启动新服务 -> 监测是否启动成功

PORT=8080
TIMEOUT=60    # 超时时间（秒）
INTERVAL=5    # 检查间隔（秒）

git fetch
git reset --hard
git rebase

conda activate openwebui

# 1. 杀死占用 8080 端口的旧进程
echo "正在检查并杀死占用 ${PORT} 端口的旧进程..."
OLD_PID=$(lsof -t -i :${PORT})

if [ -n "$OLD_PID" ]; then
    echo "发现旧进程(PID: $OLD_PID)，正在杀死..."
    kill -9 $OLD_PID
    sleep 2  # 等待旧进程完全退出
    echo "旧进程已终止"
else
    echo "没有发现占用 ${PORT} 端口的旧进程"
fi

cd backend

# 2. 启动新服务
echo "正在启动新服务..."
nohup bash start.sh &> /dev/null &

# 3. 监测端口是否启动成功
echo "服务启动中，正在监测 ${PORT} 端口..."
START_TIME=$(date +%s)
SUCCESS=0

while true; do
    # 检查端口是否被监听
    if lsof -i :${PORT} &> /dev/null; then
        SUCCESS=1
        break
    fi

    # 计算已等待时间
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    # 检查是否超时
    if [ $ELAPSED -ge $TIMEOUT ]; then
        break
    fi

    echo "等待服务启动...（已等待 ${ELAPSED} 秒）"
    sleep $INTERVAL
done

# 4. 输出结果
if [ $SUCCESS -eq 1 ]; then
    echo "✅ 部署成功！${PORT} 端口服务已启动。"
    exit 0
else
    echo "❌ 启动失败：${TIMEOUT} 秒后仍未检测到 ${PORT} 端口服务。"
    exit 1
fi