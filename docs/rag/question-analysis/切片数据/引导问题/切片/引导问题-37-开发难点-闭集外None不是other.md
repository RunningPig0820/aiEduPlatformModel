# 闭集外（地质/天文）怎么处理？为什么是 None 而不是 other？

> summary: 闭集外（地质/天文）怎么处理？为什么是 None 而不是 other？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-37-开发难点-闭集外None不是other.md
> 类别：开发难点

---

## 回答

**核心结论**：闭集外返回 **None（不是 other）**——other 的语义是"明确非学科内容"，闭集外是"**不知道**"，两回事。返回 None 让 Java 按 math 放行，**宁漏拦不误拦**，不污染 other 桶语义。

**分层展开**：
- **语义区分**：other = "明确非学科内容"（图片无法辨认/闲聊）；None = "不知道"（闭集外如地质/天文）。硬把闭集外归到 other 是语义污染。（依据：坑档案 J-QT8 / 分析-03）
- **代码实现**：`_parse_subject` 解析到闭集外 → 返回 None（不是 other），Java 按 math 放行。（依据：坑档案 J-QT8 / `subject_classify.py:45-55`）
- **为什么宁放过**：数学题永远不能被拦在门外——宁可放过（垃圾学科题可能进答疑），不可误判（学生问数学被拒是更糟产品事故）。（依据：完善文档 04 追问 / 分析-03）
- **测试锁死**：`test_subject_classify.py:71-78` 断言闭集外 → None。（依据：坑档案 J-QT8）

> 证据：详见 `7. 引导问题/问题列表.md`（第 37 问）｜ `5.难点/坑档案.md`（J-QT8）｜ `3.代码/分析-03-subject-classify学科门.md`
