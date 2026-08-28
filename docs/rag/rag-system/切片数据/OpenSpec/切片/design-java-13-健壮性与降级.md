# 健壮性与降级

> summary: 健壮性与降级（design-java-rag-project-intro-assistant）：分层超时（召回各2s/生成8s）、is_disconnected断连取消中止上游doubao、降级话术写死0token
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-13-健壮性与降级.md
> 类别：开发难点

---

### D7. 分层超时 + 断连取消,降级话术写死

> 检索摘要：分层超时：召回向量/Bm25各2s降级纯另一路，生成8s超时返回召回清单+固定话术，is_disconnected断连中止上游doubao流

- 召回层:向量/Bm25 单路各 2s 硬超时,超时 → 降级为纯另一路(`{hits:[], confidence:0}` 冒泡捕获,复用既有语义)。
- 生成层:8s 硬超时 → **不走 LLM**,直接返回召回清单 + 固定话术"我找到了以下相关资料,但生成完整答案超时了,您可以直接点击查看原文:块1、块2、块3"。
- 断连:SSE 生成循环监听 `request.is_disconnected()`,断开 → 中止上游 doubao 流。
- **为什么**:分层超时是工程底线(spec 第 7 条);超时降级话术写死成本 0,且用户拿到原始资料体验正向(非报错)。
- **备选**:统一 20s 超时 → 学生等待过久;生成超时也调 LLM 重试 → 重复花钱。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D7. 分层超时 + 断连取消）
