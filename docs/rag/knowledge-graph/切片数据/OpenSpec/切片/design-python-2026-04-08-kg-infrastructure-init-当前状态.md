# 当前状态：curriculum 模块与后续模块
> summary: 课程模块 OCR 321KB/189页，知识点提取与类型推断等需 100+ 次 glm-4-flash 调用，中途失败需重头开始，故需断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-当前状态.md
> 类别：架构设计

> 检索摘要：课程模块 OCR 321KB/189页，知识点提取与类型推断等需 100+ 次 glm-4-flash 调用，中途失败需重头开始，故需断点续传。

**curriculum 模块（课标处理）**：
- OCR 文件: 321KB（189 页）
- LLM 调用场景:
  - 知识点提取: ~15 次分块调用
  - 类型推断: ~100+ 次调用（每个知识点）
  - 定义生成: ~100+ 次调用
  - 关系提取: ~10+ 次调用
- 模型: glm-4-flash（免费）
- 问题: 中途失败需要重头开始

**后续模块（教材处理）**：
- 知识点匹配
- 先修关系推断（可能使用付费模型）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§当前状态：curriculum 模块与后续模块）
