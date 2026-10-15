# 节点重连与恢复：历史发布记录

[当前说明](../NODE_RECOVERY_RELEASE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261006-NODE-RECOVERY（镜像已发布，服务器验收待完成）

节点连接/重启/管理修改删除使用每节点生命周期锁；重复重连合并，自动失败恢复退避 30 秒，手动绕过退避。复用失效会话 transport，失败重启不无条件停远程核心；健康故障隔离，恢复时清旧状态。TLS 握手增加阶段超时并保留双向认证，错误写入原 message。全用户账号协调移出节点锁。

同一最终代码两轮 95/95 与 Linux CI、前端/依赖检查通过；UI、API/schema、用户数据、证书、端口、HWID/UDP 和 Xray v26.3.27 不变。Node/scripts 无运行时变化无需本轮更新。PR #10、源 `122632c8` 与 Actions `37340574125` 已完成；latest 双架构摘要和 OCI revision 已核对，服务器验收未执行。[发布证据和边界](../NODE_RECOVERY_RELEASE.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## MR-20261006-NODE-RECOVERY：节点卡住/恢复风险修复（镜像已发布，服务器验收待完成）

- 每 Node 连接/重启/修改/删除互斥，重复重连合并，自动退避与手动重试分开；失败不无条件 disconnect 停核心。
- 健康检查隔离异常并覆盖未创建 transport 的启用节点；健康恢复清旧状态，不反复写健康节点状态。全用户账号协调不占节点生命周期锁。
- 控制会话、TLS、配置、API readiness 等阶段错误使用原 message；REST/RPyC 取证书及 RPyC TCP/TLS 加阶段期限，保留 mTLS/证书校验与旧 Node 兼容，失败连接关闭。
- 最终代码两轮全量 95/95 通过；Python/TypeScript/Vite/pip/diff 检查通过。既有弃用和 chunk 告警单独保留。
- UI/API/schema/线协议、证书、端口、用户数据、HWID/UDP 及固定核心 v26.3.27 未改；Node/scripts 无需本轮更新。
- PR #10 已合并，源 `122632c8df4b57c43706cb59fb183e7386004ce1`；Actions `37340574125` 首次成功，Linux 95/95、前端生产构建与 Xray 版本闸门通过。latest index `sha256:ecbe03895e28c1dd7d9441907f967b1806f105e00e01d4dc36232bf7f39bb42b`，amd64/arm64 摘要与 OCI revision 已核对。Actions 上传证据为 `2026-10-05T16:33:03Z`（UTC）。
- 服务器部署与真实网络验收未执行；[日志证据、架构摘要、兼容边界和验收清单](../NODE_RECOVERY_RELEASE.md)。后续发布证据提交仅改文档，使用 `[skip ci]` 保留本轮已核对镜像，不把文档提交冒充镜像源提交。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261006-NODE-RECOVERY：既有接口行为（镜像已发布，服务器验收待完成）

`GET /api/nodes` 与 `GET /api/node/{node_id}` 原 status/message/xray_version 返回合同不变，message 增加内部失败阶段。`POST /api/node/{node_id}/reconnect` 原 sudo-admin 权限/响应不变：200 仅表示异步任务接受，进行中的重复重连可合并，不等于连接成功。`PUT`/`DELETE /api/node/{node_id}` 内部与恢复使用同一节点锁；请求、响应、权限不变。

Node REST/RPyC 方法、认证、字段及健康/设备策略线协议不变；没有新端口、数据库迁移、UI/HWID/UDP/核心变化。已配对 Node/scripts 无需本轮更新；主控镜像已发布：源 `122632c8`、Actions `37340574125`、双架构 OCI revision 核对通过。本地两轮 95/95 与 Linux 95/95 通过，服务器部署/验收未执行。[镜像摘要、完整超时、兼容和验收边界](../NODE_RECOVERY_RELEASE.md)。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261006-NODE-RECOVERY（镜像已发布，服务器验收待完成）

- [x] 生命周期/退避、健康隔离、阶段原因和 TLS 期限修复；原版组件与数据保留。
- [x] 最终同一运行时代码两轮全量 95/95；真实 TLS/mTLS/旧服务兼容、并发/管理路由、恢复与订阅/策略回归通过。
- [x] TypeScript/Vite、compileall、pip check、固定入口 Check/diff 检查通过；既有警告单独记录。
- [x] README/功能/变更/API/流程及工作区 05/08/09 登记；Node/scripts 无线协议或安装变化、不需本轮构建更新。
- [x] PR #10 合并为 `122632c8`；分支 Actions `37340492999` 与 master Actions `37340574125` 成功，Linux 全量 95/95；双架构镜像/OCI revision 核对通过。
- [ ] 主控更新、原版重连/自动恢复、故障 message、订阅/真实应用访问验收：未执行。

[本轮新摘要、发布证据与验收范围](../NODE_RECOVERY_RELEASE.md)。镜像已发布不代表服务器已更新；未执行镜像本地启动或生产网络故障注入验收。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261006-NODE-RECOVERY（镜像已发布，服务器验收待完成）

本轮只改主控恢复代码与测试/文档：每节点生命周期互斥、健康隔离、安全重试、TLS 阶段期限和原 message 原因。最终同代码两轮全量 95/95，前端构建及依赖/语法/diff 检查通过；Node/scripts 无运行时/协议/命令变化，无需本轮构建更新。

已完成 README、FORK_FEATURES、CHANGELOG、接口和发布清单，以及工作区 05/08/09。PR #10 已合入 master `122632c8`；分支 Actions `37340492999`、master Actions `37340574125` 均成功，Linux 95/95 与生产前端构建通过。新 latest index `sha256:ecbe03895e28c1dd7d9441907f967b1806f105e00e01d4dc36232bf7f39bb42b` 及两架构 OCI revision 已核对；服务器部署/验收未执行。证据回写为仅文档 `[skip ci]` 提交，不重建已核对镜像；下方历史记录不替代本轮证据。[本轮记录](../NODE_RECOVERY_RELEASE.md)。
