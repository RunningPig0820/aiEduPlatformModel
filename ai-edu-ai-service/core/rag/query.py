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
# 双池(1.13): rag_slices.jsonl = 切片池(294 块), rag_slices_full.jsonl = 全量池(23 块整篇)
DATA = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag", "data", "rag_slices.jsonl")
DATA_FULL = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag", "data", "rag_slices_full.jsonl")

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
# 1.13 Q5: 类别匹配提权——意图锁定 locked_categories 时, 切片池命中该类别的块加权
# (补强"排除式过滤"不足: 仅过滤时全量池权威 1.0 会压过坑档案 0.8, 提权让具体坑块浮上来)。
CATEGORY_WEIGHT = 1.5

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

# 9 类切片闭集(切片数据/ 每块 category 标签; intent LLM 输出 categories 供切片池过滤)。
# 1.13.2 定稿: 无 6→9 映射兜底——LLM 未给 categories 字段 → 全局查询不筛(兜底不一定比全查询好)。
SLICE_CATEGORIES = ("项目介绍", "操作流程", "数据关联", "开发难点", "业务流程",
                    "架构设计", "业务视角", "数据存储", "未来演进")

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
_INTENT_SYSTEM = """你是「AI答疑」RAG助手的意图识别器。**只输出合法JSON，禁止任何解释、markdown、额外文字。**

# 输入
输入包含两部分：
1. 当前用户问题
2. 最近会话历史：每轮携带已识别的anchor模块；取**上一轮的最终anchor作为历史基准锚点**；会话历史为空则无历史锚点。

# 输出字段 & 闭集枚举（只允许下面列出的值，禁止生成其他值）
{
  "anchor": "ai-tutoring",
  "category": "项目介绍",
  "categories": ["项目介绍"],
  "switch_detected": false,
  "ambiguous": false,
  "candidates": []
}

1. anchor（模块锚点，单选）
可选枚举：ai-tutoring | knowledge-graph | question-analysis | rag-system
- ai-tutoring：AI答疑业务产品、学生答疑业务逻辑、业务使用场景
- rag-system：底层RAG实现、代码、向量库、召回排序算法、部署、系统架构、评测
- knowledge-graph：知识图谱相关
- question-analysis：题型分析、题目解析业务

> 优先级规则：同一个问题同时涉及业务产品与底层RAG实现，看用户提问重心：问业务效果/业务流程选 ai-tutoring；问工程实现、底层技术选 rag-system。

2. category（文档页路由，单选，页面跳转使用）
枚举：项目介绍 | 操作 | 难点 | 数据关联 | 最危险 | 其他
示例：为什么做/定位/是什么 → 项目介绍；怎么走/步骤/流程 → 操作；防作弊/安全/护栏/性能卡/踩坑 → 难点；掌握度/落库/知识点 → 数据关联；没题库/答错/兜底 → 最危险

3. categories（切片池过滤标签，数组，可空数组代表不做过滤，允许多选）
枚举：项目介绍 | 操作流程 | 数据关联 | 开发难点 | 业务流程 | 架构设计 | 业务视角 | 数据存储 | 未来演进
示例：遇到哪些坑/怎么防/性能卡 → ["开发难点"]；为什么做/是什么 → ["项目介绍"]；架构分工/微服务 → ["架构设计"]；怎么存/落库 → ["数据存储"]

4. switch_detected：布尔值
- true：存在历史基准锚点，当前问题语义明确切换到另一个不同anchor模块
- false：无历史锚点 / 仍然是同一个anchor模块（哪怕category/categories变化，不算切换）

5. ambiguous：布尔值，是否问题需要澄清
- true：代词（这个/那个/它）结合历史上下文仍无法确定指代；或者问题语义天然同时指向≥2个模块；此时candidates必须填充2-4个anchor候选。
- false：指代可被上下文还原，问题语义归属单一模块；此时candidates必须为空数组。

# 兜底规则
1. 输入问题语义无法识别：anchor按重心就近选择，category="其他"，categories=[]，ambiguous=false。
2. ambiguous=false 时 candidates 必须是[]；ambiguous=true时candidates不能为空。
3. 所有字段严格使用给定枚举，禁止自定义值。
只输出 JSON 本身。"""


def _sanitize_intent(raw: dict, question: str) -> dict:
    """schema 校验(A1): anchor 必填模块 id、candidates 闭集去重、switch/ambiguous 强制布尔。

    anchor 非闭集/缺失 → 关键词兜底; candidates 只保留闭集内并去重。返回合法 intent 字典。
    """
    anchor = raw.get("anchor", "") if isinstance(raw, dict) else ""
    if anchor not in MODULE_ANCHORS:
        anchor = _fallback_module(question)
    candidates = []
    categories = []
    if isinstance(raw, dict):
        for c in raw.get("candidates", []) or []:
            if c in MODULE_ANCHORS and c not in candidates:
                candidates.append(c)
        for c in raw.get("categories", []) or []:   # 1.13 多模块: 9 类切片闭集校验
            if c in SLICE_CATEGORIES and c not in categories:
                categories.append(c)
    return {
        "anchor": anchor,
        "category": raw.get("category", "") if isinstance(raw, dict) else "",
        "categories": categories,
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


def _llm_intent(question: str, history: list, current_project: str = "ai-tutoring") -> dict:
    """LLM 结构化意图 → 合法 intent 字典; 失败/非闭集/非法 JSON → {}(调用方回退关键词)。

    复用 _llm_category 的 doubao 连接模式: mini 关思考(秒出) + 0 温度 + 20s 超时 + 关重试。
    历史只作上下文提示, 截断在 _truncate_history 已做。
    current_project(1.13.2): 当前上下文模块, 作为 LLM 倾向约束(除非问题明确属其他模块, 否则保持)。
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
        ctx_line = (f"当前上下文模块：{current_project}（除非问题明确属于其他模块, "
                    f"否则 anchor 保持该模块）")
        text = llm.invoke([
            SystemMessage(content=_INTENT_SYSTEM),
            HumanMessage(content=f"学生问题：{question}\n{ctx_line}\n最近会话：\n{hist_lines}\n\n请输出 JSON。"),
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
    raw = _llm_intent(question, history, current_project)
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

    # 1.13.2 定稿: 切片池类别过滤只取 LLM 9 类 categories(空数组=不筛);
    # LLM 未给 categories 字段/给空 → 全局查询不筛(去掉 6→9 映射兜底)。
    if raw and "categories" in raw:
        locked_categories = [c for c in (raw["categories"] or []) if c in SLICE_CATEGORIES]
    else:
        locked_categories = []

    return {
        "anchor": anchor,
        "category": category,
        "switch_detected": bool(raw.get("switch_detected")) if raw else False,
        "ambiguous": bool(raw.get("ambiguous")) if raw else False,
        "candidates": list(raw.get("candidates", [])) if raw else [],
        "locked_sections": locked,
        "locked_categories": locked_categories,
        "degraded": degraded,
    }


def classify(question: str) -> dict:
    """问题 → 锁策略{locked_sections, strategy}（既有契约, 保持原实现不动）。

    1.6B 意图钩子: 优先 LLM 语义判断意图类别(闭集映射锁节), 失败/非闭集 → 回退关键词查表。
    白盒链路用 intent(完整结构化, A1); 既有 /api/tutoring/rag/query 用 classify 保持契约不变。
    """
    category = _llm_category(question)
    if category in CATEGORY_SECTIONS:
        return {"locked_sections": list(CATEGORY_SECTIONS[category]), "strategy": "retrieve",
                "locked_categories": []}   # 1.13.2: classify 不做切片池类别过滤(全局查询)
    return {"locked_sections": sorted(_fallback_anchor(question)), "strategy": "retrieve",
            "locked_categories": []}


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


def _load_full_blocks() -> list:
    with open(DATA_FULL, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_all_blocks() -> list:
    """双池合并语料(切片池 + 全量池), BM25/keymap 用。池前缀在 _key_of 区分。"""
    return _load_blocks() + _load_full_blocks()


# ============ 召回单元 (1.6B, 独立) ============


DEFAULT_MODULE = "rag-system"        # 1.13: 未传 module 时的默认(项目介绍 RAG 上下文)
# 1.13.2: categories 不做默认——未给/空 → 全局查询不筛(去掉"默认架构设计")


def build_filter(module: str | None = None, categories: list | None = None) -> dict:
    """module/category → COS Filter($eq/$in + $and)。

    - module 恒筛(未传 → DEFAULT_MODULE rag-system); 单值 $eq
    - categories: None → 不筛类别(全量池用); 提供 list(含空=不筛) → 单值 $eq / 多值 $in
    - 两者都筛 → $and。实测: {"module":{"$eq":...}}, {"category":{"$in":[...]}},
      {"$and":[...]} 均被 COS 向量桶接受(2026-08-26)。
    """
    conds = [{"module": {"$eq": module or DEFAULT_MODULE}}]
    if categories:
        conds.append({"category": {"$eq": categories[0]}} if len(categories) == 1
                     else {"category": {"$in": categories}})
    return conds[0] if len(conds) == 1 else {"$and": conds}


def retrieve_vector(question: str, vector_type: str = "rag",
                    module: str | None = None, categories: list | None = None) -> dict:
    """向量召回单元: COS query_vectors(rag 桶, 带 module/category 条件筛选) → hits + confidence。

    独立单元契约: 入参 question + vector_type + module/categories(1.13 多模块, 向量层过滤,
    防其他模块/类别相似向量挤占 top-k), 出参 {hits, confidence}; 异常由编排器捕获。
    module 未传 → 默认 rag-system; categories 未传 → 不筛类别(调用方决定: 全量池不筛/切片池给默认)。
    """
    filt = build_filter(module, categories)
    hits = query_vector(question, top_k=VEC_K, vector_type=vector_type, filter_=filt)
    # confidence = 平均相似度(1 - 平均余弦距离); COS distance 越小越相似
    conf = 0.0
    if hits:
        conf = 1.0 - sum(h.get("distance", 1.0) for h in hits) / len(hits)
    return {"hits": hits, "confidence": max(0.0, conf)}


def retrieve_dual(question: str, corpus: str | None = None,
                  locked_categories: list | None = None) -> dict:
    """双池召回(1.13 Q3 + 多模块): 全量池向量 + 切片池向量 + BM25 → 三路供 RRF。

    向量层条件筛选(1.13 下推): 全量池只按 module; 切片池按 module + category。
    module 未传 → 默认 rag-system; 切片池 category 未传 → 默认架构设计。
    corpus(模块 anchor): 本地 BM25 只打该模块语料池(与编排层 select_corpus 一致)。
    locked_categories(9 类): 本地 BM25 只打切片池该类别的块(全量池块不过滤, 与编排层一致)。
    """
    full = retrieve_vector(question, vector_type="rag-full", module=corpus)   # 全量池: 只筛 module
    slice_ = retrieve_vector(question, vector_type="rag-slice", module=corpus,
                             categories=locked_categories)   # 切片池: module+category(空=全局查询)
    blocks = _load_all_blocks()
    pool = select_corpus(blocks, corpus) if corpus else blocks
    if locked_categories:
        cats = set(locked_categories)
        pool = [b for b in pool
                if b["tags"].get("pool") != "slice" or not b["tags"].get("category")
                or b["tags"]["category"] in cats]
    bm = retrieve_bm25(question, pool)
    return {"full": full, "slice": slice_, "bm25": bm}


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
    """块 → 向量 key(与 build_index 同规则: {池前缀}/{file}/{anchor}#{idx})。

    池前缀 = rag-{tags.pool}(rag-full/rag-slice), 与 COS 索引 key 对齐, 防两池 (file,anchor) 冲突。
    """
    t = b["tags"]
    pool = t.get("pool", "slice")
    return f"rag-{pool}/{t['file']}/{t['anchor']}#{t.get('_idx', 0)}"


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
                strategy: dict, top_k: int = TOP_K, corpus: str | None = None,
                vec2_result: dict | None = None) -> list:
    """编排器: RRF 融合 × authority 权威度 × 页面锚定加权 × 类别过滤 → top-K 完整命中。

    三路 RRF(1.13 Q4): vec_result(全量池向量) + vec2_result(切片池向量, 可选) + bm25_result。
    category 过滤(1.13 Q5): strategy.locked_categories 非空时, 只保留切片池命中该类别块
    (先 module 选池、再类别过滤两级; 全量池不过滤, 无类别锁定全保留)。
    corpus(可选, A3/C2): 模块 anchor, 给定时先按 module 过滤语料池再融合; None → 全池。
    top_k 命中项含: key/metadata/authority/source/section/file/file_path/anchor/summary/text。
    """
    pool = select_corpus(blocks, corpus) if corpus else blocks
    keymap = _assign_idx(pool)

    # 三路 rank: 全量向量(COS 返回 key) + 切片向量(可选) + BM25
    vec_keys = [h["key"] for h in vec_result["hits"]]
    vec2_keys = [h["key"] for h in vec2_result["hits"]] if vec2_result else []
    bm_keys = [h["key"] for h in bm25_result["hits"]]

    vec_rank = {k: r for r, k in enumerate(vec_keys)}
    vec2_rank = {k: r for r, k in enumerate(vec2_keys)}
    bm_rank = {k: r for r, k in enumerate(bm_keys)}
    locked = set(strategy.get("locked_sections", []))
    locked_cats = set(strategy.get("locked_categories", []) or [])

    scored = []
    for key in set(vec_rank) | set(vec2_rank) | set(bm_rank):
        rrf = 0.0
        if key in vec_rank:
            rrf += 1.0 / (RRF_K + vec_rank[key])
        if key in vec2_rank:
            rrf += 1.0 / (RRF_K + vec2_rank[key])
        if key in bm_rank:
            rrf += 1.0 / (RRF_K + bm_rank[key])
        block = keymap.get(key)
        if block is None:
            continue
        t = block["tags"]
        # 类别过滤: 只对切片池命中筛(全量池不过滤); 无锁定类别 → 全保留。
        # 无 category 的切片块不筛(防"空召回", 生产 294 块全有 category, 此处仅兜底)。
        if locked_cats and t.get("pool") == "slice" and t.get("category") \
                and t["category"] not in locked_cats:
            continue
        authority = t.get("authority", 0.7)
        anchor_w = ANCHOR_WEIGHT if t.get("section") in locked else 1.0
        # 类别提权: 意图锁定类别时, 切片池该类块加权(让具体坑块浮出, 压过全量池权威分)
        cat_w = CATEGORY_WEIGHT if locked_cats and t.get("pool") == "slice" \
            and t.get("category") in locked_cats else 1.0
        scored.append((rrf * authority * anchor_w * cat_w, rrf, authority, key))

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


_GEN_SYSTEM = """你是「AI答疑」项目的介绍人，正在接受面试官面试。下面给出检索到的项目语料块（按相关度排序，每块带来源/权威度/锚点）。

## 硬性约束
1. 只依据语料内容回答，语料没覆盖到的信息绝对不能编造、不要脑补扩展。
2. 禁止输出你的思考过程、推理草稿，只输出最终回答文本。
3. 输出格式：先简短抛出核心结论，再分层展开；适合口述面试，逻辑清晰，便于面试官追问。
4. 文档引用统一放到回答的最后一行集中展示，不在正文段落中间插入来源标记。格式示例：【参考来源：来源A/文件A/锚点A；来源B/文件B/锚点B】
5. 语料中出现的 ⚠️ ✅ 🚫 代码对账标记，**不作为主体回答内容**；仅当面试官明确问到落地现状、代码实现差异时，才引用对账信息。

## 问题分类输出规则（非常重要）
- 🔹当问题属于【为什么、动机、价值、解决什么问题、设计初衷】：
  优先提取：现实痛点、用户问题、业务收益、业务闭环价值。
  ❗禁止只复述模块定义（不要只说"AI答疑是一个XX模块"）；
  结构建议：先讲要解决哪些现实痛点，再讲产品核心理念，最后讲业务/系统闭环价值。

- 🔹当问题属于【怎么做、如何实现、架构、流程、技术方案、代码落地】：
  优先输出架构、链路、动作约束、护栏机制、落地实现细节；
  可以按需引用对账标记区分理想方案和真实代码现状。

- 🔹当问题属于【对比区别、差异】：
  采用对照式输出，把A和B放在同一维度对比，不要单方面罗列A的特性一笔带过B。

## 行文风格
语言精炼，技术面试口语化，避免大段摘抄原文；对文档内容做整合转述，不要直接复制大段原文。"""


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
    """完整问答: 意图(模块+类别) → 双池三路召回 → 编排 → 生成。

    双池(1.13) + 多模块(1.13.1): intent 判模块 anchor + 9 类 categories;
    全量池按模块筛、切片池按模块+类别筛(向量/BM25 一致), 三路 RRF。
    返回 1.6C 契约结构: {answer, references, intent, version}(API 端点/CLI 共用)。
    """
    blocks = _load_all_blocks()
    it = intent(question)
    corpus = it["anchor"] if it["anchor"] in MODULE_ANCHORS else None
    dual = retrieve_dual(question, corpus=corpus,
                         locked_categories=it["locked_categories"])
    hits = orchestrate(question, blocks, dual["full"], dual["bm25"], it,
                       top_k=top_k, vec2_result=dual["slice"], corpus=corpus)

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
