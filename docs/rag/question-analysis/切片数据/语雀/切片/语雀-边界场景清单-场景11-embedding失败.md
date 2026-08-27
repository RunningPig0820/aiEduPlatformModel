# embedding 失败
> summary: 大模型 embedding 接口超时不可用，向量层抛出 500，Java 桥降级，主链路不受影响。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景11-embedding失败.md
> 类别：开发难点

---

### 场景11：embedding 失败
> 检索摘要：大模型 embedding 接口超时不可用，向量层抛出 500，Java 桥降级，主链路不受影响。

| 属性 | 内容 |
|---|---|
| 业务场景 | embedding 失败 |
| 触发条件 | dashscope 不可用/超时 |
| 当前处理 | 向量端点错误冒泡（HTTP 500）→ Java 桥降级（与 subject-classify 相反：不吞异常） |
| 兜底降级策略 | 同上，Java 桥降级 |
| 残余风险 | embedding 是增强层，失败不影响主链路 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景11）｜ 完善文档 06-题型动态聚集与向量.md
