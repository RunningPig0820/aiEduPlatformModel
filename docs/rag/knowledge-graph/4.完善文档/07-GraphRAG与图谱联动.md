# 07 GraphRAG 与图谱联动
> summary: 解答「图谱和向量怎么配合(GraphRAG)、AI 答疑知识点怎么点亮、与掌握度/题型分析怎么联动」——向量命中 Concept → 沿 PREREQUISITE/RELATED_TO 扩展邻居 → 可解释推理路径；落地真相最大翻转=主答疑链路未真接图扩展(向量索引+前置依赖入库真实, 邻居扩展/点亮属设计口径或 Java 侧不可核验), 点亮只读零写入, 在线查询 :Entity 标签坑
> 权威度: 1.0
> 模块: knowledge-graph
> COS路径: rag-source/knowledge-graph/完善文档/07-GraphRAG与图谱联动.md
> 类别：数据关联

## 为什么（语雀）

图谱不能只是"数据做了放着"——学生答疑时要先定位"这个题考哪个知识点"，再沿前置链诊断"是当前点没掌握还是前置没学好"，这需要 **向量做语义召回（哪个概念最像）+ 图谱做关系推理（它依赖谁/谁依赖它）** 两者配合，这正是 GraphRAG 的动机。早期方案曾把图谱定位成存储/浏览，已演进为"消费侧 GraphRAG + 掌握度点亮 + 页面化"的业务闭环（见下）。

## 怎么设计（方案）

**（方案口径，已演进）** 早期：图谱只建库、页面浏览，答疑/掌握度与图谱割裂。已演进为**图谱作为 AI 助手的"活文档"**：GraphRAG 引导答疑 + 掌握度薄弱诊断 + 题型分析联动 + 知识点点亮，核心约束是"权威图谱零写入"。

### GraphRAG 工作流

```
学生提问 → 提取核心知识点 → Neo4j 查前置依赖/考法/例题
  → 「前置知识点回顾 → 考点讲解 → 解题步骤引导 → 易错点提醒」引导式答疑
  Cypher 用 [:前置依赖*1..2] 控制链路深度、collect(DISTINCT pre) 去重
```

- **图谱和向量怎么配合**：向量命中 Concept（或经 MATCHES_KG 命中教材知识点）→ **沿 PREREQUISITE/RELATED_TO 扩展邻居** → 形成可解释推理路径。文字链路：先向量检索把自由文本题型名（"分数除法"）映射到图谱节点，再沿图关系往外扩一到两跳拿到前置依赖链，这条链就是答疑"前置回顾"与缺陷诊断的依据——向量负责"召回"、图谱负责"解释"。
- **与掌握度联动**：错题 → 对应知识点 → 前置链 → 结合正确率/答题次数算掌握度 → 定位薄弱根源（当前点没掌握 vs 前置没学好）。
- **与题型分析联动**：题目"考察"知识点关系支撑 AI 组卷（按知识点全覆盖/难度梯度/题型占比）。
- **知识点点亮（kp-matching-lightup）**：掌握度主体从知识点翻转为题型，派生层 3 表只存 MySQL；权威图谱只读，解析管线最终 kp **必经镜像校验**（SHALL NOT 凭空生成镜像不存在的 kp）；点亮是"只读借 kp_uri 借权威结构"，零写入。
- **边界（Non-Goal 演进口径）**：复杂关系可视化、Neo4j 实时查询、前端页面（本期走方案 B：Neo4j→MySQL 同步、前端读 MySQL）均属方案边界，不是已实现能力。

## 落地真相（代码）

> ⚠️ **最大翻转（GraphRAG 落地范围）**：方案口径"向量命中 Concept → 沿 PREREQUISITE/RELATED_TO 扩展邻居 → 可解释路径"在**主答疑链路未真接图遍历**——本仓可核验的落地是"向量索引（bge 512 / dashscope 768）+ 前置依赖 PREREQUISITE 入库 + Python 桥桩接口"；"邻居扩展/可解释路径"在 Python 桥是**简化桩**（`get_learning_path` 只返回目标实体自身一项），点亮/掌握度联动属 Java 侧（kp-matching-lightup，本仓不可核验，如实标注设计口径）。

- **✅落地：向量命中能力**。匹配侧 bge-small-zh-v1.5 本地 512 维建 `kg_vectors.npy`（1295×512）+ checksum 校验；服务侧 dashscope text-embedding-v3 768 维写 COS 向量桶（topic/RAG 双池，put 后约 10s 异步生效）——"向量召回"能力是真实代码（`3.代码/分析-09`）。
- **✅落地：前置依赖/语义关系已入库**。PREREQUISITE（双模型投票一致且 ≥0.8 才落正式，<0.8 落 PREREQUISITE_CANDIDATE）、RELATED_TO（Concept/Statement 语义关联）均由 import 脚本 MERGE 导入 Neo4j，是学习路径/缺陷诊断的数据基础（`3.代码/分析-08`、`分析-10`）。注意：三来源融合 `fuse_results` 方法存在但**未接入主链路**，当前前置依赖实际是 LLM 单路径 + 0.8 分界（`分析-08`）。
- **⚠️ 翻转：邻居扩展在 Python 桥是简化桩**。`get_knowledge_tree` 取前 100 实体平铺两层、`get_learning_path` 只返回目标实体自身一项、`get_recommendations` 只看一跳邻居——不是方案说的"沿 PREREQUISITE 多跳扩展"；页面化真层级走 Java 同步 MySQL 侧（`3.代码/分析-01`）。
- **⚠️ 翻转：答疑主链路未真接图扩展**。`core/rag/query.py` 是 **AI 答疑 RAG 检索编排**，检索的是图谱**文档切片**（语料池），不是 Neo4j 节点数据——答疑的"图谱联动"目前以语料召回实现，Cypher 图遍历能力以 `api/neo4j.py` 裸 `/query` 接口提供给 Java 侧，主链路是否调用不在本仓（`3.代码/分析-01`）。
- **⚠️ 翻转：点亮只读、不从图谱写回业务**。权威图谱零写入落地：Python 侧不做业务派生数据持久化（掌握度/点亮存 MySQL）；解析管线最终 kp 必经镜像校验、LLM 只生成候选名不直接造 kp——点亮是"借结构只读"，任何写回业务的操作在权威图侧都不存在（`1.语雀/语雀-决策记录.md D17`；`2.OpenSpec design 决策/design-backend-kp-matching-lightup.md D1/D2/D21`）。
- **⚠️ 翻转：在线查询 `:Entity` 标签坑（J-KG10 关联）**。`api/kg.py` 依赖的 `core/kg/service.py` 全部 `MATCH (e:Entity {...})`（service.py:101-109, 180-185），而离线导入用具体标签（Textbook/Chapter/Section/TextbookKP/Concept/Statement/Class）——**在线查询可能查不到离线导入的节点**，是真实运维坑（`3.代码/分析-01` 隐性坑；`方案-代码对账 #1`）。

## 追问与防御

**预期追问：路径为什么能解释？**
→ **回答要点**：因为路径由**前置依赖关系**构成，不是黑盒相似度。PREREQUISITE 带置信度（≥0.8 才落正式、<0.8 落候选），双模型投票每对还带 reason（primary/secondary_reason）可回溯；"分数除法学不懂 → 前置分数乘法/倒数"就是沿关系往回找，解释依据是"前置知识点"的关系语义。

**预期追问：图谱是不是只是展示？**
→ **回答要点**：不是，但分层要如实。本仓可核验的真实落地是向量索引 + 前置依赖入库 + Python 桥接口；答疑点亮、掌握度薄弱诊断、学习路径消费在 Java 侧（kp-matching-lightup 设计，本仓无 Java 代码）；页面化只是图谱消费面之一，不是全部。

**预期追问：GraphRAG 可解释性从哪来？**
→ **回答要点**：向量粗召回 + 图谱精推理两段式。向量把"鸡兔同笼"这类教学题型名映射到 Concept/TextbookKP（匹配侧 bge 512 / 服务侧 dashscope 768），图谱再沿 PREREQUISITE/RELATED_TO 扩展邻居给出依赖链；可解释性来自"前置知识点是依据"的关系扩展，而非单纯的向量相似度排序。

**预期追问：图谱和向量怎么配合？**
→ **回答要点**：离线匹配阶段是"向量粗筛 top-20 → 双模型投票"（把 1905 教材知识点匹配进 Concept，率 ~97%）；在线消费阶段是"向量命中 Concept → 沿关系扩展邻居"。两套 embedding 各司其职：匹配侧本地 bge 512 维做离线粗筛，服务侧 dashscope 768 维做 RAG 检索，索引维度固定不可混用。

## 证据引用

- GraphRAG 工作流/与掌握度、题型分析联动：`1.语雀/语雀-方案总揽.md（§3.3 消费侧、§10 服务接入）`
- 权威图谱零写入（点亮只读的依据）：`1.语雀/语雀-决策记录.md（D17）`
- 前置依赖构建与"教学顺序≠学习依赖"：`1.语雀/语雀-方案总揽.md（§8）` + `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md（D2/D7）`
- 双 embedding/向量索引方案：`1.语雀/语雀-决策记录.md（D5）` + `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md（D4.3 向量检索选型）`
- 点亮派生层/零写入/解析管线镜像校验：`2.OpenSpec design 决策/design-backend-kp-matching-lightup.md（D1/D2/D21）`
- Non-Goal 边界（复杂关系可视化/Neo4j 实时查询）：`2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md（Non-Goals）`
- 落地真相（整体链路/简化桩/Entity 标签坑/rag 定位）：`3.代码/分析-01-知识图谱整体架构与数据链路.md`
- 落地真相（前置依赖入库范围/融合未接入）：`3.代码/分析-08-前置依赖推断.md`
- 落地真相（向量索引/checksum/双 embedding）：`3.代码/分析-09-向量索引构建与校验.md`
- 落地真相（RELATED_TO 等关系导入）：`3.代码/分析-10-Neo4j导入与关系构建.md`
- 落地真相（Java/前端不在本仓、graph 接口未实现）：`3.代码/分析-11-Java同步与前端页面.md`
- 翻转口径校准（Entity 标签坑/rag 定位）：`方案-代码对账.md（#1/#2）`
