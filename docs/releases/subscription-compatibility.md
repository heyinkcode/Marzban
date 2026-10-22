# 普通订阅与 HWID 兼容：历史发布记录

[当前说明](../NODE_ACTIVITY_AND_POLICY.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## 2026-10-03 订阅兼容修复（镜像已发布，服务器验收待完成）

`reject_new` 不再拒绝不带 `X-HWID` 的普通客户端：返回原共享凭据，主核心与 Node 保留该共享账号。带 HWID 的请求仍按登记额度生成/复用独立凭据，超额的新 HWID 返回 `429`；0 表示不限制登记。无 HWID 的兼容路径不能强制限制设备，也能绕过 HWID 限额。Node ACK 不证明全部客户端被拦截。本轮只改主面板订阅和账号加载/同步，Node 与安装脚本运行时无变化、不需更新；原 UI、数据、证书、端口、环境文件及核心 `v26.3.27` 保留。服务器验收待重新完成，发布证据见发布清单。

发布证据：主面板源 commit `37bab0b113c44ccb2a9db6230ac982b7d2a889a1` / Actions `37090609233` / GHCR `latest` index `sha256:c4bbe88b5b547bbdca3d6b8a4bf1e7c92aeb29ae50b36cd758b7c6eccae2edfc`；配对 Node 源 commit `c135743d1ad26d45538e4c6c7a65a9c6693856a8` / Actions `37090612247` / GHCR `latest` index `sha256:21340918298f0b8647fb7eb360294334891fc219e280a75af5d133c66ee9fbc1`。

## 历史片段 2

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 2026-10-03 订阅兼容合同（镜像已发布，服务器验收待完成）

沿用订阅 token 认证、原路径和参数，没有新增接口或迁移：

| 方法和路径 | 输入与结果 | 副作用和限制 |
| --- | --- | --- |
| `GET /{XRAY_SUBSCRIPTION_PATH}/{token}` | 无 `X-HWID`：正常订阅为 `200`，使用原共享凭据，不再因 `reject_new` 返回 `428` | 不新增设备记录；共享账号保留，无法强制执行 HWID 限额 |
| `GET /{XRAY_SUBSCRIPTION_PATH}/{token}/{client_type}` | sing-box/clash-meta/clash/outline/v2ray/v2ray-json 共用同一兼容逻辑 | User-Agent 自动识别路径同样兼容，原格式生成器未改 |
| 上述两个订阅路由，携带 `X-HWID` | `reject_new` 登记成功返回独立凭据；同 HWID 重用；新 HWID 超额 `429`；无有效登记凭据 `403`；空/过长 HWID 仍为 `400` | 0 不限制数量；成功登记后经现有通道同步共享与独立账号到主核心和在线 Node |

原鉴权、账号状态、到期与 token 错误行为保持不变；上表的 200 以原订阅有效为前提。无 HWID 或共享配置复制可以绕过 HWID 限额，因此不宣称全客户端或物理设备强制限制。`policy_enforcement` / `direct_connection_enforced` 原 ACK 字段不变，只表示合同/独立凭据支持，不证明所有客户端已被拦截。Node/scripts 运行时、UI、数据库 schema、证书、端口和 Xray `v26.3.27` 无变化；无需 Node 更新。回退使用更新前保存的镜像与配置；回退会重新带回旧版无 HWID 的订阅问题，不删除设备记录或数据卷。发布与服务器验收状态见发布清单。

发布证据：主面板源 commit `37bab0b113c44ccb2a9db6230ac982b7d2a889a1` / Actions `37090609233` / GHCR `latest` index `sha256:c4bbe88b5b547bbdca3d6b8a4bf1e7c92aeb29ae50b36cd758b7c6eccae2edfc`；配对 Node 源 commit `c135743d1ad26d45538e4c6c7a65a9c6693856a8` / Actions `37090612247` / GHCR `latest` index `sha256:21340918298f0b8647fb7eb360294334891fc219e280a75af5d133c66ee9fbc1`。镜像已经发布，服务器验收仍待完成。

## 历史片段 3

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261003-HWID-COMPAT（镜像已发布，服务器验收待完成）

- [x] 修复无 HWID 订阅 428；共享账号与独立账号共同加载、同步到主核心和在线 Node。
- [x] 文档说明无 HWID 兼容路径可绕过限额；HWID 登记不等于物理设备数，ACK 不证明所有客户端被拦截。
- [x] 完整后端测试 49 项、TypeScript/Vite、compileall 与 diff 检查通过；Vite 仅保留既有大 bundle 警告。
- [x] 仓库提交、GitHub Actions、GHCR index/架构 digest 和 OCI revision 已核对。
- [ ] 服务器更新后验证普通客户端导入、真实主核心/Node 连接，以及 HWID 登记/重复/超额拒绝。
- [x] 无新 UI、数据库迁移、Node 通道、脚本、证书、端口、环境文件或核心版本变化；Node 不需更新，核心仍 v26.3.27。

本轮代码和镜像已经发布；先前用户验收后又报告订阅失败，服务器必须按下方验收项重新验证，不能直接标为稳定发布。

发布证据：主面板源 commit `37bab0b113c44ccb2a9db6230ac982b7d2a889a1`，Actions `37090609233`，GHCR `latest` index `sha256:c4bbe88b5b547bbdca3d6b8a4bf1e7c92aeb29ae50b36cd758b7c6eccae2edfc`；配对 Node 源 commit `c135743d1ad26d45538e4c6c7a65a9c6693856a8`，Actions `37090612247`，GHCR `latest` index `sha256:21340918298f0b8647fb7eb360294334891fc219e280a75af5d133c66ee9fbc1`。Node 本轮无运行时代码变化，不需要更新 Node 服务器；两个仓库正式 Xray 均为 `v26.3.27`。

## 历史片段 4

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261003-HWID-COMPAT：订阅兼容修复（镜像已发布，服务器验收待完成）

根因：`reject_new` 对无 HWID 客户端返回 428，同时核心移除了共享账号；不仅不能导入，只修改 428 也不能恢复连接。修复同时覆盖真实订阅路由、初始配置和主核心/Node 增量账号同步。无 HWID 返回共享订阅，HWID 成功登记使用独立凭据，超额新 HWID 429，0 不限制登记。共享兼容路径可绕过限额，不保证物理设备数量；ACK 不是全客户端拦截证明。

主面板：代码及接口文档变化；Node：仅配对文档，运行时代码无变化，不需重新构建或服务器更新；scripts：无变化。没有新增数据库迁移、端口、认证通道或配置参数；UI、证书、环境文件、用户数据、数据卷及固定核心 v26.3.27 保持原样。后端/前端/差异检查、Git push、Actions、GHCR digest 已完成；服务器验收仍待执行，此前服务器通过记录不能代替这次回归验收。

发布证据：主面板源 commit `37bab0b113c44ccb2a9db6230ac982b7d2a889a1` / Actions `37090609233` / GHCR `latest` index `sha256:c4bbe88b5b547bbdca3d6b8a4bf1e7c92aeb29ae50b36cd758b7c6eccae2edfc`；配对 Node 源 commit `c135743d1ad26d45538e4c6c7a65a9c6693856a8` / Actions `37090612247` / GHCR `latest` index `sha256:21340918298f0b8647fb7eb360294334891fc219e280a75af5d133c66ee9fbc1`。Node 本轮无运行时代码变化。

原 2026-10-02 发布记录保留为历史证据；后续以本条及发布清单为最新状态。旧无 HWID 428 / 仅私有账号行为已废弃。API 详情见 [接口文档](../../MR_SHAW_API_AND_RELEASE.md)。
