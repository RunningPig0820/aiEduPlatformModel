## Context

### 背景
AI 教育平台当前已有 LLM Gateway 服务，支持智谱、DeepSeek、阿里百炼等多模型调用。现需要新增知识图谱能力，以支持：
- AI 答疑时识别知识点
- 学生学习进度可视化
- 教师备课推荐

### 技术现状
- **现有服务**: FastAPI + Python 3.11
- **LLM 集成**: LangChain 框架
- **配置管理**: Pydantic Settings

### EDUKG 项目分析
EDUKG 提供了以下可复用组件：

| 模块 | 文件 | 功能 | 复用程度 |
|------|------|------|----------|
| 知识图谱处理器 | `kg_handler.py` | TTL 加载、SPARQL 查询 | 高 |
| SPARQL 连接器 | `sparql_query.py` | Jena/Neo4j 连接 | 中（需适配） |
| 实体链接 | `linking.py` | 文本→实体识别 | 高 |
| 本体定义 | `ontology.owl` | 类/属性定义 | 直接使用 |

### 约束
1. ~~需要部署 Neo4j 图数据库~~ → **已有独立 Neo4j 服务器**
2. EDUKG TTL 数据文件需要从 Google Drive 下载
3. 实体链接使用内存词典，占用 ~20MB 内存
4. 后续需要对接向量数据库（Milvus）

## Goals / Non-Goals

**Goals:**
1. ✅ 集成 Neo4j 图数据库，支持知识图谱存储和查询
2. ✅ 实现 TTL 文件导入 Neo4j 的工具
3. ✅ 提供知识点实体查询 API
4. ✅ 实现文本实体链接服务
5. ✅ 支持学科知识树可视化数据输出
6. ✅ 预留向量数据库接口

**Non-Goals:**
- ❌ 本期不实现向量数据库集成（下一阶段）
- ❌ 不实现前端可视化（仅提供 API）
- ❌ 不实现自定义知识点编辑（后续扩展）
- ❌ 不实现知识图谱增量更新（后续扩展）

## Decisions

### D1: 图数据库选型 → Neo4j

**选择**: Neo4j
**原因**:
- 成熟的企业级图数据库，社区版免费
- 原生支持 RDF/TTL 导入（n10s 插件）
- Cypher 查询语言易学，文档完善
- EDUKG 已提供 Neo4j 导入代码

**备选方案**:
- **rdflib 内存**: 开发快，但不支持持久化和并发
- **Apache Jena**: 需要 Java 环境，运维复杂
- **NebulaGraph**: 国产图数据库，但社区生态较小

### D2: 数据导入策略 → TTL + 批量导入

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

### D3: 实体链接方案 → 结巴分词 + 内存词典

**选择**: 使用结巴分词 + 内存词典匹配
**原因**:
- 已验证效果良好
- 支持自定义词典
- 轻量级，无需额外服务
- **内存占用仅 ~20MB**，远低于 Elasticsearch（1-2GB）

**流程**:
```
启动时加载实体词典到内存 (~40,000 实体, ~10MB)
    ↓
输入文本
    ↓
jieba.lcut() + 自定义词典
    ↓
内存字典匹配 (O(1) 查找)
    ↓
返回识别结果 [{label, uri, positions}]
```

**实现**:
```python
class EntityLinker:
    def __init__(self):
        # 加载所有实体到内存
        self.entity_dict = {}  # {label: {uri, subject}}
        # 加载到 jieba 词典
        for label in self.entity_dict:
            jieba.add_word(label)

    def link(self, text: str, subject: str = None):
        words = jieba.lcut(text)
        return [{"label": w, "uri": self.entity_dict[w]["uri"]}
                for w in words if w in self.entity_dict]
```

### D4: API 设计风格 → RESTful + 分层架构

**选择**: RESTful API，三层架构
**原因**:
- 与现有 LLM Gateway 风格一致
- 便于扩展和维护

**架构层次**:
```
┌─────────────────────────────────────────┐
│           API Layer (api/kg.py)          │
│  - 请求验证、响应格式化                    │
├─────────────────────────────────────────┤
│       Service Layer (core/kg/service.py) │
│  - 业务逻辑、数据组装                      │
├─────────────────────────────────────────┤
│     Data Layer (core/kg/neo4j_client.py) │
│  - Neo4j 连接、Cypher 查询                │
└─────────────────────────────────────────┘
```

### D5: 学生进度存储 → Neo4j 关系扩展

**选择**: 在 Neo4j 中增加 Student 节点和 LEARNED 关系
**原因**:
- 进度数据本质是图关系
- 便于查询学生的知识点邻居
- 避免引入额外数据库

**数据模型**:
```cypher
(Student {id: "student_001"})
  -[:LEARNED {status: "mastered", score: 95, timestamp: "2024-01-01"}]->
(Entity {uri: "edukg:math:quadratic-equation"})
```

## Architecture

### 整体架构
```
┌─────────────────────────────────────────────────────────────────┐
│                        ai-edu-ai-service                         │
├─────────────────────────────────────────────────────────────────┤
│  api/                                                            │
│  ├── chat.py          # LLM Chat API                            │
│  └── kg.py            # Knowledge Graph API (NEW)               │
├─────────────────────────────────────────────────────────────────┤
│  core/                                                           │
│  ├── gateway/         # LLM Gateway (现有)                       │
│  └── kg/              # Knowledge Graph (NEW)                   │
│      ├── neo4j_client.py    # Neo4j 连接管理                     │
│      ├── entity_linker.py   # 实体链接 (jieba + 内存词典)         │
│      ├── graph_builder.py   # 图谱构建工具                        │
│      └── service.py         # 业务服务层                          │
├─────────────────────────────────────────────────────────────────┤
│  models/                                                         │
│  ├── chat.py          # Chat 模型 (现有)                         │
│  └── kg.py            # KG 模型 (NEW)                           │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│   LLM Providers │          │       Neo4j         │
│  (智谱/DeepSeek) │          │   (独立服务器)       │
└─────────────────┘          │    │
                             └─────────────────────┘
```

### 实体链接流程（无 Elasticsearch）
```
┌─────────────────────────────────────────────────────────────────┐
│                    EntityLinker 初始化                           │
├─────────────────────────────────────────────────────────────────┤
│  1. 加载 entities/*.json 到内存 (~10MB)                          │
│  2. 构建 entity_dict = {label: {uri, subject}}                  │
│  3. 将所有 label 添加到 jieba 词典                               │
└─────────────────────────────────────────────────────────────────┘

输入文本: "一元二次方程的解法包括配方法、公式法"
    ↓
jieba.lcut() → ["一元二次方程", "的", "解法", "包括", "配方法", "、", "公式法"]
    ↓
内存字典匹配 → 命中: "一元二次方程", "配方法", "公式法"
    ↓
输出: [{label: "一元二次方程", uri: "..."}, ...]
```

### 数据模型 (Neo4j)

**节点类型**:
```cypher
// 知识点实体
(:Entity {
  uri: "http://edukg.org/knowledge/3.0/instance/math#quadratic-equation-001",
  label: "一元二次方程",
  subject: "math",
  description: "..."
})

// 学科分类
(:Class {
  uri: "http://edukg.org/knowledge/3.0/class/math#main-C10",
  label: "方程与不等式"
})

// 学生
(:Student {
  id: "student_001",
  name: "张三"
})
```

**关系类型**:
```cypher
// 知识点层级关系
(:Entity)-[:SUBCLASS_OF]->(:Entity)
(:Entity)-[:INSTANCE_OF]->(:Class)
(:Class)-[:SUBCLASS_OF]->(:Class)

// 知识点关联关系
(:Entity)-[:RELATED_TO {predicate: "prerequisite"}]->(:Entity)
(:Entity)-[:HAS_PROPERTY]->(:Property)

// 学生学习进度
(:Student)-[:LEARNED {status, score, timestamp}]->(:Entity)
```

## Risks / Trade-offs

### R1: 数据导入性能
**风险**: EDUKG 数据量大（38.6亿三元组），导入耗时
**缓解**:
- 分学科增量导入
- 先导入核心学科（数学、物理、语文）
- 已有独立 Neo4j 服务器，性能有保障

### R2: 实体链接准确率
**风险**: 结巴分词 + 词典匹配可能有误识别
**缓解**:
- 后续可引入 BERT/NER 模型提升
- 提供人工校正接口

### R3: 与向量数据库的集成
**风险**: 后续 RAG 场景需要向量数据库
**缓解**:
- 设计抽象层，便于替换实现
- 预留 `VectorStoreInterface` 接口

## Migration Plan

### 阶段一：基础设施搭建
1. ✅ 配置 Neo4j 连接（已有独立服务器）
2. 创建 `core/kg/` 模块结构
3. 实现 `neo4j_client.py` 连接管理
4. 实现 `entity_linker.py` 内存词典实体链接

### 阶段二：数据导入
1. ✅ 下载 EDUKG TTL 文件
2. 实现 TTL → Neo4j 导入脚本
3. 验证数据完整性

### 阶段三：核心功能
1. 实现实体查询 API
2. 实现实体链接服务
3. 实现知识树输出

### 阶段四：学习进度
1. 设计学生-知识点关系模型
2. 实现进度追踪 API
3. 集成测试

### 回滚策略
- Neo4j 数据通过 TTL 文件可重建
- 知识图谱模块独立，不影响现有 LLM 服务
- 可通过配置开关关闭知识图谱功能

## Open Questions

1. **EDUKG 数据下载**: Google Drive 可能需要代理，是否需要提供国内镜像？
2. **学科优先级**: 9 个学科是否全部导入？建议先导入数学、物理、语文？
3. **前端可视化**: 知识树渲染是否使用 D3.js 或 ECharts？
4. **进度同步**: 学生进度是否需要同步到 Java 后端数据库？