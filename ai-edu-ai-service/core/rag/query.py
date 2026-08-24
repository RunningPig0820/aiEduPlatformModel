"""
1.6 检索编排核心 - 按 1.6B 接口纪律分层

架构(1.6B):
  意图钩子   classify(question) → {locked_sections, strategy}
  召回单元   retrieve_vector(question) → {hits, confidence}   # 独立, 可单独熔断/跳过
  召回单元   retrieve_bm25(question)   → {hits, confidence}   # 独立
  编排器     orchestrate(...) → RRF × authority × 锚定 → top-K
  text 反查  text_by_key(key) → 从 jsonl 反查全文(metadata 不含 text, 20KB 限制)
  生成       generate(hits, question) → doubao 答案(面试口述 + 引用)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6B + 1.6C
环境: 用 ai-edu-ai-service/venv 运行(conda 默认环境 langchain 版本冲突, 见 CLAUDE.md)
"""
import json
import math
import os

import jieba
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from core.gateway.factory import LLMFactory
from core.tutoring.vector_store import query_vector

logger = __import__("logging").getLogger(__name__)

# 语料 jsonl 副本(1.6 调整: 向量桶 role mode 不收普通对象, 留本地)
DATA = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag", "data", "rag_slices.jsonl")

# 检索参数
RRF_K = 60          # RRF 融合常数
TOP_K = 6           # 生成用块数
BM25_K = 10         # BM25 召回数
VEC_K = 12          # 向量召回数
MAX_GEN_TEXT = 1200 # 生成时单块 text 截断(上下文长度保护)

# 页面锚定: 问题关键词 → 锁定完善文档节。命中节加权 1.5, 其余 1.0。
# 1.6B: 这是最朴素意图分类器——未来换 LLM 判断意图类别, 接口不变(数据驱动, 每模块一份)。
ANCHOR_RULES = [
    # 项目介绍 → 01/03
    (("项目", "介绍", "架构", "模块", "微服务", "分工", "区别", "定位", "整体", "做什么", "是什么"), ("01", "03")),
    # 操作 → 02/06: 领域名词锚定, 不用万能疑问词(怎么/如何会稀释所有类)
    (("流程", "步骤", "操作", "图片", "OCR", "一次", "完整", "图片题", "走"), ("02", "06")),
    # 难点 → 04/07
    (("防", "套答案", "作弊", "安全", "护栏", "幻觉", "流式", "性能", "慢", "卡", "延迟"), ("04", "07")),
    # 数据关联 → 05
    (("数据", "掌握度", "落库", "关联", "存储", "统计", "图谱", "知识点", "点亮", "选错", "联动"), ("05",)),
    # 最危险/防御 → 08
    (("题库", "没问", "答错", "乱给", "兜底", "待入库", "防御"), ("08",)),
]
ANCHOR_WEIGHT = 1.5

_STOP = set("的了是在和与就都以及呢吗啊呀吧么这那我有你要他她它们一个不也没很为对从到往")


# ============ 意图钩子 (1.6B) ============


# 意图类别 → 锁节映射(与 ANCHOR_RULES 一致的页面锚定目标; 供 LLM 意图识别用)
CATEGORY_SECTIONS = {
    "项目介绍": ("01", "03"),
    "操作": ("02", "06"),
    "难点": ("04", "07"),
    "数据关联": ("05",),
    "最危险": ("08",),
    "其他": (),
}

_CLASSIFY_SYSTEM = """你是「AI答疑」项目的意图分类器。只判断面试官在问哪类问题，不回答内容。

只能输出一个类别（闭集）：项目介绍 / 操作 / 难点 / 数据关联 / 最危险 / 其他。

判断规则（看问题的语义重点，不是看字面词）：
- 项目介绍：问项目定位、架构、模块分工、和别的东西的区别
- 操作：问流程怎么走、步骤、图片题处理、OCR
- 难点：问防作弊、防套答案、安全护栏、流式性能、卡顿
- 数据关联：问掌握度、落库、存储、知识图谱联动、知识点点亮
- 最危险：问没有题库怎么办、模型答错、学生没问这题、防御性问题
- 其他：以上都不属于（天气、闲聊、无关话题）

只输出类别名，不要解释、不要多余文字。"""

# 失败/非闭集 → 回退关键词查表(1.6B: 意图钩子换 LLM, 接口不变, 降级保底)
def _fallback_anchor(question: str) -> set:
    locked = set()
    for kws, secs in ANCHOR_RULES:
        if any(k in question for k in kws):
            locked.update(secs)
    return locked


def classify(question: str) -> dict:
    """问题 → 锁策略{locked_sections, strategy}。

    1.6B 意图钩子: 优先 LLM 语义判断意图类别(闭集映射锁节), 失败/非闭集 → 回退关键词查表。
    接口不变(返回结构固定), 检索/生成只消费结果, 不关心实现。
    """
    category = _llm_category(question)
    if category in CATEGORY_SECTIONS:
        return {"locked_sections": list(CATEGORY_SECTIONS[category]), "strategy": "retrieve"}
    return {"locked_sections": sorted(_fallback_anchor(question)), "strategy": "retrieve"}


def _llm_category(question: str) -> str:
    """LLM 判意图类别 → 闭集之一; 失败/超时/非闭集 → ""(调用方回退关键词)。

    复用 subject_classify 模式: doubao mini 关思考(秒出, 不卡 RAG 查询) + 20s 超时 + 关重试。
    """
    try:
        llm = LLMFactory.create(
            "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.0,
            extra_body={"thinking": {"type": "disabled"}},
            request_timeout=20, max_retries=0,
        )
        text = llm.invoke([
            SystemMessage(content=_CLASSIFY_SYSTEM),
            HumanMessage(content=f"面试官问题：{question}\n\n请判断属于哪个类别（只输出类别名）。"),
        ]).content or ""
        for cat in CATEGORY_SECTIONS:
            if cat in text.strip():
                return cat
        return ""
    except Exception as e:
        logger.warning("RAG 意图分类 LLM 失败, 回退关键词锚定: %s", e)
        return ""


# ============ 语料加载 + text 反查 ============


def _load_blocks() -> list:
    with open(DATA, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ============ 召回单元 (1.6B, 独立) ============


def retrieve_vector(question: str) -> dict:
    """向量召回单元: COS query_vectors(rag 桶) → hits + confidence。

    独立单元契约: 入参 question, 出参 {hits, confidence}; 异常由编排器捕获(未来熔断/降级)。
    """
    hits = query_vector(question, top_k=VEC_K, vector_type="rag")
    # confidence = 平均相似度(1 - 平均余弦距离); COS distance 越小越相似
    conf = 0.0
    if hits:
        conf = 1.0 - sum(h.get("distance", 1.0) for h in hits) / len(hits)
    return {"hits": hits, "confidence": max(0.0, conf)}


def _tokenize(text: str) -> list:
    return [w for w in jieba.lcut(text) if w.strip() and w not in _STOP and len(w) > 1]


class BM25:
    """Okapi BM25 - 本地 jsonl 全文打分(不依赖向量, 断电/断网仍可用)。"""

    def __init__(self, corpus: list):
        self.k1, self.b = 1.5, 0.75
        self.N = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / self.N if self.N else 0
        self.corpus = corpus
        self.df = {}
        for d in corpus:
            for w in set(d):
                self.df[w] = self.df.get(w, 0) + 1

    def score(self, q_tokens: list, i: int) -> float:
        d = self.corpus[i]
        dl = len(d)
        if dl == 0:
            return 0.0
        tf = {}
        for w in d:
            tf[w] = tf.get(w, 0) + 1
        s = 0.0
        for w in set(q_tokens):
            f = tf.get(w, 0)
            if f == 0:
                continue
            df = self.df.get(w, 1)
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s


def retrieve_bm25(question: str, blocks: list) -> dict:
    """BM25 召回单元: jieba 分词 + 本地 jsonl 全文打分 → hits + confidence。

    独立单元契约同 retrieve_vector; 纯本地, 无外部依赖。
    """
    corpus = [_tokenize(b["summary"] + "\n" + b["text"]) for b in blocks]
    bm = BM25(corpus)
    q_tokens = _tokenize(question)
    scores = [bm.score(q_tokens, i) for i in range(len(blocks))]
    ranked = sorted(range(len(blocks)), key=lambda i: -scores[i])[:BM25_K]
    hits = [{"key": _key_of(blocks[i]), "metadata": blocks[i]["tags"], "bm25_score": scores[i]}
            for i in ranked if scores[i] > 0]
    conf = min(1.0, (scores[ranked[0]] / 10.0)) if ranked and scores[ranked[0]] > 0 else 0.0
    return {"hits": hits, "confidence": conf}


# ============ 编排器 (1.6B) ============


def _key_of(b: dict) -> str:
    """块 → 向量 key(与 build_index 同规则: 同 file+anchor 组内序号)"""
    t = b["tags"]
    return f"ai-tutoring/{t['file']}/{t['anchor']}#{t.get('_idx', 0)}"


def _assign_idx(blocks: list) -> dict:
    """为块补 _idx(同 file+anchor 组内序号), 返回 key→block 映射"""
    counters = {}
    keymap = {}
    for b in blocks:
        t = b["tags"]
        group = (t["file"], t["anchor"])
        idx = counters.get(group, 0)
        counters[group] = idx + 1
        t["_idx"] = idx
        keymap[_key_of(b)] = b
    return keymap


def orchestrate(question: str, blocks: list, vec_result: dict, bm25_result: dict,
                strategy: dict, top_k: int = TOP_K) -> list:
    """编排器: RRF 融合 × authority 权威度 × 页面锚定加权 → top-K 完整命中。

    top_k 命中项含: key/metadata/authority/source/section/file/file_path/anchor/summary/text。
    """
    keymap = _assign_idx(blocks)

    # 两路 rank: 向量路(COS 返回 key) / BM25 路
    vec_keys = [h["key"] for h in vec_result["hits"]]
    bm_keys = [h["key"] for h in bm25_result["hits"]]

    vec_rank = {k: r for r, k in enumerate(vec_keys)}
    bm_rank = {k: r for r, k in enumerate(bm_keys)}
    locked = set(strategy.get("locked_sections", []))

    scored = []
    for key in set(vec_rank) | set(bm_rank):
        rrf = 0.0
        if key in vec_rank:
            rrf += 1.0 / (RRF_K + vec_rank[key])
        if key in bm_rank:
            rrf += 1.0 / (RRF_K + bm_rank[key])
        block = keymap.get(key)
        if block is None:
            continue
        t = block["tags"]
        authority = t.get("authority", 0.7)
        anchor_w = ANCHOR_WEIGHT if t.get("section") in locked else 1.0
        scored.append((rrf * authority * anchor_w, rrf, authority, key))

    scored.sort(key=lambda x: -x[0])
    hits = []
    for final, rrf, authority, key in scored[:top_k]:
        block = keymap[key]
        t = block["tags"]
        hits.append({
            "key": key,
            "score": round(final, 4),
            "authority": authority,
            "source": t.get("source"),
            "section": t.get("section"),
            "file": t.get("file"),
            "file_path": t.get("file_path", ""),
            "anchor": t.get("anchor"),
            "summary": block.get("summary", ""),
            "text": block.get("text", ""),
        })
    return hits


# ============ 生成 (1.6B) ============


_GEN_SYSTEM = """你是「AI答疑」项目的介绍人，正在接受面试官面试。下面给出检索到的项目语料块（按相关度排序，每块带来源/权威度/锚点）。回答要求：
1. 只依据语料内容回答，语料没覆盖的不编造、不硬答
2. 面试口述风格：先给结论，再分层展开，能接住追问
3. 引用的要点在回答后注明出处（格式：〔来源/文件/锚点〕）
4. 保持简洁，不要输出思考过程"""


def _make_llm():
    return LLMFactory.create(
        "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}},
        request_timeout=60, max_retries=1,
    )


def generate(hits: list, question: str, return_usage: bool = False):
    """doubao 生成答案(面试口述风格 + 引用)。hits 为 orchestrate 输出。

    return_usage=True 时返回 (text, usage_dict)，评测/cost 统计用；默认返回 str(API 轻量)。
    """
    ctx = []
    for h in hits:
        head = f"〔{h['source']}/{h['file']}/{h['anchor']}｜权威{h['authority']}〕"
        ctx.append(f"{head}\n{h['text'][:MAX_GEN_TEXT]}")
    prompt = f"面试官问题：{question}\n\n--- 检索到的语料块 ---\n\n" + "\n\n".join(ctx)
    llm = _make_llm()
    resp = llm.invoke([
        SystemMessage(content=_GEN_SYSTEM),
        HumanMessage(content=prompt),
    ])
    if return_usage:
        usage = getattr(resp, "usage_metadata", None) or {}
        return resp.content, {
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
    return resp.content


# ============ 顶层编排 (1.6C 契约来源) ============


def rag_query(question: str, top_k: int = TOP_K) -> dict:
    """完整问答: 意图 → 双路召回 → 编排 → 生成。

    返回 1.6C 契约结构: {answer, references, intent, version}(API 端点/CLI 共用)。
    """
    blocks = _load_blocks()
    strategy = classify(question)
    vec = retrieve_vector(question)
    bm = retrieve_bm25(question, blocks)
    hits = orchestrate(question, blocks, vec, bm, strategy, top_k=top_k)

    references = [
        {k: h[k] for k in ("file", "file_path", "anchor", "authority", "summary")}
        for h in hits
    ]
    return {
        "answer": generate(hits, question),
        "references": references,
        "intent": strategy,
        "version": _current_version(blocks),
    }


def _current_version(blocks: list) -> str:
    """当前语料 version(build 同规则: 全块 text sha1[:6], 用于标注数据时效)。"""
    import hashlib
    import time
    raw = "".join(b["text"] for b in blocks).encode("utf-8")
    sha = hashlib.sha1(raw).hexdigest()[:6]
    return f"{time.strftime('%Y-%m-%d')}-{sha}"
