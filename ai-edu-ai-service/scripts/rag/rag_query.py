"""
1.6 检索+生成 (rag_query) - 面试问答闭环(CLI 薄壳, 核心在 core/rag/query.py)

按 1.6B 接口纪律分层: 意图钩子 → 独立召回单元(向量/BM25) → 编排器 → 生成。
输出 1.6C 契约结构 {answer, references, intent, version}。

用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/rag_query.py "怎么防学生套答案？" [--k 6] [--no-gen]
输入: scripts/rag/data/rag_slices.jsonl(语料) + rag-1318177119/rag-index(向量)
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.rag import query as rag_core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="面试官问题")
    ap.add_argument("--k", type=int, default=rag_core.TOP_K, help="生成用召回块数")
    ap.add_argument("--no-gen", action="store_true", help="只召回不生成")
    args = ap.parse_args()

    blocks = rag_core._load_all_blocks()
    it = rag_core.intent(args.question)
    corpus = it["anchor"] if it["anchor"] in rag_core.MODULE_ANCHORS else None
    print(f"问题: {args.question}")
    print(f"意图: 模块 {it['anchor'] or '(未判)'} 锁节 {it['locked_sections'] or '(无)'} "
          f"类别 {it['locked_categories'] or '(不筛)'}")

    try:
        dual = rag_core.retrieve_dual(args.question, corpus=corpus,
                                      locked_categories=it["locked_categories"])
        vec_note = (f"全量{len(dual['full']['hits'])}hits conf{dual['full']['confidence']:.2f} | "
                    f"切片{len(dual['slice']['hits'])}hits conf{dual['slice']['confidence']:.2f} | "
                    f"BM25 {len(dual['bm25']['hits'])}hits")
    except Exception as e:
        bm_pool = rag_core.select_corpus(blocks, corpus) if corpus else blocks
        dual = {"full": {"hits": [], "confidence": 0.0}, "slice": {"hits": [], "confidence": 0.0},
                "bm25": rag_core.retrieve_bm25(args.question, bm_pool)}
        vec_note = f"向量路失败 → 降级纯 BM25 ({e})"
    print(f"召回: {vec_note}")

    hits = rag_core.orchestrate(args.question, blocks, dual["full"], dual["bm25"], it,
                                top_k=args.k, vec2_result=dual["slice"], corpus=corpus)

    print("-" * 70)
    if not hits:
        print("无命中 → 拒答: 该问题语料未覆盖")
    for h in hits:
        frag = h["text"][:60].replace("\n", " ")
        print(f"#{hits.index(h) + 1} [{h['source']}/{h['file']}] 权威{h['authority']} 分{h['score']}")
        print(f"   锚点: {h['anchor']} | file_path: {h['file_path']}")
        print(f"   摘要: {h['summary']}")
        print(f"   {frag}...")
    print("-" * 70)

    if not args.no_gen:
        if not hits:
            print("\n== 生成回答 ==\n该问题语料未覆盖，建议问项目相关话题")
        else:
            try:
                print("\n== 生成回答 ==")
                print(rag_core.generate(hits, args.question))
            except Exception as e:
                print(f"\n== 生成失败(降级返回召回清单) ==\n生成服务不可用: {e}")


if __name__ == "__main__":
    main()
