# 网站接入：用户到期时间与流量 API

本页列出的新接口尚未随主控镜像发布。不要把未部署这些路径的实例接入生产付款链路。既有面板接口见[旧版本兼容方式](#旧版本兼容方式)。本接口不绑定任何网站、支付渠道或订阅系统。

## 接入前准备

- 由网站后端通过 HTTPS 请求自己的 Marzban 主控。不要让浏览器、小程序或客户端拿到管理员令牌、面板密码或其他用户的订阅链接。
- 网站保存「网站用户 ID → Marzban 用户名」的关系；先在自己的网站校验已登录用户确实拥有该账号，再用对应的用户名调用。不要允许前端指定任意面板用户名。
- 推荐专用普通管理员，只授予其名下用户的管理权。超级管理员的误重置补回权限不用于网站正常开通或续费。
- 使用既有 `POST /api/admin/token` 登录，表单类型为 `application/x-www-form-urlencoded`，字段为 `username`、`password`。在后续请求头发送 `Authorization: Bearer <access_token>`。认证信息以及完整订阅 URL 不进入日志或公开错误响应。

下文的 `panel.example.invalid`、`example_user` 和日期都是示例，请替换为测试实例和测试账户。

## 读取用户信息

```http
GET /api/user/example_user/entitlement
Host: panel.example.invalid
Authorization: Bearer <access_token>
```

示例响应：

```json
{
  "username": "example_user",
  "state": {
    "expires_at": 1893456000,
    "quota_bytes": "107374182400",
    "used_bytes": "45097156608",
    "remaining_bytes": "62277025792",
    "status": "active",
    "reset_strategy": "no_reset",
    "has_next_plan": false
  },
  "latest_reset": null,
  "can_restore": false
}
```

| 字段 | 网站怎么用 |
| --- | --- |
| `state.expires_at` | UTC Unix 秒，`null` 表示无固定到期；显示时按访问者时区转换。不要从它反推开通日期或付款周期。 |
| `state.quota_bytes` / `used_bytes` / `remaining_bytes` | 精确字节字符串；不限额时额度与剩余为 `null`，已用仍可读取。展示可换算成 GiB，计算请用整数或任意精度类型，不要用 JS 浮点数保存精确账目。 |
| `state.status` | `active` 可用、`limited` 流量受限、`expired` 到期、`disabled` 被禁用、`on_hold` 等待激活。判断服务状态不要只看剩余天数。 |
| `state.reset_strategy` / `has_next_plan` | `no_reset` 只禁止面板定时清零；如果存在「下一套餐」，它仍可能触发换期。接管前单独核对，不自动删除。 |
| `latest_reset` | 最近一条重置，可能为 `null`；旧记录的 `origin: "unrecorded"` 不代表能确定是谁发起。 |

需要历史累计或向本人展示订阅入口时，使用既有 `GET /api/user/{username}` 的 `lifetime_used_traffic` 或 `subscription_url`。不要把 `lifetime_used_traffic` 当作本期用量，也不要把包含协议凭据的完整响应直接返回前端。

## 付款后如何设置

本 API 只负责面板端的设置。由网站后端确认订单状态、计算准确时间，并用已绑定的 Marzban 用户名发起调用。不要把订单号、支付详情、凭证或个人信息写进面板的补回原因。账号绑定检查通过后，再选择操作：

| 业务操作 | 预览的请求体 | 作用 |
| --- | --- | --- |
| 只延长时间 | `{"action":"extend","expires_at":1893456000}` | 必须比当前有限到期时间更晚，也在未来。已用和总额度不变；已用完仍受限。 |
| 单独加 10 GiB | `{"action":"add","extra_bytes":"10737418240"}` | 给现有有限额度增加字节数；不改已用或到期。 |
| 明确开始新的计量周期 | `{"action":"renew"}` 或 `{"action":"renew","expires_at":1893456000}` | 显式将本期用量归零、保留历史。不能把普通延期映射成这个操作。 |

### 示例：网站后台增加流量

1. 只读预览：

   ```http
   POST /api/user/example_user/entitlement/preview
   Host: panel.example.invalid
   Authorization: Bearer <access_token>
   Content-Type: application/json

   {"action":"add","extra_bytes":"10737418240"}
   ```

2. 检查响应的 `before`、`after`，取得 `guard`。在网站数据库按已确认的业务事件与用户保存一个唯一 UUID 和完整提交体，再发送：

   ```http
   POST /api/user/example_user/entitlement/operations
   Host: panel.example.invalid
   Authorization: Bearer <access_token>
   Content-Type: application/json

   {
     "operation_id": "23ddf502-ed02-4d51-81c5-efacf59108ac",
     "guard": "<从本次预览原样复制>",
     "command": {"action":"add","extra_bytes":"10737418240"},
     "confirmed": false
   }
   ```

   延期使用同样流程，只替换命令。只有已明确决定换计量期时，才发送 `renew` 和 `confirmed: true`。网站不应暴露通用的超级管理员补回入口。

3. 收到成功回执后，核对 `operation_id`、`action`、`username` 和 `after`，网站再标记该操作完成。实际流量计数可能在预览与落库之间增长；以回执为准。要展示最新状态，再用概览 GET 回读，不把旧回执当作实时用量。

重试时**不能生成新 UUID**。遇到超时或暂时无法确认，查询：

```http
GET /api/user/example_user/entitlement/operations/23ddf502-ed02-4d51-81c5-efacf59108ac
Host: panel.example.invalid
Authorization: Bearer <access_token>
```

| 结果 | 处理 |
| --- | --- |
| 200，收到原回执 | 核对后结单，不再写入。 |
| 404 且 `detail.code = "receipt_not_found"` | 若之前确已提交过，可按原 UUID 和完全相同的请求体重试。其他 404 先核对版本、路径与账户，不按回执不存在处理。 |
| `entitlement_changed` | 停止本次写入，重新预览并核对订单和账号状态。此前若有未知提交，先查原回执。 |
| `operation_conflict` | 原编号的请求体或目标不一致，停止并核对；不要自动用新编号绕过。 |
| 401 / 403 / 422 | 分别核对登录令牌、用户归属/权限和请求字段。 |
| 超时或 `database_busy` | 结果可能未知，按原回执流程查证。不要回退到旧的非幂等清零接口。 |

同账号的多笔写入应串行发送。一个网站订单如果确实要做「延期 + 增额」，它是两项独立操作，各有各的回执；不能当作一次原子事务，也不能把增额实现成清零。

## 旧版本兼容方式

如果尚未部署此功能，既有 `GET /api/user/{username}` 可读取 `status`、`expire`、`data_limit`、`used_traffic`、`lifetime_used_traffic`。已有 `PUT /api/user/{username}` 使用 `expire`（UTC 秒）设置准确到期时间；`data_limit` 是绝对上限，不是增额。旧版本改用户之前要核对「下一套餐」兼容边界，见[外部订阅控制](EXTERNAL_SUBSCRIPTION_CONTROL.md)。

不要在未确认支持新接口的面板上自动退回到「读取当前上限后再用 PUT 加算」或调用旧 reset；前者不保证并发安全，后者没有同一操作回执。上线时先用测试账号执行一次只读概览、预览和回执回读，再开启真实业务写入。面板人工操作和误重置恢复限制见[用户时间与流量](NATIVE_USER_ENTITLEMENT.md)。
