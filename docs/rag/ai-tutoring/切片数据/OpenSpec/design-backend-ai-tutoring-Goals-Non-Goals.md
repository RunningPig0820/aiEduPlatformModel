# design-backend-ai-tutoring

> summary: 答疑AI后端的目标、非目标及核心规则说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-Goals-Non-Goals.md
> 类别：项目介绍

---

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
