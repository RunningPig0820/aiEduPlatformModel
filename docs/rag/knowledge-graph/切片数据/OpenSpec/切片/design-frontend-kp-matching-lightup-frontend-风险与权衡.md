# 风险与权衡

> summary: 风险：题型粒度掌握度依赖后端模型纠正、派生算法由后端定、大列表需分页、ReactFlow 全量图谱重，均有缓解或兜底方案。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-风险与权衡.md
> 类别：开发难点

---

### Risks / Trade-offs

> 检索摘要：风险：题型粒度掌握度依赖后端模型纠正、派生算法由后端定、大列表需分页、ReactFlow 全量图谱重，均有缓解或兜底方案。

- [题型粒度掌握度依赖后端模型纠正] → 前端展示「题型掌握度」与「知识点派生覆盖度」依赖后端把掌握度主键从 `kpKey` 翻转为题型。缓解：后端模型纠正到位前，前端先按现有 `kpKey` 数据兜底/空跑，不阻塞页面骨架。
- [知识点派生覆盖度的算法] → 派生公式（Σ 题型掌握度 × ratio）由后端决定，前端只消费结果。缓解：契约先定「派生覆盖度」字段，公式后端实现。
- [全量地图/题型库数据量 1000+] → 全量知识点、题型库均是大列表，必须后端分页（`page`/`size` + `total`）。缓解：新接口设计即带分页；题型掌握度明细（学生本人几十条）前端 `slice` 即可。
- [全量图谱重] → ReactFlow 组件重，仅作为「切换图谱」的次级视图，默认轻量列表。缓解：两视图分离，默认轻。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§Risks / Trade-offs）
