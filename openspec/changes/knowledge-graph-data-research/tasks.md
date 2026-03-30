# 知识图谱数据整理任务清单 (全部学科)

## 关键决策 (已确认)
- ✅ 学科范围: 全部 9 个学科
- ✅ 前置关系构建: LLM 推理 (DeepSeek/GLM-4.7)
- ✅ 验证方式: 自动验证 + 抽样测试 + 业务试点

---

## 阶段一：数据调研与准备

- [x] 1.1 分析 TTL 文件结构，识别版本兼容性
- [x] 1.2 统计各学科知识点数量、关系数量
- [x] 1.3 分析 main.ttl 与 ttl/*.ttl 的标签匹配率
- [x] 1.4 输出数据质量报告 (data-research.md)
- [x] 1.5 发现关键问题: 只有数学有关系数据，其他学科缺失

---

## 阶段二：Phase 1 - 数学学科试点 (优先)

### 前置验证
- [ ] 2.0 极简类型字段验证
  - 从 ttl/math.ttl 随机抽取 10-20 条知识点
  - 验证 `edukg:knowledgeType` 和 `rdf:type` 提取逻辑
  - 确认类型字段取值分布（定义/性质/定理/公式/方法）

### 数据清洗
- [ ] 2.1 编写 `scripts/clean_math_data.py`
  - 解析 ttl/math.ttl 提取知识点 (4,490 个)
  - 解码 Unicode 标签
  - 提取知识点名称 + 描述 + 类型 + 学科路径
  - 去重、清洗无效数据
  - **CSV 导出必须包含 type 列**
- [ ] 2.2 编写 `scripts/extract_textbook_info.py`
  - 从 main.ttl 提取教材信息
  - 通过标签匹配知识点
  - 推断年级信息（补充初中映射）
- [ ] 2.3 编写 `scripts/merge_math_data.py`
  - 合并知识点 + 教材信息
  - 输出标准化 JSON 文件

### 关系数据提取（必须保留）
- [ ] 2.4 编写 `scripts/extract_relations.py`
  - 解析 relations/math_relations.ttl
  - 提取 relateTo 关系 (9,870 条) → 导入为 RELATED_TO
  - 提取 subCategory 关系 (328 条) → 导入为 SUB_CATEGORY
  - **重要**: relateTo 不作为 PREREQUISITE，语义完全不同

### 构建关系
- [ ] 2.5 编写 `scripts/infer_teaches_before.py`
  - 基于教材章节顺序生成 **TEACHES_BEFORE** 关系
  - 仅同章节内部（跨章节由 LLM 推理）
  - **注意**：这是教学顺序，不是学习依赖
  - 输出 CSV
- [ ] 2.6 编写 `scripts/extract_definition_dependencies.py`
  - 从知识点定义文本中匹配其他知识点名称
  - 生成 **PREREQUISITE** 关系（强证据）
  - 输出 CSV
- [ ] 2.7 编写 `scripts/infer_prerequisites_llm.py`
  - 设计 LLM prompt（强调核心前置 vs 教学顺序）
  - **两模型投票**：GLM-4-flash + DeepSeek
  - 调用 LLM Gateway（scene: prerequisite_inference）
  - temperature=0.3，batch_size=10
  - 至少两模型一致才采纳
  - 高置信度(≥0.8) → PREREQUISITE
  - 低置信度(<0.8) → PREREQUISITE_CANDIDATE
  - 输出 CSV
- [ ] 2.8 编写 `scripts/fuse_prerequisites.py`
  - 融合定义依赖 + LLM 多模型投票
  - 生成最终 PREREQUISITE 关系
  - 同时生成 EduKG 标准关系（PREREQUISITE_ON）
  - 输出最终关系文件

### 导入 Neo4j
- [ ] 2.9 编写 `scripts/create_neo4j_schema.py`
  - 创建节点标签和索引
  - 定义关系类型：
    - TEACHES_BEFORE（教学顺序）
    - PREREQUISITE（学习依赖）
    - PREREQUISITE_CANDIDATE（候选关系）
    - PREREQUISITE_ON（EduKG 标准）
    - RELATED_TO（知识点关联）
    - SUB_CATEGORY（分类层级）
- [ ] 2.10 编写 `scripts/import_math_to_neo4j.py`
  - 导入学科/学段/年级节点
  - 导入教材/章节节点
  - 导入知识点节点（含类型信息）
  - 导入 TEACHES_BEFORE 关系
  - 导入 PREREQUISITE 关系
  - 导入 PREREQUISITE_CANDIDATE 关系
  - 导入 PREREQUISITE_ON 标准关系
  - 导入 RELATED_TO 关系（relateTo 数据）
  - 导入 SUB_CATEGORY 关系（subCategory 数据）
- [ ] 2.11 验证数据完整性
  - 检查节点数量
  - 检查关系数量（各类型分开统计）
  - 自动验证：
    - DAG 合规率（无环）
    - 年级倒置率（≤5%）
    - 前置关系覆盖率（≥30%）
    - 平均前置链长度（2~4跳）

### 质量抽样
- [ ] 2.12 抽查前置关系合理性
  - 从数学学科随机抽取 **100-200 条** PREREQUISITE 关系
  - 覆盖不同年级、不同类型（定义/公式/方法）
  - 由内部人员（或参照教材、课程标准）判断是否合理
  - 计算准确率，目标：≥70%
  - 若低于阈值，调整 Prompt/温度/置信度阈值
  - **无人工审核环节**
- [ ] 2.13 计算图谱质量指标
  - 前置关系覆盖率（≥30%）
  - DAG 合规率（100%）
  - 平均前置链长度（2~4跳）
  - 年级倒置率（≤5%）
  - 置信度分布（高置信度≥60%）

---

## 阶段三：Phase 2 - 物理/化学/生物

### 物理学科
- [ ] 3.1 清洗物理数据 (3,385 知识点)
- [ ] 3.2 匹配教材信息，推断年级
- [ ] 3.3 LLM 构建前置关系 (无原有关系数据)
- [ ] 3.4 导入 Neo4j

### 化学学科
- [ ] 3.5 清洗化学数据 (5,718 知识点)
- [ ] 3.6 匹配教材信息，推断年级
- [ ] 3.7 LLM 构建前置关系
- [ ] 3.8 导入 Neo4j

### 生物学科
- [ ] 3.9 清洗生物数据 (15,209 知识点)
- [ ] 3.10 匹配教材信息，推断年级
- [ ] 3.11 LLM 构建前置关系
- [ ] 3.12 导入 Neo4j

---

## 阶段四：Phase 3 - 英语

- [ ] 4.1 清洗英语数据 (5,107 知识点)
- [ ] 4.2 构建语法/词汇层级关系
- [ ] 4.3 导入 Neo4j

---

## 阶段五：Phase 4 - 历史/语文/地理/政治

### 历史学科 (主题/时间关联)
- [ ] 5.1 清洗历史数据 (4,850 知识点)
- [ ] 5.2 构建时间线关系 (非学习依赖)
- [ ] 5.3 构建主题分类
- [ ] 5.4 导入 Neo4j

### 语文学科 (主题/作品关联)
- [ ] 5.5 清洗语文数据 (8,041 知识点)
- [ ] 5.6 构建作品-作者关联
- [ ] 5.7 构建主题分类
- [ ] 5.8 导入 Neo4j

### 地理学科
- [ ] 5.9 清洗地理数据 (4,682 知识点)
- [ ] 5.10 构建区域/主题分类
- [ ] 5.11 导入 Neo4j

### 政治学科
- [ ] 5.12 清洗政治数据 (5,309 知识点)
- [ ] 5.13 构建主题分类
- [ ] 5.14 导入 Neo4j

---

## 阶段六：小学数据处理 (可选)

- [ ] 6.1 分析好未来数据结构 (haoweilai/)
- [ ] 6.2 转换为标准格式
- [ ] 6.3 补充年级信息
- [ ] 6.4 导入 Neo4j

---

## 阶段七：质量保障（Demo 阶段务实策略）

- [ ] 7.1 编写自动验证脚本
  - 循环依赖检测
  - 年级倒置检测
  - 类型合理性检测
- [ ] 7.2 抽查前置关系准确性
  - 随机抽取检查
  - ≥70% 准确率满足 demo
  - **无人工审核环节**
- [ ] 7.3 置信度处理
  - < 0.7 的关系直接丢弃
  - 不做人工复核
- [ ] 7.4 编写数据质量报告

---

## 阶段八：工具与文档

- [ ] 8.1 编写人工审核接口 (可选)
- [ ] 8.2 编写数据更新脚本
- [ ] 8.3 输出最终数据文档

---

## 数据统计汇总

| 学科 | 知识点数 | TTL 原生关系 | 构建关系 | Phase |
|------|---------|-------------|---------|-------|
| 数学 | 4,490 | 9,870 relateTo → **RELATED_TO**<br>328 subCategory → **SUB_CATEGORY** | **TEACHES_BEFORE**（教学顺序）<br>**PREREQUISITE**（学习依赖）<br>**PREREQUISITE_ON**（EduKG标准）<br>**PREREQUISITE_CANDIDATE**（候选） | P1 |
| 物理 | 3,385 | 0 | 同上 | P2 |
| 化学 | 5,718 | 0 | 同上 | P2 |
| 生物 | 15,209 | 0 | 同上 | P2 |
| 英语 | 5,107 | 0 | 语法层级 | P3 |
| 历史 | 4,850 | 0 | 主题关联 | P4 |
| 语文 | 8,041 | 0 | 主题关联 | P4 |
| 地理 | 4,682 | 0 | 主题关联 | P4 |
| 政治 | 5,309 | 0 | 主题关联 | P4 |
| **总计** | **56,391** | **10,198** (必须保留) | **约 50,000+** | - |

### 关系类型说明

| 关系类型 | 来源 | 语义 | 用途 |
|---------|------|------|------|
| **TEACHES_BEFORE** | 教材章节顺序 | 教学安排顺序（不等于学习依赖） | 教学参考、顺序查询 |
| **PREREQUISITE** | 定义依赖抽取 + LLM多模型投票 | 学习依赖（不学A就学不懂B） | AI 答疑核心：学习路径、知识诊断 |
| **PREREQUISITE_ON** | 同 PREREQUISITE | EduKG 标准关系 | 互操作、标准化 |
| **PREREQUISITE_CANDIDATE** | LLM 低置信度候选 | 待验证关系 | 后续迭代、人工审核 |
| **RELATED_TO** | TTL relateTo 数据 | 知识点关联 | 知识扩展、可视化 |
| **SUB_CATEGORY** | TTL subCategory 数据 | 分类层级 | 分类导航 |

**核心原则**：教学顺序 ≠ 学习依赖