# tutoring-subject-gate-python 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 subject-classify 端点：文本/图片学科分类、闭集输出、失败/闭集外空结果（Java 按 math 放行）、模型统一 + 慢修复参数（thinking off / 20s / retry 0）、内部鉴权、参数校验。

### 1.2 测试方式
- **Python 单元测试**：`tests/tutoring/unit/test_subject_classify.py`（核心 `classify_subject`，注入 FakeLLM）
- **Python API 测试**：`tests/tutoring/unit/test_subject_classify_api.py`（TestClient + mock LLMFactory，覆盖鉴权/参数校验/返回）
- 对齐后端 `test.md` PSC-001~005；Java 侧 GATE/CON/API 用例在后端 change 内。

### 1.3 测试环境配置
- 全部离线：注入 FakeLLM / mock `LLMFactory.create`，不打真实 LLM
- 与 test_question_understand 同模式（FakeLLM 注入 `classify_subject(req, llm=...)`）

---

## 2. 测试数据

| 参数 | 值 |
|-----|-----|
| CONTENT_PHYSICS | "物体做自由落体运动，求落地速度" |
| CONTENT_MATH | "鸡兔同笼，共35头94脚，各几只？" |
| IMAGE_URL | "https://cos-xxx/1.jpg" |

---

## 3. 测试用例清单

### 3.1 subject-classify 核心（PSC）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| PSC-001 | 文本物理题 | 纯文字 | content=自由落体… | subject=physics |
| PSC-002 | 文本数学题 | 纯文字 | content=鸡兔同笼… | subject=math |
| PSC-003 | 图片题目多模态 | image_url=受力图 | image_url 非空 | 多模态 HumanMessage（text+image_url 两个 part），subject 为学科 |
| PSC-004 | LLM 异常 | 注入抛错 llm | 任意输入 | 返回空 subject（None），不抛异常 |
| PSC-005 | 模型参数统一 | 不注入 llm，mock LLMFactory | 任意输入 | 使用 doubao-seed-2-0-mini-260428 / temp 0.3 + thinking disabled + request_timeout=20 + max_retries=0 |
| PSC-006 | 输出闭集外学科 | FakeLLM 返回 "geology"（非 K12 十值） | 任意输入 | subject=None（归一化空结果，不误判为 other） |
| PSC-007 | 无图纯文本通道 | 无 image_url | content 非空 | HumanMessage 为纯文本（无 image_url part） |

### 3.2 API 层（API）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| API-001 | 正常分类返回 | 合法 token | 文本数学题 | HTTP 200，body.subject=math |
| API-002 | 缺 token | 无 header | 任意输入 | HTTP 403 |
| API-003 | 非法 token | header 错误 | 任意输入 | HTTP 403 |
| API-004 | 全空参数 | content+image_url 均空 | `{"content": null, "image_url": null}` | HTTP 422 |
| API-005 | LLM 失败端点级 | mock classify 异常 | 任意输入 | HTTP 200 + subject=null（不 5xx） |

---

## 4. 错误码对照表

| 错误码 | 说明 |
|-------|------|
| 403 | `x-internal-token` 缺失/不匹配 |
| 422 | content 与 image_url 均为空 |
| - | 分类失败 → HTTP 200 `{"subject": null}`（不 5xx） |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| subject-classify 核心（PSC） | 7 |
| API 层（API） | 5 |
| **总计** | **12** |

---

## 6. 测试执行顺序

```
PSC-001~007 : 核心分类（文本/图片/失败/闭集外/模型参数）
API-001~005 : 端点层（鉴权/参数校验/失败降级）
```

---

## 7. 辅助方法

### 7.1 FakeLLM（core 层注入）
```python
class FakeLLM:  # 与 test_question_understand 同模式
    def __init__(self, content="math"): ...
    def invoke(self, messages): return Resp(content=self.content)

class BoomLLM:
    def invoke(self, messages): raise RuntimeError("boom")
```

### 7.2 mock LLMFactory（API 层，锁模型参数）
```python
with patch("core.tutoring.subject_classify.LLMFactory.create", return_value=fake) as m:
    resp = classify_subject(req)   # llm 默认 None → 走工厂
assert m.call_args.kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
assert m.call_args.kwargs["request_timeout"] == 20
assert m.call_args.kwargs["max_retries"] == 0
```

---

## 8. 运行测试

```bash
cd ai-edu-ai-service && ./venv/bin/python -m pytest tests/tutoring/unit/test_subject_classify*.py -v
# 全量离线回归
./venv/bin/python -m pytest tests/tutoring/unit/ -q
```
