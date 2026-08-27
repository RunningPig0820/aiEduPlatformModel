# D2 数据导入策略 → TTL + 批量导入
> summary: 数据导入选 EDUKG TTL 文件经 n10s.rdf.import 批量导入 Neo4j，流程为 graphconfig.init→nsprefixes.add→rdf.import.fetch。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-D2-数据导入策略-ttl-批量导入.md
> 类别：数据存储

> 检索摘要：数据导入选 EDUKG TTL 文件经 n10s.rdf.import 批量导入 Neo4j，流程为 graphconfig.init→nsprefixes.add→rdf.import.fetch。

**选择**: 使用 EDUKG TTL 文件通过 `n10s.rdf.import` 批量导入 Neo4j
**原因**:
- EDUKG 已提供 TTL 格式数据
- Neo4j n10s 插件原生支持 RDF 导入
- 批量导入性能优于逐条插入

**导入流程**:
```
EDUKG TTL 文件
    ↓
n10s.graphconfig.init()
    ↓
n10s.nsprefixes.add()  # 注册命名空间
    ↓
n10s.rdf.import.fetch()  # 批量导入
    ↓
Neo4j 图数据库
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§D2 数据导入策略 → TTL + 批量导入）
