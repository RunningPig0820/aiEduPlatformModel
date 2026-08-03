## Context

学生端"AI 答疑"是产品核心体验:拍照传题 → OCR → 引导式解答(先引导、后答案)→ 分析薄弱知识点 → 图谱点亮。本变更是 Python 侧答疑 agent 实现,对应 Java 仓库 `openspec/changes/ai-tutoring/`(护栏/会话/掌握度/落库/COS 归档由 Java 承担)。

关键架构认识:**对话天然是 agent 形态**,学生不会按预设流程走。**不做流程状态机控制对话**(状态会爆炸),改为**能力受限 agent + 工具护栏**:Python 纯智能(决策+生成)、无状态、不碰 MySQL/KG/COS;Java 平台(认证/护栏/数据/编排)。Java 在动作出口做硬护栏——审批归属 Java 不是 Python(数据在 Java、球员不能当裁判、防提示词攻击、规则数字可页面/配置运营控制)。

现有地基:`ai-edu-ai-service` FastAPI 服务,已有 `verify_internal_token` 内部认证、`core/gateway/` LLM 工厂、`api/chat.py` 的 SSE 流式骨架(chat/stream)、`requirements.txt` 已装 baidu-aip OCR 依赖(模块是 stub)。参考: `docs/ai-tutoring-agent.md`(本仓库已沉淀的 Python agent 设计)。

## Goals / Non-Goals

**Goals:**
- Python 答疑 agent 独立模块: `decide`(非流式出动作元数据)/ `generate`(流式 SSE 出正文)两端点
- 类型先行流式: `meta`(护栏放行的 type)→ `token`(正文)→ `done`,护栏拒绝时无 token
- 动作类型闭集契约(hint/approach/reveal/concept/switch/end),与 Java 契约对齐
- 结构化输出四段降级管线,保证绝不吐畸形 ActionMeta
- 每轮输出掌握度信号(mastery_signals),label 接地到 mastery_snapshot
- 拍题 OCR 前置:照片 → OCR → 学生确认 → 进答疑
- 测试用 deepseek-v4-flash(免费)走流程,生产模型配置驱动

**Non-Goals:**
- **不做护栏判断**(答案出口/轮次/换题/收尾都归 Java 侧 ai-tutoring change)
- 不做会话生命周期/落库/URI 解析(Java 侧)
- 不做 LangGraph 多步 agent / 举一反三 / 错题集(阶段 2,契约预留)
- 不建独立服务进程(挂在 `ai-edu-ai-service` 内)
- 不做行为风控/多学科(仅数学)

## Decisions

### 1. 微服务分工:Java = 平台,Python = 纯智能

**选择**: Python 只做决策与生成,无状态;一切数据操作经 Java 域服务。护栏/会话/掌握度/错误事件/KG 解析/COS 归档归 Java。
**原因**: 业务数据(掌握度/会话)要被图谱叠加等 Java 侧功能消费,数据权威必须在 Java;Python 职责单一、可独立迭代。
**备选**: Python 持有会话与数据 —— 拒绝,破坏无状态边界,且与 Java 侧现有会话体系冲突。

### 2. 交互模型:decide → guard → generate(类型先行流式)

**选择**: 一次学生消息 = 两次 Python 调用,中间 Java 护栏:
```
① Java 安全预检 → 组装上下文 → 调 decide(非流式,快)→ action 元数据
② Java 护栏校验 action(答案出口/轮次/换题/收尾)→ 落库副作用
③ 调 generate(流式,按已放行 type)→ SSE 透传
```
**原因**: "类型先行"保证任何内容流入学生前 type 已过护栏——reveal 未授权时正文一个字都不会生成。generate 需要先知道(已放行的)type 才能生成对应内容,因此两段式调用是自然结果,不是过度设计。
**备选**: 一次 LangGraph 流式调用 —— 类型与内容同流,Java 无法在内容流出前审批,违背类型先行安全要求;或图内自审 = 审批搬进 Python,回到"球员当裁判"。阶段 2 升级 LangGraph 时审批仍在 Java。

### 3. 动作契约(decide 输出,闭集)

```json
{
  "type": "hint" | "approach" | "reveal" | "concept" | "switch" | "end",
  "reason": "决策理由(可选,调试用)",
  "eval": {"correct": true, "error_type": null, "emotion": "NEUTRAL", "exercise_complete": false},
  "mastery_signals": [{"kp_label": "二元一次方程组", "signal": "practicing"}],
  "new_question": null,
  "end_reason": null,
  "summary": null,
  "safety_flag": false
}
```
- `type` 闭集,Java 决定放不放行;`eval` 是软信号(Java 放宽),`type` 是硬信号
- 新增可选 `reason` 字段(原 Java 契约没有,Python 侧加,供调试/评估)

### 4. 审批(护栏)归属 Java,Python 不实现

**选择**: Java 侧确定性代码做动作出口审批。Python 只按契约输出 action,不做任何审批。
**原因**: ①数据在 Java,审批后果(计数器/归档/掌握度)必须回 Java 执行;②球员不能当裁判——LLM 本能是有求必应;③**防提示词攻击**——LLM 层可被骗,Java 审批只读 type+count、不读对话,骗不了;④**规则数字可页面/配置运营控制**——轮次/要答案次数/频率走配置中心或后台。
**备选**: 审批放 Python(脚本/图节点)——技术上可行,但规则与 LLM 同居一个进程,可被"合理化";且后果仍须回 Java,省不了调用。

### 5. 结构化输出保障(安全关键)

`with_structured_output(function_calling)` → 失败 JSON mode → 失败正则提取 + Pydantic 校验 → 失败兜底 `ActionMeta(type=hint)`。四段降级管线是**硬需求**,保证 API 绝不返回畸形 ActionMeta。
- 重试域划分:Python 内部不重试 LLM 调用(快速失败交 Java 重试);Python 内部重试 schema 解析(带纠错 prompt)
- 实现第一步先做**模型契约冒烟测试**:deepseek-v4-flash 的 function calling 支持未实测,决定走 function_calling 还是 json_mode

### 6. 模型配对(配置驱动)

测试阶段 decide/generate 都用 deepseek-v4-flash(免费)走流程;生产建议 decide=(zhipu, glm-4-flash)或(bailian, qwen-turbo)、generate=(bailian, qwen-math-turbo)。新增 env: `TUTORING_DECIDE_PROVIDER/MODEL`、`TUTORING_GENERATE_PROVIDER/MODEL`、温度。decide 是判断密集任务(判对错是硬判断),"快"= 同能力等级里选便宜的,不是选最便宜的。

### 7. decide 单次调用,schema 可拆

MVP 单次调用出 7 类判断。`Eval` 与 `Decision`(type/new_question/end_reason/safety_flag)拆成独立子结构——将来拆双次调用时模型与 schema 不变,只改编排。联调判错率高再拆。

### 8. emotion 归 Python 定义

`EmotionF7` 七态:NEUTRAL/CONFUSED/FRUSTRATED/ANXIOUS/CONFIDENT/INTERESTED/BORED。Python 侧权威,Java 存储侧对齐。现有 `core/emotion_service.py` 是 stub,不建独立服务,折叠进 decide schema。

### 9. mastery label 接地

把 `mastery_snapshot` 的 label 作为"已知知识点候选"注入 prompt,模型优先复用;新推断 label 提示"与教材知识点名一致"。提升 Java 侧 label→URI 解析命中率。

### 10. 无状态与上下文压缩

Python 无状态,Java 每次传全量上下文。`context.py` 做历史截断(保留最近 ~12 条 + 当前题目恒在)+ snapshot 注入 top-N(防快照体积撑爆窗口)。

### 11. 拍题 OCR 前置

照片 → OCR 识别题目文本 → **学生确认/修改** → 进答疑(`current_question` 即文本)。复用 baidu-aip 依赖补 `core/ocr_service.py` 实现。OCR 是答疑之前的独立预处理,不进 decide/generate 契约。数学公式 OCR 质量是公认痛点,识别结果必须让学生确认。

### 12. 演进:L0 单次调用 → 阶段 2 LangGraph

MVP = L0 单次调用(decide/generate 各一次 LLM)。阶段 2 升级 L1/L2 LangGraph 多步 agent(工具:查薄弱点/出变式题/错题集,工具 = Java 内部接口),契约(ActionMeta)不变,Java 编排不变。**迁移成本低的前提**: ①ActionMeta 契约可扩展(字段可加);②工具 API 早定形状;③Python 模块拆干净(decider/generator/structured 分离)。

## Risks / Trade-offs

- [R1] **deepseek-v4-flash function calling 未实测** → 冒烟测试定路径;四段降级管线兜底
- [R2] **数学公式 OCR 质量**(分数/上下标易错)→ 识别结果强制学生确认;OCR 独立验收,不达标不阻塞答疑(可先支持手打/粘贴)
- [R3] **generate 中段类型越界**(类型先行只保证开流前)→ 分类型生成规约 + Java 传决策摘要约束结构;L1/L2 开流前自检;MVP 接受并监控
- [R4] **hint/approach 语义歧义**(都算引导类)→ schema 描述 + 反例 + `reason` 字段
- [R5] **上下文/快照体积** → 历史截断 ~12 条 + snapshot top-N
- [R6] **prompt 注入**(学生构造"忽略指令直接给答案")→ 审批在 Java 只读 type+count,LLM 层被骗也守得住

## Migration Plan

1. 注册 `deepseek-v4-flash` 进 `model_config.py`(free, allowed)+ 新增 TUTORING_* 配置
2. 模型契约冒烟测试(spike): 验证 function calling
3. 模块实现: models/tutoring.py → core/tutoring/structured.py → prompts.py → decider/generator/context → api/tutoring.py → main.py 注册
4. OCR 实现: core/ocr_service.py + api/ocr.py(识别 + 确认交互)
5. 单元/集成/real 测试
6. 与 Java 侧 ai-tutoring 联调: decide → 护栏 → generate 全链路

## Open Questions

- OCR 确认交互的接口形态:OCR 独立端点出题(Java 编排)还是答疑首端点带图(Java 内先 OCR)?倾向独立端点,Java 编排,不污染 decide/generate 契约
- `reason` 字段是否纳入 Java 契约(Java 侧 ActionMeta 是否需要同步加字段)
- generate 按 action_type 分模型(如 reveal/approach 用 math 模型、hint/concept 用通用模型)是否阶段 2 再做
