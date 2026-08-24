# tutoring-subject-gate 技术设计

## Context

已确认的现状（代码验证）：

- **Java 编排**：安全预检 → 收题（文字/图片→COS）→ `TutoringSession.start(studentId,"math")` 建会话 → Python `decide`（数学提示词）→ Java 护栏 → Python `generate` → 透传。
- **decide 是数学专用提示词**（`prompts.py _DECIDE_SYSTEM`："你是数学答疑的决策器"）；对非数学题仅有一条口头规则（"非数学题说明只辅导数学并引导回来"→ type=concept），**无结构化 subject 输出**。
- **`subject_hint` 是死参数**：Java 恒传 `subject_hint="math"`，但 decide 提示词模板无 `{subject_hint}` 占位符——传了没用到。
- **模型现状**：decide（`settings.TUTORING_DECIDE_MODEL`）与 question_understand（`_UNDERSTAND_MODEL`）**均为 `doubao-seed-2-0-mini-260428`，temp 0.3**——三个统一模型现状已满足两个。
- **Python stateless 端点模式成熟**：understand / vector 均为独立小端点，不碰 MySQL/KG，Java 经桥调用。

## Goals / Non-Goals

**Goals:**
- **decide 之前**判定学科（因为不同学科需要不同提示词），学科无关分类器先于数学 decide。
- 非数学题：不建/不续会话、不落题目/掌握度/错误事件，返回「仅支持数学」。
- 学科分类器支持**文本和图片**。
- 三个 LLM 调用统一模型 `doubao-seed-2-0-mini-260428`（temp 0.3）。

**Non-Goals（本期明确不做）：**
- 多学科答疑提示词（本期只支持 math，架构预留 subject 决定提示词的选择点）。
- analyze-question 题型分析的学科过滤。
- subject-classify 的高准确率调优（本期分类器够用即可，误判治理见 Risks）。

## Decisions

### 1. 学科判定 = 独立 subject-classify 端点，在 decide 之前

**Why**：decide 是数学提示词，不能用来判物理题的学科（"用数学人设问物理题"）。学科必须由**学科无关**的小分类器先判，再按学科选提示词。本期只有 math，非 math 直接跳过。

```
拍题 / 换题（新题文字/图片）
  ↓
① Python subject-classify（学科无关提示词）→ subject
  ↓
② Java 分流：
   ├─ subject == math → 建/续会话(subject=math) → 数学 decide → 护栏 → generate
   └─ subject != math → 跳过：不建/不续、不记录，返回「仅支持数学」
```

**备选（否决）**：decide 内输出 subject → 学科决定提示词时需二次 decide（先数学判学科再换提示词重跑），浪费且逻辑绕；本设计一次分类、一次决定，干净。

### 2. subject-classify 端点契约（文本 + 图片）

```
POST /api/tutoring/subject-classify（Python stateless，Java 经桥调）
  请求：{ "content": string|null, "image_url": string|null }   // 至少一个非空
  响应：{ "subject": "math"|"physics"|"chemistry"|"biology"|"other" }
```

- **提示词学科无关**：只问"这道题属于哪个学科？"，不做任何学科解题；图片无法辨认 → `other`。
- **文本和图片都支持**：无图走纯文本 HumanMessage；有图走多模态（复用 decide 看图同路径，`HumanMessage([{text},{image_url}])`）。
- **模型统一**：`doubao-seed-2-0-mini-260428`，temp 0.3（与 decide/understand 同款）。
- **绝不抛异常**：失败 → 空结果 → Java 按 math 放行（宁可放过不漏拦，见 Risks）。

### 3. Java 分流（decide 之前）

- **拍题（建会话）**：先 subject-classify → math 才建会话；非 math 不建，返回「仅支持数学」提示（SSE 直接返回提示流，无会话行）。
- **换题（消息带新图）**：新图先 subject-classify → 非 math 跳过该新题（不结算旧题为该题、不记录新题），返回提示；math 正常走 is_new_question→switch 结算。
- **失败降级**：classify 异常/超时 → 按 math 放行（不阻断答疑；数据污染见 Risks 治理）。
- **会话记录真实 subject**：`TutoringSession.start(studentId, subject)` 传 classify 结果（不再无条件 "math"）。

### 4. 三个 LLM 调用统一模型（已确认）

| 端点 | 模型 | 现状 |
|------|------|------|
| decide | `doubao-seed-2-0-mini-260428` / 0.3 | 已是 |
| question_understand | `doubao-seed-2-0-mini-260428` / 0.3 | 已是 |
| **subject-classify（新）** | `doubao-seed-2-0-mini-260428` / 0.3 | 沿用 |

## Risks / Trade-offs

- [分类器误判：物理题被判成 math（漏拦）] → 最坏回到现状（数据污染）；治理：会话记录真实 subject，事后可按 subject 过滤清洗；分类器准确性后续可调优（本期够用）。
- [分类器误判：数学题被判成非 math（误拦）] → **致命，必须最小化**：① 分类器提示词偏保守（拿不准输出 math/other 不误拦）；② 失败降级按 math 放行。
- [分类器失败/超时] → 按 math 放行（不阻断答疑），宁可漏拦不误拦。
- [多一次调用成本] → 轻量分类（小模型、低 token、单次判断），比「decide 判错学科再污染」的代价低得多。

## Migration Plan

1. **Python**：新增 `subject-classify` 端点（文本+图片、同款模型、绝不抛异常）→ 交付。
2. **Java**：新增 subject-classify 契约 DTO + 桥；拍题/换题先判学科再分流；会话 subject 传真实值。
3. **联调**：物理题（文本/图片）→ 首轮「仅支持数学」；数学题全流程回归；classify 失败降级回归。
4. **回滚**：Java 分流是新增路径，删掉即回滚到「无条件建会话 + 数学 decide」；Python 端点可撤。

## Open Questions

- **subject 取值闭集**：math/physics/chemistry/biology/other 是否够（学科范围）？后续加学科时扩枚举即可。
- **分类器提示词措辞**：如何表达"拿不准就 other/不误拦"（误拦最小化）——Python 侧定稿。
