# 浏览器翻译兼容：历史发布记录

[当前说明](../BROWSER_TRANSLATION.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261007-BROWSER-TRANSLATION（镜像已发布，服务器验收待完成）

HTML/body 浏览器翻译保护覆盖 React 根与 Chakra Portal；主机设置的加载/空列表文字由原 Text 组件包裹，避免外部翻译替换文本后卸载崩溃。原主题、宽度、表单、四语言与所有配置保留；无 API/数据库/Node/scripts/Xray 变化。PR #14 / 96599563 合入、正式 Actions 37494615636 成功，latest 双架构摘要/revision 已核对；既有 Fork 主控 marzban update 后重新加载页面，Node 无需更新。服务器和实际翻译服务验收仍待用户执行。[详细记录](../BROWSER_TRANSLATION.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-07 — MR-20261007-BROWSER-TRANSLATION（镜像已发布，服务器验收待完成）

- 用户确认浏览器翻译开启时，主机设置/入站出现 React removeChild DOM 异常。
- HTML/body 增加 translate=no / notranslate，head 增加 Google 翻译 opt-out；保留原 i18next 四语言，覆盖 body-mounted Portal，而不只保护 root。
- 原 HostsDialog 两个动态状态文字增加 Text as=span；不修改主题、宽度、协议、证书或字段，不覆写全局 DOM 方法吞掉错误。
- 新增 6 项源码/生产 JSX 渲染回归，与原 34 项语言测试合并执行；PR 工作流增加同一测试闸门。类型与生产构建通过，真实原组件浏览器回归证据见专门记录。
- API/数据库/Node/scripts/认证通道/设备策略/Xray v26.3.27 无变化；仅更新主控镜像。
- 源 7a0db490、PR #14 / Linux CI 37494129629 成功；合入 master 96599563、正式 Actions 37494615636 成功（116/116、40/40、类型/构建）。latest index sha256:6838f71ea0e3b97baa1cb217bb83d1f0b1acbb63466fe1e1863a2130220c2d45 与双架构 manifest/config/OCI revision 核对通过。服务器验收待执行；发布证据回写仅文档 [skip ci]，不重建镜像。[精确摘要、更新命令、边界与验收](../BROWSER_TRANSLATION.md)。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261007-BROWSER-TRANSLATION（展示兼容，镜像已发布、服务器待验收）

无接口、字段、认证、迁移、命令新增/删除。原 GET /api/hosts、PUT /api/hosts 及 GET /api/inbounds 的请求/响应/权限不变；只保护浏览器 DOM 和包装两个动态状态文本。Node REST/RPyC/HWID/UDP 与正式 Xray v26.3.27 不变；Node/scripts 不需配对更新。PR #14 合入 96599563、正式 Actions 37494615636 成功，latest 双架构摘要/OCI revision 已核对。既有 Fork 主控使用 marzban update 后重新加载页面；面板原语言菜单保留，服务器验收待执行。[源码、测试、精确摘要和上线验收边界](../BROWSER_TRANSLATION.md)。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261007-BROWSER-TRANSLATION（镜像已发布，服务器验收待完成）

- [x] 只修改原 HTML 翻译声明及 HostsDialog 动态文本包装；主题/宽度/表单/协议保留，无全局 DOM 异常吞掉补丁。
- [x] 前端语言与翻译保护回归 40/40，TypeScript 与生产构建通过；PR CI 加入同一测试命令。
- [x] 固定项目入口完整后端 116/116 与 Check/diff 通过；现有弃用提示保留，后端无修改。
- [x] 原组件浏览器模拟文本替换后状态切换/开关 10 轮，四语言及 1280px/390px 宽度/截图核对通过；无 pageerror/removeChild，保留已有开发嵌套按钮警告，非实际线上翻译验收。
- [x] README/功能/更新/API/流程及工作区 05/08/09 同步；Node/scripts 明确无变化。
- [x] 修复上传并经 PR #14 合入 96599563；PR CI 37494129629、正式 Actions 37494615636 成功；latest index/双架构 manifest/config/revision 已核对。
- [ ] 服务器更新、本轮运行 revision 核对及真实浏览器翻译验收；发布不等于部署/验收。

[详细记录和 SSH 更新命令](../BROWSER_TRANSLATION.md)。本轮修复镜像已发布，Node 不需更新；仅文档回写 [skip ci] 不改变运行时 revision。历史镜像不代替本轮摘要。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261007-BROWSER-TRANSLATION（镜像已发布，服务器验收待完成）

浏览器翻译 opt-out 与原 HostsDialog 动态状态文本包装；原主题、宽度、四语言和表单保留。主控 hosts/inbounds API、数据、证书、端口、Node 协议、HWID/UDP、Xray v26.3.27 不变，Node/scripts 无本轮运行时或命令变化。本地/干净 Linux 前端 40/40、后端 116/116、TypeScript/生产构建通过；PR #14 合入 96599563、正式 Actions 37494615636 成功，latest index/双架构 OCI revision 已核对。服务器验收待执行，不能用历史发布摘要代替；仅文档 [skip ci] 回写不重建镜像。[本轮精确证据和范围](../BROWSER_TRANSLATION.md)。
