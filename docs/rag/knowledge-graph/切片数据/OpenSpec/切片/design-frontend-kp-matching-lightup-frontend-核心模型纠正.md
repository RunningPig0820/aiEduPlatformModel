# 核心模型纠正

> summary: 纠正：学生掌握的是题型而非知识点，学会鸡兔同笼≠掌握二元一次方程；知识点由题型→知识点映射 QuestionTypeKp ratio 派生。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-核心模型纠正.md
> 类别：业务视角

---

### 核心模型纠正：掌握度主体 = 题型，知识点派生

> 检索摘要：纠正：学生掌握的是题型而非知识点，学会鸡兔同笼≠掌握二元一次方程；知识点由题型→知识点映射 QuestionTypeKp ratio 派生。

**当前（错）**：整条掌握度链路以**知识点**为主键——Python `decide` 输出 `mastery_signals[].kp_label` → `TutoringKpResolver` 解析成 TextbookKP URI → `StudentKpMastery`（`student_id + kp_key` 唯一）→ `MasteryItemDTO`（`kpKey` 主键）。把「会做某类题」直接当成「掌握某个知识点」。

**纠正（对）**：学生掌握的是**题型**，不是知识点。学会「鸡兔同笼」≠ 掌握「二元一次方程」。掌握度主体应是题型；知识点是题型经「题型→知识点映射」派生的结果。

```
学生做题（decide 输出 mastery_signals）
   → 题型掌握度（主体：题型 topicLabel，mastered/practicing/struggling → 75/50/25）
   → 题型 → 知识点 映射（QuestionTypeKp：kpUri + ratio 占比）
   → 知识点派生覆盖（某知识点 = Σ 覆盖它的题型的掌握度 × ratio）
   → 知识点总览（全量知识点，按派生覆盖度着色）
```

**后端依赖（需配合）**：掌握度信号从「知识点」粒度翻转为「题型」粒度（`MasterySignal`/`StudentKpMastery` 主键由 `kpKey` 改为题型标识 `topicKey`＝题型名），知识点掌握度由 `QuestionTypeKp`（ratio）派生。前端依赖「题型掌握度」与「知识点派生覆盖度」两个新契约。

> 旁证：`pending-kps` 返回的 `PendingKpAliasDTO` 本就是「题型（topicLabel）+ 疑似知识点（kpLabel）」结构——「待确认」天然是「某个题型的知识点归属不确定」，与题型为主体的模型一致，比知识点为主键更自洽。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§核心模型纠正：掌握度主体 = 题型，知识点派生）
