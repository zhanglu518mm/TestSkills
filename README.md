# TestSkills — 测试技能套件

为测试团队提供的 GitHub Copilot 自定义 skill 集合，覆盖 TAPD bug 回归、问题单助手等常用测试工作流。

---

## 包含的 Skills

| Skill | 入口文件 | 功能描述 |
|---|---|---|
| `tapd-bug-regression` | `.github/skills/tapd-bug-regression/SKILL.md` | 输入 TAPD bug 单 ID 和环境地址，自动查询详情、打开环境执行回归、截图留证、回写状态与评论 |
| `issue-regression-assistant` | `.github\skills\issue-regression-assistant\SKILL.md` | 通用问题单回归助手，支持自定义问题池配置 |

---

## 快速上手（每位成员只需做一次）

### 第一步：克隆仓库

```powershell
git clone https://github.com/zhanglu518mm/TestSkills.git
cd TestSkills
```

### 第二步：配置 TAPD 凭证

运行初始化脚本，按提示填入你自己的 TAPD 用户名和 API Token：

```powershell
powershell -ExecutionPolicy Bypass -File .github/skills/tapd-bug-regression/scripts/bootstrap-user-env.ps1
```

脚本会在本地生成 `local.env.ps1`（**此文件已被 `.gitignore` 忽略，不会上传**），并将凭证写入你的 PowerShell Profile，之后新开终端自动生效。

> 如果不想写入 Profile，加上 `-SkipProfileUpdate` 参数，每次手动执行 `. local.env.ps1` 加载即可。

### 第三步：在 VS Code 中打开仓库

```powershell
code .
```

打开后，Copilot 会自动识别 `.github/skills/` 下的所有 skill，即可在对话中使用。

---

## 使用方式

在 VS Code Copilot Chat 中直接输入自然语言或 skill 命令：

```
# 回归交付池 bug 1119626，环境是 https://test.example.com
回归问题单 1119626，环境地址是 https://test.example.com

# 指定产研池
/tapd-bug-regression 1234567 --workspace 产研池

# 贴完整链接，自动识别池子
/tapd-bug-regression https://www.tapd.cn/tapd_fe/65152329/bug/detail/1165152329001119626
```

Copilot 会自动：
1. 查询 TAPD 获取 bug 详情
2. 使用 Playwright 打开回归环境（等你扫码登录）
3. 按 bug 步骤执行验证并截图存入 `evidence/` 目录
4. 汇报结论，等你确认后回写 TAPD 状态与评论

---

## 问题池对照表

| 池名 | workspace_id | 适用场景 |
|---|---|---|
| 交付池 | 65152329 | 来自交付流程的缺陷 |
| 产研池 | 44949107 | 产品 / 研发规划的 bug |
| 售后池 | 41700174 | 来自客户反馈的缺陷 |

---

## 目录结构

```
TestSkills/
├── .github/
│   └── skills/
│       ├── tapd-bug-regression/      # TAPD 回归 skill
│       │   ├── SKILL.md              # Skill 定义（Copilot 读取）
│       │   ├── README.md             # 详细使用说明
│       │   ├── assets/               # 配置模板、报告模板
│       │   ├── scripts/              # 初始化脚本
│       │   └── references/           # 工作流参考文档
│       └── issue-regression-assistant/  # 通用问题单回归 skill
│           ├── SKILL.md
│           ├── assets/
│           ├── scripts/
│           └── references/
├── evidence/                         # 回归截图（本地保留，不上传）
└── .gitignore
```

---

## 注意事项

- `evidence/` 目录下的截图**只保存在本地**，不会上传至 GitHub。
- 个人 TAPD 凭证文件 `local.env.ps1` 同样不上传，请勿手动提交。
- 若推送有新的 skill 或规则更新，成员执行 `git pull` 即可同步。
