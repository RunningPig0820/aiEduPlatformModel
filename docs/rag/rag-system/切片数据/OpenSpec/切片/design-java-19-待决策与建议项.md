# 待决策与建议项

> summary: 待决策与建议项（design-java-rag-project-intro-assistant）：Risks风险与对策（intent误判/is_quoted窗口/cache_hit估算/suggestions计费/语料缺失/上下文截断/SSE时序冻结）+ Open Questions待决策
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-19-待决策与建议项.md
> 类别：未来演进

---

### Risks / Trade-offs

> 检索摘要：RAG助手设计风险：意图误判规则兜底、is_quoted窗口可调、cache_hit估算、suggestions计费、语料缺失低置信、SSE时序冻结

- [intent LLM 偶发误判] → 规则兜底(`_fallback_anchor`)+ degraded 标记走 200;评估集 `边界拒答` 类型覆盖误判回归。
- [is_quoted 匹配 8 中字符过于严格/宽松] → 参数可调(`config/settings.py`);入评估校验 quoted_keys ⊆ 召回块;前端灰显/高亮兜底。
- [cache_hit_tokens 拿不到] → tokenizer 估算 + 标注"估算"(08-21 已留口子)。
- [运行时 suggestions 增加成本] → 计入本轮 usage 展示;LLM 失败静态池兜底;可配置开关关闭。
- [多模块语料缺失导致可答面窄] → 数据驱动,先 AI答疑;未来入库即自动放行,验收按"链路真实完整"讲。
- [跨项目问题(AI答疑页问知识图谱)在无语料模块下低置信过滤] → 明确为预期行为(范围门 low_confidence),评估集覆盖。
- [上下文窗口截断丢上下文] → 保留最近 3 轮 + 锚点由 session 独立携带,前端可见截断提示(如需)。
- [SSE 事件时序被前端依赖] → 冻结契约:`permission → intent → (clarify|switch) → rewrite → rerank → token → done`,不得重排/丢失(沿用 tutoring 阶段二契约冻结纪律)。
- [流式 usage 只在结尾返回] → done 才更新成本展示(面试/汇报可讲这个坑)。

### Open Questions

> 检索摘要：待决策OpenQuestion：intent类别闭集与locked_sections映射是否沿用CATEGORY_SECTIONS，cache_hit_tokens是否真由ark返回，会话不做断线恢复改最近3轮

- intent LLM 类别闭集与 `locked_sections` 的映射是否沿用现有 `CATEGORY_SECTIONS`(项目介绍/操作/难点/数据关联/最危险),还是针对学生场景重构(spec 提到 ①②③④ 四方向)——建议沿用闭集,前端引导语对应即可。
- `cache_hit_tokens` 是否真由 doubao/ark 返回——需实现期实测,取不到按"估算"。
- 会话:**不做断线恢复**(仅 trace_id 单轮补查,用户确认);**不设轮数上限**(用户确认轮数无意义),改为上下文窗口保留**最近 3 轮**(默认,可配)。窗口大小的最终值待定。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§Risks/Trade-offs/§Open Questions）
