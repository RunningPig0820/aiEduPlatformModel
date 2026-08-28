# 演进与未来

> summary: 演进与未来（design-java-rag-project-intro-assistant）：Non-Goals边界、交付编排M1-M8里程碑纵向切片（SSE契约M2冻结）、迁移计划Python先行泛化query.py+Java网关RagAssistantController
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-18-演进与未来.md
> 类别：未来演进

---

### Non-Goals

> 检索摘要：RAG助手明确不做：生成中切换、教育内容检索、图谱Neo4j召回、mermaid动态生成、前端实现与生产级鉴权，仅定后端契约与SSE事件

**Non-Goals:**
- **不做生成中切换**:切换只发生在下一轮 intent(`switch_detected`),生成中前端断开只走 `is_disconnected()` 取消,不做服务端主动掐流(半截 token 白烧 + 上游取消不可靠)。
- **不做教育内容检索**(知识点/题库/答疑学科题)——语料是本项目方案文档,不是教育数据。
- **不做图谱检索召回**(不接 Neo4j)——召回对象是文档(向量+BM25)。
- **不接真实权限体系扩展**——本期仅学生角色,非学生固定 403。
- **不实现 mermaid 动态生成**——本期不做流程图预置/渲染(前端另立变更,可后续补)。
- **不实现前端**——仅定后端契约与 SSE 事件格式。
- **不做生产级部署与鉴权扩展**——沿用 `x-internal-token` 内部调用。

### 交付编排(M1-M8 里程碑纵向切片)

> 检索摘要：交付编排M1-M8里程碑纵向切片，每里程碑=纵向切片+三端对接测试，桩替策略使整轮可通，SSE契约M2冻结下游只补字段

**M1-M8 里程碑纵向切片**:每个里程碑 = 纵向切片 + 前后端+模型端**三端对接测试**(完成即联调,问题早暴露)。M 编号即构建顺序,依赖单向(M(n) 只依赖 ≤M(n-1) 产出)。

**桩替策略**:上游未完成阶段先返回固定占位(M2/M3 的 generate 桩替),使整轮可通、前端不被下游阻塞;M4 起移除桩替接真实。

**完成标准**:每里程碑完成 = **前端可见物** + **对接测试用例全绿**(见 test.md 里程碑门禁映射表 2A)。

**对接节奏**:每里程碑后端+Python 合并该切片 → 前端对接该切片可见物 → 跑该里程碑门禁用例全绿才进入下一步。**SSE 契约 M2 冻结,下游只补字段不重排**。

**原 7 项清单归属**:权限判断→M1、意图分析→M2(+改写/switch/SSE骨架)、多路召回+remark打分+边界→M3、生成+token展示→M4、自我检查→M5、问题提示→M6、会话收尾→M7;缺口(rewrite/clarify/范围门/switch/close+累计token/补查/超时断连/SSE骨架/评估/问候欢迎)均落到对应里程碑。

### Migration Plan

> 检索摘要：迁移落地：Python先行泛化query.py白盒链路新增ask SSE端点，Java网关RagAssistantController角色门+SSE中继，前端另立变更，语料无迁移

1. **Python 先行**(Model 仓库,对应其 `rag-project-intro-assistant-python` 变更):泛化 `core/rag/query.py` 为白盒链路(intent/rewrite/recall/rerank/generate + clarify/is_quoted/分层超时/suggestions),新增 `/api/rag/assistant/ask` SSE 端点,扩评估集。**不影响既有 `/api/tutoring/rag/query`**(独立路由)。
2. **Java 网关**:新增 `RagAssistantController`(角色门 + SSE 中继 + trace_id),复用 `LlmGateway` internalToken 调用。回滚 = 摘除路由,不影响 tutoring。
3. **前端**(另立变更):学生侧 RAG 助手页消费白盒事件。
4. **数据**:AI答疑语料保持现状;其它模块语料后续入库即自动放行,无迁移。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§Non-Goals/§交付编排/§Migration Plan）
