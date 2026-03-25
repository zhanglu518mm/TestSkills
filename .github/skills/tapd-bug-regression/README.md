# TAPD Bug 回归 Skill（通用版）

针对 TAPD 任意 bug 单的专用、可复用的回归 skill。支持交付池、产研池、售后池的跨池查询和回归。

## 特性

✅ **动态 bug ID 支持**：无需修改 skill，直接输入任意 bug ID  
✅ **自动化查询**：从 TAPD API 直接拉取 bug 详情  
✅ **智能规划**：根据 bug 优先级、属性自动生成回归策略  
✅ **跨池支持**：一个 skill，支持三个独立的问题池  
✅ **模板化报告**：结构化的回归报告模板，包含证据、结论、后续建议  
✅ **与 TAPD skill 集成**：复用现有的 TAPD API 调用能力  
✅ **Playwright 优先**：默认使用 Playwright 打开环境、页面操作与截图  
✅ **完全中文**：完整的中文文档和模板，开箱即用  

## 目录结构

```
tapd-bug-regression/
├── SKILL.md                              # 📌 Skill 主文档（必读）
├── README.md                             # 📖 快速开始指南  
├── assets/
│   ├── regression-report.template.md     # 回归报告模板（可填空）
│   └── config-pools.yaml                 # 三个问题池的配置规则
└── references/
    └── usage.md                          # 详细的工作流与使用指南
```

## 快速开始

### 前置条件

1. **已安装 TAPD skill**  
   路径：`~/.openclaw/skills/tapd/`

2. **TAPD API 凭证已配置**  
   环境变量：`TAPD_API_TOKEN`、`TAPD_API_USER`、`TAPD_API_PASSWORD`

3. **Python 3.6+**  
   ```bash
   python3 --version
   ```

### 团队共享下的凭证规范（重要）

1. 仓库中只提交模板，不提交任何真实 token 或密码。
2. 每个成员使用自己的 TAPD 凭证，写入本地 `local.env.ps1`。
3. `local.env.ps1` 已被 `.gitignore` 忽略，不会进入版本库。

初始化步骤：

```powershell
powershell -ExecutionPolicy Bypass -File .github/skills/tapd-bug-regression/scripts/bootstrap-user-env.ps1
```

说明：该脚本会交互式采集个人凭证，自动生成 `local.env.ps1`，并默认写入 `$PROFILE` 实现新终端自动加载。

如不希望写入 `$PROFILE`：

```powershell
powershell -ExecutionPolicy Bypass -File .github/skills/tapd-bug-regression/scripts/bootstrap-user-env.ps1 -SkipProfileUpdate
```

### 使用方式

在对话中输入：

```bash
# 查询交付池中的 bug 1119626
/tapd-bug-regression 1119626

# 或贴完整链接（自动识别池子）
/tapd-bug-regression https://www.tapd.cn/tapd_fe/65152329/bug/detail/1165152329001119626

# 指定产研池
/tapd-bug-regression 1234567 --workspace 产研池

# 指定售后池
/tapd-bug-regression 1234567 --workspace 售后池
```

## 工作流

```
1. 输入 bug ID / 链接 和 问题池（可选）
   ↓
2. Skill 自动查询 TAPD 拉取 bug 详情
   ↓
3. 使用 Playwright 打开回归环境并等待扫码登录
   ↓
4. 智能生成回归范围（基于优先级、属性）
   ↓
5. 按问题单步骤执行回归验证并截图留证
   ↓
6. 填充回归报告模板
   ↓
7. 生成最终结论（Pass / Fail / Blocked / Partial）
```

说明：若当前会话无法启用页面交互能力，流程会降级为手工协同模式。

## 问题池说明

| 池名 | workspace_id | 用途 | 何时使用 |
|---|---|---|---|
| 交付池 | 65152329 | 交付团队的缺陷、客户级 bug | bug 来自交付流程 |
| 产研池 | 44949107 | 产品和研发的需求 bug、技术债 | bug 来自产品/研发规划 |
| 售后池 | 41700174 | 客户反馈、售后维保缺陷 | bug 来自客户反馈 |

**默认**：交付池 (65152329)

## 文件说明

### SKILL.md（必读）
- Skill 的核心定义和工作流
- 7 个执行步骤的详细说明
- 输出规范

### references/usage.md（推荐）
- 完整的工作流演示
- 与 TAPD skill 的集成方式
- 跨池回归场景说明
- 常见问题与排查

### assets/regression-report.template.md
- **回归报告模板**（填空式）
- 包含：基本信息、问题详情、执行检查、关键证据、最终结论、剩余风险

### assets/config-pools.yaml
- 三个问题池的详细配置
- 缺陷状态流转规则
- 优先级 / SLA / 客户级别映射
- 环境配置示例
- 跨池流程说明

## 与 TAPD Skill 的集成

这个 skill 自动调用 TAPD skill 的以下能力：

| 功能 | 对应 TAPD 命令 | 调用时机 |
|---|---|---|
| 查询 bug 详情 | `bug-get` | 自动 |
| 查询池中所有 bug | `bug-list` | 可选 |
| 查询字段配置 | `bug-fields-info` | 需要时 |
| 添加验证评论（纯文本兜底） | `comment-add` | 仅网页评论贴图不可用时 |
| 更新 bug 状态 | `bug-update` | 验证完后可选 |

评论回写默认策略（强制）：
- 先走 TAPD 网页评论编辑器，复制粘贴图片到评论区。
- 粘贴失败时使用附件上传并在评论中引用。
- API 评论仅用于无图兜底，不可替代网页贴图。

更多细节见 [references/usage.md](./references/usage.md#与-tapd-skill-的集成)

## 示例场景

### 场景 1：单池回归任意 bug

```bash
# 交付池中的 bug 1119626
/tapd-bug-regression 1119626

# 交付池中的其他 bug
/tapd-bug-regression 2024568

# → 自动拉取对应 bug 详情
# → 输出初步回归计划与模板
# → 你执行验证步骤
# → 填充报告得出结论
```

### 场景 2：跨池对比回归

```bash
# 同编号 bug 在多个池中出现，需要逐个验证

# 第 1 轮：交付池（主要池）
/tapd-bug-regression 1119626 --workspace 交付池

# 第 2 轮：产研池（确认源头修复）
/tapd-bug-regression 1119626 --workspace 产研池

# 第 3 轮：售后池（确认客户影响）
/tapd-bug-regression 1119626 --workspace 售后池

# → 生成 3 个独立的报告，各池结论可能不同
```

### 场景 3：从链接直接回归

```bash
# 粘贴 TAPD 链接，自动识别池子和 bug ID
/tapd-bug-regression https://www.tapd.cn/tapd_fe/44949107/bug/detail/1144949107001234567

# → 自动识别产研池（workspace_id=44949107）
# → 自动提取 bug ID
# → 执行回归流程
```

## 常见问题

### Q：如何知道 bug 在哪个池中？

A：从 TAPD 链接中识别：

- `https://www.tapd.cn/tapd_fe/65152329/...` → 交付池
- `https://www.tapd.cn/tapd_fe/44949107/...` → 产研池
- `https://www.tapd.cn/tapd_fe/41700174/...` → 售后池

或在 TAPD 页面的左上角看项目名称。

### Q：同一个 bug 在多个池中怎么验证？

A：逐个使用 `--workspace` 参数切换，为每个池生成独立报告。

```bash
/tapd-bug-regression 1119626 --workspace 交付池
/tapd-bug-regression 1119626 --workspace 产研池
/tapd-bug-regression 1119626 --workspace 售后池
```

### Q：验证失败了怎么办？

A：在报告的"最终结论"选择 **Fail** 或 **Blocked**，并详细说明：
- 失败现象
- 失败原因
- 建议后续处理

然后贴回 TAPD 作为评论，工程师或 PM 会看到。

## 相关资源

- [TAPD Skill](../../tapd/SKILL.md)：通用的 TAPD 操作能力
- [TAPD 官方文档](https://www.tapd.cn/help/index)：TAPD 操作教程

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v2.0 | 2026-03-23 | 改造为通用版本，支持任意 bug ID 和动态池子选择 |
| v1.0 | 2026-03-23 | 初始版本，针对 bug 1119626 的专用版本 |

安全提醒：不要把个人 token 写进 `README.md`、`SKILL.md`、`usage.md` 或任何会提交到仓库的文件。

---

**Skill 名称**：tapd-bug-regression  
**Skill ID**：tapd-bug-regression  
**维护者**：[你的名字]  
**最后更新**：2026-03-23
