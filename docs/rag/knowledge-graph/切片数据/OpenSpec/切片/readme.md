# 切片数据 / OpenSpec / 切片

> OpenSpec design 素材按 ### 小节切片（**12 份 design,共 242 块**）在此目录。一个决策/背景/目标/风险/迁移/开放问题各一小节一块。
> 来源：`2.OpenSpec design 决策/design-*.md`（权威 0.7，历史设计素材层），由 `../处理方案/提示词/OpenSpec-切片-提示词.md` 生成。
> 状态：2026-08-28 全部产出。

## 组成（12 份 design,242 块）

| design 文件 | 块数 | 备注 |
|---|---|---|
| design-python-2026-04-10-knowledge-graph-data-research | 54 | 90KB 拆 #### 子块（上半 §一~九 23 + 下半 §9.5~17 31） |
| design-python-2026-04-15-kg-math-complete-graph | 29 | 匹配阈值/URI v3.1 |
| design-backend-kp-matching-lightup | 28 | D1~D22 每决策一块 |
| design-python-2026-03-28-integrate-edukg-knowledge-graph | 22 | D1~D5 + 阶段/风险/开放 |
| design-backend-2026-06-03-knowledge-graph-ui | 20 | 页面化方案 B（D12 拆 12.1~12.5） |
| design-python-2026-04-10-textbook-concept-linking | 16 | 教材↔概念匹配 |
| design-python-kg-math-prerequisite-inference | 15 | 前置依赖/双模型投票 |
| design-frontend-kp-matching-lightup-frontend | 14 | 掌握度主体纠正 |
| design-python-2026-04-08-kg-infrastructure-init | 13 | D1~D5 llmTaskLock |
| design-frontend-2026-06-09-knowledge-graph-ui-front | 13 | React Flow |
| design-backend-2026-06-03-knowledge-graph-datasource | 9 | 双数据源 @DS |
| design-python-2026-04-10-textbook-crawler | 9 | 爬虫 |
| **合计** | **242** | |

> 参考值 278 与实际 242 的差异：data-research 提示词注明"### 块数为参考值,以文档实际解析为准"，实际 54 块（超长 #### 子块按 ≤1500 token 合并策略切分）。

## 检索规则

- **素材溯源库，不作回答主来源**：权威度 0.7，回答"设计当初怎么想/为什么这么定/有哪些待决"，**不能当已上线功能**
- 检索：优先 0.8/1.0 真相源（语雀 canonical / 完善文档 / 代码），主库无答案才允许引用本层；**引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」**
- 每块正文带 `> 检索摘要：`；切片头不写状态（未落地/待决语义由 authority=0.7 + source=OpenSpec 层规则兜底）
- COS路径：`rag-slices/knowledge-graph/OpenSpec/{文件名}.md`
