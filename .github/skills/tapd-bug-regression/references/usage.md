# TAPD Bug 回归 Skill - 使用指南

## 快速开始

### 前置检查

确保你已安装并配置好 TAPD skill：

1. **环境变量配置**（每位成员使用自己的凭证）
```bash
export TAPD_API_USER="your_tapd_api_user"
export TAPD_API_PASSWORD="your_tapd_api_password"
export TAPD_API_TOKEN="your_tapd_api_token"
export SKILL_DIR="~/.openclaw/skills"
```

PowerShell 团队推荐方式：

```powershell
powershell -ExecutionPolicy Bypass -File .github/skills/tapd-bug-regression/scripts/bootstrap-user-env.ps1
```

说明：脚本会交互式采集个人 TAPD 凭证，自动生成 `local.env.ps1`，并默认写入 `$PROFILE` 以便后续新终端自动加载。

如不希望写入 `$PROFILE`：

```powershell
powershell -ExecutionPolicy Bypass -File .github/skills/tapd-bug-regression/scripts/bootstrap-user-env.ps1 -SkipProfileUpdate
. .github/skills/tapd-bug-regression/local.env.ps1
```

安全规则：
- 不共享、不提交真实 `TAPD_API_TOKEN`。
- 若 token 泄露，立即在 TAPD 个人设置中重置并更新本地 `local.env.ps1`。

2. **TAPD skill 路径**
```bash
TAPD_SCRIPT="$SKILL_DIR/tapd/scripts/tapd.py"
```

3. **Python 版本检查**
```bash
python3 --version  # 需要 >= 3.6
```

### 调用 Skill

直接在对话中输入，支持以下形式：

**形式 1：仅输入 bug ID（自动轮询三个池子）**
```
/tapd-bug-regression 1119626
```

**形式 2：贴完整链接（自动识别池子）**
```
/tapd-bug-regression https://www.tapd.cn/tapd_fe/65152329/bug/detail/1165152329001119626
```

**形式 3：指定问题池**
```
/tapd-bug-regression 1119626 --workspace 产研池
/tapd-bug-regression 1234567 --workspace 售后池
```

**形式 4：多参数组合**
```
/tapd-bug-regression https://www.tapd.cn/...bug/detail/...001234567 --workspace 产研池 --verbose
```

**形式 5：自然语言触发（推荐）**
```
回归交付池问题单，问题单号是1119626，环境地址是 https://test.example.com
```

说明：默认使用 Playwright 打开并操作回归环境页面。

### 输出是什么

你会收到一个 **完整的回归报告**，包括：
- Bug 详情摘要（从 TAPD 自动拉取）
- 回归范围分析（基于 bug 属性自动生成）
- 执行检查结果（需要手动执行或配置自动化）
- 关键证据（截图、日志、接口响应等）
- 最终结论（Pass / Fail / Blocked / Partial）

---

## 工作流详解

### 第 1 步：Skill 自动化部分

当你输入 bug ID 后，Skill 主动执行：

#### 1.1 定位问题池与 Bug ID

根据以下优先级顺序自动判断：

1. **从 URL 提取**（若用户贴的是完整链接）
   - 识别路径中的 workspace_id（格式：`/tapd_fe/{workspace_id}/bug/...`）
   - 识别 bug 的完整 ID，转换为短 ID

2. **用户参数指定**（若带 `--workspace` 参数）
   - 映射关键词到对应 workspace_id
   - 示例映射：
     - "交付池" / "交付" → 65152329
     - "产研池" / "产研" → 44949107
     - "售后池" / "售后" → 41700174

3. **自动轮询三个池子**（若无其他线索）
   - 按 65152329 → 44949107 → 41700174 顺序调用 `bug-get`
   - 第一个命中的池子作为后续回归目标

**示例**：
```
输入：/tapd-bug-regression 1119626 --workspace 产研池
→ 自动转换为 workspace_id=44949107，bug_id=1119626
```

#### 1.2 调用 TAPD 查询 Bug 详情

执行命令：
```bash
python3 "$TAPD_SCRIPT" bug-get --workspace-id 65152329 --id 1119626
```

从返回结果提取关键字段：
```json
{
  "Bug": {
    "id": "1165152329001119626",
    "title": "[页面]登录页面输入框显示错误",
    "description": "用户在登录页面输入账号时，输入框边框颜色异常显示为红色",
    "priority": "P2",
    "status": "处理中",
    "affected_version": "v1.0.0",
    "affected_module": "登录模块",
    "reproduce_steps": "1. 打开登录页面\n2. 点击账号输入框\n3. 输入任意账号",
    "expected_result": "输入框边框显示正常的蓝色",
    "actual_result": "输入框边框显示为红色",
    "reporter": "test_user",
    "assignee": "dev_user",
    "created_date": "2026-03-20",
    "updated_date": "2026-03-22"
  }
}
```

#### 1.3 分析回归范围

根据 bug 属性自动生成初步回归计划：

| 属性 | 值 | 隐含回归策略 |
|---|---|---|
| Priority | P2 | 中度回归：相邻流程 3-5 条、自动化测试覆盖 |
| Module | 登录模块 | 覆盖：注册、密码重置、OAuth 登录 |
| Type | UI 样式 | 跨浏览器测试、响应式测试 |
| Affected Version | v1.0.0 | 从 v1.0.0 开始需要验证，后续版本需要回归 |

---

### 第 2 步：人工执行回归（核心价值）

**注意**：Skill 提供方向和模板，但真实验证需要你或测试团队执行。

#### 2.1 准备环境

根据 [config-pools.yaml](./assets/config-pools.yaml) 配置，并按以下顺序执行：

1. 你提供回归环境地址。
2. 我使用 Playwright 打开页面并进入登录界面。
3. 你扫码登录。
4. 登录成功后继续执行问题单验证。

Playwright 执行范围：
- 打开环境地址
- 读取页面元素
- 按问题单步骤点击和填写
- 在关键步骤截图

示例（Web 场景）：

```bash
# 启动被测应用
cd /path/to/app
npm install
npm run dev:delivery

# 等待应用启动完成
# 验证访问: http://localhost:3000
```

#### 2.2 精确复现

按 bug 描述的步骤执行：

```
1. 打开浏览器，访问 http://localhost:3000/login
2. 点击"账号"输入框
3. 输入任意文本，检查输入框边框颜色
4. 预期：蓝色边框；发现：红色边框（原始问题）
```

**截图**：记录当前现象

执行提示：以上步骤默认由 Playwright 驱动页面操作完成。

#### 2.3 验证修复

检查相同步骤在修复后是否通过：

```
重复步骤 1-3，验证边框颜色是否已变为蓝色
```

**截图**：记录修复后现象

#### 2.4 相邻流程检查

根据自动生成的范围清单检查：

| 流程 | 检查方法 |
|---|---|
| 注册流程 | 访问注册页面，检查输入框样式 |
| 密码重置 | 访问密码重置页面，检查输入框样式 |
| OAuth 登录 | 点击第三方登录，检查相关输入框 |

**截图**：每个流程的验证结果

#### 2.6 结果确认闸门（必须）

在执行任何 TAPD 状态更新前，必须先完成以下动作：

1. 我先汇总验证结果和截图证据。
2. 你明确确认“验证通过”。
3. 仅在你确认后，才执行状态更新和评论回写。

#### 2.7 评论回写方式（必须按优先级）

回写评论时，必须按以下顺序执行：

1. 使用 TAPD API（`comment-add` / `comment-update`）直接写评论正文。
2. 将已上传附件转换为可点击的 TAPD 预览链接，并写入评论正文。
3. 若 API 回写失败或需要额外补充，再使用网页登录后的网页评论编辑器修正。
4. 仅在 API 和网页登录回写都不可用时，才使用手工协同方式处理。

注意：
- API 评论优先使用 HTML 分段结构，必须保留换行与空行，避免评论挤成一段。
- 若图片无法直接内嵌，必须提供 TAPD 附件预览链接，点击链接应能直接打开图片。
- 推荐链接格式：`https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?`
- 网页登录写评论现在是第二优先级，不再作为默认首选链路。

评论可读性要求：
- 必须使用分段结构（回归信息 / 验证结果 / 证据截图）。
- 每个“实际验证通过截图X”后必须单独换行写“实际截图结果：...”。
- 每个截图块后必须再单独一行写“查看截图X：<链接>”。
- 不允许将全部验证结果与证据写成连续段落。

推荐 API 评论片段：

```html
<p>【回归结论】验证通过。</p>
<p>【验证结果】</p>
<p>1）问答知识页导出按钮状态已核对。</p>
<p>2）文件知识页问答.txt 可见。</p>
<p>3）文件预览页无 00401 报错。</p>
<p>【截图证据】</p>
<p>实际验证通过截图1：问答知识页（导出列表按钮状态）<br/>实际截图结果：0 条数据，按钮置灰。<br/>查看截图1：<a href="https://www.tapd.cn/65152329/attachments/preview_attachments/1165152329001015133/bug?" target="_blank">打开图片</a></p>
```

#### 2.8 固定回写策略（推荐直接照做）

后续 TAPD 回归默认使用下面这条固定链路：

1. 完成验证后，先把截图保存到本地证据目录。
2. 通过 TAPD 附件区上传截图。
3. 记录每张图对应的 `attachment_id`。
4. 拼接每张图的 TAPD 预览链接。
5. 用 API 一次性写入评论正文。
6. 若 API 评论失败，再改用网页登录评论作为第二优先级。

固定链路示意：

```text
本地截图
→ 上传 TAPD 附件
→ 生成 preview_attachments 链接
→ 组织 HTML 评论正文
→ 调用 comment-add / comment-update
→ 成功后结束
```

附件链接拼接规则：

```text
https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?
```

示例：

```text
https://www.tapd.cn/65152329/attachments/preview_attachments/1165152329001015133/bug?
```

固定评论骨架（唯一版本）：

```html
<p>【回归结论】验证通过。</p>
<p>【回归时间】2026-03-25</p>
<p>【回归环境】https://baseline.wshoco.cn/</p>
<p>【验证结果】</p>
<p>1）检查项1。</p>
<p>2）检查项2。</p>
<p>3）检查项3。</p>
<p>【截图证据】</p>
<p>实际验证通过截图1：标题1<br/>实际截图结果：结论1。<br/>查看截图1：<a href="https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?" target="_blank">打开图片</a></p>
<p>实际验证通过截图2：标题2<br/>实际截图结果：结论2。<br/>查看截图2：<a href="https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?" target="_blank">打开图片</a></p>
<p>实际验证通过截图3：标题3<br/>实际截图结果：结论3。<br/>查看截图3：<a href="https://www.tapd.cn/<workspace_id>/attachments/preview_attachments/<attachment_id>/bug?" target="_blank">打开图片</a></p>
<p>【备注】仅在需要补充限制项或重跑修正点时填写。</p>
```

执行注意：
- 上传顺序要和评论中的截图顺序保持一致。
- 导出按钮若置灰或不可点，评论必须写页面实际状态，不能写成“导出成功”。
- API 评论成功后，默认不再重复登录网页写同样的评论。
- 字段顺序固定，不再使用“回归信息/回归页面”等其他变体标题。

#### 2.5 自动化测试覆盖（如已配置）

```bash
# 运行登录模块相关的单元测试
npm run test -- --testPathPattern="login"

# 运行集成测试
npm run test:integration

# 预期：所有相关测试通过
```

**输出**：测试报告（通过率、失败用例）

---

### 第 3 步：生成回归报告

#### 3.1 填充模板

使用 [regression-report.template.md](./assets/regression-report.template.md)：

```markdown
## 基本信息

- **Bug ID**：1119626
- **完整 ID**：1165152329001119626
- **所属池子**：企微需求_交付池（workspace_id: 65152329）
- **执行时间**：2026-03-23 14:30:00
- **执行人**：张三

## 最终结论

### 回归状态
- [x] **Pass**：问题单所有验证项通过，无遗留问题

### 详细说明
1. 精确复现：✓ 已确认原始问题存在（边框红色）
2. 修复验证：✓ 修复后边框颜色正确（蓝色）
3. 相邻流程：✓ 注册、密码重置、OAuth 流程输入框样式正常
4. 自动化测试：✓ 登录模块 20 个单元测试全部通过
5. 交叉浏览器：✓ Chrome、Firefox、Safari 样式一致

## 关键证据

### 截图
- 修复前：【粘贴截图】- 输入框边框为红色
- 修复后：【粘贴截图】- 输入框边框为蓝色  
- 相邻流程：【粘贴截图】- 其他模块输入框样式正常

### 测试输出
\`\`\`
$ npm run test -- --testPathPattern="login"
PASS  tests/login.test.js
  ✓ 登录页面加载 (125ms)
  ✓ 输入框获焦样式 (98ms)
  ✓ 输入框边框颜色 (105ms)
  ...
Test Suites: 1 passed
Tests: 20 passed
\`\`\`
```

#### 3.2 确定结论

4 种结论类型，选一个：

| 结论 | 何时使用 | 示例 |
|---|---|---|
| **Pass** | 所有验证项目都通过 | 问题已完全修复，无遗留 |
| **Fail** | 发现某项验证失败 | 修复后边框仍显示为橙色，非蓝色 |
| **Blocked** | 无法执行回归 | 被测应用无法启动，环境不可用 |
| **Partial** | 部分验证项通过，部分未覆盖 | 修复主流程已验证，但跨浏览器未测（缺浏览器环境） |

---

## 跨池回归场景

### 场景 A：同编号 bug 在多个池中

如果这个 bug 同时出现在交付池、产研池、售后池，你可以逐个回归：

```bash
# 第 1 轮：在交付池回归（主要池）
/tapd-bug-regression 1119626 --workspace 交付池
→ 生成：regression-report-1119626-delivery.md

# 第 2 轮：在产研池回归
/tapd-bug-regression 1119626 --workspace 产研池
→ 生成：regression-report-1119626-research.md

# 第 3 轮：在售后池回归
/tapd-bug-regression 1119626 --workspace 售后池
→ 生成：regression-report-1119626-support.md
```

每个池会生成独立的报告，因为：
- 环境配置不同（生产 vs 开发）
- 测试账号权限不同（客户 vs 内部）
- SLA 要求不同（24h vs 1 周）
- 回归深度要求不同（VIP 客户 vs 普通）

### 场景 B：跨池级联影响

如果一个修复影响多个池的功能：

1. **产研池确认**：代码修复已正确实现
2. **交付池确认**：修复已部署到测试/预发环境
3. **售后池确认**：修复已上线到生产，客户可验证

---

## 常见问题

### Q1：如何判断应该选哪个池？

**根据 bug 链接**：
- 链接中 `/tapd_fe/65152329/` → 交付池
- 链接中 `/tapd_fe/44949107/` → 产研池
- 链接中 `/tapd_fe/41700174/` → 售后池

**根据 bug 特性**：
- 客户反馈、现场问题 → 售后池 (41700174)
- 交付团队发现的功能缺陷 → 交付池 (65152329)
- 产品/技术企划的需求 bug → 产研池 (44949107)

### Q2：回归失败了怎么办？

如果回归状态为 **Fail** 或 **Blocked**，在报告中记录：

1. **失败现象**：具体哪一步失败
2. **失败原因**：是环境问题？代码问题？配置问题？
3. **重新分配**：是否需要转回给工程师、回到交付池等

然后将报告贴回 bug 的评论区，工程师或 PM 会看到并跟进。

### Q3：自动化测试不存在怎么办？

如果没有现成的自动化测试，仍然可以通过手动验证完成回归。

在报告的"建议后续"中补充：
```
- [ ] 需要补充 UI 自动化测试（登录输入框样式验证）
- [ ] 需要补充跨浏览器兼容性测试
```

### Q4：能否对某个已关闭的 bug 重新回归？

可以。有时需要对旧 bug 做回归验证（如升级版本、回滚确认等）。过程相同，只需确保：
1. 环境配置与当时保持一致（或明确说明版本差异）
2. 在报告的"环境配置"章节说明时间跨度

---

## 与 TAPD Skill 的集成

这个 bug 回归 skill 在以下环节依赖 TAPD skill：

| 环节 | 依赖 TAPD Skill 的能力 | 调用方式 |
|---|---|---|
| Bug 详情查询 | `bug-get` | 自动执行 |
| 跨池切换 | workspace_id 映射 | `--workspace` 参数驱动 |
| 补充信息 | `bug-fields-info` | 需要时手动调用 |
| 添加验证评论 | `comment-add` | 回归完成后可选调用 |
| 更新 bug 状态 | `bug-update` | 验证完成后可选调用 |

## 状态回写规则（按池子）

仅在你确认“验证通过”后执行：

| 问题池 | workspace_id | 通过后状态 |
|---|---|---|
| 交付池 | 65152329 | 已关闭 |
| 产研池 | 44949107 | 线上验证 |
| 售后池 | 41700174 | 线上验证 |

评论内容要求：
- 包含“验证通过”
- 包含验证通过截图信息（文件名、路径或链接）

使用示例：

```bash
# 当需要查看交付池的所有缺陷状态值时（补充回归报告）
python3 "$TAPD_SCRIPT" bug-fields-info --workspace-id 65152329

# 当回归完成后，想在 TAPD 上添加验证评论
python3 "$TAPD_SCRIPT" comment-add \
  --workspace-id 65152329 \
  --entry-type bug \
  --entry-id 1119626 \
  --description "✓ 验证通过。结论：Pass。截图：login-pass.png, flow-pass.png" \
  --author CURRENT_USER

# 当交付池验证通过后，更新 bug 为"已关闭"
python3 "$TAPD_SCRIPT" bug-update \
  --workspace-id 65152329 \
  --id 1119626 \
  --status "已关闭" \
  --current-user CURRENT_USER

# 当产研池或售后池验证通过后，更新 bug 为"线上验证"
python3 "$TAPD_SCRIPT" bug-update \
  --workspace-id 44949107 \
  --id 1119626 \
  --status "线上验证" \
  --current-user CURRENT_USER
```

若验证失败或阻塞：
- 不执行“已关闭/线上验证”状态更新
- 评论记录失败或阻塞原因，并附相关截图

---

## 最佳实践

1. **尽早启动回归**：Bug 修复完成后立即开始回归，不要等待
2. **充分利用自动化**：如果已有自动化测试，优先运行覆盖相关功能
3. **关键证据要齐全**：至少要有修复前后的截图或日志对比
4. **跨环境验证**：P1 bug 要在测试、预发、生产环境各验证一次
5. **先确认再回写**：先由你确认验证结果，再执行状态和评论更新
6. **记录异常**：如果发现回归过程中的环境问题或其他缺陷，一并记录

---

**文档版本**：v2.0  
**最后更新**：2026-03-23  
**维护人**：[your_team]

---

## 下载弹窗优化策略（自动化）

当 Playwright 点击下载触发系统“另存为”弹窗时，可能出现未点击“保存”导致无法证明文件已落地的问题。后续统一按以下策略执行：

1. 优先使用 Playwright 下载事件捕获（download event）并保存到证据目录：
   - 点击下载前先注册下载事件监听；
   - 触发后保存到本地证据目录；
   - 校验文件大小大于 0 视为“落地下载成功”。
2. 若系统级弹窗不可控，改走“网络响应校验”：
   - 通过下载 URL 或同源请求拿到响应；
   - 校验 HTTP 状态码为 200；
   - 校验响应体非空。
3. 若仍无法直接拿到下载响应，按“下载链路验证”作为兜底：
   - 页面出现“导出完成”与“下载导出文件”；
   - 页面无 00401/no authority/失败提示；
   - 下载链接可访问或可预览；
   - 全部关键节点截图留证。
4. 回写评论必须声明下载验证方式：
   - “已实际落地下载并验证”，或
   - “按网络响应完成下载可用性验证”，或
   - “受系统保存弹窗限制，按链路与链接可访问性完成验证”。
5. 最小证据集固定为三张：
   - 导出完成截图；
   - 下载对象可访问/可预览截图；
   - 无 00401 错误截图。

---
