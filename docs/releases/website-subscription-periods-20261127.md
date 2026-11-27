# 订阅周期 API · 发布与验证（2026-11-27）

主控镜像已正式发布，amd64 与 arm64 的版本和摘要已核对。服务器更新、API 实例验收是独立步骤；本次发布不自动改写真实账号，也不自动接管旧账号的订阅周期。

- [PR #36](https://github.com/heyinkcode/Marzban/pull/36)：源码提交 `d769cdbe31add0b9822b6da6dc150b55d9f7dc8e`，镜像 OCI revision 为 `e5cbd93fef215162967b6dd41d39611cf342efe4`。
- [PR 分支检查](https://github.com/heyinkcode/Marzban/actions/runs/45997504952)、[PR Linux 构建验证](https://github.com/heyinkcode/Marzban/actions/runs/45997504697)、[正式镜像构建](https://github.com/heyinkcode/Marzban/actions/runs/46005594418) 均通过。
- Linux 后端发现 379 项，常规 368 项通过；固定 Xray 实测另跑中转 2 项、主控出口 34 项、专线 4 项。前端 76 项、类型与生产构建通过。隔离 amd64 容器已验证完整历史迁移、新的 Alembic head `f678ab90cd12`、非空期号表降级保护以及迁移失败时退出。
- 镜像：`ghcr.io/heyinkcode/marzban:latest`；GHCR 匿名核验时间 `2026-11-27T13:28:45Z`；OCI index `sha256:b7a0635a1e297053cac1f808c696a0367e87aab668dc76beb20592f14bd32638`。

| 架构 | Manifest SHA-256 | Config / image ID SHA-256 |
| --- | --- | --- |
| linux/amd64 | `sha256:d8396be6d1c6a190839d8fd77e0b8189b30d11478d9c58a7e2ec06993481ebd8` | `sha256:e7f7397cb2e89ce092e1b222968a59b1addedaa3fa2b3c6558c13c7c392e0b5f` |
| linux/arm64 | `sha256:4841b3fd6459f89eb4eec587299b6382a87e4298bc01ecb67839fffe38433e42` | `sha256:2e4c0182deb2380b9771452ff8ccc10dce30fae45bb3ecba5057369a57a4f069` |

本次仅升级主控，Node、安装脚本和 Xray 固定版本均无变化。已有标准 Fork 安装在不依赖待升级代理的 SSH 会话中执行 `sudo marzban update && sudo marzban status`；确认已生成升级前备份，再回读运行容器的 OCI revision 和 Alembic head。数据库迁移不接管已有账户。接入生产订单前，先按[订阅周期 API](../WEBSITE_SUBSCRIPTION_PERIODS.md)用测试账号核验能力和回执。

纯文档提交可能晚于 OCI revision。确认服务器实际版本应以运行容器标签、数据库版本与本页发布证据为准。
