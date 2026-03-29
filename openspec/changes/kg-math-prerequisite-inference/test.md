# 数学前置关系推断测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证前置关系推断的所有功能，包括教学顺序推断、定义依赖抽取、LLM 多模型投票、关系融合和 DAG 验证。

### 1.2 测试方式
- **单元测试**：使用 pytest 测试脚本逻辑
- **Mock 测试**：模拟 LLM Gateway 响应
- **集成测试**：完整工作流程测试

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_KP_FILE | `tests/fixtures/test_knowledge_points.json` | 测试知识点数据 |
| MOCK_LLM_RESPONSE | 见 fixtures | 模拟 LLM 响应数据 |

---

## 3. 测试用例清单

### 3.1 教学顺序推断脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| TEACHES-001 | 章节内顺序推断 | 知识点有章节信息 | 执行推断 | 正确生成章节内 TEACHES_BEFORE |
| TEACHES-002 | 跨章节不推断 | 知识点跨章节 | 执行推断 | 不生成跨章节关系 |
| TEACHES-003 | 无章节知识跳过 | 知识点无章节信息 | 执行推断 | 跳过该知识点 |
| TEACHES-004 | CSV 输出格式 | 推断完成 | 检查输出 | CSV 结构正确 |

### 3.2 定义依赖抽取脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| DEF-001 | 匹配知识点名称 | 定义包含其他知识点名称 | 执行抽取 | 正确提取依赖关系 |
| DEF-002 | 学科内过滤 | 定义包含其他学科知识点 | 执行抽取 | 不匹配其他学科知识点 |
| DEF-003 | 最小长度过滤 | 知识点名称 <3 字符 | 执行抽取 | 跳过匹配 |
| DEF-004 | 无匹配处理 | 定义不包含知识点名称 | 执行抽取 | 返回空列表 |
| DEF-005 | CSV 输出格式 | 抽取完成 | 检查输出 | CSV 结构正确 |

### 3.3 LLM 前置关系推断脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| LLM-001 | GLM-4-flash 调用 | LLM Gateway 可用 | 调用 LLM | 成功获取响应 |
| LLM-002 | DeepSeek 调用 | LLM Gateway 可用 | 调用 LLM | 成功获取响应 |
| LLM-003 | 两模型一致 | 两模型返回相同结果 | 投票 | 接受关系 |
| LLM-004 | 两模型不一致 | 两模型返回不同结果 | 投票 | 不接受关系 |
| LLM-005 | 高置信度分类 | 置信度 ≥0.8 | 分类 | 标记为 PREREQUISITE |
| LLM-006 | 低置信度分类 | 置信度 <0.8 | 分类 | 标记为 PREREQUISITE_CANDIDATE |
| LLM-007 | 批量处理 | 大量知识点对 | 批量处理 | 按批次处理 |
| LLM-008 | Rate limit | 请求超过限制 | 限流 | 等待后重试 |
| LLM-009 | Dry-run 模式 | `--dry-run` 参数 | 执行 | 仅估算成本，不调用 LLM |
| LLM-010 | CSV 输出格式 | 推断完成 | 检查输出 | CSV 结构正确 |

### 3.4 关系融合脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| FUSE-001 | 合并定义依赖 | 定义依赖文件存在 | 融合 | 包含定义依赖关系 |
| FUSE-002 | 合并 LLM 结果 | LLM 结果文件存在 | 融合 | 包含 LLM 推断关系 |
| FUSE-003 | 去重 | 相同 source-target 对 | 融合 | 只保留一条关系 |
| FUSE-004 | 生成 先修_on | PREREQUISITE 关系存在 | 融合 | 同时生成 先修_on 关系 |
| FUSE-005 | CSV 输出格式 | 融合完成 | 检查输出 | CSV 结构正确 |

### 3.5 DAG 验证脚本测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| DAG-001 | 无环验证 | PREREQUISITE 无环 | 验证 | 验证通过，退出码 0 |
| DAG-002 | 有环检测 | PREREQUISITE 有环 | 验证 | 检测到环，退出码 1 |
| DAG-003 | 环详情输出 | 存在环 | 验证 | 输出环涉及的知识点 |
| DAG-004 | 质量指标计算 | 关系导入完成 | 验证 | 输出覆盖率、平均链长、置信度分布 |

### 3.6 集成测试

| 用例编号 | 场景描述 | 前置条件 | 输入 | 颍期结果 |
|---------|---------|---------|------|---------|
| INTEGRATE-001 | 完整工作流程 | 知识点和原生关系已导入 | 全流程执行 | 所有步骤成功，DAG 验证通过 |
| INTEGRATE-002 | LLM 调用失败处理 | LLM Gateway 不可用 | 执行推断 | 记录错误，继续处理其他知识点 |

---

## 4. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| 教学顺序推断脚本 | 4 |
| 定义依赖抽取脚本 | 5 |
| LLM 前置关系推断脚本 | 10 |
| 关系融合脚本 | 5 |
| DAG 验证脚本 | 4 |
| 集成测试 | 2 |
| **总计** | **30** |

---

## 5. 辅助方法

### 5.1 Mock LLM Gateway 响应
```python
def mock_llm_response(is_prerequisite: bool, confidence: float):
    """模拟 LLM Gateway 响应"""
    return {
        "is_prerequisite": is_prerequisite,
        "confidence": confidence,
        "reason": "Mock response for testing"
    }
```

### 5.2 创建测试环数据
```python
def create_cycle_data(driver):
    """创建测试用的环数据"""
    with driver.session() as session:
        # 创建环: A → B → C → A
        session.run("MATCH (a:KnowledgePoint {uri: 'A'}), (b:KnowledgePoint {uri: 'B'}) CREATE (a)-[:PREREQUISITE]->(b)")
        session.run("MATCH (b:KnowledgePoint {uri: 'B'}), (c:KnowledgePoint {uri: 'C'}) CREATE (b)-[:PREREQUISITE]->(c)")
        session.run("MATCH (c:KnowledgePoint {uri: 'C'}), (a:KnowledgePoint {uri: 'A'}) CREATE (c)-[:PREREQUISITE]->(a)")
```

---

## 6. 运行测试

```bash
pytest tests/kg_construction/test_prerequisite_inference/ -v
```