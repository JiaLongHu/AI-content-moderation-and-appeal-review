# AI 文字内容审核与申诉复核系统——开发计划

## 1. 计划概述

本计划依据 `需求分析.md` 制定，用于指导最小原型的开发、测试和验收。

- 项目形态：前后端分离的中文 Web 系统
- 前端：Vue 3 + TypeScript + Vite
- 后端：Python + FastAPI
- 数据库：SQLite + SQLAlchemy
- 认证：JWT
- 测试：pytest + Vitest
- 当前阶段：仅完成计划，尚未开始编码

## 2. 开发范围

本次开发包括：

- 四个预置账号登录与角色鉴权；
- 文字帖子、一级评论和一层回复；
- 基础规则与 AI 内容审核；
- L0～L4 风险分级与置信度分流；
- L2 人工内容审核；
- 被拒绝内容的一次性文字申诉；
- 申诉复核员人工终审；
- 普通用户、内容审核员和申诉复核员页面；
- 自动化测试、前后端联调和正式验收。

本次不开发：管理员、注册、游客访问、举报、下架、编辑、删除、账号处罚、通知、搜索、分页、图片与附件、无限层回复、数据大屏及生产级分布式基础设施。

## 3. 项目结构规划

```text
project-root/
├── backend/                 FastAPI 后端
│   ├── app/
│   │   ├── api/             REST API
│   │   ├── core/            配置、认证与公共能力
│   │   ├── db/              数据库连接与初始化
│   │   ├── models/          SQLAlchemy 模型
│   │   ├── schemas/         Pydantic 请求与响应模型
│   │   ├── services/        审核、内容、申诉等业务服务
│   │   └── main.py          应用入口
│   └── tests/               后端测试
├── frontend/                Vue 3 前端
│   └── src/
│       ├── api/             API 客户端
│       ├── components/      通用组件
│       ├── router/          路由及守卫
│       ├── stores/          Pinia 状态
│       ├── types/           TypeScript 类型
│       └── views/           页面
├── 需求分析.md
├── plan.md
└── ai-log.md
```

## 4. 开发阶段总览

| 阶段 | 主要内容 | 依赖 | 计划状态 |
| --- | --- | --- | --- |
| P0 | 环境与项目初始化 | 无 | 未开始 |
| P1 | API 契约与状态机 | P0 | 未开始 |
| P2 | 数据库与预置数据 | P1 | 未开始 |
| P3 | JWT 登录与角色鉴权 | P2 | 未开始 |
| P4 | AI 审核核心能力 | P2 | 未开始 |
| P5 | 帖子、评论与回复 | P3、P4 | 未开始 |
| P6 | L2 人工内容审核 | P5 | 未开始 |
| P7 | 申诉与人工复核 | P6 | 未开始 |
| P8 | 普通用户前端 | P3、P5、P7 | 未开始 |
| P9 | 审核与复核前端 | P6、P7 | 未开始 |
| P10 | 联调、安全与回归测试 | P8、P9 | 未开始 |
| P11 | 正式验收与交付 | P10 | 未开始 |

## 5. 详细任务

## P0 环境与项目初始化

### P0-1 检查开发环境

**任务**

- 确认 Python、Node.js 和 npm 可用；
- 建议使用 Python 3.11 或 3.12；
- 确认当前目录中的需求文档；
- 检查项目是否已经初始化 Git；
- 检查是否存在额外项目约束文件。

**验证命令**

```powershell
py --version
node --version
npm --version
Test-Path -LiteralPath '需求分析.md','plan.md','ai-log.md'
rg --files -g 'AGENTS.md'
git rev-parse --is-inside-work-tree
```

**通过标准**

- Python、Node.js 和 npm 均可执行；
- 三份项目文档存在；
- 已明确 Git 和项目约束状态。

### P0-2 创建后端工程

**任务**

- 创建 `backend/` 目录；
- 创建 Python 虚拟环境；
- 安装 FastAPI、Uvicorn、SQLAlchemy、Pydantic、JWT、密码哈希、httpx、pytest 和 Ruff；
- 创建最小 FastAPI 应用和健康检查接口；
- 建立测试与静态检查配置；
- 创建环境变量示例文件，不写入真实密钥。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

后端启动后执行：

```powershell
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health'
```

**通过标准**

- 后端可以启动；
- `/health` 返回正常状态；
- Ruff 和 pytest 通过。

### P0-3 创建前端工程

**任务**

- 创建 Vue 3 + TypeScript + Vite 项目；
- 安装 Vue Router、Pinia、Axios 和 Element Plus；
- 配置 ESLint、TypeScript 检查和 Vitest；
- 创建最小启动页和环境变量示例文件。

**验证命令**

```powershell
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

**通过标准**

- 前端可正常启动和构建；
- lint、类型检查和测试均通过；
- 前端不存在真实 AI 密钥或 JWT 密钥。

## P1 API 契约与状态机

### P1-1 定义业务枚举

**任务**

- 定义普通用户、内容审核员、申诉复核员三类角色；
- 定义帖子、评论、回复三种内容类型；
- 定义八类审核结果；
- 定义 L0～L4；
- 定义内容状态与申诉状态；
- 统一前后端使用的枚举值。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\domain\test_enums.py -q
npm --prefix frontend run type-check
```

**通过标准**

- 后端枚举测试通过；
- 前端类型与后端约定一致；
- 不存在管理员、举报、下架、编辑或删除相关枚举。

### P1-2 定义状态转换规则

**任务**

- 定义 L0/L1 自动发布；
- 定义 L2 进入人工审核；
- 定义 L3/L4 自动拒绝；
- 定义人工通过只能使用 L0/L1；
- 定义人工拒绝只能使用 L3/L4；
- 定义 L2 不能成为人工审核或申诉终态；
- 定义内容最多申诉一次。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\domain\test_state_machine.py -q
```

**通过标准**

- 合法转换测试通过；
- L3/L4 发布、L0/L1 拒绝、L2 作为人工终态等非法转换均被阻止。

### P1-3 定义 REST API 契约

**任务**

- 确定 `/api/v1` 接口前缀；
- 定义登录与当前用户接口；
- 定义帖子、评论、回复接口；
- 定义“我的内容”接口；
- 定义 L2 审核任务接口；
- 定义申诉提交和“我的申诉”接口；
- 定义申诉复核任务接口；
- 统一错误响应格式。

**验证命令**

后端启动后执行：

```powershell
$openapi = Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/openapi.json'
$openapi.info.title
$openapi.paths.PSObject.Properties.Name | Sort-Object
```

**通过标准**

- OpenAPI 文档可以生成；
- 核心资源接口完整；
- 不存在管理员、举报、下架、编辑或删除接口。

## P2 数据库与预置数据

### P2-1 建立数据模型

**任务**

- 建立用户模型；
- 建立统一内容模型，支持帖子、评论和回复；
- 建立审核结果模型；
- 建立人工审核任务模型；
- 建立申诉模型；
- 建立表关系、唯一约束和必要索引。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\db\test_models.py -q
```

**通过标准**

- 所有表可以创建；
- 帖子、评论、回复关系正确；
- 一条内容最多关联一条申诉；
- 数据库约束与状态规则一致。

### P2-2 建立数据库初始化

**任务**

- 创建 SQLite 连接和会话管理；
- 创建幂等初始化命令；
- 初始化普通用户 A、普通用户 B、内容审核员和申诉复核员；
- 密码仅保存哈希；
- 原型阶段不引入 Alembic。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.init_db
.\.venv\Scripts\python.exe -m backend.app.db.init_db
.\.venv\Scripts\python.exe -m pytest backend\tests\db -q
```

**通过标准**

- 连续初始化两次不会产生重复账号；
- 四个账号角色正确；
- 数据库中不存在明文密码。

## P3 JWT 登录与角色鉴权

### P3-1 实现身份认证

**任务**

- 实现用户名和密码登录；
- 校验密码哈希；
- 生成和验证 JWT；
- 实现当前登录用户接口；
- JWT 密钥从后端环境变量读取；
- 不实现注册、找回密码和修改密码。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_auth.py -q
```

**通过标准**

- 四个预置账号均可登录；
- 错误用户名或密码不能生成有效 JWT；
- 未登录请求受保护接口被拒绝。

### P3-2 实现角色权限

**任务**

- 普通用户只能使用论坛和自己的内容、申诉接口；
- 内容审核员只能访问 L2 审核功能；
- 申诉复核员只能访问申诉复核功能；
- 所有权限必须由后端校验。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_permissions.py -q
```

**通过标准**

- 合法角色访问成功；
- 所有越权组合均返回无权限结果；
- 越权请求不会修改数据库。

## P4 AI 审核核心能力

### P4-1 实现审核结果结构

**任务**

- 定义风险类别及各类别置信度；
- 定义最终风险等级；
- 定义面向用户的简短原因；
- 校验类别、等级、置信度范围和必填字段；
- 不保存命中文字、内部理由、模型版本、Token 或成本。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_result_schema.py -q
```

**通过标准**

- 合法单标签和多标签结果通过；
- 缺字段、未知类别、非法等级和越界置信度均被拒绝。

### P4-2 实现基础规则层

**任务**

- 规范化待审核文本；
- 增加少量明确违禁词规则；
- 增加少量广告和联系方式特征；
- 规则采用后端固定配置，不提供管理页面；
- 避免模糊关键词直接导致高风险误拒。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_rules.py -q
```

**通过标准**

- 明确规则样例可被识别；
- 正常相似文本不会被简单误拒；
- 规则结果符合统一审核结构。

### P4-3 实现 AI 接口客户端

**任务**

- 从环境变量读取接口地址、密钥和模型名称；
- 使用 `httpx` 调用兼容聊天补全格式的接口；
- 设置连接和响应超时；
- 要求模型返回固定结构；
- 将用户内容作为不可信数据处理；
- 提供测试替身，稳定模拟 L0～L4、超时和非法响应；
- 不记录完整提示词、响应正文或密钥。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_ai_client.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\security\test_prompt_injection.py -q
```

**通过标准**

- 合法响应可以解析；
- 超时、连接失败和非法结构可以识别；
- 自动化测试不依赖真实外部接口；
- 帖子中的指令不能改变固定输出结构。

### P4-4 实现置信度分流

**任务**

- L0/L1 且置信度不低于 0.80：发布；
- L3/L4 且置信度不低于 0.90：拒绝；
- 其他情况统一转 L2；
- AI 超时、连接失败或结果非法统一转 L2；
- 多标签内容使用最终等级对应类别的置信度；
- 测试 0.79、0.80、0.89、0.90 等边界值。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_routing.py -q
```

**通过标准**

- 所有边界值符合需求；
- 异常不会自动放行或自动拒绝；
- L0～L4 分流结果正确。

## P5 帖子、评论与回复

### P5-1 实现帖子流程

**任务**

- 发布标题 1～100 字、正文 1～3000 字的帖子；
- 提交后调用审核服务；
- 保存审核结果和内容状态；
- 实现已发布帖子列表和详情；
- 列表按发布时间倒序；
- 不实现编辑和删除。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_posts.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_post_moderation_flow.py -q
```

**通过标准**

- 合法帖子进入正确审核路径；
- 非法长度被后端拒绝；
- 公共列表只包含已发布帖子；
- 等待审核和已拒绝帖子不会泄漏给其他用户。

### P5-2 实现评论与一层回复

**任务**

- 评论和回复限制 1～500 字；
- 只能评论已发布帖子；
- 只能回复已发布一级评论；
- 不允许回复继续嵌套；
- 评论和回复均经过审核；
- 详情页数据按时间正序返回；
- 不实现编辑和删除。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_comments.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_comment_moderation_flow.py -q
```

**通过标准**

- 一级评论和一层回复成功；
- 对未发布内容操作被拒绝；
- 无限嵌套被拒绝；
- 非公开评论和回复不会出现在公共详情中。

### P5-3 实现最小必要上下文

**任务**

- 帖子审核使用标题和正文；
- 评论先使用当前评论，需要补充时加入帖子标题和正文；
- 回复先使用当前回复，需要补充时加入父评论、帖子标题和正文；
- 不加载完整评论区。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_context_builder.py -q
```

**通过标准**

- 三种内容使用的上下文符合需求；
- 无关评论不会进入 AI 请求。

### P5-4 实现“我的内容”

**任务**

- 查询当前用户提交的帖子、评论和回复；
- 返回内容类型、文字摘要、状态、风险类别、等级和简短原因；
- 不实现搜索和分页；
- 不返回其他用户的未发布内容。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_my_contents.py -q
```

**通过标准**

- 用户 A 和用户 B 的非公开内容完全隔离；
- 各种审核状态显示正确。

## P6 L2 人工内容审核

### P6-1 实现待审核任务

**任务**

- L2 内容自动创建待审核任务；
- 列表只展示 L2；
- 详情包含原始内容、最小上下文、类别、等级、置信度和简短原因；
- 仅内容审核员可访问；
- 不设计领取、锁定、转交和高级审核。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_moderation_tasks.py -q
```

**通过标准**

- 低置信度和 AI 异常内容都生成 L2 任务；
- L0/L1/L3/L4 不进入待审核列表；
- 非审核员访问被拒绝。

### P6-2 实现人工决定

**任务**

- 审核员可以调整风险类别和等级；
- L0/L1 只能通过并发布；
- L3/L4 只能拒绝；
- L2 不能完成任务；
- 已完成任务不能重复处理；
- 人工拒绝后开放一次申诉。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_manual_review_flow.py -q
```

**通过标准**

- 合法决定正确更新内容状态；
- 非法等级和决定组合被拒绝；
- 已完成任务不能再次提交。

## P7 申诉与人工复核

### P7-1 实现申诉提交

**任务**

- 申诉说明限制 10～500 字；
- 只有内容作者可以申诉；
- 只有已拒绝内容可以申诉；
- 每条内容最多申诉一次；
- 不支持附件、补充材料和多轮申诉；
- 实现“我的申诉”。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_appeals.py -q
```

**通过标准**

- 合法申诉成功；
- 非作者、非拒绝内容、重复申诉和非法长度均被拒绝；
- 用户只能查看自己的申诉。

### P7-2 实现申诉终审

**任务**

- 实现待复核申诉列表和详情；
- 展示原内容、最小上下文、审核结果、置信度和申诉说明；
- L0/L1 只能通过申诉并发布；
- L3/L4 只能驳回申诉；
- L2 不能作为终审等级；
- 已处理申诉不能重复处理；
- 仅申诉复核员可访问。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_appeal_review_flow.py -q
```

**通过标准**

- 通过和驳回流程均正确；
- 非法等级与决定组合被拒绝；
- 终审后不能再次申诉或重复处理。

## P8 普通用户前端

### P8-1 实现登录与路由保护

**任务**

- 登录页；
- Pinia 登录状态；
- Axios 统一认证头；
- 路由守卫；
- 按角色跳转；
- 退出登录；
- 不提供注册和找回密码。

**验证命令**

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run type-check
npm --prefix frontend run lint
```

**通过标准**

- 未登录用户不能进入受保护页面；
- 三类角色登录后进入正确首页；
- 前端不显示其他角色导航。

### P8-2 实现论坛页面

**任务**

- 论坛首页；
- 发布帖子页；
- 帖子详情；
- 一级评论和一层回复；
- 字数提示和表单校验；
- 不增加搜索、分页、编辑或删除。

**验证命令**

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run type-check
npm --prefix frontend run lint
npm --prefix frontend run build
```

**通过标准**

- 用户可以完成发帖、评论和回复；
- 页面只显示已发布内容；
- 表单限制与后端一致；
- 构建通过。

### P8-3 实现“我的内容”和“我的申诉”

**任务**

- 展示自己的帖子、评论和回复；
- 展示审核状态、类别、等级和简短原因；
- 对可申诉内容展示申诉入口；
- 提交 10～500 字申诉说明；
- 展示申诉处理中、通过和驳回结果；
- 已申诉内容不再显示申诉按钮。

**验证命令**

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run type-check
npm --prefix frontend run build
```

**通过标准**

- 各状态显示正确；
- 申诉入口出现条件正确；
- 重复申诉在前端和后端均被阻止。

## P9 审核与复核前端

### P9-1 实现内容审核员页面

**任务**

- L2 待审核列表；
- 审核详情和最小上下文；
- 类别、等级、置信度和原因展示；
- 调整类别和等级；
- 通过或拒绝；
- 非法组合提示；
- 不提供转交、暂缓、下架和高级审核。

**验证命令**

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run type-check
npm --prefix frontend run lint
npm --prefix frontend run build
```

**通过标准**

- 审核员可以完整处理 L2；
- 非法等级与决定组合无法提交；
- 完成任务后该任务从待办列表消失。

### P9-2 实现申诉复核员页面

**任务**

- 待复核申诉列表；
- 原内容、上下文、审核结果和申诉说明；
- 调整类别和等级；
- 通过或驳回申诉；
- 非法组合提示；
- 不提供补充材料和再次申诉功能。

**验证命令**

```powershell
npm --prefix frontend run test -- --run
npm --prefix frontend run type-check
npm --prefix frontend run lint
npm --prefix frontend run build
```

**通过标准**

- 申诉通过和驳回均可完成；
- 非法等级与决定组合无法提交；
- 已处理申诉从待办列表消失。

## P10 联调、安全与回归测试

### P10-1 前后端联调

**必须打通的流程**

1. L0/L1 帖子自动发布，另一个普通用户可评论。
2. 低置信度内容进入 L2，审核员通过后发布。
3. L2 内容被审核员拒绝，用户申诉，复核员通过。
4. L3/L4 内容自动拒绝，用户申诉，复核员驳回。
5. AI 接口异常，内容安全降级到 L2。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

后端启动后执行：

```powershell
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health'
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/openapi.json' | Select-Object -ExpandProperty info
```

**通过标准**

- 五条流程均可通过正常页面操作完成；
- 页面刷新后状态不丢失；
- 前端、接口响应和数据库状态一致。

### P10-2 安全检查

**任务**

- 检查真实密钥和明文密码；
- 检查所有受保护接口；
- 检查非法枚举、超长文字和错误父级 ID；
- 检查 AI 非法输出降级；
- 检查提示注入样例；
- 检查 CORS 开发来源配置。

**验证命令**

```powershell
rg -n --hidden -g '!node_modules/**' -g '!.venv/**' "API_KEY|SECRET_KEY|Bearer |password\s*=|sk-" .
.\.venv\Scripts\python.exe -m pytest backend\tests\security -q
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_permissions.py -q
```

**通过标准**

- 仓库中不存在真实密钥或明文密码；
- 非法输入和越权请求均被后端拒绝；
- AI 异常和非法输出均进入 L2。

### P10-3 全量质量检查

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

**通过标准**

- 六条命令全部成功；
- 不跳过核心业务测试；
- 没有未解释的错误或警告；
- 已通过流程没有出现回归。

## P11 正式验收与交付

### P11-1 执行验收清单

**任务**

- 逐项执行 `需求分析.md` 中 AC-01～AC-22；
- 逐项执行 AS-01～AS-06；
- 完成界面验收；
- 记录失败项并修复；
- 修复后执行相关回归测试。

**验证命令**

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

**通过标准**

- AC-01～AC-22 全部通过；
- AS-01～AS-06 全部通过；
- 自动化测试和前端构建通过；
- 不存在未处理的阻断问题。

### P11-2 完成交付文档

**任务**

- 编写项目 README；
- 写明环境准备和启动步骤；
- 写明环境变量；
- 写明预置账号；
- 写明测试命令；
- 写明演示流程、技术取舍、已知限制和扩展方向；
- 不在文档中写入真实密钥或真实密码。

**验证命令**

```powershell
Test-Path -LiteralPath 'README.md','需求分析.md','plan.md','ai-log.md'
rg -n "启动|环境变量|预置账号|演示|测试|已知限制|扩展" README.md
```

**通过标准**

- 新环境可以仅按 README 启动项目；
- 面试演示可在 5～10 分钟内完成自动发布、人工审核和申诉流程；
- 文档完整说明当前原型边界。

## 6. 开发顺序

```text
P0 环境与项目初始化
  ↓
P1 API 契约与状态机
  ↓
P2 数据库与预置数据
  ↓
P3 JWT 登录与角色鉴权
  ↓
P4 AI 审核核心能力
  ↓
P5 帖子、评论与回复
  ↓
P6 L2 人工内容审核
  ↓
P7 申诉与人工复核
  ↓
P8 普通用户前端
  ↓
P9 审核与复核前端
  ↓
P10 联调、安全与回归测试
  ↓
P11 正式验收与交付
```

每个阶段验证通过后再进入下一阶段。若某阶段修改了已有状态规则、接口契约或数据模型，需要重新执行受影响阶段的测试。

## 7. 当前进度

| 阶段 | 状态 |
| --- | --- |
| 需求分析 | 已完成 |
| 验收标准 | 已完成 |
| 开发计划 | 已完成 |
| P0～P11 开发任务 | 未开始 |

