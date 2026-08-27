# alias 匹配 miss 怎么解决？"静默降级"是什么坑？

> summary: alias 匹配 miss 怎么解决？"静默降级"是什么坑？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-34-开发难点-alias匹配miss静默降级.md
> 类别：开发难点

---

## 回答

**核心结论**：**静默降级** = 匹配不上不报错，直接显示"未开始"——坑在于学生练了很多却看不到掌握度。根因是分析接口返回 LLM 原始名、掌握表 key 是归并后的 canonical 名，名字对不上。解决：**后端保证 analyze 返回 topicLabel = canonical**（返回前也过归并归一），前端等号匹配即可。

**分层展开**：
- **现象**：学生"鸡兔同笼"练了很多，掌握度页却显示"未开始"。（依据：坑档案 J-QT5）
- **根因**：`analyze-question` 返回原始题型名（"解一元二次方程"），前端拿它查 `getMastery`（key=canonical "一元二次方程"）→ 等号匹配 miss → 误判未开始；**匹配不上不报错**，是静默降级。（依据：坑档案 J-QT5）
- **解决**：后端保证 analyze-question 返回的 topicLabel = canonical（返回前也过聚集 post-process）——前端直接等号匹配即可，把名字对齐收敛在后端一处。（依据：坑档案 J-QT5 / 完善文档 02 alias 收敛）
- **对账**：识别出的题型名必须和掌握表 key 同构，否则"相遇问题"vs"行程问题"静默 miss。（依据：完善文档 02）

> 证据：详见 `7. 引导问题/问题列表.md`（第 34 问）｜ `5.难点/坑档案.md`（J-QT5）｜ `4.完善文档/02-题型分析主流程怎么走.md`
