# 主面板使用系数：历史发布记录

[当前说明](../MAIN_USAGE_COEFFICIENT.md) · [历史索引](README.md)

本文按功能保留原始发布证据。记录中的「当前」「最新」「未发布」「待验收」仅指原记录形成时的状态，不能替代当前说明或新的验收记录。旧流程和旧接口描述不是现行使用指引；重复正文合并并保留来源。整理日期：2026-10-15。

## 历史片段 1

原位置：[FORK_FEATURES.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/FORK_FEATURES.md)、[CHANGELOG.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/CHANGELOG.md)、[MR_SHAW_API_AND_RELEASE.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/MR_SHAW_API_AND_RELEASE.md)、[RELEASE_CHECKLIST.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/RELEASE_CHECKLIST.md)、[docs/REPOSITORY_UPDATE_FLOW.md](https://github.com/kissow/Marzban/blob/7987f8afb7c21d81e02d25ddbc72ad89150f9f83/docs/REPOSITORY_UPDATE_FLOW.md)。

---

## MR-20261008-MAIN-USAGE-COEFFICIENT（镜像已发布，服务器验收待完成）

原节点设置顶部新增独立「主面板（本机）」使用系数，默认1，范围大于0至1000、最多五位小数；只影响本机业务用户计费，不是网速倍率。已有用量不重算，Node系数/透明中转/实际网络统计保持原范围。四语言、原Chakra主题/宽度/证书/端口保留。新增sudo GET/PUT /api/node/main/usage，additive迁移a123bc45de67接9012ab34cd56；Node/scripts无本轮变化，不需更新，Xray v26.3.27不变。

[接口、取整/采集边界、兼容性与验收流程](../MAIN_USAGE_COEFFICIENT.md)。本地后端两轮182/182，专项18/18再三轮；前端54/54（含实际组件四语言SSR）、类型/构建/依赖/diff通过。用户已认可HTML提案，自动浏览器视觉验收未执行。源6f65298e、PR #19合并为15a11e9d5bdf884fa860456e3a4ae0602d6783b1；PR CI 37777207870与正式Actions 37777455474成功。latest index sha256:ed5d2641733126431104155f62a447390767f524525e7303f5bfc46741cb5f35，双架构manifest/config/revision核对通过。Node/scripts无需本轮更新；已切换Fork的主控用marzban update，服务器验收未执行。文档[skip ci]回写不改变运行时revision。
