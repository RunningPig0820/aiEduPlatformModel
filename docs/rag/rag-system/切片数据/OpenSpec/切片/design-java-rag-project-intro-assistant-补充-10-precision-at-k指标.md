# precision_at_k 指标(相关判定细节)
> summary: precision_at_k相关判定沿用expected_references的节号匹配(非语义判断),计算相关块占比0~1纳入聚合指标展示
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-rag-project-intro-assistant-补充-10-precision-at-k指标.md
> 类别：开发难点

---

### precision_at_k 指标(相关判定细节)
> 检索摘要：precision_at_k相关判定沿用expected_references的节号匹配(非语义判断),计算相关块占比0~1纳入聚合指标展示

目标 D10 已定义 `precision_at_k`(召回 top-k 中相关块占比,纯函数)。本块独有:相关判定**沿用 expected_references 的节号匹配**(非语义判断),计算相关块占比 0~1,纳入聚合指标展示。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充(原 spec-java-rag-project-intro-assistant-eval 独有内容)/precision_at_k 指标）
