# 演进与未来

> summary: 演进与未来
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-15-演进与未来.md
> 类别：未来演进

---

> 检索摘要：多版本教材什么时候支持？URI 怎么调整为多版本？单元层级未来怎么演进？前置关系推断由谁负责？

## 多版本教材支持（D13，未来扩展）

支持北师大版、苏教版等多版本教材：
- URI 设计调整：当前 renjiao-g1s（隐含版本）→ 未来 {edition}-{grade}{semester}，如 renjiao-g1s（人教版）、bnu-g1s（北师大版）、sujiao-g1s（苏教版）
- 数据模型扩展：publisher 从固定"人民教育出版社"改动态配置；edition 从固定"人教版"改动态配置；新增 version_code 用于版本对比
- 当前阶段：不实现，记录在 Non-Goals，多版本作为 v3.2 版本规划

## 阶段与未来方向

当前设计处于教材匹配完整图谱阶段，输出 JSON 经人工验证后手动导入 Neo4j。前置关系推断（TEACHES_BEFORE/PREREQUISITE）不在此文档范围，由 kg-math-prerequisite-inference 模块负责。单元/专题层级：当前阶段采用方案 B（Chapter 增加 topic 字段），后续迭代可扩展为方案 A（新增 Unit 节点，支持跨年级专题）。

## 开放问题（Open Questions 节选）

- Q4 单元/专题层级采用哪种方案：建议当前阶段采用方案 B（Chapter.topic 字段），后续迭代可扩展
- Q6 多版本教材何时支持：建议当前专注人教版，多版本作为 v3.2 版本规划

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D13 / §D12 / §Open Questions）
