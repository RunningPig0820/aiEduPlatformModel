# 域 B 独立化

> summary: 域B 题型↔知识点改查表只读+ADMIN 独立维护，停用 obs 自动关联涌现，PENDING 语义改 canonical 未归属。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D10-域B独立化.md
> 类别：架构设计

---

### Decision 10：域 B 独立化——题型↔知识点 = 查表只读 + 独立维护（去自动关联）

> 检索摘要：域B 题型↔知识点改查表只读+ADMIN 独立维护，停用 obs 自动关联涌现，PENDING 语义改 canonical 未归属。

**目标**：所有入口只到「题型」阶段；题型↔知识点关联由**独立逻辑**维护，入口只读。业务不成熟期不做自动关联。

- **入口流程（analyze-question / 答疑 decide）**：识别题型名 → 查题型库（`findByTopicLabelOrAlias` → `t_kp_question_type_kp` 分布桶）→ **命中返回权威分布 / 未命中返回「仅题型 + canonical + 空知识点」**——不挂起、不写 obs、不顺带 LLM kps。
- **独立逻辑 = ADMIN 维护接口**：题型 CRUD + 题型↔知识点分布绑定（`t_kp_question_type` / `t_kp_question_type_kp` / 别名表）——演示手动配几条数据，入口查表即命中；是下期「题型库管理后台」的雏形。**替代「obs 共现 → LLM 归纳 ratio」的自动涌现**。
- **停用自动涌现链路**：Python `understandQuestion` 顺带 kps 的消费、`upsertPendingIfAbsent` 挂起、学生 vote 澄清、聚合 `aggregate`（obs 共现自动关联）、`KpCoverageAppService` 派生（前端已不消费）。
- **PENDING 语义更新（承接 Decision 9）**：域 B 独立化后 analyze/decide 不再产生「题型→知识点」挂起 obs → `getMastery` 的 `status=PENDING` **不再来自 obs**，改为「题目记录有但 canonical 未归属」（题目表 `canonical_label` 为空，待聚集/待归属）。
- **为什么**：演示项目 + 题型↔知识点业务不成熟——自动关联引入 obs 状态机/聚合批处理/LLM 归纳 5 个环节，分散本期核心（题目→题型→掌握度）；手动维护一张表、入口查表，可演示、可解释、可控。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 10）｜ 语雀-决策记录.md D8/D14 ｜ 完善文档 09-业务闭环与两域解耦.md ｜ 坑档案 J-QT3
