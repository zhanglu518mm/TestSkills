# 管理端用例执行规则

## 管理端说明
技术框架采用Vue3，采用vue-router路由，mode: 'history', base: '/';

## 管理端用例执行工作流
严格按照 登录页TOKEN注入 -> 打开dashboard页 -> 通过菜单导航到目标页面 -> 按照测试步骤执行用例。具体步骤为：
1. 首先通过`browser_navigate`打开登录页{HOST}/login，然后通过 “Run Playwright code” 工具在cookie中添加TOKEN信息以及在sessionStorage中添加特性环境版本及自动化标识。cookie KEY为"token"， value为具体的token值, 不需要设置过期时间，即随会话过期；sessionStorage 特性环境KEY为"module_version", value为特性环境具体值; 自动化标识KEY为"AUTOMATION_SWITCH", Value:"1"。 注入信息后，打开dashboard页，URL为：{HOST}/index/dashboard。如果TOKEN有效，可以在dashboard看到"首页"文案。如果此时页面仍然跳转到登录页，则代表TOKEN无效，流程中止。 Run Playwright code 调用时传入的`code`参数示例：
```javascript
async (page) => {
    const HOST = '{HOST}'; // 将{HOST}替换为实际运行环境域名，如 https://platform.wshoto.com，注意可能带path， 如 https://wsai.wshoto.com/scrm
    const DOMAIN = '{DOMAIN}'; // {HOST}中的domain部分，如platform.wshoto.com
    const TOKEN = '{TOKEN}'; // 将{TOKEN}替换为实际token
    const module_version = '{module_version}'; // 将{module_version}替换为实际的特性环境标识，如 'gray'（灰度）/ 'master'（正式）

    // 1. 注入TOKEN到cookie
    await page.context().addCookies([{
      name: 'token',
      value: TOKEN,  
      domain: DOMAIN,
      path: '/'
    }]);

    // 2. 设置sessionStorage, 必须
    await page.evaluate((mv) => {
        sessionStorage.setItem('module_version', mv);
        sessionStorage.setItem('AUTOMATION_SWITCH', '1');  // 自动化标识
    }, module_version);

    // 3. 跳转到dashboard页面
    await page.goto(`${HOST}/index/dashboard`);
    await page.waitForLoadState('networkidle');

    // 4. 验证登录成功
    const content = await page.content();
    if (content.includes('首页')) {
        return '✓ 环境初始化成功，已登录并跳转到dashboard';
    } else {
        throw new Error('✗ TOKEN无效，登录失败');
    }
}
```

2. 通过菜单导航打开目标页, 然后按照测试步骤执行用例。假如测试用例中的菜单导航路径不明确或错误，点击页面"查找功能"按钮，在全部菜单列表中尝试找到目标页面入口。仅能通过菜单导航、页面元素点击跳转或"查找功能"的方式跳转到目标页面。**禁止猜测页面URL并直接打开URL**

### 文件上传
当涉及图片、视频、文件上传场景时，请到Chrome默认下载目录选择对应类型的文件上传，因为是自动化测试，尽量选择符合条件且小体积的文件上传。默认下载目录已经设置为当前系统用户目录下的"Downloads"文件夹; 始终通过`upload_file`工具实现文件上传。

### 文件下载
如果你触发了文件下载，你通常会看到下载保存到的文件路径。 如果未看到保存到的本地文件路径，你应该等待片刻后（建议20s），遍历chrome默认下载目录按照修改日期倒序排序的文件列表，确认下载文件是否存在。
通过 `ls -lt ~/Downloads | head -6` BASH命令查看刚刚下载的文件，注意下载的文件可能是图片文件/zip文件/excel表格。如果是zip文件， 在macOS系统下采用`ditto`实现解压缩，在Linux系统下通过`unar`解压缩。采用unzip解压缩时，如果压缩包中有中文文件名，会出现乱码，应避免使用。

### xlsx文件操作
请始终通过编写node.js代码，调用"xlsx"类库实现文件读取，通过`bash`调用`node -e`执行代码, 本机node.js版本>18。如果执行命令时提示"xlxs"类库不存在，请帮我通过"npm install -g xlsx"实现全局安装。
管理端涉及的xlsx操作通常为xlsx模版下载、根据xlsx中的规则说明填写模版后通过"文件上传"导入到系统。xlsx文件读取、填写模版均通过`bash`执行命令实现。通过`upload_file`工具实现文件上传。

### 表格导出
表格上方如果有"导出"按钮，点击后可能会触发两种导出行为，同步导出和异步调出。 同步导出会触发文件下载。 异步导出会显示导出进度，大约数秒钟后会导出完成后显示"下载"链接，请点击"下载"链接。请按照"文件下载"章节说明确认文件下载成功。如果需要核对导出的xlsx文件中的内容，请按照"xlsx文件操作"章节读取表格。

### 帮助中心
管理端页面上的"功能介绍"对应的是[帮助中心](https://help.wshoto.com/index.html) link 外链，如果页面上有此按钮，即证明包含帮助中心链接，不要调用`click`点击打开，因为在自动化测试中不希望在chrome tab页中打开帮助中心。

### 分组移动
分组"全部"并不是一个真正的分组，它代表"全部"（所有）分类下的数据列表。选择要移动到的分组时，优先选择名称不是"全部"的分组，方便验证。此时只需验证移动后的分组包含当前项目即可，不需要验证"全部"分类下是否存在，因为"全部"分类包含所有。

### 字符长度限制
测试用例中经常出现验证文本框输入长度限制相关用例，你只能通过执行`Bash`命令获取将指定字符串重复拼写直至指定长度的字符串。下面的示例是将"测试文本"重复拼接形成长度为30的字符串。
```bash
node -e 'const f=(k,l)=>k.repeat(Math.ceil(l/k.length)).substring(0,l);console.log(f("测试文本",30));'
```
当测试用例需验证长度超过200的输入合法性验证时跳过验证，标记为"无法验证"，并在"测试结果过程"列标明"自动化测试无法实现输入长度超过200，请人工验证"。

---

## 无法验证的测试用例
以下几种测试用例无法执行，请将这些用例的测试结果标记为"无法验证"。具体为：
* 如果是PC端（或称为管理端），如未特殊说明，当前账号类型默认为"超管"，或称为超级管理员/管理员。如果测试用例的账号类型为分管（分级管理员），则无法验证。
* 当测试用例需验证长度超过200的输入合法性验证时跳过验证，标记为"无法验证"，并在"测试结果过程"列标明"自动化测试无法实现输入长度超过200，请人工验证"。
