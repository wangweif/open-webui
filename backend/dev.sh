#!/bin/bash

export OLLAMA_API_BASE_URL=http://192.168.8.250:11434/api

PORT="${PORT:-8080}"
uvicorn open_webui.main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload