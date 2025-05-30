#!/bin/bash

# 部署脚本 deploy.sh
# 功能：杀死旧服务 -> 启动新服务 -> 监测是否启动成功

PORT=8080
TIMEOUT=180    # 超时时间（秒）
INTERVAL=5    # 检查间隔（秒）

# 0. 更新代码（根据你的需求可选）
git fetch
git reset --hard
git rebase

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

# 2. 进入 backend 目录
echo "进入 backend 目录..."
cd backend || { echo "无法进入 backend 目录"; exit 1; }
echo "当前工作目录: $(pwd)"
ls -l  # 调试用，显示目录内容

# 3. 启动新服务（确保在 backend 目录下运行）
echo "正在启动新服务..."
nohup bash start.sh > logs/backend.log 2>&1 &

# 4. 监测端口是否启动成功
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

# 5. 输出结果
if [ $SUCCESS -eq 1 ]; then
    echo "✅ 部署成功！${PORT} 端口服务已启动。"
    # 实时打印最新日志（可选）
    echo "=== 最新日志 ==="
    tail -n 20 logs/backend.log
    exit 0
else
    echo "❌ 启动失败：${TIMEOUT} 秒后仍未检测到 ${PORT} 端口服务。"
    echo "=== 错误日志 ==="
    tail -n 20 logs/backend.log
    exit 1
fi