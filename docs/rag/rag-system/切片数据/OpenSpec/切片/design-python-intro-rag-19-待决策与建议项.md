# 待决策与建议项

> summary: 待决策与建议项（design-python-project-intro-rag）：Risks风险权衡（COS断网/语料完善工作量大/引导预写被质疑非纯RAG/流式usage不返回/多版本矛盾/跨页一致性）+ Open Questions待决策
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-19-待决策与建议项.md
> 类别：未来演进

---

### Risks / Trade-offs:风险与权衡

> 检索摘要：项目介绍RAG有哪些风险权衡？COS断网、语料完善工作量大、引导预写被质疑非纯RAG、流式usage不返回、多版本矛盾、跨页答案一致性，各有对策

- [COS 网络依赖] demo 现场断网/超时 → 本地索引兜底 + 降级矩阵真跑通
- [语料完善工作量大] 每模块一份完善文档是主要成本 → 分模块推进,先用知识图谱做标本
- [引导问题预写=非纯RAG] 面试官可能质疑 → 定位明确"预写保证可控、检索证明能力",自由问题走源文档池纯RAG
- [流式 usage 兼容性] 个别模型/接口不返回 usage → 降级为 tokenizer 估算 + 标注"估算"
- [多版本矛盾残留] 完善文档向代码事实对齐,冲突以代码为准
- [答案一致性] 跨页回答可能引用矛盾段落 → 完善文档第3/6节统一口径,prompt 强制按页引用

### Open Questions:开放问题

> 检索摘要：落地前还有哪些待决策？完善文档产出方式（纯人工vs LLM辅助起草+人工审核）、评估集20条Q&A是否纳入本轮、索引层每页问题清单的最终内容

- 完善文档的产出方式:纯人工 vs LLM 辅助起草 + 人工审核(建议后者,我基于已读文档起草)。
- 评估集 20 条 Q&A 是否纳入本轮(建议纳入,用于命中率演示)。
- 索引层每页问题清单的最终内容(落地时随完善文档一起产出)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§Risks/Trade-offs/§Open Questions）
