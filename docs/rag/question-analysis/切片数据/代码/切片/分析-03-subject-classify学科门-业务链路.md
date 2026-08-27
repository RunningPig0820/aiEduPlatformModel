# 分析-03-subject-classify学科门-业务链路

> summary: subject-classify学科门业务链路
> 来源: 切片 ｜ 锚点: 业务链路
> 节: 分析-03-subject-classify学科门
> COS路径: rag-slices/question-analysis/代码/分析-03-subject-classify学科门-业务链路.md
> 类别：业务流程
> target: 开发对账

---

## 业务描述与业务场景

**业务描述**：答疑系统只服务数学。学生可能发语文/英语/闲聊，或拍一张模糊的题图——系统需要在进入 AI 决策前先筛掉非数学内容，同时确保数学题永远不被误拦。

**业务场景**：
1. 学生发第一句消息或换新题时，Java 先调学科判断：数学题才建/续会话，非数学（语文/英语/闲聊）直接回「仅支持数学」，不浪费 AI 调用。
2. 图片模糊、拿不准时系统宁可放行当作数学题——数学题被误拦是对学生更糟的事故。
3. 判定失败/超时（AI 不可用）时返回"不知道"，Java 也按数学放行，保证答疑不被卡住。

## 职责

decide 之前的**前置学科判定**，只判学科不解题。"宁可放过，不可把数学题误判成别的学科"；拿不准 → math；图片无法辨认/非学科 → other。

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

**文字链路复述**：Java 在发起/换题触发点调 `POST /api/tutoring/subject-classify` → `classify_subject` 先做请求校验（content/image_url 至少一个非空，都空则 422 Pydantic 校验失败）→ 合法则走写死的 doubao 闭集模型（temp0.3/关思考/20s 超时/重试0）→ 解析命中闭集返回 subject=math/physics/...，无法辨认或非学科题返回 other，异常/超时/闭集外返回 None → Java 分流：非 math 跳过不建会不落库；math 放行走进 decide；other 也跳过；None 按 math 放行（宁可漏拦不误拦）。

> 证据：详见 `3.代码/分析-03-subject-classify学科门.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）
