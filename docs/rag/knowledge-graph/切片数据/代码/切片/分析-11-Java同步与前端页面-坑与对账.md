# 分析-11-Java同步与前端页面-坑与对账

> summary: Java同步与前端页面坑与对账
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-11-Java同步与前端页面
> COS路径: rag-slices/knowledge-graph/代码/分析-11-Java同步与前端页面-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

## 隐性坑与注意事项

- **graph 接口未实现**：前端原计划 `GET /api/kg/knowledge-points/{uri}/graph`，但 design 标注"后端当前未实现此接口"，替代方案待确认（补接口 / batchGetConceptRelations 自建 / 其他接口组合）（design-frontend:83-92,154）。
- **路径前缀不一致**：后端 design 写 `/api/kg/**`，前端 design 全部用 `/api/auth/kg/**` 前缀——两者口径未对齐，联调易 404。
- **首次下拉为空**：年级下拉来自 `t_kg_textbook DISTINCT grade`，必须先做一次全量同步才有数据（design-backend-ui D10）。
- **关联表重建有窗口**：同步先 DELETE 再 INSERT 关联表，依赖单事务保证前端看不到中间态；若事务失效会重现"空目录"联调问题（design-backend-ui D2）。
- **deleted 数据膨胀**：status='deleted' 定期物理清理需确认无下游引用（design-backend-ui Risks）。
- **URI 主键性能**：<1 万节点 VARCHAR(255) 主键可行，暴涨才考虑整型代理键（design-backend-ui Risks）。

## 对账要点

对账结论逐条复盘（原始方案 → 实际落地 → 结论），**本主题 Java/前端代码不在本仓，所有对账均为 design 文档层面核对，非代码真值**：

- **Java/前端代码是否落地**：语雀 D13/D14 描述页面化落地，实际代码不在本仓（`aiEduPlatform/`/`aiEduPlatformFront` 不存在），仅有 design 文档。⚠️无法核实（非代码真值）——不能把设计当已实现。
- **图谱 graph 接口契约**：design-backend-ui 列出 `knowledge-points/{uri}/graph`，实际 design-frontend 标注该接口后端未实现。⚠️契约断裂（design 内自相矛盾）。
- **API 前缀口径**：后端 design 写 `/api/kg/**`，前端 design 用 `/api/auth/kg/**`。⚠️口径不一致——联调易 404。
- **8 张表**：语雀 D13 口径为 4 节点主表+3 层级关联+1 同步记录，实际 design-backend-ui D1 表结构与状态机一致。✅落地——文档层面一致。
- **双数据源**：语雀 D14 `@DS("kg")` ai_edu_kg，实际 design-backend-datasource 全链路设计一致。✅落地——文档层面一致。
- **前端三栏/懒加载/React Flow**：语雀 design-frontend 目标，实际 design 一致。✅落地——文档层面一致。
- **Flyway**：注释/设计为双库分组管理，实际运行行为是当前全禁用、表手动创建。⚠️翻转——设计降级（表从 Flyway 迁移改为手动创建）。

> 证据：详见 `3.代码/分析-11-Java同步与前端页面.md`（§隐性坑与注意事项 / §对账要点）
