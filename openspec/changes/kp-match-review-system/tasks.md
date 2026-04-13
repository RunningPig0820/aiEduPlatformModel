## 1. 未匹配知识点保存（match_textbook_kp.py）

**目标**: 在匹配脚本中直接保存未匹配知识点，无需额外提取脚本

- [ ] 1.1 在 `match_textbook_kp.py` 的 `KPMatchRunner.run_match()` 方法中添加未匹配保存逻辑
- [ ] 1.2 提取 `matches_kg_relations.json` 中 `matched=false` 的记录
- [ ] 1.3 输出 `unmatched_kps.json`（含 textbook_kp_uri, textbook_kp_name, normalized_name, best_candidate, confidence, similarity, reason）
- [ ] 1.4 验证输出：308 条未匹配记录，候选列表完整

## 2. MySQL 数据存储

- [ ] 2.1 创建 MySQL 表 `textbook_kp_match_review`（DDL 脚本）
- [ ] 2.2 执行表创建（确认表结构正确）
- [ ] 2.3 创建 `import_to_mysql.py` 导入 `unmatched_kps.json`
- [ ] 2.4 验证导入结果（308 条记录，review_status=pending）

## 3. LLM 推荐接口

- [ ] 3.1 创建 `/api/kp-match/recommend` 接口（FastAPI）
- [ ] 3.2 复用 KPMatcher 向量检索逻辑
- [ ] 3.3 复用 KPMatcher 双模型投票逻辑
- [ ] 3.4 返回前 5 个候选（含 URI、名称、相似度、置信度）
- [ ] 3.5 处理 LLM 调用异常（超时、无候选）
- [ ] 3.6 测试接口：输入"分数除法意义"，返回候选列表

## 4. 人工审核页面

- [ ] 4.1 创建审核页面 Vue 组件（pending 列表展示）
- [ ] 4.2 实现详情弹窗（显示 textbook_kp_name、候选列表）
- [ ] 4.3 实现"确认匹配"按钮（更新 review_status=approved）
- [ ] 4.4 实现"选择其他候选"功能（下拉候选列表）
- [ ] 4.5 实现"拒绝匹配"按钮（更新 review_status=rejected）
- [ ] 4.6 实现"创建新知识点"按钮（生成新 URI）
- [ ] 4.7 记录 reviewer_id 和 review_time
- [ ] 4.8 测试审核流程（模拟审核 5 条记录）

## 5. Neo4j 导入

- [ ] 5.1 创建 `export_review_results.py` 从 MySQL 导出审核结果
- [ ] 5.2 输出 `reviewed_matches.json`（approved 和 new_kp）
- [ ] 5.3 创建 `import_matches_to_neo4j.py` Cypher 导入脚本
- [ ] 5.4 实现 MATCHES_KG 关系创建（approved 匹配）
- [ ] 5.5 实现新 Concept 节点创建（new_kp）
- [ ] 5.6 实现新 Concept MATCHES_KG 关系创建
- [ ] 5.7 添加 relation 属性：confidence, method="manual_review"
- [ ] 5.8 验证导入结果（Cypher 统计 MATCHES_KG 关系数量）

## 6. 集成测试

- [ ] 6.1 完整流程测试：match_textbook_kp.py → import_mysql → review → export → import_neo4j
- [ ] 6.2 验证 308 条记录完整处理
- [ ] 6.3 验证 Neo4j 关系正确性
- [ ] 6.4 文档更新：README 添加审核流程说明