# 点亮 + 疑似态

> summary: 掌握度显示=掌握值×置信档位两维，解析低置信/挂起渲染疑似态（虚线+待确认角标），错解析回退打标 MIGRATED 挂人工复核不自动删。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D6-点亮-疑似态.md
> 类别：数据存储

> 检索摘要：掌握度显示=掌握值×置信档位两维，解析低置信/挂起渲染疑似态（虚线+待确认角标），错解析回退打标 MIGRATED 挂人工复核不自动删。

**决策**：掌握度显示 = 掌握值 × 置信档位两维。

| 档位（MasteryLevel 五档） | 掌握值 | 语义 | 前端视觉 |
|---|---|---|---|
| notStarted | 0 | 未开始（还没学） | ⚪ 中性灰 |
| beginner | 25 | 入门/薄弱 | 🔴 红 |
| intermediate | 50 | 进阶/练习中 | 🟡 黄 |
| advanced | 75 | 高级/掌握 | 🟢 绿 |
| master | 100 | 精通 | 🟢 深绿 |
| 解析低置信/挂起 | — | **疑似** | ⚪ 虚线 +「待确认」角标 |

- 挂起 label **不落掌握度**（不污染数据），前端渲染"疑似薄弱"待确认态。
- `MasteryItemDTO` 增加 `status`(RESOLVED/PENDING) + `confidence`；前端再叠加 obs 的 PENDING 列表渲染疑似节点。

**掌握度回退（错解析）**：重判把 二元一次方程组→假设法 后，错记在旧 kp 上的掌握度**打标 `MIGRATED` + 挂人工复核**，不自动删（自动删可能丢真实信号）。本期只打标 + 记录迁移日志，自动迁移列为后续。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D6 点亮 + 疑似态）
