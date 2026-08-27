# 分析-03-subject-classify学科门

> summary: (无 summary)
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 高层业务调用链（学科门判定）
> 模块: question-analysis ｜ 节: 分析-03-subject-classify学科门

---

## 高层业务调用链（学科门判定）

```mermaid
flowchart TD
    JAVA[Java 编排 发起/换题触发点] -->|POST /api/tutoring/subject-classify| SC[classify_subject]
    SC -->|@1 请求校验| REQ{content/image_url 至少一个非空}
    REQ -->|都空| VERR[422 Pydantic 校验失败]
    REQ -->|合法| LLM[写死 doubao 闭集模型<br/>temp0.3 关思考 20s 超时 重试0]
    LLM -->|解析命中闭集| HIT[subject=math/physics/...]
    LLM -->|无法辨认/非学科题| OTHER[subject=other]
    LLM -->|异常/超时/闭集外| NONE[subject=None]
    HIT -->|非 math| JSKIP[Java 跳过 不建会不落库]
    HIT -->|math| JPASS[Java 放行 走进 decide]
    OTHER --> JS2[Java 跳过]
    NONE --> JPASS2[Java 按 math 放行 宁可漏拦不误拦]
```
