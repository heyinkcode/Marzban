# 节点初连与调度器：历史发布记录

[当前说明](../NODE_CONNECTION_RELEASE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261003-SCHEDULER-DEPENDENCY：调度器依赖维护（镜像已发布，服务器验收待完成）

APScheduler 已从 `3.9.1.post1` 升级并锁定为 `3.11.3`，移除旧版本导入 `pkg_resources` 产生的弃用警告。调度器仍使用原有 BackgroundScheduler、UTC、interval、coalesce 和 max_instances 配置；不新增菜单、API、数据库字段、Node 通道、证书、端口或 Xray 功能。主控连接修复与本条一起验证，Node 运行时代码本轮无需更新。

本地/Linux CI 69/69 与前端构建通过；源 `78e7b8e`、Actions `37135175798` 成功，双架构 latest 与 OCI revision 已核对。服务器真实网络验收待完成。[发布证据和兼容边界](../NODE_CONNECTION_RELEASE.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## MR-20261003-SCHEDULER-DEPENDENCY：移除 APScheduler `pkg_resources` 弃用警告（2026-10-03）

- 将 `APScheduler` 从 `3.9.1.post1` 升级并锁定到 `3.11.3`。新版使用 `importlib.metadata`，不再导入已弃用的 `pkg_resources`；不是屏蔽警告。
- 移除 requirements 中的 `setuptools<81` 兼容上限和 Docker 中为旧调度器单独安装 setuptools 的步骤。调度器仍使用原有 BackgroundScheduler、UTC、interval、coalesce 和 max_instances 设置。
- 已验证调度器启动/关闭、UTC 任务注册和项目完整 `unittest discover`（新增 6 项后 69/69）通过；TypeScript/Vite、pip check 和 diff 检查通过。其余 SQLAlchemy/Pydantic 的弃用提示属于独立后续依赖迁移，不影响本次通过结果。
- 主控连接修复同时保留：首次连接先建立 Node 会话，再执行健康检查和启动；失败原因写入节点状态。数据库、用户数据、API 路径、Node 运行时代码、证书、端口和 Xray `v26.3.27` 不变；本轮 Node 无需更新。
- 已发布主控镜像：源 `78e7b8e`、Actions `37135175798` 首次成功，latest index `sha256:9d3b20eba4e19994df9f5170f8ef3a5eaa81c3f846ab12e5f486f2c287bc2880`；两架构 OCI revision 匹配，服务器更新与验收待完成。
- 根因、现有接口执行顺序、跨仓库兼容、依赖升级、测试与发布证据统一见 [NODE_CONNECTION_RELEASE.md](../NODE_CONNECTION_RELEASE.md)。历史 setuptools 锁定记录保留作排障历史，不代表当前依赖。

## 历史片段 3

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 测试中：节点连接原因与重连入口、近期活跃用户统计（2026-10-01，未发布）

- 节点弹窗在标题栏下方、证书区上方显示连接失败/连接中/已停用的原因；优先展示后端 `node.message`，为空时使用状态兜底文案。
- `connecting` 和 `error` 状态提供“重新连接”按钮，继续调用原有 `POST /api/node/{node_id}/reconnect`；`disabled` 仅展示停用原因。官方 Chakra UI 结构、证书、端口、启用、保存、删除和原节点字段保持不变。
- 节点健康接口的 `active_users` 由主面板在有 `NodeUserUsage` 小时采样时补充为最近 2 小时有正流量的去重用户；无采样为 `null`，有采样但无符合条件用户为 `0`，不是 Xray 实时在线连接数。
- 本轮仅修改主面板 UI、健康统计及文档；Marzban-Node、脚本、Xray `v26.3.27`、证书、端口、支付和住宅出口通道无代码变化。前端 `tsc --noEmit` 与 `npm run build` 已通过；Python 语法检查和 Node 健康专项测试已通过，设备专项仍受本机依赖环境限制，未发布、未构建镜像、未提供服务器更新命令。

## 历史片段 4

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261003-NODE-CONNECT / SCHEDULER-DEPENDENCY 接口登记

本轮不新增或修改公开 API 路径、权限、请求/响应字段和数据库 schema。
既有 `POST /api/node/{node_id}/reconnect` 仍异步执行；主控先建立 Node 认证会话，
再执行非 legacy 出口健康/能力检查和启动；失败原因仍使用节点原有 `message`。
Node REST/RPyC 线协议不变，已配对 Node/scripts 不需本轮更新，Xray v26.3.27 不变。
APScheduler 锁定 3.11.3；仅主控依赖变化。[合同、测试和发布记录](../NODE_CONNECTION_RELEASE.md)。

## 历史片段 5

原位置：[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261003-SCHEDULER-DEPENDENCY（镜像已发布，服务器验收待完成）

- [x] APScheduler `3.11.3` 已替换旧 `3.9.1.post1`；不再依赖 `pkg_resources`，Docker 不再锁定旧 setuptools。
- [x] 调度器 API、UTC 任务注册/退出和主控完整 unittest `69/69` 通过，含 6 项调度器回归。
- [x] TypeScript/Vite 生产构建、pip check 与 git diff 检查通过；既有 chunk 和其他弃用提示单独登记。
- [x] 主控连接修复已加入回归测试：先 connect，再 health/start；失败原因保留。
- [x] API、数据库、Node 运行时代码、证书、端口、用户数据和 Xray `v26.3.27` 无变化；Node/scripts 无需更新。
- [x] 源 `78e7b8e` 已推送；Actions `37135175798` 首次成功，干净 Linux 后端 69/69 与前端检查通过。
- [x] 本轮 GHCR latest index/amd64/arm64 digest 与两架构 OCI revision 已核对，见 [发布证据](../NODE_CONNECTION_RELEASE.md)。
- [ ] 主控服务器更新后检查节点初连、原版重新连接、订阅和应用访问；未远程执行更新或验收。已配对 Node 不需再次更新。

发布状态只能在 Actions 和镜像证据核对后更新；本地测试通过不等于线上镜像已发布。

## 历史片段 6

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261003-SCHEDULER-DEPENDENCY：调度器与 Node 初连修复（2026-10-03，镜像已发布，服务器验收待完成）

- 根因：`connect_node()` 在未建立 Node 会话时先调用健康检查，非 legacy 出口首次连接会得到 `Node is not connected`。
- 修复：先调用既有 `node.connect()`，再执行健康/能力检查和 `start()`；异常原因写入节点状态，供原版重连按钮排障。Node 运行时代码不变。
- 依赖：主控 APScheduler 升至 `3.11.3`，移除 `pkg_resources` 弃用路径；调度器 API、UTC 和任务参数保持原样。主控完整测试 69/69、TypeScript/Vite、pip check、diff 检查通过。
- 边界：API、数据库、证书、端口、用户数据、订阅协议和 Xray `v26.3.27` 不变；Node/scripts 本轮无需更新。新提交、Actions、镜像和服务器验收必须单独记录。
- 发布：源 `78e7b8e`、Actions `37135175798` 首次成功，latest index 与两架构 OCI revision 已核对；具体摘要见 [发布证据](../NODE_CONNECTION_RELEASE.md)。服务器更新/真实网络验收未执行，不能把镜像发布当作服务器验收。
