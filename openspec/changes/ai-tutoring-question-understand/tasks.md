# ai-tutoring-question-understand 实施任务

## 1. 模型契约（models/tutoring.py 或新模块）

- [x] 1.1 `QuestionUnderstandRequest`：`image_url: str`（必填）、`topic_hint: List[str]`（可选）、`grade: int`（可选）
- [x] 1.2 `QuestionUnderstandResponse`：`topic_labels: List[str]`、`question_kps: List[str]`（可选）

## 2. 视觉题目理解（core/tutoring/）

- [x] 2.1 复用 decide 看图路径：`HumanMessage([{text}, {image_url}]) → ChatOpenAI(ark)`，模型写死 `doubao-seed-2-0-mini-260428`，温度 0.3
- [x] 2.2 瘦 prompt：看图识别题型名（每行一个，限 1~5 个，不编号不解释）+ 顺带知识点；`topic_hint` 非空时注入「优先从参考词表选取」
- [x] 2.3 解析：去编号/bullet 拆行 → topic_labels；LLM 异常/空 → 空列表（不抛异常）

## 3. 端点（api/tutoring.py）

- [x] 3.1 `POST /api/tuturing/question-understand`（verify_internal_token），请求/响应 Pydantic 校验，返回 `{topicLabels, questionKps}`

## 4. 测试

- [x] 4.1 单测（mock LLM）：正常识别（多行拆解）/ 空返回 / topicHint 注入 / 异常兜底空列表
- [ ] 4.2 联调：Java 传 COS 图 → 识别题型 → 知识点清单；不传 topicHint 的漂移对比
  > 阻塞：跨仓库，需 Java 侧 `analyze-question/image` 接线 + 真实 COS 图。Python 侧端点/模型/prompt 已就绪，待 Java 联调。
