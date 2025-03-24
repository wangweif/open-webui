#!/bin/bash

# 同步上游仓库的脚本
# 此脚本用于将原始仓库的更新同步到您的fork仓库

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的消息函数
print_message() {
  echo -e "${GREEN}[同步脚本]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
  echo -e "${RED}[错误]${NC} $1"
}

# 检查是否已经添加了upstream
if ! git remote | grep -q "upstream"; then
  print_message "添加上游仓库 (upstream): https://github.com/open-webui/open-webui.git"
  git remote add upstream https://github.com/open-webui/open-webui.git
else
  print_message "上游仓库已存在，检查URL是否正确..."
  UPSTREAM_URL=$(git remote get-url upstream)
  if [ "$UPSTREAM_URL" != "https://github.com/open-webui/open-webui.git" ]; then
    print_warning "上游仓库URL不正确，正在更新..."
    git remote set-url upstream https://github.com/open-webui/open-webui.git
  fi
fi

# 获取当前分支
CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
print_message "当前分支: $CURRENT_BRANCH"

# 保存当前未提交的修改
if [ -n "$(git status --porcelain)" ]; then
  print_warning "检测到未提交的修改，正在保存..."
  git stash save "Auto-stash before sync with upstream"
  STASHED=true
else
  STASHED=false
fi

# 拉取上游仓库的最新代码
print_message "正在拉取上游仓库的最新代码..."
if ! git fetch upstream; then
  print_error "拉取上游仓库失败，请检查网络连接或仓库URL"
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ]; then
    git stash pop
  fi
  exit 1
fi

# 查看上游分支列表
print_message "上游仓库的分支列表:"
git branch -r | grep upstream

# 询问用户要同步哪个分支
read -p "请输入要同步的上游分支名称 (默认: main): " UPSTREAM_BRANCH
UPSTREAM_BRANCH=${UPSTREAM_BRANCH:-main}

# 检查上游分支是否存在
if ! git branch -r | grep -q "upstream/$UPSTREAM_BRANCH"; then
  print_error "上游分支 '$UPSTREAM_BRANCH' 不存在"
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ]; then
    git stash pop
  fi
  exit 1
fi

# 确认是否要同步到当前分支
read -p "是否要将上游的 '$UPSTREAM_BRANCH' 分支同步到当前的 '$CURRENT_BRANCH' 分支? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  # 询问用户要同步到哪个本地分支
  read -p "请输入要同步到的本地分支名称: " LOCAL_BRANCH
  
  # 如果本地分支不存在，创建它
  if ! git branch | grep -q "$LOCAL_BRANCH"; then
    print_message "本地分支 '$LOCAL_BRANCH' 不存在，正在创建..."
    git checkout -b $LOCAL_BRANCH
  else
    # 切换到指定的本地分支
    git checkout $LOCAL_BRANCH
  fi
else
  LOCAL_BRANCH=$CURRENT_BRANCH
fi

# 尝试合并上游分支
print_message "正在将上游 '$UPSTREAM_BRANCH' 分支合并到本地 '$LOCAL_BRANCH' 分支..."
if ! git merge upstream/$UPSTREAM_BRANCH; then
  print_error "合并冲突，请手动解决冲突后提交"
  echo "解决冲突后，使用以下命令完成合并:"
  echo "  git add ."
  echo "  git commit -m 'Resolved merge conflicts with upstream'"
  echo "  git push origin $LOCAL_BRANCH"
  
  # 如果之前有stash，恢复
  if [ "$STASHED" = true ] && [ "$LOCAL_BRANCH" = "$CURRENT_BRANCH" ]; then
    print_warning "您有未提交的修改被stash，解决冲突后，请运行 'git stash pop' 恢复这些修改"
  fi
  
  exit 1
fi

# 询问是否要推送到远程仓库
read -p "是否要推送更新到远程仓库? (y/n): " PUSH_CONFIRM
if [ "$PUSH_CONFIRM" = "y" ] || [ "$PUSH_CONFIRM" = "Y" ]; then
  print_message "正在推送到远程仓库..."
  git push origin $LOCAL_BRANCH
fi

# 如果之前有stash，恢复
if [ "$STASHED" = true ] && [ "$LOCAL_BRANCH" = "$CURRENT_BRANCH" ]; then
  print_message "正在恢复您的未提交修改..."
  git stash pop
fi

# 如果切换了分支，问用户是否要切回原来的分支
if [ "$LOCAL_BRANCH" != "$CURRENT_BRANCH" ]; then
  read -p "是否要切回原来的 '$CURRENT_BRANCH' 分支? (y/n): " SWITCH_BACK
  if [ "$SWITCH_BACK" = "y" ] || [ "$SWITCH_BACK" = "Y" ]; then
    git checkout $CURRENT_BRANCH
  fi
fi

print_message "同步完成!" 