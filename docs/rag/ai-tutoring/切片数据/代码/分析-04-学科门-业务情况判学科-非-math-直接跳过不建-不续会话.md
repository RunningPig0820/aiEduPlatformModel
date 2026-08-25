# 分析-04-学科门

> summary: 讲解学科门的业务情况，非数学题直接跳过不建会话
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 业务情况（判学科 → 非 math 直接跳过，不建/不续会话）
> 模块: ai-tutoring ｜ 节: 分析-04-学科门

---

## 业务情况（判学科 → 非 math 直接跳过，不建/不续会话）

### 1. Python 侧：学科无关小分类器（decide 之前）
- 独立 stateless 端点 `POST /api/tutoring/subject-classify`，同步 JSON（非 SSE）。
- **K12 十值闭集**：`math / physics / chemistry / biology / chinese / english / politics / geography / history / other`（本期 Java 只放行 math，其余跳过）。
- **学科无关提示词**：只判学科不做解题；判定规则「**宁可放过，不可把数学题误判成别的学科**」——拿不准 math 与其他学科之间犹豫 → 输出 math。
- 模型写死 doubao `doubao-seed-2-0-mini-260428`，温度 0.3，**关思考 + 20s 超时 + 关 SDK 重试**（学科门不能成为新卡点，复用 question_understand 慢修复）。
- **绝不抛异常**：失败/超时/闭集外 → 返回 `subject=null`，Java 按 math 放行（宁可漏拦不误拦）。
- 文本（纯文本）/图片（text + image_url 多模态）双通道。

### 2. Java 侧：两个触发点，只在「新题进入」判学科
- **发起（start）**：首条消息判学科。图片题先上传到 `subject-check` 目录拿 URL 供分类器看图；非 math → 返回「仅支持数学」提示流，**不建会话、不落库**。
- **换题（sendMessage）**：仅「新图首次出现」（is_new_question）判学科；非 math → **不追加消息、不结算旧题、不记录**，原会话不受影响、**不消耗轮次**。判学科只在该轮做（非每轮）。
- `classifySafely`：端口未装配/调用异常 → null 视为失败 → 按 math 放行（绝不阻断答疑主链路）。
- 非 math 的回复流（`subjectHintStream`）：`meta(sessionId=null|原会话, status=ACTIVE, type=hint) → token「目前仅支持数学答疑」→ done`，不建/不续会话。

### 3. 学科记录
- 会话的 `subject` 字段记录分类结果（math 或其它），供会话记录真实学科 + 后续分学科答疑扩展。

---
