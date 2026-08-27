# COS 权限不足
> summary: 子账号缺少 COS 桶操作权限，put/query 全部失败，需要提前配置对应 COS 权限。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景13-COS权限不足.md
> 类别：开发难点
> 状态：⚠️
> entry_id: 场景13
> source_doc: 语雀-边界场景清单.md
> tags: ["场景13","基础设施","status_suggest"]

---

### 场景13：COS 权限不足
> 状态：⚠️
> 检索摘要：子账号缺少 COS 桶操作权限，put/query 全部失败，需要提前配置对应 COS 权限。

| 属性 | 内容 |
|---|---|
| 业务场景 | COS 权限不足 |
| 触发条件 | 子账号密钥未授权向量桶操作 |
| 当前处理 | 未处理（spike 结论：需授权 QcloudCOSFullAccess 或对应权限） |
| 兜底降级策略 | 权限补齐后 put/query/delete 全通 |
| 残余风险 | 联调前需确认参数清单 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景13）｜ 完善文档 06-题型动态聚集与向量.md
