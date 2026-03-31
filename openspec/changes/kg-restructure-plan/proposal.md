> **类型**: 重构规划 | **优先级**: 高 | **影响范围**: 所有 kg-* changes

## Why

当前知识图谱构建流程存在**执行顺序问题**：

### 问题 1：教材-知识点关联位置错误

当前顺序：
```
1. kg-neo4j-schema           → Schema 初始化
2. kg-math-knowledge-points  → 知识点导入（无教材关联）
3. kg-math-native-relations  → 原生关系导入
4. kg-infrastructure-init    → 基础设施
5. kg-math-prerequisite-inference → 前置关系推断
6. kg-math-complete-graph    → 教材-知识点关联 ← 位置太晚！
```

**问题**：知识点导入时没有教材信息，导致：
- 知识点节点缺少 `grade`、`textbook` 属性
- 无法回答"某知识点在哪个年级学习"
- 后期需要额外关联操作

### 问题 2：前面 changes 需要更新

| Change | 当前状态 | 需要更新 |
|--------|---------|---------|
| kg-neo4j-schema | 已定义 | ✅ 需要添加 Textbook, Chapter 节点定义 |
| kg-math-knowledge-points | 已定义 | ✅ 需要添加教材关联逻辑 |
| kg-math-native-relations | 已定义 | ❌ 无需修改 |
| kg-infrastructure-init | 已定义 | ❌ 无需修改 |
| kg-math-prerequisite-inference | 已定义 | ❌ 无需修改 |
| kg-math-complete-graph | 刚创建 | ❌ 应该提前到第2步 |

### 正确的执行顺序

```
1. kg-neo4j-schema (更新)
   → Schema 初始化 + Textbook/Chapter 节点定义

2. kg-textbook-import (新增)
   → 教材数据解析和导入（24册教材 + 章节）

3. kg-math-knowledge-points (更新)
   → 知识点导入 + 自动关联教材章节

4. kg-math-native-relations
   → 原生关系导入（无变化）

5. kg-infrastructure-init
   → 基础设施（无变化）

6. kg-math-prerequisite-inference
   → 前置关系推断（无变化）
```

## What Changes

### 需要更新的 Changes

1. **kg-neo4j-schema**
   - 添加 Textbook 节点定义
   - 添加 Chapter 节点定义
   - 添加 TextbookKnowledgePoint 节点定义
   - 添加关系类型：HAS_CHAPTER, USES_KNOWLEDGE_POINT, MAPPED_TO

2. **kg-math-knowledge-points**
   - 解析教材 JSON 数据
   - 导入 Textbook/Chapter 节点
   - 知识点导入时自动匹配教材章节
   - 使用 LLM 进行知识点名称匹配

### 需要新增的 Changes

无（将 kg-math-complete-graph 内容合并到 kg-math-knowledge-points）

### 需要删除的 Changes

- **kg-math-complete-graph** - 内容合并到其他 change

## Capabilities

### Modified Capabilities

- `neo4j-schema`: 添加 Textbook, Chapter, TextbookKnowledgePoint 节点定义
- `knowledge-point-importer`: 添加教材关联能力，支持 LLM 名称匹配

### New Capabilities

- `textbook-data-parser`: 教材数据解析能力（从 kg-math-complete-graph 合并）
- `llm-textbook-kp-matcher`: LLM 知识点匹配能力（从 kg-math-complete-graph 合并）

## Impact

- **kg-neo4j-schema**: 需要更新 proposal.md, design.md, tasks.md
- **kg-math-knowledge-points**: 需要更新所有 artifacts，添加教材关联逻辑
- **kg-math-complete-graph**: 应该删除，内容合并到其他 change
- **执行顺序**: 所有的顺序标记需要更新