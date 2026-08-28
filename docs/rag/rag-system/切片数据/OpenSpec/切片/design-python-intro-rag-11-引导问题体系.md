# 引导问题体系

> summary: 引导问题体系（design-python-project-intro-rag）：UI引导问题（变体文案）通过向量检索匹配索引层规范问题，而非按问题ID直连答案，避免点按钮=预定答案
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-11-引导问题体系.md
> 类别：操作流程

---

### Requirement: 引导问题变体匹配 SHALL 明细（补"按问题 ID 直连"否定项）

> 检索摘要：UI引导问题变体怎么命中规范问题？不按问题ID直连答案，走同一检索管道向量语义匹配，避免点按钮=预定答案

- 系统 SHALL 支持 UI 引导问题(变体文案)通过向量检索匹配到索引层的规范问题,**而非按问题 ID 直连答案**。

#### Scenario: 变体文案语义匹配
- **WHEN** UI 引导问题为"你们为什么拆成三段"而索引层规范问题为"为什么拆 decide/generate/question-understand"
- **THEN** 系统 SHALL 通过向量检索命中该规范问题条目(走同一检索管道)

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§补充 retrieval-引导问题变体匹配SHALL明细）
