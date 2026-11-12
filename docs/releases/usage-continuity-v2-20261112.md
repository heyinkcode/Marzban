# v2 首次付款期恢复验证（2026-11-12）

状态：代码已合并，主控双架构镜像已发布并核验；尚未代用户升级生产服务器或写客户数据。外部网站部署与实际恢复操作单独验收。

主控增加独立 v2 路由/模型及窄条件，原子写入复用 v1 的 BEGIN IMMEDIATE/CAS/审计。v1 两条历史合同不放宽。无新增迁移，Node/scripts/Xray 版本/端口/证书/首页/UI 不变。

基线 origin/master：`8b5b2115c431dcc321f86ca33d3784c0f2bba08c`；本地分支 `fix/external-reset-control-20261112`。最终本地验证：

- 首版 v2 29 项连续三轮通过（3.002s / 3.143s / 3.082s）。
- 对接方要求的 `expected.initial_reset=null` 已落地；追加机器合同/请求摘要、非 SQLite 拒绝、严格类型、禁止补造零历史、历史清除保护、重置写锁及原位历史变更验证后，最终专项 **35/35**（3.409s）。
- 原 v1 专项 **41/41**（3.655s）；外部控制专项此前连续三轮各 **8/8**。原 v1 两条历史规则未放宽。
- 全量后端先 **349/349**（152.939s）；再追加上述六项测试后最终 **355/355**（153.256s），均无跳过，使用固定 Xray v26.3.27。重复轮次不计作新增独立用例。
- 项目固定 Python 3.12.14；依赖检查、六个变更 Python 文件语法及 `git diff --check` 通过；变更文档相对链接目标检查通过。前端、Node、scripts 无本轮代码变化，未重新执行其构建。

覆盖包括真实隔离 SQL 账本/写锁/CAS、并发增量与 UUID 竞态、ASGI 权限、失败回滚、额度临界拒绝和后续限额；网站支付及生产服务器不在本地测试覆盖范围。

发布前置中的提交、PR/Linux CI、镜像构建与 OCI 核对现已完成，证据如下。仍需用户备份升级后只读探测 v2 capability；不需要更新 Node/scripts。外部系统还需独立核验首购付款与初始开通账本，持久化原请求后才能在明确授权下恢复。

隔离 SQLite WAL，签名和外部Xray报告使用测试替身；不能据此宣称生产修复、实际支付或远端Xray停用已验收。实际请求仍可能因新用量达到额度、过期、控制权变化或历史变化而拒绝。

## 正式发布证据

- 功能源 `ae67eaf1d5bce582b4b7a88bf2baf65607b169d9`；[PR #32](https://github.com/heyinkcode/Marzban/pull/32) 合并为 `8fcfd60616c951936aa795edc9817aff561177f2`。
- [PR 分支检查](https://github.com/heyinkcode/Marzban/actions/runs/43218458379)、[PR 镜像验证](https://github.com/heyinkcode/Marzban/actions/runs/43218458502) 均成功后合并；[正式构建](https://github.com/heyinkcode/Marzban/actions/runs/43219778338) 成功。
- PR 与正式构建的普通 Linux 后端均运行355项，无核心阶段11项跳过；随后固定真实 Xray v26.3.27 补跑中转2、本机出口34、专线运行时4项通过。前端73项、类型和生产构建通过。不要把普通阶段跳过项写成无跳过。
- 无网络 amd64 镜像内验证完整历史迁移、合成用户数据、重复迁移与恢复审计的回退保护；既有专线迁移 head `d456ef78ab90` 验证通过。无效 DB 路径时默认启动非零退出且不启动应用。v2没有新增迁移。
- 2026-11-12 12:53:51 UTC（北京时间20:53:51）匿名读取 GHCR，核对 index、amd64/arm64 manifest/config 原始字节 SHA-256、架构及 OCI revision。index 与正式构建输出一致；发布完成前的一次查询仍是旧 revision，未将其误报为新版本。

镜像 `ghcr.io/heyinkcode/marzban:latest`，运行时 revision：`8fcfd60616c951936aa795edc9817aff561177f2`。不可变 index：

```text
sha256:fcabb5e8094d79ade50470c1e78cc41aaee9488de0fabf9250ed4a445ab47a54
```

| 架构 | manifest SHA-256 | config / 本地 image ID SHA-256 |
| --- | --- | --- |
| linux/amd64 | `695c9dbc68b6ed815f5cf7554b0e5bf81e36775dd93999a4c286e4e42de07537` | `6da6113c1b1ffe98cc5590f2dbfe8346a13660fa7fbafc1308ff04e85f66bd41` |
| linux/arm64 | `cdea6c7a7a9849e316f720eca5d1c53fb4e2e1263b7e567fe437a6b4617c435e` | `cd9fbbad6f769914741058d7f71f7b7d927cb4a2cd19cb9203dfdc14139f54b0` |

arm64已构建及制品核验，未在真实arm64服务器验收。原README、证书、端口、.env和用户数据不改。后续纯文档 `[skip ci]` 回写不重新构建镜像，运行时revision保持上值。

已有标准 Fork 主控按[备份升级与只读验收](../USAGE_CONTINUITY_V2.md#已有标准-fork-主控的升级)执行，不重装/删卷。服务器更新、网站协调器验收、客户恢复及no_reset交接均未由本次仓库发布自动完成。
