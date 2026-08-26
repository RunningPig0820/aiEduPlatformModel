# 分析-03 subject-classify 学科门（代码真相）

> 来源：ai-edu-ai-service 深读（2026-08-26）｜权威度 0.8 ｜ 模块=question-analysis

## 职责

decide 之前的前置判定，**只判学科不解题**。"宁可放过，不可把数学题误判成别的学科"；拿不准 → 输出 math；图片无法辨认/非学科 → other。

## 代码事实

- **K12 十值闭集**：`math / physics / chemistry / biology / chinese / english / politics / geography / history / other`。（`models/tutoring.py:182-197` SubjectType；测试逐值断言 `tests/tutoring/unit/test_subject_classify.py:52-57`）
- **输出结构**：`SubjectClassifyResponse(subject: Optional[str])`；失败/超时/闭集外 → `None`（Java 按 math 放行，宁漏拦不误拦）。（`models/tutoring.py:212-220`、`core/tutoring/subject_classify.py:85-87`）
- **模型参数**：写死 doubao `doubao-seed-2-0-mini-260428`、temp 0.3、**关思考（thinking disabled）+ 20s 超时 + 关 SDK 重试**。（`subject_classify.py:24-26,66-73`）
- **解析宽容**：`_parse_subject` 大小写/前后空白/多余文字（"答案:math"）都能命中，但**闭集外 → None 而非 other**（防把地质/天文误判成 other）。（`subject_classify.py:45-55`）
- **绝不抛异常**：整个函数 try/except 包裹，LLM 异常返回空 subject。（`subject_classify.py:65-87`）
- **链路位置**：decide 之前（模块 docstring 第 2 行）；Java 在发起/换题两个触发点各判一次。（`api/tutoring.py:136-149`）

## 设计要点

- **闭集外不硬归类**：None（不是 other）——other 是"明确非学科内容"，闭集外是"不知道"，语义必须分开。
- **慢修复原则**：开思考实测 50~145s、关思考秒出——学科门不能成为新卡点。
- **宁漏不误**：拿不准放行 math，数学题永远不会被拦在门外（误拦是更糟的产品事故）。
