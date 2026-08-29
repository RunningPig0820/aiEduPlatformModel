# 演进与未来

> summary: 演进与未来
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-15-演进与未来.md
> 类别：未来演进

## 实施路线图（阶段一~四）

- **阶段一：基础设施搭建** —— 配置 Neo4j 连接（已有独立服务器）、创建 `core/kg/` 模块结构、实现 `neo4j_client.py` 连接管理与 `entity_linker.py` 实体链接
- **阶段二：数据导入** —— 下载 EDUKG TTL 文件、实现 TTL→Neo4j 导入脚本、验证数据完整性
- **阶段三：核心功能** —— 实现实体查询 API、实体链接服务、知识树输出
- **阶段四：学习进度** —— 设计学生-知识点关系模型、实现进度追踪 API、集成测试

## 未来方向（本期 Non-Goals 后置）

- **向量数据库集成（下一阶段）**：后续 RAG 场景需要向量数据库，设计抽象层便于替换实现，预留 `VectorStoreInterface` 接口（风险 R3 的缓解方案）
- **前端可视化**：本期仅提供 API；知识树渲染方案待定（D3.js 或 ECharts，见开放问题）
- **自定义知识点编辑**：后续扩展
- **知识图谱增量更新**：后续扩展

## 待决策开放问题（Open Questions）

1. **EDUKG 数据下载**：Google Drive 可能需要代理，是否需要提供国内镜像？
2. **学科优先级**：9 个学科是否全部导入？建议先导入数学、物理、语文？
3. **前端可视化**：知识树渲染是否使用 D3.js 或 ECharts？
4. **进度同步**：学生进度是否需要同步到 Java 后端数据库？
