## Why

AI 答疑无学科门:decide 是数学专用提示词("你是数学答疑的决策器"),非数学题会被硬分类、硬引导,污染掌握度数据。后端决定加学科门 `tutoring-subject-gate`:在 decide **之前**由学科无关的分类器先判学科,非 math 直接跳过。Python 侧需要新增 `subject-classify` 端点支撑这个前置判定。

## What Changes

- **新增 stateless `POST /api/tutoring/subject-classify` 端点**:输入 `{content, image_url}`(至少一个非空),输出 `{subject}`(闭集 K12 九门 + other:`math`/`physics`/`chemistry`/`biology`/`chinese`/`english`/`politics`/`geography`/`history`/`other`;2026-08 按 K12 学科面扩为 10 值)
- **学科无关提示词**:只判学科不做解题;图片无法辨认/内容非学科 → `other`;拿不准是否数学 → 偏向 `math`(宁可漏拦不误拦)
- **文本 + 图片双通道**:无图纯文本 HumanMessage;有图多模态(复用 decide 看图路径,`HumanMessage([{text},{image_url}])`)
- **模型统一**:`doubao-seed-2-0-mini-260428` / temp 0.3(与 decide / question_understand 同款)
- **绝不抛异常**:失败/超时 → 空 subject(Java 按 math 放行,不阻断答疑)
- **复用 question_understand 慢修复**:显式关思考(`extra_body thinking disabled`)+ `request_timeout=20` + `max_retries=0`(doubao mini 开思考 50~145s,必须关)
- **不改前端契约**:subject-classify 仅 Java 内部桥调用,前端不感知

## Capabilities

### New Capabilities

- `tutoring-subject-classify`:AI 答疑学科分类端点。覆盖 subject-classify 端点契约(文本/图片双通道)、闭集 subject、模型统一、失败空结果语义。

### Modified Capabilities

- 无(tutoring 端点现有 change `ai-tutoring` 无 spec-level 行为变更,本期仅新增独立端点)

## Impact

- **新文件**:`core/tutoring/subject_classify.py`(核心分类逻辑,绝不抛异常)、`models/tutoring.py`(新增 `SubjectClassifyRequest` / `SubjectClassifyResponse`)
- **路由**:`api/tutoring.py` 注册 `/api/tutoring/subject-classify`(复用 `verify_internal_token`)
- **配置**:复用 `DOUBAO_API_KEY`;模型/温度/思考开关硬编码在 subject_classify.py(与 question_understand 同模式)
- **不改动**:decide / generate / question_understand / vector;gateway factory;前端契约
- **依赖**:无新增(复用 langchain-openai ChatOpenAI + doubao)
