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
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag", "data")
DATA = os.path.join(DATA_DIR, "rag_slices.jsonl")          # 兼容旧引用 = ai-tutoring 切片池
DATA_FULL = os.path.join(DATA_DIR, "rag_slices_full.jsonl")  # ai-tutoring 全量池
# 多模块 jsonl(2026-08-27): ai-tutoring + question-analysis 共用 rag-full/rag-slice 索引,
# 语料按模块加载(MODULE_DATA 全读, 模块靠 tags.module 区分 + select_corpus 过滤)。
MODULE_DATA = {
    "ai-tutoring": ("rag_slices.jsonl", "rag_slices_full.jsonl"),
    "question-analysis": ("rag_slices-question-analysis.jsonl", "rag_slices_full-question-analysis.jsonl"),
    "knowledge-graph": ("rag_slices-knowledge-graph.jsonl", "rag_slices_full-knowledge-graph.jsonl"),
    "rag-system": ("rag_slices-rag-system.jsonl", "rag_slices_full-rag-system.jsonl"),
}

# 检索参数
RRF_K = 60          # RRF 融合常数
FULL_POOL_WEIGHT = 2.0   # 全量池权威1.0加权(2026-08-29): 只对 authority=1.0 完善文档(主答案)在向量路乘权重,
                         # 语雀/代码整篇(0.8)不加——完善文档单向量1路 vs 切片池多路易被挤出 top-5, 加权保主答案
TOP_K = 5           # 生成用块数(双向量方案编排 top-5, 2026-08-26)
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
    "问候": (),   # M6 ④(6.6): 问候走固定欢迎 + 引导, 不锁节不 recall
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

> 优先级规则：只有问题在**没有指代当前功能**、且明确问 RAG 系统本身的整体实现（如"RAG 系统整体架构""多路召回怎么实现"）才选 rag-system；问"这个功能的底层/实现/架构" → 选 current_project（current_project 语料有该功能的架构切片）。

> 指代词规则：问题中的"这个功能/它/本功能/当前功能/这个项目/这个系统"等指代词，指代的就是当前上下文模块（current_project）。除非问题明确点名另一个模块名称（如"知识图谱的…""题型分析…""RAG 系统…"），否则这些指代一律解析为 current_project，不得因"底层/实现/架构/怎么做到"等关键词跳走。

2. category（文档页路由，单选，页面跳转使用）
枚举：项目介绍 | 操作 | 难点 | 数据关联 | 最危险 | 问候 | 其他
示例：为什么做/定位/是什么 → 项目介绍；怎么走/步骤/流程 → 操作；防作弊/安全/护栏/性能卡/踩坑 → 难点；掌握度/落库/知识点 → 数据关联；没题库/答错/兜底 → 最危险；你好/您好/hi/hello 等纯问候 → 问候（ambiguous=false, 不触发澄清）

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
        ctx_line = (f"当前上下文模块：{current_project}。"
                    f"【关键】问题里出现'这个功能/它/本功能/当前功能'等指代时，指的就是 {current_project}，"
                    f"不要因'底层/实现/架构/怎么做到'等词跳到 rag-system。"
                    f"只有当问题无指代、且明确问 RAG 系统整体实现（点名 rag 系统/整体架构/召回算法）才选 rag-system。")
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


def _deictic_anchor(question: str, anchor: str, current_project: str) -> str:
    """指代词确定性兜底(后端改法4, 2026-08-26): 问题含"这个功能/这个/它/本功能/当前功能/本项目"
    指代当前模块, 且未点名其他模块名, 强制 anchor=current_project——LLM 因"底层/实现/架构"
    跳走 rag-system 时也能兜住(如"这个功能的底层是怎么实现的" current_project=ai-tutoring)。

    current_project 非闭集 → 不动; anchor 已是 current_project → 不动;
    问题点名其他模块(RAG 系统/知识图谱/题型/多路召回等) → 不动(硬路由保留)。
    """
    if current_project not in MODULE_ANCHORS or anchor == current_project:
        return anchor
    deictic = ("这个功能", "这个系统", "这个项目", "本功能", "当前功能", "这个", "它")
    named_other = ("知识图谱", "题型", "RAG 系统", "RAG系统", "rag 系统", "rag系统",
                   "RAG 项目", "多路召回", "召回算法", "向量库", "RRF", "评测")
    if any(d in question for d in deictic) and not any(n in question for n in named_other):
        return current_project
    return anchor


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

    # 改法4(后端建议, 2026-08-26): 指代词确定性兜底——LLM 因"底层/实现"把"这个功能"判走
    # rag-system 时, 强制 anchor=current_project(即使 LLM 不听话也能兜住)
    anchor = _deictic_anchor(question, anchor, current_project)

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
    """双池合并语料(所有模块的切片池 + 全量池), BM25/keymap 用。池前缀在 _key_of 区分。

    2026-08-27 多模块: 从只加载 ai-tutoring 改为加载 MODULE_DATA 全部模块(ai-tutoring + question-analysis),
    否则 qa 向量命中后 keymap/BM25 无 qa 块 → orchestrate `block is None` 被丢弃。缺失文件跳过容错。
    """
    blocks = []
    for slice_name, full_name in MODULE_DATA.values():
        for name in (slice_name, full_name):
            p = os.path.join(DATA_DIR, name)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    blocks.extend(json.loads(line) for line in f if line.strip())
    return blocks


# ============ 召回单元 (1.6B, 独立) ============


DEFAULT_MODULE = "rag-system"        # 1.13: 未传 module 时的默认(项目介绍 RAG 上下文)


def build_filter(module: str | None = None, categories: list | None = None) -> dict:
    """module → COS Filter($eq)。仅按模块筛。

    2026-08-26 决策: 查询不再按 categories 过滤——评测实测 LLM 判类别不准, 类别过滤
    会误伤相关块(如"答疑和知识图谱怎么联动"被判项目介绍, 过滤掉数据关联块)。保留
    categories 参数仅作签名兼容, 不再用于过滤。
    """
    return {"module": {"$eq": module or DEFAULT_MODULE}}


def retrieve_vector(question: str, vector_type: str = "rag",
                    module: str | None = None, categories: list | None = None,
                    top_k: int = VEC_K) -> dict:
    """向量召回单元: COS query_vectors(rag 桶, 按 module 条件筛选) → hits + confidence。

    独立单元契约: 入参 question + vector_type + module(1.13 多模块, 向量层按模块过滤,
    防其他模块相似向量挤占 top-k), 出参 {hits, confidence}; 异常由编排器捕获。
    module 未传 → 默认 rag-system。categories 参数保留兼容, 不再过滤(2026-08-26 决策)。
    top_k: 召回数(切片池双向量时 VEC_K+2, 补偿同块 -c/-q 双记录占位, task #78)。
    """
    filt = build_filter(module, categories)
    hits = query_vector(question, top_k=top_k, vector_type=vector_type, filter_=filt)
    # confidence = 平均相似度(1 - 平均余弦距离); COS distance 越小越相似
    conf = 0.0
    if hits:
        conf = 1.0 - sum(h.get("distance", 1.0) for h in hits) / len(hits)
    return {"hits": hits, "confidence": max(0.0, conf)}


def _split_roles(result: dict) -> tuple:
    """切片池双向量(2026-08-26, task #78): 按 key 后缀拆 content(-c)/question(-q) 两路。

    同块 -c/-q 都命中时, 归一化后 key 相同但 rank 不同, orchestrate 两路各自贡献 RRF(互补)。
    -c 缺省无后缀也归内容路(兼容全量池单向量, 防御)。
    返回 (content_result, question_result), 各自 {hits, confidence}。
    """
    content = {"hits": [], "confidence": result["confidence"]}
    question = {"hits": [], "confidence": result["confidence"]}
    for h in result.get("hits", []):
        key = h.get("key", "")
        if key.endswith("-q"):
            h["key"] = key[:-2]
            question["hits"].append(h)
        else:
            h["key"] = key[:-2] if key.endswith("-c") else key
            content["hits"].append(h)
    return content, question


def retrieve_dual(question: str, corpus: str | None = None,
                  locked_categories: list | None = None) -> dict:
    """双池召回(1.13 Q3 + 多模块): 全量池向量 + 切片池双向量 + BM25 → 各路供 RRF。

    向量层条件筛选(1.13 下推): 全量池/切片池都只按 module 过滤。
    双向量(2026-08-26, task #78): 切片池每块 -c/-q 两路, 这里按 key 后缀拆成
    slice(内容) + slice_q(summary/问题) 两路; 全量池单向量原样。
    module 未传 → 默认 rag-system。locked_categories 保留参数兼容, 不再过滤
    (2026-08-26 决策: LLM 判类别不准, 类别过滤误伤相关块)。
    corpus(模块 anchor): 本地 BM25 只打该模块语料池(与编排层 select_corpus 一致)。
    """
    full = retrieve_vector(question, vector_type="rag-full", module=corpus)   # 全量池: 单向量
    # 切片池双向量: 向量 top-k 多取 2(VEC_K+2), 补偿同块 -c/-q 双记录占位
    slice_ = retrieve_vector(question, vector_type="rag-slice", module=corpus,
                             top_k=VEC_K + 2)
    content, question_ = _split_roles(slice_)
    blocks = _load_all_blocks()
    pool = select_corpus(blocks, corpus) if corpus else blocks
    bm = retrieve_bm25(question, pool)
    return {"full": full, "slice": content, "slice_q": question_, "bm25": bm}


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
    """块 → 向量 key(与 build_index 同规则: {池前缀}/{module}/{file}/{anchor}#{idx})。

    池前缀 = rag-{tags.pool}(rag-full/rag-slice), 与 COS 索引 key 对齐, 防两池 (file,anchor) 冲突;
    2026-08-27 加 module 段: 多模块共用索引, 跨模块同名文件(完善文档 01-08)键必须含 module 防覆盖。
    """
    t = b["tags"]
    pool = t.get("pool", "slice")
    return f"rag-{pool}/{t.get('module', 'ai-tutoring')}/{t['file']}/{t['anchor']}#{t.get('_idx', 0)}"


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
                vec2_result: dict | None = None,
                vec3_result: dict | None = None) -> list:
    """编排器: RRF 融合 × authority 权威度 × 页面锚定加权 × 类别过滤 → top-K 完整命中。

    四路 RRF(2026-08-26 双向量, task #78): vec_result(全量池向量) + vec2_result(切片内容
    -c, 可选) + vec3_result(切片 summary/问题 -q, 可选) + bm25_result。vec2/vec3 的 key
    已由 _split_roles 归一化为块 key, 同块两路命中各自贡献 RRF(互补)。
    category 过滤(1.13 Q5): strategy.locked_categories 非空时, 只保留切片池命中该类别块
    (先 module 选池、再类别过滤两级; 全量池不过滤, 无类别锁定全保留)。
    corpus(可选, A3/C2): 模块 anchor, 给定时先按 module 过滤语料池再融合; None → 全池。
    top_k 命中项含: key/metadata/authority/source/section/file/file_path/anchor/summary/text。
    """
    pool = select_corpus(blocks, corpus) if corpus else blocks
    keymap = _assign_idx(pool)

    # 四路 rank: 全量向量 + 切片内容(-c) + 切片 summary(-q) + BM25
    vec_keys = [h["key"] for h in vec_result["hits"]]
    vec2_keys = [h["key"] for h in vec2_result["hits"]] if vec2_result else []
    vec3_keys = [h["key"] for h in vec3_result["hits"]] if vec3_result else []
    bm_keys = [h["key"] for h in bm25_result["hits"]]

    vec_rank = {k: r for r, k in enumerate(vec_keys)}
    vec2_rank = {k: r for r, k in enumerate(vec2_keys)}
    vec3_rank = {k: r for r, k in enumerate(vec3_keys)}
    bm_rank = {k: r for r, k in enumerate(bm_keys)}
    locked = set(strategy.get("locked_sections", []))

    scored = []
    for key in set(vec_rank) | set(vec2_rank) | set(vec3_rank) | set(bm_rank):
        block = keymap.get(key)
        if block is None:
            continue
        rrf = 0.0
        if key in vec_rank:
            # 精准加权(2026-08-29): 只给 authority=1.0 完善文档(主答案)加权, 语雀/代码整篇(0.8)不加
            w = FULL_POOL_WEIGHT if block["tags"].get("authority") == 1.0 else 1.0
            rrf += w / (RRF_K + vec_rank[key])
        if key in vec2_rank:
            rrf += 1.0 / (RRF_K + vec2_rank[key])
        if key in vec3_rank:
            rrf += 1.0 / (RRF_K + vec3_rank[key])
        if key in bm_rank:
            rrf += 1.0 / (RRF_K + bm_rank[key])
        t = block["tags"]
        authority = t.get("authority", 0.7)
        anchor_w = ANCHOR_WEIGHT if t.get("section") in locked else 1.0
        # 1.13.2 决策: 不做类别过滤/提权(LLM 判类别不准会误伤相关块); 保留 RRF×authority×节锚定
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


_GEN_SYSTEM = """你是「AI答疑」项目面试专属讲解助手，根据检索语料回答面试官问题，输出专业、有架构深度、适合口述的面试答案。

## 硬性核心约束（绝对遵守）
1. **只基于召回语料作答，绝不脑补、绝不编造语料外逻辑、功能、细节。**
2. 禁止输出思考过程、草稿、推理过程，只输出最终面试回答。
3. 固定输出结构：**先一句话核心结论 → 分层结构化展开（口语化、有逻辑、有重点） → 末尾统一贴参考来源**。
4. 所有文档引用统一放在回答最后集中展示，正文不插来源标记；来源按序号逐条分行展示。
5. 语料中的对账标记、特殊符号不进正文，仅面试官明确询问时才可使用。
6. **追问禁止基于上一轮残缺答案扩写！每一轮追问都必须重读全部原始召回语料，重新完整生成，不沿用旧残缺逻辑。**

## 【最重要｜面试优先级规则（根治回答简陋）】
所有技术/架构/流程类问题，**优先级从高到低强制如下**，模型必须优先输出高价值内容，低价值内容仅做辅助点缀：
1. **最高优先级（面试核心得分点，必须重点展开）**
   架构职责边界、微服务权责划分、决策权归属、校验前置拦截逻辑、并发控制、限流、锁机制、降级策略、异常兜底、安全护栏规则、状态机设计、存储取舍、工程设计权衡、扩展性设计。
2. **次级优先级（中等篇幅）**
   完整业务链路、分层执行逻辑、核心落地流程、关键步骤约束条件。
3. **最低优先级（极简带过，禁止堆砌）**
   接口名、SSE事件名、普通字段名、基础路由逻辑，**不允许大段罗列接口流水账**。

## 问题分类专属输出规则
### 1. 【怎么做/流程/架构/实现方案】（高频问题）
**禁止单纯罗列时序调用流程！！！**
必须做到：
- 每一段流程，**必须同步绑定对应的工程约束、校验条件、兜底机制、架构设计原因**
- 必须**多文档交叉融合**：流程图时序 + 微服务分工 + 决策权机制 + 落地代码规则 互相印证输出
- 明确讲清：**谁管控、谁决策、谁执行、谁兜底、为什么这么分层**
- 区分：普通业务流程（简略）、架构设计亮点（详写）

输出结构：核心结论 → 整体架构分层 → 各层职责+落地约束+设计亮点 → 关键机制（锁/降级/护栏/无状态）→ 闭环价值

### 2. 【为什么/动机/价值/痛点】
优先输出：原有痛点、设计解决的问题、风控收益、稳定性收益、架构解耦价值、可扩展价值、业务闭环价值，**禁止单纯介绍模块功能**。

### 3. 【对比/差异类问题】
严格维度对照输出，双向对比，不单边罗列特性。

## 行文风格强制规则
1. 面试口语化、干净利落、逻辑递进，**拒绝文档摘抄、拒绝流水账、拒绝纯时序复述**。
2. 所有流程讲解必须「**带条件、带约束、带原因、带价值**」，不写无意义的过程描述。
3. 突出项目**工程能力、架构管控、稳定性设计**，而不是只会调接口。

## 专属本项目强制输出规则（AI答疑项目固化）
回答本项目流程/架构问题时，**必须主动带出以下核心亮点（语料存在就必须输出）**
1. 三层微服务严格解耦：前端纯交互、Java全权管控、Python纯智能无状态
2. **Python出决策类型、Java护栏最终审批，LLM无自主决策权**的核心设计
3. 前置学科拦截、无效请求不建会话的资源优化
4. 并发锁、Redis会话管控、轮次上限强制收尾机制
5. 降级兜底、失败不中断链路的容错设计
6. 前端不直连COS、本地缓存对账兜底的安全与稳定性设计
7. Python无状态、可水平扩展、上下文推断的架构优势

## 参考来源固定格式
【参考来源】:
1. 引用 : {来源/文件名}     ← "引用"填块的来源/文件名(简短, 如"引导问题/引导问题-05"), 不带锚点、不带权威度
   锚点 : {块锚点标题}      ← "锚点"填块的锚点标题(简短问题, 如"怎么防学生套答案?"), 不填完整路径、不填正文摘要、不填权威度
2. 引用 : {来源/文件名}
   锚点 : {块锚点标题}"""


def _make_llm():
    return LLMFactory.create(
        "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}},
        request_timeout=60, max_retries=1,
    )


def generate(hits: list, question: str, return_usage: bool = False):
    """doubao 生成答案(面试口述风格 + 引用)。hits 为 orchestrate 输出。

    追问不基于旧答案(2026-08-26): _GEN_SYSTEM 硬性约束 6 要求每轮追问重读全部原始召回
    语料重新完整生成——rewrite 补全问题后重新检索, 生成读新检索块, 不沿用上一轮 answer。
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
                       top_k=top_k, vec2_result=dual["slice"],
                       vec3_result=dual["slice_q"], corpus=corpus)

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
