# 设备独立凭据：历史发布记录

[当前说明](../NODE_ACTIVITY_AND_POLICY.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-02 设备专属凭据与 Node 新连接拒绝（镜像已发布，服务器验收待完成）

> 历史行为：无 HWID 拒绝与共享账号移除已被 2026-10-03 兼容修复取代。以下保留历史发布证据，不代表最新功能边界。

- `reject_new` 用户按 HWID 生成独立的 VMess/VLESS UUID 或 Trojan/Shadowsocks 密码；订阅请求必须带 `X-HWID`，超额或未登记设备不会获得新的订阅凭据。
- 主核心和每个已连接 Node 只加载已登记设备账号，不再为 `reject_new` 用户加载共享基础账号；切回 `log_only` 时清理设备账号并恢复共享账号。
- 新增 `user_devices.credentials` 迁移 `6d7e8f9012ab_add_device_credentials.py`；不保存原始 HWID，不改变已有用户、证书、端口或数据卷。
- 本地面板 43 项、Node 39 项测试通过；主面板 commit `a6efaa8eafd82c3f68d2ff29074cf9eeb1ec8ae0`、Node commit `d6f3bec204a75085939b5b4e25fa6502f5946ae5` 已推送到各自 `master`。主面板 Actions `36975384550`、Node Actions `36975383911` 均成功，两个 GHCR `latest` 镜像已发布；真实 Linux Node、客户端矩阵和服务器验收仍待完成，不得视为稳定发布。
- 主面板镜像 index `sha256:42af5defdd9f325b0244c4be182ae6f77513d1d4e2d3572ea009215508de8dae`，amd64 `sha256:5354fb4ae86ac5f1f5fa5634c7704068caafd6c8764aad577c8f3b3df6e3f1ee`，arm64 `sha256:c07e5de4aad0089d4ca63b3baf3440b4e41dbc3bf94a386b0b51e9cdf741481b`；两个架构 OCI revision 均为主面板 commit。配对 Node 的 digest 和 revision 见 Node 仓库发布清单。
