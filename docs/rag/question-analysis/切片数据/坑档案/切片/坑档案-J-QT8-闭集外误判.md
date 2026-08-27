# 坑档案 J-QT8 闭集外误判：把地质/天文归成 other

> summary: 闭集外误判：把地质/天文归成 other
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J-QT8. 闭集外误判
> 模块: question-analysis ｜ 节: 坑档案
> COS路径: rag-slices/question-analysis/坑档案/坑档案-J-QT8-闭集外误判.md
> 类别：开发难点

---

**1. 问题现象**：非 K12 学科内容被归为 other，语义污染。

**2. 触发流程**：subject-classify 解析到闭集外内容（如"地质""天文"）→ 归到 other。

**3. 根因分析**：other 的语义是"明确非学科内容"，但闭集外是"**不知道**"——两回事。硬归类会污染 other 桶。

**4. 排查过程**：`_parse_subject` 设计讨论发现。

**5. 解决方案 & 改动点**：**闭集外 → None（不是 other）**，Java 按 math 放行（宁漏拦不误拦）。（`subject_classify.py:45-55`、测试 `test_subject_classify.py:71-78`）

**6. 面试口述要点**：other 和 None 语义必须分开——other 是"明确非学科"，None 是"我不知道"。把地质天文硬归到 other 是污染，返回 None 让上游放行更安全。宁可放过，不可误判。
