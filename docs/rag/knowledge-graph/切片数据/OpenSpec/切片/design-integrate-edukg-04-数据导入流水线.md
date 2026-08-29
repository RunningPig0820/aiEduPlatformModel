# 数据导入流水线

> summary: 数据导入流水线
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-04-数据导入流水线.md
> 类别：操作流程

## 数据导入策略（D2）

选择使用 EDUKG TTL 文件通过 Neo4j n10s 插件批量导入，而非逐条插入：
- EDUKG 已提供 TTL 格式数据
- Neo4j n10s 插件原生支持 RDF 导入
- 批量导入性能优于逐条插入

## 导入流程

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

## 实施步骤（阶段二：数据导入）

1. 下载 EDUKG TTL 文件
2. 实现 TTL → Neo4j 导入脚本
3. 验证数据完整性

## 数据导入性能风险（R1）与缓解

风险：EDUKG 数据量大（38.6 亿三元组），导入耗时长。

缓解：
- 分学科增量导入
- 先导入核心学科（数学、物理、语文）
- 已有独立 Neo4j 服务器，性能有保障
