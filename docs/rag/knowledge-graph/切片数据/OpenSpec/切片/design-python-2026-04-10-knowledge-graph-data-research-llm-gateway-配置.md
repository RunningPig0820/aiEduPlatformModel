# 10.3 LLM Gateway 配置
> summary: LLM Gateway 新增 prerequisite_inference scene 映射：zhipu glm-4-flash、temperature 0.3。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-llm-gateway-配置.md
> 类别：架构设计

> 检索摘要：LLM Gateway 新增 prerequisite_inference scene 映射：zhipu glm-4-flash、temperature 0.3。

在 config/model_config.py 新增 scene 映射：
SCENE_MODEL_MAPPING = {
    # ... 现有配置
    "prerequisite_inference": {
        "provider": "zhipu",
        "model": "glm-4-flash",
        "temperature": 0.3,
    },
}

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§10.3 LLM Gateway 配置）
