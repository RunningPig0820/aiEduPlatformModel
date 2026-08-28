# 健壮性与降级（断连取消与补查）
> summary: 健壮性与降级（断连取消与补查）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-resilience-13-健壮性与降级-2.md
> 类别：开发难点

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-resilience.md）按业务主题「健壮性与降级」重切合并（断连取消与补查部分，-2 子块）。
> ⚠️设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 ✅已落地 / ⚠️构想未实现 / ❓待决策 内容，引用需核对代码。

### Requirement: 断连取消
> 检索摘要：前端断开怎么取消生成——监听 is_disconnected 立即中止 doubao 流防空转？

系统 SHALL 在 SSE 生成循环监听 `request.is_disconnected()`；检测到前端断开 → 立即中止底层 doubao 流式请求，防后端空转烧钱。

#### Scenario: 前端断开中止流
- **WHEN** 前端在生成中途关闭连接
- **THEN** 检测 is_disconnected → 中止上游 doubao 流，停止消耗 token

#### Scenario: 正常完成
- **WHEN** 前端保持连接至生成完成
- **THEN** 正常输出 token 流至 done，不触发取消

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Requirement: 断连取消）

### Requirement: trace_id 断线补查
> 检索摘要：断线后怎么补查结果——凭 trace_id 查 turns 接口返回该轮 done 完整结果？

系统 SHALL 每轮生成 `trace_id`（Java 生成透传或 Python 生成，贯穿日志）；`GET /api/rag/assistant/turns/{traceId}` 返回该轮 done 结果（answer/quotedKeys/tokensUsage/suggestions/reason），供前端断线后补查。

#### Scenario: 断线补查
- **WHEN** 前端断线后凭 trace_id 补查
- **THEN** 返回该轮完整结果（若 trace 超保留窗口 → 10002）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-resilience.md`（§Requirement: trace_id 断线补查）
