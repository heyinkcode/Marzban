# 主控用户时间与流量 · 发布记录（2026-11-27）

状态：源代码已合并，主控 amd64 / arm64 镜像已发布并核验。未代为升级生产实例，也没有因发布自动修改客户数据。

- [功能 PR #35](https://github.com/heyinkcode/Marzban/pull/35)；源提交 6f64a8db47391b131486ee19a8b4c2a9a06e75fc；运行时 revision 773dfecd9a87296327bb9058187abeefa91b7dfe。
- [分支检查](https://github.com/heyinkcode/Marzban/actions/runs/45970469456)、[PR 分支检查](https://github.com/heyinkcode/Marzban/actions/runs/45970498422)、[PR 镜像验证](https://github.com/heyinkcode/Marzban/actions/runs/45970498380)和[正式发布构建](https://github.com/heyinkcode/Marzban/actions/runs/45971546270)均通过。
- PR Linux 后端发现 368 项，常规阶段 11 项固定 Xray 条件跳过；真实固定 Xray 随后分别完成中转 2、本机出口 34、专线 4 项。前端 75 项以及类型和生产构建通过；隔离 amd64 容器验证完整历史迁移、回执保护和迁移失败时退出。arm64 验证制品和元数据，未执行实际服务器测试。
- 原面板原组件在桌面和 390 / 320 px 验证四种语言、浅深主题和操作流程。测试只使用合成数据。
- 映像标签 ghcr.io/heyinkcode/marzban:latest；匿名 GHCR 检查 11/27/2026 09:27:12；OCI index sha256:1af1c20c22ca839f7e2b3bdda8b79115759938b9373b2d34e0e698213e7d0645。

| 架构 | Manifest SHA-256 | Config / image ID SHA-256 |
| --- | --- | --- |
| linux/amd64 | sha256:31a8d140625a73c42e35bc705215f912226cf82d0be75530242d818b1baa236b | sha256:b3d778763952a201a9c9531b54d429a4dc7d6c3238eab3022f852e14eabb55bd |
| linux/arm64 | sha256:836277b4d470435638737a6c7dac8fed62f921855aea316c216475c66d3bca1a | sha256:6570888a6f1faf3de3c9e4b44a794a4e29cbf94e39a74c721a64a583ab40da2e |

本次只更新主控，保留 Node、脚本接口、固定 Xray v26.3.27、原 .env、证书及原数据卷。不要重装或删除数据卷。新增 Alembic 迁移 e567fa89bc01，已有回执时禁止降级删除。

已有标准 Fork 安装：先备份数据库和配置，在不依赖待升级代理的已验证 SSH 会话执行 sudo marzban update，再核对运行 revision 和迁移版本。只有确认新接口可用后，再按[面板说明](../NATIVE_USER_ENTITLEMENT.md)或[网站 API 指南](../WEBSITE_ENTITLEMENT_API.md)用测试账号验收。对真实账号的历史错误修复须单独核对，发布不自动执行。

以后仅回写文档时，GitHub master 的文档提交可能晚于 OCI revision；运行时按本页已验证的镜像构建核对。
