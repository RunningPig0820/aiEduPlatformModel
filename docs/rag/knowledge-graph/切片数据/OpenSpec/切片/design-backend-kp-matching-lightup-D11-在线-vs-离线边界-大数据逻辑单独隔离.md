# 在线 vs 离线边界：大数据逻辑单独隔离

> summary: 派生层逻辑按在线（解析管线/掌握度点亮）与离线（obs→题型库聚合/维护重判）拆分，离线逻辑进 batch 包标注大数据归宿，当前 @Scheduled 过渡。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D11-在线-vs-离线边界-大数据逻辑单独隔离.md
> 类别：架构设计

> 检索摘要：派生层逻辑按在线（解析管线/掌握度点亮）与离线（obs→题型库聚合/维护重判）拆分，离线逻辑进 batch 包标注大数据归宿，当前 @Scheduled 过渡。

**决策**：派生层逻辑按「实时在线」与「离线批处理」拆分：

| 类型 | 逻辑 | 位置 |
|------|------|------|
| **在线（实时）** | 解析管线（写 obs + 读题型库先验）、掌握度点亮 | 业务域（learning / ai/tutoring） |
| **离线（批处理）** | obs→题型库聚合、维护重判、先验漂移 | `com.ai.edu.application.service.batch` |

离线逻辑单独拆到 `batch` 包，`package-info.java` + 类 javadoc 明确标注「逻辑归宿=大数据平台，当前后端 @Scheduled 过渡实现」。

**理由**：聚合/维护本质是离线批处理（不要求实时、obs 无限长尾），理想归宿是大数据平台；当前项目纯 Java DDD 后端未接大数据，故先以 @Scheduled 过渡。数据表（obs/题型库）为中性结构，大数据可直接读写，未来迁移只需替换 batch 包，在线解析管线②与数据表不变。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D11 在线 vs 离线边界：大数据逻辑单独隔离）
