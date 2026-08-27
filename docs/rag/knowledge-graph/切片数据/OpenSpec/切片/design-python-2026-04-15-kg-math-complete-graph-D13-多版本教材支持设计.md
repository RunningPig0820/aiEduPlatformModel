# 多版本教材支持设计

> summary: 多版本教材支持：URI从隐含版本扩展为{edition}-{grade}{semester}支持北师大/苏教版，数据模型加version_code，当前阶段不实现。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D13-多版本教材支持设计.md
> 类别：未来演进

---

### D13：多版本教材支持设计

> 检索摘要：多版本教材支持：URI从隐含版本扩展为{edition}-{grade}{semester}支持北师大/苏教版，数据模型加version_code，当前阶段不实现。

**未来扩展**: 支持北师大版、苏教版等多版本教材

**URI 设计调整**:

```
当前：renjiao-g1s（隐含版本）
未来：{edition}-{grade}{semester}
  - renjiao-g1s（人教版）
  - bnu-g1s（北师大版）
  - sujiao-g1s（苏教版）
```

**数据模型扩展**:

| 属性 | 当前 | 扩展后 |
|------|------|--------|
| `publisher` | 固定"人民教育出版社" | 动态配置 |
| `edition` | 固定"人教版" | 动态配置 |
| `version_code` | 无 | 新增，用于版本对比 |

**当前阶段**: 不实现，记录在 Non-Goals

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D13：多版本教材支持设计）
