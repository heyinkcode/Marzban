# 文档中心 / Documentation

- [GitHub 用户名迁移与已有服务器更新](GITHUB_NAMESPACE_MIGRATION.md)

README 只介绍产品、安装和使用入口。功能、兼容边界、更新记录与发布证据按下面的入口查阅。

## 功能与使用

- [扩展功能概览](../FORK_FEATURES.md)
- [节点 HTTP/SOCKS5 出口、DNS 和 UDP 模式](NODE_EGRESS_UDP.md)
- [出口连接检测、失败原因与安全应用](EGRESS_PROBE.md)
- [Marzban 或 Node 中转到目标 Node](NODE_RELAY_SOURCES.md)
- [中转设置步骤](NODE_RELAY.md)、[订阅显示规则](NODE_RELAY_SUBSCRIPTION.md)、[链路检测与测速](NODE_RELAY_TESTING.md)
- [主面板本机使用系数](MAIN_USAGE_COEFFICIENT.md)
- [主面板本机独立出口与连接检测](MAIN_EGRESS.md)
- [设备登记、在线用户与策略边界](NODE_ACTIVITY_AND_POLICY.md)
- [节点控制连接超时与恢复](NODE_CONTROL_RESILIENCE.md)
- [浏览器翻译兼容](BROWSER_TRANSLATION.md)
- [多语言与手机页面](DASHBOARD_I18N_MOBILE.md)

## 更新、接口与维护

- [用量连续性修复](USAGE_CONTINUITY.md)、[部署与回退闸门](USAGE_CONTINUITY_DEPLOYMENT.md)
- [更新记录](../CHANGELOG.md)
- [接口与兼容性](../MR_SHAW_API_AND_RELEASE.md)
- [配置与环境变量](CONFIGURATION.md)
- [更新流程与跨仓库登记](REPOSITORY_UPDATE_FLOW.md)
- [发布检查清单](../RELEASE_CHECKLIST.md)
- [历史首页发布记录归档](README_RELEASE_HISTORY.md)
- [按功能查阅历史发布证据](releases/README.md)

SHA、Actions、镜像摘要、测试和服务器验收状态写入对应功能/发布文档，不再插入产品首页。服务器验收与镜像发布分别记录。

## 功能发布与历史记录

各功能说明底部链接对应测试、镜像和验收记录；[历史索引](releases/README.md)保留旧阶段原文。日常设置以现行说明为准，不使用旧镜像 SHA 或已失效的开发阶段提示代替当前要求。主面板本机出口的发布记录见[专页](MAIN_EGRESS_RELEASE.md)。

## 原项目资料

- [Marzban 上游文档](https://gozargah.github.io/marzban)
- [原作者仓库与贡献者](https://github.com/Gozargah/Marzban)
- [许可证](../LICENSE)
