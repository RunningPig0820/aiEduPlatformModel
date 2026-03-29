# 数学知识点数据清洗测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证数学知识点数据清洗、教材信息提取、数据合并和 Neo4j 导入的所有场景，确保功能的正确性和健壮性。

### 1.2 测试方式
- **单元测试**：使用 pytest 测试脚本逻辑
- **集成测试**：使用 Neo4j 测试容器进行真实数据库测试
- **Mock 测试**：使用 unittest.mock 模拟文件读取和 Neo4j 连接错误场景

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- Neo4j 测试：使用 `testcontainers` 或本地 Neo4j Docker 容器
- 测试数据：使用小型 TTL 文件（10-20 个知识点）进行快速测试

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_TTL_FILE | `tests/fixtures/test_math.ttl` | 测试 TTL 文件（20 个知识点） |
| EXPECTED_KP_COUNT | 20 | 预期测试知识点数量 |
| EXPECTED_TYPE_COVERAGE | 0.7 | 预期类型覆盖率阈值 |
| EXPECTED_MATCH_COVERAGE | 0.8 | 预期匹配覆盖率阈值 |

---

## 3. 测试用例清单

### 3.1 TTL 数据清洗脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| CLEAN-001 | 正常解析 TTL 文件 | TTL 文件存在，格式正确 | 执行 `clean_math_data.py` | 成功提取 20 个知识点，输出 JSON |
| CLEAN-002 | Unicode 解码 | TTL 包含 Unicode 编码中文 | 解码 Unicode 标签 | 输出可读中文 |
| CLEAN-003 | 类型提取 | 知识点有 rdf:type | 提取类型 | 类型映射为中文（定义/性质/定理等） |
| CLEAN-004 | 去重处理 | TTL 包含重复 URI | 去重 | 只保留唯一实体 |
| CLEAN-005 | 过滤无效数据 | 知识点缺少 name | 过滤 | 排除无效实体 |
| CLEAN-006 | 类型覆盖率验证 | 处理完成 | 验证覆盖率 | ≥70% 通过 |
| CLEAN-007 | 输出 JSON 格式验证 | 清洗完成 | 检查输出文件 | JSON 结构正确，包含必需字段 |
| CLEAN-008 | 文件不存在处理 | TTL 文件不存在 | 执行脚本 | 抛出 FileNotFoundError |

### 3.2 教材信息提取脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| EXTRACT-001 | 正常提取教材信息 | main.ttl 存在 | 执行 `extract_textbook_info.py` | 成功提取教材和章节 |
| EXTRACT-002 | 标签匹配 | 知识点与章节标签匹配 | 执行匹配 | 成功创建映射关系 |
| EXTRACT-003 | 年级推断-高中教材 | 匹配到高中教材 | 推断年级 | 正确推断为高一/高二/高三 |
| EXTRACT-004 | 年级推断-初中教材 | 匹配到初中教材 | 推断年级 | 正确推断为初一/初二/初三 |
| EXTRACT-005 | 未匹配处理 | 知识点无法匹配 | 标记未匹配 | 标记为 "年级未知" |
| EXTRACT-006 | 匹配覆盖率验证 | 匹配完成 | 验证覆盖率 | ≥80% 通过 |
| EXTRACT-007 | 输出 JSON 格式验证 | 提取完成 | 检查输出文件 | JSON 结构正确 |

### 3.3 数据合并脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| MERGE-001 | 正常合并数据 | 知识点和映射文件存在 | 执行 `merge_math_data.py` | 成功合并数据 |
| MERGE-002 | 年级字段填充 | 知识点有映射记录 | 合并 | grade 字段正确填充 |
| MERGE-003 | 章节字段填充 | 知识点有映射记录 | 合并 | chapter 字段正确填充 |
| MERGE-004 | 未匹配数据保留 | 知识点无映射记录 | 合并 | grade 字段为 null |
| MERGE-005 | 输出 JSON 格式验证 | 合并完成 | 检查输出文件 | 所有必需字段存在 |
| MERGE-006 | URI 不存在处理 | 合并时找不到 URI | 合并 | 警告日志，跳过 |

### 3.4 Neo4j 导入脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| IMPORT-001 | 正常导入层级结构 | Neo4j schema 已创建 | 导入层级节点 | 成功创建 Subject, Stage, Grade, Textbook, Chapter |
| IMPORT-002 | 正常导入知识点 | 层级节点已创建 | 导入知识点 | 成功创建 KnowledgePoint 节点 |
| IMPORT-003 | 批量导入 | 大量知识点数据 | 批量导入 | 使用 UNWIND 成功导入 |
| IMPORT-004 | 创建关系 | 知识点已导入 | 创建关系 | 成功创建 HAS_KNOWLEDGE_POINT 关系 |
| IMPORT-005 | 事务回滚 | 导入过程中出错 | 模拟错误 | 事务回滚，无残留数据 |
| IMPORT-006 | Dry-run 模式 | 无 | `--dry-run` 参数 | 仅打印 Cypher，不执行 |
| IMPORT-007 | 连接失败处理 | Neo4j 未启动 | 执行导入 | 抛出 ConnectionError |
| IMPORT-008 | 重复 URI 处理 | URI 已存在 | 导入重复 URI | 约束冲突异常 |

### 3.5 数据验证脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| VALIDATE-001 | 验证成功 | 数据完整导入 | 执行验证 | 输出成功报告，退出码 0 |
| VALIDATE-002 | 验证失败-节点数量不足 | 导入不完整 | 执行验证 | 输出失败报告，退出码 1 |
| VALIDATE-003 | 验证失败-URI 重复 | URI 有重复 | 执行验证 | 输出失败报告，退出码 1 |
| VALIDATE-004 | 验证失败-字段为空 | name 为空 | 执行验证 | 输出失败报告，退出码 1 |
| VALIDATE-005 | 验证失败-类型覆盖率不足 | 类型覆盖率 <70% | 执行验证 | 输出失败报告，退出码 1 |

### 3.6 集成测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| INTEGRATE-001 | 完整工作流程 | Neo4j schema 已创建 | 执行清洗→提取→合并→导入→验证 | 所有步骤成功，验证通过 |
| INTEGRATE-002 | 清洗失败回滚 | 清洗步骤失败 | 中断流程 | 不执行后续步骤 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 0 | EXIT_SUCCESS | 脚本执行成功 |
| 1 | EXIT_FAILURE | 脚本执行失败 |
| FILE_NOT_FOUND | FileNotFoundError | 输入文件不存在 |
| INVALID_JSON | JSONDecodeError | JSON 格式错误 |
| CONNECTION_ERROR | ConnectionError | Neo4j 连接失败 |
| CONSTRAINT_ERROR | ConstraintError | 约束冲突 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| TTL 数据清洗脚本 | 8 |
| 教材信息提取脚本 | 7 |
| 数据合并脚本 | 6 |
| Neo4j 导入脚本 | 8 |
| 数据验证脚本 | 5 |
| 集成测试 | 2 |
| **总计** | **36** |

---

## 6. 测试执行顺序

测试按文件名和方法名顺序执行：

```
tests/kg_construction/
  test_clean_math_data.py       : TTL 数据清洗脚本测试
  test_extract_textbook_info.py  : 教材信息提取脚本测试
  test_merge_math_data.py        : 数据合并脚本测试
  test_import_math_kp.py         : Neo4j 导入脚本测试
  test_validate_math_import.py   : 数据验证脚本测试
  test_integration.py            : 集成测试
```

---

## 7. 辅助方法

### 7.1 创建测试 TTL 文件
```python
def create_test_ttl_file(path: str) -> None:
    """创建测试 TTL 文件"""
    content = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix edukg: <http://edukg.org/ontology#> .

<http://edukg.org/knowledge/0.1/instance/math#1> a edukg:Definition ;
    edukg:name "一元二次方程" ;
    edukg:description "只含有一个未知数的二次方程" .
"""
    with open(path, "w") as f:
        f.write(content)
```

### 7.2 创建 Neo4j 测试连接
```python
from testcontainers.neo4j import Neo4jContainer

def get_test_neo4j_connection():
    """创建 Neo4j 测试容器连接"""
    container = Neo4jContainer("neo4j:5.12")
    container.start()
    driver = container.get_driver()
    return driver, container
```

### 7.3 清理测试数据
```python
def cleanup_test_data(driver):
    """清理测试数据"""
    with driver.session() as session:
        session.run("MATCH (n:KnowledgePoint {subject: 'test'}) DETACH DELETE n")
```

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/kg_construction/test_clean_math_data.py -v

# 运行单个测试方法
pytest tests/kg_construction/test_clean_math_data.py::test_clean_ttl_success -v

# 运行所有 kg_construction 测试
pytest tests/kg_construction/ -v

# 运行并显示覆盖率
pytest tests/kg_construction/ --cov=scripts/kg_construction --cov-report=term-missing
```