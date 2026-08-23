# RAG 评测 agent 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证知识库整理（模块逐个 + 状态机）、评测 agent（评测集执行 / hit@k / 判分 / 指标）、可观测评测（trace / 报告 / 版本对比）的正确性与健壮性，**每个阶段可测**。

### 1.2 测试方式
- **单元测试**：状态机、hit@k 计算、判分解析、指标聚合、报告生成——均为纯函数直测。
- **集成测试**：TestClient 调 `/api/rag/eval/*`；mock COS（CosVectorsClient）与 doubao（判分/生成 mock）。
- **黄金文件**：报告输出与 `tests/rag/eval/golden/` 对比。

### 1.3 测试环境配置
- pytest：`pytest.ini`；环境：`.env.test`
- 语料：`docs/project-intro/corpus/`（测试用临时副本或 fixture 造数）

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_TOKEN | `test-internal-token` | 鉴权 token |
| TEST_MODULE | `knowledge-graph` | 知识图谱模块 |
| TEST_EVAL_SET | 25 条评测集（每模块 5 条） | 造数 fixture |
| TEST_ENTRY | 单条：question + expected_references + expected_points | 造数 |
| TEST_VERSION | `2026-08-21-1` | 语料版本标识 |

---

## 3. 测试用例清单

### 3.1 知识库整理（KB-ORG）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| KBORG-001 | 状态推进 | pending | 完成完善文档 | 状态 → organized |
| KBORG-002 | 状态回退 | indexed | 修改完善文档 | 状态 → chunked（待重索引） |
| KBORG-003 | 完善文档 8 节完整 | 完善文档存在 | 读文档 | 8 节齐全，「为什么」「数据流」「坑」非空模板 |
| KBORG-004 | 状态持久化 | 有状态文件 | 状态变更 | `_status.json` 落盘正确 |
| KBORG-005 | 模块清单完整 | 无 | 读清单 | 5 模块齐全（知识图谱/AI答疑/题型知识点/组织中心/RAG） |

### 3.2 评测集（EVAL-SET）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| EVALSET-001 | 评测集加载 | 评测集存在 | 加载 | 每模块 ≥5 条，结构齐全 |
| EVALSET-002 | 评测集格式校验 | 含非法条目 | 校验 | 非法条目报错并指明字段 |
| EVALSET-003 | expected 引用一致 | 完善文档就绪 | 交叉校验 | expected_references 能在完善文档中找到对应节 |

### 3.3 评测 agent（EVAL）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| EVAL-001 | 单条评测执行 | mock 检索/生成/判分 | 一条评测 | 输出含召回/得分/hit/答案/引用/usage/耗时/判分 |
| EVAL-002 | hit@3 计算 | 预期 3 条引用命中 2 | 计算 | hit@3 = 2/3 |
| EVAL-003 | 判分 JSON 解析 | 合法判分 | 解析 | score（0~5）+ rationale |
| EVAL-004 | 判分解析失败重试 | 首次非法 | 解析 | 重试 1 次后成功 |
| EVAL-005 | 判分仍失败记 0 | 两次均非法 | 解析 | score=0 且标记"判分失败" |
| EVAL-006 | 按模块聚合 | 模块 5 条完成 | 聚合 | hit@3/avg_quality/cost/latency 正确 |
| EVAL-007 | 全量聚合 | 25 条完成 | 聚合 | 全量指标 = 各模块之和/均值正确 |

### 3.4 指标与成本（METRIC）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| METRIC-001 | cost 累计 | 多轮 usage | 汇总 | cost_yuan = tokens×单价 正确累计 |
| METRIC-002 | 无 usage 降级估算 | usage 缺失 | 统计 | 走估算并标注"估算" |
| METRIC-003 | latency 统计 | 检索/生成 mock 耗时 | 统计 | 检索/生成/总耗时正确 |
| METRIC-004 | 超时按降级计 | 某环节超时 | 统计 | 耗时计超时值 + 标记降级 |

### 3.5 可观测（OBSERVE）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| OBSERVE-001 | trace 落盘 | 一次评测 | 读 trace | 每条含 query/召回/得分/hit/答案/引用/usage/耗时/判分 |
| OBSERVE-002 | 报告生成 | 评测完成 | 生成报告 | 按模块 + 全量汇总正确 |
| OBSERVE-003 | 报告黄金文件 | 有 golden | 对比 | 与黄金文件一致 |
| OBSERVE-004 | 版本对比 | 两次评测 | 对比 | delta 计算正确（hit@3/质量分） |

### 3.6 API 端到端（EVAL-API）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| EVALAPI-001 | 触发评测 | 有效 token | run(module=kg) | 返回 run_id + status=running |
| EVALAPI-002 | 查询报告 | 评测完成 | report(run_id) | 返回 summary + by_module |
| EVALAPI-003 | 版本对比 | 两次评测 | report(compare_with) | compare.delta 返回 |
| EVALAPI-004 | 鉴权失败 | 无效 token | 任意端点 | 10004 |
| EVALAPI-005 | 参数错误 | 有效 token | run(module 非法) | 10001 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10000 | SYSTEM_ERROR | 系统错误（评测集缺失/检索不可用） |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10004 | UNAUTHORIZED | 未授权 |

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| KB-ORG（知识库整理） | 5 |
| EVAL-SET（评测集） | 3 |
| EVAL（评测 agent） | 7 |
| METRIC（指标成本） | 4 |
| OBSERVE（可观测） | 4 |
| EVAL-API（端到端） | 5 |
| **总计** | **28** |

---

## 6. 测试执行顺序

```
test_rag_kb_org.py    : 知识库整理（状态机/完善文档）
test_rag_eval_set.py  : 评测集（加载/校验/一致性）
test_rag_eval_agent.py: 评测 agent（执行/hit@k/判分/聚合）
test_rag_eval_metric.py: 指标成本（cost/latency）
test_rag_eval_observe.py: 可观测（trace/报告/对比）
test_rag_eval_api.py  : API 端到端
```

按依赖顺序执行，API 端到端最后。

---

## 7. 辅助方法

### 7.1 评测集 fixture
```python
@pytest.fixture
def eval_set():
    """25 条评测集（每模块 5 条）"""
    return [
        {"module": "knowledge-graph", "question": "为什么用Neo4j？",
         "question_type": "为什么",
         "expected_references": [{"page": "knowledge-graph", "section": "为什么这么设计"}],
         "expected_points": ["依赖关系", "可解释路径"]},
        # ... 其余
    ]
```

### 7.2 Mock 判分
```python
@pytest.fixture
def mock_judge(monkeypatch):
    """mock LLM 判分，返回固定 {score, rationale}"""
    def fake_judge(answer, expected_points, expected_refs):
        return {"score": 4, "rationale": "覆盖要点，引用正确"}
    monkeypatch.setattr("core.rag.eval.agent.judge_answer", fake_judge)
```

### 7.3 认证头
```python
def auth_headers(token: str = "test-internal-token") -> dict:
    return {"x-internal-token": token}
```

---

## 8. 运行测试

```bash
cd ai-edu-ai-service && pytest tests/rag/eval/ -v

# 单文件
pytest tests/rag/eval/test_rag_eval_agent.py -v

# 覆盖率
pytest tests/rag/eval/ --cov=core.rag.eval --cov-report=term-missing
```
