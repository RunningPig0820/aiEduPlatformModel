# design-python-ai-tutoring

> summary: 解决从单次调用升级为LangGraph多步agent的演进问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 12. 演进:L0 单次调用 → 阶段 2 LangGraph
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-12-演进-L0-单次调用-阶段-2-LangGraph.md
> 类别：未来演进

---

### 12. 演进:L0 单次调用 → 阶段 2 LangGraph

MVP = L0 单次调用(decide/generate 各一次 LLM)。阶段 2 升级 L1/L2 LangGraph 多步 agent(工具:查薄弱点/出变式题/错题集,工具 = Java 内部接口),契约(ActionMeta)不变,Java 编排不变。**迁移成本低的前提**: ①ActionMeta 契约可扩展(字段可加);②工具 API 早定形状;③Python 模块拆干净(decider/generator/structured 分离)。
