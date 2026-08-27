# put 后立查 miss

> summary: COS 向量索引 put 后约 10s 异步生效，题型名向量入库后立即 query 查不到近邻；建锚不立查 + 留重试。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-前端联调问题单-问题14-put后立查miss.md
> 类别：开发难点
> 状态：✅ 已修复（方案定稿）

---

### 问题14：put 后立查 miss
> 状态：✅ 已修复（方案定稿）
> 检索摘要：COS 向量索引 put 后约 10s 异步生效，题型名向量入库后立即 query 查不到近邻；建锚不立查 + 留重试。

| 属性 | 内容 |
|---|---|
| 现象 | 题型名向量入库后立即 query 查不到近邻 |
| 触发流程 | put_vectors → 立即 query_vectors |
| 根因 | COS 向量索引 put 后 ~10s 异步生效 |
| 修复方案 | 建锚不立查 + 留重试；put 后 query 容忍延迟 |
| 状态 | ✅ 已修复（方案定稿） |
| 证据 | design-python D3 |

> 证据：详见 `1.语雀/语雀-前端联调问题单.md`（§问题14）｜ 语雀-决策记录.md D13 ｜ 完善文档 06-题型动态聚集与向量.md ｜ 坑档案 J-QT1
