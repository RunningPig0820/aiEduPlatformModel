# 坑档案 J-QT5 alias 匹配 miss：analyze 返回原始名查不到掌握度

> summary: alias 匹配 miss：analyze 返回原始名查不到掌握度
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J-QT5. alias 匹配 miss
> 模块: question-analysis ｜ 节: 坑档案
> COS路径: rag-slices/question-analysis/坑档案/坑档案-J-QT5-alias匹配miss.md
> 类别：开发难点

---

**1. 问题现象**：学生"鸡兔同笼"练了很多，掌握度页却显示"未开始"。

**2. 触发流程**：`analyze-question` 返回原始题型名（"解一元二次方程"）→ 前端拿它查 `getMastery`（key=canonical "一元二次方程"）→ 等号匹配 miss → 误判未开始。

**3. 根因分析**：analyze 返回的 topicLabel 没过聚集 post-process，不是 canonical；掌握表 key 是 canonical。名字不对齐，前端查不到。

**4. 排查过程**：语雀-方案设计2-问题1 坑1 拆解 + 联调踩过（贴"x²-5x+6=0"→"一元二次方程"原文叫"解一元二次方程"）。

**5. 解决方案 & 改动点**：**后端保证 analyze-question 返回的 topicLabel = canonical**（返回前也过聚集 post-process）——前端直接等号匹配即可。（design Decision 9）

**6. 面试口述要点**：这个坑是"静默降级"——匹配不上不报错，直接显示未开始。原因是 analyze 返回的是 LLM 原始名，掌握表 key 是向量归并后的 canonical 名，两个名字对不上。解法是让 analyze 返回前也过一遍聚集归一，前端用 canonical 名等号匹配。
