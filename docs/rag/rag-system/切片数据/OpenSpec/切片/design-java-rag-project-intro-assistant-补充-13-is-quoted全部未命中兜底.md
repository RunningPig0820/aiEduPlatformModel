# is_quoted 确定性硬匹配(全部未命中兜底)
> summary: top-K块全部未命中时answer标注"基于现有知识库,引用未能精确匹配",quotedKeys为空不假装存在引用
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-rag-project-intro-assistant-补充-13-is-quoted全部未命中兜底.md
> 类别：架构设计

---

### is_quoted 确定性硬匹配(全部未命中兜底)
> 检索摘要：top-K块全部未命中时answer标注"基于现有知识库,引用未能精确匹配",quotedKeys为空不假装存在引用

目标 D6 已定义 LCS 硬匹配、8 中/12 英窗口与 done 后补发 quoted_keys。本块独有:**全部未命中场景**——WHEN top-K 块全部未命中 → THEN answer 标注"基于现有知识库,引用未能精确匹配",`quotedKeys` 为空,**不假装存在引用**。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§补充(原 spec-java-rag-project-intro-assistant-guardrails 独有内容)/is_quoted 确定性硬匹配）
