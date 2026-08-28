# 两道门与边界拒答（权限门 Java / 范围门 0.75/0.5 / 边界话术）

> summary: 两道门与边界拒答 — 权限门在 Java（Python 不产 permission）+ 范围门低置信过滤（0.75/0.5）+ 边界话术 + 语料数据驱动无禁区
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-08-两道门与边界拒答.md
> 类别：业务流程


### 复用 vs 新增映射（范围门）

> 检索摘要：范围门复用哪些现有代码、哪些是新增——core/rag 新增、复用现有降级语义、低置信过滤（索引层 0.75/源 0.5）？

- **范围门**：`core/rag` 新增；复用现有降级语义；低置信过滤（索引层 0.75/源 0.5）。

### 沟通结论锁定（C1 语料范围）

> 检索摘要：08-25 锁定语料范围——只管 AI答疑（234 块），其他模块低置信拒答正确、语料后补自动可答（数据驱动无禁区）？

- **C1 语料范围**：只管 AI答疑（234 块）；RAG/题型/知识图谱当前低置信拒答正确，语料后补自动可答（数据驱动，无禁区）。

### 白盒链路（boundary 段）

> 检索摘要：白盒链路中边界拒答的事件产出——综合分<0.75/0.5 触发 boundary(low_confidence) 固定话术 0 token 即 done？

```
 → rerank(RRF Top-K=3) → event: rerank{blocks}  ← 只回传精排块
     ├─ 综合分<0.75/0.5 → event: boundary(low_confidence) 固定话术 0 token → done
```

### D-F. 事件时序冻结（permission 归属定死）

> 检索摘要：生产端点 Python 为什么不产 permission 事件——角色门在 Java、Python 无角色信息？

- **permission 归属定死**：production API Python **不产 permission**（角色门在 Java，Python 无角色信息）。Python 自测时在测试里模拟完整时序，生产端点从 intent 开始。

### Risks / Trade-offs（边界拒答相关）

> 检索摘要：anchor 选池后其他模块命中空的风险——低置信过滤（C1 预期）兜底？

- [anchor 选池后语料少] 当前仅 AI答疑 → 其他模块命中空 → 低置信过滤（C1 预期）。
