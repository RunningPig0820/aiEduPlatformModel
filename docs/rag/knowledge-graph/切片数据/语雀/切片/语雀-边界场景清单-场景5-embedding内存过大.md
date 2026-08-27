# 场景5 本地 embedding 内存过大
> summary: 本地 embedding 内存不够怎么办？bge 懒加载 3.5GB → 预构建索引仅 10MB（--use-prebuilt-index），numpy 单次检索 <5ms。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-边界场景清单-场景5-embedding内存过大.md
> 类别：开发难点

| 属性 | 内容 |
|---|---|
| 触发条件 | 每次匹配重新加载模型+建索引约 60 秒、内存 3.5GB |
| 当前处理 | 预构建一次（kg_vectors.npy 等 4 文件）、多次复用；内存约 10MB |
| 兜底 | checksum 失配回退懒加载 |
| 风险 | 索引过期 |
| 证据 | 证据：语雀-产品中心-问题记录.md / edukg/core/textbook/vector_index_manager.py |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（场景5）
