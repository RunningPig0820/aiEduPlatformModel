# Add Question Knowledge Points

## Why

前端「Agent 工作流」面板(openspec: `aiEduPlatformFront/openspec/changes/show-tutoring-agent-workflow`)要展示**知识点分析**阶段:首轮读题即显示题目涉及的知识点(如"二元一次方程组")。数据源 = Python decide 输出的 `question_kps`。当前 `ActionMeta` 无此字段,模型读到也不输出。需要补上,让前端槽位数据驱动(为空显示占位,后续独立"读题知识点分析"功能可替换数据源)。

## What Changes

- `ActionMeta` 新增可选字段 `question_kps: Optional[List[str]]`(模型读题时顺手列出涉及知识点,可空;不额外调用、不改决策逻辑)。
- decide 系统提示词(`_DECIDE_SYSTEM`)输出格式增加 `question_kps` 字段 + 一句指令。
- 字段经 `ActionMeta.model_json_schema()` / `bind_tools` 自动传播到两条 function-calling 路径(流式 `ark_stream.action_meta_tool` + 非流式 `structured`),零额外接线。
- 兼容:可选字段,旧调用方不受影响;Java 建模透传是 aiEduPlatform 侧配套(本 change 不含)。

## Capabilities

### New Capabilities

- `tutoring-question-kps`: decide 输出题目涉及知识点列表(`question_kps`),供前端"知识点分析"阶段展示。

### Modified Capabilities

<!-- 无既有已归档 spec 需要变更。ai-tutoring change 仍 in-progress,ActionMeta 契约在其 spec 中扩展。 -->

## Impact

- **Python(aiEduPlatformModel,本 change)**:`models/tutoring.py`(ActionMeta 加字段)、`core/tutoring/prompts.py`(decide prompt 输出格式 + 指令)。
- **测试**:`test_models.py::test_serialized_flat_contract` 断言字段集合精确相等,需加入 `"question_kps"`;新增 question_kps 可空/透传用例。
- **配套(不在本 change)**:aiEduPlatform Java `ActionMeta` + `SseMetaDTO` 建模透传;前端 `AgentWorkflowPanel` 知识点分析槽位消费。
- **数据契约**:decide `meta` 事件新增可选字段 `question_kps`,additive,向后兼容。
