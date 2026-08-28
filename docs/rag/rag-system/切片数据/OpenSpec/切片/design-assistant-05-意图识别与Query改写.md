# 意图识别与 Query 改写（intent / rewrite / clarify / history）

> summary: 意图识别与Query改写 — intent LLM结构化+规则兜底、rewrite 改写、clarify 澄清轮、history 上下文
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-05-意图识别与Query改写.md
> 类别：架构设计


### 复用 vs 新增映射（intent / rewrite / clarify）

> 检索摘要：intent 结构化、rewrite 改写、clarify 澄清轮哪些复用现有代码、哪些是新增函数？

- **intent 结构化**：Python 落点 `core/rag/query.py` classify 扩展；复用 `_fallback_anchor` / `ANCHOR_RULES` / `CATEGORY_SECTIONS` / `_llm_category`(LLM 分类)；新增 schema 加 `candidates` / `switch_detected` / `ambiguous`，重写改写。
- **rewrite**：新函数；新增 `rewrite_query(question, anchor, history)`。
- **clarify**：新逻辑；复用 intent 的 ambiguous/candidates；澄清轮状态机（0 token、最多一轮）。

### 沟通结论锁定（C4 clarify 候选 + 点选交互定稿）

> 检索摘要：08-25 锁定 clarify 候选来源与点选交互——候选=LLM candidates+会话锚点兜底、≥2 才澄清、点选后重发原问+current_project、intent 必须信任 current_project 权威信号？

- **C4 clarify 候选**：候选 = intent LLM `candidates`（主源）+ 会话历史锚点（兜底）→ 去重 → ≥2 才 clarify；default = current_project > 会话最后锚定。触发后最多一轮，仍模糊直接默认。
- **C4 点选交互定稿（2026-08-25，前端校准）**：clarify 后前端点选候选 → **重发原问 + `current_project=点选模块`**（非裸功能名）；intent 收到"原问 + current_project"时**以 `current_project` 为权威消歧锚点直接锚定**，**不因问题本身含糊再拉 ambiguous**（intent 实现必须信任该权威信号）；点选模块与会话锚点不同 → `switch` 照常触发。

### D-A2. history 上下文（联调审查 ①⑦ 定死）

> 检索摘要：intent 和 rewrite 的 history 上下文怎么传——默认几轮、Java 组装 Python 只截断？

- `intent(question, history)` / `rewrite_query(question, anchor, history)`：history 为最近 N 轮 `{question, answer, anchor}` 列表（**默认 3，含 clarify 轮**）。
- **显式截断**：取 `history[-N:]`（最近 N 轮），后端 resilience spec 的上下文窗口。history 由 Java 网关组装传入，Python 只消费+截断。

### 白盒链路（intent / clarify / switch / rewrite 段）

> 检索摘要：白盒链路开头 intent→(clarify|switch)→rewrite 的事件产出顺序？

```
 → intent(LLM结构化) → 失败回退关键词(degraded)
     ├─ ambiguous & candidates≥2 → event: clarify(0 token, 不计轮次)
     ├─ switch_detected → event: switch + 重置上下文
 → rewrite → event: rewrite{original, rewritten}
```
