# question_kps 测试用例设计

## 1. 测试概述

### 1.1 测试目标

验证 ActionMeta 新增可选字段 `question_kps` 的正确性:模型定义、提示词声明、两条 function-calling 路径(content 兜底)透传,以及向后兼容(可空)。

### 1.2 测试方式

- **单元测试**:纯函数/模型层,无网络调用(不依赖真实 LLM)
- **注入 fake streamer / fake llm**:测试 content 兜底透传路径
- 运行目录:`ai-edu-ai-service/tests/tutoring/`

### 1.3 测试环境配置

- 解释器:`ai-edu-ai-service/venv/bin/python`
- 命令:从 `ai-edu-ai-service` 目录运行 `venv/bin/pytest tests/tutoring/ -q`

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|------|
| VALID_META | 见 test_models.py `_valid_meta()` | ActionMeta 有效输入(含 reason/eval/mastery_signals) |
| KPS | `["二元一次方程组", "一元一次方程"]` | question_kps 有值样本 |

---

## 3. 测试用例清单

### 3.1 模型定义(test_models.py)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MOD-001 | 平铺契约含 question_kps | ActionMeta 模型 | `_valid_meta()` | `model_dump()` 字段集合含 `"question_kps"` |
| MOD-002 | question_kps 可空 | 模型 | `_valid_meta()`(无 question_kps) | 校验通过,字段为 `None`,无错误 |
| MOD-003 | question_kps 有值保留 | 模型 | `_valid_meta()` + `question_kps=KPS` | `model_dump()["question_kps"] == KPS` |

### 3.2 提示词(test_prompts.py)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| PRO-001 | prompt 含 question_kps | 无 | `build_decide_prompt()` | 提示词文本含 `question_kps` |
| PRO-002 | prompt 含知识点语义指令 | 无 | `build_decide_prompt()` | 含"知识点"语义指令(如示例或说明) |

### 3.3 透传路径(test_structured.py / test_decider.py)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| STR-001 | structured content 兜底透传 | FakeLLM 返回含 question_kps 的 ActionMeta content | `generate_action_meta()` | 返回 ActionMeta `question_kps == KPS` |
| DEC-001 | decider content 兜底流式透传 | fake streamer 返回含 question_kps 的 content | `iter_decide_events()` | meta 事件 `data.question_kps == KPS` |

---

## 4. 错误码对照表

本 change 不新增错误码(纯字段扩展,无新失败路径)。

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 模型定义 | 3 |
| 提示词 | 2 |
| 透传路径 | 2 |
| **总计** | **7** |

---

## 6. 测试执行顺序

按文件与方法名顺序执行,无跨用例依赖:

```
test_models.py     : 模型字段(先,因其他路径依赖模型定义)
test_prompts.py    : 提示词声明
test_structured.py : structured content 兜底透传
test_decider.py    : decider content 兜底流式透传
```

---

## 7. 辅助方法

### 7.1 Fake content 兜底 streamer(decider)

```python
def fake_streamer_content(**kwargs):
    yield {"reasoning": None, "content": json.dumps(
        {"type": "hint", "reason": "r", "eval": {"correct": True},
         "question_kps": ["二元一次方程组"]}, ensure_ascii=False),
        "tool_calls": None}
```

### 7.2 验证命令

```bash
cd ai-edu-ai-service && venv/bin/pytest tests/tutoring/unit/test_models.py::TestActionMeta -q
cd ai-edu-ai-service && venv/bin/pytest tests/tutoring/unit/test_prompts.py -q
cd ai-edu-ai-service && venv/bin/pytest tests/tutoring/unit/test_structured.py tests/tutoring/unit/test_decider.py -q
```
