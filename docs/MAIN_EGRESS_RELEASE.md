# 本机独立出口检查与发布

变更 MR-20261015-MAIN-EGRESS。当前：功能已合并，Linux CI 及正式双架构镜像构建成功，GHCR 实际摘要和 revision 已核对；生产服务器验收待执行。设置及接口见[本机独立出口](MAIN_EGRESS.md)。

## 影响范围

| 仓库 | 运行时变化 |
| --- | --- |
| Marzban | 本机独立出口、限时检测、加密存储、生命周期应用/恢复、独立 UI 与追加迁移 |
| Marzban-Node | 无；原子节点组件、端口、证书及出口/中转配置不变 |
| Marzban-scripts | 无；沿用保留数据 update |

用户已确认原组件 HTML 方案，并要求子节点区域完全保留。测试对 NodesModal、NodeEgressCard、EgressProbe、NodeRelayCard、NodeHealthCard 的规范化原文件进行摘要核对；本机只增加独立组件和本机卡片入口。

## 本地验证

- 最终后端完整三轮，各 224/224，无跳过；包括固定 Xray v26.3.27 的本机真实代理转发、移除恢复、重启/健康恢复、端口占用回滚、API 就绪和进程/管道回收，以及原中转实测。
- 前端完整三轮，各 65/65；四语言、原组件 SSR、独立接口/缓存、敏感错误、原 Node 组件一致性。TypeScript、Vite 生产构建、pip check 和差异检查通过。
- 本机专项首次 31/31。后续完整回归发现旧迁移链测试写死上一 head；追加检查新 head b234cd56ef78 连至 a123bc45de67，原链不断，修正后完整重跑三轮，保留初次失败记录。
- 恢复配置采用最新数据库账号，避免使用旧启动快照丢失期间新增的共享/设备账号；预检失败不停止原核心，数据库失败及恢复失败分别报告。

以上为 Windows 本地隔离数据库、ASGI、回环网络与真实固定核心验证，不是公网供应商或生产服务器验收。原 datetime/Pydantic 弃用及 Vite 大分块警告仍保留。浏览器自动截图通道不可用；原组件 HTML 已由用户确认，未伪称完成自动视觉验收。

## Linux 和镜像门槛

两个工作流均增加固定 v26.3.27 的 test_main_egress 专项，普通 Python 阶段没有二进制而跳过的项目不能当作执行成功；随后显式二进制步骤必须全部执行。合并前核对 Linux 检查；正式发布后分别记录源/合并 SHA、Actions、双架构 index/manifest/config 摘要与 OCI revision。

## 2026-10-15 上传、构建与镜像核对

源提交 `d757a111bbb0c972ce55f2d3a7b4f91614742a03` 经 [PR #23](https://github.com/kissow/Marzban/pull/23) 合入 `620e8c66d487ffddaea0639010e7da356c367a00`。分支 [38757830161](https://github.com/kissow/Marzban/actions/runs/38757830161)、PR [38757967218](https://github.com/kissow/Marzban/actions/runs/38757967218) / [38757967478](https://github.com/kissow/Marzban/actions/runs/38757967478) 与正式 [38758495591](https://github.com/kissow/Marzban/actions/runs/38758495591) 均成功。

Linux 普通后端共 224 项，其中缺少二进制的 7 项明确跳过；后续固定 Xray v26.3.27 步骤实际执行原中转 2/2、本机出口 34/34，无跳过。前端 65/65，类型和生产构建通过。不能把前一步跳过项算作真实核心执行。

`ghcr.io/kissow/marzban:latest` 于 2026-10-15 23:25（Asia/Hong_Kong）完成原始字节核对：index 为 `sha256:cd3969cf8d7e37c44b2ee079390d729b3d08609af24582c3c184f8ca31b34903`；下列 manifest/config 哈希与声明一致，两个平台的 OCI revision 都是上述合并提交，检查前后 latest 未变化。

| 平台 | Manifest digest | Config digest |
| --- | --- | --- |
| linux/amd64 | sha256:677bfa01d722a2cc94a450b14d49161cbdf5aba1c04832f7cf6d0111a8e73647 | sha256:400704f202525dcff3640095cade8c8be1ddda65b762fa230338f0ca7a58dc8b |
| linux/arm64 | sha256:0f2f115f30a0487b143964e77872a87c7aad6f63561be85236a6190e8618c66d | sha256:83eb59ec31cf0939285705f7b21e1c860eb3e37c749d374e0848666c154683ce |

按维护者要求，功能代码先上传并完成构建及仓库镜像核对，随后才提交功能说明和文档整理；文档为 Markdown `[skip ci]`，不重新发布镜像、不改变运行时 revision。Node 与 scripts 本轮只有文档整理，无需为本机出口重建或更新其运行时。

GitHub Actions 提示现有 actions 的 Node.js 20 兼容迁移及 ubuntu-latest 即将变更；本次任务成功，这些提示仍需在后续工具链维护中单独处理，未在本轮改变动作版本或核心基线。

## 文档整理验证

正式镜像确认后，对三个仓库执行纯 Markdown 整理：功能目录、更新摘要、接口/协议和可复用检查模板分工明确；旧证据按功能归档并链接不可变源提交。逐段核对主控 113、Node 42、scripts 13 个原始章节均保留，373 个受影响本地链接有效，三仓库首页无差异。仅文档提交未改变业务代码、部署脚本或镜像。Node 文档修正共享兼容账号范围；脚本文档单独记录用户已确认的旧更新误报修复，不扩大为本机出口验收。

## 服务器验收

只更新主面板，保留原用户、数据、证书、端口、倍率与 Node 配置。核对备份、迁移、实际镜像和日志，再测试本机与原 Node 订阅、真实出口、DNS/UDP、中转、移除与重启。生产服务器验收待执行；不能因本地或镜像构建通过就称全部链路已恢复。
