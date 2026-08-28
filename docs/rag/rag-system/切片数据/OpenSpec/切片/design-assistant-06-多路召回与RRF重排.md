# 多路召回与 RRF 重排（向量+BM25 / anchor 选池 / RRF Top-K）

> summary: 多路召回与RRF重排 — 向量+BM25 双路召回、按 anchor 选语料池、RRF 精排只回传 Top-K
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-06-多路召回与RRF重排.md
> 类别：架构设计


### 复用 vs 新增映射（recall 双路 / rerank）

> 检索摘要：多路召回与 RRF 重排哪些复用现有代码、哪些是新增？

- **recall 双路**：`retrieve_vector` / `retrieve_bm25`；复用两函数；新增单路 2s 超时包裹（asyncio.wait_for/线程池）。
- **rerank**：`orchestrate`；复用 RRF/权威度/锚定加权；新增入参加 `corpus`（按 anchor 选池，锚定公式原样），只回传 Top-K 精排块。

### 沟通结论锁定（C2 anchor 两层）

> 检索摘要：08-25 锁定 anchor 两层选池——模块级 anchor 选语料池（新）+ 节级 locked_sections 池内 authority×锚定加权（原样），anchor 缺失/ambiguous 维持全池？

- **C2 anchor 两层**：模块级 anchor（选语料池，新）+ 节级 locked_sections（池内 authority×锚定加权，原样）。orchestrate 入参加 `corpus`，锚定公式不动。anchor 缺失/ambiguous → 维持现状（全池）。

### D-A. anchor 选池（C2）

> 检索摘要：anchor 选池怎么做——orchestrate 按 corpus 参数过滤语料池，且向后兼容全池？

- `corpus` 参数：`orchestrate(question, blocks, vec, bm, strategy, top_k, corpus=None)`；`corpus` 给定时先过滤 blocks（按 module/tags.module），再走现有 RRF/权威/锚定。
- 现有 `/api/tutoring/rag/query` 不传 corpus → 全池行为不变（向后兼容）。

### 白盒链路（recall / rerank 段）

> 检索摘要：白盒链路中召回与重排的事件产出——按 anchor 选池、RRF Top-K=3、只回传精排块？

```
 → recall(向量2s超时降级 + BM25) → 按 anchor 选池
 → rerank(RRF Top-K=3) → event: rerank{blocks}  ← 只回传精排块
```
