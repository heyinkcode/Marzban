# 中转链路检测与测速

先更新客户端订阅并选择原名称条目，不应新增 Relay；入口是实际中转来源，出口应为目标 Node 或其住宅代理。保持同一电脑/手机、客户端、路由/TUN 设置和测速站点；尽量同一测速服务器，低峰无其它下载。依次比较来源服务器自身业务直连、同一目标 Node 直连、同一目标经中转，每种三轮，记录下载/上传 Mbps 和空闲/负载延迟并比较中位数。切换连接方式后刷新订阅，不需新增重复条目。fast.com 测量到 Netflix 的链路，不能代表所有线路；YABS 的服务器到其它测速机结果不是客户端这条链路。[FAST 官方说明](https://fast.com/)。

来源服务器直连须保持其原出口；目标 Node 经中转时须使用对应 Node 或其原住宅代理出口。必须验证 v2rayN/v2rayNG/Clash Meta 实际联网与至少30分钟观察；面板 running 只证明监听就绪，不证明提速。160 Kbps=0.16 Mbps，不能与服务器 Mbits/sec 忽略单位直接比较。

若中转仍慢，可选临时 iperf3 测中转来源服务器→目标 Node 段，不修改 Node 控制/API端口。两台先运行 `iperf3 --version`；没有安装时可由管理员在 Ubuntu 上安装 `apt-get update && apt-get install -y iperf3`，不是本功能必须依赖。仅在目标 Node 云安全组/防火墙临时允许 **来自中转来源服务器公网 IP** 的 TCP 5201，不对全网开放；低峰运行，注意流量和在线用户。

目标 Node 服务器 SSH（前台，不作为长期服务）：

```sh
iperf3 -s -p 5201
```

中转来源服务器另一个 SSH，输入实际目标 Node IP，不是来源服务器中转地址：

```sh
read -r -p '目标Node公网IP: ' TEST_NODE_IP
iperf3 -c "$TEST_NODE_IP" -p 5201 -t 15 -P 1
iperf3 -c "$TEST_NODE_IP" -p 5201 -t 15 -P 1 -R
```

第一条数据来源服务器→目标 Node，`-R` 数据目标 Node→来源服务器；可重复三轮，必要时对照 `-P 4` 总吞吐，不把多流成绩当单连接速度。结束在目标 Node 服务器 Ctrl+C，删除临时5201规则。[iperf3 官方参数](https://software.es.net/iperf/invoking.html)。

这个测试只测中转来源服务器与目标 Node 之间，不经过真实 REALITY 用户连接，也不测客户端→来源服务器或目标 Node→网站/住宅代理。结合相同目标切换路径后的客户端对照、两台 `docker stats --no-stream`、实际流量/重传才能定位瓶颈。不保证中转必然更快，任何一段线路/带宽/住宅代理都可能限制最终速度。

中转来源可以是 Marzban 主服务器或源 Node；上述来源服务器测试按实际选择执行。不要为测速改动原认证端口或用户额度。

[设置](NODE_RELAY.md) · [来源与状态边界](NODE_RELAY_SOURCES.md)
