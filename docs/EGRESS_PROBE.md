# Node 出口连接检测与安全应用

变更 MR-20261015-EGRESS-PROBE，2026-10-15。状态：本地复核中，未发布。配对仓库 kissow/Marzban 与 kissow/Marzban-node；scripts无本轮运行时变化。原作者版权/许可证保留；参考对话仅借鉴诊断与失败恢复思路，没有复用其他项目代码或品牌。

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

本地状态、push、Actions、镜像摘要、服务器验收分别登记；当前未发布。完成两仓库构建并核对双架构镜像revision后，先更新使用出口检测的目标Node，再更新主控。纯中转Node如不承担出口检测不强制本轮更新。原已切Fork安装使用update，新机器才install；不重装、不删卷、不重建证书。更新会短暂重启对应服务。

若部署脚本误报“仍使用官方镜像”，先核对docker inspect和Compose config --images，不能对已经是ghcr.io/kissow/marzban-node的安装重复adopt。可在确认默认Compose路径和服务名后使用Docker Compose的pull与up -d更新，不更改镜像源/卷/环境。

更新后主面板刷新页面，在节点“住宅IP／出口代理”弹窗检测1次，再选3轮；分别核对控制连通、代理认证、HTTPS出口IP及所选DNS/UDP。用客户端测试实际访问和原中转路径；至少持续30分钟核对间歇失败。两台生产服务器的真实结果仍待用户验收。

## 本地发布前证据

主控完整190/190两轮、应用专项8/8再三轮；Node完整80/80两轮、出口/固定核心恢复专项21/21再三轮且无跳过；前端60/60、类型、Vite生产构建、依赖/diff通过。记录真实失败后修复并复跑，不删除旧失败日志。真实核心测试使用固定26.3.27，预检失败保留PID、端口冲突恢复旧监听；同时修复日志线程跨进程代际和子进程/管道回收问题。Windows夹具需要SystemRoot，Linux生产环境未改。本地日志在项目.cache/egress-*-final*/release*，不提交含运行输出的日志。

## English summary

Paired panel/Node release. Authenticated bounded Node-side HTTP/SOCKS5 diagnostics are isolated from the business Xray process, with fixed public targets and redacted stage results. Tests do not prove client/relay/application connectivity or throughput. New egress writes require the capability and acknowledged apply; transport ambiguity is explicit, not silently retried. Existing data, certificates, ports and Xray v26.3.27 stay intact. Update target Node first, then panel; scripts unchanged. Production acceptance remains pending.
