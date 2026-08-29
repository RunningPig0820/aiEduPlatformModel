# 切片数据 / OpenSpec

> 来源：`2.OpenSpec design 决策/design-*.md`（历史设计素材层，doc_type=design_spec，权威 **0.7**）
> 切片方式：**提示词 + 大模型按业务主题合并**（`业务主题清单.md` 17 主题，一块 = 一个业务问题的完整答案；2026-08-29 用户口径：按业务匹配、非按文档结构 ### 硬切）。

## 一、源头（语料就绪，2026-08-27 已全部成文）

- 源文档：`2.OpenSpec design 决策/design-*.md`（**12 份 RAG 结构化重构版已完成**，由 `spec文件整理.md` 产出）
- 生成提示词：`2.OpenSpec design 决策/处理方案/提示词/spec文件整理.md`（每份 design 各自成文，权威 0.7 素材溯源库，100% 保留 Migration/Risks/OpenQuestions）
- 前提：design-*.md 已按 ### 小节结构化（每个决策/背景/目标/风险/迁移/开放各一小节），重切按业务主题归并（D#/### 作正文保留，不作文件名）
- 原始稿归档：`原来的文件/design-*.md`（证据源，不进池）；13 份低价值 proposal + review-system design 已删除（2026-08-27）

## 二、切片（提示词 + 大模型按业务主题合并）

- 粒度：**按业务主题**（`切片数据/业务主题清单.md` 17 主题大纲，按文档实际内容可偏移/新增 18+）；一份源文档只产它覆盖的主题块（不产空块），同主题跨文档不合并（靠源文档前缀区分）
- 块 = 该主题在文档内所有相关决策/背景/风险/迁移内容合并，**去结构编号头**（D# 作正文保留）
- **大小约束（2026-08-29）**：每块正文 ≤ 5000 字符（**全文向量化入桶**，embed 输入上限），超长按子块拆 -2/-3，每子块自包含
- **检索摘要必须有**：每块正文带 `> 检索摘要：`（业务向提问式）——素材层未落地/待决语义由 `authority=0.7 + source=OpenSpec` 层规则兜底
- 头部精简 5 行（summary 短标题式 `{主题短名}` / 权威度 0.7 / 模块 / COS路径 / 类别），机器元信息（entry_id/source_doc）摄入时推导
- **禁止 emoji 符号**（✅/⚠️/❓/❌）：状态一律用文字表达（已完成/待决/风险/警告），避免污染向量

## 三、本模块 design 切片清单（12 份,共 81 块,2026-08-29 按主题重切完成）

> 2026-08-29 精简：删 **10 个「主题16 方案选型与决策记录」总览索引块**（低价值/与语雀 16 块重复，见 `低价值与重复切片评估.md`），OpenSpec 91→81。

| design 文件 | 主题块数 | 覆盖主题 |
|---|---|---|
| `design-python-2026-04-10-knowledge-graph-data-research.md` | 14 | 01/02/03/04(×2)/07(×4)/12(×2)/13/18/19 |
| `design-python-2026-04-15-kg-math-complete-graph.md` | 10 | 01/02/03/04/05/06/08/12/13/15 |
| `design-backend-kp-matching-lightup.md` | 11 | 01/03/06/10/11/13/18/19/20/21/22 |
| `design-python-2026-03-28-integrate-edukg-knowledge-graph.md` | 8 | 01/02/03/04/11/15/18/19 |
| `design-backend-2026-06-03-knowledge-graph-ui.md` | 7 | 10(×4)/11/13/15 |
| `design-frontend-kp-matching-lightup-frontend.md` | 6 | 10(×4)/13/15 |
| `design-python-2026-04-08-kg-infrastructure-init.md` | 6 | 09/12(×3)/13/15 |
| `design-frontend-2026-06-09-knowledge-graph-ui-front.md` | 3 | 10/11/15 |
| `design-python-kg-math-prerequisite-inference.md` | 3 | 07/05/12 |
| `design-python-2026-04-10-textbook-crawler.md` | 3 | 02/04/13 |
| `design-python-2026-04-10-textbook-concept-linking.md` | 9 | 01/02/03/04/05/06/09/13/15 |
| `design-backend-2026-06-03-knowledge-graph-datasource.md` | 1 | 10 |
| **合计** | **81** | 全落 `切片/`（新主题 18~22：实体链接/学生进度/技术栈/成本/掌握度翻转/信任模型/维护闭环/迁移/待决） |

## 四、检索规则（入桶/查询时生效）

- **素材溯源库，不作回答主来源**：权威度 0.7，回答"设计当初怎么想/为什么这么定/有哪些待决"，**不能当已上线功能**
- 检索规则：优先 0.8/1.0 真相源（语雀 canonical / 完善文档 / 代码），主库无答案才允许引用本层；**引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」**
- COS路径：`rag-slices/knowledge-graph/OpenSpec/...`
