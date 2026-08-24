## Context

AI 答疑是学生端核心体验：引导式解答而非直接给答案，答疑中渐进确认学生知识点掌握度，按知识点 key 落库，联动知识图谱点亮。

关键认识：**对话天然是 agent 形态**——学生不会按预设流程走（中途换题、问概念、要答案、闲聊、"我不会"）。经多轮讨论确认：**不做流程状态机控制**（用状态机控制对话分支会导致状态爆炸），改为**能力受限的 agent + 工具护栏**：Python 侧是纯智能的答疑 agent（决策 + 生成），Java 侧是平台（认证网关 + 护栏 + 数据 + 基础设施）。Python 不直接碰 MySQL / KG / COS，一切数据操作经 Java 域服务。

微服务分工：Java API 网关（认证 / 会话 / 路由）+ 答疑域服务（护栏 / 落库 / 图谱 / COS 归档）为一方；Python 答疑 agent（`ai-edu-ai-service` **现有 LLM 服务内的独立模块**，不单独起服务，Java 仍按服务边界调用）为另一方，只做智能判断，暴露 `decide` / `generate` 两个端点。

## Goals / Non-Goals

**Goals:**
- 微服务拓扑：Java 网关 + 答疑域服务；Python 纯智能 agent（MVP 用 **L0 单次调用**，演进可升级 LangGraph 多步）
- **类型先行流式**：`decide`（非流式快调用，出动作元数据）→ Java 护栏校验 → `generate`（流式 SSE，出正文），护栏安全 + 体验流畅
- 能力受限：Python 只输出结构化 action（`type` 闭集），Java 在动作出口做硬护栏
- 会话仅保留**生命周期 3 状态 + 护栏计数器**，不随题目数量/对话长度/换题次数增长
- 知识点按 `TextbookKP URI` 为 key 落库，掌握度单源 MySQL，图谱前端叠加（不写 Neo4j）
- 答案出口：第 1 次要答案给思路，第 2 次给答案（Java 硬拦）
- 会话 20 轮上限；换题计数重置；仅数学（图谱完备）
- **拍题 OCR 前置**：拍照 → OCR 识别题目文本 → 学生确认/修改 → 作为**首条学生消息**进答疑（Java 编排，Python 实现识别）

**Non-Goals:**
- MVP 不做 LangGraph 多步 agent（L1/L2）、自适应学习（查薄弱点/出变式题）——阶段 2
- 不做题库指纹、结构化分步素材、易错分支预置（阶段 2）
- 不做行为风控模型、多维能力画像、可视化报告（阶段 3）
- 不向 Neo4j 写入业务状态（掌握度单源 MySQL）
- Python 不直接访问 MySQL / KG / COS（全经 Java 域服务）
- 不在本仓库实现 Python 侧（`ai-edu-ai-service` 独立排期）
- OCR 只做题目文本识别；数学公式/手写识别质量依赖识别服务，识别结果必须经学生确认；图形题/手写公式的深度识别属后续

## 架构总览（微服务拓扑）

```
┌────────────────────────────────────────────────────────────────┐
│ 前端（学生端）                                                  │
│   │  REST / SSE（登录态在 Java）                                │
│   ▼                                                            │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Java API 网关 + 答疑域服务（两个角色）                        │   │
│ │ 角色1 对外网关：认证(HttpSession) / 路由 / SSE 透传            │   │
│ │ 角色2 答疑域服务：会话 / 护栏 / 掌握度 / 错误事件 / KG / COS     │   │
│ │                                                            │   │
│ │  一次学生消息的编排（Java 主导）：                            │   │
│ │  ① 安全预检（关键词）                                        │   │
│ │  ② 组装上下文 {history, counters, 掌握度快照, subject=math}   │   │
│ │  ③ 调 Python decide（非流式）→ action 元数据                  │   │
│ │  ④ 护栏校验 action（答案/轮次/换题/收尾）→ 落库副作用          │   │
│ │  ⑤ 调 Python generate（流式）→ SSE 透传前端                   │   │
│ └──────────────┬────────────────────────────────────────────┘   │
│                │ 内部 token（复用 llm-gateway internalToken 模式）│
│                ▼                                                │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ Python 答疑 agent（ai-edu-ai-service 现有 LLM 服务内的模块）  │   │
│ │  · 无状态、纯智能，不碰 MySQL/KG/COS                        │   │
│ │  · POST /api/tutoring/decide   决策（快，出 action 元数据）   │   │
│ │  · POST /api/tutoring/generate 生成（流式，出正文）           │   │
│ └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

## Decisions

### 1. 微服务分工：Java = 平台，Python = 纯智能

**选择**: Java 持有认证、会话、护栏、掌握度、错误事件、KG 解析、COS 归档（数据与基础设施）；Python 答疑 agent（`ai-edu-ai-service` 现有 LLM 服务内的独立模块，不单独起服务）只做决策与生成，不直接访问任何数据源。

**原因**: 业务数据（掌握度/错误事件/会话）要被图谱叠加、错题本、学情等 Java 侧功能消费，数据权威必须在 Java；Python 作为独立智能微服务，职责单一、可独立迭代与扩容。

### 2. 交互模型：decide → guard → generate（类型先行流式）

**选择**: 一次学生消息 = 两次 Python 调用，中间插 Java 护栏：

```
① Java 安全预检 → 组装上下文
② Python decide（非流式，快模型）→ 返回 action 元数据 {type, eval, mastery_signals, ...}
③ Java 护栏校验 action 元数据（见决策 4）
     ✗ 拒绝 → 让 Python 重决策（带 directive）或 Java 降级
     ✓ 通过 → 落库副作用（掌握度/错误/情绪/消息）
④ Python generate（流式 SSE，按已放行 type 生成正文）→ Java 透传前端
```

**原因**: "类型先行"保证**任何内容流入学生之前，type 已过护栏**——reveal 未授权时正文一个字都不会吐出去，护栏 100% 有效；同时 generate 流式保证体验流畅。decide 用快模型（非流式），generate 用强模型（流式）。

### 3. 动作契约（decide 输出）

```json
{
  "type": "hint" | "approach" | "reveal" | "concept" | "switch" | "end",
  "reason": "决策理由（Python 可选发送；Java Jackson 默认容忍未知字段 FAIL_ON_UNKNOWN_PROPERTIES=false，无需建模）",
  "eval": {
    "correct": true,
    "error_type": null,
    "emotion": "NEUTRAL",
    "exercise_complete": false
  },
  "mastery_signals": [{"kp_label": "二元一次方程组", "signal": "practicing"}],
  "new_question": null,
  "end_reason": null,
  "summary": null,
  "degraded": false
}
```
- `degraded`：结构化输出兜底时 Python 置 true（type 必为 hint），Java 按普通 hint 放行 + 记日志（监控用），**不使用 503**
- `reason`：纯调试字段，Java 不建模，容忍未知字段即可

- `hint` 引导 / `approach` 思路 / `reveal` 答案 / `concept` 概念讲解 / `switch` 换题 / `end` 收尾
- `type` 是**闭集**（能力受限）；agent 自决 type，Java 决定放不放行
- `generate` 的 prompt 会带上已放行的 type，约束生成正文与 type 一致（如 approach 只给思路，不给完整演算）

### 4. 护栏规则（Java，动作出口，确定性）

| 护栏 | 判断 | 处理 |
|------|------|------|
| 答案 | `type=reveal` 且 `answer_request_count < 1` | 拒绝，重决策为 approach，count→1 |
| 轮次 | 引导类（hint/approach/evaluate 判定）且 `round_count ≥ 20` | 拒绝，强制 `end(ROUND_LIMIT)` |
| 安全 | 本地关键词命中（agent 启动前） | 终止，不启动 agent |
| 换题 | `type=switch` | 旧题知识点不校正（不点亮），仅计数重置（换题判定在 Python，后端不记录题目） |
| 收尾 | `type=end` | 按 end_reason 校正掌握度 + COS 终态写 + 置 ARCHIVED |
| 掌握度/错误 | action 带 `mastery_signals` / `eval.correct=false` | UPSERT 掌握度（label→URI）+ 写错误事件（含 emotion） |

护栏是**测试重点**（确定性规则，可单测），agent 路径不追求全覆盖测试。

### 5. 答案出口机制（Java 硬拦）

```
count=0 学生要答案 → decide 输出 reveal → Java 拦（count<1）→ 重决策 approach → count→1
count=1 学生再要答案 → decide 输出 reveal → Java 放行（count≥1）→ count→2，标记已揭示
```

`answer_request_count` 由 Java 管理；即使 agent 第一次就要输出 reveal，也会被 Java 硬拦成思路。"请求答案"识别由 decide 判断（学生在消息里要答案）；也可保留显式 `request-answer` API（见 api.md）。

### 6. 换题 / 回旧题（数据更新，非状态转换）

```
学生贴新题 → decide 输出 switch + new_question
   → Java 仅 round_count/answer_request_count 归零（按新题重新计）
   → 旧题知识点不校正（留档，不点亮）
学生回旧题 → 又贴那道题 → decide 输出 switch 换回（或 concept）→ 同上
```

因为没有流程状态机，换题/回旧题只是**计数重置事件**；"当前题目"由 Python decide 每次从全量 history 推断，Java 不记录、不维护题目内容（记录易错：OCR 乱码、模型转述、陈旧快照）。学生怎么跳 agent 都能接住（它读全量历史判断）。

### 7. 会话状态：生命周期 + 计数器（不随内容增长）

- 生命周期（3 个，固定）：`ACTIVE` / `ARCHIVED` / `TERMINATED`
- 护栏计数器（数据，非状态）：`round_count`、`answer_request_count`
- 掌握度快照：上下文字段（**当前题目后端不记录**，由 Python 从 history 推断）

状态数量固定为 3，不随题目数量、对话长度、换题次数增长。**"流程"由 agent 上下文承载（自然语言），Java 只留生命周期与计数器。**

### 8. 知识点 key = TextbookKP URI

（保留原决策）每个知识点的稳定 key 采用知识图谱 `TextbookKP` 节点的 **URI**。学生掌握度 `t_student_kp_mastery.kp_key` 存 URI。label→URI 解析（`TutoringKpResolver`，Java 侧）在 kg-sync 的 MySQL 镜像（`KgKnowledgePointPo`，subject=math）中解析：精确 → LIKE → 未命中（记日志 + 收尾标记"待收录"，不点亮）。解析失败不影响答疑主流程。

### 9. 掌握度规则

（保留 + 出口路径）`mastery_level` 0–100，复用学习域 `MasteryLevel` 概念。每轮 eval 返回 `mastery_signals`：mastered→75 / practicing→50 / struggling→25，取 max 单调不减；学生显式纠正时允许下调；错误只记 `t_tutoring_error_event` 不降分。**收尾按 end_reason 校正**：`COMPLETED`（独立解出）→ 提升到 75+；`ANSWER_REVEALED`（看过答案）/ `ABANDONED` / `ROUND_LIMIT` → 不提升。掌握度是**基础信号**，最终掌握靠举一反三 + 错题集（阶段 2+）校正。

### 10. 题型/题类独立枚举

（保留）答疑侧 `question_type`（题型）与 `question_kind`（题类）使用独立可扩展枚举，不绑定作业域 `QuestionType`。

### 11. 存储三层：Redis（活跃）+ MySQL（业务）+ OSS/COS（归档）

（保留 + 实时写）Redis 存活跃会话（状态、计数、完整消息列表，TTL 24h，供 decide 组装上下文与断点恢复；**不记录题目内容**）；MySQL 存 `t_tutoring_session` + `t_student_kp_mastery` + `t_tutoring_error_event`（结构化业务数据，**无题目内容、无原始消息**）；**对话每轮实时整写 COS**（`FileStorageService`，`tutoring/transcripts/{studentId}/{sessionId}.json`，幂等整写、脱敏，**COS 恒为完整对话**），会话结束终态写一次；`transcript_url`=objectKey 首次实时写即回填，读时签名 URL。

**题目图片存储（2026-08-06，image-first）**：题目/示例图按学生+会话组织 + 时间戳命名——`tutoring/questions/{studentId}/{sessionId}/{yyyyMMdd-HHmmss-SSS}.{ext}`。图片 URL 作为消息 `image_url` 进对话历史（Redis + COS transcript 均含），与对话天然关联；图片发起会话时 Java 先落库拿 sessionId 再传图（不留 pending 临时目录）。**换题=学生发新图**：Java 检测新 URL 首次出现 → decide 带 `is_new_question=true` → Python 短路 `type=switch` → Java 重置计数（判定权在 Java，Python 无状态不依赖 history 图片推断）。

### 12. 认证/会话桥接：Java 网关代理（方案 A）

前端统一走 Java 网关；Java 校验 `HttpSession.getAttribute("userId")`（STUDENT 角色）后，调 Python 时携带**内部 token + userId + sessionId**（复用 llm-gateway 的 `internalToken` 模式）。Python 不自己做认证，只信网关注入的身份。请求体不传 student_id。

### 13. 流式：类型先行（方案 ②）

**决定**：MVP 就做流式，但用"类型先行"协议保证护栏安全——即决策 2 的两段式：`decide`（非流式，先出 type）→ Java 校验 → `generate`（流式正文）。**绝不**边流式边拦截（那样答案可能已漏出）。

前端 SSE 事件：
- `event: meta, data: {"session_id", "type": "hint", "round_count": 1}` （护栏已通过的类型先行到达）
- `event: token, data: {"content": "先找题目里的已知条件..."}` （正文流）
- `event: done, data: {"session_id", "status", "eval": {...}}`

### 14. LangGraph 程度：MVP = L0 单次调用

**决定**：MVP 用 **L0 单次调用**——decide 一次调用输出 action 元数据（用 LangChain `with_structured_output` 做 schema 约束），generate 一次调用流式输出正文。**无 agent 循环、无中间工具回调**。护栏拒绝时由 Java 重决策/降级（不依赖 agent 重规划）。

**演进（阶段 2）**：升级 L1/L2 LangGraph 多步 agent——增加工具集（查薄弱点、出变式题等，工具 = Java 内部接口），agent 在循环中自然处理护栏拒绝重规划。工具接口在 MVP 已按 Java 内部 API 预留，升级为低摩擦。

### 15. 拍题入口：图像优先（2026-08-06 反转原 OCR 决策）

**选择（反转）**: 题目本身是图片（含受力分析图/实例图），答疑分析必须看到原图 → **不做传统 OCR 文本提取**，改用**视觉模型直接看图**。链路：前端 `POST /api/tutoring/sessions`（multipart 图片，可选 content）→ Java 认证 + 存 COS（`tutoring/questions/{studentId}/{sessionId}/{时间戳}.png`）→ 图片 URL 作为首条消息 `image_url` 进历史 → decide/generate 均携带 `image_url` 给**视觉模型**（豆包 `doubao-seed-2-0-lite`，全模态）看图作答。

**换题=学生发新图**: `POST /api/tutoring/sessions/{sessionId}/messages`（multipart 新图）→ **Java 检测新图 URL 首次出现** → decide 请求带 `is_new_question=true` → **Python 短路返回 `type=switch`（不调 LLM，确定性 100% 准）** → Java 重置轮次计数。判定权在 Java（只有 Java 知道"本轮新上传了图"），Python 无状态不依赖 history 图片结构推断（该做法有 bug：换题后每轮 history 都带旧图+新图，会被误判成连续换题）。

**原因（为什么不用传统 OCR）**: ① 数学公式/符号 OCR 质量是公认痛点，丢符号；② 受力分析图/实例图是图片本身的信息，文本提取必然有损，答疑分析必须引用原图；③ 视觉模型读图成本与 OCR 同数量级（~0.2–1 分/图），质量远优。**保留 `POST /api/tutoring/ocr` + `ai-edu.tutoring.ocr.enabled` 开关**作为兼容/降级路径（关闭时仅手打/粘贴，答疑核心不受阻）。

### 16. 情绪枚举以 Python F7 为准

**选择**: `eval.emotion` 使用 Python 侧权威的 **F7 七态**：`NEUTRAL / CONFUSED / FRUSTRATED / ANXIOUS / CONFIDENT / INTERESTED / BORED`。Java 学习域（答疑功能模块）定义 `TutoringEmotion` 值对象（7 态），`t_tutoring_error_event.emotion` / `t_tutoring_session.last_emotion` 存 F7 字符串。

**原因**: Python 是情绪输出方，枚举以输出方为准。**不强制复用** learning 域 `EmotionState`（5 态：POSITIVE/NEUTRAL/FRUSTRATED/CONFUSED/ANXIOUS）——那是情绪识别功能自己的枚举，两套并存，后续再统一。

## 状态与数据

| 概念 | 内容 | 归属 |
|------|------|------|
| 生命周期状态 | ACTIVE / ARCHIVED / TERMINATED | Java 会话表 |
| 护栏计数器 | round_count（≤20）、answer_request_count | Java 会话表（Redis 缓存） |
| 当前题目 | question_type/question_kind（MySQL）；**题目文本后端不记录**，Python 从 history 推断 | Java（MySQL）/ Python |
| 掌握度 | t_student_kp_mastery（按 URI） | Java（Python 经 action 上报 signal） |
| 错误事件 | t_tutoring_error_event | Java |
| 消息 | Redis（活跃期热存）→ COS（每轮实时整写，恒完整） | Java |
| 动作 | decide 输出的 type 闭集 | Python 决策 / Java 放行 |

## 数据模型（表结构）

> **域归属**：AI 答疑作为**学习域（learning bounded context）内的功能模块**落地（掌握度 / 错误事件是学习域核心数据）。三张表物理位于 **`ai_edu_learning`** 数据库；持久化层 Mapper 需 `@DS("learning")` 路由（`application.yml` 需新增 `learning` 数据源，见 tasks 11.1）。实现代码放 `com.ai.edu.domain.learning` 下的答疑子模块。

### `t_tutoring_session`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 会话 ID |
| student_id | BIGINT | 学生 ID（网关注入） |
| subject | VARCHAR(32) | 学科（本期恒为 math） |
| question_type | VARCHAR(32) | 题型（答疑侧独立可扩展枚举，可空） |
| question_kind | VARCHAR(32) | 题类（计算/应用/证明，可空） |
| intent_category | VARCHAR(16) | ACADEMIC / GUIDANCE / UNRELATED（废弃？见下） |
| last_emotion | VARCHAR(16) | 最近一轮情绪（F7 七态，Python 输出方权威） |
| status | VARCHAR(16) | ACTIVE / ARCHIVED / TERMINATED |
| round_count | INT | 轮次（≤20） |
| answer_request_count | INT | 要答案次数 |
| end_reason | VARCHAR(32) | COMPLETED / ANSWER_REVEALED / ABANDONED / ROUND_LIMIT / null |
| transcript_url | VARCHAR(512) | COS 对话归档 objectKey（首次实时写时回填） |
| created_at / updated_at / archived_at | DATETIME | created_at=会话开始（标准审计列）；archived_at=归档时间 |
| created_by / modified_by / is_deleted | BIGINT / TINYINT(1) | 标准审计列（默认 0 / 逻辑删除，与全项目一致） |

> 说明：**不建消息表、不存题目内容**。对话每轮实时整写 COS（`tutoring/transcripts/{studentId}/{sessionId}.json`，恒为完整对话），Redis 为活跃期热存；**换题只作事件（仅计数重置）**，后端不记录、不维护题目文本——换题/当前题目判定全在 Python decide。`intent_category` 在 agent 语境下由 decide 判断（无关/学习方法 直接在回复中处理），可暂不落库，或保留用于统计——MVP 建议保留但可空。

### `t_student_kp_mastery`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | |
| student_id | BIGINT | |
| kp_key | VARCHAR(255) | **TextbookKP URI** |
| kp_label | VARCHAR(255) | 知识点名（冗余，便于展示） |
| mastery_level | INT | 0–100 |
| evidence | JSON | 证据（命中步骤、错误事件 id 列表） |
| last_session_id | BIGINT | 最近一次答疑会话 |
| created_at / updated_at | DATETIME | 标准审计列 |
| created_by / modified_by / is_deleted | BIGINT / TINYINT(1) | 标准审计列（默认 0 / 逻辑删除） |
| **UNIQUE(student_id, kp_key)** | | 幂等 |

### `t_tutoring_error_event`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | |
| student_id | BIGINT | |
| session_id | BIGINT | |
| kp_key | VARCHAR(255) | 关联知识点（可空） |
| error_type | VARCHAR(64) | eval 输出的错误类型 |
| emotion | VARCHAR(16) | 该轮情绪（F7 七态） |
| step_index | INT | |
| student_answer | TEXT | 学生原答 |
| created_at / updated_at | DATETIME | 标准审计列 |
| created_by / modified_by / is_deleted | BIGINT / TINYINT(1) | 标准审计列（默认 0 / 逻辑删除） |

## Python 端点契约（L0 单次调用）

> 实现位于 `ai-edu-ai-service` 独立答疑模块；本仓库定义契约。Java 通过内部 token 调用，Python 不碰任何数据源。`subject_hint` 恒传 `math`。

### `POST /api/tutoring/decide`（非流式，快模型）

请求：`{history, round_count, answer_request_count, mastery_snapshot, subject_hint}`
- **判定链路（关键）**：换题 / 当前题目由 **Python decide 从 `history` 语义判断**，Java **不发送、不记录、不维护题目内容**——记录易错（OCR 乱码、模型转述、陈旧快照），判定权全在 Python。Java 只认 `type=switch` 事件重置计数，`new_question` 为 Python 输出、Java 仅作展示可选、不落库。
- `mastery_snapshot` 必须是 `[{kp_key, label, mastery_level}]`——**label 必带**，Python 侧用它做"label 接地"（优先复用已知知识点名，降低 Java label→URI 解析噪声）
响应：决策 3 的 action 元数据（type 闭集 + eval + mastery_signals + new_question + end_reason + summary + safety_flag + degraded）。若学生消息过简无题目 → type=concept 带澄清问题（由 decide 决定，Java 按 type 放行）。结构化输出失败兜底返回 **200 + ActionMeta(type=hint, degraded=true)**，不返回 503。

### `POST /api/tutoring/generate`（流式 SSE，强模型）

请求：`{history, subject_hint, action_type(已放行), action_meta}`（含已放行的 type 约束）
响应：SSE 流式正文，与 action_type 一致（approach 只给思路、reveal 给完整答案等）。

### `POST /api/ocr/recognize`（非流式，OCR 前置）

请求：`multipart file`（题目照片）
响应：`{text, confidence}`。Java 编排：前端上传 → Java 代理调此端点 → 返回识别文本供学生确认/修改 → 确认后作为**首条学生消息**进答疑。**不进 decide/generate 契约。**

## 安全过滤

Java 侧两层：① 本地关键词（自伤/暴力等）→ 直接终止转人工标记；② decide 输出 `safety_flag` 字段（高危内容标记），Java 判定后终止。对话脱敏、PII 合规沿用用户域约定。

## 错误处理与降级

- Python decide/generate 调用失败：重试 1 次；仍失败回复"网络波动，请重试"，会话保持 ACTIVE 不断开
- Python 结构化输出兜底：返回 **200 + ActionMeta(type=hint, degraded=true)**（不使用 503），Java 按普通 hint 放行 + 记日志——保证 API 永不返回畸形 ActionMeta
- decide 输出缺字段/非法 type：走默认（type=hint），记日志，不阻断（`degraded` 场景被此逻辑自然覆盖）
- reveal 被护栏拒绝后重决策仍输出 reveal：Java 直接降级为固定思路话术 + count→1
- 掌握度解析 label 失败：不点亮，记日志，收尾标记"待收录"
- round 达 20 后学生继续发言：Java 强制 end(ROUND_LIMIT) 收尾，提示"本轮已结束"
