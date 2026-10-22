# 设备登记限制：历史发布记录

[当前说明](../NODE_ACTIVITY_AND_POLICY.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 测试版：用户级设备登记限制（2026-10-01，CI/GHCR 已发布，服务器验收待完成）

- 在保留官方 Chakra UI、证书、端口、Node 通道、支付和原有用户数据的前提下，在用户创建/编辑窗口的流量字段右侧加入“限制设备”。
- 新增 `users.device_limit`、`device_limit_mode`、`device_limit_action` 与 `user_devices` 表；迁移为 `4a9d2e8b7c61_add_user_device_limit.py`。
- 订阅请求可选携带 `X-HWID`、`X-Device-OS`、`X-Device-Model`；原始 HWID 只保存 SHA-256 哈希。同一 HWID 换公网 IP 不重复计数，同一公网 IP 下不同 HWID 分别计数。
- 新增 `/{XRAY_SUBSCRIPTION_PATH}/{token}/device-status` 脱敏统计；`reject_new` 超限返回 `429`，`log_only` 超限继续放行；普通订阅和显式客户端格式不能通过切换格式绕过登记。
- 不带 `X-HWID` 的旧客户端保持原订阅行为；该功能限制订阅请求登记，不是 Xray 实时连接数，也不能断开已导入配置。
- 本次没有修改 Marzban-Node、Xray `v26.3.27`、证书、端口、支付或住宅出口通道。历史 `unittest discover`（22 passed）与设备限制专项测试（5 passed）记录保留；本轮完整 pytest 43 项、Node 39 项、前端 TypeScript/Vite 构建和 SQLite 迁移升级/回滚均已通过。PostgreSQL、真实客户端、Linux 联调和生产验收仍待完成，因此当前是测试版，不标记为稳定发布。
- 成功发布证据：Actions run `36838046078`，源 commit `071819b1d90ca5bcf9dac903d11748ac8080dec7`；`ghcr.io/kissow/marzban:latest` OCI index digest 为 `sha256:290994ba997ed3120e494814717520db6216d9b615df4b54bc6f8bf147771b07`，amd64 digest 为 `sha256:e17e7dab19d8cf637e2586b65a913ec9c2c758708628be31115411dece67a7e7`，arm64 digest 为 `sha256:49b1183f193113cdb6c0b5e4d8254b86bce6c0d56e261ec3fe0032fd423c5ff9`；两种架构 OCI revision 均为上述源 commit。
