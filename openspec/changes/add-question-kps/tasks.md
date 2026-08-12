## 1. 模型字段(TDD 先写测试)

- [x] 1.1 `test_models.py::test_serialized_flat_contract` 期望字段集合加入 `"question_kps"`(RED: 字段未加时失败)
- [x] 1.2 `test_models.py` 新增 question_kps 可空(null)用例(RED)
- [x] 1.3 `test_models.py` 新增 question_kps 有值时 model_dump 保留用例(RED)
- [x] 1.4 `models/tutoring.py` ActionMeta 加 `question_kps: Optional[List[str]] = Field(None, ...)`(GREEN)

## 2. 提示词(TDD 先写测试)

- [x] 2.1 `test_prompts.py` 新增 decide prompt 含 `question_kps` 字段断言(RED)
- [x] 2.2 `prompts.py::_DECIDE_SYSTEM` 输出格式加 `question_kps` 字段 + 一句指令(GREEN)

## 3. 透传路径测试(TDD)

- [x] 3.1 `test_structured.py` 新增 content 兜底解析注入含 question_kps 的 ActionMeta JSON → 字段保留(RED → GREEN 由 1.4 自然通过)
- [x] 3.2 `test_decider.py` 新增 content 兜底流式路径 question_kps 透传用例

## 4. 验证

- [x] 4.1 全量单元+集成测试通过(`venv/bin/pytest tests/tutoring/unit/ -q` 133 passed;`tests/tutoring/integration/ -q` 17 passed)
- [x] 4.2 `openspec validate add-question-kps` → "is valid"
