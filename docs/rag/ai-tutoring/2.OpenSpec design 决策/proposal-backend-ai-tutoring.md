## Why

学生端"AI 答疑"是产品核心体验：**引导式解答而非直接给答案**，并在答疑过程中沉淀学生知识点掌握度，联动知识图谱点亮。

关键认识：对话天然是 agent 形态——学生不会按预设流程走（中途换题、问概念、要答案、闲聊）。**用流程状态机控制对话分支会导致状态爆炸**，因此采用**能力受限的 agent + 工具护栏**架构：Python 侧是纯智能的答疑 agent（决策 + 生成），Java 侧是平台（认证网关 + 护栏 + 数据 + 基础设施），Python 不直接碰 MySQL / KG / COS。

现有地基：EduKG 知识图谱（Neo4j 源 + kg-sync 按 URI 镜像到 MySQL `KgKnowledgePointPo`）、`FileStorageService`（腾讯云 COS）。**缺口**：答疑 agent、护栏层、对话存储、掌握度落库与图谱点亮。

本期新增 `tutoring`（AI 答疑）能力：**Java 网关主导编排（安全 → decide → 护栏 → generate 流式）**；Python 答疑 agent（现有 `ai-edu-ai-service` LLM 服务内的独立模块，不单独起服务）暴露 `decide`（非流式出动作元数据）/ `generate`（流式出正文）两个端点，动作 `type` 为闭集（能力受限），Java 在动作出口做硬护栏（答案出口 / 轮次 / 换题 / 收尾）。答疑中渐进确认知识点掌握度，按**知识图谱 TextbookKP URI 作为 key** 落库，供图谱前端叠加展示。MVP 为 L0 单次调用（LangChain 结构化输出），演进可升级 LangGraph 多步 agent。

## What Changes

- 新增 `tutoring` 有界上下文（Java Domain / Application / Infrastructure / Interface），核心是**护栏服务 + 编排服务**
- 新增 3 张表（Flyway V9+）：`t_tutoring_session`（含 `end_reason`/`transcript_url`，**不存题目内容**）、`t_student_kp_mastery`、`t_tutoring_error_event`（**不建消息表**：对话每轮实时整写 COS 恒完整，Redis 活跃期热存）
- 会话对话全程实时写 COS：复用 `FileStorageService`（腾讯云 COS），写入 `tutoring/transcripts/{sessionId}.json`，COS 恒为完整对话，用于训练数据闭环、审计、复盘
- 定义 Python **答疑 agent**（现有 `ai-edu-ai-service` 内的独立模块）2 个端点契约：`POST /api/tutoring/decide`（非流式，输出 action 元数据：type/eval/mastery_signals/new_question/end_reason/safety_flag）、`POST /api/tutoring/generate`（流式 SSE，按已放行 type 输出正文）。**本仓库只定契约与 prompt 设计；Python 实现在 `ai-edu-ai-service` 独立模块，另行排期**
- **类型先行流式**（SSE）：`meta`（护栏已放行的 type）→ `token`（正文流）→ `done`（状态 + eval），护栏拒绝时**无 token 流**，保证任何内容流入学生前已完成校验
- **拍题 OCR 前置**：前端上传照片 → Java 代理调 Python `/api/ocr/recognize` → 返回识别文本供学生确认/修改 → 确认后作为**首条学生消息**进答疑（用户题目输入的唯一入口，本期必做）
- 新增答疑 REST + SSE API：发起会话、发送学生回答、请求答案、会话状态/断点恢复、归档、掌握度查询、**OCR 识别**
- **护栏（Java，确定性）**：答案出口（第 1 次思路 / 第 2 次答案，Java 硬拦）、轮次上限（20）、换题计数重置、安全过滤、收尾按 end_reason 校正掌握度
- 学生知识点掌握度按 `TextbookKP URI` 为 key 落库；label→URI 解析复用 kg-sync 的 MySQL 镜像；图谱点亮采用**前端叠加掌握度**（掌握度单源 MySQL，不写 Neo4j）

## Capabilities

### New Capabilities
- `ai-tutoring`: AI 答疑（能力受限 agent + 工具护栏）— Java 网关编排（安全 → decide → 护栏 → generate 流式）、动作闭集与护栏规则（答案出口/轮次/换题/收尾）、知识点渐进确认与掌握度落库（TextbookKP URI key）、错误事件、会话生命周期（ACTIVE/ARCHIVED/TERMINATED）、对话实时写 COS（恒完整）、图谱点亮联动

## Impact

- 新增 Domain 层：`com.ai.edu.domain.tutoring` 上下文
  - 聚合根 `TutoringSession`（**生命周期 3 态** ACTIVE/ARCHIVED/TERMINATED + 护栏计数器，无流程状态机）
  - 实体 `StudentKpMastery`、`ErrorEvent`（无消息实体）
  - 值对象 `TutoringState`、`ActionType`（闭集）、`EndReason`、`KpKey`、`MasterySignal`、`TutoringQuestionType/QuestionKind`
  - 仓储接口 `TutoringSessionRepository`、`StudentKpMasteryRepository`、`ErrorEventRepository`
- 新增 Application 层：`TutoringGuardrailService`（护栏校验，核心）、`TutoringAppService`（编排：安全→上下文→decide→护栏→落库→generate）、`TutoringContextAssembler`、`TutoringTranscriptArchiver`（COS 归档）
- 新增 Infrastructure 层：
  - Flyway 迁移 3 张表
  - MyBatis-Plus PO / Mapper / RepositoryImpl
  - Redis 活跃会话缓存（`TutoringSessionCache`，状态 + 完整消息，断点恢复 + 频率计数）
  - `TutoringKpResolver`（label → TextbookKP URI，复用 `KgKnowledgePointPo` 镜像）
  - `TutoringLlmClient`（WebClient 调 Python decide/generate，含 SSE）
- 新增 Interface 层：`TutoringController`（REST + 类型先行流式 SSE）+ `OcrController`（`POST /api/tutoring/ocr`，图片上传 → 代理 Python 识别）
- 新增 Infrastructure 层：`TutoringOcrClient`（WebClient 调 Python `/api/ocr/recognize`）
- 新增 Python 独立答疑 agent 端点契约（含 decide/generate/**OCR**，本仓库 `docs` 或 spec 内定义；Python 实现另排期）
- 复用：`KgKnowledgePointPo`（label→URI）、`KgSubjectEnum`（数学限定）、`FileStorageService`（COS 归档）、llm-gateway 的 `internalToken` 模式（Java↔Python 内部认证）

## Non-Goals（本期不做）

- LangGraph 多步 agent（L1/L2）、自适应学习（查薄弱点/出变式题）——阶段 2，工具接口已按 Java 内部 API 预留
- 题库指纹 / 结构化步骤 / 易错分支预置（阶段 2 题库增强）
- 行为风控模型 / 多维能力画像 / 薄弱点可视化报告（阶段 3）
- 多学科图谱（本期仅数学，语文/英语无图谱节点）
- OCR 只做题目文本识别；公式/手写深度识别、图形题识别属后续（识别结果必须经学生确认）
- Python 侧 `decide`/`generate`/OCR 的实际实现与部署
