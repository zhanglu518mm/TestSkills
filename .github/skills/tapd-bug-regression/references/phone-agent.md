# 安卓手机操作智能体

此电脑已经连接了安卓设备，你可以通过`adb`实现文件上传等操作，也可以通过`PhoneAgent` 操作微信实现复杂多步任务，如"微信发送消息"、"微信添加活码"等操作。
注意在调用`PhoneAgent`前，必须先调用`adb shell input keyevent KEYCODE_HOME`切换到桌面首页。

### adb
系统环境变量PATH中已经添加了adb所在的目录，你可以通过`adb`实现文件操作，如将下载的活码图片保存到手机。

#### 示例1: 将本地活码图片保存到手机相册中。假设本地文件路径为"~/Downloads/qr_code.png"

1. 将文件推送到手机的 Pictures 目录
   adb push ~/Downloads/qr_code.png /sdcard/Pictures/

2. 触发媒体扫描，让图库应用识别新图片
   adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Pictures/qr_code.png

#### 示例2: 按下HOME键，返回到桌面主页
adb shell input keyevent KEYCODE_HOME

#### 示例3: 打开应用首页并清除页面栈
如果希望打开某个应用（如"微信"、"企业微信"），则需要先打开应用首页，为避免应用首页已经打开且存在页面栈，通过`adb shell am start -n {componentName} -f 0x10008000`实现清空栈并启动首页。
1. 打开企业微信首页
   adb shell am start -n com.tencent.wework/.launch.LaunchSplashActivity -f 0x10008000

2. 打开微信首页
   adb shell am start -n com.tencent.mm/.ui.LauncherUI -f 0x10008000


### PhoneAgent

介绍：通过 AI 视觉模型自动操作手机完成任务，并返回结构化的执行结果。使用者通过调用 phone-agent api接口实现。

注意执行此接口前，必须先调用`adb shell input keyevent KEYCODE_HOME`切换到手机桌面首页。
如果需要打开微信或企业微信首页，则参考"示例3: 打开应用首页并清除页面栈"中的例子，打开应用并清除页面栈，然后再调用`phone-agent`接口。

接口地址：http://127.0.0.1:8373/api/phone-agent
请求方法：POST
Content-Type：application/json

---

请求参数

| 参数名          | 类型   | 必需 | 默认值 | 说明                  |
|-----------------|--------|------|-----|---------------------|
| command         | string | ✅   | -   | 要执行的任务指令（自然语言描述）    |
| timeout_seconds | int    | ❌   | 180 | 执行超时时间（秒），范围：60-600 |

参数说明

- **command**：支持任何自然语言描述的任务指令，例如：
    - "打开微信"
    - "查看当前页面的标题文字"
    - "在美团搜索附近的火锅店"
    - "截图保存当前页面"

- **timeout_seconds**：PhoneAgent 执行任务的最大等待时间
    - 最小值：60 秒
    - 最大值：600 秒（10 分钟）
    - 默认值：180 秒（3 分钟）
    - 建议：简单任务使用默认值，复杂多步骤任务可适当增加

---

响应格式

成功响应 (200 OK)

```json
{
  "result": "执行结果内容"
}
```

| 字段   | 类型   | 说明                                          |
|--------|--------|-----------------------------------------------|
| result | string | PhoneAgent 执行后返回的结果，从 AI 输出中自动提取 |

响应示例

```json
{
  "result": "微信已成功打开，当前位于\"消息\"页面"
}
```

错误响应

| HTTP 状态码 | 错误代码         | 说明                                    |
|-------------|------------------|-----------------------------------------|
| 400         | RESULT_NOT_FOUND | 执行完成但未找到 <result></result> 标签 |
| 500         | INTERNAL_ERROR   | 服务器内部错误                          |
| 504         | TIMEOUT          | 执行超时（超过 timeout_seconds 设定值） |

错误响应格式：
```json
{
  "error": "错误描述信息",
  "code": "ERROR_CODE"
}
```

---

curl 命令示例

示例 1：通过微信扫描活码（企业微信员工二维码）。注意不要省略 "-s" 参数
需要分三步完成：
1. 微信扫描活码加企微好友之前需要先在企业微信上删除微信好友
2. 在微信上删除企业微信好友之后，再扫码添加。互删好友后，微信扫码添加好友才会下发“欢迎语”。
3. 先通过上述"adb"章节说明将二维码上传到手机相册
4. 扫码添加好友。注意`command`中的从系统相册选择活码图片步骤说明需要和示例一致（选择第一张二维码图片），不能要求选择指定的文件名（如qr_code.png)，系统相册不能根据文件名称过滤。

```bash
# 1. 企业微信删除微信好友, 假设{{目标微信客户}}为“张三”
adb shell input keyevent KEYCODE_HOME
curl -X POST http://127.0.0.1:8373/api/wxwork/contacts/remove -H "Content-Type: application/json" -s -d '{"name": "张三"}'

# 2. 微信删除企业微信好友
adb shell input keyevent KEYCODE_HOME
curl -X POST http://127.0.0.1:8373/api/phone-agent -H "Content-Type: application/json" -s -d '{"command": "打开微信主页，在通讯录中搜索联系人\"智升测试\"，打开联系人详情页，查看是否有删除好友的选项。如果有，点击删除并确认；如果没有，说明已经删除了好友。返回操作结果。","timeout_seconds": 180}'

# 3. adb 上传电脑图片到手机相册，假设本地图片地址为 ~/Downloads/qr_code.png
adb push ~/Downloads/qr_code.png /sdcard/Pictures/
adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Pictures/qr_code.png

# 4. 扫码添加好友
adb shell input keyevent KEYCODE_HOME
curl -X POST http://127.0.0.1:8373/api/phone-agent -H "Content-Type: application/json" -s -d '{"command": "打开微信主页，选中底部的第一个TAB'微信'，点击顶部标题栏右侧的'+'，选择'扫一扫'，从系统相册中选择第一张二维码图片，显示出联系人信息，点击页面底部的'添加到通讯录'按钮，添加好友。如果页面底部没有'添加到通讯录'按钮，则说明是已经添加完好友了，需要先执行删除好友操作，然后重新执行扫一扫添加好友步骤。","timeout_seconds": 300}'
```

**预期响应：**
```json
{
  "result": "已添加好友"
}
```

---

示例 2：查询微信应用中与"XXX"聊天会话最后一条消息。注意不要省略 "-s" 参数

```bash
adb shell input keyevent KEYCODE_HOME
curl -X POST http://127.0.0.1:8373/api/phone-agent -H "Content-Type: application/json" -s -d '{"command": "打开微信主页，在'微信'TAB页中找到与'XXX'的聊天会话，点击打开，描述页面底部最后一条消息内容。如果是如卡片类型的消息（如链接、文件），不要点击打开卡片，只需要描述卡片上的文本内容即可。"}'
```

**预期响应：**
```json
{
  "result": "我打开了会话页面，最后一条消息内容为：...."
}
```

---

示例 3：在微信上删除"智升测试"企业微信联系人。注意不要省略 "-s" 参数

```bash
curl -X POST http://127.0.0.1:8373/api/phone-agent -H "Content-Type: application/json" -s -d '{"command": "打开微信主页，在通讯录中搜索联系人\"智升测试\"，打开联系人详情页，查看是否有删除好友的选项。如果有，点击删除并确认；如果没有，说明已经删除了好友。返回操作结果。","timeout_seconds": 180}'
```

**预期响应：**
```json
{
  "result": "成功删除了好友\"智升测试\""
}
```

---

使用建议

1. **任务描述清晰具体**：提供明确的步骤和预期结果，例如 "打开微信，进入通讯录，查找张三" 比 "找人" 更好
2. **合理设置超时**：
    - 简单操作（打开应用、点击按钮）：120 秒
    - 中等复杂度（搜索+导航）：180 秒
    - 复杂多步骤任务：300 秒
3. **结构化结果请求**：在 command 中明确要求返回的信息格式，例如 "查找联系人张三，返回其电话号码"
4. **错误重试**：遇到 TIMEOUT 错误时，可以增加 timeout_seconds 后重试
