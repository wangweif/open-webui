# 致远 OA 单点登录集成实施方案（单地址模式·已定稿）

> 目标：OA 中点击"AI 智能助手"页签/菜单，免登录直接进入我方系统。
> 方式：**单地址模式**（《CIP应用接入单点登录集成技术文档-V2.0.pdf》原文机制）——OA 跳转时把浏览器重定向到我方登录地址并拼接 `?ticket=XXX`；我方拿 ticket 回调 OA 校验接口获取用户信息，自动开户并直接登录。
> 状态：**方案已定稿，代码已实现**（2026-08-14）。

---

## 1. 确定的实施方式

```
用户点击 OA 页签
   │
   ▼
OA 302 重定向  →  https://dp.bjzntd.com/api/v1/auths/sso/seeyon/login?ticket=XXX
   │
   ▼
我方后端回调 OA  →  GET https://oa.bjny.org.cn:8443/seeyon/thirdpartyController.do?ticket=XXX
   │                （响应头 LoginName / MemberId / MemberName，响应体即登录名）
   ▼
解析/自动创建用户 → 生成 JWT → 写 Cookie(token)
   │
   ▼
302 重定向 →  https://<我方域名>/auth#token=JWT （前端自动登录，现有机制，无需改前端）
```

**不采用**：CIP 两段式 SSO 接口握手（模式二）、OAuth/Token 认证、OA 插件页签（Portal 方式 B）。仅 OA 侧配置 + 我方一个登录接口。

---

## 2. 我方已实现（代码）

| 文件 | 说明 |
|---|---|
| `backend/open_webui/routers/sso.py`（新增） | SSO 登录接口 + 用户解析/自动开户 |
| `backend/open_webui/env.py` | 新增 SEEYON_SSO_* 环境变量 |
| `backend/open_webui/main.py` | 注册路由 `/api/v1/auths/sso/seeyon/login` |
| 根目录 `.env`（新建，gitignore） | 后端 SSO 环境变量；`docker-compose.offline.yaml` 挂载进容器 |
| `scripts/mock_seeyon_oa.py`（新增） | 本地联调用的 Mock OA（ticket 校验接口模拟器） |

### 接口

`GET /api/v1/auths/sso/seeyon/login?ticket=XXX&redirect=/s/xxx（可选）`

行为：
1. 参数校验：未启用 SSO 或缺少 ticket → 302 到登录页 `/auth`；
2. 服务器回调 OA 校验接口，从响应头取 `LoginName`（缺失时回退响应体），失败（非 200 / `SSOLogoutError` 头或正文）→ 302 到 `/auth`；
3. 用户解析：① 按 `oauth_sub="seeyon:{LoginName}"` 匹配 → ② 按 email 匹配 → ③ 自动开户（随机密码、默认角色 `SEEYON_SSO_DEFAULT_ROLE`、姓名取 `MemberName`）；
4. 生成 JWT、写 `token` Cookie（HttpOnly，SameSite/Secure 沿用现有配置）；
5. 记录登录审计（`UserLogins`，`login_method=seeyon_sso`）；
6. 302 → `/auth#token=JWT`（可选 `?redirect=` 深链，仅允许站内相对路径，防开放重定向）。

### 配置（根目录 .env）

| 变量 | 说明 | 默认 |
|---|---|---|
| `ENABLE_SEEYON_SSO` | 总开关 | `false`（bjny/nkxz 已开 `true`） |
| `SEEYON_SSO_VALIDATE_URL` | OA ticket 校验接口完整地址（一个变量，直接拼接好） | `https://oa.bjny.org.cn:8443/seeyon/thirdpartyController.do` |
| `SEEYON_SSO_TIMEOUT` | 回调超时（秒） | `10` |
| `SEEYON_SSO_VERIFY_SSL` | 校验 OA 证书（自签设 False） | `True` |
| `SEEYON_SSO_EMAIL_SUFFIX` | OA 登录名非邮箱时的邮箱后缀 | 空 → `{登录名}@localhost` |
| `SEEYON_SSO_DEFAULT_ROLE` | 自动开户角色 | `user` |

> **生效方式**：后端运行时读取**项目根目录 `.env`**（`backend/open_webui/env.py` 启动时 `load_dotenv(BASE_DIR/.env)`），与前端 `.env.bjny`/`.env.nkxz`（Vite 构建用）无关。
> - 非 Docker：直接改根 `.env` 后重启后端；
> - Docker 离线部署：`docker-compose.offline.yaml` 已加挂载 `./.env:/app/.env`（`.env` 放 compose 同目录，**必须先存在**）；
> - `.env` 被 `.gitignore` 忽略，各环境（bjny/nkxz）部署机分别维护；`.env.bjny`/`.env.nkxz` 里不包含 SSO 配置（对后端无效，已移除）。

### 用户映射规则（重要）

- OA `LoginName` 是邮箱 → 直接作为本地 email；
- 非邮箱 → 拼 `SEEYON_SSO_EMAIL_SUFFIX`（如 `bjzhangzm@bjny.org.cn`）；未配置则 `bjzhangzm@localhost`；
- 已存在同 email / 同 `oauth_sub` 用户 → 直接登录（不重复建号）；
- 不存在 → 自动开户，**与注册逻辑保持一致**：带 `team_id=BASE_TEAM_ID`、`tenant_id=TENANT_ID`（RAGFLOW 基础团队/租户）。

> 建议：与 OA 管理员确认登录名格式。若 OA 登录名 = 我方 email，则 `SEEYON_SSO_EMAIL_SUFFIX` 留空即可天然匹配；否则设置后缀实现自动开户。

---

## 3. OA / CIP 侧配置步骤（管理员）

1. 【CIP集成平台】→【第三方应用】→ **产品登记**（名称：AI 智能助手）；
2. **应用注册**：接入类型选 **PC**（如需移动端追加"移动URL"）；
3. 【应用接入】→ **接入设置**：用户绑定按需（免绑定/登录名匹配或点对点绑定）；
4. **单点登录**：认证模式选 **门户认证机制**，**PC 登录地址**填：
   `https://dp.bjzntd.com/api/v1/auths/sso/seeyon/login`
   （协议必须与 OA 一致，https；若 OA 版本有独立"SSO接口"字段可留空/与登录地址同值）
5. **登录授权**：配置可见角色/人员；
6. 【应用菜单绑定】→ 新建菜单：选择该应用、命名"AI 智能助手"、选图标 → 保存；
7. 普通用户登录 OA → 点击菜单验证。

> 若 OA 不支持 CIP 应用接入（需要插件页签），备用方案：OA 服务器部署 `ThirdpartySpace` 插件，`loginURL`=上述登录地址，`pageURL`=我方首页（详见原方案附录 A，当前不采用）。

---

## 4. 网络与部署

- 我方登录地址必须 OA 服务器和用户浏览器均可访问的 HTTPS URL（本次：`https://dp.bjzntd.com/api/v1/auths/sso/seeyon/login`）；
- 反向代理（nginx）需透传 `Host` 头（`proxy_set_header Host $host;`），保证跳转回 `https://dp.bjzntd.com/auth#token=...`；
- 防火墙：我方服务器 → OA 8443 出方向放行（回调用）；
- OA 8443 若为自签证书：`SEEYON_SSO_VERIFY_SSL=False` 或配置 CA 信任；
- 建议 Nginx 对本接口限流 + 记录日志。

---

## 5. 本地联调测试（无 OA 环境）

OA 侧暂时无法配合时，用仓库里的 Mock 模拟 OA 校验接口即可全流程自测。

### 5.1 启动 Mock OA
```bash
python3 scripts/mock_seeyon_oa.py            # 默认 0.0.0.0:18080
```
模拟规则：`ticket=test1/test2` 正常返回；其它 ticket 返回默认用户；`bad*` 返回 403；`logout*` 返回 `SSOLogoutError` 头。

### 5.2 后端指向 Mock
修改根目录 `.env`（仅测试期间）：
```ini
SEEYON_SSO_VALIDATE_URL=http://127.0.0.1:18080/seeyon/thirdpartyController.do
```
重启后端进程（改 `.env` 必须重启才生效）。

### 5.3 触发登录
浏览器访问（后端默认 8081，按你本地端口改）：
```
http://127.0.0.1:8081/api/v1/auths/sso/seeyon/login?ticket=test1
```
预期：307 跳转到 `/auth#token=...` → 前端自动登录 → 进入首页；用户管理里出现 `bjzhangzm@localhost`（姓名 Zhang San）。

### 5.4 失败场景
| 访问 | 预期 |
|---|---|
| `?ticket=bad1` | 跳登录页（无会话） |
| `?ticket=logout1` | 跳登录页（无会话） |
| `?ticket=`（空） | 跳登录页 |

### 5.5 收尾
测试完把 `.env` 的 `SEEYON_SSO_VALIDATE_URL` 改回：
```ini
SEEYON_SSO_VALIDATE_URL=https://oa.bjny.org.cn:8443/seeyon/thirdpartyController.do
```
（Mock 脚本不参与生产，留在仓库仅作联调工具。）

---

## 6. 联调 Checklist


1. 我方 Mock：伪造 OA 返回 LoginName 头/正文 → 验证开户、登录、JWT Cookie、审计；
2. 无效 ticket / 非200 / SSOLogoutError → 302 登录页，无会话；
3. OA 点击 → 免登录进入系统；重复点击 / 双开（ticket 一次性由 OA 控制）；
4. 未授权用户看不到菜单；已授权未绑定用户 → 按映射规则开户或拒绝；
5. 登出后再次点击可重新免登录。

---

## 7. 参考文档

- 《CIP应用接入单点登录集成技术文档-V2.0.pdf》：单地址模式机制、`thirdpartyController.do` 响应头（LoginName/MemberId/MemberName）、正文即登录名、ticket 一次性、`logoutNotify` 有 BUG 不依赖、V6.1 起 ticket 需加密（需与 OA 管理员确认版本）。
- CIP集成平台-单点登录操作说明：open.seeyoncloud.com/v5devCIP/250/257/258.html、259.html
- Portal集成-页签集成：open.seeyon.com/book/ctp/ji-cheng-chang-jing/portalji-cheng.html
