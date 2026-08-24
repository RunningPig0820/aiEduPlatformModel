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
from core.rag import query as rag_core

logger = logging.getLogger(__name__)

HIT_K = 3           # hit@k 的 k(2A 定稿: 源文档池 top-k)


# ============ 3.2 hit@k 计算(纯函数, 可单测) ============


def hit_at_k(recall: List[dict], expected_references: List[str], k: int = HIT_K) -> float:
    """预期引用命中召回 top-k 的比例。

    expected_references: ["ai-tutoring/04-安全与防作弊", ...](节 key 前缀)
    recall: orchestrate 输出 top-K, 每项含 section(如 "04")/file/anchor
    判定: 预期引用的节号(0X) 是否出现在召回 top-k 的 section 集合中。
    返回: 命中比例 0~1(可多条引用部分命中)。
    """
    if not expected_references or k <= 0:
        return 0.0
    top_k = recall[:k]
    hit_sections = {str(h.get("section")) for h in top_k}
    expected_sections = {_ref_section(r) for r in expected_references}
    if not expected_sections:
        return 0.0
    return len(expected_sections & hit_sections) / len(expected_sections)


def _ref_section(ref: str) -> str:
    """expected_references "ai-tutoring/04-安全与防作弊" → 节号 "04"。"""
    part = ref.split("/")[-1] if "/" in ref else ref
    return part.split("-")[0].strip()


# ============ 3.3 LLM 判分 ============


_JUDGE_SYSTEM = """你是 RAG 检索质量评审。给定"面试问题 + 检索到的语料块 + 生成答案 + 预期要点"，给答案质量打分。

评分规则(0~5 整数, 按以下锚定):
- 5: 答案覆盖全部预期要点(允许同义表述), 且全部基于语料, 无编造
- 4: 覆盖大部分要点, 无编造
- 3: 覆盖部分要点, 或有一处编造
- 2: 覆盖少部分要点, 或有明显编造
- 1: 基本未覆盖要点
- 0: 答案严重偏离语料 / 编造主导 / 空答案

判定要点:
- 预期要点**以同义表述覆盖即算覆盖**——不要求字面出现。例如要点"ScoreMapper 累计"被"题型掌握度累计/按题型聚合"表述覆盖即计覆盖
- 判断"编造"时以**检索到的语料块**为准: 答案的表述只要在语料块中有支撑, 就不算编造; 只有语料块完全没提到才算编造
- 答案引用了语料块、且表述有支撑 → 引用正确

严格输出 JSON: {"score": 0~5 整数, "rationale": "一句话理由(要点覆盖+是否有编造)"}。不要任何其他文字。"""


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
            text = llm.invoke([
                SystemMessage(content=_JUDGE_SYSTEM),
                HumanMessage(content=prompt),
            ]).content or ""
            data = _extract_json(text)
            score = int(data.get("score"))
            if 0 <= score <= 5:
                return {"score": score, "rationale": str(data.get("rationale", "")), "judged": True}
            logger.warning("判分 score 越界(%s), 重试", score)
        except Exception as e:
            logger.warning("判分解析失败(尝试%d): %s", attempt + 1, e)
    return {"score": 0, "rationale": "判分解析失败", "judged": False}


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


def run_eval_case(case: dict, top_k: int = rag_core.TOP_K) -> dict:
    """单条评测: 检索 → hit@k → 生成 → 判分 → trace。

    case: 评测集一条(module/question/question_type/expected_references/expected_points)
    返回 trace dict(5.1 落盘结构):
      {question, question_type, intent, recall[], hit, hit_score,
       answer, references[], usage, latency_ms, score, rationale, judged}
    """
    question = case["question"]
    t0 = time.time()

    # 检索(真实原语, 不降级)
    blocks = rag_core._load_blocks()
    strategy = rag_core.classify(question)
    vec = rag_core.retrieve_vector(question)
    bm = rag_core.retrieve_bm25(question, blocks)
    hits = rag_core.orchestrate(question, blocks, vec, bm, strategy, top_k=top_k)

    recall = [
        {"key": h["key"], "score": h["score"], "authority": h["authority"],
         "section": h["section"], "file": h["file"], "anchor": h["anchor"]}
        for h in hits
    ]
    t_recall = time.time()

    # hit@k
    hit = hit_at_k(recall, case["expected_references"], k=HIT_K)

    # 生成 + 判分(判分带语料块, 供"编造"判定——答案在语料有支撑即非编造)
    answer = ""
    score, rationale, judged = 0, "", False
    if hits:
        answer = rag_core.generate(hits, question)
        judge = judge_quality(question, answer, case["expected_points"],
                              corpus_texts=[h["text"] for h in hits])
        score, rationale, judged = judge["score"], judge["rationale"], judge["judged"]
    t_done = time.time()

    return {
        "question": question,
        "question_type": case["question_type"],
        "intent": strategy,
        "recall": recall,
        "hit": bool(hit > 0),
        "hit_score": hit,
        "answer": answer,
        "references": [{"file": h["file"], "file_path": h.get("file_path", ""),
                        "anchor": h["anchor"], "authority": h["authority"],
                        "summary": h.get("summary", "")} for h in hits],
        "score": score,
        "rationale": rationale,
        "judged": judged,
        "latency_ms": {
            "retrieve_ms": round((t_recall - t0) * 1000),
            "generate_ms": round((t_done - t_recall) * 1000),
            "total_ms": round((t_done - t0) * 1000),
        },
        "version": rag_core._current_version(blocks),
    }


# ============ 3.4 聚合 ============


def aggregate(results: List[dict]) -> dict:
    """按模块(本期单模块 ai-tutoring)聚合指标。

    {count, hit_at_k_avg, quality_avg, judged_ratio, total_latency_ms, ...}
    """
    n = len(results)
    if n == 0:
        return {"count": 0, "hit_at_k_avg": 0.0, "quality_avg": 0.0,
                "judged_ratio": 0.0, "avg_latency_ms": 0.0}
    hit_avg = sum(r["hit_score"] for r in results) / n
    quality_avg = sum(r["score"] for r in results) / n
    judged = sum(1 for r in results if r["judged"])
    latency = [r["latency_ms"]["total_ms"] for r in results]
    return {
        "count": n,
        "hit_at_k_avg": round(hit_avg, 3),
        "quality_avg": round(quality_avg, 3),
        "judged_ratio": round(judged / n, 3),
        "avg_latency_ms": round(sum(latency) / n),
        "hit_cases": sum(1 for r in results if r["hit"]),
        "unjudged": n - judged,
    }
