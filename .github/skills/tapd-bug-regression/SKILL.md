---
name: tapd-bug-regression
description: '针对 TAPD 任意 bug 单的通用回归 skill。支持跨池查询和回归：交付池、产研池、售后池。输入问题单 ID 和环境地址后，自动打开回归环境（优先 Playwright，不可用时启动系统默认浏览器）、按问题单步骤验证、截图留证、待用户确认后自动回写问题单状态与评论。'
argument-hint: '输入 bug ID 或完整链接，并提供回归环境地址；支持自然语言如：回归交付池问题单，问题单号是1119626'
user-invocable: true
---

# TAPD Bug 回归助手 - 通用版

针对 TAPD 任意 bug 单的专用回归 skill。此 skill 集成 TAPD API 查询能力，支持自动化定位、回归执行、证据收集和报告生成。

## 快速开始

### 前置条件

1. 已配置 TAPD API 访问凭证：
   - `TAPD_API_TOKEN`：用于 bug/需求/任务的查询和更新操作（推荐）
   - 或 `TAPD_API_USER` + `TAPD_API_PASSWORD`：用于只读查询

2. 已安装 TAPD skill 脚本：`~/.openclaw/skills/tapd/scripts/tapd.py`

3. 已安装 Python 3.6+

### 典型调用

```bash
# 方式 1：仅提供 bug 短 ID（自动轮询交付池→产研池→售后池）
/tapd-bug-regression 1119626

# 方式 2：粘贴完整链接（从 URL 自动识别池子，无需轮询）
/tapd-bug-regression https://www.tapd.cn/tapd_fe/65152329/bug/detail/1165152329001119626

# 方式 3：强制指定问题池（跳过自动轮询）
/tapd-bug-regression 1119626 --workspace 产研池

# 方式 4：售后池
/tapd-bug-regression 1119626 --workspace 售后池

# 方式 5：自然语言触发
回归问题单，问题单号是1119626，环境地址是 https://test.example.com
```

## 问题池映射

| 关键词 | 池名 | workspace_id | 典型功能 |
|---|---|---|---|
| 交付 / 交付池 / 企微交付 | 企微需求_交付池 | 65152329 | 交付团队缺陷处理、客户级 bug 跟踪 |
| 产研 / 产研池 / 企微产研 | 企微需求_产研池 | 44949107 | 产品和研发 bug、技术债 |
| 售后 / 售后池 / 企微售后 | 企微需求_售后池 | 41700174 | 客服反馈、售后维保缺陷 |

## 执行流程

### 1. 定位 Bug 单

输入 bug ID 或完整链接，根据规则确定问题池。

**规则优先级**：
1. 从 URL 路径提取 workspace_id（格式：`/tapd_fe/{workspace_id}/bug/detail/{entity_id}`）
2. 用户明确指定 `--workspace` 参数，根据关键词映射到对应 workspace_id
3. 仅提供 bug 短 ID 时，**自动轮询三个池子**，使用第一个返回有效结果的池子

**自动轮询策略**（规则 3 的执行方式）：

按交付池 → 产研池 → 售后池的顺序逐一调用 `bug-get`，判断标准是命令返回非空的 bug 标题字段：

```bash
# 依次尝试三个池子
for ws_id in 65152329 44949107 41700174; do
  result=$(python3 "$TAPD_SCRIPT" bug-get --workspace-id $ws_id --id <bug_id>)
  if echo "$result" | grep -q "标题"; then
    echo "命中：workspace_id=$ws_id"
    break
  fi
done
```

- 找到后记录 `workspace_id` 与池名，后续所有操作使用该池的配置。
- 三个池子均未命中时，向用户报告"未在任何池子中找到该 bug 单"，终止流程。
- 用户可随时通过 `--workspace` 参数强制指定池子，跳过自动轮询。

### 2. 查询 Bug 详情

使用 TAPD `bug-get` 命令拉取完整信息：

```bash
python3 "$TAPD_SCRIPT" bug-get --workspace-id <ws_id> --id <bug_id>
```

**提取关键字段**：
- 标题、描述、当前状态
- **严重程度**（致命 / 严重 / 一般 / 提示 / 建议）
- **影响环境**（用于决定回写状态）
- 受影响版本
- 受影响模块、功能区
- 复现步骤（若有）
- 期望结果、实际结果
- 指派人、报告人
- 附件、相关链接

### 3. 分析回归范围

根据 bug **严重程度**决定回归深度：

| 严重程度 | 回归策略 |
|---|---|
| **致命 / 严重** | <ul><li>精确复现问题</li><li>覆盖相邻功能流程</li><li>该功能模块全量冒烟测试</li><li>回归测试用例 5+ 个</li></ul> |
| **一般 / 提示 / 建议** | <ul><li>精确复现问题</li><li>相邻流程 3-5 条</li><li>相关功能冒烟测试</li></ul> |

**通用附加规则**：
- 回归涉及的界面上若存在**导出按钮**，必须验证导出功能是否正常（点击导出 → 确认文件可成功生成或下载，无报错）。

### 4. 准备环境

- 读取你提供的回归环境地址，并优先使用 Playwright 打开页面
- 到登录界面后暂停，等待你扫码登录
- 扫码成功后继续执行回归步骤
- 配置必要的测试账号、角色、权限
- 激活必要的功能开关
- 准备测试数据

**界面入口定位规则（强制）**：
- 进入任何功能界面前，**必须先查阅** `references/platform-menu.md` 中的菜单结构，确认该功能的完整导航路径（一级 / 二级 / 三级 …）。
- 菜单文档中未收录的路径，才可根据 bug 描述或 PRD 自行推断。
- 导航路径确认后，按该路径依次点击菜单进入目标页面，不得跳过中间菜单层级。

**左侧树形菜单导航技巧（运营分析 / 基础看板等自定义树组件）**：
- 企微管理后台的运营分析侧边栏是**自定义树组件**，不使用 `el-menu-item` / `el-sub-menu__title` 类，而是 `div.node-box`。
- `li:has-text()` 会命中祖先节点导致点击无效，`text=xxx` locator 的隐藏元素也会超时。
- 正确方式：用 JavaScript `TreeWalker` 精确匹配**纯文字节点**，向上找第一个非 `SPAN` 的可见父元素并 `click()`：
  ```python
  def js_click_by_text(page, text):
      return page.evaluate("""
          (text) => {
              const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
              let node;
              while (node = walker.nextNode()) {
                  if (node.textContent.trim() === text) {
                      let el = node.parentElement;
                      while (el && el.tagName === 'SPAN') el = el.parentElement;
                      if (el && el.offsetParent !== null) {
                          el.click();
                          return 'clicked: ' + el.tagName + ' ' + el.className;
                      }
                  }
              }
              return 'not found: ' + text;
          }
      """, text)
  # 用法：点击「运营分析」后侧边栏自动展开，无需再点「基础看板」，直接点二级即可
  page.locator('text=运营分析').first.click(); page.wait_for_timeout(1500)
  js_click_by_text(page, '员工分析'); page.wait_for_timeout(1500)
  js_click_by_text(page, '员工统计'); page.wait_for_timeout(3000)
  ```

**弹窗内操作注意（Element Plus el-overlay-dialog 遮罩）**：
- Element Plus 对话框会在页面顶层渲染 `.el-overlay-dialog` 遮罩，普通 `click()` 可能报 "subtree intercepts pointer events"。
- 解决方案：将 locator 限定在 `page.locator('[role="dialog"]')` 内部，并加 `force=True`：
  ```python
  dialog = page.locator('[role="dialog"]')
  dialog.locator('.el-radio:not(.is-checked)').first.click(force=True)
  dialog.locator('button:has-text("取 消"), button:has-text("取消")').first.click(force=True)
  ```

浏览器执行策略（优先级从高到低）：
1. **Playwright 工具**（首选）：打开页面、读取页面、点击操作、截图留证，全自动执行。
2. **系统默认浏览器**（Playwright 工具不可用时）：通过终端命令自动在默认浏览器中打开回归环境地址，由你在浏览器中操作；Copilot 提供逐步检查指引，并在每一步完成后请你口头确认或截图提供结果。
   ```powershell
   # Windows：自动打开默认浏览器
   Start-Process "<回归环境地址>"
   ```
3. **纯手工协同**（仅当终端命令也无法执行时）：你自行打开浏览器，Copilot 给出完整步骤与检查点，验证结果由你反馈。
- 评论回写优先级：优先使用 **TAPD API** 写评论正文，并在正文中写入附件预览链接；网页登录后在网页评论编辑器中补充内容为第二优先级。

**管理端（PC端）登录方式（自动判断，无需人工选择）**：

> Agent 根据用户是否提供 token **自动选择**登录方式，无需人工指定。

- **用户已提供 token → Token 注入（优先）**：
  打开 `/login` 页，通过 Playwright 按以下方式注入，然后跳转到 `/index/dashboard`；出现"首页"文案即为登录成功，否则判定 token 无效，自动降级到扫码登录。
  - **Cookie**：key = `token`，value = 用户提供的 token 值，domain = 当前回归域名，path = `/`
  - **sessionStorage**：
    - `module_version`：`"master"` 或 `"gray"`（按环境填写）
    - `AUTOMATION_SWITCH`：固定值 `"1"`
  - **注意**：key 是 Cookie 中的 `token`，sessionStorage 里只需设 `module_version` 和 `AUTOMATION_SWITCH`，不需要注入 `current-token`、`hasLogin`、`WS_BASE_INFO_SESSION_STORAGE_KEY` 等其他字段。

- **用户未提供 token → 扫码登录（自动降级）**：
  用命令行打开**系统默认可见浏览器**（`start chrome <url>` 或 `webbrowser.open()`），导航到回归系统登录页，在对话中提示用户"请在刚打开的浏览器窗口中扫码登录，完成后回复我"，等待用户确认后继续执行后续步骤。

下载验证策略（强制）：
1. 首选下载事件方式：点击下载前先等待下载事件，捕获后保存文件并校验文件大小大于 0。
2. 若系统“另存为”弹窗导致无法捕获下载事件，改走网络响应校验：确认下载请求状态码为 200 且响应体非空。
3. 若仍无法直接拿到下载响应，使用链路兜底校验：验证“导出完成/可下载”状态、目标文件可预览、页面无 00401/no authority 报错，并截图留证。
4. 回写评论时必须明确本次使用的下载验证方式，不得把“链路兜底校验”描述成“已落地下载成功”。

**常用命令** 参考 TAPD skill 的使用文档

### 5. 执行回归检查

> **参考规范（按端选择，强制）**：
> - **PC 端 / 管理端**：遵守 [reference/admin-execution.md](reference/admin-execution.md) 中的全部执行规则，以下为关键摘要。
> - **移动端**：遵守 [reference/mobile-execution.md](reference/mobile-execution.md) 中的全部执行规则。
> - **手机操作（企微客户端）**：通过 [reference/phone-agent.md](reference/phone-agent.md) 中定义的手机操作智能体执行。
> - **企业微信 UI 自动化**：参照 [reference/wework-ui-automation.md](reference/wework-ui-automation.md) 的规范。

**步骤流程**：

| 序号 | 检查项 | 验证方式 |
|---|---|---|
| 1 | 复现问题 | 按 bug 描述的步骤，验证问题确实存在或已修复 |
| 2 | 验证修复 | 确认修复后的行为满足预期结果 |
| 3 | 边界测试 | 测试异常值、空值、极限值，确保修复不引入新问题 |
| 4 | 相邻流程 | 检查相同功能区的其他流程是否被波及 |
| 5 | 自动化覆盖 | 若已有单元测试/集成测试，执行相关用例 |
| 6 | 基本冒烟 | 核心功能基础检查 |

执行要求：
- 必须按问题单中的描述和测试步骤逐条验证。
- 验证过程中保留关键步骤截图，截图应可支撑最终结论。

**PC 端操作强制规范（来自 qa-testcase-execute）**：
- **菜单导航优先**：只能通过菜单点击或页面内跳转到达目标页，**禁止猜测 URL 直接跳转**；菜单路径不明确时点击"查找功能"在全局菜单中定位。
- **常规交互优先**：必须用页面点击、表单填写等正常用户操作执行验证，**禁止用 `Evaluate JavaScript` 代替页面操作**；仅 Token 注入环节或常规方式确实无解时才允许执行 JS。
- **文件上传**：统一使用 `upload_file` 工具；从系统 `Downloads` 目录选小体积文件。
- **文件下载**：触发下载后等待约 20s，确认文件出现在 `Downloads` 目录；zip 包在 Windows 下用 `Expand-Archive` 解压，避免 `unzip` 中文乱码。
- **xlsx 操作**：通过 `node -e` + `xlsx` 类库读写表格；`xlsx` 未安装时先执行 `npm install -g xlsx`。
- **表格导出**：区分同步导出（直接触发下载）和异步导出（显示进度 → 出现"下载"链接后点击），按"文件下载"规范确认落地。
- **字符长度测试**：用 `node -e` 生成指定长度重复字符串；**超过 200 字符的长度验证无法自动化，标记"无法验证"并在评论中注明"请人工验证"**。
- **无法验证的场景**：当前账号默认超管；若用例需要"分管"账号，标记为"无法验证"。

### 6. 收集证据

**关键证据类型**：
- **日志**：应用日志、API 日志、数据库日志
- **截图**：UI 变化、错误提示、关键步骤
- **API 响应**：请求参数、响应体、HTTP 状态码
- **测试输出**：单元测试、集成测试运行结果
- **性能指标**：响应时间、内存占用（若涉及性能问题）
- **对比数据**：修复前后的对比结果

### 7. 生成回归报告

填充回归报告模板：

- **状态**：Pass、Fail、Blocked、Partial（四选一）
- **问题单摘要**：标题、描述、优先级、受影响版本
- **回归范围**：实际检查了哪些场景
- **执行检查详情**：每一步的验证结果
- **关键证据**：支撑结论的直接证据
- **风险评估**：剩余风险、覆盖缺口
- **建议后续**：是否需要进一步验证、性能测试、自动化补充等

### 8. 待你确认验证结果

- 完成验证和截图后，先向你汇报结论与证据摘要。
- 只有在你明确确认“验证通过”后，才允许执行 TAPD 状态更新和评论回写。

### 9. 回写问题单状态与评论

**第一步：获取当前用户身份（强制）**

在写评论之前，先调用 TAPD API 获取当前 token 对应的用户信息，提取昵称或姓名，用于写入评论的 `【回归人】` 字段：

```bash
python3 "$TAPD_SCRIPT" account-info
```

- 成功则取返回中的 `nick`（昵称）或 `name` 字段作为回归人标识。
- 若接口返回失败或字段为空，则使用环境变量 `TAPD_API_USER` 的值作为回归人标识。
- 回归人信息必须写入评论，禁止省略。

**第二步：写评论前查重（强制）**

在调用 `comment-add` 之前，必须先检查是否已存在当前账号提交的回归评论：

```bash
python3 "$TAPD_SCRIPT" comment-list --workspace-id <workspace_id> --entry-type bug --entry-id <bug_id>
```

- 若列表中已存在由当前回归人提交且包含"回归结论"或"验证通过"的评论，**跳过 `comment-add`**，改用 `comment-update` 补充差异内容（如截图链接）。
- 若列表为空或无相关评论，正常执行 `comment-add`。
- 禁止在同一 bug 下重复写入相同结论的评论，避免因命令重试或静默重复执行导致多条重复评论。

通过后状态规则：
- 交付池（65152329）：状态更新为 `已关闭`
- 售后池（41700174）：状态更新为 `线上验证`
- 产研池（44949107）：**必须先读取问题单“影响环境”字段，再按下表回写状态**

| 问题池 | 影响环境命中关键词 | 回写状态 |
|---|---|---|
| 产研池（44949107） | 测试环境 / 基线环境 | `已关闭` |
| 产研池（44949107） | 正式环境 / 灰度环境 / 群环境 / 远航环境 | `线上验证` |

判定规则（产研池强制）：
1. 先读取并标准化“影响环境”字段（去空格、统一大小写、中文全半角差异忽略）。
2. **只要命中“基线环境”关键词，必须直接回写为 `已关闭`**（即使标题或其他字段包含“基线”同类词，也按 `已关闭` 处理）。
3. 若同时命中测试环境/基线环境与正式环境类关键词，按高风险优先，回写为 `线上验证`。
4. 若 API 返回中“影响环境”为空，必须先进行二次读取（不带 `fields` 再查一次，必要时从 TAPD 网页字段读取）后再判定。
5. 二次读取后仍无法判定时，默认回写为 `线上验证`，并在评论中注明“影响环境未明确，按线上验证流程处理”。
6. 仅当你明确确认“验证通过”后，才执行上述状态流转。

评论规则：
- 新增评论内容必须包含“验证通过”。
- 回归结论文案统一使用“【回归结论】验证通过。”，不追加“（交付池）/（产研池）/（售后池）”等池子后缀。
- 评论写入链路优先级（强制）：
  1) 优先使用 API（`comment-add` / `comment-update`）直接写评论正文。
  2) 若 API 无法满足当前场景，再使用网页登录后的网页评论编辑器补充或修正评论。
  3) 仅当 API 和网页回写都不可用时，才退化为手工协同回写。
- API 评论默认使用富文本 HTML 结构，必须通过 `<p>`、`<br>` 或等效换行方式保留空行，避免所有内容挤成连续段落。
- 若截图已上传为 TAPD 附件，API 评论中应优先写入**可点击的附件预览链接**，格式优先使用：`https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?`。
- 若 API 评论不能直接内嵌图片，必须显式写“查看截图X”链接，点击后应能打开图片预览页。
- 截图与文案必须一一对应：截图1只能放“实际验证通过截图1”，截图2只能放“实际验证通过截图2”，禁止文案与图片错位。
- 评论排版要求（强制）：每个“实际验证通过截图X”标题后必须换行写“实际截图结果：...”，并保留空行分隔，禁止把所有证据写成连续密集段落。

API 评论附加规则：
1. 优先先上传附件，再生成附件预览链接并写入评论。
2. 评论中每个截图块至少包含三行：截图标题、实际截图结果、查看链接。
3. 若当前验证页面的导出按钮为置灰、隐藏或无数据导致不可点，评论必须据实写明页面状态，禁止写成“导出成功”。
4. 若需补充网页评论，仅作为 API 评论后的修正手段，不得覆盖 API 评论中的结构化结论。

固定执行策略（强制）：
1. 先完成页面验证并在本地保存截图。
2. 通过 TAPD 附件区上传截图，拿到 `attachment_id`。
3. 按 `https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?` 规则生成每张图的预览链接。
4. 使用 API 写评论正文，正文采用 HTML 分段结构，按“结论 → 验证结果 → 截图证据”顺序排版。
5. 若 API 评论已成功落库，则默认不再重复走网页登录评论。
6. 仅当 API 评论失败、链接缺失或需要人工修正文案时，才启用网页登录评论作为第二优先级。

附件上传固定策略：
- 上传顺序：按截图在评论中出现的顺序上传，保持截图1、截图2、截图3与附件顺序一致。
- 命名规范：`YYYYMMDD-rerun-01-<meaning>.png`、`YYYYMMDD-rerun-02-<meaning>.png`。
- 上传完成后必须核对附件名称、`attachment_id`、预览链接三者一一对应。
- 若上传了错误截图，不得继续复用原链接，必须重新上传并替换评论中的错误链接。

**附件上传工具选择顺序（强制）**：
1. 首选：直接调用 `tapd-web-attachment-bridge.py`（使用站内 API `/api/entity/attachments/add_attachment_drag`，比 UI 按钮方式更可靠）。
2. Bearer token 直传（`https://api.tapd.cn/attachments`）返回 403 `attachments::_save_new` 时，跳过，直接走步骤 1，不要重试。
3. 若 bridge 脚本也失败，创建独立上传脚本（`upload_attachments.py` 模式），使用 `page.request.fetch()` 调用同一站内 API。

附件上传认证策略（强制）：
1. 默认使用当前会话 `TAPD_API_TOKEN` 上传附件。
2. 若返回 403 且信息包含 `attachments::_save_new` 或 `attachments::upload` 权限不足，则自动切换到服务账号 BasicAuth 进行附件上传。
3. 服务账号只用于“附件上传”动作，Bug/评论查询与状态流转仍优先使用个人 token。
4. 服务账号凭证禁止写入仓库、禁止出现在日志和评论，必须仅保存在本地环境变量或企业密钥管理系统中。
5. 若服务账号测试返回 `This api not writeable.`、WAF 403 或其他接口侧阻断，则判定“当前服务账号不可用于 OpenAPI 附件直传”，立即回退为“网页附件上传 + API 评论回写”。

网页上传回退链路（已验证）：
1. 在 TAPD bug 详情页登录态下，附件上传走站内接口 `POST /api/entity/attachments/add_attachment_drag?needRepeatInterceptors=false`（multipart/form-data）。
2. 上传成功后会调用 `POST /api/entity/attachments/update_attachment_sort`，并带 `dsc_token`、`workspace_id`、`entity_id`、`entity_type`、`sort`。
3. 最后通过 `GET /api/entity/attachments/attachment_list` 拉取附件列表并得到 `attachment_id`。
4. 该链路依赖 TAPD 网页登录会话（Cookie/站内鉴权），不等价于 `https://api.tapd.cn/attachments` 与 `https://api.tapd.cn/attachments/upload`。
5. 团队自动化建议：使用 Playwright 登录 TAPD 后调用上述站内接口上传附件，再继续走 API 评论回写。

API 评论固定结构：
- 第一段：`【回归结论】验证通过。`
- 第二段：`【回归时间】`、`【回归环境】`
- 第三段：`【验证结果】`，按 1/2/3 编号逐条写结论
- 第四段：`【截图证据】`，每张图独立一个段落
- 第五段：`【备注】`，仅写本次重跑修正点、限制项或补充说明

截图证据固定结构：
- `实际验证通过截图X：<截图标题>`
- `实际截图结果：<该图对应的事实结论>`
- `查看截图X：<附件预览链接>`
- 各截图块之间必须保留空行，不得写成连续文本。

统一评论模板（唯一版本，后续默认使用这一版）：

```text
【回归结论】验证通过。

【回归时间】<YYYY-MM-DD>
【回归人】<当前用户昵称或姓名>
【回归环境】<环境地址>

【验证结果】
1）<检查项1结果>
2）<检查项2结果>
3）<检查项3结果>

【截图证据】
实际验证通过截图1：<截图标题1>
实际截图结果：<截图1对应的事实结论>
查看截图1：<附件预览链接1>

实际验证通过截图2：<截图标题2>
实际截图结果：<截图2对应的事实结论>
查看截图2：<附件预览链接2>

实际验证通过截图3：<截图标题3>
实际截图结果：<截图3对应的事实结论>
查看截图3：<附件预览链接3>

【备注】<仅填写本次重跑修正点、限制项或补充说明；无则可省略>
```

统一模板约束：
1. 固定使用 `【回归结论】`、`【回归时间】`、`【回归人】`、`【回归环境】`、`【验证结果】`、`【截图证据】` 六段结构。
2. `【备注】` 为可选段，仅在需要说明重跑修正点、自动化限制、页面状态限制时出现。
3. `【验证结果】` 固定使用 `1）2）3）` 编号，不混用短横线或无序列表。
4. `【截图证据】` 中每张图固定三行：标题、结果、链接；不得缺字段。
5. 若实际只有 2 张图，则只保留截图1、截图2；若有 4 张及以上，按同一结构顺延。

推荐 API 评论 HTML 模板：

```html
<p>【回归结论】验证通过。</p>
<p>【回归时间】2026-03-25</p>
<p>【回归人】张三</p>
<p>【回归环境】https://test.example.com/</p>
<p>【验证结果】</p>
<p>1）检查项1结果。</p>
<p>2）检查项2结果。</p>
<p>3）检查项3结果。</p>

<p>【截图证据】</p>

<p>实际验证通过截图1：问答知识页（导出列表按钮状态）</p>
<p>实际截图结果：当前页 0 条数据，导出按钮置灰。</p>
<p><a href="https://www.tapd.cn/65152329/attachments/preview_attachments/1165152329001015133/bug?" target="_blank">查看截图1</a></p>

<p>实际验证通过截图2：文件知识页（含问答.txt条目）</p>
<p>实际截图结果：列表展示正常。</p>
<p><a href="https://www.tapd.cn/65152329/attachments/preview_attachments/1165152329001015134/bug?" target="_blank">查看截图2</a></p>

<p>实际验证通过截图3：问答.txt预览页</p>
<p>实际截图结果：文件预览页可正常打开，未出现权限报错。</p>
<p><a href="https://www.tapd.cn/65152329/attachments/preview_attachments/1165152329001015135/bug?" target="_blank">查看截图3</a></p>

<p>【备注】已按本次回归结果更新评论模板与证据链接。</p>
```

HTML 排版要求（强制）：
1. 每个截图块必须拆成独立三段 `<p>`：标题段、结果段、链接段。
2. 截图块之间必须保留空行，不允许用一个 `<p>` + 多个 `<br/>` 挤在一起。
3. `【验证结果】` 与 `【截图证据】` 标题段前后都要保留空行。

打标签规则（强制）：
- 回归完成并成功回写评论后，必须通过 TAPD API 为该 bug 打上 `AI Regression` 标签。
- 三个池子（交付池 / 产研池 / 售后池）均适用，无论最终状态是 `已关闭` 还是 `线上验证`。
- 使用 `bug-update` 命令的 `label` 字段实现，具体命令参考 TAPD skill 文档。
- 若当前 bug 已有其他标签，追加 `AI Regression` 而不是覆盖，保留原有标签。
- 打标签失败（如权限不足）时，在评论 `【备注】` 段中注明"AI Regression 标签打标失败，请人工补打"，不阻塞整体流程。

## 跨池快速切换

同一个 bug ID 可能在多个池子中存在。使用 `--workspace` 参数快速切换：

```bash
# 查询产研池中的同编号 bug
/tapd-bug-regression <bug_id> --workspace 产研池

# 查询售后池中的同编号 bug
/tapd-bug-regression <bug_id> --workspace 售后池
```

Agent 会自动将关键词映射到对应的 `workspace_id`，通过 `bug-get` 命令查询。

## 输出规范

### 成功（Pass）
清晰说明：
- 验证了问题单中的哪些场景
- 每一步的验证结果
- 修复前后对比的直接证据
- 是否还有遗留风险

### 失败（Fail）
明确指出：
- 具体失败在哪一步
- 失败现象和期望现象的对比
- 是否是环境问题还是真实缺陷
- 建议后续处理

### 阻塞（Blocked）
记录阻塞原因：
- 无法访问问题单系统
- 被测应用无法启动
- 缺少必要的测试账号或权限
- 测试数据不可用
- 性能/稳定性差导致无法执行

### 部分验证（Partial）
明确说明：
- 已验证的部分（含结果）
- 未验证的部分（原因）
- 建议补充验证的方向

## 回写安全规则

- 未经你确认，不允许改状态。
- 未提供截图信息，不允许写“验证通过”评论。
- 若验证失败或阻塞，仅更新回归结论和失败原因，不执行“通过状态”流转。

## 参考资料

- TAPD Skill 文档：`../../tapd/SKILL.md`
- 问题池配置与说明：[assets/config-pools.yaml](./assets/config-pools.yaml)
- 详细工作流说明：[references/usage.md](./references/usage.md)
- 回归报告模板：[assets/regression-report.template.md](./assets/regression-report.template.md)

