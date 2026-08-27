# vector query 返回字段错位

> summary: COS `query_vectors` 实际返回 `(resp, data)`、命中在 `data["vectors"]`，非契约假设的 `hits`，Java 桥解析不到；契约需按 COS 实际返回对齐。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-前端联调问题单-问题13-vector-query返回字段错位.md
> 类别：开发难点
> 状态：✅ 已修复
> entry_id: 问题13
> source_doc: 语雀-前端联调问题单.md
> tags: ["问题13","接口","status_done"]

---

### 问题13：vector query 返回字段错位
> 状态：✅ 已修复
> 检索摘要：COS `query_vectors` 实际返回 `(resp, data)`、命中在 `data["vectors"]`，非契约假设的 `hits`，Java 桥解析不到；契约需按 COS 实际返回对齐。

| 属性 | 内容 |
|---|---|
| 现象 | Java 桥解析 vector query 响应拿不到 hits |
| 触发流程 | 调 /api/tutoring/vector/query |
| 根因 | COS `query_vectors` 返回 `(resp, data)`，命中在 `data["vectors"]`，非契约假设的 `hits` |
| 修复方案 | 契约按 COS 实际返回 `{"vectors":[{key,metadata,distance}]}` 对齐 |
| 状态 | ✅ 已修复（Python 侧） |
| 证据 | design-python-question-type-mastery-python D3 |

> 证据：详见 `1.语雀/语雀-前端联调问题单.md`（§问题13）｜ 语雀-决策记录.md D13 ｜ 完善文档 03-架构与微服务分工.md
