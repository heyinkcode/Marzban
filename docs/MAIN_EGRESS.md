# 主面板本机独立出口

在节点设置顶部的「主面板（本机）」卡片中，点击「住宅 IP／出口代理 → 管理」。本机与每个 Marzban-Node 分别配置；原子节点列表、设置和添加入口不变。[发布与验收状态](MAIN_EGRESS_RELEASE.md)

## 配置范围

本机业务入站 → 本机 Xray 默认出口 → HTTP CONNECT 或 SOCKS5 代理 → Internet。

程序从共享基础配置生成一份本机运行副本，再叠加出口；不把本机代理写入共享 Xray JSON 或下发给 Node。原显式路由保留优先级，因此不是强制所有路由均走代理。Node 控制连接、面板 Web/API、其他 Node 出口和独立透明中转进程不使用本机业务出口。

保存或移除仅重启本机业务核心，会短暂中断本机用户连接；不重启子节点或中转进程。不改用户、订阅端点/名称、使用系数、证书、端口、.env、数据卷或固定 Xray v26.3.27。

## 字段和操作

协议选 HTTP 或 SOCKS5，服务器和端口填代理商提供的端点，不填面板网页 URL、Node 控制端口或 Xray API 端口。用户名和密码同时提供；已保存密码在用户名不变且密码留空时保留，密码首尾空格不裁剪。密码加密存储，GET 和检测结果不返回密码。

UDP 模式与 Node 保持同一含义：legacy 保留兼容行为；proxy 仅支持 SOCKS5；tcp_only 提供 DNS-over-TCP 兼容，其他 UDP 按既有显式路由及默认阻断规则处理，不是任意 UDP 转 TCP。[DNS 与 UDP 的详细边界](NODE_EGRESS_UDP.md)

「连接检测」只检测当前草稿，不保存或重启。测试来源是主面板本机的独立 Python 进程，分阶段检查代理解析、TCP、认证、HTTPS 出口和所选 DNS/UDP；不经过业务 Xray，不代表客户端、中转或所有应用整链通过。仅允许公网代理解析结果和固定测试目标；没有任意 URL 或内网扫描参数。

每次可选 1/3 轮、5/10 秒阶段上限；本机仅一个检测任务，30 秒总上限。停止等待只停止浏览器等待，后台任务仍在限时内结束。修改草稿会清除旧结果；代理失败不会自动切换 IP 或自动直出。

## 应用和失败恢复

本机生命周期锁串行处理保存、重启和恢复：校验草稿 → 生成本机副本 → 固定核心预检 → 替换进程并确认原 API 就绪 → 提交配置。启动失败尝试恢复原配置，数据库提交失败尝试恢复原出口；回滚配置包含当前共享及设备账号，不只依赖旧启动快照。

保存值保存在独立 main_egress 表，重启服务、管理员重启及健康恢复都会重新读取，不会静默丢失设置。解密、迁移或加载失败不等于允许自动绕过代理。恢复失败单独报告；HTTP 请求超时/断开不证明服务端操作已取消，应刷新设置并核对运行状态，不能盲目重复保存。

移除出口恢复共享基础配置中的原本机路由，不保证基础配置一定是 DIRECT。

## 管理接口

全部要求原超级管理员 Bearer Token；不新增公开监听或 Node 能力要求。

| 方法和路径 | 请求及结果 |
| --- | --- |
| GET `/api/node/main/egress` | configured、protocol、udp_mode、server、port、username、has_password；不含密码 |
| PUT 同路径 | protocol=http/socks，udp_mode=legacy/proxy/tcp_only，server，port=1–65535，可选成对 username/password；应用确认后返回脱敏配置 |
| DELETE 同路径 | 应用原基础配置并删除本机记录，返回 configured=false |
| POST `/api/node/main/egress/test` | profile 使用上述草稿，timeout_seconds=5/10，attempts=1/3；不允许布尔值或额外字段 |

检测返回 version=1、source=main-egress-probe、scope=main-to-proxy-to-fixed-target、ok、attempts、completed、checked_at、rounds；各轮包含步骤状态/耗时和可选 exit_ip。与 Node 结果区分来源，不混用 node_id。

401/403 为认证权限；422 为参数或预检失败；409 为本机忙、核心离线/未就绪或已有检测。502/503 的脱敏 code 区分应用失败已恢复、恢复失败、保存失败、读取失败和检测不可用。具体 code 见 [MainCoreError](../app/xray/main_core.py) 与[本机服务](../app/xray/main_egress_service.py)。HTTP 200 的检测仍需查看 ok 和每个步骤，不是测速结果。

## 升级与验收

本功能只更新主面板，Node 与部署脚本无运行时变化，不要求为此更新子节点。已有 Fork 使用 marzban update，新机才 install；先备份并核对镜像再升级，不重装、不删卷。新增迁移 b234cd56ef78 接在 a123bc45de67 后，创建可选空表，不改已有数据。

已有 Fork 默认命令：

```sh
sudo marzban update
sudo marzban status
```

update 包含原备份与拉取/启动流程，需确认备份成功再继续；自定义安装使用原命令名，不要改为另一个实例。容器 Up 不代表出口已验收，需核对[已发布镜像 revision](MAIN_EGRESS_RELEASE.md)和真实客户端。不要为更新本功能刷新 Node 证书或重装 Node。

升级后分别验证本机和子节点原订阅、本机代理出口 IP、移除恢复、重启保留、所选 DNS/UDP 和原中转路径。关闭本机出口不应改变子节点配置。回退到不支持此表的旧镜像会按基础配置启动，可能绕过本机代理；需先停止相关业务并恢复明确可接受的出口方案，不能把回退旧镜像当成自动安全恢复。
