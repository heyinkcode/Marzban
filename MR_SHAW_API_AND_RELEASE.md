# 扩展接口索引

分发所有者迁为 heyinkcode，API/认证/端口合同无变化；[升级边界](docs/GITHUB_NAMESPACE_MIGRATION.md)。

本文只维护现行接口入口和副作用；完整字段、错误码、兼容条件见对应合同。历史 API 描述见[按功能归档](docs/releases/README.md)，不能当作现行合同。

## 认证与边界

`dedicated-node-access-v1`：管理员 GET `/api/dedicated-nodes`、GET用户授权、PUT/DELETE `/api/user/{username}/dedicated-nodes/{node_id}`、GET操作回执；普通管理员同时检查用户归属和Node委派。sudo-only模式/委派接口及完整字段、202待生效、幂等和网站示例见[专线合同](docs/DEDICATED_NODE_ACCESS.md)。功能镜像已发布；部署后先检查能力标识，旧版本没有这些接口，服务器验收范围见对应发布记录。

sudo-only `/api/usage-continuity/v1` 的 preview、repairs POST 与 receipt GET，见[严格合同](docs/contracts/usage-continuity-v1.json)及[账目说明](docs/USAGE_CONTINUITY.md)。不是通用充值/清零接口；先按[发布记录](docs/releases/usage-continuity-20261024.md)核对运行版本。

下表节点管理接口均在 `/api` 下，要求原超级管理员 Bearer Token。令牌沿用 `POST /api/admin/token`；不得公开管理员凭据、Node 会话或代理密码。全部原版接口以代码和运行实例 OpenAPI 为准。

环境变量不是 API，见[配置说明](docs/CONFIGURATION.md)。Node 内部 REST/RPyC 使用既有认证控制连接，不应暴露为公共监控服务，也不承载中转用户流量。

## 本机、Node 与出口

| 方法与路径（含 `/api` 前缀） | 作用与副作用 | 合同 |
| --- | --- | --- |
| GET、PUT `/node/main/usage` | 读取/保存本机使用系数，仅影响后续本机业务计费 | [范围、校验与迁移](docs/MAIN_USAGE_COEFFICIENT.md) |
| GET、PUT、DELETE `/node/main/egress` | 读取/应用/移除本机出口；仅重启本机业务核心，确认后提交 | [本机合同](docs/MAIN_EGRESS.md) |
| POST `/node/main/egress/test` | 从主面板本机检测草稿，不保存、不重启业务核心 | [本机检测](docs/MAIN_EGRESS.md) |
| GET `/node/settings` | 原节点证书设置；保留原证书流程 | [配置](docs/CONFIGURATION.md) |
| GET `/nodes`、GET `/node/{node_id}` | 读取节点及标识 | [节点路由源码](app/routers/node.py) |
| POST `/node`、PUT、DELETE `/node/{node_id}` | 原节点增删改；可触发相应生命周期操作 | [节点路由源码](app/routers/node.py) |
| GET `/node/{node_id}/health` | 资源、活动来源和策略快照，不重置计费统计 | [活动与策略](docs/NODE_ACTIVITY_AND_POLICY.md) |
| POST `/node/{node_id}/reconnect` | 原异步重连，响应不代表已完成握手 | [控制连接与恢复](docs/NODE_CONTROL_RESILIENCE.md) |
| GET `/node/{node_id}/egress` | 读取此 Node 的脱敏出口配置，不返回密码 | [出口字段和 UDP](docs/NODE_EGRESS_UDP.md) |
| PUT、DELETE `/node/{node_id}/egress` | 应用/移除出口；Node 重启与 API 确认后才提交保存值 | [安全应用及失败边界](docs/EGRESS_PROBE.md) |
| POST `/node/{node_id}/egress/test` | 检测当前草稿；不保存、不重启业务核心 | [请求、结果与错误码](docs/EGRESS_PROBE.md) |
| GET `/nodes/usage` | 原节点用量查询 | [节点路由源码](app/routers/node.py) |

出口协议为 `http` 或 `socks`；UDP 模式为 `legacy`、`proxy`、`tcp_only`，其中 proxy 仅 SOCKS5。检测限 5/10 秒阶段超时、1/3 轮、每个执行端一个任务、30 秒总上限。HTTP 200 仍需检查检测结果的 ok/steps；Node ACK 丢失时只能报告结果未确认，不保证运行状态已回滚。本机与 Node 使用不同配置表、检测进程和接口。

## 中转

| 方法与路径 | 用途 |
| --- | --- |
| GET `/api/nodes/relay/options` | 可选来源、Node 和目标业务入站 |
| GET、PUT、DELETE `/api/node/{node_id}/relay` | 读取/保存/清除此目标的中转方式 |

`source=main/node`，选择 Node 来源时填写 `source_node_id`。入口填写来源服务器直连地址，目标填写业务入站，不填 Node 控制/API 端口。监听成功不等于目标公网可用；只替换原订阅中精确匹配的实际端点，不追加 Relay 条目。[字段、ACK、错误码与回滚](docs/NODE_RELAY_SOURCES.md) · [订阅合同](docs/NODE_RELAY_SUBSCRIPTION.md)。

## 设备与订阅

既有用户创建/修改接口接受 `device_limit`、`device_limit_mode=hwid`、`device_limit_action=log_only/reject_new`。0 表示不限制登记数量。无 X-HWID 返回共享兼容订阅；携带 HWID 时登记并分配独立凭据，新 HWID 超限返回 429。共享配置可绕过登记限额；不能把策略 ACK 当作全部设备受限的证明。[字段和执行范围](docs/NODE_ACTIVITY_AND_POLICY.md)。

## Node 内部扩展

| REST POST / RPyC 方法 | 合同 |
| --- | --- |
| `/health` / `fetch_health()` | [健康与采样](docs/NODE_ACTIVITY_AND_POLICY.md) |
| `/device-activity` / `fetch_device_activity()` | [活动口径](docs/NODE_ACTIVITY_AND_POLICY.md) |
| `/device-policies` / `set_device_policies()` | [完整策略快照与认证](docs/NODE_ACTIVITY_AND_POLICY.md) |
| `/relays/status`、`/relays` / `fetch_relay_status()`、`set_relays()` | [来源能力、完整快照与 ACK](docs/NODE_RELAY_SOURCES.md) |
| `/egress/probe` / `probe_egress()` | [限时检测、敏感字段与能力](docs/EGRESS_PROBE.md) |

接口变更需要同步请求、响应、权限、错误、副作用、能力和旧版本行为。完整登记要求及发布步骤见[更新流程](docs/REPOSITORY_UPDATE_FLOW.md)；不要把每次测试日志复制到本索引。

UDP 模式的线协议解析兼容，不等于当前主控允许旧 Node 使用安全保存/移除；该流程还要求 managed-egress-probe-v1 及确认应用。中转订阅只替换实际端点，原名称和条目数量不变；详见上表对应合同。测试与旧发布证据已从现行指南分离，本索引不更改 API。
