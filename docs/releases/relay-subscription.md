# 中转订阅身份：历史发布记录

[当前说明](../NODE_RELAY_SUBSCRIPTION.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)。

---

## MR-20261007-RELAY-INTERNAL-SUBSCRIPTION（本地修复，未发布）

保留原订阅别名/数量/顺序，匹配 Node 时只换地址与端口，不新增中转条目；关闭恢复直连。原 Hosts、证书、用户凭据和转发进程不改，short ID 按输出副本处理。Node/scripts 无变化；Node→Node 当前未实现。[行为、兼容与验证](../NODE_RELAY_SUBSCRIPTION.md)。

## 历史片段 2

原位置：[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)。

---

## 2026-10-07 — MR-20261007-RELAY-INTERNAL-SUBSCRIPTION（本地修复，未发布）

- 原条目内部切换中转端点，保留别名/数量/参数，不追加 Relay 或暴露管理端名称作为别名。
- 无匹配/混合地址/歧义目标校验，旧歧义行报错、失败保持原输出；首次 short ID 输出和共享对象修改修复。
- 原组件只更新路径说明、占位和四语言，无主题/结构变化；149/149 后端两轮、45/45 前端及类型/构建检查通过。Node/scripts、迁移、核心与端口不变；未推送、Actions/新镜像/服务器验收未完成。[详情](../NODE_RELAY_SUBSCRIPTION.md)。

## 历史片段 3

原位置：[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)。

---

## MR-20261007-RELAY-INTERNAL-SUBSCRIPTION（合同兼容，本地未发布）

四个既有 relay API 的权限、路径、请求和响应字段不变；PUT 新增无匹配 Host/混合地址/业务目的地歧义 422 校验。原 Hosts 持久化保留，订阅输出仅换已匹配条目的端点，别名/数量不变，不再额外输出 Relay。source 仍仅 main；Node→Node 未实现。无迁移/Node协议/scripts命令变化，Node 不需更新。[完整匹配规则、错误、回退与验证](../NODE_RELAY_SUBSCRIPTION.md)。

## 历史片段 4

原位置：[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)。

---

## MR-20261007-RELAY-INTERNAL-SUBSCRIPTION（本地测试完成，未发布）

- [x] 原别名/条目数、双Node/直连恢复/十轮保存、参数/HWID凭据、匹配/歧义/回滚与首次short ID回归。
- [x] 最终代码后端两轮149/149，含两项固定Xray真实进程；前端45/45、TypeScript/Vite、pip check、固定入口/diff通过。既有utcnow/Pydantic弃用与大chunk警告非零失败。
- [x] README/功能/更新/接口/流程与工作区05/08/09登记；Node/scripts无变更、不需更新。
- [ ] 原组件实际预览审阅（前次浏览器策略阻止，未绕过），授权推送、Linux CI、镜像构建/双架构验证。
- [ ] 服务器更新、客户端刷新旧项/别名数量/出口/持续访问验收。用户已报告旧Relay可用，不代替本轮验收。

[本轮合同和边界](../NODE_RELAY_SUBSCRIPTION.md)。Node→Node仅可行性说明，未实现。

## 历史片段 5

原位置：[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261007-RELAY-INTERNAL-SUBSCRIPTION（本地完成，未发布）

订阅按原 Host 精确匹配，仅换地址/端口，不追加中转条目或重命名。原存储和转发保持，short ID 使用输出副本；API新增校验不新增字段/迁移。最终后端149/149两轮、前端45/45、类型/构建/依赖/diff通过。Node/scripts无变化，不需服务器更新。Node→Node作为后续扩展，当前source仍仅main。公开文档和工作区05/08/09已更新；本次尚未推送/构建/验收，不复用d2350203旧镜像作为修复证据。[合同和发布门槛](../NODE_RELAY_SUBSCRIPTION.md)。
