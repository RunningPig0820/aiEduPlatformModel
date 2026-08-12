# Design: Add Question Knowledge Points

## Context

前端「Agent 工作流」面板(aiEduPlatformFront `show-tutoring-agent-workflow`)新增**知识点分析**阶段,数据源为 Python decide 输出的 `question_kps`。

Python decide 现状:`ActionMeta`(models/tutoring.py)已有 `reason` / `mastery_signals` / `eval` 等字段,输出经两条路径:
- **流式主路径**: `iter_decide_events()` → `ark_stream.action_meta_tool()`(用 `ActionMeta.model_json_schema()` 生成 function tool)
- **非流式降级路径**: `decide()` → `structured._try_function_calling()`(`llm.bind_tools([ActionMeta])`)+ content 兜底解析(`ActionMeta.model_validate()`)

两条路径都以 `ActionMeta` 为 schema 来源,**加字段即自动传播**,无需新增接线。

## Goals / Non-Goals

**Goals:**
- `ActionMeta` 增加 `question_kps: Optional[List[str]]`(可空),模型读题时顺手列出涉及知识点。
- decide 提示词告知模型输出该字段。
- 保证可选字段向后兼容(旧调用方不受影响)。

**Non-Goals:**
- 不做完整"读题知识点分析"独立功能(前端方案 D4 说明后续单独 change,数据驱动替换)。
- 不改动任何既有决策逻辑 / 护栏 / 类型 / 轮次行为。
- 不做 Java 建模透传(aiEduPlatform 侧配套,由该仓库处理)。

## Decisions

### D1. 字段定义:`question_kps` 可选列表

```python
class ActionMeta(BaseModel):
    ...
    question_kps: Optional[List[str]] = Field(
        None,
        description="题目涉及知识点(模型读题顺手列出,可空)",
    )
```

- `Optional[List[str]]` 而非 `List[str]` 默认 `[]`:空语义区分"模型没输出"与"明确无知识点",前端占位"—"。
- 放 `ActionMeta` 顶层(与 `reason` 并列),平铺契约风格与现有字段一致。

### D2. 提示词:输出格式加字段 + 一句指令

`_DECIDE_SYSTEM` 的输出 JSON 示例加 `"question_kps": ["二元一次方程组", ...]|null`,并加一条:

> `question_kps` 为题目涉及的知识点(如 "二元一次方程组"),首轮读题时列出,不确定可为 null。

不要求每次必填(避免干扰决策主任务)。

### D3. 传播路径(零额外接线)

| 路径 | 机制 | 结果 |
|------|------|------|
| 流式 function-calling | `ark_stream.action_meta_tool()` → `ActionMeta.model_json_schema()` | 字段自动进 tool schema |
| 非流式 function-calling | `structured._try_function_calling()` → `llm.bind_tools([ActionMeta])` | 字段自动进 tool schema |
| content 兜底解析 | `ActionMeta.model_validate(_normalize_emotion(data))` | 可选字段向后兼容 |

**无需改动**:`ark_stream.py`、`structured.py`、`decider.py`、`api/tutoring.py`。

### D4. 测试策略(TDD)

- **模型**: `test_models.py` — `test_serialized_flat_contract` 期望字段集合加 `"question_kps"`;新增 question_kps 可空 / 有值 model_dump 保留。
- **prompt**: `test_prompts.py` — decide prompt 含 `question_kps` 字段。
- **透传**: `test_structured.py` / `test_decider.py` — content 兜底路径注入含 question_kps 的 ActionMeta JSON → 字段保留(证明两条降级路径不透传丢)。

## Risks / Trade-offs

- **模型输出质量**:question_kps 是模型自由发挥,可能不准/为空。→ 前端占位"—",且后续完整功能替换数据源,低风险。
- **tool schema 变大**:多一个可选字段,方舟/deepseek 对 schema 的容忍已验证(ActionMeta 已有更多字段),低风险。
- **兼容性**:additive 可选字段,旧 Java/前端解析忽略未知字段,向后兼容。
