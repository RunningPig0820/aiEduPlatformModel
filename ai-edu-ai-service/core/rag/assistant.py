"""
白盒链路编排引擎 - core/rag/assistant.py（A2b 起逐步搭建）

对齐: openspec/changes/rag-project-intro-assistant-python/api.md 事件时序
      intent → (clarify|switch) → rewrite → recall → rerank → (boundary|token) → done

职责: 把 query.py 的单元(intent/rewrite/retrieve/orchestrate/generate)编排成白盒链路,
      产出 SSE 事件流。Python 无状态(D-D 定死): history/trace_id 由 Java 传入只消费,
      turns/close/累计 token 归 Java Redis; 本模块只产出 per-turn 结果。

当前实现: A2b switch(resolve_switch) + A3 recall 双路(超时降级 + anchor 选池)
          —— 后续 A5/A6/A7/A8/A9 逐步填编排主体。
"""
import asyncio
import logging

from starlette.concurrency import run_in_threadpool

from config.settings import settings
from core.rag import query as rag_core

logger = logging.getLogger(__name__)

# A3: 召回降级标记(供 done/boundary 事件透传 degraded 语义)
DEGRADED_VECTOR = "vector_timeout"   # 向量路超时/异常 → 空路
DEGRADED_BM25 = "bm25_empty"          # BM25 路无命中(语料池空或本地无匹配)

# A4: rerank 精排 Top-K(白盒 rerank 事件默认回传块数, api.md "RRF Top-K 精排块(灰显)")
RERANK_K = 3


def last_anchor(history: list | None, current_project: str) -> str:
    """会话最后锚定模块(history 末轮 anchor); 无 history/无 anchor → current_project。

    供 switch 判定 from_anchor 用: 上一轮锚定的模块。
    """
    if history:
        anchor = history[-1].get("anchor", "") if isinstance(history[-1], dict) else ""
        if anchor in rag_core.MODULE_ANCHORS:
            return anchor
    return current_project


def resolve_switch(intent_result: dict, history: list | None,
                   current_project: str = "ai-tutoring") -> dict | None:
    """intent 结果 + 会话 → 是否需上下文切换(A2b, 对齐后端 D3)。

    switch_detected=true → 返回 {from_anchor, to_anchor, reset=True}(发起 switch 事件);
    否则 → None(不切换, 正常链路)。

    判定规则(后端 D3): switch_detected = (前端 current_project ≠ 会话已锚定 project)
    或 (问题明确指向另一有语料模块)。intent LLM 已给 switch_detected, 这里只算锚点。

    重置上下文语义(Python 无状态): reset 标记让编排器用 to_anchor 走新锚点
    rewrite→recall→generate; 轮次计数实际归 Java Redis(Python 只消费)。不掐断在途流——
    switch 只发生在下一轮 intent(生成中不做服务端掐流)。
    """
    if not intent_result or not intent_result.get("switch_detected"):
        return None
    from_anchor = last_anchor(history, current_project)
    to_anchor = intent_result.get("anchor") or from_anchor
    logger.info("RAG assistant switch: %s → %s", from_anchor, to_anchor)
    return {"from_anchor": from_anchor, "to_anchor": to_anchor, "reset": True}


# ============ A3 recall 双路 + anchor 选池 ============


async def _recall_vector(question: str) -> dict:
    """向量路超时包裹: asyncio.wait_for + run_in_threadpool(同步 COS 查询)。

    A3/D-B: 单路 2s 超时, 超时/异常 → 空路降级(confidence=0), 由编排器标记 degraded。
    """
    try:
        return await asyncio.wait_for(
            run_in_threadpool(rag_core.retrieve_vector, question),
            timeout=settings.RAG_RECALL_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("RAG 向量召回超时(%.1fs), 降级空路", settings.RAG_RECALL_TIMEOUT)
        return {"hits": [], "confidence": 0.0}
    except Exception as e:
        logger.warning("RAG 向量召回异常, 降级空路: %s", e)
        return {"hits": [], "confidence": 0.0}


async def recall(question: str, anchor: str | None = None,
                 blocks: list | None = None, top_k: int = rag_core.TOP_K) -> dict:
    """双路召回编排(A3): 向量(2s 超时降级) + BM25(本地) → 按 anchor 选池 → rerank。

    返回: {vec, bm25, degraded, rerank, corpus}。
    - anchor 明确(闭集) → select_corpus 先按模块过滤语料池, 再池内双路召回 + 池内 RRF 融合(C2)
    - anchor 空/非闭集 → 全池(向后兼容)
    - 向量路超时 → 空路 + degraded 标记; BM25 无命中(含语料池空) → degraded 标记
    - rerank = orchestrate 输出(锚定公式原样, corpus 传入池过滤)
    """
    blocks = blocks if blocks is not None else rag_core._load_blocks()
    vec = await _recall_vector(question)

    corpus = anchor if anchor in rag_core.MODULE_ANCHORS else None
    pool = rag_core.select_corpus(blocks, corpus)
    bm25 = rag_core.retrieve_bm25(question, pool)

    degraded = []
    if not vec["hits"]:
        degraded.append(DEGRADED_VECTOR)
    if not bm25["hits"]:
        degraded.append(DEGRADED_BM25)

    strategy = {"locked_sections": [], "strategy": "retrieve"}
    hits = rag_core.orchestrate(question, blocks, vec, bm25, strategy,
                                top_k=top_k, corpus=corpus)
    return {
        "vec": vec,
        "bm25": bm25,
        "degraded": degraded,
        "rerank": rerank_blocks(hits, top_k=RERANK_K),  # A4: 前端契约精排块(默认 3)
        "hits": hits,                                    # orchestrate 完整(含 text, generate 用)
        "corpus": corpus,
    }


# ============ A4 rerank 精排 Top-K 前端契约 ============


def rerank_blocks(hits: list, top_k: int = RERANK_K) -> list:
    """精排块 → 前端契约 {block_id, title, summary, file_path, score}(A4)。

    hits 为 orchestrate 输出(含 text/authority/source 等完整字段);
    只回传精排 Top-K(默认 3), 不吐全量召回。snake_case 产出, Java 中继 camel 化(api.md)。
    title 取锚点(或文件名兜底), 前端灰显引用面板用。
    """
    blocks = []
    for h in hits[:top_k]:
        blocks.append({
            "block_id": h.get("key", ""),
            "title": h.get("anchor") or h.get("file", ""),
            "summary": h.get("summary", ""),
            "file_path": h.get("file_path", ""),
            "score": h.get("score", 0.0),
        })
    return blocks


# ============ A5 generate 流式化 ============

# 写死降级话术(0 token, 严禁调 LLM 生成; C 组韧性常量在此, A5 先落 generate 侧)
GEN_TIMEOUT_MSG = "生成服务超时，未能生成完整答案。以下为检索到的参考资料："
GEN_FAIL_MSG = "生成服务异常，未能生成完整答案。以下为检索到的参考资料："


def _gen_prompt(hits: list, question: str) -> str:
    """生成 prompt: 检索块上下文(复用 query._GEN_SYSTEM 语义 + MAX_GEN_TEXT 截断)。"""
    ctx = []
    for h in hits:
        head = f"〔{h.get('source', '')}/{h.get('file', '')}/{h.get('anchor', '')}｜权威{h.get('authority', 0.7)}〕"
        ctx.append(f"{head}\n{h.get('text', '')[:rag_core.MAX_GEN_TEXT]}")
    return f"面试官问题：{question}\n\n--- 检索到的语料块 ---\n\n" + "\n\n".join(ctx)


def _degrade_text(reason: str, hits: list) -> str:
    """降级话术 + 召回清单(写死, 0 token)。"""
    lines = [reason]
    for h in hits[:rag_core.TOP_K]:
        lines.append(f"〔{h.get('source', '')}/{h.get('file', '')}/{h.get('anchor', '')}〕"
                     f"{h.get('summary', '')[:60]}")
    return "\n".join(lines)


# ============ A6 is_quoted 确定性引用(LCS 硬匹配) ============

# 引用窗口: 连续 ≥QUOTE_LEN_CN 中文字符 或 ≥QUOTE_LEN_EN 英文字符命中 → is_quoted=true
QUOTE_LEN_CN = 8
QUOTE_LEN_EN = 12


def _lcs_longest(a: str, b: str) -> str:
    """最长公共子串(LCS, 连续子串) — 纯函数。O(n*m) 动态规划, 中文按字符。"""
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return ""
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    best, end = 0, 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > best:
                    best, end = dp[i][j], i
            else:
                dp[i][j] = 0
    return a[end - best:end]


def _len_of(text: str) -> float:
    """折算窗口长度(对齐"8中/12英"语义): 中文/全角按字符计 1, 英文/数字按 8/12=0.667。

    8 中文 × 1.0 = 8.0 ≥ QUOTE_LEN_CN(8) ✓; 12 英文 × 0.667 = 8.0 ≥ 8 ✓;
    11 英文 × 0.667 = 7.33 < 8 ✗(窗口不足)。纯函数。
    """
    length = 0.0
    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch == " "):
            length += 8.0 / 12.0
        else:
            length += 1.0
    return length


def lcs_quote_match(answer: str, block_texts: list) -> list:
    """answer 与各精排块 text 做 LCS 硬匹配 → is_quoted 块序号列表(A6)。

    block_texts: 与 rerank 块同序的文本列表[{"block_id":..., "text":...}]。
    任意连续窗口 ≥8 中文字符(或 12 英文字符, 按 _len_of 折算)命中 → 该块 is_quoted。
    纯函数, 无 LLM, 可单测可入评估。done 后补发 quoted_keys(chunk 粒度会撕裂窗口)。
    """
    quoted = []
    for blk in block_texts:
        match = _lcs_longest(answer, blk.get("text", ""))
        if match and _len_of(match) >= QUOTE_LEN_CN:
            quoted.append(blk.get("block_id"))
    return quoted


# ============ A7 clarify 澄清轮 ============

CLARIFY_MSG = "您的问题涉及多个功能，请明确功能名。默认回答当前功能：{default}"
CLARIFY_MIN_CANDIDATES = 2  # candidates <2 不触发 clarify(仍模糊直接走默认)


def _history_anchors(history: list) -> list:
    """会话最近 N 轮锚过的模块, 去重保序(候选兜底源, C4 ②)。"""
    seen, out = set(), []
    for turn in rag_core._truncate_history(history):
        anchor = turn.get("anchor", "") if isinstance(turn, dict) else ""
        if anchor in rag_core.MODULE_ANCHORS and anchor not in seen:
            seen.add(anchor)
            out.append(anchor)
    return out


def _last_turn_is_clarify(history: list) -> bool:
    """历史末轮是否 clarify 轮(answer 空 = 无生成, 0 token 轮) → 已澄清过一次。"""
    if not history:
        return False
    last = history[-1]
    return not (last.get("answer") if isinstance(last, dict) else None)


def resolve_clarify(intent_result: dict, history: list | None,
                    current_project: str = "ai-tutoring") -> dict | None:
    """歧义判定 → clarify 事件或 None(A7, 对齐后端 D5)。

    触发条件: intent.ambiguous=true 且候选 ≥2(C4) 且此前未澄清过(最多一轮)。
    返回 {message, candidates, default}(随后 done), 0 token、不计答案轮次、写 history(Java 组装)。
    None → 不触发(走正常链路或直接默认 current_project)。

    候选判定(C4): 主源 = intent.candidates(LLM 闭集 2~4); <2 → 会话最近 N 轮锚过模块
    去重兜底; 仍 <2 → 不触发 clarify, 直接走默认。default = current_project 优先
    > 会话最后锚定功能(前端 current_project > 历史锚点)。
    """
    if not intent_result or not intent_result.get("ambiguous"):
        return None
    if _last_turn_is_clarify(history):
        # 最多一轮: 上一轮已 clarify(answer 空) → 本轮仍模糊不再二次澄清, 直接走默认
        return None

    candidates = [c for c in intent_result.get("candidates", [])
                  if c in rag_core.MODULE_ANCHORS]
    # 去重保序
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) < CLARIFY_MIN_CANDIDATES:
        # 兜底: 历史锚过模块去重填充(排除已在候选的)
        for a in _history_anchors(history):
            if a not in candidates:
                candidates.append(a)
    if len(candidates) < CLARIFY_MIN_CANDIDATES:
        return None  # 仍 <2 → 不触发

    default = current_project if current_project in rag_core.MODULE_ANCHORS else None
    if default is None:
        for a in _history_anchors(history):  # 会话最后锚定功能兜底
            default = a
    if default is None:
        default = rag_core.MODULE_ANCHORS[0]  # 最后兜底 ai-tutoring
    logger.info("RAG assistant clarify: candidates=%s default=%s", candidates, default)
    return {"message": CLARIFY_MSG.format(default=default),
            "candidates": candidates, "default": default}


# ============ A8 suggestions 引导 ============

# 静态池兜底(预写 2~3 条, 含 RAG 方向常驻; 对齐后端 D11: 定位/架构/数据流/评测)
STATIC_SUGGESTIONS = [
    "想了解 RAG 的整体架构吗？可以聊聊多路召回和 RRF 融合",
    "想知道知识库语料是如何流转入库的吗？从切片到向量索引",
    "想看看评测体系是怎么设计的吗？hit@k 和判分机制",
]

_SUGGEST_SYSTEM = """你是「AI答疑」RAG 助手的引导建议生成器。根据上一轮回答，给面试官 1~3 条"接下来可以问什么"的建议。

规则：
1. 必须是疑问句式，可直接作为下一个问题（例如"想了解 X 吗？"）
2. 1~3 条，每条一行，不要编号
3. **必须包含至少 1 条 RAG 方向**（RAG 是底层引擎，任何模块回答后都应把话题带回 RAG：多路召回/RRF 融合/向量索引/评测/防作弊护栏）
4. 其余可围绕回答内容追问（项目介绍/操作/数据关联/难点）
只输出建议文本，每行一条。"""


def gen_suggestions(answer: str, anchor: str = "", llm=None) -> list:
    """结束引导: LLM 生成 1~3 条建议, 必含 ≥1 条 RAG 方向(C5/D11); 失败 → 静态池兜底。

    llm 注入用(测试); 默认 doubao 0.2 温度短调用。返回 1~3 条建议列表。
    """
    try:
        import json as _json
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.gateway.factory import LLMFactory
        if llm is None:
            llm = LLMFactory.create(
                "doubao", settings.TUTORING_GENERATE_MODEL, temperature=0.2,
                extra_body={"thinking": {"type": "disabled"}},
                request_timeout=20, max_retries=0,
            )
        text = llm.invoke([
            SystemMessage(content=_SUGGEST_SYSTEM),
            HumanMessage(content=f"上一轮回答（节选）：{answer[:400]}\n\n当前模块：{anchor}\n\n请生成建议："),
        ]).content or ""
        lines = [ln.strip().lstrip("1234567890.、）) ") for ln in text.strip().splitlines()
                 if ln.strip()]
        if 1 <= len(lines) <= 3:
            return lines
        # LLM 输出形状异常(0 条或 >3 条) → 兜底静态池
        return list(STATIC_SUGGESTIONS)
    except Exception as e:
        logger.warning("RAG suggestions LLM 失败, 静态池兜底: %s", e)
        return list(STATIC_SUGGESTIONS)


# ============ A9 范围门低置信过滤(唯一拒答路径) ============

# 低置信阈值(guardrails spec): 向量(索引层)0.75 / BM25(源)0.5。
# 用召回置信度(0-1)而非 rerank 的 RRF 相对分(量级 0.01~0.05, 天花板也够不到阈值)。
# 双路都低于各自阈值 → 低置信拒答; 单路高即过(双路召回互补, 一路够用)。
BOUNDARY_VEC_CONF = 0.75
BOUNDARY_BM_CONF = 0.5
BOUNDARY_MSG = "未找到关联文档，我尚未掌握。"
BOUNDARY_REASON = "low_confidence"


def check_boundary(rerank: list, vec_conf: float = 0.0, bm_conf: float = 0.0) -> dict | None:
    """范围门低置信判定(A9): 双路召回置信度都低于阈值 → boundary(固定话术, 不调 generate)。

    rerank: recall 输出(前端契约块)。vec_conf/bm_conf: 召回单元置信度(0-1)。
    判定:
      1. rerank 空(无语料模块/无命中) → 拒答(C1 唯一拒答路径)
      2. 非空但 vec_conf < 0.75 且 bm_conf < 0.5 → 拒答(双路都低才算低置信)
      3. 否则通过 → generate
    返回 {message, reason} 供 boundary 事件; None → 通过范围门。
    """
    if not rerank:
        return {"message": BOUNDARY_MSG, "reason": BOUNDARY_REASON}
    if vec_conf < BOUNDARY_VEC_CONF and bm_conf < BOUNDARY_BM_CONF:
        return {"message": BOUNDARY_MSG, "reason": BOUNDARY_REASON}
    return None


async def stream_generate(hits: list, question: str, request=None,
                          streamer=None) -> "async generator":
    """流式生成 async generator(A5): yield {type: token|usage|error}。

    - 复用 ark_stream.stream_chat 直连方舟(真流式, 逐 delta 从 executor 线程拉取)
    - include_usage=True → 流末尾 usage chunk → yield {type:usage}
    - request.is_disconnected() 每轮检测 → 中止(不掐 httpx 流, 在途流完成或前端取消)
    - 超时/异常 → yield {type:error, text: 写死话术 + 召回清单}(0 token)
    - streamer 参数注入(测试用 fake 生成器)

    Usage:
        async for ev in stream_generate(hits, question, request):
            if ev["type"] == "token":   # {text}
            elif ev["type"] == "usage": # {usage: {prompt_tokens, completion_tokens, ...}}
            elif ev["type"] == "error": # {text: 降级话术}
    """
    import asyncio

    from core.tutoring import ark_stream

    streamer = streamer or ark_stream.stream_chat
    conn = ark_stream.doubao_conn(settings.TUTORING_GENERATE_MODEL, temperature=0.2)
    messages = [
        {"role": "system", "content": rag_core._GEN_SYSTEM},
        {"role": "user", "content": _gen_prompt(hits, question)},
    ]

    queue: asyncio.Queue = asyncio.Queue()
    _END = object()

    def _pull():
        """在 executor 线程构造并逐 delta 拉取同步流, 灌入队列。

        gen 构造也在线程内(httpx 连接异常同样被捕获, 不逃逸到 async 主体)。
        """
        try:
            gen = streamer(**conn, messages=messages,
                           timeout=settings.RAG_GEN_TIMEOUT, include_usage=True)
            for delta in gen:
                queue.put_nowait(delta)
        except Exception as e:
            queue.put_nowait(("__error__", str(e)))
        finally:
            queue.put_nowait(_END)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _pull)

    while True:
        if request is not None and await request.is_disconnected():
            logger.info("RAG 流式生成: 客户端断开, 中止; 在途流交由前端取消")
            return
        try:
            item = await asyncio.wait_for(queue.get(), timeout=settings.RAG_GEN_TIMEOUT)
        except asyncio.TimeoutError:
            yield {"type": "error", "text": _degrade_text(GEN_TIMEOUT_MSG, hits)}
            return
        if item is _END:
            break
        if isinstance(item, tuple) and item and item[0] == "__error__":
            logger.warning("RAG 流式生成异常, 降级话术: %s", item[1])
            yield {"type": "error", "text": _degrade_text(GEN_FAIL_MSG, hits)}
            return
        if item.get("content"):
            yield {"type": "token", "text": item["content"]}
        if item.get("usage"):
            yield {"type": "usage", "usage": item["usage"]}
