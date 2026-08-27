# 切片数据 / OpenSpec / 切片

> OpenSpec design 素材全部按 `###` 小节切片（91 块）在此目录。一个决策/小节一个文件，正文带 `> 检索摘要` 作召回锚点，直接可入切片池 rag-slice（source=OpenSpec）。
> 来源：`2.OpenSpec design 决策/design-*.md`（6 份 RAG 版），由 `../处理方案/提示词/OpenSpec-切片-提示词.md` 生成。
> 状态：2026-08-27 全量产出完成（91 文件，85 小节 + 6 个超长拆子块）。

## 组成

| 源文档 | 小节数 | 块数（含子块） | 决策编号 |
|---|---|---|---|
| design-backend-kp-question-analysis-backend | 18 | 24（D3/5/7/8/13/风险 拆 -2） | D1~D13（乱序） |
| design-backend-question-type-mastery-backend | 15 | 15 | Decision 1~10 → D1~D10 |
| design-frontend-kp-question-analysis | 14 | 14 | 决策 1~9 → D1~D9 |
| design-frontend-question-type-mastery | 20 | 20 | 决策 1~10 → D1~D10 + 验收反馈 A-D/产品优化 |
| design-python-ai-tutoring-topic-mastery-signal | 8 | 8 | 决策 1~5 → D1~D5 |
| design-python-question-type-mastery-python | 10 | 10 | D1~D5 |
| **合计** | **85** | **91** | |

## 头部元信息（精简 5 行）

- `> summary` = 源小节 `> 检索摘要` **原样完整保留**（召回锚点，信息越全检索率越高）
- `> 权威度: 0.7` ｜ `> 模块: question-analysis` ｜ `> COS路径: rag-slices/question-analysis/OpenSpec/...`
- `> 类别`：9 视角闭集单值（架构设计/数据存储/数据关联/开发难点/操作流程/业务视角/项目介绍/未来演进）
- 正文 `> 检索摘要：` 必带（源摘要原样）；**无 `> 状态` 行**（素材层未落地/待决语义靠 `authority=0.7 + source=OpenSpec` 层规则兜底，引用必须提示核对代码）

> 机器元信息（entry_id/source_doc）**不在 md 头写**，QT⑥⑦ 摄入时从文件名推导：entry_id←文件名段（`design-{change}-D{n}-*`→{change}-D{n}、`design-{change}-Context.md`→Context、子块 `-2` 后缀）、source_doc←文件名前缀（`design-{change}-*`→design-{change}.md）。

## 检索规则

- doc_type=design_spec，**素材溯源库不作回答主来源**：优先 0.8/1.0 真相源（语雀 canonical/完善文档/代码），主库无答案才允许引用；**引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」**，禁止把设计稿当已上线功能
- 与 语雀 canonical 同切片池，靠 `authority=0.7 + source=OpenSpec` 元数据识别素材层
