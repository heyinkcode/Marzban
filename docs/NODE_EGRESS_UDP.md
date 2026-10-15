# Node 出口代理的 DNS 与 UDP 模式

在每个目标 Node 的「住宅 IP／出口代理」中选择 HTTP/SOCKS5 和 UDP 处理模式。模式仅作用于该 Node 的配置副本，主面板本机和其他 Node 各自独立。

## 为什么按 Node 设置

客户端支持 UDP 不代表每个请求都使用 UDP。不同客户端的 DNS、分流和应用回退方式可能不同；不能只凭一个客户端可用就认定供应商支持 UDP。应分别验证供应商 DNS、UDP 和具体应用；共享 Node 日志不能把所有失败归因于同一客户端。UDP 选项不改变 HWID/设备登记策略。

沿用原 Chakra 的住宅出口表单，仅增加“UDP 处理”：桌面为“协议/UDP 处理、服务器/端口、用户名/密码”三排；手机单列。保留证书、节点端口、启用开关、其他原控件及原弹窗宽度。使用真实组件预览，不另做设计稿。

## 模式合同

| `udp_mode` | 行为 | 适用范围 |
| --- | --- | --- |
| `legacy` | 默认保持此前行为：SOCKS 默认 TCP/UDP 走住宅代理，HTTP 默认只接管 TCP | 老数据/老 Node；线协议省略该字段 |
| `proxy` | SOCKS 默认 TCP/UDP 走住宅代理，不重写 DNS | 供应商确实支持 UDP ASSOCIATE；HTTP 不接受此模式 |
| `tcp_only` | 默认 UDP53 DNS 交给 DNS 出站，DNS 上游经住宅代理走 TCP；其他默认 UDP 阻断，默认 TCP 走住宅代理 | 不支持 UDP 的供应商；不是任意 UDP 转 TCP |

“默认”指未被原有显式 API、安全、域名、IP、入站等规则提前匹配的流量。新规则放在原有通用兜底之前，保留显式路由优先级；**已有显式直连规则依然可以直连**，不能把本功能称为全流量防泄漏保证。本修改不额外添加直连降级。

`tcp_only` 在该 Node 配置副本中把 `dns.servers` 替换为 `tcp://1.1.1.1`、`tcp://8.8.8.8`，保留 hosts/queryStrategy 等其他 DNS 字段，并使用内部专用 DNS tag。A/AAAA 使用该内置解析器；其他 DNS 查询通过 DNS 出站 TCP 隧道处理。供应商必须允许相应 TCP53 连接；自定义域名 DNS 分流会被替换，需管理员确认。语音、游戏、QUIC 等其他 UDP 不会因此获得支持；应用是否回退到 TCP 由应用决定。

内部保留 tag：`managed-residential-dns`、`managed-residential-dns-query`、`managed-residential-udp-block`。配置存在同名 tag 时拒绝，不覆盖原配置。Node 在副本中完整验证，失败不写入半套配置；最终配置仍由固定 Xray 预检。

## API、认证与下发

- 路径不变：`GET/PUT/DELETE /api/node/{node_id}/egress`，仍需要 sudo 管理员认证。
- PUT 新增 `udp_mode`，省略为 `legacy`；GET 配置存在时返回保存的模式。协议/服务器/端口/用户名及原密码留空保留规则不变；API 不返回密码。
- 能力：`legacy` 需要 `managed-outbounds-v1`；非 legacy 还需要 `managed-outbounds-udp-v1`。旧/离线/能力不足的 Node 在保存前返回 409；非法模式或 HTTP+proxy 返回 422；认证失败仍 401/403，未知 Node 404。
- 当前保存/移除还要求 `managed-egress-probe-v1`，经核心预检、启动和 API 就绪确认后才提交；不是旧的仅排队异步重启。传输/ACK 丢失时结果未确认，不盲目重发。成功应用仍不代表供应商连通，详见[检测与安全应用](EGRESS_PROBE.md)。重连/重启继续检查非 legacy 能力。
- 原有认证 REST/RPyC Xray 控制通道传输 `marzban_node_extensions.outbounds[0].udp_mode`，不增加接口、证书或公网端口。只改对应 Node 的配置副本，不改主核心出口。

## 数据、升级和回退

主面板新增 Alembic `7e8f9012ab34`，父版本 `6d7e8f9012ab`，只给 `node_egress` 添加非空 `udp_mode` 字段，旧记录默认 `legacy`。不删除用户、节点、代理凭据、证书、环境文件或数据卷。固定核心仍为 `v26.3.27`，scripts 无变化。

先更新具备出口模式及当前安全应用能力的目标 Node、验证主面板连接，再更新主面板并为测试 Node 选择模式。已切 Fork 的原部署只 update，不重复 adopt、不重装、不删除卷。升级前备份数据库和部署配置。

回退：先恢复目标 Node 为 legacy 并确认生效，再回退配对镜像。旧主面板不能理解新增字段；数据库降级仅移除新字段，需停服务并先备份，不能删除整个表或替换用户库。若 Node 降级但仍保存非 legacy 模式，主面板会报能力不兼容而不是静默放行。

## 使用检查

先在测试账号/隔离 Node 核对 HTTPS 出口 IP，再分别验证 DNS、应用 TCP/UDP、切回 legacy 和原中转路径。供应商支持 TCP 不等于支持 UDP；不要为排查一个客户端而关闭忙碌节点的全部出口或改设备策略。

## 上游和参考

保留 Gozargah/Marzban、Marzban-Node 和 XTLS/Xray-core 原作者与许可证。本次实现为 Mr.shaw 扩展；参考下列上游行为，未复制供应商或其他面板源码：

- Xray DNS 出站：[dns.go（固定 v26.3.27）](https://github.com/XTLS/Xray-core/blob/v26.3.27/proxy/dns/dns.go)、[dns_proxy.go](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/dns_proxy.go)。
- 客户端 DNS 对照：[Mihomo DNS 配置](https://wiki.metacubex.one/config/dns/)。它用于解释不同解析传输，不是实际手机配置的证据。

[连接检测与保存结果](EGRESS_PROBE.md) · [历史测试和发布记录](releases/node-egress-udp-guide-20261015.md)
