# 知识图谱数据整理方案设计

## 一、目标

将现有数据整理成支持 AI 作业答疑业务的知识图谱：
- 按学科、年级组织知识点
- 建立知识点前置/后置依赖关系
- 支持学习路径推荐和知识缺陷诊断

---

## 二、数据模型设计

### 2.1 知识点层级结构

```
学科 (Subject)
  └── 学段 (Stage: 小学/初中/高中)
        └── 年级 (Grade)
              └── 教材 (Textbook)
                    └── 章节 (Chapter)
                          └── 知识点 (KnowledgePoint)
```

### 2.2 Neo4j 节点模型

```cypher
// 学科节点
(:Subject {name: "数学", code: "math"})

// 学段节点
(:Stage {name: "高中", code: "high_school"})

// 年级节点
(:Grade {name: "高一", code: "g10", order: 1})

// 教材节点
(:Textbook {
  name: "高中数学必修第一册",
  isbn: "9787107336270",
  subject: "math",
  grade: "g10"
})

// 章节节点
(:Chapter {
  name: "集合与函数概念",
  order: 1,
  textbook_isbn: "9787107336270"
})

// 知识点节点 (核心)
(:KnowledgePoint {
  uri: "http://edukg.org/knowledge/0.1/instance/math#516",
  name: "一元二次方程",
  subject: "math",
  stage: "初中",
  grade: "初三",          // 推断或标注
  chapter: "一元二次方程",
  type: "定义",           // 定义/性质/定理/公式
  difficulty: 3,          // 1-5 难度等级
  source: "edukg"         // 数据来源
})
```

### 2.3 关系模型（区分教学顺序与学习依赖）

```cypher
// ========== 层级关系 ==========
(:Subject)-[:HAS_STAGE]->(:Stage)
(:Stage)-[:HAS_GRADE]->(:Grade)
(:Grade)-[:USE_TEXTBOOK]->(:Textbook)
(:Textbook)-[:HAS_CHAPTER]->(:Chapter)
(:Chapter)-[:CONTAINS]->(:KnowledgePoint)

// ========== 分类关系 ==========
(:KnowledgePoint)-[:BELONGS_TO]->(:Category)
(:KnowledgePoint)-[:SUB_CATEGORY]->(:KnowledgePoint)

// ========== 教学顺序（教材安排顺序，不是学习依赖）==========
(:KnowledgePoint)-[:TEACHES_BEFORE {
  confidence: 0.85,
  source: "textbook_chapter",
  evidence: ["chapter_order"]
}]->(:KnowledgePoint)

// ========== 核心前置关系（真正的学习依赖）==========
// 业务查询用 PREREQUISITE，EduKG 标准用 先修于
(:KnowledgePoint)-[:PREREQUISITE {
  confidence: 0.85,
  source: "llm",           // llm/definition_extraction/teacher
  evidence_types: ["definition_dependency", "llm_inference"],
  verified: false,
  standard_relation: "先修于"
}]->(:KnowledgePoint)

// EduKG 标准关系（便于互操作）
(:KnowledgePoint)-[:先修_on {
  confidence: 0.85,
  source: "llm"
}]->(:KnowledgePoint)

// ========== 候选前置关系（待验证，低置信度）==========
(:KnowledgePoint)-[:PREREQUISITE_CANDIDATE {
  confidence: 0.65,
  source: "llm_zero_shot",
  evidence_types: ["llm_inference"],
  status: "candidate"
}]->(:KnowledgePoint)

// ========== 知识点关联（TTL 原生 relateTo 数据）==========
(:KnowledgePoint)-[:RELATED_TO {
  source: "edukg_relateTo"
}]->(:KnowledgePoint)
```

**设计说明**：
- **TEACHES_BEFORE**：教材教学顺序，不等于学习依赖。如"勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理。
- **PREREQUISITE**：真正的学习依赖（不学A就学不懂B），由定义依赖抽取 + LLM 多模型投票生成。
- **PREREQUISITE_CANDIDATE**：低置信度候选关系，待后续验证。
- **先修_on**：EduKG 标准关系，方便未来互操作。

---

## 三、数据来源与整合策略

### 3.1 数据源分析

| 数据源 | 版本 | 内容 | 用途 |
|--------|------|------|------|
| **ttl/*.ttl** | v0.1 | 知识点实例 | ✅ 主要数据源 |
| **relations/*.ttl** | v0.1 | 知识点关系 | ✅ 关联/分类关系 |
| **main.ttl** | v3.0 | 教材出处 | ⚠️ 年级/教材信息 |
| **entities/*.json** | v0.1 | 实体列表 | ✅ 实体链接 |
| **好未来数据** | - | 小学数学 | 📖 层级参考 |

### 3.2 整合策略

```
Step 1: 以 ttl/*.ttl 为主数据源
        ↓
Step 2: 通过标签匹配 main.ttl 获取教材信息
        ↓
Step 3: 从教材信息推断年级
        ↓
Step 4: 导入 relations/*.ttl 的关联关系
        ↓
Step 5: 构建 PREREQUISITE 关系
```

---

## 四、年级推断规则

### 4.1 教材 → 年级映射

```python
TEXTBOOK_TO_GRADE = {
    # 高中
    "必修第一册": ("高中", "高一"),
    "必修第二册": ("高中", "高一"),
    "必修1": ("高中", "高一"),
    "必修2": ("高中", "高二"),
    "必修3": ("高中", "高二"),
    "必修4": ("高中", "高三"),
    "选择性必修1": ("高中", "高二"),
    "选择性必修2": ("高中", "高二"),
    "选择性必修3": ("高中", "高三"),

    # 初中
    "七年级上册": ("初中", "初一"),
    "七年级下册": ("初中", "初一"),
    "八年级上册": ("初中", "初二"),
    "八年级下册": ("初中", "初二"),
    "九年级上册": ("初中", "初三"),
    "九年级下册": ("初中", "初三"),
}

# 学段反向推断（fallback）
STAGE_FALLBACK = {
    "初中数学": ("初中", None),  # 年级需额外推断
    "高中数学": ("高中", None),
}
```

### 4.2 章节 → 学期推断

```python
# 从 main.ttl 的 mark 字段推断
# mark: "6.2.1" 表示 第6章 第2节 第1小节
# 通常上学期学1-4章，下学期学5-8章
```

---

## 五、前置依赖关系构建方案（多证据融合）

### 5.1 核心原则

**教学顺序 ≠ 学习依赖**

教材章节顺序是教学安排顺序，不一定等于学习依赖顺序。
- 例如："勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理
- 因此：教材顺序存为 TEACHES_BEFORE，真正的学习依赖存为 PREREQUISITE

### 5.2 证据来源分类

| 证据类型 | 说明 | 基础权重 | Demo 阶段策略 |
|---------|------|---------|--------------|
| **教材章节顺序** | 同章节内按 mark 顺序 | 0.7 | → TEACHES_BEFORE |
| **定义/定理依赖** | 从定义文本中抽取的关键概念 | 0.85 | → PREREQUISITE（实现） |
| **LLM 多模型投票** | GLM + DeepSeek 两模型一致 | 0.8 | → PREREQUISITE/CANDIDATE |
| **教师标注** | 人工审核 | 1.0 | Demo 阶段不做 |

### 5.3 教材章节顺序（仅生成 TEACHES_BEFORE）

**仅生成同章节内的 TEACHES_BEFORE 关系**，不直接转化为 PREREQUISITE。

```python
def infer_teaches_before(knowledge_points):
    """
    按教材和章节分组，按 mark 顺序生成 TEACHES_BEFORE 关系
    注意：这是教学顺序，不是学习依赖
    """
    teaches_before = []
    for textbook, kps in group_by_textbook(knowledge_points):
        sorted_kps = sort_by_chapter_and_mark(kps)
        for i in range(1, len(sorted_kps)):
            prev = sorted_kps[i-1]
            curr = sorted_kps[i]
            if prev.chapter == curr.chapter:  # 仅同章节
                teaches_before.append({
                    'from': prev.uri,
                    'to': curr.uri,
                    'confidence': 0.85,
                    'source': 'textbook_chapter',
                    'evidence': ['chapter_order']
                })
    return teaches_before
```

### 5.4 定义依赖抽取（强证据）

从知识点的定义文本中提取关键词，匹配其他知识点名称。

```python
def extract_definition_dependencies(knowledge_points):
    """
    从知识点的 definition 文本中抽取出现的其他知识点名称
    这是强证据：如果B的定义中提到A，则A很可能是B的前置
    """
    dependencies = []
    for kp in knowledge_points:
        if not kp.definition:
            continue
        # 字符串匹配（可升级为 TF-IDF 或小模型）
        for other_kp in knowledge_points:
            if other_kp.uri == kp.uri:
                continue
            if other_kp.name in kp.definition:
                dependencies.append({
                    'from': other_kp.uri,
                    'to': kp.uri,
                    'confidence': 0.85,
                    'source': 'definition_extraction',
                    'evidence_types': ['definition_dependency'],
                    'reason': f'"{kp.name}"的定义中包含"{other_kp.name}"'
                })
    return dependencies
```

**示例**：
- 知识点"一元二次方程"定义：*"含有一个未知数，且未知数的最高次数是 2 的整式方程"*
- → 匹配出"整式方程""方程"作为候选前置

### 5.5 LLM 多模型投票

**配置**：GLM-4-flash + DeepSeek 两模型投票

```python
LLM_CONFIG = {
    "providers": ["zhipu", "deepseek"],
    "model": {"zhipu": "glm-4-flash", "deepseek": "deepseek-chat"},
    "scene": "prerequisite_inference",
    "temperature": 0.3,
    "batch_size": 10,      # 调小批次，提高精度
    "max_retries": 2,
}
```

**Prompt 设计**（强调概念依赖，区分教学顺序）：

```
你是一个教育领域专家，擅长分析知识点之间的逻辑依赖关系。

任务：判断知识点 A 是否是学习知识点 B 之前必须掌握的**核心前置知识**。
核心前置知识定义：如果不会 A，则无法理解或学会 B（无论教学顺序如何）。

请严格区分：
- 核心前置：必须学会才能学 B
- 教学顺序：只是教材安排更早，但不是必须

学科：{subject}
知识点列表：
| 序号 | 名称 | 类型 | 定义描述 |
|------|------|------|----------|
{knowledge_points_table}

请为每个知识点输出其核心前置知识点列表。输出严格 JSON 格式：
{
  "B的名称": {
    "prerequisites": ["A1名称", "A2名称"],
    "reason": "简要说明为什么这些是核心前置",
    "confidence": 0.0-1.0
  },
  ...
}

注意：
- 只输出 JSON 对象，不要任何额外解释。
- 如果某个知识点没有核心前置，输出空列表。
```

**投票合并算法**：

```python
def llm_inference_with_voting(kp_batch):
    """
    两模型投票：至少两个模型输出一致才采纳
    """
    results = []
    for provider in LLM_CONFIG["providers"]:
        llm = LLMFactory.get_llm(scene="prerequisite_inference", provider=provider)
        response = llm.chat(prompt)
        parsed = parse_json(response)
        results.append(parsed)

    # 投票合并
    candidate_relations = {}
    for result in results:
        for target, info in result.items():
            for prereq in info["prerequisites"]:
                key = (prereq, target)
                if key not in candidate_relations:
                    candidate_relations[key] = []
                candidate_relations[key].append({
                    "confidence": info["confidence"],
                    "reason": info["reason"]
                })

    # 最终候选：两模型一致，取平均置信度
    final_candidates = []
    for (from_kp, to_kp), votes in candidate_relations.items():
        if len(votes) >= 2:  # 两模型一致
            avg_conf = sum(v["confidence"] for v in votes) / len(vote)
            final_candidates.append({
                "from": from_kp,
                "to": to_kp,
                "confidence": avg_conf,
                "evidence_types": ["llm_inference"],
                "source": "llm_multi_vote"
            })
    return final_candidates
```

### 5.6 多证据融合

```python
def fuse_prerequisites(definition_deps, llm_candidates):
    """
    融合定义依赖 + LLM 多模型投票，生成最终 PREREQUISITE
    """
    EVIDENCE_WEIGHTS = {
        "definition_dependency": 0.85,
        "llm_inference": 0.8,
    }

    relations = {}

    # 定义依赖（强证据，直接生成 PREREQUISITE）
    for dep in definition_deps:
        key = (dep["from"], dep["to"])
        relations[key] = {
            "confidence": EVIDENCE_WEIGHTS["definition_dependency"],
            "evidence_types": ["definition_dependency"],
            "source": "definition_extraction"
        }

    # LLM 候选（两模型一致且置信度 >=0.8）
    for cand in llm_candidates:
        key = (cand["from"], cand["to"])
        if cand["confidence"] >= 0.8:
            if key in relations:
                # 已有定义依赖，提升置信度
                relations[key]["confidence"] = min(1.0, relations[key]["confidence"] + 0.1)
                relations[key]["evidence_types"].append("llm_inference")
            else:
                relations[key] = {
                    "confidence": cand["confidence"],
                    "evidence_types": ["llm_inference"],
                    "source": "llm_multi_vote"
                }
        else:
            # 低置信度存入 PREREQUISITE_CANDIDATE
            pass

    return relations
```

**融合规则总结**：
- 定义依赖：强证据，直接生成 PREREQUISITE
- LLM 候选：两模型一致 + 置信度 ≥0.8 → PREREQUISITE；否则 → PREREQUISITE_CANDIDATE
- 教材顺序：仅作为 TEACHES_BEFORE，不转化为 PREREQUISITE

---

## 六、实施步骤

### 阶段一：数据清洗与整合 (按学科逐个处理)

```
Step 1.1: 选择学科 (从数学开始)
Step 1.2: 解析 ttl/math.ttl → 提取知识点
Step 1.3: 解析 relations/math_relations.ttl → 提取关系
Step 1.4: 匹配 main.ttl → 获取教材信息
Step 1.5: 推断年级信息
Step 1.6: 数据验证
```

### 阶段二：导入 Neo4j

```
Step 2.1: 创建学科/学段/年级节点
Step 2.2: 创建教材/章节节点
Step 2.3: 创建知识点节点
Step 2.4: 创建分类关系 (BELONGS_TO)
Step 2.5: 创建关联关系 (RELATED_TO)
```

### 阶段三：构建前置依赖

```
Step 3.1: 基于教材章节顺序生成基础依赖
Step 3.2: 调用 LLM 补充跨章节依赖
Step 3.3: 合并去重，按置信度排序
Step 3.4: 导入 Neo4j (PREREQUISITE 关系)
Step 3.5: 提供人工审核接口
```

### 阶段四：验证与优化

```
Step 4.1: 抽查前置关系的合理性
Step 4.2: 验证学习路径的正确性
Step 4.3: 收集反馈，持续优化
```

---

## 七、预期产出

### 7.1 数据产物

| 产物 | 格式 | 说明 |
|------|------|------|
| 知识点标准数据 | JSON/CSV | 整合后的知识点列表，含年级、学科、**类型** |
| 前置依赖关系 | CSV | 三元组 (from, to, confidence, source) |
| 知识图谱数据库 | Neo4j | 可直接查询的图数据库 |

**CSV 导出格式**:

```csv
# 知识点标准数据 (knowledge_points.csv)
uri,name,subject,stage,grade,chapter,type,description,difficulty,source
http://edukg.org/...,一元二次方程,数学,初中,初三,一元二次方程,定义,含有一个未知数...,3,edukg

# 前置依赖关系 (prerequisites.csv)
from_uri,to_uri,confidence,source,reason
http://edukg.org/...,http://edukg.org/...,0.85,textbook_chapter,
```

**注意**: `type` 列必须导出，便于后续按类型查询和分析 |

### 7.2 代码产物

| 代码 | 说明 |
|------|------|
| `clean_data.py` | 数据清洗脚本 |
| `import_to_neo4j.py` | Neo4j 导入脚本 |
| `build_prerequisites.py` | 前置关系构建脚本 |
| `llm_inference.py` | LLM 推理调用脚本 |

---

## 八、分学科处理策略 (已确认)

### 8.1 学科类型划分

| 学科类型 | 学科 | 关系特点 | 处理策略 | 优先级 |
|---------|------|---------|---------|--------|
| **强逻辑链学科** | 数学、物理、化学、生物 | 前置关系明确，学习顺序固定 | 构建 PREREQUISITE 关系 | P1 |
| **语言学科** | 英语 | 语法层级、词汇递进 | 构建语法/词汇层级 | P2 |
| **主题关联学科** | 历史、语文、地理、政治 | 主题/时间关联，非学习依赖 | 构建主题分类关系 | P3 |

### 8.2 处理顺序 (Phase by Phase)

```
Phase 1: 数学 (有关系数据，验证设计)
         - 知识点数: 4,490
         - relateTo: 9,870 (可直接使用)
         - subCategory: 328 (层级关系)
         - 目标: 验证整体流程可行性

Phase 2: 物理、化学、生物 (强逻辑链，需构建关系)
         - 物理: 3,385 知识点
         - 化学: 5,718 知识点
         - 生物: 15,209 知识点
         - 目标: 使用 LLM 构建前置关系

Phase 3: 英语 (语法层级)
         - 英语: 5,107 知识点
         - 目标: 构建语法/词汇层级

Phase 4: 历史、语文、地理、政治 (主题关联)
         - 历史: 4,850 知识点
         - 语文: 8,041 知识点
         - 地理: 4,682 知识点
         - 政治: 5,309 知识点
         - 目标: 构建主题分类，不做前置依赖
```

### 8.3 前置关系构建方案 (已确认: LLM 推理)

**模型选择**: GLM-4-flash (免费，主力)

```python
# LLM 推理配置
LLM_CONFIG = {
    "provider": "zhipu",
    "model": "glm-4-flash",  # 免费，主力
    "scene": "prerequisite_inference",
    "batch_size": 50,  # 每批处理50个知识点
    "temperature": 0.3,  # 降低随机性，提高一致性
}
```

**调用方式**: 复用现有 LLM Gateway，新增 `prerequisite_inference` scene

**推理流程**:
1. 按学科分组知识点
2. 按章节/主题分批 (每批 50 个)
3. 调用 LLM 分析前置关系
4. 输出带置信度的关系数据
5. 置信度 < 0.7 **直接丢弃**，不做人工审核

**relateTo 数据处理**:
- relateTo → RELATED_TO（知识点关联，必须保留）
- **Demo 阶段不做 LLM 验证补充**，核心闭环跑通后再优化

---

## 九、验证方案 (Demo 阶段务实策略)

### 9.1 验证方式

| 方式 | 说明 | Demo 阶段策略 |
|------|------|---------------|
| **自动验证** | 循环依赖检测、年级倒置检测 | 数据导入前自动执行 |
| **抽样测试** | 随机抽取检查合理性 | ≥70% 准确率即可满足 demo |
| **人工审核** | 教师审核 | **不做**，无相关人员参与 |

### 9.2 置信度处理

- 置信度 < 0.8 的 LLM 候选：存入 **PREREQUISITE_CANDIDATE**
- 定义依赖：直接生成 PREREQUISITE
- LLM 多模型投票一致 + 置信度 ≥0.8：生成 PREREQUISITE

### 9.3 抽样测试量化标准

**抽样方法**:
- 从数学学科随机抽取 **100-200 条** PREREQUISITE 关系
- 覆盖不同年级、不同类型（定义/公式/方法）
- 由内部人员（或参照教材、课程标准）判断是否合理

**评估标准**:
```
准确率 = 合理关系数 / 抽样总数
目标: ≥70%
```

**调整策略**（若低于阈值）:
1. 调整 Prompt 设计
2. 降低 temperature（如 0.2）
3. 提高置信度阈值（如 0.85）

### 9.4 图谱质量指标

| 指标 | 计算方法 | 目标值（demo） |
|------|---------|--------------|
| **前置关系覆盖率** | 有 PREREQUISITE 关系的知识点数 / 总知识点数 | ≥ 30% |
| **DAG 合规率** | 无环的知识点比例（检测环的数量） | 100% |
| **平均前置链长度** | 所有知识点的最长前置路径长度的平均值 | 2~4 跳 |
| **年级倒置率** | PREREQUISITE 关系出现高年级指向低年级的比例 | ≤ 5% |
| **置信度分布** | 高置信度（≥0.8）关系的占比 | ≥ 60% |

### 9.5 Neo4j 部署配置

| 配置项 | 值 |
|--------|-----|
| 版本 | Neo4j 社区版 4.4.x |
| 部署 | 单机部署 |
| 内存 | 4G |
| 存储 | 100G+ |
| 备份 | CSV 文件全量备份 |

### 9.6 典型业务查询模板

```cypher
// 1. 获取知识点的所有前置依赖（多跳）
MATCH (target:KnowledgePoint {uri: $uri})<-[r:PREREQUISITE*]-(prereq)
RETURN prereq, r

// 2. 获取知识点的直接教学顺序（前驱）
MATCH (target:KnowledgePoint {uri: $uri})<-[r:TEACHES_BEFORE]-(prev)
RETURN prev, r

// 3. 基于知识点集合，计算知识缺陷（未掌握的前置）
MATCH (kp:KnowledgePoint) WHERE kp.uri IN $mastered_kps
WITH COLLECT(kp) AS mastered
MATCH (target:KnowledgePoint {uri: $target_uri})<-[r:PREREQUISITE*]-(prereq)
WHERE NOT prereq IN mastered
RETURN prereq, r

// 4. 生成学习路径（拓扑排序）
MATCH (target:KnowledgePoint {uri: $target_uri})
MATCH path = (start)-[:PREREQUISITE*]->(target)
RETURN path ORDER BY LENGTH(path) ASC

// 5. 查询候选前置关系（待验证）
MATCH (kp:KnowledgePoint)-[r:PREREQUISITE_CANDIDATE]->(target)
WHERE r.confidence >= 0.6
RETURN kp, target, r
```

### 9.4 业务优先级（围绕 AI 引导式答疑）

| 优先级 | 业务场景 | 说明 |
|--------|---------|------|
| **P0** | 前置依赖查询 | 核心基础，方案核心目标 |
| **P1** | 知识点识别、知识缺陷诊断 | Demo 必实现，支撑核心功能闭环 |
| **P2** | 学习路径推荐、年级/学科定位 | 可选迭代，核心跑通后补充 |

---

## 十、技术栈与开发规范

### 10.1 技术栈

| 技术项 | 选择 | 说明 |
|--------|------|------|
| Python 版本 | 3.10+ | 与主服务一致，避免环境冲突 |
| TTL 解析库 | rdflib | Python 生态最成熟的 RDF 解析库 |
| Neo4j 驱动 | neo4j-driver 4.4.x | 与 Neo4j 版本严格匹配 |
| LLM 调用 | 复用 Gateway | 使用现有 `core/gateway/factory.py` |

### 10.2 脚本目录结构

```
ai-edu-ai-service/scripts/kg_construction/
├── requirements-scripts.txt   # 脚本独立依赖，不污染主服务
├── clean_math_data.py         # 数学数据清洗
├── extract_textbook_info.py   # 教材信息提取
├── merge_math_data.py         # 数据合并
├── infer_prerequisites_llm.py # LLM 前置关系推理
├── merge_prerequisites.py     # 前置关系合并
├── import_math_to_neo4j.py    # Neo4j 导入
├── validate_prerequisites.py  # 自动验证脚本
└── logs/                      # 错误日志目录
```

### 10.3 LLM Gateway 配置

在 `config/model_config.py` 新增 scene 映射：

```python
SCENE_MODEL_MAPPING = {
    # ... 现有配置
    "prerequisite_inference": {
        "provider": "zhipu",
        "model": "glm-4-flash",
        "temperature": 0.3,
    },
}
```

---

## 十一、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| v0.1 与 v3.0 数据不匹配 | 通过标签匹配，容忍部分缺失 |
| LLM 推理不准确 | 置信度阈值过滤（<0.7 丢弃），≥70% 准确率满足 demo |
| 年级推断不准确 | 提供人工修正接口（正式阶段） |
| 数据量太大 | 按学科逐个处理，数学先行验证 |
| relateTo 与 PREREQUISITE 语义混淆 | 严格区分，relateTo → RELATED_TO，LLM → PREREQUISITE |

---

## 十二、数据更新机制（Demo 阶段）

| 方面 | 策略 |
|------|------|
| 基准数据 | edukg 静态权威库，知识点永久冻结只读 |
| 维护规则 | 仅增量补充「题目-知识点」关联，不修改基准知识点 |
| 版本管理 | CSV 文件命名区分（如 knowledge_points_v1.csv） |
| 长期维护 | Demo 阶段不考虑，正式迭代再设计 |