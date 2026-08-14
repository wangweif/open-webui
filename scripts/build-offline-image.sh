#!/usr/bin/env bash
# build-offline-image.sh
# 在【有网机器】上构建并导出 Open WebUI 离线镜像（Dockerfile 会把 npm/pip/模型全部打进镜像，内网运行无需联网）
# 用法:
#   TARGET_PLATFORM=linux/amd64 ./scripts/build-offline-image.sh   # 内网服务器是 x86_64(默认)
#   TARGET_PLATFORM=linux/arm64 ./scripts/build-offline-image.sh  # 内网服务器是 ARM(鲲鹏/飞腾等)
set -euo pipefail

TARGET_PLATFORM="${TARGET_PLATFORM:-linux/amd64}"
IMAGE_NAME="${IMAGE_NAME:-open-webui:offline}"
OUTPUT_FILE="${OUTPUT_FILE:-open-webui-offline.tar.gz}"
# false=不下载 embedding/whisper 模型(仅聊天用, 镜像更小构建更快)
# true =下载并烘焙进镜像(需要 RAG 文档检索/语音转写时用)
DOWNLOAD_MODELS="${DOWNLOAD_MODELS:-false}"

cd "$(dirname "$0")/.."

echo ">>> [1/3] 构建镜像  platform=$TARGET_PLATFORM  image=$IMAGE_NAME"
echo "    注意: 构建需联网下载 npm 依赖 / torch / 模型, 耗时约 15~60 分钟"
docker build --platform "$TARGET_PLATFORM" \
  --build-arg USE_OLLAMA=false \
  --build-arg DOWNLOAD_MODELS="$DOWNLOAD_MODELS" \
  -t "$IMAGE_NAME" .

echo ">>> [2/3] 导出并压缩镜像 -> $OUTPUT_FILE"
docker save "$IMAGE_NAME" | gzip > "$OUTPUT_FILE"

echo ">>> [3/3] 完成!"
ls -lh "$OUTPUT_FILE"
echo ">>> 下一步: 把 $OUTPUT_FILE 拷贝到内网服务器, 然后执行:"
echo "    docker load -i $OUTPUT_FILE"
echo "    docker compose -f docker-compose.offline.yaml up -d"
