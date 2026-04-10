## 1. 创建目录结构

- [x] 1.1 创建 `edukg/core/textbook/` 目录
- [x] 1.2 创建 `edukg/core/textbook/__init__.py`
- [x] 1.3 创建输出目录 `edukg/data/edukg/math/5_教材目录/output/`

## 2. URI 生成模块

- [x] 2.1 创建 `edukg/core/textbook/uri_generator.py`
- [x] 2.2 实现 `URIGenerator` 类
- [x] 2.3 实现年级编码映射（一年级→g1, 七年级→g7, 必修第一册→bixiu1）
- [x] 2.4 实现学期编码映射（上册→s, 下册→x）
- [x] 2.5 实现 `textbook_id()` 方法
- [x] 2.6 实现 `chapter_id()` 方法
- [x] 2.7 实现 `section_id()` 方法
- [x] 2.8 实现 `textbookkp_uri()` 方法

## 3. 过滤规则模块

- [x] 3.1 创建 `edukg/core/textbook/filters.py`
- [x] 3.2 定义 `NON_KNOWLEDGE_POINT_MARKERS` 集合
- [x] 3.3 实现 `is_valid_knowledge_point()` 函数

## 4. 配置模块

- [x] 4.1 创建 `edukg/core/textbook/config.py`
- [x] 4.2 配置数据目录路径
- [x] 4.3 配置输出目录路径
- [x] 4.4 配置 URI 版本号（v3.1）

## 5. 数据生成模块

- [x] 5.1 创建 `edukg/core/textbook/data_generator.py`
- [x] 5.2 实现 `TextbookDataGenerator` 类
- [x] 5.3 实现 `discover_files()` 发现教材 JSON 文件
- [x] 5.4 实现小学 JSON 文件解析（grade1-6/shang.json, xia.json）
- [x] 5.5 实现初中 JSON 文件解析（grade7-9/shang.json, xia.json）
- [x] 5.6 实现高中 JSON 文件解析（bixiu1-3/textbook.json）
- [x] 5.7 实现 `generate_textbooks()` 生成教材节点
- [x] 5.8 实现 `generate_chapters()` 生成章节节点
- [x] 5.9 实现 `generate_sections()` 生成小节节点
- [x] 5.10 实现 `generate_textbook_kps()` 生成知识点节点（含过滤）
- [x] 5.11 实现 `generate_relations()` 生成关系数据
- [x] 5.12 实现 `generate_all()` 批量生成所有数据
- [x] 5.13 实现 JSON 文件输出

## 6. 知识点匹配模块

- [x] 6.1 创建 `edukg/core/textbook/kp_matcher.py`
- [x] 6.2 实现 `KPMatcher` 类
- [x] 6.3 实现精确匹配 `exact_match()`
- [x] 6.4 实现 LLM 匹配 `llm_match()`（调用 llm_inference 模块）
- [x] 6.5 实现 `match_all()` 批量匹配

## 7. 命令行入口 - 数据生成

- [x] 7.1 创建 `edukg/scripts/kg_data/generate_textbook_data.py`
- [x] 7.2 实现命令行参数解析（--stage, --stats, --dry-run）
- [x] 7.3 调用 `TextbookDataGenerator` 执行生成
- [x] 7.4 输出统计信息

## 8. 命令行入口 - 知识点匹配

- [x] 8.1 创建 `edukg/scripts/kg_data/match_textbook_kp.py`
- [x] 8.2 实现命令行参数解析
- [x] 8.3 加载 textbook_kps.json
- [x] 8.4 从 Neo4j 获取 EduKG Concept 列表
- [x] 8.5 调用 `KPMatcher` 执行匹配
- [x] 8.6 输出 matches_kg_relations.json

## 9. 单元测试

- [x] 9.1 创建 `tests/core/textbook/` 测试目录
- [x] 9.2 测试 `URIGenerator` 各方法
- [x] 9.3 测试 `is_valid_knowledge_point()`
- [x] 9.4 测试 `TextbookDataGenerator` 解析逻辑

## 10. 集成测试

- [x] 10.1 端到端测试：运行推理脚本
- [x] 10.2 验证输出文件格式
- [x] 10.3 验证节点数量符合预期
- [x] 10.4 验证关系完整性

## 11. 验证和手动导入

- [ ] 11.1 人工验证 JSON 数据质量
- [ ] 11.2 准备 Cypher 导入脚本模板
- [ ] 11.3 手动导入 Neo4j
- [ ] 11.4 验证导入结果