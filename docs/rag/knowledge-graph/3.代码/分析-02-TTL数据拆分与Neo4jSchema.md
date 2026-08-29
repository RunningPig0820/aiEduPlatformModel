# 分析-02 TTL数据拆分与Neo4jSchema（代码真相）

> summary: 解答「EduKG 全学科 TTL 大数据怎么按学科拆成单文件、Neo4j 的 schema 唯一约束怎么建怎么验」——本文档是图谱入库第一道工序的代码真相:先把 EduKG 全学科 TTL 按学科拆成独立单文件,再在 Neo4j 初始化唯一性约束防重复,最后验证 schema 是否就绪;仅 Python edukg 管道 4 个脚本(edukg/scripts/kg_split/)+底层 Neo4j 客户端参与,Java/前端不参与,不做数据清洗/匹配、不建性能索引、不导入实际数据。数据背景:main.ttl 约 16MB 知识点、material.ttl 约 3.5MB 教材,整包导入慢且难按学科维护。①split_main_ttl.py 按 URI 学科前缀拆分:SUBJECT_URI_PATTERN=instance/([^/#]+)[#/](split_main_ttl.py:43)同时匹配 # 与 /(instance/math#516 与 instance/math/xxx 都归 math),未匹配归 unknown;DEFAULT_SUBJECTS 8 学科(:40),--auto-discover 遍历图自动发现学科;extract_ttl_headers 保留 @prefix/@base/PREFIX/BASE 头部行(:87-112);输出 main-{subject}.ttl+main-unknown.ttl 共 9 文件;完整性校验 Original=Written 三元组数相等打 ✓ 否则 ✗(:255-261,✗不中断照常返回 stats);产物如 main-math 14,019 triples、main-biology 20,611(kg_split/README.md:32-43)。②split_material_ttl.py 按名称关键词+关系传播拆分:material 实体 URI 不体现学科,故用 RDF 类型 C3(Textbook)识别教材实体(TEXTBOOK_CLASS_URI :62)、名称属性 P4(:65)、图片路径 P7(:68);SUBJECT_KEYWORDS 10 词→9 学科(:44-56),子串匹配按 dict 顺序先命中(生物在生物学前);PARENT_CHILD_RELATIONS 仅 P13 hasLesson/P2 hasUnit/P3 hasSection 三条真实包含关系,P5 hasImage 已移除(:70-79,注释"不是包含关系",但 README:142-144 仍写 P5 属文档与代码不一致,按代码为准);BFS propagate_subject 沿教材→章→节递归传播学科(:237-243);无归属归 unknown,--skip-unknown 丢弃;产物 10 文件(9 学科+unknown),如 material-math 6,024 triples、material-physics 8,511(README:58-70)。③create_neo4j_schema.py 只建唯一约束不含性能索引:NODE_LABELS 6 标签 Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint(:45-52);UNIQUE_CONSTRAINTS 3——kp_uri_unique(KnowledgePoint.uri)/subject_code_unique(Subject.code)/textbook_isbn_unique(Textbook.isbn)(:56-61),Cypher 用 CREATE CONSTRAINT IF NOT EXISTS...IS UNIQUE(:117-120);性能索引设计上延迟到数据导入后建,避免批量导入 10x 变慢与索引碎片化(:9,180;README:129-137);RELATIONSHIP_TYPES 10 个(如 HAS_CHAPTER/PREREQUISITE 等)仅作文档参考,Neo4j 关系类型使用时自动创建无需预定义(:64-81);--dry-run 只打印 Cypher(:175-181),单条约束失败 continue 不中断(:129-131)。④validate_schema.py 用 CALL db.labels() 取标签、SHOW CONSTRAINTS 取约束(:78-88),比对 EXPECTED_LABELS 6 与 EXPECTED_CONSTRAINTS 3(:90-139);全过退出码 0 可开始导入,缺任一/连接异常退出码 1 并提示先跑 create_neo4j_schema(:190-201);明确不验证性能索引(:9)。隐性坑与对账:--skip-validation 是死参数(:293-297 定义 argparse 但 main 未传、函数无此签名,改它没用);唯一约束基于"预期标签",若实际导入用 Concept/Statement/Class 标签(见分析-01)则标签体系不一致,需先统一口径;验证只数三元组数量不校验内容;create 用 sys.path hack 加载 edukg/config/settings(:23-33),运行环境需能 import edukg 否则 ModuleNotFoundError;输入文件不存在 sys.exit(1)(:302-304;:436-438);rdflib 未安装提示并退出(:28-32)。对账:main 按 URI 前缀/material 按名称关键词两套机制差异化落地、索引延迟 D4、3 约束与 design D5 一致、README P5 旧口径与死参数翻转(代码为准)、material 输出 10 文件。已读代码:kg_split/ 下 split_main_ttl/split_material_ttl/create_neo4j_schema/validate_schema 4 脚本+README.md、edukg/config/settings.py(NEO4J_URI/USER/PASSWORD/DATABASE :31-36)、edukg/core/neo4j/client.py(Neo4jClient 单例/execute_read)。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-source/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema.md
> 类别：操作流程

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

## 代码事实

### 端点清单（CLI）

| 命令 | 作用 | 关键参数 | 证据 |
|---|---|---|---|
| `python split_main_ttl.py` | 按学科拆分 main.ttl | --input / --output-dir / --subjects / --auto-discover / --skip-validation | split_main_ttl.py:265-328 |
| `python split_material_ttl.py` | 按学科拆分 material.ttl | --input / --output-dir / --subjects / --auto-discover / --skip-unknown | split_material_ttl.py:399-463 |
| `python create_neo4j_schema.py` | 建唯一约束 | --dry-run / --database | create_neo4j_schema.py:155-205 |
| `python validate_schema.py` | 验证 schema | --verbose / --database | validate_schema.py:164-203 |

### 关键机制：split_main_ttl（按 URI 学科前缀拆分）

1. **学科识别**：`SUBJECT_URI_PATTERN = instance/([^/#]+)[#/]` 从 URI 提取学科代码，未匹配返回 `"unknown"`（split_main_ttl.py:43,46-65）
2. **默认学科**：`DEFAULT_SUBJECTS` 8 个（biology/chemistry/chinese/geo/history/math/physics/politics）（split_main_ttl.py:40）；`--auto-discover` 从图中遍历全部 subject URI 自动发现（split_main_ttl.py:68-84,208-215）
3. **头部保留**：`extract_ttl_headers` 提取 `@prefix/@base/PREFIX/BASE` 定义行（split_main_ttl.py:87-112）
4. **写文件**：按学科建子图 RDFlib serialize 成 turtle，输出 `main-{subject}.ttl` + `main-unknown.ttl`（split_main_ttl.py:136-167,235-253）
5. **完整性验证**：`Original=总三元组数` vs `Written=写入数`，相等才打 ✓，否则 ✗（split_main_ttl.py:255-261）
6. **产物规模**（README）：main-math.ttl 14,019 triples、main-biology 20,611、main-chemistry 19,999、main-unknown 159 等 9 文件（kg_split/README.md:32-43）

### 关键机制：split_material_ttl（按名称关键词 + 关系传播拆分）

1. **学科关键词映射**：`SUBJECT_KEYWORDS` 10 词 → 9 学科代码（数学→math/物理→physics/化学→chemistry/生物→biology/历史→history/地理→geo/语文→chinese/英语→english/思想政治·政治→politics）（split_material_ttl.py:44-56）；子串匹配，按 dict 顺序先命中的 `生物` 会在 `生物学` 前
2. **实体识别**：用 RDF 类型 **C3（Textbook）** 识别教材实体（而非 URI 模式，material 实体 URI 不体现学科）；章/节/子节 C4/C5/C6 也用 P4 名称识别；图片资源 C9 用 P7 imagePath 识别（split_material_ttl.py:62-68,98-142,189-223）
3. **关系传播**：`PARENT_CHILD_RELATIONS` 仅 3 条真实包含关系——P13 hasLesson（教材→章）、P2 hasUnit（章→单元）、P3 hasSection（单元→节）；**P5 hasImage 已移除**（注释明确"不是包含关系"）（split_material_ttl.py:70-79）；BFS 递归 `propagate_subject` 把教材的学科传播到所有子实体（split_material_ttl.py:237-243）
4. **兜底**：剩余无归属实体全部标 `unknown`；`--skip-unknown` 时直接丢弃不写文件（split_material_ttl.py:248-252,347-350）
5. **产物规模**（README）：material-math.ttl 6,024 triples、material-physics 8,511、material-unknown 14 等 10 文件（kg_split/README.md:58-70）

### 关键机制：create_neo4j_schema（唯一约束，不含性能索引）

1. **节点标签**：`NODE_LABELS` 6 个（Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint）（create_neo4j_schema.py:45-52）
2. **唯一约束**：`UNIQUE_CONSTRAINTS` 3 个——
   - `kp_uri_unique`（KnowledgePoint.uri）、`subject_code_unique`（Subject.code）、`textbook_isbn_unique`（Textbook.isbn）（create_neo4j_schema.py:56-61）
   - Cypher：`CREATE CONSTRAINT IF NOT EXISTS {name} FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE`（create_neo4j_schema.py:117-120）
3. **性能索引延迟**：注释与 README 明确"性能索引延迟到数据导入后创建（design.md D4）"——先建索引再批量插入会导致导入时间 10x+ 和索引碎片化（create_neo4j_schema.py:9,180；kg_split/README.md:129-137）
4. **关系类型**：`RELATIONSHIP_TYPES` 10 个仅作文档参考，Neo4j 关系类型使用时自动创建无需预定义（create_neo4j_schema.py:64-81）
5. **容错**：单个约束创建失败只 `continue` 记录错误，不中断整体（create_neo4j_schema.py:129-131）；`--dry-run` 只打印 Cypher 不执行（create_neo4j_schema.py:175-181）

### 关键机制：validate_schema（验证标签与约束）

1. 用 `CALL db.labels()` 取现有标签、`SHOW CONSTRAINTS` 取约束（validate_schema.py:78-88）
2. 比对 `EXPECTED_LABELS`（6）与 `EXPECTED_CONSTRAINTS`（3），缺任一标记 missing（validate_schema.py:90-139）
3. 全过 → 退出码 0；缺 → 退出码 1 并提示"请先运行 create_neo4j_schema.py"（validate_schema.py:190-197）；连接异常 → 退出码 1（validate_schema.py:199-201）
4. 明确"不验证性能索引"（validate_schema.py:9）

### 枚举/常量/配置

| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 默认学科 | DEFAULT_SUBJECTS | biology/chemistry/chinese/geo/history/math/physics/politics（8） | split_main_ttl.py:40 |
| URI 学科正则 | SUBJECT_URI_PATTERN | `instance/([^/#]+)[#/]` | split_main_ttl.py:43 |
| 学科关键词 | SUBJECT_KEYWORDS | 数学→math/物理→physics/化学→chemistry/生物·生物学→biology/历史→history/地理→geo/语文→chinese/英语→english/思想政治·政治→politics（10 词） | split_material_ttl.py:44-56 |
| 教材类型 URI | TEXTBOOK_CLASS_URI | `.../3.0/ontology/class/resource#C3` | split_material_ttl.py:62 |
| 名称属性 URI | NAME_PROPERTY_URI | `.../data_property/resource#P4` | split_material_ttl.py:65 |
| 图片路径属性 URI | IMAGE_PATH_PROPERTY_URI | `.../data_property/resource#P7` | split_material_ttl.py:68 |
| 包含关系 | PARENT_CHILD_RELATIONS | P13(hasLesson)/P2(hasUnit)/P3(hasSection)；P5 已移除 | split_material_ttl.py:70-79 |
| 节点标签 | NODE_LABELS | Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint（6） | create_neo4j_schema.py:45-52 |
| 唯一约束 | UNIQUE_CONSTRAINTS | kp_uri_unique(KnowledgePoint.uri)/subject_code_unique(Subject.code)/textbook_isbn_unique(Textbook.isbn) | create_neo4j_schema.py:56-61 |
| 关系类型 | RELATIONSHIP_TYPES | HAS_STAGE/HAS_GRADE/USE_TEXTBOOK/HAS_CHAPTER/HAS_KNOWLEDGE_POINT/PREREQUISITE/TEACHES_BEFORE/PREREQUISITE_ON/PREREQUISITE_CANDIDATE/RELATED_TO/SUB_CATEGORY（10） | create_neo4j_schema.py:66-81 |
| Neo4j 连接 | NEO4J_URI/USER/PASSWORD/DATABASE | bolt://localhost:7687 / neo4j / (env) / neo4j | edukg/config/settings.py:31-36 |
| 三元组量级 | main.ttl / material.ttl | 约 16MB / 3.5MB | kg_split/README.md:9-10 |

### 边界与降级

- 输入文件不存在 → 日志报错 + `sys.exit(1)`（split_main_ttl.py:302-304；split_material_ttl.py:436-438）
- rdflib 未安装 → split_material_ttl 提示安装并退出（split_material_ttl.py:28-32）
- 拆分后三元组数量不等 → 打 ✗ 但**不中断**，照常返回 stats（split_main_ttl.py:260）
- material 中无名称的实体（如 C9 图片无 P7）→ 归 unknown；`--skip-unknown` 可跳过（split_material_ttl.py:348-350）
- 约束创建失败 → 记录错误 continue（create_neo4j_schema.py:129-131）
- Neo4j 连接失败 → create/validate 主流程 catch Exception → `sys.exit(1)`（create_neo4j_schema.py:201-203；validate_schema.py:199-201）

## 隐性坑与注意事项

- **`split_main_ttl.py` 的 `--skip-validation` 是死参数**：main 里定义了 argparse 参数（split_main_ttl.py:293-297），但 `split_ttl_by_subject` 函数签名没有该参数、main 调用时也没传——传了这个 flag 不生效，验证始终执行。改它没用。
- **material 学科靠名称子串匹配，顺序敏感**：`生物` 在 `生物学` 前、`政治` 在 `思想政治` 前（dict 顺序），靠关键字命中；教材名含"化学"却被"生物学"先命中不会发生（不同关键词），但名含多个学科词时以 dict 顺序先者为准。
- **BFS 传播依赖 P13/P2/P3 三条边**：如果原始 TTL 用其他属性（如 P5）表达层级，那些子节点会漏传播落到 unknown——代码已主动移除 P5（split_material_ttl.py:74），但 **kg_split/README.md:142-144 仍写"章节实体通过 P13/P2/P3/P5 关系连接""子章节通过 P5 关系连接"**，文档与代码不一致，按代码为准。
- **split_main_ttl 的学科正则同时匹配 `#` 和 `/`**：`instance/math#516` 与 `instance/math/xxx` 都归 math（split_main_ttl.py:43）。
- **验证只数三元组数量，不校验内容**：数量相等即 ✓，语义/URI 是否干净不在此阶段把关。
- **schema 只建约束不建索引**：导入前若大量查询性能慢，是预期内（设计决策）；索引要在数据导入后的 `kg-math-knowledge-points` change 里建（kg_split/README.md:129-137）。
- **3 个唯一约束基于"预期标签"**：若实际导入用 `Concept`/`Statement`/`Class` 等标签（分析-01 核对 import 脚本），`NODE_LABELS`/`EXPECTED_LABELS` 里的 `KnowledgePoint`/`Subject`/`Textbook` 等标签与教材导入数据的标签体系**不一致**——约束防的是"按本 schema 命名"的数据重复，跨命名需先统一标签口径。
- **create_neo4j_schema.py 通过 sys.path hack 加载配置**：把 ai-edu-ai-service 加入 sys.path 读 edukg/config/settings（create_neo4j_schema.py:23-33），运行环境需能 import `edukg` 与 `config.settings`，否则报 ModuleNotFoundError。

## 设计要点

- **性能索引延迟创建**：先建唯一约束（防重复）→ 批量导入 → 后建性能索引，避免批量导入 10x 变慢与索引碎片化（create_neo4j_schema.py:9；kg_split/README.md:129-137）。
- **material 用 RDF 类型而非 URI 模式识别学科**：main.ttl 实体 URI 含学科前缀可直接正则，material.ttl 实体 URI 不体现学科，故改用 C3 类型 + P4 名称关键词 + 关系传播（split_material_ttl.py:8-12,164-173）。
- **关系传播 BFS 化**：只沿真实包含关系（P13/P2/P3）递归传播，保证"教材→章→节→子节"全链路学科一致（split_material_ttl.py:237-243）。
- **不验证不阻断**：拆分三元组数量校验仅告警；约束创建失败单条 continue——拆分/schema 工序让"数据质量门禁"更靠后的导入/校验阶段把关。
- **dry-run 友好**：create_neo4j_schema 支持 `--dry-run` 只打印 Cypher，validate 支持 `--verbose`，便于 CI 前预览。

## 对账要点

| 对账分类 | 项 | 语雀/design 口径 | 代码现状 | 结论 |
|---|---|---|---|---|
| 方案vs实现 | 拆分方式 | 方案称按学科拆分 | main 按 URI 前缀、material 按名称关键词+BFS 传播，两套机制不同 | 落地（分脚本差异化实现） |
| 方案vs实现 | 索引延迟 | design.md D4 性能索引延迟到导入后 | 代码注释+README 明确，create 只建约束 | 落地 |
| 方案vs实现 | 唯一约束 | design.md D5 3 个约束 | kp_uri/subject_code/textbook_isbn 三约束一致 | 落地 |
| 文档vs代码 | material 传播边 | kg_split/README.md:142-144 称"通过 P13/P2/P3/P5 关系连接""通过 P5 关系连接" | 代码 PARENT_CHILD_RELATIONS 已移除 P5（注释"P5 是 hasImage，不是包含关系"） | 翻转（README 旧口径，代码为准） |
| 注释vs运行行为 | split_main 的 --skip-validation | 参数注释"跳过三元组数量验证" | 参数定义了但 main 未传、函数无此签名，不生效 | 翻转（死参数） |
| 方案vs实现 | material 输出文件数 | README 列 10 个 | 9 学科+unknown=10 个 | 落地 |

## 已读代码清单

- **Python 管道（edukg）**：`edukg/scripts/kg_split/split_main_ttl.py`（extract_subject_from_uri/split_ttl_by_subject/write_subject_ttl/校验）、`split_material_ttl.py`（SUBJECT_KEYWORDS/build_entity_graph/propagate_subject/split_ttl_by_subject）、`create_neo4j_schema.py`（NODE_LABELS/UNIQUE_CONSTRAINTS/create_constraints/dry-run）、`validate_schema.py`（EXPECTED_LABELS/EXPECTED_CONSTRAINTS/validate/退出码）
- **Python（配置/客户端）**：`edukg/config/settings.py`（NEO4J_*）、`edukg/core/neo4j/client.py`（Neo4jClient 单例/execute_read）
- **数据说明**：`edukg/scripts/kg_split/README.md`（产物规模/设计决策/环境变量）
> 本主题跨 1 端（Python edukg 管道）；仅 Python 端有实际读取。Java/前端不参与 TTL 拆分与 schema，未读。
