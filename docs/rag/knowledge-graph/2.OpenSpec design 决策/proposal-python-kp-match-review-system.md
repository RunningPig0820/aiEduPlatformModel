## Why

教材知识点与 EduKG 知识图谱匹配过程中，有 308 个知识点因颗粒度差异或图谱缺失无法自动匹配。这些未匹配知识点需要人工介入审核，但目前缺乏工程化工具支持人工审核流程。

需要一个完整的审核系统来管理未匹配知识点的处理流程：数据存储、LLM 推荐、人工审核、最终建立关系。

## What Changes

- 新增 MySQL 表存储未匹配知识点及审核状态
- 新增 LLM 推荐匹配接口，为审核提供候选建议
- 新增 Web 审核页面，支持人工确认/修正匹配结果
- 新增审核完成后批量导入 Neo4j 的脚本

## Capabilities

### New Capabilities

- `unmatched-kp-storage`: 未匹配知识点数据存储（MySQL 表设计、数据导出导入）
- `llm-match-recommendation`: LLM 推荐匹配候选接口
- `kp-review-ui`: 人工审核 Web 页面（审核列表、候选推荐、确认/修正操作）
- `review-result-import`: 审核结果导入 Neo4j 脚本

### Modified Capabilities

无（新增独立系统，不修改现有 spec）

## Impact

- **新增 MySQL 表**: `textbook_kp_match_review`（存储审核数据）
- **新增 API 接口**: LLM 推荐匹配、审核结果提交
- **新增前端页面**: 人工审核界面
- **依赖现有数据**: `matches_kg_relations.json`（308 条未匹配记录）
- **最终输出**: Neo4j MATCHES_KG 关系（审核通过的匹配）