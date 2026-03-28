感谢你提供的详细反馈，这些建议非常专业且贴合实际落地需求。以下是根据你的建议修订后的方案，重点强化了**EduKG标准对齐**、**多证据融合的前置关系构建**以及**业务验证闭环**。

---

# 知识图谱数据整理方案设计（修订版）

## 一、目标（不变）

将现有数据整理成支持 AI 作业答疑业务的知识图谱：
- 按学科、年级组织知识点
- 建立知识点前置/后置依赖关系
- 支持学习路径推荐和知识缺陷诊断

---

## 二、数据模型设计（强化 EduKG 标准对齐）

### 2.1 知识点层级结构（不变）

```
学科 (Subject)
  └── 学段 (Stage: 小学/初中/高中)
        └── 年级 (Grade)
              └── 教材 (Textbook)
                    └── 章节 (Chapter)
                          └── 知识点 (KnowledgePoint)
```

### 2.2 Neo4j 节点模型（新增教材版本字段）

```cypher
// 学科节点
(:Subject {name: "数学", code: "math"})

// 学段节点
(:Stage {name: "高中", code: "high_school"})

// 年级节点
(:Grade {name: "高一", code: "g10", order: 1})

// 教材节点（增加 publisher, version_year）
(:Textbook {
  name: "高中数学必修第一册",
  publisher: "人教版",
  version_year: "2019",
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

// 知识点节点（增加 type 属性，保留 uri）
(:KnowledgePoint {
  uri: "http://edukg.org/knowledge/0.1/instance/math#516",
  name: "一元二次方程",
  subject: "math",
  stage: "初中",
  grade: "初三",          // 推断或标注
  chapter: "一元二次方程",
  type: "定义",           // 定义/性质/定理/公式/方法
  difficulty: 3,          // 1-5 难度等级
  source: "edukg"         // 数据来源
})
```

### 2.3 关系模型（增加 EduKG 标准关系与证据类型）

```cypher
// ========== 层级关系（不变）==========
(:Subject)-[:HAS_STAGE]->(:Stage)
(:Stage)-[:HAS_GRADE]->(:Grade)
(:Grade)-[:USE_TEXTBOOK]->(:Textbook)
(:Textbook)-[:HAS_CHAPTER]->(:Chapter)
(:Chapter)-[:CONTAINS]->(:KnowledgePoint)

// ========== 分类关系 ==========
(:KnowledgePoint)-[:BELONGS_TO]->(:Category)

// ========== 教学顺序（区分教学顺序与学习依赖）==========
(:KnowledgePoint)-[:TEACHES_BEFORE {
  confidence: 0.85,
  source: "textbook_chapter",
  evidence: ["chapter_order"]
}]->(:KnowledgePoint)

// ========== 核心前置关系（学习依赖）==========
// 保留两种关系类型：业务用 PREREQUISITE + EduKG 标准关系 先修于
(:KnowledgePoint)-[:PREREQUISITE {
  confidence: 0.85,
  source: "llm",           // llm/textbook/teacher/definition_dependency
  evidence_types: ["definition_dependency", "example_solution"], // 证据来源列表
  verified: false,
  standard_relation: "先修于"   // 标注标准关系名
}]->(:KnowledgePoint)

// 同时创建标准关系，便于互操作
(:KnowledgePoint)-[:先修于 {
  confidence: 0.85,
  source: "llm"
}]->(:KnowledgePoint)

// ========== 候选前置关系（待验证）==========
(:KnowledgePoint)-[:PREREQUISITE_CANDIDATE {
  confidence: 0.65,
  source: "llm_zero_shot",
  evidence_types: ["llm_inference"],
  status: "candidate"
}]->(:KnowledgePoint)

// ========== 关联关系（保留原生）==========
(:KnowledgePoint)-[:RELATED_TO {
  source: "edukg_relateTo"
}]->(:KnowledgePoint)

(:KnowledgePoint)-[:SUB_CATEGORY]->(:KnowledgePoint)
```

**设计说明**：
- 保留 **PREREQUISITE** 和 **先修于** 两种关系类型，前者用于业务查询，后者符合 EduKG 标准，方便未来互操作。
- 新增 **TEACHES_BEFORE** 关系，专门表示教材教学顺序，与真正的学习依赖（PREREQUISITE）区分。
- 新增 **PREREQUISITE_CANDIDATE** 关系，用于存放 LLM 零样本推理但尚未经过多证据验证的关系，便于后续迭代。

---

## 三、数据来源与整合策略（不变）

维持原方案，以 ttl 和 relations 为主，匹配 main.ttl 获取教材信息。

---

## 四、年级推断规则（增强教材版本处理）

### 4.1 教材 → 年级映射（增加 publisher 维度）

```python
# 使用字典嵌套 publisher
TEXTBOOK_TO_GRADE = {
    "人教版": {
        "必修第一册": ("高中", "高一"),
        "必修第二册": ("高中", "高一"),
        "必修1": ("高中", "高一"),
        "必修2": ("高中", "高二"),
        "选择性必修1": ("高中", "高二"),
        "七年级上册": ("初中", "初一"),
        "七年级下册": ("初中", "初一"),
        "八年级上册": ("初中", "初二"),
        # ...
    },
    "北师大版": {
        "必修1": ("高中", "高一"),
        # ...
    }
}

def infer_grade(textbook_name, publisher=None):
    if publisher and publisher in TEXTBOOK_TO_GRADE:
        return TEXTBOOK_TO_GRADE[publisher].get(textbook_name, (None, None))
    # 模糊匹配
    for pub, mapping in TEXTBOOK_TO_GRADE.items():
        if textbook_name in mapping:
            return mapping[textbook_name]
    return (None, None)
```

**推断规则**：
- 优先精确匹配（publisher + name）
- 其次仅匹配 name，降低置信度并标记 `inferred: true`
- 若完全无法推断，留空，后续通过章节或知识点学段字段补充

---

## 五、前置依赖关系构建方案（多证据融合）

### 5.1 证据来源分类

| 证据类型 | 说明 | 基础权重 | 示例 |
|---------|------|---------|------|
| **教材章节顺序** | 同章节内按 mark 顺序 | 0.7 | 1.1 节知识点 → 1.2 节知识点 |
| **定义/定理依赖** | 从定义文本中抽取的关键概念 | 0.85 | “一元二次方程”定义中出现“整式方程” |
| **例题/习题技能组合** | 例题解析中明确使用的方法 | 0.8 | 解方程需要“因式分解” |
| **LLM 推理** | 零样本 prompt 推理 | 0.8（F1≈0.82） | - |
| **教师标注** | 人工审核 | 1.0 | - |

### 5.2 证据抽取实现

#### 5.2.1 定义/定理依赖抽取（规则 + 小模型）

从知识点的定义文本中提取关键词，匹配其他知识点名称。

```python
def extract_definition_dependencies(kp):
    """
    从知识点的 definition 文本中抽取出现的其他知识点名称
    """
    dependencies = []
    # 简单的字符串匹配（可升级为 TF-IDF 或小模型）
    for other_kp in all_knowledge_points:
        if other_kp.name in kp.definition:
            dependencies.append(other_kp)
    return dependencies
```

**示例**：  
知识点“一元二次方程”定义：*“含有一个未知数，且未知数的最高次数是 2 的整式方程”*  
→ 匹配出“整式方程”“方程”作为候选前置。

#### 5.2.2 例题/习题技能组合（从教材习题文本抽取）

如果有教材例题或习题文本，可从中分析解题步骤涉及的知识点。Demo 阶段可先不实现，但预留接口。

### 5.3 教材章节顺序细化

**仅生成同章节内的 TEACHES_BEFORE 关系**，不再硬编码跨章节的首尾关联，避免引入不准确的依赖。

```python
def infer_teaches_before(knowledge_points):
    """
    按教材和章节分组，按 mark 顺序生成 TEACHES_BEFORE 关系
    """
    teaches_before = []
    for textbook, kps in group_by_textbook(knowledge_points):
        # 按章节和 mark 排序
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

**跨章节关系**交由 LLM 推理和定义依赖抽取完成，避免硬编码。

### 5.4 LLM 推理（作为候选生成器，配合多模型投票）

#### 5.4.1 配置

```python
LLM_CONFIG = {
    "providers": ["zhipu", "deepseek"],  # 两个模型
    "model": {"zhipu": "glm-4-flash", "deepseek": "deepseek-chat"},
    "scene": "prerequisite_inference",
    "temperature": 0.3,
    "batch_size": 10,      # 调小批次，提高精度
    "max_retries": 2,
}
```

#### 5.4.2 Prompt 设计（强调概念依赖，区分教学顺序）

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

请为每个知识点输出其核心前置知识点列表（从本列表中选择）。输出严格 JSON 格式：
{
  "B的名称": {
    "prerequisites": ["A1名称", "A2名称"],
    "reason": "简要说明为什么这些是核心前置，例如：B的定义中使用了A的概念，或B的推导依赖于A的方法",
    "confidence": 0.0-1.0
  },
  ...
}

注意：
- 只输出 JSON 对象，不要任何额外解释。
- 如果某个知识点没有核心前置，输出空列表。
- confidence 反映你对这个判断的把握。
```

#### 5.4.3 多模型投票与候选生成

```python
def llm_inference_with_voting(kp_batch):
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

    # 最终候选关系：至少两个模型输出一致，取平均置信度
    final_candidates = []
    for (from_kp, to_kp), votes in candidate_relations.items():
        if len(votes) >= 2:
            avg_conf = sum(v["confidence"] for v in votes) / len(votes)
            final_candidates.append({
                "from": from_kp,
                "to": to_kp,
                "confidence": avg_conf,
                "evidence_types": ["llm_inference"],
                "source": "llm_multi_vote"
            })
    return final_candidates
```

### 5.5 多证据融合与置信度计算

```python
def fuse_prerequisites(teaches_before, definition_deps, llm_candidates, teacher_verified=[]):
    """
    融合多种证据，生成最终的 PREREQUISITE 关系
    """
    # 证据权重
    EVIDENCE_WEIGHTS = {
        "definition_dependency": 0.85,
        "llm_inference": 0.8,
        "teacher_verified": 1.0,
        "textbook_chapter": 0.7,    # 仅作为弱参考，不直接作为 PREREQUISITE
    }

    relations = {}
    # 处理定义依赖（强证据）
    for dep in definition_deps:
        key = (dep["from"], dep["to"])
        relations[key] = {
            "confidence": EVIDENCE_WEIGHTS["definition_dependency"],
            "evidence_types": ["definition_dependency"],
            "source": "definition_extraction"
        }

    # 处理 LLM 候选（如果置信度高且没有被强证据否定）
    for cand in llm_candidates:
        key = (cand["from"], cand["to"])
        if cand["confidence"] >= 0.8:   # 高置信度候选
            if key in relations:
                # 已有强证据，提升置信度
                relations[key]["confidence"] = min(1.0, relations[key]["confidence"] + 0.1)
                relations[key]["evidence_types"].append("llm_inference")
            else:
                relations[key] = {
                    "confidence": cand["confidence"],
                    "evidence_types": ["llm_inference"],
                    "source": "llm"
                }
        else:
            # 低置信度候选存入 PREREQUISITE_CANDIDATE
            # 单独处理
            pass

    # 教师标注直接覆盖
    for teacher in teacher_verified:
        key = (teacher["from"], teacher["to"])
        relations[key] = {
            "confidence": 1.0,
            "evidence_types": ["teacher_verified"],
            "source": "teacher"
        }

    # 合并 TEACHES_BEFORE 不直接作为 PREREQUISITE，但可用于冲突检测
    # 例如，如果 PREREQUISITE 与 TEACHES_BEFORE 方向相反，则标记冲突

    return relations
```

**融合规则总结**：
- **定义依赖**：作为强证据，直接生成 PREREQUISITE。
- **LLM 候选**：置信度 ≥0.8 且没有与强证据冲突的，作为 PREREQUISITE；否则存入 CANDIDATE。
- **教材顺序**：仅作为 TEACHES_BEFORE，不直接转化为 PREREQUISITE，但可用于验证（如发现前置关系与教学顺序完全相反，则可能错误）。
- **教师标注**：最高优先级。

---

## 六、实施步骤（微调）

### 阶段一：数据清洗与整合（不变）
### 阶段二：导入 Neo4j（不变）
### 阶段三：构建前置依赖（按新流程）

```
Step 3.1: 基于教材章节顺序生成 TEACHES_BEFORE 关系
Step 3.2: 从定义文本中抽取定义依赖 → 生成部分 PREREQUISITE
Step 3.3: 调用 LLM 多模型生成候选前置关系 → 生成 PREREQUISITE_CANDIDATE
Step 3.4: 融合多证据（定义依赖 + 高置信度 LLM 候选）→ 生成 PREREQUISITE
Step 3.5: 导入 Neo4j（PREREQUISITE, PREREQUISITE_CANDIDATE, TEACHES_BEFORE）
Step 3.6: 提供人工审核接口（后续）
```

### 阶段四：验证与优化（新增业务查询和指标）

---

## 七、验证与业务闭环（新增查询模板与指标）

### 7.1 典型业务查询模板

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
```

### 7.2 图谱质量指标

| 指标 | 计算方法 | 目标值（demo） |
|------|---------|--------------|
| **前置关系覆盖率** | 有 PREREQUISITE 关系的知识点数 / 总知识点数 | ≥ 30% |
| **DAG 合规率** | 无环的知识点比例（检测环的数量） | 100% |
| **平均前置链长度** | 所有知识点的最长前置路径长度的平均值 | 2~4 跳 |
| **年级倒置率** | 前置关系出现高年级指向低年级的比例 | ≤ 5% |
| **置信度分布** | 高置信度（≥0.8）关系的占比 | ≥ 60% |

### 7.3 抽样准确率评估

- **抽样方法**：从数学学科的 PREREQUISITE 关系中随机抽取 100-200 条，覆盖不同年级、不同类型（定义/公式/方法）。
- **评估标准**：由内部人员（或参照教材、课程标准）判断是否合理。若准确率 < 70%，则调整证据融合策略或 Prompt。
- **记录**：保留评估结果，用于迭代优化。

---

## 八、分学科处理策略（微调）

| 学科类型 | 学科 | 处理策略 | 证据融合重点 |
|---------|------|---------|-------------|
| **强逻辑链** | 数学、物理、化学、生物 | 构建 PREREQUISITE + TEACHES_BEFORE | 定义依赖 + 多模型 LLM |
| **语言学科** | 英语 | 构建语法层级（TEACHES_BEFORE）和词汇递进 | 教材顺序 + 语法规则 |
| **主题关联** | 历史、语文、地理、政治 | 构建 RELATED_TOPIC / TEMPORAL_ORDER | 时间轴、主题分类，不建 PREREQUISITE |

---

## 九、技术栈与脚本目录（不变）

维持原方案。

---

## 十、风险与缓解（新增证据冲突处理）

| 风险 | 缓解措施 |
|------|---------|
| 定义依赖抽取不准确 | 使用小模型/规则+人工抽检，低精度时降级为候选 |
| LLM 多模型投票成本增加 | 仅对跨章节、跨类型的知识点对调用，非全量 |
| 教材顺序与学习依赖混淆 | 明确区分 TEACHES_BEFORE 和 PREREQUISITE，独立存储 |
| 证据冲突（如定义依赖与教材顺序矛盾） | 以强证据（定义依赖、教师标注）为准，冲突关系标记 `conflict` 属性，便于后续审核 |

---

## 十一、数据更新机制（不变）

维持原方案。

---

## 总结

本修订版方案在原有基础上强化了：
- **EduKG 标准对齐**：增加标准关系 `先修于`，增加教材版本字段。
- **多证据融合**：引入定义依赖抽取、教材顺序与 LLM 推理融合，并区分教学顺序与学习依赖。
- **业务验证闭环**：设计了典型查询模板和量化指标，便于评估图谱质量。

下一步可按照“数学先行”的原则，先实现定义依赖抽取和多模型 LLM 推理的候选生成，逐步完善证据融合逻辑。如有任何细节需要进一步讨论，随时可以调整。