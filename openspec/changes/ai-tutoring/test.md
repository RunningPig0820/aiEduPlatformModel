# AI 答疑 Python Agent 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 Python 答疑 agent 的所有业务场景:decide 闭集动作元数据、generate 分类型流式、结构化输出降级、OCR 前置、边界判定(无关/换题/收尾),确保契约与 Java 侧 ai-tutoring 对齐。

### 1.2 测试方式
- **unit**: 纯函数/管线测试(mock LLM 各段失败、schema 校验、prompt 断言)
- **integration**: TestClient 调用真实端点 + mock LLM(`pytest-httpx` / monkeypatch)
- **real**: 真实 deepseek-v4-flash 调用(无 key 时 skip)

### 1.3 测试环境配置
- pytest 配置:`ai-edu-ai-service/pytest.ini`(沿用现有 tests/llm 分层)
- 目录:`tests/tutoring/{unit, integration, real}`
- 环境:`.env`(内部 token + TUTORING_* 配置)

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|------|
| INTERNAL_TOKEN | test-internal-token | 内部认证 token |
| QUESTION | 鸡兔同笼，共35头94脚，各几只？ | 当前题目 |
| KP_LABEL | 二元一次方程组 | 知识点 label |
| MODEL_TEST | deepseek/deepseek-v4-flash | 测试模型 |

---

## 3. 测试用例清单

### 3.1 decide 端点(integration)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| DECIDE-001 | 正常决策 | mock LLM 返回合法 action | 完整 decide 请求 | 返回 ActionMeta,type 属闭集 |
| DECIDE-002 | 缺内部 token | 无 | 无 x-internal-token | 403 |
| DECIDE-003 | token 错误 | 无 | 错误 token | 403 |
| DECIDE-004 | 参数校验失败 | 无 | history 缺失/round_count 负 | 422 |
| DECIDE-005 | 学生要答案 | mock 返回 reveal | 消息含"答案给我" | type=reveal(放行与否由 Java,Python 不审批) |
| DECIDE-006 | LLM 调用失败 | mock LLM 抛异常 | 合法请求 | 500(Java 重试) |
| DECIDE-007 | LLM 输出畸形 | mock 输出非 JSON | 合法请求 | 兜底 ActionMeta(type=hint),可解析 |

### 3.2 generate 端点(integration)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| GEN-001 | 正常流式 | mock 返回 token 流 | action_type=hint | SSE: token... → done |
| GEN-002 | action_type 非法 | 无 | type=xxx(非闭集) | 422 |
| GEN-003 | 流中失败 | mock 中段抛异常 | 合法请求 | event: error,流终止 |
| GEN-004 | approach 约束 | mock | action_type=approach | 生成内容含思路大纲、不含最终数值答案(real 校验) |

### 3.3 structured 降级管线(unit)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| STR-001 | function_calling 成功 | mock 第一段成功 | LLM 输出 | 直接返回合法 ActionMeta |
| STR-002 | function_calling 失败→JSON mode | mock 第一段失败 | LLM 输出 | 第二段解析成功 |
| STR-003 | 前两段失败→正则提取 | mock 前两段失败 | 混杂文本 | 正则提取 + Pydantic 通过 |
| STR-004 | 全失败→兜底 | mock 全部失败 | 无 | ActionMeta(type=hint),记日志 |
| STR-005 | 兜底可校验 | — | 任意路径 | 返回值通过 Pydantic 校验 |

### 3.4 prompt 断言(unit)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| PROMPT-001 | 分类型生成规约齐全 | — | prompts 模块 | 六种 type 各有硬约束 |
| PROMPT-002 | hint 禁数值 | — | hint 规约 | 包含"零步骤/不含数值"约束 |
| PROMPT-003 | snapshot label 注入 | — | decide prompt | 含 snapshot 候选 label |
| PROMPT-004 | exercise_complete 联动 | — | decide prompt | 含 type=end + COMPLETED 约束 |

### 3.5 OCR(integration)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| OCR-001 | 识别成功 | mock OCR | 图片 | 返回 text + confidence |
| OCR-002 | 无效图片 | 无 | 非图片文件 | 400 |
| OCR-003 | 缺内部 token | 无 | 无 token | 403 |
| OCR-004 | 识别失败 | mock OCR 抛异常 | 合法图片 | 500 |

### 3.6 边界用例(unit,decide 判定)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| BOUND-001 | 学生"我不会" | mock | 过简消息 | type=concept(澄清),**不终止** |
| BOUND-002 | 学生"老师你好" | mock | 打招呼 | type=concept(澄清),**不终止** |
| BOUND-003 | 闲聊"今天天气" | mock | 无关消息 | type=end(终止) |
| BOUND-004 | 英语题 | mock | 非数学 | type=end(终止) |
| BOUND-005 | 贴新题 | mock | 新题文本 | type=switch + new_question |
| BOUND-006 | 独立解出 | mock | 正确+完整 | exercise_complete=true 联动 type=end/COMPLETED |
| BOUND-007 | 高危内容 | mock | 自伤/暴力 | safety_flag=true |

### 3.7 real(真实模型,skip 无 key)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| REAL-001 | 全流程答疑 | 有 key | 发起→引导→回答→换题→收尾 | decide/generate 契约符合预期,掌握度信号输出 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 403 | UNAUTHORIZED | 内部 token 缺失/不匹配 |
| 422 | INVALID_PARAMS | Pydantic 参数校验失败 |
| 500 | INTERNAL_ERROR | LLM / OCR 调用失败 |
| 503 | DEGRADED | 结构化输出兜底 type=hint(Java 按 hint 放行) |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| decide | 7 |
| generate | 4 |
| structured | 5 |
| prompt | 4 |
| OCR | 4 |
| 边界 | 7 |
| real | 1 |
| **总计** | **32** |

---

## 6. 测试执行顺序

```
tests/tutoring/unit/test_prompts.py      : prompt 断言
tests/tutoring/unit/test_structured.py   : 降级管线
tests/tutoring/unit/test_boundary.py     : 边界判定
tests/tutoring/integration/test_decide.py: decide 端点
tests/tutoring/integration/test_generate.py: generate 端点
tests/tutoring/integration/test_ocr.py   : OCR 端点
tests/tutoring/real/test_tutoring_real.py: 真实模型(有 key 才跑)
```

---

## 7. 辅助方法

### 7.1 内部 token 请求头
```python
def tutoring_headers() -> dict:
    """内部认证头(复用 verify_internal_token 校验)"""
    return {"x-internal-token": settings.INTERNAL_TOKEN}
```

### 7.2 mock LLM(结构化输出)
```python
def mock_action_meta(meta: dict):
    """monkeypatch decider 的 LLM 调用,返回指定 ActionMeta 或抛异常"""
    # 用于 DECIDE-005/006/007、structured 各段失败覆盖
    ...
```

### 7.3 构造合法请求体
```python
def decide_payload(**overrides) -> dict:
    """构造 decide 请求(默认合法值,按覆盖字段调整)"""
    base = {
        "history": [{"role": "user", "content": "设鸡有x只，则兔有35-x只"}],
        "round_count": 2,
        "answer_request_count": 0,
        "current_question": "鸡兔同笼，共35头94脚，各几只？",
        "mastery_snapshot": [{"kp_key": "http://edukg.org/knowledge/3.1/x", "label": "二元一次方程组", "mastery_level": 50}],
        "subject_hint": "math",
    }
    base.update(overrides)
    return base
```

---

## 8. 运行测试

```bash
# 运行全部答疑测试
pytest ai-edu-ai-service/tests/tutoring/ -v

# 运行单个文件
pytest ai-edu-ai-service/tests/tutoring/unit/test_structured.py -v

# 运行单个用例
pytest ai-edu-ai-service/tests/tutoring/integration/test_decide.py::test_normal -v

# 运行真实模型测试(需 .env 配好 deepseek-v4-flash key)
pytest ai-edu-ai-service/tests/tutoring/real/ -v

# 覆盖率
pytest --cov=core.tutoring --cov-report=term-missing ai-edu-ai-service/tests/tutoring/
```
