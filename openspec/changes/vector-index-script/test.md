# 向量索引脚本测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `build_vector_index.py` 和 `match_textbook_kp.py` 新增参数的功能正确性。

### 1.2 测试方式
- **命令行测试**：直接执行脚本验证输出
- **文件验证**：检查生成的索引文件是否正确
- **集成测试**：验证 KPMatcher 加载预构建索引的功能

### 1.3 测试环境配置
- Python 3.11+
- Neo4j 测试数据库
- sentence-transformers 已安装

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_MODEL | BAAI/bge-small-zh-v1.5 | 默认测试模型 |
| TEST_TOP_N | 20 | 默认候选数量 |
| TEST_INDEX_DIR | output/vector_index/ | 索引输出目录 |

---

## 3. 测试用例清单

### 3.1 build_vector_index.py

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| BUILD-001 | 正常构建索引 | Neo4j 有数据 | 无参数 | 输出 4 个索引文件 |
| BUILD-002 | 查看索引状态 | 索引已存在 | `--status` | 显示 model_name, concept_count, created_at |
| BUILD-003 | 强制重建索引 | 索引已存在 | `--force` | 重建并覆盖现有索引 |
| BUILD-004 | 使用自定义模型 | 无 | `--model BAAI/bge-large-zh` | 使用指定模型构建 |
| BUILD-005 | 索引不存在时查看状态 | 索引不存在 | `--status` | 提示索引不存在 |
| BUILD-006 | Neo4j 无数据时构建 | Neo4j 无数据 | 无参数 | 提示无知识点数据 |

### 3.2 match_textbook_kp.py - 新增参数

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MATCH-001 | 使用预构建索引 | 索引已存在 | `--use-prebuilt-index` | 加载预构建索引，不重新初始化模型 |
| MATCH-002 | 预构建索引不存在 | 索引不存在 | `--use-prebuilt-index` | 警告并回退到懒加载 |
| MATCH-003 | 预构建索引过期 | checksum 不匹配 | `--use-prebuilt-index` | 警告索引过期，建议重建 |
| MATCH-004 | 强制重建后匹配 | 无 | `--force-build-index` | 先构建索引再匹配 |
| MATCH-005 | 禁用向量检索 | 无 | `--no-vector-retrieval` | 使用 difflib 粗筛 |

### 3.3 VectorIndexManager

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| VIM-001 | 构建索引 | kg_concepts 列表 | `build_index(concepts)` | 向量矩阵 shape=(N, 512) |
| VIM-002 | 保存索引 | 索引已构建 | `save_index(output_dir)` | 生成 4 个文件 |
| VIM-003 | 加载索引 | 索引文件存在 | `load_index(output_dir)` | 返回 vectors, texts, concepts |
| VIM-004 | 计算checksum | Neo4j 有数据 | `get_checksum()` | 返回 MD5 checksum |
| VIM-005 | 检验索引有效性 | checksum 已存储 | `is_index_valid()` | 返回 True/False |

---

## 4. 错误码对照表

| 错误类型 | 说明 |
|---------|------|
| IndexNotFoundError | 预构建索引文件不存在 |
| IndexOutdatedError | 索引已过期（checksum 不匹配） |
| ModelNotFoundError | Embedding 模型下载失败 |
| Neo4jConnectionError | Neo4j 连接失败 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| build_vector_index.py | 6 |
| match_textbook_kp.py | 5 |
| VectorIndexManager | 5 |
| **总计** | **16** |

---

## 6. 测试执行顺序

```
tests/core/textbook/
├── test_vector_index_manager.py   # VectorIndexManager 单元测试
├── test_build_vector_index.py     # build_vector_index.py CLI 测试
└── test_kp_matcher_prebuilt.py    # KPMatcher 预构建索引测试
```

---

## 7. 辅助方法

### 7.1 创建测试索引
```python
def create_test_index(kg_concepts: List[Dict]) -> Path:
    """创建测试用向量索引"""
    manager = VectorIndexManager()
    manager.build_index(kg_concepts)
    output_dir = Path("output/vector_index_test/")
    manager.save_index(output_dir)
    return output_dir
```

### 7.2 模拟 Neo4j 数据
```python
def mock_kg_concepts() -> List[Dict]:
    """模拟图谱知识点数据"""
    return [
        {"uri": "test-1", "label": "加法", "description": "数学运算"},
        {"uri": "test-2", "label": "减法", "description": "数学运算"},
        {"uri": "test-3", "label": "乘法", "description": "数学运算"},
    ]
```

---

## 8. 运行测试

```bash
# 运行单元测试
pytest tests/core/textbook/test_vector_index_manager.py -v

# 运行所有向量索引测试
pytest tests/core/textbook/ -k "vector" -v

# 运行并显示覆盖率
pytest tests/core/textbook/ --cov=edukg.core.textbook --cov-report=term-missing
```