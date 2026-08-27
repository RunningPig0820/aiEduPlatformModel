# 分析-02-TTL数据拆分与Neo4jSchema-业务链路
> summary: TTL数据拆分与Neo4jSchema业务链路
> 来源: 切片 ｜ 锚点: 业务链路
> 节: 分析-02-TTL数据拆分与Neo4jSchema
> COS路径: rag-slices/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema-业务链路.md
> 类别：业务流程
> target: 开发对账

---

## 业务描述与业务场景

**业务描述**：EduKG 开源知识图谱是覆盖多学科的整包数据（main.ttl 知识点约 16MB、material.ttl 教材约 3.5MB），直接整包导入慢且难按学科维护——这段管道先按学科把 TTL 拆成独立文件，再初始化 Neo4j 的唯一性约束防止重复数据，最后验证 schema 是否就绪，是图谱入库的第一道工序。

**业务场景**：
- 教研只想要数学学科的知识点，跑 `split_main_ttl.py` 得到 `main-math.ttl`，其余学科不导入
- 教材数据 material.ttl 的实体 URI 不体现学科，要靠教材名称关键词识别归属并沿"教材→章→节"传播到所有子节点
- 新建/重置 Neo4j 库时跑 `create_neo4j_schema.py` 建唯一约束，再跑 `validate_schema.py` 确认标签与约束就绪才批量导入

## 职责

**职责**：把 EduKG 全学科 TTL 按学科拆分为单文件，并在 Neo4j 初始化唯一性约束（防重复）与验证 schema 正确性。
**不做什么**：不做数据清洗/匹配（那是 kg_data/textbook 主题）；不做性能索引创建（设计上延迟到数据导入后）；不导入实际数据（拆分产物 + schema 就绪后由 kg-math-knowledge-points 导入）。
**分工要点**：本主题仅 Python 管道（`edukg/scripts/kg_split/`）4 个脚本 + 底层 Neo4j 客户端；Java/前端不参与拆分与 schema。

## 高层业务调用链（EduKG TTL 按学科拆分 → Neo4j Schema 初始化与验证）

```mermaid
flowchart TD
    A[main.ttl 16MB<br/>知识点数据] --> B[split_main_ttl.py<br/>按URI学科前缀分组<br/>SUBJECT_URI_PATTERN instance/xxx#]
    B --> C[main-{subject}.ttl x9<br/>8学科 + unknown<br/>三元组数量验证]
    D[material.ttl 3.5MB<br/>教材数据] --> E[split_material_ttl.py<br/>P4名称关键词 + C3类型 + BFS传播<br/>P13/P2/P3 包含关系]
    E --> F[material-{subject}.ttl x10<br/>9学科 + unknown<br/>--skip-unknown 可丢弃]
    C --> G[create_neo4j_schema.py<br/>3 唯一约束<br/>kp_uri/subject_code/textbook_isbn]
    F --> G
    G -- 失败 continue --> G2[show_schema_info<br/>SHOW CONSTRAINTS/INDEXES]
    G2 --> H[validate_schema.py<br/>CALL db.labels + SHOW CONSTRAINTS<br/>6标签 + 3约束]
    H -- 全过 --> I[退出码 0<br/>可开始导入]
    H -- 缺标签/约束 --> J[退出码 1<br/>提示先跑 create_neo4j_schema]
    B -- 输入文件不存在 --> K[sys.exit 1]
    E -- 输入文件不存在 --> K
```
> 节点均可对应代码：B=`split_main_ttl.py:43,170-262`；E=`split_material_ttl.py:164-261,290-396`；G=`create_neo4j_schema.py:105-135`；H=`validate_schema.py:90-139,164-197`；K=`split_main_ttl.py:302-304`。

> 证据：详见 `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）
