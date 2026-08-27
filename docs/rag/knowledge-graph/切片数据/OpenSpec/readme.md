# 切片数据 / OpenSpec

> 来源：`2.OpenSpec design 决策/design-*.md`（历史设计素材层，doc_type=design_spec，权威 **0.7**）
> 切片方式：**提示词 + 大模型按 ### 切**（脚本导出方案已废弃，2026-08-27 与 代码/坑档案/引导问题/语雀 对齐）。

## 一、源头（语料就绪，2026-08-27 ✅ 已全部成文）

- 源文档：`2.OpenSpec design 决策/design-*.md`（**12 份 RAG 结构化重构版已完成**，由 `spec文件整理.md` 产出）
- 生成提示词：`2.OpenSpec design 决策/处理方案/提示词/spec文件整理.md`（每份 design 各自成文，权威 0.7 素材溯源库，100% 保留 Migration/Risks/OpenQuestions）
- 前提：design-*.md 已按 ### 小节结构化（每个决策/背景/目标/风险/迁移/开放各一小节，**每块已带 状态+检索摘要**）
- 原始稿归档：`原来的文件/design-*.md`（证据源，不进池）；13 份低价值 proposal + review-system design 已删除（2026-08-27）

## 二、切片（提示词 + 大模型按 ### 切）

- 粒度：一个决策/背景/目标/风险/迁移/开放问题各一小节一块；决策编号**归一化** `Decision #/决策 # → D{#}`
- 保真：决策正文/属性表/表格/流程图文本/代码块原样保留，**特别完整保留 风险与权衡/迁移计划/开放问题**；只删 文档说明
- **不写状态，检索摘要必须有**：每块正文必须带 `> 检索摘要：`（源小节检索摘要原样完整；缺失补写 1-2 句富含核心实体与动作）——素材层未落地/待决语义由 `authority=0.7 + source=OpenSpec` 层规则兜底
- 头部精简 5 行（summary/权威度 0.7/模块/COS路径/类别），机器元信息（entry_id/source_doc）摄入时推导

## 三、本模块 design 切片清单（12 份,共 242 块,2026-08-28 已全部产出）

| design 文件 | ### 块数 | 备注 |
|---|---|---|
| `design-python-2026-04-10-knowledge-graph-data-research.md` | 54 | 90KB 拆 #### 子块（上半 §一~九 23 + 下半 §9.5~17 31） |
| `design-python-2026-04-15-kg-math-complete-graph.md` | 29 | 匹配阈值/URI v3.1 |
| `design-backend-kp-matching-lightup.md` | 28 | D1~D22 每决策一块 |
| `design-python-2026-03-28-integrate-edukg-knowledge-graph.md` | 22 | D1~D5 |
| `design-backend-2026-06-03-knowledge-graph-ui.md` | 20 | 页面化方案 B（D12 拆 12.1~12.5） |
| `design-python-2026-04-10-textbook-concept-linking.md` | 16 | 教材↔概念匹配 |
| `design-python-kg-math-prerequisite-inference.md` | 15 | 前置依赖/双模型投票 |
| `design-frontend-kp-matching-lightup-frontend.md` | 14 | 掌握度主体纠正 |
| `design-python-2026-04-08-kg-infrastructure-init.md` | 13 | D1~D5 llmTaskLock |
| `design-frontend-2026-06-09-knowledge-graph-ui-front.md` | 13 | React Flow |
| `design-backend-2026-06-03-knowledge-graph-datasource.md` | 9 | 双数据源 @DS |
| `design-python-2026-04-10-textbook-crawler.md` | 9 | 爬虫 |
| **合计** | **242** | 全落 `切片/`（参考值 278，data-research 以实际解析为准 54 块） |

## 四、检索规则（入桶/查询时生效）

- **素材溯源库，不作回答主来源**：权威度 0.7，回答"设计当初怎么想/为什么这么定/有哪些待决"，**不能当已上线功能**
- 检索规则：优先 0.8/1.0 真相源（语雀 canonical / 完善文档 / 代码），主库无答案才允许引用本层；**引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」**
- COS路径：`rag-slices/knowledge-graph/OpenSpec/...`
