# 知识图谱模块测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证知识图谱模块的所有业务场景，确保功能的正确性和健壮性。

### 1.2 测试方式
- **集成测试**：使用 pytest + FastAPI TestClient 调用真实 API 端点
- **数据库**：使用真实 Neo4j 实例（已导入 EDUKG 数据）
- **只读测试**：不创建/删除测试数据，只验证查询功能

### 1.3 测试环境配置

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# conftest.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def neo4j_client():
    """获取 Neo4j 客户端（只读操作）"""
    from core.neo4j import get_neo4j_client
    return get_neo4j_client()
```

---

## 2. 测试数据（使用真实 EDUKG 数据）

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_SUBJECT | math | 测试学科 |
| TEST_ENTITY_LABEL | 一元二次方程 | 真实知识点名称 |
| TEST_TEXT | 一元二次方程是初中数学的重要内容 | 测试文本 |

---

## 3. 测试用例清单

### 3.1 实体搜索测试 (KG-ENTITY)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-ENTITY-001 | 精确搜索-存在 | 实体存在 | label="一元二次方程", subject="math" | 返回匹配实体列表 |
| KG-ENTITY-002 | 模糊搜索-存在 | 实体存在 | label="方程", subject="math" | 返回包含"方程"的实体列表 |
| KG-ENTITY-003 | 搜索-不存在 | 无匹配实体 | label="不存在的知识点" | 返回空列表 |
| KG-ENTITY-004 | 搜索-无学科过滤 | 实体存在 | label="函数" | 返回所有学科匹配结果 |
| KG-ENTITY-005 | 搜索-无效学科 | 无 | label="方程", subject="invalid" | 返回 20001 错误 |
| KG-ENTITY-006 | 搜索-空参数 | 无 | label="" | 返回 10001 错误 |
| KG-ENTITY-007 | 搜索-limit边界 | 实体数量>100 | limit=100 | 返回最多100条 |
| KG-ENTITY-008 | 未授权访问 | 无Token | 无Authorization头 | 返回 10004 错误 |

### 3.2 实体详情测试 (KG-DETAIL)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-DETAIL-001 | 获取详情-成功 | 实体存在 | 有效URI | 返回实体详情+关系 |
| KG-DETAIL-002 | 获取详情-不存在 | URI不存在 | 无效URI | 返回 10002 错误 |
| KG-DETAIL-003 | 获取详情-无效URI | 无 | 格式错误的URI | 返回 10001 错误 |
| KG-DETAIL-004 | 获取详情-包含前置知识 | 实体有前置关系 | 有效URI | 返回prerequisites列表 |
| KG-DETAIL-005 | 获取详情-包含相关知识点 | 实体有相关关系 | 有效URI | 返回relatedTo列表 |

### 3.3 实体链接测试 (KG-LINK)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-LINK-001 | 链接-单个实体 | 实体存在 | text="一元二次方程很重要" | 返回1个实体 |
| KG-LINK-002 | 链接-多个实体 | 实体存在 | text="方程和函数都是重要概念" | 返回2个实体 |
| KG-LINK-003 | 链接-无匹配 | 无匹配实体 | text="这是一段普通文本" | 返回空列表 |
| KG-LINK-004 | 链接-学科过滤 | 实体跨学科存在 | text="函数", subject="math" | 只返回数学学科实体 |
| KG-LINK-005 | 链接-位置准确 | 实体存在 | text含多个实体 | 返回正确的start/end位置 |
| KG-LINK-006 | 链接-上下文增强 | 实体存在 | text, enrichContext=true | 返回实体context字段 |
| KG-LINK-007 | 链接-长文本 | 文本>5000字符 | 长文本 | 正常处理，返回所有实体 |
| KG-LINK-008 | 链接-空文本 | 无 | text="" | 返回 10001 错误 |

### 3.4 知识树测试 (KG-TREE)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-TREE-001 | 获取知识树-成功 | 学科存在 | subject="math" | 返回嵌套知识树 |
| KG-TREE-002 | 获取知识树-深度限制 | 学科存在 | depth=2 | 返回最多2层深度的树 |
| KG-TREE-003 | 获取知识树-无效学科 | 无 | subject="invalid" | 返回 20001 错误 |
| KG-TREE-004 | 获取知识树-深度边界 | 无 | depth=10 | 使用最大深度5 |

### 3.5 学生进度测试 (KG-PROGRESS) - 暂不测试

> 注：学生进度功能涉及动态数据写入，本次迭代暂不包含自动化测试，由业务层验证。

### 3.6 知识点推荐测试 (KG-RECOMMEND)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KG-RECOMMEND-001 | 推荐-基于知识点 | 实体存在 | entityUri有效 | 返回相关知识点列表 |
| KG-RECOMMEND-002 | 推荐-学科过滤 | 无 | subject="math" | 只返回数学推荐 |
| KG-RECOMMEND-003 | 推荐-无相关知识点 | 实体孤立 | entityUri有效 | 返回空列表 |

### 3.7 学习路径测试 (KG-PATH) - 暂不测试

> 注：学习路径依赖学生进度数据，本次迭代暂不包含自动化测试。

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10000 | SYSTEM_ERROR | 系统错误 |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10002 | NOT_FOUND | 资源不存在 |
| 10003 | VALIDATION_ERROR | 参数校验失败 |
| 10004 | UNAUTHORIZED | 未授权 |
| 20001 | SUBJECT_NOT_FOUND | 学科不存在 |
| 20002 | ENTITY_NOT_FOUND | 实体不存在 |
| 20003 | KG_SERVICE_UNAVAILABLE | 图谱服务不可用 |
| 20004 | STUDENT_NOT_FOUND | 学生不存在 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 实体搜索 (KG-ENTITY) | 8 |
| 实体详情 (KG-DETAIL) | 5 |
| 实体链接 (KG-LINK) | 8 |
| 知识树 (KG-TREE) | 4 |
| 知识点推荐 (KG-RECOMMEND) | 3 |
| **总计** | **28** |

> 注：学生进度 (KG-PROGRESS)、进度统计 (KG-STATS)、学习路径 (KG-PATH) 暂不测试

---

## 6. 测试执行顺序

测试按模块顺序执行：

```
tests/real/
├── conftest.py              # 公共 fixtures
└── test_kg_neo4j.py         # Neo4j 真实连接测试
```

---

## 7. 运行测试

```bash
# 运行知识图谱测试（真实 Neo4j）
pytest tests/real/test_kg_neo4j.py -v

# 运行单个测试用例
pytest tests/real/test_kg_neo4j.py::test_search_entities_success -v

# 运行并显示覆盖率
pytest tests/real/test_kg_neo4j.py --cov=core.kg --cov-report=term-missing
```

---

## 8. 持续集成配置

```yaml
# .github/workflows/test.yml
name: Knowledge Graph Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run KG tests
        env:
          NEO4J_URI: ${{ secrets.NEO4J_URI }}
          NEO4J_USER: ${{ secrets.NEO4J_USER }}
          NEO4J_PASSWORD: ${{ secrets.NEO4J_PASSWORD }}
        run: pytest tests/real/test_kg_neo4j.py -v --cov
```

---

*文档更新时间: 2026-03-27*