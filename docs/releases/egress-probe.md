# 出口连接检测与安全应用：历史发布记录

[当前说明](../EGRESS_PROBE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)、[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)、[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)、[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)、[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261015-EGRESS-PROBE（配对镜像已发布，服务器验收待完成）

发布前验证：主控完整190/190两轮，应用专项8/8再三轮；Node完整80/80两轮，出口/真实核心恢复专项21/21再三轮（含真实子进程、TCP/UDP报文及固定Xray进程，无跳过）；前端60/60、TypeScript/Vite生产构建、pip check和固定入口diff检查通过。原组件HTML已展示，浏览器截图与两台生产服务器验收未执行。真实恢复测试额外发现旧核心进程/日志管道未回收，已修复并复跑；Windows夹具单独补SystemRoot，不修改Linux生产环境。

原出口弹窗新增目标 Node 连接检测，解析/TCP/HTTP或SOCKS5认证/HTTPS出口/DNS与UDP分阶段报告，5/10秒阶段上限、1/3轮、单Node一次、30秒总上限。四语言、原主题/宽度/账号密码/UDP模式保留。只测当前草稿，不保存或重启业务核心；停止等待不取消Node已启动的限时任务。不是客户端或中转整链验收，也不是测速/业务Xray探测。

主控新增sudo POST /api/node/{node_id}/egress/test；既有PUT/DELETE出口接口改为Node重启/API确认后才提交，失败保留保存值，Node启动失败尝试恢复旧配置，ACK丢失明确未确认且不盲目重发。Node新增认证REST /egress/probe、RPyC probe_egress与managed-egress-probe-v1能力。修复密码首尾空格被Node裁剪的问题。两仓库需配对更新；scripts无运行时变化，Xray v26.3.27、数据库迁移/证书/端口/用户/.env/数据卷无变化。

[合同、错误码、摘要证据与升级验收](../EGRESS_PROBE.md)。先更新使用出口检测的目标Node，再更新主控；scripts无运行时变化。

2026-10-15 发布证据：主控源789130c30a69a85708255154d0d4f6a24c573495，经PR #21合入258218c07c9f2e265e790764bd727e528dcb761d；Node源ce3bed0decccef70c70765f9f59936a8b6a78dc6，经PR #5合入168a9e63d7c5219dffafd5839876db30b57e3cd5。主控分支Actions38670782109、正式38671882097，Node PR38660291647/分支38660285441、正式38671875814均成功；两latest的index/双架构manifest/config摘要与OCI revision已核对。用户要求的额外一轮主控190/190、Node80/80、前端60/60、类型/生产构建/pip check也通过。仅文档[skip ci]回写不改变镜像运行时revision；服务器未更新/验收，不能据此宣称实际供应商或客户端已恢复。
