# tutoring-subject-gate-python 技术设计

## Context

- **后端契约(已冻结)**:`POST /api/tutoring/subject-classify`,请求 `{content, image_url}`(至少一个非空),响应 `{"subject": "..."}`;失败/异常 → 空结果,Java 按 math 放行。不对前端开放,仅 Java 桥调用。
- **subject 闭集(K12 十值,2026-08 扩)**:`math`/`physics`/`chemistry`/`biology`/`chinese`/`english`/`politics`/`geography`/`history`/`other`。本期 Java 只放行 math,其余跳过;显式枚举便于记录真实学科 + 后续分学科答疑。⚠️ **后端 DTO 需同步扩**(Java 严格枚举反序列化遇 chinese 等新值会报错,见 Risks)。
- **现有成熟模式**:question_understand / vector 均为 stateless 小端点(不碰 MySQL/KG),Java 经桥调用。subject-classify 完全复用该模式。
- **模型现状**:decide(`TUTORING_DECIDE_MODEL`)与 question_understand(`_UNDERSTAND_MODEL`)均为 `doubao-seed-2-0-mini-260428` / temp 0.3 —— 三个统一模型现状已满足两个,subject-classify 沿用。
- **关键已知**:doubao mini **默认开思考**(先写草稿再答),question_understand 曾因未关思考导致 32s+ 卡顿(2026-08-19 已修复:关思考 + 20s 超时 + 关 SDK 重试)。subject-classify 同为 stateless 快调用,**必须照搬该修复**,否则学科门变成 30s+ 卡点。

## Goals / Non-Goals

**Goals:**
- 学科无关小分类器:只判学科,不做任何解题。
- 文本 + 图片双通道(无图纯文本 / 有图多模态)。
- 闭集 subject(5 值);失败/超时/非法输出 → 空 subject(Java 放行)。
- 模型统一 doubao mini / 0.3;关思考 + 20s 内部超时 + 关 SDK 重试。
- 绝不抛异常(stateless 端点模式)。

**Non-Goals(本期):**
- 多学科答疑提示词(Java 侧本期只放行 math,Python 只做分类不做学科解题)。
- subject 高精度调优(后端 RisK:误判治理后续做)。
- analyze-question 题型分析的学科过滤(后端明确不涉及)。

## Decisions

### 1. 端点结构 = question_understand 同构(stateless,绝不抛异常)

```
POST /api/tutoring/subject-classify        (api/tutoring.py, verify_internal_token)
  → core/tutoring/subject_classify.classify_subject(request, llm=None)
      → LLMFactory.create("doubao", _CLASSIFY_MODEL, temperature=0.3,
                          extra_body={"thinking":{"type":"disabled"}},
                          request_timeout=20, max_retries=0)
      → HumanMessage 文本 或 多模态(text+image_url)
      → 解析 subject,校验闭集
      → 任何异常 → SubjectClassifyResponse(subject=None)
```

与 question_understand 完全同构:模型写死 doubao、`llm` 参数注入测试、try/except 兜底空结果、`logger` 记录失败。**照搬其慢修复参数**(thinking off / timeout / retry 0)——这是本次实现不可省略的一环。

### 2. 请求/响应模型(models/tutoring.py)

```
class SubjectType(str, Enum):  # 闭集,Python 侧权威
    MATH="math" PHYSICS="physics" CHEMISTRY="chemistry" BIOLOGY="biology" OTHER="other"

class SubjectClassifyRequest(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None
    # validator: content 与 image_url 至少一个非空(全空 → 422)

class SubjectClassifyResponse(BaseModel):
    subject: Optional[str] = None   # 闭集之一;失败/非法 → None(Java 按 math 放行)
```

**subject 用 `Optional[str]` 而非 `Optional[SubjectType]`**:非法输出(模型吐了闭集外学科,如 "geography")在 Python 侧归一化为 `None`,不让 Pydantic 抛枚举校验异常。语义:非法 = 拿不到结果 = 放行(漏拦方向,安全)。

### 3. 学科无关提示词(后端 Open Question 由 Python 定稿)

```
你是"学科识别器"。只判断一道题属于哪个学科，不解答题目。
只能输出一个学科：math / physics / chemistry / biology / other。

判定规则（宁可不误拦）：
- 明确数学题（代数/几何/方程/应用题/计数等）→ math
- 明确物理/化学/生物题 → 对应学科
- 图片无法辨认、内容不是学科题、或不属于以上任一学科 → other
- 拿不准该不该算数学、在 math 与其他学科之间犹豫 → 输出 math（宁可放过，不可把数学题误判成别的学科）
```

**误拦最小化的落地**:`other` 只在"确信不是 math"时用(图片无法辨认/明确非学科);拿不准 → `math` 放行。这样数学题几乎不可能被判成 physics/chemistry/biology 被 Java 拦掉(误拦),非数学题最多被漏拦(回到现状,可清洗)。

### 4. 失败/非法 → 空 subject(Java 放行),而非 other

| 情况 | 输出 | Java 行为 | 方向 |
|------|------|-----------|------|
| 明确任一非 math 学科(物理/化学/生物/语文/英语/政治/地理/历史) | 对应学科 | 跳过「仅支持数学」 | 正确 |
| 明确数学 | math | 放行走 decide | 正确 |
| 图片无法辨认/非学科 | other | 跳过 | 正确 |
| 拿不准 math vs 其他 | math | 放行 | 漏拦(安全) |
| LLM 异常/超时 | None | 按 math 放行 | 漏拦(安全) |
| 输出闭集外学科 | None | 按 math 放行 | 漏拦(安全) |

### 5. 与 decide 的边界(不复用、不侵入)

subject-classify **独立于 decide**,不改 `_DECIDE_SYSTEM`、不改 decide/generate 调用链。学科判定在 Java 侧完成分流,Python 只提供分类能力。多学科提示词是 Java 本期 Non-Goal,Python 同理不预埋。

## Risks / Trade-offs

- [subject 模型输出不稳定(偶发闭集外/中文)] → 归一化:闭集外 → None(放行),中文学科名在提示词禁止;后续可加映射表。
- [分类器误判 math→other(误拦)] → 提示词明确"拿不准→math";失败走 None 而非 other;后端 RisK 已有清洗预案。
- [⚠️ 后端 DTO 未同步扩 K12 十值] → Java 若用严格 5 值枚举反序列化,收到 `chinese` 等新值会报错→降级放行→语文题被当数学答疑(数据污染)。**回执必须要求后端扩枚举或用宽容 String**(只把 math 当特判)。
- [多一次 LLM 调用延迟] → 轻量单 token 分类,关思考后预计秒级(question_understand 实测 1.2s);Java 侧超时兜底。
- [模型未统一(若有人改了 decide 模型)] → 本端点硬编码 `_CLASSIFY_MODEL`,与 decide/understand 配置解耦;统一靠约定 + 测试锁定。

## Migration Plan

1. 实现 subject-classify(模型 + core + 路由 + 单测)。
2. 单测全绿(PSC-001~005 对齐后端 test.md)。
3. Java 侧联调(后端任务 2.x 完成时,见后端 change)。
4. 回滚:Python 端点可独立撤除,不影响 decide/generate(Java 分流回退到无条件建会话)。

## Open Questions

- **subject 取值闭集是否够**:后端契约已冻结 5 值,后续扩学科 Java/Python 同步扩枚举即可。
- **提示词语气**:误拦最小化措辞(拿不准→math)已定稿,可在联调后按误判率微调。
- **是否需要 `reason` 字段**(模型给出 subject 的依据,便于排查误判):本期不加(后端契约无),如联调需要可后补。
