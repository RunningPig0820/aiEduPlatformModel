## Context

知识图谱构建流程需要重构，修正执行顺序问题。

### 当前问题

```
错误顺序：
Schema → 知识点(无教材) → 关系 → 基础设施 → 前置推断 → 教材关联(太晚!)

正确顺序：
Schema(含教材) → 教材导入 → 知识点(关联教材) → 关系 → 基础设施 → 前置推断
```

## Goals / Non-Goals

**Goals:**
1. 修正执行顺序，教材数据在第2步导入
2. 更新 kg-neo4j-schema，添加教材相关节点定义
3. 更新 kg-math-knowledge-points，添加教材关联逻辑
4. 清理 kg-math-complete-graph，合并到其他 change

**Non-Goals:**
1. 不修改 kg-math-native-relations（无需修改）
2. 不修改 kg-infrastructure-init（无需修改）
3. 不修改 kg-math-prerequisite-inference（无需修改）

## Decisions

### D1: 教材数据在 Schema 之后立即导入

**理由**：知识点导入时就需要教材信息，才能建立关联关系

### D2: 使用 LLM 匹配教材知识点与 SPARQL 知识点

**理由**：两套数据的知识点名称不一致，需要语义匹配

### D3: 合并 kg-math-complete-graph 到 kg-math-knowledge-points

**理由**：避免两阶段导入的复杂性，一个 change 完成知识点+教材关联

## Risks / Trade-offs

### R1: 已实现的 changes 可能需要修改代码

**缓解**：检查现有实现，评估修改范围

### R2: LLM 匹配准确率

**缓解**：使用置信度阈值，低置信度结果标记为人工审核

## Migration Plan

1. 更新 kg-neo4j-schema 的 artifacts
2. 更新 kg-math-knowledge-points 的 artifacts
3. 删除 kg-math-complete-graph change
4. 更新所有 change 的执行顺序标记

## Open Questions

无