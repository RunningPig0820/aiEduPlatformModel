# token 成本与真算（usage / cache_hit / 累计 token 归 Java）

> summary: token成本与真算 — usage 真算、cache_hit 实测兜底估算、会话累计 token 由 Java 网关聚合
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-10-token成本与真算.md
> 类别：数据存储


### 复用 vs 新增映射（close / 累计 token）

> 检索摘要：会话累计 token 端点复用还是新增——新端点、Redis 或内存会话累计（Python 无状态边界待确认）？

- **close/累计token**：新端点；Redis 或内存会话累计（Python 无状态边界待确认）。

### 沟通结论锁定（C3 cache_hit）

> 检索摘要：08-25 锁定 cache_hit——开发时实测 doubao 是否返回 usage.cache_hit，取不到则 tokenizer 估算+标注"估算"？

- **C3 cache_hit**：开发时实测 doubao 是否返回 usage.cache_hit；取不到 → tokenizer 估算 + 标注"估算"。

### D-D. 会话状态（close/trace_id）——累计 token 部分

> 检索摘要：会话累计 token 谁算——close = Java 关中继，累计 token 归 Java？

- **close**：Python **不建 close 端点**——close = Java 关中继 → Python `is_disconnected()` 中止 doubao + Java Redis 置 closed + 返回累计。累计 token 归 Java。
