# 移动端用例执行规则

## 员工端说明
员工端也称为"移动端"。
技术框架采用Vue3，采用vue-router路由，mode: 'history', base: '/workbench/';
注意如果测试用例中包含'/workbench?'形式的URL，在浏览器中打开时必须转为'/workbench/'，否则可能会打开失败。

## 员工端用例执行工作流
1. 步骤一：打开首页，注入用户身份
2. 步骤二：按照“页面进入步骤” 导航到目标页面。需区别是否为侧边栏场景。
    - 侧边栏场景：参考"企微入口"章节拼接URL，打开此页面。
    - 非侧边栏场景：从首页TAB或营销台TAB模块入口列表找到模块跳转入口。
3. 步骤三：按照“测试步骤”执行用例

## 重要规则
* 必须遵循正常页面交互原则实现测试用例中的页面交互操作，采用鼠标点击操作(`click`)/键盘操作(`fill`/`fill_form`/`hover`)/触控操作等普通用户常规交互方式，避免使用"Evaluate JavaScript"这种仅开发者使用的通过编写代码实现的调试方法。仅在正常交互方式不能解决问题时，才能使用"Evaluate JavaScript"，并在测试用例结果中记录使用了"Evaluate JavaScript"方式。
* 当前设备已经连接了Android手机，当需要在"微信"应用中操作时，如"微信扫码"、"微信客户发送消息给企微好友"、"在微信中验证收到消息"，按照手机操作智能体文档说明，通过"adb"与"PhoneAgent"实现微信操作

## 步骤一：打开首页，注入用户身份
根据"运行环境与域名"章节规中的介绍，得到当前运行环境对应的域名。下方用`{HOST}`代指域名。
严格按照 打开首页 -> 注入sessionStorage/localStorage信息 -> 刷新首页验证登录成功 步骤执行。具体步骤为：
首先通过playwright`browser_navigate`打开首页`{HOST}/workbench/?wsAuthMode=manual`，然后通过 "Run Playwright code" 工具注入信息到sessionStorage和localStorage。sessionStorage KEY为"module_version"，value为{CODE_VERSION}；localStorage KEY与值列表：AUTOMATION_TOKEN值为{TOKEN}；AUTOMATION_SWITCH值为1；如果测试用例对应的是侧边栏场景，需在localStorage中注入企业微信场景值，企业微信场景值KEY为AUTOMATION_JSAPI_ENTRY，值请参考"企业微信侧边栏场景值"章节设置值，默认为"normal"。注入信息后，刷新当前页面。如果TOKEN有效，可以在页面看到"首页"TAB文案。如果此时页面仍提示需要登录或XHR接口请求中有401错误，则代表TOKEN无效，流程中止。Run Playwright code 调用时传入的`code`参数示例：

```javascript
async (page) => {
    const token = '{TOKEN}'; // 将{TOKEN}替换为实际token
    const module_version = '{module_version}'; // 将{module_version}替换为实际的特性环境标识，如 'gray'（灰度）/ 'master'（正式）/ 'v20260116'
    const jsapi_entry = '{jsapi_entry}'; // 将{jsapi_entry}替换为实际的企微侧边栏场景值，如 'normal'（默认）/ 'contact_profile'（联系人详情）/ 'single_chat_tools'（单聊工具栏）等，参考"企业微信侧边栏场景值"章节

    // 1. 注入信息
    await page.evaluate((settings) => {
        sessionStorage.setItem('module_version', settings.module_version);
        // 设置localStorage AUTOMATION_TOKEN
        localStorage.setItem('AUTOMATION_TOKEN', settings.token);
        localStorage.setItem('AUTOMATION_SWITCH', '1');
        // 设置sessionStorage AUTOMATION_JSAPI_ENTRY, 仅侧边栏场景需要设置AUTOMATION_JSAPI_ENTRY
        if (settings.jsapi_entry) {
            localStorage.setItem('AUTOMATION_JSAPI_ENTRY', settings.jsapi_entry);
        }
    }, { module_version, token, jsapi_entry });
    
    // 2. 刷新首页
    await page.reload();
    // 3. 等待页面加载
    await page.waitForTimeout(3000);
    // 4. 验证登录成功
    const content = await page.content();
    if (content.includes('首页')) {
        return '✓ 环境初始化成功，已登录并加载首页';
    } else {
        throw new Error('✗ TOKEN无效，登录失败');
    }
}
```

---

## 企微入口
应用打开时，均只能通过统一的入口页进行转发，入口页为：`/workbench/?type=xxx`，根据`type`值判断对应的模块路由URL，通过`$router.push()`实现跳转。如果未包含`type`参数，则跳往首页。 常见入口为：
* 首页：也称为HOME页、主页，首页包含"首页"（主要是"待办"列表）、"客户"列表、"营销台"（全部模块入口列表）、"我的" 四个TAB栏，可从营销台找到各模块的跳转入口。 type为空，企微入口为企业微信工作台。页面path为`/workbench/home`
* 客户待办侧边栏：`/workbench/?type=customerTodo&wsAuthMode=manual`
* 超级群发侧边栏：`/workbench/message-task.html`
* 客户画像侧边栏：`/workbench/?type=sidebarCustomer&wsAuthMode=manual`
* 聊天素材通用素材侧边栏：`/workbench/?type=sidebar&wsAuthMode=manual`
* 聊天素材组合素材侧边栏：`/workbench/?type=sidebarGroup&wsAuthMode=manual`
* 聊天素材产品库侧边栏：`/workbench/?type=productLibListShare&from=sidebar&wsAuthMode=manual`
* 营销工具侧边栏: `/workbench/?type=marketingPlugin&wsAuthMode=manual`
* 商品库侧边栏: `/workbench/?type=mallCenter&sourceType=1&wsAuthMode=manual`
* 会话记录侧边栏: `/workbench/m_scrm/conversation&wsAuthMode=manual`
* 员工知识工作台侧边栏: `/workbench/?type=aiStaffKnowlage&wsAuthMode=manual`
* WS智能助手侧边栏: `/workbench/?type=intelligentAssistant&otherAiMobile=1&wsAuthMode=manual`

### 企业微信侧边栏场景值
在企业微信侧边栏场景，通常需要注入场景值，对应通过企业微信js-sdk `wx.getContext()` 方法获得的企微打开此页面场景值。 具体类型：

* contact_profile //从联系人详情进入
* single_chat_tools //从单聊会话的工具栏进入
* group_chat_tools // 从群聊会话的工具栏进入
* chat_attachment // 从会话的聊天附件栏进入， 罕见场景
* single_kf_tools // 从微信客服的工具栏进入
* chain_single_chat_tools // 上下游单聊会话的工具栏
* chain_group_chat_tools // 上下游群聊会话的工具栏
* normal // 除以上场景之外进入，例如工作台，聊天会话等
