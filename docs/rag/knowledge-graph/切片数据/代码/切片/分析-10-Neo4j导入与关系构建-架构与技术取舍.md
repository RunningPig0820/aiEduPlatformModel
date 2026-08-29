# 分析-10-Neo4j导入与关系构建-架构与技术取舍

> summary: Neo4j导入与关系构建架构与技术取舍
> 来源: 切片 ｜ 锚点: 架构与技术取舍
> 节: 分析-10-Neo4j导入与关系构建
> COS路径: rag-slices/knowledge-graph/代码/分析-10-Neo4j导入与关系构建-架构与技术取舍.md
> 类别：架构设计
> target: 面试项目问答

---

## 架构与技术取舍

### 两段式导入（基础图谱 + 教材数据）
入库按依赖顺序分两段共 11 个脚本：先 EduKG 基础图谱（Class→Concept→Statement→RELATED_TO→PART_OF/BELONGS_TO，5 步），再人教版教材数据（Textbook→Chapter→Section→TextbookKP→IN_UNIT→MATCHES_KG，6 步）。核心约束是**节点必须先于引用它的关系**——关系引用的目标缺失时静默跳过，所以导入顺序本身就是契约。

### MERGE 幂等作为安全网（核心取舍）
所有节点/关系用 MERGE 写入：节点已存在更新属性、关系已存在跳过，全链路可重跑。失败后重导不产生重复节点/关系——这是"教研可反复点导入"的根基，也是重导安全性的来源。

### 唯一约束兜底
导入前先建 uri（部分类还建 id）唯一约束，与 MERGE 形成双保险，兜底防重。

### OPTIONAL MATCH 容错（降级策略）
关系导入用 OPTIONAL MATCH + WHERE IS NOT NULL：外部本体（Class 父类）、未匹配类型等缺失目标静默跳过、不报错——不因少量脏数据中断整批导入。

### 匹配关系只导已匹配
MATCHES_KG 关系只导 matched 且 kg_uri 非空的记录，并携带 confidence/method 属性；未匹配的 308+ 条记录跳过、只进人工审核流程，不污染图谱。

### 数据来源多样性处理
- RELATED_TO 用不带 label 的按 uri 匹配，Concept 与 Statement 均可作起终点（跨类型关系）。
- PART_OF/BELONGS_TO 从 TTL 用正则按行解析出主体/宾语，不是直接读 JSON。
- IN_UNIT 的目标 section_id 可能指向 Section 也可能指向 Chapter，用 FOREACH 分支先匹配 Section、无则落 Chapter。

### 运行模式与运维
- 每种导入脚本支持 --dry-run 预演 / --clear 先清本类再导 / --clear-only 仅清不导 / --stats 仅查库统计 / --batch-size 批量大小。
- 整库清空用 clear_neo4j（先删全部关系再删全部节点，不可恢复）；整库重建用 reimport_kg 一键按顺序重建，--skip-* 可跳步。
- 校验双查：verify_import 查 Concept 总数/v0.2 小学节点/重复 URI/无类型/版本分布；analyze_textbook_matching 算教材知识点对 Concept 的精确匹配率。

## 设计要点

- **方案 C：计算与存储分离**（语雀 D2 决策）：关系处理在 Python/JSON 完成，Neo4j 只是最后仓库；CSV/JSON 可教研维护、权威基准冻结。
- **MERGE 幂等作为安全网**：全链路可重跑，失败后重导不产生重复节点/关系。
- **OPTIONAL MATCH 容错**：外部本体、未匹配类型等缺失目标静默跳过，不因少量脏数据中断整批。
- **约束先建**：uri/id 唯一约束兜底防重，与 MERGE 双保险。
- **顺序即契约**：节点先于引用它的关系，README 明确"必须按以下顺序导入"。

> 证据：详见 `3.代码/分析-10-Neo4j导入与关系构建.md`（§代码事实 / §设计要点）｜ `4.完善文档/02-知识图谱数据入库主流程.md`
