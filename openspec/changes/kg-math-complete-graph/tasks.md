## 1. 教材数据解析

- [ ] 1.1 创建 `parse_textbook_json.py` 脚本骨架
- [ ] 1.2 实现小学 JSON 文件解析（12册）
- [ ] 1.3 实现初中 JSON 文件解析（6册）
- [ ] 1.4 实现高中 JSON 文件解析（6册）
- [ ] 1.5 实现章节和知识点结构提取
- [ ] 1.6 输出标准化 `textbook_data.json` 文件
- [ ] 1.7 添加错误处理和日志记录

## 2. 教材章节导入 Neo4j

- [ ] 2.1 创建 `import_textbook_chapters.py` 脚本骨架
- [ ] 2.2 实现 Textbook 节点创建（24个）
- [ ] 2.3 实现 Chapter 节点创建（约300个）
- [ ] 2.4 实现 HAS_CHAPTER 关系创建
- [ ] 2.5 添加幂等性处理（MERGE 操作）
- [ ] 2.6 验证导入数据数量

## 3. LLM 教材-知识点匹配

- [ ] 3.1 创建 `match_textbook_kp_llm.py` 脚本骨架
- [ ] 3.2 实现从 Neo4j 获取候选知识点列表
- [ ] 3.3 设计 LLM prompt（按章节批量匹配）
- [ ] 3.4 实现章节批量匹配逻辑
- [ ] 3.5 实现匹配置信度分类（auto_mapped/needs_review/no_match）
- [ ] 3.6 集成 StateDB 支持断点续传
- [ ] 3.7 输出 `textbook_kp_matches.csv` 文件

## 4. 教材-知识点关联导入

- [ ] 4.1 创建 `link_textbook_kp.py` 脚本骨架
- [ ] 4.2 实现 TextbookKnowledgePoint 节点创建
- [ ] 4.3 实现 USES_KNOWLEDGE_POINT 关系创建
- [ ] 4.4 实现 MAPPED_TO 关系创建（仅高置信度匹配）
- [ ] 4.5 添加幂等性处理
- [ ] 4.6 验证关联完整性

## 5. 数据验证

- [ ] 5.1 创建 `validate_textbook_coverage.py` 脚本
- [ ] 5.2 实现教材覆盖率检查
- [ ] 5.3 实现知识点关联率检查
- [ ] 5.4 输出缺失报告（未匹配的知识点列表）
- [ ] 5.5 输出最终统计报告

## 6. 集成测试

- [ ] 6.1 端到端测试：教材数据解析 → 导入 → 匹配 → 关联
- [ ] 6.2 验证知识图谱完整性
- [ ] 6.3 验证 LLM 成本在预期范围内