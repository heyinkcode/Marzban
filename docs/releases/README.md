# 按功能查阅发布历史

使用说明、接口合同与历史证据分开维护。下表是历史记录导航，不代表每项功能已完成生产验收。

| 功能 | 使用或维护说明 | 历史证据 |
| --- | --- | --- |
| 活动统计与策略 | [说明](../NODE_ACTIVITY_AND_POLICY.md) | [发布历史](activity-policy.md) |
| 浏览器翻译兼容 | [说明](../BROWSER_TRANSLATION.md) | [发布历史](browser-translation.md) |
| 控制连接恢复 | [说明](../NODE_CONTROL_RESILIENCE.md) | [发布历史](control-resilience.md) |
| Xray 核心基线 | [说明](../REPOSITORY_UPDATE_FLOW.md) | [发布历史](core-policy.md) |
| 早期 Dashboard 调整 | [说明](../DASHBOARD_I18N_MOBILE.md) | [发布历史](dashboard-history.md) |
| 早期开发与发布流程 | [说明](../REPOSITORY_UPDATE_FLOW.md) | [发布历史](development-history.md) |
| 设备独立凭据 | [说明](../NODE_ACTIVITY_AND_POLICY.md) | [发布历史](device-credentials.md) |
| 设备登记限制 | [说明](../NODE_ACTIVITY_AND_POLICY.md) | [发布历史](device-registration.md) |
| 捐赠入口 | [说明](../DONATION_LINK_RELEASE.md) | [发布历史](donation.md) |
| 出口连接检测与安全应用 | [说明](../EGRESS_PROBE.md) | [发布历史](egress-probe.md) |
| 出口 UDP 与 DNS | [说明](../NODE_EGRESS_UDP.md) | [发布历史](egress-udp.md) |
| 多语言与手机布局 | [说明](../DASHBOARD_I18N_MOBILE.md) | [发布历史](i18n-mobile.md) |
| 主面板 TCP 中转 | [说明](../NODE_RELAY.md) | [发布历史](main-relay.md) |
| 主面板使用系数 | [说明](../MAIN_USAGE_COEFFICIENT.md) | [发布历史](main-usage.md) |
| 节点初连与调度器 | [说明](../NODE_CONNECTION_RELEASE.md) | [发布历史](node-connection.md) |
| 节点重连与恢复 | [说明](../NODE_RECOVERY_RELEASE.md) | [发布历史](node-recovery.md) |
| Marzban 或 Node 中转到目标 Node | [说明](../NODE_RELAY_SOURCES.md) | [发布历史](node-relay-sources.md) |
| 中转订阅身份 | [说明](../NODE_RELAY_SUBSCRIPTION.md) | [发布历史](relay-subscription.md) |
| 普通订阅与 HWID 兼容 | [说明](../NODE_ACTIVITY_AND_POLICY.md) | [发布历史](subscription-compatibility.md) |

历史首页快照单独保留在[旧首页归档](../README_RELEASE_HISTORY.md)，不再追加新记录。新更新在对应功能专页维护，CHANGELOG只保留一句摘要和链接。

## 旧功能说明快照

以下原文完整保留拆分前的使用、测试和发布内容；当前行为以每份快照顶部的当前说明为准。

- [MR-20261007-BROWSER-TRANSLATION：浏览器翻译 DOM 兼容](browser-translation-guide-20261015.md)
- [MR-DASHBOARD-I18N-MOBILE：多语言与手机设置入站修复](dashboard-i18n-mobile-guide-20261015.md)
- [Node 出口连接检测与安全应用](egress-probe-guide-20261015.md)
- [主面板本机使用系数](main-usage-coefficient-guide-20261015.md)
- [Node 活动统计与设备策略合同](node-activity-and-policy-guide-20261015.md)
- [MR-20261006-CONTROL-RESILIENCE：慢链路与会话恢复](node-control-resilience-guide-20261015.md)
- [每个 Node 的住宅出口 UDP 策略](node-egress-udp-guide-20261015.md)
- [MR-20261007-NODE-RELAY：Marzban 主服务器中转到 Node 节点](node-relay-guide-20261015.md)
- [MR-20261008-NODE-RELAY-SOURCES](node-relay-sources-guide-20261015.md)
- [MR-20261007-RELAY-INTERNAL-SUBSCRIPTION](node-relay-subscription-guide-20261015.md)
