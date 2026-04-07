# 教材知识点关联 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `textbook-concept-linking` 模块的所有业务场景，确保教材导入、知识点匹配、PDF OCR 等功能的正确性和健壮性。

### 1.2 测试方式
- **集成测试**：使用 pytest + httpx TestClient 调用真实 API 端点
- **数据库回滚**：使用 pytest fixture 配合 Neo4j 事务回滚
- **Mock LLM**：知识点匹配的 LLM 调用使用 Mock，其他真实数据库操作

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- 数据库：Neo4j 测试实例，事务自动回滚
- 环境：使用 `.env.test` 配置
- OCR：PaddleOCR CPU 版本

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_CHAPTER_NAME | 人教版_数学_七年级_上册_第一章_有理数 | 测试章节名 |
| TEST_CONCEPT_LABEL | 一元一次方程 | 测试知识点标签 |
| TEST_GRADE | 七年级 | 测试年级 |
| TEST_SEMESTER | 上册 | 测试学期 |
| TEST_STAGE | middle | 测试学段 |
| TEST_PDF_PAGES | 1-10 | 测试PDF页码范围 |
| TEST_SUBJECT | math | 测试学科 |

---

## 3. 测试用例清单

### 3.1 教材导入 (Textbook Import)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| TB-001 | 正常导入-按学段 | Neo4j 连接正常 | `stage: middle` | 返回 imported_count > 0 |
| TB-002 | 正常导入-全部 | Neo4j 连接正常 | 无参数 | 返回所有学段章节数量 |
| TB-003 | 正常导入-按年级学期 | Neo4j 连接正常 | `grade: 七年级, semester: 上册` | 返回指定年级学期章节 |
| TB-004 | 异常-学段参数错误 | 无 | `stage: invalid` | 抛出 10003 参数无效异常 |
| TB-005 | 异常-学期参数错误 | 无 | `semester: 中册` | 抛出 10003 参数无效异常 |
| TB-006 | 异常-教材文件不存在 | 教材文件缺失 | `grade: 不存在的年级` | 抛出 20001 教材文件不存在 |
| TB-007 | 异常-Neo4j连接失败 | Neo4j 服务停止 | 正常参数 | 抛出 20002 Neo4j 连接失败 |
| TB-008 | 边界-重复导入 | 章节已存在 | 同一章节再次导入 | MERGE 行为，不创建重复节点 |

### 3.2 查询章节列表 (Query Chapters)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| QC-001 | 正常查询-全部 | 数据已导入 | 无参数 | 返回 total > 0，包含章节列表 |
| QC-002 | 正常查询-按年级 | 数据已导入 | `grade: 七年级` | 返回七年级章节 |
| QC-003 | 正常查询-按学期 | 数据已导入 | `semester: 上册` | 返回上册章节 |
| QC-004 | 正常查询-模糊匹配 | 数据已导入 | `chapter_name: 有理数` | 返回包含"有理数"的章节 |
| QC-005 | 边界-无数据 | 数据库清空 | 正常参数 | 返回 total: 0，chapters: [] |
| QC-006 | 边界-组合查询 | 数据已导入 | `grade + semester` | 返回精确匹配结果 |

### 3.3 知识点匹配 (Concept Matching)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KM-001 | 正常匹配-精确匹配 | Concept 存在"一元一次方程" | `use_llm: false` | match_type: exact, confidence: 1.0 |
| KM-002 | 正常匹配-LLM模糊匹配 | 无精确匹配 | `use_llm: true` | match_type: fuzzy, confidence < 1.0 |
| KM-003 | 正常匹配-无匹配 | Concept 不存在 | `use_llm: true` | match_type: none, confidence: 0.0 |
| KM-004 | 正常匹配-生成报告 | 匹配完成 | 正常参数 | 返回匹配统计和详情 |
| KM-005 | 异常-LLM调用失败 | LLM 服务异常 | `use_llm: true` | 返回部分匹配结果，记录错误 |
| KM-006 | 边界-空知识点列表 | 章节无知识点 | 空章节 | match_rate: 0% |

### 3.4 确认关联关系 (Confirm Linking)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| CL-001 | 正常确认-已匹配Concept | Concept 存在 | `concept_labels: ["有理数"]` | created_relations: 1 |
| CL-002 | 正常确认-创建新Concept | Concept 不存在 | `create_missing: [{label: "凑十法"}]` | created_concepts: 1 |
| CL-003 | 正常确认-批量关联 | 多个知识点 | 多个 concept_labels | created_relations = 数量 |
| CL-004 | 异常-章节不存在 | 章节不存在 | `chapter_name: 不存在` | 抛出 20004 章节不存在 |
| CL-005 | 异常-Concept不存在且未创建 | Concept 不存在 | 仅传 concept_labels | 抛出 20003 Concept 不存在 |
| CL-006 | 边界-空知识点列表 | 无 | `concept_labels: []` | created_relations: 0 |

### 3.5 PDF OCR 识别 (PDF OCR)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| OCR-001 | 正常识别-完整PDF | PDF 文件有效 | PDF 文件 | 返回 total_pages, extracted text |
| OCR-002 | 正常识别-指定页码 | PDF 文件有效 | `pages: 1-10` | 仅返回指定页内容 |
| OCR-003 | 异常-文件格式错误 | 非 PDF 文件 | 其他格式文件 | 抛出 30001 文件格式错误 |
| OCR-004 | 异常-页码超出范围 | PDF 共 10 页 | `pages: 1-20` | 抛出 30003 页码范围无效 |
| OCR-005 | 异常-OCR引擎失败 | PaddleOCR 初始化失败 | PDF 文件 | 抛出 30002 OCR 引擎初始化失败 |
| OCR-006 | 边界-空PDF | PDF 无内容 | 空白 PDF | 返回 pages text 为空字符串 |
| OCR-007 | 边界-大文件 | 189 页 PDF | 全部页码 | 分批处理，返回完整内容 |

### 3.6 课标知识点提取 (Curriculum Extraction)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| CE-001 | 正常提取-数学课标 | 数学课标 PDF | `subject: math` | 返回按学段、领域组织的知识点 |
| CE-002 | 正常提取-结构化输出 | 提取完成 | 正常参数 | JSON 结构符合规范 |
| CE-003 | 异常-学科参数错误 | 无 | `subject: invalid` | 抛出 10003 参数无效 |
| CE-004 | 异常-文件格式错误 | 非 PDF | 其他格式 | 抛出 30001 文件格式错误 |
| CE-005 | 边界-空课标PDF | PDF 无课标内容 | 空内容 PDF | 返回 stages 为空数组 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10000 | SYSTEM_ERROR | 系统错误 |
| 10001 | INVALID_PARAMS | 参数错误 |
| 10002 | NOT_FOUND | 实体不存在 |
| 10003 | VALIDATION_FAILED | 参数校验失败 |
| 10004 | UNAUTHORIZED | 未登录 |
| 20001 | TEXTBOOK_FILE_NOT_FOUND | 教材文件不存在 |
| 20002 | NEO4J_CONNECTION_FAILED | Neo4j 连接失败 |
| 20003 | CONCEPT_NOT_FOUND | Concept 不存在 |
| 20004 | CHAPTER_NOT_FOUND | 章节不存在 |
| 30001 | INVALID_FILE_FORMAT | 文件格式错误 |
| 30002 | OCR_ENGINE_INIT_FAILED | OCR 引擎初始化失败 |
| 30003 | INVALID_PAGE_RANGE | 页码范围无效 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 教材导入 (Textbook Import) | 8 |
| 查询章节 (Query Chapters) | 6 |
| 知识点匹配 (Concept Matching) | 6 |
| 确认关联 (Confirm Linking) | 6 |
| PDF OCR | 7 |
| 课标提取 (Curriculum Extraction) | 5 |
| **总计** | **32** |

---

## 6. 测试执行顺序

测试按文件名和方法名顺序执行：

```
tests/kg/
├── test_textbook_import.py    # 教材导入测试
├── test_query_chapters.py     # 查询章节测试
├── test_concept_matching.py   # 知识点匹配测试
├── test_confirm_linking.py    # 确认关联测试
├── test_pdf_ocr.py            # PDF OCR 测试
└── test_curriculum_extraction.py # 课标提取测试
```

使用 pytest 默认执行顺序（文件名字母序）。

---

## 7. 辅助方法

### 7.1 创建测试章节节点
```python
def create_test_chapter(name: str, grade: str, semester: str) -> dict:
    """创建测试章节节点"""
    query = """
    MERGE (c:textbook_chapter {name: $name})
    SET c.grade = $grade, c.semester = $semester
    RETURN c
    """
    result = neo4j_session.run(query, name=name, grade=grade, semester=semester)
    return result.single()
```

### 7.2 创建测试 Concept 节点
```python
def create_test_concept(label: str) -> dict:
    """创建测试 Concept 节点"""
    query = """
    MERGE (c:Concept {label: $label})
    RETURN c
    """
    result = neo4j_session.run(query, label=label)
    return result.single()
```

### 7.3 创建认证头
```python
def create_auth_headers(user_id: int) -> dict:
    """创建 JWT 认证头"""
    token = create_access_token({"sub": user_id})
    return {"Authorization": f"Bearer {token}"}
```

### 7.4 Mock LLM 匹配响应
```python
def mock_llm_match(textbook_kp: str, concepts: list) -> dict:
    """Mock LLM 匹配响应"""
    if textbook_kp == "正数和负数的概念":
        return {"match_type": "fuzzy", "concept": "正数", "confidence": 0.8}
    return {"match_type": "none", "confidence": 0.0}
```

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/kg/test_textbook_import.py -v

# 运行单个测试方法
pytest tests/kg/test_textbook_import.py::test_import_by_stage -v

# 运行知识图谱模块所有测试
pytest tests/kg/ -v

# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=ai_edu_ai_service/core/kg --cov-report=term-missing

# 运行特定标记的测试
pytest -m "not slow"  # 排除慢速测试（如 OCR）
pytest -m "ocr"       # 仅运行 OCR 测试
```

---

## 9. 测试配置文件

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    ocr: marks OCR-related tests
    integration: marks integration tests
    unit: marks unit tests
```

### conftest.py (Neo4j fixture)
```python
@pytest.fixture(scope="function")
def neo4j_session():
    """Neo4j 测试会话，事务自动回滚"""
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    session = driver.session()
    session.begin_transaction()
    yield session
    session.rollback_transaction()
    session.close()
    driver.close()
```

---

*文档生成时间: 2026-04-07*