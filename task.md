# AI 文字内容审核与申诉复核系统——执行任务

## 1. 执行说明

本文件将 `需求分析.md`、`plan.md` 和 `dev-workflow.md` 收敛为6个可执行步骤。

执行原则：

1. 严格按照步骤1至步骤6的依赖顺序执行；
2. 当前步骤的产出和验收标准全部满足后，才能进入下一步；
3. 验收失败时先修复当前步骤，不带着已知问题继续开发；
4. 每完成一步，执行该步骤的验证命令并记录结果；
5. 不增加管理员、举报、下架、编辑、删除、账号处罚、通知、搜索和分页等范围外功能。

## 2. 任务总览

| 步骤 | 任务 | 依赖 | 主要交付结果 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | 工程基础、数据库与登录权限 | 无 | 可启动的前后端、SQLite、四个账号、JWT鉴权 | 已完成 |
| 2 | AI审核核心能力 | 步骤1 | 规则层、AI客户端、审核结构、置信度分流 | 已完成 |
| 3 | 论坛内容发布闭环 | 步骤2 | 帖子、评论、回复、用户页面及最小上下文 | 已完成 |
| 4 | L2人工内容审核 | 步骤3 | 待审核任务、审核接口和审核员页面 | 已完成 |
| 5 | 申诉与人工复核 | 步骤4 | 一次性申诉、复核接口及复核员页面 | 已完成 |
| 6 | 联调、安全、验收与交付 | 步骤5 | 全流程可运行、测试通过、验收完成、文档齐全 | 已完成 |

---

## 步骤1：工程基础、数据库与登录权限

### 依赖

无。该步骤是后续所有功能的基础。

### 工作内容

- 创建 `backend/` FastAPI 工程；
- 创建 `frontend/` Vue 3 + TypeScript + Vite 工程；
- 配置后端测试、Ruff、前端 lint、类型检查、Vitest和构建命令；
- 建立统一业务枚举和基础状态；
- 使用 SQLAlchemy 建立用户、内容、审核结果、审核任务和申诉数据模型；
- 配置 SQLite 数据库；
- 创建幂等数据库初始化命令；
- 初始化普通用户A、普通用户B、内容审核员和申诉复核员；
- 密码使用哈希保存；
- 实现 JWT 登录和当前用户接口；
- 实现三类角色的后端权限校验；
- 实现前端登录页、登录状态、Axios认证和角色路由保护；
- 提供 `/health` 和 OpenAPI 文档。

### 明确产出

- 可独立启动的前端和后端工程；
- SQLite 数据库及5类核心数据模型；
- 4个可登录的预置账号；
- JWT认证与角色鉴权；
- 前端登录页及三类角色入口；
- 后端健康检查和自动生成的接口文档；
- 后端和前端基础测试框架。

### 验收标准

- 四个预置账号均可使用正确密码登录；
- 错误账号或密码不能获得有效JWT；
- 未登录用户不能访问受保护接口；
- 普通用户不能访问内容审核和申诉复核接口；
- 内容审核员不能执行申诉终审；
- 申诉复核员不能执行L2内容审核；
- 数据库中不存在明文密码；
- JWT密钥和AI密钥不出现在前端代码中；
- 连续执行两次初始化不会产生重复账号；
- 前后端均能启动，基础检查和测试通过；
- 满足 AC-01～AC-03、AS-01～AS-03。

### 验证命令

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.init_db
.\.venv\Scripts\python.exe -m backend.app.db.init_db
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_auth.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_permissions.py -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

后端启动后：

```powershell
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health'
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/openapi.json' | Select-Object -ExpandProperty info
```

### 完成记录（2026-10-14）

- 已创建 FastAPI 后端、Vue 3 前端、SQLite 数据模型、四个预置账号、JWT 登录和角色权限基础；
- 数据库初始化连续执行两次后仍为4个账号，密码仅保存 Argon2 哈希；
- 后端 Ruff 检查通过，后端测试 `8 passed`；
- 前端 lint、TypeScript 类型检查和 Vitest 测试通过；
- Vite 生产构建通过，前端预览页返回 HTTP 200；
- npm 完整依赖审计为0个已知漏洞；
- 前端要求 Node.js `>=20.19.0`，本次使用 Node.js 24.19.0 验证；
- 尚未实现步骤2及之后的审核和论坛业务，未扩大原型范围。

---

## 步骤2：AI审核核心能力

### 依赖

步骤1验收通过，数据库、配置读取和测试框架可用。

### 工作内容

- 定义八类审核结果和L0～L4风险等级；
- 定义风险类别、类别置信度、最终等级和简短原因的结构化输出；
- 对AI结果进行严格的数据校验；
- 实现少量明确违禁词、广告及联系方式规则；
- 实现厂商无关的AI接口客户端；
- 从环境变量读取接口地址、密钥和模型名称；
- 设置请求超时并处理连接失败、服务异常和非法响应；
- 提供测试替身，稳定模拟L0～L4、超时和非法输出；
- 实现置信度分流；
- 实现AR001～AR010和FAI001～FAI005；
- 防止用户文字改变系统审核指令或输出格式。

### 明确产出

- 统一审核结果Schema；
- 基础文字规则服务；
- AI接口客户端；
- AI测试替身；
- 置信度分流服务；
- AI异常降级到L2的处理；
- 审核核心单元测试与安全测试。

### 验收标准

- L0/L1且置信度不低于0.80时裁决为发布；
- L3/L4且置信度不低于0.90时裁决为拒绝；
- L0/L1低于0.80或L3/L4低于0.90时进入L2；
- AI直接返回L2时进入人工审核；
- AI连接失败、超时、服务错误或格式非法时进入L2；
- 无效AI结果不得导致自动发布或自动拒绝；
- 多标签结果按照最终等级对应类别的置信度分流；
- 0.79、0.80、0.89和0.90边界值测试正确；
- 提示注入样例不能改变固定审核结构；
- 满足 AC-07～AC-11、AS-05、AS-06。

### 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_result_schema.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_rules.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_ai_client.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_routing.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\security\test_prompt_injection.py -q
.\.venv\Scripts\python.exe -m ruff check backend
```

### 完成记录（2026-10-14）

- 已完成八类风险结果、L0～L4等级、最终类别和置信度的严格结构校验；
- 已完成少量明确违禁交易及“广告意图 + 联系方式”组合规则，未命中时进入AI层；
- 已完成兼容聊天补全格式的厂商无关AI客户端，配置、密钥、模型和超时均从环境变量读取；
- 已完成连接失败、服务错误、超时、不可解析和非法字段的统一L2安全降级；
- 已完成0.79、0.80、0.89、0.90边界、多标签最终类别置信度和提示注入隔离测试；
- 后端全量 Ruff 检查通过，pytest 共 `38 passed`；
- 本阶段使用模拟传输验证AI协议，真实厂商调用需在本地提供有效AI配置后执行。

---

## 步骤3：论坛内容发布闭环

### 依赖

步骤2验收通过，AI审核服务可以返回稳定、可校验的分流结果。

### 工作内容

- 实现帖子发布、公共列表和详情；
- 实现一级评论；
- 实现对一级评论的一层回复；
- 限制帖子标题1～100字、正文1～3000字；
- 限制评论和回复1～500字；
- 只允许评论已发布帖子；
- 只允许回复已发布一级评论；
- 禁止回复继续嵌套；
- 每次提交调用审核服务并保存状态；
- 实现CTX001～CTX003最小上下文；
- 实现“我的内容”接口和页面；
- 实现论坛首页、发帖、帖子详情、评论和回复页面；
- 等待审核和已拒绝内容只对作者及相应审核角色可见；
- 不提供编辑和删除功能。

### 明确产出

- 帖子、评论和回复REST API；
- 公共帖子列表和详情接口；
- 最小上下文构造服务；
- “我的内容”接口；
- 普通用户论坛首页、发布页、详情页和“我的内容”页面；
- 帖子、评论、回复的完整自动审核链路；
- 内容可见性和用户数据隔离测试。

### 验收标准

- 合法帖子、评论和回复可以提交；
- 字段缺失、字数超限和错误父级ID被前后端阻止；
- L0/L1内容出现在公共页面；
- L2内容仅作者可见并显示待人工审核；
- L3/L4内容仅作者可见并显示已拒绝及原因；
- 未发布帖子不能被评论；
- 未发布评论不能被回复；
- 回复不能继续嵌套；
- 用户A看不到用户B的非公开内容；
- 公共页面不展示等级、置信度和审核原因；
- 不存在内容编辑和删除入口或业务接口；
- 满足 AC-04～AC-11、AC-20～AC-22、AS-04。

### 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_posts.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_comments.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_my_contents.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\moderation\test_context_builder.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_post_moderation_flow.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_comment_moderation_flow.py -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

### 完成记录（2026-10-14）

- 已完成帖子列表、详情、发布，一级评论和一层回复REST API；
- 已完成帖子1～100/1～3000字、评论与回复1～500字校验，以及未发布父内容和回复层级约束；
- 已完成自动发布、L2待人工、L3/L4拒绝的内容状态写入和审核结果保存；
- 已完成评论与回复的“两阶段最小上下文”审核，首次明确时不读取上下文；
- 已完成公共页面仅查询已发布内容、作者查看本人全部状态内容和用户数据隔离；
- 已完成普通用户论坛、发帖、详情、评论、回复和“我的内容”前端页面，未提供编辑或删除入口；
- 后端 Ruff 通过，pytest 共 `51 passed`；前端 lint、类型检查、Vitest和生产构建全部通过。

---

## 步骤4：L2人工内容审核

### 依赖

步骤3验收通过，L2内容可以正确保存并与作者隔离。

### 工作内容

- L2内容自动生成待审核任务；
- 实现内容审核员待办列表；
- 实现审核详情；
- 展示原始内容、最小上下文、AI类别、等级、置信度和简短原因；
- 允许审核员调整类别和等级；
- 实现MR001～MR005；
- L0/L1只能通过并发布；
- L3/L4只能拒绝；
- L2不能作为人工终态；
- 完成后的任务不能重复处理；
- 实现内容审核员前端页面；
- 不实现暂缓、转交、高级审核和下架。

### 明确产出

- L2审核任务自动创建机制；
- 待审核列表和详情接口；
- 人工审核决定接口；
- 内容审核员待办与详情页面；
- 人工审核状态机测试；
- 审核任务权限测试。

### 验收标准

- 低置信度和AI异常内容均进入L2待办；
- L0/L1/L3/L4不进入L2待办；
- 只有内容审核员可以访问和处理任务；
- 调整为L0/L1并通过后内容发布；
- 调整为L3/L4并拒绝后内容保持不公开；
- L3/L4通过、L0/L1拒绝或L2完成等非法操作被阻止；
- 已完成任务不能重复提交；
- 人工拒绝的内容开放一次申诉入口；
- 满足 AC-12～AC-14。

### 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_moderation_tasks.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_manual_review_flow.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_permissions.py -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

### 完成记录（2026-10-14）

- L2内容自动创建待审核任务，列表只返回未完成任务；
- 审核详情展示原文、最小上下文、AI类别、等级、置信度和简短原因；
- 审核员可调整类别和等级，L0/L1只能发布，L3/L4只能拒绝，L2不能完成；
- 已完成任务重复处理返回409，普通用户和申诉复核员访问返回403；
- 内容审核员前端待办、详情和决定页面已完成；
- 人工审核专项测试与全量回归通过。

---

## 步骤5：申诉与人工复核

### 依赖

步骤4验收通过，自动拒绝和人工拒绝内容均具有稳定的“已拒绝”状态。

### 工作内容

- 实现10～500字的文字申诉；
- 只允许内容作者申诉；
- 只允许已拒绝内容申诉；
- 每条内容最多申诉一次；
- 实现AP001～AP005；
- 实现“我的申诉”接口和页面；
- 实现申诉复核员待办列表和详情；
- 展示原内容、最小上下文、原审核结果、置信度和申诉说明；
- 实现RR001～RR005；
- L0/L1只能通过申诉并发布；
- L3/L4只能驳回申诉并维持拒绝；
- L2不能作为终审等级；
- 已处理申诉不能重复处理；
- 实现申诉复核员前端页面；
- 不实现图片、附件、补充材料和多轮申诉。

### 明确产出

- 申诉提交接口；
- “我的申诉”接口及页面；
- 待复核申诉列表和详情接口；
- 申诉终审接口；
- 申诉复核员列表和详情页面；
- 一次性申诉约束；
- 申诉状态机、权限和重复操作测试。

### 验收标准

- 自动拒绝和人工拒绝内容均可由作者申诉；
- 非作者、非拒绝内容、非法字数和重复申诉均被阻止；
- 每条内容只能产生一条申诉记录；
- 只有申诉复核员可以执行终审；
- L0/L1并通过申诉后内容发布；
- L3/L4并驳回申诉后内容保持拒绝；
- L2终审、L3/L4通过或L0/L1驳回等非法组合被阻止；
- 已处理申诉不能再次处理或再次申诉；
- 普通用户可以查看自己的申诉状态和结果；
- 满足 AC-15～AC-19。

### 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_appeals.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\flows\test_appeal_review_flow.py -q
.\.venv\Scripts\python.exe -m pytest backend\tests\api\test_permissions.py -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

### 完成记录（2026-10-14）

- 自动拒绝和人工拒绝内容均可由作者提交一次10～500字文字申诉；
- 非作者、非拒绝内容、非法字数和重复申诉均被后端阻止；
- 申诉复核员可查看原内容、最小上下文、原审核结果和申诉说明；
- L0/L1只能通过申诉，L3/L4只能驳回，L2不能作为终审等级；
- 普通用户“我的申诉”和申诉复核员待办、详情、决定页面已完成；
- 申诉专项测试与全量回归通过。

---

## 步骤6：联调、安全、验收与交付

### 依赖

步骤1至步骤5全部验收通过，三类角色的功能页面和接口已经完成。

### 工作内容

- 完成前后端全流程联调；
- 验证L0/L1自动发布；
- 验证低置信度和L2进入人工审核；
- 验证L3/L4自动拒绝；
- 验证人工审核通过和拒绝；
- 验证申诉通过和驳回；
- 验证AI失败安全降级；
- 检查JWT、角色鉴权、输入校验和数据隔离；
- 检查真实密钥、明文密码和不应提交的文件；
- 执行全部后端和前端测试；
- 逐项执行 AC-01～AC-22和AS-01～AS-06；
- 完成README、环境变量说明、启动说明、测试说明和演示流程；
- 准备5～10分钟面试演示路径。

### 明确产出

- 可完整运行的前后端原型；
- 全量自动化测试结果；
- 安全检查结果；
- AC和AS逐项验收结果；
- 项目README；
- 本地启动与配置说明；
- 面试演示流程；
- 已知限制和后续扩展说明；
- 可标记为 `v0.1.0` 的最小原型。

### 验收标准

- 用户A发布L0/L1帖子后，用户B能够查看和评论；
- L2内容经过审核员通过后能够发布；
- L2内容经审核员拒绝后，用户能够申诉并由复核员通过；
- L3/L4内容自动拒绝后，用户能够申诉并由复核员驳回；
- AI接口异常时内容进入L2，不被自动发布或拒绝；
- 三类角色不存在越权访问；
- 公共页面不泄漏未发布内容和审核信息；
- 仓库中不存在真实密钥、明文密码、SQLite开发数据库、虚拟环境或`node_modules`；
- 后端测试、静态检查、前端lint、类型检查、测试和构建全部通过；
- AC-01～AC-22全部通过；
- AS-01～AS-06全部通过；
- README能够指导一个新环境启动项目；
- 项目能够在5～10分钟内演示自动发布、人工审核和申诉闭环。

### 验证命令

```powershell
.\.venv\Scripts\python.exe -m ruff check backend
.\.venv\Scripts\python.exe -m pytest backend\tests -q
npm --prefix frontend run lint
npm --prefix frontend run type-check
npm --prefix frontend run test -- --run
npm --prefix frontend run build
rg -n --hidden -g '!node_modules/**' -g '!.venv/**' "API_KEY|SECRET_KEY|Bearer |password\s*=|sk-" .
Test-Path -LiteralPath 'README.md','需求分析.md','plan.md','dev-workflow.md','task.md','ai-log.md'
```

后端启动后：

```powershell
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health'
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/openapi.json' | Select-Object -ExpandProperty info
```

### 完成记录（2026-10-14）

- 已完成自动发布、L2人工审核、自动拒绝、申诉通过和申诉驳回的端到端测试；
- AI配置缺失、连接失败、超时、服务错误和非法响应均安全降级到L2；
- 后端 Ruff 通过，pytest共 `72 passed`；
- 前端 ESLint、TypeScript类型检查、Vitest和Vite生产构建全部通过；
- npm完整安全审计为0个已知漏洞；
- 真实进程健康检查、JWT登录和AI缺失时L2降级验证通过；
- 安全扫描只命中环境变量示例、测试专用值和合法Authorization代码，未发现真实密钥或明文账号密码；
- SQLite运行数据已移除，`.env`、数据库、虚拟环境、`node_modules`和构建产物均已加入忽略列表；
- `README.md` 已包含安装、配置、初始化、启动、测试、AI协议、演示流程和已知限制；
- AC-01～AC-22与AS-01～AS-06均有实现和自动化测试或启动验收证据。

---

## 3. 最终完成条件

项目只有同时满足以下条件才视为完成：

- 6个步骤均标记为已完成；
- 所有步骤的验证命令通过；
- `需求分析.md` 的功能和安全验收全部通过；
- `dev-workflow.md` 中的判断规则和失败处理均有对应实现或测试；
- 不包含任何已明确排除的范围外功能；
- README、配置说明和演示流程完整；
- 没有未说明的阻断缺陷；
- 可以稳定完成一次端到端演示。

## 4. 2026-11-12 本地复验与维护状态

- 恢复前后端源码，使用新的 `.venv-local` 与 Node.js 24；新增 `start-local.ps1`。
- DeepSeek 接口地址为 `https://api.deepseek.com`，模型为 `deepseek-chat`；密钥仅保存在忽略的 `.env`。
- 后端72项测试通过；前端类型检查、构建和1项测试通过。本轮没有重跑 Ruff、ESLint 或全项人工验收。
- 实际登录和发帖通过；真实模型将正常帖子判为 L0、置信度0.99，内容自动发布。
- 当前数据库保留本地演示及接入验证数据，未清空。
- 本次 npm 审计为15项漏洞（13项中危、2项高危），覆盖上文历史“0漏洞”结论；尚未开展依赖修复。
