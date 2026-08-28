# 数据流转与存储

> summary: 数据流转与存储（design-java-rag-project-intro-assistant）：trace_id断线补查返回该轮完整结果、超窗返回"trace不存在"、Redis留存窗口
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-14-数据流转与存储.md
> 类别：数据关联

---

### Requirement: trace_id 生成与贯穿（断线补查返回字段与超窗语义）

> 检索摘要：断线凭trace_id补查返回该轮完整结果（answer/quotedKeys/tokensUsage/suggestions），超出保留窗口返回明确的"trace不存在"

目标 D8/D-B 已定义 trace_id 由 Java 生成透传 Python 并在 done 返回、permission 携带 trace_id。本块独有:WHEN 前端断线丢失结果凭 trace_id 查询 → THEN 系统返回该轮完整结果(`answer/quotedKeys/tokensUsage/suggestions`);**超出保留窗口 → 明确"trace 不存在"**(不静默返回空)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充 resilience-trace_id生成与贯穿）
