# analyze.topicLabel 非 canonical（alias miss）

> summary: analyze 返回原始题型名与掌握表 canonical 名不一致，前端等号匹配 miss 静默显示"未开始"，学生困惑；需后端返回前过聚集 post-process。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-前端联调问题单-问题5-analyze.topicLabel非canonical（alias miss）.md
> 类别：开发难点
> 状态：⚠️ 待办

---

### 问题5：analyze.topicLabel 非 canonical（alias miss）
> 状态：⚠️ 待办
> 检索摘要：analyze 返回原始题型名与掌握表 canonical 名不一致，前端等号匹配 miss 静默显示"未开始"，学生困惑；需后端返回前过聚集 post-process。

| 属性 | 内容 |
|---|---|
| 现象 | 学生鸡兔同笼练很多，掌握度页显示"未开始" |
| 触发流程 | analyze 返回原始名"解一元二次方程" → 前端拿它查 getMastery（key="一元二次方程"）→ 等号 miss |
| 根因 | analyze 返回前未过聚集 post-process，非 canonical；掌握表 key 是 canonical |
| 修复方案 | 后端保证 analyze 返回 topicLabel = canonical（返回前过聚集） |
| 状态 | ⚠️ 待办（P0）`后端需修` |
| 证据 | 语雀-方案设计2-问题1 坑1 |

> 证据：详见 `1.语雀/语雀-前端联调问题单.md`（§问题5）｜ 语雀-决策记录.md D22 ｜ 完善文档 05-数据落库与掌握度.md、06-题型动态聚集与向量.md ｜ 坑档案 J-QT5
