# 教材知识点关联 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 `textbook-concept-linking` 模块的所有业务场景，确保教材解析、知识点匹配、OCR 识别、LLM 提取功能的正确性。

### 1.2 测试方式
- **单元测试**：pytest 测试各服务类的方法
- **Mock 外部服务**：LLM、Neo4j 使用 Mock，OCR 使用小文件
- **集成测试**：完整流程测试，验证输出文件格式

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- LLM：使用 Mock 或 glm-4-flash（小文本）
- Neo4j：使用测试数据库或 Mock（只读查询）
- OCR：百度 OCR API（小文件测试）

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_TEXTBOOK | test_textbook.json | 测试用教材 JSON |
| TEST_PDF | test_curriculum.pdf | 测试用 PDF（3页） |
| TEST_OCR_RESULT | test_ocr.json | Mock OCR 结果 |
| TEST_STAGE | 第一学段 | 测试学段 |
| TEST_DOMAIN | 数与代数 | 测试领域 |
| TEST_KP | 20以内数的认识 | 测试知识点 |

---

## 3. 测试用例清单

### 3.1 教材解析服务

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| PARSE-001 | 正常解析-教材JSON | 教材文件有效 | 教材 JSON 文件 | 返回章节结构列表 |
| PARSE-002 | 正常解析-保存结果 | 解析完成 | 正常参数 | 生成 textbook_chapters.json |
| PARSE-003 | 异常-文件不存在 | 无 | 无效路径 | 抛出 FileNotFoundError |
| PARSE-004 | 异常-JSON格式错误 | JSON 格式错误 | 损坏的 JSON | 抛出 JSONDecodeError |
| PARSE-005 | 边界-空教材文件 | 无章节 | 空教材 JSON | 返回空章节列表 |

### 3.2 知识点匹配服务

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MATCH-001 | 正常匹配-精确匹配 | Concept 存在"一元一次方程" | 相同知识点 | match_type: exact, confidence: 1.0 |
| MATCH-002 | 正常匹配-LLM模糊匹配 | 无精确匹配 | 使用 LLM | match_type: fuzzy, confidence < 1.0 |
| MATCH-003 | 正常匹配-无匹配 | Concept 不存在 | 知识点不存在 | match_type: none, confidence: 0.0 |
| MATCH-004 | 正常匹配-生成报告 | 匹配完成 | 知识点列表 | 生成 matching_report.json |
| MATCH-005 | 异常-Neo4j 连接失败 | Neo4j 服务停止 | 正常参数 | 抛出 Neo4jConnectionError |
| MATCH-006 | 边界-空知识点列表 | 无知识点 | 空列表 | 返回空匹配结果 |

### 3.3 PDF OCR 服务

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| OCR-001 | 正常识别-小文件 | 百度 OCR API 正常 | 3页 PDF | 返回 3 页文本内容 |
| OCR-002 | 正常识别-保存结果 | OCR 完成 | 正常参数 | 生成 ocr_result.json |
| OCR-003 | 异常-文件不存在 | 无 | 无效路径 | 抛出 FileNotFoundError |
| OCR-004 | 异常-文件格式错误 | 非 PDF | txt 文件 | 抛出 InvalidFileFormat |
| OCR-005 | 异常-API Key 缺失 | 无 BAIDU_OCR_API_KEY | PDF 文件 | 抛出 ConfigurationError |
| OCR-006 | 异常-API 调用失败 | 百度 OCR 服务异常 | PDF 文件 | 抛出 OCRAPIError |
| OCR-007 | 边界-API 限流重试 | QPS 达到上限 | 多页 PDF | 等待后重试成功 |
| OCR-008 | 边界-空PDF | PDF 无内容 | 空白 PDF | 返回 pages text 为空 |

### 3.4 知识点提取服务

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KP-001 | 正常提取-结构化输出 | OCR 结果有效 | OCR 文本 | 返回学段-领域-知识点结构 |
| KP-002 | 正常提取-使用免费模型 | LLM 配置正确 | 文本 | 使用 glm-4-flash |
| KP-003 | 正常提取-保存结果 | 提取完成 | 正常参数 | 生成 curriculum_kps.json |
| KP-004 | 异常-API Key 缺失 | 无 ZHIPU_API_KEY | 正常文本 | 抛出 ConfigurationError |
| KP-005 | 异常-LLM 调用失败 | LLM 服务异常 | 文本 | 抛出 LLMCallError |
| KP-006 | 异常-输出格式错误 | LLM 返回非 JSON | 文本 | 重试或抛出 OutputFormatError |
| KP-007 | 边界-长文本分块 | 文本超长 | 10000字文本 | 分块处理，合并结果 |
| KP-008 | 边界-空文本 | OCR 无内容 | 空文本 | 返回空知识点列表 |

### 3.5 知识点对比服务

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| CMP-001 | 正常对比-精确匹配 | Concept 存在"一元一次方程" | 相同知识点 | status: matched |
| CMP-002 | 正常对比-部分匹配 | Concept 存在"正数" | "正数和负数" | status: partial_match |
| CMP-003 | 正常对比-新增知识点 | Concept 不存在 | "凑十法" | status: new |
| CMP-004 | 正常对比-生成报告 | 对比完成 | 知识点列表 | 生成 kp_comparison_report.json |
| CMP-005 | 异常-Neo4j 连接失败 | Neo4j 服务停止 | 正常参数 | 抛出 Neo4jConnectionError |
| CMP-006 | 边界-空知识点列表 | 无知识点 | 空列表 | 返回空对比结果 |
| CMP-007 | 边界-按学段统计 | 多学段数据 | 4学段知识点 | by_stage 包含统计 |

### 3.6 TTL 生成服务

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| TTL-001 | 正常生成-TTL 文件 | 知识点有效 | 知识点列表 | 生成 textbook_kps.ttl |
| TTL-002 | 正常生成-命名空间 | 知识点有效 | 正常参数 | TTL 包含正确 prefix |
| TTL-003 | 正常生成-属性关系 | 知识点有效 | 正常参数 | TTL 包含 belongsToStage, belongsToDomain |
| TTL-004 | 边界-跳过 TTL | --skip-ttl | 知识点列表 | 不生成 TTL 文件 |
| TTL-005 | 边界-空知识点 | 无知识点 | 空列表 | TTL 文件仅包含 prefix |

### 3.7 主脚本整合

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| MAIN-001 | 正常运行-完整流程 | 所有服务正常 | 无参数 | 生成所有输出文件 |
| MAIN-002 | 正常运行-跳过 OCR | ocr_result.json 存在 | --skip-ocr | 使用已有 OCR 结果 |
| MAIN-003 | 正常运行-跳过 TTL | 正常参数 | --skip-ttl | 不生成 TTL |
| MAIN-004 | 正常运行-调试模式 | 正常参数 | --debug | 输出详细日志 |
| MAIN-005 | 异常-参数错误 | 无 | 无效参数 | 显示帮助信息 |
| MAIN-006 | 异常-中间步骤失败 | OCR 失败 | 无参数 | 终止流程，显示错误 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10000 | SYSTEM_ERROR | 系统错误 |
| 10001 | INVALID_PARAMS | 参数错误 |
| 10002 | FILE_NOT_FOUND | 文件不存在 |
| 10003 | CONFIGURATION_ERROR | 配置错误 |
| 20002 | NEO4J_CONNECTION_ERROR | Neo4j 连接失败 |
| 20003 | QUERY_FAILED | 查询失败 |
| 30001 | INVALID_FILE_FORMAT | 文件格式错误 |
| 30002 | OCR_API_ERROR | 百度 OCR API 调用失败 |
| 30003 | OCR_RATE_LIMIT | OCR API 限流 |
| 30004 | OCR_PROCESSING_ERROR | OCR 处理失败 |
| 40001 | API_KEY_MISSING | API Key 缺失 |
| 40002 | LLM_CALL_ERROR | LLM 调用失败 |
| 40003 | OUTPUT_FORMAT_ERROR | 输出格式错误 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 教材解析服务 | 5 |
| 知识点匹配服务 | 6 |
| PDF OCR 服务 | 8 |
| 知识点提取服务 | 8 |
| 知识点对比服务 | 7 |
| TTL 生成服务 | 5 |
| 主脚本整合 | 6 |
| **总计** | **35** |

---

## 6. 测试执行顺序

```
tests/textbook/
├── test_parser.py          # 解析测试
├── test_matcher.py         # 匹配测试
├── test_main.py            # 主脚本测试

tests/curriculum/
├── test_pdf_ocr.py         # OCR 测试
├── test_kp_extraction.py   # LLM 提取测试
├── test_kp_comparison.py   # 对比测试
├── test_ttl_generator.py   # TTL 测试
├── test_main.py            # 主脚本测试
```

---

## 7. 辅助方法

### 7.1 Mock 教材 JSON
```python
def mock_textbook_json() -> dict:
    """生成 Mock 教材 JSON"""
    return {
        "textbook": "人教版数学",
        "chapters": [
            {
                "grade": "七年级",
                "semester": "上册",
                "chapter": "第一章有理数",
                "knowledge_points": ["有理数", "数轴", "相反数"]
            }
        ]
    }
```

### 7.2 Mock OCR 结果
```python
def mock_ocr_result(pages: int = 3) -> dict:
    """生成 Mock OCR 结果"""
    return {
        "pdf_path": "test.pdf",
        "total_pages": pages,
        "pages": [
            {"page_num": i, "text": f"测试内容第{i}页..."}
            for i in range(1, pages + 1)
        ]
    }
```

### 7.3 Mock LLM 响应
```python
def mock_llm_response() -> dict:
    """生成 Mock LLM 提取结果"""
    return {
        "stages": [
            {
                "stage": "第一学段",
                "grades": "1-2年级",
                "domains": [
                    {
                        "domain": "数与代数",
                        "knowledge_points": ["20以内数的认识", "加减法"]
                    }
                ]
            }
        ]
    }
```

### 7.4 Mock Neo4j 查询
```python
def mock_neo4j_concepts() -> list:
    """生成 Mock Concept 列表"""
    return [
        {"label": "一元一次方程"},
        {"label": "有理数"},
        {"label": "正数"},
    ]
```

---

## 8. 运行测试

```bash
# 运行单个测试文件
pytest tests/textbook/test_parser.py -v

# 运行所有测试
pytest tests/ -v

# 跳过需要外部服务的测试
pytest tests/ -v -m "not external"

# 显示覆盖率
pytest --cov=edukg/scripts --cov-report=term-missing
```

---

## 9. 测试配置

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
markers =
    external: marks tests requiring external services (LLM, Neo4j, OCR)
    slow: marks slow tests (OCR)
    integration: marks integration tests
```

---

*文档生成时间: 2026-04-07*