# 分析-07-API降级与容错-代码事实

> summary: API降级与容错端点异常处理代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-07-API降级与容错
> COS路径: rag-slices/rag-system/代码/分析-07-API降级与容错-代码事实.md
> 类别：架构设计
> target: 开发对账

---

## api/rag.py 各端点异常处理（1.6C 检索 + source + eval）

| 端点 | try-except 位置 | 降级/兜底返回 | 边界拒答条件 | 证据 |
|---|---|---|---|---|
| `GET /api/rag/source/{file_path}` 查看原文 | 外层 try（67-71） | 读 COS 失败 → **404「文件不存在」**（71） | 前缀非 `rag-source/`/`rag-slices/` → 404（65-66，防任意 COS key 读取）；`verify_internal_token` 不符 → 403 | api/rag.py:57-72 |
| `POST /api/tutoring/rag/query` 1.6C 检索问答 | 内层 try（97-106）包 `retrieve_dual` | **向量路异常 → 降级纯 BM25**：构造 `full/slice/slice_q` 空结果 + `bm25 = retrieve_bm25`，references 仍返回 | 无 | api/rag.py:97-106 |
| 同上 | 内层 try（129-135）包 `generate` | **doubao 异常 → 降级召回块清单当答案**：`"生成服务不可用，以下为检索到的语料：\n- [{file}/{anchor}] {summary}"`（133-135） | 无 | api/rag.py:129-135 |
| 同上 | 无命中分支（120-126） | **拒答**：`answer="该问题语料未覆盖，建议问项目相关话题"`，references=[]，intent/version 仍返回 | `if not hits:`（仅空命中判断，**无置信度阈值**） | api/rag.py:120-126 |
| 同上 | 外层 try（84-142）+ except（143-147） | HTTPException 原样 re-raise（143-144）；其余异常 → **500「rag query failed」**（145-147） | 鉴权 403 | api/rag.py:143-147 |
| `POST /api/rag/eval/run` 触发评测（6.1） | 外层 try（157-165） | 异常 → **500「rag eval run failed」**（166-168）；run_eval 延迟导入 + 线程池不阻塞事件循环 | 鉴权 403 | api/rag.py:153-168 |
| `GET /api/rag/eval/report` 查询报告（6.2） | 外层 try（175-190） | 无报告 → `ok=True, has_report=False, reports=[]`（178-179）；异常 → **500「rag eval report failed」**（191-193） | 鉴权 403 | api/rag.py:171-193 |

## api/rag_assistant.py 白盒端点异常处理

| 端点 | try-except 位置 | 降级/兜底返回 | 证据 |
|---|---|---|---|
| `POST /api/rag/assistant/ask` 非流式 | `_run_once` 无 done → RuntimeError（99-100）；端点 try（117-120） | 异常 → **500「rag assistant ask failed」** | rag_assistant.py:116-120 |
| 同上 流式（SSE） | `gen()` try（127-135） | 异常 → **SSE error 事件 `{"code":"500","message":"rag assistant ask failed"}`**（133-135），不中断已发出的流 | rag_assistant.py:123-141 |
| `POST /api/rag/assistant/eval/run` 重新评测 | `_start_eval_async` 后台线程（49-67） | 已有一轮在跑 → **幂等 `already_running=true`**（不重复触发）；后台异常只记日志（61-62）；线程 daemon 不阻塞 HTTP | rag_assistant.py:49-67 / 203-213 |
| `GET /api/rag/assistant/eval/report` | 外层 try（163-200） | 无报告 → **404「暂无评估报告」**（166-167）；异常 → **500「rag assistant eval report failed」** | rag_assistant.py:155-200 |
| `GET /api/rag/assistant/guide` | 无 try | 静态池 0 token，`current_project` 未知 → `FALLBACK_MODULE`（ai-tutoring，guide_pool.py:313） | rag_assistant.py:144-152 |

## core/rag/query.py 意图/改写/生成的内部降级

| 环节 | 降级行为 | 证据 |
|---|---|---|
| `intent` 意图钩子 | `_llm_intent` 失败/超时/非法 JSON → 返回 `{}` → `intent` 回退关键词锚定（模块 `_fallback_module` + 节 `_fallback_anchor`），`degraded=True` 标记 | query.py:227-258（except 256-258）/ 293-338（degraded 304、回退 306-317） |
| `_llm_intent` LLM 参数 | doubao mini 关思考 + 0 温度 + **20s 超时 + max_retries=0**（意图判断要快，不卡 RAG 查询） | query.py:235-239 |
| `classify`/`_llm_category` | LLM 判类失败 → `""` → 回退 `_fallback_anchor` 关键词 | query.py:341-352 / 355-376（except 374-376） |
| `rewrite_query` 追问改写 | LLM 失败/空 → **回退原问题**（不降级成空串） | query.py:394-420（except 418-420） |
| `_deictic_anchor` 指代兜底 | LLM 把「这个功能底层怎么实现」误判跳 rag-system → 强制 anchor=current_project（改法4） | query.py:275-290 |
| `generate` 生成 | 默认不返回 usage（`return_usage=False` → 仅返回 str）；评测侧传 `return_usage=True` 才拿 usage | query.py:759-783（776-783） |
| `_load_all_blocks` | 多模块 jsonl **缺失文件跳过容错**（os.path.exists 检查），不因一个模块文件缺崩整链路 | query.py:436-449（445-448） |
| `select_corpus` | 该模块无语料 → 返回空池 → 编排层自然低置信过滤（C1 设计：无语料模块拒答正确） | query.py:609-617 |

> 证据：详见 `3.代码/分析-07-API降级与容错.md`（§代码事实：api/rag.py 与 rag_assistant.py 与 query.py 异常处理）
