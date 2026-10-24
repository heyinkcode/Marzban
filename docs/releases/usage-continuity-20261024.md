# 用量连续性 v1 — 验证与发布记录（2026-10-24）

状态：正式发布候选，PR/Actions/镜像证据待回填，生产未修改。源基线 `aad87b9` 与先前 `94290ac7f2c7a15193fdfca04492d314e306f0c9` 文件树相同，运行时基线 `ac566ff59aa9d79438b56931feba785ad469b688`。

## 本次发布范围

仅主控后端、必要测试/发布检查和对应文档。Node/scripts/前端无运行时变化，Xray 仍固定 v26.3.27。API `usage-continuity-repair-v1` 的字段与语义保持不变。Docker 启动命令改为迁移成功才启动；CI 在推送正式镜像前构建 amd64 测试镜像，使用无网络容器和合成 SQLite 运行真实 Alembic CLI，并验证迁移失败退出。

正式范围不含本地 overlay 构建准备器及其 7 项 mock 测试；保留只读盘点 3 项、账目 41 项和新增发布 2 项，正式全量预期 272 项。最终数量以干净发布树/CI 回执为准。只读盘点用于人工核对，不自动修复账号。

## 已验证

- 专项最初 33/33；补齐 SQL 汇总/列表排序、配额审查、互斥负例、跨 owner 历史保护后，完整后端 267/267。
- 最终包含 41 项账目/API/迁移测试、7 项准备器命令边界和 3 项数据库只读盘点测试；全量连续两轮各 **277/277，无跳过**，21.177s / 21.365s。
- 实际文件 SQLite WAL、独立连接及线程并发；加量/恢复、同 UUID 重试、不同 UUID 冲突、陈旧 reset ORM、锁内 reset 重验、后续普通与 next_plan reset；回执与当前量同事务，失败整体回滚。
- Python 和 SQL lifetime 一致；原额度不变，订阅 download 更新；达到原额度后现有 reviewer 停用；恢复不调用 Xray。
- sudo ASGI 鉴权与 schema 校验通过；响应不返回代理凭据。schema additive upgrade、空表 downgrade 与存在回执时的降级阻止均验证。
- 既有固定 Xray v26.3.27 本地回归包含在全量运行中；原前端/Node/scripts 未改。
- 固定 PS7 / 项目 Python 3.12.14 / Git diff 检查通过。
- 跨运行时外部集成任务反馈：合成 SQLite 与外部测试数据库经 JSON 桥及普通采集流程通过；HTTP/身份验证/订阅签名在该桥测试为 mock，不算在线联调或生产证明。

## 发现与修正

新增发布测试最初发现 Windows Alembic locale 读取中文绝对路径失败，改用测试临时目录相对路径；完整历史 TLS 迁移的百年 OpenSSL 间隔在 Windows C long 溢出，因此本地先用未变旧表结构创建合成库再 stamp 旧 head，只验证此次真实升级/降级；Linux CI 与镜像内仍从空库执行完整历史链，不绕过旧迁移。新测试 fixture 修正历史日志表名后复跑。未为测试修改历史证书行为。

测试 fixture 初次缺 NodeUsage created_at，已补齐；异步循环在沙箱 socketpair 阻塞，获得本地回环测试权限后复跑，不是产品失败。账目测试发现删除后复用数字 ID 且模拟同 created_at 会误关联其他用户名，已把 id+username+created_at 同时纳入 Python/SQL/保护关系，保留失败用例后通过。UserResponse fixture 补合法代理。原迁移头断言更新为新头并验证完整前驱链。只读盘点显式 close SQLite 连接，避免 Windows 文件句柄残留。

## 历史准备包与当前交付边界

v2 ZIP SHA-256：`3ba81ad132387dce1e680d5e280923773cbef488f602fa6ed6d05cb990617767`。
10 个运行时文件 manifest SHA-256：`9ba2f3b358897d558fc8fd16ab207510f8e5d20d9dbd48e5b6d47a5e12faf49c`。

v1 保留不覆盖；v2 增加只读 DB 盘点，并将构建父镜像引用改为校验 ID 后生成的唯一 local base tag、构建前后复核 ID。v2 未改业务 payload。

以上为切换正式发布前的本地历史证据，v1/v2 准备包已不作为最终交付，不应部署。Docker CLI 在本地环境不可用，历史准备器 Docker 命令仅 mock 测试。新的 Linux 构建、容器迁移检查及 GHCR 发布以本页后续正式证据为准；生产数据库备份、更新及账号修复仍需单独授权和验收。

激活前必须拿到现场容器 image/revision、Compose 项目/文件/service、挂载和 SQLite/Alembic head；不得猜路径。完整[部署与回退闸门](../USAGE_CONTINUITY_DEPLOYMENT.md)和[API 合同](../contracts/usage-continuity-v1.json)。已有恢复记录禁止退回旧运行时或删除审计表。
