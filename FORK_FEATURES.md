# Marzban 开源扩展功能

- [GitHub 用户名迁移与已有服务器更新](docs/GITHUB_NAMESPACE_MIGRATION.md)

基于上游 Marzban 的开源扩展，保留原作者署名、历史与许可证。产品安装见 [README](README.md)，完整导航见[文档中心](docs/README.md)。

| 功能 | 用途与边界 | 使用说明 |
| --- | --- | --- |
| 用量连续性修复 | sudo 审核后的单次月重置恢复，原子加回当前量且不重复累计；SQLite 严格限制 | [账目与接口](docs/USAGE_CONTINUITY.md) |
| 节点状态 | 分别显示控制连接、资源和活动采样；在线用户不等于设备或连接数 | [活动统计](docs/NODE_ACTIVITY_AND_POLICY.md)、[连接恢复](docs/NODE_CONTROL_RESILIENCE.md) |
| 节点出口代理 | 每个 Node 独立配置 HTTP/SOCKS5；DNS/UDP 按模式处理 | [出口与 UDP](docs/NODE_EGRESS_UDP.md) |
| 出口连接检测 | 从目标 Node 检测代理握手、HTTPS 出口和所选 DNS/UDP；不是客户端整链测速 | [检测与安全应用](docs/EGRESS_PROBE.md) |
| 透明中转 | 选择 Marzban 或源 Node 转发到目标 Node；原订阅名称、数量和目标出口保留 | [中转设置](docs/NODE_RELAY_SOURCES.md)、[分段测速](docs/NODE_RELAY_TESTING.md) |
| 本机使用系数 | 只影响主面板业务用户后续流量计费，不是网速倍率，不重算历史 | [使用系数](docs/MAIN_USAGE_COEFFICIENT.md) |
| 本机独立出口 | 只为本机业务核心叠加 HTTP/SOCKS5 出口，提供本机检测；不下发给其他 Node | [设置与隔离](docs/MAIN_EGRESS.md) |
| 设备登记 | HWID 登记及独立凭据；无 HWID 共享兼容路径可绕过限额，不是物理设备硬限制 | [登记与策略](docs/NODE_ACTIVITY_AND_POLICY.md) |
| 原界面兼容 | 原 React/Chakra 主题、多语言、窄屏布局和浏览器翻译兼容 | [多语言与手机](docs/DASHBOARD_I18N_MOBILE.md)、[翻译](docs/BROWSER_TRANSLATION.md) |

## 兼容范围

Xray 固定 v26.3.27。Node 扩展使用原认证 REST/RPyC 控制通道，不新增公开监控端口。出口检测和安全保存要求配对 Node 能力；Node 中转要求来源支持 managed-node-relay-v1。先核对对应功能的升级条件，不能仅凭容器运行判定功能可用。

当前中转是单跳透明 TCP，首版范围为 VLESS TCP/RAW REALITY，不是任意协议或独立 UDP 中转。客户端的地址和端口必须指向真实中转入口，不能仅显示目标地址却仍由客户端连接另一个端点。

本机出口在「主面板（本机）」卡片中单独管理，不修改共享基础配置；子节点原设置和透明中转保留。实际发布和验收状态见对应专页。

## 更新和接口

[简要更新记录](CHANGELOG.md) · [接口索引](MR_SHAW_API_AND_RELEASE.md) · [发布历史](docs/releases/README.md) · [发布检查](RELEASE_CHECKLIST.md)

测试、Actions、镜像摘要与服务器验收分别记录在对应功能文档，不在此重复发布日志。
