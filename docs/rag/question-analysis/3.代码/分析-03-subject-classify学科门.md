# 分析-03 subject-classify 学科门（代码真相）

> summary: 解答「怎么判断题目是不是数学题 / 学科门怎么防误判」——K12 十值闭集 + 宁漏不误（None 放行）+ 关思考慢修复超时降级。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-source/question-analysis/代码/分析-03-subject-classify学科门.md
> 类别：操作流程

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

## 代码事实

- **K12 十值闭集**：`SubjectType(math/physics/chemistry/biology/chinese/english/politics/geography/history/other)`。（`models/tutoring.py:182-197`）
- **输出结构**：`SubjectClassifyRequest(content?, image_url?)`；`SubjectClassifyResponse(subject: Optional[str])`。（`models/tutoring.py:200-220`）
- **模型/参数写死**：doubao-seed-2-0-mini-260428、temp 0.3、**关思考** + `request_timeout=20` + `max_retries=0`。（`core/tutoring/subject_classify.py:24-26,66-73`）
- **解析宽容**：`_parse_subject` 大小写/前后空白/多余文字（"答案:math"）都能命中；**闭集外 → None 而非 other**。（`subject_classify.py:45-55`）
- **绝不抛异常**：整个函数 try/except 包裹，LLM 失败/超时返回空 subject。（`subject_classify.py:65-87`）
- **0 请求校验**：`@model_validator` 校验 content/image_url 至少一个非空，否则 422。（`models/tutoring.py:205-209`）

### 枚举/常量/配置

| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 枚举 | SubjectType | math/physics/chemistry/biology/chinese/english/politics/geography/history/other | `models/tutoring.py:182-197` |
| 配置 | 模型 | doubao-seed-2-0-mini-260428 | `subject_classify.py:24-26` |
| 配置 | 温度 | 0.3 | `subject_classify.py:26` |
| 配置 | 思考 | 关（thinking disabled） | `subject_classify.py:70` |
| 配置 | 超时 | 20s | `subject_classify.py:71` |
| 配置 | 重试 | 0（关 SDK 重试） | `subject_classify.py:72` |

## 隐性坑与注意事项

- **闭集外 → None 不是 other**：other = "明确非学科内容"，None = "不知道"，语义分开（`subject_classify.py:48-55`）。
- **图片路径**：image_url 存在时发多模态消息，纯文本走 text。（`subject_classify.py:75-81`）
- **慢修复**：开思考实测 50~145s、关思考秒出——学科门不能成为新卡点，别调高超时。（`subject_classify.py:68-69` 注释）
- **Java 触发点**：发起/换题两个点各判一次（`api/tutoring.py:136-149` 注释）。

## 设计要点

- **宁漏不误**：拿不准放行 math，数学题永远不会被拦在门外——误拦是更糟的产品事故。（`_SYSTEM_TEMPLATE` `subject_classify.py:39`）
- **闭集外不硬归类**：None（不是 other）对 Java 表示"不知道"，语义清晰。
- **慢修复原则**：学科门是前置卡点，必须秒出，20s 超时快速返回让 Java 降级。

## 对账要点

| 对账分类 | 项 | 语雀/design 口径 | 代码现状 | 结论 |
|---|---|---|---|---|
| 方案vs实现 | 学科闭集 | 早期闭集 5 值 | 完整 K12 十值 | ⚠️翻转（扩集） |
| 接口契约 | subject 返回 | `None`=失败放行 | `None`=闭集外/失败；other=明确非学科 | ✅落地 |
| 注释vs运行行为 | 失败语义 | 吞异常降级空 | try/except 全包裹返回空 subject | ✅落地 |

## 已读代码清单
- **Python**：`core/tutoring/subject_classify.py`（全）、`models/tutoring.py:182-221`、`api/tutoring.py:136-149`
- **Java**：`subject-gate`/`TutoringAppService` 编排点（参照，未逐行）
- **前端**：不涉及（本主题纯后端编排端点）