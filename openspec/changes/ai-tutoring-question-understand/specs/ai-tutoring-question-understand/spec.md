# ai-tutoring/question-understand 能力规格

无会话视觉题目理解：图片 → 题型名 + 顺带知识点，模型写死 doubao。Java 题型分析图片入口的 Python 通道。

## ADDED Requirements

### Requirement: 图片题目理解

`POST /api/tutoring/question-understand` SHALL 接收 COS 签名图片 URL（Java 上传后传），用写死的 doubao 视觉模型看图，返回 1~5 个题型名（及顺带的题目涉及知识点）。

#### Scenario: 正常识别
- **WHEN** 请求携带有效 `imageUrl`
- **THEN** 返回 `{ topicLabels: [1~5 个题型名], questionKps: [知识点...] }`，topicLabels 非空

#### Scenario: 识别失败降级
- **WHEN** 视觉调用失败 / 图片不可读 / 解析失败
- **THEN** 返回 `{ topicLabels: [] }`（HTTP 200，不报错），Java 据此降级 PENDING

#### Scenario: topicHint 命名收敛
- **WHEN** 请求携带 `topicHint`（题型库 top-N）
- **THEN** prompt 优先从 topicHint 选取题型名，命名朝题型库收敛，与 Java 文本识别对齐

#### Scenario: 无会话纯分析
- **WHEN** 任何调用
- **THEN** 端点无状态、不写任何观测（学生确认才走 vote）
