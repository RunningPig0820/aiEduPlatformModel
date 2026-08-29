# 数据加工流水线

> summary: 数据加工流水线
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-04-数据加工流水线.md
> 类别：操作流程

---

> 检索摘要：图谱数据加工走什么流水线、年级怎么推断、产出什么？教材→年级映射表 TEXTBOOK_TO_GRADE + 学段反向 fallback 推断年级，mark 字段兼容解析推学期；实施四阶段（清洗整合→导入Neo4j→构建前置依赖→验证优化）；产出知识点标准数据/前置依赖 CSV/Neo4j 图库，type 列必须导出。

**年级推断规则（状态：）**
- 核心：教材 → 年级映射表 TEXTBOOK_TO_GRADE。高中：必修第一/二册、必修1→(高中,高一)；必修2/3→(高中,高二)；必修4、选择性必修3→(高中,高三)；选择性必修1/2→(高中,高二)。初中：七年级上/下册→(初中,初一)，八年级上/下册→(初中,初二)，九年级上/下册→(初中,初三)。
- 学段反向推断 fallback：STAGE_FALLBACK = {"初中数学":("初中",None), "高中数学":("高中",None)}，年级需额外推断。
- 章节 → 学期推断（状态：）：从 main.ttl 的 mark 字段（如 "6.2.1" = 第6章第2节第1小节）推断，通常上学期学 1-4 章、下学期学 5-8 章，缺失时按教材序号。
- mark 字段解析兼容（状态：）：mark 格式可能不统一（"6.2.1"/"6-2-1"/"第六章第二节"/"Chapter 6.2.1"），parse_mark_field 兼容解析返回 (章节, 小节, 小节序号)；无法解析按教材序号 fallback（第1章、第2章）。

**实施步骤（状态：）**——四阶段，按学科逐个处理
- 阶段一 数据清洗与整合（从数学开始）：Step 1.1 选择学科 → 1.2 解析 ttl/math.ttl 提取知识点 → 1.3 解析 relations/math_relations.ttl 提取关系 → 1.4 匹配 split/main-math.ttl 获取教材信息 → 1.5 推断年级 → 1.6 数据验证
- 阶段二 导入 Neo4j：2.1 创建学科/学段/年级节点 → 2.2 教材/章节节点 → 2.3 知识点节点 → 2.4 分类关系(BELONGS_TO) → 2.5 关联关系(RELATED_TO)
- 阶段三 构建前置依赖：3.1 教材章节顺序生成基础依赖 → 3.2 调用 LLM 补充跨章节依赖 → 3.3 合并去重按置信度排序 → 3.4 导入 Neo4j(PREREQUISITE) → 3.5 提供人工审核接口
- 阶段四 验证与优化：4.1 抽查前置关系合理性 → 4.2 验证学习路径正确性 → 4.3 收集反馈持续优化

**数据产物（状态：）**

| 产物 | 格式 | 说明 |
|---|---|---|
| 知识点标准数据 | JSON/CSV | 整合后的知识点列表，含年级、学科、类型 |
| 前置依赖关系 | CSV | 三元组 (from, to, confidence, source) |
| 知识图谱数据库 | Neo4j | 可直接查询的图数据库 |

CSV 导出格式：knowledge_points.csv 列 uri,name,subject,stage,grade,chapter,type,description,difficulty,source；prerequisites.csv 列 from_uri,to_uri,confidence,source,reason。**注意 type 列必须导出**，便于后续按类型查询和分析。

**代码产物（状态：）**：clean_data.py（数据清洗）、import_to_neo4j.py（Neo4j 导入）、build_prerequisites.py（前置关系构建）、llm_inference.py（LLM 推理调用）。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§四 年级推断规则、§六 实施步骤、§七 预期产出）
