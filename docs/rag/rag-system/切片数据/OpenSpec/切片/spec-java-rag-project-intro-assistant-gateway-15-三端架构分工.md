# 三端架构分工（Java网关SSE中继、跨端trace与会话边界）

> summary: 三端边界分工：Java网关SSE白盒事件中继时序、trace_id跨端贯穿与断线补查、Python无状态会话续接
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-java-rag-project-intro-assistant-gateway-15-三端架构分工.md
> 类别：架构设计

---

### Requirement: SSE 白盒事件中继
> 检索摘要：白盒SSE事件按什么时序透传前端？permission到done顺序能否重排或丢失？clarify/switch和boundary分支怎么早停？

系统 SHALL 将 Python 引擎返回的 SSE 事件流按固定时序透传前端：`permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`，不得重排或丢失。Python 的 `meta`/`done` 内部字段由 Java 消费/重建，不透传原始事件。

#### Scenario: 正常问答时序

- **WHEN** 学生发送问题且流程正常
- **THEN** 前端依次收到 `permission`（角色门结果）→ `intent`（anchor/category/switch/ambiguous/candidates）→ `rewrite`（改写后 query）→ `rerank`（精排 top-K 块）→ `token`（正文流）→ `done`（完整结果）

#### Scenario: 澄清/切换时序

- **WHEN** intent 判定 ambiguous（多候选）或 switch_detected
- **THEN** 前端收到 `intent` 后 `clarify` 或 `switch` 事件，**无 rewrite/rerank/token 流**，随后 `done`

#### Scenario: 范围门低置信过滤时序

- **WHEN** recall 后综合分低于阈值
- **THEN** 前端收到 `rerank`（可为空）后 `boundary` 事件（reason=low_confidence），无 token 流，随后 `done`

### Requirement: trace_id 透传与断线补查
> 检索摘要：trace_id由Java入口生成还是Python生成？怎么贯穿两侧日志、done事件返回，断线后凭trace_id怎么补查单轮结果？

系统 SHALL 在每轮请求入口生成 `trace_id`（同源贯穿 Java/Python 日志），透传 Python 并在 `done` 事件返回；系统 SHALL 提供按 `trace_id` 查询单轮完整结果的接口，供前端断线后补查。

#### Scenario: trace_id 贯穿

- **WHEN** 学生发起一轮问答
- **THEN** Java 生成 `trace_id` 传入 Python，日志两侧同源，`done` 事件携带该 `trace_id`

#### Scenario: 断线补查

- **WHEN** 前端因断线丢失某轮结果，凭 `trace_id` 调 `GET /api/rag/assistant/turns/{trace_id}`
- **THEN** 系统返回该轮完整结果（answer/quotedKeys/tokensUsage/suggestions）或明确"trace 不存在"（超时保留窗口内）

### Requirement: 会话续接基础
> 检索摘要：前端怎么回传session_id携带锚点与轮次上下文？switch/clarify判定依据是什么、无会话状态时按什么处理？
> 落地说明：Python 无状态（D-D），session_id 透传但不落库会话状态；锚点/轮次上下文由前端回传 history 承载，switch/clarify 判定基于 history 锚点 + current_project。

系统 SHALL 支持前端回传 `session_id` 以携带当前锚点与轮次上下文到 Python，供 switch/clarify 判定。

#### Scenario: 续接锚点

- **WHEN** 前端回传 `session_id` 且 Python 侧存在该会话状态
- **THEN** intent 判定 `switch_detected` 时以"前端 current_project vs 会话已锚定 project"为依据

#### Scenario: 无会话状态

- **WHEN** `session_id` 缺失或 Python 侧无对应状态
- **THEN** 系统按全新会话处理，锚点取前端 `current_project`（缺失则全局模式）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-java-rag-project-intro-assistant-gateway.md`（§SSE 白盒事件中继 / §trace_id 透传与断线补查 / §会话续接基础）
