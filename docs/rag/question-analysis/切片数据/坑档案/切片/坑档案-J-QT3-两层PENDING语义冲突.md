# 坑档案 J-QT3 两层 PENDING 语义冲突

> summary: 两层 PENDING 语义冲突：识别失败与知识点待确认混用一变量
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J-QT3. 两层 PENDING 语义冲突
> 模块: question-analysis ｜ 节: 坑档案
> COS路径: rag-slices/question-analysis/坑档案/坑档案-J-QT3-两层PENDING语义冲突.md
> 类别：开发难点

---

**1. 问题现象**：前端用一个 `status === 'PENDING'` 分支同时处理两类完全不同的状态，导致"题型没认出来"和"知识点待确认"混成一种展示。

**2. 触发流程**：`analyze-question` 返回 PENDING（题型没敢确定）→ 前端按"待确认"分支展示候选；`getMastery` 返回 PENDING（题型已练但知识点待确认）→ 前端也走"待确认"。

**3. 根因分析**：同一个词 PENDING 在两个接口里含义完全不同——analyze 的 PENDING = "识别失败"；getMastery 的 PENDING = "题型掌握了但知识点挂起"。共用一个变量必然混。

**4. 排查过程**：语雀-方案设计2-问题1 逐坑拆解发现。

**5. 解决方案 & 改动点**：**两层分开判**——识别结果（analyze.status）：RESOLVED → 查掌握度 / PENDING → 展示候选，到此为止；掌握度（getMastery.status）：RESOLVED+四档 / PENDING → 待确认。绝不共用一个判断变量。

**6. 面试口述要点**：这个坑最阴——同一个词 PENDING，两个接口含义完全相反。识别层的 PENDING 是"我连题型都没敢确定"，掌握度的 PENDING 是"题型已练、知识点待确认"。如果前端用一个变量判断，学生看到的就是错误的状态。解决就是分层：识别失败就不查掌握度，识别成功才看四态。
