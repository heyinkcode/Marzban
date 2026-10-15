# Node 出口连接检测与安全应用

在目标 Node 的「住宅 IP／出口代理 → 管理」弹窗填写代理，先执行连接检测，再决定保存。检测草稿不会保存设置或重启业务核心；保存和移除会应用到目标 Node，与主面板本机出口分别管理。

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

错误：401/403认证权限，404不存在，422草稿/参数错误；409 NODE_UPGRADE_REQUIRED/NODE_OFFLINE/NODE_BUSY；502 NODE_CONTROL_UNAVAILABLE/NODE_PROBE_UNAVAILABLE/NODE_PROBE_INVALID_RESPONSE/APPLY_UNCONFIRMED_SAVED_UNCHANGED；节点启动失败但已恢复也可返回502 SAVE_FAILED_ROLLED_BACK。数据库提交失败后恢复旧配置返回503 SAVE_FAILED_ROLLED_BACK，恢复未确认返回503 SAVE_FAILED_ROLLBACK_UNCONFIRMED。HTTP200中的探测失败仍需看ok/steps，不是HTTP错误。

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

## 配对更新和使用检查

目标 Node 需支持 `managed-egress-probe-v1` 及所选出口模式能力。先更新需要检测/修改出口的目标 Node，确认控制连接后更新主控；只承担透明中转且不使用新出口流程的来源不因此强制更新。已有 Fork 使用原 update，不重装、不删卷或重建证书。脚本误报官方镜像时见[处理方法](https://github.com/kissow/Marzban-scripts/blob/master/docs/UPDATE_IMAGE_RECOGNITION.md)。

检测一轮后可再选择三轮，检查代理认证、HTTPS 出口 IP 和所选 DNS/UDP；再用真实客户端确认访问、中转和持续连接。控制已连接、HTTP 200 或检测通过都不能单独代替业务链路验收。

[历史测试与配对发布证据](releases/egress-probe-guide-20261015.md) · [主面板本机出口](https://github.com/kissow/Marzban/blob/master/docs/MAIN_EGRESS.md)
