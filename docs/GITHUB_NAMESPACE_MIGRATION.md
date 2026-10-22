# GitHub 用户名迁移与已有服务器更新

GitHub 仓库所有者现为 `heyinkcode`。当前安装、自更新、源码、面板项目入口和镜像构建统一使用新地址。上游 Gozargah/XTLS 的署名及链接不变；历史发布记录中的 `ghcr.io/kissow/...` 和摘要表示当时真实发布的制品，不伪改为新制品。

| 用途 | 现行地址 |
| --- | --- |
| 主控 | https://github.com/heyinkcode/Marzban |
| Node | https://github.com/heyinkcode/Marzban-node |
| 安装和更新脚本 | https://github.com/heyinkcode/Marzban-scripts |
| 主控镜像 | `ghcr.io/heyinkcode/marzban:latest` |
| Node 镜像 | `ghcr.io/heyinkcode/marzban-node:latest` |

## 已有部署

不要重装或删除数据卷。先从新地址刷新原 CLI，再执行 `update`。默认实例的具体一键命令、旧镜像识别、备份、失败恢复及固定版本边界见[脚本迁移指南](https://github.com/heyinkcode/Marzban-scripts/blob/master/docs/GITHUB_NAMESPACE_MIGRATION.md)。自定义实例保留原命令名和安装目录。旧命令本身不会被 GitHub 改名远程自动替换。

本轮仅变更分发命名空间和项目链接，不变更数据库、REST/RPyC 合同、证书、端口、用户、倍率或固定 Xray v26.3.27。更新仍可能有正常备份/容器切换停顿；镜像发布不等于服务器更新和业务验收。

## 本地连接

三个项目的 `origin` 改为对应 `https://github.com/heyinkcode/<repository>.git`，`upstream` 继续指向 Gozargah。GitHub CLI 的已登录身份应为 `heyinkcode`；不把用户名当作令牌，不在仓库保存认证信息。Codex/其他 GUI 的独立 OAuth 连接若出现授权提示，需要在其正规登录界面重新授权，不能通过修改 Git URL 替代授权。

发布和验收记录见[本次发布页](releases/github-namespace-20261023.md)。
