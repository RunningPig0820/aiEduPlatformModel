# 分析-03-subject-classify学科门-代码事实

> summary: subject-classify学科门代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-03-subject-classify学科门
> COS路径: rag-slices/question-analysis/代码/分析-03-subject-classify学科门-代码事实.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

- **API 端点**：`POST /api/tutoring/subject-classify`，Java 编排发起/换题触发点调用（触发点注释见 `api/tutoring.py:136-149`）。
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

## 设计要点

- **宁漏不误**：拿不准放行 math，数学题永远不会被拦在门外——误拦是更糟的产品事故。（`_SYSTEM_TEMPLATE` `subject_classify.py:39`）
- **闭集外不硬归类**：None（不是 other）对 Java 表示"不知道"，语义清晰。
- **慢修复原则**：学科门是前置卡点，必须秒出，20s 超时快速返回让 Java 降级。

> 证据：详见 `3.代码/分析-03-subject-classify学科门.md`（§代码事实 / §设计要点）
