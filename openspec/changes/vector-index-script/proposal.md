## Why

当前向量检索器 `LocalVectorRetriever` 在 `match_all()` 方法中懒加载初始化，每次运行匹配脚本都需要重新加载模型并计算向量索引，耗时约 30-60 秒。

将向量索引做成单独脚本，可以：
1. **预构建索引**：一次构建，多次使用
2. **节省时间**：避免每次匹配都重新加载模型
3. **灵活调试**：独立测试向量检索效果

## What Changes

- 创建独立的向量索引构建脚本 `build_vector_index.py`
- 索引文件保存到 `output/vector_index/` 目录
- `KPMatcher` 支持加载预构建的索引文件
- 新增命令行参数 `--use-prebuilt-index`

## Capabilities

### New Capabilities

- `vector-index-build`: 向量索引构建脚本，支持预构建和持久化存储

### Modified Capabilities

- `kp-matcher`: 知识点匹配器增加加载预构建索引的能力

## Impact

**新增文件**:
- `edukg/scripts/kg_data/build_vector_index.py` - 向量索引构建脚本
- `edukg/core/textbook/vector_index_manager.py` - 索引管理模块

**输出文件**:
- `output/vector_index/kg_vectors.npy` - 图谱知识点向量（numpy格式）
- `output/vector_index/kg_texts.json` - 知识点文本列表
- `output/vector_index/index_meta.json` - 索引元数据（模型名、维度、时间戳）

**修改文件**:
- `edukg/core/textbook/kp_matcher.py` - 新增 `load_vector_index()` 方法
- `openspec/changes/kg-math-complete-graph/tasks.md` - Task 16 更新