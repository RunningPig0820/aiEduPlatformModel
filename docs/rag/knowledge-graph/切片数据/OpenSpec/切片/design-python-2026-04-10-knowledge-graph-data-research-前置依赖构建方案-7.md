# 前置依赖构建方案（续）
> summary: 前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-前置依赖构建方案-7.md
> 类别：数据关联

---

### 五、前置依赖关系构建方案（多证据融合）（续）

> 检索摘要：前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

### 5.6 多证据融合
> 检索摘要：多证据融合规则：定义依赖强证据直接生成 PREREQUISITE，LLM 两模型一致且置信度≥0.8 生成 PREREQUISITE，否则降为候选。

def fuse_prerequisites(definition_deps, llm_candidates):
    """
    融合定义依赖 + LLM 多模型投票，生成最终 PREREQUISITE
    """
    EVIDENCE_WEIGHTS = {
        "definition_dependency": 0.85,
        "llm_inference": 0.8,
    }

    relations = {}

    # 定义依赖（强证据，直接生成 PREREQUISITE）
    for dep in definition_deps:
        key = (dep["from"], dep["to"])
        relations[key] = {
            "confidence": EVIDENCE_WEIGHTS["definition_dependency"],
            "evidence_types": ["definition_dependency"],
            "source": "definition_extraction"
        }

    # LLM 候选（两模型一致且置信度 >=0.8）
    for cand in llm_candidates:
        key = (cand["from"], cand["to"])
        if cand["confidence"] >= 0.8:
            if key in relations:
                # 已有定义依赖，提升置信度
                relations[key]["confidence"] = min(1.0, relations[key]["confidence"] + 0.1)
                relations[key]["evidence_types"].append("llm_inference")
            else:
                relations[key] = {
                    "confidence": cand["confidence"],
                    "evidence_types": ["llm_inference"],
                    "source": "llm_multi_vote"
                }
        else:
            # 低置信度存入 PREREQUISITE_CANDIDATE
            pass

    return relations

融合规则总结：
● 定义依赖：强证据，直接生成 PREREQUISITE
● LLM 候选：两模型一致 + 置信度 ≥0.8 → PREREQUISITE；否则 → PREREQUISITE_CANDIDATE
● 教材顺序：仅作为 TEACHES_BEFORE，不转化为 PREREQUISITE


> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§五、前置依赖关系构建方案（多证据融合）（续））
