# 出口 UDP 与 DNS：历史发布记录

[当前说明](../NODE_EGRESS_UDP.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261003-EGRESS-UDP（镜像已发布，服务器验收待完成）

每个 Node 的住宅出口新增 UDP 处理；保留原主题、证书、端口及原表单宽度。`legacy` 保持原样，`proxy` 要求 SOCKS 供应商支持 UDP，`tcp_only` 默认 DNS 经住宅代理 TCP、其他默认 UDP 阻断。原显式路由优先，不新增直连降级；不是通用 UDP 转 TCP。主面板增加 `udp_mode` 和 additive 迁移；新模式要求配对 Node `managed-outbounds-udp-v1`。主面板/Node 都需配对更新，scripts 运行时无变化、配对文档已更新，核心仍 v26.3.27。测试与限制见 [功能合同](../NODE_EGRESS_UDP.md)；真实 UI/手机/供应商验收待完成，下方历史发布记录不包含本功能。

发布证据（配对源 SHA、Actions、两镜像 index/架构 digest/OCI revision、scripts 文档提交）见 [EGRESS_UDP_RELEASE.md](../EGRESS_UDP_RELEASE.md)。服务器未验收，不是稳定版。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## MR-20261003-EGRESS-UDP：每个 Node 独立 UDP 处理（镜像已发布，服务器验收待完成）

- 原 Chakra 住宅出口表单新增 UDP 处理：默认保持原样、SOCKS TCP/UDP、仅 TCP 兼容；桌面三排双列，手机单列，未修改证书、节点端口或原弹窗宽度。
- 既有 egress API 新增 `udp_mode`；新增仅添加字段的迁移 `7e8f9012ab34`，旧配置默认 legacy、密码加密与留空保留规则不变。
- 非 legacy 必须配对 Node 的 `managed-outbounds-udp-v1`，保存前及重连时检查。兼容模式 DNS 经住宅代理 TCP，其他默认 UDP 阻断；原显式路由保留，不保证任意 UDP 应用可用或全流量防泄漏。
- 主面板 54 项、Node 48 项本地测试通过；TS/Vite/真实原组件预览构建通过，截图审核、Linux/实际供应商/手机验收待完成。两个仓库已推送，Actions 成功，latest 镜像及 OCI revision 已核对；不复用下方历史 digest。
- 主面板和 Node 均有运行时变化，需配对更新；scripts 运行时无变化，配对文档已更新并通过 Actions 检查，Xray 保持 v26.3.27。合同与边界见 [NODE_EGRESS_UDP.md](../NODE_EGRESS_UDP.md)。

发布证据（配对源 SHA、Actions、两镜像 index/架构 digest/OCI revision、scripts 文档提交）见 [EGRESS_UDP_RELEASE.md](../EGRESS_UDP_RELEASE.md)。服务器未验收，不是稳定版。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261003-EGRESS-UDP：住宅出口合同扩展（镜像已发布，服务器验收待完成）

没有新增路径或认证：sudo 管理员的 `GET/PUT/DELETE /api/node/{node_id}/egress` 沿用原合同。PUT 新增 `udp_mode=legacy|proxy|tcp_only`（省略 legacy），GET 已配置时返回模式；密码仍不回显。HTTP+proxy 或非法模式 422；旧/离线/能力不足 Node 在保存前 409。非 legacy 需要 `managed-outbounds-v1` 和新增 `managed-outbounds-udp-v1`，重连时重复检查。成功写库只代表异步重启已排队，不代表供应商连通性通过。

认证 REST/RPyC 配置通道只添加可选 extension 字段；legacy 为兼容旧 Node 省略此字段。additive 迁移 `7e8f9012ab34` 只增加 `node_egress.udp_mode`，不改用户/节点/凭据。两运行时仓库需要配对发布，scripts/证书/端口/环境/数据卷/核心 v26.3.27 无变化。协议、DNS 替换和显式路由优先级、错误、弃用/回退及验收完整说明见 [NODE_EGRESS_UDP.md](../NODE_EGRESS_UDP.md)。当前配对 latest 已发布并核对源提交；真实服务器与供应商仍待验收。

发布证据（配对源 SHA、Actions、两镜像 index/架构 digest/OCI revision、scripts 文档提交）见 [EGRESS_UDP_RELEASE.md](../EGRESS_UDP_RELEASE.md)。服务器未验收，不是稳定版。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261003-EGRESS-UDP（镜像已发布，服务器验收待完成）

- [x] 原 Chakra 住宅出口表单增加 per-Node UDP 处理；保留原证书、节点端口、开关和宽度，手机单列。
- [x] 既有 egress API、能力标识、迁移 `7e8f9012ab34` 和密码保留合同已登记；旧数据 legacy，原用户/节点/凭据不删除。
- [x] 主面板 54 项、Node 48 项完整本地测试通过；固定 Xray v26.3.27，含 8 组解析和 4 项实际 DNS TCP 运行测试。
- [x] TypeScript、生产 Vite 和真实原组件预览构建通过；没有新增端口、证书或脚本变化。
- [x] README/FORK_FEATURES/CHANGELOG/API、Node 线协议与工作区 05/08/09 已同步；[边界与验收](../NODE_EGRESS_UDP.md)。
- [ ] 真实桌面/手机截图审核：浏览器本地安全策略校验未通过，不能标为 UI 已验收。
- [ ] Linux 主面板/Node 认证联调、实际供应商 TCP53、v2rayNG/Clash Meta 同节点对照与 UDP 支持供应商回归。
- [x] 已获准推送；配对提交、Actions 成功、两镜像 index/架构 digest/OCI revision 已登记。服务器验收仍待完成。

本功能镜像已发布，服务器验收待完成；下方历史验收不能代替本次 UDP 功能验收。需要配对更新 Node 和主面板，优先 Node；scripts 运行时无变化、配对文档已更新。非 DNS UDP 阻断目前由路由单元测试覆盖，不是所有真实应用已验证。

发布证据（配对源 SHA、Actions、两镜像 index/架构 digest/OCI revision、scripts 文档提交）见 [EGRESS_UDP_RELEASE.md](../EGRESS_UDP_RELEASE.md)。服务器未验收，不是稳定版。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261003-EGRESS-UDP：每 Node UDP 兼容（镜像已发布，服务器验收待完成）

主面板：原 Chakra 表单增加 UDP 处理；现有 egress GET/PUT 新增 `udp_mode`，additive 迁移 `7e8f9012ab34`，旧记录 legacy。Node：能力 `managed-outbounds-udp-v1`、配置通道字段和默认 DNS TCP/UDP 路由处理、原子校验。scripts：运行时无变化，配对文档已更新并通过 Actions 检查。证书、端口、环境、数据卷和核心 v26.3.27 保留。不改 HWID 策略。

54 项主面板/48 项 Node 本地测试、TS/Vite/原组件预览构建通过；4 个实际固定 Xray DNS TCP 测试和 8 组解析通过。桌面/手机 UI 截图受浏览器策略限制未验收；Linux 和实际供应商/手机应用尚待验收。**两仓库已推送、Actions 成功、latest 镜像及 OCI revision 已核对**，发布 SHA/Actions/digest 已登记；不复用下方历史证据。

新模式须先发布并更新配对 Node 再更新主面板；不能给生产提供尚未发布镜像的更新命令。旧模式不下发新字段，新模式保存和连接都检查能力。默认 DNS TCP 不等于任意 UDP 转 TCP；原显式路由优先、自定义 DNS 上游被替换的限制见 [NODE_EGRESS_UDP.md](../NODE_EGRESS_UDP.md)。

发布证据（配对源 SHA、Actions、两镜像 index/架构 digest/OCI revision、scripts 文档提交）见 [EGRESS_UDP_RELEASE.md](../EGRESS_UDP_RELEASE.md)。服务器未验收，不是稳定版。
