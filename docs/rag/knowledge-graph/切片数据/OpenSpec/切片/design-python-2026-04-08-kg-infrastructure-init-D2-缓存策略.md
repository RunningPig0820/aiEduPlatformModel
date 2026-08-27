# D2: 缓存策略
> summary: LLM 响应缓存落盘文件，用 SHA256 前 16 位作缓存键，提供 save_cache/load_cache，保证唯一性与可调试性。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-D2-缓存策略.md
> 类别：数据存储

> 检索摘要：LLM 响应缓存落盘文件，用 SHA256 前 16 位作缓存键，提供 save_cache/load_cache，保证唯一性与可调试性。

**决策**: LLM 响应缓存到文件，使用 SHA256 作为键

```python
import hashlib
import json

def get_cache_key(prompt: str) -> str:
    """生成缓存键"""
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]

def save_cache(cache_key: str, result: dict, cache_dir: str = "cache/"):
    """保存缓存"""
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return str(cache_file)

def load_cache(cache_key: str, cache_dir: str = "cache/") -> Optional[dict]:
    """加载缓存"""
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None
```

**理由**:
- 文件缓存简单可靠
- SHA256 键保证唯一性
- 便于调试（可直接查看文件）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§D2: 缓存策略）
