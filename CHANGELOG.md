# Marzban 更新摘要

使用说明与测试/发布证据进入对应功能文档，本页仅保留摘要。历史阶段全文见[按功能归档](docs/releases/README.md)。

## 2026-10-15

- 增加主面板本机独立出口、连接检测与失败恢复，子节点原组件和设置不变。[设置](docs/MAIN_EGRESS.md)、[检查与发布](docs/MAIN_EGRESS_RELEASE.md)
- 按功能重整文档：精简功能目录、接口索引、更新流程和检查模板；历史证据分类保留，产品首页不追加日志。[文档中心](docs/README.md)
- Node 出口增加分阶段连接检测及确认后保存、失败恢复边界。[合同与发布证据](docs/EGRESS_PROBE.md)

## 2026-10-08

- 主面板本机可独立设置使用系数，仅影响后续本机业务计费。[设置与发布](docs/MAIN_USAGE_COEFFICIENT.md)
- 中转来源支持主服务器或 Node；管理弹窗和原订阅身份保持。[设置](docs/NODE_RELAY_SOURCES.md)、[发布证据](docs/NODE_RELAY_SOURCES_RELEASE.md)

## 2026-10-07

- 中转只替换匹配端点，不增加 Relay 条目。[订阅合同](docs/NODE_RELAY_SUBSCRIPTION.md)
- 增加主面板到 Node 的透明 TCP 中转。[初版说明](docs/NODE_RELAY.md)
- 修复浏览器自动翻译兼容问题。[说明](docs/BROWSER_TRANSLATION.md)

## 2026-10-06

- 改进节点控制连接、重连与恢复处理。[控制恢复](docs/NODE_CONTROL_RESILIENCE.md)、[节点恢复](docs/NODE_RECOVERY_RELEASE.md)
- 保留原组件并调整多语言和窄屏布局。[说明](docs/DASHBOARD_I18N_MOBILE.md)

## 2026-10-03

- 节点出口增加 UDP/DNS 模式。[合同](docs/NODE_EGRESS_UDP.md)、[发布证据](docs/EGRESS_UDP_RELEASE.md)
- 保留无 HWID 普通订阅兼容路径。[兼容边界](docs/NODE_ACTIVITY_AND_POLICY.md)
- 修复调度器依赖与节点初连，调整 Fork 捐赠入口。[连接说明](docs/NODE_CONNECTION_RELEASE.md)、[捐赠说明](docs/DONATION_LINK_RELEASE.md)

## 2026-10-02 及更早

- 活动采样、设备登记与独立凭据。[现行范围](docs/NODE_ACTIVITY_AND_POLICY.md)
- 早期核心基线、Dashboard 和构建过程。[历史导航](docs/releases/README.md)

镜像发布不等于服务器验收；具体版本与未完成项目以对应功能发布页为准。
