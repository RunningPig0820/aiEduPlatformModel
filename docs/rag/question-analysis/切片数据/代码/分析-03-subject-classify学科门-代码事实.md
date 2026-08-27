# 分析-03-subject-classify学科门

> summary: (无 summary)
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 代码事实
> 模块: question-analysis ｜ 节: 分析-03-subject-classify学科门

---

## 代码事实

- **K12 十值闭集**：`SubjectType(math/physics/chemistry/biology/chinese/english/politics/geography/history/other)`。（`models/tutoring.py:182-197`）
- **输出结构**：`SubjectClassifyRequest(content?, image_url?)`；`SubjectClassifyResponse(subject: Optional[str])`。（`models/tutoring.py:200-220`）
- **模型/参数写死**：doubao-seed-2-0-mini-260428、temp 0.3、**关思考** + `request_timeout=20` + `max_retries=0`。（`core/tutoring/subject_classify.py:24-26,66-73`）
- **解析宽容**：`_parse_subject` 大小写/前后空白/多余文字（"答案:math"）都能命中；**闭集外 → None 而非 other**。（`subject_classify.py:45-55`）
- **绝不抛异常**：整个函数 try/except 包裹，LLM 失败/超时返回空 subject。（`subject_classify.py:65-87`）
- **0 请求校验**：`@model_validator` 校验 content/image_url 至少一个非空，否则 422。（`models/tutoring.py:205-209`）

### 枚举/常量/配置

| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 枚举 | SubjectType | math/physics/chemistry/biology/chinese/english/politics/geography/history/other | `models/tutoring.py:182-197` |
| 配置 | 模型 | doubao-seed-2-0-mini-260428 | `subject_classify.py:24-26` |
| 配置 | 温度 | 0.3 | `subject_classify.py:26` |
| 配置 | 思考 | 关（thinking disabled） | `subject_classify.py:70` |
| 配置 | 超时 | 20s | `subject_classify.py:71` |
| 配置 | 重试 | 0（关 SDK 重试） | `subject_classify.py:72` |
