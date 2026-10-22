# 捐赠入口：历史发布记录

[当前说明](../DONATION_LINK_RELEASE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261003-DONATION-LINK：捐赠入口维护

新主面板 latest 已发布：源 e72943b、Actions 37123809995 成功，两个架构的 digest/revision 核对通过；服务器点击验收待完成。Node/scripts 不需更新。

原捐赠菜单保持原结构与主题，只将目标改为本 Fork README 的 Donation 锚点；中英文说明同步维护者提供的地址，并区分 Fork 与上游捐赠。不是新增支付、到账监控或二维码功能。API、数据库、Node/scripts、证书、端口、订阅与核心均无变化；[变更及发布证据](../DONATION_LINK_RELEASE.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## MR-20261003-DONATION-LINK：捐赠入口指向本 Fork（2026-10-03）

- 按维护者本地修改，将前端捐赠链接指向 `kissow/Marzban#donation`，同步中英文 README 的两组 USDT 地址；BNB Smart Chain 标签规范为 BEP20。
- 明确这些地址支持 Mr.shaw 社区 Fork，保留上游署名、许可证和原项目捐赠说明链接；未修改 Header 结构或 Chakra 主题。
- API、数据库、订阅、Node 通道、证书、端口、环境、用户数据及 Xray v26.3.27 无变化；Node/scripts 无变化，无需更新。主面板常量变更需要新镜像。
- 测试、提交、Actions、镜像和服务器状态分别登记于 [发布记录](../DONATION_LINK_RELEASE.md)；不沿用前一功能的镜像证据。
- 发布完成：源 e72943b、Actions 37123809995 首次成功，latest index `sha256:28ffe73996bd0078df894e0d56b0ec742087d678acebd8c8d34b646791f7eb6c`，amd64/arm64 revision 均核对通过；服务器点击验收待完成。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261003-DONATION-LINK：Fork 捐赠入口

镜像发布状态：Actions 37123809995 成功，主面板 latest 的 amd64/arm64 revision 均为 e72943b6dad1abf6ccd58307cb1008bd6793d81f；digest 与服务器更新方式见发布记录。没有 API/协议变更或 Node 更新要求，服务器点击验收尚待确认。

只更改前端 `DONATION_URL` 和中英文 README 的捐赠说明，不是 API 或收款服务。API、数据库、Node 通道、订阅、认证、证书、端口、环境文件、数据卷及 Xray v26.3.27 均无变化；Node/scripts 无需配对构建或服务器更新。[发布记录](../DONATION_LINK_RELEASE.md)。

## 历史片段 4

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## 原版环境变量、接口边界与捐赠入口

截图中 README 的“变量/描述”表不是 HTTP 接口，而是 Marzban 启动时读取的 `.env` 环境变量。完整默认示例以 [`.env.example`](../../.env.example) 为准；下面按功能说明，新增配置时必须同时更新 `.env.example` 和本文，不要把真实密码、Token、数据库连接串或钱包私钥提交到仓库。

| 配置项 | 作用 | 是否通常需要改动 |
| --- | --- | --- |
| `UVICORN_HOST` / `UVICORN_PORT` | Web/API 监听地址和端口 | 按部署端口改；反代场景通常保持默认监听 |
| `ALLOWED_ORIGINS` | 浏览器跨域来源白名单 | 有独立前端域名时按需填写 |
| `SUDO_USERNAME` / `SUDO_PASSWORD` | 初始化管理员信息 | 仅首次初始化使用，优先用 CLI 创建管理员 |
| `UVICORN_UDS` | Unix Socket 监听路径 | 只在 Nginx/本机 Socket 部署时使用 |
| `UVICORN_SSL_CERTFILE` / `UVICORN_SSL_KEYFILE` / `UVICORN_SSL_CA_TYPE` | 应用自身 HTTPS 证书、密钥和 CA 类型 | 已由反向代理终止 HTTPS 时通常不填 |
| `DASHBOARD_PATH` | 管理面板路径前缀 | 需要非根路径部署时设置 |
| `SQLALCHEMY_DATABASE_URL` | SQLite、PostgreSQL、MySQL/MariaDB 数据库连接 | 迁移数据库时设置，升级不能覆盖 |
| `SQLALCHEMY_POOL_SIZE` / `SQLIALCHEMY_MAX_OVERFLOW` | 数据库连接池参数 | 高并发时按数据库容量调整 |
| `XRAY_JSON` | Xray JSON 配置文件路径 | 使用自定义配置时设置 |
| `XRAY_EXECUTABLE_PATH` / `XRAY_ASSETS_PATH` | Xray 二进制和 Geo 资源路径 | 自定义 Xray 安装路径时设置 |
| `XRAY_SUBSCRIPTION_URL_PREFIX` / `XRAY_SUBSCRIPTION_PATH` | 用户订阅 URL 的域名/前缀和路径 | 订阅域名或路径变化时设置 |
| `XRAY_EXCLUDE_INBOUND_TAGS` / `XRAY_FALLBACKS_INBOUND_TAG` | 排除入站标签、备用入站标签 | 使用备用/回落入站时设置 |
| `TELEGRAM_API_TOKEN` / `TELEGRAM_ADMIN_ID` / `TELEGRAM_LOGGER_CHANNEL_ID` | Telegram 机器人、管理员和日志频道 | 启用 Telegram 功能时填写 |
| `TELEGRAM_DEFAULT_VLESS_FLOW` / `TELEGRAM_PROXY_URL` | Telegram 默认 VLESS flow 和代理 | 按客户端/网络环境按需设置 |
| `DISCORD_WEBHOOK_URL` | Discord 通知 Webhook | 需要 Discord 通知时填写 |
| `CUSTOM_TEMPLATES_DIRECTORY` | 自定义订阅模板目录 | 使用自定义模板时设置 |
| `CLASH_SUBSCRIPTION_TEMPLATE` / `SUBSCRIPTION_PAGE_TEMPLATE` / `HOME_PAGE_TEMPLATE` | Clash、订阅页、首页模板 | 修改订阅或页面外观时设置 |
| `V2RAY_SUBSCRIPTION_TEMPLATE` / `V2RAY_SETTINGS_TEMPLATE` | V2Ray 订阅和设置模板 | 使用自定义 V2Ray 输出时设置 |
| `SINGBOX_SUBSCRIPTION_TEMPLATE` / `SINGBOX_SETTINGS_TEMPLATE` | Sing-box 订阅和设置模板 | 使用自定义 Sing-box 输出时设置 |
| `CLASH_SETTINGS_TEMPLATE` / `USER_AGENT_TEMPLATE` / `GRPC_USER_AGENT_TEMPLATE` | Clash settings and normal/gRPC User-Agent templates | Optional; change only when client output requires it |
| `MUX_TEMPLATE` | Mux 配置模板 | 需要自定义 Mux 时设置 |
| `USE_CUSTOM_JSON_DEFAULT` / `USE_CUSTOM_JSON_FOR_V2RAYN` / `USE_CUSTOM_JSON_FOR_V2RAYNG` / `USE_CUSTOM_JSON_FOR_STREISAND` / `USE_CUSTOM_JSON_FOR_HAPP` | 是否为各客户端使用 JSON 配置 | 只有客户端需要 fragment/mux 等能力时启用 |
| `SUB_PROFILE_TITLE` / `SUB_SUPPORT_URL` / `SUB_UPDATE_INTERVAL` | 订阅响应头中的标题、支持链接和更新间隔 | 按品牌和客户端需要设置 |
| `EXTERNAL_CONFIG` | 导入外部 V2Ray 配置 | 确认外部地址可信后使用 |
| `ACTIVE_STATUS_TEXT` / `EXPIRED_STATUS_TEXT` / `LIMITED_STATUS_TEXT` / `DISABLED_STATUS_TEXT` / `ONHOLD_STATUS_TEXT` | 自定义 Active、Expired、Limited、Disabled、On-Hold 文案 | 需要本地化或品牌文案时设置 |
| `USERS_AUTODELETE_DAYS` / `USER_AUTODELETE_INCLUDE_LIMITED_ACCOUNTS` | 过期用户自动删除策略 | 谨慎设置；负数表示关闭自动删除 |
| `NOTIFY_STATUS_CHANGE` / `NOTIFY_USER_CREATED` / `NOTIFY_USER_UPDATED` / `NOTIFY_USER_DELETED` / `NOTIFY_USER_DATA_USED_RESET` / `NOTIFY_USER_SUB_REVOKED` / `NOTIFY_IF_DATA_USAGE_PERCENT_REACHED` / `NOTIFY_IF_DAYS_LEFT_REACHED` / `NOTIFY_LOGIN` / `LOGIN_NOTIFY_WHITE_LIST` | 状态、登录、用量和用户变更通知 | 按通知策略设置 |
| `DOCS` / `DEBUG` | 开启 OpenAPI 文档、调试日志 | 仅开发/排错时临时开启 |
| `WEBHOOK_ADDRESS` / `WEBHOOK_SECRET` | 多 Webhook 地址和签名密钥 | 对接外部通知服务时设置 |
| `NOTIFY_DAYS_LEFT` / `NOTIFY_REACHED_USAGE_PERCENT` | 通知触发的剩余天数/用量百分比 | 按业务提醒策略设置 |
| `VITE_BASE_API` | 前端构建时使用的 API 基地址 | 前后端域名分离或反代路径变化时设置 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 管理员 JWT 有效期 | 按安全策略设置 |
| `JOB_CORE_HEALTH_CHECK_INTERVAL` / `JOB_RECORD_NODE_USAGES_INTERVAL` / `JOB_RECORD_USER_USAGES_INTERVAL` / `JOB_REVIEW_USERS_INTERVAL` / `JOB_SEND_NOTIFICATIONS_INTERVAL` | 核心、Node、用户用量、审核和通知任务间隔（秒） | 高负载时谨慎调整 |

Compatibility note: the current source reads the historical database-pool variable name `SQLIALCHEMY_MAX_OVERFLOW` (one `A` is missing). Do not replace it with the visually corrected `SQLALCHEMY_MAX_OVERFLOW` unless the code and migration notes are changed together. `RECURRENT_NOTIFICATIONS_TIMEOUT`, `NUMBER_OF_RECURRENT_NOTIFICATIONS`, and `DISABLE_RECORDING_NODE_USAGE` are also supported runtime variables and should be documented when they are enabled.

### 捐赠菜单到底改哪里

当前“捐赠”菜单不是收款接口，也不会调用任何外部收款服务。它由三处组成：

1. 菜单项和点击行为：[`app/dashboard/src/components/Header.tsx`](../../app/dashboard/src/components/Header.tsx) 的 `Link`、`header.donation` 和 `handleOnClose`。
2. 菜单跳转地址：[`app/dashboard/src/constants/Project.ts`](../../app/dashboard/src/constants/Project.ts) 的 `DONATION_URL`。当前值是 `https://github.com/heyinkcode/Marzban#donation`，点击后打开本 Fork 的捐赠锚点。修改此常量后必须重新构建主面板镜像并更新服务器；只推送 README 不会替换已经运行的前端。
3. README 中展示的钱包地址：[`README.md`](../../README.md) 和 [`README-zh-cn.md`](../../README-zh-cn.md) 的 `Donation/捐赠` 小节。修改钱包地址时必须同时更新中英文 README，并核对网络名称，不能只改菜单 URL。

当前前端没有独立的捐赠管理页面，也没有捐赠订单、到账监控或二维码生成逻辑。若以后要接入数字货币收款，应作为独立支付功能开发，不能把钱包地址硬编码到管理端或用户端脚本中。

## 历史片段 5

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261003-DONATION-LINK（2026-10-03）

- [x] 维护者提供地址；中英文 README、前端目标和接口说明保持一致，注明 Fork 受支持方并保留上游致谢/许可证。
- [x] Header/主题/布局无变化；API、数据库、Node 通道、订阅、证书、端口、用户数据和 Xray v26.3.27 无变化。Node/scripts 无需更新。
- [x] 主面板 54 项后端测试、TS/Vite、差异检查、生产 JS 目标和中英文地址一致性检查通过。
- [x] 源提交 e72943b 已推送 master，GitHub API 核对通过；Actions 37123809995 自动触发。
- [x] Actions 37123809995 首次成功，新 latest index/两个架构 digest/OCI revision 均核对本次源 e72943b；证据见发布记录。
- [ ] 服务器更新后点击捐赠入口验收。

实际结果及边界统一登记于 [DONATION_LINK_RELEASE.md](../DONATION_LINK_RELEASE.md)，不得把推送完成写成镜像已发布。钱包地址为维护者提供，未做链上归属或转账验证。

## 历史片段 6

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261003-DONATION-LINK：捐赠入口（2026-10-03）

已发布主面板镜像：源 e72943b、Actions 37123809995 首次成功，latest index `sha256:28ffe73996bd0078df894e0d56b0ec742087d678acebd8c8d34b646791f7eb6c`，amd64/arm64 OCI revision 核对通过。服务器点击验收待完成；此轮只更新主面板，Node/scripts 无变化。

主面板只修改前端捐赠常量及中英文 README；补齐更新记录、接口说明和发布清单。Node/scripts 代码与文档合同均无变化，不需配对构建或服务器更新；所有 API、数据库、Node 通道、订阅、证书、端口、环境、数据卷及固定核心 v26.3.27 保持原样。常量变更须构建新主面板镜像，README 推送立即生效但不更新已部署前端。[测试/提交/构建/镜像/服务器记录](../DONATION_LINK_RELEASE.md)。
