## 1. 更新 kg-neo4j-schema

- [ ] 1.1 更新 proposal.md：添加 TextbookKnowledgePoint 节点说明
- [ ] 1.2 更新 design.md：添加新的关系类型说明
- [ ] 1.3 更新 tasks.md：添加新节点类型的创建任务
- [ ] 1.4 更新 specs：添加 TextbookKnowledgePoint 节点定义

## 2. 更新 kg-math-knowledge-points

- [ ] 2.1 更新 proposal.md：添加教材导入和 LLM 匹配说明，更新执行顺序为 2/5
- [ ] 2.2 更新 design.md：添加 LLM 匹配设计决策
- [ ] 2.3 更新 tasks.md：添加教材解析、导入、LLM 匹配任务
- [ ] 2.4 添加 specs：textbook-json-parser, llm-kp-matcher
- [ ] 2.5 更新 api.md：添加教材查询接口

## 3. 清理 kg-math-complete-graph

- [ ] 3.1 将有用内容合并到 kg-math-knowledge-points
- [ ] 3.2 删除 kg-math-complete-graph change 目录

## 4. 更新其他 changes 的执行顺序

- [ ] 4.1 kg-math-native-relations：更新执行顺序为 3/5
- [ ] 4.2 kg-infrastructure-init：更新执行顺序为 4/5
- [ ] 4.3 kg-math-prerequisite-inference：更新执行顺序为 5/5

## 5. 验证更新

- [ ] 5.1 检查所有 changes 的执行顺序标记正确
- [ ] 5.2 检查依赖关系正确
- [ ] 5.3 检查 specs 完整性