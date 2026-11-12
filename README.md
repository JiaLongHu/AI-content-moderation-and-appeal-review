# AI 文字内容审核与申诉复核系统

一个面向综合兴趣文字社区的前后端分离最小原型。系统对帖子、一级评论和一层回复执行“基础规则 + AI模型 + 固定置信度阈值”审核，并提供L2人工审核与一次性申诉终审闭环。

## 功能概览

- 四个预置账号：两个普通用户、一个内容审核员、一个申诉复核员；
- JWT登录、当前用户识别和后端角色权限校验；
- 纯文字帖子、一级评论和一层回复；
- 八类风险类别和L0～L4风险等级；
- L0/L1高置信度自动发布，L3/L4高置信度自动拒绝，其余进入L2；
- AI连接失败、超时、服务错误或非法输出统一安全降级到L2；
- 内容审核员可调整类别和等级，并执行“通过并发布”或“拒绝发布”；
- 被拒绝内容的作者可以提交一次10～500字的文字申诉；
- 申诉复核员可以通过申诉并发布，或驳回申诉并维持拒绝；
- 公共页面只展示已发布内容，不泄漏审核类别、等级、置信度和原因；
- 用户可以在“我的内容”和“我的申诉”查看自己的处理状态。

本原型不包含管理员、举报、下架、账号处罚、内容编辑、内容删除、图片、附件、通知、搜索、分页和多轮申诉。

## 审核规则

| AI结果 | 最终类别置信度 | 系统处理 |
| --- | ---: | --- |
| L0或L1 | ≥ 0.80 | 自动发布 |
| L0或L1 | < 0.80 | 转L2人工审核 |
| L2 | 任意 | 转L2人工审核 |
| L3或L4 | ≥ 0.90 | 自动拒绝，可申诉 |
| L3或L4 | < 0.90 | 转L2人工审核 |
| AI异常或结果非法 | — | 转L2人工审核 |

多标签结果使用`final_category`对应的置信度分流。评论首次只审核当前评论，无法确定时才补充所属帖子；回复只补充直接父评论和所属帖子，不读取完整评论区。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios、Element Plus；
- 后端：Python 3.12、FastAPI、Pydantic、SQLAlchemy、SQLite、PyJWT、httpx；
- 测试与质量：pytest、Ruff、Vitest、ESLint、vue-tsc；
- AI接口：兼容常见`/chat/completions`请求格式，不绑定具体模型厂商。

## 目录结构

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/          # 登录、论坛、人工审核和申诉接口
│  │  ├─ core/         # 配置与安全
│  │  ├─ db/           # 数据库连接与初始化
│  │  ├─ models/       # SQLAlchemy模型与业务枚举
│  │  ├─ moderation/   # 规则、AI客户端、结构校验与分流
│  │  ├─ schemas/      # API数据模型
│  │  └─ services/     # 最小上下文等领域服务
│  └─ tests/
├─ frontend/
│  └─ src/
│     ├─ api/          # 后端API调用
│     ├─ router/       # 路由与角色守卫
│     ├─ stores/       # 登录状态
│     ├─ types/        # TypeScript类型
│     └─ views/        # 三类角色页面
├─ 需求分析.md
├─ plan.md
├─ dev-workflow.md
├─ task.md
└─ ai-log.md
```

## 环境要求

- Python 3.12；
- Node.js 24推荐，最低版本为20.19；
- npm 10或更高版本；
- Windows PowerShell示例命令均从项目根目录执行。

## 当前本地运行方式（2026-11-12）

当前版本已接入 DeepSeek，版本提交为 `3e90a60`（接入deepseek审核v1）。接口仍保持兼容聊天补全协议，其他厂商可以通过环境变量替换。

本机已建立 `.venv-local`，使用 Python 3.12.14 和 Node.js 24.22.1。原 `.venv` 来自其他机器，不应继续使用。以下通用安装章节适用于新环境；本机直接执行：

```powershell
.\start-local.ps1
```

脚本依赖本机 Codex 缓存中的 Node.js 24 和项目内 `.venv-local`，在后台启动服务；已监听的端口会被跳过。它不执行重启，也不会安装依赖。修改 `.env` 后需重启后端。日志位于根目录的 `backend-server.log`、`backend-error.log`、`frontend-server.log` 和 `frontend-error.log`。

本机后端验证命令：

```powershell
.\.venv-local\Scripts\python.exe -m pytest backend\tests -q
```

四个账号的初始密码取自本机 `.env` 的 `SEED_DEFAULT_PASSWORD`，不在版本库中记录。已有数据库密码不会因修改该变量自动更新。不要用示例文件覆盖已经配置好的 `.env`。

本轮验证：后端72项测试通过，前端类型检查、生产构建及1项测试通过；健康检查、登录、发帖接口均正常。真实 DeepSeek 将日常散步帖子判为 normal/L0、置信度0.99，系统自动发布。此结果是一次接入验证，不代表模型对所有内容的准确率。

## 安装

### 1. 后端依赖

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
```

如果系统没有`py`命令，可以使用已安装的Python 3.12可执行文件创建虚拟环境。

### 2. 前端依赖

```powershell
npm --prefix frontend ci
```

## 配置

复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

编辑`.env`：

```dotenv
JWT_SECRET_KEY=请替换为足够长的随机字符串
SEED_DEFAULT_PASSWORD=请设置四个演示账号的共同初始密码
DATABASE_URL=sqlite:///./backend/data/app.db
FRONTEND_ORIGIN=http://localhost:5173
AI_API_BASE_URL=https://api.deepseek.com
AI_API_KEY=你的服务密钥
AI_MODEL=deepseek-chat
AI_TIMEOUT_SECONDS=10
```

真实密钥不得写入前端代码或提交到版本库。缺少AI配置或AI调用失败时，系统会将内容安全降级到L2，而不是自动放行。

## 初始化数据库

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.init_db
```

初始化命令可以重复执行，不会创建重复账号。四个账号使用`SEED_DEFAULT_PASSWORD`指定的共同初始密码：

| 用户名 | 角色 | 登录后入口 |
| --- | --- | --- |
| `user_a` | 普通用户A | `/forum` |
| `user_b` | 普通用户B | `/forum` |
| `content_reviewer` | 内容审核员 | `/moderation` |
| `appeal_reviewer` | 申诉复核员 | `/appeals` |

`SEED_DEFAULT_PASSWORD`只用于创建尚不存在的账号，不会覆盖已有账号密码。如果需要重置纯本地演示库，应先确认没有需要保留的数据，再删除`backend/data/app.db`并重新初始化。

## 启动

打开两个PowerShell窗口。

后端：

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```powershell
npm --prefix frontend run dev
```

访问地址：

- 前端：<http://localhost:5173>
- 后端健康检查：<http://127.0.0.1:8000/health>
- OpenAPI文档：<http://127.0.0.1:8000/docs>

## AI接口约定

系统向`{AI_API_BASE_URL}/chat/completions`发送聊天补全请求，并要求模型返回单个JSON对象：

```json
{
  "categories": [
    {"category": "harassment", "confidence": 0.93}
  ],
  "final_category": "harassment",
  "final_level": "L3",
  "reason": "内容包含针对他人的攻击性表达"
}
```

合法类别为：`normal`、`sexual`、`violence`、`illegal_fraud`、`hate_discrimination`、`harassment`、`privacy`和`spam_advertising`。后端会拒绝缺失字段、未知类别、重复类别、越界置信度、非法等级和不一致的最终类别。

## 测试与检查

后端：

```powershell
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

前端：

```powershell
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
npm --prefix frontend audit
```

## 面试演示建议

1. 使用`user_a`提交正常内容，展示自动发布；
2. 提交低置信度或模型无法确定的内容，展示其进入“等待人工审核”；
3. 使用`content_reviewer`调整为L0/L1并发布，或调整为L3/L4并拒绝；
4. 使用`user_a`对被拒绝内容提交一次文字申诉；
5. 使用`appeal_reviewer`复核，展示申诉通过后发布或申诉驳回；
6. 使用`user_b`确认公共页面只出现最终已发布内容；
7. 展示AI超时或非法响应测试，说明系统采用失败安全的L2降级策略。

## 关键设计说明

- AI只负责分类建议，业务动作由后端固定规则决定；
- 人工审核的L0/L1只能发布，L3/L4只能拒绝，L2不能作为终态；
- 申诉终审的L0/L1只能通过，L3/L4只能驳回；
- 所有权限判断均在后端执行，前端路由守卫只用于改善交互；
- 密码使用Argon2哈希保存，JWT密钥和AI密钥仅由后端环境变量读取；
- 当前使用SQLite和同步审核，适合本地演示，不代表生产部署方案。

## 已知限制

- 没有数据库迁移工具；模型变更时需在确认无保留数据后重建本地演示库；
- 没有异步任务队列，AI调用期间请求会等待；
- 没有分页、搜索、通知、监控和生产级部署配置；
- 模型自报置信度只用于原型分流，不代表统计校准概率；
- 2026-11-12 安装时 npm 审计报告15项漏洞（13项中危、2项高危），尚未升级处理。

完整产品范围、规则和验收标准请参阅[需求分析.md](需求分析.md)、[dev-workflow.md](dev-workflow.md)和[task.md](task.md)。


## 审核工作台补充功能

内容审核员可以切换待审核与历史审核记录。历史详情只读，展示原审核决定、审核员和完成时间；当前等级可能已被后续申诉更新，不作为历史等级快照。

待审核详情的“下一条”只切换任务，不提交当前修改。提交通过或拒绝后自动打开队列中下一条待审核内容；队列为空时返回列表并提示处理完毕。
