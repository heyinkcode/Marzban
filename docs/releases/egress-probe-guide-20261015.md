# Node 出口连接检测与安全应用 历史说明快照

原文截至 2026-10-15，整理于 2026-10-16。下方保留开发阶段、测试及发布证据，不是当前使用指引；其中 latest、未发布、预期 revision 等仅指当时状态。

[当前说明](../EGRESS_PROBE.md) · [历史索引](README.md) · [不可变原文](https://github.com/kissow/Marzban/blob/ec7d665e1323108ab2cd5e5a82294492f8e46bac/docs/EGRESS_PROBE.md)

---

# Node 出口连接检测与安全应用

变更 MR-20261015-EGRESS-PROBE，2026-10-15。状态：配对代码已合并、正式镜像已发布并核对摘要，服务器/自动浏览器视觉验收待完成。配对仓库 kissow/Marzban 与 kissow/Marzban-node；scripts无本轮运行时变化。原作者版权/许可证保留；参考对话仅借鉴诊断与失败恢复思路，没有复用其他项目代码或品牌。

## 范围与拓扑

客户端 → Marzban主服务器或中转Node → 目标Node → 住宅HTTP/SOCKS5 → Internet。中转连接方式与目标Node出口独立；原生出口不配置住宅代理。不会追加订阅条目或更改原别名，不改变原端点重写规则。

本轮探测使用Node独立Python子进程直接执行标准HTTP CONNECT/SOCKS5握手，固定HTTPS目标www.cloudflare.com:443/cdn-cgi/trace，证书验证始终启用。不是通过业务Xray核心发送流量，不代表客户端、中转入口、Xray全部路由或所有应用已通过。云端站点失败也不直接证明供应商故障。HTTP代理本身不新增TLS封装。

仅检测公网代理，所有解析地址必须为global，连接固定已校验的数字IP；最多尝试4个地址，共用阶段时限，不在连接时重新解析。代理私网/本机/链路本地地址拒绝检测，原存储配置结构不迁移。SOCKS5返回UDP relay也校验公网；0.0.0.0/::使用实际TCP对端。无任意URL参数或内网扫描接口。

## 主控 API

沿用Bearer认证和sudo权限、原节点访问校验。新增：

POST /api/node/{node_id}/egress/test

请求示例（合成账号，不是真实凭据）：

```json
{"profile":{"protocol":"socks","udp_mode":"tcp_only","server":"proxy.example.com","port":1080,"username":"demo-user","password":null},"timeout_seconds":5,"attempts":1}
```

协议http/socks；UDP模式legacy/proxy/tcp_only。timeout_seconds仅5或10；attempts仅1或3。密码空值且用户名不变时，仅服务端解密并复用当前节点的保存密码；不把密码返回浏览器。检测不写数据库、不重启、不改业务策略或证书。修改草稿会丢弃旧结果。

200结果：version=1、source=node-egress-probe、scope=node-to-proxy-to-fixed-target、node_id、ok、attempts、completed、checked_at与rounds。每轮包含ok、steps[{stage,status,code,duration_ms}]和可选exit_ip。stage为proxy_dns/proxy_tcp/proxy_auth/https_exit/dns_udp；失败阶段后的步骤不执行。部分轮次完成或总时限到达不记为成功。诊断不返回凭据或原始异常。

既有PUT/DELETE /api/node/{node_id}/egress保留请求字段和成功响应结构，但改为同步确认应用后才保存。新主控要求目标Node具备新能力；旧Node继续服务已有业务，但不能使用新检测/保存/删除流程，提示先升级。GET原接口及证书接口不改。

错误：401/403认证权限，404不存在，422草稿/参数错误；409 NODE_UPGRADE_REQUIRED/NODE_OFFLINE/NODE_BUSY；502 NODE_CONTROL_UNAVAILABLE/NODE_PROBE_UNAVAILABLE/NODE_PROBE_INVALID_RESPONSE/APPLY_UNCONFIRMED_SAVED_UNCHANGED；503 SAVE_FAILED_ROLLED_BACK或SAVE_FAILED_ROLLBACK_UNCONFIRMED。HTTP200中的探测失败仍需看ok/steps，不是HTTP错误。

## Node 通道

REST POST /egress/probe，原双向TLS和session_id校验先于任何探测，body={session_id,profile,timeout_seconds,attempts}。RPyC exposed probe_egress接收JSON字符串{profile,timeout,attempts}，返回JSON字符串，沿用既有认证控制连接。health增加managed-egress-probe-v1；旧主控可忽略新能力。无新公网监听端口，无数据库迁移，无新依赖。

每个Node进程只允许一个探测任务。参数仅经子进程stdin，密码不进入argv/文件/日志。父进程30秒总上限，超时杀掉并回收子进程；单阶段5/10秒，最多3轮。DNS阻塞也受子进程总上限约束。认证拒绝和非公网地址不重试。浏览器的“停止等待”只取消本次HTTP等待，Node探测仍最多30秒，不假称已远程取消。

## DNS、UDP与业务规则

legacy：只测TCP/HTTPS，UDP未验证并明确可能不走代理。

tcp_only：另用同一代理对1.1.1.1:53发真实DNS-over-TCP请求并验证事务；业务Node已有DNS兼容规则保留，其他UDP按既有兼容兜底策略阻断。已有显式路由仍有优先级，不能把此结果当成全部路由均走住宅出口。

proxy（仅SOCKS5）：UDP ASSOCIATE后实际发送封装DNS UDP请求，校验返回来源头和事务ID；只收到ASSOCIATE成功不能当UDP成功。DNS成功也不证明所有游戏/QUIC/软件UDP兼容。

## 应用与恢复边界

主控按节点生命周期锁串行写入：生成候选完整配置 → Node核心preflight → 重启/短期进程存活与原API就绪确认 → 提交加密保存值。Node保留上一份运行配置，替换启动失败尝试恢复；恢复失败单独报告。并发重启拒绝，不静默返回成功。

主控数据库提交失败，在已确认控制通道上尝试恢复原配置。控制连接/ACK丢失时不盲目重发变更；返回“结果未确认，已保存值未变”，不能承诺运行配置必然未变或已回滚。应刷新状态并核对/重新连接，恢复保存的配置。新业务核心稍后退出或真实链路故障仍需服务器验收。

不自动改成服务器直出或自动更换住宅IP。删除出口是管理员明确操作，恢复原基础Xray配置（不保证原配置一定是DIRECT）。保留设备策略与账号同步；全用户账号同步在节点写锁外进行，既有倍率/流量记录/用户/协议/证书/控制API端口不改。密码不再裁剪首尾空格；用户名仍沿用现有规范。

## 检查与防复发

多轮完整后端/Node/前端、类型与生产构建、固定Xray真实解析/UDP-DNS/中转、ASGI认证、HTTP/SOCKS5真实回环握手、TCP和UDP DNS报文、总时限/进程回收/并发、旧Node拒绝、密码保留、数据库失败/ACK丢失分别验证。不能把模拟供应商、SSR或构建成功当成生产连接/视觉验收。

已发现并修复：Windows沙箱使asyncio回环socket初始化卡住（正常本机权限复核；不改产品规避）；首次完整主控发现密码密文重复加密与新记录测试构造兼容问题，恢复原密文保留语义后重跑；并发核心重启原来静默返回已改为明确busy。所有失败需保留日志，不跳过失败用例。

原React/Chakra组件局部修改，检测详情和高级选项默认折叠，原宽度/六个字段/UDP/删除和保存保留。说明图标支持鼠标、触屏和键盘。四语言完整。无新自定义动效，沿用原组件反馈。自动浏览器视觉验收仍受通道不可用阻塞，用户已授权先发布后更新服务器验收。

## 发布与服务器验收

本地状态、push、Actions、镜像摘要、服务器验收分别登记；本轮两仓库正式构建与双架构摘要/revision核对已完成（证据见后节），服务器未更新/验收。先更新使用出口检测的目标Node，再更新主控。纯中转Node如不承担出口检测不强制本轮更新。原已切Fork安装使用update，新机器才install；不重装、不删卷、不重建证书。更新会短暂重启对应服务。

若部署脚本误报“仍使用官方镜像”，先核对docker inspect和Compose config --images，不能对已经是ghcr.io/kissow/marzban-node的安装重复adopt。可在确认默认Compose路径和服务名后使用Docker Compose的pull与up -d更新，不更改镜像源/卷/环境。

更新后主面板刷新页面，在节点“住宅IP／出口代理”弹窗检测1次，再选3轮；分别核对控制连通、代理认证、HTTPS出口IP及所选DNS/UDP。用客户端测试实际访问和原中转路径；至少持续30分钟核对间歇失败。两台生产服务器的真实结果仍待用户验收。

## 本地发布前证据

主控完整190/190两轮、应用专项8/8再三轮；Node完整80/80两轮、出口/固定核心恢复专项21/21再三轮且无跳过；前端60/60、类型、Vite生产构建、依赖/diff通过。记录真实失败后修复并复跑，不删除旧失败日志。真实核心测试使用固定26.3.27，预检失败保留PID、端口冲突恢复旧监听；同时修复日志线程跨进程代际和子进程/管道回收问题。Windows夹具需要SystemRoot，Linux生产环境未改。本地日志在项目.cache/egress-*-final*/release*，不提交含运行输出的日志。

## 2026-10-15 配对发布证据

| 项目 | Marzban主控 | Marzban-Node |
| --- | --- | --- |
| 源提交 | 789130c30a69a85708255154d0d4f6a24c573495 | ce3bed0decccef70c70765f9f59936a8b6a78dc6 |
| 合并PR | [#21](https://github.com/kissow/Marzban/pull/21) | [#5](https://github.com/kissow/Marzban-node/pull/5) |
| 运行时/镜像revision | 258218c07c9f2e265e790764bd727e528dcb761d | 168a9e63d7c5219dffafd5839876db30b57e3cd5 |
| 分支检查 | [38670782109](https://github.com/kissow/Marzban/actions/runs/38670782109) | [PR38660291647](https://github.com/kissow/Marzban-node/actions/runs/38660291647)、[分支38660285441](https://github.com/kissow/Marzban-node/actions/runs/38660285441) |
| 正式构建 | [38671882097](https://github.com/kissow/Marzban/actions/runs/38671882097) | [38671875814](https://github.com/kissow/Marzban-node/actions/runs/38671875814) |
| latest index | sha256:160cdfdd1e2e0fd32681a4ecf22d99154782a8684c670e2697b6005b406b19f9 | sha256:77edfcc4a296b061e5589e0ceb7319609e71f1eef8f0685777afccd244633738 |

两次正式构建均成功。Linux主控普通套件190项（其中2项依赖二进制先跳过，随后的固定Xray步骤2/2通过）、前端60/60、类型/生产构建通过；Node普通套件80项（先跳过10项二进制相关用例），随后固定Xray完整80/80通过。不得只摘录首轮的跳过数或将其当作真实核心验收。用户追加复核后，本地完整主控190/190、Node80/80（均无跳过）、前端60/60、类型/生产构建/pip check再通过一轮；因此完整后端本地累计各三轮，关键专项各另三轮。

2026-10-15T10:46:13+08:00至10:46:15+08:00，使用registry原始字节SHA256校验index、manifest、config；核对Docker-Content-Digest、linux/amd64和linux/arm64的revision，且验证前后latest未变：

| 镜像/架构 | manifest digest | config digest |
| --- | --- | --- |
| 主控 amd64 | sha256:a40ebf0f7a4db69ff0d8b75dbbc905dd95a8a8c05fb3f7293551340dfc7fda7f | sha256:0cc18e2f736161033aac3651e9940a1d5fd961035ab55e49691d855d5493aab8 |
| 主控 arm64 | sha256:a42b4851ce9e2e7bd31b8bfb05e74eee88088e2588b89cac794469b537465759 | sha256:e80ff1d4b68644132592314ada4345f078e1e00e6fdc1d05da57e11513ce807f |
| Node amd64 | sha256:fb8e5f2a009bf16cf7014ef788ae9d0bced9b3eaeac8f25f5cd2f880905800d3 | sha256:8be08c2325e3a233dbac0c0c6ba7d196c2cf760d0ba94e680f76b71c1aec6613 |
| Node arm64 | sha256:15255c2bf7078dcaf2caed5b161912296f8357508bb5eb242a3f5f8d0cb151dd | sha256:f5c418688f375d7ab337c093b207562f9cbff415efdf8ccc6513dbcb0adebc98 |

发布阻塞已记录：主控GitHub此前dispatch返回HTTP422 disabled，但只读仓库开关显示enabled/active；维护者Actions页面确认Fork工作流暂停后手动重新启用，随后本轮分支及正式构建成功。未修改Actions安全权限。Git fetch连续连接重置，保留证据，文档使用树内容与正式合并提交完全相同的本地源基线提交，不覆盖原工作区。

现有非失败警告：Pydantic旧json方法弃用、Vite vendor大包、GitHub Actions运行器Node版本/ubuntu-latest迁移提示；本轮未顺带升级依赖或改变固定业务核心。此处记录不等于这些维护事项已修复。原组件HTML已提供；自动浏览器截图和两台生产服务器实际供应商/手机/桌面/中转链路尚未验收，不标稳定版。

已切换Fork的服务器先在目标Node运行：

```sh
marzban-node update
marzban-node status
docker inspect marzban-node --format '{{.Config.Image}} | {{index .Config.Labels "org.opencontainers.image.revision"}}'
```

Node预期镜像ghcr.io/kissow/marzban-node:latest，revision为上表168a9e63完整SHA。如脚本误报official而inspect/Compose确认已是Fork，按前节核对默认路径后用Compose pull/up -d，不重复adopt。

然后主控运行：

```sh
marzban update
marzban status
docker ps --filter label=com.docker.compose.service=marzban --format '{{.ID}}' | xargs -r docker inspect --format '{{.Config.Image}} | {{index .Config.Labels "org.opencontainers.image.revision"}}'
```

主控预期ghcr.io/kissow/marzban:latest，revision为上表258218c0完整SHA。更新可能短暂重启；保留.env、证书、数据库和卷，不安装/重装。检测单次及三轮、核对出口IP、实际客户端访问并持续观察至少30分钟后，由维护者登记服务器验收。后续仅文档[skip ci]回写不重建上述镜像。

## English summary

Paired panel/Node release. Authenticated bounded Node-side HTTP/SOCKS5 diagnostics are isolated from the business Xray process, with fixed public targets and redacted stage results. Tests do not prove client/relay/application connectivity or throughput. New egress writes require the capability and acknowledged apply; transport ambiguity is explicit, not silently retried. Existing data, certificates, ports and Xray v26.3.27 stay intact. Update target Node first, then panel; scripts unchanged. Production acceptance remains pending.
