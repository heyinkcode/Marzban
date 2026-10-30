# Marzban 更新摘要

## 2026-10-30（本地开发，未发布）

- 新增通用专线Node授权API、管理员委派、幂等审计、Node凭证与订阅双层过滤；网站自行管理价格/支付，用户流量与套餐不变。[合同与边界](docs/DEDICATED_NODE_ACCESS.md)
- 新增原 Chakra 用户专线权限弹窗、独立节点模式设置与新建专线选项，保留原节点编辑区域；待同步和结果不明时支持原编号回执查询。[面板入口与恢复](docs/DEDICATED_NODE_ACCESS.md#面板操作入口)
- 补齐功能说明交付要求、文档归类和上架文件检查；首页继续保持产品介绍，不增加更新流水账。[文档与发布规范](docs/REPOSITORY_UPDATE_FLOW.md)

## 2026-10-24

- 增加受限、幂等、可审计的单次月重置连续性修复；保留额度/expiry/重置锚点。普通重置增加计数事务保护，修复记录阻止清空历史。[说明](docs/USAGE_CONTINUITY.md)

## 2026-10-23

- 同步 heyinkcode 仓库、安装/更新入口和 GHCR 构建命名空间；旧 Fork 更新迁移见[指南](docs/GITHUB_NAMESPACE_MIGRATION.md)。业务协议、数据和固定核心不变。

使用说明与测试/发布证据进入对应功能文档，本页仅保留摘要。历史阶段全文见[按功能归档](docs/releases/README.md)。

## 2026-10-16

- 分开现行使用说明与历史开发/发布证据，修正中转订阅、能力及保存流程的旧阶段表述；仅文档，不改功能或镜像。[文档中心](docs/README.md)

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
