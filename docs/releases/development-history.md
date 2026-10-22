# 早期开发与发布流程：历史发布记录

[当前说明](../REPOSITORY_UPDATE_FLOW.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

# Marzban 开源扩展功能

## 历史片段 2

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## 当前扩展

- `/api/node/{node_id}/health` 经现有 Node 认证通道读取对应节点的 CPU、内存、磁盘和运行时间；过期或无效快照不显示为实时值。
- 节点管理界面展示上述指标。2026-10-02 本地开发版优先读取 Xray `GetAllOnlineUsers`；旧核心回退到 Node 观察到的近期流量，旧 Node 回退到主面板 `NodeUserUsage` 记录。来源、范围、采样时间分别标注，详情见 [活动与策略合同](../NODE_ACTIVITY_AND_POLICY.md)。
- `/api/node/{node_id}/egress` 按节点 ID 保存唯一一条 HTTP/SOCKS 出站配置；新增更多 Node 时各自独立配置住宅 IP。凭据加密存储，API 不回显密码；下发时只给该节点的配置副本添加 `marzban_node_extensions` 扩展，不修改主面板 Xray 配置。
- 配置前先通过 Node 健康响应确认 `managed-outbounds-v1` 能力；不支持的旧 Node 不接收新配置。删除出站会触发节点重启以恢复原路由。
- 用户设置新增设备限制字段：`device_limit`、`device_limit_mode`、`device_limit_action`；普通订阅和指定客户端格式订阅可通过 `X-HWID`、`X-Device-OS`、`X-Device-Model` 登记设备，并由 `/device-status` 返回脱敏统计。原始 HWID 只保存 SHA-256 哈希；`reject_new` 超限返回 `429`，`log_only` 只记录不拒绝。
- 设备限制在带 HWID 的订阅请求登记时执行；`reject_new` 为每个已登记 HWID 生成独立协议凭据，并通过现有 Xray 控制通道同步到主核心和已连接 Node。配置同时保留共享账号供普通客户端兼容使用；无 HWID 返回正常订阅，不登记设备，不能保证其限额。带 HWID 的超额新请求返回 `429`，不能靠切换输出格式获得新的独立凭据；共享配置复制使用仍能绕过 HWID 限额。它不是实时在线设备数统计，真实客户端及服务器仍需验收。

设备限制代码已完成；历史专项测试为 5 passed、历史完整测试为 22 passed，本轮主面板完整 pytest 为 43 passed，Node 为 39 passed，SQLite 迁移升级/回滚也已通过。2026-10-01 的正式 Actions 记录保留为历史证据；本轮新增的设备专属凭据与 Node 配置加载尚未完成新的 Actions、镜像和服务器验收，因此当前仍是测试版，不是 Xray 实时连接数限制。

住宅出口功能必须与同一开发系列的 `kissow/Marzban-node` 配对。legacy 模式下 HTTP 代理只承载 TCP，UDP 保持原路由；本地未发布的新模式行为见上方合同。尚未实现住宅代理自动健康检查、故障摘除、按用户/分组路由及精确实时设备数限制。新增 Node 活动统计仍需配对镜像与真实服务器验收。

节点指标只由 Marzban 向 Node 通过现有认证通道读取，并由 Marzban 的受保护 API 提供。任何获授权的外部项目均可独立调用该 API；本仓库不包含特定业务系统的对接、别名映射或页面代码。

接口用途、`.env` 配置与 API 的区别，以及每次改动必须同步维护文档的发布流程，见 [Mr.shaw 扩展接口与更新规范](../../MR_SHAW_API_AND_RELEASE.md)。

## 历史片段 3

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## 本地验证

主面板 Python 单元测试：`python -B -m unittest discover -s tests -v`。管理端执行 `tsc --noEmit` 和 `vite build`。Alembic 迁移需在备份后的测试数据库先升级、回滚，再验证原有节点与用户数据。Node 端还需用其配套测试和 Xray 二进制预检。

## 历史片段 4

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

# Mr.shaw Marzban Fork 更新记录

## 历史片段 5

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-15 文档导航整理

中英文README恢复产品介绍、安装和简洁导航；发布编号、测试、Actions、镜像摘要及验收记录迁入对应docs专页，旧首页历史完整归档。新增[文档中心](../README.md)，更新维护流程，今后不在产品首页堆叠维护日志。原安装命令、上游署名及许可证保留；仅文档，不改变API、运行代码或已发布镜像。导航/证据保留检查118项通过。

## 历史片段 6

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-03 普通订阅客户端兼容修复（镜像已发布，服务器验收待完成）

- 修复开启 `reject_new` 后普通客户端因不带 `X-HWID` 而全部收到 `428`、无法导入订阅的问题；无 HWID 请求恢复原共享凭据订阅，不登记设备。
- 同时恢复主核心与 Node 的共享账号加载和增量同步，避免只修 HTTP 响应导致“能导入但无法连接”。已登记 HWID 仍使用稳定的独立协议凭据，超出登记额度的新 HWID 仍返回 `429`；`device_limit=0` 不限制登记数量。
- 明确兼容边界：不带 HWID 的客户端走共享账号，不能强制执行 HWID 限额，也能绕过这一限额。登记数量不是物理设备数或实时在线数；Node 策略 ACK 不是所有客户端被拦截的证明。
- 新增真实 ASGI 路由回归、共享/独立账号同步与 XTLS 传输规则测试；没有 UI、数据库迁移、Node 通道、脚本、证书、端口、环境文件或核心版本变化，Xray 仍为 `v26.3.27`。
- 本条替代下方历史条目的“必须 HWID / 只加载设备账号 / 无 HWID 返回 428”行为。服务器先前确认后又报告订阅失败，故本轮服务器验收重新待完成；不能沿用此前通过结论。
- 发布证据：主面板源 commit `37bab0b113c44ccb2a9db6230ac982b7d2a889a1`、Actions `37090609233`、GHCR `latest` index `sha256:c4bbe88b5b547bbdca3d6b8a4bf1e7c92aeb29ae50b36cd758b7c6eccae2edfc`；配对 Node 源 commit `c135743d1ad26d45538e4c6c7a65a9c6693856a8`、Actions `37090612247`、GHCR `latest` index `sha256:21340918298f0b8647fb7eb360294334891fc219e280a75af5d133c66ee9fbc1`。两个仓库正式 Xray 均为 `v26.3.27`。

## 历史片段 7

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## CI 构建问题登记与成功复盘（2026-10-01）

- 正式分支合并提交 `9a040201cbe0bc2e783e4ab44e7069ca6fe443a1` 触发 Actions run `36832627106`，在 `Check backend` 阶段失败，后续前端构建和 GHCR 发布未执行。
- 原因是仓库工作流使用 `python -m unittest discover -s tests -p 'test_*.py' -v`，新增 `tests/test_user_device_limit.py` 却依赖未声明的 `pytest` fixture；干净 CI 环境没有 pytest，导致 `ModuleNotFoundError`。
- 已将专项测试统一改为仓库现有的 `unittest.TestCase`、`setUp/tearDown` 规范，未新增第三方测试依赖；本条修复提交后必须重新跑完整 unittest，再等待 Actions 成功后才允许使用 `latest`。
- 防重复检查：新增测试必须使用 CI 实际执行的测试命令；如果要使用 pytest，必须同时把 pytest 固定写入依赖并修改 CI 命令，不能只在本地环境偶然通过。

### 第二轮 CI 失败复盘（run `36835708735`）

- 第一轮测试框架修复后，正式 Actions 仍在 `Check backend` 阶段失败，前端、Docker 和 GHCR 步骤仍未执行。
- 根因是锁定的 `APScheduler==3.9.1.post1` 仍导入 `pkg_resources`，而 CI 安装的最新版 setuptools 已移除该兼容模块，导致 `ModuleNotFoundError: No module named 'pkg_resources'`。
- 已在 `requirements.txt` 明确加入 `setuptools<81`，让干净 CI 和 Docker 构建使用同一套可复现依赖；这不是跳过测试，也不改变运行时业务逻辑。
- 防重复检查：每次依赖升级或 Python 版本变更后，必须在干净环境执行完整 `unittest discover`；锁定依赖若依赖已移除的兼容模块，必须在依赖文件中显式锁定兼容版本，不能依赖 CI 当时碰巧解析出的 setuptools 版本。

### 第三轮 CI 失败复盘（run `36836757035`）

- 依赖兼容修复后，`unittest` 已开始执行并通过前 17 个测试，但导入设备限制测试时仍失败；前端、Docker 和 GHCR 步骤未执行。
- 根因是该测试直接导入数据库模型，而应用导入链会初始化 Xray；干净 CI 没有 `/usr/local/bin/xray`，因此出现 `FileNotFoundError`。这不是生产镜像缺少 Xray，而是测试没有隔离应用启动副作用。
- 已让专项测试在导入前使用临时 Python 版本桩和仓库测试配置，仅隔离测试导入，不改变 `.env`、Dockerfile、生产 Xray 路径或运行时逻辑。
- 防重复检查：单元测试不得因为导入模型而隐式要求系统服务；必须在干净 CI 中验证测试模块可导入，外部二进制依赖要么由测试步骤显式安装，要么使用仅限测试的隔离桩。

### 成功构建确认（run `36838046078`）

- 修复后的后端测试、前端 TypeScript/Vite 检查与构建、Xray 正式版本校验、多架构 Docker 构建和 GHCR 发布均成功；后端日志确认 `Ran 22 tests`、`OK`。
- 本次问题登记闭环为：失败 run → 根因 → 修复提交（`7cb7117`、`eca8fcb`、`071819b`）→ 完整 CI 重跑 → 镜像 digest/revision 核对。以后不得只看到代码已推送就视为可更新，必须完成同样的闭环。
- 防复发总闸门：新增测试必须匹配 CI 命令；依赖必须在干净环境安装；测试导入不得隐式要求生产二进制；构建成功后必须核对 `latest` 的 index、amd64、arm64 digest 和 OCI revision；所有失败原因必须在本文件和发布流程登记。

## 历史片段 8

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 跨仓库更新规范登记（2026-09-30，文档变更）

- 主面板每次代码、API、数据库、UI、配置、Xray 核心或发布脚本变更，都必须与 `kissow/Marzban-node`、`kissow/Marzban-scripts` 及项目资料的变更登记卡配对记录。
- 本仓库同步维护 `FORK_FEATURES.md`、`MR_SHAW_API_AND_RELEASE.md`、README、测试验收清单、GitHub Actions run、GHCR 镜像 digest 和服务器验收状态；没有对应证据的条目不得写成“已发布”。
- 接口变化必须逐项记录方法、完整路径、权限、请求/响应、错误码、副作用、Node 兼容和回滚方式；仅 UI/文档变化明确标记 API、数据库、Node 通道、证书和端口无变化。
- 统一模板见项目资料 `08-跨仓库更新登记模板.md`，三仓库接口和命令总索引见 `09-接口登记索引.md`。本条只规范记录流程，不新增运行时 API、数据库字段或 Node 通道。

## 历史片段 9

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 文档补充（2026-09-30，未发布）

- 补齐 `MR_SHAW_API_AND_RELEASE.md` 中原版 `.env.example` 的配置项说明，包括客户端模板、状态/自动清理、通知/Webhook、JWT、调度间隔和开发开关。
- 明确截图中的“变量/描述”表是运行配置，不是 HTTP API；原版 API 以启用 `DOCS=True` 后的 `/docs`、`/redoc` 和源码路由为准。
- 记录底部捐赠菜单的真实修改位置：`app/dashboard/src/constants/Project.ts` 的 `DONATION_URL` 控制跳转，README 中英文本的 `Donation/捐赠` 小节控制钱包地址展示；本次没有修改捐赠地址、支付逻辑、数据库、Node 通道或生产配置。

## 历史片段 10

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 开发中（尚未稳定发布）

- 节点设置沿用官方 Chakra 界面与证书、端口、启用开关等原功能，新增按节点折叠展示的运行状态。
- 新增受管理员权限保护的 `GET /api/node/{node_id}/health`，通过原有认证通道读取该节点的 CPU、内存、磁盘、运行时间；无可靠来源的在线设备数返回空值。
- 每个 Marzban-Node 可独立保存一条 HTTP 或 SOCKS5 住宅 IP 出口。支持服务器、端口、可选账号密码；密码加密存储，API 不回显明文。
- 保存出口时只向对应 Node 下发配置，旧版 Node 不支持扩展时拒绝保存；删除出口后恢复原有路由。
- （历史阶段记录）设备数量限制当时尚未实现，计划在用户设置区域单独开发；该阶段已被上方的用户设备登记、独立凭据和 Node 配置加载链取代，不能把公网 IP 数当作实际设备数。

发布时须记录与 `kissow/Marzban-node` 的配对版本，并完成真实 Xray、Linux Node 与数据迁移测试。

## 历史片段 11

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

# Mr.shaw 扩展接口与更新规范

## 历史片段 12

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 三层边界

1. **主面板配置层**：`/opt/marzban/.env` 设置运行环境，`/var/lib/marzban` 保存默认数据库、Xray 配置等数据；路径随实际部署而异。`SUDO_USERNAME`/`SUDO_PASSWORD` 用于初始化管理员，`SQLALCHEMY_DATABASE_URL` 指向数据库，`UVICORN_HOST`/`UVICORN_PORT` 指定 Web 监听，`XRAY_JSON` 指向 Xray 配置文件，`XRAY_EXECUTABLE_PATH` 指向二进制，`XRAY_SUBSCRIPTION_URL_PREFIX` 是订阅 URL 前缀，`DOCS=True` 才显示 `/docs` 和 `/redoc`。这些是进程配置项，不是 HTTP 路径；不要在文档或截图中泄露 `.env`、数据库连接串和密钥。升级不要覆盖已有 `.env`。
2. **主面板管理员 API**：统一在 `/api` 下；下列节点相关接口均要求现有超级管理员 Bearer Token，不应直接开放给用户端。认证入口为 `POST /api/admin/token`，按原版现有认证流程取令牌；不要把管理员凭据写到浏览器公开脚本或第三方仓库。
3. **Node 内部通道**：Marzban 通过原有认证连接向对应 Marzban-Node 取指标并下发配置。REST 模式下 Node 的 `POST /health` 需要有效 `session_id`；RPyC 模式使用 `fetch_health`。它们不是面向第三方的公开监控接口，不新增公网监控端口。Node 的 Xray API 端口与住宅代理商提供的端口也不是同一种端口。

## 历史片段 13

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 在 GitHub 仓库构建，服务器只拉取镜像

本 Fork 的生产镜像由仓库的 `.github/workflows/build.yml` 构建，不要求每次登录服务器编译。该工作流在 `master` 分支 push 或手动运行时执行后端单元测试、Dashboard TypeScript/Vite 构建，并发布多架构镜像 `ghcr.io/kissow/marzban:latest`；`docs/*`、`feature/*` 等普通分支不会覆盖生产 `latest`。

### 发布一次更新

1. 在本地完成功能、`CHANGELOG.md`、接口文档和验收记录，运行 `git diff --check`、后端测试和前端构建。
2. 推送到 Fork 的功能/文档分支，确认检查通过后合并到 `master`。不要直接把未验收的分支当作生产镜像。
3. 打开 GitHub 仓库的 **Actions → Mr.shaw fork image**，选择 `master`，点击 **Run workflow**；或者直接 push `master` 让它自动触发。
4. 等待 `verify-and-build` 全部成功，再检查该运行对应的 commit SHA 和 `ghcr.io/kissow/marzban:latest` 的发布时间/摘要。Actions 失败或 `latest` 尚未发布时，服务器不要更新。

### 服务器更新（仅拉取，不构建）

先进入服务器实际的 Marzban Compose 目录，确认 `docker-compose.yml` 使用的是 `ghcr.io/kissow/marzban:latest`，并备份 `.env` 与 `/var/lib/marzban`。然后执行：

```bash
cd /实际的/marzban目录
cp .env ".env.backup.$(date +%Y%m%d-%H%M%S)"
sudo tar -C /var/lib -czf "/root/marzban-data-backup-$(date +%Y%m%d-%H%M%S).tar.gz" marzban
docker compose pull marzban
docker compose up -d --no-build marzban
docker compose ps
docker compose logs --tail=100 marzban
```

只更新镜像和容器，不执行 `docker compose down -v`，不删除容器卷，不覆盖 `.env`、数据库、证书、端口、Xray 配置或 Node 配置。若部署不是 Compose，而是已安装的 `marzban` 管理脚本，则先执行 `sudo marzban status` 确认脚本版本，再按该脚本的 `update` 流程操作；两种部署方式不要混用。

### 更新后的验收顺序

先确认容器为 `Up`、迁移日志无错误，再登录管理面板检查管理员、用户、订阅、证书、端口和节点；最后逐台检查 Node、订阅导入和住宅出口。只有验收通过后，才在 `CHANGELOG.md` 把“未发布”条目标记为已发布，并记录实际 commit SHA、镜像摘要、备份文件和回滚方法。

## 历史片段 14

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 本 Fork 节点 API 速查

2026-09-30 `mrshaw-v0.8.4-preview.4`（已发布）仅调整节点弹窗布局：最大宽度 800px，刷新按钮从最右端移至运行指标标题旁边，五项指标铺满可用内容区；API 请求、响应、权限和 Node 通道无变化，无需更新 Node。本机真实组件桌面/手机渲染已确认；Actions `36726339140` 成功，合并 SHA `ee96a1b8afe8fd638d75fe9b5975124268a02736`，`ghcr.io/kissow/marzban:latest` index 摘要 `sha256:e1ad34e5a0b4bd73811cc7d14f05b2f51641da80919a7b9224a0a4b469b58fdd`，amd64/arm64 revision 均匹配；服务器截图仍需在镜像发布后验收。

| 方法和路径（Marzban） | 用途与返回 | 写入/副作用 |
| --- | --- | --- |
| `GET /api/nodes` | 列出节点及 ID，供选择 `node_id`；原版接口 | 无 |
| `GET /api/node/settings` | 原版证书设置，节点安装时使用；不要删除或替换 | 无 |
| `GET /api/node/{node_id}/health` | 返回此 Node 的 `status`、`reason`、`metrics`，包含采样时间、CPU、内存、根目录磁盘、运行时间、数据来源；主面板可在 `metrics` 中补充最近 2 小时有正流量的去重用户及采样原因；离线或过期时 `metrics=null` | 通过已认证通道读取 Node，并查询主面板 `NodeUserUsage`；不写数据 |
| `GET /api/node/{node_id}/egress` | 返回 `configured`、协议、`udp_mode`、服务器、端口、用户名、`has_password`；**不返回密码** | 无；`udp_mode` 为本地未发布扩展 |
| `PUT /api/node/{node_id}/egress` | 保存该 Node 唯一的 HTTP/SOCKS5 代理。字段：`protocol`（`http`/`socks`）、`server`（代理商域名或 IP）、`port`（1–65535）、可选成对的 `username`/`password`、`udp_mode`（省略 legacy；proxy/tcp_only）。同用户名且密码留空可保留原密码 | 检查 `managed-outbounds-v1`；非 legacy 另检查 `managed-outbounds-udp-v1`；加密保存并异步重启。旧/离线/能力不足 409，参数或 HTTP+proxy 不合法 422；新模式本地未发布 |
| `DELETE /api/node/{node_id}/egress` | 清除该 Node 的代理设置 | 删除配置并异步重启该 Node，恢复原有默认路由 |
| `POST /api/node/{node_id}/reconnect` | 原版重连入口；排查离线 Node | 异步重连 |

Node 响应 `source=node-runtime` 与 `capabilities=["managed-outbounds-v1"]` 是扩展兼容性标记。主面板仅接受新鲜且合法的快照（超过 15 秒或异常则不展示为实时数据）。Node 原始快照没有可靠的在线用户来源时，`active_users` 为 `null`；主面板可根据最近 2 小时 `NodeUserUsage` 的正流量记录补充去重用户数，并返回 `active_users_window_hours`、`active_users_sampled_at` 和 `active_users_reason`。该值不是 Xray 实时在线连接数，不得用总在线数或 TCP 连接数填充。

节点管理弹窗在节点标题栏下方、证书区上方显示连接状态与原因：`node.message` 有值时优先显示后端原因，否则按 `connecting`、`error`、`disabled` 显示本地化兜底文案。`connecting` 和 `error` 状态提供“重新连接”按钮并调用上面的 `POST /api/node/{node_id}/reconnect`；`disabled` 只显示停用原因，不提供重连按钮。此项只改官方 Chakra UI 的原节点弹窗，不删除证书、端口、启用、保存或删除字段。

住宅代理地址从代理服务商取得，不填 Marzban 主面板地址、Node 地址、Node 的服务端口或 Xray API 端口。legacy 下 HTTP 只接管默认 TCP、UDP 按原路由；未发布新模式的 DNS 上游替换、显式路由优先级及其他 UDP 阻断边界见上方合同。保存操作只是排队重启，HTTP 成功**不等于**住宅代理可连通：还要复查 Node 运行日志、出站公网 IP 和原订阅可用性。本功能尚无代理失效自动摘除和自动回滚。

## 历史片段 15

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 每次更新必须执行的流程

适用于主面板、Node、安装脚本、UI 和 API；即使只修布局，也要说明“接口无变化”。

1. **确定基线**：记录本次主面板/Node/脚本提交 SHA、当前镜像摘要、影响范围和原有数据路径。保护 `.env`、数据库、证书、端口、Xray 配置和用户记录；不在旧样式后叠加补丁，应修改原规则。预览稿必须和实际 Chakra 组件使用同一宽度/断点；截图验收要记录浏览器缩放与视口大小。
2. **写更新说明**：在对应仓库 `CHANGELOG.md` 的“未发布”条目写清改动、用户可见差异、兼容性及回退风险；不要把尚未打包的提交写成已发布版本。跨主面板和 Node 的功能，两边均要记录配对版本或 SHA。
3. **核对接口清单**：新增/修改/删除 API 时同步更新本文，逐项写 HTTP 方法、路径、权限、请求、响应、错误码、副作用、Node 通道和兼容约束。仅改 UI 时明确写“API 无变更”。更改配置项则同步更新配置表、示例与迁移说明；绝不提交真实密钥。
4. **测试并记录证据**：后端单测、前端 TypeScript/Vite、Node 单测/Xray 配置预检、迁移升级/回滚；检查旧用户、证书、端口、订阅和节点连接。真机桌面与窄屏逐项核对；出现问题先修再重测，更新 `05-检测测试验收清单.md` 的结果和剩余风险。
5. **先测试后发布**：先在隔离环境测试升级。CI 成功后核对镜像确实对应预期 SHA（不能只看仓库代码已提交），再公布可执行的服务器更新命令。`latest` 未发布成功时不得让服务器提前更新。Node/主面板协议变化需配对发布并按兼容顺序升级。
6. **部署与验收**：已有安装使用 `adopt`（首次从官方切 Fork）或 `update`（已在 Fork）；新机才用 `install`。先备份并核验，再更新主面板、逐台 Node，最后检查容器、日志、用户、订阅、节点、出站及桌面/手机端。不要用 `down -v` 或覆盖数据目录。正式发布记录写入两边实际提交 SHA、镜像摘要、测试结果和已知限制。

发布检查：代码、`CHANGELOG.md`、本文接口表、相应 README/FORK_FEATURES、验收清单必须一起审查；任一项缺失不发布镜像/更新指令。仅改文档也要说明其对应代码版本，不能把尚未实现的功能写成可用。

## 历史片段 16

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 接口变更登记模板（强制）

新增、修改或删除 HTTP、WebSocket、订阅响应、Node 内部 REST/RPyC 方法或配置字段时，在本文件对应接口表旁补充以下信息，并在变更登记卡中引用代码 commit 和测试证据：

```text
方法和完整路径/方法名：
认证与权限边界：
请求字段、类型、必填性、默认值和敏感字段：
成功响应状态、字段和脱敏规则：
错误状态码、错误体和触发条件：
数据库、缓存、队列、异步重启等副作用：
Node 通道、能力标识、最低配对版本和旧 Node 行为：
订阅/客户端兼容范围：
弃用周期、替代路径和回滚方案：
契约测试、权限测试、迁移测试和隔离/真实环境证据：
```

删除接口不能只删除路由：必须记录旧客户端的错误行为、替代路径、数据迁移和恢复方法。只改 UI 或文案时，也要明确写出 `API、数据库、Node 通道、证书和端口无变化`，避免把 UI 变化误当成接口发布。

## 历史片段 17

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

# Marzban 主面板发布清单

## 历史片段 18

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## 变更登记

- [x] 已记录日期、标题、发布状态和主面板 commit。
- [x] 已标记变更是否涉及 API、数据库迁移、Node 通道、订阅响应、证书、端口、`.env`、Xray 核心和 UI。
- [x] 已确认主面板、Node、脚本是否需要配对发布；没有影响的仓库也写明“无变化”。
- [ ] 没有把 `_patch.tmp`、`ui-preview/`、构建临时目录、数据库、密钥或生产配置加入提交。

## 历史片段 19

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## 代码和接口

- [x] 新增、修改或删除的路由已在 `MR_SHAW_API_AND_RELEASE.md` 登记：方法、完整路径、认证、请求、响应、错误码、副作用、Node 兼容、弃用和回滚。
- [ ] `.env.example`、配置表和 README 已同步；真实密码、Token、数据库连接串和代理凭据未进入仓库。
- [x] 数据库变化有 Alembic 迁移、升级前备份、回滚测试和旧用户/节点数据验证。
- [ ] 只改 UI 或文案时明确写出：API、数据库、Node 通道、证书和端口无变化。
- [x] 接口、订阅字段、Node 通道或配置字段变化已同步写入 [`docs/REPOSITORY_UPDATE_FLOW.md`](../REPOSITORY_UPDATE_FLOW.md)，并通知 Node/scripts 配对文档。

## 历史片段 20

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## 测试

- [x] `python -B -m unittest discover -s tests -v`（本轮 43 项）
- [ ] CI 使用的测试命令与本地测试命令一致；新增测试默认使用仓库现有 `unittest` 规范，未引入未声明的 pytest/fixture 依赖。
- [ ] 干净 CI 安装后导入所有测试模块；旧依赖若使用已移除的兼容模块（例如 `pkg_resources`），必须在依赖文件中显式锁定兼容版本。
- [ ] 单元测试导入数据库/应用模块时不隐式依赖 `/usr/local/bin/xray` 等生产服务；外部二进制依赖必须在测试步骤显式准备或由测试专用桩隔离。
- [x] 管理端 `npm exec tsc -- --noEmit` 和 `npm run build`（package.json 没有 typecheck 脚本）
- [x] `git diff --check`
- [ ] 订阅、二维码、用户到期、节点、证书和端口回归通过。
- [x] Node 配对契约、健康状态、住宅出口（如适用）和失败回滚通过。
- [ ] 桌面和手机视口真实渲染通过；记录视口、缩放、截图和是否横向溢出。

## 历史片段 21

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## CI、镜像和发布

- [x] GitHub Actions 成功，记录 workflow、run ID、源 commit 和失败重试结果。
- [x] 如 Actions 失败，记录失败步骤、根因、修复提交和重新构建结果；失败状态不得写成镜像已发布。
- [x] `ghcr.io/kissow/marzban` 的 tag/index digest、amd64/arm64 digest 与 OCI revision 对应源 commit。
- [x] 镜像能在干净环境拉取并启动；没有把 Actions 排队或代码已推送误写成已发布。
- [x] `CHANGELOG.md`、`FORK_FEATURES.md`、README、接口文档和项目验收清单状态一致。

## 历史片段 22

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## 问题复盘与防复发（强制）

- [ ] 每个失败 run 都登记：日期、run ID、失败 job/step、完整错误摘要、根因、修复 commit、复跑 run 和最终结论。
- [ ] 每个根因都转换为一个可执行的闸门（测试命令、依赖锁定、导入隔离、镜像摘要核对或服务器验收项），不能只写“已修复”。
- [ ] 复跑必须从干净 CI 环境开始；本地通过、代码已推送或 Actions 已排队都不能替代成功证据。
- [ ] 发布前复查历史问题登记，确认本次没有重新出现同类错误；若再次出现，追加同一问题的复发记录，不覆盖旧记录。

## 历史片段 23

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## 服务器验收与回滚

- [ ] 服务器更新前完成数据库、`.env`、证书、Xray 配置和数据卷备份并记录位置/校验。
- [ ] 官方旧安装只执行 `adopt`；已切 Fork 的安装只执行 `update`；新机才执行 `install`。
- [ ] 更新后验证容器、日志、用户、订阅、节点、证书、端口、出站和手机/桌面页面。
- [ ] 明确回滚镜像/tag 和数据库恢复方式；不执行 `docker compose down -v`，不删除 `/var/lib/marzban`。
- [ ] 服务器截图和日志验收完成后，才把状态改为“稳定发布”。

## 历史片段 24

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## 发布记录最小字段

```text
主面板 commit：
配对 Node commit：
配对脚本 commit：
Actions run：
GHCR index/架构 digest：
OCI revision：
Xray 版本：
API/数据库/Node 通道变化：
测试结果：
服务器验收结果：
已知限制与回滚方式：
```

## 历史片段 25

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

# Mr.shaw Fork 更新、接口与验收登记

文档分工：README及各语言README保持产品介绍、安装/使用和简洁导航；不堆叠发布编号、测试过程、SHA、Actions、镜像摘要或验收日志。功能变更更新对应docs专页，摘要写CHANGELOG，接口写接口文档，发布证据写发布页；README仅在产品介绍/使用入口变化时调整。保留上游署名与许可；旧记录迁移保留历史并修正相对链接。

[文档中心](../README.md) · [历史首页记录](../README_RELEASE_HISTORY.md)

## 历史片段 26

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 1. 每次更新必须同步的资料

1. `CHANGELOG.md`：用户可见变化、兼容性、已知限制和发布状态。
2. `README.md` / `FORK_FEATURES.md`：功能边界、安装/更新方式和与官方版本的差异。
3. `MR_SHAW_API_AND_RELEASE.md`：新增、修改、删除的 API、数据库、Node 通道和配置字段。
4. `RELEASE_CHECKLIST.md`：代码、迁移、构建、CI、镜像和服务器验收闸门。
5. 本文：跨仓库登记、接口索引、测试证据、源 commit、镜像摘要和服务器验收状态。

只改 UI 或文档也要明确记录：API、数据库、Node 通道、证书、端口和 Xray 核心无变化。节点状态 UI 若增加失败原因或重连按钮，必须确认仍调用既有重连 API，不能另开监控端口。未完成 CI、镜像或服务器验收时，状态只能写“测试中 / 未发布”，不能给生产服务器更新命令。

## 历史片段 27

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 2. 当前变更登记卡

```text
变更编号：MR-20261001-DEVICE-LIMIT
日期：2026-10-01
标题：在官方 Chakra 用户结构中加入用户级 HWID 设备登记限制
状态：测试版镜像已发布，服务器验收待完成

主面板：kissow/Marzban
Node：kissow/Marzban-node（无变化，不需要配对更新）
脚本：kissow/Marzban-scripts（无变化）
数据库迁移：4a9d2e8b7c61_add_user_device_limit.py、6d7e8f9012ab_add_device_credentials.py
Xray：v26.3.27，保持正式基线，不升级 v26.9.9
证书、端口、.env、数据卷、支付：无变化
```

## 历史片段 28

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 3. 本次接口索引

### 用户字段

原有用户创建/修改 API 承载以下字段：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `device_limit` | integer | `0` | `0` 表示关闭限制 |
| `device_limit_mode` | enum | `hwid` | 当前按订阅请求中的 HWID 登记 |
| `device_limit_action` | enum | `log_only` | `log_only` 只记录；`reject_new` 超限拒绝新设备 |

### 订阅请求

| 方法和路径 | 请求 | 成功/错误 | 兼容性和副作用 |
| --- | --- | --- | --- |
| `GET /{XRAY_SUBSCRIPTION_PATH}/{token}` | 可选 `X-HWID`、`X-Device-OS`、`X-Device-Model`；原始 HWID 最多 512 字符 | 正常返回原订阅；空或超长 HWID 为 `400`；`reject_new` 新设备超限为 `429` | 不带 `X-HWID` 的旧客户端保持原行为；不修改已导入配置 |
| `GET /{XRAY_SUBSCRIPTION_PATH}/{token}/{client_type}` | `client_type` 可为 `sing-box`、`clash-meta`、`clash`、`outline`、`v2ray`、`v2ray-json` | 与普通订阅共用登记逻辑 | 不能通过切换订阅格式绕过限制 |
| `GET /{XRAY_SUBSCRIPTION_PATH}/{token}/device-status` | 无请求体 | 返回限制、已登记数量、剩余数量和支持状态；不返回原始或哈希 HWID | 订阅 token 认证；只读，不新增公网端口 |

服务端按 `(user_id, SHA-256(HWID))` 去重，因此同一 HWID 更换公网 IP 不新增设备；同一公网 IP 下不同 HWID 分别计数。原始 HWID 不落库，OS/型号仅保存截断后的值。

### 数据库

迁移 `4a9d2e8b7c61_add_user_device_limit.py` 与 `6d7e8f9012ab_add_device_credentials.py` 新增用户字段、`user_devices` 表、设备凭据 JSON 和 PostgreSQL 枚举。删除用户会级联清理设备记录；撤销设备后可以重新登记。回滚前必须备份数据库，禁止删除数据卷。

## 历史片段 29

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 4. 已完成的本地证据

- `python -m compileall -q app`：通过。
- 完整后端测试：本轮 `pytest` 43 项通过；历史 `unittest discover` 22 项记录保留为旧阶段证据。
- 设备限制与设备凭据加载专项测试：通过；历史设备限制专项记录为 5 passed。
- 前端 TypeScript 检查和 `npm run build`：通过。
- Alembic：`6d7e8f9012ab` 为设备限制链最新 head。
- SQLite upgrade/downgrade：通过。
- `git diff --check`：通过。

以下仍未完成：PostgreSQL 真实迁移、Linux 隔离环境、并发锁验证、V2RayN/Clash/Hiddify/Shadowrocket 的真实 HWID 兼容矩阵和生产服务器验收。因此本次只标记为“测试版镜像已发布”，不能标记为稳定发布。此前 Actions run `36832627106` 因专项测试误用未声明的 pytest 而失败，run `36835708735` 又发现锁定 APScheduler 导入 `pkg_resources`、但新版 setuptools 已移除该模块，run `36836757035` 再发现测试导入数据库模型隐式调用 `/usr/local/bin/xray`；三轮失败及修复方式均保留在 `CHANGELOG.md`，避免只依赖本地环境或误把“代码已推送”当成“镜像已发布”。

## 历史片段 30

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 5. 本次成功构建与防复发证据

- Actions run：`36838046078`；源 commit：`071819b1d90ca5bcf9dac903d11748ac8080dec7`。
- `ghcr.io/kissow/marzban:latest` OCI index：`sha256:290994ba997ed3120e494814717520db6216d9b615df4b54bc6f8bf147771b07`。
- 架构清单：amd64 `sha256:e17e7dab19d8cf637e2586b65a913ec9c2c758708628be31115411dece67a7e7`；arm64 `sha256:49b1183f193113cdb6c0b5e4d8254b86bce6c0d56e261ec3fe0032fd423c5ff9`。两者 OCI revision 均为 `071819b1d90ca5bcf9dac903d11748ac8080dec7`。
- 成功步骤包括后端 `unittest`（22 tests，`OK`）、前端类型检查/构建、Xray 版本闸门、多架构 Docker 构建和 GHCR 发布。
- 固定防复发闸门：失败必须登记 run、步骤、根因、修复提交和复跑结果；新增测试必须使用 CI 实际命令；依赖必须在干净环境安装；测试导入不得隐式要求生产二进制；发布后必须核对 index/架构 digest 与 OCI revision，最后才允许进入服务器验收。

## 历史片段 31

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 6. 发布顺序

1. 先更新代码、接口文档、CHANGELOG、README/FORK_FEATURES 和本登记卡。
2. 执行后端测试、前端构建、迁移升级/回滚和 `git diff --check`。
3. 在功能分支提交并推送；CI 成功后核对源 commit、镜像 tag、index/架构 digest 和 OCI revision。
4. 仅在镜像证据齐全后进入隔离服务器，先备份数据库、`.env`、证书、Xray 配置和数据卷。
5. 已切换 Fork 的安装使用 `marzban update`；官方旧安装首次切换使用 `marzban adopt`；新服务器才使用 `install`。
6. 服务器验收用户、订阅、节点、证书、端口、日志和手机/桌面页面后，才允许把状态改为稳定发布。

不得使用 `docker compose down -v`，不得覆盖 `.env`，不得删除 `/var/lib/marzban*`，不得把未发布代码直接覆盖正式 `latest`。
