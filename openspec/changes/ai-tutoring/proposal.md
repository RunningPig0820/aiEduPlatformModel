## Why

学生端"AI 答疑"是产品核心体验:学生**拍照传题 → OCR 识别 → 引导式解答(先引导、后答案)**。答疑中分析学生薄弱知识点,按知识图谱 TextbookKP 联动点亮学习情况。本变更实现 Python 侧答疑 agent(现有 `ai-edu-ai-service` LLM 服务内的独立模块),与 Java 仓库的 `ai-tutoring` change(护栏/会话/落库)契约对齐。

关键架构:对话天然是 agent 形态,不做流程状态机。**Python 纯智能(决策+生成),Java 平台(认证/护栏/数据/OCR 编排)**。Python 无状态、不碰 MySQL/KG/COS;护栏放 Java 侧确定性代码(防提示词攻击 + 规则数字可页面/配置运营控制)。

## What Changes

- **新增答疑 agent 模块**(`ai-edu-ai-service` 内,独立模块):
  - `POST /api/tutoring/decide`(非流式,快模型):输出动作元数据 ActionMeta(type 闭集 + eval + mastery_signals + new_question + end_reason + safety_flag)
  - `POST /api/tutoring/generate`(流式 SSE,强模型):按已放行 `action_type` 输出正文
- **动作类型闭集**:hint / approach / reveal / concept / switch / end;Java 在动作出口做硬护栏(本仓库不实现护栏,只按契约输出)
- **结构化输出保障**:function-calling → JSON mode → 正则提取 → 兜底 `type=hint` 四段降级管线(保证绝不吐畸形 ActionMeta)
- **类型先行流式**:`meta`(护栏放行的 type)→ `token`(正文流)→ `done`(状态 + eval)
- **拍题 OCR 前置**:照片 → OCR 识别题目文本 → 学生确认/修改 → 进答疑(`current_question` 即文本题目;复用 `ai-edu-ai-service` 现有 OCR 依赖,补实现)
- **掌握度信号**:每轮 decide 输出 `mastery_signals`(kp_label + mastered/practicing/struggling),label 接地到 `mastery_snapshot` 候选,Java 侧解析为 TextbookKP URI 落库点亮
- **测试用模型**:deepseek-v4-flash(免费)注册进 `model_config` 走流程;生产 decide=flash/turbo、generate=qwen-math-turbo,配置驱动

## Capabilities

### New Capabilities
- `ai-tutoring`: AI 答疑 agent(Python 侧)——decide/generate 双端点、动作类型闭集契约、结构化输出保障、类型先行流式 SSE、掌握度信号输出、拍题 OCR 前置。纯智能无状态,护栏/落库/会话归 Java(契约对齐 Java 仓库 `ai-tutoring` change)。

### Modified Capabilities
<!-- 无既有 spec 需求变更 -->

## Impact

- 新增 `ai-edu-ai-service/models/tutoring.py`(DTO + ActionMeta schema + 枚举)
- 新增 `ai-edu-ai-service/core/tutoring/`(decider / generator / structured / prompts / context)
- 新增 `ai-edu-ai-service/api/tutoring.py`(两个端点 + 内部 token + SSE)
- 修改 `ai-edu-ai-service/config/model_config.py`(注册 deepseek-v4-flash)
- 修改 `ai-edu-ai-service/config/settings.py`(新增 TUTORING_* 配置)
- 修改 `ai-edu-ai-service/main.py`(注册路由)
- 新增 `ai-edu-ai-service/core/ocr_service.py` 实现(补 OCR 识别,复用 baidu-aip)
- 复用 `verify_internal_token`(Java↔Python 内部认证)
- 与 Java 仓库 `openspec/changes/ai-tutoring/` 契约对齐(decide/generate 请求响应、ActionMeta 字段)
