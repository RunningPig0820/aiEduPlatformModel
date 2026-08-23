# RAG 项目介绍问答系统 测试用例设计

## 1. 测试概述

### 1.1 测试目标
验证 RAG 问答系统**每个关键阶段**的正确性与健壮性：文档准备 → 嵌入 → 索引 → 检索 → 打分/范围门 → 权限门 → 生成/引用 → 成本 → 会话 → 降级 → API 端到端。

### 1.2 测试方式
- **单元测试**：纯函数直测（切片器、打分、usage 解析、范围门、边界话术、成本换算）——对齐 `tests/tutoring/unit/test_ark_stream.py` 的纯函数测试模式。
- **集成测试**：TestClient 调真实 `/api/rag/*` 端点；mock COS（CosVectorsClient）与 doubao（httpx mock），避免真实网络。
- **数据库/索引**：测试用内存/临时索引，事务或临时目录回滚。

### 1.3 测试环境配置
- pytest 配置：`pytest.ini`
- 环境：`.env.test`（`COS_VECTORS_*` 用测试桶或 mock，`INTERNAL_TOKEN` 用固定测试值）
- 运行目录：`ai-edu-ai-service/`（settings 加载 `.env` 相对 cwd）

---

## 2. 测试数据

| 参数 | 值 | 说明 |
|-----|-----|-----|
| TEST_TOKEN | `test-internal-token` | 鉴权 token |
| TEST_PAGE_KG | `knowledge-graph` | 知识图谱页 |
| TEST_PAGE_AI | `ai-tutoring` | AI答疑页 |
| TEST_ROLE_MAX | `student` | demo 最高权限角色 |
| TEST_ROLE_LOW | `teacher` | 受限角色 |
| TEST_CHUNK | 完善文档切片（含 page/doc_type/section/permissions/source_doc） | 造数 |
| TEST_QA_ENTRY | 索引层 QA 条目（question/answer_points/references） | 造数 |
| TEST_QUERY_VARIANT | "你们为什么拆成三段服务？" | 引导问题变体文案 |
| TEST_QUERY_CANONICAL | "为什么拆 decide/generate/question-understand" | 规范问题 |

---

## 3. 测试用例清单

### 3.1 文档准备（CORPUS）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| CORPUS-001 | 完善文档 8 节完整性 | 知识图谱完善文档存在 | 读文档 | 8 节齐全，「为什么」「数据流转」「坑」三节非空模板 |
| CORPUS-002 | 按章节切片 | 完善文档就绪 | 切片器执行 | 每节独立 chunk，无跨节混切 |
| CORPUS-003 | metadata 齐全 | 切片完成 | 检查 chunk | page/doc_type/section/permissions/source_doc/order 均非空 |
| CORPUS-004 | source_doc 保留原文 | 切片完成 | 检查 chunk | source_doc 含该节源文档全文 |
| CORPUS-005 | QA 条目数量与结构 | 每页条目生成 | 校验条目 | 每页 5~8 条，每条含 question/answer_points/references |
| CORPUS-006 | 边界-空文档 | 空完善文档 | 切片 | 抛错或返回空，不产出脏 chunk |

### 3.2 嵌入与索引（EMBED / INDEX）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| EMBED-001 | 嵌入维度校验 | dashscope mock | 文本 | 返回 768 维向量 |
| EMBED-002 | 维度异常 | mock 返回 512 维 | 文本 | 抛 `RuntimeError`，拒绝写入 |
| EMBED-003 | embedding usage 抓取 | mock 带 usage | 文本 | embed() 返回 usage.total_tokens 单独记账 |
| INDEX-001 | 幂等重建 | 索引已存在 | `--clear` 执行 | 索引清空重建，无残留旧数据 |
| INDEX-002 | 双池写入 | 索引就绪 | qa/source 各若干 | qa/source 按 doc_type 正确写入 |
| INDEX-003 | rag 索引路由 | settings 配 rag-index | `_resolve_index("rag")` | 返回 rag-index，非法 vector_type 抛 400 |

### 3.3 检索（RETRIEVAL）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| RETRIEVAL-001 | 引导问题命中索引层池 | 索引层池有该页 QA | TEST_QUERY_VARIANT | 命中规范问题条目（语义匹配，非 ID 直连） |
| RETRIEVAL-002 | 自由问题命中源文档池 | 源文档池就绪 | 未预写的自由问题 | 返回命中的 source chunk |
| RETRIEVAL-003 | 页面锚定锁页 | 传 page=AI答疑 | 知识图谱相关问题+page | 仅返回 AI答疑页结果，不含他页 |
| RETRIEVAL-004 | 全局模式跨页 | 不传 page | 跨页问题 | 返回多页结果，可按来源页区分 |
| RETRIEVAL-005 | BM25 关键词兜底 | 向量置信度低 | 含专名"Neo4j"问题 | 关键词命中的 chunk 作为补充返回 |
| RETRIEVAL-006 | 双池结果带权限 metadata | 命中结果 | 检查结果 | 结果含 permissions 标签 |

### 3.4 打分与范围门（SCORE）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| SCORE-001 | 综合分计算 | 候选集就绪 | 相似度/类型/锚定 | 分数 = 相似度×类型×锚定加权 |
| SCORE-002 | 索引层 top-K 1~3 | 命中 5 条 | 索引层检索 | 返回 top-3 |
| SCORE-003 | 源文档池 top-K 3~5 | 命中 8 条 | 源文档检索 | 返回 top-5 |
| SCORE-004 | 索引层低于 0.75 边界 | 最高分 0.6 | 检索 | 判定未覆盖，进入边界流程 |
| SCORE-005 | 源文档池低于 0.5 边界 | 最高分 0.4 | 检索 | 判定未覆盖，进入边界流程 |
| SCORE-006 | 边界回答话术 | 边界触发 | 超范围问题("题库做了吗") | 返回预写话术含覆盖模块列表，不编造 |

### 3.5 权限门（PERMISSION）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| PERMISSION-001 | 有权限放行 | role=student, page=AI答疑 | overview/ask | permission_ok=true，正常检索生成 |
| PERMISSION-002 | 无权限拒绝 | role=teacher, page=学生端页 | overview/ask | permission_denied=true，不执行检索/生成 |
| PERMISSION-003 | demo 最高权限 | 默认 role=student | 全部页 | 权限门全部放行 |
| PERMISSION-004 | 权限标签随结果 | 命中结果 | 检查 | 结果 metadata 含 permissions |

### 3.6 生成与引用（GENERATION）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| GEN-001 | usage 解析纯函数 | SSE 行序列 | 含结尾 usage chunk | 正确解析 prompt/completion tokens |
| GEN-002 | 无 usage 降级估算 | 流无 usage | usage 缺失 | 走 tokenizer 估算并标注"估算" |
| GEN-003 | 答案强制带引用 | 生成完成 | 回答 | 每条回答携带来源页+章节引用 |
| GEN-004 | 跨页按页标注 | 命中两页 | 跨页问题 | 回答按"知识图谱页§x… AI答疑页§y…"分段标注 |
| GEN-005 | 无引用拒绝输出 | 生成未含引用 | 校验 | 输出被拒绝/修正，不裸放 |
| GEN-006 | 展示召回原文 | 生成完成 | retrieved_docs | 返回本次命中的源文档段落 |

### 3.7 成本（COST）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| COST-001 | 每轮成本累计 | 两轮会话 | 两轮 usage | 累计 = 两轮之和 |
| COST-002 | 单价换算 | 已知单价 | tokens | cost_yuan = tokens×单价 正确 |
| COST-003 | embedding 单列 | 有 embedding | cost | embedding_tokens 单独字段 |

### 3.8 会话（SESSION）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| SESSION-001 | 追问计数 | 页面锚定会话 | 连续 3 轮 | turn=1,2,3 正确递增 |
| SESSION-002 | 超限 5 轮拦截 | 已达 5 轮 | 第 6 轮 | 返回预写提示"信息较多，请开启新一轮对话" |

### 3.9 降级与重试（RESILIENCE）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| RESILIENCE-001 | COS 查询重试 | mock 首次失败 | 检索 | 指数退避重试 ≤2 次后成功 |
| RESILIENCE-002 | COS 失败降级关键词 | mock 持续失败 | 检索 | 降级关键词检索并返回结果 |
| RESILIENCE-003 | 生成失败展示预写答案 | doubao mock 失败 | 引导问题 | 展示索引层预写答案卡片 |
| RESILIENCE-004 | 生成失败展示召回原文 | doubao 失败 | 自由问题 | 展示召回原文 |
| RESILIENCE-005 | 全链路失败边界 | 检索+关键词均失败 | 任意问题 | 返回边界话术，不抛裸错误 |
| RESILIENCE-006 | LLM 不重试 | doubao 失败 | 生成 | 不自动重试（避免重复计费） |
| RESILIENCE-007 | 检索超时降级 | mock 延迟 >2s | 检索 | 中止并降级 |
| RESILIENCE-008 | 生成超时降级 | mock 延迟 >15s | 生成 | 中止并降级 |

### 3.10 API 端到端（API）

| 用例编号 | 场景描述 | 前置条件 | 输入 | 预期结果 |
|---------|---------|---------|------|---------|
| API-001 | 获取页面列表 | 服务启动 | GET /api/rag/pages | 返回 5 页（含 rag-system） |
| API-002 | 页面概览卡 | 有效 token | overview(ai-tutoring) | 返回权限+概览+引导问题 |
| API-003 | 问答-页面模式 | 有效 token | ask(page=ai-tutoring, 变体问题) | 返回答案+引用+retrieved_docs+cost |
| API-004 | 问答-全局模式 | 有效 token | ask(跨页问题) | 返回多页引用答案 |
| API-005 | 问答-边界 | 有效 token | ask("题库做了吗") | boundary=true + 预写话术 |
| API-006 | 问答-无权限 | 受限角色 | ask(学生端页, role=teacher) | permission_denied=true |
| API-007 | 鉴权失败 | 无效/缺失 token | 任意端点 | 10004 |
| API-008 | 参数错误 | 有效 token | ask(question 空) | 10001 |
| API-009 | 流式问答 | 有效 token | ask(stream=true) | SSE 事件序列 + done 带最终 cost |
| API-010 | 追问超限 | 5 轮后 | ask 第 6 轮 | 返回预写提示 |

---

## 4. 错误码对照表

| 错误码 | 常量名 | 说明 |
|-------|-------|------|
| 00000 | SUCCESS | 成功 |
| 10000 | SYSTEM_ERROR | 系统错误 |
| 10001 | INVALID_PARAMS | 参数无效 |
| 10004 | UNAUTHORIZED | 未授权 |

> 边界/无权限/降级 = 正常业务标志（boundary/permission_denied/degraded），非错误码。

---

## 5. 测试用例统计

| 模块 | 用例数量 |
|-----|---------|
| CORPUS（文档准备） | 6 |
| EMBED/INDEX（嵌入索引） | 6 |
| RETRIEVAL（检索） | 6 |
| SCORE（打分范围门） | 6 |
| PERMISSION（权限门） | 4 |
| GENERATION（生成引用） | 6 |
| COST（成本） | 3 |
| SESSION（会话） | 2 |
| RESILIENCE（降级重试） | 8 |
| API（端到端） | 10 |
| **总计** | **57** |

---

## 6. 测试执行顺序

```
test_rag_corpus.py        : 文档准备（切片/metadata/QA条目）
test_rag_embed_index.py   : 嵌入与索引（维度/幂等/usage抓取）
test_rag_retrieval.py     : 检索（双池/锚定/变体/BM25）
test_rag_score.py         : 打分与范围门（阈值/边界）
test_rag_permission.py    : 权限门（放行/拒绝/demo）
test_rag_generation.py    : 生成与引用（usage解析/引用强制）
test_rag_cost.py          : 成本（累计/换算）
test_rag_session.py       : 会话（计数/超限）
test_rag_resilience.py    : 降级与重试（矩阵/超时）
test_rag_api.py           : API 端到端（鉴权/问答/流式）
```

按依赖顺序执行（下层能力先测，API 端到端最后）。

---

## 7. 辅助方法

### 7.1 造数：切片与 QA 条目
```python
def make_chunk(page, doc_type, section, content, permissions="student") -> dict:
    """构造测试 chunk（metadata 齐全）"""
    return {"page": page, "doc_type": doc_type, "section": section,
            "content": content, "permissions": permissions,
            "source_doc": content, "order": 1}

def make_qa_entry(page, question, answer_points, references) -> dict:
    """构造索引层 QA 条目"""
    return {"page": page, "question": question,
            "answer_points": answer_points, "references": references}
```

### 7.2 Mock COS 向量桶
```python
@pytest.fixture
def mock_cos(monkeypatch):
    """mock CosVectorsClient，避免真实网络"""
    class FakeClient:
        def query_vectors(self, **kw):
            return None, {"vectors": [{"key": "k1", "metadata": {}, "distance": 0.2}]}
        def put_vectors(self, **kw):
            return None
    monkeypatch.setattr("core.tutoring.vector_store._client", FakeClient())
```

### 7.3 Mock doubao 流式（含 usage）
```python
@pytest.fixture
def mock_doubao(monkeypatch):
    """mock ark 流式响应，结尾带 usage chunk"""
    def fake_stream(**kw):
        yield {"reasoning": None, "content": "答", "tool_calls": None}
        yield {"reasoning": None, "content": None, "tool_calls": None}
        # 结尾 usage chunk 由 _parse_sse_lines 扩展后解析
    monkeypatch.setattr("core.rag.generation.stream_chat", fake_stream)
```

### 7.4 认证头
```python
def auth_headers(token: str = "test-internal-token") -> dict:
    """内部调用认证头"""
    return {"x-internal-token": token}
```

---

## 8. 运行测试

```bash
# 运行单个阶段测试
cd ai-edu-ai-service && pytest tests/rag/test_rag_retrieval.py -v

# 运行单个用例
pytest tests/rag/test_rag_generation.py::test_usage_parse -v

# 运行所有 RAG 测试
pytest tests/rag/ -v

# 运行并显示覆盖率
pytest --cov=core.rag --cov-report=term-missing
```
