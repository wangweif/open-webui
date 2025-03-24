#!/bin/bash

# 禁用OpenAI API
export HF_HUB_OFFLINE=1
export ENABLE_OPENAI_API=false
# 设置日志级别为debug
export OPEN_WEBUI_LOG_LEVEL=debug
# 设置服务监听地址和端口
export OPEN_WEBUI_LISTEN=0.0.0.0:8080
# 设置请求超时时间为600秒
export OPEN_WEBUI_TIMEOUT=600
# 设置线程数为8
export OPEN_WEBUI_THREADS=8
PORT="${PORT:-8080}"
uvicorn open_webui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload