# 配置与使用

## 目标

通过把流程与系统细节拆开，让这个 skill 可以在个人和团队之间复用。

## 如何配置

把 [../assets/issue-pool.config.template.yaml](../assets/issue-pool.config.template.yaml) 复制为真实项目配置文件，并补齐以下字段。

### 1. 问题单查询

- `tracker_name`：可读的问题系统名称，例如 Jira 或 Azure DevOps
- `lookup_mode`：`browser`、`api` 或 `cli`
- `issue_url_template`：带 `{id}` 占位符的直接访问地址模板
- `search_url`：当系统不支持直接打开问题单时使用的搜索页面
- `api_endpoint_template`：使用 API 查询时，带 `{id}` 占位符的接口地址模板

### 2. 认证方式

- `auth_requirements`：描述是否需要浏览器登录、Cookie 会话、Token 或 VPN
- `access_notes`：任何项目特有的访问前置条件

### 3. 被测应用

- `app_type`：`web`、`desktop`、`service`、`job` 或 `mixed`
- `working_directory`：仓库根目录或应用根目录
- `start_commands`：启动应用或依赖环境所需的命令
- `base_urls`：一个或多个入口地址
- `feature_flags`：必须开启的功能开关
- `test_accounts`：验证所需的账号或角色

### 4. 回归规则

- `required_issue_fields`：开始执行前问题单必须具备的字段
- `adjacent_scope_rules`：除精确修复路径外，还必须检查的相邻流程
- `automation_commands`：可用时需要执行的现有测试命令
- `evidence_requirements`：最终结果中必须包含的证据类型

## 推荐调用方式

示例：

- `/issue-regression-assistant BUG-1234`
- `/issue-regression-assistant https://tracker.example.com/browse/BUG-1234`

## 预期行为

调用后，agent 应该：

1. 根据 ID 或链接定位问题单。
2. 读取问题单并总结回归目标。
3. 打开或启动目标应用。
4. 围绕变更行为执行回归检查。
5. 输出结构化报告。

## 个人使用与团队共享

个人使用时，可以把整个目录放到以下任一位置：

- `~/.copilot/skills/issue-regression-assistant/`
- `~/.agents/skills/issue-regression-assistant/`
- `~/.claude/skills/issue-regression-assistant/`

也可以直接使用安装脚本：[../scripts/install-personal-skill.ps1](../scripts/install-personal-skill.ps1)

团队共享时，把同一份目录提交到仓库中的 `.github/skills/issue-regression-assistant/`。