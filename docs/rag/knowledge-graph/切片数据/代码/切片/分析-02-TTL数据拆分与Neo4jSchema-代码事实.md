# 分析-02-TTL数据拆分与Neo4jSchema-代码事实
> summary: TTL数据拆分与Neo4jSchema代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-02-TTL数据拆分与Neo4jSchema
> COS路径: rag-slices/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema-代码事实.md
> 类别：架构设计
> target: 开发对账

---

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

> 证据：详见 `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`（§代码事实）
