# 单次月重置的用量连续性修复（v1）

无新增界面。发布版本、构建及镜像证据见[发布记录](releases/usage-continuity-20261024.md)；安装新版本不等于已执行生产修复。

本功能不是充值、清零、续期或通用月结规则。只有管理员已经独立核实：一次月重置扣走的流量仍属于同一份有效权益时，才可把该次重置量 B 加回当前用量。面板不能自行证明付款或补偿关系；原重置表也没有记录操作者/来源。

## 账目与隔离

`current' = 当前数据库 current + B`，不是覆盖为预览值。新增采集与恢复相加，不丢失两者之间的新流量。

`lifetime = current + 原重置日志合计 - 恢复记录合计`。恢复前后 lifetime 相等；未来普通重置把 current 记入新日志并归零，仍保持此公式。Python 属性、SQL hybrid 汇总和 API 使用同一修正；原订阅头 download 为修复后的 current，total 仍为原额度。

原日志的 id、时间与数值全部保留。额度、到期时间、状态、策略、设备限制、身份、代理、下一套餐和原月重置锚点均不改；不再次增加管理员、系统或 Node 流量，也不伪造已经丢失的按节点历史分布。恢复不调用 Xray、不重启节点；继续采集后达到原额度，仍由既有配额审查停用。

## 严格适用范围

- SQLite；其他数据库的写入/预览能力拒绝，不以 mock 宣称跨数据库并发可用。
- active、到期时间有效且未到期、正数有限额度、month 策略、没有 next_plan 和历史修复。
- 完整可用日志恰好两条：创建后 5 分钟内的一条初始零值，再一条至少相隔 30 天的非零重置；没有额外重置。下一次 30 天重置不能已经到期。
- 恢复后 current 必须严格低于额度；达到或超过额度直接拒绝，不做跨数据库/Xray的不可靠状态切换。
- 已停用、已到期、on_hold、limited、多次重置/续费、未知权益归属均不自动处理。

## 接口

固定合同见 [JSON](contracts/usage-continuity-v1.json)，所有接口要求原 sudo Bearer 认证，响应 no-store。bytes 为精确十进制字符串，不用浮点；UTC 时间保留微秒。

1. GET `/api/usage-continuity/v1/users/{username}/preview`：只读快照，完整可用历史、身份/配置摘要和拒绝原因。
2. POST `/api/usage-continuity/v1/users/{username}/repairs`：原样提交 expected、全局 UUID、固定 reason、外部证据摘要。
3. GET `/api/usage-continuity/v1/repairs/{operation_id}`：不可变原回执，不返回动态当前用量。

事务获得 SQLite writer lock 后重读所有条件。原子加 B 与持久化回执同事务提交。UUID+完全相同解析后的请求/path 可显式重发，只返回原回执；相同 UUID 不同内容拒绝。不同 UUID 不能再次恢复同一账号/日志。

断线后先查同一回执。404 只表示查询瞬间未找到，不能断言在途请求不会提交；外部系统必须保留冻结，仅可显式恢复同 UUID、同 path、同 payload。没有取消/tombstone 接口，不得生成新 UUID 绕过冲突。错误或身份漂移必须人工核对，不得自动更新 expected 后重试。

## 普通重置与历史保护

普通/下一套餐重置先锁定并刷新计数，避免旧 ORM 快照覆盖新采集；定时重置锁内重新检查策略、状态和锚点。修正了原重置代码中把 expired/disabled 误写为 `expired or disabled` 的判断。

对含恢复记录的账号，`/api/users/reset` 清空所有历史操作返回 409，并整体回滚；普通单用户重置仍支持。恢复记录不随账号删除而级联删除，旧回执可查；关联同时要求 id、username、created_at，以免数字 ID 复用影响新账号。用户名和创建时间按原 API 为不可修改身份，禁止直接 SQL 伪造同一身份。

## 迁移与兼容

新增迁移 `c345de67fa89` 接 `b234cd56ef78`，只增加独立表。无恢复记录时可正常 downgrade；有任何恢复记录时拒绝删除表。恢复后不能启动不理解减项的旧程序，否则 lifetime 会双计；不能用旧备份覆盖已有新流量来撤销操作。

仅修改主控后端；Node、scripts、前端、Xray 版本、证书、端口与共享配置不变。[部署与回退边界](USAGE_CONTINUITY_DEPLOYMENT.md)。本地验证不等于 Linux 镜像构建或生产验收。

[验证与发布记录](releases/usage-continuity-20261024.md)。
