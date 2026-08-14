#!/bin/bash
# Open WebUI 内网离线一键部署脚本（服务器上 root 执行: bash deploy.sh）
set -e
cd "$(dirname "$0")"

echo "=== [1/4] 导入离线镜像 ==="
docker load -i open-webui-offline-nkxz.tar.gz

echo "=== [2/4] 创建数据目录 /root/data/open-webui ==="
mkdir -p /root/data/open-webui

echo "=== [3/4] 启动容器 ==="
docker compose -f docker-compose.offline.yaml up -d

echo "=== [4/4] 部署完成 ==="
docker ps | grep open-webui && echo "" && echo "验证: curl http://127.0.0.1:3000/health 应返回 {\"status\":true}"
echo "浏览器访问: http://服务器IP:3000"
