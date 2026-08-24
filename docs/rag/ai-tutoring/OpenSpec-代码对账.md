# OpenSpec-代码对账（22 份逐份差异明细）

> **任务**：1.3c 对齐 `2.OpenSpec design 决策/` 22 文件（11 变更 × design/proposal），逐份对照代码，标注 `✅一致 / ⚠️有改动点`。
> **真值源**：`3.代码/` 10 份业务分析 + `git/坑档案.md` + 三端代码（`文件:行号` 见各分析）。
> **用途**：1.4 完善文档的"怎么设计（方案）→ 落地真相（代码）"口径来源；旧口径降级"演进故事"，不进 RAG 正文切片。
> **日期**：2026-08-24
> **重要度**：A 级 7 变更（逐决策对齐）｜B 级 4 变更（抽查关键决策）

---

## 一、对账总览（22 份一行状态）

| # | 文件 | 端 | 分级 | 状态 | 一句话差异 |
|---|---|---|---|---|---|
| 1 | design-backend-ai-tutoring | backend | A | ⚠️ **4 处** | 决策8/9 掌握度翻转｜决策11 表变｜决策15 OCR 双通道 |
| 2 | proposal-backend-ai-tutoring | backend | A | ⚠️ | 目标含"掌握度按 URI/单调不减"→ 已翻转 |
| 3 | design-python-ai-tutoring | python | A | ⚠️ **3 处** | 决策6 模型切 doubao｜决策11 OCR 降兼容｜决策14 模型 ID |
| 4 | proposal-python-ai-tutoring | python | A | ⚠️ | 同 design：OCR 前置/模型配对过时 |
| 5 | design-python-2026-08-12-tutoring-agent-protocol | python | A | ⚠️ **1 处** | 决策8"不关思考"→ 实际 decide 关思考 |
| 6 | proposal-python-2026-08-12-tutoring-agent-protocol | python | A | ⚠️ | 同 design 决策8 |
| 7 | design-backend-add-tutoring-session-history-backend | backend | A | ⚠️ **1 处** | D5"getSession 不改"→ 实际改后端代理读 COS |
| 8 | proposal-backend-add-tutoring-session-history-backend | backend | A | ✅ | 目标全落地（软删/标题/meta 复原） |
| 9 | design-backend-tutoring-subject-gate | backend | A | ⚠️ **1 处** | 决策2 闭集 5 值→K12 十值 |
| 10 | proposal-backend-tutoring-subject-gate | backend | A | ⚠️ | 同 design 闭集扩展 |
| 11 | design-python-tutoring-subject-gate-python | python | A | ⚠️ **1 处** | 决策2 SubjectType 5→10 值（K12） |
| 12 | proposal-python-tutoring-subject-gate-python | python | A | ⚠️ | 同 design 闭集扩展 |
| 13 | design-python-ai-tutoring-question-understand | python | A | ✅ | 5 决策全落地（topic_hint/模型 mini） |
| 14 | proposal-python-ai-tutoring-question-understand | python | A | ✅ | 目标全落地 |
| 15 | design-backend-tutoring-agent-events | backend | B | ✅ | 7 决策 + D7 演进全落地 |
| 16 | proposal-backend-tutoring-agent-events | backend | B | ✅ | 目标全落地 |
| 17 | design-backend-tutoring-agent-workflow-backend | backend | B | ✅ | 5 决策 + 契约冻结全落地 |
| 18 | proposal-backend-tutoring-agent-workflow-backend | backend | B | ✅ | 目标全落地 |
| 19 | design-python-ai-tutoring-decide-guide-not-end | python | B | ⚠️ **1 处** | D4 end 三类 vs 代码四类（Java 兜底保留） |
| 20 | proposal-python-ai-tutoring-decide-guide-not-end | python | B | ⚠️ | 同 design D4 |
| 21 | design-frontend-add-ai-tutoring-frontend | frontend | B | ⚠️ **2 处** | 决策5 OCR 双通道｜决策9 chips 数据源修复 |
| 22 | proposal-frontend-add-ai-tutoring-frontend | frontend | B | ⚠️ | 同 design 决策5/9 |

**汇总**：`✅一致 9 份`｜`⚠️有改动点 13 份`。核心改动集中在 **掌握度主体翻转**、**OCR 双通道**、**模型统一 doubao**、**学科闭集扩 K12** 四处。

---

## 二、差异明细（按变更分组）

### 变更 A1：ai-tutoring（backend）—— 主方案，⚠️ 4 处核心差异

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **8. 知识点 key = TextbookKP URI** | 掌握度 `t_student_kp_mastery.kp_key` 存 URI，label→URI 解析（`TutoringKpResolver`） | **翻转**：掌握度主体改为**题型**，`t_student_topic_mastery.topic_key`=题型名（canonical），URI 解析桥移到 ADMIN 维护接口；`t_student_kp_mastery` 表已删（V22 DROP） | "掌握度按题型记，不按知识点 URI"（演进故事：早期设计按 URI） |
| **9. 掌握度规则** | mastered→75/practicing→50/struggling→25，**max 单调不减**，收尾 COMPLETED 提升 75+ | **翻转**：`ScoreMapper` 累计平均（直接答对 1.0/引导后 0.5/答错 0.0 × per-题型打折 0.7/0.8/1.0）；不再单调不减 | "每题打分 → 题型累计平均正确率"（演进故事：曾设计单调不减） |
| **11. 存储三层** | `t_tutoring_session + t_student_kp_mastery + t_tutoring_error_event`，不建消息表 | 增加 **`t_student_question_record`（题目表，事实源）**；`t_student_kp_mastery`→`t_student_topic_mastery`；Redis/COS 不变 | "题目表 + 掌握表 + 会话表 + 错误事件表" |
| **15. 图像优先（反转 OCR）** | 不做传统 OCR，视觉模型直接看图；OCR 保留 `ocr.enabled` 开关作降级 | **一致 + 深化**：直传 COS→doubao 看图为主通道 ✅；OCR `ocr.enabled` 控制前端入口显隐 ✅；新增换题信号（新图 URL 首次出现→is_new_question→短路 switch） | "图像优先直看 + OCR 兼容双通道" |

**其余一致**：决策1 微服务分工、2 decide→guard→generate、3 动作契约（mastery_signals 字段改 `topic_label`）、4 护栏规则、5 答案出口、6 换题（判定权演进见决策11/15，决策6 旧表述"判定在 Python"→实际 Java 检测新图）、7 会话 3 态+计数器、10 独立枚举、12 认证桥接、13 类型先行流式（decide 后也流式化）、14 L0、16 情绪 F7。

---

### 变更 A2：ai-tutoring（python）—— ⚠️ 3 处核心差异

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **6. 模型配对** | 测试 deepseek-v4-flash，生产 decide=flash/turbo、generate=qwen-math-turbo | **统一**：全链路 doubao `doubao-seed-2-0-mini-260428`（decide/generate/understand/classify 同款），温度 decide 0.3/generate 0.7 | "全链路统一 doubao 全模态模型" |
| **11. OCR 前置** | OCR 识别→确认→首条消息（主入口） | OCR 降为**兼容/降级通道**（`ocr.enabled` 开关）；主通道=图片直传 COS→多模态看图 | "图像优先，OCR 兜底" |
| **14. 图像优先模型** | 切 doubao-seed-2-0-lite | spike 后统一 **mini-260428**（与 decide 同款）；换题短路已实现（`is_new_question`→switch 不调 LLM） | "统一 mini 模型；换题由 Java 信号短路" |

**其余一致**：决策1 分工、2 交互（decide 流式化见 protocol 变更）、3 动作契约、4 审批归 Java、5 结构化四段降级（bind_tools 实测）、7 schema 可拆、8 emotion F7、9 mastery 接地（label→题型名）、10 无状态+压缩、12 L0→LangGraph、13 零题目状态。

---

### 变更 A3：tutoring-agent-protocol（python）—— ⚠️ 1 处核心差异

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **8. 保留思考模式** | 产品拍板"**不关思考**，把真实推理流式展示"（decide+generate 都开） | **分化**：decide **关思考**（意图秒出，实测 1.2s vs 开思考 50-145s）、generate **开思考**（thinking 作 AI 版进度条）——分层思考开关 | "decide 关思考秒出 + generate 开思考展示，分层策略"（演进故事：曾拍板全开思考） |

**其余一致**：决策1 decide 非流式→SSE 流式、2 agent 事件协议（8 阶段表）、3 Java 发 guardrail/memory（memory Python 不发占位）、4 tool 预留、5 level master/sub、6 空流兜底、7 Java 对接细节、9 ChatTurn extra=ignore。

---

### 变更 A4：add-tutoring-session-history-backend —— ⚠️ 1 处

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **D5. getSession 不改** | 详情内容前端经签名 `transcriptUrl` 拉 COS | **改了**：transcript 改**后端代理**（`GET /sessions/{id}/transcript`），前端零 COS 直连（无签名 URL 泄露/CORS）；`getSession` 返回 recentMessages（最多 50 条） | "transcript 由后端代理读 COS，前端不直连" |

**其余一致**：D1 不建消息表（COS 事实源）、D2 消息 meta 7 字段（type/denied/decide_reason/round/question_kps/eval/status 全落地）、D3 title 列（首条用户消息前 30 字）、D4 列表/删除（软删+COS 保留，全落地）。

---

### 变更 A5+A6：tutoring-subject-gate（backend + python）—— ⚠️ 各 1 处

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **后端决策2 / Python决策2：subject 闭集** | `math/physics/chemistry/biology/other`（5 值） | **扩 K12 十值**：+`chinese/english/politics/geography/history`（Java 只放行 math） | "K12 十值闭集，本期只放行数学"（演进故事：曾设计 5 值） |

**其余一致**：独立 stateless 端点、decide 之前、文本+图片双通道、失败→空 subject 按 math 放行（宁可漏拦不误拦）、模型统一 doubao mini、关思考+20s 超时+关重试（照搬 question_understand 慢修复）、拍题/换题两触发点、会话记录真实 subject。

---

### 变更 A7：ai-tutoring-question-understand —— ✅ 一致

5 决策全落地：D1 独立 stateless 视觉端点（否决通用 chat 加图）、D2 契约（topicLabels/questionKps，snake_case）、D3 实现=decide 看图 stateless 化（模型 mini-260428）、D4 命名收敛（topic_hint 词表注入）、D5 降级 PENDING（空 topic_labels 不报错）。

---

### 变更 B1：tutoring-agent-events（backend）—— ✅ 一致

D1 decide 消费 SSE（演进 D7 响应式中继 thinking）、D2 guardrail 注入（护栏后 generate 前）、D3 memory 注入（流尾收尾信号）、D4 generate 中继 agent、D5 重试/超时语义、D6 事件格式（level/stage/label/status/detail）、D7 decide thinking 响应式中继全落地；Open Question"decide agent 事件是否中继"→ 已答复**要**（workflow 变更实现）。

---

### 变更 B2：tutoring-agent-workflow-backend —— ✅ 一致

D1 decide filter thinking+agent（`orchestrate` filter 两条件）、D2 `decideReason` 字段（reason 保护栏语义）、D3 `SseMasterySignalDTO` camelCase（修复 meta.eval.masterySignals 恒空）、D4 questionKps、D5 契约文档全落地；阶段二契约冻结（前端零后端改动）。

---

### 变更 B3：ai-tutoring-decide-guide-not-end —— ⚠️ 1 处

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **D4. end 收紧三类** | COMPLETED/ABANDONED/safety 三类 | **代码四类**：`COMPLETED/ANSWER_REVEALED/ABANDONED/ROUND_LIMIT`（Java 护栏兜底的 ANSWER_REVEALED/ROUND_LIMIT 属护栏路径，Python 不主动输出） | "Python 只出三类，Java 护栏兜底两类" |

**其余一致**：D1 两分法 prompt（在答题→引导/不在→concept）、D2 判定顺序（写死优先级）、D3 hint vs approach（先想一步）、D5 reveal 门禁（仅明确要答案）、D6 end 规约收紧（不给完整解答）、D7 测试策略。注意：**无关内容是否走 Java terminate**——design Open Question 答"否，改 concept"；代码 Python 两分法已让它输出 concept，但 Java `isTerminationEnd`（type=end 且无 end_reason→terminate）仍保留兜底。

---

### 变更 B4：add-ai-tutoring-frontend —— ⚠️ 2 处

| 决策 | 方案写了什么 | 代码实际怎样 | 完善文档怎么写 |
|---|---|---|---|
| **5. OCR 前置** | 拍照 OCR 识别→确认→进答疑（📷 按钮常驻） | **双通道**：OCR 保留 + **图片直传/粘贴/拖拽直接进答疑**（多模态看图，OCR 降兜底，`ocr.enabled` 开关显隐） | "图片直传为主 + OCR 确认兜底" |
| **9. 知识点 chips 数据源** | `meta.eval.masterySignals` | **修复**：改读 `meta.masterySignals`（`meta.eval.masterySignals` 恒 undefined 的缺口） | "chips 读 meta.masterySignals" |

**其余一致**：1 页面形态、2 独立 SSE 客户端（fetch readSSE，不复用 llm.js）、3 前端会话状态机（noSession/active/ended + phase SENDING/STREAMING/IDLE）、4 类型徽标（denied 降级渲染）、6 请求答案（第 2 次弹确认）+轮次+结束、7 错误映射（50002-50006）、8 断点恢复（localStorage+对账）、10 收尾总结卡片、11 组件结构。

---

## 三、对账结论（1.4 合成要点）

**4 个贯穿性差异，是面试官追问的必答题**：
1. **掌握度主体 = 题型（canonical→ScoreMapper 累计平均），不是知识点 URI/单调不减** —— 最大翻转
2. **OCR = 兼容双通道，主通道是图片直传 COS→多模态 doubao 看图**
3. **模型全链路统一 doubao-seed-2-0-mini**（不按 decide/generate 分模型）
4. **学科闭集 K12 十值**（本期只放行 math）

**演进故事（旧方案口径，降级表述保留）**：知识点 URI 掌握度｜单调不减｜OCR 主入口｜MongoDB 存储｜状态机 7 态｜LangGraph agent 编排——均为过程产物，最终形态以代码为准。
