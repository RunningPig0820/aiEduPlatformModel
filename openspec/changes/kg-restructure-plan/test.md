# 知识图谱重构规划 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证知识图谱构建流程重构的正确性，确保各 change 的执行顺序和依赖关系正确。

### 1.2 测试方式
- **文档验证**：检查所有 change 的 artifacts 是否正确更新
- **依赖关系验证**：检查 changes 之间的依赖关系是否正确

---

## 2. 测试用例清单

### 2.1 文档一致性测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| DOC-001 | kg-neo4j-schema 更新验证 | change 存在 | 读取 proposal.md | 包含 TextbookKnowledgePoint 节点说明 |
| DOC-002 | kg-math-knowledge-points 更新验证 | change 存在 | 读取 proposal.md | 包含教材导入和 LLM 匹配说明 |
| DOC-003 | 执行顺序验证 | 所有 changes 存在 | 读取所有 proposal.md | 顺序标记正确 (1/5 到 5/5) |

### 2.2 Schema 完整性测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| SCH-001 | TextbookKnowledgePoint 节点定义 | schema 初始化 | 检查 specs | 包含属性定义 |
| SCH-002 | USES_KNOWLEDGE_POINT 关系定义 | schema 初始化 | 检查 specs | 包含关系类型定义 |
| SCH-003 | MAPPED_TO 关系定义 | schema 初始化 | 检查 specs | 包含关系类型定义 |

### 2.3 依赖关系测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| DEP-001 | kg-math-knowledge-points 依赖 kg-neo4j-schema | changes 存在 | 检查 proposal.md | 依赖声明正确 |
| DEP-002 | kg-math-native-relations 依赖 kg-math-knowledge-points | changes 存在 | 检查 proposal.md | 依赖声明正确 |
| DEP-003 | kg-infrastructure-init 依赖 kg-math-native-relations | changes 存在 | 检查 proposal.md | 依赖声明正确 |
| DEP-004 | kg-math-prerequisite-inference 依赖 kg-infrastructure-init | changes 存在 | 检查 proposal.md | 依赖声明正确 |

---

## 3. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 文档一致性测试 | 3 |
| Schema 完整性测试 | 3 |
| 依赖关系测试 | 4 |
| **总计** | **10** |

---

## 4. 运行测试

```bash
# 运行文档验证测试
pytest tests/kg/test_restructure_plan.py -v

# 运行所有验证
pytest tests/kg/ -v -m "restructure"
```