# 语雀原文：流程控制会让agent 混乱

> 来源: 语雀 业务实施→AI答疑→方案设计→流程控制会让agent混乱 (doc 279945516, 5023字)
> COS路径: rag-source/ai-tutoring/语雀/语雀-流程控制会让agent混乱.md
> 核心结论: 状态 ≠ 内容；管"它能做什么"（工具集+护栏），不管"它怎么走"（顺序）。设计从状态机 7 → 会话生命周期 3。
> **最新逻辑判断（2026-08-24 对账）**：本文"受限 agent + 护栏、状态机 7→3"方向**与最终落地一致**；仅 4 处需按代码修正（换题≠开新会话 ｜ 换题判定权回 Java ｜ Python 是 L0 两端点非 LangGraph ｜ 多会话护栏未强制），已在下文标注，详见 `方案-代码对账.md`。
> summary: 论证答疑状态设计的核心原则"状态≠内容, 把题目从状态机里拿出去"——状态(7个固定模式: NEW/CLARIFYING/GUIDING/REVEALING/SUMMARIZING/ARCHIVED/TERMINATED)只答"会话在什么模式", 题目/步数/计数是数据字段不膨胀状态; 换题原设计=归档旧会话+开新会话(浏览器标签页模型)以保持状态机纯线性, 加 end_reason 字段区分完成/看过答案/放弃/轮次上限; 提出"管它能做什么(工具集+护栏), 不管它怎么走(顺序)"的受限 agent 思路, 状态机 7→3(会话生命周期 ACTIVE/ARCHIVED/TERMINATED + 护栏计数器 round_count/answer_request_count), Python 变封闭工具集 agent(evaluate_answer/next_hint/reveal_answer/switch_question…), Java 在工具执行点硬护栏(答案护栏≥2次/轮次护栏20轮/安全护栏/多会话); 测试策略改测护栏不测路径。⚠️最终代码落地: Python 非 LangGraph agent, MVP=L0 decide/generate 两端点+ActionMeta type闭集+Java TutoringGuardrailService 审批; 换题=计数重置事件会话保持 ACTIVE(非归档开新); 换题判定权回 Java(新图出现置 is_new_question→Python 短路 switch); 多会话护栏未强制(前端 localStorage 单 ACTIVE+reconcileSession 对账)

---

**Q: 如果开启了一个新的题目 学生又回到了原来的题目 这个时候需要控制流程状态吗 我想说的是流程状态控制的话 状态会不会太多**

**A: 好问题，你戳到了状态设计的要害。直接回答：不需要为"回旧题"新增任何状态——状态机保持 7 个不变。** 关键是把两样东西分开，这是防止状态爆炸的根本。

## 核心原则：状态 ≠ 内容，把"题目"从状态机里拿出去

```
状态（TutoringState）＝ 会话处于什么"模式"       数据（session 的字段）＝ 会话在做什么"内容"
─────────────────────────────              ─────────────────────────────
  7 个，固定，不随题目数量增长               · 当前题目（Q_A / Q_B / Q_C...）
  NEW / CLARIFYING / GUIDING                · current_step（第几步）
  REVEALING / SUMMARIZING                   · round_count、answer_request_count
  ARCHIVED / TERMINATED                     · 题目内容、题目类型...
```

状态的膨胀根源，是把"题目/步数"当成了状态。题目 A 第 3 步、题目 B 第 2 步、再切回题目 A 第 4 步——如果你把这些编进状态枚举，组合数就是灾难。但它们是数据字段，挂在会话实体上，随会话生死。状态机永远只回答一个问题："这个会话现在在什么模式"，跟它是哪道题、走到第几步无关。

## 你的场景逐帧跑一遍（证明状态数不变）

规则就一条：一个学生同一时刻只有一个活跃会话；换题 = 归档旧会话 + 开新会话。

```
Q_A 引导中         贴新题 Q_B         学生回 Q_A
──────────        ────────────       ──────────────

A: GUIDING ──NEW_QUESTION确认──▶ ARCHIVED(放弃)  （留档，不算完成不点亮）
B:                     GUIDING ──NEW_QUESTION确认──▶ ARCHIVED(放弃)
C(重开A):                                       GUIDING（全新会话，从第1步开始）
```

+ 状态出现过的：GUIDING、ARCHIVED——就这俩，反复用，永远 ≤7 个
+ 每个会话只服务一道题；题目切换不是"状态跳变"，是"结束一个会话 + 开始一个新会话"
+ 这就是浏览器标签页模型：同一时刻只有一个前台标签，关掉的标签是历史记录，不是状态

> ⚠️ **最新逻辑（2026-08 代码）**：「换题=归档旧会话+开新会话」已被推翻——最终落地 = **换题是计数重置事件，会话保持 ACTIVE**（旧题知识点不校正不点亮），学生怎么跳 agent 都能读全量 history 接住（`design-backend-ai-tutoring` 决策6 / `TutoringAppService`）。「浏览器标签页模型」是中间设计，非最终形态。

## 回旧题两种做法

| 做法 | 行为 | 复杂度 |
|------|------|--------|
| A（推荐） | 回旧题 = 开新会话重新引导；旧会话记录（含掌握度、错误、transcript）永久留档 | 状态机零改动，纯线性 |
| B | 断点恢复旧会话（ARCHIVED 可转回 GUIDING） | 需给 ARCHIVED 加 resume 转换，状态机出现回边 |

断点恢复（F6）的边界要收紧：只用于"同一个会话内暂时离开"（比如中途退出 app，Redis TTL 内回来续聊）；不用于换题后的回跳。这样就不需要"多会话栈"或"回边"，状态机保持纯线性。

> ⚠️ **最新逻辑（2026-08 代码）**：换题判定权**回 Java**——Java 检测新题图 URL 首次出现 → decide 请求带 `is_new_question=true` → Python **短路返回 switch（不调 LLM）** → Java 重置计数（`TutoringAppService.sendMessage`）。原因：Python 无状态，无法区分"本轮刚换题" vs "早几轮已换在答题"；由 Java 在"新图出现这一轮"置信号最可靠。

## 配套一个小改动（不是状态，是数据）

t_tutoring_session 加一个 end_reason 字段：

| end_reason | 含义 | 掌握度处理 |
|------------|------|-----------|
| COMPLETED | GUIDING 独立解出 | 提升到 75+ |
| ANSWER_REVEALED | 看过答案 | 不提升 |
| ABANDONED | 换题/放弃 | 不提升，留档 |
| ROUND_LIMIT | 20 轮到顶 | 不提升 |

这样"换题放弃"和"独立解出"在数据层就能区分，图谱点亮口径清晰，且不需要新增状态。

一句话总结：**状态不会爆炸，因为状态描述的是"会话模式"而不是"题目"；题目是数据，一次只有一个活跃会话。**

---

**Q: 我是不是理解错了agent，以前的项目逻辑大家都是流程控制，控制的是流程，agent 是有智能。如果我们通过状态来控制 agent 状态会混乱到爆炸，我们需要的是做受限 agent 限制 agent 的功能 而不是控制业务流程**

**A: 你没理解错——而且你刚刚的推理，恰好把我差点带偏的方案拉了回来。** 加 turn-router、处理换题、状态数据分离……这些都是在给一个本该是 agent 的对话硬套流程控制，每补一个分支状态就多一分爆炸风险。方向错了。

## 你的洞察一句话版本

> **管"它能做什么"（工具集 + 护栏），不管"它怎么走"（顺序）。**

传统项目和我的初版：控制流程（状态机规定每一步往哪走）。而对话天然是 agent 形的——学生想怎么聊就怎么聊。给 agent 套流程控制 = 枚举所有对话分支 = 爆炸。正确做法是：做一个能力受限的 agent（封闭工具集），通过工具执行点的硬护栏来约束它，而不是规定业务流程。

这就是"游戏规则"思维：不给玩家剧本，但定义规则——你能用哪些技能、血条多少（20 轮）、"看答案"这个技能要满足什么条件才能用（要过 2 次）。玩家（agent）在规则内自由发挥。

## 设计坍缩：状态机 7 → 3，流程控制彻底退出

```
原来的设计（流程控制）：                        新的设计（受限 agent）：
┌───────────────────────────┐              ┌───────────────────────────┐
│ 7 个状态：NEW/CLARIFYING/  │              │ 会话生命周期（3 个）:       │
│ GUIDING/REVEALING/        │              │   ACTIVE / ARCHIVED /     │
│ SUMMARIZING/ARCHIVED/     │              │   TERMINATED              │
│ TERMINATED                │              │ 护栏计数器（数据，非状态）:  │
│ turn-router 扩状态分支     │              │   round_count             │
│ 换题/回旧题分支            │              │   answer_request_count    │
└───────────────────────────┘              └───────────────────────────┘
        ↓ 变 ↓
Python 4 个端点：                          Python：答疑 Agent（LangGraph）
  intent/socratic/eval/extract              系统提示：苏格拉底教学法
  每次 Java 调一个                          Agent 在封闭工具集内自由决策顺序

Java 状态机 + 路由                           护栏：工具执行点硬检查（Java）
  ↑ 这是正在爆炸的东西                        ↑ 这才是"限制功能"
```

## Python 侧变成真正的 agent + 封闭工具集

```
┌──────────────────────────────────────┬───────────────────────────────────────────┐
│ 工具（封闭能力集，Agent 只能调这些） │    执行点硬护栏（Java，违规直接拒绝）     │
├──────────────────────────────────────┼───────────────────────────────────────────┤
│ evaluate_answer(回答)                │ 每次调用记 round_count；满 20 拒绝        │
│ next_hint()                          │ 生成一条引导，不含答案                    │
│ give_approach()                      │ 给思路；可（第 1 次求答案的出口）         │
│ reveal_answer()                      │ 硬检查 answer_request_count ≥ 2，否则拒绝 │
│ explain_concept(知识点)              │ 简短讲解后拉回当前题                      │
│ switch_question(新题)                │ 旧题归档（end_reason=ABANDONED），开新题  │
│ extract_and_summarize()              │ 会话收尾：提取知识点/薄弱点/总结          │
└──────────────────────────────────────┴───────────────────────────────────────────┘
```

学生说"这题不会"→ agent 自己决定问"请把题目发给我"（不需要 CLARIFYING 状态）；学生贴新题 → agent 自己决定调 switch_question（不需要换题分支）；学生说"答案给我" → agent 想调 reveal_answer，但护栏发现 count=0，工具直接拒绝，agent 只能退而求其次给思路。

> ⚠️ **最新逻辑（2026-08 代码）**：Python 侧**不是 LangGraph agent**——MVP = **L0 单次调用**：`decide`（出动作元数据 type 闭集：hint/approach/reveal/concept/switch/end）+ `generate`（流式正文）两端点，Java 在动作出口审批（`TutoringGuardrailService`）。工具集（evaluate/next_hint/reveal_answer/switch_question…）的落地形态 = **ActionMeta type 闭集 + Java 护栏**，非 agent 自由调工具。`switch_question` 落地 = switch 事件 + 计数重置（**不归档旧题、不开新会话**）。LangGraph 多步 agent 是阶段2（L1/L2，ActionMeta 契约已预留）。

## 护栏放 Java（确定性、可测）——这才是"控制"的正确位置

| 硬护栏 | 拦什么 |
|--------|--------|
| 答案护栏 | reveal_answer 需 answer_request_count ≥ 2 |
| 轮次护栏 | round_count ≥ 20，evaluate_answer/next_hint 拒绝 |
| 安全护栏 | 本地关键词 + 高危内容，Agent 根本不启动 |
| 掌握度/图谱 | 工具返回结果后，Java 落库掌握度、错误事件、图谱点亮（副作用） |
| 多会话护栏 | 一个学生一个活跃会话，开新即归档旧的 |

> ⚠️ **最新逻辑（2026-08 代码）**：「一个学生一个活跃会话，开新即归档旧」**未强制落地**——后端 `start()` 直接新建会话，不检查已有活跃会话；前端靠 localStorage 单 ACTIVE + 挂载对账（`reconcileSession`）管理单会话。此护栏为约束项/演进方向，非 Java 硬护栏。

测试策略也随之变化：不测 agent 的路径（非确定性），测护栏（确定性规则）——"count=0 调 reveal 必被拒""count=20 调 evaluate 必被拒"。这比测流程分支更简单、更稳。

## 三个诚实的代价（都能兜）

1. **成本**：agent 每轮可能 2-3 次工具调用（决策+执行）。兜法：每轮工具调用上限（如 ≤3 次）+ 20 轮会话上限。
2. **可测性**：agent 顺序不可预测。兜法：测护栏而非路径。
3. **"严禁答案"更稳了**：答案是一把 reveal_answer 工具，Java 在工具执行点硬拦——比写进 prompt 强得多。

## 这恰好就是你一直想要的 LangChain 业务

LangGraph agent + 工具集 + 护栏就是这个答案。Python 侧是一个有智能的答疑 agent（LangGraph 状态图），Java 侧是护栏层（确定性、可测、掌控业务硬规则）。自适应学习（让 agent 根据掌握度决定教什么）也顺势成为可能——只是给 agent 加两个工具（查薄弱点、出变式题），而不用改状态机。

这是一次架构方向级的调整。
