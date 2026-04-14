# 数学知识图谱 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证数学知识图谱数据整合功能，包括教材数据解析、章节导入、知识点匹配、关联导入等模块。

### 1.2 测试方式
- **单元测试**：测试独立函数和类的功能
- **集成测试**：测试完整的端到端数据流程
- **数据库回滚**：使用 pytest fixture 配合事务回滚
- **LLM Mock**：使用 Mock 替代真实 LLM 调用

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- 数据库：使用测试 Neo4j 实例
- 环境：使用 `.env.test` 配置

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_TEXTBOOK_ID | middle-grade7-shang | 测试教材ID |
| TEST_CHAPTER_ID | ch-test-001 | 测试章节ID |
| TEST_KP_NAME | 正数和负数的概念 | 测试知识点名称 |
| TEST_MAPPED_KP_ID | statement#1622 | 测试匹配知识点ID |

---

## 3. 测试用例清单

### 3.1 教材数据解析 (textbook-data-parser)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| TDP-001 | 解析初中教材JSON | JSON文件存在 | grade7/shang.json | 返回正确的学段、年级、学期 |
| TDP-002 | 解析小学教材JSON | JSON文件存在 | grade1/shang.json | 返回正确的学段、年级 |
| TDP-003 | 提取章节结构 | JSON文件存在 | 包含章节的JSON | 返回章节列表和知识点 |
| TDP-004 | 处理空知识点数组 | JSON文件存在 | 空knowledge_points | 正确处理，不报错 |
| TDP-005 | 处理无效JSON | 文件存在 | 格式错误的JSON | 记录错误，跳过文件 |
| TDP-006 | 输出标准化数据 | 所有JSON已解析 | 24册数据 | 输出textbook_data.json |

### 3.2 教材章节导入 (textbook-chapter-importer)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| TCI-001 | 创建Textbook节点 | Neo4j连接正常 | 教材数据 | 创建24个Textbook节点 |
| TCI-002 | 创建Chapter节点 | Textbook已创建 | 章节数据 | 创建约300个Chapter节点 |
| TCI-003 | 创建HAS_CHAPTER关系 | 节点已创建 | 教材-章节数据 | 创建正确的关系 |
| TCI-004 | 幂等性测试 | 数据已存在 | 重复导入 | 不创建重复数据 |
| TCI-005 | 验证数据数量 | 导入完成 | 无 | 返回正确的统计数量 |

### 3.3 LLM教材-知识点匹配 (llm-textbook-kp-matcher)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| LLM-001 | 批量匹配章节知识点 | Neo4j有知识点 | 章节知识点列表 | 返回匹配结果和置信度 |
| LLM-002 | 高置信度匹配 | LLM返回结果 | confidence >= 0.9 | status = auto_mapped |
| LLM-003 | 中置信度匹配 | LLM返回结果 | 0.7 <= confidence < 0.9 | status = needs_review |
| LLM-004 | 低置信度匹配 | LLM返回结果 | confidence < 0.7 | status = no_match |
| LLM-005 | 断点续传测试 | 中断后重启 | 已处理章节 | 跳过已处理章节 |
| LLM-006 | 输出CSV文件 | 匹配完成 | 无 | 生成textbook_kp_matches.csv |

### 3.4 教材-知识点关联导入 (textbook-kp-linker)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| TKL-001 | 创建TextbookKnowledgePoint节点 | 匹配结果存在 | 匹配数据 | 创建约3000个节点 |
| TKL-002 | 创建USES_KNOWLEDGE_POINT关系 | 节点已创建 | 章节-知识点数据 | 创建正确关系 |
| TKL-003 | 创建MAPPED_TO关系(高置信) | auto_mapped状态 | 高置信度数据 | 创建映射关系 |
| TKL-004 | 不创建MAPPED_TO关系(低置信) | no_match状态 | 低置信度数据 | 不创建映射关系 |
| TKL-005 | 验证关联完整性 | 导入完成 | 无 | 返回正确的统计 |

### 3.5 数据验证 (validation)

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| VAL-001 | 教材覆盖率检查 | 数据导入完成 | 无 | 返回覆盖率统计 |
| VAL-002 | 知识点关联率检查 | 数据导入完成 | 无 | 返回关联率统计 |
| VAL-003 | 缺失报告生成 | 存在未匹配数据 | 无 | 输出未匹配列表 |
| VAL-004 | 最终统计报告 | 所有检查完成 | 无 | 输出完整报告 |

### 3.6 API接口测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| API-001 | 按教材查询知识点 | 数据存在 | textbook_id | 返回教材和知识点列表 |
| API-002 | 按章节查询知识点 | 数据存在 | chapter_id | 返回章节知识点 |
| API-003 | 查询知识点学习路径 | 数据存在 | kp_id | 返回学习上下文 |
| API-004 | 查询教材覆盖统计 | 数据存在 | 无 | 返回统计信息 |
| API-005 | 教材不存在 | 无 | 无效textbook_id | 返回错误码30002 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10000 | SYSTEM_ERROR | 系统错误 |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10002 | NOT_FOUND | 实体不存在 |
| 30001 | KP_NOT_FOUND | 知识点不存在 |
| 30002 | TEXTBOOK_NOT_FOUND | 教材不存在 |
| 30003 | CHAPTER_NOT_FOUND | 章节不存在 |
| 30004 | NO_MATCH_DATA | 无匹配数据 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 教材数据解析 | 6 |
| 教材章节导入 | 5 |
| LLM教材-知识点匹配 | 6 |
| 教材-知识点关联导入 | 5 |
| 数据验证 | 4 |
| API接口测试 | 5 |
| **总计** | **31** |

---

## 6. 测试执行顺序

测试按依赖关系顺序执行：

```
test_textbook_parser.py      : 教材数据解析测试
test_textbook_importer.py    : 教材章节导入测试
test_llm_matcher.py          : LLM匹配测试 (Mock LLM)
test_kp_linker.py            : 知识点关联导入测试
test_validation.py           : 数据验证测试
test_api.py                  : API接口测试
```

---

## 7. 辅助方法

### 7.1 创建测试教材数据
```python
def create_test_textbook() -> dict:
    """创建测试教材数据"""
    return {
        "id": "test-grade7-shang",
        "name": "七年级上册",
        "stage": "middle",
        "grade": "七年级",
        "semester": "上册",
        "chapters": [
            {
                "id": "ch-test-001",
                "name": "有理数",
                "knowledge_points": [
                    {"name": "正数和负数的概念"},
                    {"name": "绝对值"}
                ]
            }
        ]
    }
```

### 7.2 Mock LLM响应
```python
def mock_llm_response(kp_names: list) -> dict:
    """创建Mock LLM响应"""
    return {
        "matches": [
            {"name": name, "matched_id": f"statement#{i}", "confidence": 0.95}
            for i, name in enumerate(kp_names)
        ]
    }
```

### 7.3 清理测试数据
```python
def cleanup_test_data(neo4j_driver):
    """清理测试数据"""
    with neo4j_driver.session() as session:
        session.run("MATCH (n:TextbookKnowledgePoint) DELETE n")
        session.run("MATCH (n:Chapter) DELETE n")
        session.run("MATCH (n:Textbook) DELETE n")
```

---

## 9. 导入验证测试 (Import Verification)

### 9.1 验证规范

每个导入任务必须执行以下验证：

```
导入前查询基线  →  脚本 dry-run  →  执行导入  →  导入后查询验证  →  数据抽查
```

### 9.2 Textbook 节点导入验证 (Task 17)

| 用例编号 | 验证项 | 验证方法 | 预期结果 | 实际结果 |
|---------|-------|---------|---------|---------|
| IMP-001 | 导入前基线 | `MATCH (t:Textbook) RETURN count(t)` | 记录当前数量 | 23（已有旧数据） |
| IMP-002 | 数据文件检查 | 检查 textbooks.json 存在且可解析 | 23 条记录 | ✓ 23 条，结构正确 |
| IMP-003 | dry-run | `python import_textbooks.py --dry-run` | 无报错，打印 Cypher | ✓ 无报错 |
| IMP-004 | 导入后数量 | `MATCH (t:Textbook) RETURN count(t)` | 23 | ✓ 23 |
| IMP-005 | URI 唯一性 | `MATCH (t:Textbook) WITH t.uri AS uri, count(*) AS c WHERE c>1 RETURN uri, c` | 无重复 | ✓ 无重复 |
| IMP-006 | 数据抽查 | 随机查询 3 个教材节点 | stage, grade, name 属性正确 | ✓ g8s/g2x/g9x 抽查通过 |

### 9.3 Chapter 节点导入验证 (Task 18)

| 用例编号 | 验证项 | 验证方法 | 预期结果 | 实际结果 |
|---------|-------|---------|---------|---------|
| IMP-007 | 导入前基线 | `MATCH (c:Chapter) RETURN count(c)` | 记录当前数量 | 0（无旧数据） |
| IMP-008 | 数据文件检查 | 检查 chapters_enhanced.json 存在 | ~148 条 | ✓ 148 条，无重复，textbook_id 全部有效 |
| IMP-009 | dry-run | `python import_chapters.py --dry-run` | 无报错 | ✓ 无报错（修复 output/ 路径后） |
| IMP-010 | 导入后数量 | `MATCH (c:Chapter) RETURN count(c)` | 148 | ✓ 148 |
| IMP-011 | CONTAINS 关系 | `MATCH ()-[:CONTAINS]->(c:Chapter) RETURN count(*)` | 148 | ✓ 148 |
| IMP-012 | 关联正确性 | 随机查询 3 个 Chapter 确认关联到 Textbook | 关联存在且正确 | ✓ g6s-9/g2s-4/g3x-6 抽查通过 |

### 9.4 Section 节点导入验证 (Task 19)

| 用例编号 | 验证项 | 验证方法 | 预期结果 | 实际结果 |
|---------|-------|---------|---------|---------|
| IMP-013 | 导入前基线 | `MATCH (s:Section) RETURN count(s)` | 记录当前数量 | 0（无旧数据） |
| IMP-014 | 数据文件检查 | 检查 sections.json 存在 | 580 条 | ✓ 580 条，无重复，chapter_id 全部有效 |
| IMP-015 | dry-run | `python import_sections.py --dry-run` | 无报错 | ✓ 无报错（修复 output/ 路径后） |
| IMP-016 | 导入后数量 | `MATCH (s:Section) RETURN count(s)` | 580 | ✓ 580 |
| IMP-017 | CONTAINS 关系 | `MATCH (c:Chapter)-[:CONTAINS]->(s:Section) RETURN count(*)` | 580 | ✓ 580 |
| IMP-018 | 关联正确性 | 随机查询 3 个 Section 确认关联到 Chapter | 关联存在且正确 | ✓ g3x-2-5/g9s-4-5/g3s-3-2 抽查通过 |
| IMP-018 | 关联正确性 | 随机查询 3 个 Section 确认关联到 Chapter | 关联存在且正确 |

### 9.5 TextbookKP 节点导入验证 (Task 20)

| 用例编号 | 验证项 | 验证方法 | 预期结果 |
|---------|-------|---------|---------|
| IMP-019 | 导入前基线 | `MATCH (tkp:TextbookKP) RETURN count(tkp)` | 记录当前数量 |
| IMP-020 | 数据文件检查 | 检查 textbook_kps.json 存在 | 1350 条 |
| IMP-021 | 字段完整性 | 随机检查 10 个节点 | stage, grade, topic, difficulty, importance 非空 |
| IMP-022 | dry-run | `python import_textbook_kps.py --dry-run` | 无报错 |
| IMP-023 | 导入后数量 | `MATCH (tkp:TextbookKP) RETURN count(tkp)` | 1350 |
| IMP-024 | URI 唯一性 | `MATCH (tkp:TextbookKP) RETURN tkp.uri, count(*) HAVING count(*)>1` | 无重复 |
| IMP-025 | 属性分布 | 按 stage 分组统计 | primary/middle/high 分布合理 |
| IMP-026 | 重复检查 | 同一教材内无重复 label | 无重复 |

### 9.6 IN_UNIT 关系导入验证 (Task 21)

| 用例编号 | 验证项 | 验证方法 | 预期结果 |
|---------|-------|---------|---------|
| IMP-027 | 导入前基线 | `MATCH ()-[r:IN_UNIT]->() RETURN count(r)` | 记录当前数量 |
| IMP-028 | 数据文件检查 | 检查 in_unit_relations.json 存在 | ~1350 条 |
| IMP-029 | 引用有效性 | 检查所有 from/to URI 在 Neo4j 中存在 | 无孤立引用 |
| IMP-030 | dry-run | `python import_in_unit_relations.py --dry-run` | 无报错 |
| IMP-031 | 导入后数量 | `MATCH ()-[r:IN_UNIT]->() RETURN count(r)` | ~1350 |
| IMP-032 | 孤立节点检查 | `MATCH (n) WHERE NOT (n)-[:IN_UNIT]-() AND n:TextbookKP RETURN count(n)` | 应为 0 或少量 |
| IMP-033 | 数据抽查 | 随机查询 3 个 Chapter 的知识点 | IN_UNIT 关系存在 |

### 9.7 MATCHES_KG 关系导入验证 (Task 22)

| 用例编号 | 验证项 | 验证方法 | 预期结果 |
|---------|-------|---------|---------|
| IMP-034 | 导入前基线 | `MATCH ()-[r:MATCHES_KG]->() RETURN count(r)` | 记录当前数量 |
| IMP-035 | 数据文件检查 | 检查 matches_kg_relations.json，matched=true 的数量 | 1690 |
| IMP-036 | dry-run | `python import_matches_kg.py --dry-run` | 无报错 |
| IMP-037 | 导入后数量 | `MATCH ()-[r:MATCHES_KG]->() RETURN count(r)` | 1690 |
| IMP-038 | 匹配覆盖率 | `MATCH (tkp:TextbookKP) WHERE NOT (tkp)-[:MATCHES_KG]->() RETURN count(tkp)` | ~50 (未匹配) |
| IMP-039 | 置信度检查 | `MATCH ()-[r:MATCHES_KG]->() RETURN r.confidence` 分布 | 大部分 >= 0.8 |
| IMP-040 | 方法检查 | 按 r.method 分组统计 | exact_match 和 llm_vote 都有 |

### 9.8 整体验证 (Task 23)

| 用例编号 | 验证项 | 验证方法 | 预期结果 |
|---------|-------|---------|---------|
| IMP-041 | 节点总数 | `MATCH (n) RETURN labels(n) AS labels, count(*) ORDER BY labels` | 符合预期 |
| IMP-042 | 关系总数 | `MATCH ()-[r]->() RETURN type(r) AS type, count(*) ORDER BY type` | 符合预期 |
| IMP-043 | TextbookKP 覆盖 | `MATCH (tkp:TextbookKP) WHERE (tkp)-[:MATCHES_KG]->() RETURN count(tkp)` | 1690 (97.1%) |
| IMP-044 | Chapter 知识点覆盖 | `MATCH (c:Chapter) WHERE NOT (c)-[:IN_UNIT]->() RETURN count(c)` | 0 |
| IMP-045 | 路径完整性 | `MATCH (t)-[:HAS_CHAPTER]->(c)-[:CONTAINS]->(s) RETURN count(*)` | 路径通畅 |
| IMP-046 | 最终报告 | 汇总所有统计数据 | 输出完整报告 |

---

## 10. 运行测试

```bash
# 运行单个测试文件
pytest tests/kg/test_textbook_parser.py -v

# 运行单个测试方法
pytest tests/kg/test_textbook_parser.py::test_parse_middle_school_json -v

# 运行所有知识图谱测试
pytest tests/kg/ -v

# 运行并显示覆盖率
pytest tests/kg/ --cov=edukg/scripts/kg_construction --cov-report=term-missing

# 跳过LLM相关测试（无Mock环境时）
pytest tests/kg/ -v -m "not llm"
```