# 13.6 缓存策略（SHA256）
> summary: 缓存键用 SHA256 替代 MD5 避免碰撞，基于 uri 排序+prompt版本+model 生成唯一缓存键。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-缓存策略-sha256.md
> 类别：数据存储

> 检索摘要：缓存键用 SHA256 替代 MD5 避免碰撞，基于 uri 排序+prompt版本+model 生成唯一缓存键。

改进：使用 SHA256 替代 MD5，避免碰撞风险：
import hashlib
import json

def get_cache_key(batch, prompt_version: str, model: str) -> str:
    """生成唯一缓存键"""
    ids = sorted([kp.uri for kp in batch])
    key_dict = {
        'uris': ids,
        'prompt_version': prompt_version,
        'model': model,
        # 可选：加入 prompt template hash
    }
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()[:32]

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.6 缓存策略（SHA256））
