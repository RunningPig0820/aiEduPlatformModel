# PENDING 空候选 → 知识点搜索确认

> summary: PENDING 空候选→knowledge-points 加 keyword，学生搜索镜像知识点确认（机器猜不出学生自己指），vote 不 10003。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D8-pending空候选知识点搜索确认.md
> 类别：开发难点

---

### 决策 8：PENDING 空候选 → 知识点搜索确认（后端加 keyword 搜索）

> 检索摘要：PENDING 空候选→knowledge-points 加 keyword，学生搜索镜像知识点确认（机器猜不出学生自己指），vote 不 10003。

实测冷启动题型（鸡兔同笼）analyze/resolve 均返回**空候选**，PENDING 空态是死胡同——学生无法主动确认。方案：**后端给 `POST /api/kg/knowledge-points` 加可选 `keyword`**（有 keyword 时跨学段按 label 搜索，无 keyword 保持原分页行为），前端 PENDING 空态 + 待确认清单空候选时提供「搜索知识点」选择器：

```
暂无法确认关联知识点
  🔍 搜索知识点…（实时搜，防抖）
  ○ 用适当方法解二元一次方程组   ← 选中
  ○ 鸡兔同笼问题
  [确认所选知识点] → vote(topicLabel, kpLabel)
```

选中项来自知识图谱镜像（`listKnowledgePoints` 返回的 kpLabel），**天然满足 vote 的 findByLabel 校验，不会 10003**。

理由：候选空 = 后端 LLM/镜像冷启动猜不出，但教材知识图谱里有对应知识点（如「用适当方法解二元一次方程组」）——搜索是「机器猜不出，学生自己指」的兜底，把 PENDING 死胡同变成可操作路径。后端改动极小（一个可选 keyword 参数），前端搜索框可复用（题型分析空态 + 待确认清单两处）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 8）｜ 语雀-决策记录.md D15 ｜ 语雀-边界场景清单.md 场景6/场景17 ｜ 完善文档 07-题目知识点与图谱关联.md
