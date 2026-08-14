==========================================================
 Open WebUI 内网离线部署包（U盘版）
==========================================================

一、本文件夹包含什么
----------------------------------------------------------
  open-webui-offline-nkxz.tar.gz   离线镜像压缩包(约1.1GB, 导入后标签 open-webui:offline-nkxz)
  docker-compose.offline.yaml      部署编排文件(已配置数据目录 bind mount 到 /root/data/open-webui)
  deploy.sh                        服务器上一键部署脚本
  docs/离线部署指南.md               完整操作手册(参考用, 不用拷到服务器也行)

二、部署前置要求
----------------------------------------------------------
  - 服务器已安装 Docker(不需要 Python/Node)
  - 用 root 账号操作(数据目录在 /root/data/open-webui)
  - 服务器架构 x86_64 或 arm64 均可(镜像已按架构打包)

三、部署步骤（服务器上，root 执行）
----------------------------------------------------------
  把整个文件夹拷到服务器任意目录, 例如 /opt/open-webui/:

  1. 拷贝到服务器:
     直接复制整个文件夹到 /opt/ 下即可(U盘插入后 cp -r)

  2. 进入目录:
     cd /opt/open-webui

  3. 【重要】编辑 docker-compose.offline.yaml, 修改环境变量:
     - OPENAI_API_BASE_URLS: 改成模型服务/Pipeline 的真实地址
       (同一台机器: http://host.docker.internal:8000/v1;http://host.docker.internal:9099/api/v1
        其他机器:   http://那台机器IP:端口/v1)
     - WEBUI_SECRET_KEY: 改成一段随机字符串(重要, 升级前后保持一致)
     vi docker-compose.offline.yaml

  4. 一键部署:
     bash deploy.sh
     或手动执行:
       docker load -i open-webui-offline-nkxz.tar.gz
       mkdir -p /root/data/open-webui
       docker compose -f docker-compose.offline.yaml up -d

  5. 验证:
     curl http://127.0.0.1:3000/health        # 预期 {"status":true}
     浏览器访问 http://服务器IP:3000            # 首次注册的账号是管理员

四、数据在哪里
----------------------------------------------------------
  /root/data/open-webui/
    ├── webui.db      数据库(账号/聊天记录/配置)
    ├── uploads/      上传文件
    └── config.json   实例配置

  备份: 停容器后直接打包该目录即可, 不需要 docker 命令。

五、升级/重启常用命令
----------------------------------------------------------
  docker compose -f docker-compose.offline.yaml down     # 停止
  docker compose -f docker-compose.offline.yaml up -d    # 启动
  docker logs -f open-webui                              # 看日志

  升级: 拷入新镜像包 → docker load -i ... → up -d, 数据不丢。
==========================================================
