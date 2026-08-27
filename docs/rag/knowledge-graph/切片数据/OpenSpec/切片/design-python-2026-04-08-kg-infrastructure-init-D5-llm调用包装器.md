# D5: LLM 调用包装器
> summary: CachedLLM 带缓存 LLM 包装器：先查缓存再调模型，结果自动保存，支持 use_cache 开关。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-D5-llm调用包装器.md
> 类别：架构设计

> 检索摘要：CachedLLM 带缓存 LLM 包装器：先查缓存再调模型，结果自动保存，支持 use_cache 开关。

**决策**: 带 cache 的 LLM 调用包装器

```python
class CachedLLM:
    """带缓存的 LLM 调用"""

    def __init__(self, llm, cache_dir: str = "cache/"):
        self.llm = llm
        self.cache_dir = cache_dir

    def invoke(self, prompt: str, use_cache: bool = True) -> dict:
        """调用 LLM，支持缓存"""
        cache_key = get_cache_key(prompt)

        # 尝试从缓存加载
        if use_cache:
            cached = load_cache(cache_key, self.cache_dir)
            if cached:
                return cached

        # 调用 LLM
        result = self.llm.invoke(prompt)

        # 保存缓存
        save_cache(cache_key, result, self.cache_dir)

        return result
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§D5: LLM 调用包装器）
