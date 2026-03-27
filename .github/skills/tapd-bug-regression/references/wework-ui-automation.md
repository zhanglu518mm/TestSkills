### 企业微信JSSDK初始化

接口概述

功能： 搜索指定的企业微信联系人/群聊, 打开聊天会话，并完成JSSDK的初始化，以支持后续的JSSDK调用（如分享素材/发送消息给微信客户）。

接口地址： http://127.0.0.1:8373/api/wxwork/contacts/jssdk
请求方法： POST
Content-Type： application/json

---

请求参数

| 参数名      | 类型   | 必需 | 默认值  | 说明         |
|-------------|--------|------|---------|------------|
| name        | string | ✅   | -       | 联系人或群聊名称   |
| type        | string | ❌   | null    | 目标类型，可选值见下表 |
| buttonLabel | string | ❌   | "JSSDK" | 要点击的按钮标签文字 |

type 参数详细说明

| type 值          | 搜索标签 | 匹配规则                          | 使用场景             |
|------------------|----------|-----------------------------------|----------------------|
| null (不传)      | 全部     | 匹配 name                         | 不确定目标类型时使用 |
| "contact_wechat" | 联系人   | 匹配 name@微信                    | 搜索微信联系人       |
| "group"          | 群聊     | 匹配 name（多个同名时选第一个）   | 搜索群聊             |

---
响应格式

成功响应 (200 OK)
```json
{"result": true}
```

| 字段   | 类型    | 说明                                  |
|--------|---------|---------------------------------------|
| result | boolean | true = 成功打开页面；false = 执行失败 |

错误响应

| HTTP 状态码 | 错误代码          | 说明             |
|-------------|-------------------|----------------|
| 400         | INVALID_TYPE      | type 参数值不合法    |
| 500         | APP_LAUNCH_FAILED | 企业微信应用启动失败     |
| 500         | INTERNAL_ERROR    | 服务器内部错误        |
| 504         | TIMEOUT           | 执行超时（默认 180 秒） |

错误响应格式：
```json
{"error": "错误描述信息", "code": "ERROR_CODE"}
```

---

curl 命令示例

示例 1：打开与微信联系人“张三”的会话。注意不要省略"-s"参数
```
curl -X POST http://127.0.0.1:8373/api/wxwork/contacts/jssdk -H "Content-Type: application/json" -s -d '{"type": "contact_wechat", "name": "张三"}'
```
注意： buttonLabel 省略时默认为 "JSSDK"

---

示例 2：打开名称为“技术讨论组”的群聊会话。注意不要省略"-s"参数
```
curl -X POST http://127.0.0.1:8373/api/wxwork/contacts/jssdk -H "Content-Type: application/json" -s -d '{"type": "group", "name": "技术讨论组"}'
```
---
执行流程说明

接口调用后会按照以下步骤执行：

1. 启动企业微信应用首页（通过 ADB Activity 启动）
2. 导航到通讯录 -> 我的客户 -> 微信客户
3. 点击目标客户，在打开的详情页点击“发消息”，打开会话。
4. 点击 侧边栏 按钮, 打开侧边栏（点击聊天输入框上方的 buttonLabel 按钮）


### 企业微信删除微信好友

接口概述

功能： 从企业微信的"我的客户"中删除指定的微信联系人。

接口地址： http://127.0.0.1:8373/api/wxwork/contacts/remove
请求方法： POST
Content-Type： application/json

---

请求参数

| 参数名 | 类型   | 必需 | 默认值 | 说明                   |
|--------|--------|------|--------|------------------------|
| name   | string | ✅   | -      | 要删除的微信联系人名称 |

---

响应格式

成功响应 (200 OK)
```json
{
  "success": true,
  "message": "Contact '张三' has been removed successfully"
}
```

| 字段   | 类型    | 说明                                                      |
|--------|---------|-----------------------------------------------------------|
| success| boolean | true = 删除成功；false = 删除失败                         |
| message| string  | 操作结果描述信息                                          |

删除失败但联系人不存在时（视为已删除）：
```json
{
  "success": true,
  "message": "Contact '张三' not found (may already be deleted)"
}
```

错误响应

| HTTP 状态码 | 错误代码       | 说明             |
|-------------|----------------|------------------|
| 500         | INTERNAL_ERROR | 服务器内部错误   |
| 504         | TIMEOUT        | 执行超时         |

错误响应格式：
```json
{"error": "错误描述信息", "code": "ERROR_CODE"}
```

---

curl 命令示例

示例 1：删除名为"张三"的微信联系人。注意不要省略"-s"参数
```
curl -X POST http://127.0.0.1:8373/api/wxwork/contacts/remove -H "Content-Type: application/json" -s -d '{"name": "张三"}'
```

---

执行流程说明

接口调用后会按照以下步骤执行：

1. 启动企业微信应用首页（通过 ADB Activity 启动）
2. 导航到 通讯录 -> 我的客户
3. 切换到"微信客户"标签页
4. 查找并点击目标联系人
5. 在客户详情页点击右上角菜单按钮（三点）
6. 在个人信息页点击"删除"按钮
7. 在确认对话框中点击"确认删除"
8. 验证删除成功（检测"删除成功"提示或返回客户列表后确认联系人不存在）
