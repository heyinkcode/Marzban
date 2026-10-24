# 用量连续性 v1 — 验证与发布记录（2026-10-24）

状态：主控代码已合并，正式双架构镜像已发布并核验；生产服务器未更新、账号修复未执行。源基线 `aad87b9` 与先前 `94290ac7f2c7a15193fdfca04492d314e306f0c9` 文件树相同，上一运行时基线 `ac566ff59aa9d79438b56931feba785ad469b688`。

## 正式发布证据

- 功能源 `c4e1809c4f16bdc3c932c7522e205351ec36110f`，含本地验证记录的 PR 源 `4259106cbe5bf98b6ddaf875ae075983c4d74a42`；远端完整 tree 与本地一致。
- [PR #28](https://github.com/heyinkcode/Marzban/pull/28) 合并为 `d4ccc9d573888a7f1d249f0bdaf14a9c0f5a6473`。
- [分支检查](https://github.com/heyinkcode/Marzban/actions/runs/40073010173)、[PR 分支检查](https://github.com/heyinkcode/Marzban/actions/runs/40073015436)、[PR 镜像演练](https://github.com/heyinkcode/Marzban/actions/runs/40073015463) 均成功后合并。
- [正式构建 40073602093](https://github.com/heyinkcode/Marzban/actions/runs/40073602093) 成功。普通 Linux 后端272项（无核心阶段7项跳过），随后真实固定核心补跑中转2/2、本机出口34/34；前端65/65、类型与生产构建通过。
- PR 和正式构建均在无网络 amd64 容器中通过真实 Xray 26.3.27 / Alembic 全历史空库至旧 head、合成旧用户与日志、新 head 升级、重复升级、空审计降级和有回执拒绝降级。确认既有数据快照不变。无效数据库路径下镜像默认 CMD 非零退出，没有启动应用。
- 2026-10-24 07:34 UTC 匿名核对注册表 index、两架构 manifest/config 的原始字节 SHA-256 和 OCI revision；前后 latest 一致，index 与正式构建输出完全相同。两架构 CMD 均为 `alembic upgrade head && exec python main.py`。arm64 已构建及制品核验，未在真实 arm64 生产机上运行验收。

镜像：`ghcr.io/heyinkcode/marzban:latest`（同时发布 `sha-d4ccc9d`）；不可变 index：

```text
sha256:cd44bdaef4887a4391cac19f1db4fff96e6558f6cb7f3cee3334a1b8710d5153
```

| 架构 | manifest SHA-256 | config / 本地 image ID SHA-256 |
| --- | --- | --- |
| linux/amd64 | `8c7c530fb9a63985a10f3efd40e09157a551ed60b4bbde1819bfeec06be0c139` | `1317d99a125f5f14a952e209e9a9767fb94d63b4f565c0d56b0a33ef5c360fd2` |
| linux/arm64 | `cac53e6649673ea627117f59a755988fa1e4cc7a5c565986a568c8d0676aa5e9` | `bfc23830959c9ba88361b03ef08077bc356d1209af9076609b273530b10ae061` |

两架构 revision 均为 `d4ccc9d573888a7f1d249f0bdaf14a9c0f5a6473`。后续纯文档提交不改变此运行时 revision，不重新构建业务镜像。CI 提示既有 Actions Node20 运行环境弃用及 ubuntu-latest 迁移，未导致此次检查失败；不把这些提示当作产品失败或已完成平台升级。

已有标准实例使用[正式升级步骤](../USAGE_CONTINUITY_DEPLOYMENT.md)，先确认当前部署、备份再拉取；迁移后唯一 head 预期 `c345de67fa89`。只更新主控，不要求更新 Node。镜像安装本身不恢复任何账号，实际修复仍需独立核实权益和明确授权。

## 本次发布范围

仅主控后端、必要测试/发布检查和对应文档。Node/scripts/前端无运行时变化，Xray 仍固定 v26.3.27。API `usage-continuity-repair-v1` 的字段与语义保持不变。Docker 启动命令改为迁移成功才启动；CI 在推送正式镜像前构建 amd64 测试镜像，使用无网络容器和合成 SQLite 运行真实 Alembic CLI，并验证迁移失败退出。

正式范围不含本地 overlay 构建准备器及其 7 项 mock 测试；保留只读盘点 3 项、账目 41 项和新增发布 2 项。从本地提交 c4e1809 的精确 Git archive 生成干净副本，完整后端连续两轮 **272/272，无跳过**（87.168s / 102.887s）；真实固定 Xray v26.3.27。160 个变更文档相对链接、Git diff、变更内容隐私扫描和完整树制品检查通过；首页/前端/依赖/基础 Xray 配置无改动。只读盘点用于人工核对，不自动修复账号。

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
