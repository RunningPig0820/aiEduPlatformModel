"""
1.6 检索+生成 (rag_query) - 面试问答闭环

多路召回 + 加权打分 + doubao 生成:
- 向量召回: dashscope embedding, 余弦 top-K
- BM25 召回: jieba 分词, Okapi BM25 top-K
- 融合: RRF(Reciprocal Rank Fusion), 避免跨路分数归一化
- 打分: RRF × 权威度(tags.authority) × 页面锚定加权(问题分类锁节)
- 生成: doubao 用 top-K 块作上下文, 面试口述风格 + 引用清单

用法: cd ai-edu-ai-service && python scripts/rag/rag_query.py "怎么防学生套答案？" [--k 6] [--no-gen]
输入: scripts/rag/data/rag_index.npz
输出: 召回块 + 生成答案(含引用)
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import jieba
import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from core.gateway.factory import LLMFactory
from core.tutoring.vector_store import embed

DATA = os.path.join(os.path.dirname(__file__), "data", "rag_index.npz")
RRF_K = 60          # RRF 常数
TOP_K = 6           # 生成用块数
BM25_K = 10         # BM25 召回数
VEC_K = 12          # 向量召回数

# 页面锚定: 问题关键词 -> 锁定节(完善文档节号)。命中节加权 1.5, 其余 1.0。
ANCHOR_RULES = [
    (("项目", "介绍", "整体", "架构", "是什么", "做什么", "模块", "微服务", "分工"), ("01", "03")),
    (("怎么", "如何", "流程", "步骤", "操作", "图片", "OCR", "一次"), ("02", "06")),
    (("难点", "防", "套答案", "作弊", "安全", "护栏", "流式", "性能", "慢", "卡"), ("04", "07")),
    (("数据", "掌握度", "落库", "关联", "存储", "统计"), ("05",)),
    (("演进", "未来", "题库", "agent", "最危险", "规划", "路线", "坑", "闭环"), ("08",)),
]
ANCHOR_WEIGHT = 1.5

_STOP = set("的了是在和与就都以及呢吗啊呀吧么这那我有你要他她它们一个不也没很为对从到往")


def tokenize(text: str) -> list:
    return [w for w in jieba.lcut(text) if w.strip() and w not in _STOP and len(w) > 1]


class BM25:
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


def load_index():
    z = np.load(DATA, allow_pickle=True)
    V = z["vectors"]
    metas = json.loads(z["meta"])
    return V, metas


def anchor_sections(question: str) -> set:
    """问题分类 -> 锁定完善文档节集合(可能多个规则命中)"""
    locked = set()
    for kws, secs in ANCHOR_RULES:
        if any(k in question for k in kws):
            locked.update(secs)
    return locked


def retrieve(V, metas, question, top_k=TOP_K):
    q_emb = np.array(embed(question), dtype=np.float32)
    nq = np.linalg.norm(q_emb)
    q_emb = q_emb / nq if nq else q_emb
    sims = V @ q_emb  # 已归一化 → 余弦

    corpus_tokens = [tokenize(m["summary"] + "\n" + m["text"]) for m in metas]
    bm = BM25(corpus_tokens)
    q_tokens = tokenize(question)
    bm_scores = [bm.score(q_tokens, i) for i in range(len(metas))]

    # 两路 top-K
    vec_rank = {i: r for r, i in enumerate(np.argsort(-sims)[:VEC_K])}
    bm_rank = {i: r for r, i in enumerate(sorted(range(len(metas)),
                                                  key=lambda i: -bm_scores[i])[:BM25_K])}

    locked = anchor_sections(question)
    scored = []
    for i in set(vec_rank) | set(bm_rank):
        rrf = 0.0
        if i in vec_rank:
            rrf += 1.0 / (RRF_K + vec_rank[i])
        if i in bm_rank:
            rrf += 1.0 / (RRF_K + bm_rank[i])
        auth = metas[i]["tags"].get("authority", 0.7)
        anchor_w = ANCHOR_WEIGHT if metas[i]["tags"]["section"] in locked else 1.0
        scored.append((rrf * auth * anchor_w, sims[i], rrf, i))

    scored.sort(key=lambda x: -x[0])
    hits = []
    for final, sim, rrf, i in scored[:top_k]:
        m = metas[i]
        hits.append({
            "rank": len(hits) + 1,
            "score": round(final, 4),
            "sim": round(float(sim), 4),
            "authority": m["tags"]["authority"],
            "source": m["tags"]["source"],
            "section": m["tags"]["section"],
            "file": m["tags"]["file"],
            "anchor": m["tags"]["anchor"],
            "summary": m["summary"],
            "text": m["text"],
        })
    return hits, sorted(locked)


def _make_llm():
    return LLMFactory.create(
        "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.2,
        extra_body={"thinking": {"type": "disabled"}},
        request_timeout=60, max_retries=1,
    )


_GEN_SYSTEM = """你是「AI答疑」项目的介绍人，正在接受面试官面试。下面给出检索到的项目语料块（按相关度排序，每块带来源/权威度/锚点）。回答要求：
1. 只依据语料内容回答，语料没覆盖的不编造、不硬答
2. 面试口述风格：先给结论，再分层展开，能接住追问
3. 引用的要点在回答后注明出处（格式：〔来源/文件/锚点〕）
4. 保持简洁，不要输出思考过程"""


def generate(hits, question):
    ctx = []
    for h in hits:
        head = f"〔{h['source']}/{h['file']}/{h['anchor']}｜权威{h['authority']}〕"
        ctx.append(f"{head}\n{h['text'][:1200]}")
    prompt = f"面试官问题：{question}\n\n--- 检索到的语料块 ---\n\n" + "\n\n".join(ctx)
    llm = _make_llm()
    resp = llm.invoke([
        SystemMessage(content=_GEN_SYSTEM),
        HumanMessage(content=prompt),
    ])
    return resp.content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="面试官问题")
    ap.add_argument("--k", type=int, default=TOP_K, help="生成用召回块数")
    ap.add_argument("--no-gen", action="store_true", help="只召回不生成")
    args = ap.parse_args()

    V, metas = load_index()
    hits, locked = retrieve(V, metas, args.question, top_k=args.k)

    print(f"问题: {args.question}")
    print(f"锚定锁定节: {sorted(locked) if locked else '(无, 全量加权)'}")
    print("-" * 70)
    for h in hits:
        frag = h["text"][:60].replace("\n", " ")
        print(f"#{h['rank']} [{h['source']}/{h['file']}] 权威{h['authority']} "
              f"分{h['score']} sim{h['sim']}")
        print(f"   锚点: {h['anchor']} | summary: {h['summary']}")
        print(f"   {frag}...")
    print("-" * 70)

    if not args.no_gen:
        print("\n== 生成回答 ==")
        print(generate(hits, args.question))


if __name__ == "__main__":
    main()
