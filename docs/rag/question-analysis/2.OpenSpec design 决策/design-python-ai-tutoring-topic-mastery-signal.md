> summary: 掌握度信号题型化技术设计：①mastery_signals 语义从知识点翻转为题型（topic_label 输出鸡兔同笼/相遇问题/牛吃草，不输出知识点——否则污染后端题型库→掌握度/派生覆盖度/图谱点亮全脏）；②字段改名 kp_label→topic_label（Java 已 @JsonAlias 兼容旧名，关键防回归=structured.py _schema_instructions 纠错提示词必须同步改名，否则 schema 与纠错提示词脱节→Pydantic 校验失败→反复纠错→掉兜底→mastery_signals 静默丢失）；③mastery_snapshot 脱钩（题型与知识点快照不同源，保留字段 Java 契约不动降级背景参考，question_kps 仍参考快照）；④题型名稳定规范（prompt 约束+few-shot 锚定鸡兔同笼/相遇问题/牛吃草，后端只字面归一化全角半角/空白/去语气词不做同义词聚类，稳定性负担在 prompt 端）；⑤question_kps 与 signal 枚举不变（mastered/practicing/struggling→Java 映射 75/50/25）
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-source/question-analysis/OpenSpec设计决策/design-python-ai-tutoring-topic-mastery-signal.md
> 类别：数据关联

# 掌握度信号题型化 技术设计（RAG 结构化重构）

## 文档说明
> 本文件为原始 design 设计稿的 RAG 结构化重构版本。
> ⚠️重要：本文属于设计阶段素材，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度 0.8 的 canonical 真相源文档为准。本文件完整保留原始设计全部内容，不拆分到外部文档。

### 背景：掌握度信号需配合题型化翻转
> 状态：✅
> 检索摘要：decide 每轮输出 mastery_signals 的 kp_label 语义是知识点，但后端已把掌握度主体翻转为题型——若继续输出知识点名会被后端当题型落库，题型库混入知识点名致整条链路脏；Java 已用 @JsonAlias 兼容旧字段名，改名无跨仓库穿透风险。

- **现状**：`decide` 每轮输出 `mastery_signals`（`MasterySignalItem.kp_label` + `signal`），label 语义为「知识点」，接地到 `mastery_snapshot`（旧 `t_student_kp_mastery` 的知识点 label 候选）。后端 `kp-matching-lightup` 已决定把掌握度主体从知识点翻转为题型，`mastery_signals` 需配合输出题型。
- **链路**：`decide → mastery_signals[].kp_label → Java resolve → 掌握度落库 → 图谱点亮`。当前若继续输出知识点名，后端会把它当题型落进题型掌握度表 → 题型库混入知识点名 → 整条链路脏。
- **关键约束**：后端 Java 已用 `@JsonAlias("topic_label")` 兼容旧字段名；前端读的是 Java 透传的 `kpLabel`（camelCase），与 Python 字段名无关 → 改名无跨仓库穿透风险。

### 目标与非目标
> 状态：✅
> 检索摘要：目标=mastery_signals 稳定输出题型 label 不输出知识点、字段名 kp_label→topic_label、题型名稳定规范、mastery_snapshot 脱钩；非目标=改 type/eval/safety_flag/降级管线/generate、改 signal 枚举、改 question_kps、做 student_grade/LLM 消歧/离线聚合/同义词聚类。

**Goals:**
- `mastery_signals` 稳定输出**题型** label，不输出知识点。
- 字段名 `kp_label` → `topic_label`（语义清晰，Java 已兼容）。
- 题型名稳定规范（同一题型一致命名）。
- `mastery_snapshot` 脱钩（题型无法从知识点快照接地）。

**Non-Goals:**
- 不改 `type` 判定、`eval`、`safety_flag`、降级管线骨架、`generate`。
- 不改 `signal` 枚举（mastered/practicing/struggling）。
- 不改 `question_kps`（继续输出知识点）。
- 不做 student_grade（后端组织系统自查）、LLM 消歧、离线聚合（后端调 llm-gateway）。
- 不做同义词聚类（后端只做字面归一化）。

### 决策 1：掌握度信号语义翻转（题型为主体，必改）
> 状态：✅
> 检索摘要：mastery_signals[].topic_label 输出题型（鸡兔同笼/相遇问题/牛吃草）不输出知识点（二元一次方程组/假设法）；学生掌握的是题型不是知识点，知识点掌握度由后端「题型掌握度×题型→知识点映射」派生；否则 Python 输出知识点名会污染后端题型库。

`mastery_signals[].topic_label` 输出**题型**（「鸡兔同笼」「相遇问题」「牛吃草」），**不输出**知识点（「二元一次方程组」「假设法」）。

理由：学生掌握的是题型，不是知识点。知识点掌握度由后端「题型掌握度 × 题型→知识点映射」派生。若 Python 仍输出知识点名，会污染后端题型库 → 掌握度/派生覆盖度/图谱点亮全脏。

### 决策 2：字段改名 kp_label → topic_label（加分项）
> 状态：✅
> 检索摘要：MasterySignalItem.kp_label→topic_label，description 语义改「题型」，Java 已 @JsonAlias("topic_label") 兼容旧名改名无穿透风险；关键防回归=structured.py 的 _schema_instructions 纠错提示词硬编码 "kp_label" 必须同步改，否则 schema 与纠错提示词脱节致掌握度静默丢失。

`MasterySignalItem.kp_label` → `topic_label`，description 语义改「题型」。Java 已 `@JsonAlias("topic_label")` 兼容旧名，改名无穿透风险。

**关键防回归**：`structured.py` 的 `_schema_instructions` 纠错提示词硬编码了 `"kp_label"`，必须同步改为 `"topic_label"`。否则 function calling schema（绑定 Pydantic 模型，自动变 topic_label）与纠错提示词字段名脱节 → 模型输出旧名 → Pydantic 校验 `topic_label` 缺失 → 反复纠错失败 → 掉进兜底 fallback → mastery_signals 静默丢失。

### 决策 3：mastery_snapshot 脱钩
> 状态：✅
> 检索摘要：mastery_signals 不再「优先复用快照候选」——题型与知识点快照不同源，快照（旧 t_student_kp_mastery 知识点 label）无法为题型提供候选；mastery_snapshot 保留在 DecideRequest（Java 契约不动字段默认空），prompt 中降级为背景参考或不提，question_kps 仍可参考快照。

`mastery_signals` 不再「优先复用快照候选」。理由：题型与知识点快照不同源，快照（旧 `t_student_kp_mastery` 知识点 label）无法为题型提供候选。`mastery_snapshot` 保留在 `DecideRequest` 里（Java 契约不动、字段默认空），prompt 中降级为背景参考或不提；`question_kps` 仍可参考快照（继续知识点）。

### 决策 4：题型名稳定规范
> 状态：✅
> 检索摘要：prompt 加约束——同一题型用最常见/最短/规范名不随意换说法，用 few-shot 锚定常见题型（鸡兔同笼/相遇问题/牛吃草）；Java 只做字面归一化（全角半角/空白/去末尾语气词）不做同义词聚类，「鸡兔同笼」vs「鸡兔同笼问题」会被当两个题型，稳定性负担在 prompt 端。

prompt 加约束：同一题型用**最常见、最短、规范的题型名**，不随意换说法；用 few-shot 锚定常见题型（鸡兔同笼/相遇问题/牛吃草）。理由：Java 只做字面归一化（全角半角/空白/去末尾语气词），不做同义词聚类，「鸡兔同笼」vs「鸡兔同笼问题」会被当两个题型 → 稳定性负担在 prompt 端。

### 决策 5：question_kps 与 signal 不变
> 状态：✅
> 检索摘要：question_kps 继续输出知识点（读题列知识点，前端知识点分析数据源）；signal 枚举不变（mastered/practicing/struggling，Java 映射 75/50/25）。

`question_kps` 继续输出知识点（读题列知识点，前端知识点分析数据源）；`signal` 枚举不变（mastered/practicing/struggling，Java 映射 75/50/25）。

### 风险与权衡
> 状态：✅
> 检索摘要：风险覆盖题型名稳定仅靠 prompt（few-shot 锚定+最常见最短约束+后端字面归一化兜底）、改名漏改纠错提示词致掌握度静默丢失（tasks 显式列出+测试断言纠错提示词含 topic_label）、mastery_snapshot 脱钩后题型名无候选接地（few-shot+规范约束，后续题型库聚合回填先验）、历史数据口径变化（后端并行过渡旧表保留）。

- [题型名稳定仅靠 prompt 约束] → LLM 天生爱换说法，纯一句「别换说法」不够。缓解：few-shot 锚定 + 「最常见最短命名」约束 + 后端字面归一化兜底（不完美，但本期不做同义词聚类）。
- [改名漏改纠错提示词 → 掌握度静默丢失] → `_schema_instructions` 与模型字段名脱节。缓解：tasks 3.1 显式列出，测试断言纠错提示词含 topic_label。
- [mastery_snapshot 脱钩后题型名无候选接地] → 题型名由模型自由生成，冷启动无约束。缓解：few-shot + 规范约束；后续题型库聚合后可由后端回填先验（不在本期）。
- [历史数据口径变化] → 旧数据知识点粒度、新数据题型粒度。缓解：后端并行过渡（旧表保留），Python 无需处理。
