# 多语言与手机布局：历史发布记录

[当前说明](../DASHBOARD_I18N_MOBILE.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-DASHBOARD-I18N-MOBILE：多语言与手机入站弹窗（镜像已发布，服务器/视觉验收待完成）

在原 React/Chakra 组件内完善四种语言文案、在线/到期时间、日历、状态筛选及原表单校验；保留技术名称与 API 枚举。设置入站桌面 440px，手机最大为视口减 24px，长标题/原帮助/操作行可换行。主题、协议、证书、端口、数据、HWID/UDP、Xray v26.3.27 不变；Node/scripts 无本轮变化或更新要求。

本地/Linux CI 语言回归 34/34、主控回归 95/95、类型和构建通过；PR #11 合入 `56552130`、Actions `37353281396` 成功，latest 双架构 digest/OCI revision 已核对。实际浏览器视觉和服务器验收待完成，不宣称稳定上线。[详情及更新命令](../DASHBOARD_I18N_MOBILE.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## MR-DASHBOARD-I18N-MOBILE（镜像已发布，服务器/视觉验收待完成）

- 修复选择语言后在线/到期、状态筛选、日历与部分提示仍为英语，补齐原四语言词典/复数。
- 修复状态筛选值误绑定 sort，传给 API 的 status 枚举不变；原 hosts 必填提示在验证时读取当前语言。
- 原入站弹窗桌面保持 440px、手机左右留 12px；内容随容器收窄，长标题/帮助/原操作行换行。
- 新增 34 项回归并接入原 CI，本地主控 95 项、TypeScript、生产与原组件预览构建通过。
- 无 API/schema/认证/端口/证书/Node/scripts/Xray 变化，无新外部源码借入；原主题与作者归属保留。
- PR #11 已合并为 `5655213099c18532ff3daff5cead010c181a19e9`；分支 Actions `37352009623` 和正式 Actions `37353281396` 成功（Linux 95/95、语言 34/34、类型/生产构建与 Xray 闸门通过）。latest index `sha256:793c61738cf18f8641c2ce4b86037a41064903b7e59e4c49a296f8121c2947ce`，两架构 digest/OCI revision 已核对。
- 镜像推送日志为 `2026-10-05T18:16:26Z`（UTC，香港 2026-10-06）。浏览器安全策略校验无法授权，实际手机视觉与服务器验收待完成；不是稳定发布声明。详情 `docs/DASHBOARD_I18N_MOBILE.md`；发布证据仅文档回写使用 `[skip ci]`，不重复构建运行时代码。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-DASHBOARD-I18N-MOBILE：展示层修复，接口不变（镜像已发布，服务器/视觉验收待完成）

`GET /api/users` status 查询仍用 `active/on_hold/disabled/limited/expired`，只翻译显示文案。`GET /api/hosts`、`PUT /api/hosts` 请求/响应/管理员权限及端口转换不变；必填提示只是前端本地化。无接口新增删除、认证变更或数据库迁移。Node REST/RPyC、健康/设备策略协议及部署命令不变，Node/scripts 不需本轮更新；Xray v26.3.27 不变。

本地/Linux CI 语言 34/34、主控 95/95、TypeScript/构建通过。PR #11 合入 `56552130`，Actions `37353281396` 成功，latest 双架构摘要和 OCI revision 已核对；已切换 Fork 的主控使用 `marzban update`，Node 不需更新。响应式源代码约束测试不是实际浏览器验收，服务器/视觉验收仍待完成。[完整发布证据](../DASHBOARD_I18N_MOBILE.md)。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-DASHBOARD-I18N-MOBILE（镜像已发布，服务器/视觉验收待完成）

- [x] 原 React/Chakra 局部修改，主题、协议、证书、端口、数据保留。
- [x] 四语言/时间/原表单/API 枚举/响应式源代码约束回归 34/34；主控完整回归 95/95。
- [x] TypeScript、生产与原组件预览构建通过；README/功能/更新/API 文档与工作区 05/08/09 补充。
- [ ] 原组件实际浏览器 320/375/390px、桌面、深浅主题视觉核对。当前安全策略校验无法授权，不能用代码测试代替。
- [x] 2026-10-06 用户明确要求上传/构建，授权先发布；实际视觉验收仍待完成，未登记为通过。
- [x] PR #11 合入 master `5655213099c18532ff3daff5cead010c181a19e9`；正式 Actions `37353281396` 成功（Linux 95/95、语言 34/34、类型/构建及 Xray 版本闸门）。
- [x] GHCR latest index `sha256:793c61738cf18f8641c2ce4b86037a41064903b7e59e4c49a296f8121c2947ce`；两架构 manifest/config 原始字节哈希、OCI revision 与核对前后 latest 一致，完整证据见详情。
- [ ] 服务器备份/更新、镜像 revision、四语言切换、手机原入站字段/帮助/保存/关闭真实验收。

Node/scripts 无变化、不需本轮更新；本次镜像已发布，不沿用历史镜像证据。文档证据回写 `[skip ci]` 不改变已核对镜像。[详情](../DASHBOARD_I18N_MOBILE.md)。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/heyinkcode/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-DASHBOARD-I18N-MOBILE（镜像已发布，服务器/视觉验收待完成）

主控原前端四语言与手机入站宽度修复；Node/scripts 无代码/协议/命令变化。API/迁移为“无”：status 英文枚举与 hosts GET/PUT 合同不变。本地语言 34/34、主控 95/95、TypeScript/生产/原组件预览构建通过。

2026-10-06 用户明确要求上传/构建，按授权先发布；浏览器安全策略校验无法授权，实际原组件视觉验收仍待完成，不登记为通过。发布前复核与 Linux CI 34/34、95/95、类型及生产构建通过；PR #11 合入 `56552130`、Actions `37353281396` 成功，latest 双架构 digest/OCI revision 已核对。服务器验收待完成；文档证据回写使用 `[skip ci]`，镜像 revision 仍为运行时合并提交，不冒充文档提交。[完整证据与更新命令](../DASHBOARD_I18N_MOBILE.md)。
