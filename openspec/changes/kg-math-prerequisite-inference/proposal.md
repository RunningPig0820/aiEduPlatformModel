> **执行顺序: 4/4** | **设计成本: 有** (LLM 调用 ~8,980次) | **前置依赖: kg-math-native-relations**

## Why

知识图谱的核心价值在于**学习依赖关系（PREREQUISITE）**，这是 AI 引导式答疑业务的关键数据。当前数据只有教学顺序（教材章节顺序），没有学习依赖关系。

学习依赖关系需要通过以下方式构建：
1. **定义依赖抽取**：从知识点定义文本中匹配其他知识点名称（强证据）
2. **LLM 多模型投票**：GLM-4-flash + DeepSeek 两模型一致才采纳
3. **关系融合**：合并多种证据来源

**重要区别**：
- **TEACHES_BEFORE ≠ PREREQUISITE**：教材教学顺序 ≠ 学习依赖
- 例：教材可能先教"集合"再教"函数"，但学"函数"不一定要先学"集合"

这是项目的**设计成本核心部分**，消耗 LLM API 资源。

## What Changes

1. **教学顺序推断脚本**
   - 基于教材章节顺序生成 TEACHES_BEFORE 关系
   - 仅同章节内部（跨章节不推断）
   - 输出 CSV

2. **定义依赖抽取脚本**
   - 从知识点定义文本匹配其他知识点名称
   - 生成 PREREQUISITE 关系（强证据）
   - 输出 CSV

3. **LLM 前置关系推断脚本**
   - 设计 LLM prompt（区分教学顺序 vs 学习依赖）
   - 两模型投票：GLM-4-flash + DeepSeek
   - 高置信度 → PREREQUISITE
   - 低置信度 → PREREQUISITE_CANDIDATE
   - 输出 CSV

4. **关系融合脚本**
   - 融合定义依赖 + LLM 多模型投票
   - 生成最终 PREREQUISITE 关系
   - 同时生成 EduKG 标准关系（先修_on）
   - 输出最终关系文件

5. **关系导入脚本**
   - 导入 TEACHES_BEFORE 关系
   - 导入 PREREQUISITE 关系
   - 导入 PREREQUISITE_CANDIDATE 关系
   - 导入 先修_on 关系
   - 验证 DAG 合规性（无环）

## Capabilities

### New Capabilities

- `teaches-before-inference`: 教学顺序推断能力，基于教材章节顺序
- `definition-dependency-extractor`: 定义依赖抽取能力，从定义文本匹配知识点
- `llm-prerequisite-inference`: LLM 前置关系推断能力，多模型投票机制
- `prerequisite-fusion`: 前置关系融合能力，合并多证据来源
- `prerequisite-importer`: 前置关系导入 Neo4j 能力，含 DAG 验证

### Modified Capabilities

- `llm-gateway`: 新增 `prerequisite_inference` scene 映射

## Impact

- **新脚本**: `infer_teaches_before.py`, `extract_definition_deps.py`, `infer_prerequisites_llm.py`, `fuse_prerequisites.py`, `import_prereq_to_neo4j.py`
- **中间文件**: `math_teaches_before.csv`, `math_definition_deps.csv`, `math_llm_prereq.csv`, `math_final_prereq.csv`
- **Neo4j**: 新增约 50,000+ 条关系（TEACHES_BEFORE, PREREQUISITE, PREREQUISITE_CANDIDATE, 先修_on）
- **LLM Gateway**: 新增 scene `prerequisite_inference`（GLM-4-flash + DeepSeek）
- **设计成本**: 约 4,490 × 2 模型 = 8,980 次 LLM 调用（使用免费/低成本模型）
- **依赖**: 依赖 `kg-math-native-relations` change 完成并测试通过