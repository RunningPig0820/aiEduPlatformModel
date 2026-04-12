## 1. 索引管理模块

- [ ] 1.1 创建 `edukg/core/textbook/vector_index_manager.py`
- [ ] 1.2 实现 `VectorIndexManager` 类
- [ ] 1.3 实现 `build_index(kg_concepts)` 方法 - 构建向量索引
- [ ] 1.4 实现 `save_index(output_dir)` 方法 - 保存索引文件
- [ ] 1.5 实现 `load_index(output_dir)` 方法 - 加载预构建索引
- [ ] 1.6 实现 `get_checksum()` 方法 - 计算 Neo4j 数据校验和
- [ ] 1.7 实现 `is_index_valid()` 方法 - 检查索引是否过期

## 2. 索引构建脚本

- [ ] 2.1 创建 `edukg/scripts/kg_data/build_vector_index.py`
- [ ] 2.2 实现命令行参数解析（--status, --force, --model）
- [ ] 2.3 从 Neo4j 加载 EduKG Concept 列表
- [ ] 2.4 调用 `VectorIndexManager` 构建索引
- [ ] 2.5 输出索引文件到 `output/vector_index/`
- [ ] 2.6 实现 `--status` 命令显示索引状态
- [ ] 2.7 实现 checksum 检测逻辑

## 3. KPMatcher 集成

- [ ] 3.1 在 `KPMatcher.__init__` 添加 `use_prebuilt_index` 参数
- [ ] 3.2 实现 `load_vector_index()` 方法 - 加载预构建索引
- [ ] 3.3 修改 `_init_vector_retriever()` - 支持预构建索引路径
- [ ] 3.4 实现索引过期检测和警告
- [ ] 3.5 实现回退逻辑（预构建索引缺失时）

## 4. 匹配脚本更新

- [ ] 4.1 在 `match_textbook_kp.py` 添加 `--use-prebuilt-index` 参数
- [ ] 4.2 在 `match_textbook_kp.py` 添加 `--force-build-index` 参数
- [ ] 4.3 在 `match_textbook_kp.py` 添加 `--no-vector-retrieval` 参数
- [ ] 4.4 更新命令行帮助信息

## 5. kg-math-complete-graph 任务更新

- [ ] 5.1 更新 `kg-math-complete-graph/tasks.md` Task 16
- [ ] 5.2 添加向量索引构建步骤（Task 16.1-16.2）
- [ ] 5.3 更新匹配脚本使用预构建索引

## 6. 测试验证

- [ ] 6.1 测试向量索引构建脚本
- [ ] 6.2 测试 `--status` 命令输出
- [ ] 6.3 测试预构建索引加载
- [ ] 6.4 测试索引过期检测
- [ ] 6.5 测试回退逻辑