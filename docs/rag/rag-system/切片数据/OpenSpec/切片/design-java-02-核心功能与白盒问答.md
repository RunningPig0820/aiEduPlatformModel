# 核心功能与白盒问答

> summary: 核心功能与白盒问答（design-java-rag-project-intro-assistant）：白盒 SSE 全链路（权限→意图→改写→多路召回→RRF→生成）透传 + 事件序列冻结，一次完整问答的阶段展示与分支无流规则
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-02-核心功能与白盒问答.md
> 类别：操作流程

---

### Goals

> 检索摘要：白盒RAG助手目标全景：角色硬门仅STUDENT、模块全放行低置信过滤、clarify澄清一轮、is_quoted用LCS、分层超时、trace_id计费、引导与评估复用run_eval链

**Goals:**
- 白盒 RAG 链路:权限 → 意图 → 改写 → 多路召回 → RRF 重排 → 生成,全阶段 SSE 事件透传前端。
- 角色硬门:仅 STUDENT 放行,非学生/角色缺失 → 固定 403,不进 RAG 流程、0 token。
- 模块全放行 + 低置信度过滤:AI答疑/知识图谱/题型分析/RAG 四模块均可路由,无禁区硬拒答;查不到关联文档 → 范围门低置信度过滤(固定话术,付 recall 省 generate),唯一拒答路径为 `boundary`(reason=low_confidence)。
- clarify 澄清轮:歧义(多候选功能)→ 固定澄清话术 + 默认当前功能,最多一轮,不计答案轮次。
- 引用透明:仅回传 RRF 精排 Top-K 块(标题/摘要/file_path),`is_quoted` 用 LCS 硬匹配(8 中/12 英),非 LLM 自述,`done` 后补发。
- 健壮性:召回 2s / 生成 8s 分层超时,`is_disconnected()` 断连取消,超时降级话术写死(0 token)。
- 计费透明:tokens_usage `{prompt, completion, cache_hit, total}` + `trace_id`,供前端断线补查;会话累计 token(关闭对话时返回)。
- 显式关闭对话:学生可在对话中主动结束会话(中止在途流 + 会话置关闭 + 返回会话累计 token),区别于断连取消。
- 引导:完成后运行时 LLM 生成建议(1~3 条,向 ①项目介绍 ②操作 ③数据关联 ④难点 引导)。
- 评估复用:`run_eval.py` 链 + 新增 `边界拒答` 类型 + `precision_at_k` + is_quoted 校验 + baseline 报告白盒展示。

### Requirement: 白盒阶段事件序列（boundary 位置与分支无流规则）

> 检索摘要：白盒SSE事件固定顺序intent→(clarify|switch)→rewrite→rerank→(boundary)→token*→done，clarify/switch分支无rewrite/recall/generate，boundary分支无token流rerank可为空

目标 Risks 已冻结 `permission → intent → (clarify|switch) → rewrite → rerank → token → done` 时序,但未含 boundary 位置与分支无流规则。本块独有:系统 SHALL 按固定顺序产出 SSE 事件:`intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`;`clarify`/`switch` 分支**无 rewrite/recall/generate**,`boundary` 分支**无 token 流**(rerank 可为空)。
- **Scenario 正常流**:WHEN 链路完整 → THEN 事件顺序为 intent → rewrite → rerank → token* → done。
- **Scenario 早停分支**:WHEN 澄清或切换触发 → THEN 对应分支事件后直接 done,无 rewrite/rerank/token 流;WHEN 范围门低置信度触发 → THEN rerank(可为空)后 boundary 事件 + done,无 token 流。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§Goals / §补充 pipeline-白盒阶段事件序列）
