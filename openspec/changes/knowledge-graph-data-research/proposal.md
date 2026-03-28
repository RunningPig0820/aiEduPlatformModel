## Why

AI 引导式答疑业务需要知识图谱数据支持：
1. **知识点识别**: 从题目文本中识别涉及的知识点
2. **年级/学科定位**: 查询知识点所属年级和学科
3. **前置依赖关系**: 判断学习某知识点需要先掌握哪些知识（P0 核心）
4. **知识缺陷诊断**: 根据答题情况定位学生知识体系缺陷（P1）
5. **知识点关联扩展**: 查询相关知识点，支持知识图谱可视化

当前数据存在问题：
- 版本不兼容 (v0.1 vs v3.0)
- 缺少年级信息
- **只有数学有关系数据**，其他学科全部缺失
- relateTo 关系不能直接作为前置依赖（语义不同）

## What Changes

1. **数据清洗与整合**
   - 统一数据格式，以 v0.1 为主
   - 按学科逐一处理，数学先行验证
   - 补充年级信息（含初中映射）
   - 提取知识点类型信息（定义/性质/定理/公式/方法）

2. **构建关系（区分教学顺序与学习依赖）**
   - **TEACHES_BEFORE**：教材教学顺序（不等于学习依赖）
   - **PREREQUISITE**：学习依赖（不学A就学不懂B），由多证据融合生成
   - **定义依赖抽取**：从定义文本中匹配其他知识点名称（强证据）
   - **LLM 多模型投票**：GLM-4-flash + DeepSeek 两模型一致才采纳
   - **PREREQUISITE_CANDIDATE**：低置信度候选关系，待后续验证

3. **保留原生关联关系**
   - relateTo → RELATED_TO（知识点关联，必须保留）
   - subCategory → SUB_CATEGORY（分类层级）

4. **EduKG 标准对齐**
   - 新增 `先修_on` 标准关系，便于互操作

5. **导入 Neo4j**
   - 建立标准数据模型
   - 创建层级结构 (学科→学段→年级→章节→知识点)
   - 创建多种关系类型（TEACHES_BEFORE, PREREQUISITE, 先修_on, PREREQUISITE_CANDIDATE, RELATED_TO, SUB_CATEGORY）

## Capabilities

### New Capabilities

- `knowledge-graph-data`: 标准化的知识图谱数据，支持按学科/年级/类型查询知识点
- `teaches-before-relation`: 教材教学顺序关系，支持教学参考和顺序查询
- `prerequisite-relation`: 学习依赖关系（多证据融合生成），支持学习路径推荐和知识诊断
- `prerequisite-candidate`: 低置信度候选关系，支持后续迭代优化
- `related-knowledge`: 知识点横向关联（TTL 原生数据），支持知识扩展和可视化
- `edukg-standard`: EduKG 标准关系（先修_on），支持互操作

### Modified Capabilities

- `entity-linking`: 增强实体链接，关联年级、类型和前置知识信息

## Impact

- **数据目录**: 新建 `ai-edu-ai-service/scripts/kg_construction/` 目录
- **Neo4j**: 新增 6 种关系类型（TEACHES_BEFORE, PREREQUISITE, 先修_on, PREREQUISITE_CANDIDATE, RELATED_TO, SUB_CATEGORY）
- **LLM Gateway**: 新增 `prerequisite_inference` scene 映射，支持多模型投票
- **数据量**: 约 56,391 知识点，10,198 原生关系（保留），约 50,000+ 学习依赖关系（多证据融合生成）