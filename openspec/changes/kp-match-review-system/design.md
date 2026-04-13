## Context

当前教材知识点匹配流程已完成，308 个知识点因颗粒度差异或图谱缺失无法自动匹配。这些知识点需要人工介入审核确认匹配关系。

**现状**:
- `matches_kg_relations.json` 包含 308 条未匹配记录
- 未匹配原因：297 条"投票不通过"（有候选但 LLM 认为不匹配），11 条"无候选通过"
- 需要人工审核确认是否匹配 EduKG 知识点或创建新知识点

**约束**:
- MySQL 已用于其他业务数据存储
- Neo4j 为知识图谱存储
- 需要与现有 Java 后端集成

## Goals / Non-Goals

**Goals:**
- 设计 MySQL 表存储未匹配知识点审核数据
- 提供批量导入未匹配数据到 MySQL 的脚本
- 设计 LLM 推荐匹配接口（复用现有双模型投票逻辑）
- 设计审核完成后导入 Neo4j 的流程

**Non-Goals:**
- 不设计前端 UI 实现（仅定义数据结构）
- 不修改现有匹配逻辑
- 不设计用户权限管理（假设审核人员已有权限）

## Decisions

### 1. MySQL 表设计

**决策**: 单表存储审核数据，包含审核状态字段

**表结构**: `textbook_kp_match_review`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT AUTO_INCREMENT | 主键 |
| textbook_kp_uri | VARCHAR(255) | 教材知识点 URI |
| textbook_kp_name | VARCHAR(100) | 教材知识点名称 |
| normalized_name | VARCHAR(100) | 标准化名称 |
| best_candidate_uri | VARCHAR(255) | LLM 最佳推荐 URI |
| best_candidate_name | VARCHAR(100) | LLM 最佳推荐名称 |
| candidate_list | JSON | 前 5 个候选列表 |
| confidence | DECIMAL(3,2) | LLM 置信度 |
| review_status | ENUM | pending/approved/rejected/new_kp |
| reviewer_action | VARCHAR(50) | confirm/reject/select_other/create_new |
| final_kg_uri | VARCHAR(255) | 最终确认的图谱 URI |
| reviewer_id | VARCHAR(50) | 审核人员 ID |
| review_time | DATETIME | 审核时间 |
| created_at | DATETIME | 创建时间 |

**备选方案**: 多表设计（审核表 + 候选表）- 拒绝原因：单表更简单，候选数量有限（最多 5 个）

### 2. 数据导入流程

**决策**: 在 `match_textbook_kp.py` 中直接保存未匹配知识点

**流程**:
```
match_textbook_kp.py 执行匹配
    ↓ 匹配完成后自动保存
unmatched_kps.json (308条未匹配知识点 + 候选列表)
    ↓ import_to_mysql.py
MySQL textbook_kp_match_review 表
```

**实现位置**: `edukg/scripts/kg_data/match_textbook_kp.py`

**修改内容**:
- 在 `KPMatchRunner.run_match()` 方法中，匹配完成后自动提取未匹配记录
- 输出 `unmatched_kps.json`（含 textbook_kp_uri, textbook_kp_name, normalized_name, best_candidate, confidence, reason）
- 与 `matches_kg_relations.json` 同时生成，无需额外脚本

### 3. LLM 推荐接口设计

**决策**: 复用 KPMatcher 现有逻辑，新增批量推荐接口

**接口**: `/api/kp-match/recommend`
- 输入: 教材知识点名称
- 输出: 前 5 个候选（含 URI、名称、相似度、置信度）

### 4. 审核结果导入 Neo4j

**决策**: 批量 Cypher 脚本导入

**流程**:
```
MySQL review_status=approved/rejected/new_kp
    ↓ export_review_results.py
reviewed_matches.json
    ↓ import_matches_to_neo4j.py
Neo4j MATCHES_KG 关系
```

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 审核人员可能批量确认错误 | 记录 reviewer_id 和 review_time，支持回溯 |
| 创建新知识点需要定义 URI | 使用 v3.2 版本前缀，与教材知识点区分 |
| LLM 推荐可能仍不准确 | 提供 5 个候选供人工选择，不强制最佳推荐 |