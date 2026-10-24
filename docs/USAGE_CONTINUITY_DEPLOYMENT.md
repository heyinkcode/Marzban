# 用量连续性 v1 — 正式镜像升级与回退

本功能通过正常仓库和 GHCR 发布，不使用本地 overlay 作为部署交付。先核对[发布记录](releases/usage-continuity-20261024.md)中的 Actions、镜像摘要和 revision，不能把 latest 标签、容器 Up 或本地测试当作服务器验收。

## 范围与前置核对

- 只升级 Marzban 主控。Node、部署脚本和前端本轮无运行时修改；保留 Xray v26.3.27、现有端口、证书、用户、.env 和挂载。
- v1 修复仅支持 SQLite。先核对实际 Compose 文件、项目/service、镜像、挂载、数据库路径和 Alembic head；未知分叉迁移或挂载覆盖 `/code/app` 时停止。
- 迁移 `b234cd56ef78 → c345de67fa89` 只新增审计表，不自动修改任何账号。容器启动先迁移，失败即退出，不继续启动应用。
- 更新前保留一致数据库备份、环境/证书/配置/Compose 和原镜像 ID。SQLite 有 WAL 时不能只在线复制主文件；使用已有升级脚本的停写备份流程，并确认没有其他共享数据库写入者。
- 官方镜像首次切换走 adopt；已经是本 Fork 不要再次 adopt 或 reinstall。旧命名空间迁移、固定标签和自定义镜像边界见[指南](GITHUB_NAMESPACE_MIGRATION.md)。

## 已有标准 Fork 安装

仅适用于已确认由本项目脚本管理、Compose 使用本 Fork `latest` 的主控。先刷新管理脚本，再更新（命令应逐行执行，失败停止）：

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/heyinkcode/Marzban-scripts/master/marzban.sh)" @ install-script
sudo marzban update
sudo marzban status
```

`install-script` 仅刷新本机管理命令，不重新安装服务。`update` 先备份再拉取并重建主控容器，会短暂中断主控服务，须在授权维护窗口执行。必须保留脚本输出的备份路径；拉取/迁移失败时不要连续重试或删除数据卷。

自定义 Compose、固定 digest/tag 或非默认命令名的部署，必须按实际模型单独制定升级命令，不能盲目套用以上命令。不要执行 `down -v`、重装、清库或 prune。

## 更新后只读验证

核对实际容器的 `Config.Image`、`.Image` 和 `org.opencontainers.image.revision`，与发布记录中的对应架构 config/revision 比较；index digest 与本地 image ID 是不同层级，不直接比较。

新镜像自带只读数据库盘点脚本，确认容器名后运行：

```bash
docker exec -w /code <已核对的主控容器名> python -B tools/usage_continuity_db_inventory.py
```

预期 `check=ok` 且唯一 head 为 `c345de67fa89`。脚本只加载 config，不启动 app，不输出连接口令、不创建缺失数据库。随后检查日志、面板、订阅、节点连接和原用户流量；用原 sudo 身份访问 preview 验证 capability `usage-continuity-repair-v1`。不要把令牌粘贴到公开日志。

实际修复是另一个授权步骤：外部系统先核实权益、锁定账号并 dry-run，再提交原 UUID/path/expected 请求。安装镜像本身不调用修复 API，也不批量恢复账号。回执、当前/累计/额度/expiry、原日志、后续采集和配额停用均需分别验收。单次修复不改变未来周期或权益管理政策。

## 回退约束

- **无恢复记录**：停止写入并保存新状态，确认审计表为空；受控 downgrade 到 `b234cd56ef78` 后，恢复原镜像/Compose。迁移或启动失败不能当作升级成功。
- **已有恢复记录**：禁止直接运行旧镜像、删除审计表或恢复旧 DB。旧程序不理解恢复减项，会累计双计；旧备份可能丢失期间增量。应保留回执并向前修复，如确需逆向迁移必须单独审核增量保留方案。
- 不要自动把故障后的服务降回旧版本。已经应用的恢复记录会让 downgrade 主动失败，这是保护，不是需要绕过的错误。

正式镜像通过 CI 和合成数据库演练不等于生产备份、迁移或业务验收已完成。
