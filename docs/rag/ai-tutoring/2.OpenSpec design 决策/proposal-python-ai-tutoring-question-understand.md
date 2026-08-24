# ai-tutoring-question-understand 变更提案

## Why

题型分析（前端 `kp-question-analysis`）需要「图片题目 → 识别题型 → 关联知识点」入口。Java 侧两条 LLM 通道现状：

- **通道 1 · 答疑看图**（SSE 会话内）：Python decide/generate → doubao 视觉模型看图，会话绑定，stateless 的 analyze 用不了。
- **通道 2 · LlmGateway**（`/api/llm/chat`）：`AiEduChatRequest` 纯文本（无 image 字段），给不了视觉。

缺口：**无「无会话的图 → 题型名」通道**。Java 上传 COS 后需要一个视觉题目理解调用。

## 决策：方案 B（与 Java 侧推荐一致）

Python 新增独立 **stateless 视觉端点** `POST /api/tutoring/question-understand`：
`{ imageUrl, topicHint?, grade? } → { topicLabels[], questionKps?[] }`。
模型写死 `doubao-seed-2-0-mini-260428`（supports_vision=True、allowed=True、看图答疑同款）。
Java 侧 `analyze-question/image`：multipart 上传 COS → 调本端点 → 复用 resolve 管线 → DTO 与文本版一致。

## What Changes (Python)

- 新增端点 `POST /api/tutoring/question-understand`（复用 decide 看图路径，无会话一请求一返回）。
- 新增请求/响应模型 `QuestionUnderstandRequest` / `QuestionUnderstandResponse`。
- 新增瘦 prompt：看图识别题型名（1~5 个）+ 顺带知识点；注入 `topicHint` 收敛命名。
- 模型写死 doubao，低温度，不做路由/白名单。

## Non-Goals

- **不改 `/api/llm/chat`**（方案 A 否决：通用网关契约膨胀 + 非视觉模型护栏，见 design D1）。
- 不做文本题目理解（文本侧由 Java `KpQuestionAnalyzer` 自研，D1 端口预留）。
- 不动 decide/generate 会话管线。
- 不写任何观测（与 analyze 纯分析一致；学生确认才走 vote）。

## Capabilities

### New Capabilities

- `ai-tutoring/question-understand`: 无会话视觉题目理解——图片 → 题型名 + 顺带知识点，模型写死 doubao，Java 题型分析图片入口的 Python 通道。

## Impact

- Python：新增端点 + 2 个模型 + 1 个 prompt + 测试。
- Java：`POST /api/kp/analyze-question/image` 上传 COS → 调 Python 端点 → 复用 resolve 管线（半天）；调用时传 `topicHint`（题型库 top-N）。
- 契约：语义对齐后端 `QuestionUnderstandingPort.understand`，可作其图片实现/可替换实现。
