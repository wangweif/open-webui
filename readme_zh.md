## 说明：
这个代码是从https://github.com/open-webui/open-webui.git （上游仓库）fork出来的代码，新的git地址是
https://github.com/wangwei/open-webui.git

因为open-webui还在快速开发中，知识库功能还属于alpha阶段，所以我们需要是不是从上游仓库中更新代码，如果还把我们的代码放到codeup服务器上，那么就需要定时从github上更新代码，然后手工比较合并，所以这个仓库仓库放到github上。

## TODO:

- [ ] UI去掉open-webui这样的明显logo
- [ ] 去掉不需要的功能，比如大模型的参数（templator, top_p）配置（管理员账号可以保留）
- [ ] 搜索功能跑通（是否需要在香港部署服务器）

## 合并代码：

从upstream（https://github.com/open-webui/open-webui.git）上合并代码的方法：

```
添加原始仓库为远程仓库
git remote add upstream https://github.com/original-owner/repository.git
从上游仓库获取最新的代码：
git fetch upstream
将上游仓库的最新代码合并到你的主分支：
git merge upstream/main
```

我们还是基于上游仓库的master分支同步代码，最好是每发布一个版本（tag）同步一次。功能性的问题，除非特别紧急，我们就等待上游仓库修复。比如基于知识的问题，最新版本0.5.20还没解决，但dev版本已经解决，我们就等0.5.21版本。