# 活动统计与策略：历史发布记录

[当前说明](../NODE_ACTIVITY_AND_POLICY.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## 2026-10-02 发布状态

- 状态：镜像已发布，服务器验收待完成；本地测试和 GitHub Actions 已完成，不能写成“稳定发布”。
- 主面板 `a6efaa8eafd82c3f68d2ff29074cf9eeb1ec8ae0` / Actions `36975384550` / GHCR index `sha256:42af5defdd9f325b0244c4be182ae6f77513d1d4e2d3572ea009215508de8dae`。
- 配对 Node `d6f3bec204a75085939b5b4e25fa6502f5946ae5` / Actions `36975383911` / GHCR index `sha256:f2a9e93ca3168abb3559f3e48baa98d02e6377fb8d4a480407f447a97bbbf774`。
- 正式 Xray 基线为 `v26.3.27`；服务器更新前必须备份数据库、`.env`、证书、Xray 配置和数据卷。

本仓库由 Mr.shaw 基于 [Gozargah/Marzban](https://github.com/Gozargah/Marzban) 开发，供其他使用者按开源许可证使用。感谢原作者和贡献者；保留原有 Git 历史与 AGPL-3.0 许可证。本说明只记录本 Fork 的扩展，不把这些功能描述为上游官方功能。

开发参考原项目 `CONTRIBUTING.md`：后端继续使用 FastAPI、SQLAlchemy 和 Alembic，前端沿用 React/Chakra UI。`kissow/Marzban` 的 `master` 是唯一日常安装、升级和镜像发布源；临时开发分支合并后删除。原作者仓库只保留为历史基线、许可证及致谢来源，普通安装和升级流程不会自动读取其可执行内容。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-02 Node 活动与策略同步（镜像已发布，服务器验收待完成）

- 健康 API 保留并校验 Node 原生在线用户、旧核心近期流量、策略数量/revision/同步时间和执行范围；仅旧 Node 无活动合同才回退到主面板用量采样。
- 用户创建/修改/删除、Node 连接/重启/重连同步完整脱敏策略；60 秒任务自动补齐并重试。一个批次一次数据库读取，最多并发 10 个 Node，单节点失败不影响用户保存及其他节点。
- 修复真实 RPyC 联调发现的 `AsyncResult.wait(3)` 错误；使用 `set_expiry()` + `wait()`。修复 `dict(netref)` 导致的 ValueError，逐键复制远程字典。两项加入真实 RPyC 新/旧服务合同测试，覆盖健康/活动/策略方法。
- 原 Chakra 组件保留原宽度、证书、端口、使用系数和刷新，只增加在线用户口径和策略状态文案。桌面/手机截图验收受浏览器管理策略校验失败阻止，保留原组件预览供审阅，不计为视觉验收通过。
- 设备 API 的数值范围统一为 0–100000；本条是设备专属凭据实现之前的历史记录，当时没有数据库迁移或凭据替换，策略接收也尚未形成直接连接拦截。后续的“设备专属凭据与 Node 新连接拒绝”条目已补上 `6d7e8f9012ab_add_device_credentials.py` 和按已登记账号生成配置的执行链；阅读本文件时以最新条目为准。
- 本地使用隔离 Python 3.12 与仓库依赖复测；接口/升级/回退和测试说明见 [完整合同](../NODE_ACTIVITY_AND_POLICY.md)。本次已随上述配对 commit 推送并完成 Actions/GHCR 发布；服务器尚未更新或验收。

本文件仅记录本 Fork 相对 [Gozargah/Marzban](https://github.com/Gozargah/Marzban) 的改动。原作者、许可证和上游 Git 历史均保留；完整功能边界见 [FORK_FEATURES.md](../../FORK_FEATURES.md)。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 2026-10-02 本地接口增补（未发布）

`GET /api/node/{node_id}/health` 增加 Node 活动来源、scope、采样窗口和时间，以及策略数量、revision、同步时间、同步状态与 `direct_connection_enforced=true`。优先保留 Node 原生在线用户，旧 Node 才使用面板近期用量回退。

Node 内部新增 `POST /device-activity`、`POST /device-policies` 及对应 RPyC 方法；沿用 TLS 认证通道和现有端口。设备数量上限在创建/修改用户 API 统一校验为 0–100000。本轮没有新增数据库迁移；策略确认只表示接收，`reject_new` 仍在带 HWID 的订阅请求时执行。

完整请求/响应、403/422、原子替换、重试、兼容与回退见 [Node 活动统计与设备策略合同](../NODE_ACTIVITY_AND_POLICY.md)。

本文说明本 Fork 新增的用户级订阅设备登记限制、节点健康与每 Node 住宅代理功能。原版全部接口仍以代码和运行实例的 OpenAPI 为准；`.env` 变量不是 API，不应把内部 Node 通道暴露给第三方项目。没有填写住宅代理主机、端口等参数时，不会自动生成住宅 IP。

跨主面板、Node、脚本的更新登记必须同时填写仓库内的 [`docs/REPOSITORY_UPDATE_FLOW.md`](../REPOSITORY_UPDATE_FLOW.md)，并按本仓库的 [`RELEASE_CHECKLIST.md`](../../RELEASE_CHECKLIST.md) 逐项检查。本文是主面板接口字段的维护源；三仓库的可依赖接口、Node 通道和脚本命令索引也在上述文档中。任何接口、订阅响应、Node 通道或配置字段的变化，都必须在同一个变更中更新本文、总索引、对应 CHANGELOG、README/FORK_FEATURES 和验收清单。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261002-01 镜像发布核对（服务器验收待完成）

- [x] 新增 Node 活动/策略合同及真实 RPyC 新旧服务测试；主面板完整 43 项、Node 完整 39 项本地测试通过。
- [x] TypeScript 检查、Vite 本地生产构建通过；原主题、节点弹窗宽度、证书和表单控件保留。
- [x] 健康响应明确来源与执行范围；策略确认未宣称精确设备连接拦截。
- [ ] 原组件桌面/手机截图：浏览器管理策略检查失败，待服务器验收。
- [x] GitHub 推送、Actions 和镜像 digest 已核对；真实服务器验收尚未执行。

发布证据：主面板 commit `a6efaa8eafd82c3f68d2ff29074cf9eeb1ec8ae0`，Actions `36975384550`，GHCR index `sha256:42af5defdd9f325b0244c4be182ae6f77513d1d4e2d3572ea009215508de8dae`；配对 Node commit `d6f3bec204a75085939b5b4e25fa6502f5946ae5`，Actions `36975383911`，Node GHCR index `sha256:f2a9e93ca3168abb3559f3e48baa98d02e6377fb8d4a480407f447a97bbbf774`。两个仓库均固定 Xray `v26.3.27`。状态只能写“镜像已发布，服务器验收待完成”。

本清单适用于 `kissow/Marzban` 的每一次代码、接口、数据库、管理端 UI、配置、Xray 核心或文档更新。它必须和仓库内的 [`docs/REPOSITORY_UPDATE_FLOW.md`](../REPOSITORY_UPDATE_FLOW.md) 一起使用；工作区中的 05/06/08/09 项目资料仍可作为扩展记录，但仓库内文档是上传后可复核的最小完整记录。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## 2026-10-02 发布状态（镜像已发布，服务器验收待完成）

- 主面板 `master`：`a6efaa8eafd82c3f68d2ff29074cf9eeb1ec8ae0`；Actions `36975384550` 成功；GHCR index `sha256:42af5defdd9f325b0244c4be182ae6f77513d1d4e2d3572ea009215508de8dae`。
- 配对 Node `master`：`d6f3bec204a75085939b5b4e25fa6502f5946ae5`；Actions `36975383911` 成功；GHCR index `sha256:f2a9e93ca3168abb3559f3e48baa98d02e6377fb8d4a480407f447a97bbbf774`。
- 两仓库均固定 Xray `v26.3.27`；本地测试、迁移升级/回滚和镜像构建已完成，服务器尚未更新，因此不能标记为稳定发布。

## 历史片段 6

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261002-01：本地活动与策略同步，未发布

主面板工作基线 `654e6c3`（master），Node 工作基线 `140fecb`（feature/mrshaw-release）；均为本地未提交修改。scripts 运行时代码无变化，配对文档更新。

API 增加活动来源/scope/时间和策略数量/revision/同步时间/执行状态；Node 新增 REST/RPyC 活动与策略方法。设备凭据迁移为 `6d7e8f9012ab_add_device_credentials.py`，原证书、端口、配置目录、数据卷和核心 v26.3.27 保持原样。Node 内部启用 statsUserOnline；依赖新增 grpcio。完整合同见 [NODE_ACTIVITY_AND_POLICY.md](../NODE_ACTIVITY_AND_POLICY.md)。

真实 RPyC 的 wait 超时签名及远程字典转换错误已修复并加入合同测试；主面板定期清零流量会干扰增量估算，已优先使用核心在线用户 API，旧核心回退明确标为尽力统计。不得仅靠模拟结果认定协议可用。

页面使用原生产组件预览；浏览器管理策略校验失败导致本轮无法完成截图验收。代码与镜像已发布，但服务器验收仍待后续实际执行，不能标记为稳定发布。

本文把本 Fork 每次更新必须同步的流程、接口登记和本次变更证据放在仓库内，避免依赖工作区外的资料文件。它适用于 `kissow/Marzban`；如果一次变更同时涉及 `kissow/Marzban-node` 或 `kissow/Marzban-scripts`，三个仓库必须记录配对 commit 和兼容性。
