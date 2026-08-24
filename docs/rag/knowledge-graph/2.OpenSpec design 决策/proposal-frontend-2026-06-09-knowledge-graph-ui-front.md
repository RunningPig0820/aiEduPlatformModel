## Why

后端已完成知识图谱（Neo4j → MySQL）的数据建模和导航 API，需要前端页面将知识图谱数据可视化呈现，支持管理员通过树形导航浏览教材知识点体系，并通过关系图谱展示教材知识点与知识点之间的关联关系。

## What Changes

- 新建 React SPA 项目，集成知识图谱管理端页面
- 新增三栏布局页面（左侧树形导航 + 中间关系图谱 + 右侧详情面板）
- 新增知识图谱 API 模块，封装教材导航、知识点详情、图谱关系等接口
- 实现逐级懒加载树形导航（人教版 → 学科 → 年级 → 单元 → 课时 → 知识点）
- 实现基于 React Flow 的关系图谱可视化
- 实现节点详情展示功能

## Capabilities

### New Capabilities

- `kg-textbook-nav`: 教材树形导航，支持逐级展开和懒加载子节点
- `kg-graph-view`: Neo4j 关系图谱可视化，展示教材知识点与知识点的关联
- `kg-detail-panel`: 知识点详情面板，展示节点基本信息
- `kg-api`: 知识图谱 API 集成模块，封装导航、详情、图谱关系接口

### Modified Capabilities

- 无现有 Capability 需要修改

## Impact

**新增文件：**
- `src/pages/KnowledgeGraphPage.jsx` - 知识图谱主页面（三栏布局容器）
- `src/components/kg/TextbookTree.jsx` - 左侧树形导航组件
- `src/components/kg/KnowledgeGraph.jsx` - 中间 React Flow 图谱组件
- `src/components/kg/DetailPanel.jsx` - 右侧详情面板组件
- `src/api/modules/kg.js` - 知识图谱 API 模块

**新增依赖：**
- `react-flow-renderer` (React Flow) - 关系图谱渲染

**依赖后端 API：**
- `GET /api/kg/textbooks` - 获取教材列表
- `GET /api/kg/textbooks/{uri}/chapters` - 获取章节列表
- `GET /api/kg/chapters/{uri}/sections` - 获取小节列表
- `GET /api/kg/sections/{uri}/points` - 获取知识点列表
- `GET /api/kg/knowledge-points/{uri}` - 获取知识点详情
- `GET /api/kg/knowledge-points/{uri}/graph` - 获取知识点关联图谱数据（需后端提供）
