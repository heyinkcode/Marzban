# 浏览器翻译兼容与语言切换

面板内置中文、英文、俄文和波斯文。请使用面板语言菜单；浏览器强制翻译可能改写页面元素，导致主机/入站弹窗异常。以下说明兼容保护和排查方式，不改变后端接口。

## 原因和源码依据

用户确认关闭浏览器翻译后，主机设置/入站弹窗恢复正常。这里的 Node 是浏览器 DOM 元素，不是 Marzban-Node。HostsDialog 的加载和无入站状态此前直接输出条件文本；翻译工具替换 React 管理的文本节点后，React 再移除旧节点会遇到 NotFoundError/removeChild。

参考 [React issue #11538](https://github.com/facebook/react/issues/11538) 与 [HTML translate 属性规范](https://html.spec.whatwg.org/multipage/dom.html#the-translate-attribute)。本轮自行在原组件实现兼容保护，没有复制第三方补丁代码；保留上游许可证和致谢。

## 修复与边界

1. 原 index.html 的 html/body 使用 translate=no 和 notranslate，head 使用 Google opt-out；声明在 React 加载之前生效，body 同时覆盖挂载到 root 外的 Chakra Modal/Popover Portal。
2. HostsDialog 原加载/无入站文本使用 Text as=span；翻译替换 span 内部文字后，状态切换删除的是 React 保留的 span 外壳，不直接删除已经被替换的文本节点。
3. 原生 i18next en/zh/fa/ru 菜单继续可用，原主题、宽度、控件、协议、证书、端口、数据均保留。没有修改语言检测或用户此前未提交的语言代码。
4. 不改写 Node.prototype.removeChild/insertBefore，不吞掉其它真实 DOM 错误。翻译声明不是权限边界：强制改写整个元素、忽略 translate=no 的第三方扩展仍可能破坏页面；无法保证所有扩展兼容。受支持的语言切换方式是面板菜单。
5. 本修复对新加载的文档生效；已经被翻译破坏的旧标签页不能靠声明自动修复，升级后需要重新加载页面。

## API 和三仓库兼容

- GET /api/hosts、PUT /api/hosts、GET /api/inbounds 请求、响应、认证和副作用均不变；无新增/删除接口或字段。
- 数据库/订阅/认证/设备策略/HWID/UDP 不变；正式 Xray 保持 v26.3.27。
- Marzban：仅前端兼容与回归闸门，新主控镜像已发布，需要更新主控服务器。
- Marzban-node、Marzban-scripts：运行时、协议、安装/更新命令无变化，不需要本轮构建或服务器更新。

## 升级后检查

已有 Fork 仅更新主面板并重新加载页面，Node 和脚本不因本功能要求更新。检查语言菜单、主机设置、入站展开及手机布局；若只在强制翻译时失败，先关闭翻译并重新载入，再记录浏览器和扩展版本。不要禁用错误检查或改写全局 DOM 方法。

[更新流程](REPOSITORY_UPDATE_FLOW.md) · [历史测试与发布证据](releases/browser-translation-guide-20261015.md)
