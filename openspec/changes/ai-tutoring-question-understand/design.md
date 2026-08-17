# ai-tutoring-question-understand 技术设计

## Context

- 题型分析前端需要图片入口；Java 通道 2（LlmGateway `/api/llm/chat`）纯文本。
- Python decide 已有看图能力（看图答疑，design 决策 14）：`ChatOpenAI(ark)` + `HumanMessage` image_url content blocks + doubao-seed-2-0-mini-260428（全模态），生产已验证。
- 现状代码事实：
  - `models/chat.py ChatRequest.message: str` —— 纯文本，无 image 字段，无结构化内容。
  - `/api/llm/chat` 被 page_assistant/faq/homework_grading/content_generation 等场景共用（生产共享网关）。
  - `config/model_config.py` 有 `supports_vision` 标记，但 zhipu glm-4.6v `allowed: False`（不对外）；doubao-seed-2-0-mini-260428 `allowed: True + supports_vision: True`。

## 决策：方案 A vs B

### D1. 选 B（独立 stateless 视觉端点），否决 A（通用 chat 加图）

理由（代码级）：

1. **A 要改生产共享网关**：`/api/llm/chat` 被 4+ 场景共用，加 image 支持 = 契约膨胀 + 新增「非视觉模型收到图 → 400 降级」护栏逻辑，回归风险波及无关功能。
2. **A 的视觉模型池实际只有一个**：可对外视觉模型只有 doubao（allowed+vision）；glm-4.6v `allowed=False`。通用 chat 加图 = 给一个模型造通用接口，不划算。
3. **B 复用已验证路径**：decide 看图（`HumanMessage image_url → ChatOpenAI(ark)`）生产已跑通，新端点只是把这条路径 stateless 化 + 瘦 prompt，零新风险。
4. **B 模型写死 → 非视觉模型风险天然隔离**：不靠「按 model 路由 + 护栏」，靠构造上不可能（端点只用 doubao）。

### D2. 端点契约

`POST /api/tutoring/question-understand`（Java 内部，x-internal-token）：

**请求**
```json
{
  "imageUrl": "https://cos-sign-...",   // 必填，COS 签名 URL（Java 上传后传）
  "topicHint": ["鸡兔同笼", "相遇问题", "牛吃草", ...],  // 可选，Java 传题型库 top-N，收敛命名
  "grade": 6                             // 可选，年级锚（本期不强用）
}
```

**响应**
```json
{
  "topicLabels": ["鸡兔同笼"],           // 1~5 个，空数组 = 识别失败（Java 降级 PENDING）
  "questionKps": ["二元一次方程组"]       // 可选，顺带识别知识点
}
```

对齐：语义 = 后端 `QuestionUnderstandingPort.understand(questionText, grade)` 的图片形态；空 `topicLabels` ↔ understand 返回空列表 → Java 降级 PENDING，与文本路径一致。

### D3. 实现 = decide 看图路径 stateless 化

- 模型写死 `doubao-seed-2-0-mini-260428`（settings 已有，TUTORING_DECIDE_MODEL 同款）。⚠️ Java 消息写的 "doubao-seed-2-0-lite" 需与方舟控制台实际开通 ID 对齐，Python 侧以 mini-260428 为准。
- 温度 0.3（与 decide 一致，判断要稳）。
- 构造 `HumanMessage(content=[{"type":"text"},{"type":"image_url","url":imageUrl}])`，调 `ChatOpenAI(ark)` —— 与 decide 看图完全同一路径。
- 解析：纯文本返回 → 去编号/bullet 拆行 → 1~5 个；或复用 structured 降级（可选）。LLM 异常/空 → `{topicLabels: []}`。

### D4. 命名收敛（topicHint 注入）—— 词汇桥关键机制

Java 侧调用时把 `findTopTopicLabels(20)`（题型库 top-N，Java 数据库）放 `topicHint` 传入；prompt 写「优先从参考词表选取题型名，词汇不足可自拟」。让 Python 图片识别命名朝题型库收敛，与 Java 文本识别（KpQuestionAnalyzer，D1 词表注入）对齐 —— 同一 resolve 管线合并，别名合并兜底。这是两端题目理解词汇一致性的唯一机制，**必须让 Java 配合传 topicHint**。

### D5. 降级与纯分析

- 视觉调用失败 / 解析失败 → `{topicLabels: []}` → Java 降级 PENDING（带 candidates 或空态），不报错。
- 端点无状态、不写 obs（与 analyze 纯分析一致；学生确认才走 vote）。

## Risks / Trade-offs

- [视觉识别不稳定] → 空 topicLabels 降级 PENDING；前端有 OCR 兜底按钮（图片 → OCR → 文本 analyze）。
- [词汇漂移（图片识别 vs 文本识别）] → topicHint 注入收敛 + 别名合并兜底；不传 topicHint 则漂移。
- [延迟] → 一次 LLM 调用（关思考 ~1.2s），Java 同步等，前端 loading。
- [模型 ID 不一致] → Java "lite" vs Python "mini-260428"，联调前必须对齐方舟实际开通 ID。

## Migration Plan

1. Python：模型 + 端点 + prompt + 单测（mock LLM）。
2. Java：`/api/kp/analyze-question/image` 上传 → 调端点 → resolve 管线；传 topicHint。
3. 联调：图片贴题 → 识别题型 → 知识点清单；OCR 兜底。
4. 回滚：关 Python 端点或 Java 侧切回 OCR 文本路径即可。
