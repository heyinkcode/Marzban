# 主面板 TCP 中转：历史发布记录

[当前说明](../NODE_RELAY.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261007-NODE-RELAY（镜像已发布，服务器待验收）

主服务器可选每 Node TCP 中转，首版仅 VLESS TCP/RAW REALITY、IPv4 入口。原直连条目、用户凭据、REALITY 参数、证书、Node 控制/API/倍率/住宅出口保留；Node/scripts 无本轮运行时或命令变化、不需服务器更新，Xray 固定 v26.3.27。新增四个 sudo API、node_relays additive 迁移 8f9012ab34cd、独立进程及失败恢复；running 仅代表本地监听就绪。

用户已授权先发布。源 134f12faf5e29e53986ff271a8c8f57b8a38db38，PR #16 合入 d23502030358930592016f9ff2f7d3f42acad4e7；PR CI 37637526876 成功（140 项普通后端 + 两项显式真实 Linux Xray、前端44/44、类型/生产构建），本地最终142/142及前端44/44复核通过。正式 Actions 37637973415 首次成功；latest index sha256:252adac60cdcbcc83a7ef13a080d52876876017a65220c58fcf76539db9ccd03 与 amd64/arm64 manifest/config/OCI revision 已核对（d23502030358930592016f9ff2f7d3f42acad4e7）。仅文档回写 [skip ci] 不改变该运行时版本。UI 截图受浏览器管理策略阻止，服务器、公网 REALITY/手机与实际提速仍待验收，不冒称稳定发布。 [设置、接口、限制、回滚与测速](../NODE_RELAY.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-07 — MR-20261007-NODE-RELAY（镜像已发布，服务器待验收）

- 原 Chakra Node 组件增加折叠连接方式、自动/手动入口端口与虚拟订阅，不替换原主题/字段。
- 主服务器可选每 Node TCP 中转，首版仅 VLESS TCP/RAW REALITY、IPv4 入口。原直连条目、用户凭据、REALITY 参数、证书、Node 控制/API/倍率/住宅出口保留；Node/scripts 无本轮运行时或命令变化、不需服务器更新，Xray 固定 v26.3.27。新增四个 sudo API、node_relays additive 迁移 8f9012ab34cd、独立进程及失败恢复；running 仅代表本地监听就绪。
- 新增配置/存储/权限/迁移/订阅/真实进程测试；修复实现中发现的循环导入、AST夹具、React Query回调类型、自动端口显示与IPv6入口监听不匹配。两条 CI 均增加显式固定 Xray Linux 进程验证。
- 用户已授权先发布。源 134f12faf5e29e53986ff271a8c8f57b8a38db38，PR #16 合入 d23502030358930592016f9ff2f7d3f42acad4e7；PR CI 37637526876 成功（140 项普通后端 + 两项显式真实 Linux Xray、前端44/44、类型/生产构建），本地最终142/142及前端44/44复核通过。正式 Actions 37637973415 首次成功；latest index sha256:252adac60cdcbcc83a7ef13a080d52876876017a65220c58fcf76539db9ccd03 与 amd64/arm64 manifest/config/OCI revision 已核对（d23502030358930592016f9ff2f7d3f42acad4e7）。仅文档回写 [skip ci] 不改变该运行时版本。UI 截图受浏览器管理策略阻止，服务器、公网 REALITY/手机与实际提速仍待验收，不冒称稳定发布。

[完整记录与测速](../NODE_RELAY.md)。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261007-NODE-RELAY（新增管理接口，镜像已发布）

新增 sudo Bearer 的 GET /api/nodes/relay/options 与 GET/PUT/DELETE /api/node/{node_id}/relay：direct/relay、source=main、entry_address、allocation=auto/manual、listen_port、inbound_tag；返回配置/目标/本地监听状态。401/403/404/422/409，数据库失败可500且先恢复运行时；无旧接口删除。主服务器可选每 Node TCP 中转，首版仅 VLESS TCP/RAW REALITY、IPv4 入口。原直连条目、用户凭据、REALITY 参数、证书、Node 控制/API/倍率/住宅出口保留；Node/scripts 无本轮运行时或命令变化、不需服务器更新，Xray 固定 v26.3.27。新增四个 sudo API、node_relays additive 迁移 8f9012ab34cd、独立进程及失败恢复；running 仅代表本地监听就绪。

用户已授权先发布。源 134f12faf5e29e53986ff271a8c8f57b8a38db38，PR #16 合入 d23502030358930592016f9ff2f7d3f42acad4e7；PR CI 37637526876 成功（140 项普通后端 + 两项显式真实 Linux Xray、前端44/44、类型/生产构建），本地最终142/142及前端44/44复核通过。正式 Actions 37637973415 首次成功；latest index sha256:252adac60cdcbcc83a7ef13a080d52876876017a65220c58fcf76539db9ccd03 与 amd64/arm64 manifest/config/OCI revision 已核对（d23502030358930592016f9ff2f7d3f42acad4e7）。仅文档回写 [skip ci] 不改变该运行时版本。UI 截图受浏览器管理策略阻止，服务器、公网 REALITY/手机与实际提速仍待验收，不冒称稳定发布。 [完整字段、认证、错误、副作用、兼容与回滚](../NODE_RELAY.md)。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261007-NODE-RELAY（镜像已发布，服务器待验收）

- [x] 原 Chakra 局部修改，证书/端口/倍率/主题/健康/出口保留；独立 TCP 中转与专用记录、订阅/原凭据保留。
- [x] 本地后端142/142多轮、前端44/44/类型/生产构建、迁移/API/回滚与固定入口检查。
- [x] 用户授权先发布；PR #16 合入 d2350203；Linux CI 37637526876，普通140项与两项真实固定Xray、前端44项通过。
- [x] 正式 Actions 37637973415 成功，latest index sha256:252adac60cdcbcc83a7ef13a080d52876876017a65220c58fcf76539db9ccd03、双架构 manifest/config/OCI revision d23502030358930592016f9ff2f7d3f42acad4e7已核对。
- [ ] 真实原组件截图：浏览器策略blocked，不登记为通过。
- [ ] 备份升级、Marzban主服务器/目标Node/第二Node出口、手机/订阅/用量及至少30分钟公网测速验收。

Node/scripts无变化、不需本轮更新；Xray v26.3.27。[完整发布/验收证据及测速](../NODE_RELAY.md)。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261007-NODE-RELAY（镜像已发布，服务器待验收）

开源文档统一使用“Marzban 主服务器中转到 Node 节点”，不将主服务器所在地区作为前提。配置、拓扑、示例、安装、测速和验收均以主服务器/目标Node说明；示例域名使用main.example.com等通用占位，不绑定特定维护者或国家/地区。

主服务器可选每 Node TCP 中转，首版仅 VLESS TCP/RAW REALITY、IPv4 入口。原直连条目、用户凭据、REALITY 参数、证书、Node 控制/API/倍率/住宅出口保留；Node/scripts 无本轮运行时或命令变化、不需服务器更新，Xray 固定 v26.3.27。新增四个 sudo API、node_relays additive 迁移 8f9012ab34cd、独立进程及失败恢复；running 仅代表本地监听就绪。 API/迁移/回滚/兼容和工作区05/08/09已登记。

用户已授权先发布。源 134f12faf5e29e53986ff271a8c8f57b8a38db38，PR #16 合入 d23502030358930592016f9ff2f7d3f42acad4e7；PR CI 37637526876 成功（140 项普通后端 + 两项显式真实 Linux Xray、前端44/44、类型/生产构建），本地最终142/142及前端44/44复核通过。正式 Actions 37637973415 首次成功；latest index sha256:252adac60cdcbcc83a7ef13a080d52876876017a65220c58fcf76539db9ccd03 与 amd64/arm64 manifest/config/OCI revision 已核对（d23502030358930592016f9ff2f7d3f42acad4e7）。仅文档回写 [skip ci] 不改变该运行时版本。UI 截图受浏览器管理策略阻止，服务器、公网 REALITY/手机与实际提速仍待验收，不冒称稳定发布。 [详细证据、服务器流程与测速](../NODE_RELAY.md)。
