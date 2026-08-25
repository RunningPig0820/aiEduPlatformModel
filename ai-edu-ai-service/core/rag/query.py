"""
1.6 检索编排核心 - 按 1.6B 接口纪律分层

架构(1.6B):
  意图钩子   intent(question, history) → {anchor, category, switch_detected, ambiguous, candidates, locked_sections, degraded}
              classify(question)         → {locked_sections, strategy}  # 兼容层, 委托 intent
  召回单元   retrieve_vector(question) → {hits, confidence}   # 独立, 可单独熔断/跳过
  召回单元   retrieve_bm25(question)   → {hits, confidence}   # 独立
  编排器     orchestrate(...) → RRF × authority × 锚定 → top-K
  text 反查  text_by_key(key) → 从 jsonl 反查全文(metadata 不含 text, 20KB 限制)
  生成       generate(hits, question) → doubao 答案(面试口述 + 引用)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6B + 1.6C
      openspec/changes/rag-project-intro-assistant-python (A1 intent 结构化)
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

# 模块锚点闭集(模块级路由, 决定从哪个语料池召回; A1 结构化输出必填 anchor)
# 对齐后端 guardrails spec 四模块: AI答疑 / 知识图谱 / 题型分析 / RAG项目
# 三端定稿(2026-08-25): rag-system(弃 rag-project) / question-analysis(弃 question-type)
MODULE_ANCHORS = ("ai-tutoring", "knowledge-graph", "question-analysis", "rag-system")

# 模块级关键词兜底(LLM 意图失败时, 问题关键词 → 模块锚点; 与 ANCHOR_RULES 的节级锚定两层并存)
MODULE_ANCHOR_RULES = [
    (("答疑", "ai答疑", "教学", "学生", "题目", "解答", "启发"), "ai-tutoring"),
    (("rag", "检索", "召回", "重排", "向量", "bm25", "rrf", "多路", "知识库"), "rag-system"),
    (("知识图谱", "图谱", "neo4j", "知识点", "概念", "关系", "节点"), "knowledge-graph"),
    (("题型", "考点", "题型分析", "聚集"), "question-analysis"),
]

# history 截断窗口(联调⑦): Java 传入最近 N 轮, Python 只消费最近 N 轮(含 clarify 轮)
HISTORY_LIMIT = 3

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


def _fallback_module(question: str) -> str:
    """模块级关键词兜底 → 模块锚点 id; 未命中 → ""(调用方取默认 current_project)。

    与 _fallback_anchor(节级) 两层并存: 模块决定语料池, 节级池内加权。
    """
    q = question.lower()
    for kws, mod in MODULE_ANCHOR_RULES:
        if any(k in q for k in kws):
            return mod
    return ""


# 结构化意图 LLM 提示: 输出闭集 JSON, 供 intent 解析(A1)
_INTENT_SYSTEM = """你是「AI答疑」RAG 助手的意图识别器。只输出 JSON，不输出解释。

输入：学生问题 + 最近会话历史（每轮带锚定模块）。判断问题属于哪个模块、是否需要澄清/切换。

输出 JSON（必须合法 JSON，闭集枚举）：
{
  "anchor": "ai-tutoring",            // 模块锚点, 闭集: ai-tutoring|knowledge-graph|question-analysis|rag-system
  "category": "项目介绍",             // 类别闭集: 项目介绍|操作|难点|数据关联|最危险|其他
  "switch_detected": false,           // 是否从历史锚点切换到新模块
  "ambiguous": false,                 // 问题指向多个模块、需澄清
  "candidates": []                    // ambiguous=true 时给 2~4 个候选模块闭集
}

判断规则：
- anchor：问题语义指向哪个模块（AI答疑=ai-tutoring / RAG项目=rag-system / 知识图谱=knowledge-graph / 题型分析=question-analysis）
- 项目介绍/操作/难点/数据关联/最危险 → AI答疑模块内类别；问系统架构/代码/部署/评测 → RAG 项目模块(rag-system)
- switch_detected：本问题明显不再谈历史锚点模块、转向另一模块 → true
- ambiguous：问题含"这个/那个/它"指代不清、可指向多个模块 → true，并给 candidates（模块闭集内，≥2 个）
只输出 JSON 本身。"""


def _sanitize_intent(raw: dict, question: str) -> dict:
    """schema 校验(A1): anchor 必填模块 id、candidates 闭集去重、switch/ambiguous 强制布尔。

    anchor 非闭集/缺失 → 关键词兜底; candidates 只保留闭集内并去重。返回合法 intent 字典。
    """
    anchor = raw.get("anchor", "") if isinstance(raw, dict) else ""
    if anchor not in MODULE_ANCHORS:
        anchor = _fallback_module(question)
    candidates = []
    if isinstance(raw, dict):
        for c in raw.get("candidates", []) or []:
            if c in MODULE_ANCHORS and c not in candidates:
                candidates.append(c)
    return {
        "anchor": anchor,
        "category": raw.get("category", "") if isinstance(raw, dict) else "",
        "switch_detected": bool(raw.get("switch_detected", False)) if isinstance(raw, dict) else False,
        "ambiguous": bool(raw.get("ambiguous", False)) if isinstance(raw, dict) else False,
        "candidates": candidates,
    }


def _truncate_history(history: list | None) -> list:
    """history 显式截断到最近 N 轮(联调⑦): history[-HISTORY_LIMIT:], 含 clarify 轮。

    Java 网关传入最近 N 轮 {question, answer, anchor}, Python 只消费不落会话态。
    """
    if not history:
        return []
    return list(history)[-HISTORY_LIMIT:]


def _llm_intent(question: str, history: list) -> dict:
    """LLM 结构化意图 → 合法 intent 字典; 失败/非闭集/非法 JSON → {}(调用方回退关键词)。

    复用 _llm_category 的 doubao 连接模式: mini 关思考(秒出) + 0 温度 + 20s 超时 + 关重试。
    历史只作上下文提示, 截断在 _truncate_history 已做。
    """
    try:
        llm = LLMFactory.create(
            "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.0,
            extra_body={"thinking": {"type": "disabled"}},
            request_timeout=20, max_retries=0,
        )
        hist_lines = "\n".join(
            f"Q{h}: {h.get('question', '')} (anchor={h.get('anchor', '')})"
            for h in history
        ) or "（无）"
        text = llm.invoke([
            SystemMessage(content=_INTENT_SYSTEM),
            HumanMessage(content=f"学生问题：{question}\n\n最近会话：\n{hist_lines}\n\n请输出 JSON。"),
        ]).content or ""
        raw = _extract_json(text)
        if not raw:
            return {}
        return _sanitize_intent(raw, question)
    except Exception as e:
        logger.warning("RAG intent LLM 失败, 回退关键词锚定: %s", e)
        return {}


def _extract_json(text: str) -> dict | None:
    """从 LLM 文本提取 JSON 对象(容忍前后缀/``` 围栏); 无合法 JSON → None。"""
    import re
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def intent(question: str, history: list | None = None,
           current_project: str = "ai-tutoring") -> dict:
    """问题 + 会话 → 完整意图 {anchor, category, switch_detected, ambiguous, candidates,
    locked_sections, degraded}。

    A1 升级 classify: LLM 结构化输出(anchor 模块路由 + category 类别), 失败/非闭集 → 关键词兜底
    (模块 _fallback_module + 节 _fallback_anchor 两层), degraded 标记走 200。
    history 显式截断最近 N 轮(Java 传入只消费, 联调⑦)。
    """
    history = _truncate_history(history)
    raw = _llm_intent(question, history)
    degraded = not raw or not raw.get("anchor")

    if raw and raw.get("anchor"):
        anchor = raw["anchor"]
        category = raw["category"]
        if category in CATEGORY_SECTIONS:
            locked = list(CATEGORY_SECTIONS[category])
        else:
            locked = sorted(_fallback_anchor(question))  # 类别非闭集 → 节级关键词兜底
    else:
        anchor = _fallback_module(question) or current_project  # 模块兜底, 缺省当前项目
        category = ""
        locked = sorted(_fallback_anchor(question))

    return {
        "anchor": anchor,
        "category": category,
        "switch_detected": bool(raw.get("switch_detected")) if raw else False,
        "ambiguous": bool(raw.get("ambiguous")) if raw else False,
        "candidates": list(raw.get("candidates", [])) if raw else [],
        "locked_sections": locked,
        "degraded": degraded,
    }


def classify(question: str) -> dict:
    """问题 → 锁策略{locked_sections, strategy}（既有契约, 保持原实现不动）。

    1.6B 意图钩子: 优先 LLM 语义判断意图类别(闭集映射锁节), 失败/非闭集 → 回退关键词查表。
    白盒链路用 intent(完整结构化, A1); 既有 /api/tutoring/rag/query 用 classify 保持契约不变。
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


# ============ rewrite 改写 (A2) ============


_REWRITE_SYSTEM = """你是「AI答疑」RAG 助手的查询改写器。把学生口语化提问改写成适合检索的关键词查询。

只输出改写后的查询文本，不要解释、不要加引号、不要输出 JSON。

规则：
1. 保留核心实体词（模块名/功能名/技术术语），去掉口语填充（那个/这个/我想问/你知道/咱们）
2. 指代（它/这个/那套系统）结合最近会话补全成明确名词
3. 保持原问题语义，不扩写、不答内容，5~20 字内
4. 问题本身已明确（无口语、无指代）→ 原样输出
"""


def rewrite_query(question: str, anchor: str, history: list | None = None) -> str:
    """口语提问 → 检索式改写（LLM 短调用）; 失败/空 → 原问题兜底。

    anchor 提供模块上下文（改写提示约束语义方向）; history 显式截断最近 N 轮(联调⑦)。
    复用 intent 的 doubao 连接模式: mini 关思考 + 0 温度 + 20s 超时 + 关重试。
    """
    history = _truncate_history(history)
    try:
        llm = LLMFactory.create(
            "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.0,
            extra_body={"thinking": {"type": "disabled"}},
            request_timeout=20, max_retries=0,
        )
        hist_lines = "\n".join(
            f"Q{h.get('question', '')} (anchor={h.get('anchor', '')})"
            for h in history
        ) or "（无）"
        prompt = (f"模块锚点：{anchor}\n学生问题：{question}\n"
                  f"最近会话：\n{hist_lines}\n\n请输出改写后的查询：")
        text = (llm.invoke([
            SystemMessage(content=_REWRITE_SYSTEM),
            HumanMessage(content=prompt),
        ]).content or "").strip()
        return text if text else question
    except Exception as e:
        logger.warning("RAG rewrite LLM 失败, 回退原问题: %s", e)
        return question


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


def select_corpus(blocks: list, anchor: str | None) -> list:
    """C2 选池: 按模块 anchor 过滤语料池(决定从哪个模块池召回)。

    anchor 明确(闭集内) → 只留该模块块; 空/非闭集 → 全池(维持现状, 向后兼容)。
    该模块无语料 → 返回空池 → 编排层自然走范围门低置信过滤(C1 定稿: 无语料模块拒答正确)。
    """
    if not anchor or anchor not in MODULE_ANCHORS:
        return blocks
    return [b for b in blocks if b["tags"].get("module") == anchor]


def orchestrate(question: str, blocks: list, vec_result: dict, bm25_result: dict,
                strategy: dict, top_k: int = TOP_K, corpus: str | None = None) -> list:
    """编排器: RRF 融合 × authority 权威度 × 页面锚定加权 → top-K 完整命中。

    corpus(可选, A3/C2): 模块 anchor, 给定时先按 module 过滤语料池再融合; None → 全池
    (向后兼容, /api/tutoring/rag/query 不传)。锚定公式原样: 节级 locked_sections 池内加权。
    top_k 命中项含: key/metadata/authority/source/section/file/file_path/anchor/summary/text。
    """
    pool = select_corpus(blocks, corpus) if corpus else blocks
    keymap = _assign_idx(pool)

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
