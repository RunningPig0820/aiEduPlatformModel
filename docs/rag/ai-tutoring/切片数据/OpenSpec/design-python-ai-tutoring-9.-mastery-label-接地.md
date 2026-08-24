# design-python-ai-tutoring

> summary: 解决AI答疑中知识点标签与URI解析命中率问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 9. mastery label 接地
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring

---

### 9. mastery label 接地

把 `mastery_snapshot` 的 label 作为"已知知识点候选"注入 prompt,模型优先复用;新推断 label 提示"与教材知识点名一致"。提升 Java 侧 label→URI 解析命中率。
