# 分析-03-防作弊机制

> summary: 讲解防作弊的三道护栏+兜底机制，全为Java规则
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 业务情况（三道护栏 + 兜底，全在 Java 确定性规则）
> 模块: ai-tutoring ｜ 节: 分析-03-防作弊机制
> COS路径: rag-slices/ai-tutoring/代码/分析-03-防作弊机制-业务情况三道护栏-兜底全在-Java-确定性规则.md
> 类别：开发难点

---

## 业务情况（三道护栏 + 兜底，全在 Java 确定性规则）

### 1. 答案护栏（核心：禁止直接要答案）
- 学生点「请求答案」→ Java 合成「请把答案给我」消息进 decide → Python 判 `type=reveal` → Java 看 `answer_request_count`：
  - **第 1 次**（count < 1）→ 护栏 DENY，`fallback=approach`（给思路，不给答案），并 `session.requestAnswer()` 计数 →1
  - **第 2 次**（count ≥ 1）→ 放行 reveal，给完整解答后**立即收尾** `end_reason=ANSWER_REVEALED`（防止答案反复要，api.md 契约）
- reveal 被拒后重决策仍 reveal → Java 直接降级**固定思路话术**（`FALLBACK_APPROACH_SPEECH`，不依赖 LLM），并 count→1。
- 前端配套：`answerRequestCount >= 1` 时「请求答案」弹**确认框**（单向门），避免学生误触。

### 2. 轮次护栏（防无限刷轮次）
- `round_count ≥ 20`（`TutoringConstants.SESSION_ROUND_LIMIT = 20`，领域硬上限）且本轮为引导类（hint/approach）→ 护栏 DENY，`fallback=end(ROUND_LIMIT)` → Java 强制收尾，固定话术「已达 20 轮上限」，无 generate。
- 只有 hint/approach 消耗轮次（`recordRound`）；concept/switch/end/reveal 不消耗。

### 3. 安全护栏（高危内容拦截）
- Python decide 输出 `safety_flag=true` → 护栏 DENY → Java 终止会话（TERMINATED），无 token 流，回复在 meta.reply。

### 4. 兜底护栏
- **结构化输出兜底**：Python 四段管线全失败 → 返回 `type=hint + degraded=true` → 护栏按普通 hint 放行 + 记日志（监控降级频次），不使用 503（不阻断答疑）。
- **非法/缺失 type** → 默认 HINT 放行（设计：不阻断）。

### 5. 设计原则（代码注释点明）
- 护栏是**动作出口的确定性规则引擎**：任何内容流入学生之前 type 已过护栏。
- 与「LLM 无自主决策权」呼应——`type=reveal` 只是 Python 的软意图，最终是否给答案由 Java 计数器说了算。

---
