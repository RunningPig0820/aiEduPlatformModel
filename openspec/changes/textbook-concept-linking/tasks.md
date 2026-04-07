## 1. 项目结构初始化

- [ ] 1.1 创建 `ai-edu-ai-service/core/kg/textbook/` 目录结构
- [ ] 1.2 创建 `ai-edu-ai-service/core/ocr/` 目录结构
- [ ] 1.3 添加 PaddleOCR 依赖到 requirements.txt

## 2. 教材解析服务 (textbook-import)

- [ ] 2.1 实现 `TextbookParser` 类，解析教材 JSON 文件
- [ ] 2.2 实现 `TextbookImporter` 类，创建 Chapter 节点到 Neo4j
- [ ] 2.3 实现 `import_all_textbooks()` 批量导入功能
- [ ] 2.4 实现 `query_chapters()` 查询功能（按年级、学期）

## 3. 知识点关联服务 (concept-linking)

- [ ] 3.1 实现 `ConceptLinker` 类，精确匹配知识点
- [ ] 3.2 集成 LLM 实现模糊匹配功能
- [ ] 3.3 实现 `generate_matching_report()` 输出匹配报告
- [ ] 3.4 实现 `create_contains_relation()` 创建关联关系
- [ ] 3.5 实现 `create_missing_concept()` 创建缺失知识点

## 4. PDF OCR 服务 (pdf-ocr)

- [ ] 4.1 实现 `PDFOCRService` 类，初始化 PaddleOCR
- [ ] 4.2 实现 `extract_text()` 从 PDF 提取文字
- [ ] 4.3 实现 `extract_curriculum_points()` 提取课标知识点
- [ ] 4.4 添加 OCR 配置支持（语言、角度分类等）

## 5. API 接口

- [ ] 5.1 创建 `/api/kg/textbook/import` 导入教材接口
- [ ] 5.2 创建 `/api/kg/textbook/chapters` 查询章节接口
- [ ] 5.3 创建 `/api/kg/textbook/link` 知识点关联接口
- [ ] 5.4 创建 `/api/ocr/pdf` PDF OCR 接口
- [ ] 5.5 创建 `/api/ocr/curriculum` 课标提取接口

## 6. 测试

- [ ] 6.1 编写 `TextbookParser` 单元测试
- [ ] 6.2 编写 `TextbookImporter` 单元测试
- [ ] 6.3 编写 `ConceptLinker` 单元测试
- [ ] 6.4 编写 `PDFOCRService` 单元测试
- [ ] 6.5 编写 API 集成测试

## 7. 文档与部署

- [ ] 7.1 更新 README.md 记录新增模块
- [ ] 7.2 编写 API 文档
- [ ] 7.3 验证教材数据导入结果
- [ ] 7.4 验证知识点关联结果