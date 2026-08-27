# 分析-02-微服务分工

> summary: (无 summary)
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 高层业务调用链（前端→Java 编排→Python 六端点）
> 模块: question-analysis ｜ 节: 分析-02-微服务分工

---

## 高层业务调用链（前端→Java 编排→Python 六端点）

```mermaid
flowchart TD
    FE[前端 AiQa.jsx] -->|start/send/requestAnswer| JAVA[Java TutoringAppService 编排]
    JAVA -->|① 学科门 decide 前| SC[POST /api/tutoring/subject-classify 同步JSON]
    SC -->|空 subject / 非 math| SKIP[跳过: 不建/不续会话 不落库]
    SC -->|math| ENSURE[ensureCreateAllowed 频率限制]
    JAVA -->|图片题| QU[POST /api/tutoring/question-understand 同步JSON]
    QU -->|空 topic_labels| PENDING[Java 降级 PENDING 挂起]
    ENSURE -->|每轮| DECIDE[POST /api/tutoring/decide 流式SSE]
    DECIDE -->|meta ActionMeta| GUARD[Java 护栏审批 type]
    DECIDE -.流中段失败.-> ERR[event:error 流终止 Java 不可重试]
    QU -->|topic_labels| JAVA
    GUARD -->|放行| GEN[POST /api/tutoring/generate 流式SSE]
    GEN -.失败.-> ERR
    GEN -->|token 流| FE
    JAVA -->|题型名归一| V[POST /api/tutoring/vector/put|query 同步JSON]
    V -.失败 HTTP 400/500.-> FALLBACK[Java 桥降级: 回退字符规则 + 原样落库]
```
