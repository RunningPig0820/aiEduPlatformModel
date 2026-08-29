# 分析-02-TTL数据拆分与Neo4jSchema-业务与流程
> summary: TTL数据拆分与Neo4jSchema业务与流程
> 来源: 切片 ｜ 锚点: 业务与流程
> 节: 分析-02-TTL数据拆分与Neo4jSchema
> COS路径: rag-slices/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema-业务与流程.md
> 类别：业务流程
> target: 面试项目问答

---

## 业务描述与业务场景

EduKG 开源知识图谱是覆盖多学科的整包数据（main.ttl 知识点约 16MB、material.ttl 教材约 3.5MB），直接整包导入慢且难按学科维护——这段管道先把 TTL 按学科拆成独立文件，再初始化 Neo4j 的唯一性约束防止重复数据，最后验证 schema 是否就绪。这是图谱入库的第一道工序。

典型业务场景：
1. 教研只想要数学学科的知识点，跑拆分脚本得到 main-math.ttl，其余学科不导入。
2. 教材数据 material.ttl 的实体 URI 不体现学科，要靠教材名称关键词识别归属，并沿"教材→章→节"传播到所有子节点。
3. 新建/重置 Neo4j 库时先建唯一约束，再验证标签与约束就绪，才批量导入。

## 职责

把 EduKG 全学科 TTL 按学科拆分为单文件，并在 Neo4j 初始化唯一性约束（防重复）与验证 schema 正确性。

**不做什么**：不做数据清洗/匹配（那是另一个主题）；不做性能索引创建（设计上延迟到数据导入后）；不导入实际数据（拆分产物 + schema 就绪后交给 kg-math-knowledge-points 导入）。

**分工要点**：本主题仅 Python 管道 4 个脚本 + 底层 Neo4j 客户端；Java/前端不参与拆分与 schema。

## 高层业务调用链（EduKG TTL 按学科拆分 → Neo4j Schema 初始化与验证）

```mermaid
flowchart TD
    A[main.ttl 16MB<br/>知识点数据] --> B[split_main_ttl<br/>按URI学科前缀分组<br/>instance/学科# 识别]
    B --> C[main-{subject}.ttl x9<br/>8学科 + unknown<br/>三元组数量验证]
    D[material.ttl 3.5MB<br/>教材数据] --> E[split_material_ttl<br/>名称关键词 + C3类型 + BFS传播<br/>P13/P2/P3 包含关系]
    E --> F[material-{subject}.ttl x10<br/>9学科 + unknown<br/>可丢弃 unknown]
    C --> G[create_neo4j_schema<br/>3 唯一约束<br/>kp_uri/subject_code/textbook_isbn]
    F --> G
    G -- 失败 continue --> G2[show_schema_info<br/>SHOW CONSTRAINTS/INDEXES]
    G2 --> H[validate_schema<br/>CALL db.labels + SHOW CONSTRAINTS<br/>6标签 + 3约束]
    H -- 全过 --> I[退出码 0<br/>可开始导入]
    H -- 缺标签/约束 --> J[退出码 1<br/>提示先跑 create_neo4j_schema]
    B -- 输入文件不存在 --> K[sys.exit 1]
    E -- 输入文件不存在 --> K
```

**文字复述**：两条数据源并行拆学科——main.ttl（知识点，约 16MB）走 `split_main_ttl`，按 URI 里的学科前缀（instance/学科#）分组，产出 8 学科 + unknown 共 9 个文件并做三元组数量验证；material.ttl（教材，约 3.5MB）走 `split_material_ttl`，因 URI 不含学科，改用名称关键词 + C3 类型识别教材实体，再沿 P13/P2/P3 三条真实包含关系 BFS 传播学科到全部子实体，产出 9 学科 + unknown 共 10 个文件。拆分产物汇入 `create_neo4j_schema` 建 3 个唯一约束（知识点 URI / 学科 code / 教材 ISBN）；建约束失败只跳过不中断。随后 `validate_schema` 用 Neo4j 元数据（标签列表 + 约束列表）核对 6 个标签 + 3 个约束：全过退出码 0 可开始导入；缺标签/约束退出码 1 提示先建 schema。输入文件不存在则直接退出码 1。

> 证据：详见 `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）｜ `4.完善文档/02-知识图谱数据入库主流程.md`
