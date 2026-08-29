# 课标链路与小学补全

> summary: 课标链路与小学补全
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-infrastructure-init-09-课标链路与小学补全.md
> 类别：数据关联

本文为图谱基础设施初始化设计稿（design-python-2026-04-08-kg-infrastructure-init）中的课标处理（curriculum 模块）场景，属设计阶段素材（已落地/构想未实现/待决策并存），业务真实实现请以权威度 0.8 的 canonical 真相源文档为准。

## curriculum 模块（课标处理）

- OCR 文件：321KB（189 页）
- 模型：glm-4-flash（免费）
- LLM 调用场景：
  - 知识点提取：约 15 次分块调用
  - 类型推断：约 100+ 次调用（每个知识点）
  - 定义生成：约 100+ 次调用
  - 关系提取：约 10+ 次调用
- 问题：中途失败需要重头开始，故需要断点续传

## 后续模块（教材处理）

- 知识点匹配
- 先修关系推断（可能使用付费模型）
