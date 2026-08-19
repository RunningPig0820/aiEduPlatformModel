# tutoring-subject-classify 能力规格

AI 答疑学科门的前置分类能力（Python stateless 端点）：学科无关小分类器，在 decide 之前判定题目学科（文本 + 图片），支撑 Java 侧非数学题跳过。失败/异常 → 空 subject，Java 按 math 放行。

## ADDED Requirements

### Requirement: subject-classify 端点契约

`POST /api/tutoring/subject-classify` SHALL 接收「`content`（题目文本）与 `image_url`（题目图片 URL）至少一个非空」，返回 `{"subject": ...}`，subject 为闭集之一（K12 九门 + other）：`math` / `physics` / `chemistry` / `biology` / `chinese` / `english` / `politics` / `geography` / `history` / `other`。字段 snake_case，与 tutoring 端点家族一致。

#### Scenario: 正常文本分类
- **WHEN** 请求携带 `{"content": "自由落体运动…", "image_url": null}`
- **THEN** 返回 HTTP 200 `{"subject": "physics"}`

#### Scenario: 正常图片分类
- **WHEN** 请求携带 `{"content": null, "image_url": "https://cos/…"}`（受力分析图）
- **THEN** 走多模态通道返回 HTTP 200，subject 为对应学科

#### Scenario: K12 学科全覆盖
- **WHEN** 输入任一 K12 学科题目（语文/英语/政治/地理/历史等）
- **THEN** 返回对应显式学科值（`chinese`/`english`/`politics`/`geography`/`history`），不归并进 `other`

#### Scenario: 全空参数
- **WHEN** `content` 与 `image_url` 均为空/缺失
- **THEN** 返回 HTTP 422 参数校验错误

### Requirement: 学科无关分类（不解题）

分类器提示词 SHALL 学科无关，只判断学科、不做任何解题。明确数学题 → `math`；明确任一 K12 学科（物理/化学/生物/语文/英语/政治/地理/历史）→ 对应学科；图片无法辨认 / 内容非学科 / 不属于任一学科 → `other`。**拿不准是否数学时 SHALL 偏向 `math`（宁可不误拦）**。

#### Scenario: 明确数学题
- **WHEN** content 为「鸡兔同笼，共35头94脚，各几只？」
- **THEN** 返回 `{"subject": "math"}`

#### Scenario: 明确物理题
- **WHEN** content 为「物体做自由落体运动，求落地速度」
- **THEN** 返回 `{"subject": "physics"}`

#### Scenario: 明确语文/英语题
- **WHEN** content 为语文或英语阅读理解/作文/语法题
- **THEN** 返回 `{"subject": "chinese"}` 或 `{"subject": "english"}`

#### Scenario: 拿不准偏向 math
- **WHEN** 内容在数学与其他学科之间含糊（模型无法确定）
- **THEN** 优先输出 `math`，不将数学题误判成其它学科

#### Scenario: 图片无法辨认
- **WHEN** 图片模糊/无法辨认内容
- **THEN** 返回 `{"subject": "other"}`

### Requirement: 文本 + 图片双通道

无图时 SHALL 走纯文本 HumanMessage；有图时 SHALL 走多模态（`HumanMessage([{text},{image_url}])`，复用 decide 看图同路径），真实图进模型。

#### Scenario: 无图纯文本
- **WHEN** 请求仅携带 `content`，无 `image_url`
- **THEN** HumanMessage 为纯文本，分类正确

#### Scenario: 有图多模态
- **WHEN** 请求携带 `image_url`（图片题目）
- **THEN** HumanMessage 含 text + image_url 两个 part，模型结合图内容分类

### Requirement: 模型统一与慢修复

subject-classify SHALL 使用 `doubao-seed-2-0-mini-260428` / temp 0.3（与 decide / question_understand 同款），并 SHALL 显式关思考（`extra_body={"thinking": {"type": "disabled"}}`）+ `request_timeout`（20s）+ `max_retries=0`（沿用 question_understand 慢修复，避免 doubao 开思考 50~145s 卡顿）。

#### Scenario: 模型参数统一
- **WHEN** 调用 classify 且未注入 llm
- **THEN** 通过 LLMFactory 构造 doubao mini / 0.3，携带 thinking disabled + 20s 超时 + 关重试

### Requirement: 失败绝不抛异常

任何异常（LLM 失败 / 超时 / 解析失败 / 输出闭集外学科）SHALL 返回空结果（HTTP 200，subject 为空），不抛 5xx。空 subject 由 Java 按 math 放行（不阻断答疑，宁可漏拦不误拦）。

#### Scenario: LLM 异常
- **WHEN** 底层 LLM 调用抛异常
- **THEN** 返回 HTTP 200 `{"subject": null}`（或等价空结果），不抛错

#### Scenario: 输出闭集外学科
- **WHEN** 模型输出闭集外学科（如 "geology"/"astronomy"，非 K12 十值）
- **THEN** 归一化为空 subject，不报错、不误判为 other

### Requirement: 内部鉴权

端点 SHALL 与 tutoring 端点家族一致，要求 `x-internal-token` 头与 `settings.INTERNAL_TOKEN` 匹配，否则返回 403。

#### Scenario: 缺 token
- **WHEN** 请求未携带 `x-internal-token`
- **THEN** 返回 403

#### Scenario: 非法 token
- **WHEN** `x-internal-token` 与 `settings.INTERNAL_TOKEN` 不匹配
- **THEN** 返回 403
