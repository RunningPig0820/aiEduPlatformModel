# 预期产出
> summary: 数据产物三件：知识点标准数据JSON/CSV(含年级学科类型)、前置依赖CSV三元组、Neo4j图谱库，type列必须导出。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-预期产出.md
> 类别：数据存储

---

### 七、预期产出（数据产物）
> 检索摘要：数据产物三件：知识点标准数据JSON/CSV(含年级学科类型)、前置依赖CSV三元组、Neo4j图谱库，type列必须导出。

#### 7.1 数据产物
> 检索摘要：数据产物三件：知识点标准数据 JSON/CSV、前置依赖 CSV 三元组、Neo4j 图数据库，type 列必须导出。

产物	格式	说明
知识点标准数据	JSON/CSV	整合后的知识点列表，含年级、学科、类型
前置依赖关系	CSV	三元组 (from, to, confidence, source)
知识图谱数据库	Neo4j	可直接查询的图数据库

CSV 导出格式:
# 知识点标准数据 (knowledge_points.csv)
uri,name,subject,stage,grade,chapter,type,description,difficulty,source
http://edukg.org/...,一元二次方程,数学,初中,初三,一元二次方程,定义,含有一个未知数...,3,edukg

# 前置依赖关系 (prerequisites.csv)
from_uri,to_uri,confidence,source,reason
http://edukg.org/...,http://edukg.org/...,0.85,textbook_chapter,

注意: type 列必须导出，便于后续按类型查询和分析

### 7.2 代码产物
> 检索摘要：代码产物四脚本：clean_data 清洗、import_to_neo4j 导入、build_prerequisites 前置构建、llm_inference 推理调用。

代码	说明
clean_data.py	数据清洗脚本
import_to_neo4j.py	Neo4j 导入脚本
build_prerequisites.py	前置关系构建脚本
llm_inference.py	LLM 推理调用脚本

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§七、预期产出（数据产物））
