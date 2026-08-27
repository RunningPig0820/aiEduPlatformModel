# 切片数据 / OpenSpec 处理方案

1. **源头就绪**：`2.OpenSpec design 决策/design-*.md`（权威 0.7，由 `spec文件整理.md` 产出，100% 保留 Migration/Risks/OpenQuestions）
2. **按 ### 小节切片**：`提示词/OpenSpec-切片-提示词.md` —— 一个决策/背景/目标/风险/迁移/开放各一小节一块，决策编号归一化 `D{#}`；顶层 `# ==== 分节 ====` 不作 chunk
3. **原文保真 100%**：决策正文/属性表/表格/流程图文本/代码块原样保留，特别完整保留 风险与权衡/迁移计划/开放问题；只删 文档说明
4. **不写状态，检索摘要必须有**：每块正文带 `> 检索摘要：`（源小节检索摘要原样完整；缺失补写）；素材层未落地/待决语义由 `authority=0.7 + source=OpenSpec` 层规则兜底；不自动生成 WARNING
5. 入桶：COS路径 `rag-slices/knowledge-graph/OpenSpec/...`，`doc_type=design_spec`，权威 0.7

> 与 question-analysis 同构：OpenSpec 层按 ### 切（决策/背景/目标/风险/迁移/开放各一小节一块）用 `OpenSpec-切片-提示词.md`（改模块 id / design 清单表 / 文件名前缀）。
