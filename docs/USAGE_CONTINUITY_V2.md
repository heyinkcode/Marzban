# 首次付款期内单条提前重置恢复（v2）

状态：主控镜像已发布并核验，生产服务器升级和客户恢复待单独验收。此接口只修复错误减少的已用计数，不充值、不清零、不延长时间。原 v1 合同不变；无新 UI，Node/scripts 无变化。

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

### 已有标准 Fork 主控的升级

先确认本页[发布记录](releases/usage-continuity-v2-20261112.md)已列出成功的正式构建和镜像摘要。以下仅适用于已由配套脚本管理、使用 `ghcr.io/heyinkcode/marzban:latest` 的标准主控；固定 digest/tag、自定义 Compose 或容器名先单独核对，不能直接套用。

1. 使用不依赖本机 Marzban 代理的 SSH 或带外控制台，安排维护窗口。升级会暂时停止主控，不能让 SSH 本身走该主控代理。
2. 保存当前镜像 ID/revision、Compose、挂载和数据库版本；确认停写备份覆盖数据库（含 WAL 一致性）、`.env`、配置与证书，没有其他共享数据库写入者。
3. 执行既有 `sudo marzban update`。配套脚本先备份再升级，保存输出的备份路径；任何备份、拉取或启动错误均停止，不重装、不删卷、不盲目重试。成功后执行 `sudo marzban status`。
4. 对已核实名称的容器，用 `docker inspect` 核对 `.Image` 和 `org.opencontainers.image.revision`，与本次发布记录对应架构的 config/revision 比较，不把多架构 index 当作容器 image ID。
5. 只读盘点命令为 `docker exec -e PYTHONPATH=/code -w /code <已核实主控容器名> python -B tools/usage_continuity_db_inventory.py`。当前完整迁移链唯一 head 为 `d456ef78ab90`；本轮 v2 没有新增迁移，旧部署升级仍须通过此前既有迁移。
6. 使用现有 sudo Bearer 身份 GET v2 preview，核对 `capability=usage-continuity-repair-v2`，并验收面板、订阅、节点和原用量。该 GET 不恢复账号；`eligible=false` 是资格拒绝，不代表镜像未安装。

完成部署核验后，外部系统仍须完成付款证据核验、写入协调与原请求持久化。恢复与 no_reset 交接按上文分别执行，不能把容器 Up 或一次 preview 当作恢复成功。

恢复后不能回退到不认识 recovery ledger 的旧运行时；保留审计和数据库，沿用[部署与回退闸门](USAGE_CONTINUITY_DEPLOYMENT.md)。回退软件不撤销恢复，更不能删回执或还原旧数据库覆盖新用量。调用方继续需要支持已有 v2 回执。

测试及未验收项见[验证记录](releases/usage-continuity-v2-20261112.md)。
