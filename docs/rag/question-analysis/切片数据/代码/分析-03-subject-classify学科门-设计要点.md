# 分析-03-subject-classify学科门

> summary: (无 summary)
> 权威度: 0.8 ｜ 来源: 代码 ｜ 锚点: 设计要点
> 模块: question-analysis ｜ 节: 分析-03-subject-classify学科门

---

## 设计要点

- **宁漏不误**：拿不准放行 math，数学题永远不会被拦在门外——误拦是更糟的产品事故。（`_SYSTEM_TEMPLATE` `subject_classify.py:39`）
- **闭集外不硬归类**：None（不是 other）对 Java 表示"不知道"，语义清晰。
- **慢修复原则**：学科门是前置卡点，必须秒出，20s 超时快速返回让 Java 降级。
