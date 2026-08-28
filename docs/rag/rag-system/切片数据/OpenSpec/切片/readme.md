# 切片数据 / OpenSpec / 切片

> OpenSpec design 素材 16 份 RAG 版**按业务主题合并**（2026-08-28 完成，79 块）在此目录。一块=一个业务问题的完整答案（对齐 `业务主题清单.md` 20 主题），不再按 ### 结构拆；文件名 `{源文档前缀}-{主题编号}-{主题名}.md`，同主题跨文档块靠源文档前缀区分。正文带 `> 检索摘要` 作召回锚点。
> 来源：`2.OpenSpec design 决策/原来的文件/` 16 份 RAG 版，口径：`../../业务主题清单.md` + `../处理方案/提示词/OpenSpec-切片-提示词.md`。
> 状态：✅ 79 块（design-java 15 / design-python-intro-rag 14 / design-eval-agent 12 / design-assistant 8 / design-frontend 6 / spec-gateway 4 / spec-corpus 1 / spec-permission 2 / spec-eval-agent 1 / spec-observability 2 / spec-kb-org 2 / spec-pipeline 4 / spec-resilience 2 / spec-assistant-eval 1 / spec-guardrails 3 / spec-frontend-ui 6）。

## 组成

| 源文档 | 小节数 | 块数（含子块） | 决策编号 |
|---|---|---|---|
| design-python-project-intro-rag | 待生成 | 待生成 | D1~D11（双池/页面锚定/两道门/token 真算） |
| design-python-rag-eval-agent | 待生成 | 待生成 | D1~D7（评测 agent hit@k + answer_quality） |
| **合计** | **待生成** | **待生成** | |

## 头部元信息（精简 5 行）

- `> summary` = 源小节 `> 检索摘要` **原样完整保留**（召回锚点，信息越全检索率越高）
- `> 权威度: 0.7` ｜ `> 模块: rag-system` ｜ `> COS路径: rag-slices/rag-system/OpenSpec/...`
- `> 类别`：9 视角闭集单值（架构设计/数据存储/数据关联/开发难点/操作流程/业务视角/项目介绍/未来演进/业务流程）
- 正文 `> 检索摘要：` 必带（源摘要原样）；**无 `> 状态` 行**（素材层未落地/待决语义靠 `authority=0.7 + source=OpenSpec` 层规则兜底，引用必须提示核对代码）

> 机器元信息（entry_id/source_doc）**不在 md 头写**，QT⑥⑦ 摄入时从文件名推导：entry_id←文件名段（`design-{change}-D{n}-*`→{change}-D{n}、`design-{change}-Context.md`→Context、子块 `-2` 后缀）、source_doc←文件名前缀（`design-{change}-*`→design-{change}.md）。

## 检索规则

- doc_type=design_spec，**素材溯源库不作回答主来源**：优先 0.8/1.0 真相源（语雀 canonical/完善文档/代码），主库无答案才允许引用；**引用必须提示「该信息来源于历史设计文档，请核对代码确认实际落地情况」**，禁止把设计稿当已上线功能
- 与 语雀 canonical 同切片池，靠 `authority=0.7 + source=OpenSpec` 元数据识别素材层
