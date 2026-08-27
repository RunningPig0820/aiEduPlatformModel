# 图谱数据主键 URI（非自增 ID，URI 永不修改）

> summary: 图谱节点主键为什么用 URI？非自增 ID，URI 生成后永不修改，改动走合并流程，避免主键漂移。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D15-图谱数据主键URI.md
> 类别：操作流程

---

### D15 图谱数据主键 URI（非自增 ID，URI 永不修改）
> 检索摘要：图谱节点主键为什么用 URI？非自增 ID，URI 生成后永不修改，改动走合并流程，避免主键漂移。

| 属性 | 内容 |
|---|---|
| 背景 | 自增 ID 无法跨源对齐；URI 是跨 Neo4j/MySQL 唯一锚点 |
| 演进 | 无 |
| 拍板理由 | 所有主表以 uri 作主键；URI 校验（以 http://edukg.org/knowledge/ 开头）；<1 万节点 VARCHAR(255) 可行 |
| 系统影响 | 合并流程 merged_to_uri；状态机 active/deleted/merged；对账校验 |
| 证据 | 证据：语雀-页面化-ui-design.md / design-backend-2026-06-03-knowledge-graph-ui.md Decision 6 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D15）
