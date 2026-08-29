"""
3. 评测 agent 核心 - rag-eval-agent 工具底座(AI答疑 评测依赖)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 2A 评测设计 + openspec/changes/rag-eval-agent/design.md D3~D6

流程(3.1, 单条评测):
  意图钩子 → 双路召回(真实, 不降级) → orchestrate 记录 top-K
  → hit@k(3.2): expected_references 命中召回集比例
  → generate(3.1) → LLM 判分(3.3): answer_quality(答案, 预期要点) → 0~5 + rationale
  → trace(3.1): 每轮落 dict(供 5.1 落盘)

关键设计:
- 评测走**真实检索原语**(retrieve_vector/retrieve_bm25/orchestrate), 不走 rag_query
  (API 带降级语义, 评测要看真实质量, 向量挂了就暴露, 不让降级掩盖问题)
- hit@k 是纯函数(可单测); 判分 LLM 可注入(mock)
"""
import json
import logging
import time
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from core.gateway.factory import LLMFactory
from core.rag import assistant as rag_assistant  # D3: lcs_quote_match / D1: check_boundary
from core.rag import query as rag_core

logger = logging.getLogger(__name__)

HIT_K = 5           # hit@k 的 k(2026-08-26: 3→5, 对齐生成上下文 top-5; 双向量后引导问题块精确命中 #1, 深度节块常落 4-5)

# D1: 边界拒答评测类型(与 eval_dataset.VALID_TYPES 闭集一致; 断言=触发固定话术+0 token)
BOUNDARY_TYPE = "边界拒答"

# doubao-seed-2-0-mini 单价(元/千 token; 2026-08 火山方舟价, 精确单价变动时更新)
DOUBAO_PRICE_PER_1K = {
    "input": 0.003,      # 输入 prompt 单价(元/千 token)
    "output": 0.009,     # 输出 completion 单价(元/千 token)
}


# ============ 4.1 cost 计算(纯函数, 可单测) ============


def calc_cost(usage: dict) -> float:
    """token usage → 成本(元)。无 usage → 0(降级估算留给调用方)。"""
    return round(
        usage.get("prompt_tokens", 0) / 1000 * DOUBAO_PRICE_PER_1K["input"]
        + usage.get("completion_tokens", 0) / 1000 * DOUBAO_PRICE_PER_1K["output"],
        6,
    )


# ============ 3.2 hit@k 计算(纯函数, 可单测) ============


def _match_file(expected: str, files) -> bool:
    """expected 引用是否命中某个召回块的 file(双向子串匹配)。

    新格式(2026-08-26 双向量后): expected = 承载答案的源文件标识
      - 完善文档(全量池 file): "01-模块定位与核心价值" / "05-数据落库与掌握度"
      - 引导问题(切片池 file): "引导问题-05-操作流程-怎么防学生套答案"
    旧格式兼容: "ai-tutoring/04-安全与防作弊" 内含节号 "04", 与 file="04" 双向匹配。
    语义: 该来源文件是否进入召回 top-k(即答案上下文含该来源)。
    """
    e = expected.strip()
    return any(e in str(f) or str(f) in e for f in files)


def hit_at_k(recall: List[dict], expected_references: List[str], k: int = HIT_K) -> float:
    """预期来源文件命中召回 top-k 的比例。

    expected_references: 承载答案的源文件标识(完善文档/引导问题 file 名, 见 _match_file)
    recall: orchestrate 输出 top-K, 每项含 file/anchor
    判定: 预期来源的 file 是否出现在召回 top-k 中。
    返回: 命中比例 0~1(可多条引用部分命中)。
    """
    if not expected_references or k <= 0:
        return 0.0
    top_k = recall[:k]
    hit_files = [str(h.get("file")) for h in top_k]
    return sum(1 for e in expected_references if _match_file(e, hit_files)) / len(expected_references)


# ============ D2: precision@k 纯函数 ============


def precision_at_k(recall: List[dict], expected_references: List[str],
                   k: int = HIT_K) -> float:
    """召回 top-k 中相关块占比(D2, 可单测/可聚合)。

    与 hit_at_k 互补:
      - hit_at_k: 预期来源有多少被召回(分母 = 预期来源数, 看"该捞的捞到没")
      - precision_at_k: 召回的 top-k 里有多少是相关的(分母 = k, 看"捞上来的干不干净")
    相关块判定同 hit_at_k(块的 file 命中预期来源, 见 _match_file)。
    返回 0~1; k<=0 或预期空 → 0。
    """
    if k <= 0 or not expected_references:
        return 0.0
    top_k = recall[:k]
    expected = [e.strip() for e in expected_references]
    relevant = sum(1 for h in top_k
                   if any(_match_file(e, [str(h.get("file"))]) for e in expected))
    return relevant / k


# ============ 3.3 LLM 判分 ============


_JUDGE_SYSTEM = """你是 RAG 检索质量评审。给定"面试问题 + 检索到的语料块 + 生成答案 + 预期要点"，严格按下列业务规则打分。

【输出判定】(逐条比对预期要点, 只报告两个事实, 不要自己算总分):
1. covered_count: 答案**覆盖了多少条**预期要点(整数, 同义表述覆盖即算覆盖, 不要求逐字出现; 如"出口两次"算覆盖"reveal两次出口")。
2. fabricated: 是否存在**编造**内容(布尔, true/false)。判断依据=检索到的语料块: 答案表述只要在任意一块语料中有直接原文或合理推断支撑即不算编造; 语料含多源(完善文档/代码/坑档案/语雀/OpenSpec), 有出处就不算; 语料块因 600 字截断导致无法验证的部分, 不算编造。

分数由外部按规则计算(你不要输出 score)。只需:
- 逐条判断每个预期要点覆盖了没有
- 判断整体是否有编造
- 若预期要点被完整列出, 请把"覆盖了几条/共几条"写进 rationale

严格输出 JSON: {"covered_count": 整数, "fabricated": true/false, "rationale": "覆盖X/Y条; 编造有/无; 未覆盖的要点(若有)"}。不要任何其他文字。"""


def judge_quality(question: str, answer: str, expected_points: List[str],
                  corpus_texts: Optional[List[str]] = None, llm=None) -> dict:
    """LLM 判分 → {score, rationale}; 解析失败重试1次, 仍失败记 0 并标记。

    corpus_texts: 检索到的语料块文本(供"编造"判定——答案表述在语料有支撑即非编造)。
    llm 可注入(测试 mock); 默认 doubao(与生成同模型, 能力一致)。
    """
    llm = llm or _make_judge_llm()
    prompt = (
        f"面试问题：{question}\n\n生成答案：\n{answer}\n\n"
        f"预期要点：\n" + "\n".join(f"- {p}" for p in expected_points) + "\n"
    )
    if corpus_texts:
        prompt += ("\n检索到的语料块(判断'编造'的依据, 答案表述在其中有支撑即不算编造)：\n"
                   + "\n---\n".join(t[:600] for t in corpus_texts[:4]) + "\n")
    for attempt in range(2):
        try:
            resp = llm.invoke([
                SystemMessage(content=_JUDGE_SYSTEM),
                HumanMessage(content=prompt),
            ])
            text = resp.content or ""
            usage = getattr(resp, "usage_metadata", None) or {}
            data = _extract_json(text)
            covered = int(data.get("covered_count", -1))
            fabricated = bool(data.get("fabricated"))
            total = len(expected_points)
            if 0 <= covered <= total:
                return {"score": _score_from_covered(covered, total, fabricated),
                        "rationale": str(data.get("rationale", "")), "judged": True,
                        "usage": {"prompt_tokens": usage.get("input_tokens", 0),
                                  "completion_tokens": usage.get("output_tokens", 0),
                                  "total_tokens": usage.get("total_tokens", 0)}}
            logger.warning("判分 covered_count 越界(%s), 重试", covered)
        except Exception as e:
            logger.warning("判分解析失败(尝试%d): %s", attempt + 1, e)
    return {"score": 0, "rationale": "判分解析失败", "judged": False}


def _score_from_covered(covered: int, total: int, fabricated: bool) -> int:
    """按覆盖比例 + 编造封顶硬算分数(消除 LLM 百分比计算波动)。

    编造 ≥1 处 → 封顶 3 分(编造权重高于遗漏)。
    覆盖比例: 100%→5, ≥80%→4, ≥60%→3, ≥40%→2, >0%→1, 0%→0。
    """
    if covered <= 0:
        return 0
    ratio = covered / total if total else 0
    if ratio >= 1.0:
        base = 5
    elif ratio >= 0.8:
        base = 4
    elif ratio >= 0.6:
        base = 3
    elif ratio >= 0.4:
        base = 2
    else:
        base = 1
    return min(base, 3) if fabricated else base


def _make_judge_llm():
    return LLMFactory.create(
        "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.0,
        extra_body={"thinking": {"type": "disabled"}},
        request_timeout=30, max_retries=0,
    )


def _extract_json(text: str) -> dict:
    """从文本提取 JSON 对象(兼容模型输出前后空白/说明)。"""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"无 JSON 对象: {text[:100]!r}")
    return json.loads(text[start:end + 1])


# ============ 3.1 单条评测执行 ============


def _quoted_check(answer: str, hits: list) -> tuple:
    """D3: is_quoted 校验 —— lcs_quote_match 算 quoted_keys, 断言 ⊆ 召回块 key。

    返回 (quoted_keys, valid)。valid = 每个 quoted key 都对应一个精排召回块。
    空 answer(降级/拒答) → 空列表, valid=True(无引用自然合法)。
    """
    if not answer:
        return [], True
    hits_k = hits[:HIT_K]
    quoted_keys = rag_assistant.lcs_quote_match(answer, [
        {"block_id": h.get("key", ""), "text": h.get("text", "")} for h in hits_k])
    recall_keys = {h.get("key") for h in hits_k}
    valid = all(k in recall_keys for k in quoted_keys)
    return quoted_keys, valid


def run_eval_case(case: dict, top_k: int = rag_core.TOP_K) -> dict:
    """单条评测: 检索 → hit@k → 生成 → 判分 → trace。

    case: 评测集一条(module/question/question_type/expected_references/expected_points)
    返回 trace dict(5.1 落盘结构):
      {question, question_type, intent, recall[], hit, hit_score,
       answer, references[], usage, latency_ms, score, rationale, judged,
       quoted_keys, quoted_valid}(D3 新增; 边界拒答类型走 _boundary_trace)
    """
    question = case["question"]
    t0 = time.time()

    # 检索(真实原语, 不降级; 1.13 双池: intent 判模块/类别 + 双池三路召回)
    # 2026-08-29 多模块评测: 以评测集 case["module"] 为准(意图自动路由可能误判模块, 如 kg 问题被路由到 ai-tutoring)
    blocks = rag_core._load_all_blocks()
    it = rag_core.intent(question)
    corpus = (case["module"] if case.get("module") in rag_core.MODULE_ANCHORS
              else (it["anchor"] if it["anchor"] in rag_core.MODULE_ANCHORS else None))
    dual = rag_core.retrieve_dual(question, corpus=corpus,
                                  locked_categories=it["locked_categories"])
    hits = rag_core.orchestrate(question, blocks, dual["full"], dual["bm25"], it,
                                top_k=top_k, vec2_result=dual["slice"],
                                vec3_result=dual["slice_q"], corpus=corpus)

    recall = [
        {"key": h["key"], "score": h["score"], "authority": h["authority"],
         "section": h["section"], "file": h["file"], "anchor": h["anchor"]}
        for h in hits
    ]
    t_recall = time.time()

    # D1: 边界拒答类型 → 断言触发 boundary(固定话术 + 0 token, 不进 generate)
    if case["question_type"] == BOUNDARY_TYPE:
        return _boundary_trace(case, recall, dual, it, blocks, t0, t_recall)

    # hit@k + precision@k(D2: top-k 相关块占比, 可聚合)
    hit = hit_at_k(recall, case["expected_references"], k=HIT_K)
    precision = precision_at_k(recall, case["expected_references"], k=HIT_K)
    answer = ""
    score, rationale, judged = 0, "", False
    gen_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    judge_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    if hits:
        answer, gen_usage = rag_core.generate(hits, question, return_usage=True)
        judge = judge_quality(question, answer, case["expected_points"],
                              corpus_texts=[h["text"] for h in hits])
        score, rationale, judged = judge["score"], judge["rationale"], judge["judged"]
        judge_usage = judge.get("usage", judge_usage)
    t_done = time.time()

    # D3: is_quoted 校验(quotedKeys ⊆ 召回块, 入 trace)
    quoted_keys, quoted_valid = _quoted_check(answer, hits)

    usage = {
        "generate": gen_usage,
        "judge": judge_usage,
        "total_tokens": gen_usage.get("total_tokens", 0) + judge_usage.get("total_tokens", 0),
        "cost_yuan": round(calc_cost(gen_usage) + calc_cost(judge_usage), 6),
    }

    return {
        "question": question,
        "question_type": case["question_type"],
        "intent": it,
        "recall": recall,
        "hit": bool(hit > 0),
        "hit_score": hit,
        "precision": precision,
        "answer": answer,
        "references": [{"file": h["file"], "file_path": h.get("file_path", ""),
                        "anchor": h["anchor"], "authority": h["authority"],
                        "summary": h.get("summary", "")} for h in hits],
        "score": score,
        "rationale": rationale,
        "judged": judged,
        "quoted_keys": quoted_keys,
        "quoted_valid": quoted_valid,
        "usage": usage,
        "latency_ms": {
            "retrieve_ms": round((t_recall - t0) * 1000),
            "generate_ms": round((t_done - t_recall) * 1000),
            "total_ms": round((t_done - t0) * 1000),
        },
        "version": rag_core._current_version(blocks),
    }


def _boundary_trace(case: dict, recall: list, dual: dict, it: dict,
                    blocks: list, t0: float, t_recall: float) -> dict:
    """D1: 边界拒答评测 —— 断言触发低置信 boundary, 固定话术 + 0 token, 不进 generate。

    判定: 复用 assistant.check_boundary(空 rerank 或双路置信度低于阈值)。
    触发 → 拒答正确(score=5); 未触发(意外高置信) → 拒答失败(score=0)。
    0 token: 不调 generate/判分; quoted 空(无答案自然无引用)。
    1.13 双池: vec_conf = max(全量, 切片) 任一置信即不算低。
    """
    from core.rag.assistant import check_boundary
    vec_conf = max(dual["full"].get("confidence", 0.0), dual["slice"].get("confidence", 0.0))
    bd = check_boundary(recall,
                        vec_conf=vec_conf,
                        bm_conf=dual["bm25"].get("confidence", 0.0))
    ok = bd is not None
    t_done = time.time()
    zero = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    return {
        "question": case["question"],
        "question_type": BOUNDARY_TYPE,
        "intent": it,
        "recall": recall,
        "hit": False,
        "hit_score": 0.0,
        "precision": 0.0,                               # 边界拒答预期不命中, precision 0
        "answer": bd["message"] if ok else "",          # 拒答成功=固定话术; 失败=空
        "references": [],
        "score": 5 if ok else 0,                        # 拒答正确满分, 失败 0
        "rationale": "边界拒答正确: 触发低置信固定话术, 0 token" if ok
                     else "边界拒答失败: 未触发低置信(意外高置信命中)",
        "judged": True,
        "quoted_keys": [],
        "quoted_valid": True,
        "usage": {"generate": zero, "judge": zero, "total_tokens": 0, "cost_yuan": 0.0},
        "latency_ms": {
            "retrieve_ms": round((t_recall - t0) * 1000),
            "generate_ms": 0,
            "total_ms": round((t_done - t0) * 1000),
        },
        "version": rag_core._current_version(blocks),
    }


# ============ 3.4 聚合 ============


def aggregate(results: List[dict]) -> dict:
    """按模块(本期单模块 ai-tutoring)聚合指标。

    {count, hit_at_k_avg, quality_avg, judged_ratio, avg_latency_ms,
     total_cost_yuan, avg_cost_yuan, avg_tokens, ...}(4.1 cost / 4.2 latency)
    D2/D3 新增: precision_at_k_avg(top-k 相关块占比均值) / quoted_valid_ratio(引用合法率)
    """
    n = len(results)
    empty = {"count": 0, "hit_at_k_avg": 0.0, "quality_avg": 0.0, "judged_ratio": 0.0,
             "avg_latency_ms": 0.0, "total_cost_yuan": 0.0, "avg_cost_yuan": 0.0,
             "avg_tokens": 0, "precision_at_k_avg": 0.0, "quoted_valid_ratio": 0.0}
    if n == 0:
        return empty
    hit_avg = sum(r["hit_score"] for r in results) / n
    quality_avg = sum(r["score"] for r in results) / n
    judged = sum(1 for r in results if r["judged"])
    latency = [r["latency_ms"]["total_ms"] for r in results]
    cost = [r.get("usage", {}).get("cost_yuan", 0.0) for r in results]
    tokens = [r.get("usage", {}).get("total_tokens", 0) for r in results]
    # D2: precision@k 均值(边界拒答 hit_score 0, precision 由 _quoted 判定外补充)
    precision = [r.get("precision", 0.0) for r in results]
    # D3: quoted_valid 合法率(quoted_keys ⊆ 召回块)
    quoted_valid = sum(1 for r in results if r.get("quoted_valid", True))
    return {
        "count": n,
        "hit_at_k_avg": round(hit_avg, 3),
        "quality_avg": round(quality_avg, 3),
        "judged_ratio": round(judged / n, 3),
        "avg_latency_ms": round(sum(latency) / n),
        "hit_cases": sum(1 for r in results if r["hit"]),
        "unjudged": n - judged,
        "total_cost_yuan": round(sum(cost), 4),
        "avg_cost_yuan": round(sum(cost) / n, 4),
        "avg_tokens": round(sum(tokens) / n),
        "precision_at_k_avg": round(sum(precision) / n, 3),
        "quoted_valid_ratio": round(quoted_valid / n, 3),
    }
