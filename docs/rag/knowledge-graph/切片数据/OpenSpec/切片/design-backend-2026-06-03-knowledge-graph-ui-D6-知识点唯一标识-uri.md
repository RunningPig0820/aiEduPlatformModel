# D6：知识点唯一标识：URI

> summary: 决策：MySQL主表以uri为主键而非自增ID，URI是Neo4j天然唯一标识，同步按URI UPSERT，URI校验格式且永不修改。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D6-知识点唯一标识-uri.md
> 类别：数据存储

> 检索摘要：决策：MySQL主表以uri为主键而非自增ID，URI是Neo4j天然唯一标识，同步按URI UPSERT，URI校验格式且永不修改。

**决策**: MySQL 所有主表以 `uri` 作为主键（而非自增 ID）。URI 是 Neo4j 中的天然唯一标识（如 `http://edukg.org/knowledge/3.1/textbook/一年级上册`），同步时直接按 URI UPSERT，下游引用也使用 URI 而非 MySQL 自增 ID。

**URI 校验规则**:
- 同步时检查 URI 非空、格式以 `http://edukg.org/knowledge/` 开头
- 同批次同步中检测 URI 重复，记录到同步日志并跳过
- URI 生成后永不修改（若需修改走合并流程）

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D6：知识点唯一标识：URI）
