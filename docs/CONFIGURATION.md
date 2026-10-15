# 配置与环境变量

环境变量与管理员 API、Node 控制通道是不同层。升级保留既有 .env、数据库、证书、端口、配置与数据卷。


环境变量由 Marzban 启动时读取，不是 HTTP 接口。完整默认示例以 [`.env.example`](../.env.example) 为准；下面按功能说明，新增配置时必须同时更新 `.env.example` 和本文，不要把真实密码、Token、数据库连接串或钱包私钥提交到仓库。

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


捐赠入口的维护位置见[专页](DONATION_LINK_RELEASE.md)。接口见[索引](../MR_SHAW_API_AND_RELEASE.md)，发布步骤见[更新流程](REPOSITORY_UPDATE_FLOW.md)。
