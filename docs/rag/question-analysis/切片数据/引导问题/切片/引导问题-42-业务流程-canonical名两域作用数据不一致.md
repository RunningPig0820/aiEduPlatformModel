# canonical 名在两域之间起什么作用？如果两域数据不一致会怎样？

> summary: canonical 名在两域之间起什么作用？如果两域数据不一致会怎样？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-42-业务流程-canonical名两域作用数据不一致.md
> 类别：业务流程

---

## 回答

**核心结论**：canonical 名是两域的**对接缝/契约**——域 A 产出 canonical 题型名，域 B 用同名做题型↔知识点映射。如果两域数据不一致（canonical 对不上），映射查表 miss，域名 B 展示空知识点/权威分布缺失，但不影响域 A 掌握度——因为两域解耦，各自为政。

**分层展开**：
- **canonical 的契约作用**：域 A 掌握表 key = canonical；域 B 题型库 `t_kp_question_type` 也按 canonical 收——两域靠同一套题型名对齐。（依据：完善文档 09 / 分析-08）
- **不一致的后果**：域名 B 查表 miss（`findByTopicLabelOrAlias` 找不到）→ 返回"仅题型+canonical+空知识点"，知识点展示缺失——但域 A 掌握度链路不受影响，两域故障隔离。（依据：完善文档 09 / 分析-08）
- **别名表兜底**：`t_kp_question_type_alias` 存别名收敛，降低 miss；但本质对齐靠 canonical 从源头统一（落库前向量归并）。（依据：完善文档 06 / 09）
- **零写入红线**：即便不一致，也绝不污染权威图谱——派生层 MySQL 承担映射，Neo4j 只借结构。（依据：完善文档 07 / 分析-08）

> 证据：详见 `7. 引导问题/问题列表.md`（第 42 问）｜ `4.完善文档/09-业务闭环与两域解耦.md` ｜ `3.代码/分析-08-图谱与知识点关联.md`
