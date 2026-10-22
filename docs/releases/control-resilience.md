# 控制连接恢复：历史发布记录

[当前说明](../NODE_CONTROL_RESILIENCE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261006-CONTROL-RESILIENCE（镜像已发布，服务器验收待完成）

修复慢控制链路被当作会话失效的问题：保留 session、只对精确 Session mismatch 重新认证；只读请求有限重试，变更请求不立即重放；不确定健康异常退避而不盲目重启核心。并行健康探测、单快照/互斥批量账号同步及流量/日志异常隔离，防止故障扩散到健康节点。两轮 116/116、专项 20/20 与真实传输 13/13 各连续复跑三轮通过。API/数据/UI/证书/端口/HWID/Xray v26.3.27 不变，Node/scripts 不需本轮更新。[接口期限、边界、证据与验收](../NODE_CONTROL_RESILIENCE.md)。

PR #12 合入 `eb43761e`，正式 Actions `37486719383` 成功；GHCR latest index 与 amd64/arm64 OCI revision 已核对。已切换 Fork 的主控执行 `marzban update`；服务器部署与至少 30 分钟真实链路/客户端验收仍待用户执行。仅文档证据回写使用 `[skip ci]`，不改变已验证运行时镜像 revision。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-06 — MR-20261006-CONTROL-RESILIENCE（镜像已发布，服务器验收待完成）

- 证实 Node `/connect` 对已有会话有停核心副作用；修复主控短暂 ping 超时后的会话接管风险，不把网络波动当作 HWID 拒绝。
- TLS 证书阶段 15s；REST 默认连接/读取各 10s、确认只读请求最多两次；API 就绪 10s、健康统计 5s。期限不是全流程硬截止；变更请求不立即重放，认证/证书错误不绕过。
- API/控制不确定失败按原原因退避 30s，不盲目重启；已启动核心检查 API、已停止核心走 start，管理员明确配置重启保留。
- 健康探测并行；账号同步每批单快照、互斥/异常隔离；流量与日志入口隔离控制探测异常。复核发现并修正 logger 导入遗漏，补回归防复发。
- 最终相同运行时代码完整回归两轮 116/116；20 项韧性和 13 项真实 TLS/mTLS/恢复测试各再复跑三轮；compileall、pip check、Check/diff 通过。测试夹具适配失败已修正，不冒充生产失败或通过证据。
- API/schema/UI/证书/端口/数据/HWID/Xray 不变；Node/scripts 无运行时代码变化。本轮只需更新主控。
- 源 `d3d768d0`、PR #12、PR CI `37486329103`；合入 master `eb43761e`，正式 Actions `37486719383` 成功。latest index `sha256:569aa43f94fdfc7711a05c20c2e498c782ac625cd0e7e38b64503788ab1fbbcb`，两架构 manifest/config/revision 核对通过。服务器部署/验收待执行，后续仅文档 `[skip ci]` 不重建镜像。[完整证据与 SSH 命令](../NODE_CONTROL_RESILIENCE.md)。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261006-CONTROL-RESILIENCE（镜像已发布，服务器验收待完成）

不新增接口、字段、迁移或端口。原 `/api/nodes`、`/api/node/{node_id}` 的 status/message 和异步 `POST /api/node/{node_id}/reconnect` 合同保留，受理不等于连通；日志控制探测异常使用既有关闭码 4400。Node 认证通道不变：仅 `/`、`/ping`、`/health`、`/device-activity` 在网络异常后最多再读一次；改变状态的请求不立即重放。精确 403 Session mismatch 才清除 session。TLS 15s、REST 连接/读取各 10s、REST API 就绪 10s、健康统计 5s、失败退避 30s 均为阶段参数，非全流程硬期限。HWID/订阅合同和正式 Xray v26.3.27 不变。Node/scripts 无变化；新主控镜像已发布，既有 Fork 执行 `marzban update`。PR #12 / `eb43761e` / Actions `37486719383` 与双架构摘要已核对，服务器验收待执行。[完整接口合同、发布证据及上线验收](../NODE_CONTROL_RESILIENCE.md)。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261006-CONTROL-RESILIENCE（镜像已发布，服务器验收待完成）

- [x] 主控会话保留、只读有限重试、健康退避/并行、多用户同步和流量/日志隔离；无 UI/数据/端口/证书/HWID/Xray 修改。
- [x] 最终同一运行时代码完整回归两轮 116/116；20 项韧性及 13 项真实传输各再连续三轮；compileall、pip check、固定入口 Check/diff 通过。
- [x] README/FORK_FEATURES/CHANGELOG/接口/更新流程及工作区 05/08/09 更新，Node/scripts 明确无变化。
- [x] 用户授权后的推送、PR #12 合入 `eb43761e`；正式 Actions `37486719383` 成功，本轮新镜像 index/双架构 manifest/config/OCI revision 核对。
- [ ] 升级前备份、主控更新、本轮运行 revision 核对与至少 30 分钟真实网络/客户端验收。

已切换 Fork 的主控可用 `marzban update` 获取本修复；Node/scripts 不需本轮更新。镜像已发布不等于服务器已更新或链路稳定；证据回写为仅文档 `[skip ci]`，不改变已验证运行时 revision。[精确摘要、SSH 命令与验收标准](../NODE_CONTROL_RESILIENCE.md)。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261006-CONTROL-RESILIENCE（镜像已发布，服务器验收待完成）

本轮仅主控运行时代码：慢 TLS/控制链路容错、保留认证会话、只读有限重试、健康退避而不盲目重启、并行健康及单快照设备账号同步、流量/日志异常隔离。API/schema/UI/证书/端口/HWID/Xray 不变；Node/scripts 无运行时/协议/命令变化，不需本轮配对更新。两轮完整 116/116、20/20 韧性与 13/13 真实传输各再复跑三轮；固定入口、依赖和语法检查通过。PR #12 合入 `eb43761e`，正式 Actions `37486719383` 成功，本轮 latest index 与双架构 OCI revision 已核对；服务器状态仍待用户更新/验收，不能引用历史 digest 或把发布当作上线验收。证据回写仅文档 `[skip ci]`，不重建已验证镜像。具体合同/证据见 [本轮登记](../NODE_CONTROL_RESILIENCE.md)。
