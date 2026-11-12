# 首次付款期内单条提前重置恢复（v2）

状态：本地实现与测试，未发布/部署。此接口只修复错误减少的已用计数，不充值、不清零、不延长时间。原 v1 合同不变；无新 UI，Node/scripts 无变化。

## 为什么独立版本

某些新用户创建时没有零重置日志，首次原生月重置后只有一条正数日志。v1 要求“初始零 + 正数”两条，必须继续拒绝该情况，不能补造零记录骗过校验。v2 只接受一条真实正数日志，同时要求外部付款期证据；不是放开任意历史恢复。

接口与精确请求字段见[机器合同](contracts/usage-continuity-v2.json)。实现使用已有 recovery 审计表，无新增数据库迁移。必须先部署含 v2 的主控再由网站 GET 探测 capability；旧版本没有接口，不能回退调用 v1 写入。

## 权限与用途

三条接口均为 sudo Bearer，响应禁止缓存：

- GET `/api/usage-continuity/v2/users/{username}/preview`
- POST `/api/usage-continuity/v2/users/{username}/repairs`
- GET `/api/usage-continuity/v2/repairs/{operation_id}`

GET 返回完整现存历史和面板结构资格；`eligible=true` **不等于付款合法性已验证**，同时返回 `requires_paid_period_evidence=true`、`eligibility_scope=panel_state_only`。`expected.initial_reset=null`，`latest_reset` 是唯一正数日志。必须原样持久化完整 expected；不可用前端裁剪显示结果重建 POST。

POST reason 固定 `restore_first_paid_period_reset`，额外携带 `paid_period_evidence`：`starts_at`、`ends_at`、`last_observed_at` 为六位微秒的 UTC Z 字符串，`last_observed_used_traffic` 为精确字节字符串。外部系统独立核验唯一 NEW 付款、初始零基线、正确账号身份及没有其他授权重置/赠额/迁移，持久化证据后计算 `evidence_sha256`。摘要仅作审计，主控不访问支付系统。

## 写入闸门

SQLite、active、有界未到期、正有限额度、month、无 next_plan/历史恢复；完整历史恰好一条正数，距创建至少30天，未到下次30天重置。付款期起点与创建相差不得超过5分钟（容差不是付款证明）；跨度必须大于30天且不超过32天，结束时间取整秒必须等于面板 expire；最后采样在付款起点与重置之间，重置和执行均必须在期末前；采样字节必须大于0且不大于该次重置量 B。

在写锁内重新检查所有条件，原子把 B 加到**当前**已用量，不用旧采样覆盖新流量。若恢复后达到/超过原额度，直接拒绝并且不改变状态，不通过抬高额度或延长时间规避。采集后续达到原上限仍由原配额任务处理。

主控保留额度、时间、身份、设备设置、原重置日志和 reset_at；累计流量不增加，不伪造按 Node 分布，不重启 Xray。恢复回执记录 v2 capability、reason、付款期声明和 before/after 数值。主控证据不能证明原重置是谁触发的。

## 幂等与恢复顺序

先持久化全局小写 UUID、原路径和完整请求。相同请求返回原回执；修改证据/expected/路径后复用 UUID 会拒绝。未知结果只查原回执，404 不证明没有在途提交；不能新 UUID 盲重试，也不能超时就开放后续付款/同步写入。

v2 GET receipt 拒绝将 v1 回执误标成 v2。原 v1 的读取仍会返回回执真实 capability，调用方须核对它。

恢复与[外部控制交接](EXTERNAL_SUBSCRIPTION_CONTROL.md)是两笔独立操作。不要先设 no_reset：它会改变快照并导致恢复不符合 month 条件。恢复确认后，网站先按回执核对账本，再按其受控流程完成 no_reset 交接；任何一步未知都要停下核对，不重新清零。若到期或用量增加导致拒绝，不能改状态、额度或期限强行通过。

## 发布与回退

本轮需要主控镜像发布并由用户升级后才可使用；Node 和部署脚本不需要修改。已有 Fork 仍按备份后 update 流程，不能重装/删卷。不得仅因安装 v2 就执行客户恢复。

恢复后不能回退到不认识 recovery ledger 的旧运行时；保留审计和数据库，沿用[部署与回退闸门](USAGE_CONTINUITY_DEPLOYMENT.md)。回退软件不撤销恢复，更不能删回执或还原旧数据库覆盖新用量。调用方继续需要支持已有 v2 回执。

测试及未验收项见[验证记录](releases/usage-continuity-v2-20261112.md)。
