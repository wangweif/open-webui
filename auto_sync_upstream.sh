#!/bin/bash

# 自动同步上游仓库的脚本
# 此脚本用于自动将原始仓库的更新同步到您的fork仓库
# 可以设置为定时任务自动运行

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="$HOME/sync_upstream.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 打印并记录消息的函数
log_message() {
  local color=$1
  local prefix=$2
  local message=$3
  echo -e "${color}[${prefix}]${NC} $message"
  echo "[$TIMESTAMP] [$prefix] $message" >> $LOG_FILE
}

# 不同级别的日志
info() {
  log_message "$GREEN" "INFO" "$1"
}

warn() {
  log_message "$YELLOW" "WARN" "$1"
}

error() {
  log_message "$RED" "ERROR" "$1"
}

# 切换到项目目录
cd "$(dirname "$0")" || {
  error "无法切换到脚本所在目录"
  exit 1
}

# 指定要同步的上游分支和本地分支
UPSTREAM_BRANCH=${1:-"main"}  # 默认为main分支
LOCAL_BRANCH=${2:-"main"}     # 默认为main分支

info "开始自动同步 - 上游分支: $UPSTREAM_BRANCH, 本地分支: $LOCAL_BRANCH"

# 检查是否已经添加了upstream
if ! git remote | grep -q "upstream"; then
  info "添加上游仓库 (upstream): https://github.com/open-webui/open-webui.git"
  git remote add upstream https://github.com/open-webui/open-webui.git
else
  info "上游仓库已存在，检查URL是否正确..."
  UPSTREAM_URL=$(git remote get-url upstream)
  if [ "$UPSTREAM_URL" != "https://github.com/open-webui/open-webui.git" ]; then
    warn "上游仓库URL不正确，正在更新..."
    git remote set-url upstream https://github.com/open-webui/open-webui.git
  fi
fi

# 保存当前未提交的修改
if [ -n "$(git status --porcelain)" ]; then
  warn "检测到未提交的修改，正在保存..."
  git stash save "Auto-stash before sync with upstream at $TIMESTAMP"
  STASHED=true
else
  STASHED=false
fi

# 记住当前分支
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
info "当前分支: $CURRENT_BRANCH"

# 拉取上游仓库的最新代码
info "正在拉取上游仓库的最新代码..."
if ! git fetch upstream; then
  error "拉取上游仓库失败，请检查网络连接或仓库URL"
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ]; then
    git stash pop
  fi
  exit 1
fi

# 检查上游分支是否存在
if ! git branch -r | grep -q "upstream/$UPSTREAM_BRANCH"; then
  error "上游分支 '$UPSTREAM_BRANCH' 不存在"
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ]; then
    git stash pop
  fi
  exit 1
fi

# 切换到要同步的本地分支
if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
  info "切换到 '$LOCAL_BRANCH' 分支..."
  
  # 检查本地分支是否存在
  if ! git branch | grep -q "$LOCAL_BRANCH"; then
    info "本地分支 '$LOCAL_BRANCH' 不存在，正在创建..."
    if ! git checkout -b "$LOCAL_BRANCH" "upstream/$UPSTREAM_BRANCH"; then
      error "创建本地分支失败"
      # 如果之前有stash，恢复
      if [ "$STASHED" = true ]; then
        git stash pop
      fi
      exit 1
    fi
  else
    # 切换到指定的本地分支
    if ! git checkout "$LOCAL_BRANCH"; then
      error "切换到本地分支失败"
      # 如果之前有stash，恢复
      if [ "$STASHED" = true ]; then
        git stash pop
      fi
      exit 1
    fi
  fi
fi

# 尝试合并上游分支
info "正在将上游 '$UPSTREAM_BRANCH' 分支合并到本地 '$LOCAL_BRANCH' 分支..."
if ! git merge "upstream/$UPSTREAM_BRANCH" -m "Merge upstream $UPSTREAM_BRANCH into $LOCAL_BRANCH"; then
  error "合并发生冲突，请手动解决"
  # 在日志中记录冲突的文件
  git diff --name-only --diff-filter=U >> $LOG_FILE
  
  # 中止合并
  git merge --abort
  
  # 切换回原来的分支
  if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
  fi
  
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ]; then
    git stash pop
  fi
  
  exit 1
fi

# 推送到远程仓库
info "正在推送到远程仓库..."
if ! git push origin "$LOCAL_BRANCH"; then
  error "推送到远程仓库失败"
  
  # 切换回原来的分支
  if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
    git checkout "$CURRENT_BRANCH"
  fi
  
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ]; then
    git stash pop
  fi
  
  exit 1
fi

# 切换回原来的分支
if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
  info "切换回原来的 '$CURRENT_BRANCH' 分支..."
  git checkout "$CURRENT_BRANCH"
fi

# 如果之前有stash，恢复
if [ "$STASHED" = true ]; then
  info "正在恢复您的未提交修改..."
  git stash pop
fi

info "同步完成!" 