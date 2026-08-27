# 分析-11-Java同步与前端页面-代码事实-2

> summary: Java同步与前端页面代码事实
> 来源: 切片 ｜ 锚点: 代码事实-2
> 节: 分析-11-Java同步与前端页面
> COS路径: rag-slices/knowledge-graph/代码/分析-11-Java同步与前端页面-代码事实-2.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

> 本节约束：以下全部为 design 文档描述（`design-backend-*-knowledge-graph-{datasource,ui}.md` / `design-frontend-*-knowledge-graph-ui-front.md`），**代码实现不在本仓，未真读，非代码真值**。

### API 设计（design-backend-ui D12.1-D12.5）
| 接口 | 作用 |
|---|---|
| `POST /api/kg/sync/full` | 触发全量同步（可选 subject/phase/grade/textbookUri） |
| `GET /api/kg/sync/status` / `GET /api/kg/sync/records` | 同步状态/历史 |
| `GET /api/kg/dimensions/subjects|grades|phases|textbooks` | 下拉选项（枚举+MySQL 混合） |
| `GET /api/kg/subjects` / `{subject}/grades` / `{grade}/textbooks` | 6 级导航前三层 |
| `GET /api/kg/textbooks/{uri}/chapters` / `sections/{uri}/points` | 章节树/小节知识点 |
| `GET /api/kg/knowledge-points/{uri}` | 知识点详情（含 2 层父级） |
| `GET /api/kg/knowledge-points/{uri}/graph` / `{uri}/path` | 图谱关系/到概念完整路径（Neo4j） |
| `GET /api/kg/system/grade/{grade}` / `system/stats/{grade}` | 年级知识体系/统计 |
| `GET /api/kg/concepts/{uri}/relations` / `concepts/batch-relations` | 概念关联图（Neo4j+Redis 缓存） |
| `GET /api/kg/neo4j/health` | Neo4j 健康检查 |

### 前端页面（design-frontend）
1. **三栏布局**：左教材树 + 中 React Flow 关系图 + 右详情，父组件 `KnowledgeGraphPage` 用 state+props 管理选中联动（不引入 zustand）（design-frontend:8,116-124）。
2. **逐级懒加载**：自定义递归树组件（daisyUI Tree 不支持动态懒加载），树展开请求子节点并缓存，切换教材根清空缓存；6757 节点不一次性渲染（design-frontend:61-82）。
3. **React Flow**：`useNodesState/useEdgesState` 管理，优先后端返回力导向初始坐标；节点>50 提供"简化视图"仅显示 Top 10；无数据给空态文案（design-frontend:50-59,126-139）。
4. **同步管理页**：页面头部按钮触发 `POST /api/kg/sync/full`（可按学科/学段/年级/教材筛选），`status/records` 展示，MVP 用 Modal/侧边面板（design-frontend:94-103）。
5. **统计面板**：页面顶部概览卡片，`system/stats/{grade}`（教材/章节/小节/知识点数+难度分布）、`neo4j/health`（design-frontend:105-115）。
6. **错误处理**：树展开/图谱加载失败给重试按钮；渲染异常全局 Error Boundary 捕获；未登录统一拦截跳登录（design-frontend:140-146）。

## 设计要点

- **方案 B：Neo4j→MySQL 同步、前端读 MySQL**（语雀 D13）：Java 无 Neo4j 集成、前端独立 SPA，MySQL 只存节点属性+层级关系，图谱关系直查 Neo4j 而非同步——避免无限业务事实污染权威图谱（配合 D17 权威图谱零写入）。
- **URI 主键**（语雀 D15）：非自增 ID，跨 Neo4j/MySQL 唯一锚点，同步按 URI UPSERT，URI 永不修改、改动走合并流程。
- **状态机软删除**：active/deleted/merged 让"删除"可回溯、进度历史不丢（进度查询例外不过滤 deleted）。
- **降级优先**：Neo4j 关系查询 Redis TTL 300s + 空关联降级，核心导航不依赖图谱服务可用性。
- **手动按需同步而非 CDC**：demo 阶段避免实时监听复杂度，失败可重跑（UPSERT 幂等 + 单事务原子）。

> 证据：详见 `3.代码/分析-11-Java同步与前端页面.md`（§代码事实 API 设计 / 前端页面，§设计要点）
