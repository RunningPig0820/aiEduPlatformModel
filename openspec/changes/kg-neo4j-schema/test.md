# Neo4j Schema 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 Neo4j schema 初始化和验证脚本的所有场景，确保功能的正确性和健壮性。

### 1.2 测试方式
- **单元测试**：使用 pytest 测试脚本逻辑
- **集成测试**：使用 Neo4j 测试容器（testcontainers）进行真实数据库测试
- **Mock 测试**：使用 unittest.mock 模拟 Neo4j 连接错误场景

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- Neo4j 测试：使用 `testcontainers` 创建临时容器（每次测试独立环境）
- 环境变量：使用 `.env.test` 配置测试数据库连接
- **重要**：测试使用独立临时容器，不影响生产数据库数据

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_NEO4J_URI | bolt://localhost:7687 | 测试 Neo4j 连接 URI（仅用于 testcontainers） |
| TEST_NEO4J_USER | neo4j | 测试用户名 |
| TEST_NEO4J_PASSWORD | test_password | 测试密码 |
| EXPECTED_LABELS_COUNT | 6 | 预期节点标签数量 |
| EXPECTED_INDEXES_COUNT | 0 | 预期索引数量（索引延迟到数据导入后创建） |
| EXPECTED_CONSTRAINTS_COUNT | 3 | 预期约束数量 |
| **安全要求** | testcontainers | 使用临时容器，不连接生产数据库 |

---

## 3. 测试用例清单

### 3.1 Schema 创建脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| SCHEMA-001 | 正常创建所有 schema 元素 | Neo4j 服务运行，数据库为空 | 执行 `create_neo4j_schema.py` | 成功创建 6 个标签、0 个索引、3 个约束 |
| SCHEMA-002 | Dry-run 模式 | 无 | `--dry-run` 参数 | 仅打印 Cypher 语句，不执行 |
| SCHEMA-003 | 重复执行（幂等性） | Schema 已存在 | 再次执行脚本 | 跳过已存在的元素，不报错 |
| SCHEMA-004 | 连接失败处理 | Neo4j 服务未启动 | 执行脚本 | 抛出 ConnectionError 异常 |
| SCHEMA-005 | 认证失败处理 | 错误的密码 | 错误密码参数 | 抛出 AuthError 异常 |

### 3.2 Schema 验证脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| VALIDATE-001 | 验证成功 | Schema 完整创建 | 执行 `validate_schema.py` | 输出成功报告，退出码 0 |
| VALIDATE-002 | 验证失败-缺少标签 | 部分标签未创建 | 执行验证脚本 | 输出失败报告，列出缺失标签，退出码 1 |
| VALIDATE-003 | 验证失败-缺少约束 | 部分约束未创建 | 执行验证脚本 | 输出失败报告，列出缺失约束，退出码 1 |
| VALIDATE-004 | 详细模式输出 | Schema 完整创建 | `--verbose` 参数 | 显示每个元素的详细信息 |
| VALIDATE-005 | 连接失败处理 | Neo4j 服务未启动 | 执行验证脚本 | 抛出 ConnectionError 异常 |

### 3.3 main.ttl 拆分脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MAIN-SPLIT-001 | 正常拆分 main.ttl | main.ttl 文件存在 | 执行 `split_main_ttl.py` | 成功生成 8+ 个学科文件 |
| MAIN-SPLIT-002 | 自动发现学科 | main.ttl 文件存在 | `--auto-discover` 参数 | 自动检测学科并拆分 |
| MAIN-SPLIT-003 | 三元组数量验证 | 拆分完成 | 检查日志 | 原始文件三元组数 = 各文件总和 |
| MAIN-SPLIT-004 | 指定学科列表 | main.ttl 文件存在 | `--subjects math,physics` | 仅拆分指定学科 |
| MAIN-SPLIT-005 | URI 学科提取 | 各种 URI 格式 | 调用 extract_subject_from_uri | 正确提取学科或返回 "unknown" |

### 3.4 material.ttl 拆分脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MAT-SPLIT-001 | 正常拆分 material.ttl | material.ttl 文件存在 | 执行 `split_material_ttl.py` | 成功生成 9+ 个学科文件 |
| MAT-SPLIT-002 | 教材名称学科提取 | 各种教材名称 | 调用 extract_subject_from_name | 正确提取学科关键词 |
| MAT-SPLIT-003 | 三元组数量验证 | 拆分完成 | 检查日志 | 原始文件三元组数 = 各文件总和 |
| MAT-SPLIT-004 | 未知学科处理 | 存在无法识别的教材 | 执行拆分 | 生成 material-unknown.ttl |
| MAT-SPLIT-005 | 章节关联分组 | 教材有关联章节 | 执行拆分 | 章节随教材归入对应学科 |

### 3.5 集成测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| INTEGRATE-001 | 创建后验证流程 | Neo4j 数据库为空 | 1. 执行 schema 创建 2. 执行验证 | 验证成功，退出码 0 |
| INTEGRATE-002 | 知识点节点创建验证 | Schema 已创建 | 创建 KnowledgePoint 节点 | 成功创建节点 |
| INTEGRATE-003 | URI 唯一性约束验证 | Schema 已创建，已有节点 | 创建重复 URI 的节点 | 盛止创建，抛出约束冲突异常 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 0 | EXIT_SUCCESS | 脚本执行成功 |
| 1 | EXIT_FAILURE | 脚本执行失败 |
| CONNECTION_ERROR | ConnectionError | Neo4j 连接失败 |
| AUTH_ERROR | AuthError | Neo4j 认证失败 |
| CONSTRAINT_ERROR | ConstraintError | 约束冲突 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| Schema 创建脚本 | 5 |
| Schema 验证脚本 | 5 |
| main.ttl 拆分脚本 | 5 |
| material.ttl 拆分脚本 | 5 |
| 集成测试 | 3 |
| **总计** | **23** |

---

## 6. 测试执行顺序

测试按文件名和方法名顺序执行：

```
tests/kg_construction/
  test_split_main_ttl.py     : main.ttl 拆分测试
  test_split_material_ttl.py : material.ttl 拆分测试
  test_create_schema.py      : Schema 创建脚本测试
  test_validate_schema.py    : Schema 验证脚本测试
  test_integration.py        : 集成测试
```

---

## 7. 辅助方法

### 7.1 创建 Neo4j 测试连接
```python
from testcontainers.neo4j import Neo4jContainer

def get_test_neo4j_connection():
    """创建 Neo4j 测试容器连接（临时容器，测试结束后自动销毁）"""
    container = Neo4jContainer("neo4j:5.12")
    container.start()
    driver = container.get_driver()
    return driver, container

def stop_test_container(container):
    """停止并销毁测试容器（测试结束后调用）"""
    container.stop()
```

**重要**：每次测试使用独立临时容器，测试结束后自动销毁，不影响生产数据。

### 7.2 ~~清理测试 Schema~~（已移除）

**安全策略**：不再提供 cleanup_schema 方法，防止误删生产数据。

- 测试使用 `testcontainers` 临时容器，容器销毁时数据自动清除
- **禁止**在生产数据库上运行测试
- **禁止**手动删除 schema 或节点数据

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/kg_construction/test_create_schema.py -v

# 运行单个测试方法
pytest tests/kg_construction/test_create_schema.py::test_create_schema_success -v

# 运行所有 kg_construction 测试
pytest tests/kg_construction/ -v

# 运行并显示覆盖率
pytest tests/kg_construction/ --cov=scripts/kg_construction --cov-report=term-missing
```