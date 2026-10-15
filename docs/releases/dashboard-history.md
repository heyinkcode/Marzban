# 早期 Dashboard 调整：历史发布记录

[当前说明](../DASHBOARD_I18N_MOBILE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## 前端主题兼容约束

- 完整保留官方 Marzban 的 Chakra UI 主题配置、颜色 token、字体、深浅色模式和响应式断点；不修改 `app/dashboard/chakra.config.ts` 来为扩展功能另建视觉系统。
- 新增功能只能组合官方 Chakra 组件和项目已有的表单、按钮、提示、Accordion、间距及状态样式，并放入原有 Node 设置流程；不得使用独立 CSS、硬编码品牌色、独立字体或另一套卡片/布局规范。
- 原版节点名称、启用开关、节点地址、节点端口、API 端口、使用系数、证书查看/下载、保存、删除和重连交互必须继续保留。扩展的健康信息和出站配置只是原节点表单中的附加区块。
- 节点未连接时，原节点弹窗在标题栏下方、证书区上方显示后端失败/连接原因；原因为空时显示状态兜底文案。`connecting`/`error` 可从该位置点击原版重连接口，`disabled` 不显示可操作重连按钮。
- `mrshaw-v0.8.4-preview.3` 将节点弹窗最大宽度调整为 860px、指标区域最大宽度调整为 700px；手机端继续使用原视口断点。仅布局变化，不要求更新 Node。
- `mrshaw-v0.8.4-preview.4`（已发布）将节点弹窗最大宽度调整为 800px，刷新按钮移至运行指标标题旁边，五项指标铺满可用内容区，不额外保留右侧空白；原主题、左右内边距、手机端断点和原功能不变。Actions `36726339140` 已发布 `ghcr.io/kissow/marzban:latest`。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## mrshaw-v0.8.4-preview.4（2026-09-30，已发布）

- 根据服务器截图将节点设置弹窗最大宽度由 860px 收窄为 800px，原有左右对称内边距及手机端视口规则保留。
- 将运行指标的“刷新”按钮从最右端移到标题旁边，保留手动刷新和 15 秒自动刷新。五项指标铺满收窄后的可用内容区，不再因 700px 上限在右侧留出额外空白。
- 原版 Chakra 主题、证书、端口、使用系数、启用开关、保存、删除、住宅出口和五项运行指标均保留；API、数据库、Node 通道及部署配置无变化。
- 仅修改原有布局属性，不新增覆盖 CSS；本机使用真实组件和原 Chakra 主题完成桌面/手机响应式渲染验收。Actions `36726339140` 已成功发布多架构镜像；服务器截图仍需由部署环境完成验收。

## 历史片段 3

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## mrshaw-v0.8.4-preview.3（2026-09-30，服务器验收预览版）

- 按生产截图将节点设置弹窗最大宽度从 1040px 收窄为 860px，桌面横向内边距调整为 20–24px；节点运行指标区域从 820px 收窄为 700px。直接修改现有 Chakra 布局属性，不追加覆盖样式。
- 保留五项运行指标、原版 Chakra 主题、证书、端口、使用系数、启用开关、保存、删除和住宅出口管理；手机端仍按视口宽度收缩。
- API、数据库、Node 通道及部署配置均无变更，无需更新 Marzban-Node。先由 Actions 构建并核对 GHCR revision，再用于服务器验收，不标记为稳定版。

## 历史片段 4

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## mrshaw-v0.8.4-preview.2（2026-09-30，服务器验收预览版）

- 节点弹窗最大宽度由 1360px 改为 1040px，保持手机端视口内宽度；修正节点运行指标的布局，五张卡片从蓝色区块左侧开始排列、最大宽度 820px，中等宽度自动换行。原有证书、端口、节点表单和住宅出口管理不变。
- 新增 `MR_SHAW_API_AND_RELEASE.md`，明确环境变量、受保护 API、Node 内部通道及每次更新的文档/测试/镜像发布流程。本次没有改变任何 API 请求或响应。
- 本地 TypeScript/Vite 构建、17 项后端单元测试和差异空白检查通过。此次仅调整前端及文档，没有 API、数据库结构或 Node 通道变更；无需更新 Node。
- 配对 Node 基线：`kissow/Marzban-node` 的 `3e9b92e590a1c3c81af59b08d620f4a6209f2b71`。主面板镜像以本次合并提交及成功 Actions 的 OCI revision/digest 为准，不把构建排队当作发布成功。
- 用户要求先构建并在现有服务器验收本次布局；桌面/手机实际截图尚待服务器反馈，不标记为稳定版。已有部署使用 Fork 的 `marzban update`，先确认自动备份成功，保留数据库、用户、证书、端口、`.env` 和住宅代理配置。

## 历史片段 5

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## mrshaw-v0.8.4-preview.1（2026-09-30，预览版）

- 节点设置弹窗改为最大约 1360px 的响应式宽版，保留原有证书、端口、启用开关、保存和删除等官方 Chakra 界面功能。
- 节点运行状态显示 CPU、内存、磁盘、运行时间、活跃用户五项；宽屏五列、手机端两列。没有可靠节点级来源时，活跃用户显示不可用，不虚构数量。
- 本地前端构建已通过；真实 Linux Node、Xray 和测试数据库迁移仍需验收，暂不建议直接用于生产环境。
