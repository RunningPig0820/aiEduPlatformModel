# 分析-02-TTL数据拆分与Neo4jSchema-坑与对账
> summary: TTL数据拆分与Neo4jSchema坑与对账
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-02-TTL数据拆分与Neo4jSchema
> COS路径: rag-slices/knowledge-graph/代码/分析-02-TTL数据拆分与Neo4jSchema-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

## 隐性坑与注意事项

- **`split_main_ttl.py` 的 `--skip-validation` 是死参数**：main 里定义了 argparse 参数（split_main_ttl.py:293-297），但 `split_ttl_by_subject` 函数签名没有该参数、main 调用时也没传——传了这个 flag 不生效，验证始终执行。改它没用。
- **material 学科靠名称子串匹配，顺序敏感**：`生物` 在 `生物学` 前、`政治` 在 `思想政治` 前（dict 顺序），靠关键字命中；教材名含"化学"却被"生物学"先命中不会发生（不同关键词），但名含多个学科词时以 dict 顺序先者为准。
- **BFS 传播依赖 P13/P2/P3 三条边**：如果原始 TTL 用其他属性（如 P5）表达层级，那些子节点会漏传播落到 unknown——代码已主动移除 P5（split_material_ttl.py:74），但 **kg_split/README.md:142-144 仍写"章节实体通过 P13/P2/P3/P5 关系连接""子章节通过 P5 关系连接"**，文档与代码不一致，按代码为准。
- **split_main_ttl 的学科正则同时匹配 `#` 和 `/`**：`instance/math#516` 与 `instance/math/xxx` 都归 math（split_main_ttl.py:43）。
- **验证只数三元组数量，不校验内容**：数量相等即 ✓，语义/URI 是否干净不在此阶段把关。
- **schema 只建约束不建索引**：导入前若大量查询性能慢，是预期内（设计决策）；索引要在数据导入后的 `kg-math-knowledge-points` change 里建（kg_split/README.md:129-137）。
- **3 个唯一约束基于"预期标签"**：若实际导入用 `Concept`/`Statement`/`Class` 等标签（分析-01 核对 import 脚本），`NODE_LABELS`/`EXPECTED_LABELS` 里的 `KnowledgePoint`/`Subject`/`Textbook` 等标签与教材导入数据的标签体系**不一致**——约束防的是"按本 schema 命名"的数据重复，跨命名需先统一标签口径。
- **create_neo4j_schema.py 通过 sys.path hack 加载配置**：把 ai-edu-ai-service 加入 sys.path 读 edukg/config/settings（create_neo4j_schema.py:23-33），运行环境需能 import `edukg` 与 `config.settings`，否则报 ModuleNotFoundError。

## 对账复盘（原始方案 → 实际落地 → 业务影响）

**拆分方式 ✅落地（分脚本差异化实现）**：语雀/design 口径称"按学科拆分"；实际落地 main 按 URI 前缀、material 按名称关键词+BFS 传播，两套机制不同。影响：两个数据源 URI 结构差异大（main 含学科前缀、material 不含），分脚本差异化实现才能各自正确按学科拆出单文件。

**索引延迟 ✅落地**：design.md D4 要求性能索引延迟到导入后；代码注释+README 明确，create_neo4j_schema 只建唯一约束不建性能索引。影响：避免批量导入 10x 变慢与索引碎片化。

**唯一约束 ✅落地**：design.md D5 要求 3 个约束；实际落地 `kp_uri_unique`/`subject_code_unique`/`textbook_isbn_unique` 三约束与方案一致。影响：三个核心实体（知识点/学科/教材）各自唯一，防重复数据。

**material 传播边 ⚠️翻转（README 旧口径，代码为准）**：kg_split/README.md:142-144 称"章节实体通过 P13/P2/P3/P5 关系连接""子章节通过 P5 关系连接"；实际代码 `PARENT_CHILD_RELATIONS` 已移除 P5（注释明确"P5 是 hasImage，不是包含关系"）。影响：若按 README 用 P5 传播会错误地把图片关系当层级包含，导致子节点漏传播落到 unknown——排查 unknown 归属时以代码为准。

**split_main 的 `--skip-validation` ⚠️翻转（死参数）**：参数注释称"跳过三元组数量验证"；实际参数在 argparse 定义了但 main 未传、函数签名无此参数，传了不生效。影响：传这个 flag 验证仍会执行，想跳过校验不可行，改它没用。

**material 输出文件数 ✅落地**：README 列 10 个；实际落地 9 学科+unknown=10 个文件，一致。

> 证据：详见 `3.代码/分析-02-TTL数据拆分与Neo4jSchema.md`（§隐性坑与注意事项 / §对账要点）
