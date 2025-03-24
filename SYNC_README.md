# Fork仓库同步脚本使用说明

这个目录包含两个脚本，用于帮助您将fork的仓库与原始仓库（上游仓库）保持同步。

## 脚本说明

1. `sync_upstream.sh` - 交互式同步脚本
2. `auto_sync_upstream.sh` - 自动同步脚本（可以通过定时任务运行）

## 交互式同步脚本 (sync_upstream.sh)

这个脚本提供了交互式的方式来同步您的fork仓库与原始仓库。

### 使用方法

```bash
./sync_upstream.sh
```

脚本将会：
1. 检查并添加原始仓库作为上游（upstream）
2. 自动保存您未提交的修改（stash）
3. 展示上游仓库的分支
4. 询问您要同步的分支
5. 询问您是否要将更新同步到当前分支
6. 如果有冲突，会通知您手动解决
7. 询问您是否要将更改推送到您的远程仓库
8. 恢复您未提交的修改（如果有）

## 自动同步脚本 (auto_sync_upstream.sh)

这个脚本可以自动同步，适合设置为定时任务运行。

### 使用方法

```bash
./auto_sync_upstream.sh [上游分支名] [本地分支名]
```

例如：
```bash
./auto_sync_upstream.sh main main
```

参数说明：
- 第一个参数是上游分支名（默认为 main）
- 第二个参数是本地分支名（默认为 main）

### 设置定时任务

您可以使用cron设置定时任务来自动同步：

```bash
# 编辑cron任务
crontab -e

# 添加以下行以每天早上3点自动同步
0 3 * * * /path/to/your/repo/auto_sync_upstream.sh >> /path/to/your/home/sync_cron.log 2>&1
```

## 日志

自动同步脚本会在您的主目录下创建一个 `sync_upstream.log` 文件，记录同步过程中的所有操作和可能的错误。

## 注意事项

1. 这两个脚本假设原始仓库的URL是 `https://github.com/open-webui/open-webui.git`。如果不是，请修改脚本中的URL。
2. 如果您在同步过程中遇到冲突，交互式脚本会要求您手动解决，而自动脚本会中止合并并记录冲突文件。
3. 自动脚本在遇到问题时会尽量恢复到初始状态（切换回原分支，恢复stash等）。
4. 建议在使用自动脚本前先使用交互式脚本熟悉同步流程。 