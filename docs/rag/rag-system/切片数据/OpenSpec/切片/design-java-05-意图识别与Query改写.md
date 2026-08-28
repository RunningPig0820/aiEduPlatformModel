# 意图识别与Query改写

> summary: 意图识别与Query改写（design-java-rag-project-intro-assistant）：intent LLM结构化+关键词兜底、anchor/locked_sections两层锚定、switch收敛下一轮、clarify歧义澄清、问候识别、rewrite事件透传
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-05-意图识别与Query改写.md
> 类别：架构设计

---

### D2. 意图识别用 LLM 结构化输出 + 规则兜底,输出 `{anchor, category, switch_detected, ambiguous, candidates}`

> 检索摘要：意图识别用LLM结构化输出+关键词兜底：anchor模块级选语料池、locked_sections节级加权，输出ambiguous/candidates供clarify，失败回退关键词锚定

intent 为每轮开头的**非流式**调用(快模型、0 温度、关思考),输出闭集元数据。失败/超时/非闭集 → 回退关键词锚定(复用 `_fallback_anchor` + `ANCHOR_RULES`),degraded 标记走 200。
- **两层锚定(Python 侧校准确认)**:`anchor` 是**模块级**(路由层,决定从哪个语料池召回);`locked_sections`(节级,既有语义,如 04-安全/07-流式)保留为**加权层**(池内 authority × 节锚定精化)。两层并存、不是替换:orchestrate 的节级锚定加权**逻辑不改**,只新增 recall 前置"按 anchor 选语料池"(corpus 参数)。anchor 明确 → 单池召回 + 池内节加权;anchor 缺失/ambiguous → 维持现状(跨池或先 clarify)。
- **candidates(歧义候选模块)**:`ambiguous=true` 时 LLM 直接输出候选模块闭集(2~4 个,主源);LLM 未给/给 <2 → 取会话最近 N 轮锚过的模块去重填充(兜底);仍 <2 → 不触发 clarify,走默认 current_project。为 clarify 判定(D5)提供确定性输入。
- **为什么**:白盒展示"语义分析"必须真实发生;LLM 判意图类别(复用 `_CLASSIFY_SYSTEM` 的闭集分类)+ 关键词兜底 = 语义与成本平衡。接口返回结构固定(`{locked_sections, strategy}` → 扩展为 `{anchor, category, switch, ambiguous, candidates, lockedSections}`),检索/生成只消费结果。
- **备选**:纯规则 → 零成本但"语义分析"是假的,白盒露怯;纯 LLM 无兜底 → 挂了链路全断。

### D3. 切换判定收敛在下一轮 intent,服务端不做生成中切换

> 检索摘要：切换判定收敛下一轮intent不做生成中切换：switch_detected发事件重置上下文，不掐在途流避免半截token白烧，tutoring换题判定收敛Java教训同构

`switch_detected = (前端 current_project ≠ 会话已锚定 project) 或 (问题明确指向另一有语料模块)`。检测到 → 发 `switch` 事件 + 重置上下文(锚点/召回/轮次计数),走新锚点 rewrite→recall→generate。**不掐断任何在途流**——在途流要么完成、要么被 is_disconnected 取消。
- **为什么**:生成中切换 = ①中止上游 doubao HTTP 流(不可靠)②半截 token 已计费 ③前端打断渲染,三重代价,且学生真实动作只有"等完再问"或"关 fetch 再问"。tutoring 换题判定收敛 Java 的教训(换题判定在 Python decide、Java 只认 switch 事件)同构。
- **备选**:生成中服务端掐流 → 复杂 + 烧钱 + 打断感,弃(用户确认)。

### D5. clarify 澄清轮:歧义才问,默认当前功能,最多一轮

> 检索摘要：clarify澄清轮：歧义ambiguous且candidates≥2才问，固定话术0token最多一轮，默认当前功能，点选候选chip重发原问题+current_project=点选模块

`ambiguous=true` 且 `candidates ≥ 2`(多候选功能)→ 发 `event: clarify`(固定话术模板 + candidates + default),**0 token 生成、不计答案轮次、写 history**。学生下一条重跑 intent;仍模糊("就那个嘛")→ 不再 clarify,直接默认当前功能继续。`default` 绑定源优先级:前端 `current_project` > 会话最后成功锚定功能。
- **候选判定输入(Python 侧校准确认)**:`candidates` 来源 = ① intent LLM 结构化输出直接给出(`ambiguous=true` 时输出候选模块闭集 2~4 个,主源,能"读懂"问题里的功能指代)→ ② LLM 未给/给 <2 → 会话最近 N 轮锚过的模块去重填充(兜底)→ ③ 仍 <2 → 不触发 clarify,直接走默认。`candidates` 是**模块级**(非节级),与 D2 的模块 anchor 同一闭集。
- **点选交互定稿(前端校准确认)**:学生点选候选 chip 后,前端**重发原问题 + `current_project=点选模块`**(非发裸功能名)——复用"每次带 current_project 锚点"机制,intent 以 `current_project` 为**权威消歧锚点**直接锚定(不依赖 LLM 从功能名猜),原问保留供改写/召回;点选模块与会话锚点不同 → `switch` 事件照常触发(前端可提示"已切换至 X")。
- **为什么**:低摩擦引导(单一候选直接走不问),防死循环(最多一轮),降本(写死话术)。spec 第 6 条"题型引导"的歧义场景正是"切换功能后问'这个功能怎么流转'"。
- **备选**:不问直接默认 → 答错功能体验更差;无限追问 → 死循环。

### D-E. 问候识别与欢迎引导(2026-08-25 产品校准)

> 检索摘要：问候识别：你好/Hi归category问候不触发clarify，走欢迎引导固定话术+引导建议指向四大方向，0生成token；clarify仅用于功能指代不明

intent SHALL 识别"问候/寒暄"(如"你好/Hi/在吗")为 `category="问候"`、`ambiguous=false`——**不触发 clarify**(clarify 仅用于功能指代不明:ambiguous+candidates≥2,**不用于问候语**,实联调发现"你好"被误判 ambiguous 弹澄清很怪)。问候语 SHALL 走**欢迎引导路径**:不 recall 不 generate(省 token),直接返回**固定欢迎话术 + 引导建议**(指向 ①项目介绍②操作③数据关联④难点,复用 guide 静态池,0 生成 token)。

### Requirement: Query 改写透传（rewrite 事件字段）

> 检索摘要：rewrite事件透传{originalQuestion,rewrittenQuery}，前端展示"原始问题/改写后问题"对比，改写基于原问题+锚点+历史上下文

目标 D2~D3 已定义 rewrite 在链路中的位置与"走新锚点 rewrite→recall→generate",但未定义 rewrite 事件的负载字段。本块独有:系统 SHALL 基于原始问题与当前上下文(锚点、历史)生成改写后检索式 query,并在 `rewrite` 事件中透传 `{originalQuestion, rewrittenQuery}` 供前端展示。
- **Scenario 改写展示**:WHEN 学生问题含口语化表达 → THEN `rewrite` 事件返回改写后检索式,前端展示"原始问题 / 改写后问题"对比。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D2/D3/D5/D-E/§补充 pipeline-Query改写透传）
