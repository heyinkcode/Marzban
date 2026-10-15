# README 历史发布记录归档

2026-10-15 从产品首页迁入；保留历史发布、检测、镜像证据与维护流程，调整相对链接。下方未发布/current/latest为各日期原始快照，不代表当前版本。现行功能、发布与验收以[文档中心](README.md)、[更新记录](../CHANGELOG.md)和对应功能专页为准。

## English README release notes

## MR-20261015-EGRESS-PROBE（配对镜像已发布，服务器验收待完成）

发布前验证：主控完整190/190两轮，应用专项8/8再三轮；Node完整80/80两轮，出口/真实核心恢复专项21/21再三轮（含真实子进程、TCP/UDP报文及固定Xray进程，无跳过）；前端60/60、TypeScript/Vite生产构建、pip check和固定入口diff检查通过。原组件HTML已展示，浏览器截图与两台生产服务器验收未执行。真实恢复测试额外发现旧核心进程/日志管道未回收，已修复并复跑；Windows夹具单独补SystemRoot，不修改Linux生产环境。

原出口弹窗新增目标 Node 连接检测，解析/TCP/HTTP或SOCKS5认证/HTTPS出口/DNS与UDP分阶段报告，5/10秒阶段上限、1/3轮、单Node一次、30秒总上限。四语言、原主题/宽度/账号密码/UDP模式保留。只测当前草稿，不保存或重启业务核心；停止等待不取消Node已启动的限时任务。不是客户端或中转整链验收，也不是测速/业务Xray探测。

主控新增sudo POST /api/node/{node_id}/egress/test；既有PUT/DELETE出口接口改为Node重启/API确认后才提交，失败保留保存值，Node启动失败尝试恢复旧配置，ACK丢失明确未确认且不盲目重发。Node新增认证REST /egress/probe、RPyC probe_egress与managed-egress-probe-v1能力。修复密码首尾空格被Node裁剪的问题。两仓库需配对更新；scripts无运行时变化，Xray v26.3.27、数据库迁移/证书/端口/用户/.env/数据卷无变化。

[合同、错误码、摘要证据与升级验收](EGRESS_PROBE.md)。先更新使用出口检测的目标Node，再更新主控；scripts无运行时变化。

2026-10-15 发布证据：主控源789130c30a69a85708255154d0d4f6a24c573495，经PR #21合入258218c07c9f2e265e790764bd727e528dcb761d；Node源ce3bed0decccef70c70765f9f59936a8b6a78dc6，经PR #5合入168a9e63d7c5219dffafd5839876db30b57e3cd5。主控分支Actions38670782109、正式38671882097，Node PR38660291647/分支38660285441、正式38671875814均成功；两latest的index/双架构manifest/config摘要与OCI revision已核对。用户要求的额外一轮主控190/190、Node80/80、前端60/60、类型/生产构建/pip check也通过。仅文档[skip ci]回写不改变镜像运行时revision；服务器未更新/验收，不能据此宣称实际供应商或客户端已恢复。


## MR-20261008-MAIN-USAGE-COEFFICIENT（镜像已发布，服务器验收待完成）

原节点设置顶部新增独立「主面板（本机）」使用系数，默认1，范围大于0至1000、最多五位小数；只影响本机业务用户计费，不是网速倍率。已有用量不重算，Node系数/透明中转/实际网络统计保持原范围。四语言、原Chakra主题/宽度/证书/端口保留。新增sudo GET/PUT /api/node/main/usage，additive迁移a123bc45de67接9012ab34cd56；Node/scripts无本轮变化，不需更新，Xray v26.3.27不变。

[接口、取整/采集边界、兼容性与验收流程](MAIN_USAGE_COEFFICIENT.md)。本地后端两轮182/182，专项18/18再三轮；前端54/54（含实际组件四语言SSR）、类型/构建/依赖/diff通过。用户已认可HTML提案，自动浏览器视觉验收未执行。源6f65298e、PR #19合并为15a11e9d5bdf884fa860456e3a4ae0602d6783b1；PR CI 37777207870与正式Actions 37777455474成功。latest index sha256:ed5d2641733126431104155f62a447390767f524525e7303f5bfc46741cb5f35，双架构manifest/config/revision核对通过。Node/scripts无需本轮更新；已切换Fork的主控用marzban update，服务器验收未执行。文档[skip ci]回写不改变运行时revision。

## MR-20261008-NODE-RELAY-SOURCES（镜像已发布，服务器/视觉验收待完成）

连接方式采用原React/Chakra独立管理弹窗和原信息图标。可选择Marzban主服务器或另一台源Node中转到目标Node；保留原订阅别名、顺序、数量，只替换精确匹配的端点，不新增Relay。目标认证、设备凭据和出口不变。自转发/环路/占用/能力/精确ACK/失败回滚、来源隔离与恢复有回归测试。

管理API增加source/source_node_id/来源列表，additive迁移9012ab34cd56；Node新增managed-node-relay-v1、原认证REST/RPyC完整快照与独立转发进程。固定Xray26.3.27，原证书、控制/API端口、用户、.env与数据卷保留。首版VLESS TCP/RAW REALITY、IPv4/DNS-only入口、单跳选择，不是所有协议或任意UDP转发；每源512个配置不是吞吐承诺。

本地最终代码和独立发布副本再次复测：主控164/164、Node60/60（准备固定Xray，无跳过）、前端47/47、类型/生产构建、依赖/diff通过。干净Linux CI与两镜像双架构发布核对完成；真实跨服务器mTLS、公网吞吐、多引擎数据库、实际原组件UI截图仍待验收，不标稳定版。UI截图因浏览器策略blocked，未绕过。

主控revision 93bfbb5b17dd8ee731449976df1a4af4e0f57ca5，Actions37657985804；Node revision 7b45fc0dc3b4451045a06123b52ccdaaa5911b8d，Actions37657976968。scripts合并ed274ba82410f9e6f580cbec59b2a15a89ab81ea，Actions37657994843成功，脚本运行时不变。先在承担来源的Node运行marzban-node update，再在主控运行marzban update；仅作目标的既有配对Node不强制更新。新Node沿用仓库install，现在拉取新latest；旧机不重装、不删卷、不重复adopt。源业务入口TCP需放行，客户端刷新订阅。

[精确配对SHA、index/架构/config摘要、接口与SSH验收证据](https://github.com/kissow/Marzban/blob/master/docs/NODE_RELAY_SOURCES_RELEASE.md)。下方旧记录只描述各自日期的阶段，不代替本轮最新状态；文档[skip ci]提交不改变已核对的运行时镜像revision。

> **MR-20261007-RELAY-INTERNAL-SUBSCRIPTION (local fix; NOT published):** Keep original subscription aliases, order and entry count; switch only the matched Node address/port, never append `(Relay)`. Stored Hosts, credentials and forwarding runtime remain unchanged. Reject unmatched/ambiguous targets; preserve short IDs on the output copy. Backend 149/149 passed twice including pinned-Xray process tests; frontend 45/45, type/build, dependency and diff checks passed. Node/scripts need no update. Node-to-Node is a future extension, not supported in this release. [Contract and pending publication/acceptance](NODE_RELAY_SUBSCRIPTION.md).

> **MR-20261007-NODE-RELAY (image published; server/visual acceptance pending):** Optional per-Node main-server TCP relay for VLESS TCP/RAW REALITY, preserving direct entries and original credentials/certificates/Node controls. Additive migration and four sudo APIs; Node/scripts need no runtime update, Xray stays v26.3.27. PR #16 merged as d23502030358930592016f9ff2f7d3f42acad4e7; Actions 37637973415 succeeded including real pinned-Xray Linux forwarding/recovery. Backend regressions and frontend 44/44/type/build passed; latest amd64/arm64 manifests/configs/OCI revisions verified. Adopted main servers use marzban update, configure the relay, allow its business TCP port and refresh client subscriptions. UI screenshot review remains blocked by managed browser policy; public REALITY/client/speed acceptance pending. [Exact image evidence, setup, API, limitations, rollback and speed tests](NODE_RELAY.md). Documentation-only [skip ci] evidence commits do not replace the runtime image revision.

> **MR-20261007-BROWSER-TRANSLATION (image published; server acceptance pending):** The dashboard opts out of external browser translation; native en/zh/fa/ru language switching is preserved. Existing Hosts loading/empty text uses stable element wrappers to prevent translator-induced React `removeChild` failures. PR #14 merged as `96599563`; Actions `37494615636` succeeded (116 backend/40 frontend tests), and latest amd64/arm64 manifests/configs/OCI revisions were verified. Theme, form layout, protocols, API, data and Node/scripts are unchanged. Existing Fork installations use `marzban update` then reload the dashboard; paired Nodes need no update. [Exact image evidence, root cause, regression and acceptance boundaries](BROWSER_TRANSLATION.md). Documentation-only evidence commits do not replace this runtime image revision.

> **MR-20261006-CONTROL-RESILIENCE (image published; server acceptance pending):** Preserve authenticated Node sessions on transient timeouts, avoid blind core restarts, tolerate slow TLS/control stages, and isolate health/account/usage probes. Final backend suite passed twice (116/116 each); transport/resilience suites passed three further rounds (13/13 and 20/20 each). PR #12 merged as `eb43761e`; Actions `37486719383` succeeded, and both latest architecture digests/OCI revisions were verified. No new API/schema/UI/certificate/port/HWID/Xray/Node/scripts changes. Already adopted installations use `marzban update`; paired Nodes need no update for this fix. [Exact image digests, retry contracts, update commands and server acceptance](NODE_CONTROL_RESILIENCE.md). Publication is not proof of server deployment or stable public-network connectivity; older evidence below remains historical.

> **MR-DASHBOARD-I18N-MOBILE (image published; server/visual acceptance pending):** Complete shared labels, relative online/expiry times and calendars across en/fa/zh/ru. The original Hosts dialog remains 440px on desktop and fits the mobile viewport; long titles and help wrap. PR #11 merged as `56552130`; Actions `37353281396` succeeded, and both latest architecture digests/OCI revisions were verified. Locale regressions 34/34, backend regressions 95/95, TypeScript and production builds passed locally and in Linux CI. No API/schema/Node/scripts/Xray changes; paired Nodes need no update. Real mobile visual and server acceptance remain pending. [Exact image digests, scope and update instructions](DASHBOARD_I18N_MOBILE.md). The release summaries below are historical, not this latest image's source or digest.

> **Node recovery (image published; server acceptance pending):** Per-node lifecycle serialization, isolated health recovery, stage-specific errors, bounded TLS handshakes and safe retry handling address connection risks. Two complete 95/95 local runs and Linux CI passed. PR #10 merged as `122632c8`; Actions `37340574125` succeeded and both `ghcr.io/kissow/marzban:latest` architectures have the matching OCI revision. No UI/API/schema/Node wire-protocol/Xray changes; already paired Nodes and scripts need no update. [Verified image digests, scope, API semantics and server acceptance gates](NODE_RECOVERY_RELEASE.md). Server deployment and real-network acceptance have not been performed for this release.

> **Node connection / scheduler maintenance (2026-10-03, image published; server acceptance pending):** Establish the existing authenticated Node session before the non-legacy egress health check; preserve the failure reason. Pin APScheduler 3.11.3 without the deprecated pkg_resources import. Local/Linux CI 69/69 and dashboard checks passed; source `78e7b8e`, Actions `37135175798`, both latest architectures and OCI revisions verified. No API/schema/UI/certificate/port/HWID/Xray changes; already paired Nodes and scripts need no new update. [Compatibility, tests and release evidence](NODE_CONNECTION_RELEASE.md). The image records below describe earlier releases.

> **Historical release (2026-10-03, HWID compatibility):** Source commit `37bab0b113c44ccb2a9db6230ac982b7d2a889a1`, Actions `37090609233`, image index `sha256:c4bbe88b5b547bbdca3d6b8a4bf1e7c92aeb29ae50b36cd758b7c6eccae2edfc`. This is historical evidence, not the current latest digest.

> **Latest panel image (2026-10-03, MR-20261003-DONATION-LINK):** Donation menu now targets this Fork; source `e72943b6dad1abf6ccd58307cb1008bd6793d81f`, Actions `37123809995` succeeded, latest index `sha256:28ffe73996bd0078df894e0d56b0ec742087d678acebd8c8d34b646791f7eb6c`. Both architecture revisions verified. [Publication evidence and update instructions](DONATION_LINK_RELEASE.md). Node/scripts, API, database, certificates, ports and Xray v26.3.27 are unchanged. Server click acceptance remains pending. The following UDP record describes the preceding paired feature release, not the current panel digest.

> **Current release (2026-10-03, MR-20261003-EGRESS-UDP):** Paired panel/Node code and multiarchitecture latest images are published and OCI revisions verified. [Source SHAs, successful Actions and exact image digests](EGRESS_UDP_RELEASE.md). Server/provider/mobile/UI screenshot acceptance remains pending; this is not a stable-release claim. Legacy remains the default; nonlegacy requires the paired Node capability. Scripts runtime and pinned Xray v26.3.27 are unchanged. [Contract, DNS/routing limits and acceptance](NODE_EGRESS_UDP.md).

> **Mr.shaw community fork:** This repository preserves the upstream Marzban project and adds per-node health, one residential outbound per Node, and a user-level device-registration limit. Read [Fork features](../FORK_FEATURES.md), the [Changelog](../CHANGELOG.md), and the [API and release guide](../MR_SHAW_API_AND_RELEASE.md) to see what is implemented, how its interfaces work, and what remains in development. The current image is published, but server acceptance is still pending.

The 2026-10-02 paired Node online-user statistics, policy acknowledgement/status, and device credentials are documented in [Node activity and policy contracts](NODE_ACTIVITY_AND_POLICY.md). The 2026-10-03 compatibility fix is published in `latest` and awaits server acceptance: clients without `X-HWID` receive their original shared subscription, and the panel retains that shared account on the main core and Nodes. HWID-aware requests still register/reuse private credentials and reject excess new HWIDs with HTTP 429. **The shared compatibility path can bypass HWID limits; this is not a universal physical-device or online-device limit.** Node policy acknowledgements do not prove all clients are blocked. Node/scripts runtime, UI, database schema, certificates, ports and fixed Xray `v26.3.27` are unchanged; this panel-only fix does not require a Node update. Server acceptance must be repeated after publication.

For every code, API, configuration, UI, Xray-core, or documentation change, follow this repository's [`RELEASE_CHECKLIST.md`](../RELEASE_CHECKLIST.md) and [`docs/REPOSITORY_UPDATE_FLOW.md`](REPOSITORY_UPDATE_FLOW.md). A change is not considered released until the matching Node and scripts records, API/configuration notes, tests, GitHub Actions result, image digest, and server acceptance status are recorded. If this repository changes only the UI, the release record must explicitly say that API, database, Node channel, certificates, and ports are unchanged.

## 中文 README 发布记录

> **MR-DASHBOARD-I18N-MOBILE（镜像已发布，服务器/视觉验收待完成）：** 完善 en/fa/zh/ru 共用文案、在线/到期相对时间和日历语言。原设置入站桌面保持 440px，手机按视口收窄，长标题和帮助文字可换行。PR #11 合入 `56552130`，Actions `37353281396` 成功，latest 双架构摘要和 OCI revision 已核对。本地/Linux CI 语言 34/34、主控 95/95、TypeScript 与生产构建通过。API/数据库/Node/scripts/Xray 不变，已配对 Node 不需更新。真实手机视觉与服务器验收仍待完成。[新镜像摘要、范围和更新命令](DASHBOARD_I18N_MOBILE.md)。下方发布摘要为历史记录，不是本次 latest 的源提交或摘要。

> **节点连接恢复（镜像已发布，服务器验收待完成）：** 增加节点生命周期互斥、隔离健康恢复、阶段性失败原因、TLS 握手超时及安全重试。两轮本地全量 95/95 与 Linux CI 通过；PR #10 合入 `122632c8`，Actions `37340574125` 成功，`ghcr.io/kissow/marzban:latest` 双架构 OCI revision 已核对。UI/API/数据库/Node 线协议/Xray 不变，已配对 Node 和 scripts 无需本轮更新。[新镜像摘要、范围、接口含义及服务器验收闸门](NODE_RECOVERY_RELEASE.md)。本轮未执行服务器部署与真实网络验收。

> **节点初连/调度器维护（2026-10-03，镜像已发布，服务器验收待完成）：** 非 legacy 出口先建立已有认证会话，再检查健康并启动；保留具体错误原因。APScheduler 固定到 3.11.3，消除 pkg_resources 弃用依赖。本地/Linux CI 69/69、前端检查通过；源 `78e7b8e`、Actions `37135175798` 成功，双架构 latest 和 OCI revision 已核对。API/数据库/UI/证书/端口/HWID/Xray 不变，已配对 Node 与 scripts 本轮不需更新。[兼容、测试和发布证据](NODE_CONNECTION_RELEASE.md)。下方镜像记录属于此前发布。

> **Mr.shaw 开源二开版：** 保留原版 Marzban 功能，新增逐节点状态、每个 Node 独立的一条住宅 IP 出口和用户级设备登记限制。已实现内容、接口、测试证据与发布状态请看 [二开功能](../FORK_FEATURES.md)、[更新记录](../CHANGELOG.md)、[接口与发布规范](../MR_SHAW_API_AND_RELEASE.md) 和 [仓库更新流程](REPOSITORY_UPDATE_FLOW.md)。设备限制目前已完成本地测试，但仍未完成真实客户端、Linux/PostgreSQL 和生产验收，尚未作为正式版本发布。

2026-10-03 捐赠入口对应的新主面板镜像已经发布；Actions 37123809995 和两种架构的 OCI revision 均核对通过。已切换 Fork 的主面板使用 `marzban update`，Node 不需更新；[发布证据与更新说明](DONATION_LINK_RELEASE.md)。服务器更新后的点击验收待维护者确认。
