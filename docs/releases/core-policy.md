# Xray 核心基线：历史发布记录

[当前说明](../REPOSITORY_UPDATE_FLOW.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## Xray 核心版本与功能边界

仓库正式构建基线统一为 `v26.3.27`（稳定版）。主面板和 `Marzban-node` 的 Dockerfile、GitHub Actions 以及安装脚本都通过 `XRAY_CORE_VERSION` 固定到同一版本；不再使用会随时间漂移的 `latest` 核心。`v25.3.6` 和 `1.8.24` 只属于历史 UI 预览示例，不是可安装核心版本。

`v26.9.9` 当前是 Xray-core 的预发布版本，发布说明没有独立的稳定变更清单并指向后续预发布版本。因此它不能直接替换正式镜像的 `latest`，也不能因为核心版本号变大就直接在面板增加一批开关。核心支持某项协议，只表示 Xray 能解析该配置；要成为面板功能，必须同时具备：Marzban 配置模型、配置生成/订阅转换、Node 下发与重启预检、前端表单、客户端兼容性测试和回滚说明。

当前正式版只开放已在本仓库端到端验证过的功能：原有官方入站/订阅能力、REALITY/TLS/WS/gRPC/TCP 等现有配置，以及每个 Node 独立的住宅代理出站。Hysteria 2、Finalmask、XHTTP/3、ECH、WireGuard 等核心能力暂不自动显示为新面板选项；它们需要单独完成配置模型、订阅格式、Node 兼容和客户端测试后，才进入测试版，再决定是否纳入正式版。

如需验证 `v26.9.9`，只能生成独立测试标签（例如 `xray-26.9.9-test`），不覆盖 `latest`，并记录主面板、Node、Xray 配置预检、订阅客户端、回滚和数据卷检查结果。服务器上的 `core-update` 会修改外部 Xray 二进制，可能覆盖容器内版本；生产环境以仓库镜像固定版本为准，禁止把一次手动 `core-update` 当成仓库版本。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 正式版核心一致性闸门（2026-09-30，未发布）

- 构建完成后立即读取 Xray 二进制版本，并强制核对为 `v26.3.27`；下载脚本返回错误版本时镜像构建失败。
- GitHub Actions 增加正式版本锁定检查，避免主面板和 Node 的 `latest` 镜像意外混入其他核心。

## 历史片段 3

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## Xray 核心正式基线收口（2026-09-30，未发布）

- 主面板 Dockerfile、GitHub Actions 和安装脚本统一锁定 `XRAY_CORE_VERSION=v26.3.27`；不再从 Xray 的动态 `latest` 地址取核心。
- `core-update` 使用同一个仓库锁定版本，并修正完成提示，避免主面板显示为空版本或与镜像版本不一致。
- 保留显式版本参数作为隔离测试入口；正式镜像和生产更新不得使用 `v26.9.9` 等测试候选版本。
- 本次没有删除或迁移数据库、用户、证书、端口、`.env` 或 Docker 数据卷；镜像尚未由本地变更直接宣称发布。
