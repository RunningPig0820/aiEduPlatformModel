# RAG 项目介绍助手 — Python 对接说明（2026-08-25）

> 给前端/后端：Python 白盒链路的端点、事件时序、引用面板、停止方式、鉴权。
> 对齐后端契约：`aiEduPlatform/openspec/changes/rag-project-intro-assistant/api.md`
> Python 侧变更：`openspec/changes/rag-project-intro-assistant-python/`
> 本文是**对后端 api.md 的 Python 落地补充**——端点/事件/字段以两端 api.md 为准，本文侧重对接时的注意点与 Java 桥分工。

---

## 一、链路总览

```
前端 ──camelCase──▶ Java 网关 ──snake_case──▶ Python /api/rag/assistant/*
                      │ 角色门(仅 STUDENT)         │ 白盒引擎
                      │ permission 事件(Java 产)    │ intent→rewrite→rerank→token→done
                      │ turns/close/累计 token      │ (Python 无状态, 只产 per-turn)
                      ▼                             ▼
                   Redis                        doubao 流式生成
```

**分工（定死）**：
| 职责 | 归属 |
|------|------|
| 角色门 / permission 事件 | **Java**（Python 生产端点不产 permission） |
| history / trace_id 生成 | **Java**（Python 只消费；done 回显 trace_id） |
| turns 补查 / close / 会话累计 token | **Java Redis**（Python 不建 close/turns 端点） |
| 查看原文 | **Java 代理** `GET /api/rag/assistant/source?path=` → Python `/api/rag/source` |

---

## 二、Python 端点

基础路径 `/api/rag/assistant`，鉴权 `x-internal-token`（与现有 API 一致）。

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/rag/assistant/ask` | 流式（`stream=true` 走 SSE）/ 非流式 |
| GET | `/api/rag/assistant/guide` | 开始引导（RAG 定向静态池，非 SSE） |
| GET | `/api/rag/assistant/eval/report` | baseline 报告（hit@3/质量分/cost/latency/语料版本） |

Python **不建**：close、turns（归 Java）。

---

## 三、SSE 事件时序（冻结）

```
intent → (clarify|switch) → rewrite → rerank → (boundary|token*) → done
```

> **无 permission**：Python 生产端点从 `intent` 开始。Java 桥从 Python `intent` 事件转发，前端看到的是 `permission`(Java) → `intent`(Python) → … 

| 事件 | data（snake_case，Java 中继 camel 化） | 前端渲染 |
|------|------|------|
| `intent` | `{anchor, category, switch_detected, ambiguous, candidates, locked_sections, degraded}` | 阶段卡片：模块路由 + 节级加权两层 |
| `clarify` | `{message, candidates, default}` | 候选 chips 点选（**重发原问题 + currentProject=点选模块**，不要裸发候选名当 question） |
| `switch` | `{from_anchor, to_anchor}` | 提示"已切换至 X" |
| `rewrite` | `{original_question, rewritten_query}` | 改写前后对比 |
| `rerank` | `{blocks: [{block_id, title, summary, file_path, score}]}` | 引用面板**灰显** + 折叠，点击 filePath 看原文 |
| `boundary` | `{message, reason="low_confidence"}` | 展示"未找到关联文档，我尚未掌握"（随后 done） |
| `token` | `{text}` | 正文流式 |
| `done` | 见下 | 高亮 quotedKeys + 成本 + suggestions |

**`done` data**：
```json
{
  "answer": "……",
  "quoted_keys": ["block-01"],
  "tokens_usage": {"prompt_tokens": 320, "completion_tokens": 140, "cache_hit_tokens": 0, "total_tokens": 460},
  "trace_id": "trc-abc123",
  "suggestions": ["想了解RAG的整体架构吗？"],
  "reason": null
}
```
- `reason`：`low_confidence`（边界拒答）/ `timeout`（生成降级）/ `null`（正常）。**boundary/降级是正常业务结果，不是错误**。
- `suggestions` 必含 ≥1 条 RAG 方向。

---

## 四、引用面板（先灰后亮）

1. `rerank` 事件到达 → 立即渲染块（灰显 + 折叠）。
2. `done.quoted_keys` 到达 → 命中的块**高亮展开**，未命中保持灰显。
3. `quoted_keys` 为空 → 无需额外提示（answer 已标注"引用未能精确匹配"）。

---

## 五、停止方式

- **前端关闭连接**：Python `request.is_disconnected()` 在 generate 前/中检测 → 中止 doubao 流（生成中断连：已产 token 保留，不再产后续）。
- **会话关闭**：学生点"结束对话" → 前端 `POST /sessions/{sessionId}/close`（Java）+ 取消 fetch。Python 不建 close 端点，靠 is_disconnected 中止在途流。
- 关闭后同 session 再提问 → Java 返回固定话术"本轮对话已结束，可开启新对话"（Python 常量 `CLOSED_MSG`，契约对齐）。

---

## 六、降级话术（Python 写死，0 token）

| 场景 | 常量 | 话术 |
|------|------|------|
| 边界低置信 | `BOUNDARY_MSG` | 未找到关联文档，我尚未掌握。 |
| 生成超时 | `GEN_TIMEOUT_MSG` | 生成服务超时，未能生成完整答案。以下为检索到的参考资料： |
| 生成异常 | `GEN_FAIL_MSG` | 生成服务异常，未能生成完整答案。以下为检索到的参考资料： |
| 会话已关闭（Java 产） | `CLOSED_MSG` | 本轮对话已结束，可开启新对话。 |

---

## 七、模块闭集（三端定稿）

```
ai-tutoring / knowledge-graph / question-analysis / rag-system
```
- `current_project` 缺省 = `rag-system`（对齐后端 api.md；Java 桥缺省也补 rag-system）。
- 语料选池靠 `tags.module` 字段（不依赖目录名）；`slice_corpus.py` 已按闭集 id 参数化。
- clarify candidates / intent anchor 均取闭集 id。

---

## 八、评测与报告

- `GET /api/rag/assistant/eval/report`：读 `run_eval` 落盘的 `data/eval/reports/<version>.json`，返回 `version/count/hit_at_3/quality_avg/avg_latency_ms/avg_cost_yuan/judged_ratio/precision_at_3/quoted_valid_ratio`。无报告 → 404 "暂无评估报告"。
- 评测集 `VALID_TYPES` 含 **`边界拒答`**（断言=触发固定话术且 0 token）。
- 真实评测：`cd ai-edu-ai-service && venv/bin/python scripts/rag/run_eval.py`（真实 COS 检索 + doubao 生成/判分，消耗真实 token）。

---

## 九、测试

```bash
cd ai-edu-ai-service && venv/bin/python -m pytest tests/rag/ -q   # 210 passed
cd ai-edu-ai-service && venv/bin/python -m pytest tests/ --ignore=tests/llm/real --ignore=tests/tutoring/real -q   # 488 passed
```

---

## 十、联调 Checklist（对照后端 api.md）

- [ ] Java 桥 `snake↔camel` 转换正确（current_project/session_id/trace_id/top_k ↔ currentProject/sessionId/traceId/topK）
- [ ] permission 仅 Java 产，Python 从 intent 转发
- [ ] trace_id 全程一致：Java 生成 → Python 回显 → 断线补查 `GET /turns/{traceId}`
- [ ] close 中止在途流：Java 关中继 → Python is_disconnected
- [ ] 查看原文 Java 代理 `GET /api/rag/assistant/source?path=`（走 query 不走 path）
- [ ] eval/report 白盒展示含语料版本
